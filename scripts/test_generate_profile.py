from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from generate_profile import active_sources, build_request, validate_profile, write_profile


class ProfileTests(unittest.TestCase):
    def test_builds_compact_json_request_and_writes_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "backend"
            folder.mkdir()
            (folder / "resume.tex").write_text(r"Go developer with 20\% lower latency", encoding="utf-8")
            (folder / "resume.json").write_text(json.dumps({
                "id": "backend", "display_name": "Backend", "status": "active",
                "source": "resume.tex", "pdf": "resume.pdf", "role_families": ["backend"],
                "skills": ["Go"], "summary": "Backend engineer",
            }), encoding="utf-8")

            payload = build_request(active_sources(root), "test-model")
            self.assertEqual(payload["model"], "test-model")
            request_content = json.loads(payload["messages"][1]["content"])
            self.assertIn(r"20\% lower latency", request_content["documents"][0]["latex"])

            profile = {
                "version": 1, "name": "K", "headline": "Engineer", "summary": "Backend",
                "experience": [], "projects": [], "education": [], "skills": {}, "achievements": [],
            }
            validate_profile(profile)
            output = root / "llm-profile.json"
            write_profile(output, profile, "abc123")
            self.assertEqual(json.loads(output.read_text())["source_revision"], "abc123")


if __name__ == "__main__":
    unittest.main()
