#!/usr/bin/env python3
"""
Final VTT parser: Simple extraction + smart overlap removal.
Strategy: Use the v1 approach (parse both clean and <c> lines, dedup globally),
then fix within-conversation overlaps by trimming/merging.
"""
import re, json
from pathlib import Path

REAL_DIR = Path("real_elderly_audio")

def parse_vtt_simple(vtt_path):
    """Simple VTT extraction: all non-timestamp, non-tag text, globally deduped."""
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r'\n\n+', content.strip())
    all_texts = []
    seen = set()

    for block in blocks:
        block = block.strip()
        if not block or "WEBVTT" in block or "Kind:" in block or "Language:" in block:
            continue

        lines = block.split("\n")
        text_parts = []
        has_c = False

        for line in lines:
            line = line.strip()
            if not line or re.match(r'^[\d:.]+\s*-->', line):
                continue
            if line.startswith("align:") or line.startswith("position:"):
                continue

            if "<c>" in line:
                has_c = True
                # Extract text from <c>-tagged line
                cleaned = line
                # Remove timestamps within tags: <00:00:04.160>
                cleaned = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', cleaned)
                # Remove <c> and </c> tags
                cleaned = cleaned.replace("</c>", "").replace("<c>", "")
                cleaned = cleaned.strip()
                if cleaned and len(cleaned) >= 2:
                    text_parts.append(("c", cleaned))
            else:
                # Clean display line
                if len(line) >= 2:
                    text_parts.append(("clean", line))

        if not text_parts:
            continue

        # Build full text: concatenate clean prefix + c-text
        full_text = ""
        for typ, txt in text_parts:
            if typ == "clean" and not full_text:
                full_text = txt
            elif typ == "c":
                # Check overlap with current full_text
                if full_text:
                    for ol in range(min(len(full_text), 25), 2, -1):
                        if full_text[-ol:] == txt[:ol]:
                            txt = txt[ol:]
                            break
                full_text += txt

        full_text = full_text.strip()
        if not full_text or len(full_text) < 5:
            continue

        # Global dedup: keep only if new
        key = full_text[:60]
        if key not in seen:
            seen.add(key)
            all_texts.append(full_text)

    return all_texts


def build_conversations_no_overlap(utterances, stride=4, max_turns=8):
    """
    Build conversations from utterances.
    stride=4: skip 4 utterances between conversation starts (reduces overlap)
    After building, trim overlapping prefixes between adjacent turns.
    """
    # Filter to reasonable lengths
    filtered = [u for u in utterances if 10 <= len(u) <= 250]

    if len(filtered) < 4:
        return []

    conversations = []

    for start in range(0, len(filtered) - 4, stride):
        end = min(start + max_turns, len(filtered))
        chunk = filtered[start:end]
        if len(chunk) < 4:
            continue

        # Build alternating human/gpt turns
        raw_turns = []
        for j, text in enumerate(chunk):
            role = "human" if j % 2 == 0 else "gpt"
            raw_turns.append({"from": role, "value": text})

        # Fix overlap between adjacent turns
        fixed_turns = []
        for i, turn in enumerate(raw_turns):
            text = turn["value"]
            if i > 0:
                prev = fixed_turns[-1]["value"]
                # Check if current text overlaps with previous
                for ol in range(min(len(prev), 30), 4, -1):
                    if text.startswith(prev[-ol:]):
                        text = text[ol:].strip()
                        break
            if text and len(text) >= 6:
                fixed_turns.append({"from": turn["from"], "value": text})

        if len(fixed_turns) >= 4:
            conversations.append(fixed_turns)

    return conversations


def quality_filter(conversation):
    """Check if conversation meets quality standards."""
    texts = [c["value"] for c in conversation]

    # No very short turns
    if any(len(t) < 5 for t in texts):
        return False

    # No adjacent near-duplicate turns
    for i in range(len(texts)-1):
        if texts[i][:30] == texts[i+1][:30]:
            return False

    # Must have some sentence endings
    sentence_ends = sum(1 for t in texts if t.endswith("。") or t.endswith("！") or t.endswith("？") or t.endswith("…"))
    if sentence_ends < len(texts) * 0.3:
        return False

    return True


def main():
    vtt_files = sorted(REAL_DIR.glob("*.ja.vtt"))
    print(f"Processing {len(vtt_files)} VTT files...")

    all_conversations = []
    total_utterances = 0

    for vtt_path in vtt_files:
        vid = vtt_path.stem.replace(".ja", "")

        # Parse
        utterances = parse_vtt_simple(vtt_path)
        total_utterances += len(utterances)

        # Build conversations with different strides
        for stride in [3, 4, 5]:
            convos = build_conversations_no_overlap(utterances, stride=stride, max_turns=8)
            for conv in convos:
                if quality_filter(conv):
                    all_conversations.append({
                        "id": f"yt_real_{vid}_{len(all_conversations):04d}",
                        "video_id": vid,
                        "conversations": conv,
                        "source": "real_elderly_youtube_v4",
                        "quality": "real_transcribed_elderly",
                        "language": "ja",
                        "country_code": "JP",
                        "scenario": "real_daily_life",
                        "num_turns": len(conv),
                        "total_chars": sum(len(c["value"]) for c in conv),
                    })

        print(f"  {vtt_path.name}: {len(utterances)} utts -> {len([c for c in all_conversations if c['video_id']==vid])} convos")

    print(f"\nTotal: {len(all_conversations)} quality conversations from {total_utterances} utterances")

    # Final dedup by conversation content
    seen = set()
    unique = []
    for r in all_conversations:
        key = "|".join(c["value"][:50] for c in r["conversations"][:3])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    print(f"After final dedup: {len(unique)}")

    # Save
    out_path = REAL_DIR / "vtt_final_conversations.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_path}")

    # Samples
    print("\n--- Sample conversations ---")
    samples = unique[::max(1, len(unique)//6)][:6]
    for r in samples:
        print(f"\n[{r['id']}] ({r['num_turns']} turns)")
        for t in r["conversations"][:6]:
            print(f"  [{t['from']}] {t['value'][:130]}")

if __name__ == "__main__":
    main()
