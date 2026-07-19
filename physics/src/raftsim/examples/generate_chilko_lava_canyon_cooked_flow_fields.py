"""Cook the Lava Canyon (Chilko) C3 window steady flow fields for in-engine live water.

This is the authored-scenario-window counterpart to
``generate_troublemaker_cooked_flow_fields``: it runs the genuine C++ FV solver
(order 2, HLL, calibrations disabled) directly on the committed Lava Canyon
per-band scenario packages until steady state, then exports the per-band
``h/u/v/bed/wet_mask`` grids and a ``raftsim.cooked_flow_fields.v1`` manifest that
``FRaftSimLiveWaterWindow::CreateFromCookedFields`` reads unchanged. The solver is
configured with the same settings the window was authored / behaviorally validated
with (roughness_scale=1.0, bed_slope_source_scale=1.0, feature_strength_scale=0.0),
and each band's Manning n is recorded in the manifest so the loader no longer has
to pass roughness as a parameter.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..chilko_lava_canyon_c3_window import RAPID_NAME, RIVER_ID, WINDOW_ID
from ..cooked_flow_fields import (
    AuthoredWindowBand,
    ConvergenceThresholds,
    CookedFlowFieldsRunConfig,
    generate_authored_window_cooked_flow_fields,
)
from ..real_world import DISCHARGE_CFS_TO_M3S

SCENARIO_ROOT_RELATIVE = Path(
    "physics/data/real_world/chilko_river_lava_canyon/scenario_lava_canyon"
)
OUTPUT_DIR_RELATIVE = SCENARIO_ROOT_RELATIVE / "cooked_flow_fields"


def _lava_canyon_bands(repo_root: Path) -> tuple[AuthoredWindowBand, ...]:
    """Build the authored band sources from the committed window manifest."""

    window_manifest = json.loads(
        (repo_root / SCENARIO_ROOT_RELATIVE / "window_manifest.json").read_text(encoding="utf-8")
    )
    packages = window_manifest["flow_band_packages"]
    bands = []
    for band_id in ("low_runnable", "median_runnable", "high_runnable"):
        entry = packages[band_id]
        target_m3s = float(entry["target_discharge_m3s"])
        bands.append(
            AuthoredWindowBand(
                band_id=band_id,
                scenario_dir=repo_root / entry["package"],
                discharge_target_m3s=target_m3s,
                discharge_target_cfs=target_m3s / DISCHARGE_CFS_TO_M3S,
            )
        )
    return tuple(bands)


def _window_extra_top_level(repo_root: Path) -> dict[str, object]:
    window_manifest = json.loads(
        (repo_root / SCENARIO_ROOT_RELATIVE / "window_manifest.json").read_text(encoding="utf-8")
    )
    honesty = window_manifest.get("honesty", {})
    return {
        "window_id": WINDOW_ID,
        "rapid_name": RAPID_NAME,
        "window_provenance": {
            "adopted_axis_station_m": window_manifest.get("adopted_axis_station_m"),
            "station_adoption": "deterministic_upper_canyon_max_sustained_descent_order_2_of_5_pending_review",
            "dem_ground_sample_m": 30.0,
            "bed_geometry_authority": honesty.get("bed_geometry_authority", "interpreted_bed_geometry"),
            "pending_human_review": honesty.get("pending_human_review", True),
            "production_promoted": honesty.get("production_promoted", False),
            "roughness_manning_n": window_manifest.get("window_parameters", {}).get("roughness_manning_n"),
        },
    }


def _notes() -> list[str]:
    return [
        "Fields are the genuine finite-volume solver's approximate steady state for the "
        "authored Lava Canyon (Chilko / White Mile) C3 window: order 2, HLL, calibrations "
        "disabled, feature_strength_scale=0 (the wave train / constrictions / boulders are "
        "authored bed geometry, not dynamic feature forcing), matching the settings the window "
        "was behaviorally validated with.",
        "The UE river-window loader (FRaftSimLiveWaterWindow::CreateFromCookedFields) must run "
        "the embedded live solver with this manifest's solver settings (notably roughness_scale "
        "and bed_slope_source_scale) and each band's manning_n, or the seeded window drifts off "
        "the cooked state.",
        "manning_n / effective_manning_n are recorded per band from each scenario's roughness; "
        "effective_manning_n = manning_n * roughness_scale is what the solver applied.",
        "Terrain is NRCan MRDEM-30 (~30 m ground sample); it cannot resolve the basalt canyon "
        "walls, rocks, constrictions, or wave trains. The bed is interpreted (MRDEM-30 valley "
        "frame + authored continuous-wave-train geometry), Lava Canyon's station is an adopted "
        "upper-canyon anchor, and the window is pending_human_review and not production_promoted; "
        "these cooked fields inherit that provenance and make no claim of numeric parity.",
        "Flow bands are an interpreted candidate from the 08MA002 lake-outlet gauge climatology, "
        "not gauge-routed reach discharge nor guide-approved.",
        "Convergence is recorded honestly per band against the pilot thresholds; the continuous "
        "wave train and constrictions keep feature-scale cells unsteady, so a band that does not "
        "meet the thresholds is recorded as converged=false rather than hidden.",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cpp-solver",
        type=Path,
        default=Path("cpp/build/raftsim_water_solver"),
        help="Path to the raftsim_water_solver CLI binary.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Committed cooked-fields package dir (default: scenario_lava_canyon/cooked_flow_fields).",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("outputs/chilko_lava_canyon_cooked_flow_fields"),
        help="Scratch directory for raw solver runs (gitignored).",
    )
    parser.add_argument("--steps", type=int, default=16000, help="Solver steps per band (fixed_dt is 0.05 s).")
    parser.add_argument("--frame-interval", type=int, default=200, help="Steps between convergence-monitor frames.")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[4]
    output_dir = args.output_dir or (repo_root / OUTPUT_DIR_RELATIVE)

    config = CookedFlowFieldsRunConfig(
        steps=args.steps,
        frame_interval=args.frame_interval,
        solver_mode="finite_volume",
        boundary_mode="scenario",
        flux_scheme="hll",
        spatial_order=2,
        feature_strength_scale=0.0,
        roughness_scale=1.0,
        bed_slope_source_scale=1.0,
        preserve_initial_mass=False,
        disable_fixture_calibrations=True,
        thresholds=ConvergenceThresholds(),
    )

    manifest_path = generate_authored_window_cooked_flow_fields(
        _lava_canyon_bands(repo_root),
        executable=args.cpp_solver,
        output_dir=output_dir,
        work_dir=args.work_dir,
        config=config,
        river_id=RIVER_ID,
        section_id=WINDOW_ID,
        source_package=str(SCENARIO_ROOT_RELATIVE),
        notes=_notes(),
        extra_top_level=_window_extra_top_level(repo_root),
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"manifest={manifest_path}")
    all_converged = True
    for band in manifest["bands"]:
        convergence = band["convergence"]
        final = convergence["final_window"]
        all_converged &= bool(convergence["converged"])
        print(
            f"band={band['band_id']} converged={convergence['converged']} "
            f"manning_n={band['manning_n']} "
            f"final_max_abs_dh_m={final['max_abs_dh_m']:.6f} "
            f"final_max_abs_du_m_per_s={final['max_abs_du_m_per_s']:.6f} "
            f"final_max_abs_dv_m_per_s={final['max_abs_dv_m_per_s']:.6f} "
            f"wet_fraction={band['field_stats']['wet_fraction']:.3f} "
            f"speed_max={band['field_stats']['speed_max_m_per_s']:.3f}"
        )
    return 0 if all_converged else 1


if __name__ == "__main__":
    raise SystemExit(main())
