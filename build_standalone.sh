#!/bin/bash
# Build standalone binary for agrr CLI

set -e

echo "=== Building standalone binary for agrr ==="
echo ""

# Check if running in WSL
if grep -qi microsoft /proc/version; then
    echo "Detected WSL environment"
    echo ""
fi

echo "Step 1: Installing PyInstaller..."
pip install pyinstaller --upgrade --quiet

echo "Step 2: Cleaning previous builds..."
rm -rf build dist *.spec

echo "Step 3: Building with PyInstaller..."
pyinstaller \
    --onefile \
    --name agrr \
    --console \
    --clean \
    --noconfirm \
    --collect-all agrr_core \
    --hidden-import agrr_core \
    --hidden-import agrr_core.cli \
    --hidden-import pandas \
    --hidden-import numpy \
    --hidden-import scipy \
    --hidden-import statsmodels \
    --hidden-import requests \
    --hidden-import openai \
    --hidden-import dotenv \
    --hidden-import matplotlib \
    --paths src \
    src/agrr_core/cli.py

if [ -f dist/agrr ]; then
    echo ""
    echo "✓ Successfully built standalone binary!"
    echo "✓ Location: dist/agrr"
    ls -lh dist/agrr
    echo ""
    echo "Testing binary..."
    ./dist/agrr --help | head -10
    echo ""
    echo "Binary is ready for distribution!"
else
    echo ""
    echo "❌ Build failed. Binary not created."
    exit 1
fi

