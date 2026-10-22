# Changelog

## 0.1.1 — Multiple collection contract

- Add collection ID to each package manifest, allowing multiple independent wallpaper collections per GitHub repository and more than one variant for each resolution.
- Package identities and target resolutions are unchanged.

## 0.1.0 — Initial local multi-pack collection

- Publish one Star Wars/Mandalorian collection with two **independent** packages:
  `starwars-x3` (528×792) and `starwars-x4plus` (480×800).
- Each package includes 19 unique grayscale BMP wallpapers with cover-fit crops;
  both come from the same 21-image 720×1280 source batch (two exact duplicates excluded).
- Use four-level grayscale and 2-bit native BMPs for compact, fast display loading.
- Add `target_resolution` in each pack manifest and validate image dimensions.
- Release **two separate install-only ZIP assets** under a single `v0.1.0` tag.
- Replace the previous unpublished `starwars` 480×800-only collection.
