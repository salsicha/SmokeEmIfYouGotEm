"""Profile PyClaw 2.5D reference runs for research-loop runtime cost."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..profiling import profile_pyclaw_reference_runs
from ..pyclaw_reference import (
    PyClawRunConfig,
    canonical_pyclaw_scenarios,
    check_pyclaw_availability,
    write_unavailable_report,
)
from ..scenario2_5d import (
    FixtureScenario2_5DParameters,
    ProceduralScenario2_5DParameters,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
    read_scenario2_5d_package,
)

FIXTURE_CHOICES = (
    "flat_pool",
    "uniform_channel",
    "dam_break",
    "bed_step",
    "constriction",
    "wet_dry_shoreline",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-unavailable", action="store_true", help="Return 0 and write a report if PyClaw is missing.")
    parser.add_argument("--scenario-dir", type=Path, default=None, help="Existing 2.5D scenario package directory.")
    parser.add_argument("--fixture", choices=FIXTURE_CHOICES, default=None, help="Generate and profile one canonical fixture.")
    parser.add_argument("--all-fixtures", action="store_true", help="Generate and profile all canonical fixtures plus one procedural rapid.")
    parser.add_argument("--procedural", action="store_true", help="Generate and profile one procedural rapid.")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--nx", type=int, default=32)
    parser.add_argument("--ny", type=int, default=16)
    parser.add_argument("--duration", type=float, default=0.25)
    parser.add_argument("--difficulty", type=float, default=0.45)
    parser.add_argument("--num-output-times", type=int, default=2)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/profiles/pyclaw"))
    args = parser.parse_args(argv)

    availability = check_pyclaw_availability()
    if not availability.available:
        report_path = write_unavailable_report(args.output_dir, availability)
        print(f"PyClaw unavailable: {availability.reason}")
        print(f"report={report_path}")
        return 0 if args.allow_unavailable else 2

    report = profile_pyclaw_reference_runs(
        _select_scenarios(args),
        config=PyClawRunConfig(num_output_times=args.num_output_times),
        repetitions=args.repetitions,
        output_dir=args.output_dir / "runs",
    )
    report_path = report.write_json(args.output_dir / "pyclaw_profile.json")
    print(f"profile={report_path}")
    print(f"runs={len(report.runs)}")
    print(f"mean_runtime_seconds={report.mean_runtime_seconds:.6f}")
    print(f"mean_seconds_per_simulated_second={report.mean_seconds_per_simulated_second:.6f}")
    return 0


def _select_scenarios(args: argparse.Namespace):
    selected = sum(bool(value) for value in (args.scenario_dir, args.fixture, args.all_fixtures, args.procedural))
    if selected != 1:
        raise SystemExit("Select exactly one of --scenario-dir, --fixture, --all-fixtures, or --procedural.")
    if args.scenario_dir is not None:
        return (read_scenario2_5d_package(args.scenario_dir),)
    if args.fixture is not None:
        return (
            generate_fixture_scenario2_5d(
                FixtureScenario2_5DParameters(
                    fixture=args.fixture,
                    seed=args.seed,
                    nx=args.nx,
                    ny=args.ny,
                    duration=args.duration,
                )
            ),
        )
    if args.all_fixtures:
        return canonical_pyclaw_scenarios(seed=args.seed)
    return (
        generate_procedural_scenario2_5d(
            ProceduralScenario2_5DParameters(
                seed=args.seed,
                nx=args.nx,
                ny=args.ny,
                duration=args.duration,
                difficulty=args.difficulty,
            )
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
