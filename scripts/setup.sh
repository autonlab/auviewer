#!/usr/bin/env bash

conda create --name medview python=3.6
conda activate medview
conda install flask cython h5py psutil simplejson
pip install htmlmin Flask-User==0.6.21
pip uninstall Flask-User
