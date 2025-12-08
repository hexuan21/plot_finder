# Plot Finder

Plot Finder is a movie plot search engine that utilizes various information retrieval techniques to find movies based on plot descriptions. It supports:
- **BM25** (Sparse Retrieval)
- **DPR** (Dense Passage Retrieval / Embedding-based search)
- **Hybrid Search** (combining BM25 and DPR)
- **Cross-Encoder Reranking** for improved accuracy

## Prerequisites

- Python 3.8+
- Required libraries listed in `requirements.txt`

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Data Preparation

The project expects raw data in a `raw/` directory at the project root.
- `raw/IMDb_tsv`: Contains IMDb TSV files (e.g., `name.basics.tsv`, `title.basics.tsv`, etc.)
- `raw/CMU_MovieSummaries`: Contains CMU Movie Summaries dataset (`movie.metadata.tsv`, `plot_summaries.txt`, etc.)

If you do not have the raw data, the data processing steps (Step 0) may adhere to creating intermediate files if they are missing or fail.

## Usage

### Automated Pipeline
To install dependencies and run the complete data processing pipeline (Data Ingestion -> Merging -> Indexing), run the provided script:

```bash
bash setup_and_run.sh
```

### Manual Execution
You can run the pipeline steps individually:

1.  **Read Raw Data**:
    ```bash
    python src/data_process/0_read_raw.py
    ```
    *Converts raw TSV/TXT data into JSON format in `intermediate/`.*

2.  **Merge Movie Info**:
    ```bash
    python src/data_process/1_merge_movie_info.py
    ```
    *Merges metadata and plot summaries into a unified format in `data/`.*

3.  **Indexing**:
    ```bash
    python src/data_process/2_index.py
    ```
    *Generates embeddings for the movies and saves them to `data/embed/`.*

### Running the Search Demo
Once the data is processed and indexed, you can run the demo script to perform searches:

```bash
python demo.py
```
This script demonstrates BM25, DPR, Hybrid search, and Reranking with sample queries.

## Project Structure
- `src/`: Source code for data processing and retrieval.
- `data/`: Processed data and embeddings.
- `assets/`: Images and figures.
- `scripts/`: Utility scripts.