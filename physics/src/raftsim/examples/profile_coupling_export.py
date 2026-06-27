"""Profile raft coupling and probe/export runtime costs."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..profiling import profile_probe_export_runs, profile_raft_coupling_runs
from ..pyclaw_reference import PyClawRunConfig, canonical_pyclaw_scenarios
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
    parser.add_argument("--scenario-dir", type=Path, default=None, help="Existing 2.5D scenario package directory.")
    parser.add_argument("--fixture", choices=FIXTURE_CHOICES, default=None, help="Generate and profile one canonical fixture.")
    parser.add_argument("--all-fixtures", action="store_true", help="Generate and profile all canonical fixtures plus one procedural rapid.")
    parser.add_argument("--procedural", action="store_true", help="Generate and profile one procedural rapid.")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--nx", type=int, default=32)
    parser.add_argument("--ny", type=int, default=16)
    parser.add_argument("--duration", type=float, default=0.25)
    parser.add_argument("--difficulty", type=float, default=0.45)
    parser.add_argument("--samples-per-run", type=int, default=120)
    parser.add_argument("--num-output-times", type=int, default=2)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/profiles/coupling_export"))
    args = parser.parse_args(argv)

    scenarios = tuple(_select_scenarios(args))
    coupling = profile_raft_coupling_runs(
        scenarios,
        repetitions=args.repetitions,
        samples_per_run=args.samples_per_run,
    )
    export = profile_probe_export_runs(
        scenarios,
        config=PyClawRunConfig(num_output_times=args.num_output_times),
        repetitions=args.repetitions,
        output_dir=args.output_dir / "exports",
    )
    coupling_path = coupling.write_json(args.output_dir / "raft_coupling_profile.json")
    export_path = export.write_json(args.output_dir / "probe_export_profile.json")
    print(f"coupling_profile={coupling_path}")
    print(f"probe_export_profile={export_path}")
    print(f"coupling_mean_runtime_seconds={coupling.mean_runtime_seconds:.6f}")
    print(f"probe_export_mean_runtime_seconds={export.mean_runtime_seconds:.6f}")
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
