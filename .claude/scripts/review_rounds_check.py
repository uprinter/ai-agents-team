#!/usr/bin/env python3
"""Check that each review round of an MR was done by a different reviewer instance.

Reads the MR notes as JSON (a list of notes, each with ``body`` and optional
``created_at``) from a file, from stdin, or from ``glab`` for one MR. A
``REVIEW-ATTESTATION`` note has a ``reviewer-instance:`` field and a
``reviewed-sha:`` field. Two attestations for different SHAs are two rounds,
and they must name different instances. Two attestations for the same SHA are
one round and may repeat a token. Read-only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

INSTANCE = re.compile(r"^reviewer-instance:\s*(?P<value>.+?)\s*$", re.MULTILINE)
SHA = re.compile(r"^reviewed-sha:\s*(?P<value>[0-9a-fA-F]{7,64})\b", re.MULTILINE)


def attestations(notes: list[dict]) -> list[tuple[str, str]]:
    """Return (reviewer-instance, reviewed-sha) per attestation, in note order."""
    found: list[tuple[str, str]] = []
    for note in sorted(notes, key=lambda item: item.get("created_at") or ""):
        body = note.get("body") or ""
        if "REVIEW-ATTESTATION" not in body:
            continue
        instance, sha = INSTANCE.search(body), SHA.search(body)
        if instance and sha:
            found.append((instance["value"], sha["value"].lower()))
    return found


def check(notes: list[dict]) -> list[str]:
    errors: list[str] = []
    rounds = attestations(notes)
    if not rounds:
        return ["no REVIEW-ATTESTATION with reviewer-instance and reviewed-sha found"]
    instance_by_sha: dict[str, str] = {}
    for instance, sha in rounds:
        instance_by_sha.setdefault(sha, instance)
    seen: dict[str, str] = {}
    for sha, instance in instance_by_sha.items():
        if instance in seen:
            errors.append(
                f"reviewer-instance {instance!r} reviewed both {seen[instance][:12]} and {sha[:12]}; "
                "each review round needs a fresh instance"
            )
        seen.setdefault(instance, sha)
    return errors


def parse_pages(text: str) -> list[dict]:
    """Parse one JSON array, or several concatenated arrays as ``glab api --paginate`` prints them."""
    decoder = json.JSONDecoder()
    notes: list[dict] = []
    position = 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        page, position = decoder.raw_decode(text, position)
        notes.extend(page)
    return notes


def load_notes(args: argparse.Namespace) -> list[dict]:
    if args.mr:
        command = ["glab", "api", "--paginate", f"projects/:id/merge_requests/{args.mr}/notes"]
        return parse_pages(subprocess.run(command, check=True, capture_output=True, text=True).stdout)
    text = Path(args.notes).read_text(encoding="utf-8") if args.notes else sys.stdin.read()
    return parse_pages(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--notes", help="JSON file with the MR notes; stdin when omitted")
    source.add_argument("--mr", type=int, help="MR iid; reads notes with glab in the current repository")
    args = parser.parse_args()
    errors = check(load_notes(args))
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if not errors:
        print("Review rounds use distinct reviewer instances")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
