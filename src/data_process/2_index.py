import os
import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer


def load_movies(path_list):
    texts = []
    metadata = [] 
    data=[]
    for path in path_list:
        with open(path, "r", encoding="utf-8") as f:
            data.extend(json.load(f))
            
    for item in data:
        summary = item.get("summary") or ""
        title = item.get("movie_name") or ""
        if not summary.strip():
            continue 
        
        text = f"{title}. {summary}"
        texts.append(text)
        del item["summary"]
        metadata.append(item)
    return texts, metadata


def embed(texts, metadata):
    embeddings = model.encode(
        texts,
        batch_size=128,
        convert_to_numpy=True,
        show_progress_bar=True,
    )

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
    embeddings = embeddings / norms

    np.save(EMB_PATH, embeddings)

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    DATA_PATH_LIST = [Path(f"data/{x}") for x in sorted(os.listdir("data")) if x.startswith("all_movie_info") and x.endswith(".json")]
    EMB_PATH = Path("data/embed/movie_embeddings.npy")
    META_PATH = Path("data/embed/movie_metadata.json")
    
    texts, metadata = load_movies(DATA_PATH_LIST)
    print(f"Loaded {len(texts)} movies")
    embed(texts, metadata)