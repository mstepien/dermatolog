#!/bin/bash

# Get the directory where the script is located
BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$BIN_DIR")"

echo "Checking and downloading models for Dermatolog AI..."

# Use the same python executable as the app (or just python3)
# Based on previous turns, /usr/local/opt/python@3.8/bin/python3.8 was used
PYTHON_EXEC="/usr/local/opt/python@3.8/bin/python3.8"

if [ ! -x "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="python3"
fi

$PYTHON_EXEC "$BIN_DIR/download_models.py"
