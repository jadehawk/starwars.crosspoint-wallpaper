#!/usr/bin/env python3
"""Build the README contact sheet from original artwork, not dithered device BMPs."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

PACK = "starwars-x3.crosspoint-wallpaper"
PREVIEW = Path("docs/previews/starwars-gallery.png")
IMAGE_NAME = re.compile(r"wallpapers/[a-zA-Z0-9_-][a-zA-Z0-9_.-]*\.bmp\Z")
SOURCE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
COUNT = 19
TARGET_SIZE = (528, 792)
THUMB_SIZE = (160, 240)


def images_from_manifest(pack: Path) -> list[Path]:
    """Return validated wallpaper paths in the exact device manifest order."""
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    images = manifest.get("images")
    if not isinstance(images, list) or len(images) != COUNT:
        raise ValueError(f"expected exactly {COUNT} images in the X3 manifest")
    if any(not isinstance(path, str) or not IMAGE_NAME.fullmatch(path) for path in images):
        raise ValueError("invalid wallpaper image path in manifest")
    if len(set(images)) != COUNT:
        raise ValueError("duplicate wallpaper image in manifest")
    return [pack / name for name in images]


def source_filename_stem(path: Path) -> str:
    """Match the naming convention used by convert_wallpaper_batch.py."""
    return re.sub(r"[^a-z0-9_-]+", "-", path.stem.lower()).strip("-")


def source_files_for_manifest(pack: Path, source: Path) -> list[Path]:
    """Match original images to manifest entries; allow only byte-identical extras."""
    if not source.is_dir():
        raise ValueError(f"original artwork folder is missing: {source}")
    originals = sorted(
        (path for path in source.iterdir()
         if path.is_file() and not path.is_symlink()
         and path.suffix.lower() in SOURCE_EXTENSIONS),
        key=lambda path: path.name.lower(),
    )
    by_stem: dict[str, Path] = {}
    fingerprints: dict[Path, str] = {}
    for path in originals:
        stem = source_filename_stem(path)
        if not stem or stem in by_stem:
            raise ValueError(f"ambiguous original artwork filename: {path.name}")
        by_stem[stem] = path
        fingerprints[path] = hashlib.sha256(path.read_bytes()).hexdigest()

    chosen = []
    for bmp in images_from_manifest(pack):
        original = by_stem.get(bmp.stem)
        if original is None:
            raise ValueError(f"original artwork not found for: {bmp.name}")
        chosen.append(original)

    chosen_hashes = {fingerprints[path] for path in chosen}
    if len(chosen_hashes) != COUNT:
        raise ValueError("different manifest images must have distinct source artwork")
    if set(fingerprints.values()) != chosen_hashes:
        raise ValueError("source folder includes extra distinct artwork not in the pack")
    return chosen


def grayscale_thumbnail(source: Path) -> Image.Image:
    """Use the device's X3 center crop, retaining 256 grayscale levels."""
    with Image.open(source) as original:
        cropped = ImageOps.fit(
            ImageOps.exif_transpose(original).convert("RGB"),
            TARGET_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    gray = ImageOps.autocontrast(ImageOps.grayscale(cropped), cutoff=1)
    return gray.resize(THUMB_SIZE, Image.Resampling.LANCZOS)


def render_gallery(pack: Path, source: Path) -> bytes:
    paths = source_files_for_manifest(pack, source)
    thumb_width, thumb_height = THUMB_SIZE
    columns, margin, gap, padding, label_height = 5, 16, 12, 12, 30
    cell_width = thumb_width + padding * 2
    cell_height = thumb_height + label_height + padding * 2
    rows = (len(paths) + columns - 1) // columns
    canvas = Image.new(
        "L",
        (margin * 2 + columns * cell_width + (columns - 1) * gap,
         margin * 2 + rows * cell_height + (rows - 1) * gap),
        236,
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=19)

    for index, path in enumerate(paths):
        image = grayscale_thumbnail(path)
        col, row = index % columns, index // columns
        x = margin + col * (cell_width + gap)
        y = margin + row * (cell_height + gap)
        draw.rounded_rectangle(
            (x, y, x + cell_width - 1, y + cell_height - 1),
            radius=6, fill=255, outline=150, width=1,
        )
        canvas.paste(image, (x + padding, y + padding))
        draw.text(
            (x + cell_width // 2, y + padding + thumb_height + label_height // 2),
            f"{index + 1:02d}", fill=40, font=font, anchor="mm",
        )
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, required=True,
        help="Folder with the unchanged original JPEG/PNG/WebP image batch",
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="Override the PNG output path")
    parser.add_argument("--check", action="store_true", help="Fail if the gallery is out of date")
    args = parser.parse_args()
    output = args.output or args.root / PREVIEW
    image = render_gallery(args.root / PACK, args.source)
    if args.check:
        if not output.is_file() or output.read_bytes() != image:
            parser.error(f"gallery missing or out of date: {output}")
        print(f"Gallery up to date: {output}")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(image)
        print(f"Created {output} with {COUNT} original-art grayscale previews")


if __name__ == "__main__":
    main()
