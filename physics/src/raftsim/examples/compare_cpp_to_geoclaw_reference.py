"""Run the C++ solver against an existing normalized GeoClaw reference."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from ..chrono_validation import compare_chrono_bridge_telemetry
from ..comparison import (
    ScenarioThresholds,
    compare_dual_solver_diagnostics,
    compare_dual_solver_fields,
    compare_dual_solver_probes,
    evaluate_dual_solver_thresholds,
)
from ..dual_solver import CppSolverRunConfig, run_cpp_solver_scenario
from ..real_world import (
    PlayerSelection,
    default_player_selections,
    generate_real_world_scenario2_5d,
    south_fork_american_section,
)
from ..scenario2_5d import read_scenario2_5d_package
from ..tuning import write_geoclaw_dual_solver_manifest

DEFAULT_THRESHOLDS = ScenarioThresholds()


@dataclass(frozen=True, slots=True)
class ExistingGeoClawReference:
    scenario_id: str
    output_dir: Path
    manifest_path: Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario-dir", type=Path, default=None, help="Shared 2.5D scenario package used by GeoClaw.")
    parser.add_argument("--geoclaw-normalized", type=Path, default=None, help="Normalized GeoClaw output directory.")
    parser.add_argument("--fixture-registry", type=Path, default=None, help="Committed GeoClaw fixture registry JSON.")
    parser.add_argument("--flow-band", default=None, help="Flow band to load from --fixture-registry.")
    parser.add_argument("--cpp-solver", type=Path, required=True, help="Path to raftsim_water_solver.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/geoclaw_cpp_comparison"))
    parser.add_argument("--cpp-steps", type=int, default=None)
    parser.add_argument("--cpp-frame-interval", type=int, default=None)
    parser.add_argument("--solver-mode", choices=("reduced", "finite_volume"), default="reduced")
    parser.add_argument("--boundary-mode", choices=("scenario", "pyclaw"), default="scenario")
    parser.add_argument("--flux-scheme", choices=("rusanov", "hll", "roe"), default="rusanov")
    parser.add_argument("--cfl", type=float, default=0.45)
    parser.add_argument("--feature-strength-scale", type=float, default=1.0)
    parser.add_argument("--roughness-scale", type=float, default=1.0)
    parser.add_argument("--bed-slope-source-scale", type=float, default=0.0)
    parser.add_argument("--max-field-linf", type=float, default=DEFAULT_THRESHOLDS.max_field_linf)
    parser.add_argument("--max-slope-linf", type=float, default=DEFAULT_THRESHOLDS.max_slope_linf)
    parser.add_argument("--max-wet-mismatch-fraction", type=float, default=DEFAULT_THRESHOLDS.max_wet_mismatch_fraction)
    parser.add_argument("--max-probe-linf", type=float, default=DEFAULT_THRESHOLDS.max_probe_linf)
    parser.add_argument("--max-cross-section-linf", type=float, default=DEFAULT_THRESHOLDS.max_cross_section_linf)
    parser.add_argument("--max-mass-drift-delta", type=float, default=DEFAULT_THRESHOLDS.max_mass_drift_delta)
    parser.add_argument("--velocity-depth-floor", type=float, default=DEFAULT_THRESHOLDS.velocity_depth_floor)
    args = parser.parse_args(argv)

    scenario, normalized_dir = _load_reference_selection(args)
    geoclaw_reference = _existing_geoclaw_reference(normalized_dir)
    if geoclaw_reference.scenario_id != scenario.metadata.scenario_id:
        raise SystemExit(
            "Normalized GeoClaw scenario_id does not match scenario package: "
            f"{geoclaw_reference.scenario_id} != {scenario.metadata.scenario_id}"
        )

    root = args.output_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    cpp_result = run_cpp_solver_scenario(
        scenario,
        output_dir=root,
        config=CppSolverRunConfig(
            executable=args.cpp_solver,
            steps=args.cpp_steps,
            frame_interval=args.cpp_frame_interval,
            solver_mode=args.solver_mode,
            boundary_mode=args.boundary_mode,
            flux_scheme=args.flux_scheme,
            cfl=args.cfl,
            feature_strength_scale=args.feature_strength_scale,
            roughness_scale=args.roughness_scale,
            bed_slope_source_scale=args.bed_slope_source_scale,
        ),
    )
    manifest_path = write_geoclaw_dual_solver_manifest(
        root,
        scenario,
        geoclaw_reference,
        cpp_result,
        geoclaw_runtime_seconds=_geoclaw_runtime_seconds(normalized_dir),
    )

    field_report = compare_dual_solver_fields(manifest_path, output_path=root / "field_comparison.json")
    probe_report = compare_dual_solver_probes(manifest_path, output_path=root / "probe_comparison.json")
    diagnostic_report = compare_dual_solver_diagnostics(manifest_path, output_path=root / "diagnostic_comparison.json")
    threshold_report = evaluate_dual_solver_thresholds(
        manifest_path,
        thresholds=ScenarioThresholds(
            max_field_linf=args.max_field_linf,
            max_slope_linf=args.max_slope_linf,
            max_wet_mismatch_fraction=args.max_wet_mismatch_fraction,
            max_probe_linf=args.max_probe_linf,
            max_cross_section_linf=args.max_cross_section_linf,
            max_mass_drift_delta=args.max_mass_drift_delta,
            velocity_depth_floor=args.velocity_depth_floor,
        ),
        output_path=root / "threshold_evaluation.json",
    )
    bridge_report = compare_chrono_bridge_telemetry(manifest_path, output_path=root / "chrono_bridge_telemetry_comparison.json")

    print(f"manifest={manifest_path}")
    print(f"field_report={root / 'field_comparison.json'}")
    print(f"probe_report={root / 'probe_comparison.json'}")
    print(f"diagnostic_report={root / 'diagnostic_comparison.json'}")
    print(f"threshold_report={root / 'threshold_evaluation.json'}")
    print(f"chrono_bridge_report={root / 'chrono_bridge_telemetry_comparison.json'}")
    print(f"threshold_passed={threshold_report.passed}")
    print(f"field_frames={len(field_report.frame_comparisons)}")
    print(f"point_probes={len(probe_report.point_probes)}")
    print(f"cross_sections={len(probe_report.cross_sections)}")
    print(f"mass_drift_delta={diagnostic_report.delta.mass_relative_drift_delta:.6g}")
    print(f"outcome_match={bridge_report.outcome_match}")
    return 0 if threshold_report.passed else 1


def _existing_geoclaw_reference(path: Path) -> ExistingGeoClawReference:
    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Normalized GeoClaw manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return ExistingGeoClawReference(
        scenario_id=str(manifest["scenario_id"]),
        output_dir=path,
        manifest_path=manifest_path,
    )


def _load_reference_selection(args: argparse.Namespace):
    if args.fixture_registry is not None:
        if args.flow_band is None:
            raise SystemExit("--flow-band is required when using --fixture-registry.")
        if args.scenario_dir is not None or args.geoclaw_normalized is not None:
            raise SystemExit("Use either --fixture-registry/--flow-band or --scenario-dir/--geoclaw-normalized, not both.")
        return _load_from_fixture_registry(args.fixture_registry.resolve(), str(args.flow_band))

    if args.scenario_dir is None or args.geoclaw_normalized is None:
        raise SystemExit("Provide --scenario-dir and --geoclaw-normalized, or --fixture-registry and --flow-band.")
    return read_scenario2_5d_package(args.scenario_dir.resolve()), args.geoclaw_normalized.resolve()


def _load_from_fixture_registry(registry_path: Path, flow_band: str):
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    fixtures = registry.get("fixtures", [])
    if not isinstance(fixtures, list):
        raise ValueError("fixture registry must include a fixtures list.")
    entry = next((item for item in fixtures if isinstance(item, dict) and item.get("flow_band") == flow_band), None)
    if entry is None:
        raise SystemExit(f"Flow band {flow_band!r} not found in {registry_path}.")

    grid = registry.get("grid", {})
    if not isinstance(grid, dict):
        raise ValueError("fixture registry grid must be an object.")
    scenario = _south_fork_scenario_from_registry_entry(
        flow_band=flow_band,
        difficulty=str(entry["difficulty"]),
        nx=int(grid["nx"]),
        ny=int(grid["ny"]),
        duration=float(registry["duration_seconds"]),
    )
    normalized_dir = registry_path.parent / str(entry["fixture_dir"])
    return scenario, normalized_dir


def _south_fork_scenario_from_registry_entry(
    *,
    flow_band: str,
    difficulty: str,
    nx: int,
    ny: int,
    duration: float,
):
    section = south_fork_american_section()
    default_selection = next(selection for selection in default_player_selections() if selection.flow_band == flow_band)
    selection = PlayerSelection(
        region=default_selection.region,
        river_id=section.river_id,
        section_id=section.section_id,
        season=default_selection.season,
        flow_band=flow_band,
        difficulty=difficulty,
        raft_setup=default_selection.raft_setup,
    )
    return generate_real_world_scenario2_5d(
        selection,
        nx=nx,
        ny=ny,
        duration=duration,
        pyclaw_reference_min_depth_m=0.0,
    )


def _geoclaw_runtime_seconds(normalized_dir: Path) -> float:
    source_manifest = json.loads((normalized_dir / "manifest.json").read_text(encoding="utf-8"))
    source_export_manifest = Path(str(source_manifest.get("source_export_manifest", "")))
    if not source_export_manifest.is_absolute():
        source_export_manifest = (normalized_dir / source_export_manifest).resolve()
    run_manifest_path = source_export_manifest.parent / "geoclaw_run_manifest.json"
    if not run_manifest_path.exists():
        return 0.0
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    result = run_manifest.get("result", {})
    if not isinstance(result, dict):
        return 0.0
    return float(result.get("runtime_seconds", 0.0))


if __name__ == "__main__":
    raise SystemExit(main())
