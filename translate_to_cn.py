"""
日语训练数据 → 中文版（原文件不动，生成 training_data_cn/）
使用 DeepSeek API 批量翻译
"""
import sys, io, json, os, glob, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# DeepSeek API (从.env读取)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com",
)

SRC = r"c:\Users\Lenovo\Desktop\养老agent\training_data"
DST = r"c:\Users\Lenovo\Desktop\养老agent\training_data_cn"

BATCH_SIZE = 30  # 每次API调用翻译多少条
DELAY = 0.5      # API调用间隔（秒）

def translate_batch(texts: list[str]) -> list[str]:
    """批量翻译日语→中文"""
    # 用特殊分隔符保证输出可解析
    joined = "\n---SPLIT---\n".join(texts)
    prompt = f"将以下日语老人对话逐条翻译成中文（中国北方老年人自然口语风格，保留语气词）。每条翻译用「---SPLIT---」分隔，不要加编号，不要加任何解释：\n\n{joined}"

    try:
        r = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=8000,
        )
        result = r.choices[0].message.content
        # 按分隔符拆分
        parts = result.split("---SPLIT---")
        # 清理空白
        parts = [p.strip() for p in parts]
        # 补齐不足的用原文
        while len(parts) < len(texts):
            parts.append(texts[len(parts)])
        return parts[:len(texts)]
    except Exception as e:
        print(f"  ❌ API Error: {e}")
        return texts  # 失败返回原文

def process_file(src_path: str):
    """翻译单个JSONL文件"""
    rel = os.path.relpath(src_path, SRC)
    dst_path = os.path.join(DST, rel)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    # 读取
    lines = []
    with open(src_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(json.loads(line))

    if not lines:
        return

    # 收集所有需要翻译的value
    all_values = []
    for item in lines:
        for conv in item.get("conversations", []):
            all_values.append(conv["value"])

    # 批量翻译
    translated = []
    for i in range(0, len(all_values), BATCH_SIZE):
        batch = all_values[i:i + BATCH_SIZE]
        result = translate_batch(batch)
        translated.extend(result)
        print(f"    [{i+len(batch)}/{len(all_values)}]", end="\r")
        time.sleep(DELAY)

    # 替换value + 更新元数据
    idx = 0
    for item in lines:
        item["language"] = "zh"
        item["country_code"] = "CN"
        if "scenario" in item and isinstance(item["scenario"], str):
            item["scenario"] = item["scenario"].replace("interview:", "访谈:").replace("csv_transcript:", "转录:")
        for conv in item.get("conversations", []):
            conv["value"] = translated[idx]
            idx += 1

    # 写入
    with open(dst_path, 'w', encoding='utf-8') as f:
        for item in lines:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"  ✅ {rel} ({len(lines)}条)")


def main():
    print(f"翻译 {SRC} → {DST}")
    print(f"DeepSeek API · 批量大小: {BATCH_SIZE}\n")

    # 收集所有JSONL文件
    all_files = sorted(glob.glob(os.path.join(SRC, '**', '*.jsonl'), recursive=True))
    print(f"共 {len(all_files)} 个文件\n")

    for i, f in enumerate(all_files):
        rel = os.path.relpath(f, SRC)
        print(f"[{i+1}/{len(all_files)}] {rel}")
        try:
            process_file(f)
        except Exception as e:
            print(f"  ❌ 失败: {e}")

    print(f"\n完成！中文版在: {DST}")


if __name__ == "__main__":
    main()
