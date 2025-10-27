from typing import List, Dict, Any, Optional
import json, os, re
from rank_bm25 import BM25Okapi

def _tokenize(text: str, lowercase: bool = True) -> List[str]:
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    if lowercase:
        text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.findall(r"[a-z0-9]+", text)

def bm25_retrieval(
    json_path_list: List[str],
    query: str,
    top_k: int = 10,
    title_key: str = "movie_name",
    summary_key: str = "summary",
    lowercase: bool = True,
    return_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    for json_path in json_path_list:
        if not os.path.exists(json_path):
            raise FileNotFoundError(json_path)

    movies = []
    for json_path in json_path_list:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            movies.extend(data if isinstance(data, list) else next(
                (v for v in data.values() if isinstance(v, list)), []
            ))
        except json.JSONDecodeError:
            movies = []
            with open(json_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        movies.append(json.loads(line))

    if not movies:
        return []

    corpus_tokens = [_tokenize("movie_name: "+m.get(title_key, "")+"\nsummary: "+m.get(summary_key, ""), lowercase=lowercase) or [""] for m in movies]
    bm25 = BM25Okapi(corpus_tokens)

    q_tokens = _tokenize(query, lowercase=lowercase)
    scores = bm25.get_scores(q_tokens)  # ndarray (N,)

    top_idx = scores.argsort()[::-1][:top_k]
    results: List[Dict[str, Any]] = []
    for i in top_idx:
        item = {"_score": float(scores[i])}
        if return_fields is None:
            item.update(movies[i])
        else:
            for f in return_fields:
                item[f] = movies[i].get(f, None)
        results.append(item)
    return results

if __name__ == "__main__":
    hits = bm25_retrieval(
        ["movies.json"],
        query="a pop star hides in a fan's house and goes to high school",
        top_k=5,
        return_fields=["movie_name", "release_date", "summary", "imdb_movie_id", "genres"]
    )
    for h in hits:
        print(f"{h['_score']:.4f} | {h.get('movie_name')} ({h.get('release_date')})")
