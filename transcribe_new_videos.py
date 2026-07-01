#!/usr/bin/env python3
"""
转录新下载的7个采访视频 + 提取老年人对话 + 合并到V8.1
"""
import json, re, random, time, os, sys
# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)
from pathlib import Path
from collections import defaultdict, Counter

random.seed(42)
REAL_DIR = Path("real_elderly_audio")
TRAIN_DIR = Path("training_data")

# 新视频信息
NEW_VIDEOS = {
    "QbnnL0940ew": {"title": "91歳元看護師長 大病院の裏事情と介護・施設", "duration_min": 38, "type": "interview"},
    "5cvvDAQ_J9o": {"title": "元ゼネコン82歳と現役介護士78歳 年金インタビュー", "duration_min": 27, "type": "interview"},
    "QC2mjYdXXXw": {"title": "元介護助手71歳女性 年金インタビュー", "duration_min": 28, "type": "interview"},
    "i9hThYGy7QI": {"title": "計画的無年金者62歳 年金インタビュー", "duration_min": 36, "type": "interview"},
    "mZwghdKpUU4": {"title": "72歳老人ホーム検討中 年金インタビュー", "duration_min": 14, "type": "interview"},
    "K0AAUXZnvUk": {"title": "85歳マック勤務女性 年金インタビュー", "duration_min": 18, "type": "interview"},
    "fbgRFiig3Qc": {"title": "障がい持つ子供と妻 介護の現実 年金インタビュー", "duration_min": 30, "type": "interview"},
}

# 导入V8.1的核心函数
import sys
sys.path.insert(0, str(Path(__file__).parent))

from improve_dataset_v81 import (
    extract_elderly_utterances, build_conversation_from_elderly_speech,
    clean_text, quality_filter, fix_alternation, TOPIC_RESPONSES,
    detect_topic, make_elderly_speech, add_light_dialect,
)


def transcribe_with_whisper(audio_path, model_size="medium"):
    """GPU加速Whisper转录"""
    import whisper
    print(f"    加载Whisper {model_size}...")
    model = whisper.load_model(model_size).cuda()
    print(f"    转录中(GPU/fp16): {audio_path.name}")
    start = time.time()
    result = model.transcribe(
        str(audio_path),
        language="ja",
        task="transcribe",
        verbose=False,
        fp16=True,
        beam_size=5,
        best_of=5,
    )
    elapsed = time.time() - start
    print(f"    完成: {elapsed:.0f}秒, {len(result['segments'])}段")
    return result


def process_new_videos():
    """处理所有新视频：转录 + 提取对话"""
    all_records = []

    for vid, info in NEW_VIDEOS.items():
        print(f"\n{'='*50}")
        print(f"处理: {vid} ({info['title'][:60]}...)")

        # 找到音频文件
        audio_path = None
        for ext in ['.mp3', '.m4a', '.webm']:
            candidate = REAL_DIR / f"{vid}{ext}"
            if candidate.exists():
                audio_path = candidate
                break

        if not audio_path:
            print(f"  ❌ 找不到音频文件")
            continue

        print(f"  音频: {audio_path.name} ({audio_path.stat().st_size//1024//1024}MB)")

        # 转录
        trans_path = REAL_DIR / f"{vid}_whisper.json"
        if trans_path.exists():
            print(f"  已有转录，加载中...")
            with open(trans_path, encoding="utf-8") as f:
                result = json.load(f)
        else:
            try:
                result = transcribe_with_whisper(audio_path, model_size="medium")
                with open(trans_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"  转录已保存: {trans_path}")
            except Exception as e:
                print(f"  ❌ 转录失败: {e}")
                continue

        # 提取老年人发言
        segments = result.get("segments", [])
        vtype = info.get("type", "interview")
        utterances = extract_elderly_utterances(segments, vtype)
        print(f"  老年人发言: {len(utterances)}段")

        # 构建对话
        records = build_conversation_from_elderly_speech(utterances, vid, info, 0)
        print(f"  对话: {len(records)}条")

        all_records.extend(records)

    return all_records


def main():
    print("=" * 70)
    print("新视频转录 + 合并 V8.1 → V8.2")
    print("=" * 70)

    # ----------------------------------------------------------
    # Step 1: 转录新视频
    # ----------------------------------------------------------
    print("\n[Step 1] 转录7个新视频...")

    # 检查哪些需要转录
    to_transcribe = []
    for vid in NEW_VIDEOS:
        trans_path = REAL_DIR / f"{vid}_whisper.json"
        if not trans_path.exists():
            to_transcribe.append(vid)

    if to_transcribe:
        print(f"  待转录: {len(to_transcribe)}个 ({', '.join(to_transcribe)})")
        print(f"  预计GPU时间: ~{sum(NEW_VIDEOS[v]['duration_min'] for v in to_transcribe)//10}分钟")
    else:
        print(f"  全部已转录，跳过")

    new_records = process_new_videos()

    # 质量过滤
    before = len(new_records)
    new_records = [r for r in new_records if quality_filter(r)]
    print(f"\n  新视频对话: {len(new_records)}条 ({before - len(new_records)} filtered)")

    if new_records:
        avg_t = sum(len(r["conversations"]) for r in new_records) / len(new_records)
        avg_c = sum(sum(len(c["value"]) for c in r["conversations"]) for r in new_records) / len(new_records)
        print(f"  平均轮次: {avg_t:.1f}, 平均字符: {avg_c:.0f}")

        # 按视频统计
        vid_counts = Counter(r.get("video_id", "?") for r in new_records)
        for v, c in vid_counts.most_common():
            print(f"    {v}: {c}条")

    # ----------------------------------------------------------
    # Step 2: 加载V8.1数据
    # ----------------------------------------------------------
    print("\n[Step 2] 加载V8.1现有数据...")

    v81_records = []
    for split_name in ["train", "val", "test"]:
        fp = TRAIN_DIR / f"{split_name}.jsonl"
        if fp.exists():
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try:
                        v81_records.append(json.loads(line.strip()))
                    except:
                        pass

    print(f"  V8.1现有: {len(v81_records)}条")

    # ----------------------------------------------------------
    # Step 3: 合并 + 去重 + 分割
    # ----------------------------------------------------------
    print("\n[Step 3] 合并 V8.1 + 新视频...")

    all_data = v81_records + new_records
    print(f"  合并: {len(all_data)}条")

    # 去重
    seen = set()
    unique = []
    for r in all_data:
        h = "|".join(c["value"][:40] for c in r.get("conversations", [])[:4])
        if h not in seen:
            seen.add(h)
            unique.append(r)
    print(f"  去重: {len(unique)}条")

    # 分层分割
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

    # ----------------------------------------------------------
    # Step 4: 保存V8.2
    # ----------------------------------------------------------
    print("\n[Step 4] 保存V8.2...")

    for name, data in [("train", train), ("val", val), ("test", test)]:
        fp = TRAIN_DIR / f"{name}.jsonl"
        with open(fp, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  {fp}: {len(data)}条")

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
    print(f"V8.2 最终数据集报告")
    print(f"{'=' * 70}")
    print(f"  总数据:       {len(all_final)}条")
    print(f"  训练集:       {len(train)}条")
    print(f"  验证集:       {len(val)}条")
    print(f"  测试集:       {len(test)}条")
    print(f"  真实数据:     {real_count/len(all_final)*100:.1f}%")
    print(f"  老年数据:     {elderly_count/len(all_final)*100:.1f}%")
    print(f"  平均轮次:     {sum(final_turns)/len(final_turns):.1f}")
    print(f"  平均字符:     {sum(final_chars)/len(final_chars):.0f}")
    print(f"  2轮:          {sum(1 for t in final_turns if t <= 2)}条")
    print(f"  4轮以上:      {sum(1 for t in final_turns if t >= 4)}条")

    turn_dist = Counter(final_turns)
    print(f"  轮次分布:     {dict(sorted(turn_dist.items()))}")

    print(f"\n来源分布:")
    for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
        print(f"  {src:30s}: {cnt:5d} ({cnt/len(all_final)*100:5.1f}%)")

    # Video breakdown
    vid_counts = Counter(r.get("video_id", "?") for r in all_final if r.get("video_id"))
    print(f"\n视频来源:")
    for v, c in vid_counts.most_common():
        info = NEW_VIDEOS.get(v) or {"title": "original", "duration_min": "?"}
        if v in NEW_VIDEOS:
            pass  # info already set
        print(f"  {v}: {c}条")

    # 元数据
    meta = {
        "dataset": "Japanese_Elderly_Care_AI_Companion_v8.2",
        "version": "8.2.0",
        "total": len(all_final),
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
        "sources": dict(src_counts),
        "real_data_pct": round(real_count / len(all_final) * 100, 1),
        "real_elderly_pct": round(elderly_count / len(all_final) * 100, 1),
        "avg_turns": round(sum(final_turns) / len(final_turns), 1),
        "avg_chars": round(sum(final_chars) / len(final_chars), 0),
        "videos_total": len(set(r.get("video_id", "") for r in all_final if r.get("video_id"))),
        "improvements_v82": [
            "新增7个年金采访视频 (191分钟, 「年金いくら？」系列)",
            "丢弃采访者提问，只保留老年人真实发言",
            "独白型视频特殊处理（合并3段为一次发言）",
            "8话题感知AI回复 + 多轮对话扩展",
            "0条2轮短对话，100%多轮结构",
        ],
    }
    with open(TRAIN_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\nV8.2 保存完成！")


if __name__ == "__main__":
    main()
