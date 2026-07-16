"""Generate South Fork A1 full-reach window source-pull status."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_window_source_status import (
    build_south_fork_a1_window_source_pull_status,
    write_south_fork_a1_window_source_pull_status,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_south_fork_a1_window_source_pull_status(args.repo_root)
    payload = build_south_fork_a1_window_source_pull_status(args.repo_root)
    print(f"wrote={output_path}")
    print(f"status={payload['status']}")
    print(f"window_count={payload['summary']['window_count']}")
    print(f"missing_source_file_count={payload['summary']['missing_source_file_count']}")


if __name__ == "__main__":
    main()
