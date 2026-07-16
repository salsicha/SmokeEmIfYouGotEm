"""Generate official access-geometry discrepancy review for South Fork A1."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_official_access_geometry_review import (
    build_south_fork_a1_official_access_geometry_discrepancy_review,
    write_south_fork_a1_official_access_geometry_review,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_paths = write_south_fork_a1_official_access_geometry_review(args.repo_root)
    payload = build_south_fork_a1_official_access_geometry_discrepancy_review(
        args.repo_root
    )
    print(f"written_count={len(output_paths)}")
    print(f"status={payload['status']}")
    print(f"rejected_candidate_count={payload['summary']['rejected_candidate_count']}")
    print(
        "minimum_distance_to_primary_raft_takeout_m="
        f"{payload['summary']['minimum_distance_to_primary_raft_takeout_m']}"
    )


if __name__ == "__main__":
    main()
