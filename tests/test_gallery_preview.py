"""Checks for the documentation-only Star Wars contact sheet."""
from __future__ import annotations

import io
import json
import struct
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from tools import generate_previews as preview

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / preview.PACK


class WallpaperPreviewTests(unittest.TestCase):
    def test_source_manifest_has_19_safe_unique_images(self):
        paths = preview.images_from_manifest(PACK)
        self.assertEqual(len(paths), 19)
        self.assertTrue(all(path.is_file() for path in paths))

    def test_native_2bpp_image_decodes_to_four_gray_levels(self):
        image = preview.decode_2bpp_bmp(preview.images_from_manifest(PACK)[0])
        self.assertEqual(image.size, (528, 792))
        self.assertEqual(image.mode, "L")
        self.assertTrue(set(image.getdata()).issubset({0, 85, 170, 255}))
        self.assertGreater(len(set(image.getdata())), 1)

    def test_rejects_bad_manifest_image_lists(self):
        source = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
        for images in (
            source["images"][:-1],
            source["images"][:-1] + [source["images"][0]],
            source["images"][:-1] + ["../elsewhere.bmp"],
            source["images"][:-1] + [3],
        ):
            with self.subTest(images=images[-1]):
                with tempfile.TemporaryDirectory() as temp:
                    path = Path(temp)
                    (path / "manifest.json").write_text(
                        json.dumps({**source, "images": images}), encoding="utf-8"
                    )
                    with self.assertRaises(ValueError):
                        preview.images_from_manifest(path)

    def test_rejects_malformed_or_truncated_bmp(self):
        data = (preview.images_from_manifest(PACK)[0]).read_bytes()
        modified = []
        modified.append(data[:-4])
        broken_bitdepth = bytearray(data)
        struct.pack_into("<H", broken_bitdepth, 28, 8)
        modified.append(bytes(broken_bitdepth))
        broken_palette = bytearray(data)
        broken_palette[54] = 1
        modified.append(bytes(broken_palette))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test.bmp"
            for bad_data in modified:
                path.write_bytes(bad_data)
                with self.assertRaises(ValueError):
                    preview.decode_2bpp_bmp(path)

    def test_gallery_is_valid_png_and_current(self):
        generated = preview.render_gallery(PACK)
        self.assertEqual((ROOT / preview.PREVIEW).read_bytes(), generated)
        with Image.open(io.BytesIO(generated)) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.mode, "L")
            self.assertEqual(image.size, (1000, 1244))
            # The unused 20th grid slot must stay empty.
            self.assertEqual(image.getpixel((824, 970)), 236)


if __name__ == "__main__":
    unittest.main()
