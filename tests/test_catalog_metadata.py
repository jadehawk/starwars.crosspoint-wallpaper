"""Versioned catalog metadata without changing the installed wallpaper v1 schema."""
import json
import unittest
import tempfile
import shutil
from tools import wallpaper_pack_tool as tool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CatalogMetadataTests(unittest.TestCase):
    def test_release_details_and_safe_intro(self):
        details = (ROOT / "DETAILS.md").read_text(encoding="utf-8")
        self.assertTrue(details.startswith("# Star Wars"))
        self.assertIn("19 monochrome", details)
        self.assertIn("528", details)
        self.assertIn("480", details)
        self.assertIn("Jadehawk", details)

    def test_missing_or_invalid_packaged_details_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "starwars-x3.crosspoint-wallpaper"
            shutil.copytree(ROOT / "starwars-x3.crosspoint-wallpaper", root)
            (root / "DETAILS.md").unlink()
            with self.assertRaisesRegex(tool.PackError, "DETAILS.md"):
                tool.validate_one(root)
            (root / "DETAILS.md").write_bytes(b"invalid" + bytes([255]))
            with self.assertRaisesRegex(tool.PackError, "UTF-8"):
                tool.validate_one(root)

    def test_missing_short_description_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "starwars-x3.crosspoint-wallpaper"
            shutil.copytree(ROOT / "starwars-x3.crosspoint-wallpaper", root)
            path = root / "manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest.pop("description")
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(tool.PackError, "manifest keys"):
                tool.validate_one(root)

    def test_both_unchanged_variant_identities_and_versions(self):
        variants = [("starwars-x3", 528, 792), ("starwars-x4plus", 480, 800)]
        for name, width, height in variants:
            with self.subTest(name=name):
                payload = ROOT / (name + ".crosspoint-wallpaper")
                manifest = json.loads((payload / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["name"], name)
                self.assertEqual(manifest["title"], "Star Wars")
                self.assertEqual(manifest["collection"], "starwars")
                self.assertEqual(manifest["version"], "0.1.4")
                self.assertEqual(manifest["author"], "Jadehawk")
                self.assertEqual(manifest["target_resolution"], {"width": width, "height": height})
                self.assertEqual(len(manifest["images"]), 19)
                self.assertIn("DETAILS.md", manifest["files"])
                self.assertEqual((payload / "DETAILS.md").read_text(encoding="utf-8"),
                                 (ROOT / "DETAILS.md").read_text(encoding="utf-8"))
                self.assertIn("description", manifest)
                self.assertTrue(manifest["description"])
                self.assertIn("19 grayscale", (payload / "README.md").read_text(encoding="ascii"))


if __name__ == "__main__":
    unittest.main()
