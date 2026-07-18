"""Generate the adopted South Fork A1 full-reach route stationing artifacts."""

from __future__ import annotations

from pathlib import Path

from raftsim.south_fork_a1_adopted_route_stationing import (
    build_south_fork_a1_adopted_route_stationing,
    write_south_fork_a1_adopted_route_stationing,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_paths = write_south_fork_a1_adopted_route_stationing(repo_root)
    payload = build_south_fork_a1_adopted_route_stationing(repo_root)
    print(f"status={payload['status']}")
    print(f"decision_source={payload['decision']['decision_source']}")
    print(
        "adopted_route_length_m="
        f"{payload['station_axis']['adopted_route_length_m']}"
    )
    print(f"rapid_count={payload['rapid_station_summary']['rapid_count']}")
    for path in output_paths:
        print(path.relative_to(repo_root))


if __name__ == "__main__":
    main()
