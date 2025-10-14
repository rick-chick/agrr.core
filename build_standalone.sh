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

# Setup pyenv if available
if [ -d "$HOME/.pyenv" ]; then
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
    echo "pyenv detected and initialized"
fi

# Check if Python 3.12 with shared library is available
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    # Check if _ctypes module is available (indicates proper build with libffi)
    if python3.12 -c "import _ctypes" 2>/dev/null; then
        # Check if shared library exists
        PYTHON_LIB=$(python3.12 -c "import sys; print(sys.base_prefix)")/lib/libpython3.12.so
        if [ -f "$PYTHON_LIB" ] || [ -f "$PYTHON_LIB.1.0" ]; then
            PYTHON_CMD="python3.12"
            echo "✓ Found Python 3.12 with shared library support"
        fi
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3.12 with shared library support not found!"
    echo ""
    echo "Please install Python 3.12 with shared library using pyenv:"
    echo ""
    echo "  # Install build dependencies first:"
    echo "  sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \\"
    echo "      libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \\"
    echo "      libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \\"
    echo "      libffi-dev liblzma-dev"
    echo ""
    echo "  # Install Python 3.12 with shared library:"
    echo "  export PATH=\"\$HOME/.pyenv/bin:\$PATH\""
    echo "  eval \"\$(pyenv init -)\""
    echo "  pyenv uninstall -f 3.12.8 2>/dev/null || true"
    echo "  env PYTHON_CONFIGURE_OPTS=\"--enable-shared\" pyenv install 3.12.8"
    echo "  pyenv local 3.12.8"
    echo ""
    exit 1
fi

echo "Step 1: Installing PyInstaller for Python 3.12..."
$PYTHON_CMD -m pip install pyinstaller --upgrade --quiet

echo "Step 2: Cleaning previous builds..."
rm -rf build dist

echo "Step 3: Building with PyInstaller (Python 3.12)..."
$PYTHON_CMD -m PyInstaller \
    --onefile \
    --name agrr \
    --console \
    --clean \
    --noconfirm \
    --collect-all agrr_core \
    --add-data "prompts:prompts" \
    --paths src \
    src/agrr_core/cli.py

# Note: Python 3.12 with shared library is required for PyInstaller and LightGBM

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

