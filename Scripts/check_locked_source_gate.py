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

A "locked source" is any GIT-TRACKED repo-relative path that appears as a key
mapping to a 64-hex digest anywhere inside a review/evidence JSON under the
scanned roots. Locks over never-versioned machine-local evidence (for example
unreal/Saved captures or physics/outputs) are out of scope for a COMMIT gate:
a commit cannot drift them, they differ per machine, and the packet/review
tests audit them on the machine that holds them. This keeps the gate's answer
identical on macOS, Linux, and CI. The full-suite baseline lives in
Scripts/full_suite_baseline.json and lists currently-failing test ids; the
gate fails on any failure not in it.

If a tracked locked source is present only as a git-lfs pointer (checkout
without LFS content), the gate aborts with a distinct error instead of
reporting false drift — fetch LFS content first.
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


LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _is_lfs_pointer(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(len(LFS_POINTER_PREFIX)) == LFS_POINTER_PREFIX
    except OSError:
        return False


def _tracked_files() -> set[str]:
    output = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {line.strip() for line in output.splitlines() if line.strip()}


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
    tracked = _tracked_files()
    violations = []
    pointer_files: set[str] = set()
    hash_cache: dict[str, str | None] = {}
    for review, source, recorded in locks:
        # Commit-gate scope: only git-tracked sources. Machine-local evidence
        # (unreal/Saved, physics/outputs, ...) cannot drift via a commit and
        # differs per machine; its audits run where it lives.
        if source not in tracked:
            continue
        if source not in hash_cache:
            path = REPO_ROOT / source
            if _is_lfs_pointer(path):
                pointer_files.add(source)
                hash_cache[source] = None
            else:
                hash_cache[source] = _sha256(path)
        if source in pointer_files:
            continue
        actual = hash_cache[source]
        if actual != recorded:
            violations.append(
                {
                    "review": review,
                    "source": source,
                    "recorded_sha256": recorded,
                    "actual_sha256": actual,
                }
            )
    if pointer_files:
        print(
            "locked-source gate: this checkout has git-lfs POINTERS instead of "
            f"content for {len(pointer_files)} locked source(s), e.g. "
            f"{sorted(pointer_files)[0]}"
        )
        print(
            "  Fetch LFS content first (git lfs pull; in CI set `lfs: true` on "
            "actions/checkout). Refusing to report drift against pointer bytes."
        )
        raise SystemExit(2)
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
    import shutil

    uv_binary = os.environ.get("RAFTSIM_UV", "").strip() or shutil.which("uv")
    if not uv_binary:
        print(
            "locked-source gate: `uv` not found on PATH. Install uv or set "
            "RAFTSIM_UV to its location, run the suite manually, then commit "
            "with RAFTSIM_SKIP_LOCKED_GATE=1 if it passed the baseline."
        )
        return 1
    result = subprocess.run(
        [uv_binary, "run", "pytest", "-q", "-rf", "--tb=no"],
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
