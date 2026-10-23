# AI agent: make your own CrossPoint BMP wallpaper pack

Start with [WALLPAPER_PACK_CONTRACT.md](WALLPAPER_PACK_CONTRACT.md) and this working Star Wars repo as an example, **not a requirement**. Wallpapers are separate from UI themes and executable plugins.

> Act as a CrossPoint wallpaper-pack publisher. Read this file, `docs/WALLPAPER_PACK_CONTRACT.md`, `tools/wallpaper_pack_tool.py`, and inspect the source BMP images and rights/attribution. Create 1–8 direct-child `<package-id>.crosspoint-wallpaper/` folders each containing `manifest.json`, a printable ASCII plain-text `README.md` <=2 KiB (no Markdown/emoji), and `wallpapers/*.bmp`. Use `kind: wallpaper-pack`, stable package `name`, artwork `collection`, short device-ready `title`, `author`, shared `MAJOR.MINOR.PATCH` `version`, exact portrait `target_resolution`, `images` and complete `files`. If there are multiple packages, require `collection` and `target_resolution` on EVERY manifest. Reject duplicate (collection,width,height) variants, but allow different collections to share dimensions. Preserve the images and do conversion/validation on the author computer, not the e-reader. Run `python tools/wallpaper_pack_tool.py validate --root . --tag v<version>` and `python tools/wallpaper_pack_tool.py pack-all --root . --output-dir dist --tag v<version>`. Inspect each independent ZIP. Add topic `crosspoint-wallpaper`; publish one non-draft, non-prerelease GitHub Release `v<version>` containing `<package-id>-<version>.crosspoint-wallpaper.zip` for each matching resolution variant. Explain upstream CrossPoint has no SD wallpaper packs and that Razor-Crest development firmware is the only currently known implementation; compatibility is detected from `wallpaper.packs.v1`, not firmware name. Do not introduce themes, script hooks, or `device.json`/`plugin.js` to a wallpaper pack. Do not commit, push, tag or publish unless authorized by the user.

## Exact structure and supported primitives

```text
my-wallpapers.crosspoint-wallpaper/              # repository root
  my-art-528.crosspoint-wallpaper/
    manifest.json                                 # kind, name, collection, title,
                                                  # author, version, images, files,
                                                  # target_resolution
    README.md                                     # plain ASCII, <=2 KiB
    wallpapers/*.bmp                              # 1 to 32 native BMPs
  my-art-480.crosspoint-wallpaper/                # another variant, distinct ID
    manifest.json
    README.md
    wallpapers/*.bmp
  tools/                                          # developer-only
  docs/                                           # developer-only
```

The only wallpaper capability token currently exposed is **`wallpaper.packs.v1`**. It implements SD pack scanning and validation; up to eight installed packs and 32 BMP images/pack; a **Wallpaper Collection** picker directly under **Settings > Display > Sleep Screen** when Custom is selected; per-collection selection persistence; safe fallback to **All wallpapers** when the selected pack is unavailable; and wallpaper selection for regular Custom sleep and existing timed refresh. The All wallpapers choice merges `/.sleep` and `/sleep` with existing `/sleep.bmp` precedence. A named pack loads one BMP on demand instead of caching all images. This capability **does not expose theme metrics, UI layouts, fonts, scripts, callbacks or network requests**. HALO-style Dark/Light galleries are independent of this Custom wallpaper source.

Supported BMP formats and bounds, author-side: 1-, 2-, 4-, 8-, 24-, 32-bit uncompressed BMP plus documented 32-bit BI_BITFIELDS; individual file <=8 MiB, pixel dimensions <=2048x3072, <=32 images/pack and <=64 MiB total. **Every BMP must match its declared target resolution.** Only one matching portrait resolution variant per collection is installed; separate collections can coexist. Firmware must match the actual display dimensions, not `X3` or `X4` brand names.

## Known firmware and catalog support (October 2026)

| Firmware | SD wallpaper packs |
| --- | --- |
| [Razor-Crest](https://github.com/jadehawk/Razor-Crest), current development builds | Known compatible implementation; X3-tested; check exact build and the advertised `wallpaper.packs.v1` token |
| [Upstream CrossPoint](https://github.com/crosspoint-reader/crosspoint-reader) | **Unsupported** in current stock firmware |

This is **not** a fixed allowlist: any future firmware implementing the capability can be compatible. The [Plugin Hub guide](https://github.com/crosspoint-reader/crosspoint-plugin-hub/blob/main/docs/BUILD_AND_PUBLISH_EXTENSIONS.md) describes GitHub topic `crosspoint-wallpaper`, stable release validation, and automated community catalog ingestion; publishing a catalog item does not enable stock firmware to install it.
