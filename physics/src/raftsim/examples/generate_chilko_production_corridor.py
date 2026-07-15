"""Acquire inputs and build the Chilko River production corridor."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.chilko_production_corridor import (
    acquire_chilko_source_clips,
    build_chilko_production_corridor,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--acquire-source-clips", action="store_true")
    args = parser.parse_args()
    if args.acquire_source_clips:
        for path in acquire_chilko_source_clips(args.repo_root):
            print(path.relative_to(args.repo_root.resolve()))
    manifest = build_chilko_production_corridor(args.repo_root)
    print(
        f"{manifest['river_id']}: {manifest['route']['length_m']:.1f} m, "
        f"{manifest['physical_size_m']['width']:.1f} x "
        f"{manifest['physical_size_m']['height']:.1f} m"
    )


if __name__ == "__main__":
    main()
