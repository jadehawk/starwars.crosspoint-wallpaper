"""Checks for the high-quality, source-artwork Star Wars contact sheet."""
from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError
from tools import generate_previews as preview

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / preview.PACK


class WallpaperPreviewTests(unittest.TestCase):
    def test_source_manifest_has_19_safe_unique_images(self):
        paths = preview.images_from_manifest(PACK)
        self.assertEqual(len(paths), 19)
        self.assertTrue(all(path.is_file() for path in paths))

    def test_rejects_bad_manifest_image_lists(self):
        source = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
        for images in (
            source["images"][:-1],
            source["images"][:-1] + [source["images"][0]],
            source["images"][:-1] + ["../elsewhere.bmp"],
            source["images"][:-1] + [3],
        ):
            with self.subTest(last=images[-1]):
                with tempfile.TemporaryDirectory() as temp:
                    pack = Path(temp)
                    (pack / "manifest.json").write_text(
                        json.dumps({**source, "images": images}), encoding="utf-8"
                    )
                    with self.assertRaises(ValueError):
                        preview.images_from_manifest(pack)

    def make_fixture(self, parent: Path) -> tuple[Path, Path]:
        """Create 19 distinct original JPEGs and one matching duplicate pair."""
        pack = parent / "pack"
        pack.mkdir()
        source = parent / "originals"
        source.mkdir()
        names = ["wallpapers/art-00-1.bmp"]
        names.extend(f"wallpapers/art-{i:02d}.bmp" for i in range(1, 19))
        (pack / "manifest.json").write_text(
            json.dumps({"images": names}), encoding="utf-8"
        )
        for i in range(19):
            name = "art-00 (1).jpg" if i == 0 else f"art-{i:02d}.jpg"
            image = Image.new("RGB", (96, 160))
            draw = ImageDraw.Draw(image)
            for x in range(96):
                draw.line((x, 0, x, 159), fill=((x * 2 + i * 9) % 256,
                                                  (x * 3 + i * 17) % 256, x))
            image.save(source / name, quality=95)
        shutil.copyfile(source / "art-00 (1).jpg", source / "art-00.jpg")
        return pack, source

    def test_matches_manifest_order_and_ignores_only_identical_duplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            pack, source = self.make_fixture(Path(temp))
            ordered = preview.source_files_for_manifest(pack, source)
            self.assertEqual(len(ordered), 19)
            self.assertEqual(ordered[0].name, "art-00 (1).jpg")
            self.assertEqual(ordered[1].name, "art-01.jpg")
            with Image.open(io.BytesIO(preview.render_gallery(pack, source))) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (1000, 1244))
                self.assertEqual(image.mode, "L")
            Image.new("RGB", (96, 160), "red").save(source / "extra.jpg")
            with self.assertRaisesRegex(ValueError, "extra distinct artwork"):
                preview.source_files_for_manifest(pack, source)

    def test_rejects_missing_duplicate_and_bad_originals(self):
        with tempfile.TemporaryDirectory() as temp:
            pack, source = self.make_fixture(Path(temp))
            with self.assertRaisesRegex(ValueError, "missing"):
                preview.source_files_for_manifest(pack, Path(temp) / "absent")
            (source / "art-08.jpg").unlink()
            with self.assertRaisesRegex(ValueError, "not found"):
                preview.source_files_for_manifest(pack, source)
            (source / "art-08.jpg").write_bytes((source / "art-09.jpg").read_bytes())
            with self.assertRaisesRegex(ValueError, "distinct source artwork"):
                preview.source_files_for_manifest(pack, source)
            (source / "art-08.jpg").write_bytes(b"broken image")
            with self.assertRaises(UnidentifiedImageError):
                preview.render_gallery(pack, source)

    def test_rejects_ambiguous_filename_normalization(self):
        with tempfile.TemporaryDirectory() as temp:
            pack, source = self.make_fixture(Path(temp))
            shutil.copyfile(source / "art-02.jpg", source / "art 02.jpg")
            shutil.copyfile(source / "art-02.jpg", source / "art+02.jpg")
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                preview.source_files_for_manifest(pack, source)

    def test_thumbnails_use_smooth_grayscale_and_x3_center_crop(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "landscape.jpg"
            image = Image.new("RGB", (420, 200))
            draw = ImageDraw.Draw(image)
            for x in range(420):
                draw.line((x, 0, x, 199), fill=(x * 255 // 419, 40, 255 - x * 255 // 419))
            image.save(source, quality=98)
            result = preview.grayscale_thumbnail(source)
            self.assertEqual(result.size, (160, 240))
            self.assertEqual(result.mode, "L")
            self.assertGreater(len(set(result.tobytes())), 4)
            # The X3 crop must differ from stretching the full landscape source.
            with Image.open(source) as original:
                stretched = ImageOps.autocontrast(
                    ImageOps.grayscale(original), cutoff=1
                ).resize(preview.THUMB_SIZE, Image.Resampling.LANCZOS)
            self.assertNotEqual(result.tobytes(), stretched.tobytes())

    def test_committed_gallery_has_256_level_preview_quality(self):
        with Image.open(ROOT / preview.PREVIEW) as image:
            image.verify()
        with Image.open(ROOT / preview.PREVIEW) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.mode, "L")
            self.assertEqual(image.size, (1000, 1244))
            self.assertGreater(len(set(image.crop((28, 28, 188, 268)).tobytes())), 4)
            # The unused 20th grid slot remains blank.
            self.assertEqual(image.getpixel((824, 970)), 236)


if __name__ == "__main__":
    unittest.main()
