"""Generate South Fork A1 source-mile/access option matrix."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_source_mile_access_options import (
    build_south_fork_a1_source_mile_access_option_matrix,
    write_south_fork_a1_source_mile_access_option_matrix,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_paths = write_south_fork_a1_source_mile_access_option_matrix(args.repo_root)
    payload = build_south_fork_a1_source_mile_access_option_matrix(args.repo_root)
    summary = payload["summary"]
    print(f"written_count={len(output_paths)}")
    print(f"status={payload['status']}")
    print(f"official_access_option_count={summary['official_access_option_count']}")
    print(
        "all_access_options_conflict_with_published_source_miles="
        f"{summary['all_access_options_conflict_with_published_source_miles']}"
    )
    print(
        "primary_option_source_station_miles="
        f"{summary['primary_option_source_station_miles']}"
    )


if __name__ == "__main__":
    main()
