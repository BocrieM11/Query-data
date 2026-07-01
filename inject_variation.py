#!/usr/bin/env python3
"""
给AI回复注入随机变化：降低重复率
- 添加敬语变化 (です→でございます, etc.)
- 句子拼接变化
- 随机语气词
"""
import json, re, random
from pathlib import Path
from collections import defaultdict

random.seed(42)
TRAIN_DIR = Path("training_data")

# 变化策略
PREFIXES = [
    "", "", "", "", "",  # 60%不加前缀
    "はい、", "ええ、", "ああ、", "そうですね、",
    "なるほど、", "そうですか、",
]
SUFFIXES = [
    "", "", "", "", "",  # 60%不加后缀
    "いつでもお声がけくださいね。", "ゆっくりで大丈夫ですよ。",
    "ご無理なさらないでくださいね。", "お役に立てて嬉しいです。",
]
BRIDGES = [  # 两个短句之间的连接
    "", "", "",
    "。それと、", "。あと、", "。そういえば、",
]
VARIATIONS = {
    "ます": ["ます", "ます", "ます", "ますね", "ますよ", "ますからね"],
    "ですね": ["ですね", "ですね", "ですよね", "ですなあ", "でございますね"],
    "でしょう": ["でしょう", "でしょう", "でしょうか", "でしょうね", "でしょうなあ"],
    "ください": ["ください", "ください", "くださいね", "くださいな", "いただけますか"],
    "ありがとう": ["ありがとう", "ありがたいです", "感謝いたします", "嬉しいです"],
    "大丈夫": ["大丈夫", "大丈夫", "ご安心ください", "心配いりませんよ"],
}

def vary_sentence(text):
    """给句子添加随机变化"""
    # 30%概率加前缀
    if random.random() < 0.3:
        p = random.choice(PREFIXES)
        if p and not text.startswith(p[:3]):
            text = p + text

    # 20%概率加后缀
    if random.random() < 0.2:
        s = random.choice(SUFFIXES)
        if s and s not in text:
            text = text.rstrip("。！？…") + "。" + s

    # 词汇变化
    for word, variants in VARIATIONS.items():
        if word in text and random.random() < 0.25:
            v = random.choice(variants)
            if v != word:
                text = text.replace(word, v, 1)

    return text


def split_and_vary(text):
    """将长回复拆分为2-3句并各自变化"""
    sentences = re.split(r'(?<=[。！？…])', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= 1:
        return vary_sentence(text)

    # 随机重组
    if len(sentences) >= 3 and random.random() < 0.3:
        # 加入桥接
        bridge = random.choice(BRIDGES)
        idx = len(sentences) // 2
        sentences.insert(idx, bridge)

    # 每句独立变化
    varied = [vary_sentence(s) if random.random() < 0.5 else s for s in sentences]
    return "".join(varied)


def main():
    print("注入AI回复变化...")

    all_records = []
    for split_name in ["train", "val", "test"]:
        fp = TRAIN_DIR / f"{split_name}.jsonl"
        if fp.exists():
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try:
                        all_records.append(json.loads(line.strip()))
                    except:
                        pass

    print(f"Loaded: {len(all_records)}")

    # 收集所有gpt回复
    gpt_texts = set()
    for r in all_records:
        for c in r.get("conversations", []):
            if c["from"] == "gpt":
                gpt_texts.add(c["value"])

    print(f"唯一GPT回复(变化前): {len(gpt_texts)}")

    # 注入变化
    varied_count = 0
    for r in all_records:
        for c in r.get("conversations", []):
            if c["from"] == "gpt":
                orig = c["value"]
                # 30%概率变化
                if random.random() < 0.3:
                    c["value"] = vary_sentence(orig)
                    if c["value"] != orig:
                        varied_count += 1
                elif random.random() < 0.2:
                    c["value"] = split_and_vary(orig)
                    if c["value"] != orig:
                        varied_count += 1

        r["total_chars"] = sum(len(c["value"]) for c in r.get("conversations", []))

    print(f"变化注入: {varied_count}条")

    # 重新统计
    gpt_texts2 = set()
    for r in all_records:
        for c in r.get("conversations", []):
            if c["from"] == "gpt":
                gpt_texts2.add(c["value"])

    total_gpt = sum(1 for r in all_records for c in r.get("conversations", []) if c["from"] == "gpt")
    print(f"唯一GPT回复(变化后): {len(gpt_texts2)}")
    print(f"重复率: {(1-len(gpt_texts2)/total_gpt)*100:.1f}%")

    # 分割并保存
    src_groups = defaultdict(list)
    for r in all_records:
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

    for name, data in [("train", train), ("val", val), ("test", test)]:
        fp = TRAIN_DIR / f"{name}.jsonl"
        with open(fp, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 最终统计
    all_final = train + val + test
    turns = [r.get("num_turns", len(r.get("conversations", []))) for r in all_final]
    chars = [r.get("total_chars", sum(len(c["value"]) for c in r.get("conversations", []))) for r in all_final]

    print(f"\nV9.1 Final:")
    print(f"  Total: {len(all_final)}")
    print(f"  Train/Val/Test: {len(train)}/{len(val)}/{len(test)}")
    print(f"  Avg turns: {sum(turns)/len(turns):.1f}")
    print(f"  Avg chars: {sum(chars)/len(chars):.0f}")
    print(f"  AI unique: {len(gpt_texts2)}")
    print(f"  AI repeat: {(1-len(gpt_texts2)/total_gpt)*100:.1f}%")

    print("Done!")


if __name__ == "__main__":
    main()
