"""Generate the B1 photoreal asset survey/intake contract."""

from __future__ import annotations

from pathlib import Path

from raftsim.photoreal_asset_intake_b1 import (
    build_photoreal_asset_intake_b1,
    write_photoreal_asset_intake_b1,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    output_path = write_photoreal_asset_intake_b1(repo_root)
    payload = build_photoreal_asset_intake_b1()
    print(f"status={payload['status']}")
    print(f"river_count={len(payload['river_shopping_lists'])}")
    print(output_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
