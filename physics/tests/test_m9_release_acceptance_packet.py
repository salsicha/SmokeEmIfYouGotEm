from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKET_PATH = REPO_ROOT / "docs/release-review/m9-south-fork-acceptance.json"
PACKET_MARKDOWN_PATH = REPO_ROOT / "docs/release-review/m9-south-fork-acceptance.md"


def _png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    assert header[12:16] == b"IHDR"
    return struct.unpack(">II", header[16:24])


def test_m9_release_acceptance_packet_is_current_or_explicitly_stale_and_fail_closed() -> None:
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(
        (
            REPO_ROOT
            / "unreal/Content/RaftSim/Production/m9_release_candidate_manifest.json"
        ).read_text(encoding="utf-8")
    )

    assert packet["schema"] == "raftsim.m9.south_fork_release_acceptance.v1"
    assert packet["status"] == "awaiting_named_human_reviewers_not_approved"
    assert packet["passed"] is False
    assert (
        packet["candidate"]["accepted_editor_baseline"]
        == (
            manifest["local_preflight_evidence"]["full_reach_editor_generation"][
                "accepted_editor_baseline"
            ]
        )
    )
    assert (
        packet["candidate"]["environment_determinism_signature_sha256"]
        == (
            manifest["local_preflight_evidence"]["full_reach_editor_generation"][
                "environment_determinism_signature_sha256"
            ]
        )
    )
    assert (
        packet["candidate"]["procedural_geography_determinism_signature_sha256"]
        == (
            manifest["local_preflight_evidence"]["full_reach_editor_generation"][
                "procedural_geography_determinism_signature_sha256"
            ]
        )
    )
    shipping = manifest["local_preflight_evidence"][
        "exact_current_dirty_shipping_preflight"
    ]
    historical_performance = shipping["metal_full_reach_performance"]
    current_performance_evidence = json.loads(
        (
            REPO_ROOT
            / packet["candidate"]["exact_current_performance_report"]
        ).read_text(encoding="utf-8")
    )
    current_performance = current_performance_evidence["shipping_performance"]
    assert packet["candidate"]["exact_current_performance_configuration"] == "Shipping"
    assert packet["candidate"]["exact_current_performance_passed"] is True
    assert (
        packet["candidate"]["exact_current_performance_canonical_isolation_passed"]
        is False
    )
    assert packet["candidate"]["exact_current_performance_promotion_eligible"] is False
    assert packet["candidate"]["latest_completed_shipping_performance_passed"] is True
    assert (
        packet["candidate"]["exact_current_performance_p95_ms"]
        == current_performance["p95_frame_ms"]
    )
    assert current_performance["release_performance_qualified"] is True
    assert current_performance_evidence["promotion_allowed"] is False
    assert historical_performance["passed"] is True
    performance = historical_performance
    assert shipping["candidate_status"] == (
        "superseded_dirty_worktree_diagnostic_after_v552_v559_v579_v587_v595_v600_v601_v606_v610_v613_visual_deltas"
    )
    assert shipping["exact_current"] is False
    assert shipping["includes_packaged_v317_flexible_raft_upgrade"] is True
    assert shipping["includes_v418_source_true_wrap_upgrade"] is True
    assert shipping["includes_v426_runtime_camera_presentation_upgrade"] is True
    assert shipping["includes_v460_d4_contact_water_vfx_upgrade"] is True
    assert shipping["includes_v482_d4_contact_water_patch_upgrade"] is True
    assert shipping["includes_v510_solver_bounded_shoreline_presentation"] is True
    assert shipping["includes_v516_water_only_renderer_baseline"] is True
    assert shipping["includes_v520_allocation_free_overwash_stability_repair"] is True
    assert shipping["includes_v527_lumen_irradiance_occlusion_probe_pair"] is True
    assert shipping["includes_v552_procedural_boulder_upgrade"] is False
    assert shipping["includes_v559_coordinated_highside_pose_upgrade"] is False
    assert shipping["includes_v570_head_helmet_alignment_upgrade"] is False
    assert shipping["includes_v579_rights_hair_parent_shaft_head_upgrade"] is False
    assert shipping["includes_v587_boulder_source_restore"] is False
    assert shipping["shoreline_changes_collision_hydraulics_or_navigation"] is False
    assert shipping["lumen_irradiance_probe_resolution"] == 8
    assert shipping["lumen_occlusion_probe_resolution"] == 8
    assert shipping["overwash_long_run_native_evaluations"] == 20_000
    assert shipping["overwash_long_run_native_regression_passed"] is True
    assert shipping["spray_material_analytic_breakup"] is True
    assert (
        shipping["spray_material_translucency_lighting_mode"]
        == "TLM_VolumetricNonDirectional"
    )
    assert shipping["spray_material_clean_shipping_shader_compile_metal_sm5"] is True
    assert shipping["spray_material_clean_shipping_shader_compile_metal_sm6"] is True
    assert shipping["spray_material_default_material_fallback"] is False
    assert shipping["river_boulder_clean_shipping_shader_compile_metal_sm5"] is True
    assert shipping["river_boulder_clean_shipping_shader_compile_metal_sm6"] is True
    assert shipping["river_boulder_default_material_fallback"] is False
    assert shipping["archive_sha256"] == (
        "4f92bc38bec8cac643c656fd547b9ee79b7843d732b2132fe0d6328fd0812d53"
    )
    assert performance["protocol"] == (
        "normal_windowed_metal_presentation_launched_through_packaged_app_bundle"
    )
    assert performance["runs_passed"] == performance["runs_total"] == 2
    assert performance["offscreen_diagnostic_runs"] == 6
    assert performance["offscreen_diagnostic_runs_failed"] == 3
    assert performance["offscreen_diagnostic_qualified_as_release_performance"] is False
    generation = manifest["local_preflight_evidence"]["full_reach_editor_generation"]
    assert generation["post_lumen_pair_m4_exact_current"] is True
    assert generation["post_lumen_pair_m4_report"] == (
            "unreal/Saved/Automation/M9V431DepthV10M4/index.json"
    )
    assert generation["post_lumen_pair_m4_report_sha256"] == (
            "cb26301b2152cca34320df2e99bb7eb91bbf9d1ad358f16639a75f326a72fe64"
    )
    assert generation["post_lumen_pair_m5_exact_current"] is True
    assert generation["post_lumen_pair_m5_report"] == (
            "unreal/Saved/Automation/M9V432DepthV10M5/index.json"
    )
    assert generation["post_lumen_pair_m5_report_sha256"] == (
            "4c4e342dd3a3a92aee2415697910bf4539a00e774a26554596d446ccb8a5a070"
    )
    assert generation["post_hlod_m7_exact_current"] is True
    assert generation["post_hlod_m7_report"] == (
            "unreal/Saved/Automation/M9V433DepthV10M7/index.json"
    )
    assert generation["post_hlod_m7_report_sha256"] == (
            "704ec8a69af92f40a776de98671b1b03193f3756673a8e9646e838e3094b203b"
    )
    assert generation["m8_content_lock_exact_current"] is True
    assert generation["post_hlod_m8_report"] == (
            "unreal/Saved/Automation/M9V434DepthV10M8/index.json"
    )
    assert generation["post_hlod_m8_report_sha256"] == (
            "643f5c95f93dc37019ef926f08f9c033d9e5b7e78d2673a1a2c4ab648cb1b8c2"
    )
    assert generation["python_tests_exact_current"] is True
    assert generation["python_tests_report"] == (
            "physics/reports/m9/m9_v436_depth_v10_full_matrix.xml"
    )
    assert generation["python_tests_report_sha256"] == (
            "e726eab19d8e07c3bb9d5b646e569b4d60f2c3145f9f8632be11ad2171fe420f"
    )
    assert generation["python_tests_passed"] == 1146
    assert generation["python_tests_failed"] == 1
    assert generation["python_tests_failed_expected"] == 1
    assert generation["python_tests_failed_unexpected"] == 0
    assert generation["python_tests_skipped_expected"] == 3
    assert generation["python_tests_duration_seconds"] == 466.945
    assert generation[
        "python_tests_exact_current_pending_after_depth_bearing_contact_water_v10_review"
    ] is False
    assert generation["python_tests_exact_current_pending_after_v579_character_delta"] is False
    assert generation["python_tests_exact_current_pending_after_v587_material_package_delta"] is False
    assert generation[
        "python_tests_exact_current_pending_after_v595_spray_runtime_material_and_manifest_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_v600_boulder_package_and_manifest_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_v601_character_material_and_manifest_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_v606_runtime_lighting_and_manifest_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_v610_raft_material_and_manifest_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_v613_character_material_and_manifest_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_v663_named_rapid_visual_parity_material_audio_and_manifest_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_v675_solver_relief_source_test_and_manifest_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_v695_water_material_review_safety_lane"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_v730_reviewed_rock_diagnostic_lane"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_v735_contact_water_presentation_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_m9b3_v24_flow_aligned_whitewater_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_m9b3_v25_microdroplet_water_vfx_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_m9b3_v29_bounded_local_exposure_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_m9b3_v30_production_river_boot_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_m9b3_v34_production_river_boot_dark_pbr_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_m9b3_v35_articulated_paddle_grip_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_m9b3_v36_palm_centered_paddle_grip_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_m9b3_v42_d4_aware_production_raft_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_m9b3_v48_solver_breaking_water_lip_delta"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_connected_contact_water_v7_review"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_connected_contact_water_v8_review"
    ] is False
    m9_automation = manifest["local_preflight_evidence"]["m9_editor_automation"]
    assert m9_automation["exact_current"] is True
    assert m9_automation["report_path"] == (
        "unreal/Saved/Automation/M9V437DepthV10ReconciledM9/index.json"
    )
    assert m9_automation["report_sha256"] == (
        "8485da85825665b8db7dd8144be1cdd60a96754792affb85a572567e3223a2cc"
    )
    assert packet["candidate"]["exact_current_m4"] == (
        "v431_passed_4_of_4_after_depth_bearing_contact_water_v10_review"
    )
    assert packet["candidate"]["exact_current_m5"] == (
        "v432_passed_5_of_5_after_depth_bearing_contact_water_v10_review"
    )
    assert packet["candidate"]["exact_current_m7"] == (
        "v433_passed_4_of_4_after_depth_bearing_contact_water_v10_review"
    )
    assert packet["candidate"]["exact_current_m8"] == (
        "v434_passed_4_of_4_after_depth_bearing_contact_water_v10_review"
    )
    assert packet["candidate"]["exact_current_m9"] == (
        "v437_passed_5_of_5_fail_closed_after_reconciled_depth_bearing_contact_water_v10_review"
    )
    assert packet["candidate"]["exact_current_python_tests"] == (
        "v436_1146_passed_3_expected_skips_1_intentional_fail_closed_v42_visual_hash_mismatch_zero_unexpected_failures"
    )
    assert packet["candidate"]["exact_current_source_true_wrap_capture"] == (
        "docs/environment-captures/south_fork_full_reach/"
        "m9_solver_breaking_water_lip_v48_review.json"
    )
    assert packet["candidate"]["exact_current_presentation_capture"] == (
        "docs/environment-captures/south_fork_full_reach/"
        "m9_solver_breaking_water_lip_v48_review.json"
    )
    assert packet["candidate"]["exact_current_water_surface_report"] == (
        "unreal/Saved/Automation/M9B3V48BreakingLipWaterSurfaceExact/index.json"
    )
    assert packet["candidate"]["exact_current_water_surface_report_sha256"] == (
        "112e0cfa85fb1f1d99bb2a2e4b2c28047fc1f2f6a1cecb7ab0eb581115849cea"
    )
    assert packet["candidate"]["exact_current_m4_report"] == (
        "unreal/Saved/Automation/M9V431DepthV10M4/index.json"
    )
    assert packet["candidate"]["exact_current_m4_report_sha256"] == (
        "cb26301b2152cca34320df2e99bb7eb91bbf9d1ad358f16639a75f326a72fe64"
    )
    assert packet["candidate"]["exact_current_m5_report"] == (
        "unreal/Saved/Automation/M9V432DepthV10M5/index.json"
    )
    assert packet["candidate"]["exact_current_m5_report_sha256"] == (
        "4c4e342dd3a3a92aee2415697910bf4539a00e774a26554596d446ccb8a5a070"
    )
    assert packet["candidate"]["exact_current_m7_report"] == (
        "unreal/Saved/Automation/M9V433DepthV10M7/index.json"
    )
    assert packet["candidate"]["exact_current_m7_report_sha256"] == (
        "704ec8a69af92f40a776de98671b1b03193f3756673a8e9646e838e3094b203b"
    )
    assert packet["candidate"]["exact_current_m8_report"] == (
        "unreal/Saved/Automation/M9V434DepthV10M8/index.json"
    )
    assert packet["candidate"]["exact_current_m8_report_sha256"] == (
        "643f5c95f93dc37019ef926f08f9c033d9e5b7e78d2673a1a2c4ab648cb1b8c2"
    )
    assert packet["candidate"]["exact_current_m9_report"] == (
        "unreal/Saved/Automation/M9V437DepthV10ReconciledM9/index.json"
    )
    assert packet["candidate"]["exact_current_m9_report_sha256"] == (
        "8485da85825665b8db7dd8144be1cdd60a96754792affb85a572567e3223a2cc"
    )
    assert packet["candidate"]["exact_current_python_report"] == (
        "physics/reports/m9/m9_v436_depth_v10_full_matrix.xml"
    )
    assert packet["candidate"]["exact_current_python_report_sha256"] == (
        "e726eab19d8e07c3bb9d5b646e569b4d60f2c3145f9f8632be11ad2171fe420f"
    )
    assert {
        packet["candidate"]["exact_current_water_surface_report"],
        packet["candidate"]["exact_current_m4_report"],
        packet["candidate"]["exact_current_m5_report"],
        packet["candidate"]["exact_current_m7_report"],
        packet["candidate"]["exact_current_m8_report"],
        packet["candidate"]["exact_current_m9_report"],
        packet["candidate"]["exact_current_python_report"],
    }.issubset(set(packet["technical_evidence"]))
    assert packet["candidate"]["source_worktree_clean"] is False
    assert packet["candidate"]["not_for_navigation"] is True
    assert packet["candidate"]["procedural_infill_disclosure_required"] is True

    depth_v9_review_path = (
        REPO_ROOT / packet["candidate"]["depth_bearing_contact_water_v9_review"]
    )
    depth_v9_review = json.loads(depth_v9_review_path.read_text(encoding="utf-8"))
    assert depth_v9_review["passed"] is False
    assert depth_v9_review["promotion_allowed"] is False
    assert depth_v9_review["decision"] == (
        "reject_direct_stock_template_reuse_require_project_authored_depth_bearing_system"
    )
    assert depth_v9_review["production"]["selected"] is True
    assert depth_v9_review["production"]["niagara_fluids_enabled_in_uproject"] is False
    assert depth_v9_review["production"]["experimental_runtime_hook_retained"] is False
    for candidate_name in ("splash", "continuous_hose"):
        candidate = depth_v9_review["native_renderer_review"][candidate_name]
        assert candidate["component_state"] == "ready=1 visible=1 active=1"
        candidate_result = candidate["result"].lower()
        assert "perceptible" in candidate_result
        assert "no " in candidate_result or "not " in candidate_result
        for key in ("capture", "log"):
            artifact = REPO_ROOT / candidate[key]
            assert artifact.is_file()
            assert hashlib.sha256(artifact.read_bytes()).hexdigest() == (
                candidate[f"{key}_sha256"]
            )
    assert depth_v9_review["native_renderer_review"]["visual_verdict"] == "fail"
    assert depth_v9_review["post_revert_validation"]["m4"]["result"].startswith(
        "4/4 passed"
    )
    assert depth_v9_review["post_revert_validation"]["m9"]["result"].startswith(
        "5/5 passed"
    )

    depth_v10_review_path = (
        REPO_ROOT / packet["candidate"]["depth_bearing_contact_water_v10_review"]
    )
    depth_v10_review = json.loads(
        depth_v10_review_path.read_text(encoding="utf-8")
    )
    assert packet["candidate"]["depth_bearing_contact_water_v10"] == (
        "project_authored_six_frame_closed_implicit_mesh_cache_technical_candidate_photoreal_and_named_review_open"
    )
    assert depth_v10_review["passed"] is False
    assert depth_v10_review["technical_candidate_passed"] is True
    assert depth_v10_review["photoreal_acceptance_passed"] is False
    assert depth_v10_review["promotion_allowed"] is False
    assert depth_v10_review["decision"] == (
        "retain_opt_in_project_authored_candidate_pending_named_water_vfx_art_and_qualified_guide_review"
    )
    assert depth_v10_review["production"]["selected"] is False
    assert depth_v10_review["production"]["default_off"] is True
    assert depth_v10_review["production"]["physics_forces_changed"] is False
    assert depth_v10_review["production"]["collision_changed"] is False
    assert depth_v10_review["production"]["water_samples_changed"] is False
    assert depth_v10_review["implementation"]["ownership"] == (
        "project_owned_first_party_procedural"
    )
    assert depth_v10_review["implementation"]["frame_count"] == 6
    assert depth_v10_review["implementation"]["generated_depth_cm"] >= 100.0
    assert depth_v10_review["implementation"]["closed_volume"] is True
    assert depth_v10_review["implementation"]["runtime_geometry_rebuild"] is False
    assert depth_v10_review["authority_boundary"]["feedback_to_d4"] is False
    assert depth_v10_review["authority_boundary"]["feedback_to_live_water"] is False
    assert depth_v10_review["authority_boundary"]["feedback_to_gameplay"] is False
    for renderer_key in (
        "frame_0",
        "frame_2",
        "frame_4",
        "runtime_unforced",
        "waterless_isolation",
    ):
        renderer_evidence = depth_v10_review["native_renderer_review"][renderer_key]
        for key in ("capture", "log"):
            artifact = REPO_ROOT / renderer_evidence[key]
            assert artifact.is_file()
            assert hashlib.sha256(artifact.read_bytes()).hexdigest() == (
                renderer_evidence[f"{key}_sha256"]
            )
        assert _png_size(REPO_ROOT / renderer_evidence["capture"]) == (1280, 720)
    assert depth_v10_review["native_renderer_review"]["technical_visual_verdict"] == (
        "pass"
    )
    assert depth_v10_review["native_renderer_review"]["photoreal_visual_verdict"] == (
        "fail_pending_named_review_and_full_scene_art_upgrade"
    )
    for source_path, expected_hash in depth_v10_review[
        "implementation_sha256"
    ].items():
        assert hashlib.sha256((REPO_ROOT / source_path).read_bytes()).hexdigest() == (
            expected_hash
        )
    for automation_key in ("m4", "m5", "m7", "m8", "m9"):
        automation = depth_v10_review["exact_current_validation"][automation_key]
        report = REPO_ROOT / automation["report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            automation["report_sha256"]
        )
    python_matrix = depth_v10_review["exact_current_validation"][
        "full_python_data_source_matrix"
    ]
    assert python_matrix["tests"] == 1150
    assert python_matrix["passed"] == 1146
    assert python_matrix["failed_expected"] == 1
    assert python_matrix["failed_unexpected"] == 0
    assert python_matrix["skipped_expected"] == 3
    assert python_matrix["duration_seconds"] == 466.945
    python_report = REPO_ROOT / python_matrix["report"]
    assert hashlib.sha256(python_report.read_bytes()).hexdigest() == (
        python_matrix["report_sha256"]
    )
    assert depth_v10_review["reviewers"]["named_water_vfx_art_reviewer"] is None
    assert depth_v10_review["reviewers"]["qualified_south_fork_guide"] is None
    assert depth_v10_review["reviewers"]["art_approval"] is False
    assert depth_v10_review["reviewers"]["guide_approval"] is False
    assert str(depth_v10_review_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]

    pfd_review_path = (
        REPO_ROOT
        / packet["candidate"]["production_whitewater_pfd_visual_review"]
    )
    pfd_review = json.loads(pfd_review_path.read_text(encoding="utf-8"))
    assert pfd_review["status"] == (
        "technical_upgrade_accepted_photoreal_art_rejected"
    )
    assert pfd_review["runtime_asset"]["authored_lod0_triangles"] == 21_180
    assert pfd_review["runtime_asset"]["nanite_fallback_triangles"] == 2_168
    assert pfd_review["runtime_asset"]["material_slot_count"] == 5
    assert pfd_review["roster_audit"]["characters_using_production_pfd"] == 5
    assert pfd_review["roster_audit"]["maximum_runtime_torso_error_cm"] == 0.0
    assert pfd_review["automation"]["succeeded"] == 3
    assert pfd_review["automation"]["succeeded_with_warnings"] == 1
    assert pfd_review["automation"]["failed"] == 0
    assert pfd_review["d4_telemetry"]["contacts"] == 4
    assert pfd_review["d4_telemetry"]["wrapping"] == 3
    assert pfd_review["d4_telemetry"]["pinned"] == 1
    assert pfd_review["d4_telemetry"]["recovering"] == 1
    assert pfd_review["human_approved"] is False
    assert pfd_review["marketing_approved"] is False
    generation = manifest["local_preflight_evidence"]["full_reach_editor_generation"]
    assert generation["production_whitewater_pfd_source_fbx_sha256"] == (
        pfd_review["source"]["fbx_sha256"]
    )
    assert generation["production_whitewater_pfd_authored_lod0_triangles"] == 21_180
    assert generation["production_whitewater_pfd_maximum_torso_error_cm"] == 0.0
    assert generation["production_whitewater_pfd_m5_tests_passed"] == 4
    assert generation["production_whitewater_pfd_focused_tests_passed"] == 22
    assert generation["production_whitewater_pfd_photoreal_art_accepted"] is False

    raft_v42_review_path = (
        REPO_ROOT
        / packet["candidate"]["d4_aware_production_raft_visual_review"]
    )
    raft_v42_review = json.loads(raft_v42_review_path.read_text(encoding="utf-8"))
    assert raft_v42_review["status"] == (
        "technical_upgrade_accepted_photoreal_art_rejected"
    )
    assert raft_v42_review["implementation"]["physics_authority"] == (
        "existing D4 flexible segment state"
    )
    assert raft_v42_review["implementation"]["minimum_compressed_scale"] == 0.9
    assert raft_v42_review["implementation"]["lighting_gradient_scale"] == 0.52
    assert raft_v42_review["implementation"]["topology_changed"] is False
    assert raft_v42_review["implementation"]["collision_changed"] is False
    assert raft_v42_review["implementation"]["d3_or_d4_changed"] is False
    raft_v42_source = REPO_ROOT / raft_v42_review["source"]["runtime_deformer"]
    assert hashlib.sha256(raft_v42_source.read_bytes()).hexdigest() == (
        raft_v42_review["source"]["runtime_deformer_sha256"]
    )
    for path_key, hash_key in (
        ("material_authoring", "material_authoring_sha256"),
        ("raft_tube_material", "raft_tube_material_sha256"),
        ("raft_floor_material", "raft_floor_material_sha256"),
    ):
        assert hashlib.sha256(
            (REPO_ROOT / raft_v42_review["source"][path_key]).read_bytes()
        ).hexdigest() == raft_v42_review["source"][hash_key]
    raft_v42_m5 = REPO_ROOT / raft_v42_review["automation"]["exact_m5_report"]
    assert hashlib.sha256(raft_v42_m5.read_bytes()).hexdigest() == (
        raft_v42_review["automation"]["exact_m5_report_sha256"]
    )
    raft_v42_m1 = REPO_ROOT / raft_v42_review["automation"]["focused_m1_report"]
    assert hashlib.sha256(raft_v42_m1.read_bytes()).hexdigest() == (
        raft_v42_review["automation"]["focused_m1_report_sha256"]
    )
    assert raft_v42_review["automation"]["m5_succeeded"] == 4
    assert raft_v42_review["automation"]["m5_succeeded_with_warnings"] == 0
    for path_key, hash_key in (
        ("primary_capture", "primary_capture_sha256"),
        ("contact_capture", "contact_capture_sha256"),
    ):
        capture_path = REPO_ROOT / raft_v42_review["renderer_evidence"][path_key]
        assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == (
            raft_v42_review["renderer_evidence"][hash_key]
        )
    assert raft_v42_review["primary_capture_telemetry"]["contacts"] == 4
    assert raft_v42_review["primary_capture_telemetry"]["wrapping"] == 3
    assert raft_v42_review["primary_capture_telemetry"]["pinned"] == 1
    assert raft_v42_review["primary_capture_telemetry"]["recovering"] == 1
    assert raft_v42_review["human_approved"] is False
    assert raft_v42_review["marketing_approved"] is False
    assert generation["d4_aware_production_raft_runtime_source_sha256"] == (
        raft_v42_review["source"]["runtime_deformer_sha256"]
    )
    assert generation["d4_aware_production_raft_m5_report_sha256"] == (
        raft_v42_review["automation"]["exact_m5_report_sha256"]
    )
    assert generation["d4_aware_production_raft_m5_tests_passed"] == 4
    assert generation["d4_aware_production_raft_m5_exact_current"] is True
    assert generation["d4_aware_production_raft_physics_or_gameplay_changes"] is False
    assert generation["d4_aware_production_raft_photoreal_art_accepted"] is False
    presentation = manifest["local_preflight_evidence"]["presentation_review"]
    assert presentation["source_true_wrap_raft_tube_material_sha256"] == (
        raft_v42_review["source"]["raft_tube_material_sha256"]
    )
    assert presentation["source_true_wrap_raft_floor_material_sha256"] == (
        raft_v42_review["source"]["raft_floor_material_sha256"]
    )

    boulder_review_path = (
        REPO_ROOT
        / packet["candidate"]["production_river_boulder_visual_review"]
    )
    boulder_review = json.loads(boulder_review_path.read_text(encoding="utf-8"))
    assert boulder_review["status"] == (
        "technical_upgrade_accepted_photoreal_art_rejected"
    )
    assert boulder_review["runtime_asset"]["authored_lod0_triangles"] == 81_920
    assert boulder_review["runtime_asset"]["nanite_fallback_triangles"] == 1_766
    assert boulder_review["runtime_asset"]["collision_enabled"] is False
    assert boulder_review["construction"]["contact_envelope_fraction"] == 0.96
    boulder_asset_path = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/Rocks/Production/"
        "SM_RaftSim_ProductionRiverBoulder.uasset"
    )
    boulder_material_path = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Materials/"
        "M_RaftSim_ProductionRiverBoulder.uasset"
    )
    assert hashlib.sha256(boulder_asset_path.read_bytes()).hexdigest() == (
        boulder_review["runtime_asset"]["uasset_sha256"]
    )
    assert hashlib.sha256(boulder_material_path.read_bytes()).hexdigest() == (
        boulder_review["runtime_asset"]["material_uasset_sha256"]
    )
    boulder_import_report = REPO_ROOT / boulder_review["runtime_asset"]["import_report"]
    assert hashlib.sha256(boulder_import_report.read_bytes()).hexdigest() == (
        boulder_review["runtime_asset"]["import_report_sha256"]
    )
    boulder_m5_report = REPO_ROOT / boulder_review["automation"]["report"]
    assert hashlib.sha256(boulder_m5_report.read_bytes()).hexdigest() == (
        boulder_review["automation"]["report_sha256"]
    )
    assert boulder_review["d4_telemetry"]["contacts"] == 4
    assert boulder_review["d4_telemetry"]["wrapping"] == 3
    assert boulder_review["d4_telemetry"]["pinned"] == 1
    assert boulder_review["d4_telemetry"]["recovering"] == 1
    assert boulder_review["human_approved"] is False
    assert boulder_review["marketing_approved"] is False
    assert generation["production_river_boulder_source_fbx_sha256"] == (
        boulder_review["source"]["fbx_sha256"]
    )
    assert generation["production_river_boulder_authored_lod0_triangles"] == 81_920
    assert generation["production_river_boulder_nanite_fallback_triangles"] == 1_766
    assert generation["production_river_boulder_collision_enabled"] is False
    assert generation["production_river_boulder_m5_tests_passed"] == 4
    assert generation["production_river_boulder_m5_exact_current"] is True
    assert generation["production_river_boulder_m5_report_sha256"] == (
        boulder_review["automation"]["report_sha256"]
    )
    assert generation["production_river_boulder_photoreal_art_accepted"] is False

    water_review_path = (
        REPO_ROOT / packet["candidate"]["flow_aligned_whitewater_foam_visual_review"]
    )
    water_review = json.loads(water_review_path.read_text(encoding="utf-8"))
    assert water_review["status"] == (
        "technical_upgrade_accepted_photoreal_art_rejected"
    )
    assert water_review["source"]["generator_version"] == (
        "raftsim-production-whitewater-foam-lace-v3"
    )
    foam_source = REPO_ROOT / water_review["source"]["source_texture"]
    foam_provenance = REPO_ROOT / water_review["source"]["provenance"]
    foam_generator = REPO_ROOT / water_review["source"]["generator"]
    assert hashlib.sha256(foam_source.read_bytes()).hexdigest() == (
        water_review["source"]["source_texture_sha256"]
    )
    assert hashlib.sha256(foam_provenance.read_bytes()).hexdigest() == (
        water_review["source"]["provenance_sha256"]
    )
    assert hashlib.sha256(foam_generator.read_bytes()).hexdigest() == (
        water_review["source"]["generator_sha256"]
    )
    foam_texture_asset = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
        "T_RaftSim_SouthForkWater_FoamLace.uasset"
    )
    broad_water_material = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Materials/M_RaftSim_PhotorealRiverWater.uasset"
    )
    assert hashlib.sha256(foam_texture_asset.read_bytes()).hexdigest() == (
        water_review["runtime_assets"]["foam_lace_texture_uasset_sha256"]
    )
    assert hashlib.sha256(broad_water_material.read_bytes()).hexdigest() == (
        water_review["runtime_assets"]["broad_water_material_uasset_sha256"]
    )
    water_surface_report = REPO_ROOT / water_review["automation"][
        "water_surface_report"
    ]
    water_m5_report = REPO_ROOT / water_review["automation"]["m5_report"]
    assert hashlib.sha256(water_surface_report.read_bytes()).hexdigest() == (
        water_review["automation"]["water_surface_report_sha256"]
    )
    assert hashlib.sha256(water_m5_report.read_bytes()).hexdigest() == (
        water_review["automation"]["m5_report_sha256"]
    )
    assert water_review["automation"]["water_surface_failed"] == 0
    assert water_review["automation"]["m5_failed"] == 0
    assert water_review["presentation_contract"]["foam_generation_authority_changed"] is False
    assert water_review["presentation_contract"]["d3_changed"] is False
    assert water_review["presentation_contract"]["d4_changed"] is False
    assert water_review["d4_telemetry"]["contacts"] == 4
    assert water_review["d4_telemetry"]["wrapping"] == 3
    assert water_review["d4_telemetry"]["pinned"] == 1
    assert water_review["d4_telemetry"]["recovering"] == 1
    assert water_review["human_approved"] is False
    assert water_review["marketing_approved"] is False
    assert generation["flow_aligned_whitewater_foam_source_texture_sha256"] == (
        water_review["source"]["source_texture_sha256"]
    )
    assert generation["flow_aligned_whitewater_foam_texture_uasset_sha256"] == (
        water_review["runtime_assets"]["foam_lace_texture_uasset_sha256"]
    )
    assert generation["flow_aligned_whitewater_material_uasset_sha256"] == (
        water_review["runtime_assets"]["broad_water_material_uasset_sha256"]
    )
    assert generation["flow_aligned_whitewater_surface_tests_passed"] == 1
    assert generation["flow_aligned_whitewater_m5_tests_passed"] == 4
    assert generation["flow_aligned_whitewater_surface_report"] == (
        "unreal/Saved/Automation/M9B3V48BreakingLipWaterSurfaceExact/index.json"
    )
    assert generation["flow_aligned_whitewater_surface_report_sha256"] == (
        "112e0cfa85fb1f1d99bb2a2e4b2c28047fc1f2f6a1cecb7ab0eb581115849cea"
    )
    assert generation["flow_aligned_whitewater_m5_report"] == (
        "unreal/Saved/Automation/M9B3V48BreakingLipM5Exact/index.json"
    )
    assert generation["flow_aligned_whitewater_m5_report_sha256"] == (
        "6f0af8526f279d89919bc3a84293b6eef5d01b2e372ff6a11648383b69b1efa7"
    )
    assert generation["flow_aligned_whitewater_photoreal_art_accepted"] is False

    vfx_review_path = (
        REPO_ROOT / packet["candidate"]["microdroplet_water_vfx_visual_review"]
    )
    vfx_review = json.loads(vfx_review_path.read_text(encoding="utf-8"))
    assert vfx_review["status"] == (
        "technical_upgrade_accepted_photoreal_art_rejected"
    )
    vfx_runtime_source = REPO_ROOT / vfx_review["scope"]["runtime_source"]
    assert hashlib.sha256(vfx_runtime_source.read_bytes()).hexdigest() == (
        vfx_review["scope"]["runtime_source_sha256"]
    )
    vfx_m4_report = REPO_ROOT / vfx_review["automation"]["m4_report"]
    vfx_m5_report = REPO_ROOT / vfx_review["automation"]["m5_report"]
    assert hashlib.sha256(vfx_m4_report.read_bytes()).hexdigest() == (
        vfx_review["automation"]["m4_report_sha256"]
    )
    assert hashlib.sha256(vfx_m5_report.read_bytes()).hexdigest() == (
        vfx_review["automation"]["m5_report_sha256"]
    )
    assert vfx_review["automation"]["m4_failed"] == 0
    assert vfx_review["automation"]["m5_failed"] == 0
    assert vfx_review["presentation_contract"]["vfx_classifier_changed"] is False
    assert vfx_review["presentation_contract"]["vfx_trajectories_changed"] is False
    assert vfx_review["presentation_contract"]["contact_water_patch_changed"] is False
    assert vfx_review["presentation_contract"]["d3_changed"] is False
    assert vfx_review["presentation_contract"]["d4_changed"] is False
    assert vfx_review["d4_telemetry"]["contacts"] == 4
    assert vfx_review["d4_telemetry"]["wrapping"] == 3
    assert vfx_review["d4_telemetry"]["pinned"] == 1
    assert vfx_review["d4_telemetry"]["recovering"] == 1
    assert vfx_review["d4_telemetry"]["deterministic_instance_counts"] == {
        "fine_spray": 91,
        "mist": 5,
        "contact_foam": 9,
        "droplets": 144,
    }
    vfx_capture = REPO_ROOT / vfx_review["renderer_evidence"]["capture"]
    assert hashlib.sha256(vfx_capture.read_bytes()).hexdigest() == (
        vfx_review["renderer_evidence"]["capture_sha256"]
    )
    assert _png_size(vfx_capture) == (1470, 956)
    assert vfx_review["human_approved"] is False
    assert vfx_review["marketing_approved"] is False
    assert generation["microdroplet_water_vfx_runtime_source_sha256"] == (
        vfx_review["scope"]["runtime_source_sha256"]
    )
    assert generation["microdroplet_water_vfx_capture_sha256"] == (
        vfx_review["renderer_evidence"]["capture_sha256"]
    )
    assert generation["microdroplet_water_vfx_m4_tests_passed"] == 3
    assert generation["microdroplet_water_vfx_m4_exact_current"] is False
    assert generation["microdroplet_water_vfx_m5_tests_passed"] == 4
    assert generation["microdroplet_water_vfx_m5_exact_current"] is False
    assert generation["microdroplet_water_vfx_photoreal_art_accepted"] is False
    presentation = manifest["local_preflight_evidence"]["presentation_review"]
    assert presentation["source_true_wrap_spray_instances"] == 91
    assert presentation["source_true_wrap_mist_instances"] == 5
    assert presentation["source_true_wrap_impact_foam_instances"] == 9
    assert presentation["source_true_wrap_droplet_instances"] == 144
    assert presentation["source_true_wrap_contact_water_patch_triangles"] == 96

    exposure_review_path = (
        REPO_ROOT / packet["candidate"]["bounded_local_exposure_visual_review"]
    )
    exposure_review = json.loads(exposure_review_path.read_text(encoding="utf-8"))
    assert exposure_review["status"] == (
        "technical_upgrade_accepted_photoreal_art_rejected"
    )
    # The capture command is a shared evidence harness. Its v29 hash remains a
    # historical review fact and is intentionally not compared to the current
    # file after later water/raft telemetry additions. The two implementation
    # sources owned by the exposure review must still match exactly.
    assert len(exposure_review["scope"]["capture_command_source_sha256"]) == 64
    for source_key, hash_key in (
        ("runtime_camera_source", "runtime_camera_source_sha256"),
        ("m7_camera_contract_source", "m7_camera_contract_source_sha256"),
    ):
        source_path = REPO_ROOT / exposure_review["scope"][source_key]
        assert hashlib.sha256(source_path.read_bytes()).hexdigest() == (
            exposure_review["scope"][hash_key]
        )
    for report_key, hash_key in (
        ("m4_report", "m4_report_sha256"),
        ("m5_report", "m5_report_sha256"),
        ("m7_report", "m7_report_sha256"),
    ):
        report_path = REPO_ROOT / exposure_review["automation"][report_key]
        assert hashlib.sha256(report_path.read_bytes()).hexdigest() == (
            exposure_review["automation"][hash_key]
        )
    assert exposure_review["automation"]["m4_failed"] == 0
    assert exposure_review["automation"]["m5_failed"] == 0
    assert exposure_review["automation"]["m7_failed"] == 0
    assert exposure_review["presentation_contract"]["exposure_bias_after_ev"] == 1.25
    assert exposure_review["presentation_contract"]["highlight_contrast_scale"] == 0.78
    assert exposure_review["presentation_contract"]["shadow_contrast_scale"] == 0.72
    assert exposure_review["presentation_contract"]["materials_changed"] is False
    assert exposure_review["presentation_contract"]["lighting_actors_changed"] is False
    assert exposure_review["presentation_contract"]["d3_changed"] is False
    assert exposure_review["presentation_contract"]["d4_changed"] is False
    exposure_capture = REPO_ROOT / exposure_review["renderer_evidence"]["capture"]
    assert hashlib.sha256(exposure_capture.read_bytes()).hexdigest() == (
        exposure_review["renderer_evidence"]["capture_sha256"]
    )
    assert _png_size(exposure_capture) == (1470, 956)
    assert exposure_review["d4_telemetry"]["contacts"] == 4
    assert exposure_review["d4_telemetry"]["wrapping"] == 3
    assert exposure_review["d4_telemetry"]["pinned"] == 1
    assert exposure_review["d4_telemetry"]["recovering"] == 1
    assert exposure_review["human_approved"] is False
    assert exposure_review["marketing_approved"] is False
    assert generation["bounded_local_exposure_camera_source_sha256"] == (
        exposure_review["scope"]["runtime_camera_source_sha256"]
    )
    assert generation["bounded_local_exposure_capture_sha256"] == (
        exposure_review["renderer_evidence"]["capture_sha256"]
    )
    assert generation["bounded_local_exposure_m4_tests_passed"] == 3
    assert generation["bounded_local_exposure_m5_tests_passed"] == 4
    assert generation["bounded_local_exposure_m7_tests_passed"] == 4
    assert generation["bounded_local_exposure_photoreal_art_accepted"] is False
    assert presentation["runtime_camera_exposure_bias_ev"] == 1.25
    assert presentation["runtime_camera_local_exposure_method"] == "Bilateral"

    boot_review_path = (
        REPO_ROOT / packet["candidate"]["production_river_boot_visual_review"]
    )
    boot_review = json.loads(boot_review_path.read_text(encoding="utf-8"))
    assert boot_review["status"] == (
        "technical_upgrade_accepted_photoreal_art_rejected"
    )
    for path_key, hash_key in (
        ("generator", "generator_sha256"),
        ("importer", "importer_sha256"),
        ("material_builder", "material_builder_sha256"),
        ("manifest", "manifest_sha256"),
        ("blend", "blend_sha256"),
        ("fbx", "fbx_sha256"),
    ):
        source_path = REPO_ROOT / boot_review["source"][path_key]
        assert hashlib.sha256(source_path.read_bytes()).hexdigest() == (
            boot_review["source"][hash_key]
        )
    assert boot_review["source"]["external_inputs"] == []
    assert boot_review["runtime_asset"]["authored_lod0_triangles"] == 9708
    assert boot_review["runtime_asset"]["nanite_fallback_triangles"] == 1704
    assert boot_review["runtime_asset"]["material_slot_count"] == 3
    assert boot_review["runtime_asset"]["outsole_lugs"] == 12
    assert boot_review["runtime_asset"]["nanite_enabled"] is True
    boot_asset = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Equipment/Production/"
        "SM_RaftSim_WhitewaterRiverBoot.uasset"
    )
    assert hashlib.sha256(boot_asset.read_bytes()).hexdigest() == (
        boot_review["runtime_asset"]["uasset_sha256"]
    )
    upper_material = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Materials/M_RaftSim_RiverBootUpper.uasset"
    )
    rubber_material = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Materials/M_RaftSim_RiverBootRubber.uasset"
    )
    assert hashlib.sha256(upper_material.read_bytes()).hexdigest() == (
        boot_review["materials"]["upper_asset_sha256"]
    )
    assert hashlib.sha256(rubber_material.read_bytes()).hexdigest() == (
        boot_review["materials"]["rubber_asset_sha256"]
    )
    boot_material_report = REPO_ROOT / boot_review["materials"]["report"]
    assert hashlib.sha256(boot_material_report.read_bytes()).hexdigest() == (
        boot_review["materials"]["report_sha256"]
    )
    assert boot_review["materials"]["upper_base_tint_linear"] == [
        0.018,
        0.023,
        0.028,
    ]
    assert boot_review["materials"]["rubber_roughness"] == 0.62
    assert boot_review["materials"]["visual_only"] is True
    for path_key, hash_key in (
        ("crew_runtime_source", "crew_runtime_source_sha256"),
        ("crew_runtime_header", "crew_runtime_header_sha256"),
    ):
        integration_path = REPO_ROOT / boot_review["integration"][path_key]
        assert hashlib.sha256(integration_path.read_bytes()).hexdigest() == (
            boot_review["integration"][hash_key]
        )
    assert boot_review["integration"]["production_roster_count"] == 5
    assert boot_review["integration"]["production_boot_instances"] == 10
    assert boot_review["integration"]["production_boot_collision_enabled"] is False
    assert boot_review["integration"]["physics_or_rescue_changes"] is False
    boot_import_report = REPO_ROOT / boot_review["import_audit"]["report"]
    assert hashlib.sha256(boot_import_report.read_bytes()).hexdigest() == (
        boot_review["import_audit"]["report_sha256"]
    )
    boot_m5_report = REPO_ROOT / boot_review["automation"]["report"]
    assert hashlib.sha256(boot_m5_report.read_bytes()).hexdigest() == (
        boot_review["automation"]["report_sha256"]
    )
    assert boot_review["automation"]["succeeded"] == 3
    assert boot_review["automation"]["succeeded_with_warnings"] == 1
    assert boot_review["automation"]["failed"] == 0
    boot_capture = REPO_ROOT / boot_review["renderer_evidence"]["capture"]
    assert hashlib.sha256(boot_capture.read_bytes()).hexdigest() == (
        boot_review["renderer_evidence"]["capture_sha256"]
    )
    assert _png_size(boot_capture) == (1470, 956)
    assert boot_review["human_approved"] is False
    assert boot_review["marketing_approved"] is False
    assert generation["production_river_boot_source_fbx_sha256"] == (
        boot_review["source"]["fbx_sha256"]
    )
    assert generation["production_river_boot_authored_lod0_triangles"] == 9708
    assert generation["production_river_boot_nanite_fallback_triangles"] == 1704
    assert generation["production_river_boot_instance_count"] == 10
    assert generation["production_river_boot_upper_material_sha256"] == (
        boot_review["materials"]["upper_asset_sha256"]
    )
    assert generation["production_river_boot_rubber_material_sha256"] == (
        boot_review["materials"]["rubber_asset_sha256"]
    )
    assert generation["production_river_boot_material_audit_sha256"] == (
        boot_review["materials"]["report_sha256"]
    )
    assert generation["production_river_boot_m5_tests_passed"] == 4
    assert generation["production_river_boot_m5_exact_current"] is False
    assert generation["production_river_boot_photoreal_art_accepted"] is False

    grip_review_path = (
        REPO_ROOT / packet["candidate"]["palm_centered_paddle_grip_visual_review"]
    )
    grip_review = json.loads(grip_review_path.read_text(encoding="utf-8"))
    assert grip_review["status"] == (
        "technical_upgrade_accepted_photoreal_art_rejected"
    )
    for path_key, hash_key in (
        ("production_adapter", "production_adapter_sha256"),
        ("production_adapter_header", "production_adapter_header_sha256"),
    ):
        runtime_path = REPO_ROOT / grip_review["replacement_boundary"][path_key]
        assert hashlib.sha256(runtime_path.read_bytes()).hexdigest() == (
            grip_review["replacement_boundary"][hash_key]
        )
    assert grip_review["replacement_boundary"]["physics_or_gameplay_changes"] is False
    assert grip_review["implementation"]["production_roster_count"] == 5
    assert grip_review["implementation"]["articulated_hands_per_avatar"] == 2
    assert grip_review["implementation"]["digit_chains_per_hand"] == 5
    grip_m5_report = REPO_ROOT / grip_review["automation"]["report"]
    assert hashlib.sha256(grip_m5_report.read_bytes()).hexdigest() == (
        grip_review["automation"]["report_sha256"]
    )
    assert grip_review["automation"]["succeeded"] == 4
    assert grip_review["automation"]["succeeded_with_warnings"] == 0
    assert grip_review["automation"]["failed"] == 0
    for path_key, hash_key in (
        ("matched_capture", "matched_capture_sha256"),
        ("contact_diagnostic", "contact_diagnostic_sha256"),
    ):
        capture_path = REPO_ROOT / grip_review["renderer_evidence"][path_key]
        assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == (
            grip_review["renderer_evidence"][hash_key]
        )
        assert _png_size(capture_path) == (1470, 956)
    assert grip_review["human_approved"] is False
    assert grip_review["marketing_approved"] is False
    assert generation["articulated_paddle_grip_runtime_source_sha256"] == (
        "4cced2e354d8eaa5a7a6c993d5cd1e520a2582857cee6bcadead095a54972794"
    )
    assert generation["articulated_paddle_grip_runtime_header_sha256"] == (
        "255b80b0ea62e20359024af62793d673049b1f1f410c7f8b5b57baa612f2076a"
    )
    assert generation["articulated_paddle_grip_roster_count"] == 5
    assert generation["articulated_paddle_grip_hand_count"] == 10
    assert generation["articulated_paddle_grip_m5_tests_passed"] == 4
    assert generation["articulated_paddle_grip_m5_exact_current"] is False
    assert generation["articulated_paddle_grip_physics_or_gameplay_changes"] is False
    assert generation["articulated_paddle_grip_photoreal_art_accepted"] is False
    assert generation["palm_centered_paddle_grip_runtime_source_sha256"] == (
        grip_review["replacement_boundary"]["production_adapter_sha256"]
    )
    assert generation["palm_centered_paddle_grip_runtime_header_sha256"] == (
        grip_review["replacement_boundary"]["production_adapter_header_sha256"]
    )
    assert generation["palm_centered_paddle_grip_roster_count"] == 5
    assert generation["palm_centered_paddle_grip_hand_count"] == 10
    assert generation["palm_centered_paddle_grip_maximum_error_cm"] == 0.25
    assert generation["palm_centered_paddle_grip_m5_tests_passed"] == 4
    assert generation["palm_centered_paddle_grip_m5_exact_current"] is True
    assert generation["palm_centered_paddle_grip_m5_report"] == (
        grip_review["automation"]["report"]
    )
    assert generation["palm_centered_paddle_grip_m5_report_sha256"] == (
        grip_review["automation"]["report_sha256"]
    )
    assert generation["palm_centered_paddle_grip_physics_or_gameplay_changes"] is False
    assert generation["palm_centered_paddle_grip_photoreal_art_accepted"] is False

    lip_review_path = (
        REPO_ROOT / packet["candidate"]["solver_breaking_water_lip_visual_review"]
    )
    lip_review = json.loads(lip_review_path.read_text(encoding="utf-8"))
    assert lip_review["schema"] == "raftsim.m9.solver_breaking_water_lip_review.v1"
    assert lip_review["status"] == (
        "technical_upgrade_accepted_photoreal_art_rejected"
    )
    for path_key, hash_key in (
        ("runtime_surface", "runtime_surface_sha256"),
        ("runtime_header", "runtime_header_sha256"),
        ("material_authoring", "material_authoring_sha256"),
        ("material_authoring_script", "material_authoring_script_sha256"),
        ("capture_harness", "capture_harness_sha256"),
    ):
        source_path = REPO_ROOT / lip_review["source"][path_key]
        assert hashlib.sha256(source_path.read_bytes()).hexdigest() == (
            lip_review["source"][hash_key]
        )
    lip_material = REPO_ROOT / lip_review["runtime_asset"]["material"]
    assert hashlib.sha256(lip_material.read_bytes()).hexdigest() == (
        lip_review["runtime_asset"]["material_sha256"]
    )
    assert lip_review["runtime_asset"]["blend_mode"] == "BLEND_Translucent"
    assert lip_review["runtime_asset"]["two_sided"] is True
    assert len(lip_review["runtime_asset"]["serialized_texture_dependencies"]) == 2
    assert lip_review["runtime_asset"]["metal_sm6_default_material_fallback"] is False
    assert lip_review["implementation"]["multi_valued_overhang"] is True
    assert lip_review["implementation"]["separate_from_solver_surface"] is True
    assert lip_review["implementation"]["collision_enabled"] is False
    assert lip_review["implementation"]["water_sampling_changed"] is False
    assert lip_review["implementation"]["foam_site_generation_changed"] is False
    assert lip_review["implementation"]["d3_changed"] is False
    assert lip_review["implementation"]["d4_changed"] is False
    assert lip_review["implementation"]["maximum_site_count"] == 24
    assert lip_review["implementation"]["triangles_per_site"] == 128
    assert lip_review["implementation"]["maximum_triangle_count"] == 3072
    for report_key, hash_key in (
        ("water_surface_report", "water_surface_report_sha256"),
        ("m4_report", "m4_report_sha256"),
        ("m5_report", "m5_report_sha256"),
    ):
        report_path = REPO_ROOT / lip_review["automation"][report_key]
        assert hashlib.sha256(report_path.read_bytes()).hexdigest() == (
            lip_review["automation"][hash_key]
        )
    assert lip_review["automation"]["focused_python_passed"] == 34
    assert lip_review["automation"]["focused_python_failed"] == 0
    assert lip_review["automation"]["water_surface_succeeded"] == 1
    assert lip_review["automation"]["water_surface_succeeded_with_warnings"] == 0
    assert lip_review["automation"]["water_surface_failed"] == 0
    assert lip_review["automation"]["m4_succeeded"] == 3
    assert lip_review["automation"]["m4_succeeded_with_warnings"] == 0
    assert lip_review["automation"]["m4_failed"] == 0
    assert lip_review["automation"]["m5_succeeded"] == 4
    assert lip_review["automation"]["m5_succeeded_with_warnings"] == 0
    assert lip_review["automation"]["m5_failed"] == 0
    assert lip_review["breaking_water_telemetry"]["active_sites"] == 5
    assert lip_review["breaking_water_telemetry"]["visible_triangles"] == 640
    assert lip_review["breaking_water_telemetry"]["visible"] is True
    assert lip_review["breaking_water_telemetry"]["hero_wrapping"] == 3
    assert lip_review["breaking_water_telemetry"]["hero_pinned"] == 1
    for path_key, hash_key in (
        ("hero_capture", "hero_capture_sha256"),
        ("breaking_water_capture", "breaking_water_capture_sha256"),
    ):
        capture_path = REPO_ROOT / lip_review["renderer_evidence"][path_key]
        assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == (
            lip_review["renderer_evidence"][hash_key]
        )
        assert _png_size(capture_path) == (1470, 956)
    assert lip_review["human_approved"] is False
    assert lip_review["marketing_approved"] is False
    assert generation["solver_breaking_water_lip_status"] == (
        "m9b3_v48_technical_upgrade_accepted_photoreal_art_rejected"
    )
    assert generation["solver_breaking_water_lip_visual_review_sha256"] == (
        hashlib.sha256(lip_review_path.read_bytes()).hexdigest()
    )
    assert generation["solver_breaking_water_lip_runtime_surface_sha256"] == (
        lip_review["source"]["runtime_surface_sha256"]
    )
    assert generation["solver_breaking_water_lip_runtime_header_sha256"] == (
        lip_review["source"]["runtime_header_sha256"]
    )
    assert generation["solver_breaking_water_lip_material_uasset_sha256"] == (
        lip_review["runtime_asset"]["material_sha256"]
    )
    assert generation["solver_breaking_water_lip_active_sites"] == 5
    assert generation["solver_breaking_water_lip_visible_triangles"] == 640
    assert generation["solver_breaking_water_lip_maximum_triangles"] == 3072
    assert generation["solver_breaking_water_lip_material_default_fallback"] is False
    assert generation["solver_breaking_water_lip_water_surface_exact_current"] is True
    assert generation["solver_breaking_water_lip_m4_exact_current"] is True
    assert generation["solver_breaking_water_lip_m5_exact_current"] is True
    assert generation["solver_breaking_water_lip_physics_or_gameplay_changes"] is False
    assert generation["solver_breaking_water_lip_photoreal_art_accepted"] is False
    presentation = manifest["local_preflight_evidence"]["presentation_review"]
    assert presentation["solver_breaking_water_lip_active_sites"] == 5
    assert presentation["solver_breaking_water_lip_visible_triangles"] == 640
    assert presentation["solver_breaking_water_lip_material_default_fallback"] is False
    assert presentation["solver_breaking_water_lip_photoreal_art_accepted"] is False

    generated_rock_provenance = json.loads(
        (
            REPO_ROOT
            / "unreal/SourceArt/RaftSim/Rocks/Generated/"
            "T_RaftSim_SierraGranodiorite_BaseColor_v1.provenance.json"
        ).read_text(encoding="utf-8")
    )
    generated_rock_source = REPO_ROOT / generated_rock_provenance["path"]
    assert hashlib.sha256(generated_rock_source.read_bytes()).hexdigest() == (
        generated_rock_provenance["sha256"]
    )
    assert generated_rock_provenance["runtime_material_reference_present"] is False
    assert generated_rock_provenance["production_promoted"] is False
    assert generated_rock_provenance["renderer_attempts"][0]["accepted"] is False

    assert len(packet["captures"]) == 5
    assert any(
        capture["capture_id"] == "meat_grinder_d4_wrap_v24_flow_aligned_foam"
        for capture in packet["diagnostic_art_evidence"]
    )
    assert any(
        capture["capture_id"]
        == "meat_grinder_d4_wrap_v25_microdroplet_water_vfx"
        for capture in packet["diagnostic_art_evidence"]
    )
    assert any(
        capture["capture_id"]
        == "meat_grinder_d4_wrap_v29_bounded_local_exposure"
        for capture in packet["diagnostic_art_evidence"]
    )
    assert any(
        capture["capture_id"]
        == "meat_grinder_d4_wrap_v34_production_river_boot_dark_pbr"
        for capture in packet["diagnostic_art_evidence"]
    )
    assert any(
        capture["capture_id"]
        == "meat_grinder_d4_wrap_v35_articulated_paddle_grip"
        for capture in packet["diagnostic_art_evidence"]
    )
    assert any(
        capture["capture_id"]
        == "meat_grinder_d4_wrap_v36_palm_centered_paddle_grip"
        for capture in packet["diagnostic_art_evidence"]
    )
    assert any(
        capture["capture_id"]
        == "meat_grinder_d4_wrap_v48_flow_lace_breaking_lips_hero"
        for capture in packet["diagnostic_art_evidence"]
    )
    assert any(
        capture["capture_id"]
        == "meat_grinder_d4_wrap_v48_strongest_flow_lace_breaking_lip_review"
        for capture in packet["diagnostic_art_evidence"]
    )
    for capture in packet["captures"] + packet["diagnostic_art_evidence"]:
        capture_path = REPO_ROOT / capture["path"]
        assert capture_path.is_file()
        assert (
            hashlib.sha256(capture_path.read_bytes()).hexdigest() == capture["sha256"]
        )
        assert _png_size(capture_path) == (capture["width"], capture["height"])
        assert capture["human_approved"] is False

    expected_domains = {
        "product_owner_release_scope",
        "river_guide_hydraulic_and_rescue_fidelity",
        "art_direction_photoreal_environment_character_raft_water",
        "geospatial_alignment_and_procedural_authority",
        "legal_rights_provenance_and_release_media",
    }
    assert {
        domain["domain_id"] for domain in packet["review_domains"]
    } == expected_domains
    for domain in packet["review_domains"]:
        assert domain["reviewer_name"] is None
        assert domain["reviewed_utc"] is None
        assert domain["evidence"] == []
        assert domain["decision"] == "pending"
        assert domain["approved"] is False
        assert domain["required_evidence"]

    assert all(
        value is False for value in packet["external_platform_acceptance"].values()
    )
    assert packet["approved_presskit_media"] == []
    assert manifest["passed"] is False
    assert all(value is None for value in manifest["required_evidence"].values())

    wrap_review_path = (
        REPO_ROOT
        / "docs/environment-captures/south_fork_full_reach/"
        "m9_meat_grinder_d4_wrap_v735_review.json"
    )
    current_wrap_review = json.loads(wrap_review_path.read_text(encoding="utf-8"))
    assert current_wrap_review["capture_id"] == "meat_grinder_d4_wrap_v735"
    assert current_wrap_review["source_true_contact"]["contact_count"] == 4
    assert current_wrap_review["source_true_contact"]["wrapping_contact_count"] == 3
    assert current_wrap_review["source_true_contact"]["pinned_contact_count"] == 1
    assert current_wrap_review["source_true_contact"]["recovering_contact_count"] == 1
    assert current_wrap_review["source_true_contact"]["d4_is_only_collision_authority"] is True
    breakup = current_wrap_review["contact_water_breakup"]
    assert breakup["presentation_only"] is True
    assert breakup["contact_patch_topology_changed"] is False
    assert breakup["material_package_changed"] is False
    assert breakup["analytic_breakup_gain_after"] == 0.24
    assert breakup["analytic_breakup_floor_after"] == 0.66
    assert breakup["changes_to_d4_collision_authority"] is False
    hydraulic_review = json.loads(
        (REPO_ROOT / current_wrap_review["underlying_hydraulic_review"]).read_text(
            encoding="utf-8"
        )
    )
    named_parity = hydraulic_review["named_rapid_visual_parity"]
    assert named_parity["environment_algorithm"] == (
        "south_fork_photoreal_environment_v25_named_rapid_visual_parity"
    )
    assert named_parity["named_rapid_window_count"] == 20
    assert named_parity["flow_band_count_per_window"] == 3
    assert named_parity["saved_pixel_matches_runtime_cooked_field"] is True
    assert named_parity["corrected_surface_delta_m"] > 0.55
    assert hydraulic_review["audio_runtime_correction"]["retained"] is True
    relief = hydraulic_review["solver_resolved_hydraulic_relief"]
    assert relief["algorithm"] == "solver_resolved_station_curvature_v1"
    assert relief["presentation_only"] is True
    assert relief["linear_grade_residual_m"] == 0.0
    assert relief["calm_curved_water_relief_m"] == 0.0
    assert relief["measured_runtime_abs_max_relief_m"] == 0.2624
    assert relief["changes_to_d3_runtime_authority"] is False
    assert relief["changes_to_d4_collision_authority"] is False
    assert hydraulic_review["validation"]["water_surface_renderer_automation"] == (
        "1/1 passed (v673)"
    )
    assert current_wrap_review["validation"]["exact_current_m4"] == "3/3 passed (v735)"
    assert current_wrap_review["validation"]["exact_current_m5_production_quality"] == (
        "4/4 passed (v736)"
    )
    assert current_wrap_review["validation"]["exact_current_m7_rendered_presentation"] == (
        "4/4 passed (v737)"
    )
    assert current_wrap_review["validation"]["exact_current_m8_content_lock"] == (
        "4/4 passed (v738)"
    )
    assert current_wrap_review["validation"]["m9_fail_closed"] == "5/5 passed (v742)"
    assert current_wrap_review["validation"]["full_python_matrix"] == (
        "1095 passed, 3 expected skips, 0 failed in 1224.66 seconds "
        "(v741; JUnit SHA-256 "
        "4bd6156fd7b7c4d5445b337a27fab222ceb6f6e9250c107648ba7e68254f4b51)"
    )
    assert current_wrap_review["photoreal_art_accepted"] is False

    prior_material_review = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach/"
            "m9_meat_grinder_d4_wrap_v663_review.json"
        ).read_text(encoding="utf-8")
    )
    for relative_path, expected_sha256 in prior_material_review[
        "current_material_package_sha256"
    ].items():
        if relative_path.endswith(
            (
                "/M_RaftSim_RiverBoulder.uasset",
                "/M_RaftSim_PhotorealRiverWater.uasset",
                "/M_RaftSim_RaftTube.uasset",
                "/M_RaftSim_RaftFloor.uasset",
            )
        ):
            # Superseded intentionally by the v20 boulder, v24 water and
            # restored v42 raft contracts; current hashes are locked by their
            # exact-current reviews.
            continue
        assert hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_sha256
        )

    wrap_review = json.loads(
        (
            REPO_ROOT
            / "docs/environment-captures/south_fork_full_reach/"
            "m9_meat_grinder_d4_wrap_v613_review.json"
        ).read_text(encoding="utf-8")
    )
    hair = wrap_review["rights_tracked_hair_baseline"]
    assert hair["character_variant_count"] == 5
    assert hair["hair_style_count"] == 3
    assert hair["license"] == "CC-BY-4.0"
    assert hair["terminal_head_bone_uses_parent_to_head_authored_shaft"] is True
    assert hair["production_helmet_outer_shell_scale"] == 1.22
    assert hair["production_helmet_center_offset_cm"] == [3.0, 0.0, 1.0]
    character_material = wrap_review["character_material_iteration"]
    assert character_material["variant_skin_eye_and_hair_atlases_retained"] is True
    assert character_material["skeletal_wetsuit_slot_uses_generated_neoprene"] is True
    assert character_material["wetsuit_material_asset_sha256"] == (
        "363d43a2385aee6eb1f3eeb4b545a8556bf89e345d435ff5a91efe3de0b4a0a4"
    )
    assert character_material["wetsuit_skeletal_mesh_usage_enabled"] is True
    assert character_material["technical_upgrade_accepted"] is True
    assert character_material["photoreal_art_accepted"] is False
    raft_material = wrap_review["raft_material_iteration"]
    assert raft_material["v609_missing_static_mesh_usage_attempt_rejected"] is True
    assert raft_material["focused_production_raft_material_command"] == (
        "RaftSim.CreateProductionRaftMaterials"
    )
    assert raft_material["static_mesh_usage_enabled"] is True
    assert raft_material["tube_material_asset_sha256"] == (
        "860a0c7b819b255cf9caf8b26ffdeedca64560732254d3fb830e5a2d3fce7629"
    )
    assert raft_material["floor_material_asset_sha256"] == (
        "b24d1b19980c025bd5bd241913d2d24a8c46093a9dd13fc33c2e9940d4c8077d"
    )
    assert raft_material["current_saturated_roughness_scale"] == 0.46
    assert raft_material["current_saturated_roughness_max"] == 0.40
    assert raft_material["changes_raft_geometry_d4_contact_or_rescue_authority"] is False
    assert raft_material["technical_upgrade_accepted"] is True
    assert raft_material["photoreal_art_accepted"] is False
    skin_material = wrap_review["production_cc0_skin_iteration"]
    assert skin_material["rights_tracked_variant_atlases_retained"] is True
    assert skin_material["skeletal_meshes_rigging_and_slots_changed"] is False
    assert skin_material["focused_material_command"] == (
        "RaftSim.CreateProductionCC0SkinMaterials"
    )
    assert skin_material["shading_model"] == "MSM_PreintegratedSkin"
    assert skin_material["v612_broad_subsurface_tint_attempt_rejected"] is True
    assert skin_material["microdetail_base_gain_min"] == 0.95
    assert skin_material["microdetail_base_gain_max"] == 1.05
    assert skin_material["microdetail_normal_strength"] == 0.16
    assert skin_material["preintegrated_scatter_opacity"] == 0.94
    assert skin_material["material_sha256"]["guide"] == (
        "d457b3f1c4b4fe38b3e13eb0c3295ea79e999576626f54e526d220173bcf20f3"
    )
    assert skin_material["changes_gameplay_pose_d4_contact_or_rescue_authority"] is False
    assert skin_material["technical_upgrade_accepted"] is True
    assert skin_material["photoreal_art_accepted"] is False
    boulder = wrap_review["boulder_iteration"]
    assert boulder["project_owned_procedural_geometry_retained"] is True
    assert boulder["procedural_mesh_collision_enabled"] is False
    assert boulder["d4_contact_geometry_or_authority_changed"] is False
    assert boulder["reviewed_cc0_scan_texture_on_generated_shell_promoted"] is False
    assert boulder["v584_tangent_normal_attempt_rejected"] is True
    assert boulder["v585_scan_albedo_roughness_attempt_rejected"] is True
    assert boulder["v599_generated_world_aligned_granodiorite_attempt_rejected"] is True
    assert boulder["v605_lifted_mineral_midtone_attempt_rejected"] is True
    assert boulder["v608_lifted_mineral_color_only_attempt_rejected"] is True
    assert boulder["generated_granodiorite_source_art_retained_unpromoted"] is True
    assert boulder["generated_granodiorite_runtime_material_reference_removed"] is True
    assert boulder["v579_procedural_material_source_constants_restored"] is True
    assert boulder["v600_source_equivalent_procedural_material_restored"] is True
    assert boulder["restored_material_asset_sha256"] == (
        "187cbe757260521c236c4133d3828d0fbd8b230651ea27dffe63ac76f40e0e3c"
    )
    assert boulder["restored_material_byte_identical_to_v587"] is False
    assert boulder["visual_improvement_accepted"] is False
    assert boulder["baseline_regression_resolved"] is True
    water_vfx = wrap_review["water_vfx_iteration"]
    assert water_vfx["v594_broad_water_roughness_modulation_rejected"] is True
    assert water_vfx["broad_water_source_restored"] is True
    assert water_vfx["broad_water_material_asset_sha256"] == (
        "a6d1ca66ee9daac62b11835c88002f177c40723abc9165631c60017c701634cd"
    )
    assert water_vfx["spray_material_asset_sha256"] == (
        "d60fd253265c647b31e302c9c1509c5654524e57f648339704688f219c00bbee"
    )
    assert water_vfx["spray_soft_radial_edge"] is True
    assert water_vfx["spray_opacity"] == 0.20
    assert water_vfx["spray_low_discrepancy_phase_rate_width_and_arc_variation"] is True
    assert water_vfx["spray_distribution_technical_upgrade_accepted"] is True
    assert water_vfx["spray_distribution_changes_d4_or_water_authority"] is False
    assert water_vfx["broad_water_photoreal_art_accepted"] is False
    assert water_vfx["spray_photoreal_art_accepted"] is False
    lighting = wrap_review["presentation_lighting_iteration"]
    assert lighting["captured_scene_skylight_retained"] is True
    assert lighting["previous_dry_sky_intensity"] == 0.9
    assert lighting["current_dry_sky_intensity"] == 1.25
    assert lighting["clear_morning_applied_sky_intensity"] == 1.2185
    assert lighting["changes_gameplay_pose_d4_contact_or_rescue_authority"] is False
    assert lighting["technical_upgrade_accepted"] is True
    assert lighting["photoreal_art_accepted"] is False
    assert wrap_review["rights_tracked_hair_technical_upgrade_accepted"] is True
    assert wrap_review["skeletal_neoprene_technical_upgrade_accepted"] is True
    assert wrap_review["captured_sky_fill_technical_upgrade_accepted"] is True
    assert wrap_review["raft_wet_film_technical_upgrade_accepted"] is True
    assert wrap_review["production_cc0_skin_technical_upgrade_accepted"] is True
    assert wrap_review["boulder_visual_upgrade_accepted"] is False
    assert wrap_review["water_vfx_technical_upgrade_accepted"] is True
    assert wrap_review["photoreal_art_accepted"] is False


def test_m9_release_acceptance_packet_references_existing_evidence_and_images() -> None:
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    markdown = PACKET_MARKDOWN_PATH.read_text(encoding="utf-8")

    for evidence_path in packet["source_evidence"] + packet["technical_evidence"]:
        assert (REPO_ROOT / evidence_path).exists(), evidence_path
    for capture in packet["captures"]:
        assert Path(capture["path"]).name in markdown
    for capture in packet["diagnostic_art_evidence"]:
        assert Path(capture["path"]).name in markdown

    assert "awaiting_named_human_reviewers_not_approved" in markdown
    assert "not approved as photoreal" in markdown
    assert "Procedural terrain and geography" in markdown
    assert "M9 may pass only after" in markdown
