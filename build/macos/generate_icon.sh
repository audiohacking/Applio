#!/bin/bash
# Generate Applio.icns from ICO file for macOS app bundle
# Converts the Windows ICO to macOS ICNS format

set -e

ICO_FILE="assets/ICON.ico"
ICONSET_DIR="build/macos/Applio.iconset"
OUTPUT_ICNS="build/macos/Applio.icns"

if [ ! -f "$ICO_FILE" ]; then
    echo "Error: Icon file not found at $ICO_FILE"
    exit 1
fi

# Prefer ImageMagick 7 (magick) or 6 (convert); fallback to sips; ultimate fallback to Python
USE_IM=
if command -v magick &> /dev/null; then
    USE_IM=magick
elif command -v convert &> /dev/null; then
    USE_IM=convert
fi

# Note: If neither ImageMagick nor sips is available, we'll use Python fallback
# The sips command is typically available on macOS but may not be on CI runners
if [ -z "$USE_IM" ] && ! command -v sips &> /dev/null; then
    echo "Warning: ImageMagick (magick/convert) or sips not found."
    echo "Will use Python fallback to generate icon."
fi

rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"

echo "Generating icon sizes from ICO file..."

# Convert ICO to PNG first (largest size)
TEMP_PNG="build/macos/temp_icon.png"
if [ -n "$USE_IM" ]; then
    if [ "$USE_IM" = "magick" ]; then
        magick "$ICO_FILE" -background none -alpha set -alpha on -resize 1024x1024 "PNG32:$TEMP_PNG" || true
    else
        convert "$ICO_FILE" -background none -alpha set -alpha on -resize 1024x1024 "PNG32:$TEMP_PNG" || true
    fi
else
    sips -s format png "$ICO_FILE" --out "$TEMP_PNG" || true
fi

# Fallback: Generate icon using Python if conversion failed
if [ ! -f "$TEMP_PNG" ]; then
    echo "⚠ Icon conversion failed, generating fallback icon..."
    python3 build/macos/generate_fallback_icon.py "$TEMP_PNG"
fi

# Verify temp icon exists
if [ ! -f "$TEMP_PNG" ]; then
    echo "Error: Failed to create temp icon at $TEMP_PNG"
    exit 1
fi

sizes=(16 32 128 256 512)
for size in "${sizes[@]}"; do
    echo "  Generating ${size}x${size}..."
    double=$((size * 2))
    if [ -n "$USE_IM" ]; then
        if [ "$USE_IM" = "magick" ]; then
            magick "$TEMP_PNG" -resize ${size}x${size} "PNG32:$ICONSET_DIR/icon_${size}x${size}.png"
            magick "$TEMP_PNG" -resize ${double}x${double} "PNG32:$ICONSET_DIR/icon_${size}x${size}@2x.png"
        else
            convert "$TEMP_PNG" -resize ${size}x${size} "PNG32:$ICONSET_DIR/icon_${size}x${size}.png"
            convert "$TEMP_PNG" -resize ${double}x${double} "PNG32:$ICONSET_DIR/icon_${size}x${size}@2x.png"
        fi
    else
        sips -z $size $size "$TEMP_PNG" --out "$ICONSET_DIR/icon_${size}x${size}.png"
        sips -z $double $double "$TEMP_PNG" --out "$ICONSET_DIR/icon_${size}x${size}@2x.png"
    fi
done

echo "Creating .icns file..."
iconutil -c icns "$ICONSET_DIR" -o "$OUTPUT_ICNS"

rm -rf "$ICONSET_DIR"
rm -f "$TEMP_PNG"

echo "✓ Icon created: $OUTPUT_ICNS"
ls -lh "$OUTPUT_ICNS"
