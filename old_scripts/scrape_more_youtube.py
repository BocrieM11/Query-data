#!/usr/bin/env python3
"""
YouTube elderly video search + download + VTT extraction
"""
import subprocess
import json
import os
import re
from pathlib import Path

REAL_DIR = Path("real_elderly_audio")
REAL_DIR.mkdir(exist_ok=True)

# ============================================================
# Step 1: Search for videos
# ============================================================

QUERIES = [
    "80代 一人暮らし 日常 語り",
    "高齢者 生活 インタビュー 思い出",
    "お年寄り 話 昔 昭和",
    "老人ホーム 日常 会話 様子",
    "90歳 思い出話 戦後",
    "日本の田舎 お年寄り 暮らし",
    "高齢者 ひとりごと 日常",
    "おばあちゃん 知恵 話",
    "年金生活 80代 工夫",
    "高齢者 買い物 料理 日常",
]

def search_videos():
    """Search YouTube for Japanese elderly content"""
    all_results = []

    for query in QUERIES:
        try:
            cmd = [
                "yt-dlp", f"ytsearch5:{query}",
                "--flat-playlist", "--dump-json",
                "--no-warnings", "--socket-timeout", "15"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    info = json.loads(line)
                    dur = info.get("duration", 0) or 0
                    if dur > 120 and dur < 7200:  # 2min - 2hr
                        all_results.append({
                            "id": info.get("id"),
                            "title": info.get("title", ""),
                            "duration": dur,
                            "url": f"https://youtube.com/watch?v={info.get('id')}",
                            "query": query,
                        })
                except:
                    pass
        except Exception as e:
            print(f"  Search error [{query}]: {e}")

    # Deduplicate
    seen = set()
    unique = []
    for r in all_results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)

    return unique


# ============================================================
# Step 2: Filter out already downloaded
# ============================================================

def filter_new(videos):
    """Filter out already downloaded videos"""
    existing = set()
    for f in REAL_DIR.glob("*.ja.vtt"):
        vid = f.stem  # "XXXXX.ja" -> "XXXXX"
        existing.add(vid)
    for f in REAL_DIR.glob("*.wav"):
        existing.add(f.stem)

    new = [v for v in videos if v["id"] not in existing]
    return new, existing


# ============================================================
# Step 3: Download (audio only + subtitles)
# ============================================================

def download_videos(video_ids, max_videos=8):
    """Download audio + Japanese subtitles"""
    downloaded = []
    for vid in video_ids[:max_videos]:
        print(f"\n  Downloading: {vid} ...")
        try:
            cmd = [
                "yt-dlp",
                f"https://youtube.com/watch?v={vid}",
                "-f", "bestaudio[ext=m4a]/bestaudio",
                "--extract-audio", "--audio-format", "wav",
                "--write-subs", "--sub-langs", "ja",
                "--convert-subs", "vtt",
                "-o", str(REAL_DIR / "%(id)s.%(ext)s"),
                "--no-warnings", "--no-playlist",
                "--socket-timeout", "30",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                downloaded.append(vid)
                print(f"    OK")
            else:
                # Try audio only (no subs)
                print(f"    VTT failed, trying audio only...")
                cmd2 = [
                    "yt-dlp",
                    f"https://youtube.com/watch?v={vid}",
                    "-f", "bestaudio[ext=m4a]/bestaudio",
                    "--extract-audio", "--audio-format", "wav",
                    "-o", str(REAL_DIR / "%(id)s.%(ext)s"),
                    "--no-warnings", "--no-playlist",
                    "--socket-timeout", "30",
                ]
                subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
                downloaded.append(vid)
                print(f"    OK (audio only)")
        except Exception as e:
            print(f"    FAILED: {e}")

    return downloaded


# ============================================================
# Step 4: Extract clean text from VTT
# ============================================================

def parse_vtt_clean(vtt_path):
    """Extract clean text lines from VTT, removing timing/duplicates"""
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by subtitle blocks
    # Pattern: timestamp --> timestamp, then text
    blocks = re.split(r'\n\n+', content)

    clean_lines = []
    seen_texts = set()

    for block in blocks:
        block = block.strip()
        if not block or block == "WEBVTT" or "Kind:" in block or "Language:" in block:
            continue

        # Remove timestamp lines
        lines = block.split("\n")
        text_parts = []
        for line in lines:
            # Skip timestamp lines
            if re.match(r'^[\d:.]+\s*-->', line):
                continue
            # Skip cue settings
            if line.startswith("align:") or line.startswith("position:"):
                continue
            # Clean the text: remove <c> tags and timestamps within tags
            cleaned = re.sub(r'<c>', '', line)
            cleaned = re.sub(r'</c>', '', cleaned)
            cleaned = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', cleaned)
            cleaned = cleaned.strip()
            if cleaned and len(cleaned) >= 3:
                text_parts.append(cleaned)

        if text_parts:
            full_text = "".join(text_parts)
            # Deduplicate (VTT often repeats lines for timing)
            text_key = full_text[:60]
            if text_key not in seen_texts and len(full_text) >= 5:
                seen_texts.add(text_key)
                clean_lines.append(full_text)

    return clean_lines


# ============================================================
# Step 5: Build conversation segments
# ============================================================

def build_conversations(clean_lines, min_chars=10, max_chars=200):
    """Build natural multi-turn conversation segments from VTT text"""
    # Filter: keep reasonable length lines
    filtered = [l for l in clean_lines if min_chars <= len(l) <= max_chars]

    if len(filtered) < 4:
        return []

    conversations = []
    # Sliding window: 4-8 line chunks with overlap
    for i in range(0, len(filtered) - 3, 2):
        chunk = filtered[i:i+6]
        if len(chunk) < 3:
            continue

        # Alternate human/gpt
        convs = []
        for j, text in enumerate(chunk):
            role = "human" if j % 2 == 0 else "gpt"
            convs.append({"from": role, "value": text})

        conversations.append(convs)

    return conversations


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("YouTube Elderly Video Scraper + VTT Extractor")
    print("=" * 60)

    # Search
    print("\n[1] Searching YouTube...")
    videos = search_videos()
    print(f"  Found {len(videos)} candidate videos")
    for v in videos[:20]:
        mins = v["duration"] // 60
        print(f"  [{v['id']}] ({mins}min) {v['title'][:80]}")

    # Filter new
    new_vids, existing = filter_new(videos)
    print(f"\n[2] Already downloaded: {len(existing)}")
    print(f"    New candidates: {len(new_vids)}")

    # Download
    if new_vids:
        print(f"\n[3] Downloading up to 8 new videos...")
        vids_to_dl = [v["id"] for v in new_vids]
        downloaded = download_videos(vids_to_dl, max_videos=8)
        print(f"    Downloaded: {len(downloaded)}")
    else:
        print(f"\n[3] No new videos to download")
        downloaded = []

    # Parse all VTT files
    print(f"\n[4] Parsing all VTT files...")
    all_vtt = sorted(REAL_DIR.glob("*.ja.vtt"))
    total_clean = 0
    total_convos = 0
    all_conversations = []

    for vtt_path in all_vtt:
        video_id = vtt_path.stem.replace(".ja", "")
        clean = parse_vtt_clean(vtt_path)
        convos = build_conversations(clean)

        # Add video metadata
        for c in convos:
            c_with_meta = {
                "id": f"yt_real_{video_id}_{len(all_conversations):04d}",
                "video_id": video_id,
                "conversations": c,
                "source": "real_elderly_youtube_v2",
                "quality": "real_transcribed_elderly",
                "language": "ja",
                "country_code": "JP",
                "num_turns": len(c),
                "total_chars": sum(len(t["value"]) for t in c),
            }
            all_conversations.append(c_with_meta)

        print(f"  {vtt_path.name}: {len(clean)} clean lines -> {len(convos)} conversations")
        total_clean += len(clean)
        total_convos += len(convos)

    print(f"\n  Total: {total_clean} clean lines -> {total_convos} potential conversations")

    # Save
    out_path = REAL_DIR / "vtt_extracted_conversations.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_conversations, f, ensure_ascii=False, indent=2)
    print(f"\n[5] Saved: {out_path} ({len(all_conversations)} records)")

    # Report
    print(f"\n{'=' * 60}")
    print(f"DONE")
    print(f"{'=' * 60}")
    print(f"  Videos existing: {len(existing)}")
    print(f"  New downloaded:  {len(downloaded)}")
    print(f"  VTT files:       {len(all_vtt)}")
    print(f"  Clean lines:     {total_clean}")
    print(f"  Conversations:   {total_convos}")

if __name__ == "__main__":
    main()
