#!/usr/bin/env python3
"""
Quality-fix pass over the v6 dataset, then rebuild.
Fixes:
1. Clean transcription markers from real_corpus
2. Fix V5 template artifacts
3. Context-aware AI responses for real elderly utterances
4. Remove low-quality records
"""
import json, re, random
from pathlib import Path
from collections import defaultdict

random.seed(42)
TRAIN_DIR = Path("training_data")

# ============================================================
# Fix 1: Clean transcription markers from real_corpus
# ============================================================

def clean_corpus_text(text):
    """Remove transcription markers from real corpus text."""
    # Remove overlap markers: {<}, {>}, <...>
    text = re.sub(r'\{[<>]\}', '', text)
    # Remove <word> angle-bracketed annotations
    text = re.sub(r'<[^>]+>', '', text)
    # Remove ### markers
    text = re.sub(r'###', '', text)
    # Clean up whitespace
    text = re.sub(r'\s+', '', text)
    # Remove empty brackets
    text = re.sub(r'\[\]', '', text)
    text = text.strip()
    return text if len(text) >= 3 else ""


# ============================================================
# Fix 2: Better AI response generation
# ============================================================

# Topic → appropriate verb mapping
TOPIC_VERBS = {
    "お湯": ["お持ちし", "ご用意し"],
    "薬": ["確認し", "お持ちし"],
    "食事": ["ご用意し", "準備し"],
    "掃除": ["お手伝いし", "確認し"],
    "洗濯": ["お手伝いし", "確認し"],
    "テレビ": ["確認し", "調べ"],
    "リモコン": ["確認し", "調べ"],
    "電話": ["確認し", "お知らせし"],
    "病院": ["手配し", "予約し", "確認し"],
    "買い物": ["準備し", "確認し"],
    "痛い": ["確認し", "お手伝いし"],
    "寒い": ["確認し", "ご用意し"],
    "暑い": ["確認し", "ご用意し"],
}

AI_SHORT = [
    "はい、わかりました。",
    "そうですね。",
    "ええ、お聞きしています。",
    "なるほど。",
    "そうでしたか。",
    "承知しました。",
    "はい、かしこまりました。",
    "はいはい、大丈夫ですよ。",
]

AI_HELPFUL = [
    "わかりました。{v}ますね。",
    "大丈夫ですよ。{v}ましょう。",
    "すぐに{v}ます。少々お待ちください。",
    "いいですね。一緒に{v}ましょうか。",
    "承知しました。{v}しておきます。",
    "かしこまりました。{v}ます。",
]

AI_EMPATHETIC = [
    "それは大変でしたね。お気持ち、よくわかります。",
    "そうだったんですね。ゆっくりお話しください。",
    "なるほど…。何かお手伝いできることはありますか。",
    "ご心配なさらないでください。いつでもお手伝いしますよ。",
    "よくお話しくださいました。ありがとうございます。",
    "そうですか…。無理なさらないでくださいね。",
]


def pick_verb_for_text(text):
    """Pick an appropriate verb based on text content."""
    for topic, verbs in TOPIC_VERBS.items():
        if topic in text:
            return random.choice(verbs)
    return random.choice(["確認し", "ご用意し", "お持ちし", "調べ", "準備し", "見てき", "お手伝いし"])


def generate_ai_response_v2(human_text):
    """Generate contextually appropriate AI response."""
    text = human_text.strip()
    length = len(text)

    # Very short → aizuchi
    if length < 15:
        return random.choice(AI_SHORT)

    # Short → sometimes aizuchi
    if length < 25 and random.random() < 0.4:
        return random.choice(AI_SHORT)

    # Questions
    if "？" in text or "?" in text or text.endswith("か") or text.endswith("かな"):
        verb = pick_verb_for_text(text)
        return random.choice(AI_HELPFUL).format(v=verb)

    # Complaints / expressions of difficulty
    complaint_kw = ["痛い", "しんどい", "疲れた", "困った", "寂しい", "さみしい", "怖い", "嫌", "だめ", "できない", "できへん", "わからん", "あかん"]
    if any(kw in text for kw in complaint_kw):
        if random.random() < 0.6:
            return random.choice(AI_EMPATHETIC)
        else:
            verb = pick_verb_for_text(text)
            return random.choice(AI_HELPFUL).format(v=verb)

    # Requests
    request_kw = ["手伝って", "助けて", "お願い", "ください", "頼む", "見て", "やって", "してくれ"]
    if any(kw in text for kw in request_kw):
        verb = pick_verb_for_text(text)
        return random.choice(AI_HELPFUL).format(v=verb)

    # Default: balanced aizuchi/helpful
    if random.random() < 0.3:
        return random.choice(AI_SHORT)
    else:
        verb = pick_verb_for_text(text)
        return random.choice(AI_HELPFUL).format(v=verb)


# ============================================================
# Fix 3: Clean V5 synthetic templates
# ============================================================

def clean_v5_text(text):
    """Fix common V5 template artifacts."""
    # Fix double punctuation
    text = re.sub(r'[。！？]{2,}', '。', text)
    text = re.sub(r'[、,]{2,}', '、', text)
    # Fix ？。 pattern
    text = text.replace('？。', '？')
    text = text.replace('！。', '！')
    # Fix dialect injection creating double どす etc
    text = re.sub(r'(どす|さかい|ほんま|やで|のう)\s*(どす|さかい|ほんま|やで|のう)', r'\1', text)
    # Remove leading …
    text = re.sub(r'^…+', '', text)
    # Normalize
    text = text.strip()
    # Ensure ends with punctuation
    if text and not text[-1] in '。！？…、':
        text += '。'
    return text


# ============================================================
# Full quality pass
# ============================================================

def quality_fix_record(record):
    """Apply all quality fixes to a single record."""
    convs = record.get("conversations", [])

    fixed_convs = []
    for c in convs:
        text = c.get("value", "")
        role = c.get("from", "human")

        # Clean transcription markers from real corpus
        if record.get("source") == "real_corpus_slice":
            text = clean_corpus_text(text)
            if not text:
                continue

        # Fix V5 artifacts
        if record.get("source") in ["V5_synthetic", "V5_realistic"]:
            if role == "human":
                text = clean_v5_text(text)
            elif role == "gpt":
                # Regenerate bad AI responses
                if text.endswith("し。") or text.endswith("き。") or "ご用意し。" in text or "見てき。" in text:
                    # Find the preceding human text to generate better response
                    prev_human = ""
                    for prev_c in reversed(fixed_convs):
                        if prev_c.get("from") == "human":
                            prev_human = prev_c.get("value", "")
                            break
                    if prev_human:
                        text = generate_ai_response_v2(prev_human)

        if text and len(text) >= 2:
            fixed_convs.append({"from": role, "value": text})

    # Ensure proper alternation
    if fixed_convs:
        # Fix consecutive same-role turns
        merged = []
        for c in fixed_convs:
            if merged and merged[-1]["from"] == c["from"]:
                # Merge consecutive same-role turns
                merged[-1]["value"] += " " + c["value"]
            else:
                merged.append(c)

        if len(merged) >= 2:
            record["conversations"] = merged
            record["num_turns"] = len(merged)
            record["total_chars"] = sum(len(c["value"]) for c in merged)
            return record

    return None


def main():
    print("=" * 60)
    print("QUALITY FIX + REBUILD")
    print("=" * 60)

    # Load all existing data from previous run
    all_records = []
    for split_name in ["train", "val", "test"]:
        fp = TRAIN_DIR / f"{split_name}.jsonl"
        if fp.exists():
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line.strip())
                        r["_split"] = split_name
                        all_records.append(r)
                    except:
                        pass

    print(f"\nLoaded {len(all_records)} total records")

    # Apply fixes
    fixed = []
    for r in all_records:
        result = quality_fix_record(r)
        if result:
            fixed.append(result)

    print(f"After quality fix: {len(fixed)} records ({len(all_records) - len(fixed)} removed)")

    # Remove low-quality records
    quality_records = []
    for r in fixed:
        convs = r.get("conversations", [])
        texts = [c["value"] for c in convs]

        # Filter: must not have only 1-char turns
        if any(len(t) < 3 for t in texts):
            continue
        # Filter: must have both human and gpt
        roles = set(c["from"] for c in convs)
        if len(roles) < 2:
            continue
        # Filter: too short total
        total_len = sum(len(t) for t in texts)
        if total_len < 20:
            continue

        quality_records.append(r)

    print(f"After quality filter: {len(quality_records)}")

    # Dedup
    seen = set()
    unique = []
    for r in quality_records:
        h = "|".join(c["value"][:40] for c in r.get("conversations", [])[:2])
        if h not in seen:
            seen.add(h)
            unique.append(r)

    print(f"After final dedup: {len(unique)}")

    # Split by source
    src_groups = defaultdict(list)
    for r in unique:
        src_groups[r.get("source", "?")].append(r)

    train, val, test = [], [], []
    for src, recs in src_groups.items():
        random.shuffle(recs)
        n = len(recs)
        t_end = int(n * 0.8)
        v_end = int(n * 0.9)
        train.extend(recs[:t_end])
        val.extend(recs[t_end:v_end])
        test.extend(recs[v_end:])

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    print(f"\nSplit: train={len(train)} val={len(val)} test={len(test)}")

    # Save
    for name, data in [("train", train), ("val", val), ("test", test)]:
        fpath = TRAIN_DIR / f"{name}.jsonl"
        with open(fpath, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  {fpath}: {len(data)}")

    # Metadata
    all_data = train + val + test
    src_counts = defaultdict(int)
    for r in all_data:
        src_counts[r.get("source", "?")] += 1

    real_count = sum(1 for r in all_data if "real" in r.get("source", "").lower())
    elderly_real = sum(1 for r in all_data if "elderly_youtube" in r.get("source", ""))

    meta = {
        "dataset": "Japanese_Elderly_Care_AI_Companion_v6_fixed",
        "version": "6.1.0",
        "total": len(all_data),
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
        "sources": dict(src_counts),
        "real_data_pct": round(real_count / len(all_data) * 100, 1),
        "real_elderly_pct": round(elderly_real / len(all_data) * 100, 1),
        "quality_fixes": [
            "Context-aware AI responses (topic→verb matching)",
            "Transcription marker cleanup (real_corpus)",
            "V5 template artifact fixes (double punctuation, incomplete sentences)",
            "Consecutive same-role merging",
            "Quality filter: min turn length, role diversity, total length",
        ],
    }

    with open(TRAIN_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Report
    print(f"\n{'=' * 60}")
    print(f"DATASET v6.1 COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Total:        {len(all_data)}")
    print(f"  Train/Val/Test: {len(train)}/{len(val)}/{len(test)}")
    print(f"  Real data:    {meta['real_data_pct']}%")
    print(f"  Real elderly: {meta['real_elderly_pct']}%")
    print(f"\nSource breakdown:")
    for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
        pct = cnt / len(all_data) * 100
        bar = "█" * int(pct)
        print(f"  {src:30s}: {cnt:5d} ({pct:5.1f}%) {bar}")

    # Show quality samples
    print(f"\n--- Quality Check: Random Samples ---")
    samples = random.sample(all_data, min(5, len(all_data)))
    for i, r in enumerate(samples):
        convs = r.get("conversations", [])
        print(f"\n[Sample {i+1}] {r.get('source','?')} | {len(convs)} turns")
        for c in convs[:6]:
            print(f"  [{c['from']}] {c['value'][:140]}")


if __name__ == "__main__":
    main()
