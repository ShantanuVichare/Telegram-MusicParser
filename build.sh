#!/usr/bin/env bash
# Exit on error
set -o errexit

uname -a

# Remove existing miniconda installation
if [ -d "$HOME/miniconda" ];
then
    echo "Existing miniconda installation found"
    # echo "Removing existing miniconda installation"
    # rm -rf $HOME/miniconda
else
    echo "No existing miniconda installation found... Installing Miniconda"
    # Install Miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -q -O miniconda.sh
    bash miniconda.sh -b -p $HOME/miniconda
fi

export PATH="$HOME/miniconda/bin:$PATH"
conda init bash
source ~/.bashrc

# Check if the conda environment already exists
if conda env list | grep -q 'music-parser'; then
    echo "Conda environment 'music-parser' already exists. Updating environment."
    conda env update -f environment.yml -n music-parser
else
    echo "Conda environment 'music-parser' does not exist. Creating new environment."
    conda env create -f environment.yml -n music-parser
fi

# Activate conda environment
conda activate music-parser

# Modify this line as needed for your package manager (pip, poetry, etc.)
# pip install -r requirements.txt

