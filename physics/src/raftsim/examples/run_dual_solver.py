"""Run PyClaw and the C++ reduced solver on one shared 2.5D scenario."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..dual_solver import CppSolverRunConfig, DualSolverRunConfig, run_dual_solver_scenario
from ..pyclaw_reference import PyClawRunConfig
from ..scenario2_5d import (
    FixtureScenario2_5DParameters,
    ProceduralScenario2_5DParameters,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario-dir", type=Path, default=None, help="Existing shared 2.5D scenario package.")
    parser.add_argument("--mode", choices=("fixture", "procedural"), default="fixture")
    parser.add_argument("--fixture", default="flat_pool")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--nx", type=int, default=24)
    parser.add_argument("--ny", type=int, default=12)
    parser.add_argument("--duration", type=float, default=0.25)
    parser.add_argument("--difficulty", type=float, default=0.45)
    parser.add_argument("--feature-count", type=int, default=None)
    parser.add_argument("--cpp-solver", type=Path, required=True, help="Path to raftsim_water_solver.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/dual_solver"))
    parser.add_argument("--cpp-steps", type=int, default=None)
    parser.add_argument("--cpp-frame-interval", type=int, default=None)
    parser.add_argument("--pyclaw-output-times", type=int, default=2)
    args = parser.parse_args(argv)

    scenario_or_path = args.scenario_dir
    if scenario_or_path is None:
        if args.mode == "fixture":
            scenario_or_path = generate_fixture_scenario2_5d(
                FixtureScenario2_5DParameters(
                    fixture=args.fixture,
                    seed=args.seed,
                    nx=args.nx,
                    ny=args.ny,
                    duration=args.duration,
                )
            )
        else:
            scenario_or_path = generate_procedural_scenario2_5d(
                ProceduralScenario2_5DParameters(
                    seed=args.seed,
                    nx=args.nx,
                    ny=args.ny,
                    duration=args.duration,
                    difficulty=args.difficulty,
                    feature_count=args.feature_count,
                )
            )

    result = run_dual_solver_scenario(
        scenario_or_path,
        output_dir=args.output_dir,
        config=DualSolverRunConfig(
            pyclaw=PyClawRunConfig(num_output_times=args.pyclaw_output_times),
            cpp=CppSolverRunConfig(
                executable=args.cpp_solver,
                steps=args.cpp_steps,
                frame_interval=args.cpp_frame_interval,
            ),
        ),
    )
    print(f"manifest={result.manifest_path}")
    print(f"scenario={result.scenario_dir / 'scenario.json'}")
    print(f"pyclaw={result.pyclaw_output_dir / 'manifest.json'}")
    print(f"cpp={result.cpp.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
