"""Generate the Milestone 17 analytic shallow-water fixture suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..analytic_fixtures import write_analytic_fixture_suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/validation/milestone17/analytic_fixtures"),
        help="Directory for manifest.json and fixtures/.",
    )
    args = parser.parse_args(argv)

    manifest_path = write_analytic_fixture_suite(args.output_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"manifest={manifest_path}")
    print(f"fixture_count={len(manifest['fixtures'])}")
    for fixture in manifest["fixtures"]:
        print(f"fixture={fixture['fixture_id']} scenario={fixture['outputs']['scenario_package']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
