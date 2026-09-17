#pragma once

#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/MaterialExpressionPerInstanceRandom.h"
#include "Materials/MaterialInstanceConstant.h"

// Private implementation shared by the landscape biome preparation and placement passes.
namespace RaftSimEditorEnvironment::LandscapeFoliage
{
constexpr TCHAR ZambeziVegetationMaterialPath[] = TEXT(
    "/Game/RaftSim/Environment/ZambeziRun/Vegetation/Materials/"
    "M_RaftSim_Zambezi_OpaqueVegetation");
constexpr TCHAR ZambeziVegetationMeshRoot[] = TEXT(
    "/Game/RaftSim/Environment/ZambeziRun/Vegetation/Meshes/");
constexpr TCHAR TemperateVegetationMaterialPath[] = TEXT(
    "/Game/RaftSim/Environment/TemperateRivers/Vegetation/Materials/"
    "M_RaftSim_Temperate_OpaqueVegetation");
constexpr TCHAR TemperateVegetationMeshRoot[] = TEXT(
    "/Game/RaftSim/Environment/TemperateRivers/Vegetation/Meshes/");
constexpr TCHAR ChilkoMutedGroundCoverMaterialPath[] = TEXT(
    "/Game/RaftSim/Environment/ChilkoRun/Vegetation/Materials/"
    "MI_RaftSim_Chilko_MutedGroundCoverV3");
constexpr TCHAR PacuareRainforestVegetationMaterialPath[] = TEXT(
    "/Game/RaftSim/Environment/PacuareRun/Vegetation/Materials/"
    "M_RaftSim_Pacuare_OpaqueRainforestVegetation");
constexpr TCHAR PacuareRainforestVegetationMeshRoot[] = TEXT(
    "/Game/RaftSim/Environment/PacuareRun/Vegetation/Meshes/");
constexpr TCHAR HanceDrylandVegetationMaterialPath[] = TEXT(
    "/Game/RaftSim/Environment/ColoradoRun/Vegetation/Materials/"
    "M_RaftSim_Hance_OpaqueDrylandVegetationV2");
constexpr TCHAR HanceDrylandVegetationMeshRoot[] = TEXT(
    "/Game/RaftSim/Environment/ColoradoRun/Vegetation/Meshes/");
constexpr int32 HanceDrylandGroundCoverInstanceCount = 3000;
constexpr int32 HanceDrylandShrubInstanceCount = 480;
constexpr int32 HanceDrylandMinimumGroundCoverInstanceCount = 2700;
constexpr int32 HanceDrylandMinimumShrubInstanceCount = 420;
constexpr float HanceDrylandGroundCoverSlopeCeilingDegrees = 38.0f;
constexpr float HanceDrylandShrubSlopeCeilingDegrees = 30.0f;
constexpr int32 ZambeziEvidenceBankMosaicInstanceCount = 1200;
constexpr int32 ZambeziEvidenceWoodyInstanceCount = 240;
constexpr float ZambeziEvidenceWoodySlopeCeilingDegrees = 24.0f;
constexpr int32 ZambeziRunnableLaunchBankCoverInstanceCount = 7200;
constexpr int32 ZambeziRunnableLaunchMinimumBankCoverInstanceCount = 4500;
constexpr float ZambeziRunnableLaunchGroundCoverSlopeCeilingDegrees = 42.0f;
constexpr int32 ZambeziRunnableLaunchWoodyInstanceCount = 640;
constexpr int32 ZambeziRunnableLaunchCameraFaceWoodyInstanceCount = 240;
constexpr int32 ZambeziRunnableLaunchMinimumCameraFaceWoodyInstanceCount = 120;
constexpr int32 ZambeziRunnableLaunchMinimumWoodyInstanceCount = 560;
constexpr float ZambeziRunnableLaunchWoodySlopeCeilingDegrees = 34.0f;
constexpr int32 ZambeziRunnableLaunchEcologyElevationBandCount = 3;
constexpr int32 ZambeziRunnableLaunchEcologyStratumCount = 6;
constexpr int32 ZambeziRunnableLaunchMinimumGroundCoverPerStratum = 450;
constexpr int32 ZambeziRunnableLaunchMinimumWoodyPerStratum = 45;
constexpr float ZambeziRunnableLaunchGroundCoverBandMinimumDryHeightCm[] = {
    80.0f, 800.0f, 2500.0f};
constexpr float ZambeziRunnableLaunchGroundCoverBandMaximumDryHeightCm[] = {
    5000.0f, 8000.0f, 16000.0f};
constexpr float ZambeziRunnableLaunchGroundCoverTargetMinimumDryHeightCm[] = {
    150.0f, 1500.0f, 4500.0f};
constexpr float ZambeziRunnableLaunchGroundCoverTargetMaximumDryHeightCm[] = {
    1800.0f, 5000.0f, 12000.0f};
constexpr float ZambeziRunnableLaunchWoodyBandMinimumDryHeightCm[] = {
    300.0f, 800.0f, 2000.0f};
constexpr float ZambeziRunnableLaunchWoodyBandMaximumDryHeightCm[] = {
    8000.0f, 8000.0f, 16000.0f};
constexpr float ZambeziRunnableLaunchWoodyTargetMinimumDryHeightCm[] = {
    300.0f, 1800.0f, 5000.0f};
constexpr float ZambeziRunnableLaunchWoodyTargetMaximumDryHeightCm[] = {
    1800.0f, 5000.0f, 12000.0f};
constexpr int32 ZambeziRunnableLaunchTalusInstanceCount = 360;
constexpr float ZambeziRunnableLaunchTalusSlopeCeilingDegrees = 48.0f;
constexpr int32 ZambeziDryScarpOutcropInstanceCount = 320;
constexpr int32 ZambeziDryScarpOutcropMinimumInstanceCount = 280;
constexpr float ZambeziDryScarpOutcropSlopeCeilingDegrees = 55.0f;
constexpr float ZambeziDryScarpOutcropMinimumHeightAboveWaterCm = 600.0f;
constexpr int32 TemperateWaterlineStructureTargetInstanceCount = 1440;
constexpr int32 TemperateWaterlineStructureMinimumInstanceCount = 1250;
constexpr float TemperateWaterlineStructureSlopeCeilingDegrees = 55.0f;
constexpr int32 TemperateNearBankEcologyTargetInstanceCount = 1800;
constexpr int32 TemperateNearBankEcologyMinimumInstanceCount = 1600;
constexpr float TemperateNearBankEcologySlopeCeilingDegrees = 38.0f;
constexpr int32 ChilkoOrganicShorelineGravelTargetInstanceCount = 7200;
constexpr int32 ChilkoOrganicShorelineGravelMinimumInstanceCount = 6800;
constexpr float ChilkoOrganicShorelineGravelSlopeCeilingDegrees = 42.0f;
constexpr int32 ChilkoOrganicShorelineGroundCoverTargetInstanceCount = 8400;
constexpr int32 ChilkoOrganicShorelineGroundCoverMinimumInstanceCount = 7900;
constexpr float ChilkoOrganicShorelineGravelRareMaximumHeightCm = 85.0f;
constexpr float ChilkoOrganicShorelineGroundCoverMinimumHeightCm = 18.0f;
constexpr float ChilkoOrganicShorelineGroundCoverMaximumHeightCm = 58.0f;
constexpr float ChilkoOrganicShorelineGroundCoverSlopeCeilingDegrees = 32.0f;
constexpr float ChilkoOrganicShorelineStartStationCm = 250.0f;
constexpr float ChilkoOrganicShorelineEndStationCm = 59750.0f;
constexpr int32 PacuareOrganicShorelineRockTargetInstanceCount = 2600;
constexpr int32 PacuareOrganicShorelineRockMinimumInstanceCount = 2350;
constexpr float PacuareOrganicShorelineRockSlopeCeilingDegrees = 50.0f;
constexpr int32 PacuareOrganicShorelineGroundCoverTargetInstanceCount = 5200;
constexpr int32 PacuareOrganicShorelineGroundCoverMinimumInstanceCount = 4700;
constexpr float PacuareOrganicShorelineGroundCoverSlopeCeilingDegrees = 44.0f;
constexpr int32 PacuareScannedFernTargetInstanceCount = 3640;
constexpr int32 PacuareScannedFernMinimumInstanceCount = 3300;
constexpr int32 PacuareOrganicShorelineShrubTargetInstanceCount = 1200;
constexpr int32 PacuareOrganicShorelineShrubMinimumInstanceCount = 1050;
constexpr float PacuareOrganicShorelineShrubSlopeCeilingDegrees = 38.0f;
constexpr int32 PacuareForestFloorLeafLitterTargetInstanceCount = 2600;
constexpr int32 PacuareForestFloorLeafLitterMinimumInstanceCount = 2350;
constexpr float PacuareForestFloorLeafLitterSlopeCeilingDegrees = 36.0f;
constexpr int32 PacuareForestFloorWoodyTargetInstanceCount = 700;
constexpr int32 PacuareForestFloorWoodyMinimumInstanceCount = 620;
constexpr float PacuareForestFloorWoodySlopeCeilingDegrees = 32.0f;
constexpr int32 PacuareForestFloorDeterministicSeed = 18437;
constexpr TCHAR ZambeziRunnableLaunchTalusParentMaterialPath[] = TEXT(
    "/Game/RaftSim/Materials/M_RaftSim_RiverBoulder.M_RaftSim_RiverBoulder");
constexpr TCHAR ZambeziRunnableLaunchTalusMaterialAssetName[] = TEXT(
    "MI_RaftSim_Zambezi_BasaltTalusV1");
constexpr TCHAR ZambeziRunnableLaunchTalusMaterialPackagePath[] = TEXT(
    "/Game/RaftSim/Environment/ZambeziRun/Rocks/Materials/"
    "MI_RaftSim_Zambezi_BasaltTalusV1");
constexpr float ZambeziRunnableLaunchTalusReviewedSourceBlend = 0.42f;
constexpr float ZambeziRunnableLaunchTalusWetBandWidthCm = 220.0f;

enum class EZambeziVegetationForm : uint8
{
    RiparianTree,
    UmbrellaTree,
    ThornScrub,
    SavannaGroundCover,
};

enum class ETemperateVegetationForm : uint8
{
    BroadleafTree,
    ConiferTree,
    RiparianShrub,
    GroundCover,
};

enum class EPacuareForestFloorForm : uint8
{
    FoldedLeafLitter,
    ButtressRoot,
    Deadwood,
};


float ZambeziVegetationUnitRandom(int32 Index, int32 Salt);
void AppendZambeziColoredSegment(
    const FVector& Start,
    const FVector& End,
    float StartRadius,
    float EndRadius,
    int32 SideCount,
    const FLinearColor& StartColor,
    const FLinearColor& EndColor,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors);
void AppendOpaqueLobe(
    const FVector& Center,
    const FVector& Radii,
    int32 Seed,
    const FLinearColor& BaseColor,
    int32 RingCount,
    int32 SegmentCount,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors);
void AppendZambeziOpaqueLobe(
    const FVector& Center,
    const FVector& Radii,
    int32 Seed,
    const FLinearColor& BaseColor,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors);
void AppendOrientedRainforestLobe(
    const FVector& Center,
    const FVector& Radii,
    const FRotator& Rotation,
    int32 Seed,
    const FLinearColor& BaseColor,
    int32 RingCount,
    int32 SegmentCount,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors);
void AppendRainforestOpaqueCrownlet(
    const FVector& Center,
    const FVector& Radii,
    int32 Seed,
    const FLinearColor& BaseColor,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors);
void AppendTemperateOpaqueLobe(
    const FVector& Center,
    const FVector& Radii,
    int32 Seed,
    const FLinearColor& BaseColor,
    bool bRainforestPalette,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors);
void AppendPacuareFoldedLeaf(
    const FVector& Center,
    float LengthCm,
    float WidthCm,
    float FoldHeightCm,
    float CurlHeightCm,
    const FRotator& Rotation,
    const FLinearColor& TopColor,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors);
UStaticMesh* CreatePacuareForestFloorMesh(
    UWorld* World,
    const TCHAR* AssetToken,
    EPacuareForestFloorForm Form,
    int32 Seed,
    UMaterialInterface* Material,
    FString& OutSummary);
bool CreatePacuareForestFloorAssets(
    UWorld* World,
    UMaterialInterface* Material,
    TArray<UStaticMesh*>& OutMeshes,
    FString& OutSummary);
UMaterial* CreateOpaqueVegetationMaterial(
    const TCHAR* MaterialPath,
    const TCHAR* ProfileLabel,
    float ShadowFillStrength,
    float InstanceEnergyMinimum,
    float InstanceEnergyMaximum,
    FString& OutSummary);
UMaterial* CreateZambeziOpaqueVegetationMaterial(FString& OutSummary);
UStaticMesh* CreateZambeziOpaqueVegetationMesh(
    UWorld* World,
    const TCHAR* AssetToken,
    EZambeziVegetationForm Form,
    int32 Seed,
    UMaterialInterface* Material,
    const TCHAR* MeshRoot,
    const TCHAR* ProfileLabel,
    bool bHanceDrylandPalette,
    bool bSecondaryMorphology,
    FString& OutSummary);
bool CreateZambeziOpaqueVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutRiparianTree,
    UStaticMesh*& OutUmbrellaTree,
    UStaticMesh*& OutThornScrub,
    UStaticMesh*& OutGroundCoverA,
    UStaticMesh*& OutGroundCoverB,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary);
bool CreateHanceOpaqueDrylandVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutShrubA,
    UStaticMesh*& OutShrubB,
    UStaticMesh*& OutGroundCoverA,
    UStaticMesh*& OutGroundCoverB,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary);
UStaticMesh* CreateTemperateOpaqueVegetationMesh(
    UWorld* World,
    const TCHAR* AssetToken,
    ETemperateVegetationForm Form,
    int32 Seed,
    UMaterialInterface* Material,
    const TCHAR* MeshRoot,
    const TCHAR* ProfileLabel,
    bool bRainforestPalette,
    bool bSecondaryMorphology,
    FString& OutSummary);
bool CreateTemperateOpaqueVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutBroadleafTreeA,
    UStaticMesh*& OutBroadleafTreeB,
    UStaticMesh*& OutConiferTreeA,
    UStaticMesh*& OutConiferTreeB,
    UStaticMesh*& OutShrubA,
    UStaticMesh*& OutShrubB,
    UStaticMesh*& OutGroundCoverA,
    UStaticMesh*& OutGroundCoverB,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary);
UMaterialInstanceConstant* CreateChilkoMutedGroundCoverMaterial(
    UMaterialInterface* Parent,
    FString& OutSummary);
bool CreatePacuareOpaqueRainforestVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutCanopyTreeA,
    UStaticMesh*& OutCanopyTreeB,
    UStaticMesh*& OutShrub,
    UStaticMesh*& OutGroundCover,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary);
bool ValidateZambeziOpaqueVegetationMaterial(UMaterialInterface* Material);
UMaterialInstanceConstant* LoadOrCreateZambeziRunnableLaunchTalusMaterial(
    FString& OutSummary);

struct FPlacementContext
{
    UWorld*& World;
    ALandscape*& Landscape;
    const FRaftSimLandscapeImportCandidateSpec& Candidate;
    FRaftSimLandscapeImportCandidateResult& OutResult;
    FString& OutSummary;
    const bool& bPacuare;
    const bool& bFutaleufu;
    const bool& bChilko;
    const bool& bColoradoHance;
    const bool& bOpaqueTemperate;
    const bool& bUsesOpaqueVolumetricVegetation;
    TArray<UStaticMesh*>& ReviewedRockMeshes;
    TArray<UStaticMesh*>& ReviewedPineMeshes;
    TArray<UStaticMesh*>& FutaleufuScannedUnderstoryMeshes;
    TArray<UStaticMesh*>& PacuareScannedFernMeshes;
    UStaticMesh*& BroadleafTreeMesh;
    UStaticMesh*& ConiferTreeMesh;
    UStaticMesh*& ShrubMesh;
    UStaticMesh*& UnderstoryMesh;
    UStaticMesh*& ZambeziGroundCoverMeshB;
    UStaticMesh*& TemperateBroadleafTreeMeshB;
    UStaticMesh*& TemperateConiferTreeMeshB;
    UStaticMesh*& TemperateShrubMeshB;
    UStaticMesh*& TemperateUnderstoryMeshB;
    TArray<UStaticMesh*>& PacuareForestFloorMeshes;
    UStaticMesh*& HanceDrylandShrubMeshA;
    UStaticMesh*& HanceDrylandShrubMeshB;
    UStaticMesh*& HanceDrylandGroundCoverMeshA;
    UStaticMesh*& HanceDrylandGroundCoverMeshB;
    FRaftSimPreviewImage& WaterMask;
    FRaftSimPreviewImage& VegetationMask;
    const FRaftSimEnvironmentPreviewSpec& Spec;
    UHierarchicalInstancedStaticMeshComponent*& BroadleafTreeInstances;
    UHierarchicalInstancedStaticMeshComponent*& ConiferTreeInstances;
    UHierarchicalInstancedStaticMeshComponent*& ShrubInstances;
    UHierarchicalInstancedStaticMeshComponent*& UnderstoryInstances;
    UHierarchicalInstancedStaticMeshComponent*& TemperateBroadleafTreeInstancesB;
    UHierarchicalInstancedStaticMeshComponent*& TemperateConiferTreeInstancesB;
    UHierarchicalInstancedStaticMeshComponent*& TemperateShrubInstancesB;
    UHierarchicalInstancedStaticMeshComponent*& TemperateUnderstoryInstancesB;
    UHierarchicalInstancedStaticMeshComponent*& HanceDrylandGroundCoverInstancesA;
    UHierarchicalInstancedStaticMeshComponent*& HanceDrylandGroundCoverInstancesB;
    UHierarchicalInstancedStaticMeshComponent*& HanceDrylandShrubInstancesA;
    UHierarchicalInstancedStaticMeshComponent*& HanceDrylandShrubInstancesB;
    UHierarchicalInstancedStaticMeshComponent*& ZambeziBankMosaicInstances;
    UHierarchicalInstancedStaticMeshComponent*& ZambeziCameraRiparianTreeInstances;
    UHierarchicalInstancedStaticMeshComponent*& ZambeziCameraUmbrellaTreeInstances;
    UHierarchicalInstancedStaticMeshComponent*& ZambeziCameraThornScrubInstances;
    UHierarchicalInstancedStaticMeshComponent*& ZambeziRunnableLaunchGroundCoverInstances;
    UHierarchicalInstancedStaticMeshComponent*& ZambeziRunnableLaunchGroundCoverInstancesB;
    UHierarchicalInstancedStaticMeshComponent*& ZambeziRunnableLaunchRiparianTreeInstances;
    UHierarchicalInstancedStaticMeshComponent*& ZambeziRunnableLaunchUmbrellaTreeInstances;
    UHierarchicalInstancedStaticMeshComponent*& ZambeziRunnableLaunchThornScrubInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& ReviewedRockInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& TemperateWaterlineStructureInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& ChilkoOrganicShorelineGravelInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& ChilkoOrganicShorelineGroundCoverInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& PacuareOrganicShorelineRockInstances;
    UHierarchicalInstancedStaticMeshComponent*& PacuareOrganicShorelineGroundCoverInstances;
    UHierarchicalInstancedStaticMeshComponent*& PacuareOrganicShorelineShrubInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& PacuareScannedFernInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& PacuareForestFloorInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& ZambeziRunnableLaunchTalusInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& ZambeziDryScarpOutcropInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& ReviewedPineInstances;
    TArray<UHierarchicalInstancedStaticMeshComponent*>& FutaleufuScannedUnderstoryInstances;
};

struct FPlacementQueries
{
    bool bPhysicalCorridor;
    bool bZambeziWoodland;
    float ActiveRiverHalfWidth;
    TFunctionRef<FVector2D(float, float)> ResolveLogicalRiverPoint;
    TFunctionRef<float(const FVector2D&)> GetMinimumCenterlineDistanceCm;
    TFunctionRef<float(float)> GetConditionedWaterWorldZ;
    TFunctionRef<float(float, float)> GetLandscapeHeight;
    TFunctionRef<float(float, float)> GetLandscapeSlopeDegrees;
    TFunctionRef<int32(UHierarchicalInstancedStaticMeshComponent*, UStaticMesh*, const FVector2D&, float, const FRotator&, const FVector&)> AddGroundedInstance;
};

struct FPacuarePlacementCounts
{
    int32 PacuareShorelineRockPlacedCount;
    int32 PacuareShorelineGroundCoverPlacedCount;
    int32 PacuareScannedFernPlacedCount;
    int32 PacuareShorelineShrubPlacedCount;
    int32 PacuareForestFloorLeafLitterPlacedCount;
    int32 PacuareForestFloorWoodyPlacedCount;
};

struct FZambeziPlacementCounts
{
    int32 RunnableLaunchGroundCoverPlacedCount;
    int32 RunnableLaunchWoodyPlacedCount;
    bool bRunnableLaunchEcologyStrataValidated;
};

bool AddLandscapeCandidatePlacements(const FPlacementContext& Context);
FPacuarePlacementCounts AddPacuarePlacements(const FPlacementContext& Context, const FPlacementQueries& Queries);
FZambeziPlacementCounts AddZambeziLaunchPlacements(const FPlacementContext& Context, const FPlacementQueries& Queries);
}
