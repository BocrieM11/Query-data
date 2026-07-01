#!/usr/bin/env python3
"""Search all queries + download best candidates"""
import subprocess, json, sys
from pathlib import Path

REAL_DIR = Path("real_elderly_audio")
REAL_DIR.mkdir(exist_ok=True)

QUERIES = [
    "80代 一人暮らし 日常 語り",
    "高齢者 生活 インタビュー 思い出",
    "お年寄り 昔 昭和 語り",
    "老人ホーム 日常 会話",
    "90歳 思い出話",
    "日本の田舎 お年寄り 暮らし",
    "高齢者 ひとりごと 料理",
    "おばあちゃん 知恵 話 暮らし",
    "年金生活 80代 一人暮らし",
    "介護 高齢者 会話 様子 vlog",
]

def search_all():
    all_results = []
    for q in QUERIES:
        try:
            cmd = ["python", "-m", "yt_dlp", f"ytsearch5:{q}",
                   "--flat-playlist", "--dump-json", "--no-warnings", "--socket-timeout", "15"]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            for line in r.stdout.strip().split("\n"):
                if not line.strip(): continue
                try:
                    info = json.loads(line)
                    dur = info.get("duration", 0) or 0
                    if 120 < dur < 7200:
                        all_results.append({
                            "id": info.get("id"), "title": info.get("title",""),
                            "duration": dur, "query": q,
                            "channel": info.get("channel",""),
                        })
                except: pass
        except Exception as e:
            print(f"  ERR [{q}]: {e}")
    # Dedup
    seen = set(); unique = []
    for r in all_results:
        if r["id"] not in seen:
            seen.add(r["id"]); unique.append(r)
    return unique

def filter_new(videos):
    existing = set()
    for f in REAL_DIR.glob("*.ja.vtt"): existing.add(f.stem.replace(".ja",""))
    for f in REAL_DIR.glob("*.wav"): existing.add(f.stem)
    return [v for v in videos if v["id"] not in existing], existing

def download_one(vid):
    try:
        cmd = ["python", "-m", "yt_dlp",
               f"https://youtube.com/watch?v={vid}",
               "-f", "bestaudio[ext=m4a]/bestaudio",
               "--extract-audio", "--audio-format", "wav",
               "--write-subs", "--sub-langs", "ja",
               "--convert-subs", "vtt",
               "-o", str(REAL_DIR / "%(id)s.%(ext)s"),
               "--no-warnings", "--no-playlist",
               "--socket-timeout", "30", "--retries", "2"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode == 0
    except:
        return False

def main():
    print("=" * 50)
    print("Searching YouTube...")
    videos = search_all()
    print(f"Found {len(videos)} candidates")

    # Sort by relevance: prefer longer videos with elderly-related channels
    for v in videos:
        dur = v["duration"]
        ch = v.get("channel","")
        score = min(dur/60, 40)  # up to 40 points for duration
        title = v["title"]
        for kw in ["80","90","歳","高齢","老人","一人暮らし","年金","昭和","祖母"]:
            if kw in title: score += 5
            if kw in ch: score += 3
        v["score"] = score

    videos.sort(key=lambda v: -v["score"])

    print("\nTop candidates:")
    for v in videos[:25]:
        mins = v["duration"]//60
        print(f"  [{v['id']}] ({mins}min) s={v['score']:.0f} {v['title'][:85]}")

    # Filter
    new_vids, existing = filter_new(videos)
    print(f"\nExisting: {len(existing)} | New: {len(new_vids)}")

    if not new_vids:
        print("No new videos to download")
        return

    # Download top 8
    to_dl = new_vids[:8]
    print(f"\nDownloading {len(to_dl)} videos...")
    for i, v in enumerate(to_dl):
        mins = v["duration"]//60
        print(f"  [{i+1}/{len(to_dl)}] {v['id']} ({mins}min) {v['title'][:70]}")
        ok = download_one(v["id"])
        print(f"    {'OK' if ok else 'FAILED'}")

    # Final count
    vtt_files = list(REAL_DIR.glob("*.ja.vtt"))
    print(f"\nTotal VTT files: {len(vtt_files)}")

if __name__ == "__main__":
    main()
