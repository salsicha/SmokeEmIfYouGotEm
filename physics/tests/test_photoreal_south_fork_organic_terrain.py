from pathlib import Path
import hashlib
import json


REPO_ROOT = Path(__file__).resolve().parents[2]
ORGANIC_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorSouthForkMaterial.cpp"
)
LANDSCAPE_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorMaterialsBase.cpp"
)
FULL_REACH_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorPhotorealMaterials.cpp"
)
MANIFEST = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "landscape_candidate_manifest_american_south_fork.json"
)
REVIEW = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_south_fork_organic_foothill_terrain_v1_review.json"
)


def test_south_fork_organic_terrain_is_shared_and_shade_only():
    organic_source = ORGANIC_SOURCE.read_text(encoding="utf-8")
    landscape_source = LANDSCAPE_SOURCE.read_text(encoding="utf-8")
    full_reach_source = FULL_REACH_SOURCE.read_text(encoding="utf-8")

    assert "BuildSouthForkOrganicFoothillBaseColor" in organic_source
    assert "WorldPositionOffset" not in organic_source
    assert "Landscape->Import" not in organic_source
    assert "SetCollision" not in organic_source
    assert 'Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")' in (
        landscape_source
    )
    assert "BuildSouthForkOrganicFoothillBaseColor(\n            Material" in (
        landscape_source
    )
    assert "0.58f" in landscape_source
    assert "SlopeConditionedBaseColor->A.Expression = FinalBaseColor" in (
        landscape_source
    )
    assert "RaftSimEditorEnvironment::BuildSouthForkOrganicFoothillBaseColor" in (
        full_reach_source
    )
    assert "0.30f" in full_reach_source


def test_south_fork_organic_terrain_uses_incommensurate_world_scales():
    source = ORGANIC_SOURCE.read_text(encoding="utf-8")

    assert "Noise(0.00013f, 3)" in source
    assert "Noise(0.00073f, 3)" in source
    assert "Noise(0.00310f, 2)" in source
    assert "SouthForkOakLitterTint" in source
    assert "SouthForkDryGrassTint" in source
    assert "SouthForkGraniticSoilTint" in source
    assert "SouthForkWeatheredGraniteTint" in source
    assert "SouthForkWeatheredGraniteSlopeStart" in source
    assert "SouthForkWeatheredGraniteSlopeGain" in source


def test_south_fork_generated_manifest_records_lit_organic_authority():
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "american_south_fork"
    assert candidate["status"] == "captured_source_landscape_import_candidate"
    assert candidate["landscape_material_shading_model"] == "DefaultLit"
    assert candidate["landscape_material_organic_surface_status"].startswith(
        "south_fork_v1_three_scale_world_space"
    )
    assert candidate["landscape_material_organic_world_noise_scales_per_cm"] == [
        0.00013,
        0.00073,
        0.0031,
    ]
    assert candidate["landscape_material_geometry_authority_status"] == (
        "shade_only_no_world_position_offset_no_collision_or_solver_change"
    )


def test_south_fork_organic_terrain_assets_and_captures_exist():
    asset_paths = (
        "unreal/Content/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain.uasset",
        "unreal/Content/RaftSim/Materials/LandscapeCandidates/"
        "M_RaftSim_americansouthfork_physicalcorridor_SourceLandscapeCandidate.uasset",
    )
    for relative_path in asset_paths:
        assert (REPO_ROOT / relative_path).is_file()

    for capture_name in (
        "chili_bar_launch_downstream.png",
        "meat_grinder_guide_eye.png",
        "troublemaker_approach.png",
        "coloma_bridge_context.png",
        "salmon_falls_takeout.png",
    ):
        assert (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach"
            / capture_name
        ).is_file()


def test_south_fork_organic_terrain_review_is_hash_locked_and_fail_closed():
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["status"] == (
        "technical_candidate_retained_external_environment_art_geospatial_and_guide_"
        "review_open"
    )
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["promotion_allowed"] is False
    assert review["authority"]["terrain_geometry_changed"] is False
    assert review["authority"]["collision_changed"] is False
    assert review["authority"]["hydraulics_changed"] is False
    assert review["authority"]["navigation_changed"] is False
    assert len(review["photoreal_rejection_reasons"]) >= 5
    assert len(review["open_gates"]) >= 3

    for artifact in review["hash_locked_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
