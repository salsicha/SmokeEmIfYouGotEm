#pragma once

#include "CoreMinimal.h"

class UMaterial;
class UMaterialExpression;
class UMaterialInterface;
class UStaticMesh;
class UTexture2D;
class UWorld;
class AActor;
class ACameraActor;
struct FColorMaterialInput;
struct FVectorMaterialInput;
struct FScalarMaterialInput;
enum class ENaniteShapePreservation : uint8;

namespace RaftSimEditorFoliage
{
FString EscapeRaftSimJsonString(const FString& Value);

struct FRaftSimEnvironmentPreviewSpec
{
    FString RiverId;
    FString DisplayName;
    FString MapPackagePath;
    FString SourceManifest;
    FString AerialDrapeImage;
    FString TerrainReliefImage;
    FString HeightfieldPreviewImage;
    FString WaterMaskImage;
    FString VegetationMaskImage;
    FString ElevationSample;
    FString SourceDrapeDescription;
    FString FlowBandId;
    FString FlowBandDisplayName;
    FString FlowBandSource;
    FString FlowVisualDescription;
    FLinearColor WaterColor = FLinearColor(0.05f, 0.26f, 0.32f);
    FLinearColor TerrainColor = FLinearColor(0.26f, 0.23f, 0.18f);
    FLinearColor RockColor = FLinearColor(0.35f, 0.33f, 0.29f);
    FLinearColor FoliageColor = FLinearColor(0.18f, 0.34f, 0.16f);
    FLinearColor RaftColor = FLinearColor(0.90f, 0.28f, 0.08f);
    float FlowReferenceDischargeCfs = -1.0f;
    float FlowWidthScale = 1.0f;
    float FlowFoamScale = 1.0f;
    float FlowWetBankScale = 1.0f;
    float FlowCurrentCueScale = 1.0f;
    float FlowWaterLevelOffsetCm = 0.0f;
    float CanyonHeightCm = 850.0f;
    float RiverHalfWidthCm = 360.0f;
    float BankWidthCm = 760.0f;
    float BendAmplitudeCm = 240.0f;
    float TerrainReliefAmplitudeCm = 0.0f;
    float HeightfieldPreviewAmplitudeCm = 0.0f;
    float HeightfieldLocalReliefAmplitudeCm = 0.0f;
    float HeightfieldSeamFeatherUv = 0.0f;
    float TerrainNormalSofteningBlend = 0.45f;
    int32 BoulderCount = 18;
    int32 FoliageCount = 32;
    int32 FoamTrainCount = 12;
    bool bHasWaterfalls = false;
    bool bDesertCanyon = false;
    bool bDeterministicValidationCapture = false;
};

struct FRaftSimPhotographicCaptureSettings
{
    float SunIntensity = 5.20f;
    float SkyLightIntensity = 1.25f;
    float FogDensity = 0.0025f;
    float ExposureBias = -0.32f;
    float Saturation = 1.06f;
    float Contrast = 1.04f;
    float Sharpen = 0.24f;
    float Vignette = 0.06f;
    float FilmGrainIntensity = 0.0f;
    FLinearColor SunColor = FLinearColor(0.98f, 0.965f, 0.91f);
    FLinearColor FogColor = FLinearColor(0.52f, 0.57f, 0.50f);
};

FRaftSimPhotographicCaptureSettings GetPhotographicCaptureSettings(
    const FString& RiverId);

UStaticMesh* LoadPreviewMesh(const TCHAR* MeshPath);

FString GetRepoRoot();
FLinearColor ScalePreviewColor(const FLinearColor& Color, float Scale);
TArray<FVector> ComputePreviewMeshNormals(
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles);

void AddPvePreviewLightRig(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec);
bool SavePreviewWorld(
    UWorld* World,
    const FString& PackagePath,
    FString& OutSummary);
ACameraActor* FindPreviewCaptureCamera(
    UWorld* World,
    const FString& PreferredCameraLabel);

bool CapturePvePreviewImageForSpec(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& CaptureRoot,
    FString& OutRelativeCapturePath,
    const FString& CameraLabel,
    const FString& CaptureId,
    const FString& CaptureDescription,
    bool bHideForegroundRaftProxies,
    FString& OutSummary,
    const TFunction<bool(UWorld*, ACameraActor*, FString&)>& WorldSetup = {});

bool ConfigureFutaleufuComplementaryTransitionCapture(
    UWorld* LoadedWorld,
    ACameraActor* CaptureCamera,
    const FString& AuthorityMode,
    float SourceCoverage,
    FString& SetupSummary,
    float PatternSize = 4.0f,
    float TransitionMode = 0.0f);

bool CapturePveFutaleufuComplementaryTransitionMotionSequence(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& RelativeCaptureBase,
    const FString& AuthorityMode,
    int32 PatternSize,
    TArray<FString>& OutRelativeCapturePaths,
    FString& OutSummary,
    bool bLitRiverView = false,
    const TFunction<bool(
        UWorld*,
        ACameraActor*&,
        AActor*&,
        FVector&,
        FVector&,
        FVector&,
        FString&)>& SceneSetup = {},
    float TransitionMode = 0.0f,
    bool bHlodFrameSearch = false,
    int32* OutAutomaticHlodFrame = nullptr,
    bool bHlodSplitShadingSearch = false,
    bool bHlodDualLayerReview = false,
    bool bHlodTransmissionLightBracketReview = false,
    bool bHlodMergedGeometryShapeBracketReview = false,
    bool bHlodMergedComponentParityReview = false);

UMaterial* CreateOrUpdateFutaleufuCypressFarProxyMaterial(
    FString& OutSummary);

void ConnectPreviewMaterialColorInput(
    FColorMaterialInput& Input,
    UMaterialExpression* Expression);
void ConnectPreviewMaterialVectorInput(
    FVectorMaterialInput& Input,
    UMaterialExpression* Expression);
void ConnectPreviewMaterialScalarInput(
    FScalarMaterialInput& Input,
    UMaterialExpression* Expression);

UMaterialExpression* AddComplementaryScreenDitherOpacity(
    UMaterial* Material,
    UMaterialExpression* BaseOpacity,
    int32 BaseOpacityOutputIndex,
    bool bKeepSourceSide,
    float DefaultSourceCoverage,
    int32 EditorX,
    int32 EditorY);

AActor* AddPreviewProceduralMeshActor(
    UWorld* World,
    const FString& Label,
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles,
    const TArray<FVector>& Normals,
    const TArray<FVector2D>& UVs,
    const FLinearColor& Color,
    UMaterialInterface* MaterialOverride = nullptr,
    const TArray<FLinearColor>* VertexColorOverride = nullptr,
    bool bCreateCollision = true);

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
    UMaterialInterface* SecondMaterial);

UStaticMesh* ConvertNativeCanopyProceduralActorToStaticMesh(
    AActor* Actor,
    const FString& PackagePath,
    UMaterialInterface* Material,
    bool bEnableNanite,
    ENaniteShapePreservation ShapePreservation,
    FString& OutSummary);

bool CreateFutaleufuCordilleraCypressTextureAssets(
    TMap<FString, UTexture2D*>& OutTextureAssetsByKey,
    FString& OutSummary);

UMaterial* CreateOrUpdateFutaleufuNativeCanopyMaterial(
    const FString& AssetName,
    bool bLeafMaterial,
    const TMap<FString, UTexture2D*>& Textures,
    FString& OutSummary,
    bool bDefaultLitLeafDiagnostic = false,
    const FString& LeafTextureKeyPrefix = FString(),
    bool bFreezeWindForDeterministicReview = false,
    bool bEnableComplementaryTransition = false);

void AppendNativeCanopyTaperedSegment(
    const FVector& Start,
    const FVector& End,
    float StartRadius,
    float EndRadius,
    int32 SegmentCount,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs);

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
    TArray<FVector2D>& UVs);

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
    TArray<FVector2D>& UVs);
} // namespace RaftSimEditorFoliage
