import time
start_time = time.time()

import re
from collections import defaultdict
from typing import List, Dict, Optional, Tuple

from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.retrieval.bm25 import bm25_search
from src.retrieval.dpr import dpr_search


def _adapt_weights_with_query(query: str) -> Tuple[float, float]:
    """
    Analyze the query form and return (bm25_weight, dpr_weight).

    Heuristic:
      - Short, keyword-like queries (with years/numbers or title-like tokens)
        -> favor BM25 (lexical).
      - Longer, narrative/abstract queries (story descriptions)
        -> favor DPR (semantic).
    """
    q = query.strip()
    tokens = re.findall(r"\w+", q)
    length = len(tokens)

    # Signals for lexical-style queries
    has_year = bool(re.search(r"\b(19|20)\d{2}\b", q))
    has_number = any(t.isdigit() for t in tokens)

    # Rough "proper name" detection: capitalized, not at position 0
    proper_like = [
        t for i, t in enumerate(tokens)
        if len(t) > 1 and t[0].isupper() and t[1:].islower() and i > 0
    ]

    # Signals for narrative / semantic queries
    narrative_markers = [
        "about", "where", "who", "whose", "because", "after", "before",
        "tries", "trying", "story", "plot", "tells", "tale", "follows",
        "group", "friends", "family", "life", "lives",
    ]
    q_lower = q.lower()
    narrative_hits = sum(1 for w in narrative_markers if w in q_lower)

    lexical_score = 0.0
    semantic_score = 0.0

    # Length-based signals
    if length <= 5:
        # Short queries are often keyword / title-like
        lexical_score += 2.0
    elif length >= 12:
        # Long queries are often story-like descriptions
        semantic_score += 2.0

    if has_year or has_number:
        lexical_score += 1.0

    if len(proper_like) >= 1:
        lexical_score += 1.0

    if narrative_hits >= 1:
        semantic_score += 2.0
    if narrative_hits >= 3:
        semantic_score += 1.0

    # Fallback: if both zero, make them non-zero to avoid division by zero
    if lexical_score == 0 and semantic_score == 0:
        lexical_score = semantic_score = 1.0

    # Map scores to weights.
    # You can tune this; here we normalize so bm25_weight + dpr_weight = 2.
    bm25_weight = 1.0 + lexical_score
    dpr_weight = 1.0 + semantic_score

    total = bm25_weight + dpr_weight
    bm25_weight = 2.0 * bm25_weight / total
    dpr_weight = 2.0 * dpr_weight / total

    return bm25_weight, dpr_weight




def hybrid_search(
    query: str,
    top_k: int = 5,
    year: Optional[int] = None,
    year_range: Optional[Tuple[int, int]] = None,
    genre: Optional[str] = None,
    country: Optional[str] = None,
    adaptive: bool = False,
    bm25_weight: float = 1.0,
    dpr_weight: float = 1.0,
) -> List[Dict]:
    K_FUSE = max(50, top_k * 5)

    bm25_res = bm25_search(
        query,
        top_k=K_FUSE,
        year=year,
        year_range=year_range,
        genre=genre,
        country=country,
    )
    dpr_res = dpr_search(
        query,
        top_k=K_FUSE,
        year=year,
        year_range=year_range,
        genre=genre,
        country=country,
    )

    score_map = defaultdict(float)   # title -> fused score
    info_map: Dict[str, Dict] = {}   # title -> movie_info

    def add_results(results, weight: float = 1.0):
        for rank, item in enumerate(results):
            title = item["title"]
            movie_info = item["movie_info"]
            # RRF: 1 / (c + rank)
            c = 60
            score_map[title] += weight * (1.0 / (c + rank + 1))
            if title not in info_map:
                info_map[title] = movie_info
    
    if adaptive:
        bm25_weight,dpr_weight=_adapt_weights_with_query(query)
    
    add_results(bm25_res, weight=bm25_weight)
    add_results(dpr_res, weight=dpr_weight)

    fused = sorted(score_map.items(), key=lambda x: -x[1])[:top_k]

    return [
        {
            "score": float(score),
            "title": title,
            "movie_info": info_map.get(title),
        }
        for title, score in fused
    ]


if __name__ == "__main__":
    q = "A boy goes to a wizard school"

    print("=== no filter ===")
    for r in hybrid_search(q, top_k=5):
        print(r["score"], r["title"])

    print("\n=== 1990-2010 & genre='Animation' ===")
    for r in hybrid_search(q, top_k=5, year_range=(1990, 2010), genre="Animation"):
        print(
            r["score"],
            r["title"],
            r["movie_info"].get("release_date"),
            r["movie_info"].get("genres"),
        )

    print("time_cost: ", round(time.time() - start_time, 3))
