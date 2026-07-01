#!/usr/bin/env python3
"""
Final quality improvement pass:
1. Better AI responses for real elderly data (safe, universal responses)
2. Fix V5 template artifacts more aggressively
3. Filter bad auto-caption utterances
"""
import json, re, random
from pathlib import Path
from collections import defaultdict

random.seed(42)
TRAIN_DIR = Path("training_data")

# ============================================================
# Universal safe AI responses for real elderly data
# (Since VTT auto-captions are noisy, use safe universal responses)
# ============================================================

SAFE_AI_RESPONSES = [
    "はい、かしこまりました。",
    "おっしゃる通りですね。",
    "なるほど、よくわかりました。",
    "はい、承知しました。",
    "そうでしたか。教えてくださってありがとうございます。",
    "わかりました。何かお手伝いしましょうか。",
    "はい、いつでもお声がけくださいね。",
    "そうですね。私もそう思います。",
    "ありがとうございます。良いお話を聞かせていただきました。",
    "はい、ご安心ください。",
    "大丈夫ですよ。ゆっくりで結構です。",
    "お気持ち、よくわかります。",
]

# ============================================================
# Fix V5 human templates
# ============================================================

def fix_v5_human_text(text):
    """Aggressive fix of V5 template artifacts."""
    # Remove leading punctuation
    text = re.sub(r'^[、,。！？…\s]+', '', text)

    # Fix double dialect words
    text = re.sub(r'(どす|さかい|ほんま|やで|のう|おおきに|めっちゃ|あかん|ちゃう|せや)\s*(どす|さかい|ほんま|やで|のう|おおきに|めっちゃ|あかん|ちゃう|せや)', r'\1', text)

    # Fix …X…X pattern (double dialect injection)
    text = re.sub(r'…(どす|さかい|ほんま)…\1', r'…\1', text)

    # Fix isolated particles
    text = re.sub(r'^[はがをのにでへとからより]\s', '', text)
    text = re.sub(r'、[はがをのにでへとからより]$', '', text)

    # Remove empty dialect injection markers
    text = re.sub(r'……+', '…', text)
    text = re.sub(r'。。+', '。', text)
    text = re.sub(r'、、+', '、', text)
    text = re.sub(r'？！', '？', text)
    text = re.sub(r'！。', '！', text)
    text = re.sub(r'？。', '？', text)

    # Ensure ends with sentence-ending punctuation
    text = text.strip()
    if text and text[-1] not in '。！？…':
        text += '。'

    # Remove very short or broken utterances
    if len(text) < 5:
        return None
    # Remove utterances that are just filler
    if re.match(r'^[あのー、…。\s]+$', text):
        return None

    return text


def fix_v5_ai_text(text, prev_human_text=""):
    """Fix V5 AI response — fix template conjugation bugs and match context."""

    # --- Fix known template bugs ---
    # "確認しので" → "確認しますので"
    text = re.sub(r'(確認|用意|持ち|調べ|準備|手配|見て|知らせ|手伝い|案内)しので', r'\1しますので', text)
    # "ご用意ししておきます" → "ご用意しておきます"
    text = re.sub(r'ご(確認|用意|案内)ししておきます', r'ご\1しておきます', text)
    # "見てきしておきます" → "見ておきます"
    text = re.sub(r'見てきしておきます', '確認しておきます', text)
    # "ご用意ししましょう" → "ご用意しましょう"
    text = re.sub(r'ご(確認|用意|案内)ししましょう', r'ご\1しましょう', text)
    # Generic: Xししておく → Xしておく (for suru verbs with honorific prefix)
    text = re.sub(r'(確認|用意|持ち|調べ|準備|手配|手伝い)しし(て|ます|ましょう|た)', r'\1し\2', text)

    # --- Check if text is still broken ---
    is_broken = bool(re.search(r'(しので|きので|ししてお|きしてお|ししま|きしま)', text))
    is_short_bad = text.strip() in ["うん。", "うん", "ええ。", "ああ。", "うん", "ええ"]

    if is_broken or is_short_bad:
        # Replace with safe response appropriate to human context
        if prev_human_text:
            if any(kw in prev_human_text for kw in ["痛", "しんど", "疲れ", "寂し", "怖", "困"]):
                return random.choice([
                    "お気持ち、よくわかります。無理なさらないでくださいね。",
                    "それはご心配ですね。いつでもお手伝いしますよ。",
                    "そうでしたか…。ゆっくりお話しください。",
                ])
            elif "？" in prev_human_text or "?" in prev_human_text or "かな" in prev_human_text or "か" in prev_human_text[-5:]:
                return random.choice([
                    "はい、確認してみますね。",
                    "わかりました。すぐに調べます。",
                    "かしこまりました。少々お待ちください。",
                ])

        return random.choice([
            "はい、かしこまりました。",
            "なるほど。何かお手伝いしましょうか。",
            "そうですね。承知しました。",
            "おっしゃる通りですね。",
        ])

    return text


# ============================================================
# Main fix pass
# ============================================================

def quality_fix_v2(record):
    """More aggressive quality fix."""
    source = record.get("source", "")
    convs = record.get("conversations", [])

    fixed = []
    for i, c in enumerate(convs):
        text = c.get("value", "")
        role = c.get("from", "human")

        # Clean transcription markers
        if source == "real_corpus_slice":
            text = re.sub(r'\{[<>]\}', '', text)
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'###', '', text)
            text = re.sub(r',,', '', text)          # pause markers
            text = re.sub(r'\([^)]*\)', '', text)   # parenthetical notes
            text = re.sub(r'\s+', '', text)
            # Filter pure aizuchi-only turns (low info)
            if re.match(r'^[うんはいええああそうへえふーんなるほど]+[。、！？…]*$', text):
                continue

        # Fix V5 human text
        if source in ["V5_synthetic", "V5_realistic"] and role == "human":
            text = fix_v5_human_text(text)
            if text is None:
                continue

        # Fix ALL AI text — template bugs can appear in any source
        if role == "gpt":
            prev_human = ""
            for prev_c in reversed(fixed):
                if prev_c.get("from") == "human":
                    prev_human = prev_c.get("value", "")
                    break

            # Always run template fix (catches bugs from all sources)
            text = fix_v5_ai_text(text, prev_human)

        if text and len(text) >= 2:
            fixed.append({"from": role, "value": text})

    # Merge consecutive same-role turns
    if fixed:
        merged = []
        for c in fixed:
            if merged and merged[-1]["from"] == c["from"]:
                merged[-1]["value"] += c["value"]
            else:
                merged.append(c)

        if len(merged) >= 2:
            # Check for minimum quality
            texts = [c["value"] for c in merged]
            if all(len(t) >= 3 for t in texts):
                if sum(len(t) for t in texts) >= 15:
                    roles = set(c["from"] for c in merged)
                    if len(roles) >= 2:
                        record["conversations"] = merged
                        record["num_turns"] = len(merged)
                        record["total_chars"] = sum(len(c["value"]) for c in merged)
                        return record

    return None


def main():
    print("=" * 60)
    print("FINAL QUALITY FIX v2")
    print("=" * 60)

    # Load current data
    all_records = []
    for split_name in ["train", "val", "test"]:
        fp = TRAIN_DIR / f"{split_name}.jsonl"
        if fp.exists():
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line.strip())
                        all_records.append(r)
                    except:
                        pass

    print(f"Loaded: {len(all_records)}")

    # Apply fixes
    fixed = []
    for r in all_records:
        result = quality_fix_v2(r)
        if result:
            fixed.append(result)

    print(f"After fix: {len(fixed)} ({len(all_records) - len(fixed)} removed)")

    # Dedup
    seen = set()
    unique = []
    for r in fixed:
        h = "|".join(c["value"][:40] for c in r.get("conversations", [])[:2])
        if h not in seen:
            seen.add(h)
            unique.append(r)

    print(f"After dedup: {len(unique)}")

    # Split
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

    random.shuffle(train); random.shuffle(val); random.shuffle(test)

    print(f"Split: train={len(train)} val={len(val)} test={len(test)}")

    # Save
    for name, data in [("train", train), ("val", val), ("test", test)]:
        fpath = TRAIN_DIR / f"{name}.jsonl"
        with open(fpath, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Metadata
    all_data = train + val + test
    src_counts = defaultdict(int)
    for r in all_data: src_counts[r.get("source","?")] += 1

    real_count = sum(1 for r in all_data if "real" in r.get("source","").lower())
    elderly_count = sum(1 for r in all_data if "elderly" in r.get("source",""))

    meta = {
        "dataset": "Japanese_Elderly_Care_AI_Companion_v6_final",
        "version": "6.2.0",
        "total": len(all_data),
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
        "sources": dict(src_counts),
        "real_data_pct": round(real_count/len(all_data)*100, 1) if all_data else 0,
        "real_elderly_pct": round(elderly_count/len(all_data)*100, 1) if all_data else 0,
    }

    with open(TRAIN_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Report
    print(f"\n{'=' * 60}")
    print(f"FINAL DATASET")
    print(f"{'=' * 60}")
    print(f"  Total:    {len(all_data)}")
    print(f"  Train:    {len(train)}")
    print(f"  Val:      {len(val)}")
    print(f"  Test:     {len(test)}")
    print(f"  Real:     {meta['real_data_pct']}%")
    print(f"  Elderly:  {meta['real_elderly_pct']}%")
    print(f"\nSources:")
    for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
        print(f"  {src:30s}: {cnt:5d} ({cnt/len(all_data)*100:5.1f}%)")

    # Quality samples
    print(f"\n--- Samples ---")
    samples = random.sample(all_data, min(6, len(all_data)))
    for i, r in enumerate(samples):
        convs = r.get("conversations", [])
        print(f"\n[Sample {i+1}] {r.get('source','?')}")
        for c in convs[:4]:
            print(f"  [{c['from']}] {c['value'][:120]}")


if __name__ == "__main__":
    main()
