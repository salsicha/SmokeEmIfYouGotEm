"""Generate raft/water parameter sweep reports."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..pyclaw_reference import canonical_pyclaw_scenarios
from ..scenario2_5d import (
    FixtureScenario2_5DParameters,
    ProceduralScenario2_5DParameters,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
    read_scenario2_5d_package,
)
from ..sweeps import default_parameter_sweep_candidates, run_raft_force_parameter_sweep

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
    parser.add_argument("--scenario-dir", type=Path, default=None, help="Existing 2.5D scenario package directory.")
    parser.add_argument("--fixture", choices=FIXTURE_CHOICES, default=None, help="Generate and sweep one canonical fixture.")
    parser.add_argument("--all-fixtures", action="store_true", help="Generate and sweep all canonical fixtures plus one procedural rapid.")
    parser.add_argument("--procedural", action="store_true", help="Generate and sweep one procedural rapid.")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--nx", type=int, default=32)
    parser.add_argument("--ny", type=int, default=16)
    parser.add_argument("--duration", type=float, default=0.25)
    parser.add_argument("--difficulty", type=float, default=0.45)
    parser.add_argument("--scale-values", default="0.75,1.0,1.25", help="Comma-separated positive scale values.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/parameter_sweeps"))
    args = parser.parse_args(argv)

    candidates = default_parameter_sweep_candidates(_parse_scale_values(args.scale_values))
    for scenario in _select_scenarios(args):
        report = run_raft_force_parameter_sweep(scenario, candidates=candidates)
        report_path = report.write_json(args.output_dir / f"{scenario.metadata.scenario_id}_parameter_sweep.json")
        print(f"scenario={scenario.metadata.scenario_id}")
        print(f"report={report_path}")
        print(f"candidates={len(report.results)}")
    return 0


def _parse_scale_values(value: str) -> tuple[float, ...]:
    return tuple(float(part.strip()) for part in value.split(",") if part.strip())


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
