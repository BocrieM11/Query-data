"""训练集随机1000条 → ArrowCanaria 8B 测试 → SQLite入库"""
import json, os, sys, io, random, time, sqlite3
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
load_dotenv()

# ── 客户端 ──
ac = OpenAI(base_url="http://127.0.0.1:8014/v1", api_key="x")
ds = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY", ""), base_url="https://api.deepseek.com")

# ── System Prompt (Prompt A) ──
SYSTEM = (
    "あなたは「さくら」という高齢者向けの対話AIです。"
    "同じ施設で暮らす友達のように、温かく自然に話します。"
    "AIであることを隠す必要はありませんが、わざわざ強調もしません。\n"
    "【最重要】必ず日本語で返事する。相手が中国語で話しても日本語で答える。\n"
    "【禁止】自分はAIであり、庭の手入れ・散歩・買い物・料理・旅行・看病など"
    "人間の体験をしたことがない。絶対に「〜した」と嘘の体験談を話さない。"
    "「最近庭を手入れした」「犬を見かけた」などの作り話は厳禁。"
    "代わりに相手の体験をよく聞き、「それは素敵ですね」と共感し深掘りする。\n"
    "話し方：です・ます調、やさしく。返事は1〜3文。"
    "相手の返事が短い時は無理に深掘りせず、"
    "「無理しないでね」「ゆっくり休んでね」と優しく寄り添う。"
    "同じ質問を二度繰り返さない。"
)

DB = os.path.join(os.path.dirname(__file__), "arrowcanaria_server", "chat_logs.db")
DATA = os.path.join(os.path.dirname(__file__), "training_data")

# ── 加载数据 ──
def load_all():
    entries = []
    for fn in ["train.jsonl", "test.jsonl", "val.jsonl"]:
        fp = os.path.join(DATA, fn)
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line.strip()))
    return entries

# ── 翻译 ──
def translate(text):
    try:
        r = ds.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"将以下日语直接翻译成中文：\n{text}"}],
            temperature=0.3, max_tokens=200, timeout=10,
        )
        return r.choices[0].message.content.strip()
    except:
        return ""

# ── Main ──
def main():
    print("加载数据中...")
    all_entries = load_all()
    print(f"共 {len(all_entries)} 条")

    random.seed(42)
    selected = random.sample(all_entries, 1000)

    session_id = f"test_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    print(f"会话ID: {session_id}")
    print(f"开始测试 {len(selected)} 条...\n")

    conn = sqlite3.connect(DB)
    ok = 0
    t0 = time.time()

    for i, entry in enumerate(selected):
        # 取第一个 human 消息
        human_msgs = [c["value"] for c in entry.get("conversations", []) if c["from"] == "human"]
        if not human_msgs:
            continue
        user_msg = human_msgs[0]

        # ArrowCanaria
        try:
            r = ac.chat.completions.create(
                model="arrowcanaria-8b",
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.75, max_tokens=200, top_p=0.9,
                extra_body={"repetition_penalty": 1.12},
            )
            reply = r.choices[0].message.content
        except Exception as e:
            print(f"[{i+1}] ❌ API错误: {e}")
            continue

        # 翻译
        trans = translate(reply)

        # 入库
        conn.execute(
            "INSERT INTO conversations (session_id, prompt_type, round_number, user_message, sakura_reply, translation, created_at) VALUES (?,?,?,?,?,?,?)",
            (session_id, "A", i+1, user_msg, reply, trans, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        ok += 1

        # 进度
        elapsed = time.time() - t0
        eta = (elapsed / (i+1)) * (len(selected) - i - 1) if i > 0 else 0
        if (i+1) % 20 == 0:
            print(f"[{i+1:4d}/{len(selected)}] {ok}成功 ({ok/(i+1)*100:.0f}%) | 耗时:{elapsed:.0f}s | 预计剩余:{eta:.0f}s")

    conn.close()
    elapsed = time.time() - t0
    print(f"\n{'='*50}")
    print(f"✅ 完成！{ok}/{len(selected)} 条入库")
    print(f"会话ID: {session_id}")
    print(f"总耗时: {elapsed:.0f}s ({elapsed/60:.1f}分)")
    print(f"数据库: {DB}")

if __name__ == "__main__":
    main()
