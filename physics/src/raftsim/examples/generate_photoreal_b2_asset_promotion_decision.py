"""Generate the B2 per-river asset-promotion decision template."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_b2_asset_promotion_decision import (
    build_b2_asset_promotion_decision_template,
    write_b2_asset_promotion_decision_template,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_b2_asset_promotion_decision_template(args.repo_root)
    payload = build_b2_asset_promotion_decision_template()
    print(f"decision_template={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"river_decision_count={payload['river_decision_count']}")
    print(f"can_run_corridor_substitution={payload['promotion_gate']['can_run_corridor_substitution']}")


if __name__ == "__main__":
    main()
