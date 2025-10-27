# 🚀 快速设置和运行指南

## ✅ 已完成的工作

1. ✅ 创建新分支 `yuhaoc7`
2. ✅ 添加标注辅助工具 `annotation_helper.py`
3. ✅ 添加自动生成工具 `auto_generate_samples.py`
4. ✅ 创建 Conda 环境配置 `environment.yml`
5. ✅ 创建环境设置脚本 `setup_env.sh`
6. ✅ 修复 BM25 检索代码的语法错误
7. ✅ 更新依赖文件和文档

## 📦 第一步：设置环境

### 使用自动脚本（最简单）

```bash
# 在项目根目录运行
./setup_env.sh
```

### 或者手动设置

```bash
# 创建 conda 环境
conda env create -f environment.yml

# 激活环境
conda activate plot_finder

# 验证安装
python -c "from rank_bm25 import BM25Okapi; print('✅ All dependencies installed!')"
```

## 🎬 第二步：生成测试样本

你有两种方式生成测试样本：

### 方式1：自动生成10个样本（推荐先运行这个！）

```bash
# 激活环境后运行
conda activate plot_finder
python auto_generate_samples.py
```

这个脚本会：
- 从数据中精选10部多样化的电影
- 为每部电影创建改编的query
- 自动运行BM25检索
- 智能选择strong和weak matches
- 追加到 `data/test_data.json`

**预期结果：** 你的测试集将从10个样本增加到20个样本

### 方式2：交互式手动标注

```bash
# 标注单个样本
python annotation_helper.py --query "你的查询语句"

# 从电影改编的query（推荐）
python annotation_helper.py \
  --query "一个记者调查政府腐败案件" \
  --source_id "12345"

# 自定义检索数量
python annotation_helper.py --query "时间旅行改变历史" --topk 100
```

## 📊 当前状态

- **现有测试样本:** 10个（在 `data/test_data.json`）
- **目标样本数:** 30-40个
- **自动生成脚本准备好了:** ✅ 可以一键生成10个
- **还需标注:** 约10-20个（可以用交互式工具）

## 📝 工作流程建议

```
第1天：
1. 设置环境（5分钟）
   ./setup_env.sh

2. 运行自动生成（10-15分钟）
   python auto_generate_samples.py
   → 你现在有20个样本了！

3. 手动标注5-10个（30-45分钟）
   python annotation_helper.py --query "..."
   
第2-3天：
4. 继续手动标注10-15个
   → 达到30-35个样本

5. 检查质量，确保多样性
```

## 🎯 自动生成脚本精选的10部电影

1. **Taxi Blues** - 友情/冲突主题
2. **On War** - 神秘邪教
3. **Lucky 7** - 浪漫喜剧
4. **Une chance sur deux** - 寻亲冒险
5. **The Mistress of Spices** - 魔幻爱情
6. **Zohi Sdom** - 喜剧/历史
7. **Narasimham** - 复仇剧
8. **Fire and Ice** - 运动/追逐
9. **Kundiman ng Puso** - 姐妹情谊
10. **The Hunger Games** - 反乌托邦/生存游戏

涵盖了：剧情、喜剧、动作、爱情、科幻、历史等多种类型 ✅

## 📚 相关文档

- **ANNOTATION_GUIDE.md** - 详细的标注指南和最佳实践
- **environment.yml** - Conda环境配置
- **requirements.txt** - Python依赖列表

## 🆘 常见问题

### Q: 运行时提示 "No module named 'rank_bm25'"
**A:** 确保激活了conda环境：`conda activate plot_finder`

### Q: auto_generate_samples.py 运行很慢？
**A:** 正常！它需要加载~35,000-45,000部电影并运行10次BM25检索，预计10-15分钟

### Q: 如何修改自动生成的电影选择？
**A:** 编辑 `auto_generate_samples.py` 中的 `SELECTED_MOVIES` 列表

### Q: 可以同时运行多个标注吗？
**A:** 可以！每次运行都会追加到 test_data.json，不会覆盖

## 🎉 下一步

运行自动生成脚本后，你可以：
1. 查看生成的样本质量
2. 根据需要手动调整
3. 继续用交互式工具标注剩余样本
4. 达到30-40个样本目标！

祝标注顺利！🎬

