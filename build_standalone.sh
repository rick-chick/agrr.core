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

echo "Step 1: Installing PyInstaller for Python 3.8..."
python3.8 -m pip install pyinstaller --upgrade --quiet

echo "Step 2: Cleaning previous builds..."
rm -rf build dist

echo "Step 3: Building with PyInstaller (Python 3.8)..."
python3.8 -m PyInstaller \
    --onefile \
    --name agrr \
    --console \
    --clean \
    --noconfirm \
    --collect-all agrr_core \
    --add-data "prompts:prompts" \
    --paths src \
    src/agrr_core/cli.py

# Note: Python 3.8 is used because it has libpython available in WSL
# Python 3.12 requires libpython3.12-dev which needs sudo

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

