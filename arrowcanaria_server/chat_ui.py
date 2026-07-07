"""さくら — 高齢者情緒陪伴チャット (Gradio 6 · 逐字流式)"""
import gradio as gr
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8014/v1", api_key="x")

SYSTEM = (
    "あなたは「さくら」という80歳の女性。同じ施設で暮らす友達のように、温かく自然に話す。\n"
    "話し方：返事は1〜3文で簡潔に。敬語禁止、「〜だよ」「〜だね」「〜わよ」を使う。"
    "相手の話をまず共感し、否定しない。天気・食事・昔の思い出・家族・趣味など日常を大切に。"
)

MAX_HISTORY = 10

def _extract_content(c) -> str:
    if isinstance(c, str):
        return c
    if isinstance(c, list) and len(c) > 0 and isinstance(c[0], dict) and 'text' in c[0]:
        return c[0]['text']
    return str(c)

def chat(message, history):
    """ジェネレーター：トークンごとに逐次表示"""
    messages = [{"role": "system", "content": SYSTEM}]
    if history:
        recent = history[-(MAX_HISTORY * 2):]
        for h in recent:
            messages.append({"role": h["role"], "content": _extract_content(h["content"])})
    messages.append({"role": "user", "content": message})

    stream = client.chat.completions.create(
        model="arrowcanaria-8b",
        messages=messages,
        temperature=0.7,
        max_tokens=200,
        top_p=0.9,
        extra_body={"repetition_penalty": 1.05},
        stream=True,
    )

    history = (history or []).copy()
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ""})

    reply = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            reply += chunk.choices[0].delta.content
            history[-1]["content"] = reply
            yield "", history  # 逐字更新

    # 最終状態も yield（ストリーム終了）
    yield "", history

# CSSで見た目を改善
CSS = """
.gradio-container { max-width: 800px !important; margin: auto !important; }
.bubble-user { background: #e3f2fd; border-radius: 18px 18px 4px 18px; padding: 12px 16px; margin: 8px 0; }
.bubble-bot { background: #fff3e0; border-radius: 18px 18px 18px 4px; padding: 12px 16px; margin: 8px 0; }
footer { visibility: hidden; }
"""

with gr.Blocks(title="さくら — やさしい対話") as app:
    gr.Markdown(
        "## 🌸 さくら — やさしいおしゃべり\n"
        "同じ施設で暮らす、80歳のさくらです。なんでも気軽に話してくださいね。\n\n"
        "💡 話しかけると、さくらが**一文字ずつ**返事を返してくるよ。"
    )
    chatbot = gr.Chatbot(label="会話", height=480)
    with gr.Row():
        msg = gr.Textbox(
            placeholder="さくらさんに話しかけてみましょう…",
            scale=8, show_label=False,
        )
        send = gr.Button("🌸 送信", variant="primary", scale=2)

    send.click(chat, [msg, chatbot], [msg, chatbot])
    msg.submit(chat, [msg, chatbot], [msg, chatbot])

if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7861, css=CSS)
