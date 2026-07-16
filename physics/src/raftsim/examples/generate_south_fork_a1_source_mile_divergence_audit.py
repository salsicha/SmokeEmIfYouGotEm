"""Generate South Fork A1 source-mile divergence audit."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_source_mile_divergence_audit import (
    build_south_fork_a1_source_mile_divergence_audit,
    write_south_fork_a1_source_mile_divergence_audit,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_paths = write_south_fork_a1_source_mile_divergence_audit(args.repo_root)
    payload = build_south_fork_a1_source_mile_divergence_audit(args.repo_root)
    summary = payload["divergence_summary"]
    print(f"written_count={len(output_paths)}")
    print(f"status={payload['status']}")
    print(
        "excess_source_path_after_21_miles_m="
        f"{summary['excess_source_path_after_21_miles_m']}"
    )
    print(
        "geodesic_21_mile_point_to_official_access_m="
        f"{summary['geodesic_21_mile_point_to_official_access_m']}"
    )


if __name__ == "__main__":
    main()
