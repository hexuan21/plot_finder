from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, Union
from functools import lru_cache
import numpy as np, json, os

@lru_cache(maxsize=2)
def _load_index(index_path: str):
    import faiss
    return faiss.read_index(index_path)

@lru_cache(maxsize=2)
def _load_idmap(idmap_path: str) -> List[str]:
    with open(idmap_path, "r", encoding="utf-8") as f:
        return json.load(f)

@lru_cache(maxsize=2)
def _load_model(model_name: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)

def _load_metadata(src_data_path: str, id_key: Optional[str]) -> Dict[str, Dict[str, Any]]:
    table: Dict[str, Dict[str, Any]] = {}
    if not src_data_path or not os.path.exists(src_data_path):
        return table
    try:
        with open(src_data_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        docs = obj if isinstance(obj, list) else next((v for v in obj.values() if isinstance(v, list)), [])
    except json.JSONDecodeError:
        docs = []
        with open(src_data_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    docs.append(json.loads(line))

    if id_key is None:
        candidates = ["imdb_id", "id", "doc_id", "wiki_movie_id"]
        for c in candidates:
            if any(isinstance(d, dict) and c in d for d in docs):
                id_key = c
                break
    if id_key is None:
        return table

    for d in docs:
        if isinstance(d, dict) and id_key in d:
            key = str(d[id_key])
            table[key] = d
    return table

def dense_retrieval(
    query: str,
    k: int = 10,
    *,
    index_path: str = "index/faiss.index",
    idmap_path: str = "embeddings/idmap.json",
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    normalize: bool = True,                 
    ef_search: Optional[int] = None,      
    src_data_path: Optional[str] = None,    
    id_key: Optional[str] = None,           
    return_fields: Optional[List[str]] = None 
) -> List[Dict[str, Any]]:

    index = _load_index(index_path)
    idmap = _load_idmap(idmap_path)
    model = _load_model(model_name)

    if ef_search is not None and hasattr(index, "hnsw"):
        index.hnsw.efSearch = int(ef_search)

    qv = model.encode([query], normalize_embeddings=normalize).astype(np.float32)  # (1, D)
    scores, idx = index.search(qv, k)  # (1, k)

    doc_table = _load_metadata(src_data_path, id_key) if src_data_path else {}

    results: List[Dict[str, Any]] = []
    for i, s in zip(idx[0], scores[0]):
        if i < 0 or i >= len(idmap):
            continue
        doc_id = idmap[int(i)]
        row: Dict[str, Any] = {"id": doc_id, "score": float(s)}
        if doc_table:
            doc = doc_table.get(str(doc_id))
            if doc:
                if return_fields is None:
                    row.update(doc)
                else:
                    for f in return_fields:
                        row[f] = doc.get(f)
        results.append(row)
    return results

if __name__ == "__main__":
    ### example
    hits = dense_retrieval(
        "two strangers meet on a train and fall in love",
        k=5,
        index_path="index/faiss.index",
        idmap_path="embeddings/idmap.json",
        src_data_path="data/all_info_chunk.json",          
        id_key=None,                                 
        return_fields=["title","genres","summary","year"]  
    )
    for h in hits:
        print(f"{h['score']:.4f} | {h.get('title', h['id'])}")
