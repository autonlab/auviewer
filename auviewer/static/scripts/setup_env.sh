#!/usr/bin/env bash

conda create -y --name medview python=3.6 flask cython psutil simplejson
conda activate medview
pip install --upgrade pip
pip install htmlmin watchdog Flask-User==0.6.21
pip uninstall --yes Flask-User

# For realtime functionality
pip install "python-socketio[client]"
pip install flask-socketio

# For realtime files
pip install watchdog

# audata needed for the server.
git clone https://github.com/autonlab/audata.git
cd audata
./rebuild