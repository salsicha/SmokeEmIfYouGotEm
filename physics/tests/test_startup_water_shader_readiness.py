"""Source contracts only; the unskipped native startup replay proves rendering."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
          "RaftSimShorelineMeshComponent.cpp").read_text()
PREPARE = SOURCE.split("void PrepareStartupWaterShaders(", 1)[1].split(
    "FDynamicMeshVertex RenderVertex", 1)[0]


def test_preparation_is_editor_rendering_game_world_only():
    assert "#if WITH_EDITOR" in PREPARE and "#endif" in PREPARE
    for guard in ("!FApp::CanEverRender()", "!IsInGameThread()",
                  "!Component->GetWorld()", "!Component->GetWorld()->IsGameWorld()",
                  "!Component->GetWorld()->Scene"):
        assert guard in PREPARE
    assert "FParse::Param" not in PREPARE


def test_only_actual_incomplete_water_material_is_prepared():
    for required in ("Component->GetMaterial(0)", "GetMaterialResource(",
                     "MSM_SingleLayerWater", "IsGameThreadShaderMapComplete()"):
        assert required in PREPARE
    assert PREPARE.index("IsGameThreadShaderMapComplete()") < PREPARE.index("CacheShaders(")
    assert "CacheShaders(EMaterialShaderPrecompileMode::Synchronous)" in PREPARE
    assert "Resource->FinishCompilation()" in PREPARE
    assert "LogTemp,Error" in PREPARE
    for forbidden in ("FinishAllCompilation", "GShaderCompilingManager",
                      "GetShaderTypeByName", "FlushRenderingCommands", "Sleep("):
        assert forbidden not in PREPARE


def test_both_mesh_paths_prepare_only_before_first_publication():
    plain = SOURCE.split("bool URaftSimShorelineMeshComponent::SetWaterMesh(", 1)[1].split(
        "bool URaftSimShorelineMeshComponent::SetClippedWaterMesh(", 1)[0]
    clipped = SOURCE.split("bool URaftSimShorelineMeshComponent::SetClippedWaterMesh(", 1)[1].split(
        "FPrimitiveSceneProxy* URaftSimShorelineMeshComponent::CreateSceneProxy()", 1)[0]
    assert "if (WaterVertices.IsEmpty()) PrepareStartupWaterShaders(this);" in plain
    assert "if (!BeforeVertices) PrepareStartupWaterShaders(this);" in clipped
    for publication in (plain, clipped):
        assert publication.index("PrepareStartupWaterShaders(this)") < publication.index("MarkRenderStateDirty()")
    assert SOURCE.count("PrepareStartupWaterShaders(this)") == 2


def test_read_only_audit_does_not_trigger_fallback_compilation():
    audit = SOURCE.split("void GetDynamicMeshElements(", 1)[1].split(
        "if (!ActiveIndices) return;", 1)[0]
    assert "GetMaterialNoFallback" in audit
    assert "GetMaterialWithFallback" not in audit
    assert "bStartupRenderAudit && Family.FrameNumber<8" in audit
    assert "CacheShaders" not in audit and "FinishCompilation" not in audit
