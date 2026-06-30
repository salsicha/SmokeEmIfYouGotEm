"""Run setup checks for the optional GeoClaw 2.5D reference harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..geoclaw_reference import (
    GEOCLAW_CANONICAL_FIXTURES,
    GeoClawExportConfig,
    GeoClawRunConfig,
    check_geoclaw_availability,
    export_cascading_geoclaw_scenarios,
    export_canonical_geoclaw_scenarios,
    export_rafting_geoclaw_scenarios,
    export_geoclaw_scenario,
    normalize_geoclaw_cascading_fixed_grid_output,
    normalize_geoclaw_fixed_grid_output,
    run_geoclaw_export,
    write_geoclaw_setup_report,
)
from ..real_world import PlayerSelection, default_player_selections, south_fork_american_flow_bands, south_fork_american_section
from ..scenario2_5d import (
    FixtureScenario2_5DParameters,
    ProceduralScenario2_5DParameters,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
    read_scenario2_5d_package,
)

FIXTURE_CHOICES = GEOCLAW_CANONICAL_FIXTURES
SOUTH_FORK_FLOW_BANDS = tuple(band.flow_band for band in south_fork_american_flow_bands())
DIFFICULTY_CHOICES = ("beginner", "intermediate", "advanced", "expert")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report whether GeoClaw is importable and runnable.")
    parser.add_argument("--allow-unavailable", action="store_true", help="Return 0 even if GeoClaw is not installed.")
    parser.add_argument("--scenario-dir", type=Path, default=None, help="Existing 2.5D scenario package directory.")
    parser.add_argument("--fixture", choices=FIXTURE_CHOICES, default=None, help="Generate and export one canonical fixture.")
    parser.add_argument("--south-fork-flow-band", choices=SOUTH_FORK_FLOW_BANDS, default=None, help="Generate one South Fork American real-world flow-band scenario.")
    parser.add_argument("--south-fork-difficulty", choices=DIFFICULTY_CHOICES, default=None, help="Override the default difficulty for a South Fork flow band.")
    parser.add_argument("--all-fixtures", action="store_true", help="Generate and export the full canonical GeoClaw fixture suite.")
    parser.add_argument("--rafting-suite", action="store_true", help="Generate and export rafting feature cases plus real-world flow bands.")
    parser.add_argument("--cascading-suite", action="store_true", help="Generate and export South Fork cascading reach/drop flow-band packages.")
    parser.add_argument("--normalize-export", type=Path, default=None, help="Normalize an existing GeoClaw export directory.")
    parser.add_argument("--normalize-cascading-export", type=Path, default=None, help="Normalize an existing cascading GeoClaw export into stitched and reach-window outputs.")
    parser.add_argument("--run-export", type=Path, default=None, help="Run an existing generated GeoClaw export directory.")
    parser.add_argument("--run", action="store_true", help="Run GeoClaw after exporting one selected scenario.")
    parser.add_argument("--claw-root", type=Path, default=None, help="Optional Clawpack checkout root for GeoClaw execution.")
    parser.add_argument("--make-target", default=".output", help="Make target to use for GeoClaw execution.")
    parser.add_argument("--timeout-seconds", type=float, default=300.0, help="GeoClaw execution timeout.")
    parser.add_argument("--no-normalize-after-run", action="store_true", help="Skip normalization after a GeoClaw run.")
    parser.add_argument("--procedural", action="store_true", help="Generate and export one procedural rapid.")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--nx", type=int, default=64)
    parser.add_argument("--ny", type=int, default=32)
    parser.add_argument("--difficulty", type=float, default=0.45)
    parser.add_argument("--num-output-times", type=int, default=8)
    parser.add_argument("--amr-min-level", type=int, default=1)
    parser.add_argument("--amr-max-level", type=int, default=3)
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

    if args.normalize_export is not None:
        _ensure_single_mode(args, "normalize-export")
        result = normalize_geoclaw_fixed_grid_output(args.normalize_export, args.output_dir)
        print(f"scenario={result.scenario_id}")
        print(f"manifest={result.manifest_path}")
        print(f"frames={result.frame_count}")
        return 0

    if args.normalize_cascading_export is not None:
        _ensure_single_mode(args, "normalize-cascading-export")
        result = normalize_geoclaw_cascading_fixed_grid_output(args.normalize_cascading_export, args.output_dir)
        print(f"scenario={result.scenario_id}")
        print(f"manifest={result.manifest_path}")
        print(f"stitched_manifest={result.stitched_manifest_path}")
        print(f"reach_windows={result.reach_window_count}")
        print(f"drop_transition_windows={result.drop_transition_window_count}")
        return 0

    if args.run_export is not None:
        _ensure_single_mode(args, "run-export")
        if not availability.available:
            print(f"GeoClaw unavailable for execution: {availability.reason}")
            return 0 if args.allow_unavailable else 2
        return _run_export(args.run_export, args, _export_config(args))

    if args.all_fixtures:
        if args.run:
            raise SystemExit("--run is only supported for one selected scenario, not suites.")
        if any((args.scenario_dir, args.fixture, args.south_fork_flow_band, args.rafting_suite, args.cascading_suite, args.normalize_export, args.normalize_cascading_export, args.run_export, args.procedural)):
            raise SystemExit("Select --all-fixtures by itself, or choose one single scenario source.")
        result = export_canonical_geoclaw_scenarios(
            args.output_dir / f"canonical_geoclaw_seed_{args.seed}",
            seed=args.seed,
            config=_export_config(args),
        )
        print(f"suite={result.suite_id}")
        print(f"manifest={result.manifest_path}")
        print(f"scenarios={len(result.results)}")
        if not availability.available:
            print(f"GeoClaw unavailable for execution: {availability.reason}")
            return 0 if args.allow_unavailable else 2
        return 0

    if args.rafting_suite:
        if args.run:
            raise SystemExit("--run is only supported for one selected scenario, not suites.")
        if any((args.scenario_dir, args.fixture, args.south_fork_flow_band, args.cascading_suite, args.normalize_export, args.normalize_cascading_export, args.run_export, args.procedural)):
            raise SystemExit("Select --rafting-suite by itself, or choose one single scenario source.")
        result = export_rafting_geoclaw_scenarios(
            args.output_dir / f"rafting_geoclaw_seed_{args.seed}",
            seed=args.seed,
            config=_export_config(args),
        )
        print(f"suite={result.suite_id}")
        print(f"manifest={result.manifest_path}")
        print(f"scenarios={len(result.results)}")
        if not availability.available:
            print(f"GeoClaw unavailable for execution: {availability.reason}")
            return 0 if args.allow_unavailable else 2
        return 0

    if args.cascading_suite:
        if args.run:
            raise SystemExit("--run is only supported for one selected scenario, not suites.")
        if any((args.scenario_dir, args.fixture, args.south_fork_flow_band, args.all_fixtures, args.rafting_suite, args.normalize_export, args.normalize_cascading_export, args.run_export, args.procedural)):
            raise SystemExit("Select --cascading-suite by itself, or choose one single scenario source.")
        result = export_cascading_geoclaw_scenarios(
            args.output_dir / "south_fork_cascading_geoclaw",
            config=_export_config(args),
            nx=args.nx,
            ny=args.ny,
        )
        print(f"suite={result.suite_id}")
        print(f"manifest={result.manifest_path}")
        print(f"scenarios={len(result.results)}")
        if not availability.available:
            print(f"GeoClaw unavailable for execution: {availability.reason}")
            return 0 if args.allow_unavailable else 2
        return 0

    scenario = _select_scenario(args)
    if scenario is not None:
        cfg = _export_config(args)
        result = export_geoclaw_scenario(
            scenario,
            args.output_dir / scenario.metadata.scenario_id,
            config=cfg,
        )
        print(f"scenario={result.scenario_id}")
        print(f"manifest={result.manifest_path}")
        print(f"files={len(result.files)}")
        if not availability.available:
            print(f"GeoClaw unavailable for execution: {availability.reason}")
            return 0 if args.allow_unavailable else 2
        if args.run:
            return _run_export(result.output_dir, args, cfg)
        return 0

    report_path = write_geoclaw_setup_report(args.output_dir, availability)
    print(f"GeoClaw setup report={report_path}")
    if not availability.available:
        print(f"GeoClaw unavailable: {availability.reason}")
        return 0 if args.allow_unavailable else 2
    return 0


def _select_scenario(args: argparse.Namespace):
    selected = sum(bool(value) for value in (args.scenario_dir, args.fixture, args.south_fork_flow_band, args.procedural))
    if selected == 0:
        return None
    if selected != 1:
        raise SystemExit("Select at most one of --scenario-dir, --fixture, --south-fork-flow-band, or --procedural.")
    if args.scenario_dir is not None:
        return read_scenario2_5d_package(args.scenario_dir)
    if args.fixture is not None:
        return generate_fixture_scenario2_5d(
            FixtureScenario2_5DParameters(fixture=args.fixture, seed=args.seed, nx=args.nx, ny=args.ny)
        )
    if args.south_fork_flow_band is not None:
        return _south_fork_scenario(args)
    return generate_procedural_scenario2_5d(
        ProceduralScenario2_5DParameters(seed=args.seed, nx=args.nx, ny=args.ny, difficulty=args.difficulty)
    )


def _south_fork_scenario(args: argparse.Namespace):
    section = south_fork_american_section()
    default_selection = next(selection for selection in default_player_selections() if selection.flow_band == args.south_fork_flow_band)
    selection = PlayerSelection(
        region=default_selection.region,
        river_id=section.river_id,
        section_id=section.section_id,
        season=default_selection.season,
        flow_band=args.south_fork_flow_band,
        difficulty=args.south_fork_difficulty or default_selection.difficulty,
        raft_setup=default_selection.raft_setup,
    )
    from ..real_world import generate_real_world_scenario2_5d

    return generate_real_world_scenario2_5d(
        selection,
        nx=args.nx,
        ny=args.ny,
        duration=8.0,
        pyclaw_reference_min_depth_m=0.0,
    )


def _export_config(args: argparse.Namespace) -> GeoClawExportConfig:
    return GeoClawExportConfig(
        num_output_times=args.num_output_times,
        amr_min_level=args.amr_min_level,
        amr_max_level=args.amr_max_level,
    )


def _ensure_single_mode(args: argparse.Namespace, mode: str) -> None:
    conflicts = {
        "normalize-export": (args.scenario_dir, args.fixture, args.south_fork_flow_band, args.all_fixtures, args.rafting_suite, args.cascading_suite, args.normalize_cascading_export, args.run_export, args.procedural, args.run),
        "normalize-cascading-export": (args.scenario_dir, args.fixture, args.south_fork_flow_band, args.all_fixtures, args.rafting_suite, args.cascading_suite, args.normalize_export, args.run_export, args.procedural, args.run),
        "run-export": (args.scenario_dir, args.fixture, args.south_fork_flow_band, args.all_fixtures, args.rafting_suite, args.cascading_suite, args.normalize_export, args.normalize_cascading_export, args.procedural, args.run),
    }
    if any(conflicts[mode]):
        raise SystemExit(f"Select --{mode} by itself, or choose one single scenario source.")


def _run_export(export_dir: Path, args: argparse.Namespace, export_config: GeoClawExportConfig) -> int:
    run_result = run_geoclaw_export(
        export_dir,
        config=GeoClawRunConfig(
            claw_root=args.claw_root,
            timeout_seconds=args.timeout_seconds,
            make_target=args.make_target,
        ),
        export_config=export_config,
    )
    print(f"run_manifest={run_result.export_dir / 'geoclaw_run_manifest.json'}")
    print(f"run_returncode={run_result.returncode}")
    print(f"run_frames={run_result.frame_count}")
    if not args.no_normalize_after_run and run_result.returncode == 0:
        normalized = normalize_geoclaw_fixed_grid_output(run_result.export_dir, run_result.export_dir / "normalized", config=export_config)
        print(f"normalized_manifest={normalized.manifest_path}")
        print(f"normalized_frames={normalized.frame_count}")
    return 0 if run_result.passed else run_result.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
