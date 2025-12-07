import json
import os

INPUT_PATH = "data/all_movie_info.json"
OUTPUT_DIR = "data/"
CHUNK_SIZE = 10000  # 每个文件 10000 条

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. 读入整个 JSON（100MB 级别，用 json.load 直接读问题不大）
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, list):
    raise TypeError("期望顶层是 list，如果是 dict/别的结构要稍微改一下脚本。")

# 2. 按 10000 条切块写出
for i in range(0, len(data), CHUNK_SIZE):
    chunk = data[i:i + CHUNK_SIZE]
    idx = i // CHUNK_SIZE  # 第几个块，从 0 开始
    out_path = os.path.join(OUTPUT_DIR, f"all_movie_info_{idx:02d}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunk, f, ensure_ascii=False)
    print(f"Wrote {len(chunk)} items to {out_path}")

print("Done, total items:", len(data))
