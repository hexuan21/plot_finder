#!/usr/bin/env python3
"""
辅助标注脚本：帮助快速创建测试集
用法：python annotation_helper.py --query "你的查询" --topk 50
"""

import json
import argparse
from pathlib import Path
from retrieval_method.bm25_retrieval import bm25_retrieval

def get_all_chunk_paths(data_dir="data"):
    """获取所有数据chunk文件"""
    data_path = Path(data_dir)
    chunks = sorted(data_path.glob("all_info_chunk*.json"))
    return [str(p) for p in chunks]

def display_results(results, start_idx=0):
    """美化展示检索结果"""
    print("\n" + "="*100)
    for i, movie in enumerate(results[start_idx:], start=start_idx+1):
        score = movie.get('_score', 0)
        name = movie.get('movie_name', 'Unknown')
        year = movie.get('release_date', '')
        summary = movie.get('summary', '')[:150] + "..." if movie.get('summary') else ""
        genres = ", ".join(movie.get('genres', [])[:3])
        
        print(f"\n【{i}】Score: {score:.2f} | {name} ({year})")
        print(f"    Genres: {genres}")
        print(f"    Summary: {summary}")
        print(f"    ID: {movie.get('wiki_movie_id')}")
    print("\n" + "="*100)

def interactive_annotation(query, results, source_movie_id=None):
    """交互式标注"""
    print(f"\n🔍 Query: {query}\n")
    
    annotation = {
        "query": query,
        "strong_matches": [],
        "weak_matches": []
    }
    
    if source_movie_id:
        # 从results中找到source电影
        for r in results:
            if r.get('wiki_movie_id') == source_movie_id:
                annotation["source"] = {
                    "wiki_movie_id": r.get('wiki_movie_id'),
                    "movie_name": r.get('movie_name')
                }
                break
    
    display_results(results, 0)
    
    print("\n📝 请标注强相关电影（1-3个）")
    print("输入序号，用逗号分隔，例如: 1,3,5")
    print("如果没有强相关，直接按回车")
    strong_input = input("Strong matches: ").strip()
    
    if strong_input:
        strong_indices = [int(x.strip())-1 for x in strong_input.split(',')]
        for idx in strong_indices:
            if 0 <= idx < len(results):
                movie = results[idx]
                annotation["strong_matches"].append({
                    "wiki_movie_id": movie.get('wiki_movie_id'),
                    "movie_name": movie.get('movie_name'),
                    "release_date": movie.get('release_date'),
                    "score": movie.get('_score')
                })
    
    print("\n📝 请标注弱相关电影（3-6个）")
    print("输入序号，用逗号分隔")
    weak_input = input("Weak matches: ").strip()
    
    if weak_input:
        weak_indices = [int(x.strip())-1 for x in weak_input.split(',')]
        for idx in weak_indices:
            if 0 <= idx < len(results):
                movie = results[idx]
                annotation["weak_matches"].append({
                    "wiki_movie_id": movie.get('wiki_movie_id'),
                    "movie_name": movie.get('movie_name'),
                    "release_date": movie.get('release_date'),
                    "score": movie.get('_score')
                })
    
    return annotation

def load_existing_annotations(file_path):
    """加载已有的标注"""
    if Path(file_path).exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_annotation(annotation, file_path="data/test_data.json"):
    """保存标注到文件"""
    existing = load_existing_annotations(file_path)
    existing.append(annotation)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ 已保存到 {file_path}")
    print(f"   当前共有 {len(existing)} 条测试样本")

def main():
    parser = argparse.ArgumentParser(description="辅助标注工具")
    parser.add_argument("--query", required=True, help="查询语句")
    parser.add_argument("--topk", type=int, default=50, help="检索前k个结果")
    parser.add_argument("--source_id", default=None, help="如果query是从某电影改编的，提供其wiki_movie_id")
    parser.add_argument("--output", default="data/test_data.json", help="输出文件路径")
    parser.add_argument("--data_dir", default="data", help="数据目录")
    
    args = parser.parse_args()
    
    # 获取所有数据文件
    chunk_paths = get_all_chunk_paths(args.data_dir)
    print(f"📚 加载了 {len(chunk_paths)} 个数据文件")
    
    # BM25检索
    print(f"🔍 正在检索: {args.query}")
    results = bm25_retrieval(
        json_path_list=chunk_paths,
        query=args.query,
        top_k=args.topk,
        title_key="movie_name",
        summary_key="summary",
        return_fields=["movie_name", "release_date", "summary", "wiki_movie_id", "genres"]
    )
    
    print(f"✅ 找到 {len(results)} 个结果")
    
    # 交互式标注
    annotation = interactive_annotation(args.query, results, args.source_id)
    
    # 确认保存
    print("\n" + "="*50)
    print("标注摘要:")
    print(f"  Query: {annotation['query']}")
    print(f"  Strong: {len(annotation['strong_matches'])} 个")
    print(f"  Weak: {len(annotation['weak_matches'])} 个")
    
    confirm = input("\n是否保存? (y/n): ").strip().lower()
    if confirm == 'y':
        save_annotation(annotation, args.output)
    else:
        print("❌ 已取消")

if __name__ == "__main__":
    main()

