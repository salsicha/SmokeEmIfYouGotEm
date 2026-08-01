from __future__ import annotations

import argparse
import json
from pathlib import Path

from raftsim.colorado_hance_visual_terrain import build_colorado_hance_visual_terrain


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the reach-local Colorado Hance Unreal terrain bundle."
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--output-size-px", type=int, default=1009)
    args = parser.parse_args()
    manifest = build_colorado_hance_visual_terrain(
        args.repo_root,
        output_dir=args.output_dir,
        output_size_px=args.output_size_px,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
