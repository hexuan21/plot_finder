import json, re, os, unicodedata
from typing import Dict, Any, List, Iterable

def _normalize_text(s: str) -> str:
    if not isinstance(s, str):
        s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u00A0", " ").replace("\u200b", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _ascii_letter_ratio(s: str) -> float:
    if not s: return 0.0
    letters = sum(c.isalpha() and ord(c) < 128 for c in s)
    return letters / max(1, len(s))

def _split_sentences(s: str, max_sent: int = 30) -> List[str]:
    # quick & dirty sentence split
    parts = re.split(r"(?<=[.!?])\s+", s)
    return [p.strip() for p in parts if p.strip()][:max_sent]

def _clean_genres(x) -> List[str]:
    if x is None: return []
    if isinstance(x, str):
        # handle CSV-like
        toks = [t.strip() for t in re.split(r"[;,/]", x) if t.strip()]
    elif isinstance(x, (list, tuple)):
        toks = [str(t).strip() for t in x if str(t).strip()]
    else:
        toks = []
    return [t.title() for t in toks]


def _load_any_json(path: str) -> List[Dict[str, Any]]:
    # supports list-JSON or JSONL
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else next((v for v in data.values() if isinstance(v, list)), [])
    except json.JSONDecodeError:
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

def _save_jsonl(items: List[Dict[str, Any]], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for d in items:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

def _save_pyserini_json(items: List[Dict[str, Any]], out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    for d in items:
        j = {"id": d["id"], "contents": d["contents"], "raw": d}
        with open(os.path.join(out_dir, f"{d['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(j, f, ensure_ascii=False)


def preprocess_item(raw: Dict[str, Any],
                    ) -> Dict[str, Any] | None:
    movie_name   = _normalize_text(raw.get("movie_name") or "")
    summary = _normalize_text(raw.get("summary") or "")
    genres  = _clean_genres(raw.get("genres"))
    wiki_id = _normalize_text(raw.get("wiki_movie_id") or "")
    
    raw["movie_name"] = movie_name
    raw["summary"] = summary
    raw["genres"] = genres
    raw["wiki_movie_id"] = wiki_id
    
    # cheap language filter
    if _ascii_letter_ratio(summary) < 0.6:
        return None

    # length filter
    words = summary.split(" ") 
    if len(words) > MAX_WORDS:
        return None
    if len(words) < MIN_WORDS:
        return None

    return raw


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser("Preprocess CMU Movie Summary → clean JSONL & Pyserini JSON")
    ap.add_argument("--input", required=True, help="Path to raw CMU json/jsonl you already have (merged or raw rows).")
    ap.add_argument("--out_jsonl", default="data/docstore.jsonl", help="Clean docstore (for UI/dense).")
    ap.add_argument("--out_pyserini", default="data/pyserini_json", help="Folder with per-doc JSON for BM25.")
    args = ap.parse_args()
    
    MIN_WORDS=10
    MAX_WORDS=1000
    
    raw = _load_any_json(args.input)
    cleaned = []
    for r in raw:
        d = preprocess_item(r)
        if d:
            cleaned.append(d)
    
    _save_jsonl(cleaned, args.out_jsonl)
    # save_pyserini_json(cleaned, args.out_pyserini)
