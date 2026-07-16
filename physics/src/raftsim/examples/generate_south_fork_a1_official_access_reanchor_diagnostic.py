"""Generate South Fork A1 official-access reanchor route diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_a1_official_access_reanchor_diagnostic import (
    build_south_fork_a1_official_access_reanchor_diagnostic,
    write_south_fork_a1_official_access_reanchor_diagnostic,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_paths = write_south_fork_a1_official_access_reanchor_diagnostic(
        args.repo_root
    )
    payload = build_south_fork_a1_official_access_reanchor_diagnostic(args.repo_root)
    route = payload["route_path"]
    official_seed = payload["official_access_seed"]
    print(f"written_count={len(output_paths)}")
    print(f"status={payload['status']}")
    print(
        "official_seed_snap_distance_m="
        f"{official_seed['nearest_graph_node_distance_m']}"
    )
    print(f"path_geometry_length_m={route['path_geometry_length_m']}")
    print(
        "geometry_minus_published_run_length_m="
        f"{route['geometry_minus_published_run_length_m']}"
    )


if __name__ == "__main__":
    main()
