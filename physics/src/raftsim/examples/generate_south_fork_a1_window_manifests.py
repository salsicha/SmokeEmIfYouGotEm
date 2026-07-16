"""Generate South Fork A1 full-reach per-window source manifests."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_window_manifests import (
    build_south_fork_a1_full_reach_window_source_manifests,
    write_south_fork_a1_full_reach_window_source_manifests,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_paths = write_south_fork_a1_full_reach_window_source_manifests(args.repo_root)
    payload = build_south_fork_a1_full_reach_window_source_manifests(args.repo_root)
    print(f"written_count={len(output_paths)}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"window_count={payload['summary']['window_count']}")


if __name__ == "__main__":
    main()
