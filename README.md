# Star Wars Wallpaper Collection — X3 and X4+ packs

Unofficial Star Wars/Mandalorian sleep-wallpaper collection. Author: Jadehawk.
Version: **0.1.4**. This is one local source repository, with **two separately
installable wallpaper packages** and **one GitHub release containing two ZIP assets**.
The collections contain BMP images only; they are not plugins or UI themes.

**Build your own pack with AI:** [AI Agent Guide](docs/AI_AGENT_GUIDE.md) | [Complete wallpaper contract](docs/WALLPAPER_PACK_CONTRACT.md) | [Plugin Hub publishing guide](https://github.com/crosspoint-reader/crosspoint-plugin-hub/blob/main/docs/BUILD_AND_PUBLISH_EXTENSIONS.md).

**Firmware support:** stock upstream CrossPoint does **not** yet implement standalone SD wallpaper packs. The only established implementation currently is the development `razor-crest` branch of [Razor-Crest](https://github.com/jadehawk/Razor-Crest), gated by `wallpaper.packs.v1` capabilities rather than firmware branding.

## Choose only one download

| Variant | Screen dimensions | Intended displays | ZIP asset |
| --- | --- | --- | --- |
| 528×792 variant | 528×792 | 528×792 portrait screens | `starwars-x3-0.1.4.crosspoint-wallpaper.zip` |
| 480×800 variant | 480×800 | 480×800 portrait screens | `starwars-x4plus-0.1.4.crosspoint-wallpaper.zip` |

**Both variants display simply `Star Wars` on the device.** Firmware chooses
by `target_resolution`, independently of the displayed title.

**Do not install both just to use the collection on one device.** Both are
independently usable. Each includes 19 distinct images from the same batch,
cropped to fill that display without white borders, then resized and
Floyd–Steinberg dithered to four native grayscale levels as uncompressed 2bpp BMP.

To install manually on compatible firmware, extract **only the chosen ZIP** to
the SD card:

```text
/.crosspoint/wallpapers/starwars-x3.crosspoint-wallpaper/
```

or

```text
/.crosspoint/wallpapers/starwars-x4plus.crosspoint-wallpaper/
```

In firmware advertising `wallpaper.packs.v1`, choose **Sleep Screen → Custom**
and select the named collection under **Wallpaper Collection**.

## Build and validate both release assets

```powershell
python tools/wallpaper_pack_tool.py validate --root . --tag v0.1.4
python tools/wallpaper_pack_tool.py pack-all --root . --output-dir dist --tag v0.1.4
```

The release workflow verifies all manifests match the Git tag, builds two
ZIPs and attaches them to **one** release. Each asset contains only its own
collection folder and files listed in its manifest; no conversion utilities,
source images, workflows or developer files are installed.

To regenerate BMP artwork locally, install Pillow and run the included conversion
tool with the **unchanged source batch**:

```powershell
python -m pip install Pillow
python tools/convert_wallpaper_batch.py --source "C:\\Users\\Admin\\Downloads\\starwars wallpaper 2" --output "C:\\Temp\\starwars-x3" --width 528 --height 792
python tools/convert_wallpaper_batch.py --source "C:\\Users\\Admin\\Downloads\\starwars wallpaper 2" --output "C:\\Temp\\starwars-x4plus" --width 480 --height 800
```

The tool omits byte-identical source duplicates, preserving 19 unique images
from the 21 downloaded JPEGs. It refuses to overwrite a nonempty output directory.
Original source JPEGs are not included in this repository.

## Compatibility and Plugin Hub

Compatibility is capability-based: `wallpaper.packs.v1` permits standalone
wallpaper collections. Every variant manifest includes its authoritative
`target_resolution`. The firmware itself can load multiple installed packs,
but that does **not** mean a release must install them all.

Capability-aware Plugin Hub catalogs publish wallpaper collections with
resolution-specific ZIP variants. Automatic installation requires firmware with
the extension catalog consumer. Never install every variant or infer resolution
from a firmware name.

See `docs/WALLPAPER_PACK_CONTRACT.md` for the v1 package and release rules.

## Rights and attribution

Star Wars, Mandalorian characters and imagery are owned by their respective
rights holders. This is an **unofficial fan collection**, not endorsed by
Lucasfilm or Disney. Source artwork came from third-party images; verify
redistribution rights and attribution before pushing imagery to a public
GitHub repository or publishing downloadable release archives.
