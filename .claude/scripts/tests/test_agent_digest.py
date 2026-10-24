from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "agent_digest.py"
SPEC = importlib.util.spec_from_file_location("agent_digest", SCRIPT)
assert SPEC and SPEC.loader
agent_digest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agent_digest)

NOW = 1_800_000_000.0
DAY = 86400


def stamp(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat().replace("+00:00", "Z")


class DigestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.projects = Path(self.temporary.name)
        self.count = 0

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_agent(self, agent: str, days_ago: float, errors: int = 0, tools: int = 4) -> None:
        self.count += 1
        folder = self.projects / "proj" / "session" / "subagents"
        folder.mkdir(parents=True, exist_ok=True)
        name = f"agent-{self.count}"
        (folder / f"{name}.meta.json").write_text(json.dumps({"agentType": agent, "finished": True}))
        start = NOW - days_ago * DAY
        blocks = [{"type": "tool_use"}] * tools + [{"type": "tool_result", "is_error": True}] * errors
        lines = [
            {"timestamp": stamp(start), "type": "user", "message": {"content": "go"}},
            {"timestamp": stamp(start + 60), "type": "assistant", "message": {"content": blocks}},
        ]
        (folder / f"{name}.jsonl").write_text("\n".join(json.dumps(line) for line in lines))
        import os

        os.utime(folder / f"{name}.meta.json", (NOW - days_ago * DAY, NOW - days_ago * DAY))

    def report(self) -> str:
        return agent_digest.digest(self.projects, 7, 28, now=NOW)

    def test_agent_with_steady_volume_is_not_flagged(self) -> None:
        for days_ago in (1, 9, 16, 23, 30):
            self.run_agent("code-reviewer", days_ago)
        self.assertIn("Flagged agents: 0", self.report())

    def test_agent_with_no_runs_this_window_is_flagged(self) -> None:
        for days_ago in (9, 12, 16, 23):
            self.run_agent("seo-specialist", days_ago)
        report = self.report()
        self.assertIn("! seo-specialist", report)
        self.assertIn("no runs this window", report)

    def test_tool_error_spike_is_flagged(self) -> None:
        for days_ago in (10, 17, 24, 30):
            self.run_agent("devops-infra-expert", days_ago, errors=0)
        for days_ago in (1, 2, 3):
            self.run_agent("devops-infra-expert", days_ago, errors=3)
        self.assertIn("tool errors", self.report())

    def test_small_window_skips_rate_flags(self) -> None:
        for days_ago in (10, 17, 24, 30):
            self.run_agent("product-owner", days_ago)
        self.run_agent("product-owner", 1, errors=4)
        self.assertNotIn("tool errors", self.report())


if __name__ == "__main__":
    unittest.main()
