# Changelog

## 0.1.4 — Unified extension publishing contract (development only)

- Display the same clean `Star Wars` title for both device resolutions; keep resolution selection in `target_resolution`.
- Match plugin publication: a versioned manifest, tagged ZIP, short description and rich details.
- Reject missing/invalid details at packaging time; preserve artwork and collection IDs.
- Do not tag or release until catalog, firmware and package tests pass together.

## 0.1.3 — Catalog description and details

- Add release-tagged `DETAILS.md` for a richer Plugin Hub information page and a clear short description.
- Keep two separately installable wallpaper variants, with all existing images, resolutions, and identifiers unchanged.
- Keep installed package manifests minimal and compatible with existing firmware.

## 0.1.2 — Device-friendly collection titles and READMEs

- Shorten the X3 and X4+ package titles to display their actual portrait resolutions.
- Replace the installable READMEs with concise ASCII text, without emoji or Markdown markers.
- Keep all BMP artwork and stable package/collection identifiers unchanged.

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
