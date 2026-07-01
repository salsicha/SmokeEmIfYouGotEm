"""Generate the Milestone 18 constriction face-state width/depth diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..milestone18 import build_milestone18_constriction_face_state_width_depth_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dual-solver-manifest", type=Path, required=True)
    parser.add_argument("--wet-depth-threshold-m", type=float, default=0.15)
    parser.add_argument("--velocity-sign-floor-mps", type=float, default=0.05)
    parser.add_argument("--flux-delta-threshold-m3ps", type=float, default=0.25)
    parser.add_argument("--depth-delta-threshold-m", type=float, default=0.25)
    parser.add_argument("--wet-width-delta-threshold-cells", type=int, default=1)
    parser.add_argument("--bank-row-delta-threshold-cells", type=int, default=1)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("reports/milestone18/constriction_face_state_width_depth_diagnostic.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports/milestone18/constriction_face_state_width_depth_diagnostic.md"),
    )
    args = parser.parse_args(argv)

    report = build_milestone18_constriction_face_state_width_depth_report(
        args.dual_solver_manifest,
        wet_depth_threshold_m=args.wet_depth_threshold_m,
        velocity_sign_floor_mps=args.velocity_sign_floor_mps,
        flux_delta_threshold_m3ps=args.flux_delta_threshold_m3ps,
        depth_delta_threshold_m=args.depth_delta_threshold_m,
        wet_width_delta_threshold_cells=args.wet_width_delta_threshold_cells,
        bank_row_delta_threshold_cells=args.bank_row_delta_threshold_cells,
    )
    json_path = report.write_json(args.output_json)
    markdown_path = report.write_markdown(args.output_md)
    print(f"constriction_face_state_width_depth_report={json_path}")
    print(f"markdown_report={markdown_path}")
    print(f"decision={report.to_json_dict()['decision']}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
