# ruff: noqa: F405

from photoreal_test_support import *  # noqa: F401,F403


def test_production_flow_variant_intake_records_review_gated_flow_evidence():
    intake = json.loads(PRODUCTION_FLOW_VARIANT_INTAKE_PATH.read_text(encoding="utf-8"))
    visual_bands = json.loads(
        FLOW_VISUAL_BAND_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert intake["schema"] == "raftsim.production_flow_variant_intake.v1"
    assert (
        intake["status"]
        == "review_gated_flow_variant_intake_recorded_no_visual_or_gameplay_promotion"
    )
    assert (
        intake["flow_visual_band_manifest"]
        == "unreal/Content/RaftSim/Rendering/river_flow_visual_bands.json"
    )
    assert (
        visual_bands["production_flow_variant_intake"]
        == "physics/data/real_world/production_flow_variant_intake.json"
    )
    assert intake["policy"]["flow_controls_visuals_only_until_promoted"] is True
    assert intake["policy"]["must_not_hide_conservation_or_solver_failures"] is True
    assert (
        intake["policy"][
            "feature_forcing_requires_flow_response_and_manifest_recording"
        ]
        is True
    )
    assert (
        intake["policy"]["promotion_requires_capture_evidence_for_each_variant"] is True
    )

    assert intake["summary"] == {
        "river_count": 3,
        "variant_count": 10,
        "numeric_reference_variant_count": 6,
        "relative_only_variant_count": 4,
        "promoted_variant_count": 0,
        "capture_variant_count": 0,
        "per_river_variant_count": {
            "american_south_fork": 3,
            "colorado_river": 3,
            "pacuare": 4,
        },
    }
    assert {
        "hole_stickiness_or_washout",
        "wave_train_strength",
        "eddyline_shear",
        "swimmer_drift_speed",
        "rescue_readability",
    }.issubset(set(intake["visual_and_gameplay_parameters_controlled"]))
    assert {
        "selected_datetime_window",
        "guide_oarsman_or_local_review",
        "capture_variant_png_or_video",
        "solver_conservation_or_forcing_nonmasking_check",
        "final_promotion_decision",
    }.issubset(set(intake["required_fields_before_promotion"]))

    rivers = {river["river_id"]: river for river in intake["rivers"]}
    assert set(rivers) == {"american_south_fork", "colorado_river", "pacuare"}
    assert (
        rivers["american_south_fork"]["source_status"]
        == "short_cdec_release_window_attached_not_seasonal_authority"
    )
    assert (
        rivers["colorado_river"]["source_status"]
        == "usbr_daily_release_history_attached_subdaily_routing_and_oarsman_review_block_promotion"
    )
    assert (
        rivers["pacuare"]["source_status"]
        == "relative_rainfed_bands_only_numeric_station_records_blocked"
    )

    variants_by_river = {
        river_id: {variant["flow_band"]: variant for variant in river["variant_items"]}
        for river_id, river in rivers.items()
    }
    assert (
        variants_by_river["american_south_fork"]["low_runnable"][
            "reference_discharge_cfs"
        ]
        == 900.0
    )
    assert variants_by_river["american_south_fork"]["median_runnable"][
        "selected_or_candidate_windows"
    ]
    assert not variants_by_river["american_south_fork"]["high_runnable"][
        "selected_or_candidate_windows"
    ]
    assert (
        variants_by_river["colorado_river"]["low_release_planning"][
            "reference_discharge_cfs"
        ]
        == 8000.0
    )
    assert variants_by_river["colorado_river"]["high_release_planning"][
        "promotion_blockers"
    ]
    assert (
        variants_by_river["pacuare"]["flash_response_review_only"]["relative_flow"]
        == "rapid_rise"
    )
    assert (
        variants_by_river["pacuare"]["flash_response_review_only"][
            "reference_discharge_cfs"
        ]
        is None
    )
    for river in intake["rivers"]:
        for variant in river["variant_items"]:
            assert variant["promotion_decision"] == "not_promoted"
            assert variant["visual_parameters"]["foam_scale"] > 0.0
            assert variant["promotion_blockers"]


def test_photoreal_flow_variant_capture_plan_records_required_unreal_variants():
    plan = json.loads(FLOW_VARIANT_CAPTURE_PLAN_PATH.read_text(encoding="utf-8"))
    capture_manifest = json.loads(CAPTURE_MANIFEST_PATH.read_text(encoding="utf-8"))
    flow_variant_capture_manifest = json.loads(
        FLOW_VARIANT_CAPTURE_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert plan == build_photoreal_flow_variant_capture_plan(REPO_ROOT)
    assert plan["schema"] == "raftsim.unreal.photoreal_flow_variant_capture_plan.v1"
    assert (
        plan["status"]
        == "band_named_flow_variant_captures_available_not_lifelike_approved"
    )
    assert (
        plan["source_flow_visual_bands"]
        == "unreal/Content/RaftSim/Rendering/river_flow_visual_bands.json"
    )
    assert (
        plan["source_flow_variant_intake"]
        == "physics/data/real_world/production_flow_variant_intake.json"
    )
    assert (
        plan["source_capture_manifest"]
        == "docs/environment-captures/photoreal_river_previews/environment_capture_manifest.json"
    )
    assert (
        plan["policy"][
            "default_band_captures_do_not_cover_all_seasonal_release_or_rain_variants"
        ]
        is True
    )
    assert (
        plan["policy"]["band_named_capture_required_for_each_flow_variant_and_view"]
        is True
    )
    assert (
        plan["policy"][
            "flow_variant_visuals_must_not_hide_solver_conservation_or_forcing_failures"
        ]
        is True
    )
    assert plan["required_view_ids"] == [
        "guide_seat_downstream",
        "river_eye_downstream",
    ]
    assert plan["summary"] == {
        "river_count": 3,
        "variant_count": 10,
        "default_variant_count": 3,
        "required_capture_count": 20,
        "existing_band_named_capture_count": 20,
        "missing_band_named_capture_count": 0,
        "current_default_capture_count": 6,
        "fully_captured_variant_count": 10,
        "approved_variant_count": 0,
        "per_river_variant_count": {
            "american_south_fork": 3,
            "colorado_river": 3,
            "pacuare": 4,
        },
    }
    assert (
        "All required band-named guide-seat and river-eye flow-variant captures exist"
        in plan["current_decision"]
    )

    default_bands = {
        river["river_id"]: river["flow_band_id"]
        for river in capture_manifest["captures"]
    }
    manifest_by_variant = {
        (entry["river_id"], entry["flow_band_id"]): entry
        for entry in flow_variant_capture_manifest["captures"]
    }
    for river in plan["rivers"]:
        assert (
            river["capture_manifest_default_flow_band"]
            == default_bands[river["river_id"]]
        )
        assert river["variant_count"] == len(river["variants"])
        assert river["band_named_capture_count"] == 2 * river["variant_count"]
        assert river["current_default_capture_count"] == 2
        for variant in river["variants"]:
            manifest_entry = manifest_by_variant[
                (river["river_id"], variant["flow_band"])
            ]
            assert variant["promotion_decision"] == "not_promoted"
            assert variant["required_captures"]
            assert variant["visual_parameters"]["river_width_scale"] is not None
            assert variant["visual_parameters"]["water_level_offset_cm"] is not None
            assert variant["hydraulic_feature_expectation"]
            assert variant["status"] == "band_named_capture_set_available_not_approved"
            assert all(
                "Band-named guide-seat and river-eye Unreal captures are missing"
                not in blocker
                for blocker in variant["promotion_blockers"]
            )
            assert len(variant["required_captures"]) == 2
            if variant["is_default_preview_band"]:
                assert variant["flow_band"] == default_bands[river["river_id"]]
                assert all(
                    capture["current_default_capture_exists"] is True
                    for capture in variant["required_captures"]
                )
            else:
                assert all(
                    capture["current_default_capture"] is None
                    for capture in variant["required_captures"]
                )

            for capture in variant["required_captures"]:
                assert capture["status"] == "band_named_capture_attached"
                assert capture["exists"] is True
                assert (REPO_ROOT / capture["expected_capture"]).exists()
                assert capture["expected_capture"].startswith(
                    "docs/environment-captures/photoreal_river_previews/flow_variants/"
                )
                assert variant["flow_band"] in capture["expected_capture"]
                assert river["river_id"] in capture["expected_capture"]
                assert (
                    "Capture this exact river/flow/view combination"
                    in capture["review_requirement"]
                )
            assert (
                manifest_entry["guide_seat_capture"]
                == variant["required_captures"][0]["expected_capture"]
            )
            assert (
                manifest_entry["river_eye_capture"]
                == variant["required_captures"][1]["expected_capture"]
            )
            assert (
                manifest_entry["status"]
                == "captured_band_named_flow_variant_preview_renders"
            )


def test_flow_variant_capture_manifest_records_unreal_outputs():
    manifest = json.loads(
        FLOW_VARIANT_CAPTURE_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert (
        manifest["schema"]
        == "raftsim.unreal.environment_flow_variant_capture_manifest.v1"
    )
    assert (
        manifest["status"]
        == "all_band_named_flow_variant_previews_captured_not_lifelike_approved"
    )
    assert len(manifest["captures"]) == 10
    assert {entry["river_id"] for entry in manifest["captures"]} == {
        "american_south_fork",
        "colorado_river",
        "pacuare",
    }

    png_paths = []
    for entry in manifest["captures"]:
        assert entry["map_package"].startswith(
            "/Game/RaftSim/Maps/EnvironmentPreviews/FlowVariants/"
        )
        # Preview maps are regenerable diagnostics and are no longer versioned
        # (docs/generated-artifact-retention-policy.md, July 17 revision); the
        # manifest remains the authoritative record of the generated package.
        assert entry["map_package"].endswith(("_low", "_median", "_high", "_flood", "_drought")) or "/" in entry["map_package"]
        assert entry["status"] == "captured_band_named_flow_variant_preview_renders"
        assert entry["flow_visual_width_scale"] > 0.0
        assert entry["flow_visual_foam_scale"] > 0.0
        assert entry["flow_visual_wet_bank_scale"] > 0.0
        assert entry["flow_visual_current_cue_scale"] > 0.0
        assert entry["source_terrain_macro_amplitude_cm"] > 0.0
        assert entry["source_terrain_local_relief_amplitude_cm"] > 0.0
        assert 0.0 < entry["source_terrain_seam_feather_uv"] < 0.1
        assert 0.0 < entry["source_terrain_normal_softening_blend"] < 0.6
        assert 0.26 <= entry["water_material_emissive_fill_scale"] <= 0.28
        assert 0.18 <= entry["water_material_roughness_scale"] <= 0.22
        assert 0.28 <= entry["water_material_roughness_floor"] <= 0.34
        assert 0.18 <= entry["water_material_specular_level"] <= 0.22
        assert 0.22 <= entry["water_material_normal_intensity"] <= 0.36
        assert 0.12 <= entry["water_mesh_normal_up_blend"] <= 0.18
        assert entry["fidelity_note"]
        for capture_key in ("guide_seat_capture", "river_eye_capture"):
            capture_path = REPO_ROOT / entry[capture_key]
            assert capture_path.exists()
            assert capture_path.suffix == ".png"
            png_paths.append(capture_path)

    assert len(png_paths) == 20
    assert len({path.name for path in png_paths}) == 20


def test_flow_variant_capture_quality_review_covers_all_band_named_images():
    review = json.loads(
        FLOW_VARIANT_CAPTURE_QUALITY_REVIEW_PATH.read_text(encoding="utf-8")
    )

    assert review == build_flow_variant_capture_quality_review(REPO_ROOT)
    assert (
        review["schema"]
        == "raftsim.unreal.photoreal_flow_variant_capture_quality_review.v1"
    )
    assert review["status"] == EXPECTED_FLOW_VARIANT_CAPTURE_QUALITY_STATUS
    assert review["source_flow_variant_capture_manifest"] == (
        "docs/environment-captures/photoreal_river_previews/flow_variant_capture_manifest.json"
    )
    assert review["source_flow_variant_capture_plan"] == str(
        FLOW_VARIANT_CAPTURE_PLAN_RELATIVE_PATH
    )
    assert review["summary"]["variant_count"] == 10
    assert review["summary"]["capture_count"] == 20
    assert review["summary"]["blocking_capture_count"] == 20
    assert review["summary"]["blocker_counts"][EXPECTED_CAPTURE_BLOCKER_ID] == 20
    assert review["summary"]["per_river"]["american_south_fork"]["capture_count"] == 6
    assert review["summary"]["per_river"]["colorado_river"]["variant_count"] == 3
    assert review["summary"]["per_river"]["pacuare"]["capture_count"] == 8
    assert len(review["summary"]["per_variant"]) == 10

    seen_variant_views = set()
    for capture in review["captures"]:
        assert capture["review_scope"] == "flow_variant"
        assert capture["status"] == EXPECTED_CAPTURE_STATUS
        assert EXPECTED_CAPTURE_BLOCKER_ID in {
            blocker["id"] for blocker in capture["blockers"]
        }
        assert capture["flow_band_id"]
        assert capture["flow_context"]["flow_visual_width_scale"] > 0.0
        assert (REPO_ROOT / capture["capture"]).exists()
        assert capture["metrics"]["source_size"] == [1280, 720]
        seen_variant_views.add(
            (capture["river_id"], capture["flow_band_id"], capture["view_id"])
        )

    assert len(seen_variant_views) == 20


def test_flow_variant_human_and_performance_reviews_cover_every_variant():
    handoff = json.loads(
        FLOW_VARIANT_HUMAN_LIFELIKE_REVIEW_HANDOFF_PATH.read_text(encoding="utf-8")
    )
    performance = json.loads(
        FLOW_VARIANT_ENVIRONMENT_PERFORMANCE_REVIEW_PATH.read_text(encoding="utf-8")
    )

    assert handoff == build_flow_variant_human_lifelike_review_handoff(REPO_ROOT)
    assert performance == build_flow_variant_environment_performance_review(REPO_ROOT)
    assert (
        handoff["schema"]
        == "raftsim.unreal.photoreal_flow_variant_human_lifelike_review_handoff.v1"
    )
    assert (
        handoff["status"] == "awaiting_flow_variant_human_lifelike_review_not_approved"
    )
    assert handoff["summary"] == {
        "river_count": 3,
        "variant_count": 10,
        "capture_count": 20,
        "candidate_capture_count": 0,
        "automated_blocking_capture_count": 20,
        "human_approved_variant_count": 0,
        "open_human_review_gate_count": 70,
        "per_river": {
            "american_south_fork": {
                "review_status": "awaiting_flow_variant_human_lifelike_review_not_approved",
                "variant_count": 3,
                "capture_count": 6,
                "open_review_gate_count": 21,
            },
            "colorado_river": {
                "review_status": "awaiting_flow_variant_human_lifelike_review_not_approved",
                "variant_count": 3,
                "capture_count": 6,
                "open_review_gate_count": 21,
            },
            "pacuare": {
                "review_status": "awaiting_flow_variant_human_lifelike_review_not_approved",
                "variant_count": 4,
                "capture_count": 8,
                "open_review_gate_count": 28,
            },
        },
    }
    assert len(handoff["variants"]) == 10
    assert all(len(variant["captures"]) == 2 for variant in handoff["variants"])
    assert all(
        len(variant["open_review_gates"]) == 7 for variant in handoff["variants"]
    )

    assert (
        performance["schema"]
        == "raftsim.unreal.photoreal_flow_variant_environment_performance_review.v1"
    )
    assert (
        performance["status"]
        == "awaiting_measured_flow_variant_desktop_vr_performance_capture_not_approved"
    )
    assert performance["summary"] == {
        "variant_count": 10,
        "capture_count": 20,
        "profile_count": 20,
        "profile_ids": ["desktop", "vr"],
        "measured_profile_count": 0,
        "open_profile_measurement_count": 20,
        "automated_capture_blocking_count": 20,
        "approved_variant_count": 0,
    }
    assert len(performance["variants"]) == 10
    for variant in performance["variants"]:
        assert len(variant["profiles"]) == 2
        assert {profile["profile_id"] for profile in variant["profiles"]} == {
            "desktop",
            "vr",
        }
        # Preview map binaries are pruned per the July 17 retention revision;
        # the inventory records their path honestly with exists=False.
        assert variant["static_inventory"]["map_asset"]["path"].startswith(
            "unreal/Content/RaftSim/Maps/"
        )
        assert len(variant["static_inventory"]["captures"]) == 2
        assert all(
            capture["exists"] is True
            for capture in variant["static_inventory"]["captures"]
        )
