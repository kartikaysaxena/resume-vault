#!/usr/bin/env python3
"""Validate resume metadata and build the GitHub Pages artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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


def load_project(project_path: Path) -> dict[str, Any]:
    source = project_path.read_text(encoding="utf-8")
    metadata = {
        match.group(1): match.group(2).strip()
        for match in re.finditer(r"^%\s*([a-z-]+):\s*(.+?)\s*$", source, re.MULTILINE)
    }
    required = {
        "project-id", "project-name", "repository-url", "source-revision",
        "role-families", "skills",
    }
    missing = sorted(required - metadata.keys())
    if missing:
        raise ValueError(f"{project_path}: missing metadata comments: {', '.join(missing)}")

    project_id = metadata["project-id"]
    if project_id != project_path.stem or project_id != project_path.parent.name:
        raise ValueError(f"{project_path}: project id must match its folder and filename")
    if not metadata["repository-url"].startswith("https://github.com/"):
        raise ValueError(f"{project_path}: repository-url must be a GitHub HTTPS URL")
    if not re.fullmatch(r"[0-9a-f]{40}", metadata["source-revision"]):
        raise ValueError(f"{project_path}: source-revision must be a full Git commit SHA")

    bullet_ids = [
        value.strip()
        for value in re.findall(r"^%\s*bullet-id:\s*(.+?)\s*$", source, re.MULTILINE)
    ]
    bullet_skills = [
        value.strip()
        for value in re.findall(r"^%\s*bullet-skills:\s*(.+?)\s*$", source, re.MULTILINE)
    ]
    rendered_bullets = re.findall(r"^\\item\s*\{", source, re.MULTILINE)
    if not 3 <= len(bullet_ids) <= 4 or len(rendered_bullets) != len(bullet_ids):
        raise ValueError(f"{project_path}: expected 3 or 4 tagged resume item bullets")
    if len(bullet_skills) != len(bullet_ids) or not all(bullet_skills):
        raise ValueError(f"{project_path}: every bullet requires a bullet-skills comment")
    if len(set(bullet_ids)) != len(bullet_ids) or not all(bullet_ids):
        raise ValueError(f"{project_path}: bullet IDs must be non-empty and unique")
    required_commands = ("\\resumeSubheading", "\\resumeItemListStart", "\\resumeItemListEnd")
    if not all(command in source for command in required_commands):
        raise ValueError(f"{project_path}: project body must use the resume-native command set")

    pdf_path = project_path.with_suffix(".pdf")
    if not pdf_path.is_file():
        raise ValueError(f"{project_path}: missing compiled preview {pdf_path.name}")

    return {
        "id": project_id,
        "name": metadata["project-name"],
        "repository_url": metadata["repository-url"],
        "source_revision": metadata["source-revision"],
        "role_families": [value.strip() for value in metadata["role-families"].split(",")],
        "skills": [value.strip() for value in metadata["skills"].split(",")],
        "bullet_count": len(bullet_ids),
        "_tex_path": project_path,
        "_pdf_path": pdf_path,
    }


def build_project_catalog(
    root: Path,
    site: Path,
    revision: str,
    pages_base_url: str,
) -> Path:
    projects = []
    project_ids: set[str] = set()
    destination_dir = site / "projects"
    destination_dir.mkdir(parents=True, exist_ok=True)

    style = root / "projects" / "project-blob.sty"
    if not style.is_file():
        raise ValueError("missing projects/project-blob.sty")
    shutil.copy2(style, destination_dir / style.name)

    for project_path in sorted((root / "projects").glob("*/*.tex")):
        project = load_project(project_path)
        project_id = project["id"]
        if project_id in project_ids:
            raise ValueError(f"duplicate project id: {project_id}")
        project_ids.add(project_id)

        tex: Path = project.pop("_tex_path")
        pdf: Path = project.pop("_pdf_path")
        relative_tex = tex.relative_to(root).as_posix()
        relative_pdf = pdf.relative_to(root).as_posix()
        tex_destination = site / relative_tex
        pdf_destination = site / relative_pdf
        tex_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tex, tex_destination)
        shutil.copy2(pdf, pdf_destination)
        project.update(
            {
                "tex_url": f"{pages_base_url.rstrip('/')}/{quote(relative_tex, safe='/')}",
                "pdf_url": f"{pages_base_url.rstrip('/')}/{quote(relative_pdf, safe='/')}",
                "tex_sha256": sha256(tex),
                "pdf_sha256": sha256(pdf),
            }
        )
        projects.append(project)

    if not projects:
        raise ValueError("no reusable project blocks found")

    catalog_path = destination_dir / "index.json"
    catalog_path.write_text(
        json.dumps(
            {
                "version": 1,
                "vault_revision": revision,
                "style_url": f"{pages_base_url.rstrip('/')}/projects/project-blob.sty",
                "style_sha256": sha256(style),
                "projects": projects,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    return catalog_path


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

    if len(resumes) != 1:
        raise ValueError(
            f"expected exactly one active canonical resume, found {len(resumes)}"
        )

    project_catalog_path = build_project_catalog(
        root, site, revision, pages_base_url,
    )

    manifest = {
        "version": 1,
        "source_revision": revision,
        "profile_url": f"{pages_base_url.rstrip('/')}/llm-profile.json",
        "profile_sha256": sha256(profile_path),
        "project_catalog_url": f"{pages_base_url.rstrip('/')}/projects/index.json",
        "project_catalog_sha256": sha256(project_catalog_path),
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
