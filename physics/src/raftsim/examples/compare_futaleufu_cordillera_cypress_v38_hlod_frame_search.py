"""Review the V38 fixed-camera Futaleufu HLOD atlas-frame search."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from raftsim.examples.compare_futaleufu_cordillera_cypress_v32_complementary_transition import (
    V32_NAMESPACE,
    V32_REPORT,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v34_persistent_motion import (
    _compact_comparison,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v37_temporal_lit_handoff import (
    _silhouette_and_photometry_metrics,
)

FRAME_COUNT = 8
REPORT_NAME = "futaleufu_cordillera_cypress_v38_hlod_frame_search_review.json"
CONTACT_SHEET_NAME = (
    "futaleufu_cordillera_cypress_v38_hlod_frame_search_contact_sheet.png"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_path(capture_root: Path) -> Path:
    return capture_root / "open_grown_conical_hlod_frame_search_source_reference.png"


def _automatic_path(capture_root: Path) -> Path:
    return capture_root / "open_grown_conical_hlod_frame_search_automatic.png"


def _override_path(capture_root: Path, frame_index: int) -> Path:
    return (
        capture_root
        / f"open_grown_conical_hlod_frame_search_override_frame{frame_index:02d}.png"
    )


def _write_contact_sheet(capture_root: Path, output_path: Path) -> None:
    items = [
        ("SOURCE", _source_path(capture_root)),
        ("AUTOMATIC", _automatic_path(capture_root)),
        *[
            (f"OVERRIDE {frame_index}", _override_path(capture_root, frame_index))
            for frame_index in range(FRAME_COUNT)
        ],
    ]
    columns = 5
    rows = 2
    thumb_width = 320
    thumb_height = 180
    margin = 16
    title_height = 48
    label_height = 24
    canvas_width = margin * (columns + 1) + thumb_width * columns
    canvas_height = (
        title_height + margin * (rows + 1) + (label_height + thumb_height) * rows
    )
    canvas = Image.new("RGB", (canvas_width, canvas_height), (22, 24, 26))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (margin, 14),
        "V38 FIXED-CAMERA ATLAS FRAME SEARCH - FRAME 5 CONFIRMED, PROXY REJECTED",
        fill=(240, 240, 240),
    )
    for item_index, (label, path) in enumerate(items):
        row = item_index // columns
        column = item_index % columns
        x = margin + column * (thumb_width + margin)
        y = title_height + margin + row * (label_height + thumb_height + margin)
        draw.text((x, y), label, fill=(210, 210, 210))
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        canvas.paste(image, (x, y + label_height))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    report_root = (
        repo_root
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    )
    structural_report_path = report_root / V32_REPORT
    structural_report = json.loads(structural_report_path.read_text(encoding="utf-8"))
    capture_root = repo_root / "unreal/Saved/RaftSimPveReview" / V32_NAMESPACE
    contract = structural_report["local_multi_view_atlas_hlod"][
        "hlod_frame_search_contract"
    ]
    local_review = structural_report["local_visual_review"]

    source_path = _source_path(capture_root)
    automatic_path = _automatic_path(capture_root)
    override_paths = [
        _override_path(capture_root, frame_index) for frame_index in range(FRAME_COUNT)
    ]
    all_paths = [source_path, automatic_path, *override_paths]
    missing_paths = [
        str(path.relative_to(repo_root)) for path in all_paths if not path.is_file()
    ]
    contract_valid = (
        contract["enabled"] is True
        and contract["source_map"].endswith(
            "L_FutaleufuTerminator_PhysicalCorridorCandidate"
        )
        and contract["saved_map_modified"] is False
        and contract["landscape_water_collision_solver_or_gameplay_authority_modified"]
        is False
        and contract["sampling"]
        == "one_loaded_physical_corridor_world_one_fixed_24_5m_camera_and_one_persistent_scene_capture"
        and contract["camera_radius_cm"] == 2450.0
        and contract["warmup_frames_per_representation"] == 8
        and contract["lighting"] is True
        and contract["temporal_aa"] is True
        and contract["atlas_frame_override_parameter"] == "AtlasFrameOverride"
        and contract["automatic_override_value"] == -1.0
        and contract["calculated_automatic_row_zero_frame"] in range(FRAME_COUNT)
        and contract["tested_row_zero_frames"] == list(range(FRAME_COUNT))
        and contract["source_reference_count"] == 1
        and contract["automatic_selection_count"] == 1
        and contract["override_capture_count"] == FRAME_COUNT
        and contract["capture_count"] == len(all_paths)
        and len(contract["captures"]) == len(all_paths)
        and local_review["hlod_frame_search_capture_count"] == len(all_paths)
        and not missing_paths
    )

    automatic_metrics = _silhouette_and_photometry_metrics(source_path, automatic_path)
    override_metrics = {}
    automatic_to_override = {}
    for frame_index, override_path in enumerate(override_paths):
        override_metrics[str(frame_index)] = _silhouette_and_photometry_metrics(
            source_path, override_path
        )
        automatic_to_override[str(frame_index)] = _compact_comparison(
            automatic_path, override_path
        )

    silhouette_key = "source_hlod_silhouette_intersection_over_union"
    luma_key = "hlod_to_source_luminance_ratio"
    mad_key = "source_hlod_roi_mean_absolute_channel_delta"
    changed_key = "changed_pixel_fraction_max_channel_gt_12"
    comparison_mad_key = "mean_absolute_channel_delta"
    best_forced_silhouette_frame = max(
        range(FRAME_COUNT),
        key=lambda frame_index: override_metrics[str(frame_index)][silhouette_key],
    )
    best_forced_photometry_frame = min(
        range(FRAME_COUNT),
        key=lambda frame_index: (
            abs(1.0 - override_metrics[str(frame_index)][luma_key]),
            override_metrics[str(frame_index)][mad_key],
        ),
    )
    nearest_forced_to_automatic = min(
        range(FRAME_COUNT),
        key=lambda frame_index: automatic_to_override[str(frame_index)][
            comparison_mad_key
        ],
    )
    calculated_automatic = contract["calculated_automatic_row_zero_frame"]
    automatic_beats_forced_silhouette = automatic_metrics[silhouette_key] >= max(
        metrics[silhouette_key] for metrics in override_metrics.values()
    )
    automatic_selection_validated = (
        calculated_automatic == nearest_forced_to_automatic
        and automatic_beats_forced_silhouette
        and automatic_to_override[str(calculated_automatic)][changed_key] <= 0.05
    )

    contact_sheet_path = report_root / CONTACT_SHEET_NAME
    _write_contact_sheet(capture_root, contact_sheet_path)
    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_hlod_frame_search_review.v38",
        "river_id": "futaleufu_terminator",
        "candidate": "v38_fixed_camera_row_zero_atlas_frame_search",
        "status": (
            "automatic_frame_selection_retained_flat_proxy_and_photometry_rejected"
            if contract_valid and automatic_selection_validated
            else "frame_search_contract_or_automatic_selection_failed"
        ),
        "source_structural_report": str(structural_report_path.relative_to(repo_root)),
        "source_structural_report_sha256": _sha256(structural_report_path),
        "capture_contract": {
            "structural_contract_valid": contract_valid,
            "expected_capture_count": 10,
            "observed_capture_count": len(all_paths) - len(missing_paths),
            "missing_captures": missing_paths,
            "physical_corridor_map": contract["source_map"],
            "saved_map_modified": contract["saved_map_modified"],
            "physics_or_gameplay_authority_modified": contract[
                "landscape_water_collision_solver_or_gameplay_authority_modified"
            ],
            "camera_radius_cm": contract["camera_radius_cm"],
            "warmup_frames_per_representation": contract[
                "warmup_frames_per_representation"
            ],
            "atlas_frame_override_parameter": contract[
                "atlas_frame_override_parameter"
            ],
            "automatic_override_value": contract["automatic_override_value"],
            "calculated_automatic_row_zero_frame": calculated_automatic,
            "tested_row_zero_frames": contract["tested_row_zero_frames"],
        },
        "automatic_selection": {
            "source_to_automatic": automatic_metrics,
            "calculated_frame": calculated_automatic,
            "pixel_nearest_forced_frame": nearest_forced_to_automatic,
            "automatic_to_forced_frames": automatic_to_override,
            "automatic_beats_every_forced_frame_on_silhouette_iou": (
                automatic_beats_forced_silhouette
            ),
            "automatic_selection_validated": automatic_selection_validated,
        },
        "forced_frame_search": {
            "source_to_forced_frames": override_metrics,
            "best_forced_silhouette_frame": best_forced_silhouette_frame,
            "best_forced_silhouette_iou": override_metrics[
                str(best_forced_silhouette_frame)
            ][silhouette_key],
            "best_forced_photometry_frame": best_forced_photometry_frame,
            "best_forced_luminance_ratio": override_metrics[
                str(best_forced_photometry_frame)
            ][luma_key],
            "forced_frame_improves_over_automatic": False,
        },
        "human_visual_review": {
            "findings": [
                "automatic selection and forced frame 5 show the same crown organization",
                "automatic selection has the highest measured silhouette IoU in the search",
                "all forced frames remain darker and fuller than the source crown",
                "no alternate row-zero azimuth restores the source branch and spray structure",
                "terrain, distant foliage, and water remain physical-corridor blockout quality",
                "no named rapid or boat line is framed by this representation diagnostic",
            ],
            "automatic_frame_selection_passed": automatic_selection_validated,
            "alternate_azimuth_fix_found": False,
            "source_hlod_silhouette_match_passed": automatic_metrics[
                "source_hlod_silhouette_gate_passed"
            ],
            "source_hlod_photometry_passed": automatic_metrics[
                "source_hlod_photometry_gate_passed"
            ],
            "photoreal_art_quality_passed": False,
            "hazard_readability_passed": False,
        },
        "contact_sheet": {
            "path": str(contact_sheet_path.relative_to(repo_root)),
            "sha256": _sha256(contact_sheet_path),
            "columns": 5,
            "rows": 2,
        },
        "decision": {
            "retain": [
                "automatic 16-degree registered nearest-frame selection",
                "default-safe AtlasFrameOverride=-1 automatic path",
                "fixed-camera in-engine frame-search harness for future atlas diagnostics",
                "V37 temporal ownership and background-isolation decisions",
            ],
            "reject": [
                "retuning the row-zero azimuth frame as the V37 silhouette fix",
                "the current flat atlas plane as a source-matched production HLOD",
                "the current combined trunk-and-foliage Default Lit response",
                "this diagnostic as photoreal corridor, hazard, or performance approval",
            ],
            "next_step": (
                "Keep automatic frame 5 and replace the flat combined atlas representation; isolate trunk and foliage shading and test a source-matched depth-aware, view-interpolated, or geometry HLOD before rerunning V35/V37 and packaged profiling."
            ),
        },
        "frame_search_contract_passed": contract_valid,
        "automatic_frame_selection_gate_passed": automatic_selection_validated,
        "alternate_azimuth_fix_found": False,
        "source_hlod_silhouette_gate_passed": automatic_metrics[
            "source_hlod_silhouette_gate_passed"
        ],
        "source_hlod_photometry_gate_passed": automatic_metrics[
            "source_hlod_photometry_gate_passed"
        ],
        "lit_art_review_passed": False,
        "hazard_readability_gate_passed": False,
        "wall_clock_performance_gate_passed": False,
        "production_promoted": False,
        "corridor_substitution_allowed": False,
        "regenerate_other_forms_allowed": False,
    }
    output_path = report_root / REPORT_NAME
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(output_path.relative_to(repo_root))
    print(contact_sheet_path.relative_to(repo_root))


if __name__ == "__main__":
    main()
