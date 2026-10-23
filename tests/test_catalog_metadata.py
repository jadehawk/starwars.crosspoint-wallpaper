"""Versioned catalog metadata without changing the installed wallpaper v1 schema."""
import json
import unittest
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

    def test_both_unchanged_variant_identities_and_versions(self):
        variants = [("starwars-x3", 528, 792), ("starwars-x4plus", 480, 800)]
        for name, width, height in variants:
            with self.subTest(name=name):
                payload = ROOT / (name + ".crosspoint-wallpaper")
                manifest = json.loads((payload / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["name"], name)
                self.assertEqual(manifest["version"], "0.1.3")
                self.assertEqual(manifest["author"], "Jadehawk")
                self.assertEqual(manifest["target_resolution"], {"width": width, "height": height})
                self.assertEqual(len(manifest["images"]), 19)
                self.assertNotIn("DETAILS.md", manifest["files"])
                self.assertNotIn("description", manifest)
                self.assertIn("19 grayscale", (payload / "README.md").read_text(encoding="ascii"))


if __name__ == "__main__":
    unittest.main()
