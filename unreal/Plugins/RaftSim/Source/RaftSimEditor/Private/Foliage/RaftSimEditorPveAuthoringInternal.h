#pragma once

#include "CoreMinimal.h"

class AActor;
class AStaticMeshActor;
class UMaterial;
class UPCGGraph;
class UPCGNode;
class UPCGSettings;
class UWorld;

namespace RaftSimEditorPve
{
struct FFutaleufuCypressPveFormSpec
{
    FString Id;
    FString DisplayName;
    FString AssetToken;
    FString LifeStage;
    int32 Seed = 0;
    float WholeTreeScale = 1.0f;
    float LiveTwigScale = 1.0f;
    float BranchScale = 0.8f;
    float PrimaryAxilAngle = 72.0f;
    float AxillaryParentGrowth = 1.4f;
    float AxillaryChildGrowth = 1.2f;
    int32 GraftDensity = 20;
    float GraftRelativeStart = 0.1f;
    bool bAllowSenescence = false;
    float ApicalRandomAngle = 2.0f;
    float AxillaryRandomAngle = 5.0f;
    float GravityStrength = 0.2f;
    float GravityAngleCorrection = 0.65f;
};

struct FRaftSimPveMultiViewAtlasBakeResult
{
    bool bAtlasFilesSaved = false;
    bool bTextureAssetsSaved = false;
    bool bMaterialSaved = false;
    bool bRelightableMaterialSaved = false;
    bool bRelightableTrunkMaterialSaved = false;
    bool bRelightableFoliageMaterialSaved = false;
    bool bProxyActorCreated = false;
    int32 ViewCount = 0;
    int32 TileResolution = 0;
    int32 AtlasResolution = 0;
    float OrthoWidthCm = 0.0f;
    float AzimuthOffsetDegrees = 0.0f;
    bool bPerspectiveCapture = false;
    float CaptureRadiusCm = 0.0f;
    float PerspectiveHorizontalFovDegrees = 0.0f;
    bool bDepthParallaxEnabled = false;
    float DepthParallaxScaleCm = 0.0f;
    bool bComplementaryTransitionEnabled = false;
    int32 ProxyVertexCount = 0;
    int32 ProxyTriangleCount = 0;
    int64 MaterialIdentityFallbackPixelCount = 0;
    float MinimumCoverage = 1.0f;
    float MaximumCoverage = 0.0f;
    FLinearColor ColorGain = FLinearColor::White;
    FString OpacitySource;
    FString ManifestRelativePath;
    FString BaseColorRelativePath;
    FString AlbedoRelativePath;
    FString NormalRelativePath;
    FString OpacityRelativePath;
    FString DepthRelativePath;
    FString MaterialIdentityRelativePath;
    FString BaseColorDigest;
    FString AlbedoDigest;
    FString NormalDigest;
    FString OpacityDigest;
    FString DepthDigest;
    FString MaterialIdentityDigest;
    FString BaseColorAssetPath;
    FString AlbedoAssetPath;
    FString NormalAssetPath;
    FString OpacityAssetPath;
    FString DepthAssetPath;
    FString MaterialIdentityAssetPath;
    FString MaterialAssetPath;
    FString RelightableMaterialAssetPath;
    FString RelightableTrunkMaterialAssetPath;
    FString RelightableFoliageMaterialAssetPath;
    UMaterial* Material = nullptr;
    UMaterial* RelightableMaterial = nullptr;
    UMaterial* RelightableTrunkMaterial = nullptr;
    UMaterial* RelightableFoliageMaterial = nullptr;
    AStaticMeshActor* ProxyActor = nullptr;

    bool IsReady() const
    {
        return bAtlasFilesSaved && bTextureAssetsSaved && bMaterialSaved &&
            bProxyActorCreated && ViewCount == 16 &&
            (TileResolution == 512 || TileResolution == 1024) &&
            AtlasResolution == TileResolution * 4 && MinimumCoverage >= 0.002f &&
            MaximumCoverage <= 0.85f &&
            (!bDepthParallaxEnabled ||
             (ProxyVertexCount == 1089 && ProxyTriangleCount == 2048));
    }

    bool IsRelightableReady() const
    {
        return IsReady() && bRelightableMaterialSaved &&
            !AlbedoRelativePath.IsEmpty() && !AlbedoDigest.IsEmpty() &&
            !AlbedoAssetPath.IsEmpty() && !MaterialIdentityRelativePath.IsEmpty() &&
            !MaterialIdentityDigest.IsEmpty() && !MaterialIdentityAssetPath.IsEmpty() &&
            !RelightableMaterialAssetPath.IsEmpty() &&
            RelightableMaterial != nullptr;
    }

    bool IsSplitRelightableReady() const
    {
        return IsRelightableReady() && bRelightableTrunkMaterialSaved &&
            bRelightableFoliageMaterialSaved &&
            !RelightableTrunkMaterialAssetPath.IsEmpty() &&
            !RelightableFoliageMaterialAssetPath.IsEmpty() &&
            RelightableTrunkMaterial != nullptr &&
            RelightableFoliageMaterial != nullptr;
    }
};

const FFutaleufuCypressPveFormSpec* FindFutaleufuCypressPveFormSpec(
    const FString& Id);
bool SetPveFoliagePaletteMeshes(
    UPCGSettings* Settings,
    const TArray<FString>& MeshObjectPaths);
bool SetPveGraftPaletteEntryCount(UPCGSettings* Settings, int32 EntryCount);
bool SetPveNestedFloat(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* NestedStructName,
    const TCHAR* ValueName,
    float Value);
bool SetPveNestedInt(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* NestedStructName,
    const TCHAR* ValueName,
    int64 Value);
bool SetPvePropertyText(
    UObject* Object,
    const TCHAR* ValueName,
    const FString& ValueText);
bool SetPveNestedText(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* NestedStructName,
    const TCHAR* ValueName,
    const FString& ValueText);
bool SetPveNestedBool(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* NestedStructName,
    const TCHAR* ValueName,
    bool Value);
bool SetPveNestedRamp(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* NestedStructName,
    const TCHAR* ValueName,
    const TArray<FVector2f>& Points);
bool SetPveStructFloat(
    UObject* Object,
    const TCHAR* RootStructName,
    const TCHAR* ValueName,
    float Value);
bool CreateFutaleufuCypressPvePalette(
    UWorld* World,
    const FString& PaletteMode,
    TArray<FString>& OutLiveTwigPaths,
    FString& OutDeadTwigPath,
    FString& OutSummary);
UPCGSettings* FindPveSettingsByClassName(
    const UPCGGraph* Graph,
    const TCHAR* ClassName);
UPCGNode* AddProjectPveNode(
    UPCGGraph* Graph,
    const TCHAR* ClassName,
    UPCGSettings*& OutSettings);
bool ConfigureFutaleufuCypressPveGrower(
    UPCGSettings* Settings,
    const FFutaleufuCypressPveFormSpec& Spec,
    bool bBranchletGrower,
    bool bDeTieredCrown,
    int32 BranchTemplateIndex);
bool BakeFutaleufuCypressMultiViewAtlas(
    UWorld* World,
    AActor* TrunkActor,
    AActor* FoliageActor,
    const FString& VariantId,
    const FString& AssetToken,
    const FString& LocalSavedNamespace,
    const FString& LocalReviewNamespace,
    bool bUseColorCorrectHlod,
    const FLinearColor& AtlasColorGain,
    bool bDeterministicValidationCapture,
    float AzimuthOffsetDegrees,
    bool bUsePerspectiveCapture,
    float RequestedPerspectiveCaptureRadiusCm,
    bool bUseDepthParallax,
    bool bEnableComplementaryTransition,
    int32 RequestedTileResolution,
    FRaftSimPveMultiViewAtlasBakeResult& OutResult,
    FString& OutSummary);
} // namespace RaftSimEditorPve
