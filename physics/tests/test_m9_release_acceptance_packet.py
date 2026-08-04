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
    assert packet["candidate"]["capture_repeat_passed"] is True
    assert packet["candidate"]["capture_repeat_exact_current"] is False
    assert packet["candidate"]["hlod_repeat_exact_current"] is True
    shipping = manifest["local_preflight_evidence"][
        "exact_current_dirty_shipping_preflight"
    ]
    historical_performance = shipping["metal_full_reach_performance"]
    current_performance_evidence = json.loads(
        (
            REPO_ROOT
            / packet["candidate"]["latest_completed_shipping_performance_report"]
        ).read_text(encoding="utf-8")
    )
    current_performance = current_performance_evidence["shipping_performance"]
    assert packet["candidate"]["exact_current_performance_report"] is None
    assert packet["candidate"]["exact_current_performance_configuration"] is None
    assert packet["candidate"]["exact_current_performance_passed"] is False
    assert (
        packet["candidate"]["exact_current_performance_canonical_isolation_passed"]
        is False
    )
    assert packet["candidate"]["exact_current_performance_promotion_eligible"] is False
    assert packet["candidate"]["latest_completed_shipping_performance_passed"] is True
    assert packet["candidate"]["exact_current_performance_p95_ms"] is None
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
    assert generation["v269_v270_capture_repeat_exact_current"] is False
    assert generation["hlod_repeat_exact_current"] is True
    assert generation["hlod_actor_count"] == 28
    assert generation["hlod_actors_built"] == 28
    assert generation["hlod_repeat_modified_and_saved_actor_count"] == 0
    assert generation["post_lumen_pair_m4_exact_current"] is True
    assert generation["post_lumen_pair_m4_report"] == (
        "unreal/Saved/Automation/M9V586ContinuousThighKneeM4/index.json"
    )
    assert generation["post_lumen_pair_m4_report_sha256"] == (
        "1841471e5fc6afd08dd64a7fc060965d5467773b27c7c43dc1f04428b55220d9"
    )
    assert generation["post_lumen_pair_m5_exact_current"] is True
    assert generation["post_lumen_pair_m5_report"] == (
        "unreal/Saved/Automation/M9V585ContinuousThighKneeM5Renderer/index.json"
    )
    assert generation["post_lumen_pair_m5_report_sha256"] == (
        "51397b43654535f8975a5a8d5c2a41631951ce1f862270fa1f87ea6869797f52"
    )
    assert generation["post_hlod_m7_exact_current"] is True
    assert generation["post_hlod_m7_report"] == (
        "unreal/Saved/Automation/M9V587ContinuousThighKneeM7Renderer/index.json"
    )
    assert generation["post_hlod_m7_report_sha256"] == (
        "e8e9ac2f69672d335f6ccfbb863f81f098f6ca09198288039456f85b758066b2"
    )
    assert generation["m8_content_lock_exact_current"] is True
    assert generation["post_hlod_m8_report"] == (
        "unreal/Saved/Automation/M9V588ContinuousThighKneeM8Renderer/index.json"
    )
    assert generation["post_hlod_m8_report_sha256"] == (
        "ba624deb2333bf7eec5e8de791d049a98705a3bb9f82b61c5d4a3bfe38308bfe"
    )
    assert generation["python_tests_exact_current"] is True
    assert generation[
        "python_tests_exact_current_pending_after_continuous_thigh_knee_v1"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_organic_bank_mosaic_v2"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_raft_interior_water_transmission_v1"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_identity_fitted_helmet_v1"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_unpadded_pfd_v1"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_seated_waist_hip_v1"
    ] is False
    assert generation["python_tests_report"] == (
        "physics/reports/m9/m9_v589_continuous_thigh_knee_full_matrix.xml"
    )
    assert generation["python_tests_report_sha256"] == (
        "1a4b08866846e32c64b90c94666f323208fe44a54d87ed9d40fdca7e0708cf25"
    )
    assert generation["python_tests_passed"] == 1148
    assert generation["python_tests_failed"] == 0
    assert generation["python_tests_failed_expected"] == 0
    assert generation["python_tests_failed_unexpected"] == 0
    assert generation["python_tests_skipped_expected"] == 3
    assert generation["python_tests_duration_seconds"] == 428.19
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
    assert generation[
        "python_tests_exact_current_pending_after_raft_crew_foam_occlusion_v1"
    ] is False
    assert generation[
        "python_tests_exact_current_pending_after_seat_side_paddle_v1"
    ] is False
    m9_automation = manifest["local_preflight_evidence"]["m9_editor_automation"]
    assert m9_automation["exact_current"] is True
    assert m9_automation["pending_after_continuous_thigh_knee_v1"] is False
    assert m9_automation["pending_after_opaque_profile_hips_v1"] is False
    assert m9_automation["pending_after_raft_crew_foam_occlusion_v1"] is False
    assert m9_automation["pending_after_seat_side_paddle_v1"] is False
    assert m9_automation[
        "pending_after_raft_interior_water_transmission_v1"
    ] is False
    assert m9_automation["pending_after_identity_fitted_helmet_v1"] is False
    assert m9_automation["pending_after_unpadded_pfd_v1"] is False
    assert m9_automation["pending_after_seated_waist_hip_v1"] is False
    assert m9_automation["pending_after_soft_rounded_pfd_v1"] is False
    assert m9_automation["pending_after_organic_bank_mosaic_v2"] is False
    assert m9_automation["report_path"] == (
        "unreal/Saved/Automation/M9V590ContinuousThighKneeReconciledM9/index.json"
    )
    assert m9_automation["report_sha256"] == (
        "1b24c9f577f4c3018466f0472a208d96eb73d7574ae2cced7c6f07f861a4055c"
    )
    assert m9_automation["confirmation_report_path"] == (
        "unreal/Saved/Automation/M9V591ContinuousThighKneeExactM9/index.json"
    )
    assert m9_automation["confirmation_report_sha256"] == (
        "2768e42c42f5753ffd619800ab0d765bd78d6116ba634030da4c12719009e6d7"
    )
    confirmation_report = REPO_ROOT / m9_automation["confirmation_report_path"]
    assert hashlib.sha256(confirmation_report.read_bytes()).hexdigest() == (
        m9_automation["confirmation_report_sha256"]
    )
    assert m9_automation["confirmation_report_path"] in packet["technical_evidence"]
    assert m9_automation["confirmation_passed"] is True
    assert packet["candidate"]["exact_current_m4"] == (
        "4/4 result entries passed (M9V586ContinuousThighKneeM4)"
    )
    assert packet["candidate"]["exact_current_m5"] == (
        "5/5 result entries passed renderer-enabled "
        "(M9V585ContinuousThighKneeM5Renderer)"
    )
    assert packet["candidate"]["exact_current_m7"] == (
        "4/4 result entries passed offscreen-rendered (M9V587ContinuousThighKneeM7Renderer)"
    )
    assert packet["candidate"]["exact_current_m8"] == (
        "4/4 passed offscreen-rendered (M9V588ContinuousThighKneeM8Renderer)"
    )
    assert packet["candidate"]["exact_current_m9"] == (
        "6/6 passed after continuous thigh/knee V1 evidence reconciliation "
        "(M9V590ContinuousThighKneeReconciledM9)"
    )
    assert packet["candidate"]["exact_current_python_tests"] == (
        "1148 passed, 3 expected skips, 0 failed in 428.19 seconds "
        "(M9V589ContinuousThighKnee)"
    )
    assert generation["python_tests_exact_current"] is True
    assert generation[
        "python_tests_exact_current_pending_after_opaque_profile_hips_v1"
    ] is False
    assert packet["candidate"]["exact_current_source_true_wrap_capture"] == (
        "docs/environment-captures/south_fork_full_reach/"
        "m9_raft_interior_water_transmission_v1_review.json"
    )
    assert packet["candidate"]["exact_current_presentation_capture"] == (
        "docs/environment-captures/south_fork_full_reach/"
        "m9_continuous_thigh_knee_v1_review.json"
    )
    assert packet["candidate"]["exact_current_water_surface_report"] == (
        "unreal/Saved/Automation/M9V490WaterFloorP2/index.json"
    )
    assert packet["candidate"]["exact_current_water_surface_report_sha256"] == (
        "adf7ccd953f7f41bf7dd374f6b7223d227e537d057502ddb71cab22fed77ab0b"
    )
    exact_current_native_reports = {
        "exact_current_m4_report": (
            "unreal/Saved/Automation/M9V586ContinuousThighKneeM4/index.json",
            "1841471e5fc6afd08dd64a7fc060965d5467773b27c7c43dc1f04428b55220d9",
        ),
        "exact_current_m5_report": (
            "unreal/Saved/Automation/M9V585ContinuousThighKneeM5Renderer/index.json",
            "51397b43654535f8975a5a8d5c2a41631951ce1f862270fa1f87ea6869797f52",
        ),
        "exact_current_m7_report": (
            "unreal/Saved/Automation/M9V587ContinuousThighKneeM7Renderer/index.json",
            "e8e9ac2f69672d335f6ccfbb863f81f098f6ca09198288039456f85b758066b2",
        ),
        "exact_current_m8_report": (
            "unreal/Saved/Automation/M9V588ContinuousThighKneeM8Renderer/index.json",
            "ba624deb2333bf7eec5e8de791d049a98705a3bb9f82b61c5d4a3bfe38308bfe",
        ),
    }
    for report_key, (report_path, report_sha256) in exact_current_native_reports.items():
        assert packet["candidate"][report_key] == report_path
        assert packet["candidate"][f"{report_key}_sha256"] == report_sha256
        report = REPO_ROOT / report_path
        assert hashlib.sha256(report.read_bytes()).hexdigest() == report_sha256
        assert report_path in packet["technical_evidence"]
    python_report_path = (
        "physics/reports/m9/m9_v589_continuous_thigh_knee_full_matrix.xml"
    )
    python_report_sha256 = (
        "1a4b08866846e32c64b90c94666f323208fe44a54d87ed9d40fdca7e0708cf25"
    )
    assert packet["candidate"]["exact_current_python_report"] == python_report_path
    assert packet["candidate"]["exact_current_python_report_sha256"] == (
        python_report_sha256
    )
    assert hashlib.sha256((REPO_ROOT / python_report_path).read_bytes()).hexdigest() == (
        python_report_sha256
    )
    assert python_report_path in packet["technical_evidence"]
    m9_report_path = (
        "unreal/Saved/Automation/M9V590ContinuousThighKneeReconciledM9/index.json"
    )
    m9_report_sha256 = (
        "1b24c9f577f4c3018466f0472a208d96eb73d7574ae2cced7c6f07f861a4055c"
    )
    assert packet["candidate"]["exact_current_m9_report"] == m9_report_path
    assert packet["candidate"]["exact_current_m9_report_sha256"] == m9_report_sha256
    assert hashlib.sha256((REPO_ROOT / m9_report_path).read_bytes()).hexdigest() == (
        m9_report_sha256
    )
    assert m9_report_path in packet["technical_evidence"]
    assert packet["candidate"]["exact_current_water_surface_report"] in packet[
        "technical_evidence"
    ]
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
        current_hash = hashlib.sha256((REPO_ROOT / source_path).read_bytes()).hexdigest()
        if source_path.endswith("RaftSimCaptureCommand.cpp"):
            # The V10 ledger intentionally retains its immutable historical
            # capture-harness hash. Paddle V1 adds only a mirrored diagnostic
            # camera to that file and records the replacement hash in its own
            # exact-current review.
            assert len(expected_hash) == 64
            assert current_hash == (
                "4aef3ebf7a7444f3da33261e00d6fb7477551cf8ce1d11cb2037e26c7b5dac2e"
            )
        elif source_path.endswith("test_flexible_raft_visual_upgrade.py"):
            # V10 preserves the historical source-test hash; raft-interior
            # transmission, PFD, seated-hip, and upright-boot reviews extend
            # this test and record their replacements in exact-current evidence.
            assert len(expected_hash) == 64
            assert current_hash == (
                "2a91eab9c02a267ed8557ab7abc11d1476b2f417e8bb8891ae386805c9e353d8"
            )
        else:
            assert current_hash == expected_hash
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

    foam_occlusion_review_path = (
        REPO_ROOT / packet["candidate"]["raft_crew_foam_occlusion_visual_review"]
    )
    foam_occlusion_review = json.loads(
        foam_occlusion_review_path.read_text(encoding="utf-8")
    )
    assert packet["candidate"]["raft_crew_foam_occlusion"] == (
        "v1_technical_candidate_retained_external_art_and_guide_review_open"
    )
    assert foam_occlusion_review["status"] == (
        "technical_candidate_retained_external_art_and_guide_review_open"
    )
    assert foam_occlusion_review["passed"] is False
    assert foam_occlusion_review["technical_candidate_passed"] is True
    assert foam_occlusion_review["photoreal_acceptance_passed"] is False
    assert foam_occlusion_review["promotion_allowed"] is False
    assert foam_occlusion_review["implementation"][
        "base_water_hydraulic_foam_intensity"
    ] == 0.0
    assert foam_occlusion_review["implementation"]["collision_changed"] is False
    assert foam_occlusion_review["implementation"]["water_samples_changed"] is False
    assert foam_occlusion_review["implementation"]["physics_forces_changed"] is False
    foam_replacement_hashes = {
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp": "146bbad2c6a5c7c99dfe5fa7d423a4c122544ba2041aa80f30c9ae28b4122fcf",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimWaterSurfaceActor.h": "31feee3d61bb80e70535c9d011bef843a5a9e7b910a9ec38e38989eab5ac22f0",
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorSouthForkWaterPresentation.cpp": "ec22984153d4be835e4a6469b88df9e6486fb2d2dd73719261f66bd9a2582822",
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorMaterialsBase.cpp": "b53081b42d81fc6c60d19c379303f937cd05169e8b4b7893136769b2efd701a9",
        "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/RaftSimWaterSurfaceTest.cpp": "2c988a3c2823de09ccdea19674f131c334f13bb25def42c11189a4e47352ef39",
        "unreal/Content/RaftSim/Materials/MPC_RaftSim_RaftFoamOcclusion.uasset": "f87d48b55199399adbf56f955592095ce5e4107bea0527f408f9a872d666cd37",
        "unreal/Content/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverFieldFoamCandidate.uasset": "01a084b508cebade6abc05320697fc4968bedfc8bd853020f7e4826527852e11",
        "unreal/Content/RaftSim/Environment/SouthForkFullReach/Water/Materials/MI_RaftSim_SouthForkProductionWater.uasset": "797336a64b97fce1b40facffb68ea642acb4add98989dd65ec5a04004ee63ff8",
    }
    for source_path, expected_hash in foam_occlusion_review[
        "implementation_sha256"
    ].items():
        current_hash = hashlib.sha256((REPO_ROOT / source_path).read_bytes()).hexdigest()
        if source_path in foam_replacement_hashes:
            assert len(expected_hash) == 64
            assert current_hash == foam_replacement_hashes[source_path]
        else:
            assert current_hash == expected_hash
    for renderer_key in ("contact_port", "wrap_hero"):
        renderer_evidence = foam_occlusion_review["renderer_evidence"][renderer_key]
        for artifact_key in ("capture", "log"):
            artifact = REPO_ROOT / renderer_evidence[artifact_key]
            assert hashlib.sha256(artifact.read_bytes()).hexdigest() == (
                renderer_evidence[f"{artifact_key}_sha256"]
            )
        assert _png_size(REPO_ROOT / renderer_evidence["capture"]) == (1280, 720)
    focused_report = REPO_ROOT / foam_occlusion_review["validation"][
        "native_automation_report"
    ]
    assert hashlib.sha256(focused_report.read_bytes()).hexdigest() == (
        foam_occlusion_review["validation"]["native_automation_report_sha256"]
    )
    assert foam_occlusion_review["reviewers"]["named_water_vfx_art_reviewer"] is None
    assert foam_occlusion_review["reviewers"]["qualified_south_fork_guide"] is None
    assert foam_occlusion_review["reviewers"]["art_approval"] is False
    assert foam_occlusion_review["reviewers"]["guide_approval"] is False
    assert str(foam_occlusion_review_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]
    assert generation["raft_crew_foam_occlusion_visual_review_sha256"] == (
        hashlib.sha256(foam_occlusion_review_path.read_bytes()).hexdigest()
    )
    assert generation["raft_crew_foam_occlusion_water_surface_report"] == str(
        focused_report.relative_to(REPO_ROOT)
    )
    assert generation["raft_crew_foam_occlusion_water_surface_report_sha256"] == (
        foam_occlusion_review["validation"]["native_automation_report_sha256"]
    )
    assert generation["raft_crew_foam_occlusion_water_surface_tests_passed"] == 1
    assert generation["raft_crew_foam_occlusion_water_surface_exact_current"] is False
    assert generation["raft_crew_foam_occlusion_physics_or_gameplay_changes"] is False
    assert generation["raft_crew_foam_occlusion_photoreal_art_accepted"] is False

    paddle_review_path = (
        REPO_ROOT
        / packet["candidate"]["seat_side_paddle_orientation_visual_review"]
    )
    paddle_review = json.loads(paddle_review_path.read_text(encoding="utf-8"))
    assert packet["candidate"]["seat_side_paddle_orientation"] == (
        "v1_technical_candidate_retained_external_animation_art_and_guide_review_open"
    )
    assert paddle_review["status"] == (
        "technical_candidate_retained_external_animation_art_and_guide_review_open"
    )
    assert paddle_review["passed"] is False
    assert paddle_review["technical_candidate_passed"] is True
    assert paddle_review["photoreal_acceptance_passed"] is False
    assert paddle_review["promotion_allowed"] is False
    assert paddle_review["implementation"]["ordinary_t_grip_side"] == "inboard"
    assert paddle_review["implementation"]["ordinary_blade_side"] == "outboard"
    assert paddle_review["implementation"]["port_lower_shaft_hand"] == "left"
    assert paddle_review["implementation"]["starboard_lower_shaft_hand"] == "right"
    assert paddle_review["implementation"]["high_side_body_translation_changed"] is False
    assert paddle_review["implementation"]["high_side_local_blade_z_max_cm"] <= -10.0
    assert paddle_review["implementation"]["collision_changed"] is False
    assert paddle_review["implementation"]["water_samples_changed"] is False
    assert paddle_review["implementation"]["physics_forces_changed"] is False
    assert paddle_review["implementation"]["crew_mass_changed"] is False
    helmet_fit_replacement_hashes = {
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCrewAvatarActor.cpp": "4a642f4be9d9c0e8306bc6a7b06e2f8f3fdbb48ae03946806e690da342346b8c",
        "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/RaftSimM5ProductionQualityTest.cpp": "890d1b5ebaf2b72a7594350886b0b019afc61458f078a730453028fb30670728",
    }
    for source_path, expected_hash in paddle_review["implementation_sha256"].items():
        current_hash = hashlib.sha256((REPO_ROOT / source_path).read_bytes()).hexdigest()
        if source_path in helmet_fit_replacement_hashes:
            # Paddle V1 retains its immutable historical implementation
            # hashes. Helmet Fit V1 adds headgear assertions, and unpadded PFD
            # V1 updates the bounded vest-height contract; their reviews record
            # replacements without rewriting the paddle ledger.
            assert len(expected_hash) == 64
            assert current_hash == helmet_fit_replacement_hashes[source_path]
        else:
            assert current_hash == expected_hash
    for renderer_key in ("contact_port", "contact_starboard"):
        renderer_evidence = paddle_review["renderer_evidence"][renderer_key]
        for artifact_key in ("capture", "log"):
            artifact = REPO_ROOT / renderer_evidence[artifact_key]
            assert hashlib.sha256(artifact.read_bytes()).hexdigest() == (
                renderer_evidence[f"{artifact_key}_sha256"]
            )
        assert _png_size(REPO_ROOT / renderer_evidence["capture"]) == (1280, 720)
    for report_key in ("m4", "m5", "m7", "m8", "m9"):
        report = REPO_ROOT / paddle_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            paddle_review["validation"][f"{report_key}_report_sha256"]
        )
    paddle_python_report = REPO_ROOT / paddle_review["validation"]["python_report"]
    assert hashlib.sha256(paddle_python_report.read_bytes()).hexdigest() == (
        paddle_review["validation"]["python_report_sha256"]
    )
    assert paddle_review["reviewers"]["named_character_animation_art_reviewer"] is None
    assert paddle_review["reviewers"]["qualified_south_fork_guide"] is None
    assert paddle_review["reviewers"]["art_approval"] is False
    assert paddle_review["reviewers"]["guide_approval"] is False
    assert str(paddle_review_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]
    paddle_review_sha256 = hashlib.sha256(paddle_review_path.read_bytes()).hexdigest()
    assert packet["candidate"][
        "seat_side_paddle_orientation_visual_review_sha256"
    ] == paddle_review_sha256
    assert generation["seat_side_paddle_visual_review"] == str(
        paddle_review_path.relative_to(REPO_ROOT)
    )
    assert generation["seat_side_paddle_visual_review_sha256"] == paddle_review_sha256
    assert generation["seat_side_paddle_m5_report"] == (
        paddle_review["validation"]["m5_report"]
    )
    assert generation["seat_side_paddle_m5_report_sha256"] == (
        paddle_review["validation"]["m5_report_sha256"]
    )
    assert generation["seat_side_paddle_m5_leaf_tests_passed"] == 5
    assert generation["seat_side_paddle_physics_or_gameplay_changes"] is False
    assert generation["seat_side_paddle_photoreal_art_accepted"] is False

    interior_review_path = (
        REPO_ROOT
        / packet["candidate"]["raft_interior_water_transmission_visual_review"]
    )
    interior_review = json.loads(interior_review_path.read_text(encoding="utf-8"))
    assert packet["candidate"]["raft_interior_water_transmission"] == (
        "v1_technical_candidate_retained_external_water_vfx_art_and_guide_review_open"
    )
    assert interior_review["status"] == (
        "technical_candidate_retained_external_water_vfx_art_and_guide_review_open"
    )
    assert interior_review["passed"] is False
    assert interior_review["technical_candidate_passed"] is True
    assert interior_review["photoreal_acceptance_passed"] is False
    assert interior_review["promotion_allowed"] is False
    assert interior_review["implementation"]["shared_water_parent_modified"] is False
    assert interior_review["implementation"]["raft_interior_surface_opacity_scale"] == 0.0
    assert interior_review["implementation"]["raft_interior_behind_water_scale"] == 1.0
    assert interior_review["implementation"]["aperture_tracks_live_raft_transform"] is True
    assert interior_review["implementation"]["collision_changed"] is False
    assert interior_review["implementation"]["water_samples_changed"] is False
    assert interior_review["implementation"]["physics_forces_changed"] is False
    assert interior_review["implementation"]["raft_mass_or_buoyancy_changed"] is False
    interior_replacement_hashes = {
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp": "146bbad2c6a5c7c99dfe5fa7d423a4c122544ba2041aa80f30c9ae28b4122fcf",
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorSouthForkWaterPresentation.cpp": "ec22984153d4be835e4a6469b88df9e6486fb2d2dd73719261f66bd9a2582822",
    }
    for source_path, expected_hash in interior_review["implementation_sha256"].items():
        assert hashlib.sha256((REPO_ROOT / source_path).read_bytes()).hexdigest() == (
            interior_replacement_hashes.get(source_path, expected_hash)
        )
    for renderer_key in ("contact_port", "contact_starboard"):
        renderer_evidence = interior_review["renderer_evidence"][renderer_key]
        for artifact_key in ("capture", "log"):
            artifact = REPO_ROOT / renderer_evidence[artifact_key]
            assert hashlib.sha256(artifact.read_bytes()).hexdigest() == renderer_evidence[f"{artifact_key}_sha256"]
        assert _png_size(REPO_ROOT / renderer_evidence["capture"]) == (1280, 720)
    for report_key in ("water_surface", "m4", "m5", "m7", "m8", "m9"):
        report = REPO_ROOT / interior_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == interior_review["validation"][f"{report_key}_report_sha256"]
    interior_python_report = REPO_ROOT / interior_review["validation"]["python_report"]
    assert hashlib.sha256(interior_python_report.read_bytes()).hexdigest() == interior_review["validation"]["python_report_sha256"]
    assert interior_review["reviewers"]["named_water_vfx_art_reviewer"] is None
    assert interior_review["reviewers"]["qualified_south_fork_guide"] is None
    assert interior_review["reviewers"]["product_owner"] is None
    assert str(interior_review_path.relative_to(REPO_ROOT)) in packet["technical_evidence"]
    interior_review_sha256 = hashlib.sha256(interior_review_path.read_bytes()).hexdigest()
    assert packet["candidate"]["raft_interior_water_transmission_visual_review_sha256"] == interior_review_sha256
    assert generation["raft_interior_water_transmission_visual_review"] == str(interior_review_path.relative_to(REPO_ROOT))
    assert generation["raft_interior_water_transmission_visual_review_sha256"] == interior_review_sha256
    assert generation["raft_interior_water_surface_tests_passed"] == 1
    assert generation["raft_interior_water_surface_exact_current"] is True
    assert generation["raft_interior_water_physics_or_gameplay_changes"] is False
    assert generation["raft_interior_water_photoreal_art_accepted"] is False

    helmet_review_path = (
        REPO_ROOT / packet["candidate"]["identity_fitted_helmet_visual_review"]
    )
    helmet_review = json.loads(helmet_review_path.read_text(encoding="utf-8"))
    assert packet["candidate"]["identity_fitted_helmet"] == (
        "v1_technical_candidate_retained_external_character_art_and_safety_review_open"
    )
    assert helmet_review["status"] == (
        "technical_candidate_retained_external_character_art_and_safety_review_open"
    )
    assert helmet_review["passed"] is False
    assert helmet_review["technical_candidate_passed"] is True
    assert helmet_review["photoreal_acceptance_passed"] is False
    assert helmet_review["promotion_allowed"] is False
    assert helmet_review["implementation"]["runtime_alignment_basis"] == (
        "rendered_face_world_forward_and_up"
    )
    assert helmet_review["implementation"]["skull_center_lift_cm"] == 9.5
    assert helmet_review["implementation"]["helmet_mesh_or_material_changed"] is False
    assert helmet_review["implementation"]["collision_changed"] is False
    assert helmet_review["implementation"]["physics_forces_changed"] is False
    metrics = helmet_review["runtime_roster_metrics"]
    assert metrics["captured_character_count"] == 5
    assert metrics["maximum_head_error_cm"] <= 1.0
    assert metrics["minimum_forward_alignment"] >= 0.98
    assert metrics["minimum_fit_scale"] >= 0.899
    assert metrics["maximum_fit_scale"] <= 1.021
    roster_report = REPO_ROOT / metrics["source_report"]
    assert hashlib.sha256(roster_report.read_bytes()).hexdigest() == (
        metrics["source_report_sha256"]
    )
    waist_hip_replacement_hashes = {
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCrewAvatarActor.h": "b73256c4d0219c907e6506d7e7cbaefa09f3d52dad9bfe29fd43e63ab392925e",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCrewAvatarActor.cpp": "4a642f4be9d9c0e8306bc6a7b06e2f8f3fdbb48ae03946806e690da342346b8c",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimMetaHumanCrewVisualActor.h": "4196f93d70c8518f357309a135989506995ad412657816d88de58ee26109a799",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimMetaHumanCrewVisualActor.cpp": "571495eea1b26cc5e0b62ca2681bdfc78fdd6288563539e3e37e2ff6b36585c7",
        "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/RaftSimM5ProductionQualityTest.cpp": "890d1b5ebaf2b72a7594350886b0b019afc61458f078a730453028fb30670728",
        "unreal/Scripts/capture_metahuman_production_roster.py": "6295f9720059d2b92df4309be12fb47feed40501a1c0cba9ccb8182bd2239385",
        "physics/tests/test_cc0_production_characters.py": "62050991368b32e7b6a43274cacb4a19493a5ac54e238c2b5f54ed39249dc5d6",
    }
    for source_path, expected_hash in helmet_review["implementation_sha256"].items():
        current_hash = hashlib.sha256((REPO_ROOT / source_path).read_bytes()).hexdigest()
        if source_path in waist_hip_replacement_hashes:
            # Helmet V1 keeps its immutable review hash. The later unpadded-PFD
            # and seated-waist repairs record replacements without rewriting
            # that historical ledger.
            assert len(expected_hash) == 64
            assert current_hash == waist_hip_replacement_hashes[source_path]
        else:
            assert current_hash == expected_hash
    for renderer_evidence in helmet_review["renderer_evidence"].values():
        if not isinstance(renderer_evidence, dict):
            continue
        capture = REPO_ROOT / renderer_evidence["capture"]
        assert hashlib.sha256(capture.read_bytes()).hexdigest() == (
            renderer_evidence["capture_sha256"]
        )
        assert _png_size(capture) == (1536, 1024)
    for report_key in ("m4", "m5", "m7", "m8"):
        report = REPO_ROOT / helmet_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            helmet_review["validation"][f"{report_key}_report_sha256"]
        )
    helmet_python_report = REPO_ROOT / helmet_review["validation"][
        "full_python_report"
    ]
    assert hashlib.sha256(helmet_python_report.read_bytes()).hexdigest() == (
        helmet_review["validation"]["full_python_report_sha256"]
    )
    assert helmet_review["reviewers"]["named_character_art_reviewer"] is None
    assert helmet_review["reviewers"]["qualified_whitewater_safety_reviewer"] is None
    assert helmet_review["reviewers"]["art_approval"] is False
    assert helmet_review["reviewers"]["safety_approval"] is False
    assert str(helmet_review_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]
    helmet_review_sha256 = hashlib.sha256(helmet_review_path.read_bytes()).hexdigest()
    assert packet["candidate"]["identity_fitted_helmet_visual_review_sha256"] == (
        helmet_review_sha256
    )
    assert generation["identity_fitted_helmet_visual_review"] == str(
        helmet_review_path.relative_to(REPO_ROOT)
    )
    assert generation["identity_fitted_helmet_visual_review_sha256"] == (
        helmet_review_sha256
    )
    assert generation["identity_fitted_helmet_minimum_forward_alignment"] >= 0.98
    assert generation["identity_fitted_helmet_physics_or_gameplay_changes"] is False
    assert generation["identity_fitted_helmet_photoreal_art_accepted"] is False
    assert generation["identity_fitted_helmet_safety_accepted"] is False

    waist_hip_review_path = (
        REPO_ROOT / packet["candidate"]["seated_waist_hip_visual_review"]
    )
    waist_hip_review = json.loads(waist_hip_review_path.read_text(encoding="utf-8"))
    assert packet["candidate"]["seated_waist_hip_silhouette"] == (
        "v2_technical_candidate_retained_external_character_art_review_open"
    )
    assert waist_hip_review["status"] == (
        "technical_candidate_retained_external_character_art_review_open"
    )
    assert waist_hip_review["passed"] is False
    assert waist_hip_review["technical_candidate_passed"] is True
    assert waist_hip_review["photoreal_acceptance_passed"] is False
    assert waist_hip_review["promotion_allowed"] is False
    assert waist_hip_review["runtime_boundary"]["collision"] == "disabled"
    assert waist_hip_review["runtime_boundary"]["production_visual_only"] is True
    assert waist_hip_review["runtime_boundary"]["animation_changed"] is False
    assert waist_hip_review["runtime_boundary"]["crew_mass_changed"] is False
    assert waist_hip_review["runtime_boundary"]["physics_forces_changed"] is False
    waist_metrics = waist_hip_review["runtime_roster_metrics"]
    assert waist_metrics["captured_character_count"] == 5
    assert waist_metrics["characters_with_visible_waist_hip_silhouette"] == 5
    assert waist_metrics["maximum_hip_center_error_cm"] == 0.0
    assert waist_metrics["minimum_extent_cm"][0] >= 14.0
    assert waist_metrics["minimum_extent_cm"][1] >= 21.0
    assert waist_metrics["minimum_extent_cm"][2] >= 13.8
    waist_roster = REPO_ROOT / waist_metrics["source_report"]
    assert hashlib.sha256(waist_roster.read_bytes()).hexdigest() == (
        waist_metrics["source_report_sha256"]
    )
    upright_boot_replacement_hashes = {
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCrewAvatarActor.h": "b73256c4d0219c907e6506d7e7cbaefa09f3d52dad9bfe29fd43e63ab392925e",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCrewAvatarActor.cpp": "4a642f4be9d9c0e8306bc6a7b06e2f8f3fdbb48ae03946806e690da342346b8c",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimMetaHumanCrewVisualActor.h": "4196f93d70c8518f357309a135989506995ad412657816d88de58ee26109a799",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimMetaHumanCrewVisualActor.cpp": "571495eea1b26cc5e0b62ca2681bdfc78fdd6288563539e3e37e2ff6b36585c7",
        "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/RaftSimM5ProductionQualityTest.cpp": "890d1b5ebaf2b72a7594350886b0b019afc61458f078a730453028fb30670728",
        "unreal/Scripts/capture_metahuman_production_roster.py": "6295f9720059d2b92df4309be12fb47feed40501a1c0cba9ccb8182bd2239385",
        "physics/tests/test_cc0_production_characters.py": "62050991368b32e7b6a43274cacb4a19493a5ac54e238c2b5f54ed39249dc5d6",
    }
    for source_path, expected_hash in waist_hip_review[
        "implementation_sha256"
    ].items():
        current_hash = hashlib.sha256((REPO_ROOT / source_path).read_bytes()).hexdigest()
        if source_path in upright_boot_replacement_hashes:
            assert len(expected_hash) == 64
            assert current_hash == upright_boot_replacement_hashes[source_path]
        else:
            assert current_hash == expected_hash
    for renderer_evidence in waist_hip_review["renderer_evidence"].values():
        if not isinstance(renderer_evidence, dict):
            continue
        capture = REPO_ROOT / renderer_evidence["capture"]
        assert hashlib.sha256(capture.read_bytes()).hexdigest() == (
            renderer_evidence["capture_sha256"]
        )
        assert _png_size(capture) == (1536, 1024)
    for report_key in ("m4", "m5", "m7", "m8"):
        report = REPO_ROOT / waist_hip_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            waist_hip_review["validation"][f"{report_key}_report_sha256"]
        )
    waist_python_report = (
        REPO_ROOT / waist_hip_review["validation"]["full_python_report"]
    )
    assert hashlib.sha256(waist_python_report.read_bytes()).hexdigest() == (
        waist_hip_review["validation"]["full_python_report_sha256"]
    )
    assert waist_hip_review["reviewers"]["named_character_art_reviewer"] is None
    assert waist_hip_review["reviewers"]["art_approval"] is False
    assert str(waist_hip_review_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]
    waist_review_sha256 = hashlib.sha256(waist_hip_review_path.read_bytes()).hexdigest()
    assert packet["candidate"]["seated_waist_hip_visual_review_sha256"] == (
        waist_review_sha256
    )
    assert generation["seated_waist_hip_visual_review"] == str(
        waist_hip_review_path.relative_to(REPO_ROOT)
    )
    assert generation["seated_waist_hip_visual_review_sha256"] == waist_review_sha256
    assert generation["seated_waist_hip_roster_count"] == 5
    assert generation["seated_waist_hip_maximum_center_error_cm"] == 0.0
    assert generation["seated_waist_hip_collision_enabled"] is False
    assert generation["seated_waist_hip_physics_or_gameplay_changes"] is False
    assert generation["seated_waist_hip_photoreal_art_accepted"] is False

    pfd_review_path = (
        REPO_ROOT
        / packet["candidate"]["production_whitewater_pfd_visual_review"]
    )
    pfd_review = json.loads(pfd_review_path.read_text(encoding="utf-8"))
    assert pfd_review["status"] == (
        "technical_candidate_retained_external_character_art_and_safety_review_open"
    )
    assert pfd_review["technical_candidate_passed"] is True
    assert pfd_review["photoreal_acceptance_passed"] is False
    assert pfd_review["promotion_allowed"] is False
    assert pfd_review["runtime_asset"]["authored_lod0_triangles"] == 25_320
    assert pfd_review["runtime_asset"]["nanite_fallback_triangles"] == 2_260
    assert pfd_review["runtime_asset"]["material_slot_count"] == 5
    assert pfd_review["construction"]["shoulder_foam_pads"] == 0
    assert pfd_review["construction"]["shoulder_webbing_runs"] == 2
    assert pfd_review["construction"]["shoulder_webbing_width_cm"] == 2.0
    assert pfd_review["construction"]["shoulder_webbing_thickness_cm"] == 0.18
    assert pfd_review["runtime_roster_metrics"]["characters_using_production_pfd"] == 5
    assert pfd_review["runtime_roster_metrics"]["maximum_runtime_torso_error_cm"] == 0.0
    assert pfd_review["soft_geometry"]["flat_exterior_foam_faces"] == 0
    assert pfd_review["soft_geometry"]["outline_corner_rounding_passes"] == 4
    assert pfd_review["soft_geometry"]["front_panel_crown_depth_cm"] == 1.45
    assert pfd_review["soft_geometry"]["back_panel_crown_depth_cm"] == 1.65
    assert pfd_review["implementation"]["flat_exterior_foam_faces_after"] == 0
    assert pfd_review["implementation"]["shoulder_foam_pads_after"] == 0
    assert pfd_review["implementation"]["collision_changed"] is False
    assert pfd_review["implementation"]["physics_forces_changed"] is False
    assert pfd_review["reviewers"]["named_character_art_reviewer"] is None
    assert pfd_review["reviewers"]["qualified_whitewater_safety_reviewer"] is None
    assert pfd_review["reviewers"]["art_approval"] is False
    assert pfd_review["reviewers"]["safety_approval"] is False
    for path_key, hash_key in (
        ("generator", "generator_sha256"),
        ("importer", "importer_sha256"),
        ("manifest", "manifest_sha256"),
        ("fbx", "fbx_sha256"),
        ("blend", "blend_sha256"),
    ):
        source = REPO_ROOT / pfd_review["source"][path_key]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == (
            pfd_review["source"][hash_key]
        )
    runtime_asset = REPO_ROOT / pfd_review["runtime_asset"]["uasset"]
    assert hashlib.sha256(runtime_asset.read_bytes()).hexdigest() == (
        pfd_review["runtime_asset"]["uasset_sha256"]
    )
    for evidence in pfd_review["renderer_evidence"].values():
        if not isinstance(evidence, dict):
            continue
        capture = REPO_ROOT / evidence["capture"]
        assert hashlib.sha256(capture.read_bytes()).hexdigest() == (
            evidence["capture_sha256"]
        )
        assert _png_size(capture) == (1536, 1024)
    for report_key in ("m4", "m5", "m7", "m8"):
        report = REPO_ROOT / pfd_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            pfd_review["validation"][f"{report_key}_report_sha256"]
        )
    pfd_python_report = REPO_ROOT / pfd_review["validation"]["full_python_report"]
    assert hashlib.sha256(pfd_python_report.read_bytes()).hexdigest() == (
        pfd_review["validation"]["full_python_report_sha256"]
    )
    pfd_m9_report = REPO_ROOT / pfd_review["validation"]["m9_report"]
    assert hashlib.sha256(pfd_m9_report.read_bytes()).hexdigest() == (
        pfd_review["validation"]["m9_report_sha256"]
    )
    assert str(pfd_review_path.relative_to(REPO_ROOT)) in packet["technical_evidence"]
    pfd_review_sha256 = hashlib.sha256(pfd_review_path.read_bytes()).hexdigest()
    assert packet["candidate"]["production_whitewater_pfd_visual_review_sha256"] == (
        pfd_review_sha256
    )
    generation = manifest["local_preflight_evidence"]["full_reach_editor_generation"]
    assert generation["production_whitewater_pfd_source_fbx_sha256"] == (
        pfd_review["source"]["fbx_sha256"]
    )
    assert generation["production_whitewater_pfd_visual_review_sha256"] == (
        pfd_review_sha256
    )
    assert generation["production_whitewater_pfd_authored_lod0_triangles"] == 25_320
    assert generation["production_whitewater_pfd_nanite_fallback_triangles"] == 2_260
    assert generation["production_whitewater_pfd_maximum_torso_error_cm"] == 0.0
    assert generation["production_whitewater_pfd_m5_tests_passed"] == 4
    assert generation["production_whitewater_pfd_focused_tests_passed"] == 27
    assert generation["production_whitewater_pfd_shoulder_foam_pads"] == 0
    assert generation["production_whitewater_pfd_shoulder_webbing_runs"] == 2
    assert generation["production_whitewater_pfd_flat_exterior_foam_faces"] == 0
    assert generation["production_whitewater_pfd_outline_corner_rounding_passes"] == 4
    assert generation["production_whitewater_pfd_photoreal_art_accepted"] is False

    organic_review_path = (
        REPO_ROOT / packet["candidate"]["organic_bank_mosaic_visual_review"]
    )
    organic_review = json.loads(organic_review_path.read_text(encoding="utf-8"))
    assert packet["candidate"]["organic_bank_mosaic"] == (
        "v2_technical_candidate_retained_external_environment_art_and_"
        "geospatial_review_open"
    )
    assert organic_review["status"] == (
        "technical_candidate_retained_external_environment_art_and_"
        "geospatial_review_open"
    )
    assert organic_review["passed"] is False
    assert organic_review["technical_candidate_passed"] is True
    assert organic_review["photoreal_acceptance_passed"] is False
    assert organic_review["promotion_allowed"] is False
    implementation = organic_review["implementation"]
    assert implementation["grass_blades_per_tuft"] == 52
    assert implementation["low_forb_leaves_per_tuft"] == 10
    assert implementation["ground_cover_instances"] == 220_759
    assert implementation["near_corridor_foliage_instances"] == 82_609
    assert implementation["collision_enabled"] is False
    assert implementation["navigation_changed"] is False
    assert implementation["terrain_geometry_changed"] is False
    assert implementation["water_geometry_changed"] is False
    assert implementation["hydraulics_changed"] is False
    for path_key, hash_key in (
        ("ground_cover_generator", "ground_cover_generator_sha256"),
        ("understory_generator", "understory_generator_sha256"),
        ("native_contract_test", "native_contract_test_sha256"),
        ("python_contract_test", "python_contract_test_sha256"),
    ):
        source = REPO_ROOT / organic_review["source"][path_key]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == (
            organic_review["source"][hash_key]
        )
    for evidence in organic_review["renderer_evidence"].values():
        if not isinstance(evidence, dict):
            continue
        capture = REPO_ROOT / evidence["capture"]
        assert hashlib.sha256(capture.read_bytes()).hexdigest() == (
            evidence["capture_sha256"]
        )
        assert _png_size(capture) == (1280, 720)
    for report_key in ("m4", "m5", "m7", "m8"):
        report = REPO_ROOT / organic_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            organic_review["validation"][f"{report_key}_report_sha256"]
        )
    assert organic_review["reviewers"]["named_environment_art_reviewer"] is None
    assert organic_review["reviewers"]["named_geospatial_reviewer"] is None
    assert organic_review["reviewers"]["named_south_fork_guide_reviewer"] is None
    assert organic_review["reviewers"]["environment_art_approval"] is False
    assert organic_review["reviewers"]["geospatial_approval"] is False
    assert organic_review["reviewers"]["guide_approval"] is False
    assert str(organic_review_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]
    organic_review_sha256 = hashlib.sha256(organic_review_path.read_bytes()).hexdigest()
    assert packet["candidate"]["organic_bank_mosaic_visual_review_sha256"] == (
        organic_review_sha256
    )
    assert generation["organic_bank_mosaic_visual_review"] == str(
        organic_review_path.relative_to(REPO_ROOT)
    )
    assert generation["organic_bank_mosaic_visual_review_sha256"] == (
        organic_review_sha256
    )
    assert generation["organic_bank_mosaic_ground_cover_instances"] == 220_759
    assert generation["organic_bank_mosaic_near_corridor_foliage_instances"] == 82_609
    assert generation["organic_bank_mosaic_collision_enabled"] is False
    assert generation["organic_bank_mosaic_physics_or_gameplay_changes"] is False
    assert generation["organic_bank_mosaic_photoreal_art_accepted"] is False

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
    assert hashlib.sha256(raft_v42_source.read_bytes()).hexdigest() != (
        raft_v42_review["source"]["runtime_deformer_sha256"]
    ), "the retained V42 review must remain explicitly historical"
    for path_key, hash_key in (
        ("material_authoring", "material_authoring_sha256"),
        ("raft_tube_material", "raft_tube_material_sha256"),
        ("raft_floor_material", "raft_floor_material_sha256"),
    ):
        current_hash = hashlib.sha256(
            (REPO_ROOT / raft_v42_review["source"][path_key]).read_bytes()
        ).hexdigest()
        assert current_hash != raft_v42_review["source"][hash_key]
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
    assert generation["d4_aware_production_raft_m5_exact_current"] is False
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
    assert boulder_asset_path.is_file()
    assert boulder_material_path.is_file()
    assert len(boulder_review["runtime_asset"]["uasset_sha256"]) == 64
    assert len(boulder_review["runtime_asset"]["material_uasset_sha256"]) == 64
    boulder_import_report = REPO_ROOT / boulder_review["runtime_asset"]["import_report"]
    assert boulder_import_report.is_file()
    assert len(boulder_review["runtime_asset"]["import_report_sha256"]) == 64
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
    assert generation["production_river_boulder_m5_exact_current"] is False
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
    assert foam_source.is_file()
    assert foam_provenance.is_file()
    assert foam_generator.is_file()
    assert len(water_review["source"]["source_texture_sha256"]) == 64
    assert len(water_review["source"]["provenance_sha256"]) == 64
    assert len(water_review["source"]["generator_sha256"]) == 64
    foam_texture_asset = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
        "T_RaftSim_SouthForkWater_FoamLace.uasset"
    )
    broad_water_material = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Materials/M_RaftSim_PhotorealRiverWater.uasset"
    )
    assert foam_texture_asset.is_file()
    assert broad_water_material.is_file()
    assert len(
        water_review["runtime_assets"]["foam_lace_texture_uasset_sha256"]
    ) == 64
    assert len(
        water_review["runtime_assets"]["broad_water_material_uasset_sha256"]
    ) == 64
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
    assert vfx_runtime_source.is_file()
    assert len(vfx_review["scope"]["runtime_source_sha256"]) == 64
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
    # sources owned by the exposure review remain historical after later deltas.
    assert len(exposure_review["scope"]["capture_command_source_sha256"]) == 64
    for source_key, hash_key in (
        ("runtime_camera_source", "runtime_camera_source_sha256"),
        ("m7_camera_contract_source", "m7_camera_contract_source_sha256"),
    ):
        source_path = REPO_ROOT / exposure_review["scope"][source_key]
        assert source_path.is_file()
        assert len(exposure_review["scope"][hash_key]) == 64
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
    assert packet["candidate"]["production_river_boot"] == (
        "upright_fitted_v1_technical_candidate_retained_"
        "external_character_art_and_guide_review_open"
    )
    assert boot_review["status"] == (
        "technical_candidate_retained_external_character_art_and_guide_review_open"
    )
    assert boot_review["passed"] is False
    assert boot_review["technical_candidate_passed"] is True
    assert boot_review["photoreal_acceptance_passed"] is False
    assert boot_review["promotion_allowed"] is False
    for path_key, hash_key in (
        ("generator", "generator_sha256"),
        ("importer", "importer_sha256"),
        ("material_builder", "material_builder_sha256"),
        ("manifest", "manifest_sha256"),
        ("blend", "blend_sha256"),
        ("fbx", "fbx_sha256"),
    ):
        source_path = REPO_ROOT / boot_review["source"][path_key]
        assert source_path.is_file()
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
    assert boot_asset.is_file()
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
    assert upper_material.is_file()
    assert rubber_material.is_file()
    assert hashlib.sha256(upper_material.read_bytes()).hexdigest() == (
        boot_review["materials"]["upper_asset_sha256"]
    )
    assert hashlib.sha256(rubber_material.read_bytes()).hexdigest() == (
        boot_review["materials"]["rubber_asset_sha256"]
    )
    boot_material_report = REPO_ROOT / boot_review["materials"]["report"]
    assert boot_material_report.is_file()
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
    closed_grip_replacement_hashes = {
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCrewAvatarActor.cpp": "4a642f4be9d9c0e8306bc6a7b06e2f8f3fdbb48ae03946806e690da342346b8c",
        "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCrewAvatarActor.h": "b73256c4d0219c907e6506d7e7cbaefa09f3d52dad9bfe29fd43e63ab392925e",
        "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/RaftSimM5ProductionQualityTest.cpp": "890d1b5ebaf2b72a7594350886b0b019afc61458f078a730453028fb30670728",
        "unreal/Scripts/capture_metahuman_production_roster.py": "6295f9720059d2b92df4309be12fb47feed40501a1c0cba9ccb8182bd2239385",
        "physics/tests/test_cc0_production_characters.py": "62050991368b32e7b6a43274cacb4a19493a5ac54e238c2b5f54ed39249dc5d6",
    }
    for path_key, hash_key in (
        ("crew_runtime_source", "crew_runtime_source_sha256"),
        ("crew_runtime_header", "crew_runtime_header_sha256"),
        ("native_test_source", "native_test_source_sha256"),
        ("capture_source", "capture_source_sha256"),
        ("source_contract_test", "source_contract_test_sha256"),
    ):
        integration_path = REPO_ROOT / boot_review["integration"][path_key]
        assert integration_path.is_file()
        current_hash = hashlib.sha256(integration_path.read_bytes()).hexdigest()
        integration_relpath = boot_review["integration"][path_key]
        if integration_relpath in closed_grip_replacement_hashes:
            assert len(boot_review["integration"][hash_key]) == 64
            assert current_hash == closed_grip_replacement_hashes[integration_relpath]
        else:
            assert current_hash == boot_review["integration"][hash_key]
    assert boot_review["integration"]["production_roster_count"] == 5
    assert boot_review["integration"]["production_boot_instances"] == 10
    assert boot_review["integration"]["fitted_upright_boot_instances"] == 10
    assert boot_review["integration"]["toe_axis"] == "+X"
    assert boot_review["integration"]["cuff_axis"] == "+Z"
    assert boot_review["integration"]["presentation_scale"] == [0.88, 0.92, 0.68]
    assert boot_review["integration"]["sole_contact_preserved_from_source_minimum_z"] is True
    assert boot_review["integration"]["production_boot_collision_enabled"] is False
    assert boot_review["integration"]["physics_or_rescue_changes"] is False
    boot_roster_report = REPO_ROOT / boot_review["runtime_roster_metrics"]["report"]
    assert hashlib.sha256(boot_roster_report.read_bytes()).hexdigest() == (
        boot_review["runtime_roster_metrics"]["report_sha256"]
    )
    assert boot_review["runtime_roster_metrics"]["captured_character_count"] == 5
    assert boot_review["runtime_roster_metrics"]["fitted_upright_boot_instance_count"] == 10
    assert boot_review["runtime_roster_metrics"]["minimum_toe_forward_alignment"] >= 0.999
    assert boot_review["runtime_roster_metrics"]["minimum_cuff_up_alignment"] >= 0.999
    boot_import_report = REPO_ROOT / boot_review["import_audit"]["report"]
    assert boot_import_report.is_file()
    assert hashlib.sha256(boot_import_report.read_bytes()).hexdigest() == (
        boot_review["import_audit"]["report_sha256"]
    )
    for report_key in ("m4", "m5", "m7", "m8"):
        report = REPO_ROOT / boot_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            boot_review["validation"][f"{report_key}_report_sha256"]
        )
    for renderer_evidence in boot_review["renderer_evidence"].values():
        if not isinstance(renderer_evidence, dict):
            continue
        boot_capture = REPO_ROOT / renderer_evidence["capture"]
        assert hashlib.sha256(boot_capture.read_bytes()).hexdigest() == (
            renderer_evidence["capture_sha256"]
        )
        assert _png_size(boot_capture) == (1536, 1024)
    assert boot_review["human_approved"] is False
    assert boot_review["marketing_approved"] is False
    assert generation["production_river_boot_source_fbx_sha256"] == (
        boot_review["source"]["fbx_sha256"]
    )
    assert generation["production_river_boot_authored_lod0_triangles"] == 9708
    assert generation["production_river_boot_nanite_fallback_triangles"] == 1704
    assert generation["production_river_boot_instance_count"] == 10
    assert generation["production_river_boot_fitted_upright_instance_count"] == 10
    assert generation["production_river_boot_presentation_scale"] == [0.88, 0.92, 0.68]
    assert generation["production_river_boot_minimum_cuff_up_alignment"] >= 0.999
    assert generation["production_river_boot_minimum_toe_forward_alignment"] >= 0.999
    assert generation["production_river_boot_sole_contact_preserved"] is True
    assert generation["production_river_boot_upper_material_sha256"] == (
        boot_review["materials"]["upper_asset_sha256"]
    )
    assert generation["production_river_boot_rubber_material_sha256"] == (
        boot_review["materials"]["rubber_asset_sha256"]
    )
    assert generation["production_river_boot_material_audit_sha256"] == (
        boot_review["materials"]["report_sha256"]
    )
    assert generation["production_river_boot_m5_tests_passed"] == 5
    assert generation["production_river_boot_m5_exact_current"] is True
    assert generation["production_river_boot_photoreal_art_accepted"] is False
    boot_review_sha256 = hashlib.sha256(boot_review_path.read_bytes()).hexdigest()
    assert packet["candidate"]["production_river_boot_visual_review_sha256"] == (
        boot_review_sha256
    )
    assert generation["production_river_boot_visual_review_sha256"] == (
        boot_review_sha256
    )
    assert str(boot_review_path.relative_to(REPO_ROOT)) in packet["technical_evidence"]

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
        assert runtime_path.is_file()
        assert len(grip_review["replacement_boundary"][hash_key]) == 64
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
    assert generation["palm_centered_paddle_grip_m5_exact_current"] is False
    assert generation["palm_centered_paddle_grip_m5_report"] == (
        grip_review["automation"]["report"]
    )
    assert generation["palm_centered_paddle_grip_m5_report_sha256"] == (
        grip_review["automation"]["report_sha256"]
    )
    assert generation["palm_centered_paddle_grip_physics_or_gameplay_changes"] is False
    assert generation["palm_centered_paddle_grip_photoreal_art_accepted"] is False

    closed_grip_review_path = (
        REPO_ROOT / packet["candidate"]["closed_finger_paddle_grip_visual_review"]
    )
    closed_grip_review = json.loads(
        closed_grip_review_path.read_text(encoding="utf-8")
    )
    assert packet["candidate"]["closed_finger_paddle_grip"] == (
        "v1_technical_candidate_retained_external_character_art_and_guide_review_open"
    )
    assert closed_grip_review["schema"] == (
        "raftsim.m9.closed_finger_paddle_grip_review.v1"
    )
    assert closed_grip_review["status"] == (
        "technical_candidate_retained_external_character_art_and_guide_review_open"
    )
    assert closed_grip_review["passed"] is False
    assert closed_grip_review["technical_candidate_passed"] is True
    assert closed_grip_review["photoreal_acceptance_passed"] is False
    assert closed_grip_review["promotion_allowed"] is False
    visible_shoulders_replacement_hashes = {
        "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/RaftSimM5ProductionQualityTest.cpp": "890d1b5ebaf2b72a7594350886b0b019afc61458f078a730453028fb30670728",
        "unreal/Scripts/capture_metahuman_production_roster.py": "6295f9720059d2b92df4309be12fb47feed40501a1c0cba9ccb8182bd2239385",
        "physics/tests/test_cc0_production_characters.py": "62050991368b32e7b6a43274cacb4a19493a5ac54e238c2b5f54ed39249dc5d6",
    }
    for path_key, hash_key in (
        ("production_adapter", "production_adapter_sha256"),
        ("production_adapter_header", "production_adapter_header_sha256"),
        ("native_test_source", "native_test_source_sha256"),
        ("capture_source", "capture_source_sha256"),
        ("source_contract_test", "source_contract_test_sha256"),
    ):
        source_path = REPO_ROOT / closed_grip_review["replacement_boundary"][path_key]
        assert source_path.is_file()
        current_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        source_relpath = closed_grip_review["replacement_boundary"][path_key]
        if source_relpath in visible_shoulders_replacement_hashes:
            assert len(closed_grip_review["replacement_boundary"][hash_key]) == 64
            assert current_hash == visible_shoulders_replacement_hashes[source_relpath]
        else:
            assert current_hash == closed_grip_review["replacement_boundary"][hash_key]
    closed_impl = closed_grip_review["implementation"]
    assert closed_impl["production_roster_count"] == 5
    assert closed_impl["visible_paddle_hands"] == 10
    assert closed_impl["explicit_non_thumb_finger_chains"] == 40
    assert closed_impl["finger_arc_cumulative_degrees"] == [50.0, 68.0, 52.0]
    assert closed_impl["finger_arc_radii_cm"] == [3.2, 2.65, 2.35]
    assert closed_impl["maximum_allowed_runtime_palm_anchor_error_cm"] == 0.25
    assert closed_impl["maximum_allowed_runtime_distal_contact_error_cm"] == 0.25
    assert closed_impl["measured_maximum_runtime_palm_anchor_error_cm"] <= 0.25
    assert closed_impl["measured_maximum_runtime_distal_contact_error_cm"] <= 0.25
    assert closed_impl["thumb_contact_is_visually_reviewed_not_metric_gated"] is True
    assert closed_grip_review["replacement_boundary"]["physics_or_gameplay_changes"] is False
    closed_roster_path = (
        REPO_ROOT / closed_grip_review["runtime_roster_metrics"]["report"]
    )
    assert hashlib.sha256(closed_roster_path.read_bytes()).hexdigest() == (
        closed_grip_review["runtime_roster_metrics"]["report_sha256"]
    )
    closed_roster = json.loads(closed_roster_path.read_text(encoding="utf-8-sig"))
    assert closed_roster["status"] == "capture_complete"
    assert closed_roster["captured_character_count"] == 5
    assert len(closed_roster["characters"]) == 5
    assert all(
        character["runtime_articulated_paddle_grip"] is True
        for character in closed_roster["characters"]
    )
    assert max(
        character["runtime_paddle_grip_anchor_error_cm"]
        for character in closed_roster["characters"]
    ) <= 0.25
    assert max(
        character["runtime_paddle_grip_contact_error_cm"]
        for character in closed_roster["characters"]
    ) <= 0.25
    for renderer_evidence in closed_grip_review["renderer_evidence"].values():
        if not isinstance(renderer_evidence, dict):
            continue
        capture = REPO_ROOT / renderer_evidence["capture"]
        assert hashlib.sha256(capture.read_bytes()).hexdigest() == (
            renderer_evidence["capture_sha256"]
        )
        assert _png_size(capture) == (1536, 1024)
    for report_key in ("m4", "m5", "m7", "m8"):
        report = REPO_ROOT / closed_grip_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            closed_grip_review["validation"][f"{report_key}_report_sha256"]
        )
    for report_key in (
        "full_python",
        "m9_reconciled",
        "m9_exact_confirmation",
    ):
        report = REPO_ROOT / closed_grip_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            closed_grip_review["validation"][f"{report_key}_report_sha256"]
        )
    closed_review_sha256 = hashlib.sha256(closed_grip_review_path.read_bytes()).hexdigest()
    assert packet["candidate"]["closed_finger_paddle_grip_visual_review_sha256"] == (
        closed_review_sha256
    )
    assert generation["closed_finger_paddle_grip_visual_review_sha256"] == (
        closed_review_sha256
    )
    assert generation["closed_finger_paddle_grip_runtime_source_sha256"] == (
        closed_grip_review["replacement_boundary"]["production_adapter_sha256"]
    )
    assert generation["closed_finger_paddle_grip_runtime_header_sha256"] == (
        closed_grip_review["replacement_boundary"]["production_adapter_header_sha256"]
    )
    assert generation["closed_finger_paddle_grip_roster_count"] == 5
    assert generation["closed_finger_paddle_grip_hand_count"] == 10
    assert generation["closed_finger_paddle_grip_distal_contact_joint_count"] == 40
    assert generation["closed_finger_paddle_grip_maximum_anchor_error_cm"] <= 0.25
    assert generation["closed_finger_paddle_grip_maximum_contact_error_cm"] <= 0.25
    assert generation["closed_finger_paddle_grip_m5_tests_passed"] == 5
    assert generation["closed_finger_paddle_grip_m5_exact_current"] is True
    assert generation["closed_finger_paddle_grip_physics_or_gameplay_changes"] is False
    assert generation["closed_finger_paddle_grip_photoreal_art_accepted"] is False
    assert str(closed_grip_review_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]
    assert str(closed_roster_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]

    shoulder_review_path = (
        REPO_ROOT / packet["candidate"]["visible_shoulders_visual_review"]
    )
    shoulder_review = json.loads(shoulder_review_path.read_text(encoding="utf-8"))
    assert packet["candidate"]["visible_shoulders"] == (
        "v1_technical_candidate_retained_external_character_art_and_guide_review_open"
    )
    assert shoulder_review["schema"] == "raftsim.m9.visible_shoulders_review.v1"
    assert shoulder_review["status"] == (
        "technical_candidate_retained_external_character_art_and_guide_review_open"
    )
    assert shoulder_review["passed"] is False
    assert shoulder_review["technical_candidate_passed"] is True
    assert shoulder_review["photoreal_acceptance_passed"] is False
    assert shoulder_review["promotion_allowed"] is False
    shoulder_impl = shoulder_review["implementation"]
    assert shoulder_impl["production_roster_count"] == 5
    assert shoulder_impl["visible_sleeves_per_avatar"] == 2
    assert shoulder_impl["reference_sleeve_radius_cm"] == 5.2
    assert shoulder_impl["shoulder_to_elbow_fraction"] == 1.0
    assert shoulder_impl["pfd_shoulder_foam_added"] is False
    assert shoulder_impl["physics_or_gameplay_changes"] is False
    for source_relpath, expected_hash in shoulder_review[
        "implementation_sha256"
    ].items():
        assert hashlib.sha256((REPO_ROOT / source_relpath).read_bytes()).hexdigest() == (
            expected_hash
        )
    shoulder_roster_path = REPO_ROOT / shoulder_review["runtime_roster_metrics"][
        "report"
    ]
    assert hashlib.sha256(shoulder_roster_path.read_bytes()).hexdigest() == (
        shoulder_review["runtime_roster_metrics"]["report_sha256"]
    )
    shoulder_roster = json.loads(
        shoulder_roster_path.read_text(encoding="utf-8-sig")
    )
    assert shoulder_roster["status"] == "capture_complete"
    assert shoulder_roster["captured_character_count"] == 5
    assert len(shoulder_roster["characters"]) == 5
    assert all(
        character["runtime_shoulder_silhouette"] is True
        for character in shoulder_roster["characters"]
    )
    assert min(
        character["runtime_shoulder_sleeve_minimum_extent_cm"][0]
        for character in shoulder_roster["characters"]
    ) >= 4.7
    assert max(
        character["runtime_shoulder_sleeve_anchor_error_cm"]
        for character in shoulder_roster["characters"]
    ) <= 0.25
    for renderer_evidence in shoulder_review["renderer_evidence"].values():
        if not isinstance(renderer_evidence, dict):
            continue
        capture = REPO_ROOT / renderer_evidence["capture"]
        assert hashlib.sha256(capture.read_bytes()).hexdigest() == (
            renderer_evidence["capture_sha256"]
        )
        assert _png_size(capture) == (1536, 1024)
    for report_key in ("m4", "m5", "m7", "m8"):
        report = REPO_ROOT / shoulder_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            shoulder_review["validation"][f"{report_key}_report_sha256"]
        )
    shoulder_review_sha256 = hashlib.sha256(shoulder_review_path.read_bytes()).hexdigest()
    assert packet["candidate"]["visible_shoulders_visual_review_sha256"] == (
        shoulder_review_sha256
    )
    assert generation["visible_shoulders_visual_review_sha256"] == (
        shoulder_review_sha256
    )
    assert generation["visible_shoulders_runtime_source_sha256"] == (
        shoulder_review["implementation_sha256"][
            "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCrewAvatarActor.cpp"
        ]
    )
    assert generation["visible_shoulders_runtime_header_sha256"] == (
        shoulder_review["implementation_sha256"][
            "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCrewAvatarActor.h"
        ]
    )
    assert generation["visible_shoulders_roster_count"] == 5
    assert generation["visible_shoulders_sleeve_count"] == 10
    assert generation["visible_shoulders_minimum_radius_cm"] >= 4.7
    assert generation["visible_shoulders_minimum_half_length_cm"] >= 5.6
    assert generation["visible_shoulders_maximum_anchor_error_cm"] <= 0.25
    assert generation["visible_shoulders_m5_tests_passed"] == 5
    assert generation["visible_shoulders_m5_exact_current"] is True
    assert generation["visible_shoulders_pfd_shoulder_foam_pads_added"] == 0
    assert generation["visible_shoulders_physics_or_gameplay_changes"] is False
    assert generation["visible_shoulders_photoreal_art_accepted"] is False
    assert str(shoulder_review_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]
    assert str(shoulder_roster_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]

    hip_review_path = (
        REPO_ROOT / packet["candidate"]["opaque_profile_hips_visual_review"]
    )
    hip_review = json.loads(hip_review_path.read_text(encoding="utf-8"))
    assert packet["candidate"]["opaque_profile_hips"] == (
        "v1_technical_candidate_retained_external_character_art_and_guide_review_open"
    )
    assert hip_review["schema"] == "raftsim.m9.opaque_profile_hips_review.v1"
    assert hip_review["status"] == (
        "technical_candidate_retained_external_character_art_and_guide_review_open"
    )
    assert hip_review["passed"] is False
    assert hip_review["technical_candidate_passed"] is True
    assert hip_review["photoreal_acceptance_passed"] is False
    assert hip_review["promotion_allowed"] is False
    hip_impl = hip_review["implementation"]
    assert hip_impl["production_roster_count"] == 5
    assert hip_impl["opaque_hip_bridges_per_avatar"] == 2
    assert hip_impl["reference_bridge_radius_cm"] == 6.8
    assert hip_impl["bridge_start_fraction"] == -0.15
    assert hip_impl["bridge_end_fraction"] == 0.58
    assert hip_impl["material_blend_mode"] == "BLEND_Opaque"
    assert hip_impl["physics_or_gameplay_changes"] is False
    for source_relpath, expected_hash in hip_review["implementation_sha256"].items():
        assert hashlib.sha256((REPO_ROOT / source_relpath).read_bytes()).hexdigest() == (
            expected_hash
        )
    hip_roster_path = REPO_ROOT / hip_review["runtime_roster_metrics"]["report"]
    assert hashlib.sha256(hip_roster_path.read_bytes()).hexdigest() == (
        hip_review["runtime_roster_metrics"]["report_sha256"]
    )
    hip_roster = json.loads(hip_roster_path.read_text(encoding="utf-8-sig"))
    assert hip_roster["status"] == "capture_complete"
    assert hip_roster["captured_character_count"] == 5
    assert len(hip_roster["characters"]) == 5
    assert all(
        character["runtime_waist_hip_silhouette"] is True
        for character in hip_roster["characters"]
    )
    assert all(
        character["runtime_waist_hip_material_opaque"] is True
        for character in hip_roster["characters"]
    )
    assert min(
        character["runtime_hip_thigh_bridge_minimum_extent_cm"][0]
        for character in hip_roster["characters"]
    ) >= 6.2
    assert max(
        character["runtime_hip_thigh_bridge_coverage_error_cm"]
        for character in hip_roster["characters"]
    ) <= 0.25
    for renderer_evidence in hip_review["renderer_evidence"].values():
        if not isinstance(renderer_evidence, dict):
            continue
        capture = REPO_ROOT / renderer_evidence["capture"]
        assert hashlib.sha256(capture.read_bytes()).hexdigest() == (
            renderer_evidence["capture_sha256"]
        )
        assert _png_size(capture) == (1536, 1024)
    for report_key in ("m4", "m5", "m7", "m8"):
        report = REPO_ROOT / hip_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            hip_review["validation"][f"{report_key}_report_sha256"]
        )
    for report_key in ("full_python", "m9"):
        report = REPO_ROOT / hip_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            hip_review["validation"][f"{report_key}_report_sha256"]
        )
    hip_review_sha256 = hashlib.sha256(hip_review_path.read_bytes()).hexdigest()
    assert packet["candidate"]["opaque_profile_hips_visual_review_sha256"] == (
        hip_review_sha256
    )
    assert generation["opaque_profile_hips_visual_review_sha256"] == (
        hip_review_sha256
    )
    assert generation["opaque_profile_hips_runtime_source_sha256"] == (
        hip_review["implementation_sha256"][
            "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCrewAvatarActor.cpp"
        ]
    )
    assert generation["opaque_profile_hips_runtime_header_sha256"] == (
        hip_review["implementation_sha256"][
            "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCrewAvatarActor.h"
        ]
    )
    assert generation["opaque_profile_hips_roster_count"] == 5
    assert generation["opaque_profile_hips_bridge_count"] == 10
    assert generation["opaque_profile_hips_minimum_radius_cm"] >= 6.2
    assert generation["opaque_profile_hips_minimum_half_length_cm"] >= 9.5
    assert generation["opaque_profile_hips_maximum_centreline_error_cm"] <= 0.25
    assert generation["opaque_profile_hips_m5_tests_passed"] == 5
    assert generation["opaque_profile_hips_m5_exact_current"] is True
    assert generation["opaque_profile_hips_material_opaque"] is True
    assert generation["opaque_profile_hips_physics_or_gameplay_changes"] is False
    assert generation["opaque_profile_hips_photoreal_art_accepted"] is False
    assert str(hip_review_path.relative_to(REPO_ROOT)) in packet["technical_evidence"]
    assert str(hip_roster_path.relative_to(REPO_ROOT)) in packet["technical_evidence"]

    thigh_knee_review_path = (
        REPO_ROOT / packet["candidate"]["continuous_thigh_knee_visual_review"]
    )
    thigh_knee_review = json.loads(
        thigh_knee_review_path.read_text(encoding="utf-8")
    )
    assert packet["candidate"]["continuous_thigh_knee"] == (
        "v1_technical_candidate_retained_external_character_art_and_guide_review_open"
    )
    assert thigh_knee_review["schema"] == (
        "raftsim.m9.continuous_thigh_knee_review.v1"
    )
    assert thigh_knee_review["status"] == (
        "technical_candidate_retained_external_character_art_and_guide_review_open"
    )
    assert thigh_knee_review["passed"] is False
    assert thigh_knee_review["technical_candidate_passed"] is True
    assert thigh_knee_review["photoreal_acceptance_passed"] is False
    assert thigh_knee_review["promotion_allowed"] is False
    thigh_impl = thigh_knee_review["implementation"]
    assert thigh_impl["production_roster_count"] == 5
    assert thigh_impl["continuous_thighs_per_avatar"] == 2
    assert thigh_impl["reference_maximum_thigh_radius_cm"] == 8.0
    assert thigh_impl["bridge_start_fraction"] == -0.15
    assert thigh_impl["bridge_end_fraction"] == 1.06
    assert thigh_impl["material_blend_mode"] == "BLEND_Opaque"
    assert thigh_impl["physics_or_gameplay_changes"] is False
    for source_relpath, expected_hash in thigh_knee_review[
        "implementation_sha256"
    ].items():
        assert hashlib.sha256((REPO_ROOT / source_relpath).read_bytes()).hexdigest() == (
            expected_hash
        )
    thigh_roster_path = REPO_ROOT / thigh_knee_review["runtime_roster_metrics"][
        "report"
    ]
    assert hashlib.sha256(thigh_roster_path.read_bytes()).hexdigest() == (
        thigh_knee_review["runtime_roster_metrics"]["report_sha256"]
    )
    thigh_roster = json.loads(thigh_roster_path.read_text(encoding="utf-8-sig"))
    assert thigh_roster["status"] == "capture_complete"
    assert thigh_roster["captured_character_count"] == 5
    assert len(thigh_roster["characters"]) == 5
    assert all(
        character["runtime_thigh_knee_silhouette"] is True
        for character in thigh_roster["characters"]
    )
    assert min(
        character["runtime_hip_thigh_bridge_minimum_extent_cm"][0]
        for character in thigh_roster["characters"]
    ) >= 7.2
    assert max(
        character["runtime_thigh_knee_bridge_coverage_error_cm"]
        for character in thigh_roster["characters"]
    ) <= 0.25
    for renderer_evidence in thigh_knee_review["renderer_evidence"].values():
        if not isinstance(renderer_evidence, dict):
            continue
        capture = REPO_ROOT / renderer_evidence["capture"]
        assert hashlib.sha256(capture.read_bytes()).hexdigest() == (
            renderer_evidence["capture_sha256"]
        )
        assert _png_size(capture) == (1536, 1024)
    for report_key in ("m4", "m5", "m7", "m8", "full_python", "m9"):
        report = REPO_ROOT / thigh_knee_review["validation"][f"{report_key}_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == (
            thigh_knee_review["validation"][f"{report_key}_report_sha256"]
        )
    exact_report = REPO_ROOT / thigh_knee_review["validation"][
        "m9_exact_confirmation_report"
    ]
    assert hashlib.sha256(exact_report.read_bytes()).hexdigest() == (
        thigh_knee_review["validation"]["m9_exact_confirmation_report_sha256"]
    )
    thigh_review_sha256 = hashlib.sha256(thigh_knee_review_path.read_bytes()).hexdigest()
    assert packet["candidate"]["continuous_thigh_knee_visual_review_sha256"] == (
        thigh_review_sha256
    )
    assert generation["continuous_thigh_knee_visual_review_sha256"] == (
        thigh_review_sha256
    )
    assert generation["continuous_thigh_knee_runtime_source_sha256"] == (
        thigh_knee_review["implementation_sha256"][
            "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCrewAvatarActor.cpp"
        ]
    )
    assert generation["continuous_thigh_knee_runtime_header_sha256"] == (
        thigh_knee_review["implementation_sha256"][
            "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCrewAvatarActor.h"
        ]
    )
    assert generation["continuous_thigh_knee_roster_count"] == 5
    assert generation["continuous_thigh_knee_bridge_count"] == 10
    assert generation["continuous_thigh_knee_minimum_radius_cm"] >= 7.2
    assert generation["continuous_thigh_knee_minimum_half_length_cm"] >= 15.5
    assert generation["continuous_thigh_knee_maximum_centreline_error_cm"] <= 0.25
    assert generation["continuous_thigh_knee_m5_tests_passed"] == 5
    assert generation["continuous_thigh_knee_m5_exact_current"] is True
    assert generation["continuous_thigh_knee_material_opaque"] is True
    assert generation["continuous_thigh_knee_physics_or_gameplay_changes"] is False
    assert generation["continuous_thigh_knee_photoreal_art_accepted"] is False
    assert str(thigh_knee_review_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]
    assert str(thigh_roster_path.relative_to(REPO_ROOT)) in packet[
        "technical_evidence"
    ]

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
        assert source_path.is_file()
        assert len(lip_review["source"][hash_key]) == 64
    lip_material = REPO_ROOT / lip_review["runtime_asset"]["material"]
    assert lip_material.is_file()
    assert len(lip_review["runtime_asset"]["material_sha256"]) == 64
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
    assert generation["solver_breaking_water_lip_water_surface_exact_current"] is False
    assert generation["solver_breaking_water_lip_m4_exact_current"] is False
    assert generation["solver_breaking_water_lip_m5_exact_current"] is False
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
    assert any(
        capture["capture_id"] == "seat_side_paddle_v1_contact_port"
        for capture in packet["diagnostic_art_evidence"]
    )
    assert any(
        capture["capture_id"] == "seat_side_paddle_v1_contact_starboard"
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
    # Retained historical contact-water evidence. The exact-current presentation
    # review is the foam-occlusion V1 ledger asserted above.
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
        assert (REPO_ROOT / relative_path).is_file()
        assert len(expected_sha256) == 64

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
