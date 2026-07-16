"""Generate the South Fork A1 source-mile/access decision packet."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_source_mile_access_decision import (
    build_south_fork_a1_source_mile_access_decision_packet,
    write_south_fork_a1_source_mile_access_decision_packet,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_south_fork_a1_source_mile_access_decision_packet(
        args.repo_root
    )
    payload = build_south_fork_a1_source_mile_access_decision_packet(args.repo_root)
    evidence = payload["evidence_summary"]
    print(f"decision_packet={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"primary_access_source_station_miles={evidence['primary_access_source_station_miles']}")
    print(f"can_promote_route_now={payload['current_operating_mode']['can_promote_route_now']}")


if __name__ == "__main__":
    main()
