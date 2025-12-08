#!/bin/bash
set -e

echo "==========================================="
echo "Plot Finder: Setup and Execution Script"
echo "==========================================="

# 1. Install Dependencies
echo "[1/4] Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# 2. Step 0: Read Raw Data
echo "[2/4] Running Step 0: Read Raw Data (src/data_process/0_read_raw.py)..."
if [ -d "raw" ]; then
    python src/data_process/0_read_raw.py
else
    echo "WARNING: 'raw' directory not found. "
    echo "Skipping execution of 0_read_raw.py. Ensure you have 'intermediate/' data or 'raw/' data available."
    # We don't exit here because the user might already have intermediate data
fi

# 3. Step 1: Merge Movie Info
echo "[3/4] Running Step 1: Merge Movie Info (src/data_process/1_merge_movie_info.py)..."
python src/data_process/1_merge_movie_info.py

# 4. Step 2: Indexing
echo "[4/4] Running Step 2: Indexing (src/data_process/2_index.py)..."
python src/data_process/2_index.py

echo "==========================================="
echo "Pipeline execution completed successfully!"
echo "You can now run 'python demo.py' to test the search."
echo "==========================================="
