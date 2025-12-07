import time
start_time = time.time()

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_EMBED_DIR = Path("data/embed")

DPR_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_DPR_MODEL: SentenceTransformer | None = None
_DPR_EMB: np.ndarray | None = None   # shape = (N, D)
_DPR_TITLES: List[str] | None = None
_DPR_PATH: str | None = None
_DPR_META: List[Dict] | None = None 


def _load_dpr_embeddings(embed_dir: Path):
    emb_path = embed_dir / "movie_embeddings.npy"
    meta_path = embed_dir / "movie_metadata.json"

    embeddings = np.load(emb_path)  # (N, D)

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
    embeddings = embeddings / norms

    with meta_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)

    titles: List[str] = []
    for m in metadata:
        title = (m.get("movie_name") or "").strip()
        titles.append(title if title else "UNKNOWN_TITLE")

    return embeddings, titles, metadata


def _get_dpr_model() -> SentenceTransformer:
    global _DPR_MODEL
    if _DPR_MODEL is None:
        _DPR_MODEL = SentenceTransformer(DPR_MODEL_NAME)
    return _DPR_MODEL


def _extract_year(meta: Dict) -> Optional[int]:
    date_str = (meta.get("release_date") or "").strip()
    if len(date_str) >= 4 and date_str[:4].isdigit():
        return int(date_str[:4])
    return None


def dpr_search(
    query: str,
    embed_path: str | Path = DEFAULT_EMBED_DIR,
    top_k: int = 5,
    year: Optional[int] = None,
    year_range: Optional[Tuple[int, int]] = None,
    genre: Optional[str] = None,
    country: Optional[str] = None,
) -> List[Dict]:
    global _DPR_EMB, _DPR_TITLES, _DPR_PATH, _DPR_META

    embed_dir = Path(embed_path)

    if _DPR_EMB is None or _DPR_PATH != str(embed_dir):
        _DPR_EMB, _DPR_TITLES, _DPR_META = _load_dpr_embeddings(embed_dir)
        _DPR_PATH = str(embed_dir)

    model = _get_dpr_model()

    q_emb = model.encode(query, convert_to_numpy=True)
    q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-12)

    scores = _DPR_EMB @ q_emb  # shape = (N,)
    N = len(scores)
    all_idx = np.arange(N)

    def pass_filters(i: int) -> bool:
        meta = _DPR_META[i]

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
            "title": _DPR_TITLES[idx],
            "movie_info": _DPR_META[idx],
        })
    return results


if __name__ == "__main__":
    q = "A man repeatedly relives the same day in a small town"

    print("=== no filter ===")
    for r in dpr_search(q, top_k=5):
        print(r["score"], r["title"])

    print("\n=== year_range=(1990, 2010), genre='Animation' ===")
    for r in dpr_search(q, top_k=5, year_range=(1990, 2010), genre="Animation"):
        print(r["score"], r["title"], r["movie_info"].get("release_date"), r["movie_info"].get("genres"))

    print("time_cost: ", round(time.time() - start_time, 3))
