"""
V2: 先翻译 train/test/val → 建立翻译缓存 → 应用到 classified 文件
"""
import sys, io, json, os, glob, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com",
)

SRC = r"c:\Users\Lenovo\Desktop\养老agent\training_data"
DST = r"c:\Users\Lenovo\Desktop\养老agent\training_data_cn"
CACHE_FILE = os.path.join(DST, "_translation_cache.json")

BATCH = 80  # 批量大小

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
    """翻译一批文本，返回翻译列表"""
    joined = "\n---\n".join(texts)
    r = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": f"将以下日语逐条翻译成中文（北方老年人自然口语风格）。每条用「---」分隔，不要编号：\n\n{joined}"}],
        temperature=0.3, max_tokens=8192,
    )
    parts = [p.strip() for p in r.choices[0].message.content.split("---")]
    while len(parts) < len(texts):
        parts.append(texts[len(parts)])
    return parts[:len(texts)]

def process_file(filepath, cache):
    """翻译单个文件（使用缓存）"""
    rel = os.path.relpath(filepath, SRC)
    dst_path = os.path.join(DST, rel)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    lines = []
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                lines.append(json.loads(line.strip()))

    if not lines:
        return

    # 收集需要翻译的value
    all_vals = []
    for item in lines:
        for c in item["conversations"]:
            all_vals.append(c["value"])

    # 找出未缓存的
    to_translate = [(i, v) for i, v in enumerate(all_vals) if v not in cache]
    uncached_texts = [v for _, v in to_translate]

    print(f"  总计: {len(all_vals)} | 已缓存: {len(all_vals)-len(to_translate)} | 需翻译: {len(to_translate)}")

    if uncached_texts:
        for i in range(0, len(uncached_texts), BATCH):
            batch = uncached_texts[i:i+BATCH]
            result = translate_batch(batch)
            for j, (orig_idx, _) in enumerate(to_translate[i:i+BATCH]):
                cache[all_vals[orig_idx]] = result[j]
            print(f"    [{min(i+BATCH, len(uncached_texts))}/{len(uncached_texts)}]", end="\r")
        save_cache(cache)
        print()

    # 重建文件
    idx = 0
    for item in lines:
        item["language"] = "zh"
        item["country_code"] = "CN"
        for c in item["conversations"]:
            c["value"] = cache[all_vals[idx]]
            idx += 1

    with open(dst_path, 'w', encoding='utf-8') as f:
        for item in lines:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"  ✅ {rel} ({len(lines)}条)")


def main():
    cache = load_cache()
    print(f"缓存已有: {len(cache)} 条\n")

    # Phase 1: 核心文件
    for fname in ["train.jsonl", "test.jsonl", "val.jsonl"]:
        fp = os.path.join(SRC, fname)
        if os.path.exists(fp):
            print(f"[核心] {fname}")
            process_file(fp, cache)
            save_cache(cache)

    # Phase 2: classified 文件
    classified_files = sorted(glob.glob(os.path.join(SRC, "classified", "**", "*.jsonl"), recursive=True))
    print(f"\n[分类] {len(classified_files)} 个文件")
    for i, fp in enumerate(classified_files):
        rel = os.path.relpath(fp, SRC)
        print(f"[{i+1}/{len(classified_files)}] {rel}")
        process_file(fp, cache)

    # Phase 3: metadata 等非jsonl文件直接复制
    for f in ["DATACARD.md", "metadata.json", "classify_topics_intents.py"]:
        src = os.path.join(SRC, f)
        if os.path.exists(src):
            dst = os.path.join(DST, f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            import shutil
            shutil.copy2(src, dst)
            print(f"  📄 {f} (复制)")

    print(f"\n✅ 完成! {DST}")
    print(f"翻译缓存: {len(cache)} 条")


if __name__ == "__main__":
    main()
