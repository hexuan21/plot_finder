from __future__ import annotations
from typing import List, Dict, Any, Iterable, Tuple, Union, Optional
import os, json, argparse, re
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
import faiss

def build_text(
    item: Union[str, Dict[str, Any]],
    prefer_fields: Tuple[str, ...] = ("text", "summary", "plot"),
    fallback_fields: Tuple[str, ...] = ("title", "genres", "description"),
) -> str:
    if isinstance(item, str):
        return item.strip()
    if not isinstance(item, dict):
        return str(item)

    for f in prefer_fields:
        v = item.get(f)
        if isinstance(v, str) and v.strip():
            return v.strip()

    parts = []
    # title
    if isinstance(item.get("title"), str):
        parts.append(item["title"].strip())
    # genres
    g = item.get("genres")
    if isinstance(g, (list, tuple)):
        parts.append(" ".join([str(x) for x in g]))
    elif isinstance(g, str):
        parts.append(g)
    for f in fallback_fields:
        if f == "genres":
            continue
        v = item.get(f)
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())

    t = " [SEP] ".join([p for p in parts if p])
    return t if t else ""

def normalize_space(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s

def encode_corpus(
    corpus: List[Union[str, Dict[str, Any]]],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    batch_size: int = 64,
    normalize: bool = True,   # True: normalize for inner-product search
    dtype: str = "float32",   # "float32" or "float16"
    show_progress: bool = True,
) -> Tuple[np.ndarray, List[str]]:
    texts, ids = [], []
    for i, it in enumerate(corpus):
        txt = normalize_space(build_text(it))
        texts.append(txt if txt else "")
        _id = None
        if isinstance(it, dict):
            _id = it.get("imdb_id") or it.get("id") or it.get("doc_id") or it.get("wiki_movie_id")
        if not _id:
            _id = f"doc_{i:08d}"
        ids.append(str(_id))

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)
    emb = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        normalize_embeddings=normalize,
    )  # (N, D) float32

    if dtype not in ("float32", "float16"):
        raise ValueError("dtype must be 'float32' or 'float16'")
    if dtype == "float16":
        emb = emb.astype(np.float16)
    return emb, ids

def persist_embeddings(
    emb: np.ndarray,
    ids: List[str],
    emb_path: str = "embeddings/doc_embeddings.npy",
    idmap_path: str = "embeddings/idmap.json",
):
    os.makedirs(os.path.dirname(emb_path), exist_ok=True)
    os.makedirs(os.path.dirname(idmap_path), exist_ok=True)
    np.save(emb_path, emb)
    with open(idmap_path, "w", encoding="utf-8") as f:
        json.dump(ids, f)

def build_faiss_index(
    emb_path: str = "embeddings/doc_embeddings.npy",
    index_path: str = "index/faiss.index",
    index_type: str = "flat",   # "flat" | "hnsw" | "ivfpq"
    normalize: bool = True,
    hnsw_M: int = 32,
    hnsw_efC: int = 200,
    ivf_nlist: int = 4096,
    pq_m: int = 16,
    pq_bits: int = 8,
):
    import faiss
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    E = np.load(emb_path)
    if E.dtype != np.float32:
        E = E.astype(np.float32)  # faiss favors float32
    n, d = E.shape

    if index_type == "flat":
        index = faiss.IndexFlatIP(d) if normalize else faiss.IndexFlatL2(d)
        index.add(E)

    elif index_type == "hnsw":
        index = faiss.IndexHNSWFlat(d, hnsw_M)
        index.hnsw.efConstruction = hnsw_efC
        index.add(E)

    elif index_type == "ivfpq":
        quantizer = faiss.IndexFlatIP(d) if normalize else faiss.IndexFlatL2(d)
        index = faiss.IndexIVFPQ(quantizer, d, ivf_nlist, pq_m, pq_bits)
        index.train(E)
        index.add(E)
    else:
        raise ValueError("index_type must be one of {'flat','hnsw','ivfpq'}")

    faiss.write_index(index, index_path)
    return {"ntotal": int(index.ntotal), "dim": d, "type": index_type, "path": index_path}

class DenseSearcher:
    def __init__(
        self,
        index_path: str = "index/faiss.index",
        idmap_path: str = "embeddings/idmap.json",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        normalize: bool = True,
        efSearch: Optional[int] = None,  
    ):
        

        self.index = faiss.read_index(index_path)
        with open(idmap_path, "r", encoding="utf-8") as f:
            self.idmap = json.load(f)
        self.model = SentenceTransformer(model_name)
        self.normalize = normalize

        if efSearch is not None and hasattr(self.index, "hnsw"):
            self.index.hnsw.efSearch = int(efSearch)

    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        qv = self.model.encode([query], normalize_embeddings=self.normalize).astype(np.float32)  # (1, D)
        scores, idx = self.index.search(qv, k)  # (1, k)
        hits = []
        for i, s in zip(idx[0], scores[0]):
            if 0 <= i < len(self.idmap):
                hits.append((self.idmap[i], float(s)))
        return hits

def main():
    parser = argparse.ArgumentParser("Dense embedding & FAISS index builder + quick search")
    parser.add_argument("--input_json", type=str, default=None,)
    parser.add_argument("--model_name", type=str, default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--normalize", type=int, default=1)
    parser.add_argument("--dtype", type=str, default="float32", choices=["float32","float16"])
    parser.add_argument("--emb_path", type=str, default="embeddings/doc_embeddings.npy")
    parser.add_argument("--idmap_path", type=str, default="embeddings/idmap.json")
    parser.add_argument("--index_path", type=str, default="index/faiss.index")
    parser.add_argument("--index_type", type=str, default="flat", choices=["flat","hnsw","ivfpq"])
    parser.add_argument("--hnsw_M", type=int, default=32)
    parser.add_argument("--hnsw_efC", type=int, default=200)
    parser.add_argument("--ivf_nlist", type=int, default=4096)
    parser.add_argument("--pq_m", type=int, default=16)
    parser.add_argument("--pq_bits", type=int, default=8)
    parser.add_argument("--demo_query", type=str, default=None)
    parser.add_argument("--topk", type=int, default=5)
    args = parser.parse_args()

    if args.input_json and os.path.exists(args.input_json):
        try:
            with open(args.input_json, "r", encoding="utf-8") as f:
                corpus = json.load(f)
            if not isinstance(corpus, list):
                corpus = next((v for v in corpus.values() if isinstance(v, list)), [])
        except json.JSONDecodeError:
            corpus = []
            with open(args.input_json, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        corpus.append(json.loads(line))
    else:
        corpus = [
            {"id":"inception","title":"Inception","genres":["Action","Sci-Fi"],"summary":"A thief enters dreams to steal secrets."},
            {"id":"before_sunrise","title":"Before Sunrise","genres":["Romance","Drama"],"summary":"Two strangers meet on a train and spend one night talking."},
            {"id":"spotlight","title":"Spotlight","genres":["Drama"],"summary":"Journalists investigate systemic abuse and expose corruption."},
            "A soldier re-lives the same day in a time loop to fight aliens." 
        ]
        print("[info] Using small in-memory demo corpus (since --input_json not provided).")

    emb, ids = encode_corpus(
        corpus,
        model_name=args.model_name,
        batch_size=args.batch_size,
        normalize=bool(args.normalize),
        dtype=args.dtype,
        show_progress=True,
    )
    persist_embeddings(emb, ids, emb_path=args.emb_path, idmap_path=args.idmap_path)

    info = build_faiss_index(
        emb_path=args.emb_path,
        index_path=args.index_path,
        index_type=args.index_type,
        normalize=bool(args.normalize),
        hnsw_M=args.hnsw_M, hnsw_efC=args.hnsw_efC,
        ivf_nlist=args.ivf_nlist, pq_m=args.pq_m, pq_bits=args.pq_bits,
    )
    print(f"[ok] index built: {info}")

    if args.demo_query:
        searcher = DenseSearcher(
            index_path=args.index_path,
            idmap_path=args.idmap_path,
            model_name=args.model_name,
            normalize=bool(args.normalize),
            efSearch=64 if args.index_type=="hnsw" else None,
        )
        hits = searcher.search(args.demo_query, k=args.topk)
        print("[demo results]")
        for doc_id, score in hits:
            print(f"{score:.4f} | {doc_id}")

if __name__ == "__main__":
    main()
