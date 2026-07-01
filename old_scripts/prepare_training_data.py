#!/usr/bin/env python3
"""
トレーニングデータ準備パイプライン
Step 1: V3+V4+実コーパス 統合
Step 2: 8:1:1 分割
Step 3: 統計レポート
Step 4: V4フォーマット拡張生成
"""

import json
import re
import random
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.model_selection import train_test_split

# ============================================================
# 設定
# ============================================================
TRAIN_DIR = Path("training_data")
TRAIN_DIR.mkdir(exist_ok=True)

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# 高齢者ケア関連のキーワード（実コーパスのフィルタリング用）
ELDERLY_KEYWORDS = [
    '老', '年', '孫', '薬', '病', '痛', '散歩', '昔', '戦争', '昭和',
    '夫', '妻', '娘', '息子', '介護', '施設', 'ホーム', '退職', '年金',
    '思い出', '懐', '死', '余生', '余生', '余生', '余生',
]

# 高齢者特有のフィラー・語彙（スコアリング用）
ELDERLY_MARKERS = [
    'のう', 'じゃ', 'わし', 'どす', 'さかい', 'おる', 'やで',
    'ほんま', 'あかん', 'めっちゃ', 'せや', 'おおきに',
    '昔', '若い頃', '年取', '孫', '腰が痛', '薬',
    '散歩', '囲碁', '演歌', '昭和', '戦後',
]


# ============================================================
# データローダー
# ============================================================

def load_jsonl(path):
    """JSONL読み込み"""
    records = []
    if not Path(path).exists():
        print(f"  ⚠️ ファイルなし: {path}")
        return records
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def load_v3_jp():
    """V3日本データ"""
    path = "sharegpt_output/by_country/JP.jsonl"
    records = load_jsonl(path)
    for r in records:
        r["source"] = "V3_persona"
        r["quality"] = "synthetic"
    return records


def load_v4_jp():
    """V4統計校正データ"""
    path = "sharegpt_output/JP_V4_calibrated.jsonl"
    records = load_jsonl(path)
    for r in records:
        r["source"] = "V4_calibrated"
        r["quality"] = "synthetic_stats_aligned"
    return records


def load_real_corpus():
    """実コーパス"""
    path = "corpus_analysis/real_corpus_all.jsonl"
    records = load_jsonl(path)
    # 各レコードに実データメタ情報を付与
    for r in records:
        r["source"] = "real_corpus"
        r["quality"] = "real_human"
        r["country_code"] = "JP"
        r["language"] = "ja"
        # conversationsフィールドの正規化
        if "conversations" in r:
            for c in r["conversations"]:
                if "from" not in c:
                    c["from"] = "human"
    return records


def filter_elderly_relevant(real_records, min_markers=2):
    """実コーパスから高齢者関連度の高い会話をフィルタ"""
    scored = []
    for r in real_records:
        all_text = " ".join(
            c.get("value", "") for c in r.get("conversations", [])
        )
        score = sum(1 for m in ELDERLY_MARKERS if m in all_text)
        scored.append((score, r))

    # スコア順にソート、上位50%を保持
    scored.sort(key=lambda x: -x[0])
    keep_n = max(len(scored) // 3, 30)  # 最低30件は残す
    kept = [r for s, r in scored[:keep_n]]
    for r in kept:
        r["elderly_relevance"] = "filtered"
    return kept


# ============================================================
# データ正規化
# ============================================================

def normalize_record(record, idx):
    """全レコードを統一形式に正規化"""
    conversations = record.get("conversations", [])

    # 空会話スキップ
    if not conversations or len(conversations) < 2:
        return None

    # 最低限のフィールドを保証
    normalized = {
        "id": f"jp_elderly_{record.get('source','unknown')}_{idx:04d}",
        "conversations": conversations,
        "source": record.get("source", "unknown"),
        "quality": record.get("quality", "synthetic"),
        "language": record.get("language", "ja"),
        "country_code": record.get("country_code", "JP"),
        # オプショナル
        "persona_id": record.get("persona_id", ""),
        "persona_name": record.get("persona_name", ""),
        "scenario": record.get("scenario", record.get("source_type", "")),
        "group": record.get("group", 0),
        "num_turns": len(conversations),
    }

    # 会話テキストの全長
    all_text = " ".join(c.get("value", "") for c in conversations)
    normalized["total_chars"] = len(all_text)

    return normalized


# ============================================================
# データ拡張: V4フォーマットで追加生成
# ============================================================

# V4のペルソナ情報（既存から再利用）
V4_PERSONAS = [
    ("A", "山下ハル", "82歳・京都・浓関西弁", "老人", ["どす", "さかい", "ほんま", "めっちゃ", "あかん", "のう"]),
    ("B", "田中セツ", "85歳・大阪・清晰干脆型", "老人", ["了解", "以上", "基本や", "シンプル", "確認"]),
    ("C", "佐藤キヨ", "88歳・和歌山・喋喋不休型", "老人", ["なあ", "あんた", "めっちゃ", "ほんま", "ぎょうさん"]),
    ("D", "伊藤タケ", "79歳・神戸・标准语型", "老人", ["です", "ます", "ですね", "ありがとう", "思います"]),
    ("E", "加藤フミ", "91歳・奈良・温和絮叨型", "老人", ["ねえ", "〜やろか", "〜してほしい", "ありがとう", "ごめんね"]),
    ("F", "村田カツ", "83歳・大阪・急躁易怒型", "老人", ["はよ", "あかん", "なんでや", "もう", "ええ加減"]),
    ("G", "清水サダ", "86歳・京都市内・怀旧少言型", "老人", ["…", "昔", "思い出", "寂しい", "ありがとう"]),
    ("H", "木村ケン", "80歳・兵庫・沉默寡言型", "老人", ["…", "うん", "ああ", "そうか", "助かった"]),
]

# シーン別AI応答テンプレート（V4の統計に基づく: 30%相槌 + 70%応答）
AI_SHORT = [
    "うん。", "そうですね。", "ええ。", "はい。", "そうですか。",
    "なるほど。", "それは良かったです。", "わかります。",
]
AI_LONG_TEMPLATES = [
    "わかりました。{action}ますね。",
    "大丈夫ですよ。{reassurance}。",
    "確認しました。{confirmation}。",
    "いいですね。{positive}。",
]

V4_SCENARIOS = [
    ("朝の検温・体調確認", ["体温測りましょう", "よく眠れました", "朝は寒い", "血圧はかりましょう"]),
    ("食堂での朝食", ["パンがいい", "ご飯が硬い", "味噌汁ぬるい", "おかわりしたい"]),
    ("テレビの操作", ["リモコン効かない", "チャンネル変えて", "音が小さい", "ニュース見たい"]),
    ("昔の写真を見ながら", ["これ戦後の写真", "若い頃のわし", "この人もう亡くなった", "懐かしいなあ"]),
    ("トイレの介助", ["一人で行ける", "手すり持つ", "転ばんように", "呼んですぐ来て"]),
    ("週末の面会予定", ["息子が来る", "部屋片付けな", "何時に来る", "楽しみや"]),
    ("天気と洗濯物", ["今日晴れる", "布団干したい", "梅雨いつまで", "湿気が嫌や"]),
    ("足腰のリハビリ", ["ちょっと歩く", "無理せんとこ", "杖どこや", "疲れた"]),
    ("夕方の血圧測定", ["今日は高い", "なんでやろ", "薬効いてる", "心配せんでええ"]),
    ("就寝前のひととき", ["今日も無事終わった", "明日は何曜日", "いい夢見たい", "おやすみ"]),
]


def generate_v4_expansion(target_count=380):
    """
    V4フォーマットで会話を生成（ルールベース拡張）
    目標: 120既存 + 380新規 = 500
    """
    print(f"\n--- V4拡張: 目標{target_count}件 ---")
    new_records = []

    for i in range(target_count):
        ptype, pname, pinfo, prole, pwords = random.choice(V4_PERSONAS)
        scenario_name, scenario_hints = random.choice(V4_SCENARIOS)
        hint = random.choice(scenario_hints)

        # 会話を構築（3-5ターン）
        num_turns = random.randint(3, 5)
        conversations = []

        for t in range(num_turns):
            # 老人発話: 短め(15-25字)、フィラー率高め
            filler = random.choice(["なんか", "あのー", "うーん", "まあ", ""])
            if random.random() < 0.22:  # 22%フィラー密度
                human_text = f"{filler}、{hint}…{random.choice(pwords)}。"
            else:
                human_text = f"{hint}…{random.choice(pwords)}。"

            # 短縮（約20字目標）
            if len(human_text) > 30:
                human_text = human_text[:28] + "…"

            conversations.append({"from": "human", "value": human_text})

            # AI応答: 30%は相槌
            if random.random() < 0.30:
                ai_text = random.choice(AI_SHORT)
            else:
                action = random.choice(["確認し", "お手伝いし", "ご用意し", "お知らせし"])
                reassurance = random.choice(["ご安心ください", "ゆっくりで大丈夫です", "私がついています", "いつでも呼んでください"])
                confirmation = random.choice(["記録しました", "問題ありません", "正常です", "承知しました"])
                positive = random.choice(["一緒に頑張りましょう", "素敵ですね", "楽しみですね", "良い一日になりますように"])
                template = random.choice(AI_LONG_TEMPLATES)
                ai_text = template.format(action=action, reassurance=reassurance,
                                          confirmation=confirmation, positive=positive)

            conversations.append({"from": "gpt", "value": ai_text})

        record = {
            "id": f"jp_elderly_V4_expanded_{i:04d}",
            "conversations": conversations,
            "source": "V4_expanded",
            "quality": "synthetic_rule_based",
            "language": "ja",
            "country_code": "JP",
            "persona_id": ptype,
            "persona_name": pname,
            "scenario": scenario_name,
            "num_turns": len(conversations),
            "total_chars": sum(len(c["value"]) for c in conversations),
        }
        new_records.append(record)

    print(f"  生成: {len(new_records)}件")
    return new_records


# ============================================================
# メイン
# ============================================================

def main():
    print("=" * 60)
    print("Training Data Preparation Pipeline")
    print("=" * 60)

    # ---- Step 1: データ収集 ----
    print("\n[Step 1] データ読み込み...")

    v3 = load_v3_jp()
    print(f"  V3日本: {len(v3)}件")

    v4 = load_v4_jp()
    print(f"  V4日本: {len(v4)}件")

    real = load_real_corpus()
    print(f"  実コーパス: {len(real)}件")

    # 実コーパスから高齢者関連度の高いものだけ抽出
    real_filtered = filter_elderly_relevant(real, min_markers=1)
    print(f"  実コーパス（高齢者関連フィルタ後）: {len(real_filtered)}件")

    # ---- Step 2: 正規化 ----
    print("\n[Step 2] データ正規化...")

    all_records = []
    for i, r in enumerate(v3 + v4 + real_filtered):
        norm = normalize_record(r, i)
        if norm:
            all_records.append(norm)

    print(f"  正規化後: {len(all_records)}件")

    # ---- Step 3: 品質フィルタリング ----
    print("\n[Step 3] 品質チェック...")

    # 実コーパスのフォーマット修復: human-only会話をhuman-gpt交互に変換
    fixed_real = []
    for r in all_records:
        if r["source"] == "real_corpus":
            convs = r["conversations"]
            if all(c["from"] == "human" for c in convs):
                # 奇数ターンをhuman、偶数ターンをgptとして再構成
                new_convs = []
                for i, c in enumerate(convs):
                    if i % 2 == 0:
                        new_convs.append({"from": "human", "value": c["value"]})
                    else:
                        new_convs.append({"from": "gpt", "value": c["value"]})
                if new_convs:
                    r["conversations"] = new_convs
                    r["num_turns"] = len(new_convs)
                    fixed_real.append(r)
            else:
                fixed_real.append(r)
        else:
            fixed_real.append(r)

    # V4_expanded除去（ルールベース品質不足）
    cleaned = [r for r in fixed_real if r.get("source") != "V4_expanded"]

    print(f"  実コーパス修復: {len([r for r in cleaned if r['source']=='real_corpus'])}件保持")
    print(f"  V4_expanded除去: 品質不足のため")
    print(f"  クリーニング後: {len(cleaned)}件")
    all_records = cleaned

    # 最低限のターン数チェック + 長すぎる会話のスライス
    sliced = []
    for r in all_records:
        if r["num_turns"] < 2:
            continue
        if r["num_turns"] > 20:
            # 長い会話を10ターンずつにスライス
            convs = r["conversations"]
            for start in range(0, len(convs), 10):
                chunk = convs[start:start+10]
                if len(chunk) >= 2:
                    nr = dict(r)
                    nr["conversations"] = chunk
                    nr["num_turns"] = len(chunk)
                    nr["total_chars"] = sum(len(c.get("value","")) for c in chunk)
                    nr["id"] = f"{r['id']}_s{start//10}"
                    sliced.append(nr)
        else:
            sliced.append(r)

    all_records = sliced
    print(f"  スライス後: {len(all_records)}件")

    # 実コーパスをもう一度数える
    real_count = len([r for r in all_records if r["source"] == "real_corpus"])
    print(f"  実コーパス利用可能: {real_count}件")

    # ---- Step 4: データセット構築 ----
    print("\n[Step 4] データセット構築...")

    # 実コーパスとV3+V4を分離
    synthetic = [r for r in all_records if r["source"] in ("V3_persona", "V4_calibrated")]
    real_corpus = [r for r in all_records if r["source"] == "real_corpus"]

    print(f"  合成データ (V3+V4): {len(synthetic)}件")
    print(f"  実コーパス: {len(real_corpus)}件")

    # 実コーパスをダウンサンプリング（合成データの20%を上限に）
    max_real = int(len(synthetic) * 0.2)
    random.shuffle(real_corpus)
    real_sample = real_corpus[:max_real]
    print(f"  実コーパス ダウンサンプル: {len(real_sample)}件 (上限{max_real})")

    # メインデータセット: 合成 + 少量実コーパス
    all_records = synthetic + real_sample
    random.shuffle(all_records)
    print(f"  最終データセット: {len(all_records)}件")

    # ペルソナ別に分割して、全ペルソナが全splitに含まれるようにする
    persona_groups = defaultdict(list)
    no_persona = []
    for r in all_records:
        pid = r.get("persona_id", "")
        if pid and pid != "?":
            persona_groups[pid].append(r)
        else:
            no_persona.append(r)

    train, val, test = [], [], []
    for pid, recs in persona_groups.items():
        random.shuffle(recs)
        n = len(recs)
        t_end = int(n * 0.8)
        v_end = int(n * 0.9)
        train.extend(recs[:t_end])
        val.extend(recs[t_end:v_end])
        test.extend(recs[v_end:])

    # ペルソナなしデータ（実コーパス）はランダムに分配
    random.shuffle(no_persona)
    n = len(no_persona)
    t_end = int(n * 0.8)
    v_end = int(n * 0.9)
    train.extend(no_persona[:t_end])
    val.extend(no_persona[t_end:v_end])
    test.extend(no_persona[v_end:])

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    print(f"  train: {len(train)}件 ({len(train)/len(all_records)*100:.0f}%)")
    print(f"  val:   {len(val)}件 ({len(val)/len(all_records)*100:.0f}%)")
    print(f"  test:  {len(test)}件 ({len(test)/len(all_records)*100:.0f}%)")

    # ---- Step 5: 保存 ----
    print("\n[Step 5] 保存...")

    splits = {"train": train, "val": val, "test": test}
    for name, data in splits.items():
        fpath = TRAIN_DIR / f"{name}.jsonl"
        with open(fpath, "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  ✅ {fpath} ({len(data)}件)")

    # メタデータ
    meta = {
        "dataset": "Japanese_Elderly_Care_AI_Companion",
        "version": "1.0.0",
        "format": "ShareGPT",
        "total": len(all_records),
        "splits": {
            "train": len(train), "val": len(val), "test": len(test)
        },
        "sources": {
            "V3_persona": len([r for r in all_records if r["source"] == "V3_persona"]),
            "V4_calibrated": len([r for r in all_records if r["source"] == "V4_calibrated"]),
            "real_corpus": len([r for r in all_records if r["source"] == "real_corpus"]),
            "V4_expanded": len([r for r in all_records if r["source"] == "V4_expanded"]),
        },
        "persona_distribution": dict(Counter(
            r.get("persona_id", "?") for r in all_records
        )),
        "quality_distribution": dict(Counter(
            r.get("quality", "?") for r in all_records
        )),
        "avg_turns": sum(r["num_turns"] for r in all_records) / len(all_records),
        "avg_chars": sum(r["total_chars"] for r in all_records) / len(all_records),
    }
    with open(TRAIN_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {TRAIN_DIR / 'metadata.json'}")

    # ---- Step 6: レポート ----
    print("\n" + "=" * 60)
    print("📊 データセットレポート")
    print("=" * 60)
    print(f"  総件数:          {len(all_records):,}件")
    print(f"  総発話数:        {sum(r['num_turns'] for r in all_records):,}ターン")
    print(f"  平均ターン数:     {meta['avg_turns']:.1f}")
    print(f"  平均文字数:       {meta['avg_chars']:.0f}字")
    print(f"")
    print(f"  train: {len(train):,}件  →  training_data/train.jsonl")
    print(f"  val:   {len(val):,}件    →  training_data/val.jsonl")
    print(f"  test:  {len(test):,}件   →  training_data/test.jsonl")
    print(f"")
    print(f"  ソース内訳:")
    for src, cnt in meta["sources"].items():
        bar = "█" * (cnt // 20)
        print(f"    {src:20s}: {cnt:4d}件 {bar}")
    print(f"")
    print(f"  ペルソナ分布:")
    for p, cnt in sorted(meta["persona_distribution"].items()):
        if p != "?":
            print(f"    {p}: {cnt}件")
    print(f"")
    print(f"  LlamaFactory設定:")
    print(f"    dataset: training_data/train.jsonl")
    print(f"    val_dataset: training_data/val.jsonl")
    print(f"    Format: ShareGPT")


if __name__ == "__main__":
    main()
