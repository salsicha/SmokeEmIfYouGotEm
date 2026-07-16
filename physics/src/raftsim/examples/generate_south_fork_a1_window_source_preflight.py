"""Generate South Fork A1 source-pull preflight review."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_window_source_preflight import (
    build_south_fork_a1_window_source_pull_preflight,
    write_south_fork_a1_window_source_pull_preflight,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_south_fork_a1_window_source_pull_preflight(args.repo_root)
    payload = build_south_fork_a1_window_source_pull_preflight(args.repo_root)
    print(f"preflight={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(
        "can_execute_overcover_source_pull="
        f"{payload['execution_readiness']['can_execute_overcover_source_pull']}"
    )


if __name__ == "__main__":
    main()
