"""Generate or execute South Fork A1 full-reach window source-pull tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from raftsim.south_fork_a1_window_source_execution import (
    DEFAULT_MAX_BYTES_PER_FILE,
    build_south_fork_a1_window_source_pull_execution_plan,
    execute_south_fork_a1_window_source_pulls,
    write_south_fork_a1_window_source_pull_execution_plan,
)


def _csv_set(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--window-ids", type=str, default=None)
    parser.add_argument("--roles", type=str, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--max-bytes-per-file", type=int, default=DEFAULT_MAX_BYTES_PER_FILE)
    args = parser.parse_args()

    plan_path = write_south_fork_a1_window_source_pull_execution_plan(args.repo_root)
    plan = build_south_fork_a1_window_source_pull_execution_plan(args.repo_root)
    print(f"plan={plan_path}")
    print(f"schema={plan['schema']}")
    print(f"task_count={plan['summary']['task_count']}")
    print(f"destination_missing_count={plan['summary']['destination_missing_count']}")

    if args.execute:
        report = execute_south_fork_a1_window_source_pulls(
            args.repo_root,
            window_ids=_csv_set(args.window_ids),
            roles=_csv_set(args.roles),
            overwrite=args.overwrite,
            max_bytes_per_file=args.max_bytes_per_file,
        )
        print(json.dumps(report["summary"], sort_keys=True))
        if report["summary"]["failed_count"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
