#!/usr/bin/env python3
"""
V8.1 数据质量修复：
1. 修复Whisper对话：只保留老年人发言作为human，丢弃采访者提问
2. 修复AI回复：使回复与上下文更相关
3. 处理独白型视频（W2pW9, igfukXU）
4. 修复连续同角色问题
"""
import json, re, random
from pathlib import Path
from collections import defaultdict, Counter

random.seed(42)
REAL_DIR = Path("real_elderly_audio")
TRAIN_DIR = Path("training_data")

VIDEO_INFO = {
    "06e_und6-C8": {"title": "65歳以上年金インタビュー", "duration_min": 61, "type": "interview"},
    "rQJEtScQqlU": {"title": "60-80代老後夫婦年金生活インタビュー", "duration_min": 81, "type": "interview"},
    "W2pW9-R0YfY": {"title": "76歳一人暮らし体験談", "duration_min": 56, "type": "monologue"},
    "igfukXU_i-Y": {"title": "83歳一人暮らし老人ホームの現実", "duration_min": 29, "type": "monologue"},
}

# ================================================================
# 工具函数
# ================================================================

def is_question(text):
    """检测是否为采访者提问"""
    text = text.strip()
    if len(text) < 3:
        return False
    if any(text.endswith(e) for e in ['か', 'か？', 'ですか', 'ですか？', 'ますか', 'ますか？', 'かな', 'かね']):
        return True
    if '？' in text or '?' in text:
        return True
    # Interviewer patterns
    interviewer_patterns = [
        r'聞いていい', r'教えて(ください|くれ|もら)', r'どう(いう|な|やって)',
        r'いくら', r'何歳', r'いつから', r'どこで',
        r'そうです[かね]', r'なるほど', r'へ[えー]',
    ]
    for p in interviewer_patterns:
        if re.search(p, text):
            return True
    return False

def is_short_fragment(text):
    """检测太短的碎片"""
    text = text.strip()
    if len(text) <= 3:
        return True
    if re.match(r'^[うんはいええああそうへえふーん]+[。、！？…]*$', text):
        return True
    if text in ['うん', 'はい', 'ええ', 'そう', 'うんうん', 'そうそう']:
        return True
    return False

def detect_topic(text):
    """话题检测"""
    combined = text
    topics = []
    if any(kw in combined for kw in ["年金", "お金", "受給", "生活費", "万円", "貯金", "給料", "収入", "支給"]):
        topics.append("pension")
    if any(kw in combined for kw in ["病気", "病院", "介護", "痛", "薬", "治療", "医者", "手術", "障害", "認知"]):
        topics.append("health")
    if any(kw in combined for kw in ["家族", "子供", "孫", "主人", "妻", "夫", "娘", "息子", "親", "両親"]):
        topics.append("family")
    if any(kw in combined for kw in ["施設", "ホーム", "入居", "老人"]):
        topics.append("facility")
    if any(kw in combined for kw in ["食事", "料理", "買い物", "掃除", "洗濯"]):
        topics.append("daily")
    if any(kw in combined for kw in ["孤独", "寂し", "一人", "友達", "話し相手"]):
        topics.append("loneliness")
    if any(kw in combined for kw in ["仕事", "働", "職業", "勤め", "退職", "現役", "会社"]):
        topics.append("work")
    if any(kw in combined for kw in ["旅行", "趣味", "楽しみ", "テレビ", "散歩", "運動"]):
        topics.append("hobby")
    return topics[0] if topics else "general"

# Enhanced topic responses — more specific and contextual
TOPIC_RESPONSES = {
    "pension": [
        "年金のことは本当に大切ですね。毎月のやりくり、大変だと思いますが、何かお手伝いできることはありますか？",
        "そうですか、年金だけでの生活はなかなか厳しいものがありますね。一緒に家計の見直しをしてみましょうか？",
        "なるほど。年金受給のことでご不安なことがあれば、いつでもご相談くださいね。",
        "生活費のことは心配ですよね。節約のアイデアなど、私でよければ一緒に考えますよ。",
    ],
    "health": [
        "お体のことはご心配ですよね。無理をなさらないでください。何か症状がありましたら教えてくださいね。",
        "健康が何より大切ですからね。お薬のことや通院のこと、何でもお手伝いしますよ。",
        "そうでしたか。体調管理は本当に大事です。ゆっくり休んで、ご無理なさらないでください。",
    ],
    "family": [
        "ご家族のことを大切に思われているんですね。素敵なことだと思います。",
        "そうでしたか。ご家族とのお話、もっと聞かせてください。",
        "家族の絆は本当に大切ですよね。何かお困りのことがあれば、いつでもお話しください。",
    ],
    "facility": [
        "施設のことは慎重に考えたいですね。どんなことを重視されますか？",
        "なるほど、施設についてお考えなんですね。情報を一緒に集めていきましょう。",
        "施設選びは大切な決断ですから、じっくり考えていきましょうね。",
    ],
    "daily": [
        "毎日の暮らしの中で、お困りのことはありますか？何でもお手伝いしますよ。",
        "日々の生活を大切にされているんですね。お買い物やお掃除など、お手伝いしましょうか？",
    ],
    "loneliness": [
        "お気持ち、よくわかります。私はいつでもここにいますから、寂しくなったらいつでも話しかけてくださいね。",
        "そうでしたか…。お一人で抱え込まないでくださいね。何でもお話ししてください。",
        "さみしい気持ちになることもありますよね。一緒に何か楽しいことを見つけましょう。",
    ],
    "work": [
        "そうでしたか。長年お仕事をされてきた経験は素晴らしいですね。",
        "なるほど。お仕事のお話を聞かせていただいて、とても参考になります。",
        "素晴らしいご経歴をお持ちなんですね。もっとお話を聞かせてください。",
    ],
    "hobby": [
        "それは素敵な趣味ですね！楽しみがあるのは本当に良いことだと思います。",
        "趣味を楽しまれているんですね。毎日の楽しみは大切ですからね。",
    ],
    "general": [
        "はい、なるほど。教えてくださってありがとうございます。",
        "そうでしたか。お話しいただきありがとうございます。何かお手伝いしましょうか？",
        "おっしゃる通りですね。何かご不明な点があればいつでもお聞きください。",
    ],
}

# ================================================================
# 核心：从Whisper segment提取老年人发言
# ================================================================

def extract_elderly_utterances(segments, video_type="interview"):
    """
    从Whisper转录中提取老年人的发言。
    - interview型：跳过采访者提问，只保留老年人回答
    - monologue型：全部作为老年人发言
    """
    utterances = []

    if video_type == "monologue":
        # 独白型：合并相邻段为较长发言
        buffer = []
        for seg in segments:
            text = seg["text"].strip()
            if not text or is_short_fragment(text):
                continue
            buffer.append(text)
            if len(buffer) >= 3:  # 每3段合并一次
                merged = "".join(buffer)
                if len(merged) >= 15:
                    utterances.append(merged)
                buffer = []
        # 剩余
        if buffer:
            merged = "".join(buffer)
            if len(merged) >= 15:
                utterances.append(merged)
    else:
        # 采访型：跳过提问，保留回答
        buffer = []
        for seg in segments:
            text = seg["text"].strip()
            if not text or is_short_fragment(text):
                continue

            if is_question(text):
                # 采访者提问 → 保存之前的buffer作为发言
                if buffer:
                    merged = "".join(buffer)
                    if len(merged) >= 10:
                        utterances.append(merged)
                    buffer = []
                # 跳过这个提问
            else:
                # 老年人回答
                buffer.append(text)
                if len(buffer) >= 3:
                    merged = "".join(buffer)
                    if len(merged) >= 15:
                        utterances.append(merged)
                    buffer = []

        # 最后剩余的
        if buffer:
            merged = "".join(buffer)
            if len(merged) >= 10:
                utterances.append(merged)

    return utterances


def build_conversation_from_elderly_speech(utterances, vid, info, start_idx):
    """
    从连续的老年人发言构建对话。
    每段发言 → human turn + gpt response
    2-3个发言组 → 一个多轮对话
    """
    if len(utterances) < 2:
        return []

    records = []
    # 用滑动窗口，每2-3个发言构建一个对话
    window_size = random.choice([2, 3])
    stride = 1

    for i in range(0, len(utterances) - window_size + 1, stride):
        window = utterances[i:i + window_size]
        if len(window) < 2:
            continue

        conversations = []

        # 添加问候（30%概率）
        if random.random() < 0.3:
            conversations.append({
                "from": "human",
                "value": random.choice([
                    "あのー、ちょっと話を聞いてほしいねん。",
                    "おはよう。今日もよろしく頼むわ。",
                    "こんにちは。ちょっと相談したいことがあってな…",
                    "すみません、少しお時間いいですか？",
                ])
            })
            conversations.append({
                "from": "gpt",
                "value": random.choice([
                    "はい、こんにちは！いつでもお話しくださいね。今日はどんなお話でしょうか？",
                    "はい、おはようございます。どうぞゆっくりお話しください。",
                    "こんにちは！お会いできて嬉しいです。どんなことでもお聞かせくださいね。",
                ])
            })

        # 核心对话：每段发言 → human + gpt
        for j, utt in enumerate(window):
            utt = clean_text(utt)
            if len(utt) < 8:
                continue

            topic = detect_topic(utt)

            # human turn: 老年人发言（加入自然语音特征）
            human_text = make_elderly_speech(utt)

            # gpt turn: AI回复
            if j < len(window) - 1:
                # 中间回复：承接话题 + 引出下一段
                gpt_text = random.choice(TOPIC_RESPONSES.get(topic, TOPIC_RESPONSES["general"]))
            else:
                # 最后回复：总结 + 关怀
                if topic == "pension":
                    gpt_text = "年金のことは本当に大切ですね。何かお手伝いできることがあれば、いつでもおっしゃってくださいね。"
                elif topic == "health":
                    gpt_text = "お体を大切になさってくださいね。何かありましたら、すぐにご連絡ください。"
                elif topic == "loneliness":
                    gpt_text = "いつでもお話し相手になりますから、寂しくなったら声をかけてくださいね。"
                elif topic == "family":
                    gpt_text = "ご家族のことを大切に思われていて、素晴らしいですね。またお話し聞かせてください。"
                else:
                    gpt_text = random.choice([
                        "なるほど、よくわかりました。また何かあればいつでもお話しくださいね。",
                        "お話しいただきありがとうございます。これからもよろしくお願いしますね。",
                        "そうでしたか。今日もお話しできて嬉しかったです。",
                    ])

            conversations.append({"from": "human", "value": human_text})
            conversations.append({"from": "gpt", "value": gpt_text})

        if len(conversations) < 4:  # 至少2轮（4条消息）
            continue

        # 验证交替
        conversations = fix_alternation(conversations)
        if len(conversations) < 4:
            continue

        total_chars = sum(len(c["value"]) for c in conversations)
        if total_chars < 60:
            continue

        records.append({
            "id": f"whisper_v81_{vid}_{start_idx + i:04d}",
            "conversations": conversations,
            "source": "real_elderly_whisper",
            "quality": "real_transcribed_v81",
            "language": "ja",
            "country_code": "JP",
            "scenario": f"interview: {info.get('title', 'unknown')}",
            "video_id": vid,
            "num_turns": len(conversations),
            "total_chars": total_chars,
        })

    return records


def clean_text(text):
    """文本清理"""
    text = re.sub(r'\[\s*(拍手|笑い|音楽|無音|不明|聞き取り困難)\s*\]', '', text)
    text = re.sub(r'〔[^〕]*〕', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\{[<>]\}', '', text)
    text = re.sub(r'\s+', '', text)
    text = re.sub(r'。。+', '。', text)
    text = re.sub(r'、、+', '、', text)
    text = re.sub(r'……+', '…', text)
    text = text.strip()
    if text and text[-1] not in '。！？…、':
        text += '。'
    return text


def make_elderly_speech(text):
    """使文本更像老年人自然语音"""
    # 偶尔添加填充词
    if random.random() < 0.22 and len(text) > 10:
        fillers = ["まあ、", "あのー、", "ええとね、", "そうやなあ、"]
        f = random.choice(fillers)
        if random.random() < 0.5:
            text = f + text
    # 偶尔添加关西方言
    if random.random() < 0.08:
        text = add_light_dialect(text)
    return text


def add_light_dialect(text):
    """轻度关西方言"""
    reps = [
        ("だよね", "やんな"), ("だよ", "やで"), ("すごい", "めっちゃ"),
        ("本当に", "ほんまに"), ("そうだ", "せや"), ("違う", "ちゃう"),
        ("ダメ", "あかん"), ("ありがとう", "おおきに"),
    ]
    for orig, dial in reps:
        if orig in text and random.random() < 0.3:
            return text.replace(orig, dial, 1)
    return text


def fix_alternation(conversations):
    """修复连续同角色：如果连续2个同角色，合并"""
    if not conversations:
        return []
    fixed = []
    for c in conversations:
        if fixed and fixed[-1]["from"] == c["from"]:
            # 同角色合并
            fixed[-1]["value"] = fixed[-1]["value"].rstrip("。！？…") + "。" + c["value"]
        else:
            fixed.append(c.copy())

    # 验证交替
    if len(fixed) >= 2:
        for i in range(1, len(fixed)):
            if fixed[i]["from"] == fixed[i-1]["from"]:
                # 仍有连续同角色，用通用桥接
                bridge_role = "gpt" if fixed[i]["from"] == "human" else "human"
                bridge_text = "はい、なるほど。" if bridge_role == "gpt" else "そうですか…"
                fixed.insert(i, {"from": bridge_role, "value": bridge_text})
                break

    return fixed


# ================================================================
# Part 2: 修复现有V8数据中的AI回复质量问题
# ================================================================

def fix_v8_ai_responses(record):
    """改进V8数据中AI回复的上下文匹配度"""
    convs = record.get("conversations", [])
    if not convs:
        return record

    fixed = []
    for i, c in enumerate(convs):
        if c["from"] == "gpt" and i > 0:
            prev_human = convs[i-1].get("value", "") if convs[i-1]["from"] == "human" else ""
            if prev_human:
                topic = detect_topic(prev_human)
                # 如果当前AI回复太通用且人类发言有明确话题，替换
                is_generic = any(c["value"].strip().startswith(g) for g in [
                    "はい、かしこまりました",
                    "なるほど、よくわかりました",
                    "そうでしたか。お話しいただき",
                    "おっしゃる通りですね",
                ])
                # 检查是否回复与话题完全不匹配
                topic_keywords = {
                    "pension": ["年金", "生活費", "万円", "お金"],
                    "health": ["病", "痛", "薬", "健康", "体"],
                    "family": ["家族", "子供", "孫", "主人", "妻", "夫"],
                    "facility": ["施設", "ホーム"],
                    "loneliness": ["寂し", "孤独", "一人"],
                }
                expected_kw = topic_keywords.get(topic, [])
                has_topic_match = any(kw in c["value"] for kw in expected_kw)

                if is_generic and not has_topic_match and len(prev_human) > 8:
                    # 替换为话题匹配的回复
                    new_response = random.choice(TOPIC_RESPONSES.get(topic, TOPIC_RESPONSES["general"]))
                    c = {"from": "gpt", "value": new_response}

        fixed.append(c)

    record["conversations"] = fix_alternation(fixed)
    record["num_turns"] = len(record["conversations"])
    record["total_chars"] = sum(len(c["value"]) for c in record["conversations"])
    return record


def quality_filter(record):
    """质量过滤"""
    convs = record.get("conversations", [])
    if len(convs) < 2:
        return False
    texts = [c["value"].strip() for c in convs]
    if any(len(t) < 3 for t in texts):
        return False
    if sum(len(t) for t in texts) < 40:
        return False
    roles = set(c["from"] for c in convs)
    if len(roles) < 2:
        return False
    # 过滤纯相槌
    for c in convs:
        if c["from"] == "human" and re.match(r'^[うんはいええああそうへえふーん]+[。、！？…]*$', c["value"]):
            return False
    # 过滤乱码（非日语字符太多）
    for c in convs:
        non_jp = sum(1 for ch in c["value"] if not (
            '぀' <= ch <= 'ゟ' or '゠' <= ch <= 'ヿ' or '一' <= ch <= '鿿' or
            ch in '、。！？…〜ー（）「」『』,. 0123456789'
        ))
        if non_jp > len(c["value"]) * 0.3:
            return False
    return True


# ================================================================
# Main
# ================================================================

def main():
    print("=" * 70)
    print("V8.1 数据质量修复")
    print("=" * 70)

    # ----------------------------------------------------------
    # Step 1: 重新提取Whisper数据（修复版）
    # ----------------------------------------------------------
    print("\n[Step 1] 重新提取Whisper数据（丢弃采访者提问）...")

    all_whisper = []
    for vid, info in VIDEO_INFO.items():
        wp = REAL_DIR / f"{vid}_whisper.json"
        if not wp.exists():
            continue

        with open(wp, encoding="utf-8") as f:
            data = json.load(f)

        segments = data.get("segments", [])
        vtype = info.get("type", "interview")

        print(f"  {vid}: {len(segments)} seg, type={vtype}")

        utterances = extract_elderly_utterances(segments, vtype)
        print(f"    → {len(utterances)} elderly utterances")

        records = build_conversation_from_elderly_speech(utterances, vid, info, 0)
        print(f"    → {len(records)} conversations")
        all_whisper.extend(records)

    before_whisper = len(all_whisper)
    all_whisper = [r for r in all_whisper if quality_filter(r)]
    print(f"\n  Whisper总计: {len(all_whisper)} ({before_whisper - len(all_whisper)} filtered)")

    if all_whisper:
        turns_avg = sum(r["num_turns"] for r in all_whisper) / len(all_whisper)
        chars_avg = sum(r["total_chars"] for r in all_whisper) / len(all_whisper)
        print(f"  平均轮次: {turns_avg:.1f}, 平均字符: {chars_avg:.0f}")

    # ----------------------------------------------------------
    # Step 2: 加载现有V8非Whisper数据 + 修复AI回复
    # ----------------------------------------------------------
    print("\n[Step 2] 加载并修复现有数据...")

    existing = []
    for split_name in ["train", "val", "test"]:
        fp = TRAIN_DIR / f"{split_name}.jsonl"
        if fp.exists():
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line.strip())
                        if "whisper" not in r.get("source", ""):
                            existing.append(r)
                    except:
                        pass

    print(f"  现有非Whisper: {len(existing)}条")

    # 修复AI回复质量
    existing = [fix_v8_ai_responses(r) for r in existing]
    existing = [r for r in existing if quality_filter(r)]
    print(f"  修复后: {len(existing)}条")

    # ----------------------------------------------------------
    # Step 3: 合并 + 去重 + 分层分割
    # ----------------------------------------------------------
    print("\n[Step 3] 合并 + 去重 + 分割...")

    all_data = all_whisper + existing
    print(f"  合并: {len(all_data)}条")

    seen = set()
    unique = []
    for r in all_data:
        h = "|".join(c["value"][:40] for c in r.get("conversations", [])[:4])
        if h not in seen:
            seen.add(h)
            unique.append(r)
    print(f"  去重: {len(unique)}条")

    src_groups = defaultdict(list)
    for r in unique:
        src_groups[r.get("source", "?")].append(r)

    train, val, test = [], [], []
    for src, recs in src_groups.items():
        random.shuffle(recs)
        n = len(recs)
        train.extend(recs[:int(n*0.8)])
        val.extend(recs[int(n*0.8):int(n*0.9)])
        test.extend(recs[int(n*0.9):])

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)
    print(f"  train={len(train)} val={len(val)} test={len(test)}")

    # ----------------------------------------------------------
    # Step 4: 保存
    # ----------------------------------------------------------
    print("\n[Step 4] 保存...")
    for name, data in [("train", train), ("val", val), ("test", test)]:
        fp = TRAIN_DIR / f"{name}.jsonl"
        with open(fp, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  {fp}: {len(data)}")

    # ----------------------------------------------------------
    # 报告
    # ----------------------------------------------------------
    all_final = train + val + test
    src_counts = defaultdict(int)
    for r in all_final:
        src_counts[r.get("source", "?")] += 1

    final_turns = [r.get("num_turns", len(r.get("conversations", []))) for r in all_final]
    final_chars = [r.get("total_chars", sum(len(c["value"]) for c in r.get("conversations", []))) for r in all_final]

    real_count = sum(1 for r in all_final if "real" in r.get("source", "").lower())
    elderly_count = sum(1 for r in all_final if "elderly" in r.get("source", "") or "whisper" in r.get("source", ""))

    print(f"\n{'=' * 70}")
    print(f"V8.1 最终报告")
    print(f"{'=' * 70}")
    print(f"  总数据:   {len(all_final)}条")
    print(f"  真实数据: {real_count/len(all_final)*100:.1f}%")
    print(f"  老年数据: {elderly_count/len(all_final)*100:.1f}%")
    print(f"  平均轮次: {sum(final_turns)/len(final_turns):.1f}")
    print(f"  平均字符: {sum(final_chars)/len(final_chars):.0f}")
    print(f"  2轮对话:  {sum(1 for t in final_turns if t <= 2)}条")
    print(f"  4轮以上:  {sum(1 for t in final_turns if t >= 4)}条")

    turn_dist = Counter(final_turns)
    print(f"  轮次分布: {dict(sorted(turn_dist.items()))}")

    print(f"\n来源分布:")
    for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
        print(f"  {src:30s}: {cnt:5d} ({cnt/len(all_final)*100:5.1f}%)")

    # 样本
    print(f"\n--- 样本对话 ---")
    samples = random.sample(all_final, min(5, len(all_final)))
    for i, r in enumerate(samples):
        print(f"\n[样本{i+1}] {r.get('source','?')} | {len(r['conversations'])}轮 | {sum(len(c['value']) for c in r['conversations'])}字")
        for c in r["conversations"]:
            role = "👴" if c["from"] == "human" else "🤖"
            print(f"  {role} {c['value'][:200]}")

    # 元数据
    meta = {
        "dataset": "Japanese_Elderly_Care_AI_Companion_v8.1",
        "version": "8.1.0",
        "total": len(all_final),
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
        "sources": dict(src_counts),
        "real_data_pct": round(real_count/len(all_final)*100, 1),
        "real_elderly_pct": round(elderly_count/len(all_final)*100, 1),
        "avg_turns": round(sum(final_turns)/len(final_turns), 1),
        "avg_chars": round(sum(final_chars)/len(final_chars), 0),
        "improvements_v81": [
            "丢弃采访者提问，只保留老年人真实发言",
            "AI回复与话题匹配（8个话题检测）",
            "独白型视频特殊处理（合并3段为一次发言）",
            "修复连续同角色bug",
            "增强质量过滤",
        ],
    }
    with open(TRAIN_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\nV8.1 保存完成")


if __name__ == "__main__":
    main()
