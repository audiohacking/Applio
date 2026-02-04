#!/bin/bash
# ---------------------------------------------------------------------------
#  Applio - Local macOS Build Script
#  Replicates .github/workflows/build-macos-release.yml for local testing.
#  Steps are kept in sync with the workflow so local and CI behave the same.
# ---------------------------------------------------------------------------

set -e  # Exit on error

echo "=========================================="
echo "Applio - Local macOS Build"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# --- Step: Set up Python (GA: actions/setup-python@v5, python-version: '3.11') ---
if ! command -v python3.11 &> /dev/null && ! python3 --version 2>&1 | grep -q "3.11"; then
    echo "ERROR: Python 3.11 not found"
    echo "GitHub Actions uses Python 3.11. Please install it for consistent builds."
    exit 1
fi

PYTHON="python3"
if command -v python3.11 &> /dev/null; then
    PYTHON="python3.11"
fi

echo "Using Python: $($PYTHON --version)"
echo ""

# --- Step: Install system dependencies (GA: brew install imagemagick) ---
echo "Checking system dependencies..."
if ! command -v convert &> /dev/null && ! command -v magick &> /dev/null; then
    echo "WARNING: ImageMagick not found; icon generation may use Python fallback."
    echo "For parity with CI: brew install imagemagick"
    echo ""
fi

# --- Step: Install Python dependencies (GA: pip upgrade + requirements_macos.txt) ---
echo "Installing Python dependencies..."
$PYTHON -m pip install --upgrade pip
$PYTHON -m pip install -r requirements_macos.txt

echo "Verifying critical dependencies (same checks as GitHub Actions)..."
MISSING=""
for pkg in webrtcvad-wheels pyinstaller torch gradio pywebview; do
    if ! $PYTHON -m pip show "$pkg" &>/dev/null; then
        MISSING="${MISSING} ${pkg}"
    fi
done
if [ -n "$MISSING" ]; then
    echo "ERROR: Missing package(s):$MISSING"
    echo "Run: $PYTHON -m pip install -r requirements_macos.txt"
    exit 1
fi
echo "✓ Critical packages present (webrtcvad-wheels, pyinstaller, torch, gradio, pywebview)"
echo ""

# --- Step: Generate app icon (GA: generate_icon.sh) ---
echo "Generating app icon..."
chmod +x build/macos/generate_icon.sh
export PYTHON
./build/macos/generate_icon.sh

echo ""

# --- Step: Check build assets (GA: Check build/macos assets) ---
echo "Checking build assets..."
if [ ! -f "build/macos/Applio.icns" ]; then
    echo "ERROR: build/macos/Applio.icns not found after generation."
    exit 1
fi
if [ ! -f "build/macos/codesign.sh" ]; then
    echo "ERROR: build/macos/codesign.sh not found."
    exit 1
fi
if [ ! -f ".github/DMG_README.txt" ]; then
    echo "ERROR: .github/DMG_README.txt not found."
    exit 1
fi
echo "✓ All build assets present"
echo ""

# --- Step: Clean previous PyInstaller outputs (GA: Clean previous PyInstaller outputs) ---
echo "Cleaning previous builds..."
rm -rf dist/Applio.app build/Applio

# --- Step: Build with PyInstaller (GA: Build with PyInstaller) ---
echo "Building with PyInstaller..."
$PYTHON -m PyInstaller Applio.spec --clean --noconfirm

echo ""

# --- Step: Set up app bundle executable (GA: Set up app bundle executable) ---
echo "Setting up app bundle executable..."
cp dist/Applio.app/Contents/MacOS/Applio_bin dist/Applio.app/Contents/MacOS/Applio
chmod +x dist/Applio.app/Contents/MacOS/Applio

# --- Step: Code sign (GA: Code sign the app bundle, identity from env or '-') ---
echo "Code signing app bundle..."
chmod +x build/macos/codesign.sh
MACOS_SIGNING_IDENTITY="${MACOS_SIGNING_IDENTITY:--}" ./build/macos/codesign.sh dist/Applio.app

echo ""
echo "=========================================="
echo "✓ Build Complete!"
echo "=========================================="
echo ""
echo "App: dist/Applio.app"
echo ""
echo "To test:"
echo "  open dist/Applio.app"
echo ""
echo "If blocked by Gatekeeper:"
echo "  xattr -cr dist/Applio.app"
echo "  (then right-click → Open)"
echo ""
