import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LIGHTING_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
    "RaftSimEditorNearFieldAndLighting.cpp"
)
CATALOG_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
    "RaftSimEditorEnvironmentCatalog.cpp"
)
MAP_TEST_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimTroublemakerMapTest.cpp"
)
RUNTIME_CONFIG_HEADER = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimWater/Public/"
    "RaftSimRiverWaterConfig.h"
)
RUNTIME_CONFIG_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimWater/Private/"
    "RaftSimRiverWaterConfig.cpp"
)
LANDSCAPE_GEOMETRY_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
    "RaftSimEditorLandscapeGeometry.cpp"
)
REVIEW_PATH = REPO_ROOT / (
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "pacuare_humid_atmosphere_v1_review.json"
)


def test_pacuare_humidity_contract_is_river_local_and_layered():
    source = LIGHTING_SOURCE.read_text(encoding="utf-8")
    catalog = CATALOG_SOURCE.read_text(encoding="utf-8")

    assert 'Spec.RiverId == TEXT("pacuare")' in source
    assert "bPacuareHumidAtmosphere" in source
    assert "RaftSimPacuareHumidAtmosphereV1" in source
    assert "RaftSimLayeredRainforestHumidity" in source
    assert "SetFogMaxOpacity(0.62f)" in source
    assert "SetStartDistance(450.0f)" in source
    assert "SetSecondFogDensity(0.0012f)" in source
    assert "SetSecondFogHeightOffset(-160.0f)" in source
    assert "SetSecondFogHeightFalloff(0.06f)" in source
    assert "SetVolumetricFog(false)" in source
    capture_settings = catalog.split(
        "FRaftSimPhotographicCaptureSettings GetPhotographicCaptureSettings", 1
    )[1]
    pacuare_settings = capture_settings.split(
        'else if (RiverId == TEXT("pacuare"))', 1
    )[1].split('else if (RiverId == TEXT("zambezi_batoka_gorge"))', 1)[0]
    assert "Settings.SkyLightIntensity = 1.90f" in pacuare_settings
    assert "Settings.FogDensity = 0.0075f" in pacuare_settings
    assert "Settings.FogColor = FLinearColor(0.58f, 0.68f, 0.60f)" in (
        pacuare_settings
    )


def test_pacuare_humidity_contract_uses_physical_sky_scattering_not_mist_cards():
    source = LIGHTING_SOURCE.read_text(encoding="utf-8")

    assert "SetMultiScatteringFactor(1.08f)" in source
    assert "SetMieScatteringScale(0.0048f)" in source
    assert "SetMieAnisotropy(0.72f)" in source
    assert "SetMieExponentialDistribution(0.90f)" in source
    assert "RaftSimHumidAerialPerspective" in source
    assert "AddPreviewTranslucentMeshActor" not in source


def test_pacuare_humidity_contract_is_presentation_only_and_runtime_audited():
    lighting = LIGHTING_SOURCE.read_text(encoding="utf-8")
    map_test = MAP_TEST_SOURCE.read_text(encoding="utf-8")

    assert "RaftSimPresentationOnlyNoHydraulicAuthority" in lighting
    for forbidden in (
        "Landscape->Import",
        "SetCollision",
        "CookedFieldsDir =",
        "FlowBand =",
        "LiveSurface",
        "RaftForces",
    ):
        assert forbidden not in lighting

    for token in (
        "Pacuare has a four-actor humid-atmosphere contract",
        "Pacuare humidity avoids rejected volumetric occlusion",
        "Pacuare humidity keeps a bounded opacity",
        "Pacuare humidity begins beyond the guide camera",
        "Pacuare humidity uses a restrained water-level layer",
        "Pacuare humidity disclaims hydraulic authority",
    ):
        assert token in map_test


def test_pacuare_humidity_contract_survives_ue_state_stream_world_duplication():
    header = RUNTIME_CONFIG_HEADER.read_text(encoding="utf-8")
    runtime = RUNTIME_CONFIG_SOURCE.read_text(encoding="utf-8")
    geometry = LANDSCAPE_GEOMETRY_SOURCE.read_text(encoding="utf-8")

    for token in (
        "bEnforceTaggedHeightFogPresentation",
        "RuntimeHeightFogActorTag",
        "RuntimeHeightFogDensity",
        "bRuntimeVolumetricFogEnabled",
    ):
        assert token in header
        assert token in geometry
    assert "PrimaryActorTick.TickGroup = TG_PostUpdateWork" in runtime
    assert "ApplyTaggedHeightFogPresentation" in runtime
    assert "SetFogDensity(RuntimeHeightFogDensity)" in runtime
    assert "SetVolumetricFog(bRuntimeVolumetricFogEnabled)" in runtime
    pacuare_geometry = geometry.split(
        "WaterConfig->bEnforceTaggedHeightFogPresentation", 1
    )[1][:1200]
    assert 'TEXT("RaftSimLayeredRainforestHumidity")' in pacuare_geometry
    assert "RuntimeHeightFogDensity = 0.0075f" in pacuare_geometry
    assert "bRuntimeVolumetricFogEnabled = false" in pacuare_geometry


def test_pacuare_humidity_review_is_fail_closed_and_hash_locked():
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))

    assert review["status"] == (
        "retained_layered_humidity_improvement_photoreal_promotion_open"
    )
    assert review["passed"] is False
    decision = review["decision"]
    assert decision["reference_runnable"] is True
    assert decision["technical_candidate_passed"] is True
    assert decision["visual_bank_readability_improved"] is True
    assert decision["photoreal_acceptance_passed"] is False
    assert decision["production_promoted"] is False
    for unchanged_contract in (
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
    assert review["rejected_iterations"]["count"] == 3
    for view in ("guide_seat", "river_eye", "solver_rapid"):
        metrics = review["matched_capture_metrics"][view]
        assert metrics["bank_mean_luminance_after"] > metrics[
            "bank_mean_luminance_before"
        ]
        assert metrics["bank_near_black_fraction_after"] < metrics[
            "bank_near_black_fraction_before"
        ]
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file(), artifact["path"]
        if artifact.get("hash_locked", True):
            assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
