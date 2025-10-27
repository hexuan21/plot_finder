# main.py
from __future__ import annotations
import argparse, json, sys
from typing import List, Dict, Any, Optional

# ---- Try to import your previously defined functions ----
bm25_fn = None
dense_fn = None
mod_name = "retrieval_method" 

# Try importing BM25 function
try:
    mod = __import__(mod_name, fromlist=["bm25_retrieval"])
    bm25_fn = getattr(mod, "bm25_retrieval", None)
except Exception:
    pass

# Try importing dense function
try:
    mod = __import__(mod_name, fromlist=["dense_search"])
    dense_fn = getattr(mod, "dense_search", None)
except Exception:
    pass

def parse_args():
    p = argparse.ArgumentParser(
        description="Unified search entry for PlotFindr (BM25 / Dense)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    p.add_argument("--method", required=True, choices=["bm25", "dense"],
                   help="Search method: bm25 or dense")
    p.add_argument("--query", required=True, help="Natural-language plot description")
    p.add_argument("--topk", type=int, default=10, help="Return top-k results")
    p.add_argument("--return_fields", type=str, default="movie_name,release_date,summary,genres",
                   help="Fields to include in BM25 output, comma-separated; empty means return full document")
    
    
    # ---- BM25 options ----
    p.add_argument("--json_path_list", type=List[str], default=["data/all_info_chunk0.json"],
                   help="Movies list JSON or JSONL (for BM25)")
    p.add_argument("--summary_key", type=str, default="summary",
                   help="Field name to search over (BM25)")
    p.add_argument("--title_key", type=str, default="title",
                   help="Field name to search over (BM25)")
    p.add_argument("--lowercase", type=int, default=1,
                   help="Lowercase tokens in BM25 tokenizer (1/0)")
    

    # ---- Dense options ----
    p.add_argument("--index_path", type=str, default="index/faiss.index",
                   help="FAISS index path (dense)")
    p.add_argument("--idmap_path", type=str, default="embeddings/idmap.json",
                   help="ID map aligned with index order (dense)")
    p.add_argument("--model_name", type=str, default="sentence-transformers/all-MiniLM-L6-v2",
                   help="Query encoder model name (dense)")
    p.add_argument("--normalize", type=int, default=1,
                   help="L2-normalize query embeddings (1/0); must match indexing (dense)")
    p.add_argument("--ef_search", type=int, default=None,
                   help="efSearch for HNSW index (dense, optional)")
    p.add_argument("--src_data_path", type=str, default="data/all_info_chunk0.json",
                   help="Optional: original documents JSON/JSONL to enrich results (dense)")
    p.add_argument("--id_key", type=str, default=None,
                   help="Field in metadata that matches idmap (dense). If omitted, it will be auto-detected.")

    # Output format
    p.add_argument("--format", type=str, choices=["table", "json"], default="table",
                   help="Output format")
    return p.parse_args()

def _split_fields(s: Optional[str]) -> Optional[List[str]]:
    if s is None or s.strip() == "":
        return None
    return [x.strip() for x in s.split(",") if x.strip()]

def main():
    args = parse_args()

    if args.method == "bm25":
        if bm25_fn is None:
            print("ERROR: bm25_search_from_json not found. Ensure a module like bm25_utils.py/bm25_search.py is available in PYTHONPATH.", file=sys.stderr)
            sys.exit(1)
        return_fields = _split_fields(args.return_fields)
        results: List[Dict[str, Any]] = bm25_fn(
            json_path_list=args.json_path_list,
            query=args.query,
            top_k=args.topk,
            summary_key=args.summary_key,
            title_key=args.title_key,
            lowercase=bool(args.lowercase),
            return_fields=return_fields
        )

    elif args.method == "dense":
        if dense_fn is None:
            print("ERROR: dense_search not found. Ensure a module like dense_index.py/dense_utils.py is available in PYTHONPATH.", file=sys.stderr)
            sys.exit(1)
        return_fields = _split_fields(args.return_fields)
        results: List[Dict[str, Any]] = dense_fn(
            query=args.query,
            k=args.topk,
            index_path=args.index_path,
            idmap_path=args.idmap_path,
            model_name=args.model_name,
            normalize=bool(args.normalize),
            ef_search=args.ef_search,
            src_data_path=args.src_data_path,
            id_key=args.id_key,
            return_fields=return_fields
        )
    else:
        print("ERROR: Unsupported method.", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for i, r in enumerate(results, 1):
            score = r.get("_score", r.get("score", None))
            title = r.get("title") or r.get("movie_name") or r.get("id")
            year = r.get("year") or r.get("release_date") or ""
            print(f"{i:>2}. {score if score is not None else '':>8} | {title} {f'({year})' if year else ''}")

if __name__ == "__main__":
    main()


# # BM25
# python main.py --method bm25 --query "a pop star hides in a fan's house and goes to high school" \
#   --movies_json data/movies.json --topk 5 --format table

# # Dense
# python main.py --method dense --query "two strangers meet on a train and fall in love" \
#   --index_path index/faiss.index --idmap_path embeddings/idmap.json \
#   --src_data_path data/docstore.jsonl --topk 5 --format json
