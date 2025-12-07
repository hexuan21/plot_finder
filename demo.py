from src.retrieval.bm25 import bm25_search
from src.retrieval.dpr import dpr_search
from src.retrieval.hybrid import hybrid_search


def main():
    q = "A boy goes to a wizard school"
    print("BM25:", bm25_search(q, top_k=5))
    print("DPR:", dpr_search(q, top_k=5))
    print("HYBRID:", hybrid_search(q, top_k=5))

if __name__ == "__main__":
    main()
