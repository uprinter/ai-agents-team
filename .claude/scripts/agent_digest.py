#!/usr/bin/env python3
"""Weekly digest of agent runs, read from Claude Code's own subagent transcripts.

Each run leaves ``<projects>/<project>/<session>/subagents/agent-<id>.jsonl``
and a ``.meta.json`` with the agent type. The digest compares the last
``--days`` days with the ``--baseline-days`` before them, per agent type, and
flags a drop in volume, a jump in tool errors, steps or duration, and runs
that never finished. It reads local files only and costs no tokens.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path


MIN_RUNS = 3


def parse_time(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def read_run(meta_path: Path) -> dict | None:
    try:
        meta = json.loads(meta_path.read_text())
    except (OSError, ValueError):
        return None
    transcript = meta_path.with_name(meta_path.name.removesuffix(".meta.json") + ".jsonl")
    if not transcript.is_file():
        return None
    first = last = None
    tools = errors = 0
    try:
        lines = transcript.read_text(errors="replace").splitlines()
    except OSError:
        return None
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        stamp = record.get("timestamp")
        if stamp:
            seconds = parse_time(stamp)
            first = seconds if first is None else min(first, seconds)
            last = seconds if last is None else max(last, seconds)
        content = (record.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            kind = block.get("type")
            if kind == "tool_use":
                tools += 1
            elif kind == "tool_result" and block.get("is_error"):
                errors += 1
    if first is None or last is None:
        return None
    return {
        "agent": meta.get("agentType") or "unknown",
        "start": first,
        "seconds": last - first,
        "tools": tools,
        "errors": errors,
        "finished": bool(meta.get("finished", True)),
    }


def collect(projects: Path, since: float) -> list[dict]:
    runs = []
    for meta_path in projects.glob("*/*/subagents/*.meta.json"):
        if meta_path.stat().st_mtime < since:
            continue
        run = read_run(meta_path)
        if run and run["start"] >= since:
            runs.append(run)
    return runs


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def summarize(runs: list[dict]) -> dict:
    tools = sum(run["tools"] for run in runs)
    return {
        "runs": len(runs),
        "unfinished": sum(1 for run in runs if not run["finished"]),
        "error_rate": sum(run["errors"] for run in runs) / tools if tools else 0.0,
        "steps": median([run["tools"] for run in runs]),
        "seconds": median([run["seconds"] for run in runs]),
    }


def flags(window: dict, baseline: dict, weeks: float) -> list[str]:
    found = []
    expected = baseline["runs"] / weeks
    if baseline["runs"] >= MIN_RUNS and window["runs"] == 0:
        found.append("no runs this window")
    elif baseline["runs"] >= MIN_RUNS and window["runs"] < expected / 2:
        found.append(f"volume fell: {window['runs']} against {expected:.1f} per window")
    if window["runs"] < MIN_RUNS:
        return found
    if window["unfinished"] / window["runs"] > baseline["unfinished"] / max(baseline["runs"], 1) + 0.25:
        found.append(f"{window['unfinished']} of {window['runs']} runs unfinished")
    if window["error_rate"] >= 0.1 and window["error_rate"] >= 2 * baseline["error_rate"]:
        found.append(f"tool errors {window['error_rate']:.0%} against {baseline['error_rate']:.0%}")
    if baseline["steps"] and window["steps"] >= 2 * baseline["steps"]:
        found.append(f"steps per run {window['steps']:.0f} against {baseline['steps']:.0f}")
    if baseline["seconds"] and window["seconds"] >= 2 * baseline["seconds"]:
        found.append(f"duration {window['seconds']:.0f}s against {baseline['seconds']:.0f}s")
    return found


def digest(projects: Path, days: int, baseline_days: int, now: float | None = None) -> str:
    now = time.time() if now is None else now
    window_start = now - days * 86400
    baseline_start = window_start - baseline_days * 86400
    runs = collect(projects, baseline_start)
    window = [run for run in runs if run["start"] >= window_start]
    baseline = [run for run in runs if run["start"] < window_start]
    weeks = max(baseline_days / days, 1.0)
    agents = sorted({run["agent"] for run in runs})
    lines = [f"# Agent digest: last {days} days against the {baseline_days} before", ""]
    flagged = 0
    for agent in agents:
        now_stats = summarize([run for run in window if run["agent"] == agent])
        old_stats = summarize([run for run in baseline if run["agent"] == agent])
        found = flags(now_stats, old_stats, weeks)
        flagged += bool(found)
        mark = "!" if found else " "
        lines.append(f"{mark} {agent}: {now_stats['runs']} runs (baseline {old_stats['runs']})")
        lines.extend(f"    - {item}" for item in found)
    if not agents:
        lines.append("No runs found.")
    lines += ["", f"Flagged agents: {flagged}"]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--baseline-days", type=int, default=28)
    parser.add_argument("--projects", type=Path, default=Path.home() / ".claude" / "projects")
    args = parser.parse_args()
    if not args.projects.is_dir():
        print(f"ERROR: no transcripts at {args.projects}", file=sys.stderr)
        return 1
    print(digest(args.projects, args.days, args.baseline_days))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
