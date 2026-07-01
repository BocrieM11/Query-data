#!/usr/bin/env python3
"""
将Whisper转写的采访对话合并到训练数据集
"""
import json, random
from pathlib import Path
from collections import defaultdict

random.seed(42)
TRAIN_DIR = Path("training_data")
REAL_DIR = Path("real_elderly_audio")

def main():
    # 加载Whisper采访数据
    whisper_path = REAL_DIR / "whisper_interviews.json"
    if not whisper_path.exists():
        print("Whisper采访数据还不存在，等转写完成后再运行。")
        return

    with open(whisper_path, encoding="utf-8") as f:
        whisper_records = json.load(f)

    print(f"Whisper采访记录: {len(whisper_records)}")

    # 加载现有训练数据
    existing = []
    for split_name in ["train", "val", "test"]:
        fp = TRAIN_DIR / f"{split_name}.jsonl"
        if fp.exists():
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try:
                        existing.append(json.loads(line.strip()))
                    except:
                        pass
    print(f"现有训练数据: {len(existing)}")

    # 合并
    all_records = existing + whisper_records
    print(f"合并后: {len(all_records)}")

    # 去重
    seen = set()
    unique = []
    for r in all_records:
        h = "|".join(c["value"][:40] for c in r.get("conversations", [])[:2])
        if h not in seen:
            seen.add(h)
            unique.append(r)
    print(f"去重后: {len(unique)}")

    # 按来源分层分割
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

    print(f"\n分割: train={len(train)} val={len(val)} test={len(test)}")

    # 保存
    for name, data in [("train", train), ("val", val), ("test", test)]:
        fpath = TRAIN_DIR / f"{name}.jsonl"
        with open(fpath, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  {fpath}: {len(data)}")

    # 统计
    all_data = train + val + test
    src_counts = defaultdict(int)
    for r in all_data: src_counts[r.get("source", "?")] += 1

    real_count = sum(1 for r in all_data if "real" in r.get("source", "").lower())
    elderly_count = sum(1 for r in all_data if "elderly" in r.get("source", "") or "whisper" in r.get("source", ""))

    print(f"\n来源分布:")
    for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
        pct = cnt / len(all_data) * 100
        print(f"  {src:30s}: {cnt:5d} ({pct:5.1f}%)")
    print(f"\n真实数据: {real_count/len(all_data)*100:.1f}%")
    print(f"老年数据: {elderly_count/len(all_data)*100:.1f}%")
    print(f"总计: {len(all_data)}条")

    # 更新metadata
    meta = {
        "dataset": "Japanese_Elderly_Care_AI_Companion_v7",
        "version": "7.0.0",
        "total": len(all_data),
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
        "sources": dict(src_counts),
        "real_data_pct": round(real_count/len(all_data)*100, 1),
        "real_elderly_pct": round(elderly_count/len(all_data)*100, 1),
        "improvements_v7": [
            "新增Whisper转写：4个老年采访视频",
            "采访内容：年金、独居、养老院现实",
            "总数据量目标：2000+条",
            "真实老年数据目标：50%+",
        ],
    }
    with open(TRAIN_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 合并完成，metadata已更新")


if __name__ == "__main__":
    main()
