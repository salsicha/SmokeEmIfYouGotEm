"""Generate South Fork A1 directed NHD station candidates."""

from __future__ import annotations

from pathlib import Path

from raftsim.south_fork_a1_directed_station_candidates import (
    build_south_fork_a1_directed_station_candidates,
    write_south_fork_a1_directed_station_candidates,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_south_fork_a1_directed_station_candidates(repo_root)
    payload = build_south_fork_a1_directed_station_candidates(repo_root)
    direction = payload["direction_evidence"]
    coloma = payload["source_anchor_station_candidates"][
        "coloma_bridge_checkpoint"
    ]
    print(f"status={payload['status']}")
    print(
        "directed_edge_count_from_chili_bar="
        f"{direction['directed_edge_count_from_chili_bar']}"
    )
    print(f"coloma_candidate_lon_lat={coloma['lon_lat']}")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
