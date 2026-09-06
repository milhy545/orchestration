#!/usr/bin/env python3
"""Build one marketplace skill package and refresh skills-index.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path


def read_manifest(skill_dir: Path) -> dict:
    manifest_path = skill_dir / "skill.yaml"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_archive(skill_dir: Path, catalog_dir: Path, manifest: dict) -> Path:
    artifacts_dir = catalog_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    archive_name = f"{manifest['name']}-{manifest['version']}.tar.gz"
    archive_path = artifacts_dir / archive_name
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(skill_dir, arcname=manifest["name"])
    return archive_path


def update_catalog(catalog_dir: Path, manifest: dict, archive_path: Path) -> None:
    index_path = catalog_dir / "skills-index.json"
    index = {"skills": []}
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))

    entry = {
        "name": manifest["name"],
        "version": manifest["version"],
        "description": manifest.get("description", ""),
        "kind": manifest.get("kind", "skill"),
        "package_type": manifest.get("package_type", "single-skill"),
        "archive_url": f"artifacts/{archive_path.name}",
        "sha256": sha256_file(archive_path),
        "tags": manifest.get("tags", []),
        "source": manifest.get("source", "internal"),
        "targets": manifest.get("targets", []),
        "runtime": manifest.get("runtime", {}),
        "manifest_path": manifest.get("manifest_path", "skill.yaml"),
    }

    skills = [
        item
        for item in index.get("skills", [])
        if not (item.get("name") == entry["name"] and item.get("version") == entry["version"])
    ]
    skills.append(entry)
    skills.sort(key=lambda item: (item.get("name", ""), item.get("version", "")))
    index["skills"] = skills
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True)
    parser.add_argument(
        "--catalog-dir",
        default="mcp-servers/marketplace-mcp/catalog",
    )
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    catalog_dir = Path(args.catalog_dir).resolve()
    manifest = read_manifest(skill_dir)
    archive_path = build_archive(skill_dir, catalog_dir, manifest)
    update_catalog(catalog_dir, manifest, archive_path)
    print(archive_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
