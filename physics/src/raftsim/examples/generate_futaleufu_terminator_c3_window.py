"""Generate the Futaleufú Terminator reach-local C3 water-window scenario packages.

Writes the three flow-band scenario packages plus the honest window manifest, and
(when ``--solver-executable`` is provided) runs the genuine C++ FV solver (order 2,
HLL, calibrations disabled) at all three bands to produce the behavioral-validation
evidence.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from raftsim.futaleufu_terminator_c3_window import (
    SCENARIO_ROOT_RELATIVE,
    run_terminator_behavioral_validation,
    write_terminator_scenario_packages,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--solver-executable",
        type=Path,
        default=None,
        help="Path to the built raftsim_water_solver CLI; omit to only write packages.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Uncommitted solver run directory (default: physics/outputs/futaleufu_terminator_c3_window).",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=4000,
        help=(
            "Solver steps per band (fixed_dt 0.05 s; bounded feature-formation settle -- at this settle "
            "the reach is still approaching mass equilibrium and the solver flags its benign mass-drift "
            "validation, recorded honestly)."
        ),
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[4]
    manifest = write_terminator_scenario_packages(repo_root)
    print(f"wrote={SCENARIO_ROOT_RELATIVE}/window_manifest.json")
    for band_id, entry in manifest["flow_band_packages"].items():
        print(
            f"band={band_id} package={entry['package']} "
            f"Q={entry['target_discharge_m3s']:.2f} m3/s ({entry['flow_band_source']}) "
            f"stage_west={entry['stage_west_m']:.2f} m"
        )
    print(f"axis_to_thalweg_offset_m={manifest['geometry']['axis_to_heightfield_thalweg_offset_m']:.1f}")
    print(f"conditioned_drop_m={manifest['conditioning']['conditioned_profile_drop_m']:.2f}")

    if args.solver_executable is None:
        print("solver=skipped (no --solver-executable)")
        return

    work_dir = args.work_dir or (repo_root / "physics/outputs/futaleufu_terminator_c3_window")
    report = run_terminator_behavioral_validation(
        repo_root,
        args.solver_executable.resolve(),
        work_dir=work_dir,
        steps=args.steps,
    )
    print(f"wrote={SCENARIO_ROOT_RELATIVE}/behavioral_validation.json")
    for band_id, band in report["bands"].items():
        flags = {name: check["passed"] for name, check in band["checks"].items()}
        print(f"band={band_id} checks={flags} Q_achieved={band['achieved_discharge_m3s']}")
    print(f"headline_gate={report['headline_gate']}")


if __name__ == "__main__":
    main()
