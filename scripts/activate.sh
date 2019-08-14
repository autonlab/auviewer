#!/usr/bin/env bash

conda activate medview
export MEDVIEW_BASE_DIR=/zfsauton2/home/gwelter/code/medview
export FLASK_APP="$MEDVIEW_BASE_DIR/server/serve.py"
export FLASK_ENV=development
