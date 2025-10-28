#!/usr/bin/env python3
"""
Auto-generate test samples: Select 10 real movies from data, create queries and auto-annotate
"""

import json
import random
from pathlib import Path
from retrieval_method.bm25_retrieval import bm25_retrieval

# All IDs are verified to exist in the actual data files
# These movies were selected to ensure genre diversity and good summary quality
SELECTED_MOVIES = [
    {
        "wiki_movie_id": "6473343",  # One Hot Summer Night (1998) - Crime/Drama
        "query": "A woman trapped in an abusive marriage starts an affair with a lawyer, only for her husband to turn up dead"
    },
    {
        "wiki_movie_id": "8267711",  # Perils of Nyoka (1942) - Action/Adventure
        "query": "An adventurer searches for the ancient Golden Tablets of Hippocrates while being hunted by a ruthless queen"
    },
    {
        "wiki_movie_id": "18717177",  # Shrek (2001) - Animation/Comedy/Fantasy
        "query": "An ogre's peaceful life is disrupted when he sets out to rescue a princess for a lord, only to fall in love with her himself"
    },
    {
        "wiki_movie_id": "26161289",  # Rechukka (1954) - Drama
        "query": "A prince raised as a thief discovers his royal identity and fights to reclaim his kingdom from an evil minister"
    },
    {
        "wiki_movie_id": "32655855",  # The Silence of Dean Maitland (1934) - Drama
        "query": "A clergyman hides his guilt after his friend is wrongfully imprisoned for a death he caused"
    },
    {
        "wiki_movie_id": "14320073",  # That Certain Woman (1937) - Romance/Drama
        "query": "A young widow struggles with love, loss, and motherhood as she faces class prejudice and personal sacrifice"
    },
    {
        "wiki_movie_id": "25269403",  # A.D. (2010) - Horror/Animation
        "query": "A group of survivors in Las Vegas must fight for their lives during a sudden zombie outbreak"
    },
    {
        "wiki_movie_id": "15294037",  # Naked Blood (1996) - Horror/Japanese
        "query": "A scientist’s experiment turning pain into pleasure spirals out of control as test subjects mutilate themselves"
    },
    {
        "wiki_movie_id": "9381735",  # Kanda Naal Mudhal (2005) - Romantic Comedy
        "query": "Two childhood rivals repeatedly cross paths as adults and unexpectedly fall in love after years of conflict"
    },
    {
        "wiki_movie_id": "18848055",  # Die Feuerzangenbowle (1944) - Comedy/Black-and-white
        "query": "A successful writer disguises himself as a student to relive the school days he never had, causing humorous chaos"
    }
]

def get_all_chunk_paths(data_dir="data"):
    """Get all data chunk file paths"""
    data_path = Path(data_dir)
    chunks = sorted(data_path.glob("all_info_chunk*.json"))
    return [str(p) for p in chunks]

def load_all_movies(chunk_paths):
    """Load all movie data from chunk files"""
    all_movies = []
    for path in chunk_paths:
        with open(path, 'r', encoding='utf-8') as f:
            movies = json.load(f)
            all_movies.extend(movies)
    return all_movies

def find_movie_by_id(movies, movie_id):
    """Find a movie by its wiki_movie_id"""
    for movie in movies:
        if movie.get('wiki_movie_id') == movie_id:
            return movie
    return None

def auto_select_matches(results, source_id):
    """
    Automatically select strong and weak matches based on BM25 scores
    Rules:
    - Strong matches: source movie + top movies with score >= source*0.6 (max 3 total)
    - Weak matches: movies with score between source*0.3 and source*0.6 (4-6 movies)
    """
    if not results:
        return [], []
    
    # Find the source movie's score
    source_score = None
    source_idx = None
    for i, r in enumerate(results):
        if r.get('wiki_movie_id') == source_id:
            source_score = r.get('_score', 0)
            source_idx = i
            break
    
    if source_score is None:
        # If source not found, use the top result as baseline
        source_score = results[0].get('_score', 100)
        source_idx = 0
    
    strong_matches = []
    weak_matches = []
    
    # Strong matches: include source + other movies with score >= source*0.6 (max 3 total)
    for i, r in enumerate(results[:15]):  # Only check top 15
        score = r.get('_score', 0)
        if r.get('wiki_movie_id') == source_id:
            strong_matches.append({
                "wiki_movie_id": r.get('wiki_movie_id'),
                "movie_name": r.get('movie_name'),
                "release_date": r.get('release_date'),
                "score": score
            })
        elif score >= source_score * 0.6 and len(strong_matches) < 3:
            strong_matches.append({
                "wiki_movie_id": r.get('wiki_movie_id'),
                "movie_name": r.get('movie_name'),
                "release_date": r.get('release_date'),
                "score": score
            })
    
    # Weak matches: scores between source*0.3 and source*0.6 (4-6 movies)
    for i, r in enumerate(results[:30]):  # Check top 30
        score = r.get('_score', 0)
        if source_score * 0.3 <= score < source_score * 0.6 and len(weak_matches) < 6:
            if r.get('wiki_movie_id') != source_id:  # Don't duplicate source
                weak_matches.append({
                    "wiki_movie_id": r.get('wiki_movie_id'),
                    "movie_name": r.get('movie_name'),
                    "release_date": r.get('release_date'),
                    "score": score
                })
    
    # If weak matches are insufficient, supplement from mid-range scores
    if len(weak_matches) < 3:
        for i, r in enumerate(results[3:20]):  # Skip top 3, check rest
            if len(weak_matches) >= 5:
                break
            if r.get('wiki_movie_id') not in [m['wiki_movie_id'] for m in strong_matches + weak_matches]:
                weak_matches.append({
                    "wiki_movie_id": r.get('wiki_movie_id'),
                    "movie_name": r.get('movie_name'),
                    "release_date": r.get('release_date'),
                    "score": r.get('_score', 0)
                })
    
    return strong_matches, weak_matches

def generate_test_samples():
    """Generate 10 test samples by running BM25 retrieval and auto-selecting matches"""
    print("🚀 Starting automatic test sample generation...")
    
    # Load all data
    chunk_paths = get_all_chunk_paths("data")
    print(f"📚 Loading data files: {len(chunk_paths)} chunks")
    
    all_movies = load_all_movies(chunk_paths)
    print(f"🎬 Total movies loaded: {len(all_movies)} movies")
    
    new_samples = []
    
    for idx, selected in enumerate(SELECTED_MOVIES, 1):
        movie_id = selected['wiki_movie_id']
        query = selected['query']
        
        print(f"\n{'='*80}")
        print(f"[{idx}/10] Processing: {query[:60]}...")
        
        # Find the source movie
        source_movie = find_movie_by_id(all_movies, movie_id)
        if not source_movie:
            print(f"⚠️  Movie {movie_id} not found, skipping")
            continue
        
        print(f"    Source: {source_movie['movie_name']} ({source_movie['release_date']})")
        
        # Run BM25 retrieval
        print(f"    🔍 Running BM25 retrieval...")
        results = bm25_retrieval(
            json_path_list=chunk_paths,
            query=query,
            top_k=50,
            title_key="movie_name",
            summary_key="summary",
            return_fields=["movie_name", "release_date", "summary", "wiki_movie_id", "genres"]
        )
        
        if not results:
            print(f"    ⚠️  No retrieval results, skipping")
            continue
        
        print(f"    ✅ Found {len(results)} results")
        
        # Auto-select matches
        strong_matches, weak_matches = auto_select_matches(results, movie_id)
        
        print(f"    📊 Strong: {len(strong_matches)} movies, Weak: {len(weak_matches)} movies")
        
        # Build sample
        sample = {
            "query": query,
            "source": {
                "wiki_movie_id": movie_id,
                "movie_name": source_movie['movie_name']
            },
            "strong_matches": strong_matches,
            "weak_matches": weak_matches
        }
        
        new_samples.append(sample)
        
        # Display matched movies
        print(f"    Strong matches:")
        for m in strong_matches[:2]:
            print(f"      - {m['movie_name']} ({m['release_date']}) [{m['score']:.2f}]")
        print(f"    Weak matches:")
        for m in weak_matches[:3]:
            print(f"      - {m['movie_name']} ({m['release_date']}) [{m['score']:.2f}]")
    
    print(f"\n{'='*80}")
    print(f"✅ Generation complete! Total: {len(new_samples)} samples")
    
    return new_samples

def save_samples(new_samples, output_path="data/test_data.json"):
    """Save samples to file by appending to existing samples"""
    # Load existing samples
    existing = []
    if Path(output_path).exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    
    print(f"\n📝 Existing samples: {len(existing)} samples")
    
    # Append new samples
    existing.extend(new_samples)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=4)
    
    print(f"💾 Saved to: {output_path}")
    print(f"📊 Total samples: {len(existing)} samples")

def main():
    print("="*80)
    print("Automatic Test Sample Generator")
    print("="*80)
    
    # Generate samples
    new_samples = generate_test_samples()
    
    if not new_samples:
        print("\n❌ No samples generated")
        return
    
    # Confirm save
    print(f"\n{'='*80}")
    print("Ready to save to data/test_data.json")
    confirm = input("Save to file? (y/n): ").strip().lower()
    
    if confirm == 'y':
        save_samples(new_samples)
        print("\n✅ Done!")
    else:
        print("\n❌ Cancelled")
        # Optional: save to temporary file
        temp_path = "data/test_data_new.json"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(new_samples, f, ensure_ascii=False, indent=4)
        print(f"💾 New samples saved to: {temp_path}")

if __name__ == "__main__":
    main()

