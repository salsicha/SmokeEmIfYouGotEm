# ruff: noqa: F405

from photoreal_test_support import *  # noqa: F401,F403
from _capture_evidence import assert_capture_recorded


def test_rights_reviewed_fir_import_is_hashed_isolated_and_visually_rejected():
    script = REVIEWED_BIOME_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    source_manifest = json.loads(
        REVIEWED_FIR_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    import_report = json.loads(
        REVIEWED_FIR_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )
    visual_review = json.loads(
        REVIEWED_FIR_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )

    assert "RAFTSIM_REVIEWED_BIOME_SOURCE_ROOT" in script
    assert "Hash mismatch" in script
    assert "transform_vertex_to_absolute = False" in script
    assert "bake_pivot_in_vertex = True" in script
    assert "StaticMeshEditorSubsystem" in script
    assert "SAMPLERTYPE_NORMAL" in script
    assert "SAMPLERTYPE_MASKS" in script
    assert "MSM_TWO_SIDED_FOLIAGE" in script
    assert "production_promoted" in script

    assert (
        source_manifest["status"]
        == "rights_reviewed_source_bundle_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert source_manifest["source"]["license"] == "CC0 1.0 Universal"
    assert (
        source_manifest["source"]["acquisition_method"]
        == "manual download from the asset website"
    )
    assert source_manifest["source"]["public_api_used"] is False
    assert source_manifest["source"]["source_bundle_committed"] is False
    assert len(source_manifest["expected_source_files"]) == 9
    assert source_manifest["import"]["destination"].startswith(
        "/Game/RaftSim/Environment/ExternalReview/"
    )

    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 9
    assert len(import_report["meshes"]) == 3
    assert len(import_report["textures"]) == 8
    assert len(import_report["materials"]) == 2
    assert "_a_LOD0" in import_report["selection_for_first_visual_review"]
    for mesh in import_report["meshes"]:
        assert (
            mesh["source_triangle_count_lod0"]
            > mesh["nanite_fallback_triangle_count_lod0"]
        )
        assert mesh["instance_pivot"]["centered_for_instancing"] is True
        assert mesh["physical_scale"]["plausible_tree_height"] is True
        assert mesh["physical_scale"]["lod0_build_scale"] == [100.0, 100.0, 100.0]
        assert mesh["nanite_enabled"] is True
        package_path = mesh["asset_path"].split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()

    assert visual_review["status"] == (
        "rights_clear_import_validated_visual_comparison_rejected_not_lifelike"
    )
    assert visual_review["production_promoted"] is False
    assert visual_review["decision"] == (
        "retain_import_pipeline_and_isolated_assets_reject_visual_promotion"
    )
    assert len(visual_review["visual_findings"]) == 4
    assert len(visual_review["next_asset_requirements"]) == 5
    for capture_key, hash_key in (
        ("river_eye_capture", "river_eye_sha256"),
        ("solver_rapid_river_eye_capture", "solver_rapid_river_eye_sha256"),
    ):
        capture = REPO_ROOT / visual_review["reviewed_candidate"][capture_key]
        assert_capture_recorded(capture)
        if capture.exists():
            assert _sha256(capture) == visual_review["reviewed_candidate"][hash_key]


def test_rights_reviewed_broadleaf_import_is_physical_isolated_and_visually_rejected():
    script = REVIEWED_BROADLEAF_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    source_manifest = json.loads(
        REVIEWED_BROADLEAF_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    import_report = json.loads(
        REVIEWED_BROADLEAF_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )
    visual_review = json.loads(
        REVIEWED_BROADLEAF_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )

    assert "RAFTSIM_REVIEWED_BROADLEAF_SOURCE_ROOT" in script
    assert "Hash mismatch" in script
    assert "transform_vertex_to_absolute = False" in script
    assert "bake_pivot_in_vertex = True" in script
    assert "MSM_TWO_SIDED_FOLIAGE" in script
    assert "PRESERVE_AREA" in script
    assert "pivot_within_footprint" in script
    assert "pivot_meets_ground" in script

    assert (
        source_manifest["status"]
        == "rights_reviewed_source_bundle_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert source_manifest["source"]["license"] == "CC0 1.0 Universal"
    assert source_manifest["source"]["public_api_used"] is False
    assert source_manifest["source"]["source_bundle_committed"] is False
    assert source_manifest["review_boundaries"][
        "south_fork_exact_species_approval"
    ] == ("not_approved_use_as_visual_structure_analog_only")
    assert len(source_manifest["expected_source_files"]) == 11

    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 11
    assert len(import_report["textures"]) == 10
    assert len(import_report["materials"]) == 3
    mesh = import_report["mesh"]
    assert mesh["source_triangle_count_lod0"] is None
    assert mesh["source_triangle_count_status"] == (
        "not_recomputed_from_existing_nanite_asset"
    )
    assert mesh["publisher_reported_triangle_count_label"] == "5M"
    assert mesh["nanite_fallback_triangle_count_lod0"] > 0
    assert 350.0 <= mesh["effective_height_cm"] <= 700.0
    assert mesh["plausible_tree_height"] is True
    assert mesh["pivot_within_footprint"] is True
    assert mesh["pivot_meets_ground"] is True
    assert mesh["valid_for_instancing"] is True
    assert mesh["lod0_build_scale"] == [100.0, 100.0, 100.0]
    assert mesh["nanite_enabled"] is True
    assert "PRESERVE_AREA" in mesh["nanite_shape_preservation"]
    assert {slot["role"] for slot in mesh["material_slots"]} == {
        "branches",
        "leaves",
        "trunk",
    }
    package_path = mesh["asset_path"].split(".", 1)[0]
    assert (
        REPO_ROOT / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
    ).is_file()

    assert visual_review["status"] == (
        "rights_clear_import_validated_visual_comparison_rejected_not_lifelike"
    )
    assert visual_review["production_promoted"] is False
    assert visual_review["decision"] == (
        "retain_import_pipeline_and_isolated_assets_reject_visual_promotion"
    )
    assert len(visual_review["visual_findings"]) == 4
    assert len(visual_review["next_asset_requirements"]) == 5
    for capture_key, hash_key in (
        ("guide_seat_capture", "guide_seat_sha256"),
        ("river_eye_capture", "river_eye_sha256"),
        ("solver_rapid_river_eye_capture", "solver_rapid_river_eye_sha256"),
    ):
        capture = REPO_ROOT / visual_review["reviewed_candidate"][capture_key]
        assert_capture_recorded(capture)
        if capture.exists():
            assert _sha256(capture) == visual_review["reviewed_candidate"][hash_key]


def test_rights_reviewed_rock_set_is_hashed_physical_and_isolated():
    script = REVIEWED_ROCK_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    source_manifest = json.loads(
        REVIEWED_ROCK_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    import_report = json.loads(
        REVIEWED_ROCK_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )

    assert "RAFTSIM_REVIEWED_ROCK_SOURCE_ROOT" in script
    assert "Hash mismatch" in script
    assert "combine_meshes = False" in script
    assert "flip_green_channel" in script
    assert "StaticMeshEditorSubsystem" in script
    assert "production_promoted" in script

    assert (
        source_manifest["status"]
        == "rights_reviewed_source_bundle_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert source_manifest["source"]["license"] == "CC0 1.0 Universal"
    assert source_manifest["source"]["public_api_used"] is False
    assert source_manifest["source"]["source_bundle_committed"] is False
    assert len(source_manifest["expected_source_files"]) == 4
    assert source_manifest["import"]["destination"].startswith(
        "/Game/RaftSim/Environment/ExternalReview/"
    )

    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 4
    assert len(import_report["meshes"]) == 6
    assert len(import_report["textures"]) == 3
    assert len(import_report["materials"]) == 1
    for mesh in import_report["meshes"]:
        assert 15.0 <= max(mesh["dimensions_cm"]) <= 500.0
        assert mesh["nanite_enabled"] is True
        assert mesh["material_slot_count"] >= 1
        assert mesh["material"].endswith(
            "M_RockMossSet01_ReviewLit.M_RockMossSet01_ReviewLit"
        )
        package_path = mesh["asset_path"].split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()


def test_rights_reviewed_jacaranda_import_is_isolated_and_visually_rejected():
    script = REVIEWED_JACARANDA_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    source_manifest = json.loads(
        REVIEWED_JACARANDA_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    import_report = json.loads(
        REVIEWED_JACARANDA_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )
    visual_review = json.loads(
        REVIEWED_JACARANDA_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")
    active_manifest = LANDSCAPE_CANDIDATE_MANIFEST_PATH.read_text(encoding="utf-8")

    assert "RAFTSIM_REVIEWED_JACARANDA_SOURCE_ROOT" in script
    assert "Hash mismatch" in script
    assert "flip_green_channel" in script
    assert "PRESERVE_AREA" in script
    assert "production_promoted" in script

    assert (
        source_manifest["status"]
        == "rights_reviewed_source_bundle_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert source_manifest["source"]["license"] == "CC0 1.0 Universal"
    assert source_manifest["source"]["public_api_used"] is False
    assert source_manifest["source"]["source_bundle_committed"] is False
    assert len(source_manifest["expected_source_files"]) == 11
    assert source_manifest["review_boundaries"]["batoka_species_approval"].startswith(
        "not_reviewed_structure_analog_only"
    )

    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 11
    assert len(import_report["textures"]) == 10
    assert len(import_report["materials"]) == 3
    mesh = import_report["mesh"]
    assert mesh["source_triangle_count_lod0"] == 3133049
    assert mesh["publisher_reported_triangle_count_label"] == "312K"
    assert (
        mesh["source_triangle_count_lod0"] > mesh["nanite_fallback_triangle_count_lod0"]
    )
    assert mesh["pivot_within_footprint"] is True
    assert mesh["pivot_meets_ground"] is True
    assert mesh["valid_for_instancing"] is True
    assert mesh["nanite_enabled"] is True
    assert "PRESERVE_AREA" in mesh["nanite_shape_preservation"]
    assert {slot["role"] for slot in mesh["material_slots"]} == {
        "branches",
        "leaves",
        "trunk",
    }
    for asset_path in [
        mesh["asset_path"],
        *import_report["textures"],
        *import_report["materials"],
    ]:
        package_path = asset_path.split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()

    assert visual_review["status"] == (
        "rights_clear_import_validated_visual_comparison_rejected_not_lifelike"
    )
    assert visual_review["production_promoted"] is False
    assert visual_review["decision"] == (
        "retain_import_pipeline_and_isolated_assets_reject_visual_promotion"
    )
    assert len(visual_review["visual_findings"]) == 5
    assert len(visual_review["next_asset_requirements"]) == 5
    for capture_key, hash_key in (
        ("guide_seat_capture", "guide_seat_sha256"),
        ("river_eye_capture", "river_eye_sha256"),
        ("restored_baseline_guide_seat_capture", "restored_baseline_guide_seat_sha256"),
        ("restored_baseline_river_eye_capture", "restored_baseline_river_eye_sha256"),
    ):
        capture = REPO_ROOT / visual_review["reviewed_candidate"][capture_key]
        assert_capture_recorded(capture)
        if capture.exists():
            assert _sha256(capture) == visual_review["reviewed_candidate"][hash_key]

    assert "JacarandaTree_1K" not in editor_source
    assert "jacaranda" not in active_manifest.lower()


def test_rights_reviewed_futaleufu_forest_set_is_isolated_and_visually_rejected():
    shared_importer = REVIEWED_BIOME_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    script = REVIEWED_FUTALEUFU_FOREST_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    source_manifest = json.loads(
        REVIEWED_FUTALEUFU_FOREST_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    import_report = json.loads(
        REVIEWED_FUTALEUFU_FOREST_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )
    visual_review = json.loads(
        REVIEWED_FUTALEUFU_FOREST_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")
    active_manifest = LANDSCAPE_CANDIDATE_MANIFEST_PATH.read_text(encoding="utf-8")

    assert 'or "alpha" in texture_name' in shared_importer
    assert "RAFTSIM_FUTALEUFU_FOREST_SOURCE_ROOT" in script
    assert "Hash mismatch" in script
    assert "combine_meshes = False" in script
    assert "flip_green_channel" in script
    assert "PRESERVE_AREA" in script
    assert "production_promoted" in script
    assert 'startswith(f"{prefix}_")' in script

    assert (
        source_manifest["status"]
        == "rights_reviewed_source_bundle_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert len(source_manifest["sources"]) == 3
    assert {source["license"] for source in source_manifest["sources"]} == {
        "CC0 1.0 Universal"
    }
    assert source_manifest["acquisition"]["public_api_used"] is False
    assert source_manifest["acquisition"]["source_bundle_committed"] is False
    assert len(source_manifest["expected_source_files"]) == 21
    assert source_manifest["review_boundaries"][
        "futaleufu_species_approval"
    ].startswith("not_reviewed_structure_analog_only")

    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 21
    assert import_report["variant_counts"] == {
        "fir_sapling_medium": 3,
        "fir_sapling": 3,
        "fern_02": 4,
    }
    assert len(import_report["meshes"]) == 10
    assert len(import_report["textures"]) == 18
    assert len(import_report["materials"]) == 5
    expected_roles = {
        "fir_sapling_medium": {"branches", "twigs"},
        "fir_sapling": {"branches", "twigs"},
        "fern_02": {"fronds"},
    }
    for mesh in import_report["meshes"]:
        assert mesh["plausible_physical_height"] is True
        assert mesh["pivot_meets_ground"] is True
        assert mesh["pivot_within_footprint"] is True
        assert mesh["nanite_enabled"] is True
        assert "PRESERVE_AREA" in mesh["nanite_shape_preservation"]
        assert mesh["preconfiguration_triangle_count_lod0"] > 0
        assert mesh["nanite_fallback_triangle_count_lod0"] > 0
        assert {slot["role"] for slot in mesh["material_slots"]} == expected_roles[
            mesh["collection"]
        ]
        package_path = mesh["asset_path"].split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()
    for asset_path in [*import_report["textures"], *import_report["materials"]]:
        package_path = asset_path.split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()

    assert visual_review["status"] == (
        "rights_clear_import_validated_visual_comparison_rejected_not_lifelike"
    )
    assert visual_review["production_promoted"] is False
    assert visual_review["material_diagnostic"]["clean_start_compile_after_fix"] is True
    assert visual_review["decision"] == (
        "retain_import_pipeline_and_isolated_assets_reject_visual_promotion"
    )
    assert len(visual_review["visual_findings"]) == 5
    assert len(visual_review["next_asset_requirements"]) == 5
    for capture_key, hash_key in (
        ("guide_seat_capture", "guide_seat_sha256"),
        ("river_eye_capture", "river_eye_sha256"),
        (
            "pre_trial_baseline_guide_seat_capture",
            "pre_trial_baseline_guide_seat_sha256",
        ),
        ("pre_trial_baseline_river_eye_capture", "pre_trial_baseline_river_eye_sha256"),
        ("restored_active_guide_seat_capture", "restored_active_guide_seat_sha256"),
        ("restored_active_river_eye_capture", "restored_active_river_eye_sha256"),
    ):
        capture = REPO_ROOT / visual_review["reviewed_candidate"][capture_key]
        assert_capture_recorded(capture)
        if capture.exists():
            assert _sha256(capture) == visual_review["reviewed_candidate"][hash_key]

    assert "FutaleufuTemperateForestSet_1K" not in editor_source
    assert "futaleufu_temperate_forest_set" not in active_manifest.lower()


def test_rights_reviewed_futaleufu_island_tree_set_is_isolated_and_visually_rejected():
    script = REVIEWED_FUTALEUFU_ISLAND_TREE_IMPORT_SCRIPT_PATH.read_text(
        encoding="utf-8"
    )
    source_manifest = json.loads(
        REVIEWED_FUTALEUFU_ISLAND_TREE_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    import_report = json.loads(
        REVIEWED_FUTALEUFU_ISLAND_TREE_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )
    visual_review = json.loads(
        REVIEWED_FUTALEUFU_ISLAND_TREE_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")
    active_manifest = LANDSCAPE_CANDIDATE_MANIFEST_PATH.read_text(encoding="utf-8")

    assert "RAFTSIM_FUTALEUFU_ISLAND_TREE_SOURCE_ROOT" in script
    assert "Hash mismatch" in script
    assert "combine_meshes = False" in script
    assert "flip_green_channel" in script
    assert "PRESERVE_AREA" in script
    assert "publisher_width_relative_error" in script
    assert "production_promoted" in script

    assert (
        source_manifest["status"]
        == "rights_reviewed_source_bundle_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert len(source_manifest["sources"]) == 3
    assert {source["license"] for source in source_manifest["sources"]} == {
        "CC0 1.0 Universal"
    }
    assert source_manifest["acquisition"]["public_api_used"] is False
    assert source_manifest["acquisition"]["source_bundle_committed"] is False
    assert len(source_manifest["expected_source_files"]) == 33
    assert source_manifest["review_boundaries"][
        "futaleufu_species_approval"
    ].startswith("not_reviewed_dense_coastal_broadleaf_structure_analog_only")

    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 33
    assert len(import_report["meshes"]) == 3
    assert len(import_report["textures"]) == 30
    assert len(import_report["materials"]) == 9
    assert [
        round(mesh["publisher_width_cm"], 2) for mesh in import_report["meshes"]
    ] == [
        1250.0,
        850.0,
        850.0,
    ]
    for mesh in import_report["meshes"]:
        assert mesh["publisher_width_relative_error"] <= 0.02
        assert mesh["plausible_physical_height"] is True
        assert mesh["plausible_crown_width"] is True
        assert mesh["pivot_meets_ground"] is True
        assert mesh["pivot_within_footprint"] is True
        assert mesh["nanite_enabled"] is True
        assert "PRESERVE_AREA" in mesh["nanite_shape_preservation"]
        assert {slot["role"] for slot in mesh["material_slots"]} == {
            "trunk",
            "leaves",
            "branches",
        }
        package_path = mesh["asset_path"].split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()
    for asset_path in [*import_report["textures"], *import_report["materials"]]:
        package_path = asset_path.split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()

    assert visual_review["status"] == (
        "rights_clear_import_validated_visual_comparison_rejected_not_lifelike"
    )
    assert visual_review["production_promoted"] is False
    assert visual_review["decision"] == (
        "retain_import_pipeline_and_isolated_assets_reject_visual_promotion"
    )
    assert len(visual_review["visual_findings"]) == 5
    assert len(visual_review["next_asset_requirements"]) == 5
    for capture_key, hash_key in (
        ("guide_seat_capture", "guide_seat_sha256"),
        ("river_eye_capture", "river_eye_sha256"),
        (
            "pre_trial_baseline_guide_seat_capture",
            "pre_trial_baseline_guide_seat_sha256",
        ),
        ("pre_trial_baseline_river_eye_capture", "pre_trial_baseline_river_eye_sha256"),
        ("restored_active_guide_seat_capture", "restored_active_guide_seat_sha256"),
        ("restored_active_river_eye_capture", "restored_active_river_eye_sha256"),
    ):
        capture = REPO_ROOT / visual_review["reviewed_candidate"][capture_key]
        assert_capture_recorded(capture)
        if capture.exists():
            assert _sha256(capture) == visual_review["reviewed_candidate"][hash_key]

    assert "FutaleufuIslandTreeSet_1K" not in editor_source
    assert "futaleufu_island_tree" not in active_manifest.lower()


def test_rights_reviewed_pine_set_is_hashed_physical_and_isolated():
    script = REVIEWED_PINE_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    shared_importer = REVIEWED_BIOME_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    source_manifest = json.loads(
        REVIEWED_PINE_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    import_report = json.loads(
        REVIEWED_PINE_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )

    assert "RAFTSIM_REVIEWED_PINE_SOURCE_ROOT" in script
    assert "Hash mismatch" in script
    assert "combine_meshes = False" in script
    assert "flip_green_channel" in script
    assert "PRESERVE_AREA" in script
    assert "production_promoted" in script
    assert '"norgl" in texture_name' in shared_importer
    assert '"rough" in texture_name' in shared_importer

    assert (
        source_manifest["status"]
        == "rights_reviewed_source_bundle_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert source_manifest["source"]["license"] == "CC0 1.0 Universal"
    assert source_manifest["source"]["public_api_used"] is False
    assert source_manifest["source"]["source_bundle_committed"] is False
    assert len(source_manifest["expected_source_files"]) == 17

    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 17
    assert len(import_report["meshes"]) == 3
    assert len(import_report["textures"]) == 16
    assert len(import_report["materials"]) == 5
    for mesh in import_report["meshes"]:
        assert 1000.0 <= mesh["height_cm"] <= 3000.0
        assert mesh["plausible_tree_height"] is True
        assert mesh["nanite_enabled"] is True
        assert "PRESERVE_AREA" in mesh["nanite_shape_preservation"]
        assert "needles" in {slot["role"] for slot in mesh["material_slots"]}
        package_path = mesh["asset_path"].split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()


def test_rights_reviewed_terrain_detail_is_hashed_isolated_and_source_bounded():
    script = REVIEWED_TERRAIN_DETAIL_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    source_manifest = json.loads(
        REVIEWED_TERRAIN_DETAIL_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    import_report = json.loads(
        REVIEWED_TERRAIN_DETAIL_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )

    assert "RAFTSIM_REVIEWED_TERRAIN_DETAIL_SOURCE_ROOT" in script
    assert "Hash mismatch" in script
    assert "flip_green_channel" in script
    assert "production_promoted" in script

    assert source_manifest["status"] == (
        "rights_reviewed_source_maps_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert source_manifest["source"]["license"] == "CC0 1.0 Universal"
    assert source_manifest["source"]["public_api_used"] is False
    assert source_manifest["source"]["source_bundle_committed"] is False
    assert source_manifest["source"]["publisher_width_m"] == 2.0
    assert len(source_manifest["expected_source_files"]) == 3
    assert source_manifest["review_boundaries"]["blocked_now"][0] == (
        "replacing NAIP macro color authority"
    )

    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 3
    assert len(import_report["textures"]) == 3
    for texture in import_report["textures"]:
        package_path = texture.split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()


def test_rights_reviewed_rock_ground_is_hashed_isolated_and_source_bounded():
    script = REVIEWED_ROCK_GROUND_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    source_manifest = json.loads(
        REVIEWED_ROCK_GROUND_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    import_report = json.loads(
        REVIEWED_ROCK_GROUND_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )

    assert "RAFTSIM_REVIEWED_ROCK_GROUND_SOURCE_ROOT" in script
    assert "Hash mismatch" in script
    assert "flip_green_channel" in script
    assert "production_promoted" in script

    assert source_manifest["status"] == (
        "rights_reviewed_source_maps_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert source_manifest["source"]["license"] == "CC0 1.0 Universal"
    assert source_manifest["source"]["public_api_used"] is False
    assert source_manifest["source"]["source_bundle_committed"] is False
    assert source_manifest["source"]["publisher_width_m"] == 1.5
    assert len(source_manifest["expected_source_files"]) == 3
    assert source_manifest["review_boundaries"]["blocked_now"][0] == (
        "replacing NAIP macro color authority"
    )

    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 3
    assert len(import_report["textures"]) == 3
    for texture in import_report["textures"]:
        package_path = texture.split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()


def test_rights_reviewed_zambezi_cliff_is_hashed_nanite_and_geology_bounded():
    script = REVIEWED_ZAMBEZI_CLIFF_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")
    source_manifest = json.loads(
        REVIEWED_ZAMBEZI_CLIFF_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    import_report = json.loads(
        REVIEWED_ZAMBEZI_CLIFF_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )
    comparison_report = json.loads(
        REVIEWED_ZAMBEZI_CLIFF_COMPARISON_REPORT_PATH.read_text(encoding="utf-8")
    )
    visual_review = json.loads(
        REVIEWED_ZAMBEZI_CLIFF_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )

    assert "RAFTSIM_REVIEWED_ZAMBEZI_CLIFF_SOURCE_ROOT" in script
    assert "Hash mismatch" in script
    assert "flip_green_channel" in script
    assert "set_nanite_settings" in script
    assert "18-23 m publisher-scale gate" in script
    assert "production_promoted" in script

    assert source_manifest["status"] == (
        "rights_reviewed_source_bundle_ready_for_isolated_import"
    )
    assert source_manifest["production_promoted"] is False
    assert source_manifest["source"]["license"] == "CC0 1.0 Universal"
    assert source_manifest["source"]["public_api_used"] is False
    assert source_manifest["source"]["source_bundle_committed"] is False
    assert source_manifest["source"]["publisher_width_m"] == 20.2
    assert len(source_manifest["expected_source_files"]) == 4
    assert source_manifest["review_boundaries"]["batoka_basalt_match"].startswith(
        "not_established"
    )
    assert (
        "default corridor inclusion"
        in source_manifest["review_boundaries"]["blocked_now"]
    )

    assert import_report["status"] == "isolated_review_candidate_imported"
    assert import_report["production_promoted"] is False
    assert len(import_report["verified_source_files"]) == 4
    assert len(import_report["textures"]) == 3
    assert len(import_report["materials"]) == 1
    assert {
        item["relative_path"]: item["sha256"]
        for item in import_report["verified_source_files"]
    } == source_manifest["expected_source_files"]

    mesh = import_report["mesh"]
    assert 1800.0 <= max(mesh["dimensions_cm"]) <= 2300.0
    assert mesh["lod0_build_scale"] == [100.0, 100.0, 100.0]
    assert mesh["nanite_enabled"] is True
    assert mesh["nanite_fallback_triangle_count_lod0"] > 0
    assert mesh["material_slot_count"] == 1
    for asset_path in [
        mesh["asset_path"],
        *import_report["textures"],
        *import_report["materials"],
    ]:
        package_path = asset_path.split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()

    assert "RaftSim.CaptureZambeziCliffComparison" in editor_source
    assert "RF_Transient" in editor_source
    assert "RaftSim_ExternalReviewOnly" in editor_source
    assert "ECollisionEnabled::NoCollision" in editor_source
    assert comparison_report["status"] == (
        "paired_transient_corridor_comparison_captured_pending_human_review"
    )
    assert comparison_report["production_promoted"] is False
    assert comparison_report["corridor_substitution_performed"] is False
    assert comparison_report["instances_per_capture"] == 8
    assert comparison_report["captures"]["all_captured"] is True
    assert len(comparison_report["guide_seat_placements"]) == 8
    assert len(comparison_report["river_eye_placements"]) == 8
    for placement in (
        comparison_report["guide_seat_placements"]
        + comparison_report["river_eye_placements"]
    ):
        assert 0.9 <= placement["scale"][0] <= 1.6
        assert placement["scale"][0] == placement["scale"][1] == placement["scale"][2]

    assert visual_review["status"] == (
        "rights_clear_import_validated_corridor_comparison_rejected_not_lifelike"
    )
    assert visual_review["production_promoted"] is False
    assert visual_review["corridor_substitution_performed"] is False
    assert visual_review["decision"] == (
        "retain_the_isolated_asset_and_transient_comparison_gate_reject_default_corridor_promotion"
    )
    assert len(visual_review["accepted_findings"]) == 3
    assert len(visual_review["rejection_reasons"]) == 5
    assert len(visual_review["next_iteration_requirements"]) == 5
    assert (
        visual_review["reviewed_evidence"]["comparison_guide_seat"][
            "changed_pixel_fraction_from_baseline"
        ]
        < 0.02
    )
    assert (
        visual_review["reviewed_evidence"]["comparison_river_eye"][
            "changed_pixel_fraction_from_baseline"
        ]
        < 0.01
    )
    for evidence in visual_review["reviewed_evidence"].values():
        capture = REPO_ROOT / evidence["capture"]
        assert_capture_recorded(capture)
        if capture.exists():
            assert _sha256(capture) == evidence["sha256"]


def test_batoka_surface_sources_are_hashed_cc0_and_isolated():
    detail_script = REVIEWED_BATOKA_DETAIL_IMPORT_SCRIPT_PATH.read_text(
        encoding="utf-8"
    )
    detail_manifest = json.loads(
        REVIEWED_BATOKA_DETAIL_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    detail_report = json.loads(
        REVIEWED_BATOKA_DETAIL_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )
    macro_script = REVIEWED_BATOKA_MACRO_IMPORT_SCRIPT_PATH.read_text(encoding="utf-8")
    macro_manifest = json.loads(
        REVIEWED_BATOKA_MACRO_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    macro_report = json.loads(
        REVIEWED_BATOKA_MACRO_IMPORT_REPORT_PATH.read_text(encoding="utf-8")
    )

    for script in (detail_script, macro_script):
        assert "Hash mismatch" in script
        assert "flip_green_channel" in script
        assert "TC_NORMALMAP" in script
        assert "TC_MASKS" in script
        assert "never_stream" in script
        assert "production_promoted" in script

    assert detail_manifest["source"]["license"] == "CC0 1.0 Universal"
    assert macro_manifest["source"]["license"] == "CC0"
    assert detail_manifest["production_promoted"] is False
    assert macro_manifest["production_promoted"] is False
    assert detail_manifest["source"]["source_bundle_committed"] is False
    assert macro_manifest["source"]["source_bundle_committed"] is False
    assert detail_manifest["review_boundaries"]["batoka_basalt_match"].startswith(
        "not_established"
    )
    assert macro_manifest["review_boundaries"]["batoka_basalt_match"].startswith(
        "not_established"
    )
    assert macro_manifest["source"]["publisher_scale_m"] == 50
    assert macro_manifest["source"]["publisher_density_px_per_cm"] == 0.8

    assert detail_report["status"] == "isolated_review_surface_candidate_imported"
    assert macro_report["status"] == (
        "isolated_review_macro_surface_candidate_imported"
    )
    assert detail_report["production_promoted"] is False
    assert macro_report["production_promoted"] is False
    assert len(detail_report["textures"]) == 5
    assert len(macro_report["textures"]) == 5
    assert {
        item["relative_path"]: item["sha256"]
        for item in detail_report["verified_source_files"]
    } == detail_manifest["expected_source_files"]
    assert {
        item["relative_path"]: item["sha256"]
        for item in macro_report["verified_source_files"]
    } == macro_manifest["expected_source_files"]
    for asset_path in [*detail_report["textures"], *macro_report["textures"]]:
        package_path = asset_path.split(".", 1)[0]
        assert (
            REPO_ROOT
            / ("unreal/Content" + package_path.removeprefix("/Game") + ".uasset")
        ).is_file()


def test_batoka_basalt_iterations_are_isolated_hashed_and_source_bounded():
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")
    manifest = json.loads(
        ZAMBEZI_BATOKA_BASALT_AUTHORING_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    assert manifest["status"] == (
        "v13_bounded_visual_morphology_rejected_insufficient_source_resolution"
    )
    assert manifest["production_promoted"] is False
    assert manifest["corridor_substitution_performed"] is False
    assert manifest["authorship"]["external_pixels_copied"] is True
    assert manifest["authorship"]["external_geometry_copied"] is False
    assert manifest["authorship"]["third_party_asset_dependency"] is True
    assert manifest["authorship"]["third_party_dependencies"] == [
        "polyhaven_aerial_rocks_02_4k",
        "ambientcg_rock037_2k",
    ]
    assert len(manifest["provenance"]) == 2
    assert manifest["provenance"][0]["publisher"] == "Zambezi River Authority"
    assert manifest["provenance"][1]["publisher"] == (
        "Environmental Resources Management"
    )
    assert len(manifest["module_family"]) == 4
    assert [item["version"] for item in manifest["iteration_history"]] == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
    ]
    assert [item["version"] for item in manifest["corridor_iteration_history"]] == [
        1,
        2,
        3,
        4,
        5,
    ]
    assert [item["status"] for item in manifest["corridor_iteration_history"]] == [
        "rejected",
        "rejected",
        "rejected",
        "projection_basis_retained_scene_rejected",
        "rejected",
    ]
    forbidden = " ".join(manifest["authority_boundary"]["forbidden_now"])
    for boundary in (
        "source DEM",
        "centerline",
        "collision",
        "custom C++ water",
        "GeoClaw",
        "feature-forcing",
        "hydrodynamic",
    ):
        assert boundary in forbidden

    assert "RaftSim.CreateZambeziBatokaBasaltFamily" in editor_source
    assert "ComputeBatokaBasaltNormals" in editor_source
    assert "SM_RaftSim_ZambeziBatokaBasalt_%s_V10" in editor_source
    assert "detached_flow_break_geometry_present" in editor_source
    assert "shared_vertex_surface_normals_applied" in editor_source
    assert "polyhaven_aerial_rocks_02_4k" in editor_source
    assert "ambientcg_rock037_2k" in editor_source

    iterations = (
        (
            1,
            ZAMBEZI_BATOKA_BASALT_V1_REPORT_RELATIVE_PATH,
            ZAMBEZI_BATOKA_BASALT_V1_REVIEW_RELATIVE_PATH,
            build_zambezi_batoka_basalt_v1_visual_review,
            "v1_disconnected_slab_geometry_rejected_v2_connected_wall_required",
        ),
        (
            2,
            ZAMBEZI_BATOKA_BASALT_V2_REPORT_RELATIVE_PATH,
            ZAMBEZI_BATOKA_BASALT_V2_REVIEW_RELATIVE_PATH,
            build_zambezi_batoka_basalt_v2_visual_review,
            "v2_connected_wall_culling_defect_localized_v3_winding_fix_required",
        ),
        (
            3,
            ZAMBEZI_BATOKA_BASALT_V3_REPORT_RELATIVE_PATH,
            ZAMBEZI_BATOKA_BASALT_V3_REVIEW_RELATIVE_PATH,
            build_zambezi_batoka_basalt_v3_visual_review,
            "v3_winding_fixed_morphology_rejected_v4_ledge_talus_material_revision_required",
        ),
        (
            4,
            ZAMBEZI_BATOKA_BASALT_V4_REPORT_RELATIVE_PATH,
            ZAMBEZI_BATOKA_BASALT_V4_REVIEW_RELATIVE_PATH,
            build_zambezi_batoka_basalt_v4_visual_review,
            "v4_ledges_and_talus_improved_surface_rejected_v5_smooth_joint_normals_required",
        ),
        (
            5,
            ZAMBEZI_BATOKA_BASALT_V5_REPORT_RELATIVE_PATH,
            ZAMBEZI_BATOKA_BASALT_V5_REVIEW_RELATIVE_PATH,
            build_zambezi_batoka_basalt_v5_visual_review,
            "v5_connected_surface_readable_rejected_v6_fracture_planes_surface_detail_required",
        ),
        (
            6,
            ZAMBEZI_BATOKA_BASALT_V6_REPORT_RELATIVE_PATH,
            ZAMBEZI_BATOKA_BASALT_V6_REVIEW_RELATIVE_PATH,
            build_zambezi_batoka_basalt_v6_visual_review,
            "v6_rock037_surface_detail_improved_rejected_v7_scale_and_morphology_revision_required",
        ),
        (
            7,
            ZAMBEZI_BATOKA_BASALT_V7_REPORT_RELATIVE_PATH,
            ZAMBEZI_BATOKA_BASALT_V7_REVIEW_RELATIVE_PATH,
            build_zambezi_batoka_basalt_v7_visual_review,
            "v7_macro_scale_improved_hard_panel_mosaic_rejected_v8_shared_surface_required",
        ),
        (
            8,
            ZAMBEZI_BATOKA_BASALT_V8_REPORT_RELATIVE_PATH,
            ZAMBEZI_BATOKA_BASALT_V8_REVIEW_RELATIVE_PATH,
            build_zambezi_batoka_basalt_v8_visual_review,
            "v8_shared_surface_readable_rock037_macro_pattern_rejected_v9_nonrepeating_surface_required",
        ),
        (
            9,
            ZAMBEZI_BATOKA_BASALT_V9_REPORT_RELATIVE_PATH,
            ZAMBEZI_BATOKA_BASALT_V9_REVIEW_RELATIVE_PATH,
            build_zambezi_batoka_basalt_v9_visual_review,
            "v9_nonrepeating_macro_surface_passes_distance_rejected_close_detail_v10_two_scale_required",
        ),
        (
            10,
            ZAMBEZI_BATOKA_BASALT_V10_REPORT_RELATIVE_PATH,
            ZAMBEZI_BATOKA_BASALT_V10_REVIEW_RELATIVE_PATH,
            build_zambezi_batoka_basalt_v10_visual_review,
            "v10_two_scale_surface_conditionally_accepted_for_transient_corridor_comparison_only",
        ),
    )
    for version, report_path, review_path, builder, review_status in iterations:
        report = json.loads((REPO_ROOT / report_path).read_text(encoding="utf-8"))
        review = json.loads((REPO_ROOT / review_path).read_text(encoding="utf-8"))
        assert report["schema"].endswith(f"isolated_family.v{version}")
        assert report["production_promoted"] is False
        assert report["corridor_substitution_performed"] is False
        assert report["collision_enabled"] is False
        assert report["module_count"] == 4
        assert report["capture_count"] == 16
        # Builder reproducibility only holds while the version's capture
        # binaries remain in the working tree; superseded-version binaries are
        # pruned (July 17 retention revision) and the committed review JSON is
        # the evidence of record.
        try:
            rebuilt = builder(REPO_ROOT)
        except FileNotFoundError:
            rebuilt = None
        if rebuilt is not None:
            assert review == rebuilt
        assert review["status"] == review_status
        assert review["production_promoted"] is False
        assert review["corridor_substitution_performed"] is False
        assert len(review["captures"]) == 16
        for module in report["modules"]:
            assert module["nanite_enabled"] is True
            assert module["collision_enabled"] is False
            asset = REPO_ROOT / (
                "unreal/Content"
                + module["mesh_asset"].removeprefix("/Game")
                + ".uasset"
            )
            assert asset.is_file()
        for capture in review["captures"]:
            capture_path = REPO_ROOT / capture["path"]
            assert_capture_recorded(capture_path)
            if capture_path.exists():
                assert _sha256(capture_path) == capture["sha256"]

    v2_report = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_BASALT_V2_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    v5_report = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_BASALT_V5_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    v10_report = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_BASALT_V10_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    assert v2_report["isolated_review_two_sided_culling_diagnostic"] is True
    assert v5_report["isolated_review_two_sided_culling_diagnostic"] is False
    assert v5_report["cliff_specific_normals_applied"] is True
    assert v5_report["smooth_joint_profiles_applied"] is True
    assert v5_report["detached_flow_break_geometry_present"] is False
    assert v10_report["shared_vertex_surface_normals_applied"] is True
    assert v10_report["external_pixels_copied"] is True
    assert v10_report["external_geometry_copied"] is False
    assert v10_report["surface_texture_asset_id"] == ("polyhaven_aerial_rocks_02_4k")
    assert v10_report["detail_texture_asset_id"] == "ambientcg_rock037_2k"
    assert v10_report["surface_texture_tile_cm"] == 5000.0
    assert v10_report["detail_texture_tile_cm"] == 240.0

    assert "RaftSim.CaptureZambeziBatokaBasaltCorridorComparison" in editor_source
    assert "RaftSimCaptureZambeziBatokaBasaltCorridorComparison" in editor_source
    assert "RaftSim.CaptureZambeziBatokaTerrainIntegratedComparison" in editor_source
    assert "RaftSimCaptureZambeziBatokaTerrainIntegratedComparison" in editor_source
    assert "RaftSim.CaptureZambeziBatokaWorldAlignedTerrainComparison" in editor_source
    assert "RaftSimCaptureZambeziBatokaWorldAlignedTerrainComparison" in editor_source
    assert "RaftSim.CaptureZambeziBatokaVisualMorphologyComparison" in editor_source
    assert "RaftSimCaptureZambeziBatokaVisualMorphologyComparison" in editor_source
    c1_report = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_BASALT_C1_CORRIDOR_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    c1_review = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_BASALT_C1_CORRIDOR_REVIEW_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    c2_report = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_BASALT_C2_CORRIDOR_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    c2_review = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_BASALT_C2_CORRIDOR_REVIEW_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    assert c1_report["production_promoted"] is False
    assert c1_report["corridor_substitution_performed"] is False
    assert c1_report["source_map_modified"] is False
    assert c1_report["collision_or_gameplay_authority_modified"] is False
    assert c1_report["instances_per_capture"] == 8
    try:
        _rebuilt = build_zambezi_batoka_basalt_c1_corridor_visual_review(REPO_ROOT)
    except FileNotFoundError:
        _rebuilt = None  # pruned evidence; committed review is the record
    if _rebuilt is not None:
        assert c1_review == _rebuilt
    assert c1_review["status"] == (
        "v10_c1_transient_corridor_comparison_rejected_small_pasted_panels"
    )
    assert c2_report["schema"].endswith("corridor_comparison.v2")
    assert c2_report["production_promoted"] is False
    assert c2_report["corridor_substitution_performed"] is False
    assert c2_report["source_map_modified"] is False
    assert c2_report["collision_or_gameplay_authority_modified"] is False
    assert c2_report["instances_per_capture"] == 8
    try:
        _rebuilt = build_zambezi_batoka_basalt_c2_corridor_visual_review(REPO_ROOT)
    except FileNotFoundError:
        _rebuilt = None  # pruned evidence; committed review is the record
    if _rebuilt is not None:
        assert c2_review == _rebuilt
    assert c2_review["status"] == (
        "v10_c2_gorge_scale_corridor_comparison_rejected_terrain_integration_required"
    )
    for report in (c1_report, c2_report):
        assert report["captures"]["all_captured"] is True
        for placement in (
            report["guide_seat_placements"] + report["river_eye_placements"]
        ):
            assert placement["scale"][0] == placement["scale"][1]
            assert placement["scale"][1] == placement["scale"][2]
    for review in (c1_review, c2_review):
        for evidence in review["reviewed_evidence"].values():
            for key in ("baseline", "comparison"):
                capture_path = REPO_ROOT / evidence[f"{key}_capture"]
                assert_capture_recorded(capture_path)
                if capture_path.exists():
                    assert _sha256(capture_path) == evidence[f"{key}_sha256"]

    c3_report = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_C3_TERRAIN_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    c3_review = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_C3_TERRAIN_REVIEW_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    assert c3_report["schema"].endswith("terrain_integrated_comparison.v1")
    assert c3_report["production_promoted"] is False
    assert c3_report["corridor_substitution_performed"] is False
    assert c3_report["source_map_modified"] is False
    assert c3_report["landscape_height_or_collision_modified"] is False
    assert c3_report["hydrodynamic_or_gameplay_authority_modified"] is False
    assert c3_report["expected_visual_tile_count"] == 4
    assert c3_report["guide_overridden_visual_tile_count"] == 4
    assert c3_report["river_eye_overridden_visual_tile_count"] == 4
    assert c3_report["material_parameters"]["macro_tile_cm"] == 5000.0
    assert c3_report["material_parameters"]["detail_tile_cm"] == 240.0
    try:
        _rebuilt = build_zambezi_batoka_v11_terrain_integrated_visual_review(REPO_ROOT)
    except FileNotFoundError:
        _rebuilt = None  # pruned evidence; committed review is the record
    if _rebuilt is not None:
        assert c3_review == _rebuilt
    assert c3_review["status"] == (
        "v11_continuous_terrain_material_rejected_world_projection_and_geometry_required"
    )
    for evidence in c3_review["reviewed_evidence"].values():
        for key in ("baseline", "comparison"):
            capture_path = REPO_ROOT / evidence[f"{key}_capture"]
            assert_capture_recorded(capture_path)
            if capture_path.exists():
                assert _sha256(capture_path) == evidence[f"{key}_sha256"]

    c4_report = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_C4_WORLD_ALIGNED_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    c4_review = json.loads(
        (REPO_ROOT / ZAMBEZI_BATOKA_C4_WORLD_ALIGNED_REVIEW_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    assert c4_report["schema"].endswith("world_aligned_terrain_comparison.v1")
    assert c4_report["production_promoted"] is False
    assert c4_report["source_map_modified"] is False
    assert c4_report["landscape_height_or_collision_modified"] is False
    assert c4_report["hydrodynamic_or_gameplay_authority_modified"] is False
    assert c4_report["guide_overridden_visual_tile_count"] == 4
    assert c4_report["river_eye_overridden_visual_tile_count"] == 4
    assert c4_report["material_parameters"]["projection"] == ("world_aligned_triplanar")
    assert c4_report["material_parameters"]["world_space_normal_output"] is True
    try:
        _rebuilt = build_zambezi_batoka_v12_world_aligned_visual_review(REPO_ROOT)
    except FileNotFoundError:
        _rebuilt = None  # pruned evidence; committed review is the record
    if _rebuilt is not None:
        assert c4_review == _rebuilt
    assert c4_review["status"] == (
        "v12_world_alignment_retained_as_projection_basis_terrain_and_scene_rejected"
    )
    for evidence in c4_review["reviewed_evidence"].values():
        for key in ("baseline", "comparison"):
            capture_path = REPO_ROOT / evidence[f"{key}_capture"]
            assert_capture_recorded(capture_path)
            if capture_path.exists():
                assert _sha256(capture_path) == evidence[f"{key}_sha256"]

    c5_report = json.loads(
        (
            REPO_ROOT / ZAMBEZI_BATOKA_C5_VISUAL_MORPHOLOGY_REPORT_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )
    c5_review = json.loads(
        (
            REPO_ROOT / ZAMBEZI_BATOKA_C5_VISUAL_MORPHOLOGY_REVIEW_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )
    assert c5_report["schema"].endswith("visual_morphology_comparison.v1")
    assert c5_report["production_promoted"] is False
    assert c5_report["survey_or_source_terrain_replacement_performed"] is False
    assert c5_report["source_map_modified"] is False
    assert c5_report["landscape_height_or_collision_modified"] is False
    assert c5_report["hydrodynamic_or_gameplay_authority_modified"] is False
    assert c5_report["morphology_parameters"]["maximum_absolute_offset_m"] == 4.5
    assert c5_report["morphology_parameters"]["river_protection_full_width_m"] == 220.0
    for view_name in ("comparison_guide_seat", "comparison_river_eye"):
        stats = c5_report["treatment_statistics"][view_name]
        assert stats["visual_tile_count"] == 4
        assert stats["total_vertex_count"] == 1_631_500
        assert stats["modified_vertex_count"] == 69_987
        assert stats["protected_river_corridor_vertex_count"] == 76_403
        assert -450.0 <= stats["minimum_offset_cm"] < 0.0
        assert 0.0 < stats["maximum_offset_cm"] <= 450.0
    try:
        _rebuilt = build_zambezi_batoka_v13_visual_morphology_review(REPO_ROOT)
    except FileNotFoundError:
        _rebuilt = None  # pruned evidence; committed review is the record
    if _rebuilt is not None:
        assert c5_review == _rebuilt
    assert c5_review["status"] == (
        "v13_bounded_visual_morphology_rejected_insufficient_source_resolution"
    )
    for evidence in c5_review["reviewed_evidence"].values():
        for key in ("baseline", "comparison"):
            capture_path = REPO_ROOT / evidence[f"{key}_capture"]
            assert_capture_recorded(capture_path)
            if capture_path.exists():
                assert _sha256(capture_path) == evidence[f"{key}_sha256"]
