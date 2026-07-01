#!/usr/bin/env python3
"""
Whisper语音转文字 → 采访对话提取 → ShareGPT JSONL
"""
import json, re, os, time
from pathlib import Path
from collections import defaultdict

REAL_DIR = Path("real_elderly_audio")

# 视频信息
VIDEO_INFO = {
    "06e_und6-C8": {"title": "65歳以上年金インタビュー", "duration_min": 61},
    "rQJEtScQqlU": {"title": "60-80代老後夫婦年金生活インタビュー", "duration_min": 81},
    "W2pW9-R0YfY": {"title": "76歳一人暮らし体験談", "duration_min": 56},
    "igfukXU_i-Y": {"title": "83歳一人暮らし老人ホームの現実", "duration_min": 29},
}

# ============================================================
# Step 1: Whisper转写
# ============================================================

def transcribe_with_whisper(audio_path, model_size="medium"):
    """用Whisper转写音频"""
    import whisper
    print(f"  加载Whisper {model_size}模型...")
    model = whisper.load_model(model_size).cuda()

    print(f"  转写中(GPU): {audio_path.name} ...")
    start = time.time()
    result = model.transcribe(
        str(audio_path),
        language="ja",
        task="transcribe",
        verbose=False,
        fp16=True,
    )
    elapsed = time.time() - start
    print(f"  完成: {elapsed:.0f}秒, {len(result['segments'])}段")

    return result


# ============================================================
# Step 2: 从采访中提取对话对
# ============================================================

def extract_interview_qa(segments):
    """
    从Whisper分段中提取采访问答对。
    策略：
    - 交替说话模式检测（通过停顿、内容变化判断）
    - 长段落→短段落交替 → 可能是问答
    - 问句（か？ですか？）→ 陈述 → 识别为QA对
    """
    qa_pairs = []
    texts = []

    for seg in segments:
        text = seg["text"].strip()
        if text and len(text) >= 5:
            texts.append(text)

    if len(texts) < 4:
        return qa_pairs

    # 策略1：交替模式 —— 每隔一个取为Q，另一个为A
    for i in range(0, len(texts) - 1, 2):
        q = texts[i]
        a = texts[i + 1] if i + 1 < len(texts) else ""

        # 质量过滤
        if len(q) < 5 or len(a) < 5:
            continue
        if len(q) > 200 or len(a) > 200:
            continue

        qa_pairs.append({"question": q, "answer": a})

    # 策略2：问句检测 —— 找到问句，下一个非问句作为答案
    for i, text in enumerate(texts):
        is_question = (
            text.endswith("か") or text.endswith("か？") or
            text.endswith("ですか") or text.endswith("ですか？") or
            text.endswith("ますか") or text.endswith("ますか？") or
            "？" in text or "?" in text
        )
        if is_question and i + 1 < len(texts):
            answer = texts[i + 1]
            # 答案不能也是问句
            if not (answer.endswith("か") or answer.endswith("？")):
                if 5 <= len(answer) <= 200:
                    qa_pairs.append({"question": text, "answer": answer})

    return qa_pairs


# ============================================================
# Step 3: 转ShareGPT格式
# ============================================================

def qa_to_sharegpt(qa_pairs, video_id, video_info):
    """将QA对转为ShareGPT格式"""
    records = []
    for i, qa in enumerate(qa_pairs):
        conversations = [
            {"from": "human", "value": qa["question"]},
            {"from": "gpt", "value": qa["answer"]},
        ]
        records.append({
            "id": f"whisper_{video_id}_{i:04d}",
            "conversations": conversations,
            "source": "real_elderly_whisper",
            "quality": "real_transcribed_interview",
            "language": "ja",
            "country_code": "JP",
            "scenario": f"interview: {video_info.get('title', 'unknown')}",
            "video_id": video_id,
            "num_turns": 2,
            "total_chars": sum(len(c["value"]) for c in conversations),
        })
    return records


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 60)
    print("Whisper转录 + 采访对话提取")
    print("=" * 60)

    # 找到所有mp3文件（新下载的）
    mp3_files = sorted(REAL_DIR.glob("*.mp3"))
    if not mp3_files:
        # 也检查m4a
        mp3_files = sorted(REAL_DIR.glob("*.m4a"))
    if not mp3_files:
        print("没有找到音频文件，可能还在下载中...")
        return

    print(f"\n找到 {len(mp3_files)} 个音频文件")
    for f in mp3_files:
        vid = f.stem
        info = VIDEO_INFO.get(vid, {})
        print(f"  {f.name} ({info.get('duration_min', '?')}min) - {info.get('title', '?')}")

    all_records = []

    for audio_path in mp3_files:
        vid = audio_path.stem
        info = VIDEO_INFO.get(vid, {})

        print(f"\n{'='*40}")
        print(f"处理: {audio_path.name}")

        # Whisper转写
        trans_path = REAL_DIR / f"{vid}_whisper.json"
        if trans_path.exists():
            print(f"  已有转写结果，跳过...")
            with open(trans_path, encoding="utf-8") as f:
                result = json.load(f)
        else:
            try:
                result = transcribe_with_whisper(audio_path, model_size="medium")
                # 保存转写结果
                with open(trans_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"  转写已保存: {trans_path}")
            except Exception as e:
                print(f"  转写失败: {e}")
                continue

        # 提取QA对
        segments = result.get("segments", [])
        qa_pairs = extract_interview_qa(segments)
        print(f"  提取QA对: {len(qa_pairs)}")

        # 转ShareGPT
        records = qa_to_sharegpt(qa_pairs, vid, info)
        all_records.extend(records)
        print(f"  ShareGPT记录: {len(records)}")

    # 保存
    if all_records:
        out_path = REAL_DIR / "whisper_interviews.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_records, f, ensure_ascii=False, indent=2)
        print(f"\n{'='*60}")
        print(f"完成! {len(all_records)} 条Whisper采访对话")
        print(f"保存至: {out_path}")

        # 样例
        print(f"\n--- 样例 ---")
        for r in all_records[:5]:
            print(f"\n[{r['id']}] {r['scenario']}")
            for c in r["conversations"]:
                print(f"  [{c['from']}] {c['value'][:150]}")
    else:
        print("\n没有提取到任何对话。")


if __name__ == "__main__":
    main()
