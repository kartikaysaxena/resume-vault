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
            projects = root / "projects"
            projects.mkdir()
            (projects / "project-blob.sty").write_text("style", encoding="utf-8")
            project = projects / "agent-runtime"
            project.mkdir()
            (project / "agent-runtime.tex").write_text(
                "% project-id: agent-runtime\n"
                "% project-name: Agent Runtime\n"
                "% repository-url: https://github.com/owner/agent-runtime\n"
                f"% source-revision: {'1' * 40}\n"
                "% role-families: backend, ai engineering\n"
                "% skills: Go, OpenTelemetry\n"
                "\\resumeSubheading\n{ Agent Runtime}\n{\\href{https://github.com/owner/agent-runtime}{Github}}\n"
                "{An agent runtime}\n{}\n"
                "\\resumeItemListStart\n"
                "% bullet-id: runtime\n% bullet-skills: Go\n\\item {Built the runtime.}\n"
                "% bullet-id: tracing\n% bullet-skills: OpenTelemetry\n\\item {Added tracing.}\n"
                "% bullet-id: tests\n% bullet-skills: Testing\n\\item {Covered the runtime.}\n"
                "\\resumeItemListEnd\n\\vspace{-2mm}\n",
                encoding="utf-8",
            )
            (project / "agent-runtime.pdf").write_bytes(b"%PDF-project")

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
            self.assertEqual(
                manifest["project_catalog_url"],
                "https://owner.github.io/vault/projects/index.json",
            )
            self.assertTrue((site / "projects/agent-runtime/agent-runtime.tex").is_file())
            self.assertTrue((site / "projects/agent-runtime/agent-runtime.pdf").is_file())
            catalog = json.loads((site / "projects/index.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["vault_revision"], "abc123")
            self.assertEqual(catalog["projects"][0]["id"], "agent-runtime")
            self.assertEqual(catalog["projects"][0]["bullet_count"], 3)
            self.assertIn("agent-runtime.tex", catalog["projects"][0]["tex_url"])
            self.assertIn("agent-runtime.pdf", catalog["projects"][0]["pdf_url"])

    def test_rejects_multiple_active_base_resumes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "llm-profile.json").write_text(json.dumps({
                "version": 1, "name": "Kartikay", "source_revision": "abc123",
            }), encoding="utf-8")
            for resume_id in ("one", "two"):
                folder = root / resume_id
                folder.mkdir()
                (folder / f"{resume_id}.tex").write_text("tex", encoding="utf-8")
                (folder / f"{resume_id}.pdf").write_bytes(b"%PDF-test")
                (folder / "resume.json").write_text(json.dumps({
                    "id": resume_id,
                    "display_name": resume_id.title(),
                    "status": "active",
                    "source": f"{resume_id}.tex",
                    "pdf": f"{resume_id}.pdf",
                    "role_families": ["engineering"],
                    "skills": ["Python"],
                    "summary": "Canonical resume",
                }), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "exactly one active canonical resume"):
                build_manifest(
                    root, root / "_site", "owner/vault", "abc123",
                    "https://owner.github.io/vault",
                )


if __name__ == "__main__":
    unittest.main()
