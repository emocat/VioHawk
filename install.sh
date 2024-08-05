#!/bin/bash

sudo apt-get update && apt-get install -y \
    git \
    wget \
    gcc

# miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir ~/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh

export PATH="~/miniconda3/bin:${PATH}"
conda init && conda create -n viohawk python=3.7 -y -q
source ~/miniconda3/bin/activate viohawk

# lgsvl
cd PythonAPI
pip install -r requirements.txt --user .
cd ..

# viohawk
cd VioHawk
pip install -r requirements.txt
pip install opencv-python-headless
cd ..

patch ~/miniconda3/envs/viohawk/lib/python3.7/site-packages/commonroad_reach/utility/coordinate_system.py coordinate_system.py.patch
patch ~/miniconda3/envs/viohawk/lib/python3.7/site-packages/commonroad_reach/data_structure/configuration.py configuration.py.patch
