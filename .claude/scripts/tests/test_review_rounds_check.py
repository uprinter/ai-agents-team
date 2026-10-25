from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "review_rounds_check.py"
SPEC = importlib.util.spec_from_file_location("review_rounds_check", SCRIPT)
assert SPEC and SPEC.loader
review_rounds_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review_rounds_check)

SHA_A = "a" * 40
SHA_B = "b" * 40


def note(instance: str, sha: str, at: str) -> dict:
    body = f"REVIEW-ATTESTATION\nreviewer-instance: {instance}\nreviewed-sha: {sha}\nverdict: approve"
    return {"body": body, "created_at": at}


class ReviewRoundsTests(unittest.TestCase):
    def test_distinct_instances_per_round_pass(self) -> None:
        notes = [note("rev-1", SHA_A, "2026-01-01"), note("rev-2", SHA_B, "2026-01-02")]
        self.assertEqual(review_rounds_check.check(notes), [])

    def test_same_instance_on_two_rounds_fails(self) -> None:
        notes = [note("rev-1", SHA_A, "2026-01-01"), note("rev-1", SHA_B, "2026-01-02")]
        errors = review_rounds_check.check(notes)
        self.assertEqual(len(errors), 1)
        self.assertIn("rev-1", errors[0])

    def test_same_instance_repeating_one_sha_is_one_round(self) -> None:
        notes = [note("rev-1", SHA_A, "2026-01-01"), note("rev-1", SHA_A, "2026-01-02")]
        self.assertEqual(review_rounds_check.check(notes), [])

    def test_notes_out_of_order_are_sorted_by_time(self) -> None:
        notes = [note("rev-2", SHA_B, "2026-01-02"), note("rev-1", SHA_A, "2026-01-01")]
        self.assertEqual([i for i, _ in review_rounds_check.attestations(notes)], ["rev-1", "rev-2"])

    def test_no_attestation_fails(self) -> None:
        notes = [{"body": "looks good", "created_at": "2026-01-01"}]
        self.assertEqual(len(review_rounds_check.check(notes)), 1)

    def test_note_without_literal_fields_is_ignored(self) -> None:
        notes = [{"body": "REVIEW-ATTESTATION\nCommit reviewed: abc1234"}]
        self.assertEqual(len(review_rounds_check.check(notes)), 1)

    def test_concatenated_pages_are_all_read(self) -> None:
        first = json.dumps([note("rev-1", SHA_A, "2026-01-01")])
        second = json.dumps([note("rev-1", SHA_B, "2026-01-02")])
        notes = review_rounds_check.parse_pages(first + "\n" + second + "\n")
        self.assertEqual(len(notes), 2)
        self.assertEqual(len(review_rounds_check.check(notes)), 1)

    def test_single_array_and_empty_input(self) -> None:
        self.assertEqual(review_rounds_check.parse_pages('[{"body": "x"}]'), [{"body": "x"}])
        self.assertEqual(review_rounds_check.parse_pages(""), [])


if __name__ == "__main__":
    unittest.main()
