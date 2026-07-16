"""Generate the South Fork B2 photoreal asset-selection manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_south_fork_asset_selection_b2 import (
    build_south_fork_b2_asset_selection,
    write_south_fork_b2_asset_selection,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_south_fork_b2_asset_selection(args.repo_root)
    payload = build_south_fork_b2_asset_selection()
    print(f"manifest={output_path}")
    print(f"schema={payload['schema']}")
    print(f"candidate_asset_count={payload['candidate_asset_count']}")
    print(f"assets_imported={payload['assets_imported']}")
    print(f"corridor_substitution_allowed={payload['corridor_substitution_allowed']}")


if __name__ == "__main__":
    main()
