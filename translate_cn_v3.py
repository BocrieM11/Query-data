"""极简翻译脚本 - 使用 DeepSeek API"""
import json, os, glob

# 手动加载 .env
with open(r"c:\Users\Lenovo\Desktop\养老agent\.env", "r") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v

from openai import OpenAI
client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

SRC = r"c:\Users\Lenovo\Desktop\养老agent\training_data"
DST = r"c:\Users\Lenovo\Desktop\养老agent\training_data_cn"
CACHE_FILE = os.path.join(DST, "_translation_cache.json")
os.makedirs(DST, exist_ok=True)

# 测通API
print("Testing API...", end=" ", flush=True)
r = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "翻译成中文：おはよう"}],
    max_tokens=20,
)
print("OK:", r.choices[0].message.content.strip(), flush=True)

# 加载缓存
cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
    print(f"Loaded cache: {len(cache)} entries", flush=True)

def translate(batch):
    """翻译一批文本"""
    text = "\n---\n".join(batch)
    r = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": f"将以下日语逐条翻译成中文（老年人口语）。每条用「---」分隔，不编号：\n\n{text}"}],
        temperature=0.3, max_tokens=8192,
    )
    parts = [p.strip() for p in r.choices[0].message.content.split("---")]
    while len(parts) < len(batch):
        parts.append(batch[len(parts)])
    return parts[:len(batch)]

def process(fp):
    """处理单个文件"""
    rel = os.path.relpath(fp, SRC)
    dst_path = os.path.join(DST, rel)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    items = []
    with open(fp, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line.strip()))

    all_vals = []
    for item in items:
        for c in item["conversations"]:
            all_vals.append(c["value"])

    uncached_vals = [(i, v) for i, v in enumerate(all_vals) if v not in cache]
    to_translate = [v for _, v in uncached_vals]
    BATCH = 100

    if to_translate:
        for i in range(0, len(to_translate), BATCH):
            batch = to_translate[i:i+BATCH]
            result = translate(batch)
            for j, (orig_idx, _) in enumerate(uncached_vals[i:i+BATCH]):
                cache[all_vals[orig_idx]] = result[j]
            done = min(i+BATCH, len(to_translate))
            print(f"  [{done}/{len(to_translate)}]", end=" ", flush=True)
            # 每个batch后保存缓存（防止中断丢失）
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
        print(flush=True)

    # 保存缓存
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)

    # 重建文件
    idx = 0
    for item in items:
        item["language"] = "zh"
        item["country_code"] = "CN"
        for c in item["conversations"]:
            c["value"] = cache[all_vals[idx]]
            idx += 1

    with open(dst_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"  -> {os.path.basename(fp)} ({len(items)} rows)", flush=True)

# Phase 1: 主文件
for fn in ["train.jsonl", "test.jsonl", "val.jsonl"]:
    fp = os.path.join(SRC, fn)
    if os.path.exists(fp):
        print(f"\n[{fn}]", flush=True)
        process(fp)

# Phase 2: 分类文件
cfs = sorted(glob.glob(os.path.join(SRC, "classified", "**", "*.jsonl"), recursive=True))
print(f"\nClassified files: {len(cfs)}", flush=True)
for i, fp in enumerate(cfs):
    print(f"[{i+1}/{len(cfs)}]", end=" ", flush=True)
    process(fp)

# 复制 metadata
import shutil
for f in ["DATACARD.md", "metadata.json", "classify_topics_intents.py"]:
    s, d = os.path.join(SRC, f), os.path.join(DST, f)
    if os.path.exists(s):
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)

print(f"\nDone! {DST}", flush=True)
