#!/usr/bin/env bash

python "$MEDVIEW_BASE_DIR/server/setup.py" build_ext --inplace
flask run --port=8001 --no-reload