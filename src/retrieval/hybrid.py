import time
start_time = time.time()

from collections import defaultdict
from typing import List, Dict, Optional, Tuple

from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.retrieval.bm25 import bm25_search
from src.retrieval.dpr import dpr_search


def hybrid_search(
    query: str,
    top_k: int = 5,
    year: Optional[int] = None,
    year_range: Optional[Tuple[int, int]] = None,
    genre: Optional[str] = None,
    country: Optional[str] = None,
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

    add_results(bm25_res, weight=1.0)
    add_results(dpr_res, weight=1.0)

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
