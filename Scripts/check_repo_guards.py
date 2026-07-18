#!/usr/bin/env python3
"""Repository guards (release-1.0-plan.md P1): fail CI when a commit adds an
oversized non-LFS file or tracks a file under a generated-map path."""

from __future__ import annotations

import subprocess
import sys

MAX_NON_LFS_BYTES = 50 * 1024 * 1024
FORBIDDEN_TRACKED_PREFIXES = (
    "unreal/Content/RaftSim/Maps/EnvironmentPreviews/",
    "unreal/Content/RaftSim/Environment/GeneratedLocalReview/",
)


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


def lfs_files() -> set[str]:
    out = subprocess.run(
        ["git", "lfs", "ls-files", "-n"], capture_output=True, text=True
    ).stdout
    return {line for line in out.splitlines() if line}


def main() -> int:
    failures: list[str] = []
    lfs = lfs_files()
    for path in tracked_files():
        for prefix in FORBIDDEN_TRACKED_PREFIXES:
            if path.startswith(prefix):
                failures.append(f"tracked file under generated-map path: {path}")
        if path in lfs:
            continue
        size = subprocess.run(
            ["git", "cat-file", "-s", f"HEAD:{path}"], capture_output=True, text=True
        )
        if size.returncode == 0 and int(size.stdout.strip() or 0) > MAX_NON_LFS_BYTES:
            failures.append(
                f"non-LFS file over {MAX_NON_LFS_BYTES // (1024 * 1024)} MB: {path}"
            )
    for failure in failures:
        print(f"GUARD FAILURE: {failure}")
    if not failures:
        print("repo guards passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
