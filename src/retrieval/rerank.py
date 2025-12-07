import time
start_time = time.time()

from typing import List, Dict, Optional
from pathlib import Path

from sentence_transformers import CrossEncoder

CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_RERANKER: CrossEncoder | None = None


def _get_reranker(model_name: str = CROSS_ENCODER_MODEL_NAME) -> CrossEncoder:
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoder(model_name)
    return _RERANKER


def _build_doc_text(movie_info: Dict) -> str:
    title = (movie_info.get("movie_name") or "").strip()
    summary = (movie_info.get("summary") or "").strip()
    if title and summary:
        return f"{title}. {summary}"
    elif summary:
        return summary
    else:
        return title or ""


def rerank_crossencoder(
    query: str,
    candidates: List[Dict],
    top_k: Optional[int] = None,
    model_name: str = CROSS_ENCODER_MODEL_NAME,
) -> List[Dict]:
    if not candidates:
        return []

    reranker = _get_reranker(model_name)

    pairs = []
    for item in candidates:
        movie_info = item.get("movie_info", {})
        doc_text = _build_doc_text(movie_info)
        pairs.append((query, doc_text))

    scores = reranker.predict(pairs)  # shape = (len(candidates),)

    enriched: List[Dict] = []
    for i, (item, s) in enumerate(zip(candidates, scores)):
        new_item = item.copy()
        new_item["rerank_score"] = float(s)
        new_item["original_score"] = float(item.get("score", 0.0))
        new_item["original_rank"] = i
        enriched.append(new_item)

    enriched_sorted = sorted(enriched, key=lambda x: -x["rerank_score"])

    if top_k is not None:
        enriched_sorted = enriched_sorted[:top_k]

    return enriched_sorted


if __name__ == "__main__":
    from pathlib import Path
    import sys
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.append(str(ROOT))
    from hw.plot_finder.src.retrieval.bm25 import bm25_search

    q = "A boy goes to a wizard school"

    
    cands = bm25_search(q, top_k=50)
    print(f"BM25 got {len(cands)} candidates")
    print(cands[:10])

    reranked = rerank_crossencoder(q, cands, top_k=5)
    for r in reranked:
        print(
            f"[rerank_score={r['rerank_score']:.4f}] "
            f"[orig={r['original_score']:.4f}, rank={r['original_rank']:02d}] "
            f"{r['title']}"
        )

    print("time_cost: ", round(time.time() - start_time, 3))
