"""Generate the isolated South Fork terrain-detail v2 review candidate."""

from pathlib import Path

from raftsim.south_fork_terrain_detail_review import (
    MANIFEST_RELATIVE_PATH,
    generate_south_fork_terrain_detail_v2_review,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    generate_south_fork_terrain_detail_v2_review(repo_root)
    print(repo_root / MANIFEST_RELATIVE_PATH)


if __name__ == "__main__":
    main()
