#!/usr/bin/env python3
"""
V10: 从现有Whisper JSON中提取更多对话
- 宽松合并策略（2段合1 + 3段合1 双策略）
- 重叠滑动窗口（stride=1）
- 更精确的话题检测
"""
import json, re, random, sys
if sys.platform == 'win32':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
from pathlib import Path
from collections import Counter

random.seed(42)
REAL_DIR = Path("real_elderly_audio")

VIDEO_INFO = {
    "06e_und6-C8": {"title": "65歳以上年金インタビュー", "type": "interview"},
    "rQJEtScQqlU": {"title": "60-80代老後夫婦年金生活インタビュー", "type": "interview"},
    "W2pW9-R0YfY": {"title": "76歳一人暮らし体験談", "type": "monologue"},
    "igfukXU_i-Y": {"title": "83歳一人暮らし老人ホームの現実", "type": "monologue"},
    "QbnnL0940ew": {"title": "91歳元看護師長", "type": "interview"},
    "5cvvDAQ_J9o": {"title": "元ゼネコン82歳と現役介護士78歳", "type": "interview"},
    "QC2mjYdXXXw": {"title": "元介護助手71歳女性", "type": "interview"},
    "i9hThYGy7QI": {"title": "計画的無年金者62歳", "type": "interview"},
    "mZwghdKpUU4": {"title": "72歳老人ホーム検討中", "type": "interview"},
    "K0AAUXZnvUk": {"title": "85歳マック勤務女性", "type": "interview"},
    "fbgRFiig3Qc": {"title": "障がい持つ子供と妻、介護の現実", "type": "interview"},
}

# ─── 工具函数（从improve_dataset_v81.py复用） ───

def is_question(text):
    text = text.strip()
    if len(text) < 3: return False
    if any(text.endswith(e) for e in ['か', 'か？', 'ですか', 'ますか', 'かな', 'かね']): return True
    if '？' in text or '?' in text: return True
    for p in [r'聞いていい', r'教えて(ください|くれ|もら)', r'どう(いう|な|やって)',
              r'いくら', r'何歳', r'いつから', r'どこで', r'そうです[かね]', r'なるほど']:
        if re.search(p, text): return True
    return False

def is_short_fragment(text):
    text = text.strip()
    if len(text) <= 3: return True
    if re.match(r'^[うんはいええああそうへえふーん]+[。、！？…]*$', text): return True
    return text in ['うん', 'はい', 'ええ', 'そう', 'うんうん', 'そうそう']

def clean_text(text):
    text = re.sub(r'\[\s*(拍手|笑い|音楽|無音|不明|聞き取り困難)\s*\]', '', text)
    text = re.sub(r'〔[^〕]*〕', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\{[<>]\}', '', text)
    text = re.sub(r'\s+', '', text)
    text = re.sub(r'。。+', '。', text)
    text = re.sub(r'、、+', '、', text)
    text = text.strip()
    if text and text[-1] not in '。！？…、': text += '。'
    return text

def detect_topic(text):
    if any(kw in text for kw in ["年金","お金","受給","生活費","万円","貯金","収入","支給","保険料"]): return "pension"
    if any(kw in text for kw in ["病","痛","薬","健康","体調","医者","治療","介護","障害","認知","癌"]): return "health"
    if any(kw in text for kw in ["家族","子供","孫","主人","妻","夫","娘","息子","親","両親","兄弟"]): return "family"
    if any(kw in text for kw in ["施設","ホーム","入居","老人ホーム"]): return "facility"
    if any(kw in text for kw in ["食事","料理","買い物","掃除","洗濯","片付け"]): return "daily"
    if any(kw in text for kw in ["寂し","孤独","一人","話し相手","交流"]): return "loneliness"
    if any(kw in text for kw in ["仕事","働","職業","勤め","退職","現役","会社"]): return "work"
    if any(kw in text for kw in ["旅行","趣味","楽しみ","テレビ","散歩","運動"]): return "hobby"
    if any(kw in text for kw in ["亡くな","死","葬式","墓","看取","最後","お別れ"]): return "death"
    if any(kw in text for kw in ["昔","昔は","若い頃","戦後","昭和","平成","思い出"]): return "nostalgia"
    if any(kw in text for kw in ["スマホ","携帯","パソコン","ネット","機械","操作"]): return "technology"
    if any(kw in text for kw in ["感謝","ありがた","嬉し","幸せ","十分","満足"]): return "gratitude"
    if any(kw in text for kw in ["近所","隣","ご近所","町内","自治会"]): return "community"
    return "general"


# ─── V10改进：宽松提取策略 ───

def extract_elderly_utterances_v10(segments, video_type="interview"):
    """
    V10版：宽松合并 + 双窗口策略
    - interview型：跳过提问，2段即可合并（原来3段）
    - monologue型：2段合并（原来3段）
    - 返回utterances列表
    """
    utterances = []

    if video_type == "monologue":
        # 独白型：2段合并（更宽松）
        buffer = []
        for seg in segments:
            text = seg["text"].strip()
            if not text or is_short_fragment(text): continue
            buffer.append(text)
            if len(buffer) >= 2:  # ★ V10: 3→2
                merged = "".join(buffer)
                if len(merged) >= 12:  # ★ V10: 15→12 更宽松
                    utterances.append(merged)
                buffer = []
        if buffer:
            merged = "".join(buffer)
            if len(merged) >= 12: utterances.append(merged)
    else:
        # 采访型：跳过提问，2段合并
        buffer = []
        for seg in segments:
            text = seg["text"].strip()
            if not text or is_short_fragment(text): continue

            if is_question(text):
                if buffer:
                    merged = "".join(buffer)
                    if len(merged) >= 8:  # ★ V10: 10→8 更宽松
                        utterances.append(merged)
                    buffer = []
            else:
                buffer.append(text)
                if len(buffer) >= 2:  # ★ V10: 3→2
                    merged = "".join(buffer)
                    if len(merged) >= 12:  # ★ V10: 15→12
                        utterances.append(merged)
                    buffer = []

        if buffer:
            merged = "".join(buffer)
            if len(merged) >= 8: utterances.append(merged)

    return utterances


def build_conversations_v10(utterances, vid, info, start_idx):
    """
    V10版对话构建：
    - 双窗口策略（2段窗口 + 3段窗口同时产出）
    - 每段发言→更精准的话题匹配
    """
    if len(utterances) < 2: return []

    records = []
    # 策略A: 2段窗口（短对话）
    # 策略B: 3段窗口（长对话）
    all_windows = []

    for wsize in [2, 3]:
        if len(utterances) < wsize: continue
        for i in range(0, len(utterances) - wsize + 1, 1):  # stride=1 密集采样
            window = utterances[i:i + wsize]
            if len(window) >= 2:
                all_windows.append((wsize, window))

    # 去重：相同窗口内容只保留一次
    seen = set()
    unique_windows = []
    for wsize, window in all_windows:
        key = "|".join(w[:30] for w in window)
        if key not in seen:
            seen.add(key)
            unique_windows.append((wsize, window))

    for wsize, window in unique_windows:
        conversations = []

        # 30%概率加问候开头
        if random.random() < 0.3:
            conversations.append({"from": "human", "value": random.choice([
                "あのー、ちょっと話を聞いてほしいねん。",
                "おはよう。今日もよろしく頼むわ。",
                "こんにちは。ちょっと相談したいことがあってな…",
            ])})
            conversations.append({"from": "gpt", "value": random.choice([
                "はい、こんにちは！いつでもお話しくださいね。今日はどんなお話でしょうか？",
                "はい、おはようございます。どうぞゆっくりお話しください。",
                "こんにちは！お会いできて嬉しいです。どんなことでもお聞かせくださいね。",
            ])})

        for j, utt in enumerate(window):
            utt = clean_text(utt)
            if len(utt) < 6: continue

            topic = detect_topic(utt)
            human_text = make_elderly_speech(utt)

            if j < len(window) - 1:
                gpt_text = get_topic_response(topic, "acknowledgment")
            else:
                gpt_text = get_topic_response(topic, "closing")

            conversations.append({"from": "human", "value": human_text})
            conversations.append({"from": "gpt", "value": gpt_text})

        if len(conversations) < 4: continue

        # 修复连续同角色
        conversations = fix_alternation(conversations)
        if len(conversations) < 4: continue

        total_chars = sum(len(c["value"]) for c in conversations)
        if total_chars < 60: continue

        records.append({
            "id": f"whisper_v10_{vid}_{start_idx + len(records):04d}",
            "conversations": conversations,
            "source": "real_elderly_whisper",
            "quality": "real_transcribed_v10",
            "language": "ja",
            "country_code": "JP",
            "scenario": f"interview: {info.get('title', 'unknown')}",
            "video_id": vid,
            "num_turns": len(conversations),
            "total_chars": total_chars,
        })

    return records


# ─── 简版话题回复（后续V10脚本会替换为更好的回复） ───

TOPIC_RESPONSES_SIMPLE = {
    "pension": {
        "acknowledgment": ["なるほど、年金のことを詳しく教えてくださってありがとうございます。","年金の実情をお聞かせいただき、ありがとうございます。"],
        "closing": ["年金のことは本当に大切ですね。何かお手伝いできることがあれば、いつでもおっしゃってくださいね。"],
    },
    "health": {
        "acknowledgment": ["なるほど、健康状態について教えてくださってありがとうございます。","お体のこと、詳しくお話しいただきありがとうございます。"],
        "closing": ["お体を大切になさってくださいね。何かありましたら、すぐにご連絡ください。"],
    },
    "family": {
        "acknowledgment": ["ご家族のお話を聞かせてくださってありがとうございます。","なるほど。家族の絆は本当に大切ですよね。"],
        "closing": ["ご家族のことを大切に思われていて、素晴らしいですね。またお話し聞かせてください。"],
    },
    "facility": {
        "acknowledgment": ["施設についてのお考えを教えてくださってありがとうございます。","なるほど、施設のことを真剣に考えていらっしゃるんですね。"],
        "closing": ["施設のことは慎重に考えたいですね。一緒に情報を集めていきましょう。"],
    },
    "daily": {
        "acknowledgment": ["日々の暮らしのことを教えてくださってありがとうございます。","なるほど、毎日の生活リズムができているんですね。"],
        "closing": ["毎日の暮らしの中で、お困りのことはありますか？何でもお手伝いしますよ。"],
    },
    "loneliness": {
        "acknowledgment": ["一人暮らしのこと、お話しいただきありがとうございます。","お気持ち、よくわかります。お話ししてくださってありがとうございます。"],
        "closing": ["いつでもお話し相手になりますから、寂しくなったら声をかけてくださいね。"],
    },
    "work": {
        "acknowledgment": ["そうでしたか、長年のお仕事のお話、とても興味深いです。","なるほど。素晴らしいキャリアをお持ちなんですね。"],
        "closing": ["素晴らしいご経歴をお持ちなんですね。もっとお話を聞かせてください。"],
    },
    "hobby": {
        "acknowledgment": ["それは素敵な趣味ですね！毎日の楽しみがあるのは、本当に素晴らしいことです。","趣味のお話を聞かせてくださってありがとうございます。"],
        "closing": ["日々の楽しみがあるのは本当に良いことです。趣味の時間を大切になさってくださいね。"],
    },
    "death": {
        "acknowledgment": ["そうでしたか…。大切な方を亡くされたお気持ち、お察しいたします。","お話しくださってありがとうございます。とても辛いご経験をされたんですね。"],
        "closing": ["今日は貴重なお話をありがとうございました。またいつでもお気持ちをお聞かせください。"],
    },
    "nostalgia": {
        "acknowledgment": ["昔のことを思い出されていたんですね。その頃のお話、もっと聞かせてください。","懐かしい思い出をシェアしてくださってありがとうございます。"],
        "closing": ["昔のお話を聞かせてくださって、とても嬉しかったです。また思い出話を聞かせてくださいね。"],
    },
    "technology": {
        "acknowledgment": ["新しい機器のことは戸惑いますよね。私もご一緒に覚えていきますから、焦らなくて大丈夫ですよ。","なるほど、機械の操作でお困りなんですね。一緒に少しずつ慣れていきましょう。"],
        "closing": ["機械のことは焦らずゆっくりで大丈夫です。いつでもご質問してくださいね。"],
    },
    "gratitude": {
        "acknowledgment": ["そうおっしゃっていただけると、とても嬉しいです。こちらこそ、いつもありがとうございます。","感謝のお気持ちを聞かせてくださってありがとうございます。"],
        "closing": ["今日も素敵なお話をありがとうございました。これからもよろしくお願いしますね。"],
    },
    "community": {
        "acknowledgment": ["ご近所のお話を聞かせてくださってありがとうございます。地域のつながりは大切ですよね。","なるほど、近所付き合いのことは色々ありますよね。"],
        "closing": ["地域とのつながりを大切にされていますね。これからも良いご近所付き合いが続くといいですね。"],
    },
    "general": {
        "acknowledgment": ["はい、なるほど。教えてくださってありがとうございます。","おっしゃる通りですね。参考になるお話をありがとうございます。"],
        "closing": ["今日もお話しできて嬉しかったです。またいつでも話しかけてくださいね。"],
    },
}

def get_topic_response(topic, intent):
    bank = TOPIC_RESPONSES_SIMPLE.get(topic, TOPIC_RESPONSES_SIMPLE["general"])
    options = bank.get(intent, bank.get("acknowledgment", ["はい、なるほど。"]))
    return random.choice(options)


def make_elderly_speech(text):
    if random.random() < 0.22 and len(text) > 10:
        fillers = ["まあ、", "あのー、", "ええとね、", "そうやなあ、"]
        f = random.choice(fillers)
        if random.random() < 0.5: text = f + text
    if random.random() < 0.10:  # ★ V10: 8%→10% 方言密度提升
        reps = [("だよね","やんな"),("だよ","やで"),("すごい","めっちゃ"),
                ("本当に","ほんまに"),("そうだ","せや"),("違う","ちゃう"),
                ("ダメ","あかん"),("ありがとう","おおきに")]
        for orig, dial in reps:
            if orig in text and random.random() < 0.3:
                text = text.replace(orig, dial, 1)
                break
    return text


def fix_alternation(conversations):
    if not conversations: return []
    fixed = []
    for c in conversations:
        if fixed and fixed[-1]["from"] == c["from"]:
            fixed[-1]["value"] = fixed[-1]["value"].rstrip("。！？…") + "。" + c["value"]
        else:
            fixed.append(c.copy())
    if len(fixed) >= 2:
        for i in range(1, len(fixed)):
            if fixed[i]["from"] == fixed[i-1]["from"]:
                bridge = {"from": "gpt" if fixed[i]["from"] == "human" else "human",
                          "value": "はい、なるほど。" if fixed[i]["from"] == "human" else "そうですか…"}
                fixed.insert(i, bridge)
                break
    return fixed


def quality_filter(record):
    convs = record.get("conversations", [])
    if len(convs) < 4: return False  # 至少2轮
    texts = [c["value"].strip() for c in convs]
    if any(len(t) < 3 for t in texts): return False
    if sum(len(t) for t in texts) < 60: return False
    roles = set(c["from"] for c in convs)
    if len(roles) < 2: return False
    for c in convs:
        if c["from"] == "human" and re.match(r'^[うんはいええああそうへえふーん]+[。、！？…]*$', c["value"]):
            return False
    return True


# ─── Main ───

def main():
    print("=" * 70)
    print("V10 从现有Whisper JSON中提取更多对话")
    print("=" * 70)

    all_new = []
    vid_stats = {}

    for vid, info in VIDEO_INFO.items():
        wp = REAL_DIR / f"{vid}_whisper.json"
        if not wp.exists():
            print(f"  {vid}: ❌ 找不到 {wp}")
            continue

        with open(wp, encoding="utf-8") as f:
            data = json.load(f)

        segments = data.get("segments", [])
        vtype = info.get("type", "interview")

        print(f"\n{vid} ({info['title'][:50]}...):")
        print(f"  总段数: {len(segments)}, 类型: {vtype}")

        # V10宽松提取
        utterances = extract_elderly_utterances_v10(segments, vtype)
        print(f"  V10提取发言: {len(utterances)}段")

        # 构建对话
        records = build_conversations_v10(utterances, vid, info, 0)
        print(f"  原始生成: {len(records)}条")

        # 质量过滤
        records = [r for r in records if quality_filter(r)]
        print(f"  过滤后: {len(records)}条")

        vid_stats[vid] = len(records)
        all_new.extend(records)

    print(f"\n{'=' * 70}")
    print(f"V10新提取总结")
    print(f"{'=' * 70}")
    print(f"  总新对话: {len(all_new)}条")

    # 与现有数据去重（基于前4条消息的hash）
    existing_hashes = set()
    for split_name in ["train", "val", "test"]:
        fp = Path("training_data") / f"{split_name}.jsonl"
        if fp.exists():
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line.strip())
                        h = "|".join(c["value"][:40] for c in r.get("conversations", [])[:4])
                        existing_hashes.add(h)
                    except: pass

    deduped = []
    for r in all_new:
        h = "|".join(c["value"][:40] for c in r.get("conversations", [])[:4])
        if h not in existing_hashes:
            existing_hashes.add(h)
            deduped.append(r)

    print(f"  去重后: {len(deduped)}条（排除了与V9.1重复的）")

    # 统计
    if deduped:
        avg_t = sum(len(r["conversations"]) for r in deduped) / len(deduped)
        avg_c = sum(sum(len(c["value"]) for c in r["conversations"]) for r in deduped) / len(deduped)
        print(f"  平均轮次: {avg_t:.1f}")
        print(f"  平均字符: {avg_c:.0f}")

        topic_counts = Counter()
        for r in deduped:
            all_text = " ".join(c["value"] for c in r["conversations"])
            topic_counts[detect_topic(all_text)] += 1
        print(f"  话题分布:")
        for t, c in topic_counts.most_common():
            print(f"    {t}: {c} ({c/len(deduped)*100:.1f}%)")

    # 保存
    outpath = Path("training_data/v10_new_whisper.jsonl")
    with open(outpath, "w", encoding="utf-8") as f:
        for r in deduped:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n  已保存: {outpath} ({len(deduped)}条)")
    print("✅ V10 Whisper提取完成!")


if __name__ == "__main__":
    main()
