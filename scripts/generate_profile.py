#!/usr/bin/env python3
"""Generate a compact, factual candidate profile from active resume TeX files."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "deepseek/deepseek-chat"
MAX_SOURCE_BYTES = 256_000


def active_sources(root: Path) -> list[tuple[dict[str, Any], Path]]:
    sources: list[tuple[dict[str, Any], Path]] = []
    total_size = 0
    for metadata_path in sorted(root.glob("*/resume.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("status") != "active":
            continue
        source = (metadata_path.parent / metadata["source"]).resolve()
        if root.resolve() not in source.parents or not source.is_file():
            raise ValueError(f"invalid active resume source: {source}")
        total_size += source.stat().st_size
        if total_size > MAX_SOURCE_BYTES:
            raise ValueError(f"active resume sources exceed {MAX_SOURCE_BYTES} bytes")
        sources.append((metadata, source))
    if not sources:
        raise ValueError("no active resume sources found")
    return sources


def response_schema() -> dict[str, Any]:
    return {
        "version": 1,
        "name": "string",
        "headline": "string",
        "summary": "string",
        "contact": {"email": "string", "website": "string", "github": "string", "linkedin": "string"},
        "experience": [{"organization": "string", "role": "string", "period": "string", "highlights": ["string"]}],
        "projects": [{"name": "string", "url": "string", "summary": "string", "highlights": ["string"]}],
        "education": [{"institution": "string", "degree": "string", "year": "string"}],
        "skills": {"languages": ["string"], "frameworks": ["string"], "infrastructure": ["string"]},
        "achievements": ["string"],
    }


def build_request(sources: list[tuple[dict[str, Any], Path]], model: str) -> dict[str, Any]:
    documents = [
        {
            "resume": {key: value for key, value in metadata.items() if key not in {"source", "pdf"}},
            "latex": source.read_text(encoding="utf-8"),
        }
        for metadata, source in sources
    ]
    return {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Extract one compact candidate profile from the supplied resumes. "
                    "Return JSON only, matching the supplied shape exactly. Preserve factual wording, "
                    "metrics, dates, employers, links, and skills; never infer or embellish. "
                    "Deduplicate facts and omit empty optional values."
                ),
            },
            {
                "role": "user",
                "content": json.dumps({"output_shape": response_schema(), "documents": documents}, separators=(",", ":")),
            },
        ],
    }


def call_llm(payload: dict[str, Any], api_key: str, base_url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read(4096).decode("utf-8", errors="replace")
        raise RuntimeError(f"profile LLM returned HTTP {error.code}: {detail}") from error
    try:
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("profile LLM did not return a JSON object") from error


def validate_profile(profile: dict[str, Any]) -> None:
    required = {"version", "name", "headline", "summary", "experience", "projects", "education", "skills", "achievements"}
    missing = sorted(required - profile.keys())
    if missing:
        raise ValueError(f"generated profile is missing: {', '.join(missing)}")
    if profile["version"] != 1 or not isinstance(profile["name"], str) or not profile["name"].strip():
        raise ValueError("generated profile has an invalid version or name")
    for key in ("experience", "projects", "education", "achievements"):
        if not isinstance(profile[key], list):
            raise ValueError(f"generated profile field {key!r} must be a list")
    if not isinstance(profile["skills"], dict):
        raise ValueError("generated profile field 'skills' must be an object")


def current_revision(root: Path) -> str:
    configured = os.environ.get("GITHUB_SHA", "").strip()
    if configured:
        return configured
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def write_profile(output: Path, profile: dict[str, Any], revision: str) -> None:
    profile["version"] = 1
    profile["source_revision"] = revision
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, delete=False) as handle:
        json.dump(profile, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("llm-profile.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    api_key = os.environ.get("PROFILE_LLM_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("PROFILE_LLM_API_KEY is required")
    model = os.environ.get("PROFILE_LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    base_url = os.environ.get("PROFILE_LLM_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    profile = call_llm(build_request(active_sources(root), model), api_key, base_url)
    validate_profile(profile)
    output = args.output if args.output.is_absolute() else root / args.output
    write_profile(output, profile, current_revision(root))


if __name__ == "__main__":
    main()
