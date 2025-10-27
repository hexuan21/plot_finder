#!/usr/bin/env python3
"""
自动生成测试样本：从原始数据中选择10部电影，创建query并自动标注
"""

import json
import random
from pathlib import Path
from retrieval_method.bm25_retrieval import bm25_retrieval

# 手动精选的10部电影及其改编query
SELECTED_MOVIES = [
    {
        "wiki_movie_id": "23890098",
        "query": "A taxi driver and a musician develop an unlikely friendship despite their different backgrounds and initial conflicts"
    },
    {
        "wiki_movie_id": "18737103", 
        "query": "A film director locks himself in a coffin by accident and becomes fascinated by death, eventually joining a mysterious cult"
    },
    {
        "wiki_movie_id": "15985034",
        "query": "A woman believes she will marry her seventh boyfriend, but falls in love with number six and must find a replacement"
    },
    {
        "wiki_movie_id": "34114113",
        "query": "After leaving prison, a woman searches for her unknown father among two men her mother once loved"
    },
    {
        "wiki_movie_id": "4996220",
        "query": "A mystical shopkeeper with supernatural powers breaks sacred rules when she falls in love with a customer"
    },
    {
        "wiki_movie_id": "35744959",
        "query": "God plans to destroy Sodom, but the corrupt king schemes to swap places with the righteous man meant to be saved"
    },
    {
        "wiki_movie_id": "20663735",
        "query": "A man wrongly imprisoned for murder seeks revenge on those who framed him after his release from prison"
    },
    {
        "wiki_movie_id": "8598070",
        "query": "Two skiers meet in Aspen and one follows the other across the country"
    },
    {
        "wiki_movie_id": "3797781",
        "query": "Two sisters go abroad for work, but conflict arises when one announces her pregnancy"
    },
    {
        "wiki_movie_id": "31186339",
        "query": "In a dystopian future, teenagers are forced to fight to the death in a televised competition until only one survives"
    }
]

def get_all_chunk_paths(data_dir="data"):
    """获取所有数据chunk文件"""
    data_path = Path(data_dir)
    chunks = sorted(data_path.glob("all_info_chunk*.json"))
    return [str(p) for p in chunks]

def load_all_movies(chunk_paths):
    """加载所有电影数据"""
    all_movies = []
    for path in chunk_paths:
        with open(path, 'r', encoding='utf-8') as f:
            movies = json.load(f)
            all_movies.extend(movies)
    return all_movies

def find_movie_by_id(movies, movie_id):
    """根据ID找到电影"""
    for movie in movies:
        if movie.get('wiki_movie_id') == movie_id:
            return movie
    return None

def auto_select_matches(results, source_id):
    """
    自动选择strong和weak matches
    规则：
    - Strong: source电影 + 分数>source*0.8的前2个
    - Weak: 分数在source*0.4到source*0.8之间的，选4-6个
    """
    if not results:
        return [], []
    
    # 找到source电影的分数
    source_score = None
    source_idx = None
    for i, r in enumerate(results):
        if r.get('wiki_movie_id') == source_id:
            source_score = r.get('_score', 0)
            source_idx = i
            break
    
    if source_score is None:
        # 如果找不到source，用第一个作为基准
        source_score = results[0].get('_score', 100)
        source_idx = 0
    
    strong_matches = []
    weak_matches = []
    
    # Strong matches: 包含source + 分数>=source*0.6的其他电影（最多3个）
    for i, r in enumerate(results[:15]):  # 只看前15个
        score = r.get('_score', 0)
        if r.get('wiki_movie_id') == source_id:
            strong_matches.append({
                "wiki_movie_id": r.get('wiki_movie_id'),
                "movie_name": r.get('movie_name'),
                "release_date": r.get('release_date'),
                "score": score
            })
        elif score >= source_score * 0.6 and len(strong_matches) < 3:
            strong_matches.append({
                "wiki_movie_id": r.get('wiki_movie_id'),
                "movie_name": r.get('movie_name'),
                "release_date": r.get('release_date'),
                "score": score
            })
    
    # Weak matches: 分数在source*0.3到source*0.6之间的（4-6个）
    for i, r in enumerate(results[:30]):  # 看前30个
        score = r.get('_score', 0)
        if source_score * 0.3 <= score < source_score * 0.6 and len(weak_matches) < 6:
            if r.get('wiki_movie_id') != source_id:  # 不要重复source
                weak_matches.append({
                    "wiki_movie_id": r.get('wiki_movie_id'),
                    "movie_name": r.get('movie_name'),
                    "release_date": r.get('release_date'),
                    "score": score
                })
    
    # 如果weak matches不够，从中间分数区域补充
    if len(weak_matches) < 3:
        for i, r in enumerate(results[3:20]):  # 跳过前3个，看后面的
            if len(weak_matches) >= 5:
                break
            if r.get('wiki_movie_id') not in [m['wiki_movie_id'] for m in strong_matches + weak_matches]:
                weak_matches.append({
                    "wiki_movie_id": r.get('wiki_movie_id'),
                    "movie_name": r.get('movie_name'),
                    "release_date": r.get('release_date'),
                    "score": r.get('_score', 0)
                })
    
    return strong_matches, weak_matches

def generate_test_samples():
    """生成10个测试样本"""
    print("🚀 开始自动生成测试样本...")
    
    # 加载所有数据
    chunk_paths = get_all_chunk_paths("data")
    print(f"📚 加载数据文件: {len(chunk_paths)} 个")
    
    all_movies = load_all_movies(chunk_paths)
    print(f"🎬 总共加载电影: {len(all_movies)} 部")
    
    new_samples = []
    
    for idx, selected in enumerate(SELECTED_MOVIES, 1):
        movie_id = selected['wiki_movie_id']
        query = selected['query']
        
        print(f"\n{'='*80}")
        print(f"[{idx}/10] 处理: {query[:60]}...")
        
        # 找到source电影
        source_movie = find_movie_by_id(all_movies, movie_id)
        if not source_movie:
            print(f"⚠️  找不到电影 {movie_id}，跳过")
            continue
        
        print(f"    Source: {source_movie['movie_name']} ({source_movie['release_date']})")
        
        # BM25检索
        print(f"    🔍 BM25检索中...")
        results = bm25_retrieval(
            json_path_list=chunk_paths,
            query=query,
            top_k=50,
            title_key="movie_name",
            summary_key="summary",
            return_fields=["movie_name", "release_date", "summary", "wiki_movie_id", "genres"]
        )
        
        if not results:
            print(f"    ⚠️  没有检索结果，跳过")
            continue
        
        print(f"    ✅ 找到 {len(results)} 个结果")
        
        # 自动选择matches
        strong_matches, weak_matches = auto_select_matches(results, movie_id)
        
        print(f"    📊 Strong: {len(strong_matches)} 个, Weak: {len(weak_matches)} 个")
        
        # 构建样本
        sample = {
            "query": query,
            "source": {
                "wiki_movie_id": movie_id,
                "movie_name": source_movie['movie_name']
            },
            "strong_matches": strong_matches,
            "weak_matches": weak_matches
        }
        
        new_samples.append(sample)
        
        # 显示匹配的电影
        print(f"    Strong matches:")
        for m in strong_matches[:2]:
            print(f"      - {m['movie_name']} ({m['release_date']}) [{m['score']:.2f}]")
        print(f"    Weak matches:")
        for m in weak_matches[:3]:
            print(f"      - {m['movie_name']} ({m['release_date']}) [{m['score']:.2f}]")
    
    print(f"\n{'='*80}")
    print(f"✅ 生成完成! 共 {len(new_samples)} 个样本")
    
    return new_samples

def save_samples(new_samples, output_path="data/test_data.json"):
    """保存样本到文件"""
    # 加载现有样本
    existing = []
    if Path(output_path).exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    
    print(f"\n📝 现有样本: {len(existing)} 个")
    
    # 追加新样本
    existing.extend(new_samples)
    
    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=4)
    
    print(f"💾 已保存到: {output_path}")
    print(f"📊 总样本数: {len(existing)} 个")

def main():
    print("="*80)
    print("自动测试样本生成器")
    print("="*80)
    
    # 生成样本
    new_samples = generate_test_samples()
    
    if not new_samples:
        print("\n❌ 没有生成任何样本")
        return
    
    # 确认保存
    print(f"\n{'='*80}")
    print("准备保存到 data/test_data.json")
    confirm = input("是否保存? (y/n): ").strip().lower()
    
    if confirm == 'y':
        save_samples(new_samples)
        print("\n✅ 完成!")
    else:
        print("\n❌ 已取消")
        # 可选：保存到临时文件
        temp_path = "data/test_data_new.json"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(new_samples, f, ensure_ascii=False, indent=4)
        print(f"💾 新样本已保存到: {temp_path}")

if __name__ == "__main__":
    main()

