import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FOLIAGE_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
    "RaftSimEditorLandscapeFoliage.cpp"
)
NATIVE_TEST_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Tests/"
    "RaftSimEditorPacuareTerrainTest.cpp"
)
REVIEW_PATH = REPO_ROOT / (
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "pacuare_canopy_morphology_v2_review.json"
)


def test_pacuare_v2_uses_compound_oriented_opaque_crownlets():
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    assert "AppendOrientedRainforestLobe" in source
    assert "AppendRainforestOpaqueCrownlet" in source
    assert "LeafClusterCount = 6" in source
    assert "ClusterRotation" in source
    assert "AppendRainforestOpaqueCrownlet(" in source
    assert "This is morphology-only presentation geometry" in source


def test_pacuare_v2_assets_replace_v1_in_the_runtime_generator():
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")
    native_test = NATIVE_TEST_SOURCE.read_text(encoding="utf-8")

    for asset_name in (
        "SM_RaftSim_Pacuare_CanopyTree_A_OpaqueV2",
        "SM_RaftSim_Pacuare_CanopyTree_B_OpaqueV2",
        "SM_RaftSim_Pacuare_RiparianShrub_A_OpaqueV2",
        "SM_RaftSim_Pacuare_RainforestGroundCover_A_OpaqueV2",
    ):
        assert asset_name in source
        assert asset_name in native_test
    assert "Mesh->GetNumVertices(0) > 1000" in native_test
    assert "Mesh->GetNumTriangles(0) > 1000" in native_test


def test_pacuare_v2_shadow_lift_is_bounded_to_rainforest_material():
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")
    pacuare_factory = source.split(
        "bool CreatePacuareOpaqueRainforestVegetationAssets", 1
    )[1].split("bool ValidateZambeziOpaqueVegetationMaterial", 1)[0]

    assert 'TEXT("Pacuare rainforest"),' in pacuare_factory
    assert "0.20f," in pacuare_factory
    assert "0.84f," in pacuare_factory
    assert "1.16f," in pacuare_factory
    assert "SetCollision" not in pacuare_factory
    assert "Landscape->Import" not in pacuare_factory
    assert "WorldPositionOffset" not in pacuare_factory


def test_pacuare_v2_review_is_fail_closed_and_hash_locked():
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))

    assert review["status"] == (
        "retained_canopy_breakup_improvement_photoreal_promotion_open"
    )
    assert review["passed"] is False
    decision = review["decision"]
    assert decision["reference_runnable"] is True
    assert decision["technical_candidate_passed"] is True
    assert decision["visual_crown_breakup_improved"] is True
    assert decision["photoreal_acceptance_passed"] is False
    for unchanged_contract in (
        "instance_placement_changed",
        "landscape_geometry_changed",
        "landscape_collision_changed",
        "water_geometry_changed",
        "cooked_fields_changed",
        "wet_dry_mask_changed",
        "bathymetry_changed",
        "hydraulics_changed",
        "raft_forces_changed",
    ):
        assert decision[unchanged_contract] is False

    runtime = review["runtime_contract"]
    assert runtime["opaque_mesh_family_count"] == 4
    assert runtime["source_skeletal_mesh_count"] == 0
    assert runtime["alpha_card_source_count"] == 0
    assert runtime["canopy_instance_count"] == 5993
    assert runtime["collision"] is False
    assert runtime["nanite"] is True
    assert runtime["leaf_cluster_count_per_former_lobe"] == 6
    assert runtime["canopy_tree_a_vertices"] > 10000
    assert runtime["canopy_tree_b_vertices"] > 10000

    for view in ("guide_seat", "river_eye"):
        metrics = review["matched_capture_metrics"][view]
        assert metrics["edge_fraction_after"] > metrics["edge_fraction_before"]
        assert metrics["near_black_fraction_after"] < metrics["near_black_fraction_before"]
        assert (
            metrics["gradient_orientation_entropy_after"]
            > metrics["gradient_orientation_entropy_before"]
        )
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file(), artifact["path"]
        if artifact.get("hash_locked", True):
            assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
