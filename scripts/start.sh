#!/usr/bin/env bash

###
### This script starts the AUView server. The environment must have been created
### previously with the setup_env.sh script.
###

# Detect the code base directory
export MEDVIEW_BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. >/dev/null 2>&1 && pwd )"
echo $MEDVIEW_BASE_DIR
# Set the python path so that code not in the medview/server folder can use the
# modules contained therein.
if [[ $PYTHONPATH != *$MEDVIEW_BASE_DIR/server* ]]
then
    export PYTHONPATH=$MEDVIEW_BASE_DIR/server:$PYTHONPATH
fi

# Activate the conda environment
conda activate medview

# Build cython & clean
rm -rf "$MEDVIEW_BASE_DIR/server/cylib.c" "$MEDVIEW_BASE_DIR/server/cylib.cpython"*
python "$MEDVIEW_BASE_DIR/server/setup.py" build_ext --build-lib "$MEDVIEW_BASE_DIR/server/"
rm -rf build

# Run the server
python "$MEDVIEW_BASE_DIR/server/serve.py"
