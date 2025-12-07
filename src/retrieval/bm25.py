import time
start_time = time.time()

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import os
import numpy as np
from rank_bm25 import BM25Okapi


DATA_PATH_LIST = [Path(f"data/{x}") for x in sorted(os.listdir("data")) if x.startswith("all_movie_info") and x.endswith(".json")]

_BM25_INDEX: BM25Okapi | None = None
_BM25_TITLES: List[str] | None = None
_BM25_META: List[Dict] | None = None


def _load_bm25_index(data_path_list: List[str | Path]):

    docs: List[List[str]] = []
    titles: List[str] = []
    metas: List[Dict] = []

    data=[]
    for path in data_path_list:
        with open(path, "r", encoding="utf-8") as f:
            data.extend(json.load(f))

    for item in data:
        title = (item.get("movie_name") or "").strip()
        summary = (item.get("summary") or "").strip()
        if not summary:
            continue

        text = f"{title}. {summary}" if title else summary
        tokens = text.lower().split()

        docs.append(tokens)
        titles.append(title if title else "UNKNOWN_TITLE")
        metas.append(item)

    bm25 = BM25Okapi(docs)
    return bm25, titles, metas


def _extract_year(meta: Dict) -> Optional[int]:

    date_str = (meta.get("release_date") or "").strip()
    if len(date_str) >= 4 and date_str[:4].isdigit():
        return int(date_str[:4])
    return None


def bm25_search(
    query: str,
    top_k: int = 5,
    year: Optional[int] = None,
    year_range: Optional[Tuple[int, int]] = None,
    genre: Optional[str] = None,
    country: Optional[str] = None,
    use_rerank: Optional[bool] = False,
    rerank_candidate_num: Optional[int] = 50,
) -> List[Dict]:

    global _BM25_INDEX, _BM25_TITLES, _BM25_META, DATA_PATH_LIST

    if _BM25_INDEX is None:
        _BM25_INDEX, _BM25_TITLES, _BM25_META = _load_bm25_index(DATA_PATH_LIST)

    tokens = query.lower().split()
    scores = _BM25_INDEX.get_scores(tokens)  # np.array, shape = (N,)
    N = len(scores)

    all_idx = np.arange(N)

    def pass_filters(i: int) -> bool:
        meta = _BM25_META[i]

        y = _extract_year(meta)
        if year is not None:
            if y is None or y != year:
                return False
        if year_range is not None:
            y0, y1 = year_range
            if y is None or not (y0 <= y <= y1):
                return False

        if genre is not None:
            g_list = meta.get("genres") or []
            g_list_lower = [g.lower() for g in g_list]
            if genre.lower() not in g_list_lower:
                return False
        if country is not None:
            c_list = meta.get("countries") or []
            c_list_lower = [c.lower() for c in c_list]
            if country.lower() not in c_list_lower:
                return False

        return True

    candidate_idx = [i for i in all_idx if pass_filters(i)]

    if not candidate_idx:
        return []

    cand_scores = scores[candidate_idx]
    k = min(top_k, len(candidate_idx))
    top_local = np.argsort(-cand_scores)[:k]

    results: List[Dict] = []
    for local_i in top_local:
        idx = candidate_idx[local_i]
        results.append({
            "score": float(cand_scores[local_i]),
            "title": _BM25_TITLES[idx],
            "movie_info": _BM25_META[idx],
        })
    return results


if __name__ == "__main__":
    q = "A boy goes to a wizard school"

    print("=== no filter ===")
    for r in bm25_search(q, top_k=5):
        print(r["score"], r["title"])

    print("\n=== year == 1999 ===")
    for r in bm25_search(q, top_k=5, year=1999):
        print(r["score"], r["title"], r["movie_info"].get("release_date"))

    print("\n=== 1990-2010 & genre=Animation ===")
    for r in bm25_search(q, top_k=5, year_range=(1990, 2010), genre="Animation"):
        print(r["score"], r["title"], r["movie_info"].get("genres"))

    print("time_cost: ", round(time.time() - start_time, 3))
