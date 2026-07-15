"""Review the V35 8x8 handoff in its V36 lit Futaleufu river view."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from raftsim.examples.compare_futaleufu_cordillera_cypress_v20_1_dense_sprays import (
    _comparison,
)
from raftsim.examples.compare_futaleufu_cordillera_cypress_v32_complementary_transition import (
    V32_NAMESPACE,
    V32_REPORT,
)

AUTHORITIES = ("source_only", "hlod_only", "combined")
SAVED_FRAME_COUNT = 49
SELECTED_FRAMES = (0, 15, 30, 40, 48)
REPORT_NAME = "futaleufu_cordillera_cypress_v36_lit_river_view_review.json"
CONTACT_SHEET_NAME = "futaleufu_cordillera_cypress_v36_lit_river_view_contact_sheet.png"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _capture_name(frame_index: int, authority: str) -> str:
    if frame_index < 41:
        radius_cm = 2300 + frame_index * 10
        distance = f"{radius_cm // 100:02d}m{radius_cm % 100:02d}"
        return (
            "open_grown_conical_motion_8x8_lit_river_view_"
            f"f{frame_index:03d}_{distance}_{authority}.png"
        )
    settle_index = frame_index - 40
    return (
        "open_grown_conical_motion_8x8_lit_river_view_"
        f"f{frame_index:03d}_settle{settle_index:02d}_27m00_{authority}.png"
    )


def _mean_absolute_delta(before: np.ndarray, after: np.ndarray) -> float:
    return float(np.abs(before.astype(np.int16) - after.astype(np.int16)).mean())


def _phase_ownership_metrics(
    source_path: Path,
    hlod_path: Path,
    combined_path: Path,
) -> dict:
    source = np.asarray(Image.open(source_path).convert("RGB"), dtype=np.int16)
    hlod = np.asarray(Image.open(hlod_path).convert("RGB"), dtype=np.int16)
    combined = np.asarray(Image.open(combined_path).convert("RGB"), dtype=np.int16)

    # The fixed ROI encloses the reviewed crown without relying on a color key.
    x_min, y_min, x_max, y_max = 280, 0, 1000, 540
    source = source[y_min:y_max, x_min:x_max]
    hlod = hlod[y_min:y_max, x_min:x_max]
    combined = combined[y_min:y_max, x_min:x_max]
    source_distance = np.abs(combined - source).mean(axis=2)
    hlod_distance = np.abs(combined - hlod).mean(axis=2)
    valid = np.abs(source - hlod).max(axis=2) > 24
    source_owned = source_distance < hlod_distance

    phase_source_fractions: list[list[float | None]] = []
    populated_fractions: list[float] = []
    for phase_y in range(8):
        row: list[float | None] = []
        for phase_x in range(8):
            phase_valid = valid[phase_y::8, phase_x::8]
            phase_owned = source_owned[phase_y::8, phase_x::8]
            if phase_valid.any():
                value = float(phase_owned[phase_valid].mean())
                populated_fractions.append(value)
                row.append(value)
            else:
                row.append(None)
        phase_source_fractions.append(row)

    phase_contrast = max(populated_fractions) - min(populated_fractions)
    return {
        "frame": 15,
        "distance_m": 24.5,
        "roi_xyxy": [x_min, y_min, x_max, y_max],
        "classification": (
            "pixels whose source/HLOD maximum-channel delta exceeds 24 are assigned "
            "to the closer authority image, then grouped by 8x8 screen phase"
        ),
        "valid_pixel_fraction": float(valid.mean()),
        "observed_source_owned_fraction": float(source_owned[valid].mean()),
        "phase_source_owned_fractions": phase_source_fractions,
        "phase_source_fraction_range": [
            min(populated_fractions),
            max(populated_fractions),
        ],
        "phase_contrast": phase_contrast,
        "maximum_acceptable_phase_contrast": 0.20,
        "visible_periodic_pattern_gate_passed": phase_contrast <= 0.20,
    }


def _background_stability_metrics(source_path: Path, hlod_path: Path) -> dict:
    source = np.asarray(Image.open(source_path).convert("RGB"), dtype=np.uint8)
    hlod = np.asarray(Image.open(hlod_path).convert("RGB"), dtype=np.uint8)
    regions = {
        "left_terrain": (0, 250, 280, 450),
        "foreground_water": (0, 540, 1280, 700),
    }
    region_metrics = {}
    for name, (x_min, y_min, x_max, y_max) in regions.items():
        region_metrics[name] = {
            "roi_xyxy": [x_min, y_min, x_max, y_max],
            "source_to_hlod_mean_absolute_channel_delta": _mean_absolute_delta(
                source[y_min:y_max, x_min:x_max],
                hlod[y_min:y_max, x_min:x_max],
            ),
        }
    maximum_delta = max(
        metric["source_to_hlod_mean_absolute_channel_delta"]
        for metric in region_metrics.values()
    )
    return {
        "frame": 15,
        "regions": region_metrics,
        "maximum_mean_absolute_channel_delta": maximum_delta,
        "maximum_acceptable_mean_absolute_channel_delta": 4.0,
        "authority_background_stability_gate_passed": maximum_delta <= 4.0,
    }


def _write_contact_sheet(capture_root: Path, output_path: Path) -> None:
    thumb_width = 400
    thumb_height = 225
    margin = 16
    title_height = 48
    header_height = 28
    row_label_width = 92
    canvas_width = row_label_width + margin * 4 + thumb_width * 3
    canvas_height = (
        title_height + header_height + margin * 6 + thumb_height * len(SELECTED_FRAMES)
    )
    canvas = Image.new("RGB", (canvas_width, canvas_height), (22, 24, 26))
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (margin, 14),
        "V36 LIT RIVER-VIEW HANDOFF - ART REJECTED",
        fill=(240, 240, 240),
    )
    for column, authority in enumerate(AUTHORITIES):
        x = row_label_width + margin * (column + 1) + thumb_width * column
        draw.text(
            (x, title_height), authority.replace("_", " ").upper(), fill=(210, 210, 210)
        )

    top = title_height + header_height + margin
    for row, frame_index in enumerate(SELECTED_FRAMES):
        y = top + row * (thumb_height + margin)
        label = f"f{frame_index:03d}"
        if frame_index == 15:
            label += "\n24.5 m"
        elif frame_index == 48:
            label += "\nsettled"
        draw.multiline_text((margin, y + 8), label, fill=(210, 210, 210), spacing=4)
        for column, authority in enumerate(AUTHORITIES):
            image = Image.open(
                capture_root / _capture_name(frame_index, authority)
            ).convert("RGB")
            image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            x = row_label_width + margin * (column + 1) + thumb_width * column
            canvas.paste(image, (x, y))
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
        "lit_river_view_motion_sequence_contract"
    ]
    local_review = structural_report["local_visual_review"]

    all_paths = [
        capture_root / _capture_name(frame_index, authority)
        for authority in AUTHORITIES
        for frame_index in range(SAVED_FRAME_COUNT)
    ]
    missing_paths = [
        str(path.relative_to(repo_root)) for path in all_paths if not path.is_file()
    ]
    contract_valid = (
        contract["enabled"] is True
        and contract["source_map"]
        == "/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/"
        "L_FutaleufuTerminator_PhysicalCorridorCandidate"
        and contract["saved_map_modified"] is False
        and contract["landscape_water_collision_solver_or_gameplay_authority_modified"]
        is False
        and contract["sampling"]
        == "one_loaded_physical_corridor_world_and_one_persistent_scene_capture_per_authority_mode"
        and contract["pattern"] == "deterministic_8x8_screen_bayer"
        and contract["pattern_rank_count"] == 64
        and contract["authority_modes"] == list(AUTHORITIES)
        and contract["radial_band_cm"] == [2300.0, 2700.0]
        and contract["camera_step_cm"] == 10.0
        and contract["persistent_view_state"] is True
        and contract["temporal_history"] is True
        and contract["anti_aliasing_method"] == "temporal_aa"
        and contract["lighting"] is True
        and contract["atmosphere"] is True
        and contract["fog"] is True
        and contract["ambient_occlusion"] is True
        and contract["global_illumination"] is True
        and contract["lumen_gi"] is True
        and contract["lumen_reflections"] is True
        and contract["capture_count"] == 147
        and len(contract["captures"]) == 147
        and local_review["lit_river_view_motion_transition_capture_count"] == 147
        and not missing_paths
    )

    selected_frame_relationships = {}
    for frame_index in SELECTED_FRAMES:
        paths = {
            authority: capture_root / _capture_name(frame_index, authority)
            for authority in AUTHORITIES
        }
        selected_frame_relationships[str(frame_index)] = {
            "source_to_hlod": _comparison(paths["source_only"], paths["hlod_only"]),
            "combined_to_source": _comparison(paths["combined"], paths["source_only"]),
            "combined_to_hlod": _comparison(paths["combined"], paths["hlod_only"]),
        }

    midpoint_paths = {
        authority: capture_root / _capture_name(15, authority)
        for authority in AUTHORITIES
    }
    pattern_metrics = _phase_ownership_metrics(
        midpoint_paths["source_only"],
        midpoint_paths["hlod_only"],
        midpoint_paths["combined"],
    )
    background_metrics = _background_stability_metrics(
        midpoint_paths["source_only"], midpoint_paths["hlod_only"]
    )
    contact_sheet_path = report_root / CONTACT_SHEET_NAME
    _write_contact_sheet(capture_root, contact_sheet_path)

    output = {
        "schema": "raftsim.unreal.futaleufu_cypress_lit_river_view_review.v36",
        "river_id": "futaleufu_terminator",
        "candidate": "v35_8x8_handoff_in_v36_lit_physical_corridor_capture",
        "status": (
            "lit_river_view_captured_art_rejected_visible_periodic_pattern_"
            "hlod_photometry_and_background_instability"
        ),
        "source_structural_report": str(structural_report_path.relative_to(repo_root)),
        "source_structural_report_sha256": _sha256(structural_report_path),
        "capture_contract": {
            "structural_contract_valid": contract_valid,
            "expected_capture_count": 147,
            "observed_capture_count": len(all_paths) - len(missing_paths),
            "missing_captures": missing_paths,
            "physical_corridor_map": contract["source_map"],
            "saved_map_modified": contract["saved_map_modified"],
            "physics_or_gameplay_authority_modified": contract[
                "landscape_water_collision_solver_or_gameplay_authority_modified"
            ],
            "fixed_delta_is_wall_clock_performance_evidence": False,
        },
        "selected_frame_relationships": selected_frame_relationships,
        "visible_pattern_review": pattern_metrics,
        "authority_background_stability": background_metrics,
        "human_visual_review": {
            "reviewed_frames": [0, 15, 30, 40, 48],
            "reviewed_authorities": list(AUTHORITIES),
            "findings": [
                "the combined midpoint exposes the fixed 8x8 ownership pattern across crown and trunk",
                "the HLOD is a flat peach/green emissive representation that does not share the source tree's lit material response",
                "source and HLOD silhouettes diverge across the crown, branch tips, and trunk",
                "authority-only frames do not preserve the terrain and water background response",
                "terrain, distant foliage, and water remain physical-corridor blockout quality rather than photoreal",
                "no named rapid, boat line, hole, wave, or other hazard is present in the reviewed framing",
            ],
            "visible_mask_patterning_passed": False,
            "source_hlod_silhouette_match_passed": False,
            "source_hlod_lit_material_response_passed": False,
            "photoreal_art_quality_passed": False,
            "hazard_readability": "not_assessable_no_named_hazard_in_frame",
            "hazard_readability_passed": False,
        },
        "contact_sheet": {
            "path": str(contact_sheet_path.relative_to(repo_root)),
            "sha256": _sha256(contact_sheet_path),
            "selected_frames": list(SELECTED_FRAMES),
            "authority_columns": list(AUTHORITIES),
        },
        "decision": {
            "retain": [
                "V34/V35 isolated persistent-motion harness as a temporal regression guard",
                "physical-corridor lit capture path as the required art-review context",
                "transient non-colliding review setup and unchanged saved-map authority boundary",
            ],
            "reject": [
                "fixed 8x8 screen-space ownership as a production lit handoff",
                "the unlit emissive HLOD proxy as a production foliage representation",
                "this sequence as evidence of hazard readability or photoreal corridor quality",
                "fixed 60 Hz simulation delta as packaged desktop or target-VR performance proof",
            ],
            "next_step": (
                "Replace the visibly periodic screen mask and rebuild the HLOD with a lit, "
                "source-matched material and silhouette; rerun this gate before packaged "
                "performance, corridor substitution, or regeneration of the other seven forms."
            ),
        },
        "lit_capture_contract_passed": contract_valid,
        "visible_patterning_gate_passed": False,
        "source_hlod_silhouette_gate_passed": False,
        "source_hlod_photometry_gate_passed": False,
        "authority_background_stability_gate_passed": background_metrics[
            "authority_background_stability_gate_passed"
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
