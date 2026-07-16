"""Generate the B2 per-river asset-promotion readiness report."""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.photoreal_b2_asset_promotion_readiness import (
    build_b2_asset_promotion_readiness_report,
    write_b2_asset_promotion_readiness_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    output_path = write_b2_asset_promotion_readiness_report(args.repo_root)
    payload = build_b2_asset_promotion_readiness_report()
    summary = payload["summary"]
    print(f"readiness_report={output_path}")
    print(f"schema={payload['schema']}")
    print(f"status={payload['status']}")
    print(f"ready_river_count={summary['ready_river_count']}")
    print(f"blocked_river_count={summary['blocked_river_count']}")
    print(f"can_promote_any_b2_asset_set={payload['global_gate_status']['can_promote_any_b2_asset_set']}")


if __name__ == "__main__":
    main()
