#!/bin/bash

# Exit on error
set -e

echo "Generating Python models..."

# Find datamodel-codegen in path or venv
if command -v datamodel-codegen >/dev/null 2>&1; then
    CODEGEN_BIN="datamodel-codegen"
elif [ -f "./venv/bin/datamodel-codegen" ]; then
    CODEGEN_BIN="./venv/bin/datamodel-codegen"
else
    echo "datamodel-codegen not found. Attempting to install..."
    pip install datamodel-code-generator || ./venv/bin/pip install datamodel-code-generator
    CODEGEN_BIN="datamodel-codegen"
    if ! command -v "$CODEGEN_BIN" >/dev/null 2>&1 && [ -f "./venv/bin/datamodel-codegen" ]; then
        CODEGEN_BIN="./venv/bin/datamodel-codegen"
    fi
fi

if ! "$CODEGEN_BIN" --input openapi.yaml --output app/models.py; then
    echo "Error: Python model generation failed. Check openapi.yaml for syntax errors."
    exit 1
fi

echo "API Generation for Python Complete!"
