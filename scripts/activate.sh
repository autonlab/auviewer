#!/usr/bin/env bash

conda activate medview
cd /zfsauton2/home/gwelter/code/medview/server
export FLASK_APP=serve.py
export FLASK_ENV=development
