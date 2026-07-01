#!/usr/bin/env python3
"""
将全部对话Markdown文件转换为ShareGPT JSONL格式
按 国家/语言/人格类型/场景 分类
"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict

# ============================================================
# 配置
# ============================================================
INPUT_DIR = Path("对话")
OUTPUT_DIR = Path("sharegpt_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# 国家→文件映射和元数据
COUNTRY_CONFIG = {
    "JP": {
        "file": "V3日本养老院老人&AI陪护 第三版（8用户画像版）.md",
        "country_cn": "日本",
        "country_en": "Japan",
        "language": "ja",
        "language_cn": "日语",
    },
    "KR": {
        "file": "韩国养老院老人&AI陪护 80轮对话（8人格×10轮｜韩中对照）.md",
        "country_cn": "韩国",
        "country_en": "Korea",
        "language": "ko",
        "language_cn": "韩语",
    },
    "US": {
        "file": "美国养老院老人&AI陪护 80轮对话（8人格×10轮｜英中对照）.md",
        "country_cn": "美国",
        "country_en": "USA",
        "language": "en",
        "language_cn": "美式英语",
    },
    "CN_N": {
        "file": "中国北方养老院老人&AI陪护 80轮对话（8人格×10轮｜普通话·北方方言）.md",
        "country_cn": "中国",
        "country_en": "China",
        "language": "zh-CN",
        "language_cn": "普通话·北方方言",
        "region": "华北/东北",
    },
    "UK": {
        "file": "英国养老院老人&AI陪护 80轮对话（8人格×10轮｜英中对照）.md",
        "country_cn": "英国",
        "country_en": "UK",
        "language": "en-GB",
        "language_cn": "英式英语",
    },
    "TH": {
        "file": "泰国养老院老人&AI陪护 80轮对话（8人格×10轮｜泰中对照）.md",
        "country_cn": "泰国",
        "country_en": "Thailand",
        "language": "th",
        "language_cn": "泰语",
    },
    "CN_YUE": {
        "file": "中国粤语养老院老人&AI陪护 80轮对话（8人格×10轮｜粤语·普通话对照）.md",
        "country_cn": "中国",
        "country_en": "China",
        "language": "yue",
        "language_cn": "粤语",
        "region": "广东/香港",
    },
    "FR": {
        "file": "法国养老院老人&AI陪护 80轮对话（8人格×10轮｜法中对照）.md",
        "country_cn": "法国",
        "country_en": "France",
        "language": "fr",
        "language_cn": "法语",
    },
}

# 人格类型元数据
PERSONA_META = {
    "A": {"type_cn": "寡言沉默型", "type_en": "Taciturn", "traits": "慢语速、短句、大量沉默、内敛"},
    "B": {"type_cn": "喋喋话痨型", "type_en": "Chatterbox", "traits": "快语速、话题跳跃、自我重复、情绪外放"},
    "C": {"type_cn": "浓方言型", "type_en": "Heavy Dialect", "traits": "方言词汇密集、本土文化浓厚"},
    "D": {"type_cn": "标准高知型", "type_en": "Educated Standard", "traits": "标准语、敬语完整、条理清晰"},
    "E": {"type_cn": "温柔奶奶型", "type_en": "Gentle Grandmother", "traits": "语速慢、话多但轻柔、反复关心他人"},
    "F": {"type_cn": "急躁直率型", "type_en": "Irritable Direct", "traits": "语速快、反问多、直接表达不满"},
    "G": {"type_cn": "怀旧少言型", "type_en": "Nostalgic Quiet", "traits": "极慢语速、断断续续、沉浸过去"},
    "H": {"type_cn": "干脆简洁型", "type_en": "Crisp Concise", "traits": "短句、指令式、不说废话"},
}


def find_input_file(filename, country_code=""):
    """查找输入文件，优先精确匹配"""
    path = INPUT_DIR / filename
    if path.exists():
        return path
    # 模糊匹配：按国家代码优先级
    candidates = []
    for f in INPUT_DIR.glob("*.md"):
        fname = f.name
        # 跳过非目标国家的文件
        if country_code == "JP" and "日本" not in fname:
            continue
        if country_code == "JP" and ("V1" in fname or "100轮" in fname):
            continue  # 跳过V1模板版
        candidates.append(f)

    if candidates:
        # 优先选V3或第三版
        for c in candidates:
            if "V3" in c.name or "第三版" in c.name:
                return c
        return candidates[0]
    return None


def parse_japanese_v3(text):
    """解析日本第三版"""
    records = []
    current_persona = None
    current_persona_type = None
    current_group = None
    current_round = None
    scenario = ""
    human_lines = []
    ai_lines = []

    lines = text.split("\n")

    for line in lines:
        # 检测场景头: ## 第X組｜A:山下ハル（82歳・京都・浓関西弁）
        group_match = re.match(
            r"##\s*第(\d+)組[｜|]\s*([A-H]):\s*(\S+?)（(\d+)歳・(\S+)・(.+?)）", line
        )
        if group_match:
            # 保存之前的数据
            if human_lines and ai_lines:
                records.append(build_record(
                    current_persona, current_persona_type, current_group,
                    scenario, human_lines, ai_lines
                ))
            current_group = int(group_match.group(1))
            current_persona_type = group_match.group(2)
            current_persona = {
                "id": group_match.group(2),
                "name": group_match.group(3),
                "age": int(group_match.group(4)),
                "origin": group_match.group(5),
                "persona_type_cn": group_match.group(6),
            }
            human_lines = []
            ai_lines = []
            continue

        # 检测场景: **場面：朝の起居・服薬確認**
        scene_match = re.match(r"\*\*場面[：:]\s*(.+?)\*\*", line)
        if scene_match:
            scenario = scene_match.group(1).strip()
            continue

        # 检测回合: **1-1**
        round_match = re.match(r"\*\*(\d+)-(\d+)\*\*", line)
        if round_match:
            # 保存前一个round
            if human_lines and ai_lines:
                records.append(build_record(
                    current_persona, current_persona_type, current_group,
                    scenario, human_lines, ai_lines
                ))
            current_round = int(round_match.group(2))
            human_lines = []
            ai_lines = []
            continue

        # 检测对话行
        dialog_match = re.match(
            r"([^\s：:]{1,15})[：:]\s*(.+)", line
        )
        if dialog_match and current_persona:
            speaker = dialog_match.group(1).strip()
            text = dialog_match.group(2).strip()

            if speaker == "AI" or speaker == "ＡＩ":
                ai_lines.append(text)
            elif speaker not in ("翻訳", "翻译", "場面", "场景"):
                human_lines.append(text)

    # 最后一个record
    if human_lines and ai_lines:
        records.append(build_record(
            current_persona, current_persona_type, current_group,
            scenario, human_lines, ai_lines
        ))

    return records


def parse_generic_multilang(text, country_code):
    """
    通用解析：韩/美/英/泰/粤/法/中国北方
    """
    # ==== 预处理：展开紧凑格式 ====
    # UK/FR/CN_YUE 使用紧凑格式：A-1: text / AI: text / name: text
    expanded_lines = []
    for line in text.split("\n"):
        if re.search(r"\s*/\s*(?:AI|ＡＩ)[：:]", line):
            parts = re.split(r"\s*/\s*(?=(?:AI|ＡＩ|[A-Z][a-z]+)[：:])", line)
            for part in parts:
                expanded_lines.append(part.strip())
        else:
            expanded_lines.append(line)
    text = "\n".join(expanded_lines)

    records = []
    current_persona = None
    current_persona_type = None
    current_group = None
    scenario = ""
    human_lines = []
    ai_lines = []

    lines = text.split("\n")

    for line in lines:
        # 检测类型头: 支持多种格式
        #   ## 【A型｜寡言沉默型】name / ## 【Type A｜Taciturn】name / ## 【A寡言】name
        header_match = re.match(
            r"##\s*【(?:Type\s*)?([A-H])\s*(?:[型｜|])?\s*(.+?)】\s*(.+)", line
        )
        if header_match:
            if human_lines and ai_lines:
                records.append(build_record(
                    current_persona, current_persona_type, current_group,
                    scenario, human_lines, ai_lines
                ))
            current_persona_type = header_match.group(1)
            type_name = header_match.group(2)
            person_info = header_match.group(3)

            # 尝试解析个人信息
            info_match = re.match(r"(\S+?)（(\d+)歳[・·]\s*(.+?)）", person_info)
            if info_match:
                current_persona = {
                    "id": current_persona_type,
                    "name": info_match.group(1),
                    "age": int(info_match.group(2)),
                    "origin": info_match.group(3),
                    "persona_type_cn": type_name,
                }
            else:
                # 英语格式: Walter "Walt" Kowalski（84・Detroit・Retired...）
                en_match = re.match(
                    r"(\S+(?:\s+\"[^\"]+\")?(?:\s+\S+)?)[（(](\d+)[・·,\s]+(.+?)[）)]", person_info
                )
                if en_match:
                    current_persona = {
                        "id": current_persona_type,
                        "name": en_match.group(1),
                        "age": int(en_match.group(2)),
                        "origin": en_match.group(3),
                        "persona_type_cn": type_name,
                    }
                else:
                    current_persona = {
                        "id": current_persona_type,
                        "name": person_info[:30],
                        "age": 0,
                        "origin": "",
                        "persona_type_cn": type_name,
                    }
            human_lines = []
            ai_lines = []
            continue

        # 检测场景/回合: ### A-1｜scene 或 ### A-1
        round_match = re.match(r"###\s*([A-H])-(\d+)[｜|]?\s*(.*)", line)
        if round_match:
            if human_lines and ai_lines:
                records.append(build_record(
                    current_persona, current_persona_type, current_group,
                    scenario, human_lines, ai_lines
                ))
            current_group = ord(round_match.group(1)) - ord("A") + 1
            scenario = round_match.group(3).strip() if round_match.group(3) else ""
            human_lines = []
            ai_lines = []
            continue

        # 检测回合 (紧凑格式): A-1: text
        compact_round = re.match(r"([A-H])-(\d+)[：:]\s*(.+)", line)
        if compact_round and current_persona:
            if human_lines and ai_lines:
                records.append(build_record(
                    current_persona, current_persona_type, current_group,
                    scenario, human_lines, ai_lines
                ))
            current_group = ord(compact_round.group(1)) - ord("A") + 1
            scenario = ""
            text = compact_round.group(3).strip()
            # 如果text以…开头或很短，可能是人类说
            if text and not text.startswith("(AI:"):
                human_lines.append(text)
            continue

        # 检测对话行: name: text 或 AI: text
        # 跳过分隔线和空行
        if re.match(r"^[-–—]{3,}$", line) or re.match(r"^\s*$", line):
            continue

        # 匹配人类或AI对话
        dialog = re.match(r"([^\s：:]{1,20})[：:]\s*(.+)", line)
        if dialog and current_persona:
            speaker = dialog.group(1).strip()
            text = dialog.group(2).strip()

            # 跳过明显的非对话行
            if speaker in ("---", "===", "…", "―", "場面", "场景", "Scenario", "類型", "类型"):
                continue

            if speaker in ("AI", "ＡＩ", "ai"):
                ai_lines.append(text)
            else:
                # 宽松匹配：只要不是明确的元数据标签，都当作人类对话
                # 支持缩写名（如 "최" 是 "최광수" 的缩写）
                persona_name = current_persona.get("name", "")
                if len(speaker) >= 1 and speaker not in (
                    "AI", "ＡＩ", "ai", "翻訳", "翻译", "Translation",
                ):
                    human_lines.append(text)

    # 最后一个
    if human_lines and ai_lines:
        records.append(build_record(
            current_persona, current_persona_type, current_group,
            scenario, human_lines, ai_lines
        ))

    return records


def build_record(persona, persona_type, group, scenario, human_lines, ai_lines):
    """构建单个ShareGPT记录"""
    if not persona or not human_lines or not ai_lines:
        return None

    conversations = []
    # 交错排列 human-AI 对话
    max_len = max(len(human_lines), len(ai_lines))
    for i in range(max_len):
        if i < len(human_lines) and human_lines[i].strip():
            conversations.append({
                "from": "human",
                "value": human_lines[i].strip()
            })
        if i < len(ai_lines) and ai_lines[i].strip():
            conversations.append({
                "from": "gpt",
                "value": ai_lines[i].strip()
            })

    if not conversations:
        return None

    return {
        "conversations": conversations,
        "persona_id": persona_type,
        "persona_name": persona.get("name", ""),
        "persona_age": persona.get("age", 0),
        "persona_origin": persona.get("origin", ""),
        "persona_type_cn": persona.get("persona_type_cn", ""),
        "scenario": scenario,
        "group": group,
    }


def post_process_records(records, country_code, config):
    """为记录添加国家和元数据"""
    for rec in records:
        if rec is None:
            continue
        rec["country_code"] = country_code
        rec["country_cn"] = config["country_cn"]
        rec["country_en"] = config["country_en"]
        rec["language"] = config["language"]
        rec["language_cn"] = config.get("language_cn", "")
        rec["region"] = config.get("region", "")
        # 添加人格元数据
        ptype = rec.get("persona_id", "")
        if ptype in PERSONA_META:
            rec["persona_type_en"] = PERSONA_META[ptype]["type_en"]
            rec["persona_traits"] = PERSONA_META[ptype]["traits"]
        # 生成唯一ID
        rec["id"] = f"{country_code}_{rec['persona_id']}_G{rec['group']:02d}_{rec['scenario'][:10]}"
    return [r for r in records if r is not None]


def save_records(records, country_code, output_dir):
    """保存记录到JSONL文件，按多个维度分类"""
    if not records:
        print(f"  ⚠️  {country_code}: 无记录")
        return

    base = output_dir

    # 1. 按国家分
    country_dir = base / "by_country"
    country_dir.mkdir(parents=True, exist_ok=True)
    with open(country_dir / f"{country_code}.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 2. 按人格类型分
    persona_dir = base / "by_persona"
    persona_dir.mkdir(parents=True, exist_ok=True)
    persona_groups = defaultdict(list)
    for r in records:
        persona_groups[r["persona_id"]].append(r)
    for ptype, recs in persona_groups.items():
        pname = PERSONA_META.get(ptype, {}).get("type_en", ptype)
        with open(persona_dir / f"{country_code}_{ptype}_{pname}.jsonl", "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 3. 全量合并文件
    all_file = base / "all.jsonl"
    mode = "a" if all_file.exists() else "w"
    with open(all_file, mode, encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"  ✅ {country_code}: {len(records)}条 → by_country/{country_code}.jsonl + by_persona/ + all.jsonl")


def generate_index(output_dir):
    """生成数据集索引文件"""
    all_records = []
    all_file = output_dir / "all.jsonl"
    if all_file.exists():
        with open(all_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_records.append(json.loads(line))

    # 统计
    stats = defaultdict(lambda: defaultdict(int))
    for r in all_records:
        stats[r["country_code"]]["total"] += 1
        stats[r["country_code"]][r["persona_id"]] += 1

    index = {
        "dataset_name": "Global_Elderly_Care_AI_Companion_Dialogue_Dataset",
        "version": "1.0.0",
        "format": "ShareGPT",
        "total_conversations": len(all_records),
        "countries": {},
    }

    for cc, config in COUNTRY_CONFIG.items():
        if cc in stats:
            index["countries"][cc] = {
                "country_cn": config["country_cn"],
                "country_en": config["country_en"],
                "language": config["language"],
                "language_cn": config.get("language_cn", ""),
                "total_conversations": stats[cc]["total"],
                "persona_breakdown": {
                    pt: count for pt, count in stats[cc].items() if pt != "total"
                },
            }

    with open(output_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n📊 索引: {output_dir / 'index.json'}")
    print(f"📊 总计: {len(all_records)} 条对话")


def main():
    print("=" * 60)
    print("ShareGPT Format Converter")
    print("=" * 60)

    total = 0

    for country_code, config in COUNTRY_CONFIG.items():
        print(f"\n📂 {config['country_cn']} ({country_code}) ...")

        filepath = find_input_file(config["file"], country_code)
        if not filepath:
            print(f"  ⚠️  找不到文件: {config['file']}")
            continue

        print(f"  📄 {filepath.name}")

        with open(filepath, encoding="utf-8") as f:
            text = f.read()

        # 选择解析器
        if country_code == "JP":
            records = parse_japanese_v3(text)
        else:
            records = parse_generic_multilang(text, country_code)

        records = post_process_records(records, country_code, config)
        save_records(records, country_code, OUTPUT_DIR)
        total += len(records)

    generate_index(OUTPUT_DIR)

    print(f"\n{'=' * 60}")
    print(f"✅ 转换完成！总计 {total} 条对话")
    print(f"📁 输出目录: {OUTPUT_DIR.absolute()}")
    print(f"\n目录结构:")
    print(f"  sharegpt_output/")
    print(f"  ├── all.jsonl                 ← 全量合并")
    print(f"  ├── index.json                ← 数据集索引")
    print(f"  ├── by_country/               ← 按国家分")
    print(f"  │   ├── JP.jsonl  KR.jsonl  US.jsonl  ...")
    print(f"  └── by_persona/               ← 按人格分")
    print(f"      ├── JP_A_Taciturn.jsonl ...")


if __name__ == "__main__":
    main()
