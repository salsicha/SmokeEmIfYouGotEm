"""Generate the reach-local Terminator Landscape inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from raftsim.futaleufu_terminator_visual_terrain import (
    build_futaleufu_terminator_visual_terrain,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-size-px", type=int, default=1009)
    args = parser.parse_args()
    manifest = build_futaleufu_terminator_visual_terrain(
        args.repo_root, output_size_px=args.output_size_px
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
