"""Generate the B1 per-asset-set photoreal intake command manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_asset_set_intake_b1 import (
    build_photoreal_asset_set_intake_b1,
    write_photoreal_asset_set_intake_b1,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_photoreal_asset_set_intake_b1(args.repo_root)
    payload = build_photoreal_asset_set_intake_b1(args.repo_root)
    print(f"manifest={output_path}")
    print(f"schema={payload['schema']}")
    print(f"asset_set_count={payload['asset_set_count']}")
    print(f"assets_imported={payload['assets_imported']}")


if __name__ == "__main__":
    main()
