"""
ArrowCanaria 8B OpenAI 互換 API サーバー
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import torch, torchvision
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TextIteratorStreamer
from threading import Thread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import uvicorn, time, uuid, json, os, sqlite3
from datetime import datetime, timezone

load_dotenv()

# ---- モデル読み込み ----
MODEL_NAME = 'DataPilot/ArrowCanaria-Llama-8B-SFT-v0.1'
print(f'Loading {MODEL_NAME}...')
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type='nf4',
    ),
    device_map='auto',
)
print(f'Loaded! VRAM: {torch.cuda.memory_allocated()/1e9:.1f} GB')

# ---- FastAPI ----
app = FastAPI(title="ArrowCanaria API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 静态文件 & 前端页面
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "arrowcanaria-8b"
    messages: list[Message]
    temperature: float = 0.75
    max_tokens: int = 256
    top_p: float = 0.9
    repetition_penalty: float = 1.12
    stream: bool = False

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict]

@app.get("/v1/models")
async def list_models():
    return {"object": "list", "data": [{"id": "arrowcanaria-8b", "object": "model"}]}

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    prompt = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors='pt').to(model.device)

    if req.stream:
        # 流式输出
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        gen_kwargs = dict(
            **inputs,
            max_new_tokens=req.max_tokens,
            temperature=req.temperature,
            do_sample=True,
            top_p=req.top_p,
            repetition_penalty=req.repetition_penalty,
            pad_token_id=tokenizer.eos_token_id,
            streamer=streamer,
        )
        thread = Thread(target=model.generate, kwargs=gen_kwargs)
        thread.start()

        async def generate():
            cid = f"chatcmpl-{uuid.uuid4().hex[:8]}"
            for text in streamer:
                chunk = {
                    "id": cid, "object": "chat.completion.chunk",
                    "created": int(time.time()), "model": req.model,
                    "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}]
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    # 非流式
    with torch.no_grad():
        outputs = model.generate(
            **inputs, max_new_tokens=req.max_tokens,
            temperature=req.temperature, do_sample=True,
            top_p=req.top_p, repetition_penalty=req.repetition_penalty,
            pad_token_id=tokenizer.eos_token_id,
        )
    response_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return ChatResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:8]}", created=int(time.time()), model=req.model,
        choices=[{"index": 0, "message": {"role": "assistant", "content": response_text}, "finish_reason": "stop"}]
    )

# ---- 翻訳 API (DeepSeek) ----
ds_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com"
)

class TranslateRequest(BaseModel):
    text: str

@app.post("/v1/translate")
async def translate(req: TranslateRequest):
    """日语 → 中文翻译"""
    try:
        r = ds_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f"将以下日语直接翻译成中文：\n{req.text}"}],
            temperature=0.3, max_tokens=300, timeout=10,
        )
        return {"translation": r.choices[0].message.content.strip()}
    except Exception as e:
        return {"translation": "", "error": str(e)}

# ---- SQLite データベース ----
DB_PATH = os.path.join(os.path.dirname(__file__), "chat_logs.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                prompt_type TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                user_message TEXT NOT NULL,
                sakura_reply TEXT NOT NULL,
                translation TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON conversations(session_id, round_number)")
        conn.commit()

init_db()
print(f"DB ready: {DB_PATH}")

class LogRequest(BaseModel):
    session_id: str
    prompt_type: str
    round_number: int
    user_message: str
    sakura_reply: str
    translation: str = ""

@app.post("/v1/log")
async def save_log(req: LogRequest):
    """保存一轮对话"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO conversations (session_id, prompt_type, round_number, user_message, sakura_reply, translation, created_at) VALUES (?,?,?,?,?,?,?)",
                (req.session_id, req.prompt_type, req.round_number, req.user_message, req.sakura_reply, req.translation, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/v1/logs")
async def list_sessions():
    """列出所有会话"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT session_id, prompt_type, COUNT(*) as rounds,
                   MIN(created_at) as started, MAX(created_at) as last_active,
                   MIN(user_message) as first_msg
            FROM conversations
            GROUP BY session_id
            ORDER BY last_active DESC
            LIMIT 50
        """).fetchall()
        return {
            "sessions": [dict(r) for r in rows]
        }

@app.get("/v1/logs/{session_id}")
async def get_session(session_id: str):
    """获取某个会话的完整对话"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM conversations WHERE session_id=? ORDER BY round_number",
            (session_id,)
        ).fetchall()
        return {
            "session_id": session_id,
            "rounds": [dict(r) for r in rows]
        }

@app.delete("/v1/logs/{session_id}")
async def delete_session(session_id: str):
    """删除某个会话"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM conversations WHERE session_id=?", (session_id,))
        conn.commit()
    return {"ok": True}

if __name__ == "__main__":
    print("Starting server on http://0.0.0.0:8014")
    uvicorn.run(app, host="0.0.0.0", port=8014)
