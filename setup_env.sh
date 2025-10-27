#!/bin/bash
# Setup script for plot_finder conda environment

echo "=========================================="
echo "Plot Finder Environment Setup"
echo "=========================================="

# Create conda environment
echo ""
echo "📦 Creating conda environment 'plot_finder'..."
conda env create -f environment.yml

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Environment created successfully!"
    echo ""
    echo "To activate the environment, run:"
    echo "    conda activate plot_finder"
    echo ""
    echo "Then you can run:"
    echo "    python auto_generate_samples.py"
    echo "    python annotation_helper.py --query 'your query here'"
else
    echo ""
    echo "❌ Failed to create environment"
    echo ""
    echo "If the environment already exists, update it with:"
    echo "    conda env update -f environment.yml --prune"
fi

