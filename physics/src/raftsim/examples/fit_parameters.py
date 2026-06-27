"""Fit C++ water and raft-force parameters against PyClaw output."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..pyclaw_reference import PyClawRunConfig
from ..scenario2_5d import FixtureScenario2_5DParameters, generate_fixture_scenario2_5d
from ..sweeps import ParameterSweepCandidate, default_parameter_sweep_candidates
from ..tuning import fit_cpp_and_raft_parameters_against_pyclaw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", default="flat_pool")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--nx", type=int, default=16)
    parser.add_argument("--ny", type=int, default=8)
    parser.add_argument("--duration", type=float, default=0.05)
    parser.add_argument("--cpp-solver", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/parameter_fit"))
    parser.add_argument("--cpp-steps", type=int, default=None)
    parser.add_argument("--cpp-frame-interval", type=int, default=None)
    parser.add_argument("--pyclaw-output-times", type=int, default=1)
    parser.add_argument("--scale-values", default="0.85,1.0,1.15")
    parser.add_argument(
        "--candidate",
        action="append",
        default=None,
        help="label:roughness:feature:drag:buoyancy:grounding_friction:contact_stiffness:contact_damping",
    )
    args = parser.parse_args(argv)

    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(
            fixture=args.fixture,
            seed=args.seed,
            nx=args.nx,
            ny=args.ny,
            duration=args.duration,
        )
    )
    if args.candidate:
        candidates = tuple(_parse_candidate(value) for value in args.candidate)
    else:
        candidates = default_parameter_sweep_candidates(_parse_scale_values(args.scale_values))
    report = fit_cpp_and_raft_parameters_against_pyclaw(
        scenario,
        output_dir=args.output_dir,
        cpp_solver_executable=args.cpp_solver,
        candidates=candidates,
        pyclaw_config=PyClawRunConfig(num_output_times=args.pyclaw_output_times),
        cpp_steps=args.cpp_steps,
        cpp_frame_interval=args.cpp_frame_interval,
    )
    print(f"report={args.output_dir / 'parameter_fit_report.json'}")
    print(f"best={report.best_candidate.candidate.label} score={report.best_candidate.score:.6g}")
    print(f"water_score={report.best_candidate.water_score:.6g}")
    print(f"raft_force_score={report.best_candidate.raft_force_score:.6g}")
    return 0


def _parse_scale_values(value: str) -> tuple[float, ...]:
    return tuple(float(part.strip()) for part in value.split(",") if part.strip())


def _parse_candidate(value: str) -> ParameterSweepCandidate:
    label, roughness, feature, drag, buoyancy, friction, stiffness, damping = value.split(":")
    return ParameterSweepCandidate(
        label=label,
        roughness_scale=float(roughness),
        feature_strength_scale=float(feature),
        raft_drag_scale=float(drag),
        buoyancy_density_scale=float(buoyancy),
        grounding_friction_scale=float(friction),
        contact_stiffness_scale=float(stiffness),
        contact_damping_scale=float(damping),
    )


if __name__ == "__main__":
    raise SystemExit(main())
