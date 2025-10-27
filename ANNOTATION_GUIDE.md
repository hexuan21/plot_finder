# 测试集标注指南

## 📦 环境设置

### 方法1：使用 Conda（推荐）

```bash
# 创建并激活环境
./setup_env.sh

# 或者手动创建
conda env create -f environment.yml
conda activate plot_finder
```

### 方法2：使用 pip

```bash
pip install -r requirements.txt
```

### 验证安装

```bash
python -c "from rank_bm25 import BM25Okapi; print('✅ BM25 installed')"
```

## 🎯 目标

收集 30-40 条测试样本，每个样本包含：
- 1个查询语句（query）
- 1-3个强相关电影（strong matches）
- 3-6个弱相关电影（weak matches）

## 🚀 快速开始

### 基本用法

```bash
python annotation_helper.py --query "你的查询语句" --topk 50
```

### 示例1：自己编写query

```bash
python annotation_helper.py --query "一个记者调查政府腐败，最终揭露真相"
```

### 示例2：从电影改编query（推荐）

```bash
# 如果你从某个电影的summary改编了query，记录它的ID
python annotation_helper.py \
  --query "一个记者调查政府腐败，最终揭露真相" \
  --source_id "12345"
```

## 📝 标注流程

1. **运行脚本**：脚本会自动用BM25检索所有电影
2. **查看结果**：显示top 50相关电影，包含：
   - 电影名、年份
   - 类型（genres）
   - 简介前150字
   - BM25分数
   - wiki_movie_id
3. **标注强相关**：输入序号，如 `1,3,5`
4. **标注弱相关**：输入序号，如 `2,7,10,15,20`
5. **确认保存**：输入 `y` 保存到 `data/test_data.json`

## 💡 编写Query技巧

### 方法1：从电影改编（最快！）

```bash
# 1. 随机浏览一些电影
python -c "
import json
with open('data/all_info_chunk0.json') as f:
    movies = json.load(f)
    for i, m in enumerate(movies[100:120]):
        print(f'{i}. {m[\"movie_name\"]}: {m[\"summary\"][:100]}...')
"

# 2. 选一个有趣的，改编它的summary
# 原summary: "Carl Fredricksen reluctantly agrees to go on a date..."
# 改编query: "一个老人不情愿地开始约会"
```

### 方法2：主题关键词

- "关于...的电影"
- "一个[职业]做[动作]"
- "两个[角色]在[地点]发生[事件]"

**示例：**
- ✅ "找出关于记者揭露腐败的电影"
- ✅ "一个黑客入侵大型公司的系统"
- ✅ "两个陌生人在火车上相遇并坠入爱河"
- ✅ "时间旅行者试图改变历史"

## 🎯 标注标准

### Strong Matches（强相关）

✅ 符合：
- 核心情节完全匹配
- 主题一致
- 你会首先推荐这部电影

❌ 不符合：
- 只有部分元素相似
- 只是类型相同

### Weak Matches（弱相关）

✅ 符合：
- 部分情节相似
- 主题有重叠但不完全匹配
- 包含相似元素（如都有记者、都有调查）
- 类型/风格相似

## 📊 测试集质量控制

### 多样性覆盖

- **类型**：动作、爱情、科幻、悬疑、喜剧、恐怖、剧情等
- **时代**：老电影（1930-1980）、现代电影（1980-2010）、新电影（2010+）
- **复杂度**：
  - 简单 (10个): "关于复仇的电影"
  - 中等 (15个): "一个律师为被诬陷的人辩护"
  - 复杂 (10个): "两个敌对阵营的人相爱，最终为和平牺牲"

### 进度建议

- 每天标注 10-15 个
- 分 3-4 天完成
- 避免疲劳标注

## 📂 输出格式

标注会自动追加到 `data/test_data.json`：

```json
{
    "query": "你的查询",
    "source": {
        "wiki_movie_id": "12345",
        "movie_name": "Source Movie"
    },
    "strong_matches": [
        {
            "wiki_movie_id": "12345",
            "movie_name": "Movie Name",
            "release_date": "1976",
            "score": 85.32
        }
    ],
    "weak_matches": [...]
}
```

## ⚠️ 注意事项

1. **不要手动编辑 test_data.json**（脚本会自动追加）
2. **source字段是可选的**（只在从电影改编query时使用）
3. **可以随时中断**（输入 `n` 取消保存）
4. **数据会实时保存**，不会丢失

## 🔧 高级选项

```bash
# 自定义top-k数量
python annotation_helper.py --query "..." --topk 100

# 指定输出文件
python annotation_helper.py --query "..." --output "my_test_set.json"

# 指定数据目录
python annotation_helper.py --query "..." --data_dir "path/to/data"
```

## ❓ 常见问题

**Q: 如果query和所有电影都不太相关怎么办？**
A: 这说明query可能太抽象或太具体。建议从某个电影的summary改编query。

**Q: Strong和Weak的界限在哪里？**
A: 粗略标准：Strong是你100%会推荐的，Weak是你可能会推荐的。

**Q: 可以跳过某个query吗？**
A: 可以，输入 `n` 取消保存即可。

**Q: 已有10个样本，我需要再标注多少个？**
A: 建议再标注 20-30 个，达到总共 30-40 个。

---

开始标注吧！🎬

