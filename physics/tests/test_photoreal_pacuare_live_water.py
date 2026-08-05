from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageStat


REPO_ROOT = Path(__file__).resolve().parents[2]
EDITOR_ROOT = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
GEOMETRY_SOURCE = EDITOR_ROOT / "Landscape/RaftSimEditorLandscapeGeometry.cpp"
WATER_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorPacuareWaterMaterial.cpp"
TEXTURE_SOURCE = EDITOR_ROOT / "Materials/RaftSimEditorPhotorealTextureAssets.cpp"
MAP_TEST_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimTroublemakerMapTest.cpp"
)
SOURCE_ART_ROOT = REPO_ROOT / "unreal/SourceArt/RaftSim/Water/PacuareUpperHuacas"
FLOW_NORMAL = SOURCE_ART_ROOT / "T_RaftSim_PacuareUpperHuacas_FlowNormalV1.png"
FOAM_LACE = SOURCE_ART_ROOT / "T_RaftSim_PacuareUpperHuacas_FoamLaceV1.png"
REVIEW = REPO_ROOT / (
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "pacuare_live_transmitting_water_v1_review.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pacuare_runtime_uses_a_solver_owned_transmitting_core() -> None:
    geometry = GEOMETRY_SOURCE.read_text(encoding="utf-8")
    water = WATER_SOURCE.read_text(encoding="utf-8")
    map_test = MAP_TEST_SOURCE.read_text(encoding="utf-8")

    for token in (
        "LoadOrCreatePacuareUpperHuacasLiveWaterInstance",
        "bEnableLiveSolverVolumeCore = true",
        "LiveSurfaceCalmCoverage = 0.035f",
        "LiveSurfaceActiveCoverage = 0.14f",
        "LivePresentationSurfaceSmoothingStrength = 0.62f",
        "LiveShallowWaterOpacity = 0.46f",
        "RaftSimPacuareTransmittingWaterV1",
        "RaftSimNoSolverStateMutation",
    ):
        assert token in geometry
    for token in (
        "MI_RaftSim_PacuareUpperHuacas_LiveVolumeWaterV1",
        "M_RaftSim_SouthForkRaftTransmissionWater",
        "WaterFlowNormalPrimary",
        "WhitewaterFoamLace",
        "HydraulicFoamCoverageGain",
    ):
        assert token in water
    assert "Pacuare enables the transmitting wet-cell volume core" in map_test
    assert "Pacuare shallow transmission remains open enough for bed cues" in map_test


def test_pacuare_visual_textures_are_first_party_and_hash_locked() -> None:
    texture_source = TEXTURE_SOURCE.read_text(encoding="utf-8")
    expected = {
        FLOW_NORMAL: (
            "pacuare_upper_huacas_flow_normal_v1",
            "9b975bb352087142f9e59cc0fb8c702d56581f9b16a9b9ecdbc5d3eb275f18de",
            "project_owned_pacuare_multiscale_river_flow_normal",
        ),
        FOAM_LACE: (
            "pacuare_upper_huacas_foam_lace_v1",
            "f60fcf09c44dc802497a4f41c4c35bcc00c114ed9af22e83d689d7d445015345",
            "project_owned_pacuare_solver_masked_whitewater_lace",
        ),
    }
    for texture, (asset_id, sha256, map_kind) in expected.items():
        assert texture.is_file()
        assert _sha256(texture) == sha256
        provenance_path = texture.with_suffix(".provenance.json")
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        assert provenance["asset_id"] == asset_id
        assert provenance["project_ownership"] == "first-party generated project asset"
        assert provenance["texture"]["sha256"] == sha256
        assert provenance["texture"]["width"] == 1254
        assert provenance["texture"]["height"] == 1254
        assert "no hydraulic" in provenance["asset_role"]
        assert map_kind in texture_source

    with Image.open(FLOW_NORMAL) as image:
        assert image.size == (1254, 1254)
        assert image.mode == "RGB"
    with Image.open(FOAM_LACE).convert("L") as image:
        assert image.size == (1254, 1254)
        assert ImageStat.Stat(image).mean[0] < 80.0


def test_pacuare_live_water_keeps_physics_and_static_capture_authority_separate() -> None:
    geometry = GEOMETRY_SOURCE.read_text(encoding="utf-8")

    assert "RaftSimPacuareUpperHuacasSolverVisualization" in geometry
    assert "RaftSimPacuareCaptureOnlyWater" in geometry
    assert "RaftSimLiveSolverWaterOwnsRuntimeRendering" in geometry
    assert "visual-only" in WATER_SOURCE.read_text(encoding="utf-8")
    assert "Landscape->Import" not in WATER_SOURCE.read_text(encoding="utf-8")
    assert "SetCollision" not in WATER_SOURCE.read_text(encoding="utf-8")


def test_pacuare_transmitting_water_review_is_honest_and_hash_locked() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == "raftsim.environment.pacuare_live_water_review.v1"
    assert review["status"] == (
        "retained_technical_visual_improvement_photoreal_promotion_open"
    )
    assert review["passed"] is False
    decision = review["decision"]
    assert decision["reference_runnable"] is True
    assert decision["technical_candidate_passed"] is True
    assert decision["visual_improvement_passed"] is True
    assert decision["photoreal_acceptance_passed"] is False
    assert decision["hydraulics_changed"] is False
    assert decision["raft_forces_changed"] is False
    assert decision["authored_capture_water_hidden_in_game"] is True
    assert review["runtime_contract"]["live_volume_core_enabled"] is True
    assert review["runtime_contract"]["shallow_opacity"] == 0.46
    assert review["runtime_contract"]["detail_surface_calm_coverage"] == 0.035
    assert len(review["remaining_photoreal_defects"]) >= 5
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        if artifact.get("hash_locked", True):
            assert _sha256(path) == artifact["sha256"]
