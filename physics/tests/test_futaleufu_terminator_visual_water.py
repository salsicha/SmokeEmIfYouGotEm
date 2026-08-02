from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from raftsim.futaleufu_terminator_visual_water import (
    FLOW_BAND,
    PACKED_TEXTURE_RELATIVE,
    SCHEMA,
    build_futaleufu_terminator_visual_water,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_RELATIVE = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_terminator_reach_local_runnable_v1_review.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_build_futaleufu_terminator_visual_water() -> None:
    manifest = build_futaleufu_terminator_visual_water(REPO_ROOT)

    assert manifest["schema"] == SCHEMA
    assert manifest["flow_band"] == FLOW_BAND
    assert manifest["solver_evidence"]["solver"] == "raftsim_water_cpp_v1"
    assert manifest["solver_evidence"]["feature_strength_scale"] == 0.0
    assert manifest["solver_evidence"]["converged"] is False
    assert manifest["hydraulic_visualization_evidence"]["wet_cell_count"] > 8000
    assert manifest["hydraulic_visualization_evidence"][
        "supercritical_cell_count"
    ] > 400
    assert manifest["hydraulic_visualization_evidence"][
        "foam_eligible_cell_count"
    ] > 800
    assert manifest["render_binding"]["map"] == "/Game/RaftSim/Maps/L_Terminator"
    assert manifest["render_binding"]["capture_only"] is True
    assert manifest["authority_policy"]["changes_solver_state"] is False

    image = Image.open(REPO_ROOT / PACKED_TEXTURE_RELATIVE)
    assert image.mode == "RGBA"
    assert image.size == (1024, 256)


def test_terminator_runnable_review_is_hash_locked_and_honest() -> None:
    review = json.loads((REPO_ROOT / REVIEW_RELATIVE).read_text(encoding="utf-8"))

    assert review["status"] == (
        "accepted_reference_runnable_photoreal_promotion_rejected"
    )
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["production_promoted"] is False
    assert review["decision"]["live_solver_owns_gameplay_rendering_and_forces"]
    assert review["decision"]["authored_capture_water_hidden_in_game"]
    assert review["coordinate_contract"][
        "maximum_static_to_runtime_centerline_surface_error_m"
    ] == 0.0
    assert review["terrain_authority"]["surveyed_terminator_bathymetry"] is False
    assert review["cooked_field_evidence"]["converged"] is False
    assert review["interpreted_contact_geometry"]["count"] == 1
    assert len(review["required_external_acceptance_gates"]) == 6
    assert len(review["remaining_photoreal_defects"]) >= 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
