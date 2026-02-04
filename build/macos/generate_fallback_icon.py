#!/usr/bin/env python3
"""
Generate a fallback icon for Applio macOS build.
Creates a 256x256 black icon with a centered white letter 'A'.
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow library not found. Install with: pip install Pillow")
    sys.exit(1)


def generate_fallback_icon(output_path: str, size: int = 256):
    """
    Generate a simple fallback icon.
    
    Args:
        output_path: Path where the icon will be saved
        size: Size of the square icon (default: 256)
    """
    # Create a black background image
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    
    # Calculate font size and position for centered 'A'
    font_size = int(size * 0.6)  # 60% of image size
    
    # Try to use a system font, fall back to default if not available
    font = None
    font_paths = [
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/HelveticaNeue.ttc',
        '/Library/Fonts/Arial.ttf',
    ]
    
    for font_path in font_paths:
        try:
            if Path(font_path).exists():
                font = ImageFont.truetype(font_path, font_size)
                break
        except Exception:
            continue
    
    # If no font found, use default
    if font is None:
        font = ImageFont.load_default()
    
    # Draw the letter 'A' in white, centered
    text = 'A'
    
    # Get text bounding box to center it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = (
        (size - text_width) // 2 - bbox[0],
        (size - text_height) // 2 - bbox[1]
    )
    
    draw.text(position, text, fill=(255, 255, 255, 255), font=font)
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the image
    img.save(output_path, 'PNG')
    print(f"✓ Fallback icon generated: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = 'build/macos/temp_icon.png'
    
    size = 1024 if len(sys.argv) > 2 else 1024  # Use 1024 for better quality
    
    try:
        generate_fallback_icon(output_path, size)
    except Exception as e:
        print(f"Error generating fallback icon: {e}")
        sys.exit(1)
