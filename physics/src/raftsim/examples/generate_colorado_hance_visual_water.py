"""Generate Colorado Hance capture-only hydraulic visual fields."""

from pathlib import Path

from raftsim.colorado_hance_visual_water import (
    MANIFEST_RELATIVE,
    build_colorado_hance_visual_water,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    build_colorado_hance_visual_water(repo_root)
    print(repo_root / MANIFEST_RELATIVE)


if __name__ == "__main__":
    main()
