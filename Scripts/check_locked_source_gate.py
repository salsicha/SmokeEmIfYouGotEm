#!/usr/bin/env python3
"""Gate commits that touch hash-locked sources (release-1.0-plan.md testing rule).

Review/evidence JSONs across the repo record SHA-256 locks for the source
files their conclusions depend on. Editing a locked source without refreshing
those locks silently invalidates the evidence chain; that drift is exactly
what this gate blocks.

Modes:
  --all      Repo-wide consistency: every recorded lock must match the file on
             disk, except entries explicitly recorded in the debt file. Run in
             CI (repo guards) and before tagging releases.
  --staged   Pre-commit: if any staged file is a locked source, (1) each
             touched lock must be refreshed in the same commit, and (2) the
             full physics suite must pass (no failures beyond the recorded
             baseline). Install via Scripts/install_git_hooks.sh.
             RAFTSIM_SKIP_LOCKED_GATE=1 skips (use consciously).
  --write-debt
             Regenerate Scripts/locked_source_debt.json from current
             mismatches. Maintainer action for acknowledging pre-existing
             drift; entries should only ever be removed as locks are repaired.

A "locked source" is any repo-relative path that appears as a key mapping to
a 64-hex digest anywhere inside a review/evidence JSON under the scanned
roots. The full-suite baseline lives in Scripts/full_suite_baseline.json and
lists currently-failing test ids; the gate fails on any failure not in it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("docs", "unreal/Content", "physics/data", "physics/reports")
DEBT_PATH = REPO_ROOT / "Scripts/locked_source_debt.json"
BASELINE_PATH = REPO_ROOT / "Scripts/full_suite_baseline.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _iter_locks(node: object, review: str):
    """Yield (review, source_path, recorded_hash) for path->digest entries."""
    if isinstance(node, dict):
        for key, value in node.items():
            if (
                isinstance(key, str)
                and "/" in key
                and not key.startswith(("http://", "https://"))
                and isinstance(value, str)
                and HEX64.fullmatch(value)
            ):
                yield review, key, value
            else:
                yield from _iter_locks(value, review)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_locks(value, review)


def collect_locks() -> list[tuple[str, str, str]]:
    locks: list[tuple[str, str, str]] = []
    for root in SCAN_ROOTS:
        for json_path in sorted((REPO_ROOT / root).rglob("*.json")):
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            review = str(json_path.relative_to(REPO_ROOT))
            locks.extend(_iter_locks(data, review))
    return locks


def load_debt() -> set[tuple[str, str, str]]:
    if not DEBT_PATH.exists():
        return set()
    data = json.loads(DEBT_PATH.read_text(encoding="utf-8"))
    return {
        (entry["review"], entry["source"], entry["recorded_sha256"])
        for entry in data.get("entries", [])
    }


def find_violations(locks) -> list[dict]:
    violations = []
    hash_cache: dict[str, str | None] = {}
    for review, source, recorded in locks:
        if source not in hash_cache:
            hash_cache[source] = _sha256(REPO_ROOT / source)
        actual = hash_cache[source]
        # Locks may legitimately point at never-versioned machine-local
        # evidence (unreal/Saved, physics/outputs); absence there is not
        # drift on other checkouts.
        if actual is None and source.startswith(("unreal/Saved/", "physics/outputs/")):
            continue
        if actual != recorded:
            violations.append(
                {
                    "review": review,
                    "source": source,
                    "recorded_sha256": recorded,
                    "actual_sha256": actual,
                }
            )
    return violations


def check_all() -> int:
    debt = load_debt()
    violations = [
        v
        for v in find_violations(collect_locks())
        if (v["review"], v["source"], v["recorded_sha256"]) not in debt
    ]
    if violations:
        print("locked-source gate: drifted locks not covered by recorded debt:")
        for v in violations:
            print(f"  {v['review']}\n    {v['source']}")
            print(f"    recorded {v['recorded_sha256']}")
            print(f"    actual   {v['actual_sha256']}")
        print(
            f"{len(violations)} violation(s). Refresh the review locks (and re-run "
            "their evidence flows) in the same change, or record acknowledged "
            "debt via --write-debt."
        )
        return 1
    print("locked-source gate: all locks consistent (recorded debt excluded)")
    return 0


def _staged_files() -> set[str]:
    output = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {line.strip() for line in output.splitlines() if line.strip()}


def _run_full_suite() -> int:
    baseline = set()
    if BASELINE_PATH.exists():
        baseline = set(
            json.loads(BASELINE_PATH.read_text(encoding="utf-8")).get(
                "known_failures", []
            )
        )
    print("locked-source gate: running the full physics suite (required for "
          "commits touching locked sources)...")
    result = subprocess.run(
        ["uv", "run", "pytest", "-q", "-rf", "--tb=no"],
        cwd=REPO_ROOT / "physics",
        capture_output=True,
        text=True,
    )
    failed = {
        line.split()[1]
        for line in result.stdout.splitlines()
        if line.startswith("FAILED ")
    }
    new_failures = failed - baseline
    print(result.stdout.splitlines()[-1] if result.stdout.splitlines() else "")
    if new_failures:
        print("locked-source gate: failures beyond the recorded baseline:")
        for test_id in sorted(new_failures):
            print(f"  {test_id}")
        return 1
    fixed = baseline - failed
    if fixed:
        print(
            "locked-source gate: baseline entries now pass and should be removed "
            f"from {BASELINE_PATH.name}: {', '.join(sorted(fixed))}"
        )
    print("locked-source gate: full suite has no failures beyond the baseline")
    return 0


def check_staged() -> int:
    if os.environ.get("RAFTSIM_SKIP_LOCKED_GATE") == "1":
        print("locked-source gate: skipped via RAFTSIM_SKIP_LOCKED_GATE=1")
        return 0
    staged = _staged_files()
    if not staged:
        return 0
    locks = collect_locks()
    locked_sources = {source for _, source, _ in locks}
    touched = sorted(staged & locked_sources)
    if not touched:
        return 0
    print("locked-source gate: staged files are hash-locked sources:")
    for path in touched:
        print(f"  {path}")
    debt = load_debt()
    stale = [
        v
        for v in find_violations(
            [(r, s, h) for r, s, h in locks if s in staged]
        )
        if (v["review"], v["source"], v["recorded_sha256"]) not in debt
    ]
    if stale:
        print("locked-source gate: these locks must be refreshed in this commit:")
        for v in stale:
            print(f"  {v['review']} -> {v['source']}")
        return 1
    return _run_full_suite()


def write_debt() -> int:
    violations = find_violations(collect_locks())
    payload = {
        "schema": "raftsim.locked_source_debt.v1",
        "policy": (
            "Acknowledged pre-existing lock drift. Entries may only be removed "
            "(as locks are repaired on the evidence machine); adding entries "
            "requires the same scrutiny as changing evidence."
        ),
        "entries": [
            {
                "review": v["review"],
                "source": v["source"],
                "recorded_sha256": v["recorded_sha256"],
            }
            for v in violations
        ],
    }
    DEBT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"recorded {len(violations)} debt entr(ies) in {DEBT_PATH}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--staged", action="store_true")
    group.add_argument("--write-debt", action="store_true")
    args = parser.parse_args()
    if args.all:
        return check_all()
    if args.staged:
        return check_staged()
    return write_debt()


if __name__ == "__main__":
    sys.exit(main())
