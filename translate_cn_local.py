"""
使用本地 ArrowCanaria 8B 将日语训练数据翻译成中文
"""
import sys, io, json, os, glob, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8014/v1", api_key="x")

SRC = r"c:\Users\Lenovo\Desktop\养老agent\training_data"
DST = r"c:\Users\Lenovo\Desktop\养老agent\training_data_cn"
CACHE_FILE = os.path.join(DST, "_translation_cache.json")
BATCH = 20

PROMPT = "你是日译中翻译器。将日语逐条翻译成中文（老年人口语·自然·北方风格）。每条用「---」分隔，不编号不解释。"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(c):
    os.makedirs(DST, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(c, f, ensure_ascii=False)

def translate_batch(texts):
    joined = "\n---\n".join(texts)
    try:
        r = client.chat.completions.create(
            model="arrowcanaria-8b",
            messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": joined}],
            temperature=0.3, max_tokens=2048,
        )
        parts = [p.strip() for p in r.choices[0].message.content.split("---")]
    except Exception as e:
        print(f"  ❌ API错误: {e}")
        return texts
    while len(parts) < len(texts):
        parts.append(texts[len(parts)])
    return parts[:len(texts)]

def process_file(filepath, cache):
    rel = os.path.relpath(filepath, SRC)
    dst_path = os.path.join(DST, rel)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    items = []
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line.strip()))

    all_vals = []
    for item in items:
        for c in item["conversations"]:
            all_vals.append(c["value"])

    uncached = [(i, v) for i, v in enumerate(all_vals) if v not in cache]
    uncached_texts = [v for _, v in uncached]

    total, done = len(uncached_texts), 0
    print(f"  {len(all_vals)}条 | 缓存:{len(all_vals)-total} | 待翻译:{total}")

    for i in range(0, total, BATCH):
        batch = uncached_texts[i:i+BATCH]
        result = translate_batch(batch)
        for j, (orig_idx, _) in enumerate(uncached[i:i+BATCH]):
            cache[all_vals[orig_idx]] = result[j]
        done = min(i+BATCH, total)
        print(f"  [{done}/{total}]", end="\r")
    if total > 0:
        save_cache(cache)
        print()

    # 重建
    idx = 0
    for item in items:
        item["language"] = "zh"
        item["country_code"] = "CN"
        for c in item["conversations"]:
            c["value"] = cache[all_vals[idx]]
            idx += 1

    with open(dst_path, 'w', encoding='utf-8') as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"  ✅ {os.path.basename(filepath)}")

def main():
    cache = load_cache()
    print(f"已缓存: {len(cache)} 条\n")

    # Phase 1: 核心文件
    for fn in ["train.jsonl", "test.jsonl", "val.jsonl"]:
        fp = os.path.join(SRC, fn)
        if os.path.exists(fp):
            print(f"[核心] {fn}")
            process_file(fp, cache)
            save_cache(cache)
            time.sleep(2)

    # Phase 2: classified
    cfs = sorted(glob.glob(os.path.join(SRC, "classified", "**", "*.jsonl"), recursive=True))
    print(f"\n[分类] {len(cfs)} 文件")
    for i, fp in enumerate(cfs):
        print(f"[{i+1}/{len(cfs)}] {os.path.relpath(fp, SRC)}")
        process_file(fp, cache)
        if i % 20 == 0:
            save_cache(cache)
    save_cache(cache)

    # 复制非jsonl文件
    import shutil
    for f in ["DATACARD.md", "metadata.json", "classify_topics_intents.py"]:
        s, d = os.path.join(SRC, f), os.path.join(DST, f)
        if os.path.exists(s):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)

    print(f"\n✅ 完成! {DST}")

if __name__ == "__main__":
    main()
