#!/usr/bin/env python3
"""
photo_to_ascii.py — converts a photo to an ASCII portrait for the profile card.

Handles white/light backgrounds by treating near-white pixels as spaces,
so only actual face pixels become ASCII characters.
"""

from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────
INPUT_FILE  = "Gemini_Generated_Image_6muc1q6muc1q6muc.png"
OUTPUT_FILE = "portrait.txt"

COLS = 96          # characters wide  (must match ART_CW * COLS < INFO_X - ART_X)
ROWS = 44          # lines tall        (match portrait area in SVG)

# White-background threshold: pixels brighter than this become spaces
# 0-255; increase to treat more grey as background
BG_THRESHOLD = 210

# Characters from darkest → lightest (face shading)
CHARS = "@%#*+=-:. "

# How much to boost contrast before conversion (1.0 = no change)
CONTRAST = 1.6
SHARPNESS = 1.4
# ────────────────────────────────────────────────────────────────────────────


def luminance(r, g, b):
    """Perceived brightness (0=black, 255=white)."""
    return 0.299 * r + 0.587 * g + 0.114 * b


def is_background(r, g, b):
    """True if this pixel is near-white background."""
    return r > BG_THRESHOLD and g > BG_THRESHOLD and b > BG_THRESHOLD


def pixel_to_char(r, g, b):
    if is_background(r, g, b):
        return " "
    lum = luminance(r, g, b)
    idx = int(lum / 255 * (len(CHARS) - 1))
    return CHARS[idx]


def image_to_ascii(img_path, cols, rows):
    img = Image.open(img_path).convert("RGB")

    # Crop: find the bounding box of non-white pixels to auto-center on face
    import numpy as np
    arr = __import__("numpy").array(img)
    mask = (arr[:, :, 0] < BG_THRESHOLD) | \
           (arr[:, :, 1] < BG_THRESHOLD) | \
           (arr[:, :, 2] < BG_THRESHOLD)
    rows_with_face = __import__("numpy").any(mask, axis=1)
    cols_with_face = __import__("numpy").any(mask, axis=0)
    rmin, rmax = __import__("numpy").where(rows_with_face)[0][[0, -1]]
    cmin, cmax = __import__("numpy").where(cols_with_face)[0][[0, -1]]

    # Add padding around detected face
    pad_r = int((rmax - rmin) * 0.05)
    pad_c = int((cmax - cmin) * 0.05)
    h, w = arr.shape[:2]
    rmin = max(0, rmin - pad_r)
    rmax = min(h - 1, rmax + pad_r)
    cmin = max(0, cmin - pad_c)
    cmax = min(w - 1, cmax + pad_c)

    img = img.crop((cmin, rmin, cmax + 1, rmax + 1))

    # Enhance contrast and sharpness for crisper ASCII
    img = ImageEnhance.Contrast(img).enhance(CONTRAST)
    img = ImageEnhance.Sharpness(img).enhance(SHARPNESS)

    # Resize to target ASCII dimensions
    # Chars are roughly 2× taller than wide, so compensate height
    char_aspect = 0.55   # width/height ratio of a monospace character
    target_w = cols
    target_h = int(rows / char_aspect)
    img = img.resize((target_w, target_h), Image.LANCZOS)

    # Build ASCII lines
    lines = []
    for y in range(rows):
        # Sample one row from the resized image
        row_y = int(y * (target_h / rows))
        row_chars = []
        for x in range(cols):
            r, g, b = img.getpixel((x, row_y))
            row_chars.append(pixel_to_char(r, g, b))
        lines.append("".join(row_chars))

    return lines


def main():
    img_path = Path(__file__).parent / INPUT_FILE
    if not img_path.exists():
        print(f"ERROR: {INPUT_FILE} not found")
        return

    print(f"Converting {INPUT_FILE} → {OUTPUT_FILE} ({COLS}×{ROWS})...")
    lines = image_to_ascii(img_path, COLS, ROWS)

    out = Path(__file__).parent / OUTPUT_FILE
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Done! Wrote {len(lines)} lines to {OUTPUT_FILE}")

    # Preview first few lines
    print("\nPreview (first 5 lines):")
    for l in lines[:5]:
        print(l[:60] + "...")


if __name__ == "__main__":
    main()
