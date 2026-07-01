#!/usr/bin/env python3
"""
Proper VTT parser for YouTube Japanese captions.
Strategy: Parse <c>-tagged lines for full text, use short-duration blocks
as checkpoints, build complete non-overlapping utterances.
"""
import re, json
from pathlib import Path

REAL_DIR = Path("real_elderly_audio")

def parse_vtt_proper(vtt_path):
    """Parse VTT and extract clean, non-overlapping text segments."""
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into blocks (separated by blank lines)
    raw_blocks = re.split(r'\n\n+', content.strip())

    segments = []
    for block in raw_blocks:
        block = block.strip()
        if not block or "WEBVTT" in block or "Kind:" in block or "Language:" in block:
            continue

        lines = block.split("\n")

        # Find timestamp line
        ts_line = None
        clean_lines = []
        c_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^[\d:.]+\s*-->', line):
                ts_line = line
            elif "<c>" in line:
                c_lines.append(line)
            elif not line.startswith("align:") and not line.startswith("position:"):
                clean_lines.append(line)

        if not c_lines:
            continue

        # Extract duration
        dur = 0
        if ts_line:
            parts = ts_line.split("-->")
            if len(parts) == 2:
                def to_sec(t):
                    t = t.strip().split(":")[-3:] if ":" in t else ["0","0","0"]
                    try:
                        h, m, s = float(t[-3]), float(t[-2]), float(t[-1])
                        return h*3600 + m*60 + s
                    except:
                        return 0
                dur = to_sec(parts[1]) - to_sec(parts[0])

        # Extract text from <c> lines: strip all tags
        c_text_parts = []
        for cl in c_lines:
            # Remove all <c> </c> and timestamp tags
            cleaned = re.sub(r'</c>', '', cl)
            cleaned = re.sub(r'<c>', '', cleaned)
            cleaned = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', cleaned)
            cleaned = cleaned.strip()
            if cleaned:
                c_text_parts.append(cleaned)

        c_text = "".join(c_text_parts)

        # Prepend any clean prefix (the partial text shown before <c> additions)
        prefix = " ".join(clean_lines).strip() if clean_lines else ""

        # Build full text: if prefix ends where c_text begins, join intelligently
        if prefix and c_text:
            # Find overlap and merge
            for overlap_len in range(min(len(prefix), 30), 2, -1):
                if prefix[-overlap_len:] == c_text[:overlap_len]:
                    c_text = c_text[overlap_len:]
                    break
            full_text = prefix + c_text
        elif c_text:
            full_text = c_text
        else:
            full_text = prefix

        full_text = full_text.strip()
        if not full_text or len(full_text) < 3:
            continue

        segments.append({
            "text": full_text,
            "duration": dur,
            "is_checkpoint": dur < 0.15,  # Short blocks = cumulative text
        })

    # Now build utterances by accumulating incremental segments
    utterances = []
    current = ""

    for seg in segments:
        text = seg["text"]

        if seg["is_checkpoint"]:
            # Checkpoint: full accumulated text so far
            if text and len(text) > len(current):
                current = text
        else:
            # Incremental: text adds to previous
            if current and text:
                # Find overlap
                found_overlap = False
                for ol in range(min(len(current), 30), 2, -1):
                    if current[-ol:] == text[:ol]:
                        current = current + text[ol:]
                        found_overlap = True
                        break
                if not found_overlap:
                    # No overlap - might be a new sentence
                    # Append to current if it seems like continuation
                    if not current.endswith("。") and not current.endswith("！"):
                        current = current + text
                    else:
                        # Save current, start new
                        if len(current) >= 5:
                            utterances.append(current)
                        current = text
            elif text:
                current = text

    # Add final
    if current and len(current) >= 5:
        utterances.append(current)

    # Deduplicate by removing substrings
    # If utterance B is fully contained in utterance A (or overlaps heavily), skip
    final = []
    for i, utt in enumerate(utterances):
        is_dup = False
        for j in range(max(0, i-3), i):
            prev = utterances[j]
            # If this utterance's start is in previous utterance, it's overlap
            if len(utt) > 5 and len(prev) > 5:
                if utt[:min(20, len(utt))] in prev:
                    is_dup = True
                    break
        if not is_dup and 5 <= len(utt) <= 300:
            final.append(utt)

    return final


def build_conversations(utterances, min_turns=4):
    """Build conversations from utterances, alternating human/gpt."""
    filtered = [u for u in utterances if 8 <= len(u) <= 250]

    conversations = []
    # Non-overlapping sliding window
    for i in range(0, len(filtered) - min_turns + 1, min_turns):
        chunk = filtered[i:i+8]  # Up to 8 turns
        if len(chunk) < min_turns:
            continue

        convs = []
        for j, text in enumerate(chunk):
            convs.append({"from": "human" if j % 2 == 0 else "gpt", "value": text})

        # Only keep if adjacent turns don't share significant text
        texts = [c["value"] for c in convs]
        has_overlap = False
        for ti in range(len(texts)-1):
            for w in range(5, min(25, len(texts[ti]), len(texts[ti+1]))):
                if texts[ti][-w:] in texts[ti+1] and len(texts[ti][-w:]) > 6:
                    has_overlap = True
                    break
            if has_overlap:
                break

        if not has_overlap:
            conversations.append(convs)

    return conversations


def main():
    vtt_files = sorted(REAL_DIR.glob("*.ja.vtt"))
    print(f"Processing {len(vtt_files)} VTT files...")

    all_conversations = []
    all_utterances = []

    for vtt_path in vtt_files:
        vid = vtt_path.stem.replace(".ja", "")
        utterances = parse_vtt_proper(vtt_path)
        convos = build_conversations(utterances)

        print(f"  {vtt_path.name}: {len(utterances)} utterances -> {len(convos)} conversations")

        for i, conv in enumerate(convos):
            all_conversations.append({
                "id": f"yt_real_{vid}_{i:04d}",
                "video_id": vid,
                "conversations": conv,
                "source": "real_elderly_youtube_v3",
                "quality": "real_transcribed_elderly",
                "language": "ja",
                "country_code": "JP",
                "scenario": "real_daily_life",
                "num_turns": len(conv),
                "total_chars": sum(len(c["value"]) for c in conv),
            })

        all_utterances.extend(utterances)

    print(f"\nTotal: {len(all_conversations)} conversations from {len(all_utterances)} utterances")

    # Save
    out_path = REAL_DIR / "vtt_parsed_v3.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_conversations, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_path}")

    # Quality samples
    print("\n--- Sample conversations ---")
    for conv_data in all_conversations[::max(1, len(all_conversations)//6)][:6]:
        cid = conv_data["id"]
        convs = conv_data["conversations"]
        print(f"\n[{cid}] ({len(convs)} turns)")
        for t in convs[:4]:
            print(f"  [{t['from']}] {t['value'][:130]}")

if __name__ == "__main__":
    main()
