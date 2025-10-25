from typing import List, Dict, Any, Union, Tuple
import os, json
import numpy as np

def build_dense_index(
    items: List[Dict[str, Any]],
    emb_path: str = "embeddings/doc_embeddings.npy",
    idmap_path: str = "embeddings/idmap.json",
    index_path: str = "index/faiss_flatip.index",
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    batch_size: int = 64,
    normalize: bool = True,          # True: normalized to unit vectors
    dtype: str = "float32",          # "float32" or "float16"
) -> Dict[str, Any]:

    # concatenate text
    def _to_text(it: Dict[str, Any]) -> str:
        title = (it.get("title") or "").strip()
        genres = " ".join(it.get("genres") or [])
        summary = (it.get("summary") or "").strip()
        return f"{title} [SEP] {genres} [SEP] {summary}".strip()

    texts = [_to_text(it) for it in items]

    # collect ids
    ids = []
    for i, it in enumerate(items):
        _id = it.get("imdb_id") or it.get("id") or f"doc_{i:06d}"
        ids.append(str(_id))

    # encode texts
    from sentence_transformers import SentenceTransformer
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)

    emb = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=normalize,  
    )  # np.ndarray, shape=(N, D), float32

    if dtype not in ("float32", "float16"):
        raise ValueError("dtype must be 'float32' or 'float16'")
    emb = emb.astype(np.float16 if dtype == "float16" else np.float32)

    # save embeddings and id mapping
    os.makedirs(os.path.dirname(emb_path), exist_ok=True)
    os.makedirs(os.path.dirname(idmap_path), exist_ok=True)
    np.save(emb_path, emb)
    with open(idmap_path, "w", encoding="utf-8") as f:
        json.dump(ids, f)

    # build faiss index
    import faiss
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    E = emb
    d = E.shape[1]
    if normalize:
        index = faiss.IndexFlatIP(d)
    else:
        index = faiss.IndexFlatL2(d)
    index.add(E.astype(np.float32)) 
    faiss.write_index(index, index_path)

    return {
        "num_docs": int(E.shape[0]),
        "dim": int(E.shape[1]),
        "dtype": str(E.dtype),
        "normalize": normalize,
        "emb_path": emb_path,
        "idmap_path": idmap_path,
        "index_path": index_path,
        "model_name": model_name,
    }


def topk_bruteforce(E: np.ndarray, q: np.ndarray, k: int = 10):
    q = q.astype(np.float32)
    q /= (np.linalg.norm(q) + 1e-12)
    scores = E @ q  # (N,)
    idx = np.argpartition(-scores, k)[:k]
    idx = idx[np.argsort(-scores[idx])]
    return idx, scores[idx]


if __name__ == "__main__":
    items = [
        {"title":"Inception","genres":["Action","Sci-Fi"],"summary":"A thief enters dreams to steal secrets."},
        {"title":"Before Sunrise","genres":["Romance","Drama"],"summary":"Two strangers meet on a train and spend a night in Vienna."},
        # ...
    ]
    summary = build_dense_index(items, normalize=True, dtype="float32")
    print(summary)