"""Generate the South Fork A1 full-reach NHD route graph diagnostic."""

from __future__ import annotations

from pathlib import Path

from raftsim.south_fork_a1_route_graph import (
    build_south_fork_a1_route_graph_diagnostic,
    write_south_fork_a1_route_graph_diagnostic,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_south_fork_a1_route_graph_diagnostic(repo_root)
    payload = build_south_fork_a1_route_graph_diagnostic(repo_root)
    source_pool = payload["source_pool"]
    coloma = payload["anchor_diagnostics"]["current_coloma_access_seed"]
    print(f"status={payload['status']}")
    print(f"feature_count={source_pool['feature_count']}")
    print(f"coloma_graph_station_m={coloma['graph_station_from_chili_bar_m']}")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
