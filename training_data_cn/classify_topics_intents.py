#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日本語老人介護対話データセットの話題×意図分類スクリプト
Japanese Elderly Care Dialogue — Topic × Intent Classifier

14話題 × 8意図 のキーワードベース分類
出力: classified/ 以下に話題別・意図別・交差別のJSONLファイル
"""

import json
import os
import re
from collections import Counter, defaultdict

# ============================================================
# 分類体系 — Classification Taxonomy
# ============================================================

# 14の話題 (Topics) — 日本語キーワード + 重み
TOPICS = {
    "gratitude": {
        "ja": "感謝・感恩",
        "zh": "感恩",
        "keywords": [
            ("ありがとう", 3), ("感謝", 3), ("嬉しい", 2), ("助かる", 2),
            ("おかげ", 2), ("お世話", 2), ("恩", 2), ("幸せ", 2),
            ("良かった", 1), ("お礼", 2), ("感激", 2), ("ありがたい", 3),
            ("うれしい", 2), ("しあわせ", 1), ("かんしゃ", 3),
        ]
    },
    "pension": {
        "ja": "年金・経済",
        "zh": "年金",
        "keywords": [
            ("年金", 3), ("お金", 2), ("貯金", 2), ("生活費", 2),
            ("経済", 2), ("お金がない", 3), ("貧乏", 2), ("節約", 2),
            ("もらえる", 1), ("支給", 2), ("金銭", 2), ("借金", 2),
            ("払う", 1), ("高い", 1), ("安い", 1), ("給料", 2),
            ("退職金", 2), ("国保", 2), ("保険料", 2), ("物価", 2),
            ("ねんきん", 3), ("おかね", 2), ("ちょきん", 2),
        ]
    },
    "nostalgia": {
        "ja": "懐かしさ・思い出",
        "zh": "怀旧",
        "keywords": [
            ("昔", 3), ("思い出", 3), ("懐かしい", 3), ("若い頃", 3),
            ("子供の頃", 3), ("昭和", 3), ("戦後", 2), ("あの頃", 2),
            ("覚えてる", 2), ("思い出す", 2), ("振り返る", 2), ("昔話", 3),
            ("むかし", 3), ("おもいで", 3), ("なつかしい", 3),
            ("わかいころ", 2), ("しょうわ", 3), ("せんご", 2),
        ]
    },
    "family": {
        "ja": "家族",
        "zh": "家族",
        "keywords": [
            ("家族", 3), ("子供", 2), ("息子", 2), ("娘", 2),
            ("孫", 2), ("夫", 2), ("妻", 2), ("お父さん", 2),
            ("お母さん", 2), ("兄弟", 2), ("親", 2), ("おじいちゃん", 2),
            ("おばあちゃん", 2), ("嫁", 2), ("旦那", 2), ("両親", 2),
            ("かぞく", 3), ("こども", 2), ("むすこ", 2), ("むすめ", 2),
            ("まご", 2), ("おっと", 2), ("つま", 2),
        ]
    },
    "health": {
        "ja": "健康・医療",
        "zh": "健康",
        "keywords": [
            ("健康", 3), ("病気", 3), ("病院", 3), ("医者", 2),
            ("薬", 2), ("痛い", 2), ("具合", 2), ("手術", 2),
            ("入院", 2), ("リハビリ", 2), ("介護", 1), ("看護", 2),
            ("血圧", 2), ("糖尿病", 3), ("癌", 3), ("ガン", 3),
            ("怪我", 2), ("骨折", 2), ("痛み", 2), ("めまい", 2),
            ("けんこう", 3), ("びょうき", 3), ("びょういん", 3),
            ("くすり", 2), ("いたい", 2), ("ぐあい", 2),
        ]
    },
    "death": {
        "ja": "死・喪失・臨終",
        "zh": "临终",
        "keywords": [
            ("死", 3), ("亡くなる", 3), ("お葬式", 3), ("お墓", 3),
            ("お別れ", 2), ("命", 2), ("天国", 2), ("遺言", 2),
            ("葬式", 3), ("供養", 2), ("仏壇", 2), ("他界", 3),
            ("看取る", 2), ("余命", 3), ("末期", 3), ("最期", 3),
            ("なくなる", 2), ("おそうしき", 2), ("おはか", 2),
            ("いのち", 2), ("ついとく", 2),
        ]
    },
    "work": {
        "ja": "仕事・職業",
        "zh": "工作",
        "keywords": [
            ("仕事", 3), ("働く", 2), ("会社", 2), ("退職", 2),
            ("職業", 2), ("勤め", 2), ("定年", 2), ("就職", 2),
            ("転職", 2), ("同僚", 2), ("上司", 2), ("部下", 2),
            ("しごと", 3), ("はたらく", 2), ("かいしゃ", 2),
            ("たいしょく", 2), ("ていねん", 2),
        ]
    },
    "hobby": {
        "ja": "趣味・楽しみ",
        "zh": "兴趣",
        "keywords": [
            ("趣味", 3), ("好き", 2), ("楽しい", 2), ("遊び", 2),
            ("旅行", 2), ("旅行", 2), ("写真", 2), ("音楽", 2),
            ("映画", 2), ("本", 1), ("読書", 2), ("料理", 2),
            ("釣り", 2), ("将棋", 2), ("囲碁", 2), ("麻雀", 2),
            ("カラオケ", 2), ("パチンコ", 2), ("園芸", 2),
            ("しゅみ", 3), ("たのしい", 2), ("すき", 2),
        ]
    },
    "daily": {
        "ja": "日常・生活",
        "zh": "日常",
        "keywords": [
            ("天気", 2), ("食事", 2), ("散歩", 2), ("買い物", 2),
            ("掃除", 2), ("洗濯", 2), ("風呂", 2), ("寝る", 2),
            ("朝ごはん", 2), ("昼ごはん", 2), ("晩ごはん", 2),
            ("ご飯", 1), ("お風呂", 2), ("着替え", 2),
            ("にちじょう", 2), ("てんき", 2), ("しょくじ", 2),
            ("さんぽ", 2), ("かいもの", 2),
        ]
    },
    "facility": {
        "ja": "施設・介護施設",
        "zh": "设施",
        "keywords": [
            ("施設", 3), ("老人ホーム", 3), ("介護施設", 3),
            ("入所", 2), ("デイサービス", 2), ("特養", 3),
            ("グループホーム", 3), ("ケアマネ", 2), ("見学", 1),
            ("申し込む", 1), ("入居", 2), ("空き", 2),
            ("しせつ", 3), ("ろうじんホーム", 3), ("かごしせつ", 3),
            ("にゅうしょ", 2),
        ]
    },
    "loneliness": {
        "ja": "孤独・寂しさ",
        "zh": "孤独",
        "keywords": [
            ("寂しい", 3), ("孤独", 3), ("一人", 2), ("独り", 3),
            ("一人暮らし", 3), ("ひとり", 2), ("誰もいない", 3),
            ("会話がない", 2), ("話し相手", 2), ("独居", 3),
            ("孤立", 3), ("さびしい", 3), ("こどく", 3),
            ("ひとりぐらし", 3), ("だれもいない", 2),
        ]
    },
    "community": {
        "ja": "近所・地域・コミュニティ",
        "zh": "邻里",
        "keywords": [
            ("近所", 3), ("隣", 2), ("地域", 2), ("町内", 2),
            ("ご近所", 2), ("隣人", 2), ("回覧板", 2), ("自治会", 2),
            ("町内会", 2), ("祭り", 1), ("ボランティア", 2),
            ("きんじょ", 3), ("となり", 2), ("ちいき", 2),
            ("りんじん", 2),
        ]
    },
    "technology": {
        "ja": "テクノロジー・機械",
        "zh": "科技",
        "keywords": [
            ("スマホ", 3), ("パソコン", 3), ("インターネット", 3),
            ("機械", 2), ("ロボット", 2), ("AI", 2), ("アプリ", 3),
            ("パソコン", 3), ("ケータイ", 2), ("携帯", 2),
            ("タブレット", 2), ("Wi-Fi", 3), ("WiFi", 3),
            ("ネット", 2), ("デジタル", 2), ("オンライン", 2),
            ("すまほ", 3), ("ぱそこん", 3), ("きかい", 2),
        ]
    },
    "general": {
        "ja": "一般・雑談",
        "zh": "一般",
        "keywords": [
            ("そうですね", 0.5), ("なるほど", 0.5),
        ]
    },
}

# 8の意図 (Intents)
INTENTS = {
    "nostalgia": {
        "ja": "懐かしむ",
        "zh": "怀旧",
        "keywords": [
            ("昔は", 3), ("あの頃", 2), ("思い出す", 2), ("懐かしい", 3),
            ("昔話", 2), ("振り返る", 2), ("若い時", 2), ("子供の時", 2),
        ]
    },
    "grief": {
        "ja": "悲しみ・喪失",
        "zh": "悲伤/丧失",
        "keywords": [
            ("悲しい", 3), ("辛い", 2), ("苦しい", 2), ("涙", 2),
            ("泣く", 2), ("死", 2), ("亡く", 2), ("失う", 2),
            ("寂しい", 2), ("寂しくて", 2), ("切ない", 2), ("悔しい", 2),
            ("かなしい", 3), ("つらい", 2), ("くるしい", 2),
        ]
    },
    "confusion": {
        "ja": "困惑・迷い",
        "zh": "困惑",
        "keywords": [
            ("わからない", 3), ("どうすれば", 2), ("困る", 2),
            ("迷う", 2), ("不安", 2), ("心配", 2), ("どうしたら", 2),
            ("わけがわからない", 3), ("混乱", 2), ("戸惑", 2),
            ("こまる", 2), ("まよう", 2), ("ふあん", 2),
            ("しんぱい", 2),
        ]
    },
    "gratitude": {
        "ja": "感謝",
        "zh": "感谢",
        "keywords": [
            ("ありがとう", 3), ("感謝", 3), ("おかげ", 2),
            ("助かった", 2), ("嬉しい", 2), ("お礼", 2),
            ("ありがたい", 3), ("恩", 2), ("うれしい", 2),
        ]
    },
    "complaint": {
        "ja": "不満・愚痴",
        "zh": "抱怨",
        "keywords": [
            ("嫌だ", 2), ("むかつく", 3), ("不満", 2), ("文句", 2),
            ("ひどい", 2), ("最低", 2), ("大変", 1), ("面倒", 2),
            ("うるさい", 2), ("めんどくさい", 3), ("だめ", 1),
            ("いやだ", 2),
        ]
    },
    "inquiry": {
        "ja": "質問・問い合わせ",
        "zh": "询问",
        "keywords": [
            ("どうやって", 2), ("教えて", 2), ("知ってる", 1),
            ("ですか？", 1), ("ますか？", 1), ("なに", 1),
            ("どこ", 1), ("いつ", 1), ("なぜ", 2), ("なんで", 2),
            ("どうして", 2), ("質問", 2), ("おしえて", 2),
        ]
    },
    "sharing": {
        "ja": "共有・報告",
        "zh": "分享",
        "keywords": [
            ("教える", 2), ("話す", 1), ("実は", 2), ("そういえば", 2),
            ("知ってる？", 2), ("聞いて", 2), ("報告", 2), ("伝える", 2),
        ]
    },
    "request": {
        "ja": "依頼・お願い",
        "zh": "请求",
        "keywords": [
            ("お願い", 3), ("手伝って", 2), ("やって", 1),
            ("欲しい", 1), ("ください", 1), ("頼む", 2),
            ("手伝い", 2), ("助けて", 2), ("代わりに", 2),
            ("おねがい", 3), ("てつだって", 2), ("たのむ", 2),
        ]
    },
}


def classify_text(text, categories):
    """
    Keyword-score classifier.
    Returns list of (category_key, score) sorted by score desc.
    """
    scores = defaultdict(float)
    text_lower = text.lower()

    for cat_key, cat_info in categories.items():
        for keyword, weight in cat_info["keywords"]:
            # Count occurrences and weight them
            count = text.count(keyword)
            if count > 0:
                scores[cat_key] += weight * count

    # Sort by score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked


def classify_conversation(conversations):
    """
    Classify a conversation by merging all turns' text.
    Returns (topic, intent, topic_score, intent_score, topic_all, intent_all)
    """
    # Merge all human + AI text
    full_text = ""
    human_text = ""
    for turn in conversations:
        if turn["from"] == "human":
            human_text += turn["value"] + " "
        full_text += turn["value"] + " "

    # Classify topic (use full text)
    topic_ranks = classify_text(full_text, TOPICS)
    top_topic = topic_ranks[0] if topic_ranks else ("general", 0)

    # Classify intent (bias toward human text since intent is human-driven)
    intent_ranks = classify_text(human_text, INTENTS)
    if not intent_ranks or intent_ranks[0][1] < 0.5:
        # fallback: classify on full text
        intent_ranks = classify_text(full_text, INTENTS)
    top_intent = intent_ranks[0] if intent_ranks else ("sharing", 0)

    # If topic score is too low, default to general
    if top_topic[1] < 1.0:
        top_topic = ("general", 0)

    # If intent score is too low, default to sharing
    if top_intent[1] < 0.5:
        top_intent = ("sharing", 0)

    return {
        "topic": top_topic[0],
        "topic_score": round(top_topic[1], 1),
        "topic_ranks": [(k, round(s, 1)) for k, s in topic_ranks[:3]],
        "intent": top_intent[0],
        "intent_score": round(top_intent[1], 1),
        "intent_ranks": [(k, round(s, 1)) for k, s in intent_ranks[:3]],
    }


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_files = ["train.jsonl", "val.jsonl", "test.jsonl"]
    output_root = os.path.join(base_dir, "classified")

    # Create output directories
    dirs = [
        os.path.join(output_root, "by_topic"),
        os.path.join(output_root, "by_intent"),
        os.path.join(output_root, "by_topic_intent"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # Collectors: keyed by topic, intent, and topic_intent
    all_data = []
    topic_buckets = defaultdict(list)
    intent_buckets = defaultdict(list)
    cross_buckets = defaultdict(list)

    stats = {
        "total": 0,
        "per_source": Counter(),
        "per_topic": Counter(),
        "per_intent": Counter(),
        "per_topic_intent": Counter(),
        "per_split": {"train": Counter(), "val": Counter(), "test": Counter()},
    }

    # Process each file
    for fname in input_files:
        fpath = os.path.join(base_dir, fname)
        if not os.path.exists(fpath):
            print(f"[WARN] File not found: {fpath}")
            continue

        split_name = fname.replace(".jsonl", "")
        print(f"Processing {fname}...")

        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                item = json.loads(line)
                convs = item.get("conversations", [])

                # Classify
                result = classify_conversation(convs)

                # Enrich item with classification
                item["topic"] = result["topic"]
                item["topic_score"] = result["topic_score"]
                item["topic_top3"] = result["topic_ranks"]
                item["intent"] = result["intent"]
                item["intent_score"] = result["intent_score"]
                item["intent_top3"] = result["intent_ranks"]
                item["topic_intent"] = f"{result['topic']}_{result['intent']}"

                # Track split origin
                item["_split"] = split_name

                all_data.append(item)

                # Bucket by topic
                topic_buckets[result["topic"]].append(item)

                # Bucket by intent
                intent_buckets[result["intent"]].append(item)

                # Bucket by topic×intent cross
                cross_key = f"{result['topic']}_{result['intent']}"
                cross_buckets[cross_key].append(item)

                # Stats
                stats["total"] += 1
                stats["per_source"][item.get("source", "unknown")] += 1
                stats["per_topic"][result["topic"]] += 1
                stats["per_intent"][result["intent"]] += 1
                stats["per_topic_intent"][cross_key] += 1
                stats["per_split"][split_name][result["topic"]] += 1

    # ============================================
    # Write output files
    # ============================================

    print(f"\nWriting classified outputs to {output_root}/ ...")

    # 1. By topic
    for topic_key, items in sorted(topic_buckets.items()):
        out_path = os.path.join(output_root, "by_topic", f"{topic_key}.jsonl")
        with open(out_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  by_topic/{topic_key}.jsonl → {len(items)} records")

    # 2. By intent
    for intent_key, items in sorted(intent_buckets.items()):
        out_path = os.path.join(output_root, "by_intent", f"{intent_key}.jsonl")
        with open(out_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  by_intent/{intent_key}.jsonl → {len(items)} records")

    # 3. By topic + intent cross
    for cross_key, items in sorted(cross_buckets.items()):
        out_path = os.path.join(output_root, "by_topic_intent", f"{cross_key}.jsonl")
        with open(out_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        if len(items) >= 50:  # Only print significant buckets
            print(f"  by_topic_intent/{cross_key}.jsonl → {len(items)} records")

    # 4. Full merged file (all splits combined, classified)
    all_path = os.path.join(output_root, "all_classified.jsonl")
    with open(all_path, "w", encoding="utf-8") as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"  all_classified.jsonl → {len(all_data)} records (full merge)")

    # 5. Summary JSON
    summary = {
        "classifier": "keyword_score_v1",
        "topics": {k: {"ja": v["ja"], "zh": v["zh"]} for k, v in TOPICS.items()},
        "intents": {k: {"ja": v["ja"], "zh": v["zh"]} for k, v in INTENTS.items()},
        "total_records": stats["total"],
        "topic_distribution": dict(stats["per_topic"].most_common()),
        "intent_distribution": dict(stats["per_intent"].most_common()),
        "topic_intent_matrix": {
            topic: {intent: stats["per_topic_intent"].get(f"{topic}_{intent}", 0)
                    for intent in INTENTS}
            for topic in TOPICS
        },
        "per_split": {
            split: dict(cnt.most_common())
            for split, cnt in stats["per_split"].items()
        },
        "per_source": dict(stats["per_source"].most_common()),
    }

    summary_path = os.path.join(output_root, "classification_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  classification_summary.json → written")

    # 6. Print summary table
    print("\n" + "=" * 70)
    print("  分類サマリー / Classification Summary")
    print("=" * 70)

    print("\n【話題分布 / Topic Distribution】")
    print(f"{'Topic':<20} {'ZH':<10} {'Count':>8} {'%':>8}")
    print("-" * 50)
    for topic_key, count in stats["per_topic"].most_common():
        zh = TOPICS[topic_key]["zh"]
        pct = count / stats["total"] * 100
        print(f"{topic_key:<20} {zh:<10} {count:>8} {pct:>7.1f}%")

    print(f"\n【意図分布 / Intent Distribution】")
    print(f"{'Intent':<20} {'ZH':<10} {'Count':>8} {'%':>8}")
    print("-" * 50)
    for intent_key, count in stats["per_intent"].most_common():
        zh = INTENTS[intent_key]["zh"]
        pct = count / stats["total"] * 100
        print(f"{intent_key:<20} {zh:<10} {count:>8} {pct:>7.1f}%")

    print(f"\n【話題×意図 マトリックス / Topic×Intent Matrix (>100件)】")
    for topic_key in TOPICS:
        row = []
        for intent_key in INTENTS:
            count = stats["per_topic_intent"].get(f"{topic_key}_{intent_key}", 0)
            if count >= 100:
                row.append(f"{intent_key}={count}")
        if row:
            print(f"  {topic_key}: {', '.join(row)}")

    print(f"\n出力先: {output_root}/")
    print(f"  by_topic/      — {len(topic_buckets)} files")
    print(f"  by_intent/     — {len(intent_buckets)} files")
    print(f"  by_topic_intent/ — {len(cross_buckets)} files")
    print(f"  all_classified.jsonl — {stats['total']} records")
    print(f"  classification_summary.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
