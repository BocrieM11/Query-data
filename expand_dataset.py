#!/usr/bin/env python3
"""
数据集拡張パイプライン
1. V5生成: 方言濃度半減 + リアル老年話題
2. 粤语拡張: 36→80ラウンド
3. YouTube実データ再フォーマット
4. 全データ統合 → train/val/test
"""

import json, random, re, os
from pathlib import Path
from collections import defaultdict
from sklearn.model_selection import train_test_split

random.seed(42)
TRAIN_DIR = Path("training_data")
TRAIN_DIR.mkdir(exist_ok=True)

# ============================================================
# V5 ペルソナ定義 (方言 半減版)
# ============================================================
PERSONAS_V5 = {
    "A": {"name": "山下ハル", "age": 82, "origin": "京都", "type": "浓関西弁→軽減",
          "words": ["どす", "さかい", "ほんま", "おおきに"],
          "freq": 0.08},  # 以前25%→今8%
    "B": {"name": "田中セツ", "age": 85, "origin": "大阪", "type": "清晰干脆→軽方言",
          "words": ["了解", "基本や", "以上", "頼むで"],
          "freq": 0.05},
    "C": {"name": "佐藤キヨ", "age": 88, "origin": "和歌山", "type": "喋喋不休→軽方言",
          "words": ["なあ", "ほんま", "めっちゃ", "ぎょうさん"],
          "freq": 0.10},
    "D": {"name": "伊藤タケ", "age": 79, "origin": "神戸", "type": "标准语",
          "words": ["です", "ます", "ありがとう", "思います"],
          "freq": 0.0},
    "E": {"name": "加藤フミ", "age": 91, "origin": "奈良", "type": "温和絮叨→軽方言",
          "words": ["ねえ", "ありがとう", "ごめんね", "〜やろか"],
          "freq": 0.03},
    "F": {"name": "村田カツ", "age": 83, "origin": "大阪", "type": "急躁→中方言",
          "words": ["はよ", "あかん", "なんでや", "もう"],
          "freq": 0.08},
    "G": {"name": "清水サダ", "age": 86, "origin": "京都", "type": "怀旧少言→低方言",
          "words": ["…", "昔", "思い出", "ありがとう"],
          "freq": 0.02},
    "H": {"name": "木村ケン", "age": 80, "origin": "兵庫", "type": "沉默寡言→低方言",
          "words": ["…", "うん", "そうか", "助かった"],
          "freq": 0.02},
}

# 新シナリオ: リアル老年日常 (YouTubeから学んだ平凡な話題)
NEW_SCENARIOS = [
    ("お湯を沸かす朝", ["やかん", "ガス", "火", "お茶", "ポット"]),
    ("洗濯物を干す", ["ハンガー", "風", "日差し", "乾く", "取り込む"]),
    ("冷蔵庫の整理", ["賞味期限", "古い", "買い物", "捨てる", "もったいない"]),
    ("爪を切る", ["爪切り", "見えない", "厚い", "手伝って", "危ない"]),
    ("郵便物を確認", ["手紙", "請求書", "読めない", "老眼鏡", "ゴミ"]),
    ("机の上を片付ける", ["ほこり", "写真立て", "薬", "ティッシュ", "どこに置く"]),
    ("カレンダーをめくる", ["今月", "来月", "予定", "面会", "検診"]),
    ("暑さ対策", ["扇風機", "窓", "すだれ", "水分", "日陰"]),
    ("冬の暖房", ["ストーブ", "灯油", "こたつ", "みかん", "電気代"]),
    ("買い物リスト", ["牛乳", "パン", "卵", "安い", "重い"]),
    ("テレビ番組の話", ["ニュース", "天気予報", "時代劇", "うるさい", "消す"]),
    ("電池交換", ["リモコン", "電池", "切れた", "どこ", "新しい"]),
    ("髪をとかす", ["くし", "鏡", "白髪", "薄い", "昔は多かった"]),
    ("眼鏡を探す", ["老眼鏡", "どこ", "頭の上", "見えない", "困った"]),
    ("昼寝から目覚める", ["今何時", "寝すぎた", "ぼんやり", "夢", "お茶"]),
]

FILLERS_V5 = ["なんか", "あのー", "うーん", "まあ", "えー", "あの", "その"]
AI_SHORT_V5 = ["うん。", "そうですね。", "ええ。", "はい。", "そうですか。", "なるほど。"]
AI_FULL_V5 = [
    "わかりました。{v}ますね。",
    "大丈夫ですよ。{v}。",
    "確認しました。{v}。",
    "すぐにお持ちします。{v}。",
    "いいですね。{v}ましょう。",
]


# ============================================================
# V5 生成
# ============================================================

def make_human_text(persona, scenario_words):
    """自然な老人発話を生成"""
    p = persona
    word = random.choice(scenario_words)
    fword = random.choice(p["words"]) if random.random() < p["freq"] else ""

    # 22% フィラー
    filler = random.choice(FILLERS_V5) if random.random() < 0.22 else ""

    patterns = [
        f"{filler}、{word}…どうしよう。",
        f"…{word}、どこやったかな。{fword}",
        f"{word}のことやけど…{filler}ちょっと手伝って。",
        f"あの…{word}がな、うまくできへんのや。{fword}",
        f"{word}…まあええか。{filler}",
        f"なあ、{word}見てくれる？{fword}",
        f"…{word}。もう何年もこうや。",
    ]
    text = random.choice(patterns)
    # 方言ワードがない時はクリーンに
    if not fword:
        text = re.sub(r'\s*。\s*$', '。', text.replace('。', '。').rstrip('。').rstrip() + '。')

    # 20字前後に調整
    if len(text) > 30:
        text = text[:28] + "…"
    return text


def make_ai_text(short_ratio=0.30):
    """AI応答: 30%相槌"""
    if random.random() < short_ratio:
        return random.choice(AI_SHORT_V5)
    v = random.choice(["確認し", "ご用意し", "お手伝いし", "お知らせし", "見てき", "調べ", "持ってき", "準備し"])
    template = random.choice(AI_FULL_V5)
    return template.format(v=v)


def generate_v5(target_count=400):
    """V5対話を生成"""
    records = []
    for i in range(target_count):
        pid = random.choice(list(PERSONAS_V5.keys()))
        p = PERSONAS_V5[pid]
        scenario_name, scenario_words = random.choice(NEW_SCENARIOS)

        conversations = []
        num_turns = random.randint(3, 5)

        for t in range(num_turns):
            conversations.append({"from": "human", "value": make_human_text(p, scenario_words)})
            conversations.append({"from": "gpt", "value": make_ai_text()})

        record = {
            "id": f"jp_V5_realistic_{i:04d}",
            "conversations": conversations,
            "source": "V5_realistic",
            "quality": "synthetic_calibrated_v5",
            "language": "ja",
            "country_code": "JP",
            "persona_id": pid,
            "persona_name": p["name"],
            "persona_age": p["age"],
            "scenario": f"日常: {scenario_name}",
            "num_turns": len(conversations),
            "total_chars": sum(len(c["value"]) for c in conversations),
        }
        records.append(record)

    return records


# ============================================================
# 粤语 拡張 (36→80)
# ============================================================

CANTONESE_SCENARIOS = [
    ("朝早起身", ["幾點", "天光", "眼矇", "鐘", "早晨"]),
    ("食早餐", ["白粥", "油炸鬼", "腸粉", "茶", "麵包"]),
    ("睇天氣", ["落雨", "好天", "濕", "凍", "熱"]),
    ("搵眼鏡", ["老花鏡", "唔見咗", "睇唔清", "邊度", "頭頂"]),
    ("聽收音機", ["新聞", "天氣", "粵曲", "大聲", "嘈"]),
    ("打電話畀仔女", ["電話", "撳掣", "唔識", "聲", "掛住"]),
    ("去廁所", ["廁所", "手杖", "慢慢行", "地滑", "小心"]),
    ("食藥", ["藥丸", "幾粒", "記得", "血壓", "糖尿"]),
    ("睇電視", ["新聞", "電視劇", "大聲啲", "噏乜", "眼瞓"]),
    ("換衫", ["衫", "凍", "著多件", "除衫", "洗衫"]),
    ("抹枱", ["枱", "污糟", "抹布", "濕", "乾淨"]),
    ("收衫", ["衫", "乾晒", "摺", "衣櫃", "香"]),
    ("唸舊時", ["後生", "住邊", "街坊", "拆晒", "唔同晒"]),
    ("睇相簿", ["相", "舊時", "邊個", "唔認得", "後生"]),
    ("肚餓", ["餅乾", "生果", "雪梨", "蘋果", "軟"]),
    ("唞涼", ["風扇", "冷氣", "窗", "熱", "汗"]),
    ("腳痛", ["膝頭", "痛", "行路", "慢", "按摩"]),
    ("孫仔來訪", ["孫", "聽日", "開心", "糖", "玩具"]),
    ("唔開心", ["悶", "冇人", "出街", "傾偈", "孤獨"]),
    ("唞覺", ["眼瞓", "早唞", "熄燈", "被", "暖"]),
]

CANTONESE_FILLERS = ["哎呀", "唉", "咁", "呢", "囉", "其實"]
CANTONESE_AI_SHORT = ["係呀。", "好。", "知道。", "得。", "明白。", "咁樣呀。"]
CANTONESE_AI_FULL = [
    "好，我幫你{v}。",
    "得，{v}咗喇。",
    "放心啦，{v}㗎。",
    "我而家去{v}。",
    "冇問題，{v}。",
]


def generate_cantonese(target_count=50):
    """粤语对话拡張"""
    records = []
    for i in range(target_count):
        scenario_name, words = random.choice(CANTONESE_SCENARIOS)
        word = random.choice(words)
        filler = random.choice(CANTONESE_FILLERS) if random.random() < 0.20 else ""

        conversations = []
        for t in range(random.randint(3, 5)):
            htext = f"{filler}…{word}{random.choice(['喎','啫','添','囉','啦'])}。" if filler else f"…{word}{random.choice(['喎','啫','添','囉','啦'])}。"
            if random.random() < 0.30:
                atext = random.choice(CANTONESE_AI_SHORT)
            else:
                atext = random.choice(CANTONESE_AI_FULL).format(v=random.choice(["搞掂", "睇過", "問咗", "準備好", "放喺度", "幫你攞"]))
            conversations.append({"from": "human", "value": htext})
            conversations.append({"from": "gpt", "value": atext})

        records.append({
            "id": f"yue_expanded_{i:04d}",
            "conversations": conversations,
            "source": "V5_cantonese_expanded",
            "quality": "synthetic_calibrated",
            "language": "yue",
            "country_code": "CN_YUE",
            "scenario": scenario_name,
            "num_turns": len(conversations),
            "total_chars": sum(len(c["value"]) for c in conversations),
        })
    return records


# ============================================================
# 既存データの再フォーマット
# ============================================================

def fix_youtube_real_data():
    """YouTube実データ: all-human → human-gpt交互"""
    fpath = Path("real_elderly_audio/cleaned_elderly_speech.json")
    if not fpath.exists():
        return []

    with open(fpath, encoding='utf-8') as f:
        segments = json.load(f)

    records = []
    for i in range(0, len(segments) - 3, 4):
        chunk = segments[i:i+4]
        if all(len(c) > 10 for c in chunk):
            convs = []
            for j, text in enumerate(chunk):
                convs.append({"from": "human" if j % 2 == 0 else "gpt", "value": text})
            records.append({
                "id": f"real_elderly_yt_{i//4:04d}",
                "conversations": convs,
                "source": "real_elderly_youtube",
                "quality": "real_human_elderly",
                "language": "ja", "country_code": "JP",
                "scenario": "real_daily_life",
                "num_turns": len(convs),
                "total_chars": sum(len(c["value"]) for c in convs),
            })
    return records


def load_existing_jsonl():
    """既存の全ShareGPT JSONLからレコードをロード"""
    records = []

    # JP V3
    for fpath in ["sharegpt_output/by_country/JP.jsonl",
                  "sharegpt_output/JP_V4_calibrated.jsonl"]:
        fp = Path(fpath)
        if fp.exists():
            with open(fp, encoding='utf-8') as f:
                for line in f:
                    try:
                        r = json.loads(line.strip())
                        r["source"] = r.get("source", "V3_V4_existing")
                        records.append(r)
                    except:
                        pass

    # Real corpus (スライス形式に変換)
    fp = Path("corpus_analysis/real_corpus_all.jsonl")
    if fp.exists():
        with open(fp, encoding='utf-8') as f:
            for line in f:
                try:
                    r = json.loads(line.strip())
                    convs = r.get("conversations", [])
                    # 長すぎる会話は10ターンずつにスライス
                    for start in range(0, len(convs), 10):
                        chunk = convs[start:start+10]
                        if len(chunk) >= 2:
                            # all-humanの場合は修復
                            if all(c.get("from") == "human" for c in chunk):
                                fixed = []
                                for j, c in enumerate(chunk):
                                    fixed.append({"from": "human" if j%2==0 else "gpt", "value": c["value"]})
                                chunk = fixed
                            records.append({
                                "id": f"real_corpus_{len(records):04d}",
                                "conversations": chunk,
                                "source": "real_corpus_slice",
                                "quality": "real_human",
                                "language": "ja",
                                "country_code": "JP",
                                "scenario": r.get("source_type", ""),
                                "num_turns": len(chunk),
                                "total_chars": sum(len(c["value"]) for c in chunk),
                            })
                except:
                    pass

    # 明示的なdedup: 会話テキストのハッシュで
    seen = set()
    unique = []
    for r in records:
        # IDベース dedup
        rid = r.get("id", "")
        if rid and rid in seen:
            continue
        # 内容ベース dedup
        text_hash = "".join(c.get("value","")[:50] for c in r.get("conversations",[])[:2])
        if text_hash in seen:
            continue
        seen.add(rid)
        seen.add(text_hash)
        unique.append(r)

    # フィルタ: 2-100ターン
    unique = [r for r in unique if 2 <= r.get("num_turns", 0) <= 100]

    return unique


# ============================================================
# メイン
# ============================================================

def main():
    print("=" * 60)
    print("Dataset Expansion Pipeline")
    print("=" * 60)

    # 1. V5生成
    print("\n[1] V5生成...")
    v5 = generate_v5(400)
    print(f"  V5 realistic: {len(v5)}件")

    # 2. 粤语拡張
    print("\n[2] 粤语拡張...")
    yue = generate_cantonese(50)
    print(f"  Cantonese expanded: {len(yue)}件")

    # 3. YouTube実データ
    print("\n[3] YouTube実データ再処理...")
    yt = fix_youtube_real_data()
    print(f"  YouTube elderly: {len(yt)}件")

    # 4. 既存データ
    print("\n[4] 既存データ読み込み...")
    existing = load_existing_jsonl()
    print(f"  Existing (dedup): {len(existing)}件")

    # 5. 統合 + バランス調整
    print("\n[5] 統合・バランス調整...")

    # V3+V4を直接読み込む
    v3v4 = []
    for fname in ["sharegpt_output/by_country/JP.jsonl", "sharegpt_output/JP_V4_calibrated.jsonl"]:
        fp = Path(fname)
        if fp.exists():
            with open(fp, encoding='utf-8') as f:
                for line in f:
                    try:
                        r = json.loads(line.strip())
                        r["source"] = "V3V4_existing"
                        v3v4.append(r)
                    except:
                        pass
    print(f"  V3+V4既存: {len(v3v4)}件")

    # 実コーパスを分類
    real_corpus_records = [r for r in existing if r.get("source") == "real_corpus_slice"]

    print(f"  V5新規: {len(v5)}件")
    print(f"  粤语新規: {len(yue)}件")
    print(f"  YouTube実: {len(yt)}件")
    print(f"  実コーパス: {len(real_corpus_records)}件")

    # 実コーパスをダウンサンプリング
    synthetic_total = len(v5) + len(v3v4)
    max_real = int(synthetic_total * 0.25)
    random.shuffle(real_corpus_records)
    real_sample = real_corpus_records[:max_real]
    print(f"  実コーパス制限: {len(real_sample)}件 (上限{max_real})")

    all_records = v5 + yue + yt + v3v4 + real_sample

    # ターン数フィルタ
    all_records = [r for r in all_records if 2 <= r.get("num_turns", 0) <= 100]
    print(f"  Total (filtered): {len(all_records)}件")

    # 6. 分割
    print("\n[6] 8:1:1分割...")
    random.shuffle(all_records)

    # stratified by source
    src_groups = defaultdict(list)
    for r in all_records:
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

    print(f"  train: {len(train)} | val: {len(val)} | test: {len(test)}")

    # 7. 保存
    print("\n[7] 保存...")
    for name, data in [("train", train), ("val", val), ("test", test)]:
        fpath = TRAIN_DIR / f"{name}.jsonl"
        with open(fpath, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  ✅ {fpath} ({len(data)}件)")

    # メタデータ
    src_counts = defaultdict(int)
    for r in all_records:
        src_counts[r["source"]] += 1

    meta = {
        "dataset": "Japanese_Elderly_Care_AI_Companion_v5",
        "version": "5.0.0",
        "total": len(all_records),
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
        "sources": dict(src_counts),
        "improvements_v5": [
            "方言密度 半減 (YouTube実老年データに基づく)",
            "日常話題 15種追加 (お湯、洗濯、冷蔵庫、爪切り…)",
            "粤语 36→80+ラウンド拡張",
            "YouTube実老年音声 4動画から75会話追加",
            "総量 483→{len(all_records)}件",
        ],
    }
    with open(TRAIN_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # レポート
    print(f"\n{'=' * 60}")
    print(f"✅ 拡張完了: {len(all_records)}件")
    print(f"{'=' * 60}")
    print(f"\nソース構成:")
    for src, cnt in sorted(src_counts.items(), key=lambda x: -x[1]):
        pct = cnt / len(all_records) * 100
        bar = "█" * int(pct / 2)
        print(f"  {src:25s}: {cnt:4d}件 ({pct:5.1f}%) {bar}")
    print(f"\nLlamaFactory設定:")
    print(f"  dataset: training_data/train.jsonl ({len(train)}件)")
    print(f"  val_dataset: training_data/val.jsonl ({len(val)}件)")


if __name__ == "__main__":
    main()
