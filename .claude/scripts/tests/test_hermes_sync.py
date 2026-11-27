from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("hermes_sync", ROOT / ".hermes" / "sync-agents.py")
assert SPEC and SPEC.loader
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)

# Mirrors html_comment_injection in Hermes tools/threat_patterns.py (case-insensitive).
HTML_COMMENT = re.compile(r"<!--[^>]{0,512}(?:ignore|override|system|secret|hidden)[^>]{0,512}-->", re.I)


class HermesSoulTests(unittest.TestCase):
    def souls(self):
        return {src.stem: sync.convert(src)["SOUL.md"] for src in sorted(sync.SRC.glob("*.md"))}

    def test_no_soul_trips_html_comment_scanner(self):
        for stem, soul in self.souls().items():
            self.assertIsNone(HTML_COMMENT.search(soul), stem)

    def test_lead_system_architect_header_is_clean(self):
        soul = self.souls()["lead-system-architect"]
        self.assertNotIn("system", soul.split("\n", 1)[0].lower())

    def test_notes_describe_profile_routes(self):
        for stem, soul in self.souls().items():
            self.assertIn("profile_routes", soul, stem)
            self.assertNotIn("Hermes cannot start a named", soul, stem)


if __name__ == "__main__":
    unittest.main()
