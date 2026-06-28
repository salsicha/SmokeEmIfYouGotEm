"""Run setup checks for the optional GeoClaw 2.5D reference harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..geoclaw_reference import (
    GeoClawExportConfig,
    check_geoclaw_availability,
    export_geoclaw_scenario,
    write_geoclaw_setup_report,
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
    parser.add_argument("--check", action="store_true", help="Report whether GeoClaw is importable and runnable.")
    parser.add_argument("--allow-unavailable", action="store_true", help="Return 0 even if GeoClaw is not installed.")
    parser.add_argument("--scenario-dir", type=Path, default=None, help="Existing 2.5D scenario package directory.")
    parser.add_argument("--fixture", choices=FIXTURE_CHOICES, default=None, help="Generate and export one canonical fixture.")
    parser.add_argument("--procedural", action="store_true", help="Generate and export one procedural rapid.")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--nx", type=int, default=64)
    parser.add_argument("--ny", type=int, default=32)
    parser.add_argument("--difficulty", type=float, default=0.45)
    parser.add_argument("--num-output-times", type=int, default=8)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/geoclaw_reference"))
    args = parser.parse_args(argv)

    availability = check_geoclaw_availability()
    if args.check:
        print(f"available={availability.available}")
        print(f"reason={availability.reason}")
        print(f"missing_modules={','.join(availability.missing_modules)}")
        print(f"missing_executables={','.join(availability.missing_executables)}")
        write_geoclaw_setup_report(args.output_dir, availability)
        return 0 if availability.available or args.allow_unavailable else 1

    scenario = _select_scenario(args)
    if scenario is not None:
        result = export_geoclaw_scenario(
            scenario,
            args.output_dir / scenario.metadata.scenario_id,
            config=GeoClawExportConfig(num_output_times=args.num_output_times),
        )
        print(f"scenario={result.scenario_id}")
        print(f"manifest={result.manifest_path}")
        print(f"files={len(result.files)}")
        if not availability.available:
            print(f"GeoClaw unavailable for execution: {availability.reason}")
            return 0 if args.allow_unavailable else 2
        return 0

    report_path = write_geoclaw_setup_report(args.output_dir, availability)
    print(f"GeoClaw setup report={report_path}")
    if not availability.available:
        print(f"GeoClaw unavailable: {availability.reason}")
        return 0 if args.allow_unavailable else 2
    return 0


def _select_scenario(args: argparse.Namespace):
    selected = sum(bool(value) for value in (args.scenario_dir, args.fixture, args.procedural))
    if selected == 0:
        return None
    if selected != 1:
        raise SystemExit("Select at most one of --scenario-dir, --fixture, or --procedural.")
    if args.scenario_dir is not None:
        return read_scenario2_5d_package(args.scenario_dir)
    if args.fixture is not None:
        return generate_fixture_scenario2_5d(
            FixtureScenario2_5DParameters(fixture=args.fixture, seed=args.seed, nx=args.nx, ny=args.ny)
        )
    return generate_procedural_scenario2_5d(
        ProceduralScenario2_5DParameters(seed=args.seed, nx=args.nx, ny=args.ny, difficulty=args.difficulty)
    )


if __name__ == "__main__":
    raise SystemExit(main())
