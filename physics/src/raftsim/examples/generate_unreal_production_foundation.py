from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.unreal_production_foundation import write_production_foundation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synchronize the Unreal production foundation with the project."
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    write_production_foundation(args.repo_root.resolve())


if __name__ == "__main__":
    main()
