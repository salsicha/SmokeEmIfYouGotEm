from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CC0_RUNTIME_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
    "RaftSimCC0CrewVisualActor.cpp"
)


def test_per_frame_pose_dispatch_reuses_loaded_body_and_materials() -> None:
    source = CC0_RUNTIME_SOURCE.read_text(encoding="utf-8")
    ensure_body = source.split(
        "bool ARaftSimCC0CrewVisualActor::EnsureBodyLoaded()", 1
    )[1].split(
        "void ARaftSimCC0CrewVisualActor::CacheReferencePose()", 1
    )[0]
    cache_guard = ensure_body.index("if (bBodyReady && Body->GetSkinnedAsset()")
    mesh_load = ensure_body.index("LoadObject<USkeletalMesh>")
    material_override = ensure_body.index("ApplyProductionBodyMaterialOverrides")
    assert cache_guard < mesh_load < material_override
    assert "return true;" in ensure_body[cache_guard:mesh_load]


def test_helmet_anchor_transforms_a_cached_head_local_point() -> None:
    source = CC0_RUNTIME_SOURCE.read_text(encoding="utf-8")
    anchor = source.split(
        "bool ARaftSimCC0CrewVisualActor::TryGetRenderedFaceEyeCenterWorld", 1
    )[1].split(
        "void ARaftSimCC0CrewVisualActor::ConfigureCrewAppearance_Implementation", 1
    )[0]
    assert "HeadTransform.TransformPosition(RenderedFaceAnchorHeadLocal)" in anchor
    assert "GetSkinnedVertexPosition" not in anchor
    assert "CacheRefToLocalMatrices" not in anchor
