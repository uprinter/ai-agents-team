#!/usr/bin/env python3
"""Print the review state of one GitLab MR and say what is still needed.

Read-only. Reads the MR, its notes and its approvals with ``glab api`` (or from
JSON files for tests). It reports the head SHA, every ``REVIEW-ATTESTATION`` with
its reviewed SHA and verdict, each approval event with its time, and one last
line, ``NEXT``:

- ``merge-ready``: the head has a positive attestation and, by its tier, a
  current approval made late enough after it: Tier 0 needs the attestation only,
  Tier 1 a 15 s gap, Tier 2 a 120 s gap (``code-reviewer.md``); an attestation
  with no readable tier is read as Tier 2. ``--gap`` overrides the floor.
- ``approval-only``: the head has a positive attestation but no current approval.
  One reviewer instance approves; never two at once.
- ``review``: no positive attestation on the head. One reviewer reviews; never two at once.

``approved: true`` from the approvals API is not evidence: a project with no
approval rule returns it with an empty ``approved_by``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from urllib.parse import quote

INSTANCE = re.compile(r"^reviewer-instance:\s*(?P<value>\S+)", re.MULTILINE)
SHA = re.compile(r"^reviewed-sha:\s*(?P<value>[0-9a-fA-F]{7,64})\b", re.MULTILINE)
VERDICT = re.compile(r"^verdict:\s*(?P<value>.+?)\s*$", re.MULTILINE)
TIER = re.compile(r"^tier:\s*(?:tier\s*)?(?P<value>[012])", re.MULTILINE | re.IGNORECASE)
FLOOR_BY_TIER = {0: None, 1: 15, 2: 120}


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def positive(verdict: str) -> bool:
    text = verdict.lower()
    return ("pass" in text or "approve" in text) and "change" not in text and "block" not in text


def attestations(notes: list[dict]) -> list[dict]:
    found = []
    for note in sorted(notes, key=lambda item: item.get("created_at") or ""):
        body = note.get("body") or ""
        if "REVIEW-ATTESTATION" not in body:
            continue
        sha, instance, verdict, tier = SHA.search(body), INSTANCE.search(body), VERDICT.search(body), TIER.search(body)
        if not sha:
            continue
        found.append(
            {
                "id": note.get("id"),
                "at": parse_time(note["created_at"]),
                "sha": sha["value"].lower(),
                "instance": instance["value"] if instance else "?",
                "verdict": verdict["value"] if verdict else "?",
                "tier": int(tier["value"]) if tier else 2,
            }
        )
    return found


def approval_events(notes: list[dict]) -> list[tuple[datetime, bool]]:
    """Return (time, is_approval) for each GitLab system note about approval, oldest first."""
    events = []
    for note in sorted(notes, key=lambda item: item.get("created_at") or ""):
        body = (note.get("body") or "").strip().lower()
        if not note.get("system"):
            continue
        if body.startswith("unapproved"):
            events.append((parse_time(note["created_at"]), False))
        elif body.startswith("approved"):
            events.append((parse_time(note["created_at"]), True))
    return events


def current_approval(events: list[tuple[datetime, bool]]) -> datetime | None:
    """The time of the latest approval that no later unapproval has withdrawn."""
    current = None
    for at, approved in events:
        current = at if approved else None
    return current


def evaluate(mr: dict, approvals: dict, notes: list[dict], gap: int | None) -> tuple[list[str], str]:
    head = (mr.get("sha") or "").lower()
    lines = [f"state={mr.get('state')} head={head[:12]}"]
    rounds = attestations(notes)
    for item in rounds:
        mark = "head" if item["sha"] == head else "old"
        lines.append(
            f"attestation {item['id']} {item['at']:%H:%M:%S}Z {item['instance']} "
            f"sha={item['sha'][:12]} tier={item['tier']} verdict={item['verdict']} [{mark}]"
        )
    approved_by = [entry["user"]["username"] for entry in approvals.get("approved_by", [])]
    events = approval_events(notes)
    for at, approved in events:
        lines.append(f"{'approval' if approved else 'unapproval'} {at:%H:%M:%S}Z")
    lines.append(f"approved_by={approved_by or 'EMPTY'}")

    on_head = [item for item in rounds if item["sha"] == head and positive(item["verdict"])]
    if not on_head:
        return lines, "review: no positive attestation on the head; one reviewer"
    latest = on_head[-1]
    floor = gap if gap is not None else FLOOR_BY_TIER[latest["tier"]]
    if floor is None:
        return lines, "merge-ready: Tier 0 needs the attestation only"
    approved_at = current_approval(events)
    if not approved_by or approved_at is None:
        return lines, "approval-only: head attested, no current approval; one reviewer approves"
    seconds = (approved_at - latest["at"]).total_seconds()
    lines.append(f"approval is {seconds:.0f} s after attestation {latest['id']} (floor {floor} s)")
    if seconds < floor:
        return lines, "approval-only: approval came too early; one reviewer re-approves"
    return lines, "merge-ready"


def glab_json(path: str) -> object:
    result = subprocess.run(["glab", "api", "--paginate", path], check=True, capture_output=True, text=True)
    decoder, text, position, merged = json.JSONDecoder(), result.stdout, 0, []
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        page, position = decoder.raw_decode(text, position)
        if isinstance(page, list):
            merged.extend(page)
        else:
            return page
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="project path, for example group/project")
    parser.add_argument("mr", type=int, help="MR iid")
    parser.add_argument("--gap", type=int, default=None, help="seconds between attestation and approval; default by tier")
    args = parser.parse_args()
    base = f"projects/{quote(args.project, safe='')}/merge_requests/{args.mr}"
    mr, approvals, notes = glab_json(base), glab_json(f"{base}/approvals"), glab_json(f"{base}/notes?per_page=100")
    lines, nxt = evaluate(mr, approvals, notes, args.gap)
    print(f"MR {args.mr} {args.project}")
    for line in lines:
        print(line)
    print(f"NEXT {nxt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
