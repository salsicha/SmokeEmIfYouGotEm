from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_SOURCE = (
    REPO_ROOT / "physics/src/raftsim/south_fork_photoreal_environment.py"
)
EDITOR_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
    "RaftSimEditorSouthForkFullReach.cpp"
)
MANIFEST = (
    REPO_ROOT
    / "physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
    "photoreal_environment/manifest.json"
)
REVIEW = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_organic_horizon_v1/review.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_horizon_generation_is_nonrectilinear_and_non_authoritative() -> None:
    generator = GENERATOR_SOURCE.read_text(encoding="utf-8")
    editor = EDITOR_SOURCE.read_text(encoding="utf-8")

    for token in (
        "south_fork_photoreal_environment_v33_organic_horizon_termination",
        "FAR_FIELD_DOMAIN_PADDING_M = 2400.0",
        "FAR_FIELD_HORIZON_BOUNDARY_EROSION_MIN_M = 120.0",
        "FAR_FIELD_HORIZON_BOUNDARY_EROSION_MAX_M = 720.0",
        "FAR_FIELD_MACRO_SOURCE_DETAIL_AUTHORITY_MAX = 0.58",
        "_far_field_horizon_boundary_erosion_m",
        "procedural_infill_explicit",
        "not_for_navigation",
    ):
        assert token in generator
    assert "RaftSimRebuildSouthForkFarFieldMeshes" in editor
    assert "RaftSimRebuildSouthForkFarFieldMacroTextures" in editor
    assert "ECollisionEnabled::NoCollision" in editor


def test_generated_far_field_has_an_irregular_closed_outer_contour() -> None:
    manifest = load_json(MANIFEST)
    far_field = manifest["far_field"]
    topology = far_field["topology"]

    assert manifest["algorithm"] == (
        "south_fork_photoreal_environment_v33_organic_horizon_termination"
    )
    assert far_field["grid_size"] == [1673, 743]
    assert topology["procedural_domain_padding_m"] == 2400.0
    assert topology["organic_horizon_boundary_erosion_range_m"] == [120.0, 720.0]
    assert topology["organic_horizon_boundary_shape"] == (
        "deterministic_world_space_domain_warped_nonrectilinear_v1"
    )
    assert topology["macro_source_detail_authority_max"] == 0.58
    assert topology["not_for_navigation"] is True

    masks = [
        np.asarray(Image.open(REPO_ROOT / patch["corridor_exclusion_mask"]["path"]))
        for patch in far_field["patches"]
    ]
    tile_rows = []
    for row in range(2):
        tile_rows.append(
            np.concatenate(
                [
                    masks[row * 4 + column]
                    if column == 0
                    else masks[row * 4 + column][:, 1:]
                    for column in range(4)
                ],
                axis=1,
            )
        )
    global_mask = np.concatenate((tile_rows[0], tile_rows[1][1:]), axis=0)

    assert global_mask.shape == (743, 1673)
    assert np.all(global_mask[0] == 0)
    assert np.all(global_mask[-1] == 0)
    assert np.all(global_mask[:, 0] == 0)
    assert np.all(global_mask[:, -1] == 0)
    for oriented in (
        global_mask,
        global_mask[::-1],
        global_mask.T,
        global_mask[:, ::-1].T,
    ):
        visible = np.any(oriented > 0, axis=0)
        first_visible = np.argmax(oriented[:, visible] > 0, axis=0)
        assert np.unique(first_visible).size > 20


def test_review_hashes_shipping_captures_and_retains_external_gates() -> None:
    review = load_json(REVIEW)

    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["promotion_allowed"] is False
    assert review["review_decision"]["accepted"] is True
    assert review["review_decision"]["observed_rectangular_horizon_shelf"] is False
    assert review["metrics"]["far_field_vertices"] == 1118073
    assert review["metrics"]["far_field_triangles"] == 2218304
    assert review["verification"]["map_check"] == "0 errors, 0 warnings"
    assert len(review["objective_capture_comparison"]) == 5

    for comparison in review["objective_capture_comparison"]:
        baseline = comparison["baseline"]
        candidate = comparison["candidate"]
        assert sha256(REPO_ROOT / baseline["path"]) == baseline["sha256"]
        assert sha256(REPO_ROOT / candidate["path"]) == candidate["sha256"]
        canonical = (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach"
            / f"{comparison['capture']}.png"
        )
        assert sha256(canonical) == candidate["sha256"]
        assert comparison["technical_result"] == "pass"

    for artifact in review["hash_locked_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert sha256(path) == artifact["sha256"]

    expected_gates = {
        "whitewater_guide_review",
        "geospatial_and_terrain_review",
        "hydrology_and_hydraulics_review",
        "rights_and_attribution_review",
        "human_environment_art_review",
        "hazard_readability_review",
        "target_platform_performance_review",
    }
    assert {gate["gate"] for gate in review["open_gates"]} == expected_gates
    assert all(gate["status"] == "required_open" for gate in review["open_gates"])


def test_saved_map_contains_all_eight_far_field_and_dressing_actors() -> None:
    external_actor_root = (
        REPO_ROOT
        / "unreal/Content/__ExternalActors__/RaftSim/Maps/"
        "L_SouthForkAmerican_FullReach"
    )
    actor_packages = [
        path
        for path in external_actor_root.rglob("*.uasset")
        if b"RaftSim_SouthFork_FarField" in path.read_bytes()
    ]
    assert len(actor_packages) == 16

    mesh_root = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/SouthForkFullReach/FarField"
    )
    texture_root = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/SouthForkFullReach/Terrain/"
        "MacroTextures"
    )
    assert len(list(mesh_root.glob("SM_far_field_*.uasset"))) == 8
    assert len(list(texture_root.glob("T_RaftSim_far_field_*_MacroAlbedo.uasset"))) == 8
