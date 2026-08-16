#!/usr/bin/env python3
"""Validate resume metadata and build the GitHub Pages artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import quote


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_resume(metadata_path: Path, root: Path) -> dict[str, Any]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    required = {
        "id", "display_name", "status", "source", "pdf",
        "role_families", "skills", "summary",
    }
    missing = sorted(required - metadata.keys())
    if missing:
        raise ValueError(f"{metadata_path}: missing fields: {', '.join(missing)}")

    folder = metadata_path.parent
    if metadata["id"] != folder.name:
        raise ValueError(f"{metadata_path}: id must match folder name {folder.name!r}")
    if metadata["status"] not in {"active", "unavailable"}:
        raise ValueError(f"{metadata_path}: unsupported status")
    if not isinstance(metadata["role_families"], list) or not metadata["role_families"]:
        raise ValueError(f"{metadata_path}: role_families must be a non-empty list")
    if not isinstance(metadata["skills"], list) or not metadata["skills"]:
        raise ValueError(f"{metadata_path}: skills must be a non-empty list")

    source = (folder / metadata["source"]).resolve()
    pdf = (folder / metadata["pdf"]).resolve()
    root_resolved = root.resolve()
    if root_resolved not in source.parents or root_resolved not in pdf.parents:
        raise ValueError(f"{metadata_path}: artifact path escapes repository")
    if metadata["status"] == "active":
        if not source.is_file():
            raise ValueError(f"{metadata_path}: missing source {source.name}")
        if not pdf.is_file():
            raise ValueError(f"{metadata_path}: missing PDF {pdf.name}")

    metadata["_source_path"] = source
    metadata["_pdf_path"] = pdf
    return metadata


def build_manifest(
    root: Path,
    site: Path,
    repository: str,
    revision: str,
    pages_base_url: str,
) -> dict[str, Any]:
    profile_path = root / "llm-profile.json"
    if not profile_path.is_file():
        raise ValueError("missing llm-profile.json")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if profile.get("version") != 1 or not profile.get("name") or not profile.get("source_revision"):
        raise ValueError("llm-profile.json is missing version, name, or source_revision")
    site.mkdir(parents=True, exist_ok=True)
    shutil.copy2(profile_path, site / "llm-profile.json")

    resumes = []
    ids: set[str] = set()
    for metadata_path in sorted(root.glob("*/resume.json")):
        metadata = load_resume(metadata_path, root)
        resume_id = metadata["id"]
        if resume_id in ids:
            raise ValueError(f"duplicate resume id: {resume_id}")
        ids.add(resume_id)
        if metadata["status"] != "active":
            continue

        source: Path = metadata.pop("_source_path")
        pdf: Path = metadata.pop("_pdf_path")
        relative_source = source.relative_to(root).as_posix()
        relative_pdf = pdf.relative_to(root).as_posix()
        destination = site / relative_pdf
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf, destination)

        metadata.update(
            {
                "source_url": (
                    "https://raw.githubusercontent.com/"
                    f"{repository}/{quote(revision, safe='')}/{quote(relative_source, safe='/')}"
                ),
                "pdf_url": f"{pages_base_url.rstrip('/')}/{quote(relative_pdf, safe='/')}",
                "source_sha256": sha256(source),
                "pdf_sha256": sha256(pdf),
                "source_revision": revision,
            }
        )
        resumes.append(metadata)

    if not resumes:
        raise ValueError("no active resumes found")

    manifest = {
        "version": 1,
        "source_revision": revision,
        "profile_url": f"{pages_base_url.rstrip('/')}/llm-profile.json",
        "profile_sha256": sha256(profile_path),
        "resumes": resumes,
    }
    site.mkdir(parents=True, exist_ok=True)
    (site / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--pages-base-url", required=True)
    args = parser.parse_args()
    build_manifest(
        args.root.resolve(), args.site.resolve(), args.repository,
        args.revision, args.pages_base_url,
    )


if __name__ == "__main__":
    main()
