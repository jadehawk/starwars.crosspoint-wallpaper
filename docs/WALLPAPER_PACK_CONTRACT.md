# CrossPoint Standalone Wallpaper Pack Contract — v1 (experimental)

A **provisional capability-based community contract**, not an upstream CrossPoint standard. A wallpaper pack is a separately versioned collection of ordinary BMP sleep images. It is **not** a UI theme, plugin, executable package, or a subtheme.

## One repository, one or more independently installable collections

A repository may publish **1–8** distinct wallpaper packs as direct-child folders.
Each pack has its **own immutable lowercase ID**, manifest, README and BMP file list;
the repository shares one version tag, changelog, tools, validation and release workflow.
A GitHub Release contains **one independent ZIP asset per pack**. A device installs
only the appropriate asset, never a ZIP containing all size variants.

~~~text
starwars.crosspoint-wallpaper/             ← single GitHub repository
├── starwars-x3.crosspoint-wallpaper/      ← separate installable pack, 528×792
│   ├── manifest.json
│   ├── README.md
│   └── wallpapers/*.bmp
├── starwars-x4plus.crosspoint-wallpaper/  ← separate installable pack, 480×800
│   ├── manifest.json
│   ├── README.md
│   └── wallpapers/*.bmp
├── .github/workflows/
│   ├── validate.yml
│   └── release.yml
├── docs/WALLPAPER_PACK_CONTRACT.md
├── tools/wallpaper_pack_tool.py
├── CHANGELOG.md
├── README.md
└── .gitignore
~~~

The repository name need not equal any payload ID. For **each pack**, the installable
folder stem, `manifest.json` `name`, SD path and catalog identity must match.
Changing an installed pack ID creates a new collection, not an update.

Only install the selected folder under
`/.crosspoint/wallpapers/<pack-id>.crosspoint-wallpaper/`.
Do not install a repo root, a multi-pack ZIP, a ZIP file without extracting it,
or anything under the theme, plugin or legacy sleep roots.

## Manifest schema (v1)

~~~json
{
  "kind": "wallpaper-pack",
  "name": "starwars",
  "title": "Star Wars",
  "author": "Pack Author",
  "version": "0.1.0",
  "target_resolution": {"width": 528, "height": 792},
  "images": ["wallpapers/planet.bmp", "wallpapers/starfield.bmp"],
  "files": [
    "manifest.json", "README.md",
    "wallpapers/planet.bmp", "wallpapers/starfield.bmp"
  ]
}
~~~

- kind distinguishes wallpapers from theme-pack and plugin manifests.
- name is a stable 1–32-character lowercase ID containing only letters, digits and hyphens.
- title is user-facing (max 60 characters); author is nonempty (max 120 characters).
- version is semantic major.minor.patch. Every manifest in a repository must have the **same release version** matching the Git tag `v<version>`.
- target_resolution is optional for a one-pack repository, but required for **each** pack in multi-pack repositories: `{"width": integer, "height": integer}`. These values must match the exact BMP dimensions. A multi-pack repository may not repeat the same target resolution.
- images is the list of **1–32** BMP files **per pack**. files lists precisely the manifest, README and every BMP, once each.
- Image paths must be directly beneath wallpapers/ with simple ASCII names and lowercase .bmp. No paths outside the collection, URLs, symlinks, executable files or nested image folders.
- Each BMP: maximum **8 MiB** and maximum dimensions **2048×3072**. The host tool limits the installable package to 64 MiB.
- Supported native formats: uncompressed 1-, 2-, 4-, 8-, 24- or 32-bit BMP; also supported 32-bit BI_BITFIELDS. Prefer standard uncompressed 24-bit BMP.
- PNG/JPEG are supported as **authoring inputs** on the developer's computer, not native installed image formats in v1. Convert them to BMP before release.
- CPB, CPFONT, animations, scripts, theme.json, device.json and plugin.js are **not** part of wallpaper packs.

The pack contains images and metadata only; it does not change fonts, layout, Home, Library, Settings, button gestures or installed plugins.

## Firmware capability contract

Firmware should advertise **wallpaper.packs.v1** only when its discovery, validation, picker, persistence, BMP selection and sleep/timed-refresh paths are implemented. Do not infer compatibility solely from a firmware name or version string.

Current development implementation:

- Discover at /.crosspoint/wallpapers/*.crosspoint-wallpaper/ (bounded to 8 installed packs, 32 images per pack, small manifest).
- Validate the manifest's ID, file allowlist and supported BMP images before showing it.
- Show **Wallpaper Collection** immediately below **Sleep Screen** in Settings → Display, **only when Sleep Screen is Custom**. Tapping it opens a separate scrollable selection screen (not a bounded option popup). Default is **All wallpapers (/.sleep + /sleep)**, preserving the merged legacy pool and `/sleep.bmp` precedence.
- With a named collection, **Custom** sleep uses only that collection's images. Timed refresh uses the same collection when the existing refresh path runs.
- With **All wallpapers**, existing /sleep.bmp precedence and the merged /.sleep and /sleep pools remain unchanged.
- If the chosen pack becomes invalid or missing, fall back to the normal Custom pool safely rather than reading arbitrary files.
- UI theme Dark/Light sleep galleries remain separate. Cover, Quick Resume and transparent overlay modes keep their original behavior.
- Don't load an entire image collection into X3 RAM; select a path then decode one BMP.

**Status:** the wallpaper collection picker and loading were verified on X3 hardware in October 2026. Stock CrossPoint and unverified forks are not automatically compatible.

## Versioned GitHub publication

The repository owns one shared release version, while each installable variant has
its own persistent ID. Bump every manifest version together for one repository release.

1. Add GitHub topic **crosspoint-wallpaper**. Maintain README and CHANGELOG.
2. Run `python tools/wallpaper_pack_tool.py validate --root .` and unit tests.
3. Use `python tools/wallpaper_pack_tool.py pack-all --root . --output-dir dist` to create one ZIP per pack.
4. Commit and tag `v0.1.0` (matching every manifest version). The release workflow validates the tag and attaches all variant ZIPs to **one** GitHub Release.
5. Each asset `<id>-0.1.0.crosspoint-wallpaper.zip` contains **only** the one matching `<id>.crosspoint-wallpaper/` directory and declared runtime files; never bundle both sizes in one ZIP.
6. Tests, workflows, original color artwork, converters, repo changelog and developer docs are excluded from install-only ZIPs.

A future Plugin Hub wallpaper catalog may discover the `crosspoint-wallpaper`
topic, inspect **each asset/manifest separately**, expose supported packs only on
firmware advertising `wallpaper.packs.v1`, and match `target_resolution` against
a trusted display resolution provided by the firmware. The current `/api/status`
does not advertise width/height; **automatic choice is not yet implemented**.
Do not match firmware names as a workaround, and do not install both variants.

## Create a new repository and additional variants

From the neutral authoring template, create the initial repository:

~~~powershell
python tools/create_wallpaper_repo.py --name StarWars --title "Star Wars" --author "Creator" --images "C:\Wallpapers\StarWars-BMP" --destination "C:\Users\Admin\Documents\Github Working Repos"
~~~

The generator initializes one standalone repository containing one valid collection.
To add other sizes, create additional distinct direct-child folders following the
same manifest and BMP layout; set `target_resolution` on **every** variant, then
validate the whole repository and run `pack-all`. Additional folders do **not**
need another repository, workflow, release tag or common installed ZIP.
Publishing a public GitHub repository remains a separate action.
