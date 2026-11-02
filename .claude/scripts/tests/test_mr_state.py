from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "mr_state.py"
SPEC = importlib.util.spec_from_file_location("mr_state", SCRIPT)
assert SPEC and SPEC.loader
mr_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mr_state)

HEAD = "a" * 40
OLD = "b" * 40


def attestation(note_id: int, sha: str, at: str, verdict: str = "PASS", tier: str = "Tier 2") -> dict:
    body = f"REVIEW-ATTESTATION\nreviewer-instance: rev/{note_id}\nreviewed-sha: {sha}\ntier: {tier}\nverdict: {verdict}"
    return {"id": note_id, "body": body, "created_at": at}


def system(body: str, at: str) -> dict:
    return {"id": 0, "body": body, "created_at": at, "system": True}


MR = {"state": "opened", "sha": HEAD}
APPROVED = {"approved": True, "approved_by": [{"user": {"username": "approver"}}]}
NOBODY = {"approved": True, "approved_by": []}


class MrStateTests(unittest.TestCase):
    def test_no_attestation_needs_review(self) -> None:
        _, nxt = mr_state.evaluate(MR, NOBODY, [], None)
        self.assertTrue(nxt.startswith("review"))

    def test_attestation_on_old_sha_needs_review(self) -> None:
        notes = [attestation(1, OLD, "2026-11-02T08:00:00Z")]
        _, nxt = mr_state.evaluate(MR, NOBODY, notes, None)
        self.assertTrue(nxt.startswith("review"))

    def test_changes_requested_needs_review(self) -> None:
        notes = [attestation(1, HEAD, "2026-11-02T08:00:00Z", "changes requested")]
        _, nxt = mr_state.evaluate(MR, NOBODY, notes, None)
        self.assertTrue(nxt.startswith("review"))

    def test_attested_head_without_approval_needs_approval_only(self) -> None:
        notes = [attestation(1, HEAD, "2026-11-02T08:00:00Z")]
        _, nxt = mr_state.evaluate(MR, NOBODY, notes, None)
        self.assertTrue(nxt.startswith("approval-only"))

    def test_approved_true_with_empty_approved_by_is_not_approval(self) -> None:
        notes = [attestation(1, HEAD, "2026-11-02T08:00:00Z"), system("approved this merge request", "2026-11-02T08:03:00Z")]
        _, nxt = mr_state.evaluate(MR, NOBODY, notes, None)
        self.assertTrue(nxt.startswith("approval-only"))

    def test_approval_after_floor_is_merge_ready(self) -> None:
        notes = [attestation(1, HEAD, "2026-11-02T08:00:00Z"), system("approved this merge request", "2026-11-02T08:02:15Z")]
        _, nxt = mr_state.evaluate(MR, APPROVED, notes, None)
        self.assertEqual(nxt, "merge-ready")

    def test_approval_before_floor_is_not_ready(self) -> None:
        notes = [attestation(1, HEAD, "2026-11-02T08:00:00Z"), system("approved this merge request", "2026-11-02T08:01:00Z")]
        _, nxt = mr_state.evaluate(MR, APPROVED, notes, None)
        self.assertTrue(nxt.startswith("approval-only"))

    def test_unapproval_withdraws_the_earlier_approval(self) -> None:
        notes = [
            attestation(1, HEAD, "2026-11-02T08:00:00Z"),
            system("approved this merge request", "2026-11-02T08:03:00Z"),
            system("unapproved this merge request", "2026-11-02T08:04:00Z"),
        ]
        _, nxt = mr_state.evaluate(MR, NOBODY, notes, None)
        self.assertTrue(nxt.startswith("approval-only"))

    def test_reapproval_after_unapproval_counts(self) -> None:
        notes = [
            attestation(1, HEAD, "2026-11-02T08:00:00Z"),
            system("approved this merge request", "2026-11-02T08:03:00Z"),
            system("unapproved this merge request", "2026-11-02T08:04:00Z"),
            system("approved this merge request", "2026-11-02T08:05:00Z"),
        ]
        _, nxt = mr_state.evaluate(MR, APPROVED, notes, None)
        self.assertEqual(nxt, "merge-ready")

    def test_tier_1_floor_is_fifteen_seconds(self) -> None:
        notes = [
            attestation(1, HEAD, "2026-11-02T08:00:00Z", tier="Tier 1 (CI config)"),
            system("approved this merge request", "2026-11-02T08:00:20Z"),
        ]
        _, nxt = mr_state.evaluate(MR, APPROVED, notes, None)
        self.assertEqual(nxt, "merge-ready")

    def test_tier_2_floor_is_120_seconds(self) -> None:
        notes = [
            attestation(1, HEAD, "2026-11-02T08:00:00Z", tier="Tier 2"),
            system("approved this merge request", "2026-11-02T08:00:20Z"),
        ]
        _, nxt = mr_state.evaluate(MR, APPROVED, notes, None)
        self.assertTrue(nxt.startswith("approval-only"))

    def test_tier_0_needs_the_attestation_only(self) -> None:
        notes = [attestation(1, HEAD, "2026-11-02T08:00:00Z", tier="0 (documents only)")]
        _, nxt = mr_state.evaluate(MR, NOBODY, notes, None)
        self.assertTrue(nxt.startswith("merge-ready"))


if __name__ == "__main__":
    unittest.main()
