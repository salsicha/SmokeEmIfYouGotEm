from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/GrassBermuda01_1K"
)
BUILD_MANIFEST = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/SouthForkFullReach/full_reach_environment_build_manifest.json"
)
SOURCE_MANIFEST = ASSET_ROOT / "polyhaven_grass_bermuda_01_source_manifest.json"
PREP_REPORT = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/polyhaven_grass_bermuda_01_fbx_prep_report.json"
)
IMPORT_REPORT = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/polyhaven_grass_bermuda_01_import_report.json"
)
REVIEW = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/m9_cc0_scanned_ground_cover_v216_review.json"
)
PERFORMANCE_AB = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/m9_cc0_scanned_ground_cover_v216_performance_ab.json"
)
BASELINE_ROOT = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/photographic_v216_pre_cc0_scanned_ground_cover"
)
CANDIDATE_ROOT = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/photographic_v216_cc0_scanned_ground_cover"
)
GROUND_COVER_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorSouthForkGroundCover.cpp"
)
FULL_REACH_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorSouthForkFullReach.cpp"
)
CAPTURE_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/RaftSimEditorSouthForkCapture.cpp"
)
CONTENT_LOCK_SOURCE = (
    REPO_ROOT
    / "unreal/Source/SmokeEmIfYouGotEm/RaftSimContentLockDirector.cpp"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_cc0_scanned_ground_cover_source_and_import_are_rights_tracked() -> None:
    source = load_json(SOURCE_MANIFEST)
    prep = load_json(PREP_REPORT)
    imported = load_json(IMPORT_REPORT)

    assert source["product_page"] == "https://polyhaven.com/a/grass_bermuda_01"
    assert source["license"]["name"] == "CC0 1.0 Universal"
    assert source["authors"] == ["Rico Cilliers"]
    assert source["files"][0]["sha256"] == (
        "ec188edf028e1a76ed2e63f7483165ea765f0212b317e4b73fdc3d64610500cd"
    )
    assert prep["removed_zero_area_forms"] == [
        "grass_bermuda_01_single_a",
        "grass_bermuda_01_single_b",
    ]
    assert prep["retained_mesh_form_count"] == 19
    assert prep["geometry_or_material_authorship_changed"] is False
    assert imported["imported_mesh_form_count"] == 19
    assert imported["production_mesh_form_count"] == 8
    assert imported["nanite_enabled"] is False
    assert "no exact South Fork species" in imported["authority"]


def test_cc0_scanned_ground_cover_assets_and_fail_closed_map_contract_exist() -> None:
    expected_assets = {
        "M_GrassBermuda01_Foliage.uasset",
        "T_GrassBermuda01_BaseColor_1K.uasset",
        "T_GrassBermuda01_NormalGL_1K.uasset",
        "T_GrassBermuda01_Opacity_1K.uasset",
        "T_GrassBermuda01_Roughness_1K.uasset",
        "SM_GrassBermuda01_grass_bermuda_01_dead_a.uasset",
        "SM_GrassBermuda01_grass_bermuda_01_dead_b.uasset",
        "SM_GrassBermuda01_grass_bermuda_01_flattened_a.uasset",
        "SM_GrassBermuda01_grass_bermuda_01_medium_a.uasset",
        "SM_GrassBermuda01_grass_bermuda_01_medium_c.uasset",
        "SM_GrassBermuda01_grass_bermuda_01_medium_d.uasset",
        "SM_GrassBermuda01_grass_bermuda_01_medium_f.uasset",
        "SM_GrassBermuda01_grass_bermuda_01_small_c.uasset",
    }
    assert expected_assets <= {path.name for path in ASSET_ROOT.glob("*.uasset")}

    full_reach = FULL_REACH_SOURCE.read_text(encoding="utf-8")
    ground_cover = GROUND_COVER_SOURCE.read_text(encoding="utf-8")
    capture = CAPTURE_SOURCE.read_text(encoding="utf-8")
    content_lock = CONTENT_LOCK_SOURCE.read_text(encoding="utf-8")
    for token in (
        "ScannedGroundCoverVariantCount = 8",
        "ScannedGroundCoverComponentCount",
        "Cc0ScannedGroundCoverPrimary",
        "Cc0ScannedGroundCoverSatellite",
        "ECollisionEnabled::NoCollision",
        "VfxImage.Pixels[Index].A > 0.1f",
        "if (!bPrimaryEcologySample)",
    ):
        assert token in full_reach
    assert "AddSouthForkScannedGroundCoverInstances" in ground_cover
    assert "BankDistanceM >= 14.0f" in ground_cover
    assert "BankDistanceM < 30.0f" in ground_cover
    assert "GetSouthForkScannedGroundCoverScaleCalibration" in ground_cover
    assert "RaftSimCc0ScannedGroundCoverBaselineReview" in capture
    assert "SetVisibility(false, true)" in capture
    assert "RaftSimCc0ScannedGroundCoverBaselineReview" in content_lock
    assert "baseline_hidden_scanned_ground_cover_instance_count" in content_lock
    assert "Shrub02" not in full_reach


def test_generated_manifest_records_layered_non_authoritative_contract() -> None:
    manifest = load_json(BUILD_MANIFEST)
    assert manifest["cc0_scanned_ground_cover_v1"] is True
    assert manifest["cc0_scanned_ground_cover_mesh_forms"] == 8
    assert manifest["cc0_scanned_ground_cover_imported_family_forms"] == 19
    assert manifest["cc0_scanned_ground_cover_import_build_scale"] == 1000
    assert manifest["cc0_scanned_ground_cover_forms_per_source_cluster"] == 2
    assert manifest["cc0_scanned_ground_cover_nanite_enabled"] is False
    assert "solver/VFX wet-mask cells excluded" in manifest[
        "cc0_scanned_ground_cover_dry_transition_band_m"
    ]
    authority = manifest["cc0_scanned_ground_cover_authority"]
    for phrase in (
        "no exact South Fork species",
        "no collision",
        "terrain",
        "water",
        "hydraulic",
        "raft authority",
    ):
        assert phrase in authority
    metrics = manifest["metrics"]
    assert metrics["procedural_noncolliding_ground_cover_instances"] == 220759
    assert metrics["cc0_noncolliding_scanned_ground_cover_instances"] == 442938


def test_fixed_capture_evidence_is_hash_locked_and_fail_closed() -> None:
    review = load_json(REVIEW)
    performance = load_json(PERFORMANCE_AB)
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["promotion_allowed"] is False
    assert review["implementation"]["project_owned_tuft_instances_retained"] == 220759
    assert review["implementation"]["cc0_scanned_ground_cover_instances"] == 442938
    assert review["authority"]["visual_presentation_only"] is True
    assert review["authority"]["terrain_collision_changed"] is False
    assert review["authority"]["water_geometry_changed"] is False
    assert review["authority"]["hydraulics_changed"] is False
    assert review["review_decision"]["observed_water_overlap"] is False
    assert len(review["photoreal_rejection_reasons"]) >= 6
    assert len(review["open_gates"]) >= 6

    comparisons = review["objective_capture_comparison"]
    assert len(comparisons) == 5
    changed = []
    for item in comparisons:
        baseline = BASELINE_ROOT / f"{item['capture']}.png"
        candidate = CANDIDATE_ROOT / f"{item['capture']}.png"
        assert sha256(baseline) == item["baseline_sha256"]
        assert sha256(candidate) == item["candidate_sha256"]
        assert item["changed_pixel_fraction_gt8"] > 0.0
        changed.append(item["changed_pixel_fraction_gt8"])
    assert max(changed) >= 0.004

    assert performance["baseline"]["hidden_component_count"] == 16
    assert performance["baseline"]["hidden_streamed_instance_count"] == 40436
    assert performance["baseline"]["total_saved_map_scanned_instance_count"] == 442938
    assert performance["comparison"]["candidate_minus_baseline_p95_ms"] < 0.5
    assert performance["comparison"]["candidate_regression_budget_passed"] is True
    assert performance["comparison"]["sixty_fps_full_map_gate_passed"] is False
    assert performance["profile"]["release_performance_qualification_eligible"] is False
