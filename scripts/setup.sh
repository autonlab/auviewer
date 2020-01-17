#!/usr/bin/env bash

conda create -y --name medview python=3.6
conda activate medview
conda install -y flask cython h5py psutil simplejson
pip install --upgrade pip
pip install htmlmin Flask-User==0.6.21
pip uninstall --yes Flask-User

# Packages for realtime functionality
pip install "python-socketio[client]"
pip install flask-socketio
