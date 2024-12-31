#!/usr/bin/env bash

uname -a

export PROJECT_ROOT=$RENDER_PROJECT_ROOT
# export PROJECT_ROOT=$HOME/project
echo "Project root: $PROJECT_ROOT"

export PATH="$PROJECT_ROOT/miniconda/bin:$PATH"
conda init bash
source ~/.bashrc

conda activate music-parser

echo "Running python from $(which python)"

python src/bot.py
