#!/usr/bin/env python3
"""Build device-sized, four-gray-level BMP wallpaper images from color sources.

Requires Pillow. Center-crops to the requested aspect ratio before resizing and
dithering. Deduplicates byte-identical inputs, leaving sources untouched.
The BMP is uncompressed, bottom-up 2bpp with four native gray palette entries.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path

from PIL import Image, ImageOps


def create_bmp(source: Path, dest: Path, width: int, height: int) -> None:
    with Image.open(source) as original:
        img = ImageOps.exif_transpose(original).convert("RGB")
        img = ImageOps.fit(img, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        mono = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)

    four_shade = Image.new("P", (1, 1))
    four_shade.putpalette(
        [channel for level in (0, 85, 170, 255) for channel in (level, level, level)]
        + [255, 255, 255] * 252
    )
    reduced = mono.convert("RGB").quantize(palette=four_shade, dither=Image.Dither.FLOYDSTEINBERG)
    palette_indices = bytes(min(3, (v + 42) // 85) for v in reduced.convert("L").tobytes())

    rowbytes = ((width * 2 + 31) // 32) * 4
    pixel_data = bytearray()
    for y in range(height - 1, -1, -1):
        raw_row = palette_indices[y * width:(y + 1) * width]
        output_row = bytearray(rowbytes)
        for x, level in enumerate(raw_row):
            output_row[x // 4] |= level << (6 - (x % 4) * 2)
        pixel_data.extend(output_row)

    palette_bytes = b"".join(bytes((level, level, level, 0)) for level in (0, 85, 170, 255))
    offset = 14 + 40 + len(palette_bytes)
    header = struct.pack("<2sIHHI", b"BM", offset + len(pixel_data), 0, 0, offset)
    dib = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 2, 0, len(pixel_data), 2835, 2835, 4, 4)
    dest.write_bytes(header + dib + palette_bytes + pixel_data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    args = parser.parse_args()
    if not args.source.is_dir():
        parser.error("source directory is missing")
    if not (0 < args.width <= 2048 and 0 < args.height <= 3072):
        parser.error("target dimensions are outside the firmware limits")
    originals = sorted(
        (x for x in args.source.iterdir() if x.is_file() and x.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")),
        key=lambda x: (bool(re.search(r" \\(\\d+\\)$", x.stem)), x.name.lower()),
    )
    seen: set[str] = set()
    unique: list[Path] = []
    for file in originals:
        sha = hashlib.sha256(file.read_bytes()).hexdigest()
        if sha in seen:
            print(f"Skipping byte-identical duplicate: {file.name}")
            continue
        seen.add(sha)
        unique.append(file)
    if not 1 <= len(unique) <= 32:
        parser.error("the wallpaper-pack contract supports 1–32 unique images")
    names = []
    for f in unique:
        safe = re.sub(r"[^a-z0-9_-]+", "-", f.stem.lower()).strip("-")
        if not safe or len(safe) > 80 or safe in names:
            parser.error(f"invalid or colliding output name: {f.name}")
        names.append(safe)
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error("output directory must be empty; refusing to overwrite other work")
    for file, name in zip(unique, names):
        dest = args.output / (name + ".bmp")
        create_bmp(file, dest, args.width, args.height)
        print(f"{dest.name}: {args.width}x{args.height}, {dest.stat().st_size} bytes")
    print(f"Created {len(unique)} unique wallpapers; skipped {len(originals) - len(unique)} duplicates")


if __name__ == "__main__":
    main()
