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
    // October (late dry season) Batoka woodland: deciduous trees bare or
    // holding a few dry leaves, thorn scrub leafless.
    DrySeasonBareTree,
    DrySeasonSparseTree,
    DrySeasonScrub,
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
// Loads the saved Zambezi family without rebuilding or re-saving it (the
// Zambezi upper gorge shares it with L_Zambezi).
bool LoadZambeziOpaqueVegetationAssets(
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
    // Station length of the physical centreline (0 when there is none).
    float CenterlineLengthM = 0.0f;
};

struct FPacuarePlacementCounts
{
    int32 PacuareShorelineRockPlacedCount;
    int32 PacuareShorelineGroundCoverPlacedCount;
    int32 PacuareScannedFernPlacedCount;
    int32 PacuareShorelineShrubPlacedCount;
    int32 PacuareForestFloorLeafLitterPlacedCount;
    int32 PacuareForestFloorWoodyPlacedCount;
    // Minimums scaled with the reach length like the targets (density per
    // metre of centreline, set on the 600 m straight Upper Huacas reach).
    int32 RockMinimum = PacuareOrganicShorelineRockMinimumInstanceCount;
    int32 GroundCoverMinimum = PacuareOrganicShorelineGroundCoverMinimumInstanceCount;
    int32 FernMinimum = PacuareScannedFernMinimumInstanceCount;
    int32 ShrubMinimum = PacuareOrganicShorelineShrubMinimumInstanceCount;
    int32 LeafLitterMinimum = PacuareForestFloorLeafLitterMinimumInstanceCount;
    int32 WoodyMinimum = PacuareForestFloorWoodyMinimumInstanceCount;
    // Evidence canopy over the whole Landscape window and emergent-rock
    // shells (placement JSON rows and the instances placed; 0 when the reach
    // has no placement).
    int32 EvidenceCanopyExpected = 0;
    int32 EvidenceCanopyPlaced = 0;
    int32 EvidenceRockExpected = 0;
    int32 EvidenceRockPlaced = 0;
};

struct FZambeziPlacementCounts
{
    int32 RunnableLaunchGroundCoverPlacedCount;
    int32 RunnableLaunchWoodyPlacedCount;
    bool bRunnableLaunchEcologyStrataValidated;
};

struct FEvidenceCanopyCounts
{
    int32 Expected = 0;
    int32 Placed = 0;
    int32 Trees = 0;
};

// Evidence dressing placements written beside a reach's terrain
// (RaftSimEditorLandscapeFoliageEvidence.cpp).
TSharedPtr<FJsonObject> LoadEvidencePlacement(
    const FString& TerrainFolder, const TCHAR* FileName, const TCHAR* Schema, FString& OutSummary);
// Forms 0 and 1 use the reach's broadleaf and conifer canopy meshes; forms
// 2.. use ExtraTreeForms in order. Understory rows whose optional sixth field
// (kind) is 1 use AltUnderstoryMesh when it is given.
FEvidenceCanopyCounts AddEvidenceCanopy(
    const FPlacementContext& Context, const FPlacementQueries& Queries, const FString& TerrainFolder,
    const TCHAR* FileName, const TCHAR* Schema, const TCHAR* ComponentPrefix, const TCHAR* ActorTag,
    const TCHAR* SourceDescription, TConstArrayView<UStaticMesh*> ExtraTreeForms = {},
    UStaticMesh* AltUnderstoryMesh = nullptr);
// The reach's observed rock colour for the reviewed rock meshes (grey
// granite on the Futaleufu, dark basalt on the Chilko; instances of
// M_RaftSim_ReviewedRockTinted, unreal/Scripts/create_tinted_rock_materials.py),
// or nullptr where the scan's own mossy material stays.
UMaterialInterface* LoadReachRockMaterial(const FString& RiverId, FString& OutSummary);
// October (late dry season) Zambezi forms: a leafless tree, a tree holding a
// few dry leaves and leafless scrub, saved once beside the Zambezi family.
bool LoadOrCreateZambeziDrySeasonVegetationAssets(
    UWorld* World, UMaterialInterface* Material, UStaticMesh*& OutBareTree, UStaticMesh*& OutSparseTree,
    UStaticMesh*& OutScrub, FString& OutSummary);

struct FObservedRockCounts
{
    int32 Expected = 0;
    int32 Placed = 0;
};

// Observed rock (bedrock outcrops, cliff blocks, waterline talus) written
// beside a reach's terrain (observed_rock_placement.json, schema
// raftsim.observed_rock_placement.v1, built by
// physics/scripts/build_observed_rock_placement.py from guidebook, outfitter,
// photo and video descriptions): the six reviewed rock meshes fitted to the
// described sizes on the Landscape. Positions and sizes are approximate;
// visual only (no collision, no water authority).
FObservedRockCounts AddObservedRockShells(
    const FPlacementContext& Context, const FPlacementQueries& Queries, const FString& TerrainFolder,
    const TCHAR* FileName, const TCHAR* ComponentPrefix, const TCHAR* ActorTag);

bool AddLandscapeCandidatePlacements(const FPlacementContext& Context);
FPacuarePlacementCounts AddPacuarePlacements(const FPlacementContext& Context, const FPlacementQueries& Queries);
FZambeziPlacementCounts AddZambeziLaunchPlacements(const FPlacementContext& Context, const FPlacementQueries& Queries);
// Patchy green riverine fringe (shrubs and riparian trees) at the waterline
// along the whole L_Zambezi reach; returns the instances placed.
int32 AddZambeziWaterlineFringe(const FPlacementContext& Context, const FPlacementQueries& Queries);
int32 AddZambeziGorgeWallRocks(const FPlacementContext& Context, const FPlacementQueries& Queries);
}
