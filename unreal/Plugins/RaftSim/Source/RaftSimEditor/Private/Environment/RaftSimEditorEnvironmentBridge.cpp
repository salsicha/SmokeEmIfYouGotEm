#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorFoliage
{
FString EscapeRaftSimJsonString(const FString& Value)
{
    return RaftSimEditorEnvironment::EscapeRaftSimJsonString(Value);
}

FString GetRepoRoot()
{
    return RaftSimEditorEnvironment::GetRepoRoot();
}

FLinearColor ScalePreviewColor(const FLinearColor& Color, float Scale)
{
    return RaftSimEditorEnvironment::ScalePreviewColor(Color, Scale);
}

TArray<FVector> ComputePreviewMeshNormals(
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles)
{
    return RaftSimEditorEnvironment::ComputePreviewMeshNormals(Vertices, Triangles);
}

void AddPvePreviewLightRig(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec)
{
    RaftSimEditorEnvironment::AddPreviewLightRig(World, Spec);
}

bool SavePreviewWorld(
    UWorld* World,
    const FString& PackagePath,
    FString& OutSummary)
{
    return RaftSimEditorEnvironment::SavePreviewWorld(World, PackagePath, OutSummary);
}

ACameraActor* FindPreviewCaptureCamera(
    UWorld* World,
    const FString& PreferredCameraLabel)
{
    return RaftSimEditorEnvironment::FindPreviewCaptureCamera(World, PreferredCameraLabel);
}

bool CapturePvePreviewImageForSpec(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& CaptureRoot,
    FString& OutRelativeCapturePath,
    const FString& CameraLabel,
    const FString& CaptureId,
    const FString& CaptureDescription,
    bool bHideForegroundRaftProxies,
    FString& OutSummary,
    const TFunction<bool(UWorld*, ACameraActor*, FString&)>& WorldSetup)
{
    return RaftSimEditorEnvironment::CapturePreviewImageForSpec(
        Spec,
        CaptureRoot,
        OutRelativeCapturePath,
        CameraLabel,
        CaptureId,
        CaptureDescription,
        bHideForegroundRaftProxies,
        OutSummary,
        WorldSetup);
}

bool ConfigureFutaleufuComplementaryTransitionCapture(
    UWorld* LoadedWorld,
    ACameraActor* CaptureCamera,
    const FString& AuthorityMode,
    float SourceCoverage,
    FString& SetupSummary,
    float PatternSize,
    float TransitionMode)
{
    return RaftSimEditorEnvironment::ConfigureFutaleufuComplementaryTransitionCapture(
        LoadedWorld,
        CaptureCamera,
        AuthorityMode,
        SourceCoverage,
        SetupSummary,
        PatternSize,
        TransitionMode);
}

bool CapturePveFutaleufuComplementaryTransitionMotionSequence(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& RelativeCaptureBase,
    const FString& AuthorityMode,
    int32 PatternSize,
    TArray<FString>& OutRelativeCapturePaths,
    FString& OutSummary,
    bool bLitRiverView,
    const TFunction<bool(
        UWorld*,
        ACameraActor*&,
        AActor*&,
        FVector&,
        FVector&,
        FVector&,
        FString&)>& SceneSetup,
    float TransitionMode,
    bool bHlodFrameSearch,
    int32* OutAutomaticHlodFrame,
    bool bHlodSplitShadingSearch,
    bool bHlodDualLayerReview,
    bool bHlodTransmissionLightBracketReview,
    bool bHlodMergedGeometryShapeBracketReview,
    bool bHlodMergedComponentParityReview)
{
    return RaftSimEditorEnvironment::CaptureFutaleufuComplementaryTransitionMotionSequence(
        Spec,
        RelativeCaptureBase,
        AuthorityMode,
        PatternSize,
        OutRelativeCapturePaths,
        OutSummary,
        bLitRiverView,
        SceneSetup,
        TransitionMode,
        bHlodFrameSearch,
        OutAutomaticHlodFrame,
        bHlodSplitShadingSearch,
        bHlodDualLayerReview,
        bHlodTransmissionLightBracketReview,
        bHlodMergedGeometryShapeBracketReview,
        bHlodMergedComponentParityReview);
}

UMaterial* CreateOrUpdateFutaleufuCypressFarProxyMaterial(
    FString& OutSummary)
{
    return RaftSimEditorEnvironment::CreateOrUpdateFutaleufuCypressFarProxyMaterial(OutSummary);
}

FRaftSimPhotographicCaptureSettings GetPhotographicCaptureSettings(
    const FString& RiverId)
{
    const RaftSimEditorEnvironment::FRaftSimPhotographicCaptureSettings Settings =
        RaftSimEditorEnvironment::GetPhotographicCaptureSettings(RiverId);
    FRaftSimPhotographicCaptureSettings Result;
    Result.SunIntensity = Settings.SunIntensity;
    Result.SkyLightIntensity = Settings.SkyLightIntensity;
    Result.FogDensity = Settings.FogDensity;
    Result.ExposureBias = Settings.ExposureBias;
    Result.Saturation = Settings.Saturation;
    Result.Contrast = Settings.Contrast;
    Result.Sharpen = Settings.Sharpen;
    Result.Vignette = Settings.Vignette;
    Result.FilmGrainIntensity = Settings.FilmGrainIntensity;
    Result.SunColor = Settings.SunColor;
    Result.FogColor = Settings.FogColor;
    return Result;
}

UStaticMesh* LoadPreviewMesh(const TCHAR* MeshPath)
{
    return RaftSimEditorEnvironment::LoadPreviewMesh(MeshPath);
}

void ConnectPreviewMaterialColorInput(
    FColorMaterialInput& Input,
    UMaterialExpression* Expression)
{
    RaftSimEditorEnvironment::ConnectPreviewMaterialColorInput(Input, Expression);
}

void ConnectPreviewMaterialVectorInput(
    FVectorMaterialInput& Input,
    UMaterialExpression* Expression)
{
    RaftSimEditorEnvironment::ConnectPreviewMaterialVectorInput(Input, Expression);
}

void ConnectPreviewMaterialScalarInput(
    FScalarMaterialInput& Input,
    UMaterialExpression* Expression)
{
    RaftSimEditorEnvironment::ConnectPreviewMaterialScalarInput(Input, Expression);
}

UMaterialExpression* AddComplementaryScreenDitherOpacity(
    UMaterial* Material,
    UMaterialExpression* BaseOpacity,
    int32 BaseOpacityOutputIndex,
    bool bKeepSourceSide,
    float DefaultSourceCoverage,
    int32 EditorX,
    int32 EditorY)
{
    return RaftSimEditorEnvironment::AddComplementaryScreenDitherOpacity(
        Material,
        BaseOpacity,
        BaseOpacityOutputIndex,
        bKeepSourceSide,
        DefaultSourceCoverage,
        EditorX,
        EditorY);
}

AActor* AddPreviewProceduralMeshActor(
    UWorld* World,
    const FString& Label,
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles,
    const TArray<FVector>& Normals,
    const TArray<FVector2D>& UVs,
    const FLinearColor& Color,
    UMaterialInterface* MaterialOverride,
    const TArray<FLinearColor>* VertexColorOverride,
    bool bCreateCollision)
{
    return RaftSimEditorEnvironment::AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        MaterialOverride,
        VertexColorOverride,
        bCreateCollision);
}

AActor* AddPreviewTwoSectionProceduralMeshActor(
    UWorld* World,
    const FString& Label,
    const TArray<FVector>& FirstVertices,
    const TArray<int32>& FirstTriangles,
    const TArray<FVector>& FirstNormals,
    const TArray<FVector2D>& FirstUVs,
    UMaterialInterface* FirstMaterial,
    const TArray<FVector>& SecondVertices,
    const TArray<int32>& SecondTriangles,
    const TArray<FVector>& SecondNormals,
    const TArray<FVector2D>& SecondUVs,
    UMaterialInterface* SecondMaterial)
{
    return RaftSimEditorEnvironment::AddPreviewTwoSectionProceduralMeshActor(
        World,
        Label,
        FirstVertices,
        FirstTriangles,
        FirstNormals,
        FirstUVs,
        FirstMaterial,
        SecondVertices,
        SecondTriangles,
        SecondNormals,
        SecondUVs,
        SecondMaterial);
}

UStaticMesh* ConvertNativeCanopyProceduralActorToStaticMesh(
    AActor* Actor,
    const FString& PackagePath,
    UMaterialInterface* Material,
    bool bEnableNanite,
    ENaniteShapePreservation ShapePreservation,
    FString& OutSummary)
{
    return RaftSimEditorEnvironment::ConvertNativeCanopyProceduralActorToStaticMesh(
        Actor,
        PackagePath,
        Material,
        bEnableNanite,
        ShapePreservation,
        OutSummary);
}

bool CreateFutaleufuCordilleraCypressTextureAssets(
    TMap<FString, UTexture2D*>& OutTextureAssetsByKey,
    FString& OutSummary)
{
    return RaftSimEditorEnvironment::CreateFutaleufuCordilleraCypressTextureAssets(
        OutTextureAssetsByKey,
        OutSummary);
}

UMaterial* CreateOrUpdateFutaleufuNativeCanopyMaterial(
    const FString& AssetName,
    bool bLeafMaterial,
    const TMap<FString, UTexture2D*>& Textures,
    FString& OutSummary,
    bool bDefaultLitLeafDiagnostic,
    const FString& LeafTextureKeyPrefix,
    bool bFreezeWindForDeterministicReview,
    bool bEnableComplementaryTransition)
{
    return RaftSimEditorEnvironment::CreateOrUpdateFutaleufuNativeCanopyMaterial(
        AssetName,
        bLeafMaterial,
        Textures,
        OutSummary,
        bDefaultLitLeafDiagnostic,
        LeafTextureKeyPrefix,
        bFreezeWindForDeterministicReview,
        bEnableComplementaryTransition);
}

void AppendNativeCanopyTaperedSegment(
    const FVector& Start,
    const FVector& End,
    float StartRadius,
    float EndRadius,
    int32 SegmentCount,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs)
{
    RaftSimEditorEnvironment::AppendNativeCanopyTaperedSegment(
        Start,
        End,
        StartRadius,
        EndRadius,
        SegmentCount,
        Vertices,
        Triangles,
        Normals,
        UVs);
}

void AppendNativeCanopyLeafCard(
    const FVector& Center,
    const FVector& Right,
    const FVector& Up,
    float Width,
    float Height,
    int32 AtlasTile,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs)
{
    RaftSimEditorEnvironment::AppendNativeCanopyLeafCard(
        Center,
        Right,
        Up,
        Width,
        Height,
        AtlasTile,
        Vertices,
        Triangles,
        Normals,
        UVs);
}

void AppendNativeCanopyAtlasCurvedCard(
    const FVector& Start,
    const FVector& Axis,
    const FVector& Right,
    float Width,
    float Length,
    float Camber,
    float LateralSweep,
    int32 SegmentCount,
    int32 AtlasTile,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs)
{
    RaftSimEditorEnvironment::AppendNativeCanopyAtlasCurvedCard(
        Start,
        Axis,
        Right,
        Width,
        Length,
        Camber,
        LateralSweep,
        SegmentCount,
        AtlasTile,
        Vertices,
        Triangles,
        Normals,
        UVs);
}
} // namespace RaftSimEditorFoliage
