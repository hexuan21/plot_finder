from src.retrieval.bm25 import bm25_search
from src.retrieval.dpr import dpr_search
from src.retrieval.hybrid import hybrid_search
from src.retrieval.rerank import rerank_crossencoder


def main():
    q = "A boy goes to a wizard school"

    print("=== BM25: no filter ===")
    for res in bm25_search(q, top_k=5):
        print(res["score"], res["title"])

    print("\n=== BM25: year=1999 ===")
    for res in bm25_search(q, top_k=5, year=1999):
        print(res["score"], 
              res["title"], 
              res["movie_info"].get("release_date"),)
        
        

    print("=== DPR: no filter ===")
    for res in dpr_search(q, top_k=5):
        print(res["score"], res["title"])

    print("\n=== DPR: country='United Stats of America' & genre='Animation' ===")
    for res in dpr_search(q, top_k=5, country='United Stats of America', genre="Animation"):
        print(res["score"], 
              res["title"], 
              res["movie_info"].get("country"), 
              res["movie_info"].get("genres"),)
        


    print("=== HYBRID: no filter ===")
    for res in hybrid_search(q, top_k=5):
        print(res["score"], res["title"])

    print("\n=== HYBRID: 1990-2010 & genre='Animation' ===")
    for res in hybrid_search(q, top_k=5, year_range=(1990, 2010), genre="Animation"):
        print(
            res["score"],
            res["title"],
            res["movie_info"].get("release_date"),
            res["movie_info"].get("genres"),)
        
    
    
    print("=== RERANK with original candidates ===")
    
    print("=== BM25 + Cross-Encoder Rerank ===")
    bm25_candidates = bm25_search(q, top_k=50)
    bm25_reranked = rerank_crossencoder(q, bm25_candidates, top_k=5)
    for res in bm25_reranked:
        print(
            f"[rerank={res['rerank_score']:.4f}] "
            f"[orig={res['original_score']:.4f} rank={res['original_rank']:02d}] "
            f"{res['title']}"
        )
    
    print("=== DPR + Cross-Encoder Rerank ===")
    dpr_candidates = dpr_search(q, top_k=50)
    dpr_reranked = rerank_crossencoder(q, dpr_candidates, top_k=5)
    for res in dpr_reranked:
        print(
            f"[rerank={res['rerank_score']:.4f}] "
            f"[orig={res['original_score']:.4f} rank={res['original_rank']:02d}] "
            f"{res['title']}"
        )

    
if __name__ == "__main__":
    main()
