#!/usr/bin/env bash

python setup.py build_ext --inplace
flask run --port=8001 --no-reload