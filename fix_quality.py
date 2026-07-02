#!/usr/bin/env python3
"""修复4个已确认的语病问题"""
import json, re, sys, random
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
from pathlib import Path
from collections import Counter

random.seed(42)
TRAIN_DIR = Path("training_data")

# ─── 修复函数 ───

def clean_ai_response(text):
    """修复AI回复的拼接错误"""
    # 1. 修复重复标点: 。。→ 。  、、→ 、
    text = re.sub(r'。。+', '。', text)
    text = re.sub(r'、、+', '、', text)

    # 2. 修复乱序拼接: "ですよですよ" → "ですよ"  ;  "ですからねよ" → "ですからね"
    text = re.sub(r'(ですよ)+', 'ですよ', text)
    text = re.sub(r'(ますよ)+', 'ますよ', text)
    text = re.sub(r'(ですからね)+', 'ですからね', text)
    text = re.sub(r'(くださいね)+', 'くださいね', text)

    # 3. 修复 "、。" → "。"
    text = text.replace('、。', '。').replace('。、', '。')

    # 4. 修复开头乱码: "ああ、はい、" → "はい、"  "ふむ、" → ""
    text = re.sub(r'^(ああ、|ふむ、|ええっと、)+(はい、|そうですか、)?', '', text)
    text = re.sub(r'^そうですね、そうですか、', 'そうですね、', text)

    # 5. 修复 "。なので、" → "。"（不当接续）
    text = text.replace('。なので、', '。').replace('。ですから、', '。')

    # 6. 修复 ".  " 中的多余空格
    text = re.sub(r'\s+', '', text)

    # 7. 如果修复后太短，返回空标记
    text = text.strip()
    if not text or len(text) < 6:
        return None

    # 确保以句号结尾
    if text[-1] not in '。！？…、': text += '。'
    return text


def clean_human_csv(text):
    """修复CSV人类发言中的采访者提问残留"""
    # 明确是采访者的话，删除
    q_patterns = [
        r'^(そうなんですか|そうですか|なるほど)[。、]?',
        r'[。、](そうなんですか|そうですかね)[。、]?',
        r'(ですかね|ですか|ますか)[。、]?\s*$',
        r'^(はい、|ええ、){2,}',  # 连续附和
    ]
    for p in q_patterns:
        text = re.sub(p, '', text)

    # 如果整句基本都是采访者提问，标记删除
    interviewer_indicators = ['聞いていいですか', '教えていただけますか', '何歳ですか',
                              'いくらですか', 'お名前は', 'ご年齢', '教えてください',
                              'どうですか', 'いかがですか', 'どういう', 'どんな']
    interviewer_score = sum(1 for kw in interviewer_indicators if kw in text)
    if interviewer_score >= 2 and len(text) < 40:
        return None

    text = text.strip()
    if not text or len(text) < 5: return None
    if text[-1] not in '。！？…、': text += '。'
    return text


def remove_duplicate_ai(conversations):
    """同一对话内去重AI回复"""
    seen_gpt = set()
    fixed = []
    for c in conversations:
        if c['from'] == 'gpt':
            text = c['value']
            # 如果完全相同，替换为通用过渡回复
            if text in seen_gpt:
                alt = random.choice([
                    "なるほど、もう少し詳しくお聞かせいただけますか？",
                    "そうでしたか。お話を続けてください。",
                    "はい、よくわかります。他にも何かお気持ちはありますか？",
                ])
                c = {'from': 'gpt', 'value': alt}
            seen_gpt.add(text)
        fixed.append(c)
    return fixed


# ─── Main ───

def main():
    print("=" * 70)
    print("数据集质量修复")
    print("=" * 70)

    all_records = []
    for split_name in ["train", "val", "test"]:
        fp = TRAIN_DIR / f"{split_name}.jsonl"
        if fp.exists():
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try: all_records.append(json.loads(line.strip()))
                    except: pass
    print(f"\n加载: {len(all_records)} 条")

    # 统计
    fixes = Counter()

    for r in all_records:
        convs = r.get("conversations", [])
        src = r.get("source", "")

        # 修复1: AI拼接错误
        for c in convs:
            if c["from"] == "gpt":
                orig = c["value"]
                cleaned = clean_ai_response(orig)
                if cleaned and cleaned != orig:
                    c["value"] = cleaned
                    fixes["AI拼接修复"] += 1
                elif cleaned is None:
                    c["value"] = "はい、お話しいただきありがとうございます。"
                    fixes["AI拼接→替换"] += 1

        # 修复2: CSV人类发言采访者提问残留
        if "csv" in src:
            for c in convs:
                if c["from"] == "human":
                    orig = c["value"]
                    cleaned = clean_human_csv(orig)
                    if cleaned and cleaned != orig:
                        c["value"] = cleaned
                        fixes["CSV提问残留修复"] += 1
                    elif cleaned is None:
                        c["value"] = "もう少しお話を続けさせてください。"
                        fixes["CSV提问→替换"] += 1

        # 修复3: 同对话AI回复去重
        orig_gpt = [c["value"] for c in convs if c["from"] == "gpt"]
        convs = remove_duplicate_ai(convs)
        new_gpt = [c["value"] for c in convs if c["from"] == "gpt"]
        if orig_gpt != new_gpt:
            fixes["同对话AI去重"] += 1

        r["conversations"] = convs
        r["num_turns"] = len(convs)
        r["total_chars"] = sum(len(c["value"]) for c in convs)

    # 过滤掉修复后质量太差的记录
    filtered = []
    removed = 0
    for r in all_records:
        convs = r["conversations"]
        texts = [c["value"].strip() for c in convs]
        # 至少4条消息，每条≥3字，总计≥80字
        if len(convs) < 4: removed += 1; continue
        if any(len(t) < 3 for t in texts): removed += 1; continue
        if sum(len(t) for t in texts) < 80: removed += 1; continue
        filtered.append(r)

    print(f"过滤移除: {removed} 条")
    print(f"\n修复统计:")
    for fix, count in fixes.most_common():
        print(f"  {fix}: {count} 次")

    # 分割保存
    from collections import defaultdict
    src_groups = defaultdict(list)
    for r in filtered:
        src_groups[r.get("source", "?")].append(r)

    train, val, test = [], [], []
    for src, recs in src_groups.items():
        random.shuffle(recs)
        n = len(recs)
        train.extend(recs[:int(n*0.8)])
        val.extend(recs[int(n*0.8):int(n*0.9)])
        test.extend(recs[int(n*0.9):])

    random.shuffle(train); random.shuffle(val); random.shuffle(test)

    for name, data in [("train", train), ("val", val), ("test", test)]:
        fp = TRAIN_DIR / f"{name}.jsonl"
        with open(fp, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 报告
    all_final = train + val + test
    turns = [len(r["conversations"]) for r in all_final]
    chars = [sum(len(c["value"]) for c in r["conversations"]) for r in all_final]
    gpt_unique = len(set(c["value"] for r in all_final for c in r["conversations"] if c["from"]=="gpt"))
    total_gpt = sum(1 for r in all_final for c in r["conversations"] if c["from"]=="gpt")

    print(f"\n修复后数据集:")
    print(f"  总条数: {len(all_final)}")
    print(f"  训练/验证/测试: {len(train)}/{len(val)}/{len(test)}")
    print(f"  平均轮次: {sum(turns)/len(turns):.1f}")
    print(f"  平均字符: {sum(chars)/len(chars):.0f}")
    print(f"  AI去重回复: {gpt_unique}")
    print(f"  AI重复率: {(1-gpt_unique/total_gpt)*100:.1f}%")

    # 验证修复效果
    full_scan(all_final)

    print(f"\n✅ 修复完成!")


def full_scan(data):
    """快速验证修复效果"""
    concat = sum(1 for r in data for c in r["conversations"]
                 if c["from"]=="gpt" and ('。。' in c["value"] or '、。' in c["value"]))
    dup = 0
    for r in data:
        gpt_msgs = [c["value"] for c in r["conversations"] if c["from"]=="gpt"]
        if len(gpt_msgs) != len(set(gpt_msgs)): dup += 1

    print(f"\n修复后残留:")
    print(f"  拼接错误残留: {concat} 条 ({concat/len(data)*100:.2f}%)")
    print(f"  同对话AI重复残留: {dup} 条 ({dup/len(data)*100:.2f}%)")


if __name__ == "__main__":
    main()
