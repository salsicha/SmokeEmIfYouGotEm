"""Cook the South Fork per-flow-band steady flow fields (release-1.0-plan section 5 A-1, P2)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..cooked_flow_fields import (
    CookedFlowFieldsRunConfig,
    ConvergenceThresholds,
    generate_south_fork_cooked_flow_fields,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cpp-solver",
        type=Path,
        default=Path("cpp/build/raftsim_water_solver"),
        help="Path to the raftsim_water_solver CLI binary.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/real_world/south_fork_american_chili_bar/cooked_flow_fields"),
        help="Committed package directory that receives the arrays and manifest.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("outputs/cooked_flow_fields"),
        help="Scratch directory for scenario packages and raw solver runs (gitignored).",
    )
    parser.add_argument("--steps", type=int, default=36000, help="Solver steps per band (fixed_dt is 1/60 s).")
    parser.add_argument("--frame-interval", type=int, default=600, help="Steps between convergence-monitor frames.")
    args = parser.parse_args(argv)

    config = CookedFlowFieldsRunConfig(
        steps=args.steps,
        frame_interval=args.frame_interval,
        thresholds=ConvergenceThresholds(),
    )
    manifest_path = generate_south_fork_cooked_flow_fields(
        executable=args.cpp_solver,
        output_dir=args.output_dir,
        work_dir=args.work_dir,
        config=config,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"manifest={manifest_path}")
    all_converged = True
    for band in manifest["bands"]:
        convergence = band["convergence"]
        final = convergence["final_window"]
        all_converged &= bool(convergence["converged"])
        print(
            f"band={band['band_id']} converged={convergence['converged']} "
            f"final_max_abs_dh_m={final['max_abs_dh_m']:.6f} "
            f"final_max_abs_du_m_per_s={final['max_abs_du_m_per_s']:.6f} "
            f"final_max_abs_dv_m_per_s={final['max_abs_dv_m_per_s']:.6f} "
            f"wet_fraction={band['field_stats']['wet_fraction']:.3f} "
            f"speed_max={band['field_stats']['speed_max_m_per_s']:.3f}"
        )
    return 0 if all_converged else 1


if __name__ == "__main__":
    raise SystemExit(main())
