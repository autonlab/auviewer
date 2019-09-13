#!/usr/bin/env bash

. config.sh
rm -rf "$MEDVIEW_BASE_DIR/server/cylib.c" "$MEDVIEW_BASE_DIR/server/cylib.cpython"*
python "$MEDVIEW_BASE_DIR/server/setup.py" build_ext --build-lib "$MEDVIEW_BASE_DIR/server/"
rm -rf build
python "$MEDVIEW_BASE_DIR/server/serve.py"