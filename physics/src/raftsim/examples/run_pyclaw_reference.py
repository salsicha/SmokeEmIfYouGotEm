"""Run or check the optional PyClaw 2.5D reference harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..pyclaw_reference import (
    PyClawRunConfig,
    PyClawUnavailableError,
    canonical_pyclaw_scenarios,
    check_pyclaw_availability,
    run_pyclaw_reference,
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
    parser.add_argument("--check", action="store_true", help="Only report whether PyClaw is importable.")
    parser.add_argument("--allow-unavailable", action="store_true", help="Return 0 and write an unavailable report if PyClaw is missing.")
    parser.add_argument("--scenario-dir", type=Path, default=None, help="Existing 2.5D scenario package directory.")
    parser.add_argument("--fixture", choices=FIXTURE_CHOICES, default=None, help="Generate and run one canonical fixture.")
    parser.add_argument("--all-fixtures", action="store_true", help="Generate and run all canonical fixtures plus one procedural rapid.")
    parser.add_argument("--procedural", action="store_true", help="Generate and run one procedural rapid.")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--nx", type=int, default=64)
    parser.add_argument("--ny", type=int, default=32)
    parser.add_argument("--difficulty", type=float, default=0.45)
    parser.add_argument("--num-output-times", type=int, default=8)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/pyclaw_reference"))
    args = parser.parse_args(argv)

    availability = check_pyclaw_availability()
    if args.check:
        print(f"available={availability.available}")
        print(f"reason={availability.reason}")
        return 0 if availability.available or args.allow_unavailable else 1

    scenarios = _select_scenarios(args)
    if not availability.available:
        report_path = write_unavailable_report(args.output_dir, availability)
        print(f"PyClaw unavailable: {availability.reason}")
        print(f"report={report_path}")
        return 0 if args.allow_unavailable else 2

    config = PyClawRunConfig(num_output_times=args.num_output_times)
    for scenario in scenarios:
        output_dir = args.output_dir / scenario.metadata.scenario_id
        try:
            result = run_pyclaw_reference(scenario, config=config, output_dir=output_dir)
        except PyClawUnavailableError as exc:
            print(f"PyClaw unavailable: {exc}")
            return 0 if args.allow_unavailable else 2
        print(f"scenario={scenario.metadata.scenario_id}")
        print(f"output={output_dir}")
        print(f"validation_passed={result.validation.passed}")
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
                FixtureScenario2_5DParameters(fixture=args.fixture, seed=args.seed, nx=args.nx, ny=args.ny)
            ),
        )
    if args.all_fixtures:
        return canonical_pyclaw_scenarios(seed=args.seed)
    return (
        generate_procedural_scenario2_5d(
            ProceduralScenario2_5DParameters(seed=args.seed, nx=args.nx, ny=args.ny, difficulty=args.difficulty)
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
