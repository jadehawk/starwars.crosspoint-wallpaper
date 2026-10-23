# CrossPoint Standalone Wallpaper Pack Contract — v1 (experimental)

A **provisional capability-based community contract**, not an upstream CrossPoint standard. A wallpaper pack is a separately versioned collection of ordinary BMP sleep images. It is **not** a UI theme, plugin, executable package, or a subtheme.

**New developers and AI assistants:** follow [AI_AGENT_GUIDE.md](AI_AGENT_GUIDE.md) for a copy/paste development checklist. Plugin Hub's [build/publish guide](https://github.com/crosspoint-reader/crosspoint-plugin-hub/blob/main/docs/BUILD_AND_PUBLISH_EXTENSIONS.md) gives the discovery and GitHub Release rules. Current upstream CrossPoint does **not** implement `wallpaper.packs.v1`; only Razor-Crest development builds are known to implement the standalone BMP pack selection path. This is not an allowlist.

## One repository, one or more independently installable collections

A repository may publish **1–8** distinct wallpaper packages as direct-child folders.
Each package declares its artwork `collection` so independent collections can each
have their own X3 and X4+ resolution variants.
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

The package manifest `title` is displayed directly in the installed list and Details page. Keep it concise (for example, `Star Wars`) and use the same display title across resolution variants of a collection. The device selects the correct package by its `target_resolution` metadata, not by parsing a resolution or model name from the title. The installable package `README.md` is a **plain-text device preview**: printable ASCII, no Markdown heading markers or emoji, and ideally no more than 2 KiB. Keep longer, richly formatted instructions in the repository-root README. Do not require firmware to allocate memory for text conversion.

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
  "name": "starwars-x3",
  "collection": "starwars",
  "title": "Star Wars",
  "description": "19 monochrome Star Wars and Mandalorian sleep wallpapers",
  "author": "Pack Author",
  "version": "0.1.0",
  "target_resolution": {"width": 528, "height": 792},
  "images": ["wallpapers/planet.bmp", "wallpapers/starfield.bmp"],
  "files": [
    "manifest.json", "README.md", "DETAILS.md",
    "wallpapers/planet.bmp", "wallpapers/starfield.bmp"
  ]
}
~~~

- kind distinguishes wallpapers from theme-pack and plugin manifests.
- name is a stable 1–32-character lowercase ID containing only letters, digits and hyphens.
- title is user-facing (max 60 characters); author is nonempty (max 120 characters).
- version is semantic major.minor.patch. Every manifest in a repository must have the **same release version** matching the Git tag `v<version>`.
- collection is a safe lowercase ID grouping all resolution variants of one artwork collection. It is optional in a single-pack repository but **required for each package** in a multi-pack repository.
- target_resolution is optional for a one-pack repository, but required for **each** pack in multi-pack repositories: `{"width": integer, "height": integer}`. These values must match the exact BMP dimensions. A multi-pack repository may repeat a target resolution across **different collections**, but must not repeat a `(collection, target_resolution)` pair.
- images is the list of **1–32** BMP files **per pack**. files lists precisely the manifest, README, packaged DETAILS.md and every BMP, once each.
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

### Catalog description and rich details

Put **`DETAILS.md` inside each installable wallpaper variant**, declared in the manifest's `files`, with a short introductory paragraph
and useful details (contents, compatible display sizes, installation steps,
attribution). The capability-aware Plugin Hub reads that file at the exact
released ZIP, uses the manifest's `description` as the short catalog description and publishes safe versioned
HTML for its details screen. The catalog must reject a new package when
the packaged `DETAILS.md` is missing or invalid.

Do put `DETAILS.md` into wallpaper manifest `files` and add a concise
`description` field to each wallpaper manifest. The updated installer
accepts the complete declared package while retaining support for legacy packages.
The installed plugin list displays manifest descriptions (or legacy README fallback)
without requiring scripts, internet access or dynamic text conversion.

## Versioned GitHub publication

The repository owns one shared release version, while each installable variant has
its own persistent ID. Bump every manifest version together for one repository release.

1. Add GitHub topic **crosspoint-wallpaper**. Maintain README and CHANGELOG.
2. Run `python tools/wallpaper_pack_tool.py validate --root .` and unit tests.
3. Use `python tools/wallpaper_pack_tool.py pack-all --root . --output-dir dist` to create one ZIP per pack.
4. Commit and tag `v0.1.0` (matching every manifest version). The release workflow validates the tag and attaches all variant ZIPs to **one** GitHub Release.
5. Each asset `<id>-0.1.0.crosspoint-wallpaper.zip` contains **only** the one matching `<id>.crosspoint-wallpaper/` directory and declared runtime files; never bundle both sizes in one ZIP.
6. Tests, workflows, original color artwork, converters, repo changelog and developer docs are excluded from install-only ZIPs.

Plugin Hub already publishes `community-wallpapers.json` and the `catalog-lists-capabilities.json` v2 index from public `crosspoint-wallpaper` repos and stable release assets. A compatible firmware consumer matches `target_resolution` to the panel's actual portrait dimensions; current Razor-Crest development builds implement this, while stock CrossPoint does not. `/api/status` advertises `wallpaper.packs.v1` capabilities, not display width/height. Never match a firmware name instead or download both variants.

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
