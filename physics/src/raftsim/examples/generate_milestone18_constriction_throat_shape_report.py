"""Generate the Milestone 18 constriction throat shape diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone18 import build_milestone18_constriction_throat_shape_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dual-solver-manifest", type=Path, required=True)
    parser.add_argument("--wet-depth-threshold-m", type=float, default=0.15)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("reports/milestone18/constriction_throat_shape_diagnostic.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports/milestone18/constriction_throat_shape_diagnostic.md"),
    )
    args = parser.parse_args(argv)

    report = build_milestone18_constriction_throat_shape_report(
        args.dual_solver_manifest,
        wet_depth_threshold_m=args.wet_depth_threshold_m,
    )
    json_path = report.write_json(args.output_json)
    markdown_path = report.write_markdown(args.output_md)
    print(f"constriction_throat_report={json_path}")
    print(f"markdown_report={markdown_path}")
    print(f"decision={report.to_json_dict()['decision']}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
