#!/bin/bash
# Build standalone binary for agrr CLI
# Supports both --onefile (single binary) and --onedir (fast startup) formats

set -e

# Parse command line arguments
BUILD_FORMAT="onedir"  # Default to onedir for faster startup
PACKAGE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --onefile)
            BUILD_FORMAT="onefile"
            PACKAGE=false
            shift
            ;;
        --onedir)
            BUILD_FORMAT="onedir"
            PACKAGE=true
            shift
            ;;
        --no-package)
            PACKAGE=false
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --onefile       Build single binary (slower startup ~6s, 125MB)"
            echo "  --onedir        Build directory bundle (fast startup ~2s, 353MB) [default]"
            echo "  --no-package    Skip packaging step for onedir build"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Build onedir with packaging (recommended)"
            echo "  $0 --onefile    # Build single binary"
            echo "  $0 --onedir --no-package  # Build onedir without packaging"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "=== Building standalone binary for agrr ==="
echo "Format: $BUILD_FORMAT"
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

if [ "$BUILD_FORMAT" = "onefile" ]; then
    echo "Step 3: Building with PyInstaller (--onefile format)..."
    $PYTHON_CMD -m PyInstaller \
        --onefile \
        --name agrr \
        --console \
        --clean \
        --noconfirm \
        --collect-all agrr_core \
        --add-data "prompts:prompts" \
        --paths src \
        --hidden-import agrr_core.daemon \
        --hidden-import agrr_core.daemon.server \
        --hidden-import agrr_core.daemon.client \
        --hidden-import agrr_core.daemon.manager \
        --exclude-module matplotlib \
        --exclude-module pytest \
        --exclude-module pygments \
        --exclude-module py \
        src/agrr_core/__main__.py

    if [ -f dist/agrr ]; then
        echo ""
        echo "✓ Successfully built standalone binary (--onefile)!"
        echo "✓ Location: dist/agrr"
        echo "✓ Size:"
        ls -lh dist/agrr
        echo ""
        echo "Note: --onefile format has ~6s startup time due to extraction."
        echo "      Use --onedir for faster startup (~2s)."
    else
        echo ""
        echo "❌ Build failed. Binary not created."
        exit 1
    fi
else
    echo "Step 3: Building with PyInstaller (--onedir format for fast startup)..."
    $PYTHON_CMD -m PyInstaller \
        --onedir \
        --name agrr \
        --console \
        --clean \
        --noconfirm \
        --collect-all agrr_core \
        --add-data "prompts:prompts" \
        --paths src \
        --hidden-import agrr_core.daemon \
        --hidden-import agrr_core.daemon.server \
        --hidden-import agrr_core.daemon.client \
        --hidden-import agrr_core.daemon.manager \
        --exclude-module matplotlib \
        --exclude-module pytest \
        --exclude-module pygments \
        --exclude-module py \
        src/agrr_core/__main__.py

    if [ -f dist/agrr/agrr ]; then
        echo ""
        echo "✓ Successfully built standalone binary (--onedir)!"
        echo "✓ Location: dist/agrr/"
        echo "✓ Size:"
        du -sh dist/agrr
        
        if [ "$PACKAGE" = true ]; then
            echo ""
            echo "Step 4: Creating distribution package..."
            
            # Create package directory
            PACKAGE_NAME="agrr-$(date +%Y%m%d)"
            PACKAGE_DIR="dist/$PACKAGE_NAME"
            
            echo "Package name: $PACKAGE_NAME"
            mkdir -p "$PACKAGE_DIR"
            
            # Copy agrr directory
            echo "Copying files..."
            cp -r dist/agrr/* "$PACKAGE_DIR/"
            
            # Create README
            cat > "$PACKAGE_DIR/README.txt" << 'EOF'
agrr - Agricultural Resource & Risk management CLI
===================================================

Installation:
-------------

1. Extract this directory anywhere:
   tar -xzf agrr-YYYYMMDD.tar.gz

2. Run directly:
   ./agrr --help

3. Or install system-wide:
   sudo mv agrr /opt/
   sudo ln -s /opt/agrr/agrr /usr/local/bin/agrr

System Requirements:
-------------------

- Linux (Ubuntu 18.04+, Debian, WSL2, etc.)
- x86_64 architecture
- No Python installation required
- No additional dependencies required

Performance:
-----------

- Fast startup: ~2 seconds (vs ~6s for single binary)
- All dependencies included
- No extraction overhead

Usage:
------

  agrr weather --help
  agrr optimize --help
  agrr crop --help

All dependencies are included in the _internal/ directory.

Version Information:
-------------------

EOF

            # Add version info
            if [ -f "src/agrr_core/__init__.py" ]; then
                grep "^__version__" src/agrr_core/__init__.py >> "$PACKAGE_DIR/README.txt" || echo "Version: Latest" >> "$PACKAGE_DIR/README.txt"
            else
                echo "Version: Latest" >> "$PACKAGE_DIR/README.txt"
            fi
            
            echo "Build Date: $(date)" >> "$PACKAGE_DIR/README.txt"
            
            # Create tarball
            TARBALL="dist/${PACKAGE_NAME}.tar.gz"
            echo "Creating tarball: $TARBALL"
            tar -czf "$TARBALL" -C "dist" "$PACKAGE_NAME"
            
            # Show results
            echo ""
            echo "✓ Package created successfully!"
            echo "✓ Package size:"
            du -h "$TARBALL"
            echo ""
            echo "Distribution file: $TARBALL"
            
            # Cleanup
            rm -rf "$PACKAGE_DIR"
            echo "Temporary directory cleaned up."
        else
            echo ""
            echo "Note: Skipping packaging step (--no-package specified)"
        fi
    else
        echo ""
        echo "❌ Build failed. Binary not created."
        exit 1
    fi
fi

echo ""
echo "Testing binary..."
if [ "$BUILD_FORMAT" = "onefile" ]; then
    ./dist/agrr --help | head -10
else
    ./dist/agrr/agrr --help | head -10
fi

echo ""
echo "Binary is ready for distribution!"

if [ "$BUILD_FORMAT" = "onedir" ]; then
    echo ""
    echo "Usage:"
    if [ "$PACKAGE" = true ]; then
        echo "  Distribution: dist/agrr-$(date +%Y%m%d).tar.gz"
        echo "  Extract and run: ./agrr-$(date +%Y%m%d)/agrr --help"
    else
        echo "  Direct run: ./dist/agrr/agrr --help"
    fi
    echo ""
    echo "Performance: ~2s startup (vs ~6s for --onefile)"
fi
