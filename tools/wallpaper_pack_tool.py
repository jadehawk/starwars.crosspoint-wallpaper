#!/usr/bin/env python3
"""Validate and deterministically package one or more CrossPoint BMP wallpaper packs.

A repository may contain up to eight direct-child *.crosspoint-wallpaper folders.
Each archive contains exactly one installable pack, never the whole repository.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
NAME_RE = re.compile(r"^wallpapers/[A-Za-z0-9_-][A-Za-z0-9_.-]{0,79}\.bmp$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
DIB = struct.Struct("<IiiHHI")
SUFFIX = ".crosspoint-wallpaper"


class PackError(ValueError):
    pass


def check(condition, message):
    if not condition:
        raise PackError(message)


def bmp_validate(file: Path):
    data = file.read_bytes()
    check(54 <= len(data) <= 8 * 1024 * 1024, "invalid BMP size: " + file.name)
    check(data[:2] == b"BM", "not a BMP: " + file.name)
    offset = struct.unpack_from("<I", data, 10)[0]
    dib_size, width, height, planes, bpp, compression = DIB.unpack_from(data, 14)
    check(dib_size >= 40 and width > 0 and height != 0, "invalid BMP dimensions/DIB")
    check(width <= 2048 and abs(height) <= 3072 and planes == 1, "BMP unsupported dimensions or planes")
    check(bpp in (1, 2, 4, 8, 24, 32), "BMP bit depth unsupported")
    check(compression == 0 or (bpp == 32 and compression == 3), "BMP compression unsupported")
    row_bytes = ((width * bpp + 31) // 32) * 4
    check(54 <= offset <= len(data) and row_bytes * abs(height) <= len(data) - offset,
          "BMP has truncated pixel data")
    return width, abs(height)


def collection_roots(root: Path) -> list[Path]:
    """Accept either a direct installable collection or a repository of collections."""
    root = root.resolve()
    check(root.is_dir(), "pack root must be a directory")
    if root.name.endswith(SUFFIX) and (root / "manifest.json").is_file():
        return [root]
    candidates = sorted(p for p in root.iterdir() if p.name.endswith(SUFFIX))
    check(1 <= len(candidates) <= 8, "repository must contain 1–8 direct-child wallpaper packs")
    check(all(p.is_dir() and not p.is_symlink() for p in candidates),
          "repository contains an invalid or symlinked wallpaper pack")
    return candidates


def validate_one(root: Path):
    check(root.is_dir() and not root.is_symlink(), "invalid collection directory")
    manifest_path = root / "manifest.json"
    check(manifest_path.is_file() and not manifest_path.is_symlink(), "missing safe manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {"kind", "name", "title", "author", "version", "images", "files"}
    optional = {"target_resolution", "collection"}
    check(isinstance(manifest, dict) and required.issubset(manifest) and
          set(manifest).issubset(required | optional), "invalid manifest keys")
    pack_id = root.name[:-len(SUFFIX)]
    check(manifest["kind"] == "wallpaper-pack" and manifest["name"] == pack_id and
          ID_RE.fullmatch(pack_id) is not None, "invalid pack identity")
    for key, max_len in (("title", 60), ("author", 120), ("version", 24)):
        check(isinstance(manifest[key], str) and 0 < len(manifest[key]) <= max_len,
              "invalid " + key)
    check(VERSION_RE.fullmatch(manifest["version"]) is not None,
          "version must be semantic major.minor.patch")
    collection = manifest.get("collection")
    if collection is not None:
        check(isinstance(collection, str) and ID_RE.fullmatch(collection) is not None,
              "invalid collection identity")
    resolution = manifest.get("target_resolution")
    if resolution is not None:
        check(isinstance(resolution, dict) and set(resolution) == {"width", "height"} and
              all(type(resolution[k]) is int and 0 < resolution[k] <= (2048 if k == "width" else 3072)
                  for k in ("width", "height")), "invalid target_resolution")
    images = manifest["images"]
    check(isinstance(images, list) and 1 <= len(images) <= 32,
          "images must contain 1–32 BMPs")
    check(len(images) == len(set(images)) and
          all(isinstance(p, str) and NAME_RE.fullmatch(p) for p in images),
          "unsafe or repeated image path")
    files = manifest["files"]
    check(isinstance(files, list) and len(files) == len(images) + 2 and
          len(files) == len(set(files)), "invalid files list")
    check(set(files) == set(images) | {"manifest.json", "README.md"},
          "manifest files mismatch")
    total = 0
    for path in files:
        candidate = root / path
        check(not candidate.is_symlink() and
              not any(p.is_symlink() for p in candidate.parents if p != root.parent),
              "symlinks forbidden")
        check(candidate.is_file() and candidate.resolve().is_relative_to(root),
              "file missing or outside collection")
        total += candidate.stat().st_size
        check(total <= 64 * 1024 * 1024, "pack exceeds 64 MiB")
        if path in images:
            dimensions = bmp_validate(candidate)
            if resolution is not None:
                check(dimensions == (resolution["width"], resolution["height"]),
                      "image dimensions do not match target_resolution: " + path)
    info = {"name": pack_id, "version": manifest["version"],
            "images": len(images), "bytes": total}
    if resolution is not None:
        info["target_resolution"] = resolution
    if collection is not None:
        info["collection"] = collection
    return info


def validate(root: Path, tag: str | None = None):
    roots = collection_roots(root)
    validated = [validate_one(pack) for pack in roots]
    versions = {entry["version"] for entry in validated}
    check(len(versions) == 1,
          "all collections in one repository must have the same release version")
    version = next(iter(versions))
    if tag is not None:
        check(tag == "v" + version,
              f"release tag {tag!r} must equal v{version}")
    if len(validated) > 1:
        check(all("target_resolution" in e and "collection" in e for e in validated),
              "multi-pack repository requires collection and target_resolution for every package")
        identities = [(e["collection"], e["target_resolution"]["width"],
                       e["target_resolution"]["height"]) for e in validated]
        check(len(set(identities)) == len(identities),
              "duplicate collection and target_resolution variant")
    if len(validated) == 1:
        return validated[0]
    return {"version": version, "packs": validated,
            "images": sum(x["images"] for x in validated),
            "bytes": sum(x["bytes"] for x in validated)}


def _archive_one(pack_root: Path, target: Path):
    info = validate_one(pack_root)
    manifest = json.loads((pack_root / "manifest.json").read_text(encoding="utf-8"))
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".zip", delete=False) as temp:
        tmp = Path(temp.name)
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_STORED) as archive:
            for rel in sorted(manifest["files"]):
                member = zipfile.ZipInfo(pack_root.name + "/" + rel, (1980, 1, 1, 0, 0, 0))
                member.compress_type = zipfile.ZIP_STORED
                member.external_attr = 0o100644 << 16
                archive.writestr(member, (pack_root / rel).read_bytes())
        os.replace(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)
    return {**info, "archive": str(target)}


def pack(root: Path, target: Path):
    roots = collection_roots(root)
    check(len(roots) == 1,
          "repository contains multiple collections; use pack-all to publish separate ZIP assets")
    validate(root)
    return _archive_one(roots[0], target)


def pack_all(root: Path, output_dir: Path, tag: str | None = None):
    summary = validate(root, tag=tag)
    roots = collection_roots(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for pack_root in roots:
        manifest = json.loads((pack_root / "manifest.json").read_text(encoding="utf-8"))
        name = manifest["name"] + "-" + manifest["version"] + SUFFIX + ".zip"
        results.append(_archive_one(pack_root, output_dir / name))
    return {"version": summary["version"], "assets": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "pack", "pack-all"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--tag", help="require every manifest version to match Git tag vVERSION")
    args = parser.parse_args()
    try:
        if args.command == "pack":
            check(args.output is not None and args.output.suffix.lower() == ".zip",
                  "pack needs --output .zip")
            result = pack(args.root, args.output)
        elif args.command == "pack-all":
            check(args.output_dir is not None, "pack-all needs --output-dir")
            result = pack_all(args.root, args.output_dir, tag=args.tag)
        else:
            result = validate(args.root, tag=args.tag)
        print(json.dumps(result, sort_keys=True))
    except (PackError, OSError, ValueError, KeyError, TypeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
