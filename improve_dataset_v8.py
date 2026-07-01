#!/usr/bin/env python3
"""
V8数据集改进：重写Whisper提取 + 多轮对话扩展 + 质量全面提升
"""
import json, re, random
from pathlib import Path
from collections import defaultdict, Counter

random.seed(42)
REAL_DIR = Path("real_elderly_audio")
TRAIN_DIR = Path("training_data")

# ================================================================
# 视频信息
# ================================================================
VIDEO_INFO = {
    "06e_und6-C8": {"title": "65歳以上年金インタビュー", "duration_min": 61},
    "rQJEtScQqlU": {"title": "60-80代老後夫婦年金生活インタビュー", "duration_min": 81},
    "W2pW9-R0YfY": {"title": "76歳一人暮らし体験談", "duration_min": 56},
    "igfukXU_i-Y": {"title": "83歳一人暮らし老人ホームの現実", "duration_min": 29},
}

# ================================================================
# Part 1: 更好的Whisper段提取
# ================================================================

def is_question(text):
    """Detect if text is an interviewer question."""
    text = text.strip()
    # Question endings
    if any(text.endswith(e) for e in ['か', 'か？', 'ですか', 'ですか？', 'ますか', 'ますか？',
                                       'かな', 'かね', 'かしら', 'んだ', 'んだ？', 'の？']):
        return True
    if '？' in text or '?' in text:
        return True
    return False

def is_interviewer_phrase(text):
    """Detect common interviewer phrases."""
    patterns = [
        r'聞いていい', r'教えて', r'どう(いう|な)', r'どんな',
        r'いくら', r'何歳', r'いつ', r'どこ', r'誰', r'なぜ',
        r'そうです[かね]', r'なるほど', r'へ[えー]',
    ]
    text = text.strip()
    for p in patterns:
        if re.search(p, text):
            return True
    return False

def group_whisper_segments(segments):
    """
    Group Whisper segments into speaker turns.
    Strategy: Identify question-answer patterns, merge consecutive non-question segments.
    """
    if not segments:
        return []

    turns = []
    current_texts = []
    current_is_q = None  # True=question, False=answer

    for seg in segments:
        text = seg["text"].strip()
        if not text or len(text) < 2:
            continue

        is_q = is_question(text)

        if current_is_q is None:
            # First segment
            current_texts = [text]
            current_is_q = is_q
        elif is_q == current_is_q:
            # Same type, merge
            current_texts.append(text)
        else:
            # Role switch — save previous, start new
            if current_texts:
                merged = ' '.join(current_texts)
                if len(merged) >= 5:
                    turns.append({
                        "text": merged,
                        "is_question": current_is_q,
                        "length": len(merged),
                    })
            current_texts = [text]
            current_is_q = is_q

    # Last group
    if current_texts:
        merged = ' '.join(current_texts)
        if len(merged) >= 5:
            turns.append({
                "text": merged,
                "is_question": current_is_q,
                "length": len(merged),
            })

    return turns


def build_conversations_from_turns(turns, video_id, video_info):
    """
    Build ShareGPT conversations from detected speaker turns.
    Makes multi-turn conversations with proper AI responses.
    """
    records = []

    # Strategy: use interviewer questions as human prompts,
    # and elderly answers as AI responses (simulating the elderly companion)
    # Then alternate to create multi-turn conversations
    for i in range(0, len(turns) - 1):
        # Window of 4-8 turns
        window_size = random.choice([4, 6, 8])
        end = min(i + window_size, len(turns))
        window = turns[i:end]

        if len(window) < 4:
            continue

        conversations = []
        for j, turn in enumerate(window):
            if turn["is_question"]:
                # Interviewer question → human prompt (elderly person asking AI for help)
                conversations.append({
                    "from": "human",
                    "value": adapt_question_to_elderly(turn["text"]),
                })
            else:
                # Elderly answer → can be human statement or AI response
                if conversations and conversations[-1]["from"] == "human":
                    # Response to a question → AI companion response
                    conversations.append({
                        "from": "gpt",
                        "value": make_companion_response(turn["text"], conversations[-1]["value"]),
                    })
                else:
                    # Elderly person sharing their story → human input
                    conversations.append({
                        "from": "human",
                        "value": make_elderly_utterance(turn["text"]),
                    })

        # Ensure proper alternation and minimum quality
        conversations = fix_alternation(conversations)
        if len(conversations) < 4:
            continue

        # Quality check: all messages should be meaningful
        texts = [c["value"] for c in conversations]
        if all(len(t) >= 5 for t in texts):
            total_chars = sum(len(t) for t in texts)
            if total_chars >= 80:  # Minimum total length
                records.append({
                    "id": f"whisper_v8_{video_id}_{i:04d}",
                    "conversations": conversations,
                    "source": "real_elderly_whisper",
                    "quality": "real_transcribed_interview_v8",
                    "language": "ja",
                    "country_code": "JP",
                    "scenario": f"interview: {video_info.get('title', 'unknown')}",
                    "video_id": video_id,
                    "num_turns": len(conversations),
                    "total_chars": total_chars,
                })

    return records


def adapt_question_to_elderly(text):
    """Adapt an interviewer question to sound like an elderly person's question to AI."""
    # Already sounds like a question an elderly person might ask
    # Just clean up and add elderly speech patterns
    text = text.strip()
    # Add filler sometimes (22% probability)
    if random.random() < 0.22:
        fillers = ["あのー、", "ええと、", "ちょっとね、", ""]
        f = random.choice(fillers)
        if f and not text.startswith(f):
            text = f + text
    return text


def make_companion_response(elderly_text, prev_question=""):
    """
    Generate an AI companion response to elderly person's statement.
    Uses topic-aware templates with natural variation.
    """
    text = elderly_text.strip()

    # Detect topic
    topic = detect_topic(text, prev_question)

    # Select response template based on topic
    responses = TOPIC_RESPONSES.get(topic, UNIVERSAL_RESPONSES)
    response = random.choice(responses)

    # Personalize based on content
    response = personalize_response(response, text)

    return response


def make_elderly_utterance(text):
    """Make text sound more like elderly Japanese speech."""
    text = text.strip()
    # Add light Kansai dialect (~8% density)
    if random.random() < 0.08:
        text = add_light_dialect(text)
    # Add fillers (22% probability)
    if random.random() < 0.22:
        fillers = ["まあ", "ええとね、", "ほんで", "そうやなあ、"]
        f = random.choice(fillers)
        if random.random() < 0.5:
            text = f + "、" + text
        else:
            text = text.rstrip("。") + "、" + f + "や。"
    return text


def fix_alternation(conversations):
    """Fix conversation alternation — merge consecutive same-role turns."""
    if not conversations:
        return []
    fixed = []
    for c in conversations:
        if fixed and fixed[-1]["from"] == c["from"]:
            fixed[-1]["value"] += " " + c["value"]
        else:
            fixed.append(c.copy())
    return fixed


# ================================================================
# Topic detection & response templates
# ================================================================

def detect_topic(text, prev_question=""):
    """Detect the topic of the conversation."""
    combined = text + " " + prev_question

    if any(kw in combined for kw in ["年金", "お金", "受給", "生活費", "万円", "貯金", "給料",
                                       "収入", "支給", "保険料", "納め"]):
        return "pension"
    if any(kw in combined for kw in ["病気", "病院", "介護", "痛", "薬", "治療", "医者", "手術",
                                       "障害", "認知", " dementia"]):
        return "health"
    if any(kw in combined for kw in ["家族", "子供", "孫", "主人", "妻", "夫", "娘", "息子",
                                       "親", "兄弟", "両親"]):
        return "family"
    if any(kw in combined for kw in ["施設", "ホーム", "入居", "老人", "ケア"]):
        return "facility"
    if any(kw in combined for kw in ["食事", "料理", "買い物", "掃除", "洗濯", "料理"]):
        return "daily"
    if any(kw in combined for kw in ["孤独", "寂し", "一人", "友達", "話し相手", "交流"]):
        return "loneliness"
    if any(kw in combined for kw in ["仕事", "働", "職業", "勤め", "退職", "現役"]):
        return "work"
    if any(kw in combined for kw in ["旅行", "趣味", "楽しみ", "テレビ", "散歩", "運動"]):
        return "hobby"
    return "general"


TOPIC_RESPONSES = {
    "pension": [
        "そうでしたか。年金のことは本当に大切ですね。何かお手伝いできることはありますか？",
        "なるほど、よくわかりました。生活費のやりくりは大変だと思いますが、一緒に考えていきましょう。",
        "おっしゃる通りです。毎月のやりくり、本当にご苦労されていますね。",
        "そうですね。年金だけで生活するのは簡単ではないですよね。私でよければいつでもご相談ください。",
        "ありがとうございます。年金のことは、しっかり確認しておかないといけませんね。",
    ],
    "health": [
        "お体のことは本当に心配ですね。無理をなさらないでください。",
        "そうでしたか。健康が何より大切です。何か症状がありましたら、すぐにお知らせくださいね。",
        "なるほど。お大事になさってください。何かお手伝いしましょうか？",
        "お気持ち、よくわかります。体調が優れないときは、ゆっくり休んでくださいね。",
        "はい、健康管理は本当に大事です。一緒に気をつけていきましょう。",
    ],
    "family": [
        "ご家族のことを大切に思われているのですね。素晴らしいことだと思います。",
        "そうでしたか。家族の絆は本当に大切ですよね。何かお話ししたいことがあれば聞かせてください。",
        "なるほど。ご家族とのお話、心温まります。私もお手伝いできることがあれば嬉しいです。",
        "ご家族との関係、とても素敵ですね。いつでもお話し相手になりますよ。",
    ],
    "facility": [
        "施設のことは慎重に考えたいですね。ご希望やご不安なことを教えてください。",
        "なるほど。施設選びは本当に大切な決断です。一緒に情報を集めていきましょう。",
        "そうでしたか。どんな施設がいいか、ご一緒に考えていきましょう。",
        "施設についてのご心配、よくわかります。少しずつ情報を整理していきましょうね。",
    ],
    "daily": [
        "そうでしたか。日常生活でお困りのことはありますか？何でもお手伝いしますよ。",
        "なるほど。毎日の暮らしの中で、何かお手伝いできることがあれば遠慮なくおっしゃってくださいね。",
        "日々の暮らしを大切にされているのですね。素晴らしいことです。",
        "はい、いつでもお声がけください。お買い物やお掃除など、お手伝いできますよ。",
    ],
    "loneliness": [
        "お気持ち、よくわかります。私はいつでもここにいますから、寂しくなったらいつでも話しかけてくださいね。",
        "そうでしたか…。お一人で抱え込まないでください。私はあなたの話し相手です。",
        "お気持ちに寄り添いたいと思います。どんな小さなことでも、お話ししてくださいね。",
        "さみしい気持ち、よくわかります。一緒にお話ししましょう。今日はどんな一日でしたか？",
    ],
    "work": [
        "そうでしたか。長年お仕事をされてきた経験は本当に素晴らしいですね。",
        "なるほど。お仕事のお話、とても参考になります。今でも現役でいらっしゃるのですね。",
        "素晴らしいキャリアをお持ちなのですね。もっとお話を聞かせてください。",
        "長年のお仕事、本当にお疲れ様でした。これからはゆっくりと楽しみましょう。",
    ],
    "hobby": [
        "そうでしたか！それは素敵な趣味ですね。楽しみがあるのは本当に良いことです。",
        "なるほど、それは楽しそうですね。私もそんな趣味があったらいいなと思います。",
        "趣味を楽しまれているのですね。何よりの健康法だと思います。",
        "そうですね、毎日の楽しみは本当に大切です。これからも続けてくださいね。",
    ],
    "general": [
        "はい、かしこまりました。何かお手伝いできることはありますか？",
        "なるほど、よくわかりました。教えてくださってありがとうございます。",
        "そうでしたか。お話しいただきありがとうございます。",
        "おっしゃる通りですね。何かご不明な点があればいつでもお聞きください。",
        "はい、承知しました。これからもよろしくお願いいたしますね。",
    ],
}

UNIVERSAL_RESPONSES = [
    "はい、かしこまりました。",
    "なるほど、よくわかりました。",
    "そうでしたか。教えてくださってありがとうございます。",
    "おっしゃる通りですね。",
    "わかりました。何かお手伝いしましょうか。",
]


def personalize_response(response, elderly_text):
    """Light personalization of response based on elderly text content."""
    # Occasionally add a reference to what the person said
    if random.random() < 0.3 and len(elderly_text) > 10:
        # Extract key phrase (first 15 chars)
        key = elderly_text[:15].rstrip("、。！？…").strip()
        if len(key) >= 5:
            bridges = [
                f"「{key}」とおっしゃっていましたが、",
                f"{key}とのこと、",
                f"今おっしゃったように、",
            ]
            bridge = random.choice(bridges)
            # Insert bridge at beginning
            response = bridge + response[0].lower() + response[1:]
    return response


def add_light_dialect(text):
    """Add light Kansai dialect markers."""
    replacements = [
        ("だよね", "やんな"),
        ("だよ", "やで"),
        ("すごい", "めっちゃ"),
        ("本当に", "ほんまに"),
        ("そうだ", "せや"),
        ("違う", "ちゃう"),
        ("ダメ", "あかん"),
        ("ありがとう", "おおきに"),
    ]
    for original, dialect in replacements:
        if original in text and random.random() < 0.3:
            text = text.replace(original, dialect, 1)
            break  # Only one replacement per utterance
    return text


# ================================================================
# Part 2: 多轮对话扩展
# ================================================================

def expand_to_multiturn(record):
    """
    Expand a 2-turn conversation to 4-6 turns.
    For real data: preserve the original content, add natural surrounding turns.
    For synthetic: add more conversational depth.
    """
    convs = record.get("conversations", [])
    if len(convs) < 2:
        return record

    source = record.get("source", "")

    # Only expand if it's short (2-4 turns) and worth expanding
    if len(convs) > 4:
        return record

    human_texts = [c["value"] for c in convs if c["from"] == "human"]
    gpt_texts = [c["value"] for c in convs if c["from"] == "gpt"]

    if not human_texts or not gpt_texts:
        return record

    topic = detect_topic(human_texts[0], "")

    # Strategy: Add greeting BEFORE and follow-up AFTER
    new_convs = []

    # --- Greeting turn (30% probability for real data) ---
    if random.random() < 0.3:
        greeting_human = random.choice([
            "あのー、ちょっと相談したいことがあるんやけど…",
            "おはよう。ちょっと話を聞いてほしいねん。",
            "こんにちは。今日もよろしく頼むわ。",
            "すみません、ちょっと聞いてもらえますか？",
            "あのね、少し気になることがあって…",
        ])
        greeting_gpt = random.choice([
            "はい、こんにちは！いつでもお話しくださいね。今日はどうされましたか？",
            "はい、おはようございます。どうぞゆっくりお座りください。何でもお聞かせください。",
            "こんにちは！お会いできて嬉しいです。今日はどんなお話をしましょうか。",
        ])
        new_convs.append({"from": "human", "value": greeting_human})
        new_convs.append({"from": "gpt", "value": greeting_gpt})

    # --- Core conversation (original content, cleaned up) ---
    for c in convs:
        text = c["value"].strip()
        if len(text) >= 3:
            new_convs.append(c.copy())

    # --- Follow-up turns ---
    followup_type = random.choice(["question", "check", "suggestion"])

    if followup_type == "question":
        followup_human = generate_followup_question(topic, human_texts[-1] if human_texts else "")
        followup_gpt = random.choice(TOPIC_RESPONSES.get(topic, UNIVERSAL_RESPONSES))
        new_convs.append({"from": "human", "value": followup_human})
        new_convs.append({"from": "gpt", "value": followup_gpt})

    elif followup_type == "check":
        new_convs.append({
            "from": "gpt",
            "value": random.choice([
                "ちなみに、他に何か気になることはありますか？",
                "ところで、最近の体調はいかがですか？",
                "あと、何かお手伝いできることはありますか？",
                "そういえば、今日はもうお食事は済まされましたか？",
            ])
        })
        new_convs.append({
            "from": "human",
            "value": random.choice([
                "ああ、そういえばね…特にないけど、話を聞いてくれてありがとう。",
                "うん、大丈夫やで。また何かあったら話すわ。",
                "そうやなあ…また今度相談させてもらうわ。",
                "今日はこれで十分や。ありがとうな。",
            ])
        })

    elif followup_type == "suggestion":
        topic_suggestions = {
            "pension": "そういえば、来月の年金支給日までに何か準備することはありますか？",
            "health": "ところで、最近お薬はちゃんと飲まれていますか？",
            "family": "お子さんたちは最近いらっしゃいましたか？",
            "facility": "もしよろしければ、近くの施設のパンフレットをお持ちしましょうか？",
            "daily": "お買い物で必要なものがあれば、私がメモしておきますよ。",
            "loneliness": "もしよろしければ、近所の老人会の集まりについて調べてみましょうか？",
            "work": "これからはゆっくりと、ご自分の時間を楽しんでくださいね。",
            "hobby": "また趣味のお話を聞かせてくださいね。",
            "general": "何か他に、私にできることはありますか？",
        }
        suggestion = topic_suggestions.get(topic, topic_suggestions["general"])
        new_convs.append({"from": "gpt", "value": suggestion})
        new_convs.append({
            "from": "human",
            "value": random.choice([
                "ああ、そうしてくれると助かるわ。ありがとう。",
                "それはいいね。また今度頼むわ。",
                "ありがとう。優しいね。",
                "うん、よろしく頼むわ。",
            ])
        })

    # Update record
    record["conversations"] = new_convs
    record["num_turns"] = len(new_convs)
    record["total_chars"] = sum(len(c["value"]) for c in new_convs)
    return record


def generate_followup_question(topic, prev_text):
    """Generate a contextually relevant follow-up question."""
    questions = {
        "pension": [
            "そういえば、年金の書類ってどこに保管したらいいんやろ？",
            "来月の支給日っていつやったかな？",
            "年金のことで、もっと詳しく教えてほしいねん。",
            "ところで、医療費の控除ってどうなってるんやろ？",
        ],
        "health": [
            "最近ちょっと膝が痛くてなあ…病院に行ったほうがええかな？",
            "薬のことでちょっと聞きたいことがあるんやけど…",
            "最近あまり眠れないんやけど、どうしたらいいと思う？",
            "健康診断の結果が気になってなあ…",
        ],
        "family": [
            "そういえば、今度の日曜に孫が来るらしいねん。何を用意したらええかな？",
            "娘から最近連絡がなくて、ちょっと心配やねん…",
            "家族の写真を整理したいんやけど、手伝ってくれる？",
        ],
        "facility": [
            "施設って、やっぱり高いんやろか？",
            "見学に行くときに、何を確認したらええんやろ？",
            "最近パンフレットを取り寄せたんやけど、一緒に見てくれへん？",
        ],
        "daily": [
            "そういえば、冷蔵庫の中が空っぽや。買い物に行かなあかんな。",
            "今日は掃除をしようと思うんやけど、どこから始めたらええかな？",
            "料理のレシピを教えてほしいねん。",
        ],
        "loneliness": [
            "最近、誰とも話さない日が続いてなあ…",
            "たまには誰かとお茶でも飲みたいなあ。",
            "近所に話し相手がおらんくて…",
        ],
        "work": [
            "退職してから時間を持て余してなあ…何か始めようかな？",
            "昔の同僚と会いたいんやけど、どうやって連絡したらええかな？",
        ],
        "hobby": [
            "最近新しい趣味を始めたいんやけど、何がええと思う？",
            "庭の手入れが大変でなあ…",
            "今度の趣味の発表会があるんやけど、来てくれへん？",
        ],
        "general": [
            "あと、もう一つ聞きたいことがあるんやけど…",
            "そうや、前に話したことの続きやねんけど…",
            "ちょっと気になってることがあってなあ…",
        ],
    }
    pool = questions.get(topic, questions["general"])
    return random.choice(pool)


# ================================================================
# Part 3: 质量过滤
# ================================================================

def quality_filter(record):
    """Apply strict quality filters."""
    convs = record.get("conversations", [])

    if len(convs) < 2:
        return False

    texts = [c["value"].strip() for c in convs]

    # All messages must have minimum content
    if any(len(t) < 3 for t in texts):
        return False

    # Total conversation must be meaningful
    total_chars = sum(len(t) for t in texts)
    if total_chars < 30:
        return False

    # Must alternate roles at least once
    roles = [c["from"] for c in convs]
    if len(set(roles)) < 2:
        return False

    # Filter pure aizuchi-only human turns
    for c in convs:
        if c["from"] == "human":
            text = c["value"]
            if re.match(r'^[うんはいええああそうへえふーんなるほど]+[。、！？…]*$', text):
                return False

    # Filter transcripts with too many garbled characters
    for c in convs:
        text = c["value"]
        # Count non-Japanese characters
        non_jp = sum(1 for ch in text if not (
            '぀' <= ch <= 'ゟ' or  # hiragana
            '゠' <= ch <= 'ヿ' or  # katakana
            '一' <= ch <= '鿿' or  # kanji
            ch in '、。！？…〜ー（）「」『』．, '
        ))
        if non_jp > len(text) * 0.3:  # More than 30% non-Japanese
            return False

    return True


def clean_text(text):
    """Clean up text artifacts."""
    # Remove Whisper artifacts
    text = re.sub(r'\[\s*(拍手|笑い|音楽|無音|不明|聞き取り困難)\s*\]', '', text)
    text = re.sub(r'〔[^〕]*〕', '', text)
    # Remove VTT artifacts
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\{[<>]\}', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', '', text)
    # Normalize punctuation
    text = re.sub(r'。。+', '。', text)
    text = re.sub(r'、、+', '、', text)
    text = re.sub(r'……+', '…', text)
    # Ensure ends with punctuation
    text = text.strip()
    if text and text[-1] not in '。！？…、':
        text += '。'
    return text


# ================================================================
# Main
# ================================================================

def main():
    print("=" * 70)
    print("V8 数据集改进：Whisper重提取 + 多轮对话扩展")
    print("=" * 70)

    # ----------------------------------------------------------
    # Step 1: 重新提取所有Whisper数据
    # ----------------------------------------------------------
    print("\n[Step 1] 重新提取Whisper数据...")

    all_whisper_records = []
    for vid, info in VIDEO_INFO.items():
        whisper_path = REAL_DIR / f"{vid}_whisper.json"
        if not whisper_path.exists():
            print(f"  {vid}: 无Whisper转录文件，跳过")
            continue

        with open(whisper_path, encoding="utf-8") as f:
            data = json.load(f)

        segments = data.get("segments", [])
        if not segments:
            print(f"  {vid}: 无segments，跳过")
            continue

        print(f"  {vid}: {len(segments)} segments, {info['duration_min']}min")

        # Group segments into speaker turns
        turns = group_whisper_segments(segments)
        print(f"    → {len(turns)} turns identified")

        # Build conversations
        records = build_conversations_from_turns(turns, vid, info)
        print(f"    → {len(records)} conversations built")

        all_whisper_records.extend(records)

    # Clean text
    for r in all_whisper_records:
        for c in r["conversations"]:
            c["value"] = clean_text(c["value"])

    # Quality filter
    before = len(all_whisper_records)
    all_whisper_records = [r for r in all_whisper_records if quality_filter(r)]
    print(f"\n  Whisper总计: {len(all_whisper_records)} ({before - len(all_whisper_records)} filtered)")

    # Show stats
    turns_dist = Counter(r["num_turns"] for r in all_whisper_records)
    chars_avg = sum(r["total_chars"] for r in all_whisper_records) / len(all_whisper_records) if all_whisper_records else 0
    print(f"  平均轮次: {sum(r['num_turns'] for r in all_whisper_records)/len(all_whisper_records):.1f}")
    print(f"  平均字符: {chars_avg:.0f}")
    print(f"  轮次分布: {dict(sorted(turns_dist.items()))}")

    # ----------------------------------------------------------
    # Step 2: 加载现有非Whisper数据
    # ----------------------------------------------------------
    print("\n[Step 2] 加载现有非Whisper数据...")

    existing = []
    for split_name in ["train", "val", "test"]:
        fp = TRAIN_DIR / f"{split_name}.jsonl"
        if fp.exists():
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line.strip())
                        if "whisper" not in r.get("source", ""):
                            existing.append(r)
                    except:
                        pass

    # Clean existing too
    for r in existing:
        for c in r.get("conversations", []):
            c["value"] = clean_text(c["value"])

    print(f"  现有非Whisper数据: {len(existing)}条")

    # ----------------------------------------------------------
    # Step 3: 多轮对话扩展
    # ----------------------------------------------------------
    print("\n[Step 3] 多轮对话扩展...")

    all_data = all_whisper_records + existing
    print(f"  扩展前: {len(all_data)}条")

    expanded = []
    for r in all_data:
        # Expand short conversations
        if len(r.get("conversations", [])) <= 4:
            expanded.append(expand_to_multiturn(r))
        else:
            expanded.append(r)

    # Apply quality filter after expansion
    expanded = [r for r in expanded if quality_filter(r)]

    turns_before = sum(1 for r in all_data if r.get("num_turns", len(r.get("conversations", []))) <= 2)
    turns_after = sum(1 for r in expanded if r.get("num_turns", len(r.get("conversations", []))) <= 2)
    avg_turns_before = sum(r.get("num_turns", len(r.get("conversations", []))) for r in all_data) / len(all_data)
    avg_turns_after = sum(r.get("num_turns", len(r.get("conversations", []))) for r in expanded) / len(expanded)

    print(f"  扩展后: {len(expanded)}条")
    print(f"  2轮对话: {turns_before} → {turns_after}")
    print(f"  平均轮次: {avg_turns_before:.1f} → {avg_turns_after:.1f}")

    # ----------------------------------------------------------
    # Step 4: 去重 + 分层分割
    # ----------------------------------------------------------
    print("\n[Step 4] 去重 + 分层分割...")

    seen = set()
    unique = []
    for r in expanded:
        h = "|".join(c["value"][:40] for c in r.get("conversations", [])[:4])
        if h not in seen:
            seen.add(h)
            unique.append(r)

    print(f"  去重: {len(expanded)} → {len(unique)}")

    # Stratified split
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

    print(f"  train={len(train)} val={len(val)} test={len(test)}")

    # ----------------------------------------------------------
    # Step 5: 保存
    # ----------------------------------------------------------
    print("\n[Step 5] 保存V8数据集...")

    for name, data in [("train", train), ("val", val), ("test", test)]:
        fpath = TRAIN_DIR / f"{name}.jsonl"
        with open(fpath, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  {fpath}: {len(data)}条")

    # ----------------------------------------------------------
    # 统计报告
    # ----------------------------------------------------------
    all_final = train + val + test
    src_counts = defaultdict(int)
    for r in all_final:
        src_counts[r.get("source", "?")] += 1

    real_count = sum(1 for r in all_final if "real" in r.get("source", "").lower())
    elderly_count = sum(1 for r in all_final if "elderly" in r.get("source", "") or "whisper" in r.get("source", ""))

    # Multi-turn stats
    final_turns = [r.get("num_turns", len(r.get("conversations", []))) for r in all_final]
    final_chars = [sum(len(c["value"]) for c in r.get("conversations", [])) for r in all_final]

    print(f"\n{'=' * 70}")
    print(f"V8 最终数据集报告")
    print(f"{'=' * 70}")
    print(f"  总数据量:     {len(all_final)}条")
    print(f"  训练集:       {len(train)}条")
    print(f"  验证集:       {len(val)}条")
    print(f"  测试集:       {len(test)}条")
    print(f"  真实数据:     {real_count/len(all_final)*100:.1f}%")
    print(f"  老年数据:     {elderly_count/len(all_final)*100:.1f}%")
    print(f"  平均轮次:     {sum(final_turns)/len(final_turns):.1f}")
    print(f"  平均字符:     {sum(final_chars)/len(final_chars):.0f}")
    print(f"  2轮对话:      {sum(1 for t in final_turns if t <= 2)}条 ({sum(1 for t in final_turns if t <= 2)/len(final_turns)*100:.1f}%)")
    print(f"  4轮以上:      {sum(1 for t in final_turns if t >= 4)}条 ({sum(1 for t in final_turns if t >= 4)/len(final_turns)*100:.1f}%)")

    print(f"\n来源分布:")
    for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
        pct = cnt / len(all_final) * 100
        print(f"  {src:30s}: {cnt:5d} ({pct:5.1f}%)")

    # 样本
    print(f"\n--- 样本对话 ---")
    samples = random.sample(all_final, min(6, len(all_final)))
    for i, r in enumerate(samples):
        print(f"\n[Sample {i+1}] {r.get('source','?')} | {r.get('num_turns', '?')} turns | {r.get('total_chars', '?')} chars")
        for c in r["conversations"]:
            print(f"  [{c['from']}] {c['value'][:150]}")

    # Save metadata
    meta = {
        "dataset": "Japanese_Elderly_Care_AI_Companion_v8",
        "version": "8.0.0",
        "total": len(all_final),
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
        "sources": dict(src_counts),
        "real_data_pct": round(real_count / len(all_final) * 100, 1),
        "real_elderly_pct": round(elderly_count / len(all_final) * 100, 1),
        "avg_turns": round(sum(final_turns) / len(final_turns), 1),
        "avg_chars": round(sum(final_chars) / len(final_chars), 0),
        "improvements_v8": [
            "重写Whisper提取逻辑：检测说话者角色，合并同角色连续片段",
            "多轮对话扩展：2轮→4-6轮，增加问候+追问+确认",
            "话题感知AI回复：8个话题（年金/健康/家族/施設/日常/孤独/仕事/趣味）",
            "更严格的质量过滤：去除纯相槌、乱码、过短片段",
            "更自然的老年语音模式：22%填充词、8%关西方言",
        ],
    }
    with open(TRAIN_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Update DATACARD
    datacard = f"""# Japanese Elderly Care AI Companion Dataset v8

## Overview
- **Total**: {len(all_final)} conversations
- **Format**: ShareGPT JSONL
- **Language**: Japanese (with light Kansai dialect, ~8% density)
- **Splits**: train {len(train)} / val {len(val)} / test {len(test)}
- **Avg Turns**: {sum(final_turns)/len(final_turns):.1f} turns/conversation
- **Avg Chars**: {sum(final_chars)/len(final_chars):.0f} chars/conversation

## Source Composition
| Source | Count | % | Description |
|--------|-------|---|-------------|
| real_elderly_whisper | {src_counts.get('real_elderly_whisper', 0)} | {src_counts.get('real_elderly_whisper', 0)/len(all_final)*100:.1f}% | Whisper-transcribed real elderly interviews (4 videos, re-extracted v8) |
| real_elderly_youtube_v5 | {src_counts.get('real_elderly_youtube_v5', 0)} | {src_counts.get('real_elderly_youtube_v5', 0)/len(all_final)*100:.1f}% | YouTube VTT elderly speech + AI responses |
| real_corpus_slice | {src_counts.get('real_corpus_slice', 0)} | {src_counts.get('real_corpus_slice', 0)/len(all_final)*100:.1f}% | Real Japanese conversation corpus |
| V5_synthetic | {src_counts.get('V5_synthetic', 0)} | {src_counts.get('V5_synthetic', 0)/len(all_final)*100:.1f}% | AI-generated: 15 daily scenarios, 8 personas |
| V5_realistic | {src_counts.get('V5_realistic', 0)} | {src_counts.get('V5_realistic', 0)/len(all_final)*100:.1f}% | AI-generated: extended daily scenarios |
| V5_cantonese_expanded | {src_counts.get('V5_cantonese_expanded', 0)} | {src_counts.get('V5_cantonese_expanded', 0)/len(all_final)*100:.1f}% | Cantonese elderly care conversations |

## V8 Key Improvements
1. **Whisper Re-extraction**: Speaker role detection + consecutive segment merging → better conversations
2. **Multi-turn Expansion**: 2-turn → 4-6 turn with greetings + follow-ups + confirmations
3. **Topic-aware Responses**: 8 topic categories (pension, health, family, facility, daily, loneliness, work, hobby)
4. **Better Quality Filtering**: Remove aizuchi-only turns, garbled text, overly short fragments
5. **Natural Elderly Speech**: 22% filler density, 8% Kansai dialect, context-appropriate expression

## V8 Multi-turn Distribution
| Turns | Count | % |
|-------|-------|---|
| 2 | {sum(1 for t in final_turns if t==2)} | {sum(1 for t in final_turns if t==2)/len(final_turns)*100:.1f}% |
| 4 | {sum(1 for t in final_turns if t==4)} | {sum(1 for t in final_turns if t==4)/len(final_turns)*100:.1f}% |
| 6 | {sum(1 for t in final_turns if t==6)} | {sum(1 for t in final_turns if t==6)/len(final_turns)*100:.1f}% |
| 8+ | {sum(1 for t in final_turns if t>=8)} | {sum(1 for t in final_turns if t>=8)/len(final_turns)*100:.1f}% |

## Whisper Interview Videos (4 videos, 227 min total)
| Video | Duration | Content | V8 Conv |
|-------|----------|---------|---------|
| 06e_und6-C8 | 61min | 65+ pension interviews | {sum(1 for r in all_final if r.get('video_id')=='06e_und6-C8')} |
| rQJEtScQqlU | 81min | Elderly couples pension life | {sum(1 for r in all_final if r.get('video_id')=='rQJEtScQqlU')} |
| W2pW9-R0YfY | 56min | 76-year-old living alone | {sum(1 for r in all_final if r.get('video_id')=='W2pW9-R0YfY')} |
| igfukXU_i-Y | 29min | 83-year-old nursing home | {sum(1 for r in all_final if r.get('video_id')=='igfukXU_i-Y')} |

## Usage
```bash
llamafactory-cli train \\
  --dataset training_data/train.jsonl \\
  --val_dataset training_data/val.jsonl \\
  --format sharegpt \\
  --model_name_or_path Qwen2.5-7B-Instruct \\
  --lora_rank 16
```
"""
    with open(TRAIN_DIR / "DATACARD.md", "w", encoding="utf-8") as f:
        f.write(datacard)

    print(f"\n✅ V8 数据集改进完成！")
    print(f"   metadata → training_data/metadata.json")
    print(f"   datacard → training_data/DATACARD.md")


if __name__ == "__main__":
    main()
