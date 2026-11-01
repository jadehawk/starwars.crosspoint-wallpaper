#!/usr/bin/env python3
"""Generate the single README contact sheet from the X3 pack's native 2bpp BMPs."""
from __future__ import annotations

import argparse
import io
import json
import re
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PACK = "starwars-x3.crosspoint-wallpaper"
PREVIEW = Path("docs/previews/starwars-gallery.png")
IMAGE_NAME = re.compile(r"wallpapers/[a-zA-Z0-9_-][a-zA-Z0-9_.-]*\.bmp\Z")
COUNT = 19


def images_from_manifest(pack: Path) -> list[Path]:
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    images = manifest.get("images")
    if not isinstance(images, list) or len(images) != COUNT:
        raise ValueError(f"expected exactly {COUNT} images in the X3 manifest")
    if any(not isinstance(path, str) or not IMAGE_NAME.fullmatch(path) for path in images):
        raise ValueError("invalid wallpaper image path in manifest")
    if len(set(images)) != COUNT:
        raise ValueError("duplicate wallpaper image in manifest")
    return [pack / name for name in images]


def decode_2bpp_bmp(path: Path) -> Image.Image:
    """Decode the uncompressed, padded, bottom-up 2-bit BMP written by our converter.

    Pillow does not natively support the custom 2bpp BMP format.
    """
    data = path.read_bytes()
    if len(data) < 70 or data[:2] != b"BM":
        raise ValueError(f"invalid BMP header: {path}")
    file_size = struct.unpack_from("<I", data, 2)[0]
    offset = struct.unpack_from("<I", data, 10)[0]
    dib_size, width, signed_height, planes, bpp, compression = struct.unpack_from(
        "<IiiHHI", data, 14
    )
    if (file_size != len(data) or dib_size != 40 or not 0 < width <= 2048
            or not 0 < signed_height <= 3072 or planes != 1 or bpp != 2
            or compression != 0 or offset < 70):
        raise ValueError(f"unsupported 2bpp BMP: {path}")
    palette = []
    for i in range(4):
        b, g, r, _ = data[54 + 4 * i:58 + 4 * i]
        if r != g or g != b:
            raise ValueError(f"non-grayscale BMP palette: {path}")
        palette.append(r)
    stride = ((width * 2 + 31) // 32) * 4
    if offset + stride * signed_height > len(data):
        raise ValueError(f"truncated BMP pixel data: {path}")

    pixels = bytearray(width * signed_height)
    for y in range(signed_height):
        start = offset + (signed_height - 1 - y) * stride
        row = data[start:start + stride]
        dest = y * width
        for x in range(width):
            pixels[dest + x] = palette[(row[x // 4] >> (6 - (x % 4) * 2)) & 3]
    return Image.frombytes("L", (width, signed_height), bytes(pixels))


def render_gallery(pack: Path) -> bytes:
    paths = images_from_manifest(pack)
    thumb_width, thumb_height = 160, 240
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
        image = decode_2bpp_bmp(path)
        if image.size != (528, 792):
            raise ValueError(f"unexpected X3 wallpaper dimensions: {path}")
        col, row = index % columns, index // columns
        x = margin + col * (cell_width + gap)
        y = margin + row * (cell_height + gap)
        draw.rounded_rectangle(
            (x, y, x + cell_width - 1, y + cell_height - 1),
            radius=6, fill=255, outline=150, width=1,
        )
        canvas.paste(
            image.resize((thumb_width, thumb_height), Image.Resampling.NEAREST),
            (x + padding, y + padding),
        )
        draw.text(
            (x + cell_width // 2, y + padding + thumb_height + label_height // 2),
            f"{index + 1:02d}", fill=40, font=font, anchor="mm",
        )
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="Override the PNG output path")
    parser.add_argument("--check", action="store_true", help="Fail if the gallery is out of date")
    args = parser.parse_args()
    output = args.output or args.root / PREVIEW
    image = render_gallery(args.root / PACK)
    if args.check:
        if not output.is_file() or output.read_bytes() != image:
            parser.error(f"gallery missing or out of date: {output}")
        print(f"Gallery up to date: {output}")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(image)
        print(f"Created {output} with {COUNT} wallpaper previews")


if __name__ == "__main__":
    main()
