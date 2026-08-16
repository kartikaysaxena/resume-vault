from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from generate_manifest import build_manifest


class ManifestTests(unittest.TestCase):
    def test_builds_urls_hashes_and_pages_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "llm-profile.json").write_text(json.dumps({
                "version": 1, "name": "Kartikay", "source_revision": "abc123",
            }), encoding="utf-8")
            folder = root / "backend"
            folder.mkdir()
            (folder / "backend.tex").write_text("tex", encoding="utf-8")
            (folder / "backend.pdf").write_bytes(b"%PDF-test")
            (folder / "resume.json").write_text(
                json.dumps({
                    "id": "backend", "display_name": "Backend", "status": "active",
                    "source": "backend.tex", "pdf": "backend.pdf",
                    "role_families": ["backend"], "skills": ["Go"],
                    "summary": "Backend engineer",
                }),
                encoding="utf-8",
            )

            site = root / "_site"
            manifest = build_manifest(
                root, site, "owner/vault", "abc123", "https://owner.github.io/vault"
            )

            resume = manifest["resumes"][0]
            self.assertEqual(resume["id"], "backend")
            self.assertIn("abc123/backend/backend.tex", resume["source_url"])
            self.assertTrue((site / "backend/backend.pdf").is_file())
            self.assertTrue((site / "manifest.json").is_file())
            self.assertTrue((site / "llm-profile.json").is_file())
            self.assertEqual(manifest["profile_url"], "https://owner.github.io/vault/llm-profile.json")


if __name__ == "__main__":
    unittest.main()
