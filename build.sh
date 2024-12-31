#!/usr/bin/env bash
# Exit on error
set -o errexit

conda env create -f environment.yml -n music-parser
conda activate music-parser

# Modify this line as needed for your package manager (pip, poetry, etc.)
# pip install -r requirements.txt

