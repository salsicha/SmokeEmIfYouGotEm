from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR_ROOT = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
MATERIAL_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorChilkoMaterial.cpp"
BASE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorMaterialsBase.cpp"
MANIFEST = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "landscape_candidate_manifest_chilko_river_lava_canyon.json"
)
REVIEW = MANIFEST.with_name("chilko_lava_canyon_organic_lit_terrain_v1_review.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_chilko_organic_material_is_default_lit_and_non_displacing() -> None:
    material_source = MATERIAL_SOURCE.read_text(encoding="utf-8")
    base_source = BASE_SOURCE.read_text(encoding="utf-8")

    assert "BuildChilkoOrganicLavaCanyonBaseColor" in material_source
    assert base_source.count("BuildChilkoOrganicLavaCanyonBaseColor") == 1
    assert 'Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon")' in (
        base_source
    )
    assert "bUsesDefaultLitLandscape ? MSM_DefaultLit : MSM_Unlit" in base_source
    assert "WorldPositionOffset" not in material_source
    assert "Landscape->Import" not in material_source
    assert "SetCollision" not in material_source


def test_chilko_organic_material_has_four_incommensurate_world_scales() -> None:
    source = MATERIAL_SOURCE.read_text(encoding="utf-8")

    assert "Noise(0.00016f, 3)" in source
    assert "Noise(0.00059f, 3)" in source
    assert "Noise(0.00270f, 2)" in source
    assert "Noise(0.00790f, 2)" in source
    assert "ChilkoOpenBenchPaletteWeight" in source
    assert "ChilkoBasaltSlopeStart" in source
    assert "ChilkoBasaltSlopeGain" in source
    assert "ChilkoMineralSoilTint" in source
    assert "ChilkoDryGrassTint" in source
    assert "ChilkoWetBasaltTint" in source
    assert "ChilkoOxidizedBasaltTint" in source
    assert "ChilkoScreeTint" in source


def test_chilko_generated_manifest_records_shading_and_authority_separation() -> None:
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "chilko_river_lava_canyon"
    assert candidate["landscape_material_shading_model"] == "DefaultLit"
    assert candidate["landscape_material_organic_surface_status"].startswith(
        "chilko_v1_four_scale_world_space"
    )
    assert candidate["landscape_material_organic_world_noise_scales_per_cm"] == [
        0.00016,
        0.00059,
        0.0027,
        0.0079,
    ]
    assert candidate["landscape_material_geometry_authority_status"] == (
        "shade_only_no_world_position_offset_no_collision_or_solver_change"
    )
    assert candidate["landscape_material_promotion_status"] == (
        "review_only_not_lifelike_not_gameplay_promoted"
    )


def test_chilko_organic_terrain_review_retains_immutable_evidence_and_is_honest() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.chilko_lava_canyon_organic_lit_terrain_review.v1"
    )
    assert review["status"] == (
        "technical_candidate_retained_photoreal_and_external_review_open"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["terrain_geometry_changed"] is False
    assert review["decision"]["terrain_collision_changed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["decision"]["raft_forces_changed"] is False
    assert review["material"]["world_position_offset_connected"] is False
    assert review["material"]["organic_world_noise_scales_per_cm"] == [
        0.00016,
        0.00059,
        0.0027,
        0.0079,
    ]
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 6

    # The native-water milestone supersedes the mutable map, manifest, current
    # captures, and shared generator wiring. Its own review locks their current
    # hashes; this historical terrain review continues to lock the immutable
    # before frames, audit reports, terrain material, and terrain-only source.
    superseded_paths = {
        "unreal/Content/RaftSim/Maps/L_LavaCanyon.umap",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/landscape_candidate_manifest_chilko_river_lava_canyon.json",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_river_lava_canyon_guide_seat_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_river_lava_canyon_river_eye_downstream.png",
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_river_lava_canyon_solver_rapid_river_eye_downstream.png",
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorMaterialsBase.cpp",
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Commands/RaftSimEditorEnvironmentAutomation.cpp",
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorEnvironmentInternal.h",
        "unreal/Content/RaftSim/Materials/LandscapeCandidates/M_RaftSim_chilkoriverlavacanyon_physicalcorridor_SourceLandscapeCandidate.uasset",
    }
    for artifact in review["retained_artifacts"]:
        if artifact["path"] in superseded_paths:
            continue
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
