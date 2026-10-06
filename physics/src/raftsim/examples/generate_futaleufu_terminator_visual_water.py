"""Generate the Terminator median-flow capture field."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from raftsim.futaleufu_terminator_visual_water import (
    build_futaleufu_terminator_visual_water,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            build_futaleufu_terminator_visual_water(args.repo_root), indent=2
        )
    )


if __name__ == "__main__":
    main()
