"""Generate the deterministic South Fork full-reach geography completion."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.south_fork_procedural_geography import (
    DEFAULT_SEED,
    build_south_fork_procedural_geography_manifest,
    write_south_fork_procedural_geography,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    output = write_south_fork_procedural_geography(args.repo_root, args.seed)
    manifest = build_south_fork_procedural_geography_manifest(args.repo_root)
    print(f"wrote={output}")
    print(f"status={manifest['status']}")
    print(f"station_end_m={manifest['grid']['station_end_m']}")
    print(f"tile_count={manifest['unreal_import']['tile_count']}")
    print(f"boulder_count={manifest['hydraulic_features']['boulder_count']}")


if __name__ == "__main__":
    main()
