"""Acquire imagery and build the Zambezi/Futaleufu production corridors."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.international_production_corridor import (
    DEFINITIONS,
    acquire_sentinel_visual,
    build_production_corridor,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("river_id", choices=sorted(DEFINITIONS))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--acquire-sentinel", action="store_true")
    args = parser.parse_args()
    if args.acquire_sentinel:
        print(acquire_sentinel_visual(args.repo_root, args.river_id))
    manifest = build_production_corridor(args.repo_root, args.river_id)
    print(f"{manifest['river_id']}: {manifest['route']['length_m']:.1f} m")


if __name__ == "__main__":
    main()

