"""Tune C++ reduced solver parameters against a reference scenario."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..pyclaw_reference import PyClawRunConfig
from ..scenario2_5d import FixtureScenario2_5DParameters, generate_fixture_scenario2_5d
from ..tuning import CppTuningCandidate, tune_cpp_solver_against_geoclaw, tune_cpp_solver_against_pyclaw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-solver", choices=("geoclaw", "pyclaw"), default="geoclaw")
    parser.add_argument("--fixture", default="flat_pool")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--nx", type=int, default=16)
    parser.add_argument("--ny", type=int, default=8)
    parser.add_argument("--duration", type=float, default=0.05)
    parser.add_argument("--cpp-solver", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/tuning"))
    parser.add_argument("--cpp-steps", type=int, default=None)
    parser.add_argument("--cpp-frame-interval", type=int, default=None)
    parser.add_argument("--candidate", action="append", default=None, help="label:feature_scale:roughness_scale")
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
    candidates = tuple(_parse_candidate(value) for value in args.candidate) if args.candidate else (
        CppTuningCandidate("baseline", feature_strength_scale=1.0, roughness_scale=1.0),
        CppTuningCandidate("lower_forcing", feature_strength_scale=0.75, roughness_scale=1.0),
        CppTuningCandidate("higher_roughness", feature_strength_scale=1.0, roughness_scale=1.25),
    )
    if args.reference_solver == "pyclaw":
        report = tune_cpp_solver_against_pyclaw(
            scenario,
            output_dir=args.output_dir,
            cpp_solver_executable=args.cpp_solver,
            candidates=candidates,
            pyclaw_config=PyClawRunConfig(num_output_times=1),
            cpp_steps=args.cpp_steps,
            cpp_frame_interval=args.cpp_frame_interval,
        )
        report_path = args.output_dir / "tuning_report.json"
    else:
        report = tune_cpp_solver_against_geoclaw(
            scenario,
            output_dir=args.output_dir,
            cpp_solver_executable=args.cpp_solver,
            candidates=candidates,
            cpp_steps=args.cpp_steps,
            cpp_frame_interval=args.cpp_frame_interval,
        )
        report_path = args.output_dir / "geoclaw_tuning_report.json"
    print(f"report={report_path}")
    print(f"best={report.best_candidate.candidate.label} score={report.best_candidate.score:.6g}")
    return 0


def _parse_candidate(value: str) -> CppTuningCandidate:
    label, feature_scale, roughness_scale = value.split(":")
    return CppTuningCandidate(
        label,
        feature_strength_scale=float(feature_scale),
        roughness_scale=float(roughness_scale),
    )


if __name__ == "__main__":
    raise SystemExit(main())
