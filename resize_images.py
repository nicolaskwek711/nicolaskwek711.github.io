#!/usr/bin/env python3
"""
Resize all images in the images/ folder for web use.
- Preserves aspect ratio (resizes by long edge).
- Skips files already small enough.
- Saves a backup to images-original/ on first run only.
- Re-encodes JPEGs at quality 82 and optimises PNGs.

Usage:
    pip install Pillow
    python3 resize_images.py
"""

import os
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Pillow not installed. Run: pip3 install Pillow")
    sys.exit(1)

# ---- config ----
ROOT          = Path(__file__).resolve().parent
SRC_DIR       = ROOT / "images"
BACKUP_DIR    = ROOT / "images-original"
MAX_LONG_EDGE = 2000     # px
JPEG_QUALITY  = 82       # 80–85 is the sweet spot for web
EXTS          = {".jpg", ".jpeg", ".png"}
# ----------------


def human(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} TB"


def back_up_originals():
    if BACKUP_DIR.exists():
        print(f"Backup already exists at {BACKUP_DIR} — skipping backup.\n")
        return
    print(f"Backing up originals to {BACKUP_DIR} ...")
    shutil.copytree(SRC_DIR, BACKUP_DIR)
    print("Backup done.\n")


def resize_one(path: Path) -> tuple[int, int]:
    """Returns (bytes_before, bytes_after)."""
    before = path.stat().st_size
    try:
        with Image.open(path) as im:
            # Honour EXIF orientation so portraits don't end up rotated
            im = ImageOps.exif_transpose(im)

            w, h = im.size
            long_edge = max(w, h)
            needs_resize = long_edge > MAX_LONG_EDGE

            if needs_resize:
                scale = MAX_LONG_EDGE / long_edge
                new_size = (round(w * scale), round(h * scale))
                im = im.resize(new_size, Image.LANCZOS)

            ext = path.suffix.lower()
            if ext in (".jpg", ".jpeg"):
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
                im.save(path, format="JPEG", quality=JPEG_QUALITY,
                        optimize=True, progressive=True)
            elif ext == ".png":
                im.save(path, format="PNG", optimize=True)
    except Exception as e:
        print(f"  !! Failed: {path.name} — {e}")
        return before, before

    return before, path.stat().st_size


def main():
    if not SRC_DIR.exists():
        print(f"Source folder not found: {SRC_DIR}")
        sys.exit(1)

    files = [p for p in SRC_DIR.rglob("*") if p.suffix.lower() in EXTS]
    if not files:
        print("No images found.")
        return

    print(f"Found {len(files)} images under {SRC_DIR}\n")
    back_up_originals()

    total_before = 0
    total_after  = 0
    for i, path in enumerate(files, 1):
        rel = path.relative_to(ROOT)
        before, after = resize_one(path)
        total_before += before
        total_after  += after
        saved = before - after
        pct = (saved / before * 100) if before else 0
        print(f"[{i:3}/{len(files)}] {rel}  "
              f"{human(before)} → {human(after)}  ({pct:+.0f}%)")

    saved_total = total_before - total_after
    pct_total = (saved_total / total_before * 100) if total_before else 0
    print("\n----")
    print(f"Total: {human(total_before)} → {human(total_after)} "
          f"(saved {human(saved_total)}, -{pct_total:.0f}%)")
    print(f"Originals safe at: {BACKUP_DIR}")
    print("\nNext: drag the Portfolio folder onto Netlify Deploys to push.")


if __name__ == "__main__":
    main()
