#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/MaterialExpressionPerInstanceRandom.h"
#include "Materials/MaterialInstanceConstant.h"

namespace RaftSimEditorEnvironment
{
namespace
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
constexpr int32 PacuareOrganicShorelineShrubTargetInstanceCount = 1200;
constexpr int32 PacuareOrganicShorelineShrubMinimumInstanceCount = 1050;
constexpr float PacuareOrganicShorelineShrubSlopeCeilingDegrees = 38.0f;
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

float ZambeziVegetationUnitRandom(int32 Index, int32 Salt)
{
    uint32 Hash = static_cast<uint32>(Index) * 0x9E3779B9u;
    Hash ^= static_cast<uint32>(Salt) * 0x85EBCA6Bu;
    Hash ^= Hash >> 16;
    Hash *= 0x7FEB352Du;
    Hash ^= Hash >> 15;
    Hash *= 0x846CA68Bu;
    Hash ^= Hash >> 16;
    return static_cast<float>(Hash & 0x00FFFFFFu) / 16777215.0f;
}

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
    TArray<FLinearColor>& Colors)
{
    const int32 FirstVertex = Vertices.Num();
    AppendNativeCanopyTaperedSegment(
        Start,
        End,
        StartRadius,
        EndRadius,
        SideCount,
        Vertices,
        Triangles,
        Normals,
        Uvs);
    const int32 AddedVertexCount = Vertices.Num() - FirstVertex;
    for (int32 VertexIndex = 0; VertexIndex < AddedVertexCount; ++VertexIndex)
    {
        const bool bEndRing = VertexIndex >= AddedVertexCount / 2;
        Colors.Add(bEndRing ? EndColor : StartColor);
    }
}

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
    TArray<FLinearColor>& Colors)
{
    check(RingCount >= 3);
    check(SegmentCount >= 6);
    const int32 BottomIndex = Vertices.Num();
    Vertices.Add(Center - FVector::UpVector * Radii.Z);
    Normals.Add(-FVector::UpVector);
    Uvs.Add(FVector2D(0.5f, 1.0f));
    Colors.Add(ScalePreviewColor(BaseColor, 0.70f));

    const int32 FirstRingStart = Vertices.Num();
    for (int32 RingIndex = 0; RingIndex < RingCount; ++RingIndex)
    {
        const float RingT = static_cast<float>(RingIndex + 1) /
            static_cast<float>(RingCount + 1);
        const float Latitude = -0.5f * PI + RingT * PI;
        const float Radial = FMath::Cos(Latitude);
        const float UnitZ = FMath::Sin(Latitude);
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const float SegmentT = static_cast<float>(SegmentIndex) /
                static_cast<float>(SegmentCount);
            const float Longitude = SegmentT * UE_TWO_PI;
            const float EdgeNoise =
                0.94f +
                0.045f * FMath::Sin(
                    Longitude * (3.0f + static_cast<float>(Seed % 3)) +
                    static_cast<float>(RingIndex) * 0.83f + Seed * 0.19f) +
                0.020f * FMath::Sin(Longitude * 7.0f - Seed * 0.31f);
            const FVector Unit(
                Radial * FMath::Cos(Longitude) * EdgeNoise,
                Radial * FMath::Sin(Longitude) * EdgeNoise,
                UnitZ * (0.94f + 0.06f * FMath::Sin(Longitude * 2.0f + Seed)));
            Vertices.Add(Center + Unit * Radii);
            Normals.Add(FVector(
                Unit.X / FMath::Max(1.0f, Radii.X),
                Unit.Y / FMath::Max(1.0f, Radii.Y),
                Unit.Z / FMath::Max(1.0f, Radii.Z)).GetSafeNormal());
            Uvs.Add(FVector2D(SegmentT, 1.0f - RingT));
            const float Tint = 0.82f + 0.14f * RingT +
                0.06f * FMath::Sin(Longitude * 4.0f + Seed * 0.47f);
            Colors.Add(ScalePreviewColor(BaseColor, Tint));
        }
    }

    const int32 TopIndex = Vertices.Num();
    Vertices.Add(Center + FVector::UpVector * Radii.Z);
    Normals.Add(FVector::UpVector);
    Uvs.Add(FVector2D(0.5f, 0.0f));
    Colors.Add(ScalePreviewColor(BaseColor, 1.02f));

    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
        Triangles.Append({
            BottomIndex,
            FirstRingStart + NextSegment,
            FirstRingStart + SegmentIndex});
    }
    for (int32 RingIndex = 0; RingIndex < RingCount - 1; ++RingIndex)
    {
        const int32 LowerStart = FirstRingStart + RingIndex * SegmentCount;
        const int32 UpperStart = LowerStart + SegmentCount;
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
            Triangles.Append({
                LowerStart + SegmentIndex,
                UpperStart + NextSegment,
                UpperStart + SegmentIndex,
                LowerStart + SegmentIndex,
                LowerStart + NextSegment,
                UpperStart + NextSegment});
        }
    }
    const int32 LastRingStart =
        FirstRingStart + (RingCount - 1) * SegmentCount;
    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
        Triangles.Append({
            LastRingStart + SegmentIndex,
            LastRingStart + NextSegment,
            TopIndex});
    }
}

void AppendZambeziOpaqueLobe(
    const FVector& Center,
    const FVector& Radii,
    int32 Seed,
    const FLinearColor& BaseColor,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors)
{
    AppendOpaqueLobe(
        Center,
        Radii,
        Seed,
        BaseColor,
        8,
        16,
        Vertices,
        Triangles,
        Normals,
        Uvs,
        Colors);
}

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
    TArray<FLinearColor>& Colors)
{
    const int32 FirstVertex = Vertices.Num();
    AppendOpaqueLobe(
        Center,
        Radii,
        Seed,
        BaseColor,
        RingCount,
        SegmentCount,
        Vertices,
        Triangles,
        Normals,
        Uvs,
        Colors);
    for (int32 VertexIndex = FirstVertex;
         VertexIndex < Vertices.Num();
         ++VertexIndex)
    {
        Vertices[VertexIndex] = Center + Rotation.RotateVector(
            Vertices[VertexIndex] - Center);
    }
}

void AppendRainforestOpaqueCrownlet(
    const FVector& Center,
    const FVector& Radii,
    int32 Seed,
    const FLinearColor& BaseColor,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs,
    TArray<FLinearColor>& Colors)
{
    // One large low-resolution ellipsoid produced the repeated polygon fans
    // visible from the Upper Huacas guide cameras.  The V2 fallback keeps an
    // opaque, distance-stable core but wraps it in smaller oblique crownlets.
    // This is morphology-only presentation geometry: it has no collision,
    // species authority, wind authority, or terrain/hydraulic influence.
    const float CoreScale = FMath::Lerp(
        0.58f,
        0.68f,
        ZambeziVegetationUnitRandom(Seed, 6101));
    AppendOpaqueLobe(
        Center,
        Radii * FVector(
            CoreScale,
            CoreScale * 0.86f,
            CoreScale * 0.72f),
        Seed,
        ScalePreviewColor(BaseColor, 0.91f),
        10,
        20,
        Vertices,
        Triangles,
        Normals,
        Uvs,
        Colors);

    constexpr int32 LeafClusterCount = 6;
    for (int32 ClusterIndex = 0;
         ClusterIndex < LeafClusterCount;
         ++ClusterIndex)
    {
        const int32 ClusterSeed = Seed + 89 + ClusterIndex * 47;
        const float Angle =
            UE_TWO_PI * static_cast<float>(ClusterIndex) /
                static_cast<float>(LeafClusterCount) +
            Seed * 0.031f +
            FMath::Lerp(
                -0.24f,
                0.24f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6113));
        const float RadialScale = FMath::Lerp(
            0.32f,
            0.48f,
            ZambeziVegetationUnitRandom(ClusterSeed, 6121));
        const FVector Offset(
            FMath::Cos(Angle) * Radii.X * RadialScale,
            FMath::Sin(Angle) * Radii.Y * RadialScale,
            Radii.Z * FMath::Lerp(
                -0.24f,
                0.27f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6131)));
        const FVector ClusterRadii = Radii * FVector(
            FMath::Lerp(
                0.38f,
                0.52f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6133)),
            FMath::Lerp(
                0.22f,
                0.34f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6143)),
            FMath::Lerp(
                0.24f,
                0.38f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6151)));
        const FRotator ClusterRotation(
            FMath::Lerp(
                -20.0f,
                20.0f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6163)),
            FMath::RadiansToDegrees(Angle),
            FMath::Lerp(
                -13.0f,
                13.0f,
                ZambeziVegetationUnitRandom(ClusterSeed, 6173)));
        AppendOrientedRainforestLobe(
            Center + Offset,
            ClusterRadii,
            ClusterRotation,
            ClusterSeed,
            ScalePreviewColor(
                BaseColor,
                FMath::Lerp(
                    0.82f,
                    1.16f,
                    ZambeziVegetationUnitRandom(ClusterSeed, 6197))),
            6,
            12,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
    }
}

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
    TArray<FLinearColor>& Colors)
{
    if (bRainforestPalette)
    {
        AppendRainforestOpaqueCrownlet(
            Center,
            Radii,
            Seed,
            BaseColor,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        return;
    }

    // Build one continuous, asymmetric crownlet from four overlapping volumes.
    // This keeps the opaque, distance-stable fallback while removing the single
    // balloon/diamond silhouette that dominated the runnable river cameras.
    const float CoreScale = FMath::Lerp(
        0.84f,
        0.93f,
        ZambeziVegetationUnitRandom(Seed, 6029));
    AppendOpaqueLobe(
        Center,
        Radii * FVector(CoreScale, CoreScale * 0.96f, CoreScale * 1.04f),
        Seed,
        BaseColor,
        9,
        18,
        Vertices,
        Triangles,
        Normals,
        Uvs,
        Colors);

    constexpr int32 SatelliteLobeCount = 3;
    for (int32 LobeIndex = 0;
         LobeIndex < SatelliteLobeCount;
         ++LobeIndex)
    {
        const int32 LobeSeed = Seed + 71 + LobeIndex * 43;
        const float Angle =
            UE_TWO_PI * static_cast<float>(LobeIndex) /
                static_cast<float>(SatelliteLobeCount) +
            Seed * 0.037f +
            FMath::Lerp(
                -0.31f,
                0.31f,
                ZambeziVegetationUnitRandom(LobeSeed, 6037));
        const float RadialScale = FMath::Lerp(
            0.20f,
            0.31f,
            ZambeziVegetationUnitRandom(LobeSeed, 6043));
        const FVector LobeOffset(
            FMath::Cos(Angle) * Radii.X * RadialScale,
            FMath::Sin(Angle) * Radii.Y * RadialScale,
            Radii.Z * FMath::Lerp(
                -0.18f,
                0.20f,
                ZambeziVegetationUnitRandom(LobeSeed, 6053)));
        const FVector LobeRadii = Radii * FVector(
            FMath::Lerp(
                0.39f,
                0.49f,
                ZambeziVegetationUnitRandom(LobeSeed, 6067)),
            FMath::Lerp(
                0.36f,
                0.46f,
                ZambeziVegetationUnitRandom(LobeSeed, 6073)),
            FMath::Lerp(
                0.41f,
                0.52f,
                ZambeziVegetationUnitRandom(LobeSeed, 6079)));
        AppendOpaqueLobe(
            Center + LobeOffset,
            LobeRadii,
            LobeSeed,
            ScalePreviewColor(
                BaseColor,
                FMath::Lerp(
                    0.88f,
                    1.08f,
                    ZambeziVegetationUnitRandom(LobeSeed, 6089))),
            5,
            10,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
    }
}

UMaterial* CreateOpaqueVegetationMaterial(
    const TCHAR* MaterialPath,
    const TCHAR* ProfileLabel,
    float ShadowFillStrength,
    float InstanceEnergyMinimum,
    float InstanceEnergyMaximum,
    FString& OutSummary)
{
    const FString AssetName =
        FPackageName::GetLongPackageAssetName(MaterialPath);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"), MaterialPath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material
        ? Material->GetOutermost()
        : CreatePackage(MaterialPath);
    if (!Package)
    {
        return nullptr;
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->DitheredLODTransition = true;

    auto Add = [Material](auto* Expression)
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionVertexColor* VertexColor = Add(
        NewObject<UMaterialExpressionVertexColor>(Material));
    UMaterialExpressionPerInstanceRandom* InstanceRandom = Add(
        NewObject<UMaterialExpressionPerInstanceRandom>(Material));
    UMaterialExpressionVectorParameter* VegetationColorScale = Add(
        NewObject<UMaterialExpressionVectorParameter>(Material));
    VegetationColorScale->ParameterName = TEXT("VegetationColorScale");
    VegetationColorScale->DefaultValue = FLinearColor::White;
    VegetationColorScale->Group = TEXT("RaftSimOpaqueVegetation");
    UMaterialExpressionConstant* EnergyMinimum = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    EnergyMinimum->R = InstanceEnergyMinimum;
    UMaterialExpressionConstant* EnergyMaximum = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    EnergyMaximum->R = InstanceEnergyMaximum;
    UMaterialExpressionLinearInterpolate* InstanceEnergy = Add(
        NewObject<UMaterialExpressionLinearInterpolate>(Material));
    InstanceEnergy->A.Expression = EnergyMinimum;
    InstanceEnergy->B.Expression = EnergyMaximum;
    InstanceEnergy->Alpha.Expression = InstanceRandom;
    UMaterialExpressionMultiply* ScaledVertexColor = Add(
        NewObject<UMaterialExpressionMultiply>(Material));
    ScaledVertexColor->A.Expression = VertexColor;
    ScaledVertexColor->B.Expression = VegetationColorScale;
    UMaterialExpressionMultiply* VariedVertexColor = Add(
        NewObject<UMaterialExpressionMultiply>(Material));
    VariedVertexColor->A.Expression = ScaledVertexColor;
    VariedVertexColor->B.Expression = InstanceEnergy;
    UMaterialExpressionConstant* Roughness = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    Roughness->R = 0.91f;
    UMaterialExpressionConstant* Specular = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    Specular->R = 0.08f;
    UMaterialExpressionConstant* AmbientOcclusion = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    AmbientOcclusion->R = 1.0f;
    UMaterialExpressionConstant* ShadowFloor = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    ShadowFloor->R = ShadowFillStrength;
    UMaterialExpressionScalarParameter* VegetationShadowFillScale = Add(
        NewObject<UMaterialExpressionScalarParameter>(Material));
    VegetationShadowFillScale->ParameterName =
        TEXT("VegetationShadowFillScale");
    VegetationShadowFillScale->DefaultValue = 1.0f;
    VegetationShadowFillScale->Group = TEXT("RaftSimOpaqueVegetation");
    UMaterialExpressionMultiply* ScaledShadowFloor = Add(
        NewObject<UMaterialExpressionMultiply>(Material));
    ScaledShadowFloor->A.Expression = ShadowFloor;
    ScaledShadowFloor->B.Expression = VegetationShadowFillScale;
    UMaterialExpressionMultiply* ShadowFill = Add(
        NewObject<UMaterialExpressionMultiply>(Material));
    ShadowFill->A.Expression = VariedVertexColor;
    ShadowFill->B.Expression = ScaledShadowFloor;

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(
        EditorOnlyData->BaseColor, VariedVertexColor);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    ConnectPreviewMaterialScalarInput(
        EditorOnlyData->AmbientOcclusion, AmbientOcclusion);
    ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, ShadowFill);

    Material->SetUsageByFlag(MATUSAGE_InstancedStaticMeshes, true);
    Material->SetUsageByFlag(MATUSAGE_Nanite, true);
    Material->PostEditChange();
    Material->ForceRecompileForRendering();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
        GShaderCompilingManager->ProcessAsyncResults(false, true);
    }
    const FMaterialResource* Resource =
        Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (!Resource ||
        Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ||
        !Resource->GetCompileErrors().IsEmpty())
    {
        OutSummary += TEXT(
            "Opaque vegetation material failed its shader gate.\n");
        return nullptr;
    }

    Material->MarkPackageDirty();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        MaterialPath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to save %s opaque vegetation material.\n"),
            ProfileLabel);
        return nullptr;
    }
    return Material;
}

UMaterial* CreateZambeziOpaqueVegetationMaterial(FString& OutSummary)
{
    return CreateOpaqueVegetationMaterial(
        ZambeziVegetationMaterialPath,
        TEXT("Zambezi"),
        0.09f,
        1.0f,
        1.0f,
        OutSummary);
}

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
    FString& OutSummary)
{
    if (!World || !AssetToken || !Material || !MeshRoot || !ProfileLabel)
    {
        return nullptr;
    }

    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    const FLinearColor BarkBase = bHanceDrylandPalette
        ? FLinearColor(0.105f, 0.066f, 0.030f, 1.0f)
        : FLinearColor(0.175f, 0.125f, 0.070f, 1.0f);
    const FLinearColor BarkTip = bHanceDrylandPalette
        ? FLinearColor(0.142f, 0.091f, 0.040f, 1.0f)
        : FLinearColor(0.215f, 0.155f, 0.082f, 1.0f);
    const FLinearColor LeafGreen = Form == EZambeziVegetationForm::UmbrellaTree
        ? FLinearColor(0.060f, 0.088f, 0.022f, 1.0f)
        : FLinearColor(0.052f, 0.080f, 0.020f, 1.0f);
    const FLinearColor ScrubGreen = bHanceDrylandPalette
        ? FLinearColor(0.050f, 0.060f, 0.018f, 1.0f)
        : FLinearColor(0.050f, 0.075f, 0.018f, 1.0f);
    const FLinearColor DryGrass = bHanceDrylandPalette
        ? FLinearColor(0.180f, 0.118f, 0.035f, 1.0f)
        : FLinearColor(0.200f, 0.135f, 0.035f, 1.0f);
    const FLinearColor LowPlantGreen = bHanceDrylandPalette
        ? FLinearColor(0.055f, 0.068f, 0.018f, 1.0f)
        : FLinearColor(0.065f, 0.095f, 0.022f, 1.0f);
    const FLinearColor BladeGreen = bHanceDrylandPalette
        ? FLinearColor(0.070f, 0.082f, 0.020f, 1.0f)
        : FLinearColor(0.085f, 0.115f, 0.027f, 1.0f);

    if (Form == EZambeziVegetationForm::SavannaGroundCover)
    {
        AppendZambeziOpaqueLobe(
            FVector(0.0f, 0.0f, bSecondaryMorphology ? 8.0f : 10.0f),
            bSecondaryMorphology
                ? FVector(72.0f, 58.0f, 11.0f)
                : FVector(46.0f, 38.0f, 15.0f),
            Seed,
            ScalePreviewColor(DryGrass, 0.62f),
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        // One opaque mesh instance covers a several-metre patch.  This is
        // intentionally solid tapered geometry rather than masked crossed
        // cards, so the near banks break up organically without returning the
        // black/green card artifacts rejected by the visual review.
        const int32 BladeCount = bSecondaryMorphology ? 28 : 54;
        for (int32 BladeIndex = 0; BladeIndex < BladeCount; ++BladeIndex)
        {
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1201);
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Radius = FMath::Lerp(
                bSecondaryMorphology ? 18.0f : 12.0f,
                bSecondaryMorphology ? 275.0f : 240.0f,
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1213));
            const float Height = FMath::Lerp(
                bSecondaryMorphology ? 18.0f : 24.0f,
                bSecondaryMorphology ? 56.0f : 82.0f,
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1231));
            const float Lean = FMath::Lerp(
                5.0f,
                bSecondaryMorphology ? 38.0f : 28.0f,
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1249));
            const FVector Start = Direction * Radius;
            const FVector End = Start + Direction * Lean + FVector::UpVector * Height;
            const float Dryness = ZambeziVegetationUnitRandom(
                BladeIndex + Seed, 1277);
            const FLinearColor BladeColor = FMath::Lerp(
                BladeGreen,
                DryGrass,
                Dryness);
            AppendZambeziColoredSegment(
                Start,
                End,
                1.8f,
                0.42f,
                5,
                ScalePreviewColor(BladeColor, 0.72f),
                ScalePreviewColor(BladeColor, 1.08f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
        const int32 LowForbCount = bSecondaryMorphology ? 18 : 11;
        for (int32 ForbIndex = 0; ForbIndex < LowForbCount; ++ForbIndex)
        {
            const int32 RandomIndex = ForbIndex + Seed * 2;
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(RandomIndex, 1301);
            const float Radius = FMath::Lerp(
                34.0f,
                205.0f,
                ZambeziVegetationUnitRandom(RandomIndex, 1303));
            const float Scale = FMath::Lerp(
                0.72f,
                1.24f,
                ZambeziVegetationUnitRandom(RandomIndex, 1307));
            const FLinearColor ForbColor = FMath::Lerp(
                LowPlantGreen,
                DryGrass,
                ZambeziVegetationUnitRandom(RandomIndex, 1319));
            AppendZambeziOpaqueLobe(
                FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * Radius +
                    FVector::UpVector * (9.0f * Scale),
                (bSecondaryMorphology
                     ? FVector(29.0f, 23.0f, 9.0f)
                     : FVector(21.0f, 17.0f, 11.0f)) * Scale,
                RandomIndex,
                ForbColor,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else if (Form == EZambeziVegetationForm::ThornScrub)
    {
        const int32 StemCount = bSecondaryMorphology ? 19 : 13;
        for (int32 StemIndex = 0; StemIndex < StemCount; ++StemIndex)
        {
            const float Angle = UE_TWO_PI *
                static_cast<float>(StemIndex) / static_cast<float>(StemCount) +
                Seed * 0.17f;
            const FVector Direction(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Length = (bSecondaryMorphology ? 88.0f : 115.0f) +
                (bSecondaryMorphology ? 46.0f : 52.0f) *
                ZambeziVegetationUnitRandom(StemIndex + Seed, 1601);
            const FVector Start = Direction * 9.0f;
            const FVector Mid = Direction * Length * 0.48f +
                FVector::UpVector *
                    ((bSecondaryMorphology ? 58.0f : 75.0f) +
                     (bSecondaryMorphology ? 12.0f : 18.0f) *
                         (StemIndex % 3));
            const FVector End = Direction * Length +
                FVector::UpVector *
                    ((bSecondaryMorphology ? 104.0f : 125.0f) +
                     (bSecondaryMorphology ? 22.0f : 32.0f) *
                         (StemIndex % 4));
            AppendZambeziColoredSegment(
                Start,
                Mid,
                9.0f,
                5.0f,
                7,
                BarkBase,
                BarkTip,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendZambeziColoredSegment(
                Mid,
                End,
                5.0f,
                2.1f,
                6,
                BarkTip,
                ScalePreviewColor(BarkTip, 1.12f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendZambeziOpaqueLobe(
                End,
                (bSecondaryMorphology
                     ? FVector(82.0f, 68.0f, 34.0f)
                     : FVector(64.0f, 52.0f, 46.0f)) *
                    (0.86f + 0.12f * static_cast<float>(StemIndex % 4)),
                Seed + StemIndex * 17,
                ScrubGreen,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else
    {
        const bool bUmbrella = Form == EZambeziVegetationForm::UmbrellaTree;
        const FVector LowerTrunkEnd(
            bUmbrella ? 18.0f : -14.0f,
            bUmbrella ? -12.0f : 16.0f,
            bUmbrella ? 360.0f : 410.0f);
        const FVector UpperTrunkEnd(
            bUmbrella ? -8.0f : 24.0f,
            bUmbrella ? 14.0f : -18.0f,
            bUmbrella ? 555.0f : 610.0f);
        AppendZambeziColoredSegment(
            FVector::ZeroVector,
            LowerTrunkEnd,
            bUmbrella ? 48.0f : 42.0f,
            bUmbrella ? 29.0f : 25.0f,
            10,
            BarkBase,
            BarkTip,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        AppendZambeziColoredSegment(
            LowerTrunkEnd,
            UpperTrunkEnd,
            bUmbrella ? 29.0f : 25.0f,
            15.0f,
            9,
            BarkTip,
            ScalePreviewColor(BarkTip, 1.16f),
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);

        constexpr int32 RootCount = 7;
        for (int32 RootIndex = 0; RootIndex < RootCount; ++RootIndex)
        {
            const float Angle = UE_TWO_PI * static_cast<float>(RootIndex) /
                static_cast<float>(RootCount) + Seed * 0.11f;
            AppendZambeziColoredSegment(
                FVector(0.0f, 0.0f, 18.0f),
                FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) *
                    (92.0f + 12.0f * static_cast<float>(RootIndex % 3)),
                18.0f,
                4.0f,
                7,
                BarkBase,
                ScalePreviewColor(BarkBase, 0.82f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }

        const int32 BranchCount = bUmbrella ? 14 : 12;
        for (int32 BranchIndex = 0; BranchIndex < BranchCount; ++BranchIndex)
        {
            const float Angle = FMath::Fmod(
                137.50776f * BranchIndex + Seed * 23.0f,
                360.0f) * PI / 180.0f;
            const FVector Direction(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Radius = bUmbrella
                ? 315.0f + 34.0f * static_cast<float>(BranchIndex % 4)
                : 250.0f + 42.0f * static_cast<float>(BranchIndex % 5);
            const float StartZ = bUmbrella
                ? 390.0f + 22.0f * static_cast<float>(BranchIndex % 5)
                : 380.0f + 31.0f * static_cast<float>(BranchIndex % 6);
            const float EndZ = bUmbrella
                ? 575.0f + 28.0f * static_cast<float>(BranchIndex % 3)
                : 590.0f + 55.0f * static_cast<float>(BranchIndex % 5);
            const FVector Start(0.0f, 0.0f, StartZ);
            const FVector Mid = Direction * Radius * 0.48f +
                FVector::UpVector * FMath::Lerp(StartZ, EndZ, 0.62f);
            const FVector End = Direction * Radius + FVector::UpVector * EndZ;
            AppendZambeziColoredSegment(
                Start,
                Mid,
                15.0f,
                8.0f,
                8,
                BarkTip,
                ScalePreviewColor(BarkTip, 1.10f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendZambeziColoredSegment(
                Mid,
                End,
                8.0f,
                3.2f,
                7,
                ScalePreviewColor(BarkTip, 1.10f),
                ScalePreviewColor(BarkTip, 1.18f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            const FVector LobeRadii = bUmbrella
                ? FVector(188.0f, 132.0f, 72.0f) *
                    (0.88f + 0.08f * static_cast<float>(BranchIndex % 4))
                : FVector(154.0f, 126.0f, 112.0f) *
                    (0.86f + 0.09f * static_cast<float>(BranchIndex % 4));
            AppendZambeziOpaqueLobe(
                End + FVector::UpVector * (bUmbrella ? 18.0f : 34.0f),
                LobeRadii,
                Seed + BranchIndex * 29,
                LeafGreen,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }

        constexpr int32 CrownFillCount = 5;
        for (int32 FillIndex = 0; FillIndex < CrownFillCount; ++FillIndex)
        {
            const float Angle = UE_TWO_PI * static_cast<float>(FillIndex) /
                static_cast<float>(CrownFillCount) + Seed * 0.07f;
            const FVector Center(
                FMath::Cos(Angle) * (bUmbrella ? 118.0f : 92.0f),
                FMath::Sin(Angle) * (bUmbrella ? 118.0f : 92.0f),
                bUmbrella ? 628.0f : 690.0f + 34.0f * (FillIndex % 2));
            AppendZambeziOpaqueLobe(
                Center,
                bUmbrella
                    ? FVector(205.0f, 155.0f, 76.0f)
                    : FVector(168.0f, 142.0f, 128.0f),
                Seed + 500 + FillIndex * 37,
                ScalePreviewColor(LeafGreen, 0.94f + 0.03f * FillIndex),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }

    if (Vertices.IsEmpty() || Triangles.IsEmpty() ||
        Colors.Num() != Vertices.Num() || Uvs.Num() != Vertices.Num())
    {
        OutSummary += FString::Printf(
            TEXT("%s vegetation geometry contract failed for %s.\n"),
            ProfileLabel,
            AssetToken);
        return nullptr;
    }
    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* TemporaryActor = AddPreviewProceduralMeshActor(
        World,
        FString::Printf(
            TEXT("RaftSim_%s_%s_BuildSource"), ProfileLabel, AssetToken),
        Vertices,
        Triangles,
        Normals,
        Uvs,
        FLinearColor::White,
        Material,
        &Colors,
        false);
    if (!TemporaryActor)
    {
        return nullptr;
    }
    const FString PackagePath = FString(MeshRoot) + AssetToken;
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor,
        PackagePath,
        Material,
        true,
        ENaniteShapePreservation::None,
        OutSummary);
    TemporaryActor->Destroy();
    if (Mesh)
    {
        OutSummary += FString::Printf(
            TEXT("Prepared %s %s opaque volumetric vegetation: "
                 "vertices=%d triangles=%d Nanite=%d collision=false.\n"),
            ProfileLabel,
            AssetToken,
            Mesh->GetNumVertices(0),
            Mesh->GetNumTriangles(0),
            Mesh->IsNaniteEnabled());
    }
    return Mesh;
}

bool CreateZambeziOpaqueVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutRiparianTree,
    UStaticMesh*& OutUmbrellaTree,
    UStaticMesh*& OutThornScrub,
    UStaticMesh*& OutGroundCoverA,
    UStaticMesh*& OutGroundCoverB,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary)
{
    OutMaterial = CreateZambeziOpaqueVegetationMaterial(OutSummary);
    if (!OutMaterial)
    {
        return false;
    }
    OutRiparianTree = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_RiparianTree_A_OpaqueV1"),
        EZambeziVegetationForm::RiparianTree,
        1709,
        OutMaterial,
        ZambeziVegetationMeshRoot,
        TEXT("Zambezi"),
        false,
        false,
        OutSummary);
    OutUmbrellaTree = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_UmbrellaTree_B_OpaqueV1"),
        EZambeziVegetationForm::UmbrellaTree,
        2713,
        OutMaterial,
        ZambeziVegetationMeshRoot,
        TEXT("Zambezi"),
        false,
        false,
        OutSummary);
    OutThornScrub = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_ThornScrub_A_OpaqueV1"),
        EZambeziVegetationForm::ThornScrub,
        3907,
        OutMaterial,
        ZambeziVegetationMeshRoot,
        TEXT("Zambezi"),
        false,
        false,
        OutSummary);
    OutGroundCoverA = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_SavannaGroundCover_A_OpaqueV1"),
        EZambeziVegetationForm::SavannaGroundCover,
        4933,
        OutMaterial,
        ZambeziVegetationMeshRoot,
        TEXT("Zambezi"),
        false,
        false,
        OutSummary);
    OutGroundCoverB = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_SavannaGroundCover_B_OpaqueV2"),
        EZambeziVegetationForm::SavannaGroundCover,
        5077,
        OutMaterial,
        ZambeziVegetationMeshRoot,
        TEXT("Zambezi"),
        false,
        true,
        OutSummary);
    const bool bComplete =
        OutRiparianTree && OutUmbrellaTree && OutThornScrub &&
        OutGroundCoverA && OutGroundCoverB;
    if (!bComplete)
    {
        OutSummary += TEXT(
            "Failed to build the complete Zambezi opaque vegetation family.\n");
    }
    return bComplete;
}

bool CreateHanceOpaqueDrylandVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutShrubA,
    UStaticMesh*& OutShrubB,
    UStaticMesh*& OutGroundCoverA,
    UStaticMesh*& OutGroundCoverB,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary)
{
    OutMaterial = CreateOpaqueVegetationMaterial(
        HanceDrylandVegetationMaterialPath,
        TEXT("Colorado Hance dryland"),
        0.045f,
        1.0f,
        1.0f,
        OutSummary);
    if (!OutMaterial)
    {
        return false;
    }
    OutShrubA = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Hance_DesertShrub_A_OpaqueV2"),
        EZambeziVegetationForm::ThornScrub,
        7307,
        OutMaterial,
        HanceDrylandVegetationMeshRoot,
        TEXT("HanceDryland"),
        true,
        false,
        OutSummary);
    OutShrubB = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Hance_DesertShrub_B_OpaqueV2"),
        EZambeziVegetationForm::ThornScrub,
        7351,
        OutMaterial,
        HanceDrylandVegetationMeshRoot,
        TEXT("HanceDryland"),
        true,
        true,
        OutSummary);
    OutGroundCoverA = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Hance_DryGroundCover_A_OpaqueV2"),
        EZambeziVegetationForm::SavannaGroundCover,
        7411,
        OutMaterial,
        HanceDrylandVegetationMeshRoot,
        TEXT("HanceDryland"),
        true,
        false,
        OutSummary);
    OutGroundCoverB = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Hance_DryGroundCover_B_OpaqueV2"),
        EZambeziVegetationForm::SavannaGroundCover,
        7457,
        OutMaterial,
        HanceDrylandVegetationMeshRoot,
        TEXT("HanceDryland"),
        true,
        true,
        OutSummary);
    if (!OutShrubA || !OutShrubB || !OutGroundCoverA || !OutGroundCoverB)
    {
        OutSummary += TEXT(
            "Failed to build the Hance opaque dryland vegetation family.\n");
        return false;
    }
    return true;
}

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
    FString& OutSummary)
{
    if (!World || !AssetToken || !Material)
    {
        return nullptr;
    }

    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    // These are linear-space radiance values under a 4.75-5.05 lux review
    // sun. The former preview-green values clipped into pale mint balloons
    // once solid lobes stopped casting their invalid card-like shadows.
    const FLinearColor BarkBase = bRainforestPalette
        ? FLinearColor(0.038f, 0.029f, 0.019f, 1.0f)
        : FLinearColor(0.060f, 0.040f, 0.025f, 1.0f);
    const FLinearColor BarkTip = bRainforestPalette
        ? FLinearColor(0.060f, 0.048f, 0.029f, 1.0f)
        : FLinearColor(0.082f, 0.058f, 0.035f, 1.0f);
    const FLinearColor BroadleafGreen = bRainforestPalette
        ? FLinearColor(0.020f, 0.082f, 0.030f, 1.0f)
        : FLinearColor(0.032f, 0.098f, 0.047f, 1.0f);
    const FLinearColor ConiferGreen = bRainforestPalette
        ? FLinearColor(0.026f, 0.096f, 0.038f, 1.0f)
        : FLinearColor(0.026f, 0.078f, 0.044f, 1.0f);
    const FLinearColor ShrubGreen = bRainforestPalette
        ? FLinearColor(0.030f, 0.110f, 0.040f, 1.0f)
        : FLinearColor(0.035f, 0.090f, 0.042f, 1.0f);
    const FLinearColor GroundGreen = bRainforestPalette
        ? FLinearColor(0.038f, 0.125f, 0.044f, 1.0f)
        : FLinearColor(0.040f, 0.100f, 0.045f, 1.0f);

    if (Form == ETemperateVegetationForm::GroundCover)
    {
        AppendTemperateOpaqueLobe(
            FVector(0.0f, 0.0f, 8.0f),
            FVector(74.0f, 60.0f, 16.0f),
            Seed,
            ScalePreviewColor(GroundGreen, 0.66f),
            bRainforestPalette,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        const int32 BladeCount = bRainforestPalette ? 72 : 58;
        for (int32 BladeIndex = 0; BladeIndex < BladeCount; ++BladeIndex)
        {
            const int32 RandomIndex = Seed + BladeIndex;
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(RandomIndex, 5101);
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Radius = FMath::Lerp(
                10.0f,
                225.0f,
                ZambeziVegetationUnitRandom(RandomIndex, 5113));
            const float Height = FMath::Lerp(
                28.0f,
                96.0f,
                ZambeziVegetationUnitRandom(RandomIndex, 5119));
            const FLinearColor BladeColor = FMath::Lerp(
                bRainforestPalette
                    ? FLinearColor(0.028f, 0.105f, 0.034f, 1.0f)
                    : FLinearColor(0.105f, 0.245f, 0.085f, 1.0f),
                bRainforestPalette
                    ? FLinearColor(0.050f, 0.135f, 0.042f, 1.0f)
                    : FLinearColor(0.19f, 0.25f, 0.095f, 1.0f),
                ZambeziVegetationUnitRandom(RandomIndex, 5147));
            AppendZambeziColoredSegment(
                Direction * Radius,
                Direction * (Radius + 12.0f) + FVector::UpVector * Height,
                1.7f,
                0.38f,
                5,
                ScalePreviewColor(BladeColor, 0.72f),
                ScalePreviewColor(BladeColor, 1.08f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
        const int32 ForbCount = bRainforestPalette ? 26 : 18;
        for (int32 ForbIndex = 0; ForbIndex < ForbCount; ++ForbIndex)
        {
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(Seed + ForbIndex, 5209);
            const float Radius = FMath::Lerp(
                28.0f,
                205.0f,
                ZambeziVegetationUnitRandom(Seed + ForbIndex, 5227));
            AppendTemperateOpaqueLobe(
                FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * Radius +
                    FVector::UpVector * 16.0f,
                FVector(28.0f, 20.0f, 13.0f),
                Seed + ForbIndex * 31,
                ScalePreviewColor(
                    GroundGreen,
                    0.76f + 0.28f * ZambeziVegetationUnitRandom(
                        Seed + ForbIndex, 5231)),
                bRainforestPalette,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else if (Form == ETemperateVegetationForm::RiparianShrub)
    {
        const int32 StemCount = bRainforestPalette ? 20 : 16;
        for (int32 StemIndex = 0; StemIndex < StemCount; ++StemIndex)
        {
            const float Angle = UE_TWO_PI * static_cast<float>(StemIndex) /
                static_cast<float>(StemCount) + Seed * 0.13f;
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Length = 90.0f + 75.0f *
                ZambeziVegetationUnitRandom(Seed + StemIndex, 5407);
            const FVector Mid = Direction * Length * 0.45f +
                FVector::UpVector * (72.0f + 12.0f * (StemIndex % 4));
            const FVector End = Direction * Length +
                FVector::UpVector * (145.0f + 24.0f * (StemIndex % 5));
            AppendZambeziColoredSegment(
                FVector::ZeroVector,
                Mid,
                7.5f,
                4.0f,
                7,
                BarkBase,
                BarkTip,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendZambeziColoredSegment(
                Mid,
                End,
                4.0f,
                1.6f,
                6,
                BarkTip,
                ScalePreviewColor(BarkTip, 1.10f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            AppendTemperateOpaqueLobe(
                End,
                FVector(66.0f, 54.0f, 48.0f) *
                    (0.84f + 0.10f * static_cast<float>(StemIndex % 4)),
                Seed + StemIndex * 19,
                ShrubGreen,
                bRainforestPalette,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else if (Form == ETemperateVegetationForm::ConiferTree &&
             !bRainforestPalette)
    {
        constexpr float TreeHeightCm = 850.0f;
        AppendZambeziColoredSegment(
            FVector::ZeroVector,
            FVector(8.0f, -7.0f, TreeHeightCm),
            42.0f,
            7.0f,
            10,
            BarkBase,
            BarkTip,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        constexpr int32 TierCount = 11;
        for (int32 TierIndex = 0; TierIndex < TierCount; ++TierIndex)
        {
            const float TierT = static_cast<float>(TierIndex) /
                static_cast<float>(TierCount - 1);
            const float TierZ = FMath::Lerp(160.0f, 845.0f, TierT) +
                FMath::Lerp(
                    -18.0f,
                    18.0f,
                    ZambeziVegetationUnitRandom(Seed + TierIndex, 5651));
            const float TierRadius = FMath::Lerp(310.0f, 62.0f, TierT) *
                FMath::Lerp(
                    0.88f,
                    1.12f,
                    ZambeziVegetationUnitRandom(Seed + TierIndex, 5659));
            const int32 BranchCount = 6 + FMath::Clamp(
                FMath::FloorToInt(
                    3.0f * ZambeziVegetationUnitRandom(
                        Seed + TierIndex,
                        5663)),
                0,
                2);
            const float TierRotation = FMath::Lerp(
                -0.24f,
                0.24f,
                ZambeziVegetationUnitRandom(Seed + TierIndex, 5667));
            for (int32 BranchIndex = 0;
                 BranchIndex < BranchCount;
                 ++BranchIndex)
            {
                const int32 BranchSeed = Seed + TierIndex * 107 +
                    BranchIndex * 23;
                const bool bStormShortenedBranch =
                    BranchIndex == BranchCount - 1 && BranchCount > 5 &&
                    ZambeziVegetationUnitRandom(BranchSeed, 5668) < 0.22f;
                const float Angle = UE_TWO_PI *
                        static_cast<float>(BranchIndex) /
                        static_cast<float>(BranchCount) +
                    TierIndex * 0.43f + Seed * 0.017f + TierRotation +
                    FMath::Lerp(
                        -0.15f,
                        0.15f,
                        ZambeziVegetationUnitRandom(
                            Seed + TierIndex * 17 + BranchIndex,
                            5669));
                const FVector Direction(
                    FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
                const float BranchLengthScale = FMath::Lerp(
                    0.84f,
                    1.15f,
                    ZambeziVegetationUnitRandom(BranchSeed, 5671)) *
                    (bStormShortenedBranch ? 0.62f : 1.0f);
                const float BranchZOffset = FMath::Lerp(
                    -24.0f,
                    24.0f,
                    ZambeziVegetationUnitRandom(BranchSeed, 5677));
                const FVector Start(
                    8.0f * TierT,
                    -7.0f * TierT,
                    TierZ + BranchZOffset);
                const FVector End =
                    Start + Direction * TierRadius * BranchLengthScale +
                    FVector::UpVector *
                        FMath::Lerp(-18.0f, 48.0f, TierT);
                AppendZambeziColoredSegment(
                    Start,
                    End,
                    FMath::Lerp(10.0f, 4.0f, TierT),
                    1.8f,
                    6,
                    BarkTip,
                    ScalePreviewColor(BarkTip, 1.08f),
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
                AppendTemperateOpaqueLobe(
                    FMath::Lerp(Start, End, 0.37f) +
                        FVector::UpVector * 10.0f,
                    FVector(
                        FMath::Lerp(70.0f, 34.0f, TierT),
                        FMath::Lerp(52.0f, 27.0f, TierT),
                        FMath::Lerp(42.0f, 25.0f, TierT)) *
                        FMath::Lerp(
                            0.86f,
                            1.12f,
                            ZambeziVegetationUnitRandom(BranchSeed, 5683)),
                    BranchSeed,
                    ScalePreviewColor(
                        ConiferGreen,
                        0.80f + 0.18f *
                            ZambeziVegetationUnitRandom(BranchSeed, 5689)),
                    bRainforestPalette,
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
                AppendTemperateOpaqueLobe(
                    FMath::Lerp(Start, End, 0.68f),
                    FVector(
                        FMath::Lerp(80.0f, 38.0f, TierT),
                        FMath::Lerp(56.0f, 30.0f, TierT),
                        FMath::Lerp(34.0f, 24.0f, TierT)),
                    Seed + TierIndex * 101 + BranchIndex * 13,
                    ScalePreviewColor(
                        ConiferGreen,
                        0.82f + 0.16f * ZambeziVegetationUnitRandom(
                            TierIndex + BranchIndex, Seed)),
                    bRainforestPalette,
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
                AppendTemperateOpaqueLobe(
                    End,
                    FVector(
                        FMath::Lerp(92.0f, 42.0f, TierT),
                        FMath::Lerp(60.0f, 32.0f, TierT),
                        FMath::Lerp(38.0f, 24.0f, TierT)),
                    Seed + TierIndex * 103 + BranchIndex * 17,
                    ConiferGreen,
                    bRainforestPalette,
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
            }

            const float ConiferCrownBodyScale = FMath::Lerp(
                0.68f,
                0.82f,
                ZambeziVegetationUnitRandom(Seed + TierIndex, 5767));
            const FVector CrownBodyCenter(
                8.0f * TierT + FMath::Lerp(
                    -18.0f,
                    18.0f,
                    ZambeziVegetationUnitRandom(Seed + TierIndex, 5779)),
                -7.0f * TierT + FMath::Lerp(
                    -16.0f,
                    16.0f,
                    ZambeziVegetationUnitRandom(Seed + TierIndex, 5783)),
                TierZ + FMath::Lerp(
                    -10.0f,
                    18.0f,
                    ZambeziVegetationUnitRandom(Seed + TierIndex, 5791)));
            AppendTemperateOpaqueLobe(
                CrownBodyCenter,
                FVector(
                    TierRadius * ConiferCrownBodyScale,
                    TierRadius * ConiferCrownBodyScale * 0.91f,
                    FMath::Lerp(112.0f, 54.0f, TierT)),
                Seed + 1301 + TierIndex * 61,
                ScalePreviewColor(
                    ConiferGreen,
                    FMath::Lerp(
                        0.80f,
                        0.98f,
                        ZambeziVegetationUnitRandom(
                            Seed + TierIndex,
                            5801))),
                bRainforestPalette,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
        AppendTemperateOpaqueLobe(
            FVector(0.0f, 0.0f, 900.0f),
            FVector(54.0f, 48.0f, 92.0f),
            Seed + 991,
            ConiferGreen,
            bRainforestPalette,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
    }
    else
    {
        const bool bRainforestCanopyB =
            bRainforestPalette && Form == ETemperateVegetationForm::ConiferTree;
        const float LowerTrunkHeight = bRainforestCanopyB ? 470.0f : 410.0f;
        const float UpperTrunkHeight = bRainforestCanopyB ? 770.0f : 650.0f;
        const FVector LowerTrunkEnd(-12.0f, 10.0f, LowerTrunkHeight);
        const FVector UpperTrunkEnd(18.0f, -14.0f, UpperTrunkHeight);
        AppendZambeziColoredSegment(
            FVector::ZeroVector,
            LowerTrunkEnd,
            46.0f,
            28.0f,
            10,
            BarkBase,
            BarkTip,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        AppendZambeziColoredSegment(
            LowerTrunkEnd,
            UpperTrunkEnd,
            28.0f,
            12.0f,
            9,
            BarkTip,
            ScalePreviewColor(BarkTip, 1.12f),
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        const int32 BranchCount = bRainforestPalette ? 17 : 13;
        for (int32 BranchIndex = 0; BranchIndex < BranchCount; ++BranchIndex)
        {
            const float Angle = FMath::Fmod(
                137.50776f * BranchIndex + Seed * 19.0f,
                360.0f) * PI / 180.0f;
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Radius = bRainforestPalette
                ? FMath::Lerp(
                      bRainforestCanopyB ? 145.0f : 185.0f,
                      bRainforestCanopyB ? 285.0f : 345.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex, 5843))
                : FMath::Lerp(
                      205.0f,
                      355.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex,
                          5843));
            const float StartZ = bRainforestPalette
                ? FMath::Lerp(
                      LowerTrunkHeight * 0.80f,
                      UpperTrunkHeight * 0.94f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex, 5851))
                : FMath::Lerp(
                      365.0f,
                      535.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex,
                          5851));
            const float EndZ = bRainforestPalette
                ? UpperTrunkHeight + FMath::Lerp(
                      -95.0f,
                      bRainforestCanopyB ? 105.0f : 155.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex, 5861))
                : FMath::Lerp(
                      585.0f,
                      790.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex,
                          5861));
            const FVector Start(0.0f, 0.0f, StartZ);
            const FVector End = Direction * Radius + FVector::UpVector * EndZ;
            AppendZambeziColoredSegment(
                Start,
                End,
                13.0f,
                3.0f,
                7,
                BarkTip,
                ScalePreviewColor(BarkTip, 1.10f),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            const float CrownScale = bRainforestPalette
                ? FMath::Lerp(
                      0.72f,
                      1.18f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex, 5879))
                : FMath::Lerp(
                      0.78f,
                      1.12f,
                      ZambeziVegetationUnitRandom(
                          Seed + BranchIndex,
                          5879));
            const FVector CrownRadii = bRainforestPalette
                ? FVector(
                      bRainforestCanopyB ? 112.0f : 138.0f,
                      bRainforestCanopyB ? 92.0f : 112.0f,
                      bRainforestCanopyB ? 88.0f : 96.0f) * CrownScale
                : FVector(158.0f, 132.0f, 112.0f) * CrownScale;
            AppendTemperateOpaqueLobe(
                End + FVector::UpVector * (18.0f + 18.0f * CrownScale),
                CrownRadii,
                Seed + BranchIndex * 29,
                ScalePreviewColor(
                    BroadleafGreen,
                    0.84f + 0.14f * ZambeziVegetationUnitRandom(
                        Seed + BranchIndex, 5903)),
                bRainforestPalette,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
            if (bRainforestPalette && BranchIndex % 2 == 0)
            {
                const FVector Tangent(-Direction.Y, Direction.X, 0.0f);
                AppendTemperateOpaqueLobe(
                    End - Direction * (38.0f + 24.0f * CrownScale) +
                        Tangent * (BranchIndex % 4 < 2 ? 34.0f : -34.0f) +
                        FVector::UpVector * 58.0f,
                    CrownRadii * FVector(0.66f, 0.72f, 0.72f),
                    Seed + BranchIndex * 41 + 17,
                    ScalePreviewColor(BroadleafGreen, 0.92f),
                    bRainforestPalette,
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
            }
        }
        const int32 CrownFillCount = bRainforestPalette ? 10 : 8;
        for (int32 FillIndex = 0; FillIndex < CrownFillCount; ++FillIndex)
        {
            const float Angle = UE_TWO_PI * static_cast<float>(FillIndex) /
                static_cast<float>(CrownFillCount) + Seed * 0.05f;
            const float FillRadius = bRainforestPalette
                ? FMath::Lerp(
                      45.0f,
                      bRainforestCanopyB ? 115.0f : 155.0f,
                      ZambeziVegetationUnitRandom(Seed + FillIndex, 5923))
                : FMath::Lerp(
                      52.0f,
                      138.0f,
                      ZambeziVegetationUnitRandom(
                          Seed + FillIndex,
                          5923));
            const float FillScale = bRainforestPalette
                ? FMath::Lerp(
                      0.62f,
                      1.08f,
                      ZambeziVegetationUnitRandom(Seed + FillIndex, 5939))
                : FMath::Lerp(
                      0.82f,
                      1.10f,
                      ZambeziVegetationUnitRandom(
                          Seed + FillIndex,
                          5939));
            AppendTemperateOpaqueLobe(
                FVector(
                    FMath::Cos(Angle) * FillRadius,
                    FMath::Sin(Angle) * FillRadius,
                    (bRainforestPalette ? UpperTrunkHeight + 70.0f : 700.0f) +
                        (bRainforestPalette
                             ? FMath::Lerp(
                                   -52.0f,
                                   98.0f,
                                   ZambeziVegetationUnitRandom(
                                       Seed + FillIndex, 5953))
                             : FMath::Lerp(
                                   -82.0f,
                                   92.0f,
                                   ZambeziVegetationUnitRandom(
                                       Seed + FillIndex,
                                       5953)))),
                FVector(172.0f, 145.0f, 126.0f) * FillScale,
                Seed + 700 + FillIndex * 37,
                BroadleafGreen,
                bRainforestPalette,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }

    if (bSecondaryMorphology && !bRainforestPalette)
    {
        // The B family is a different deterministic plant silhouette, not an
        // instance-scale variation. Seeded branch/crown placement above is
        // combined with form-specific proportions and a bounded growth lean.
        // The transform is baked into the mesh before normals are recomputed.
        for (FVector& Vertex : Vertices)
        {
            const float HeightT = FMath::Clamp(Vertex.Z / 1100.0f, 0.0f, 1.0f);
            if (Form == ETemperateVegetationForm::ConiferTree)
            {
                Vertex.X = Vertex.X * 0.80f + 44.0f * HeightT * HeightT;
                Vertex.Y *= 0.87f;
                Vertex.Z *= 1.18f;
            }
            else if (Form == ETemperateVegetationForm::BroadleafTree)
            {
                Vertex.X = Vertex.X * 0.79f - 38.0f * HeightT * HeightT;
                Vertex.Y *= 0.93f;
                Vertex.Z *= 1.16f;
            }
            else if (Form == ETemperateVegetationForm::RiparianShrub)
            {
                Vertex.X = Vertex.X * 1.22f + 18.0f * HeightT;
                Vertex.Y *= 0.76f;
                Vertex.Z *= 1.08f;
            }
            else
            {
                Vertex.X *= 1.18f;
                Vertex.Y *= 0.82f;
                Vertex.Z *= 0.86f;
            }
        }
    }

    if (Vertices.IsEmpty() || Triangles.IsEmpty() ||
        Colors.Num() != Vertices.Num() || Uvs.Num() != Vertices.Num())
    {
        OutSummary += FString::Printf(
            TEXT("Temperate vegetation geometry contract failed for %s.\n"),
            AssetToken);
        return nullptr;
    }
    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* TemporaryActor = AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_Temperate_%s_BuildSource"), AssetToken),
        Vertices,
        Triangles,
        Normals,
        Uvs,
        FLinearColor::White,
        Material,
        &Colors,
        false);
    if (!TemporaryActor)
    {
        return nullptr;
    }
    const FString PackagePath = FString(MeshRoot) + AssetToken;
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor,
        PackagePath,
        Material,
        true,
        ENaniteShapePreservation::None,
        OutSummary);
    TemporaryActor->Destroy();
    if (Mesh)
    {
        OutSummary += FString::Printf(
            TEXT("Prepared %s %s opaque volumetric vegetation: "
                 "vertices=%d triangles=%d Nanite=%d collision=false.\n"),
            ProfileLabel,
            AssetToken,
            Mesh->GetNumVertices(0),
            Mesh->GetNumTriangles(0),
            Mesh->IsNaniteEnabled());
    }
    return Mesh;
}

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
    FString& OutSummary)
{
    OutMaterial = CreateOpaqueVegetationMaterial(
        TemperateVegetationMaterialPath,
        TEXT("temperate-river"),
        0.06f,
        0.88f,
        1.13f,
        OutSummary);
    if (!OutMaterial)
    {
        return false;
    }
    OutBroadleafTreeA = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_BroadleafTree_A_OpaqueV1"),
        ETemperateVegetationForm::BroadleafTree,
        6101,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        false,
        OutSummary);
    OutBroadleafTreeB = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_BroadleafTree_B_OpaqueV1"),
        ETemperateVegetationForm::BroadleafTree,
        6113,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        true,
        OutSummary);
    OutConiferTreeA = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_ConiferTree_A_OpaqueV1"),
        ETemperateVegetationForm::ConiferTree,
        6203,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        false,
        OutSummary);
    OutConiferTreeB = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_ConiferTree_B_OpaqueV1"),
        ETemperateVegetationForm::ConiferTree,
        6217,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        true,
        OutSummary);
    OutShrubA = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_RiparianShrub_A_OpaqueV1"),
        ETemperateVegetationForm::RiparianShrub,
        6301,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        false,
        OutSummary);
    OutShrubB = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_RiparianShrub_B_OpaqueV1"),
        ETemperateVegetationForm::RiparianShrub,
        6317,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        true,
        OutSummary);
    OutGroundCoverA = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_GroundCover_A_OpaqueV1"),
        ETemperateVegetationForm::GroundCover,
        6421,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        false,
        OutSummary);
    OutGroundCoverB = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_GroundCover_B_OpaqueV1"),
        ETemperateVegetationForm::GroundCover,
        6437,
        OutMaterial,
        TemperateVegetationMeshRoot,
        TEXT("temperate-river"),
        false,
        true,
        OutSummary);
    const bool bComplete =
        OutBroadleafTreeA && OutBroadleafTreeB &&
        OutConiferTreeA && OutConiferTreeB &&
        OutShrubA && OutShrubB && OutGroundCoverA && OutGroundCoverB;
    if (!bComplete)
    {
        OutSummary += TEXT(
            "Failed to build the complete opaque temperate vegetation family.\n");
    }
    return bComplete;
}

UMaterialInstanceConstant* CreateChilkoMutedGroundCoverMaterial(
    UMaterialInterface* Parent,
    FString& OutSummary)
{
    if (!Parent)
    {
        return nullptr;
    }
    const FString AssetName =
        FPackageName::GetLongPackageAssetName(
            ChilkoMutedGroundCoverMaterialPath);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"),
        ChilkoMutedGroundCoverMaterialPath,
        *AssetName);
    UPackage* Package = CreatePackage(ChilkoMutedGroundCoverMaterialPath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterialInstanceConstant* Instance =
        LoadObject<UMaterialInstanceConstant>(nullptr, *ObjectPath);
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Instance)
        {
            FAssetRegistryModule::AssetCreated(Instance);
        }
    }
    if (!Instance)
    {
        return nullptr;
    }

    Instance->Modify();
    Instance->SetParentEditorOnly(Parent);
    Instance->ClearParameterValuesEditorOnly();
    // The current shared mesh palette becomes fluorescent under Lava
    // Canyon's open-sky review lighting. Apply a Chilko-only dry-meadow olive
    // retone and reduce the shadow fill while preserving the original mesh,
    // instance distribution, opacity, roughness, and Futaleufu parent output.
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("VegetationColorScale")),
        FLinearColor(0.62f, 0.38f, 0.24f, 1.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("VegetationShadowFillScale")),
        0.28f);
    Instance->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();

    const FString Filename = FPackageName::LongPackageNameToFilename(
        ChilkoMutedGroundCoverMaterialPath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Instance, *Filename, SaveArgs))
    {
        OutSummary += TEXT(
            "Failed to save the Chilko muted ground-cover material.\n");
        return nullptr;
    }
    OutSummary += TEXT(
        "Built a Chilko-only muted dry-meadow ground-cover material V3; "
        "the shared Futaleufu temperate parent retains identity defaults.\n");
    return Instance;
}

bool CreatePacuareOpaqueRainforestVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutCanopyTreeA,
    UStaticMesh*& OutCanopyTreeB,
    UStaticMesh*& OutShrub,
    UStaticMesh*& OutGroundCover,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary)
{
    OutMaterial = CreateOpaqueVegetationMaterial(
        PacuareRainforestVegetationMaterialPath,
        TEXT("Pacuare rainforest"),
        0.20f,
        0.84f,
        1.16f,
        OutSummary);
    if (!OutMaterial)
    {
        return false;
    }
    OutCanopyTreeA = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Pacuare_CanopyTree_A_OpaqueV2"),
        ETemperateVegetationForm::BroadleafTree,
        7103,
        OutMaterial,
        PacuareRainforestVegetationMeshRoot,
        TEXT("Pacuare rainforest"),
        true,
        false,
        OutSummary);
    // The second canopy form deliberately reuses the solid broadleaf grammar
    // with a different deterministic seed. It adds crown/branch variation
    // without importing the conifer silhouette that made no ecological sense
    // in the Upper Huacas rainforest fallback.
    OutCanopyTreeB = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Pacuare_CanopyTree_B_OpaqueV2"),
        ETemperateVegetationForm::ConiferTree,
        7207,
        OutMaterial,
        PacuareRainforestVegetationMeshRoot,
        TEXT("Pacuare rainforest"),
        true,
        false,
        OutSummary);
    OutShrub = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Pacuare_RiparianShrub_A_OpaqueV2"),
        ETemperateVegetationForm::RiparianShrub,
        7309,
        OutMaterial,
        PacuareRainforestVegetationMeshRoot,
        TEXT("Pacuare rainforest"),
        true,
        false,
        OutSummary);
    OutGroundCover = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Pacuare_RainforestGroundCover_A_OpaqueV2"),
        ETemperateVegetationForm::GroundCover,
        7411,
        OutMaterial,
        PacuareRainforestVegetationMeshRoot,
        TEXT("Pacuare rainforest"),
        true,
        false,
        OutSummary);
    const bool bComplete =
        OutCanopyTreeA && OutCanopyTreeB && OutShrub && OutGroundCover;
    if (!bComplete)
    {
        OutSummary += TEXT(
            "Failed to build the complete Pacuare opaque rainforest family.\n");
    }
    return bComplete;
}

bool ValidateZambeziOpaqueVegetationMaterial(UMaterialInterface* Material)
{
    const UMaterial* BaseMaterial = Material ? Material->GetMaterial() : nullptr;
    return BaseMaterial && BaseMaterial->BlendMode == BLEND_Opaque &&
        !BaseMaterial->TwoSided &&
        BaseMaterial->GetUsageByFlag(MATUSAGE_InstancedStaticMeshes) &&
        BaseMaterial->GetUsageByFlag(MATUSAGE_Nanite);
}

UMaterialInstanceConstant* LoadOrCreateZambeziRunnableLaunchTalusMaterial(
    FString& OutSummary)
{
    UMaterialInterface* ParentMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        ZambeziRunnableLaunchTalusParentMaterialPath);
    if (!ParentMaterial)
    {
        OutSummary += TEXT(
            "Failed to load the project-owned river-boulder parent for the "
            "Zambezi launch talus.\n");
        return nullptr;
    }

    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"),
        ZambeziRunnableLaunchTalusMaterialPackagePath,
        ZambeziRunnableLaunchTalusMaterialAssetName);
    UPackage* Package = CreatePackage(
        ZambeziRunnableLaunchTalusMaterialPackagePath);
    if (!Package)
    {
        return nullptr;
    }

    UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(
        StaticLoadObject(
            UMaterialInstanceConstant::StaticClass(),
            nullptr,
            *ObjectPath));
    if (!Instance)
    {
        Instance = FindObject<UMaterialInstanceConstant>(
            Package,
            ZambeziRunnableLaunchTalusMaterialAssetName);
    }
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package,
            ZambeziRunnableLaunchTalusMaterialAssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Instance)
        {
            FAssetRegistryModule::AssetCreated(Instance);
        }
    }
    if (!Instance)
    {
        return nullptr;
    }

    Instance->Modify();
    Instance->SetParentEditorOnly(ParentMaterial);
    // Keep enough of the reviewed CC0 scan to preserve real microstructure,
    // but mix most of its green/ochre appearance into the project-authored
    // neutral mineral branch. This remains a generic visual analog and makes
    // no Batoka lithology claim.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RockVisualSourceBlend")),
        ZambeziRunnableLaunchTalusReviewedSourceBlend);
    // The scalar remains a dry fail-safe. Launch talus binds each instance's
    // conditioned local visual-surface elevation through custom-data channel
    // zero, so a curved reach never collapses to one invented flat waterline.
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RockWaterlineZCm")),
        -1.0e7f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RockWetBandWidthCm")),
        ZambeziRunnableLaunchTalusWetBandWidthCm);
    Instance->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename = FPackageName::LongPackageNameToFilename(
        ZambeziRunnableLaunchTalusMaterialPackagePath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Instance, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to save %s.\n"),
            *ObjectPath);
        return nullptr;
    }

    OutSummary += FString::Printf(
        TEXT("Built Zambezi launch-talus material %s with %.2f reviewed-source "
             "blend and dry-bank waterline fail-safe.\n"),
        *ObjectPath,
        ZambeziRunnableLaunchTalusReviewedSourceBlend);
    return Instance;
}
} // namespace

UMaterialInstanceConstant* LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const TCHAR* FoliageType,
    const TCHAR* SourceParentObjectPath,
    const FLinearColor& FrontTint,
    const FLinearColor& BackTint,
    const FLinearColor& TransmissionTint,
    float RoughnessStrength,
    float NormalStrength,
    FString& OutSummary)
{
    UMaterialInterface* SourceParent = LoadObject<UMaterialInterface>(nullptr, SourceParentObjectPath);
    const FString RiverAssetName = GetFirstPartyMaterialRiverAssetName(Spec.RiverId);
    if (!SourceParent || RiverAssetName.IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("Failed to load %s foliage parent for %s.\n"),
            FoliageType,
            *Spec.RiverId);
        return nullptr;
    }

    const FString AssetName = FString::Printf(
        TEXT("MI_RaftSim_%s_%s_BiomeFoliageCandidate"),
        *RiverAssetName,
        FoliageType);
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/%s"),
        *AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }

    UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(
        StaticLoadObject(UMaterialInstanceConstant::StaticClass(), nullptr, *ObjectPath));
    if (!Instance)
    {
        Instance = FindObject<UMaterialInstanceConstant>(Package, *AssetName);
    }
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Instance)
        {
            FAssetRegistryModule::AssetCreated(Instance);
        }
    }
    if (!Instance)
    {
        return nullptr;
    }

    Instance->Modify();
    Instance->SetParentEditorOnly(SourceParent);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("BaseColor Tint Leaves")),
        FrontTint);
    for (const TCHAR* ParameterName : {
             TEXT("BaseColor Tint Leaf Backside"),
             TEXT("Tint Leaf Backside")})
    {
        Instance->SetVectorParameterValueEditorOnly(
            FMaterialParameterInfo(ParameterName),
            BackTint);
    }
    for (const TCHAR* ParameterName : {
             TEXT("Translucency Tint Leaves"),
             TEXT("Translucency Tint"),
             TEXT("Tint Translucency")})
    {
        Instance->SetVectorParameterValueEditorOnly(
            FMaterialParameterInfo(ParameterName),
            TransmissionTint);
    }
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Roughness Leaves Strength")),
        RoughnessStrength);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Roughness Leaf Backside")),
        FMath::Clamp(RoughnessStrength + 0.06f, 0.0f, 1.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Roughness Min")),
        FMath::Clamp(RoughnessStrength - 0.12f, 0.0f, 1.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Normal Strength")),
        NormalStrength);
    Instance->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Instance, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Failed to save %s.\n"), *ObjectPath);
        return nullptr;
    }

    OutSummary += FString::Printf(
        TEXT("Built %s %s texture-preserving foliage candidate (roughness %.3f, normal %.3f).\n"),
        *Spec.RiverId,
        FoliageType,
        RoughnessStrength,
        NormalStrength);
    return Instance;
}

int32 BindLandscapeCandidateFoliageMaterial(
    UHierarchicalInstancedStaticMeshComponent* Component,
    UStaticMesh* Mesh,
    UMaterialInterface* FoliageMaterial)
{
    if (!Component || !Mesh || !FoliageMaterial)
    {
        return 0;
    }

    int32 BoundSlotCount = 0;
    const TArray<FStaticMaterial>& StaticMaterials = Mesh->GetStaticMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < StaticMaterials.Num(); ++MaterialIndex)
    {
        const FString SlotName = StaticMaterials[MaterialIndex].MaterialSlotName.ToString();
        UMaterialInterface* SourceMaterial = Mesh->GetMaterial(MaterialIndex);
        const bool bIsFoliageSlot =
            SlotName.Equals(TEXT("TwoSided"), ESearchCase::IgnoreCase) ||
            (SourceMaterial && SourceMaterial->GetName().Contains(TEXT("Foliage"), ESearchCase::IgnoreCase));
        if (bIsFoliageSlot)
        {
            Component->SetMaterial(MaterialIndex, FoliageMaterial);
            ++BoundSlotCount;
        }
    }
    return BoundSlotCount;
}

bool ValidateLandscapeCandidateReviewedFirMaterials(UStaticMesh* Mesh)
{
    if (!Mesh)
    {
        return false;
    }

    bool bHasReviewedBark = false;
    bool bHasReviewedNeedles = false;
    const TArray<FStaticMaterial>& StaticMaterials = Mesh->GetStaticMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < StaticMaterials.Num(); ++MaterialIndex)
    {
        const FString SlotName = StaticMaterials[MaterialIndex].MaterialSlotName.ToString();
        UMaterialInterface* Material = Mesh->GetMaterial(MaterialIndex);
        if (!Material)
        {
            continue;
        }

        bHasReviewedBark |=
            SlotName.Contains(TEXT("bark"), ESearchCase::IgnoreCase) &&
            Material->GetPathName().Contains(TEXT("M_FirTree01_Bark"));
        bHasReviewedNeedles |=
            SlotName.Contains(TEXT("twig"), ESearchCase::IgnoreCase) &&
            Material->GetPathName().Contains(TEXT("M_FirTree01_Needles"));
    }
    return bHasReviewedBark && bHasReviewedNeedles;
}

bool ValidateLandscapeCandidateReviewedBroadleafMaterials(UStaticMesh* Mesh)
{
    if (!Mesh)
    {
        return false;
    }

    bool bHasReviewedTrunk = false;
    bool bHasReviewedBranches = false;
    bool bHasReviewedLeaves = false;
    const TArray<FStaticMaterial>& StaticMaterials = Mesh->GetStaticMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < StaticMaterials.Num(); ++MaterialIndex)
    {
        const FString SlotName = StaticMaterials[MaterialIndex].MaterialSlotName.ToString();
        UMaterialInterface* Material = Mesh->GetMaterial(MaterialIndex);
        if (!Material)
        {
            continue;
        }

        bHasReviewedTrunk |=
            SlotName.Contains(TEXT("trunk"), ESearchCase::IgnoreCase) &&
            Material->GetPathName().Contains(TEXT("M_TreeSmall02_Trunk"));
        bHasReviewedBranches |=
            SlotName.Contains(TEXT("branch"), ESearchCase::IgnoreCase) &&
            Material->GetPathName().Contains(TEXT("M_TreeSmall02_Branches"));
        bHasReviewedLeaves |=
            SlotName.Contains(TEXT("leaves"), ESearchCase::IgnoreCase) &&
            Material->GetPathName().Contains(TEXT("M_TreeSmall02_Leaves"));
    }
    return bHasReviewedTrunk && bHasReviewedBranches && bHasReviewedLeaves;
}

bool ValidateLandscapeCandidateReviewedRockMaterial(UStaticMesh* Mesh)
{
    if (!Mesh || Mesh->GetStaticMaterials().Num() < 1)
    {
        return false;
    }
    UMaterialInterface* Material = Mesh->GetMaterial(0);
    return Material &&
        Material->GetPathName().Contains(TEXT("M_RockMossSet01")) &&
        Mesh->IsNaniteEnabled();
}

bool ValidateLandscapeCandidateReviewedPineMaterials(UStaticMesh* Mesh)
{
    if (!Mesh || !Mesh->IsNaniteEnabled())
    {
        return false;
    }
    bool bHasNeedles = false;
    bool bHasWood = false;
    for (int32 MaterialIndex = 0; MaterialIndex < Mesh->GetStaticMaterials().Num(); ++MaterialIndex)
    {
        UMaterialInterface* Material = Mesh->GetMaterial(MaterialIndex);
        if (!Material)
        {
            continue;
        }
        const FString Path = Material->GetPathName();
        bHasNeedles |= Path.Contains(TEXT("M_PineTree01_Needles"));
        bHasWood |= Path.Contains(TEXT("M_PineTree01_Bark")) ||
            Path.Contains(TEXT("M_PineTree01_Trunk"));
    }
    return bHasNeedles && bHasWood;
}

FBox GetLandscapeCandidateEffectiveMeshBounds(UStaticMesh* Mesh)
{
    if (!Mesh)
    {
        return FBox(EForceInit::ForceInit);
    }

    const FBox RawBounds = Mesh->GetBoundingBox();
    if (RawBounds.GetSize().Z >= 100.0f || Mesh->GetNumSourceModels() == 0)
    {
        return RawBounds;
    }

    const FVector BuildScale = Mesh->GetSourceModel(0).BuildSettings.BuildScale3D;
    return FBox(RawBounds.Min * BuildScale, RawBounds.Max * BuildScale);
}

UStaticMesh* LoadOrCreateLandscapeCandidatePveStaticMesh(
    UWorld* World,
    const TCHAR* SourceSkeletalMeshPath,
    const TCHAR* OutputPackagePath,
    FString& OutSummary)
{
    if (!World)
    {
        return nullptr;
    }

    const FString AssetName = FPackageName::GetLongPackageAssetName(OutputPackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), OutputPackagePath, *AssetName);
    if (UStaticMesh* ExistingMesh = LoadObject<UStaticMesh>(nullptr, *ObjectPath))
    {
        return ExistingMesh;
    }

    USkeletalMesh* SourceMesh = LoadObject<USkeletalMesh>(nullptr, SourceSkeletalMeshPath);
    if (!SourceMesh)
    {
        OutSummary += FString::Printf(
            TEXT("Could not load complete PVE source species mesh %s.\n"),
            SourceSkeletalMeshPath);
        return nullptr;
    }

    ASkeletalMeshActor* ConversionActor = World->SpawnActor<ASkeletalMeshActor>(
        ASkeletalMeshActor::StaticClass(),
        FTransform::Identity);
    if (!ConversionActor)
    {
        OutSummary += FString::Printf(
            TEXT("Could not create the PVE static-mesh conversion actor for %s.\n"),
            SourceSkeletalMeshPath);
        return nullptr;
    }

    USkeletalMeshComponent* SourceComponent = ConversionActor->GetSkeletalMeshComponent();
    SourceComponent->SetSkeletalMeshAsset(SourceMesh);
    SourceComponent->SetWorldTransform(FTransform::Identity);
    SourceComponent->RefreshBoneTransforms();
    SourceComponent->UpdateComponentToWorld();
    SourceComponent->MarkRenderStateDirty();
    FlushRenderingCommands();

    IMeshUtilities& MeshUtilities =
        FModuleManager::Get().LoadModuleChecked<IMeshUtilities>(TEXT("MeshUtilities"));
    TArray<UMeshComponent*> ComponentsToConvert;
    ComponentsToConvert.Add(SourceComponent);
    UStaticMesh* ConvertedMesh = MeshUtilities.ConvertMeshesToStaticMesh(
        ComponentsToConvert,
        FTransform::Identity,
        OutputPackagePath);
    ConversionActor->Destroy();
    if (!ConvertedMesh)
    {
        OutSummary += FString::Printf(
            TEXT("Failed to convert complete PVE source species mesh %s.\n"),
            SourceSkeletalMeshPath);
        return nullptr;
    }

    ConvertedMesh->Modify();
    ConvertedMesh->GetNaniteSettings().bEnabled = true;
    ConvertedMesh->Build(false);
    ConvertedMesh->PostEditChange();
    ConvertedMesh->MarkPackageDirty();

    UPackage* Package = ConvertedMesh->GetOutermost();
    const FString Filename =
        FPackageName::LongPackageNameToFilename(OutputPackagePath, FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, ConvertedMesh, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to save converted PVE species mesh %s.\n"),
            OutputPackagePath);
        return nullptr;
    }

    OutSummary += FString::Printf(
        TEXT("Converted complete PVE source species %s -> %s with Nanite enabled.\n"),
        SourceSkeletalMeshPath,
        OutputPackagePath);
    return ConvertedMesh;
}

                                             
 
                               
                               
                            
                                         
                                                    
                                                
                                          
                                   
                                      
                                           
                                            
                                 
                                           
                                           
                                         
                                              
                                              
                                              
                                               
                                                
                                                    
                                                             
                                       
                                            
                                                   
                                                     
                                                   
                                                      
                                                    
                                               
                                            
                                                         
                                            
                                                         
                                                             
                                                              
                                                           
                                                            
                                        
                                                                                             
                                      
                                                                                       
                                    
                              
                                               
                                                  
                                            
                                            
                                                  
  

bool AddLandscapeCandidateBiomeDressing(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FRaftSimLandscapeImportCandidateResult& OutResult,
    FString& OutSummary)
{
    if (!World || !Landscape)
    {
        return false;
    }

    static const TCHAR* BroadleafSourcePath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/PVE_Deciduous_Tree_01.PVE_Deciduous_Tree_01");
    static const TCHAR* ConiferSourcePath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01/PVE_Conifer_01.PVE_Conifer_01");
    static const TCHAR* ShrubSourcePath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/Deciduous_Shrub_01/PVE_Deciduous_Shrub_01.PVE_Deciduous_Shrub_01");
    static const TCHAR* UnderstorySourcePath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/Plant_01/PVE_Plant_01.PVE_Plant_01");

    const bool bSouthFork = Candidate.PreviewSpec.RiverId == TEXT("american_south_fork");
    const bool bZambezi = Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge");
    const bool bPacuare = Candidate.PreviewSpec.RiverId == TEXT("pacuare");
    const bool bFutaleufu = Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
    const bool bChilko =
        Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
    const bool bColoradoHance =
        Candidate.PreviewSpec.RiverId == TEXT("colorado_river");
    const bool bOpaqueTemperate = bFutaleufu || bChilko;
    const bool bUsesOpaqueVolumetricVegetation =
        bZambezi || bPacuare || bOpaqueTemperate;
    TArray<UStaticMesh*> ReviewedRockMeshes;
    if (bSouthFork || bZambezi || bPacuare || bFutaleufu || bChilko)
    {
        for (int32 RockIndex = 1; RockIndex <= 6; ++RockIndex)
        {
            const FString AssetName = FString::Printf(
                TEXT("SM_RockMossSet01_rock_moss_set_01_rock%02d"),
                RockIndex);
            const FString ObjectPath = FString::Printf(
                TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockMossSet01_1K/%s.%s"),
                *AssetName,
                *AssetName);
            if (UStaticMesh* RockMesh = LoadObject<UStaticMesh>(nullptr, *ObjectPath))
            {
                ReviewedRockMeshes.Add(RockMesh);
            }
        }
        OutResult.DressingExternalRockMeshCount = ReviewedRockMeshes.Num();
        OutResult.DressingExternalReviewAssetCount += ReviewedRockMeshes.Num();
        OutResult.bDressingExternalRockMaterialsValidated =
            ReviewedRockMeshes.Num() == 6 &&
            Algo::AllOf(ReviewedRockMeshes, [](UStaticMesh* Mesh)
            {
                return ValidateLandscapeCandidateReviewedRockMaterial(Mesh);
            });
        if (!OutResult.bDressingExternalRockMaterialsValidated)
        {
            OutSummary += FString::Printf(
                TEXT("%s reviewed rock comparison loaded %d/6 meshes or failed material/Nanite validation.\n"),
                *Candidate.PreviewSpec.RiverId,
                ReviewedRockMeshes.Num());
            return false;
        }
    }

    TArray<UStaticMesh*> ReviewedPineMeshes;
    if (bSouthFork)
    {
        constexpr TCHAR VariantLabels[] = {TEXT('a'), TEXT('b'), TEXT('c')};
        for (const TCHAR VariantLabel : VariantLabels)
        {
            const FString AssetName = FString::Printf(
                TEXT("SM_PineTree01_pine_tree_01_%c_LOD0"),
                VariantLabel);
            const FString ObjectPath = FString::Printf(
                TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/%s.%s"),
                *AssetName,
                *AssetName);
            if (UStaticMesh* PineMesh = LoadObject<UStaticMesh>(nullptr, *ObjectPath))
            {
                ReviewedPineMeshes.Add(PineMesh);
            }
        }
        OutResult.DressingExternalPineMeshCount = ReviewedPineMeshes.Num();
        OutResult.DressingExternalReviewAssetCount += ReviewedPineMeshes.Num();
        OutResult.bDressingExternalPineMaterialsValidated =
            ReviewedPineMeshes.Num() == 3 &&
            Algo::AllOf(ReviewedPineMeshes, [](UStaticMesh* Mesh)
            {
                return ValidateLandscapeCandidateReviewedPineMaterials(Mesh);
            });
        if (!OutResult.bDressingExternalPineMaterialsValidated)
        {
            OutSummary += FString::Printf(
                TEXT("%s reviewed pine comparison loaded %d/3 meshes or failed material/Nanite validation.\n"),
                *Candidate.PreviewSpec.RiverId,
                ReviewedPineMeshes.Num());
            return false;
        }
    }

    UStaticMesh* BroadleafTreeMesh = nullptr;
    UStaticMesh* ConiferTreeMesh = nullptr;
    UStaticMesh* ShrubMesh = nullptr;
    UStaticMesh* UnderstoryMesh = nullptr;
    UStaticMesh* ZambeziGroundCoverMeshB = nullptr;
    UStaticMesh* TemperateBroadleafTreeMeshB = nullptr;
    UStaticMesh* TemperateConiferTreeMeshB = nullptr;
    UStaticMesh* TemperateShrubMeshB = nullptr;
    UStaticMesh* TemperateUnderstoryMeshB = nullptr;
    UMaterialInterface* ZambeziOpaqueVegetationMaterial = nullptr;
    UMaterialInterface* PacuareOpaqueRainforestVegetationMaterial = nullptr;
    UMaterialInterface* TemperateOpaqueVegetationMaterial = nullptr;
    UMaterialInterface* ChilkoMutedGroundCoverMaterial = nullptr;
    UStaticMesh* HanceDrylandShrubMeshA = nullptr;
    UStaticMesh* HanceDrylandShrubMeshB = nullptr;
    UStaticMesh* HanceDrylandGroundCoverMeshA = nullptr;
    UStaticMesh* HanceDrylandGroundCoverMeshB = nullptr;
    UMaterialInterface* HanceDrylandVegetationMaterial = nullptr;
    if (bZambezi)
    {
        if (!CreateZambeziOpaqueVegetationAssets(
                World,
                BroadleafTreeMesh,
                ConiferTreeMesh,
                ShrubMesh,
                UnderstoryMesh,
                ZambeziGroundCoverMeshB,
                ZambeziOpaqueVegetationMaterial,
                OutSummary))
        {
            return false;
        }
        OutResult.DressingBroadleafAssetPath = BroadleafTreeMesh->GetPathName();
        OutResult.DressingConiferAssetPath = ConiferTreeMesh->GetPathName();
        OutResult.DressingShrubAssetPath = ShrubMesh->GetPathName();
        OutResult.DressingUnderstoryAssetPath = UnderstoryMesh->GetPathName();
        OutResult.DressingFoliageMaterialAssetPath =
            ZambeziOpaqueVegetationMaterial->GetPathName();
        OutResult.bDressingUsesOpaqueVolumetricVegetation = true;
    }
    else if (bPacuare)
    {
        if (!CreatePacuareOpaqueRainforestVegetationAssets(
                World,
                BroadleafTreeMesh,
                ConiferTreeMesh,
                ShrubMesh,
                UnderstoryMesh,
                PacuareOpaqueRainforestVegetationMaterial,
                OutSummary))
        {
            return false;
        }
        OutResult.DressingBroadleafAssetPath = BroadleafTreeMesh->GetPathName();
        OutResult.DressingConiferAssetPath = ConiferTreeMesh->GetPathName();
        OutResult.DressingShrubAssetPath = ShrubMesh->GetPathName();
        OutResult.DressingUnderstoryAssetPath = UnderstoryMesh->GetPathName();
        OutResult.DressingFoliageMaterialAssetPath =
            PacuareOpaqueRainforestVegetationMaterial->GetPathName();
        OutResult.bDressingUsesOpaqueVolumetricVegetation = true;
    }
    else if (bOpaqueTemperate)
    {
        if (!CreateTemperateOpaqueVegetationAssets(
                World,
                BroadleafTreeMesh,
                TemperateBroadleafTreeMeshB,
                ConiferTreeMesh,
                TemperateConiferTreeMeshB,
                ShrubMesh,
                TemperateShrubMeshB,
                UnderstoryMesh,
                TemperateUnderstoryMeshB,
                TemperateOpaqueVegetationMaterial,
                OutSummary))
        {
            return false;
        }
        OutResult.DressingBroadleafAssetPath = BroadleafTreeMesh->GetPathName();
        OutResult.DressingConiferAssetPath = ConiferTreeMesh->GetPathName();
        OutResult.DressingShrubAssetPath = ShrubMesh->GetPathName();
        OutResult.DressingUnderstoryAssetPath = UnderstoryMesh->GetPathName();
        OutResult.DressingBroadleafVariantAssetPath =
            TemperateBroadleafTreeMeshB->GetPathName();
        OutResult.DressingConiferVariantAssetPath =
            TemperateConiferTreeMeshB->GetPathName();
        OutResult.DressingShrubVariantAssetPath =
            TemperateShrubMeshB->GetPathName();
        OutResult.DressingUnderstoryVariantAssetPath =
            TemperateUnderstoryMeshB->GetPathName();
        OutResult.DressingFoliageMaterialAssetPath =
            TemperateOpaqueVegetationMaterial->GetPathName();
        OutResult.bDressingUsesOpaqueVolumetricVegetation = true;
        if (bChilko)
        {
            ChilkoMutedGroundCoverMaterial =
                CreateChilkoMutedGroundCoverMaterial(
                    TemperateOpaqueVegetationMaterial,
                    OutSummary);
            if (!ChilkoMutedGroundCoverMaterial)
            {
                return false;
            }
            OutResult.DressingUnderstoryFoliageMaterialAssetPath =
                ChilkoMutedGroundCoverMaterial->GetPathName();
        }
    }
    else
    {
        for (const TCHAR* SourcePath :
             {BroadleafSourcePath, ConiferSourcePath, ShrubSourcePath, UnderstorySourcePath})
        {
            OutResult.DressingSourceSkeletalMeshCount +=
                LoadObject<USkeletalMesh>(nullptr, SourcePath) ? 1 : 0;
        }

        BroadleafTreeMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
            World,
            BroadleafSourcePath,
            TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousTree01_Static"),
            OutSummary);
        ConiferTreeMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
            World,
            ConiferSourcePath,
            TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Conifer01_Static"),
            OutSummary);
        ShrubMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
            World,
            ShrubSourcePath,
            TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousShrub01_Static"),
            OutSummary);
        UnderstoryMesh = LoadOrCreateLandscapeCandidatePveStaticMesh(
            World,
            UnderstorySourcePath,
            TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Plant01_Static"),
            OutSummary);
    }
    TArray<UStaticMesh*> ConvertedSpeciesMeshes = {
        BroadleafTreeMesh,
        ConiferTreeMesh,
        ShrubMesh,
        UnderstoryMesh};
    if (bOpaqueTemperate)
    {
        ConvertedSpeciesMeshes.Append({
            TemperateBroadleafTreeMeshB,
            TemperateConiferTreeMeshB,
            TemperateShrubMeshB,
            TemperateUnderstoryMeshB});
    }
    for (UStaticMesh* Mesh : ConvertedSpeciesMeshes)
    {
        OutResult.DressingAssetCount += Mesh ? 1 : 0;
        OutResult.DressingConvertedStaticMeshCount += Mesh ? 1 : 0;
    }
    OutResult.DressingAssetCount += ReviewedRockMeshes.Num() + ReviewedPineMeshes.Num();
    if (bColoradoHance)
    {
        if (!CreateHanceOpaqueDrylandVegetationAssets(
                World,
                HanceDrylandShrubMeshA,
                HanceDrylandShrubMeshB,
                HanceDrylandGroundCoverMeshA,
                HanceDrylandGroundCoverMeshB,
                HanceDrylandVegetationMaterial,
                OutSummary))
        {
            return false;
        }
        OutResult.DressingAssetCount += 4;
        OutResult.DressingShrubAssetPath =
            HanceDrylandShrubMeshA->GetPathName();
        OutResult.DressingShrubVariantAssetPath =
            HanceDrylandShrubMeshB->GetPathName();
        OutResult.DressingUnderstoryAssetPath =
            HanceDrylandGroundCoverMeshA->GetPathName();
        OutResult.DressingUnderstoryVariantAssetPath =
            HanceDrylandGroundCoverMeshB->GetPathName();
    }
    OutResult.bDressingAssetsLoaded = bUsesOpaqueVolumetricVegetation
        ? OutResult.DressingSourceSkeletalMeshCount == 0 &&
            OutResult.DressingConvertedStaticMeshCount ==
                (bOpaqueTemperate ? 8 : 4) &&
            ValidateZambeziOpaqueVegetationMaterial(
                bZambezi
                    ? ZambeziOpaqueVegetationMaterial
                    : (bPacuare
                           ? PacuareOpaqueRainforestVegetationMaterial
                           : TemperateOpaqueVegetationMaterial))
        : OutResult.DressingSourceSkeletalMeshCount == 4 &&
            OutResult.DressingConvertedStaticMeshCount == 4;
    if (!OutResult.bDressingAssetsLoaded)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s loaded %d source and %d/%d converted species meshes.\n"),
            *Candidate.PreviewSpec.RiverId,
            OutResult.DressingSourceSkeletalMeshCount,
            OutResult.DressingConvertedStaticMeshCount,
            bOpaqueTemperate ? 8 : 4);
        return false;
    }

    if (bSouthFork)
    {
        OutSummary += TEXT(
            "South Fork physical corridor excludes the previously rejected Poly Haven fir and "
            "small broadleaf candidates "
            "after their recorded not-lifelike visual rejection; converted PVE species remain the "
            "temporary non-production fallback. The rights-reviewed six-variant mossy rock set and "
            "three-variant dense pine set are enabled only for this isolated visual comparison.\n");
    }
    else if (bZambezi)
    {
        OutSummary += FString::Printf(
            TEXT("%s uses the rights-reviewed CC0 rock set only as an isolated river-specific visual "
                 "evaluation. Rejected tree candidates and the evaluated alpha-card savanna pack "
                 "remain excluded; four project-owned opaque volumetric vegetation forms replace "
                 "the PVE cards without claiming exact species, lifelike, or gameplay promotion.\n"),
            *Candidate.PreviewSpec.RiverId);
    }
    else if (bPacuare)
    {
        OutSummary += TEXT(
            "Pacuare replaces the repeated PVE alpha-card banks with two "
            "project-owned solid canopy forms plus opaque riparian shrub and "
            "ground-cover meshes. The source-mask and slope-screened family is "
            "procedural rainforest infill, not exact species, ecology, or "
            "photoreal approval.\n");
    }
    else if (bOpaqueTemperate)
    {
        OutSummary += FString::Printf(
            TEXT("%s replaces repeated alpha-card PVE banks with eight project-owned "
                 "opaque volumetric temperate meshes: two deterministic morphologies "
                 "for each conifer, broadleaf, shrub, and ground-cover form. The family is procedural infill, "
                 "not exact-species or photoreal approval.\n"),
            *Candidate.PreviewSpec.RiverId);
    }
    else if (bColoradoHance)
    {
        OutSummary += TEXT(
            "Colorado Hance retains its four legacy PVE evaluation assets for "
            "compatibility but places zero legacy instances; two project-owned "
            "opaque dryland forms provide the countable ground-cover and shrub "
            "layers without the former horizontal PVE bench band. The added "
            "family is procedural gap fill, not exact-species, "
            "ecology, surveyed-terrain, or photoreal approval.\n");
    }

    OutResult.bDressingBoulderMeshNaniteEnabled =
        ReviewedRockMeshes.Num() == 6 &&
        Algo::AllOf(ReviewedRockMeshes, [](UStaticMesh* Mesh)
        {
            return Mesh && Mesh->IsNaniteEnabled();
        });
    OutResult.bDressingBroadleafMeshNaniteEnabled =
        BroadleafTreeMesh->IsNaniteEnabled() && ShrubMesh->IsNaniteEnabled() &&
        (!bOpaqueTemperate ||
         (TemperateBroadleafTreeMeshB->IsNaniteEnabled() &&
          TemperateShrubMeshB->IsNaniteEnabled()));
    OutResult.bDressingConiferMeshNaniteEnabled =
        ConiferTreeMesh->IsNaniteEnabled() &&
        (!bOpaqueTemperate || TemperateConiferTreeMeshB->IsNaniteEnabled()) &&
        (ReviewedPineMeshes.IsEmpty() ||
         Algo::AllOf(ReviewedPineMeshes, [](UStaticMesh* Mesh)
         {
             return Mesh && Mesh->IsNaniteEnabled();
         }));
    OutResult.bDressingUnderstoryMeshNaniteEnabled =
        UnderstoryMesh->IsNaniteEnabled() &&
        (!bOpaqueTemperate || TemperateUnderstoryMeshB->IsNaniteEnabled());

    FRaftSimPreviewImage WaterMask;
    FRaftSimPreviewImage VegetationMask;
    const bool bWaterMaskLoaded =
        !Candidate.PreviewSpec.WaterMaskImage.IsEmpty() &&
        LoadPreviewPngImage(Candidate.PreviewSpec.WaterMaskImage, WaterMask);
    const bool bVegetationMaskLoaded =
        !Candidate.PreviewSpec.VegetationMaskImage.IsEmpty() &&
        LoadPreviewPngImage(Candidate.PreviewSpec.VegetationMaskImage, VegetationMask);
    OutResult.bDressingSourceMasksLoaded = bWaterMaskLoaded && bVegetationMaskLoaded;
    if (!OutResult.bDressingSourceMasksLoaded)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s requires both water and vegetation masks.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }

    const FRaftSimEnvironmentPreviewSpec& Spec = Candidate.PreviewSpec;
    const FRaftSimLandscapeCandidateFoliageSettings FoliageSettings =
        GetLandscapeCandidateFoliageSettings(Spec.RiverId);
    UMaterialInterface* OpaqueVegetationMaterial = bZambezi
        ? ZambeziOpaqueVegetationMaterial
        : (bPacuare
               ? PacuareOpaqueRainforestVegetationMaterial
               : TemperateOpaqueVegetationMaterial);
    UMaterialInterface* BroadleafFoliageMaterial = OpaqueVegetationMaterial;
    UMaterialInterface* ConiferFoliageMaterial = OpaqueVegetationMaterial;
    UMaterialInterface* UnderstoryFoliageMaterial = OpaqueVegetationMaterial;
    if (bChilko)
    {
        UnderstoryFoliageMaterial = ChilkoMutedGroundCoverMaterial;
    }
    if (!bUsesOpaqueVolumetricVegetation)
    {
        BroadleafFoliageMaterial =
            LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
                Spec,
                TEXT("Broadleaf"),
                TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/Materials/MI_LeafTree_01_Foliage.MI_LeafTree_01_Foliage"),
                FoliageSettings.BroadleafFrontTint,
                FoliageSettings.BroadleafBackTint,
                FoliageSettings.BroadleafTransmissionTint,
                FoliageSettings.RoughnessStrength,
                FoliageSettings.NormalStrength,
                OutSummary);
        ConiferFoliageMaterial =
            LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
                Spec,
                TEXT("Conifer"),
                TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01/Materials/MI_Conifer_Foliage_01.MI_Conifer_Foliage_01"),
                FoliageSettings.ConiferFrontTint,
                FoliageSettings.ConiferBackTint,
                FoliageSettings.ConiferTransmissionTint,
                FoliageSettings.RoughnessStrength,
                FoliageSettings.NormalStrength,
                OutSummary);
        UnderstoryFoliageMaterial =
            LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
                Spec,
                TEXT("Understory"),
                TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/Plant_01/Materials/MI_PVE_Plant_01.MI_PVE_Plant_01"),
                FoliageSettings.BroadleafFrontTint,
                FoliageSettings.BroadleafBackTint,
                FoliageSettings.BroadleafTransmissionTint,
                FoliageSettings.RoughnessStrength,
                FoliageSettings.NormalStrength,
                OutSummary);
    }
    OutResult.DressingFoliageMaterialAssetCount = (bUsesOpaqueVolumetricVegetation
        ? (OpaqueVegetationMaterial ? 1 : 0) +
            (bChilko && ChilkoMutedGroundCoverMaterial ? 1 : 0)
        : (BroadleafFoliageMaterial ? 1 : 0) +
            (ConiferFoliageMaterial ? 1 : 0) +
            (UnderstoryFoliageMaterial ? 1 : 0)) +
        (bColoradoHance && HanceDrylandVegetationMaterial ? 1 : 0);
    const int32 ExpectedFoliageMaterialAssetCount =
        (bUsesOpaqueVolumetricVegetation ? (bChilko ? 2 : 1) : 3) +
        (bColoradoHance ? 1 : 0);
    if (OutResult.DressingFoliageMaterialAssetCount !=
        ExpectedFoliageMaterialAssetCount)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s loaded %d/%d required foliage materials.\n"),
            *Spec.RiverId,
            OutResult.DressingFoliageMaterialAssetCount,
            ExpectedFoliageMaterialAssetCount);
        return false;
    }
    const FString BroadleafComponentName =
        bZambezi
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziOpaqueRiparianTree_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : bPacuare
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PacuareOpaqueCanopyA_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : bOpaqueTemperate
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueBroadleaf_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ReviewedBroadleaf_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PveWholeBroadleaf_%s"),
                  *Candidate.PreviewSpec.RiverId);
    UHierarchicalInstancedStaticMeshComponent* BroadleafTreeInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            BroadleafTreeMesh,
            BroadleafComponentName,
            true,
            bUsesOpaqueVolumetricVegetation ? OpaqueVegetationMaterial : nullptr);
    const FString ConiferComponentName =
        bZambezi
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziOpaqueUmbrellaTree_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : bPacuare
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PacuareOpaqueCanopyB_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : bOpaqueTemperate
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueConifer_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")
            ? FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ReviewedFirConifer_%s"),
                  *Candidate.PreviewSpec.RiverId)
            : FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PveWholeConifer_%s"),
                  *Candidate.PreviewSpec.RiverId);
    UHierarchicalInstancedStaticMeshComponent* ConiferTreeInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            ConiferTreeMesh,
            ConiferComponentName,
            true,
            bUsesOpaqueVolumetricVegetation ? OpaqueVegetationMaterial : nullptr);
    UHierarchicalInstancedStaticMeshComponent* ShrubInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            ShrubMesh,
            bZambezi
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_ZambeziOpaqueThornScrub_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : bPacuare
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_PacuareOpaqueRiparianShrub_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : bOpaqueTemperate
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueShrub_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_PveWholeShrub_%s"),
                      *Candidate.PreviewSpec.RiverId),
            true,
            bUsesOpaqueVolumetricVegetation ? OpaqueVegetationMaterial : nullptr);
    UHierarchicalInstancedStaticMeshComponent* UnderstoryInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            UnderstoryMesh,
            bZambezi
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_ZambeziOpaqueGroundCover_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : bPacuare
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_PacuareOpaqueGroundCover_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : bOpaqueTemperate
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueGroundCover_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_PveWholeUnderstory_%s"),
                      *Candidate.PreviewSpec.RiverId),
            true,
            bUsesOpaqueVolumetricVegetation ? UnderstoryFoliageMaterial : nullptr);
    UHierarchicalInstancedStaticMeshComponent* TemperateBroadleafTreeInstancesB =
        bOpaqueTemperate
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              TemperateBroadleafTreeMeshB,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueBroadleafB_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              TemperateOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* TemperateConiferTreeInstancesB =
        bOpaqueTemperate
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              TemperateConiferTreeMeshB,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueConiferB_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              TemperateOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* TemperateShrubInstancesB =
        bOpaqueTemperate
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              TemperateShrubMeshB,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueShrubB_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              TemperateOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* TemperateUnderstoryInstancesB =
        bOpaqueTemperate
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              TemperateUnderstoryMeshB,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueGroundCoverB_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              bChilko
                  ? ChilkoMutedGroundCoverMaterial
                  : TemperateOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* HanceDrylandGroundCoverInstancesA =
        bColoradoHance
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              HanceDrylandGroundCoverMeshA,
              TEXT("RaftSim_LandscapeCandidate_HanceDrylandGroundCoverA"),
              false,
              HanceDrylandVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* HanceDrylandGroundCoverInstancesB =
        bColoradoHance
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              HanceDrylandGroundCoverMeshB,
              TEXT("RaftSim_LandscapeCandidate_HanceDrylandGroundCoverB"),
              false,
              HanceDrylandVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* HanceDrylandShrubInstancesA =
        bColoradoHance
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              HanceDrylandShrubMeshA,
              TEXT("RaftSim_LandscapeCandidate_HanceDrylandShrubA"),
              true,
              HanceDrylandVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* HanceDrylandShrubInstancesB =
        bColoradoHance
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              HanceDrylandShrubMeshB,
              TEXT("RaftSim_LandscapeCandidate_HanceDrylandShrubB"),
              true,
              HanceDrylandVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent* ZambeziBankMosaicInstances =
        bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              UnderstoryMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziOrganicBankMosaic_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziCameraRiparianTreeInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              BroadleafTreeMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziCameraRiparianTree_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziCameraUmbrellaTreeInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ConiferTreeMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziCameraUmbrellaTree_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziCameraThornScrubInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ShrubMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziCameraThornScrub_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziRunnableLaunchGroundCoverInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              UnderstoryMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchGroundCover_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziRunnableLaunchGroundCoverInstancesB = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ZambeziGroundCoverMeshB,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchGroundCoverB_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziRunnableLaunchRiparianTreeInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              BroadleafTreeMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchRiparianTree_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziRunnableLaunchUmbrellaTreeInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ConiferTreeMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchUmbrellaTree_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        ZambeziRunnableLaunchThornScrubInstances = bZambezi
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ShrubMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchThornScrub_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              ZambeziOpaqueVegetationMaterial)
        : nullptr;
    TArray<UHierarchicalInstancedStaticMeshComponent*> ReviewedRockInstances;
    for (int32 RockIndex = 0; RockIndex < ReviewedRockMeshes.Num(); ++RockIndex)
    {
        ReviewedRockInstances.Add(AddLandscapeCandidateInstancedMeshComponent(
            World,
            ReviewedRockMeshes[RockIndex],
            FString::Printf(
                TEXT("RaftSim_LandscapeCandidate_ReviewedRock%02d_%s"),
                RockIndex + 1,
                *Candidate.PreviewSpec.RiverId),
            true));
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        TemperateWaterlineStructureInstances;
    if (bOpaqueTemperate)
    {
        for (int32 RockIndex = 0; RockIndex < ReviewedRockMeshes.Num(); ++RockIndex)
        {
            TemperateWaterlineStructureInstances.Add(
                AddLandscapeCandidateInstancedMeshComponent(
                    World,
                    ReviewedRockMeshes[RockIndex],
                    FString::Printf(
                        TEXT("RaftSim_LandscapeCandidate_TemperateWaterlineStructureRock%02d_%s"),
                        RockIndex + 1,
                        *Candidate.PreviewSpec.RiverId),
                    true));
        }
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        ChilkoOrganicShorelineGravelInstances;
    if (bChilko)
    {
        for (int32 RockIndex = 0; RockIndex < ReviewedRockMeshes.Num(); ++RockIndex)
        {
            ChilkoOrganicShorelineGravelInstances.Add(
                AddLandscapeCandidateInstancedMeshComponent(
                    World,
                    ReviewedRockMeshes[RockIndex],
                    FString::Printf(
                        TEXT("RaftSim_LandscapeCandidate_ChilkoOrganicShorelineGravelRock%02d_%s"),
                        RockIndex + 1,
                        *Candidate.PreviewSpec.RiverId),
                    true));
        }
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        ChilkoOrganicShorelineGroundCoverInstances;
    if (bChilko)
    {
        ChilkoOrganicShorelineGroundCoverInstances = {
            AddLandscapeCandidateInstancedMeshComponent(
                World,
                UnderstoryMesh,
                FString::Printf(
                    TEXT("RaftSim_LandscapeCandidate_ChilkoOrganicShorelineGroundCoverA_%s"),
                    *Candidate.PreviewSpec.RiverId),
                false,
                ChilkoMutedGroundCoverMaterial),
            AddLandscapeCandidateInstancedMeshComponent(
                World,
                TemperateUnderstoryMeshB,
                FString::Printf(
                    TEXT("RaftSim_LandscapeCandidate_ChilkoOrganicShorelineGroundCoverB_%s"),
                    *Candidate.PreviewSpec.RiverId),
                false,
                ChilkoMutedGroundCoverMaterial)};
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        PacuareOrganicShorelineRockInstances;
    if (bPacuare)
    {
        for (int32 RockIndex = 0; RockIndex < ReviewedRockMeshes.Num(); ++RockIndex)
        {
            PacuareOrganicShorelineRockInstances.Add(
                AddLandscapeCandidateInstancedMeshComponent(
                    World,
                    ReviewedRockMeshes[RockIndex],
                    FString::Printf(
                        TEXT("RaftSim_LandscapeCandidate_PacuareOrganicShorelineRock%02d_%s"),
                        RockIndex + 1,
                        *Candidate.PreviewSpec.RiverId),
                    true));
        }
    }
    UHierarchicalInstancedStaticMeshComponent*
        PacuareOrganicShorelineGroundCoverInstances = bPacuare
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              UnderstoryMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PacuareOrganicShorelineGroundCover_%s"),
                  *Candidate.PreviewSpec.RiverId),
              false,
              PacuareOpaqueRainforestVegetationMaterial)
        : nullptr;
    UHierarchicalInstancedStaticMeshComponent*
        PacuareOrganicShorelineShrubInstances = bPacuare
        ? AddLandscapeCandidateInstancedMeshComponent(
              World,
              ShrubMesh,
              FString::Printf(
                  TEXT("RaftSim_LandscapeCandidate_PacuareOrganicShorelineShrub_%s"),
                  *Candidate.PreviewSpec.RiverId),
              true,
              PacuareOpaqueRainforestVegetationMaterial)
        : nullptr;
    TArray<UHierarchicalInstancedStaticMeshComponent*>
        ZambeziRunnableLaunchTalusInstances;
    UMaterialInstanceConstant* ZambeziRunnableLaunchTalusMaterial = bZambezi
        ? LoadOrCreateZambeziRunnableLaunchTalusMaterial(OutSummary)
        : nullptr;
    if (bZambezi)
    {
        for (int32 RockIndex = 0; RockIndex < ReviewedRockMeshes.Num(); ++RockIndex)
        {
            UHierarchicalInstancedStaticMeshComponent* TalusComponent =
                AddLandscapeCandidateInstancedMeshComponent(
                    World,
                    ReviewedRockMeshes[RockIndex],
                    FString::Printf(
                        TEXT("RaftSim_LandscapeCandidate_ZambeziRunnableLaunchTalusRock%02d_%s"),
                        RockIndex + 1,
                        *Candidate.PreviewSpec.RiverId),
                    true,
                    ZambeziRunnableLaunchTalusMaterial);
            if (TalusComponent)
            {
                TalusComponent->SetNumCustomDataFloats(1);
            }
            ZambeziRunnableLaunchTalusInstances.Add(TalusComponent);
        }
    }
    TArray<UHierarchicalInstancedStaticMeshComponent*> ReviewedPineInstances;
    for (int32 PineIndex = 0; PineIndex < ReviewedPineMeshes.Num(); ++PineIndex)
    {
        ReviewedPineInstances.Add(AddLandscapeCandidateInstancedMeshComponent(
            World,
            ReviewedPineMeshes[PineIndex],
            FString::Printf(
                TEXT("RaftSim_LandscapeCandidate_ReviewedPine%02d_%s"),
                PineIndex + 1,
                *Candidate.PreviewSpec.RiverId),
            true));
    }
    if (!BroadleafTreeInstances || !ConiferTreeInstances ||
        !ShrubInstances || !UnderstoryInstances ||
        (bOpaqueTemperate &&
         (!TemperateBroadleafTreeInstancesB ||
          !TemperateConiferTreeInstancesB ||
          !TemperateShrubInstancesB ||
          !TemperateUnderstoryInstancesB)) ||
        (bColoradoHance &&
         (!HanceDrylandGroundCoverInstancesA ||
          !HanceDrylandGroundCoverInstancesB ||
          !HanceDrylandShrubInstancesA ||
          !HanceDrylandShrubInstancesB)) ||
        (bZambezi && !ZambeziBankMosaicInstances) ||
        (bZambezi &&
         (!ZambeziCameraRiparianTreeInstances ||
          !ZambeziCameraUmbrellaTreeInstances ||
          !ZambeziCameraThornScrubInstances ||
          !ZambeziRunnableLaunchGroundCoverInstances ||
          !ZambeziRunnableLaunchGroundCoverInstancesB ||
          !ZambeziRunnableLaunchRiparianTreeInstances ||
          !ZambeziRunnableLaunchUmbrellaTreeInstances ||
          !ZambeziRunnableLaunchThornScrubInstances ||
          !ZambeziRunnableLaunchTalusMaterial)) ||
        Algo::AnyOf(ReviewedRockInstances, [](UHierarchicalInstancedStaticMeshComponent* Component)
        {
            return Component == nullptr;
        }) ||
        Algo::AnyOf(
            TemperateWaterlineStructureInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        Algo::AnyOf(
            ChilkoOrganicShorelineGravelInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        Algo::AnyOf(
            ChilkoOrganicShorelineGroundCoverInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        Algo::AnyOf(
            PacuareOrganicShorelineRockInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        (bPacuare &&
         (!PacuareOrganicShorelineGroundCoverInstances ||
          !PacuareOrganicShorelineShrubInstances)) ||
        Algo::AnyOf(
            ZambeziRunnableLaunchTalusInstances,
            [](UHierarchicalInstancedStaticMeshComponent* Component)
            {
                return Component == nullptr;
            }) ||
        Algo::AnyOf(ReviewedPineInstances, [](UHierarchicalInstancedStaticMeshComponent* Component)
        {
            return Component == nullptr;
        }))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to create one or more Landscape biome dressing instance components for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    if (bColoradoHance)
    {
        const TArray<UHierarchicalInstancedStaticMeshComponent*> Components = {
            HanceDrylandGroundCoverInstancesA,
            HanceDrylandGroundCoverInstancesB,
            HanceDrylandShrubInstancesA,
            HanceDrylandShrubInstancesB};
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimColoradoHanceRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimHanceOpaqueDrylandVegetationV2"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralVegetationFallback"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimOfficialReferenceConstrainedProceduralGapFill"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(TEXT("RaftSimNoEcologyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimNoGeographyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimNoHydraulicAuthority"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimHanceOpaqueDrylandVegetationV2"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOutsideProtectedSolverStrip"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimNonCollisionRenderSurface"));
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            GroundCoverComponents = {
                HanceDrylandGroundCoverInstancesA,
                HanceDrylandGroundCoverInstancesB};
        for (UHierarchicalInstancedStaticMeshComponent* GroundCover :
             GroundCoverComponents)
        {
            GroundCover->SetCastShadow(false);
            GroundCover->ComponentTags.AddUnique(
                TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
        }
    }
    if (bOpaqueTemperate || bPacuare)
    {
        TArray<UHierarchicalInstancedStaticMeshComponent*> Components = {
            BroadleafTreeInstances,
            ConiferTreeInstances,
            ShrubInstances,
            UnderstoryInstances};
        if (bOpaqueTemperate)
        {
            Components.Append({
                TemperateBroadleafTreeInstancesB,
                TemperateConiferTreeInstancesB,
                TemperateShrubInstancesB,
                TemperateUnderstoryInstancesB});
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimOpaqueVolumetricVegetation"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralVegetationFallback"));
                Owner->Tags.AddUnique(TEXT("RaftSimSlopeScreenedPlacement"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(
                    bPacuare
                        ? TEXT("RaftSimPacuareUpperHuacasRun")
                        : (bChilko
                               ? TEXT("RaftSimChilkoLavaCanyonRun")
                               : TEXT("RaftSimFutaleufuTerminatorRun")));
                if (bPacuare)
                {
                    Owner->Tags.AddUnique(
                        TEXT("RaftSimPacuareOpaqueRainforestV1"));
                    Owner->Tags.AddUnique(
                        TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
                }
                if (bOpaqueTemperate)
                {
                    Owner->Tags.AddUnique(
                        TEXT("RaftSimTemperateBankEcologyV4"));
                    Owner->Tags.AddUnique(
                        TEXT("RaftSimTemperateMorphologyVariantFamily"));
                }
            }
            if (Component)
            {
                // Solid procedural lobes are a fail-closed replacement for
                // rejected alpha cards, not transmissive leaf clusters. Their
                // aggregate canopy shadows otherwise form a near-black bank
                // wall, so this fallback family does not cast scene shadows.
                Component->SetCastShadow(false);
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimOpaqueVolumetricVegetation"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimOpaqueFallbackShadowSuppressed"));
                if (bPacuare)
                {
                    Component->ComponentTags.AddUnique(
                        TEXT("RaftSimPacuareOpaqueRainforestV1"));
                }
                if (bOpaqueTemperate)
                {
                    Component->ComponentTags.AddUnique(
                        TEXT("RaftSimTemperateBankEcologyV4"));
                    Component->ComponentTags.AddUnique(
                        TEXT("RaftSimTemperateMorphologyVariantFamily"));
                }
            }
        }
        UnderstoryInstances->SetCastShadow(false);
        TArray<UHierarchicalInstancedStaticMeshComponent*> GroundCoverComponents = {
            UnderstoryInstances};
        if (bOpaqueTemperate)
        {
            TemperateUnderstoryInstancesB->SetCastShadow(false);
            GroundCoverComponents.Add(TemperateUnderstoryInstancesB);
        }
        for (UHierarchicalInstancedStaticMeshComponent* GroundCoverComponent :
             GroundCoverComponents)
        {
            if (AActor* GroundOwner = GroundCoverComponent
                    ? GroundCoverComponent->GetOwner()
                    : nullptr)
            {
                GroundOwner->Tags.AddUnique(TEXT("RaftSimOrganicBankGroundCover"));
                GroundOwner->Tags.AddUnique(
                    TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
                if (bChilko)
                {
                    GroundOwner->Tags.AddUnique(
                        TEXT("RaftSimChilkoMutedGroundCoverV3"));
                }
            }
            GroundCoverComponent->ComponentTags.AddUnique(
                TEXT("RaftSimOrganicBankGroundCover"));
            if (bChilko)
            {
                GroundCoverComponent->ComponentTags.AddUnique(
                    TEXT("RaftSimChilkoMutedGroundCoverV3"));
            }
        }
    }
    if (bOpaqueTemperate)
    {
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             TemperateWaterlineStructureInstances)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(
                    bChilko
                        ? TEXT("RaftSimChilkoLavaCanyonRun")
                        : TEXT("RaftSimFutaleufuTerminatorRun"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimTemperateWaterlineStructureV1"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimProceduralSourceGapFill"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimRightsReviewedCC0RockAnalog"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimPresentationOnlyNoHydraulicAuthority"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimTemperateWaterlineStructureV1"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimOutsideProtectedSolverStrip"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
            }
        }
    }
    if (bChilko)
    {
        auto TagChilkoShorelineComponent = [](
            UHierarchicalInstancedStaticMeshComponent* Component,
            FName FamilyTag)
        {
            if (!Component)
            {
                return;
            }
            if (AActor* Owner = Component->GetOwner())
            {
                Owner->Tags.AddUnique(TEXT("RaftSimChilkoLavaCanyonRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimChilkoOrganicShorelineV2"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimChilkoShorelineNaturalismV3"));
                Owner->Tags.AddUnique(FamilyTag);
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralSourceGapFill"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimPresentationOnlyNoHydraulicAuthority"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimChilkoOrganicShorelineV2"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimChilkoShorelineNaturalismV3"));
            Component->ComponentTags.AddUnique(FamilyTag);
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOutsideProtectedSolverStrip"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimNonCollisionRenderSurface"));
        };
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ChilkoOrganicShorelineGravelInstances)
        {
            TagChilkoShorelineComponent(
                Component,
                TEXT("RaftSimChilkoShorelineGravel"));
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(
                    TEXT("RaftSimRightsReviewedCC0RockAnalog"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimChilkoSortedGravelScaleV3"));
            }
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ChilkoOrganicShorelineGroundCoverInstances)
        {
            TagChilkoShorelineComponent(
                Component,
                TEXT("RaftSimChilkoShorelineGroundCover"));
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimOrganicBankGroundCover"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimChilkoMutedGroundCoverV3"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOrganicBankGroundCover"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimChilkoMutedGroundCoverV3"));
        }
    }
    if (bPacuare)
    {
        auto TagPacuareShorelineComponent = [](
            UHierarchicalInstancedStaticMeshComponent* Component,
            FName FamilyTag)
        {
            if (!Component)
            {
                return;
            }
            if (AActor* Owner = Component->GetOwner())
            {
                Owner->Tags.AddUnique(TEXT("RaftSimPacuareUpperHuacasRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimPacuareOrganicShorelineV1"));
                Owner->Tags.AddUnique(FamilyTag);
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralSourceGapFill"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimPresentationOnlyNoHydraulicAuthority"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimPacuareOrganicShorelineV1"));
            Component->ComponentTags.AddUnique(FamilyTag);
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOutsideProtectedSolverStrip"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimNonCollisionRenderSurface"));
        };
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             PacuareOrganicShorelineRockInstances)
        {
            TagPacuareShorelineComponent(
                Component,
                TEXT("RaftSimPacuareShorelineMossRock"));
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimRightsReviewedCC0RockAnalog"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
            }
        }
        TagPacuareShorelineComponent(
            PacuareOrganicShorelineGroundCoverInstances,
            TEXT("RaftSimPacuareShorelineGroundCover"));
        TagPacuareShorelineComponent(
            PacuareOrganicShorelineShrubInstances,
            TEXT("RaftSimPacuareShorelineShrub"));
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            PacuareEcologyComponents = {
                PacuareOrganicShorelineGroundCoverInstances,
                PacuareOrganicShorelineShrubInstances};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             PacuareEcologyComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimOrganicBankGroundCover"));
            }
        }
        PacuareOrganicShorelineGroundCoverInstances->SetCastShadow(false);
        if (AActor* Owner =
                PacuareOrganicShorelineGroundCoverInstances->GetOwner())
        {
            Owner->Tags.AddUnique(
                TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
        }
        PacuareOrganicShorelineGroundCoverInstances->ComponentTags.AddUnique(
            TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
    }
    if (bZambezi)
    {
        const TArray<UHierarchicalInstancedStaticMeshComponent*> Components = {
            BroadleafTreeInstances,
            ConiferTreeInstances,
            ShrubInstances,
            UnderstoryInstances,
            ZambeziBankMosaicInstances,
            ZambeziCameraRiparianTreeInstances,
            ZambeziCameraUmbrellaTreeInstances,
            ZambeziCameraThornScrubInstances,
            ZambeziRunnableLaunchGroundCoverInstances,
            ZambeziRunnableLaunchGroundCoverInstancesB,
            ZambeziRunnableLaunchRiparianTreeInstances,
            ZambeziRunnableLaunchUmbrellaTreeInstances,
            ZambeziRunnableLaunchThornScrubInstances};
        const TArray<UStaticMesh*> Meshes = {
            BroadleafTreeMesh,
            ConiferTreeMesh,
            ShrubMesh,
            UnderstoryMesh,
            UnderstoryMesh,
            BroadleafTreeMesh,
            ConiferTreeMesh,
            ShrubMesh,
            UnderstoryMesh,
            ZambeziGroundCoverMeshB,
            BroadleafTreeMesh,
            ConiferTreeMesh,
            ShrubMesh};
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziOpaqueVegetation"));
                Owner->Tags.AddUnique(TEXT("RaftSimOpaqueVolumetricVegetation"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralVegetationFallback"));
                Owner->Tags.AddUnique(TEXT("RaftSimSlopeScreenedPlacement"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziOpaqueVegetation"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
            }
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ZambeziRunnableLaunchTalusInstances)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziRun"));
                Owner->Tags.AddUnique(TEXT("RaftSimRunnableLaunchTalusV1"));
                Owner->Tags.AddUnique(TEXT("RaftSimZambeziBasaltAnalogMaterialV1"));
                Owner->Tags.AddUnique(TEXT("RaftSimProjectOwnedMineralRetone"));
                Owner->Tags.AddUnique(TEXT("RaftSimRightsReviewedCC0RockAnalog"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralGeologyFallback"));
                Owner->Tags.AddUnique(TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimDryBankPlacement"));
                Owner->Tags.AddUnique(TEXT("RaftSimSlopeScreenedPlacement"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(TEXT("RaftSimPresentationOnlyNoHydraulicAuthority"));
                Owner->Tags.AddUnique(TEXT("RaftSimConditionedWaterlineWetBankV1"));
                Owner->Tags.AddUnique(TEXT("RaftSimPerInstanceConditionedWaterline"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralWetBankNoMeasuredAuthority"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchTalusV1"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziBasaltAnalogMaterialV1"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimGenericRockAnalogNoLithologyAuthority"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimNonCollisionRenderSurface"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimConditionedWaterlineWetBankV1"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimPerInstanceConditionedWaterline"));
            }
        }
        if (AActor* MosaicOwner = ZambeziBankMosaicInstances
                ? ZambeziBankMosaicInstances->GetOwner()
                : nullptr)
        {
            MosaicOwner->Tags.AddUnique(TEXT("RaftSimOrganicBankMosaic"));
            MosaicOwner->Tags.AddUnique(TEXT("RaftSimCameraVisibleBankCover"));
        }
        if (ZambeziBankMosaicInstances)
        {
            UnderstoryInstances->SetCastShadow(false);
            ZambeziBankMosaicInstances->SetCastShadow(false);
            ZambeziBankMosaicInstances->ComponentTags.AddUnique(
                TEXT("RaftSimOrganicBankMosaic"));
            ZambeziBankMosaicInstances->ComponentTags.AddUnique(
                TEXT("RaftSimCameraVisibleBankCover"));
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            CameraWoodyComponents = {
                ZambeziCameraRiparianTreeInstances,
                ZambeziCameraUmbrellaTreeInstances,
                ZambeziCameraThornScrubInstances};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             CameraWoodyComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(
                    TEXT("RaftSimCameraVisibleWoodyEcology"));
                Owner->Tags.AddUnique(TEXT("RaftSimOrganicWoodyBankLayer"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimWoodySlopeCeiling24Degrees"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimCameraVisibleWoodyEcology"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimOrganicWoodyBankLayer"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimWoodySlopeCeiling24Degrees"));
            }
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            RunnableLaunchComponents = {
                ZambeziRunnableLaunchGroundCoverInstances,
                ZambeziRunnableLaunchGroundCoverInstancesB,
                ZambeziRunnableLaunchRiparianTreeInstances,
                ZambeziRunnableLaunchUmbrellaTreeInstances,
                ZambeziRunnableLaunchThornScrubInstances};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             RunnableLaunchComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimRunnableLaunchBankEcologyV1"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimZambeziLowerEnergyLaunchEcologyV18"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimZambeziElevationStratifiedEcologyV19"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimEcologyStratumCustomDataV1"));
            }
            if (Component)
            {
                Component->SetCullDistances(0, 120000);
                Component->SetNumCustomDataFloats(1);
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchBankEcologyV1"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziLowerEnergyLaunchEcologyV18"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziElevationStratifiedEcologyV19"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimEcologyStratumCustomDataV1"));
            }
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            RunnableLaunchGroundCoverComponents = {
                ZambeziRunnableLaunchGroundCoverInstances,
                ZambeziRunnableLaunchGroundCoverInstancesB};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             RunnableLaunchGroundCoverComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimRunnableLaunchBankCover"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimOrganicGroundCoverMorphologyV2"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchBankCover"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimOrganicGroundCoverMorphologyV2"));
            }
        }
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            RunnableLaunchWoodyComponents = {
                ZambeziRunnableLaunchRiparianTreeInstances,
                ZambeziRunnableLaunchUmbrellaTreeInstances,
                ZambeziRunnableLaunchThornScrubInstances};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             RunnableLaunchWoodyComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimRunnableLaunchWoodyEcology"));
                Owner->Tags.AddUnique(TEXT("RaftSimWoodySlopeCeiling34Degrees"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimRunnableLaunchWoodyShadowSuppressed"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimZambeziLaunchCameraFaceMosaicV19"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchWoodyEcology"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimWoodySlopeCeiling34Degrees"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchWoodyShadowSuppressed"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimZambeziLaunchCameraFaceMosaicV19"));
            }
        }
        OutResult.DressingFoliageMaterialBoundSlotCount = 0;
        for (UStaticMesh* Mesh : Meshes)
        {
            OutResult.DressingFoliageMaterialBoundSlotCount +=
                Mesh && Mesh->GetStaticMaterials().Num() == 1 &&
                    Mesh->GetMaterial(0) == ZambeziOpaqueVegetationMaterial
                ? 1
                : 0;
        }
        OutResult.DressingNativeFoliageMaterialFallbackSlotCount = 0;
        OutResult.bDressingFoliageMaterialsValidated =
            OutResult.DressingFoliageMaterialBoundSlotCount == 13 &&
            ValidateZambeziOpaqueVegetationMaterial(
                ZambeziOpaqueVegetationMaterial) &&
            Algo::AllOf(
                Components,
                [ZambeziOpaqueVegetationMaterial](
                    UHierarchicalInstancedStaticMeshComponent* Component)
                {
                    return Component &&
                        Component->GetCollisionEnabled() ==
                            ECollisionEnabled::NoCollision &&
                        Component->GetMaterial(0) ==
                            ZambeziOpaqueVegetationMaterial;
                });
    }
    else if (bOpaqueTemperate || bPacuare)
    {
        TArray<UHierarchicalInstancedStaticMeshComponent*> Components = {
            BroadleafTreeInstances,
            ConiferTreeInstances,
            ShrubInstances,
            UnderstoryInstances};
        TArray<UStaticMesh*> Meshes = {
            BroadleafTreeMesh,
            ConiferTreeMesh,
            ShrubMesh,
            UnderstoryMesh};
        if (bOpaqueTemperate)
        {
            Components.Append({
                TemperateBroadleafTreeInstancesB,
                TemperateConiferTreeInstancesB,
                TemperateShrubInstancesB,
                TemperateUnderstoryInstancesB});
            Meshes.Append({
                TemperateBroadleafTreeMeshB,
                TemperateConiferTreeMeshB,
                TemperateShrubMeshB,
                TemperateUnderstoryMeshB});
        }
        OutResult.DressingFoliageMaterialBoundSlotCount = 0;
        for (UStaticMesh* Mesh : Meshes)
        {
            OutResult.DressingFoliageMaterialBoundSlotCount +=
                Mesh && Mesh->GetStaticMaterials().Num() == 1 &&
                    Mesh->GetMaterial(0) == OpaqueVegetationMaterial
                ? 1
                : 0;
        }
        OutResult.DressingNativeFoliageMaterialFallbackSlotCount = 0;
        UMaterialInstanceConstant* ChilkoGroundCoverInstance =
            Cast<UMaterialInstanceConstant>(ChilkoMutedGroundCoverMaterial);
        FLinearColor ChilkoGroundCoverColorScale = FLinearColor::Black;
        float ChilkoGroundCoverShadowFillScale = 0.0f;
        const bool bChilkoGroundCoverMaterialValidated = !bChilko ||
            (ChilkoGroundCoverInstance &&
             ChilkoGroundCoverInstance->Parent == OpaqueVegetationMaterial &&
             ChilkoGroundCoverInstance->GetVectorParameterValue(
                 FMaterialParameterInfo(TEXT("VegetationColorScale")),
                 ChilkoGroundCoverColorScale) &&
             ChilkoGroundCoverInstance->GetScalarParameterValue(
                 FMaterialParameterInfo(TEXT("VegetationShadowFillScale")),
                 ChilkoGroundCoverShadowFillScale) &&
             ChilkoGroundCoverColorScale.Equals(
                 FLinearColor(0.62f, 0.38f, 0.24f, 1.0f),
                 0.001f) &&
             FMath::IsNearlyEqual(
                 ChilkoGroundCoverShadowFillScale,
                 0.28f,
                 0.001f));
        OutResult.bDressingFoliageMaterialsValidated =
            OutResult.DressingFoliageMaterialBoundSlotCount ==
                (bOpaqueTemperate ? 8 : 4) &&
            ValidateZambeziOpaqueVegetationMaterial(
                OpaqueVegetationMaterial) &&
            bChilkoGroundCoverMaterialValidated &&
            Algo::AllOf(
                Components,
                [bChilko,
                 OpaqueVegetationMaterial,
                 ChilkoMutedGroundCoverMaterial,
                 UnderstoryInstances,
                 TemperateUnderstoryInstancesB](
                    UHierarchicalInstancedStaticMeshComponent* Component)
                {
                    UMaterialInterface* ExpectedMaterial =
                        bChilko &&
                            (Component == UnderstoryInstances ||
                             Component == TemperateUnderstoryInstancesB)
                        ? ChilkoMutedGroundCoverMaterial
                        : OpaqueVegetationMaterial;
                    return Component &&
                        Component->GetCollisionEnabled() ==
                            ECollisionEnabled::NoCollision &&
                        Component->GetMaterial(0) ==
                            ExpectedMaterial;
                }) &&
            (!bPacuare ||
             (PacuareOrganicShorelineGroundCoverInstances &&
              PacuareOrganicShorelineGroundCoverInstances->GetCollisionEnabled() ==
                  ECollisionEnabled::NoCollision &&
              PacuareOrganicShorelineGroundCoverInstances->GetMaterial(0) ==
                  OpaqueVegetationMaterial &&
              PacuareOrganicShorelineShrubInstances &&
              PacuareOrganicShorelineShrubInstances->GetCollisionEnabled() ==
                  ECollisionEnabled::NoCollision &&
              PacuareOrganicShorelineShrubInstances->GetMaterial(0) ==
                  OpaqueVegetationMaterial));
    }
    else
    {
        OutResult.DressingFoliageMaterialBoundSlotCount =
            BindLandscapeCandidateFoliageMaterial(
                BroadleafTreeInstances,
                BroadleafTreeMesh,
                BroadleafFoliageMaterial) +
            BindLandscapeCandidateFoliageMaterial(
                ConiferTreeInstances,
                ConiferTreeMesh,
                ConiferFoliageMaterial) +
            BindLandscapeCandidateFoliageMaterial(
                ShrubInstances,
                ShrubMesh,
                BroadleafFoliageMaterial) +
            BindLandscapeCandidateFoliageMaterial(
                UnderstoryInstances,
                UnderstoryMesh,
                UnderstoryFoliageMaterial);
        if (OutResult.bDressingExternalConiferReviewAssetLoaded)
        {
            OutResult.DressingFoliageMaterialBoundSlotCount +=
                OutResult.bDressingExternalConiferMaterialsValidated ? 1 : 0;
        }
        if (OutResult.bDressingExternalBroadleafReviewAssetLoaded)
        {
            OutResult.DressingFoliageMaterialBoundSlotCount +=
                OutResult.bDressingExternalBroadleafMaterialsValidated ? 1 : 0;
        }
        OutResult.DressingNativeFoliageMaterialFallbackSlotCount =
            FMath::Max(0, 4 - OutResult.DressingFoliageMaterialBoundSlotCount);
        OutResult.bDressingFoliageMaterialsValidated =
            OutResult.DressingFoliageMaterialBoundSlotCount >= 3 &&
            (!OutResult.bDressingExternalBroadleafReviewAssetLoaded ||
             OutResult.bDressingExternalBroadleafMaterialsValidated) &&
            (!OutResult.bDressingExternalConiferReviewAssetLoaded ||
             OutResult.bDressingExternalConiferMaterialsValidated);
    }
    if (bColoradoHance)
    {
        const bool bHanceOpaqueDrylandValidated =
            ValidateZambeziOpaqueVegetationMaterial(
                HanceDrylandVegetationMaterial) &&
            HanceDrylandShrubMeshA &&
            HanceDrylandShrubMeshA->GetStaticMaterials().Num() == 1 &&
            HanceDrylandShrubMeshA->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandShrubMeshB &&
            HanceDrylandShrubMeshB->GetStaticMaterials().Num() == 1 &&
            HanceDrylandShrubMeshB->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandGroundCoverMeshA &&
            HanceDrylandGroundCoverMeshA->GetStaticMaterials().Num() == 1 &&
            HanceDrylandGroundCoverMeshA->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandGroundCoverMeshB &&
            HanceDrylandGroundCoverMeshB->GetStaticMaterials().Num() == 1 &&
            HanceDrylandGroundCoverMeshB->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandGroundCoverInstancesA->GetCollisionEnabled() ==
                ECollisionEnabled::NoCollision &&
            HanceDrylandGroundCoverInstancesA->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandGroundCoverInstancesB->GetCollisionEnabled() ==
                ECollisionEnabled::NoCollision &&
            HanceDrylandGroundCoverInstancesB->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandShrubInstancesA->GetCollisionEnabled() ==
                ECollisionEnabled::NoCollision &&
            HanceDrylandShrubInstancesA->GetMaterial(0) ==
                HanceDrylandVegetationMaterial &&
            HanceDrylandShrubInstancesB->GetCollisionEnabled() ==
                ECollisionEnabled::NoCollision &&
            HanceDrylandShrubInstancesB->GetMaterial(0) ==
                HanceDrylandVegetationMaterial;
        OutResult.DressingFoliageMaterialBoundSlotCount +=
            bHanceOpaqueDrylandValidated ? 4 : 0;
        OutResult.bDressingFoliageMaterialsValidated &=
            bHanceOpaqueDrylandValidated;
    }
    if (!OutResult.bDressingFoliageMaterialsValidated)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s bound %d foliage slots; material contract failed.\n"),
            *Spec.RiverId,
            OutResult.DressingFoliageMaterialBoundSlotCount);
        return false;
    }

    const bool bRainforest = Spec.bHasWaterfalls;
    const bool bZambeziWoodland = Spec.RiverId == TEXT("zambezi_batoka_gorge");
    TArray<FRaftSimLandscapeCandidateCenterlinePoint> PhysicalCenterline;
    if (!LoadLandscapeCandidateLocalCenterline(Candidate, PhysicalCenterline, OutSummary))
    {
        return false;
    }
    const bool bPhysicalCorridor = Candidate.bPhysicalScaleSourceCorridor && PhysicalCenterline.Num() >= 2;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float LandscapeHalfWidth = Candidate.HorizontalSpanYCm * 0.5f;
    const float MaxBankOffset = bPhysicalCorridor
        ? FMath::Min(
              bZambeziWoodland ? 52000.0f : 18000.0f,
              LandscapeHalfWidth - 220.0f)
        : FMath::Max(ActiveRiverHalfWidth + 300.0f, LandscapeHalfWidth - 220.0f);
    auto ResolveLogicalRiverPoint =
        [&Candidate, &PhysicalCenterline, bPhysicalCorridor](float LogicalX, float LateralOffset)
    {
        if (!bPhysicalCorridor)
        {
            return FVector2D(
                LogicalX,
                GetPreviewRiverCenterY(Candidate.PreviewSpec, LogicalX) + LateralOffset);
        }
        const float Progress = FMath::Clamp((LogicalX + 2500.0f) / 27900.0f, 0.0f, 1.0f);
        FVector2D Tangent;
        const FVector2D Center = SampleLandscapeCandidateCenterlineWorld(
            Candidate,
            PhysicalCenterline,
            Progress,
            &Tangent);
        const FVector2D Normal(-Tangent.Y, Tangent.X);
        return Center + Normal * LateralOffset;
    };
    TArray<FVector2D> PhysicalCenterlineWorldPoints;
    PhysicalCenterlineWorldPoints.Reserve(PhysicalCenterline.Num());
    for (int32 PointIndex = 0;
         PointIndex < PhysicalCenterline.Num();
         ++PointIndex)
    {
        const float Progress = PhysicalCenterline.Num() > 1
            ? static_cast<float>(PointIndex) /
                static_cast<float>(PhysicalCenterline.Num() - 1)
            : 0.0f;
        PhysicalCenterlineWorldPoints.Add(
            SampleLandscapeCandidateCenterlineWorld(
                Candidate,
                PhysicalCenterline,
                Progress));
    }
    auto GetMinimumCenterlineDistanceCm =
        [&PhysicalCenterlineWorldPoints](const FVector2D& Point)
    {
        float MinimumDistanceSquared = TNumericLimits<float>::Max();
        for (int32 SegmentIndex = 1;
             SegmentIndex < PhysicalCenterlineWorldPoints.Num();
             ++SegmentIndex)
        {
            const FVector2D Start =
                PhysicalCenterlineWorldPoints[SegmentIndex - 1];
            const FVector2D End =
                PhysicalCenterlineWorldPoints[SegmentIndex];
            const FVector2D Delta = End - Start;
            const float LengthSquared = Delta.SizeSquared();
            const float SegmentT = LengthSquared > UE_SMALL_NUMBER
                ? FMath::Clamp(
                    FVector2D::DotProduct(Point - Start, Delta) /
                        LengthSquared,
                    0.0f,
                    1.0f)
                : 0.0f;
            MinimumDistanceSquared = FMath::Min(
                MinimumDistanceSquared,
                FVector2D::DistSquared(Point, Start + Delta * SegmentT));
        }
        return FMath::Sqrt(MinimumDistanceSquared);
    };
    auto GetConditionedWaterWorldZ =
        [&Candidate, &PhysicalCenterline](float LogicalX)
    {
        const float Progress = FMath::Clamp(
            (LogicalX + 2500.0f) / 27900.0f,
            0.0f,
            1.0f);
        float SurfaceWorldZ = 0.0f;
        if (!SampleLandscapeCandidateConditionedVisualSurfaceWorldZ(
                Candidate,
                PhysicalCenterline,
                Progress,
                SurfaceWorldZ))
        {
            return Candidate.PreviewSpec.FlowWaterLevelOffsetCm;
        }
        return SurfaceWorldZ +
            Candidate.PreviewSpec.FlowWaterLevelOffsetCm;
    };
    auto GetLandscapeHeight = [Landscape, &Spec](float X, float Y)
    {
        return Landscape->GetHeightAtLocation(FVector(X, Y, 0.0f), EHeightfieldSource::Editor)
            .Get(Spec.FlowWaterLevelOffsetCm - 24.0f);
    };
    auto GetLandscapeSlopeDegrees = [&GetLandscapeHeight](float X, float Y)
    {
        // The physical-corridor DEM is sampled at roughly 6-10 m spacing. A
        // 12 m baseline rejects cliff faces without reacting to single-vertex
        // noise or forcing woody vegetation onto the water-adjacent bank.
        constexpr float SampleRadiusCm = 1200.0f;
        const float GradientX =
            (GetLandscapeHeight(X + SampleRadiusCm, Y) -
             GetLandscapeHeight(X - SampleRadiusCm, Y)) /
            (2.0f * SampleRadiusCm);
        const float GradientY =
            (GetLandscapeHeight(X, Y + SampleRadiusCm) -
             GetLandscapeHeight(X, Y - SampleRadiusCm)) /
            (2.0f * SampleRadiusCm);
        return FMath::RadiansToDegrees(
            FMath::Atan(FMath::Sqrt(GradientX * GradientX + GradientY * GradientY)));
    };
    auto AddGroundedInstance = [](UHierarchicalInstancedStaticMeshComponent* Component,
                                  UStaticMesh* Mesh,
                                  const FVector2D& GroundLocation,
                                  float GroundZ,
                                  const FRotator& Rotation,
                                  const FVector& Scale)
    {
        const FBox Bounds = GetLandscapeCandidateEffectiveMeshBounds(Mesh);
        const float GroundedPivotZ = GroundZ - Bounds.Min.Z * Scale.Z;
        return Component->AddInstance(
            FTransform(
                Rotation,
                FVector(GroundLocation.X, GroundLocation.Y, GroundedPivotZ),
                Scale),
            true);
    };

    int32 RunnableLaunchTalusPlacedCount = 0;
    int32 RunnableLaunchTalusRejectedPlacementCount = 0;
    float RunnableLaunchTalusMaximumSlopeDegrees = 0.0f;
    const int32 BoulderCount = bPhysicalCorridor
        ? 180
        : (Spec.bDesertCanyon ? 62 : (bRainforest ? 48 : 44));
    for (int32 BoulderIndex = 0; BoulderIndex < BoulderCount; ++BoulderIndex)
    {
        const float T = (static_cast<float>(BoulderIndex) + 0.5f) / static_cast<float>(BoulderCount);
        const float Phase = static_cast<float>(BoulderIndex) * 1.6180339f;
        const float Side = (BoulderIndex % 2 == 0) ? -1.0f : 1.0f;
        const bool bChannelRock = BoulderIndex % 9 == 0;
        const float BaseX = FMath::Lerp(
            bPhysicalCorridor ? 5000.0f : -1600.0f,
            25500.0f,
            T) + 180.0f * FMath::Sin(Phase);
        const float BaseOffset = bChannelRock
            ? ActiveRiverHalfWidth * (0.62f + 0.24f * FMath::Abs(FMath::Sin(Phase * 0.77f)))
            : FMath::Lerp(
                  ActiveRiverHalfWidth + (bPhysicalCorridor && BaseX < 3200.0f ? 900.0f : 260.0f),
                  MaxBankOffset * 0.78f,
                  FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.43f)), 0.72f));

        const FVector2D BasePoint = ResolveLogicalRiverPoint(BaseX, Side * BaseOffset);
        float BestX = BasePoint.X;
        float BestY = BasePoint.Y;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 7; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                155.0f * FMath::Sin(Phase * 0.61f + static_cast<float>(CandidateIndex) * 1.17f);
            const float CandidateOffset = FMath::Clamp(
                BaseOffset + 135.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.93f),
                ActiveRiverHalfWidth * 0.20f,
                MaxBankOffset);
            const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                CandidateX,
                Side * CandidateOffset);
            const float CandidateWorldX = CandidatePoint.X;
            const float CandidateWorldY = CandidatePoint.Y;
            const float WaterT = bPhysicalCorridor
                ? FMath::Clamp(1.0f - CandidateOffset / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f)
                : SamplePreviewMaskAtWorld(Spec, &WaterMask, CandidateWorldX, CandidateWorldY);
            const float VegetationT = bPhysicalCorridor
                ? SmoothPreviewStep(ActiveRiverHalfWidth + 400.0f, MaxBankOffset, CandidateOffset)
                : SamplePreviewMaskAtWorld(Spec, &VegetationMask, CandidateWorldX, CandidateWorldY);
            const float TargetWaterT = bChannelRock ? 0.68f : 0.20f;
            const float Score = 1.0f - FMath::Abs(WaterT - TargetWaterT) -
                VegetationT * (bChannelRock ? 0.12f : 0.34f) +
                0.06f * FMath::Sin(Phase + static_cast<float>(CandidateIndex));
            if (Score > BestScore)
            {
                BestScore = Score;
                BestX = CandidateWorldX;
                BestY = CandidateWorldY;
            }
        }

        const float TargetBoulderHeightCm = bPhysicalCorridor
            ? (65.0f + 18.0f * static_cast<float>(BoulderIndex % 6)) *
                (bChannelRock ? 1.05f : 1.0f)
            : (Spec.bDesertCanyon
                   ? 82.0f + 20.0f * static_cast<float>(BoulderIndex % 5)
                   : (bRainforest ? 74.0f + 18.0f * static_cast<float>(BoulderIndex % 5)
                                  : 66.0f + 16.0f * static_cast<float>(BoulderIndex % 5))) *
                (bChannelRock ? 0.72f : 1.0f);
        const float BoulderScaleZ = TargetBoulderHeightCm / 100.0f;
        if (ReviewedRockMeshes.Num() == 6 && ReviewedRockInstances.Num() == 6)
        {
            const int32 VariantIndex = BoulderIndex % ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetBoulderHeightCm / MeshHeightCm;
            AddGroundedInstance(
                ReviewedRockInstances[VariantIndex],
                RockMesh,
                FVector2D(BestX, BestY),
                GetLandscapeHeight(BestX, BestY),
                FRotator(
                    bChannelRock ? -5.0f : 2.0f * FMath::Sin(Phase),
                    static_cast<float>((BoulderIndex * 47) % 360),
                    3.0f * FMath::Cos(Phase * 0.73f)),
                FVector(
                    UniformScale * (0.92f + 0.07f * static_cast<float>(BoulderIndex % 4)),
                    UniformScale * (0.88f + 0.06f * static_cast<float>((BoulderIndex + 2) % 5)),
                    UniformScale));
        }
        else
        {
            const FLinearColor BoulderColor = FMath::Lerp(
                ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.70f : 0.52f),
                ScalePreviewColor(Spec.WaterColor, 0.28f),
                bChannelRock ? 0.24f : (bRainforest ? 0.16f : 0.10f));
            AActor* BoulderActor = AddPreviewIrregularRockActor(
                World,
                FString::Printf(TEXT("RaftSim_LandscapeCandidate_IrregularBoulder_%03d_%s"), BoulderIndex, *Spec.RiverId),
                FVector(BestX, BestY, GetLandscapeHeight(BestX, BestY)),
                static_cast<float>((BoulderIndex * 47) % 360),
                FVector(
                    BoulderScaleZ * (1.15f + 0.08f * static_cast<float>(BoulderIndex % 4)),
                    BoulderScaleZ * (0.76f + 0.07f * static_cast<float>((BoulderIndex + 2) % 5)),
                    BoulderScaleZ),
                BoulderColor,
                BoulderIndex + 42000);
            if (BoulderActor)
            {
                if (UProceduralMeshComponent* BoulderComponent =
                        BoulderActor->FindComponentByClass<UProceduralMeshComponent>())
                {
                    BoulderComponent->SetCastShadow(true);
                    BoulderComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                }
            }
        }
        ++OutResult.DressingBoulderInstanceCount;
    }

    int32 TemperateWaterlinePlacedCount = 0;
    int32 TemperateWaterlineRejectedPlacementCount = 0;
    float TemperateWaterlineMinimumCenterlineDistanceCm =
        TNumericLimits<float>::Max();
    float TemperateWaterlineMaximumSlopeDegrees = 0.0f;
    if (bOpaqueTemperate &&
        ReviewedRockMeshes.Num() == 6 &&
        TemperateWaterlineStructureInstances.Num() == 6)
    {
        // The source DEM establishes terrain and collision, while the live C++
        // water/solver owns the playable channel. This dense CC0 morphology-
        // donor layer fills only unresolved sub-DEM bank structure. Every
        // instance is grounded on the source Landscape, starts outside the
        // complete visible-water width, remains non-colliding, and carries no
        // lithology, bathymetry, hydraulic, or raft-force authority.
        const float VisibleRiverHalfWidth = ActiveRiverHalfWidth *
            (bChilko ? 1.20f : 1.18f);
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            TemperateWaterlineStructureTargetInstanceCount / BankSideCount;
        for (int32 StructureIndex = 0;
             StructureIndex < TemperateWaterlineStructureTargetInstanceCount;
             ++StructureIndex)
        {
            const int32 SideIndex = StructureIndex % BankSideCount;
            const int32 AlongIndex = StructureIndex / BankSideCount;
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(StructureIndex, 10103)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX =
                FMath::Lerp(-2380.0f, 25300.0f, AlongT) +
                95.0f * FMath::Sin(
                    static_cast<float>(StructureIndex) * 1.3247179f);

            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + 420.0f));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 72;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX +
                    FMath::Lerp(
                        -115.0f,
                        115.0f,
                        ZambeziVegetationUnitRandom(
                            StructureIndex * 79 + CandidateIndex,
                            10111));
                const float CandidateAdditionalOffset = FMath::Lerp(
                    85.0f,
                    3200.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            StructureIndex * 83 + CandidateIndex,
                            10133),
                        1.72f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side *
                        (VisibleRiverHalfWidth + CandidateAdditionalOffset));
                const float CandidateSlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float CandidateCenterlineDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float HeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (CandidateSlopeDegrees >
                        TemperateWaterlineStructureSlopeCeilingDegrees ||
                    CandidateCenterlineDistanceCm <
                        VisibleRiverHalfWidth + 60.0f ||
                    HeightAboveWaterCm < -25.0f ||
                    HeightAboveWaterCm > 2200.0f)
                {
                    continue;
                }

                const float TargetDryHeightCm = 85.0f +
                    210.0f * ZambeziVegetationUnitRandom(
                        StructureIndex,
                        10139);
                const float PlacementScore =
                    0.62f * FMath::Abs(
                        HeightAboveWaterCm - TargetDryHeightCm) / 2200.0f +
                    0.24f * CandidateAdditionalOffset / 3200.0f +
                    0.14f * CandidateSlopeDegrees /
                        TemperateWaterlineStructureSlopeCeilingDegrees;
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestPoint = CandidatePoint;
                    BestSlopeDegrees = CandidateSlopeDegrees;
                    BestCenterlineDistanceCm =
                        CandidateCenterlineDistanceCm;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++TemperateWaterlineRejectedPlacementCount;
                continue;
            }

            const int32 ScaleClass = StructureIndex % 20;
            const float TargetHeightCm = ScaleClass == 0
                ? FMath::Lerp(
                      160.0f,
                      260.0f,
                      ZambeziVegetationUnitRandom(StructureIndex, 10141))
                : (ScaleClass < 5
                       ? FMath::Lerp(
                             60.0f,
                             135.0f,
                             ZambeziVegetationUnitRandom(
                                 StructureIndex,
                                 10151))
                       : FMath::Lerp(
                             22.0f,
                             58.0f,
                             ZambeziVegetationUnitRandom(
                                 StructureIndex,
                                 10159)));
            const int32 VariantIndex = StructureIndex %
                ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            UHierarchicalInstancedStaticMeshComponent* StructureComponent =
                TemperateWaterlineStructureInstances[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                StructureComponent,
                RockMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.10f, 0.0f, 5.5f),
                    360.0f * ZambeziVegetationUnitRandom(
                        StructureIndex,
                        10163),
                    FMath::Lerp(
                        -5.0f,
                        5.0f,
                        ZambeziVegetationUnitRandom(
                            StructureIndex,
                            10169))),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.76f,
                        1.34f,
                        ZambeziVegetationUnitRandom(
                            StructureIndex,
                            10177)),
                    UniformScale * FMath::Lerp(
                        0.74f,
                        1.30f,
                        ZambeziVegetationUnitRandom(
                            StructureIndex,
                            10181)),
                    UniformScale));
            ++TemperateWaterlinePlacedCount;
            ++OutResult.DressingBoulderInstanceCount;
            TemperateWaterlineMinimumCenterlineDistanceCm = FMath::Min(
                TemperateWaterlineMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            TemperateWaterlineMaximumSlopeDegrees = FMath::Max(
                TemperateWaterlineMaximumSlopeDegrees,
                BestSlopeDegrees);
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             TemperateWaterlineStructureInstances)
        {
            if (Component)
            {
                Component->MarkRenderStateDirty();
            }
        }
        OutSummary += FString::Printf(
            TEXT("%s organic waterline structure V1: %d/%d source-grounded, ")
            TEXT("non-colliding CC0 rock analogs across both banks; %d targets ")
            TEXT("rejected by visible-water clearance, dry-height, or %.1f-degree ")
            TEXT("slope gates; minimum full-route centerline distance %.1f cm and ")
            TEXT("maximum placed slope %.2f degrees. Presentation-only procedural ")
            TEXT("gap fill with no lithology, hydraulic, collision, bathymetry, or ")
            TEXT("raft-force authority.\n"),
            *Spec.RiverId,
            TemperateWaterlinePlacedCount,
            TemperateWaterlineStructureTargetInstanceCount,
            TemperateWaterlineRejectedPlacementCount,
            TemperateWaterlineStructureSlopeCeilingDegrees,
            TemperateWaterlineMinimumCenterlineDistanceCm,
            TemperateWaterlineMaximumSlopeDegrees);
    }
    OutResult.DressingTemperateWaterlineTargetInstanceCount =
        bOpaqueTemperate
            ? TemperateWaterlineStructureTargetInstanceCount
            : 0;
    OutResult.DressingTemperateWaterlineInstanceCount =
        TemperateWaterlinePlacedCount;
    OutResult.DressingTemperateWaterlineRejectedPlacementCount =
        TemperateWaterlineRejectedPlacementCount;
    OutResult.DressingTemperateWaterlineMinimumCenterlineDistanceCm =
        TemperateWaterlinePlacedCount > 0
            ? TemperateWaterlineMinimumCenterlineDistanceCm
            : 0.0f;
    OutResult.DressingTemperateWaterlineMaximumSlopeDegrees =
        TemperateWaterlineMaximumSlopeDegrees;

    int32 ChilkoShorelineGravelPlacedCount = 0;
    int32 ChilkoShorelineGravelRejectedPlacementCount = 0;
    float ChilkoShorelineGravelMinimumCenterlineDistanceCm =
        TNumericLimits<float>::Max();
    float ChilkoShorelineGravelMaximumSlopeDegrees = 0.0f;
    if (bChilko && bPhysicalCorridor &&
        ReviewedRockMeshes.Num() == 6 &&
        ChilkoOrganicShorelineGravelInstances.Num() == 6)
    {
        // Break up the broad, visibly smooth Lava Canyon shoreline benches
        // with small, irregular CC0 rock morphology donors. The conditioned
        // source Landscape remains ground/collision authority; this layer is
        // always outside the full visible-water width and cannot affect the
        // solver, bathymetry, hydraulics, or raft forces. V2 covers the entire
        // 0-600 m runnable corridor; V1 stopped before the 300 m evidence site.
        const float VisibleRiverHalfWidth = ActiveRiverHalfWidth * 1.03f;
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            ChilkoOrganicShorelineGravelTargetInstanceCount / BankSideCount;
        for (int32 GravelIndex = 0;
             GravelIndex < ChilkoOrganicShorelineGravelTargetInstanceCount;
             ++GravelIndex)
        {
            const int32 SideIndex = GravelIndex % BankSideCount;
            const int32 AlongIndex = GravelIndex / BankSideCount;
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(GravelIndex, 10303)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX =
                FMath::Lerp(
                    ChilkoOrganicShorelineStartStationCm,
                    ChilkoOrganicShorelineEndStationCm,
                    AlongT) +
                72.0f * FMath::Sin(
                    static_cast<float>(GravelIndex) * 0.7548777f);
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + 360.0f));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 48;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX + FMath::Lerp(
                    -105.0f,
                    105.0f,
                    ZambeziVegetationUnitRandom(
                        GravelIndex * 53 + CandidateIndex,
                        10313));
                const float AdditionalOffset = FMath::Lerp(
                    70.0f,
                    2400.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            GravelIndex * 59 + CandidateIndex,
                            10321),
                        1.90f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (VisibleRiverHalfWidth + AdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float CenterlineDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float HeightAboveWaterCm = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y) -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees >
                        ChilkoOrganicShorelineGravelSlopeCeilingDegrees ||
                    CenterlineDistanceCm < VisibleRiverHalfWidth + 45.0f ||
                    HeightAboveWaterCm < -5.0f ||
                    HeightAboveWaterCm > 650.0f)
                {
                    continue;
                }
                const float TargetDryHeightCm = FMath::Lerp(
                    48.0f,
                    260.0f,
                    ZambeziVegetationUnitRandom(GravelIndex, 10331));
                const float Score =
                    0.58f * FMath::Abs(
                        HeightAboveWaterCm - TargetDryHeightCm) / 650.0f +
                    0.29f * AdditionalOffset / 2400.0f +
                    0.13f * SlopeDegrees /
                        ChilkoOrganicShorelineGravelSlopeCeilingDegrees;
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestPoint = CandidatePoint;
                    BestSlopeDegrees = SlopeDegrees;
                    BestCenterlineDistanceCm = CenterlineDistanceCm;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++ChilkoShorelineGravelRejectedPlacementCount;
                continue;
            }

            // Preserve a gravel/cobble-dominant bank. V2 devoted one in 36
            // instances to 0.8-1.4 m silhouettes; that produced the isolated
            // boulder-sized outlier in the matched close view. V3 makes the
            // rare class half as frequent and hard-caps it at one metre.
            const int32 ScaleClass = GravelIndex % 72;
            const float TargetHeightCm = ScaleClass == 0
                ? FMath::Lerp(
                      65.0f,
                      ChilkoOrganicShorelineGravelRareMaximumHeightCm,
                      ZambeziVegetationUnitRandom(GravelIndex, 10343))
                : (ScaleClass < 12
                       ? FMath::Lerp(
                             28.0f,
                             62.0f,
                             ZambeziVegetationUnitRandom(
                                 GravelIndex,
                                 10351))
                       : FMath::Lerp(
                             8.0f,
                             28.0f,
                             ZambeziVegetationUnitRandom(
                                 GravelIndex,
                                 10357)));
            const int32 VariantIndex = GravelIndex % ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            UHierarchicalInstancedStaticMeshComponent* GravelComponent =
                ChilkoOrganicShorelineGravelInstances[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                GravelComponent,
                RockMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.08f, 0.0f, 3.4f),
                    360.0f * ZambeziVegetationUnitRandom(
                        GravelIndex,
                        10369),
                    FMath::Lerp(
                        -4.0f,
                        4.0f,
                        ZambeziVegetationUnitRandom(
                            GravelIndex,
                            10373))),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.70f,
                        1.48f,
                        ZambeziVegetationUnitRandom(
                            GravelIndex,
                            10379)),
                    UniformScale * FMath::Lerp(
                        0.72f,
                        1.44f,
                        ZambeziVegetationUnitRandom(
                            GravelIndex,
                            10391)),
                    UniformScale));
            ++ChilkoShorelineGravelPlacedCount;
            ++OutResult.DressingBoulderInstanceCount;
            ChilkoShorelineGravelMinimumCenterlineDistanceCm = FMath::Min(
                ChilkoShorelineGravelMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            ChilkoShorelineGravelMaximumSlopeDegrees = FMath::Max(
                ChilkoShorelineGravelMaximumSlopeDegrees,
                BestSlopeDegrees);
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ChilkoOrganicShorelineGravelInstances)
        {
            Component->MarkRenderStateDirty();
        }
        OutSummary += FString::Printf(
            TEXT("%s organic shoreline gravel V3: %d/%d source-grounded, ")
            TEXT("non-colliding six-morphology cobbles across both full-route ")
            TEXT("banks; %d targets rejected by visible-water clearance, ")
            TEXT("dry-height, or %.1f-degree slope gates; minimum centerline ")
            TEXT("distance %.1f cm and maximum placed slope %.2f degrees. ")
            TEXT("Presentation-only procedural gap fill with no lithology, ")
            TEXT("collision, bathymetry, hydraulic, or raft-force authority.\n"),
            *Spec.RiverId,
            ChilkoShorelineGravelPlacedCount,
            ChilkoOrganicShorelineGravelTargetInstanceCount,
            ChilkoShorelineGravelRejectedPlacementCount,
            ChilkoOrganicShorelineGravelSlopeCeilingDegrees,
            ChilkoShorelineGravelMinimumCenterlineDistanceCm,
            ChilkoShorelineGravelMaximumSlopeDegrees);
    }
    OutResult.DressingChilkoOrganicShorelineGravelTargetInstanceCount =
        bChilko ? ChilkoOrganicShorelineGravelTargetInstanceCount : 0;
    OutResult.DressingChilkoOrganicShorelineGravelInstanceCount =
        ChilkoShorelineGravelPlacedCount;
    OutResult.DressingChilkoOrganicShorelineGravelRejectedPlacementCount =
        ChilkoShorelineGravelRejectedPlacementCount;
    OutResult.DressingChilkoOrganicShorelineGravelMinimumCenterlineDistanceCm =
        ChilkoShorelineGravelPlacedCount > 0
            ? ChilkoShorelineGravelMinimumCenterlineDistanceCm
            : 0.0f;
    OutResult.DressingChilkoOrganicShorelineGravelMaximumSlopeDegrees =
        ChilkoShorelineGravelMaximumSlopeDegrees;

    int32 ChilkoShorelineGroundCoverPlacedCount = 0;
    int32 ChilkoShorelineGroundCoverRejectedPlacementCount = 0;
    float ChilkoShorelineGroundCoverMinimumCenterlineDistanceCm =
        TNumericLimits<float>::Max();
    float ChilkoShorelineGroundCoverMaximumSlopeDegrees = 0.0f;
    if (bChilko && bPhysicalCorridor &&
        ChilkoOrganicShorelineGroundCoverInstances.Num() == 2)
    {
        // Short, non-shadowing meadow patches soften the transition from the
        // gravel band to the wider shrub/canopy layer. They are selected only
        // on dry, low-slope source Landscape and make no species or ecology
        // claim. V2 spans the full runnable 0-600 m corridor.
        const float VisibleRiverHalfWidth = ActiveRiverHalfWidth * 1.03f;
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            ChilkoOrganicShorelineGroundCoverTargetInstanceCount /
            BankSideCount;
        for (int32 CoverIndex = 0;
             CoverIndex < ChilkoOrganicShorelineGroundCoverTargetInstanceCount;
             ++CoverIndex)
        {
            const int32 SideIndex = CoverIndex % BankSideCount;
            const int32 AlongIndex = CoverIndex / BankSideCount;
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(CoverIndex, 10403)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX =
                FMath::Lerp(
                    ChilkoOrganicShorelineStartStationCm,
                    ChilkoOrganicShorelineEndStationCm,
                    AlongT) +
                88.0f * FMath::Sin(
                    static_cast<float>(CoverIndex) * 0.618034f);
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + 620.0f));
            float BestLogicalX = BaseLogicalX;
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 48;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX + FMath::Lerp(
                    -130.0f,
                    130.0f,
                    ZambeziVegetationUnitRandom(
                        CoverIndex * 61 + CandidateIndex,
                        10411));
                const float AdditionalOffset = FMath::Lerp(
                    120.0f,
                    4200.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            CoverIndex * 73 + CandidateIndex,
                            10427),
                        1.48f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (VisibleRiverHalfWidth + AdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float CenterlineDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float HeightAboveWaterCm = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y) -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees >
                        ChilkoOrganicShorelineGroundCoverSlopeCeilingDegrees ||
                    CenterlineDistanceCm < VisibleRiverHalfWidth + 85.0f ||
                    HeightAboveWaterCm < 18.0f ||
                    HeightAboveWaterCm > 1100.0f)
                {
                    continue;
                }
                const float TargetDryHeightCm = FMath::Lerp(
                    125.0f,
                    650.0f,
                    ZambeziVegetationUnitRandom(CoverIndex, 10433));
                const float Score =
                    0.58f * FMath::Abs(
                        HeightAboveWaterCm - TargetDryHeightCm) / 1100.0f +
                    0.28f * AdditionalOffset / 4200.0f +
                    0.14f * SlopeDegrees /
                        ChilkoOrganicShorelineGroundCoverSlopeCeilingDegrees;
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestPoint = CandidatePoint;
                    BestLogicalX = CandidateLogicalX;
                    BestSlopeDegrees = SlopeDegrees;
                    BestCenterlineDistanceCm = CenterlineDistanceCm;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++ChilkoShorelineGroundCoverRejectedPlacementCount;
                continue;
            }

            const int32 MorphologyIndex =
                ZambeziVegetationUnitRandom(CoverIndex, 10439) > 0.48f ? 1 : 0;
            UStaticMesh* CoverMesh = MorphologyIndex == 0
                ? UnderstoryMesh
                : TemperateUnderstoryMeshB;
            UHierarchicalInstancedStaticMeshComponent* CoverComponent =
                ChilkoOrganicShorelineGroundCoverInstances[MorphologyIndex];
            const float TargetHeightCm = FMath::Lerp(
                ChilkoOrganicShorelineGroundCoverMinimumHeightCm,
                ChilkoOrganicShorelineGroundCoverMaximumHeightCm,
                ZambeziVegetationUnitRandom(CoverIndex, 10453));
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(CoverMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                CoverComponent,
                CoverMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.02f, 0.0f, 0.65f),
                    360.0f * ZambeziVegetationUnitRandom(
                        CoverIndex,
                        10457),
                    0.45f * FMath::Sin(BestLogicalX * 0.0013f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.74f,
                        1.42f,
                        ZambeziVegetationUnitRandom(
                            CoverIndex,
                            10463)),
                    UniformScale * FMath::Lerp(
                        0.76f,
                        1.38f,
                        ZambeziVegetationUnitRandom(
                            CoverIndex,
                            10477)),
                    UniformScale));
            ++ChilkoShorelineGroundCoverPlacedCount;
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
            ChilkoShorelineGroundCoverMinimumCenterlineDistanceCm = FMath::Min(
                ChilkoShorelineGroundCoverMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            ChilkoShorelineGroundCoverMaximumSlopeDegrees = FMath::Max(
                ChilkoShorelineGroundCoverMaximumSlopeDegrees,
                BestSlopeDegrees);
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ChilkoOrganicShorelineGroundCoverInstances)
        {
            Component->MarkRenderStateDirty();
        }
        OutSummary += FString::Printf(
            TEXT("%s organic shoreline ground cover V3: %d/%d short, ")
            TEXT("non-shadowing, source-grounded patches across both full-route ")
            TEXT("dry banks; %d targets rejected by visible-water clearance, ")
            TEXT("dry-height, or %.1f-degree slope gates; minimum centerline ")
            TEXT("distance %.1f cm and maximum placed slope %.2f degrees. ")
            TEXT("Presentation-only procedural gap fill with no species, ")
            TEXT("ecology, survey, hydraulic, collision, or raft-force authority.\n"),
            *Spec.RiverId,
            ChilkoShorelineGroundCoverPlacedCount,
            ChilkoOrganicShorelineGroundCoverTargetInstanceCount,
            ChilkoShorelineGroundCoverRejectedPlacementCount,
            ChilkoOrganicShorelineGroundCoverSlopeCeilingDegrees,
            ChilkoShorelineGroundCoverMinimumCenterlineDistanceCm,
            ChilkoShorelineGroundCoverMaximumSlopeDegrees);
    }
    OutResult.DressingChilkoOrganicShorelineGroundCoverTargetInstanceCount =
        bChilko ? ChilkoOrganicShorelineGroundCoverTargetInstanceCount : 0;
    OutResult.DressingChilkoOrganicShorelineGroundCoverInstanceCount =
        ChilkoShorelineGroundCoverPlacedCount;
    OutResult.DressingChilkoOrganicShorelineGroundCoverRejectedPlacementCount =
        ChilkoShorelineGroundCoverRejectedPlacementCount;
    OutResult.DressingChilkoOrganicShorelineGroundCoverMinimumCenterlineDistanceCm =
        ChilkoShorelineGroundCoverPlacedCount > 0
            ? ChilkoShorelineGroundCoverMinimumCenterlineDistanceCm
            : 0.0f;
    OutResult.DressingChilkoOrganicShorelineGroundCoverMaximumSlopeDegrees =
        ChilkoShorelineGroundCoverMaximumSlopeDegrees;

    if (bZambeziWoodland &&
        ReviewedRockMeshes.Num() == 6 &&
        ZambeziRunnableLaunchTalusInstances.Num() == 6)
    {
        // The legacy physical-corridor boulder distribution starts around
        // station 5 km. Give the actually runnable first kilometre its own
        // auditable dry-bank talus layer. These generic CC0 rock analogs are
        // visual dressing only: the source Landscape remains collision and
        // height authority, and no instance may enter the active route.
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            ZambeziRunnableLaunchTalusInstanceCount / BankSideCount;
        for (int32 TalusIndex = 0;
             TalusIndex < ZambeziRunnableLaunchTalusInstanceCount;
             ++TalusIndex)
        {
            const int32 SideIndex = TalusIndex % BankSideCount;
            const int32 AlongIndex = TalusIndex / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(TalusIndex, 9403)) /
                static_cast<float>(InstancesPerSide);
            // Logical X -2390..-1580 maps to approximately 118-993 m down
            // the conditioned route, just ahead of the station-75 m launch.
            const float BaseLogicalX = FMath::Lerp(-2390.0f, -1580.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (ActiveRiverHalfWidth + 1800.0f));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestPlacementScore = TNumericLimits<float>::Max();
            float BestLogicalX = BaseLogicalX;
            for (int32 CandidateIndex = 0; CandidateIndex < 128; ++CandidateIndex)
            {
                const float CandidatePhase =
                    static_cast<float>(TalusIndex) * 0.7548777f +
                    static_cast<float>(CandidateIndex) * 1.3247179f;
                const float CandidateLogicalX = BaseLogicalX +
                    32.0f * FMath::Sin(CandidatePhase);
                const float CandidateAdditionalOffset = FMath::Lerp(
                    600.0f,
                    14000.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            TalusIndex * 131 + CandidateIndex,
                            9419),
                        1.55f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (ActiveRiverHalfWidth + CandidateAdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                const float FullRouteDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                if (SlopeDegrees >
                        ZambeziRunnableLaunchTalusSlopeCeilingDegrees ||
                    DryHeightAboveWaterCm < 100.0f ||
                    DryHeightAboveWaterCm > 16000.0f ||
                    FullRouteDistanceCm < ActiveRiverHalfWidth + 300.0f)
                {
                    continue;
                }
                const float PlacementScore =
                    0.08f * FMath::Abs(SlopeDegrees - 18.0f) +
                    0.35f * CandidateAdditionalOffset / 14000.0f +
                    0.15f * FMath::Abs(DryHeightAboveWaterCm - 2800.0f) /
                        16000.0f;
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestPoint = CandidatePoint;
                    BestSlopeDegrees = SlopeDegrees;
                    BestLogicalX = CandidateLogicalX;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++RunnableLaunchTalusRejectedPlacementCount;
                continue;
            }

            const int32 ScaleClass = TalusIndex % 20;
            const float TargetHeightCm = ScaleClass == 0
                ? FMath::Lerp(
                      380.0f,
                      520.0f,
                      ZambeziVegetationUnitRandom(TalusIndex, 9431))
                : (ScaleClass < 5
                       ? FMath::Lerp(
                             220.0f,
                             360.0f,
                             ZambeziVegetationUnitRandom(TalusIndex, 9433))
                       : FMath::Lerp(
                             95.0f,
                             220.0f,
                             ZambeziVegetationUnitRandom(TalusIndex, 9437)));
            const int32 VariantIndex = TalusIndex % ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            UHierarchicalInstancedStaticMeshComponent* TalusComponent =
                ZambeziRunnableLaunchTalusInstances[VariantIndex];
            const int32 InstanceIndex = AddGroundedInstance(
                TalusComponent,
                RockMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.16f, 0.0f, 7.5f),
                    360.0f * ZambeziVegetationUnitRandom(TalusIndex, 9461),
                    FMath::Lerp(
                        -6.0f,
                        6.0f,
                        ZambeziVegetationUnitRandom(TalusIndex, 9473))),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.82f,
                        1.28f,
                        ZambeziVegetationUnitRandom(TalusIndex, 9491)),
                    UniformScale * FMath::Lerp(
                        0.78f,
                        1.22f,
                        ZambeziVegetationUnitRandom(TalusIndex, 9497)),
                    UniformScale));
            TalusComponent->SetCustomDataValue(
                InstanceIndex,
                0,
                GetConditionedWaterWorldZ(BestLogicalX),
                false);
            ++RunnableLaunchTalusPlacedCount;
            RunnableLaunchTalusMaximumSlopeDegrees = FMath::Max(
                RunnableLaunchTalusMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++OutResult.DressingBoulderInstanceCount;
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             ZambeziRunnableLaunchTalusInstances)
        {
            if (Component)
            {
                Component->MarkRenderStateDirty();
            }
        }
        OutSummary += FString::Printf(
            TEXT("Zambezi runnable-launch talus: %d/%d source-grounded, "
                 "non-colliding generic rock analogs across both dry banks, each "
                 "with a conditioned-profile waterline in custom-data channel zero; "
                 "%d targets rejected by full-route distance, dry-height, or "
                 "%.1f-degree slope gates; maximum placed slope %.2f degrees. "
                 "Presentation-only with no Batoka lithology or hydraulic authority.\n"),
            RunnableLaunchTalusPlacedCount,
            ZambeziRunnableLaunchTalusInstanceCount,
            RunnableLaunchTalusRejectedPlacementCount,
            ZambeziRunnableLaunchTalusSlopeCeilingDegrees,
            RunnableLaunchTalusMaximumSlopeDegrees);
    }
    OutResult.DressingRunnableLaunchTalusTargetInstanceCount =
        bZambeziWoodland ? ZambeziRunnableLaunchTalusInstanceCount : 0;
    OutResult.DressingRunnableLaunchTalusInstanceCount =
        RunnableLaunchTalusPlacedCount;
    OutResult.DressingRunnableLaunchTalusRejectedPlacementCount =
        RunnableLaunchTalusRejectedPlacementCount;
    OutResult.DressingRunnableLaunchTalusMaximumSlopeDegrees =
        RunnableLaunchTalusMaximumSlopeDegrees;

    const int32 FoliageClusterCount = bColoradoHance
        ? 0
        : bPhysicalCorridor
        ? (bZambeziWoodland
               ? 5600
               : (bOpaqueTemperate ? 6200 : (Spec.bDesertCanyon ? 800 : 12000)))
        : (Spec.bDesertCanyon ? 110 : (bRainforest ? 420 : 260));
    for (int32 ClusterIndex = 0; ClusterIndex < FoliageClusterCount; ++ClusterIndex)
    {
        const float T = (static_cast<float>(ClusterIndex) + 0.5f) /
            static_cast<float>(FoliageClusterCount);
        const float Phase = static_cast<float>(ClusterIndex) * 1.3247179f;
        const float Side = (ClusterIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = FMath::Lerp(
            bZambeziWoodland ? 4500.0f : -2500.0f,
            25400.0f,
            T) + 230.0f * FMath::Sin(Phase * 0.71f);
        const float BaseOffset = FMath::Lerp(
            ActiveRiverHalfWidth +
                (bZambeziWoodland ? 2600.0f : (Spec.bDesertCanyon ? 260.0f : 180.0f)),
            MaxBankOffset,
            FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.47f)), bRainforest ? 0.42f : 0.66f));

        const FVector2D BasePoint = ResolveLogicalRiverPoint(BaseX, Side * BaseOffset);
        float BestX = BasePoint.X;
        float BestY = BasePoint.Y;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 8; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                190.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.07f);
            const float NearCameraMinimumOffset = CandidateX < 2600.0f
                ? ActiveRiverHalfWidth +
                    (bZambeziWoodland
                         ? 5200.0f
                         : (bRainforest ? 860.0f : (Spec.bDesertCanyon ? 720.0f : 660.0f)))
                : ActiveRiverHalfWidth + (bZambeziWoodland ? 2600.0f : 120.0f);
            const float SearchPhase =
                Phase * 0.69f + static_cast<float>(CandidateIndex) * 0.89f;
            const float CandidateOffset = bZambeziWoodland
                ? FMath::Lerp(
                      NearCameraMinimumOffset,
                      MaxBankOffset,
                      0.08f + 0.92f * FMath::Abs(FMath::Sin(SearchPhase)))
                : FMath::Clamp(
                      BaseOffset + 210.0f * FMath::Sin(SearchPhase),
                      NearCameraMinimumOffset,
                      MaxBankOffset);
            const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                CandidateX,
                Side * CandidateOffset);
            const float CandidateWorldX = CandidatePoint.X;
            const float CandidateWorldY = CandidatePoint.Y;
            const float WaterT = bPhysicalCorridor
                ? FMath::Clamp(1.0f - CandidateOffset / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f)
                : SamplePreviewMaskAtWorld(Spec, &WaterMask, CandidateWorldX, CandidateWorldY);
            const float VegetationT = bPhysicalCorridor
                ? SmoothPreviewStep(ActiveRiverHalfWidth + 500.0f, MaxBankOffset, CandidateOffset)
                : SamplePreviewMaskAtWorld(Spec, &VegetationMask, CandidateWorldX, CandidateWorldY);
            const float SlopeDegrees =
                (bZambeziWoodland || bOpaqueTemperate || bPacuare)
                ? GetLandscapeSlopeDegrees(CandidateWorldX, CandidateWorldY)
                : 0.0f;
            const float SteepSlopePenalty = bZambeziWoodland
                ? 3.2f * SmoothPreviewStep(10.0f, 24.0f, SlopeDegrees)
                : bPacuare
                ? 2.2f * SmoothPreviewStep(24.0f, 42.0f, SlopeDegrees)
                : bOpaqueTemperate
                ? 2.5f * SmoothPreviewStep(18.0f, 34.0f, SlopeDegrees)
                : 0.0f;
            const float Score = VegetationT *
                    (bRainforest ? 1.85f : (bZambeziWoodland ? 1.22f : (Spec.bDesertCanyon ? 0.58f : 1.34f))) -
                WaterT * 1.18f +
                ((bZambeziWoodland || bOpaqueTemperate || bPacuare)
                     ? 0.65f * (1.0f - FMath::Clamp(SlopeDegrees / 18.0f, 0.0f, 1.0f))
                     : 0.0f) -
                SteepSlopePenalty +
                0.07f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.83f);
            if (Score > BestScore)
            {
                BestScore = Score;
                BestX = CandidateWorldX;
                BestY = CandidateWorldY;
            }
        }

        UStaticMesh* SpeciesMesh = UnderstoryMesh;
        UHierarchicalInstancedStaticMeshComponent* SpeciesInstances = UnderstoryInstances;
        bool bCanopyTree = false;
        float TargetHeightCm = 100.0f;
        const bool bNearEvidenceCamera = !bPhysicalCorridor && BaseX < 3800.0f;
        if (bNearEvidenceCamera && !Spec.bDesertCanyon)
        {
            if (ClusterIndex % 2 == 0)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = bRainforest
                    ? 220.0f + 28.0f * static_cast<float>(ClusterIndex % 5)
                    : 185.0f + 24.0f * static_cast<float>(ClusterIndex % 5);
            }
            else
            {
                TargetHeightCm = bRainforest
                    ? 128.0f + 18.0f * static_cast<float>(ClusterIndex % 5)
                    : 104.0f + 15.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (bZambeziWoodland)
        {
            const int32 SpeciesSelector = ClusterIndex % 8;
            if (SpeciesSelector <= 4)
            {
                const bool bUmbrellaTree = ClusterIndex % 2 != 0;
                SpeciesMesh = bUmbrellaTree
                    ? ConiferTreeMesh
                    : BroadleafTreeMesh;
                SpeciesInstances = bUmbrellaTree
                    ? ConiferTreeInstances
                    : BroadleafTreeInstances;
                TargetHeightCm = 720.0f + 72.0f * static_cast<float>(ClusterIndex % 7);
                bCanopyTree = true;
            }
            else if (SpeciesSelector <= 6)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 190.0f + 28.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                TargetHeightCm = 96.0f + 15.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (Spec.bDesertCanyon)
        {
            if (ClusterIndex % 3 == 0)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 165.0f + 24.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                TargetHeightCm = 88.0f + 13.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (bOpaqueTemperate)
        {
            // Each 20-instance block retains the exact biome ratio, but a
            // coprime permutation and block-specific rotation prevent the
            // former conifer/broadleaf/shrub stripes from repeating downriver.
            constexpr int32 TemperateSpeciesBlockSize = 20;
            constexpr int32 TemperateSpeciesPermutation = 7;
            const int32 TemperateBlockIndex =
                ClusterIndex / TemperateSpeciesBlockSize;
            const int32 TemperateBlockOffset = FMath::Clamp(
                FMath::FloorToInt(
                    ZambeziVegetationUnitRandom(
                        TemperateBlockIndex,
                        bChilko ? 8971 : 8963) *
                    static_cast<float>(TemperateSpeciesBlockSize)),
                0,
                TemperateSpeciesBlockSize - 1);
            const int32 SpeciesSelector =
                ((ClusterIndex % TemperateSpeciesBlockSize) *
                     TemperateSpeciesPermutation +
                 TemperateBlockOffset) %
                TemperateSpeciesBlockSize;
            const int32 ConiferLimit = bChilko ? 12 : 8;
            const int32 BroadleafLimit = bChilko ? 15 : 15;
            const bool bUseSecondaryMorphology =
                ZambeziVegetationUnitRandom(ClusterIndex, 8989) > 0.48f;
            if (SpeciesSelector < ConiferLimit)
            {
                SpeciesMesh = bUseSecondaryMorphology
                    ? TemperateConiferTreeMeshB
                    : ConiferTreeMesh;
                SpeciesInstances = bUseSecondaryMorphology
                    ? TemperateConiferTreeInstancesB
                    : ConiferTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    bChilko ? 1040.0f : 920.0f,
                    bChilko ? 1640.0f : 1490.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 8999));
                bCanopyTree = true;
            }
            else if (SpeciesSelector < BroadleafLimit)
            {
                SpeciesMesh = bUseSecondaryMorphology
                    ? TemperateBroadleafTreeMeshB
                    : BroadleafTreeMesh;
                SpeciesInstances = bUseSecondaryMorphology
                    ? TemperateBroadleafTreeInstancesB
                    : BroadleafTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    bChilko ? 720.0f : 880.0f,
                    bChilko ? 1180.0f : 1370.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 9001));
                bCanopyTree = true;
            }
            else if (SpeciesSelector < 18)
            {
                SpeciesMesh = bUseSecondaryMorphology
                    ? TemperateShrubMeshB
                    : ShrubMesh;
                SpeciesInstances = bUseSecondaryMorphology
                    ? TemperateShrubInstancesB
                    : ShrubInstances;
                TargetHeightCm = 205.0f +
                    28.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                SpeciesMesh = bUseSecondaryMorphology
                    ? TemperateUnderstoryMeshB
                    : UnderstoryMesh;
                SpeciesInstances = bUseSecondaryMorphology
                    ? TemperateUnderstoryInstancesB
                    : UnderstoryInstances;
                TargetHeightCm = 92.0f +
                    14.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (bRainforest)
        {
            const int32 SpeciesSelector = FMath::Clamp(
                FMath::FloorToInt(
                    ZambeziVegetationUnitRandom(ClusterIndex, 9041) * 10.0f),
                0,
                9);
            if (SpeciesSelector <= 2)
            {
                SpeciesMesh = BroadleafTreeMesh;
                SpeciesInstances = BroadleafTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    880.0f,
                    1460.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 9059));
                bCanopyTree = true;
            }
            else if (SpeciesSelector <= 4)
            {
                SpeciesMesh = ConiferTreeMesh;
                SpeciesInstances = ConiferTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    1020.0f,
                    1680.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 9067));
                bCanopyTree = true;
            }
            else if (SpeciesSelector <= 7)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = FMath::Lerp(
                    175.0f,
                    390.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 9091));
            }
            else
            {
                TargetHeightCm = FMath::Lerp(
                    68.0f,
                    168.0f,
                    ZambeziVegetationUnitRandom(ClusterIndex, 9103));
            }
        }
        else
        {
            const int32 SpeciesSelector = ClusterIndex % (bPhysicalCorridor ? 20 : 5);
            if (bPhysicalCorridor && SpeciesSelector == 0 &&
                ReviewedPineMeshes.Num() == 3 && ReviewedPineInstances.Num() == 3)
            {
                const int32 PineVariant = (ClusterIndex / 20) % ReviewedPineMeshes.Num();
                SpeciesMesh = ReviewedPineMeshes[PineVariant];
                SpeciesInstances = ReviewedPineInstances[PineVariant];
                TargetHeightCm = 1350.0f + 95.0f * static_cast<float>((ClusterIndex / 20) % 6);
                bCanopyTree = true;
            }
            else if (!bPhysicalCorridor && SpeciesSelector == 0)
            {
                SpeciesMesh = ConiferTreeMesh;
                SpeciesInstances = ConiferTreeInstances;
                TargetHeightCm = 940.0f + 92.0f * static_cast<float>(ClusterIndex % 6);
                bCanopyTree = true;
            }
            else if (SpeciesSelector == (bPhysicalCorridor ? 19 : 4))
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 225.0f + 32.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                SpeciesMesh = BroadleafTreeMesh;
                SpeciesInstances = BroadleafTreeInstances;
                TargetHeightCm = 690.0f + 68.0f * static_cast<float>(ClusterIndex % 6);
                bCanopyTree = true;
            }
        }

        const float MeshHeightCm = FMath::Max(
            1.0f,
            GetLandscapeCandidateEffectiveMeshBounds(SpeciesMesh).GetSize().Z);
        const float UniformScale = TargetHeightCm / MeshHeightCm;
        const FVector SpeciesScale(
            UniformScale * FMath::Lerp(
                bRainforest ? 0.72f : (bOpaqueTemperate ? 0.76f : 0.88f),
                bRainforest ? 1.18f : (bOpaqueTemperate ? 1.16f : 1.04f),
                ZambeziVegetationUnitRandom(ClusterIndex, 9133)),
            UniformScale * FMath::Lerp(
                bRainforest ? 0.74f : (bOpaqueTemperate ? 0.78f : 0.90f),
                bRainforest ? 1.16f : (bOpaqueTemperate ? 1.14f : 1.04f),
                ZambeziVegetationUnitRandom(ClusterIndex, 9151)),
            UniformScale);
        AddGroundedInstance(
            SpeciesInstances,
            SpeciesMesh,
            FVector2D(BestX, BestY),
            GetLandscapeHeight(BestX, BestY),
            FRotator(
                1.4f * FMath::Sin(Phase * 0.73f),
                bOpaqueTemperate
                    ? 360.0f * ZambeziVegetationUnitRandom(ClusterIndex, 9161)
                    : static_cast<float>((ClusterIndex * 137) % 360),
                1.2f * FMath::Cos(Phase * 0.61f)),
            SpeciesScale);
        ++OutResult.DressingFoliageInstanceCount;
        if (bCanopyTree)
        {
            ++OutResult.DressingCanopyTreeInstanceCount;
        }
        else
        {
            ++OutResult.DressingUnderstoryInstanceCount;
        }
    }

    int32 PacuareShorelineRockPlacedCount = 0;
    int32 PacuareShorelineRockRejectedPlacementCount = 0;
    int32 PacuareShorelineGroundCoverPlacedCount = 0;
    int32 PacuareShorelineGroundCoverRejectedPlacementCount = 0;
    int32 PacuareShorelineShrubPlacedCount = 0;
    int32 PacuareShorelineShrubRejectedPlacementCount = 0;
    float PacuareShorelineMinimumCenterlineDistanceCm =
        TNumericLimits<float>::Max();
    float PacuareShorelineMaximumSlopeDegrees = 0.0f;
    if (bPacuare && bPhysicalCorridor &&
        ReviewedRockMeshes.Num() == 6 &&
        PacuareOrganicShorelineRockInstances.Num() == 6)
    {
        // Upper Huacas is only 78 m wide, so the 30 m source context leaves a
        // narrow bank transition visible from the raft. Fill that unresolved
        // band with deterministic, source-grounded moss-rock morphology,
        // short rainforest floor cover, and shrubs. The complete visible
        // river width and a hard centerline clearance remain protected. These
        // HISM layers are non-colliding visual infill; Landscape height and
        // collision plus cooked-field water retain all geography, bathymetry,
        // hydraulic, and raft-force authority.
        const float VisibleRiverHalfWidth =
            FMath::Max(1700.0f, ActiveRiverHalfWidth * 1.32f);
        constexpr int32 BankSideCount = 2;
        const int32 RockInstancesPerSide =
            PacuareOrganicShorelineRockTargetInstanceCount / BankSideCount;
        for (int32 RockIndex = 0;
             RockIndex < PacuareOrganicShorelineRockTargetInstanceCount;
             ++RockIndex)
        {
            const float Side = RockIndex % 2 == 0 ? -1.0f : 1.0f;
            const int32 AlongIndex = RockIndex / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(RockIndex, 11101)) /
                static_cast<float>(RockInstancesPerSide);
            const float BaseLogicalX = FMath::Lerp(-2425.0f, 25325.0f, AlongT) +
                FMath::Lerp(
                    -72.0f,
                    72.0f,
                    ZambeziVegetationUnitRandom(RockIndex, 11107));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + 260.0f));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 28;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX + FMath::Lerp(
                    -90.0f,
                    90.0f,
                    ZambeziVegetationUnitRandom(
                        RockIndex * 31 + CandidateIndex,
                        11113));
                const float AdditionalOffset = FMath::Lerp(
                    45.0f,
                    1650.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            RockIndex * 37 + CandidateIndex,
                            11117),
                        1.72f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (VisibleRiverHalfWidth + AdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float CenterlineDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float HeightAboveWaterCm = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y) -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees >
                        PacuareOrganicShorelineRockSlopeCeilingDegrees ||
                    CenterlineDistanceCm < VisibleRiverHalfWidth + 30.0f ||
                    HeightAboveWaterCm < -5.0f ||
                    HeightAboveWaterCm > 1450.0f)
                {
                    continue;
                }
                const float TargetDryHeightCm = FMath::Lerp(
                    30.0f,
                    430.0f,
                    ZambeziVegetationUnitRandom(RockIndex, 11119));
                const float Score =
                    0.62f * FMath::Abs(
                        HeightAboveWaterCm - TargetDryHeightCm) / 1450.0f +
                    0.25f * AdditionalOffset / 1650.0f +
                    0.13f * SlopeDegrees /
                        PacuareOrganicShorelineRockSlopeCeilingDegrees;
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestPoint = CandidatePoint;
                    BestSlopeDegrees = SlopeDegrees;
                    BestCenterlineDistanceCm = CenterlineDistanceCm;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++PacuareShorelineRockRejectedPlacementCount;
                continue;
            }

            const int32 ScaleClass = RockIndex % 30;
            const float TargetHeightCm = ScaleClass == 0
                ? FMath::Lerp(
                      95.0f,
                      155.0f,
                      ZambeziVegetationUnitRandom(RockIndex, 11123))
                : (ScaleClass < 7
                       ? FMath::Lerp(
                             38.0f,
                             88.0f,
                             ZambeziVegetationUnitRandom(RockIndex, 11129))
                       : FMath::Lerp(
                             12.0f,
                             42.0f,
                             ZambeziVegetationUnitRandom(RockIndex, 11131)));
            const int32 VariantIndex = RockIndex % ReviewedRockMeshes.Num();
            UStaticMesh* RockMesh = ReviewedRockMeshes[VariantIndex];
            UHierarchicalInstancedStaticMeshComponent* RockComponent =
                PacuareOrganicShorelineRockInstances[VariantIndex];
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(RockMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                RockComponent,
                RockMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.08f, 0.0f, 4.0f),
                    360.0f * ZambeziVegetationUnitRandom(RockIndex, 11137),
                    FMath::Lerp(
                        -5.0f,
                        5.0f,
                        ZambeziVegetationUnitRandom(RockIndex, 11141))),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.68f,
                        1.52f,
                        ZambeziVegetationUnitRandom(RockIndex, 11149)),
                    UniformScale * FMath::Lerp(
                        0.70f,
                        1.46f,
                        ZambeziVegetationUnitRandom(RockIndex, 11159)),
                    UniformScale));
            ++PacuareShorelineRockPlacedCount;
            ++OutResult.DressingBoulderInstanceCount;
            PacuareShorelineMinimumCenterlineDistanceCm = FMath::Min(
                PacuareShorelineMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            PacuareShorelineMaximumSlopeDegrees = FMath::Max(
                PacuareShorelineMaximumSlopeDegrees,
                BestSlopeDegrees);
        }

        const int32 EcologyTargetCount =
            PacuareOrganicShorelineGroundCoverTargetInstanceCount +
            PacuareOrganicShorelineShrubTargetInstanceCount;
        for (int32 EcologyIndex = 0;
             EcologyIndex < EcologyTargetCount;
             ++EcologyIndex)
        {
            const bool bShrub = EcologyIndex >=
                PacuareOrganicShorelineGroundCoverTargetInstanceCount;
            const int32 FamilyIndex = bShrub
                ? EcologyIndex -
                    PacuareOrganicShorelineGroundCoverTargetInstanceCount
                : EcologyIndex;
            const int32 FamilyTargetCount = bShrub
                ? PacuareOrganicShorelineShrubTargetInstanceCount
                : PacuareOrganicShorelineGroundCoverTargetInstanceCount;
            const float Side = FamilyIndex % 2 == 0 ? -1.0f : 1.0f;
            const int32 AlongIndex = FamilyIndex / BankSideCount;
            const int32 InstancesPerSide = FamilyTargetCount / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(EcologyIndex, 11201)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX = FMath::Lerp(-2425.0f, 25325.0f, AlongT) +
                FMath::Lerp(
                    -105.0f,
                    105.0f,
                    ZambeziVegetationUnitRandom(EcologyIndex, 11213));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + (bShrub ? 420.0f : 190.0f)));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestScore = TNumericLimits<float>::Max();
            const float SlopeCeilingDegrees = bShrub
                ? PacuareOrganicShorelineShrubSlopeCeilingDegrees
                : PacuareOrganicShorelineGroundCoverSlopeCeilingDegrees;
            for (int32 CandidateIndex = 0; CandidateIndex < 24;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX + FMath::Lerp(
                    -125.0f,
                    125.0f,
                    ZambeziVegetationUnitRandom(
                        EcologyIndex * 29 + CandidateIndex,
                        11227));
                const float AdditionalOffset = FMath::Lerp(
                    bShrub ? 230.0f : 75.0f,
                    bShrub ? 1950.0f : 1800.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            EcologyIndex * 43 + CandidateIndex,
                            11239),
                        bShrub ? 1.18f : 1.48f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (VisibleRiverHalfWidth + AdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float CenterlineDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float HeightAboveWaterCm = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y) -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                const float MinimumDryHeightCm = bShrub ? 35.0f : 12.0f;
                const float MaximumDryHeightCm = bShrub ? 2100.0f : 1650.0f;
                if (SlopeDegrees > SlopeCeilingDegrees ||
                    CenterlineDistanceCm < VisibleRiverHalfWidth +
                        (bShrub ? 180.0f : 55.0f) ||
                    HeightAboveWaterCm < MinimumDryHeightCm ||
                    HeightAboveWaterCm > MaximumDryHeightCm)
                {
                    continue;
                }
                const float TargetDryHeightCm = FMath::Lerp(
                    bShrub ? 210.0f : 75.0f,
                    bShrub ? 980.0f : 620.0f,
                    ZambeziVegetationUnitRandom(EcologyIndex, 11243));
                const float Score =
                    0.57f * FMath::Abs(
                        HeightAboveWaterCm - TargetDryHeightCm) /
                        MaximumDryHeightCm +
                    0.28f * AdditionalOffset /
                        (bShrub ? 1950.0f : 1800.0f) +
                    0.15f * SlopeDegrees / SlopeCeilingDegrees;
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestPoint = CandidatePoint;
                    BestSlopeDegrees = SlopeDegrees;
                    BestCenterlineDistanceCm = CenterlineDistanceCm;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                if (bShrub)
                {
                    ++PacuareShorelineShrubRejectedPlacementCount;
                }
                else
                {
                    ++PacuareShorelineGroundCoverRejectedPlacementCount;
                }
                continue;
            }

            UStaticMesh* EcologyMesh = bShrub ? ShrubMesh : UnderstoryMesh;
            UHierarchicalInstancedStaticMeshComponent* EcologyComponent = bShrub
                ? PacuareOrganicShorelineShrubInstances
                : PacuareOrganicShorelineGroundCoverInstances;
            const float TargetHeightCm = FMath::Lerp(
                bShrub ? 135.0f : 26.0f,
                bShrub ? 360.0f : 118.0f,
                ZambeziVegetationUnitRandom(EcologyIndex, 11251));
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(EcologyMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                EcologyComponent,
                EcologyMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.025f, 0.0f, 1.0f),
                    360.0f * ZambeziVegetationUnitRandom(EcologyIndex, 11257),
                    FMath::Lerp(
                        -1.2f,
                        1.2f,
                        ZambeziVegetationUnitRandom(EcologyIndex, 11261))),
                FVector(
                    UniformScale * FMath::Lerp(
                        bShrub ? 0.76f : 0.66f,
                        bShrub ? 1.28f : 1.46f,
                        ZambeziVegetationUnitRandom(EcologyIndex, 11269)),
                    UniformScale * FMath::Lerp(
                        bShrub ? 0.78f : 0.70f,
                        bShrub ? 1.24f : 1.40f,
                        ZambeziVegetationUnitRandom(EcologyIndex, 11273)),
                    UniformScale));
            if (bShrub)
            {
                ++PacuareShorelineShrubPlacedCount;
            }
            else
            {
                ++PacuareShorelineGroundCoverPlacedCount;
            }
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
            PacuareShorelineMinimumCenterlineDistanceCm = FMath::Min(
                PacuareShorelineMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            PacuareShorelineMaximumSlopeDegrees = FMath::Max(
                PacuareShorelineMaximumSlopeDegrees,
                BestSlopeDegrees);
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             PacuareOrganicShorelineRockInstances)
        {
            Component->MarkRenderStateDirty();
        }
        PacuareOrganicShorelineGroundCoverInstances->MarkRenderStateDirty();
        PacuareOrganicShorelineShrubInstances->MarkRenderStateDirty();
        OutSummary += FString::Printf(
            TEXT("Pacuare organic shoreline V1: %d/%d moss-rock analogs, ")
            TEXT("%d/%d short rainforest-floor patches, and %d/%d shrubs ")
            TEXT("placed across both full-route banks; rejected rock/cover/shrub ")
            TEXT("targets=%d/%d/%d, minimum centerline distance %.1f cm, and ")
            TEXT("maximum slope %.2f degrees. Source-Landscape-grounded, ")
            TEXT("non-colliding procedural gap fill with no lithology, species, ")
            TEXT("ecology, survey, hydraulic, bathymetry, or raft-force authority.\n"),
            PacuareShorelineRockPlacedCount,
            PacuareOrganicShorelineRockTargetInstanceCount,
            PacuareShorelineGroundCoverPlacedCount,
            PacuareOrganicShorelineGroundCoverTargetInstanceCount,
            PacuareShorelineShrubPlacedCount,
            PacuareOrganicShorelineShrubTargetInstanceCount,
            PacuareShorelineRockRejectedPlacementCount,
            PacuareShorelineGroundCoverRejectedPlacementCount,
            PacuareShorelineShrubRejectedPlacementCount,
            PacuareShorelineMinimumCenterlineDistanceCm,
            PacuareShorelineMaximumSlopeDegrees);
    }

    int32 TemperateNearBankPlacedCount = 0;
    int32 TemperateNearBankRejectedPlacementCount = 0;
    float TemperateNearBankMinimumCenterlineDistanceCm =
        TNumericLimits<float>::Max();
    float TemperateNearBankMaximumSlopeDegrees = 0.0f;
    if (bOpaqueTemperate && bPhysicalCorridor)
    {
        // Fill the visibly bare strip between waterline rocks and the wider
        // canopy. Every patch is selected against the source Landscape and
        // full centerline, is dry at the conditioned reference surface, and
        // remains a non-colliding presentation layer.
        const float VisibleRiverHalfWidth = ActiveRiverHalfWidth *
            (bChilko ? 1.20f : 1.18f);
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerSide =
            TemperateNearBankEcologyTargetInstanceCount / BankSideCount;
        const TArray<UStaticMesh*> NearBankMeshes = {
            UnderstoryMesh,
            TemperateUnderstoryMeshB,
            ShrubMesh,
            TemperateShrubMeshB};
        const TArray<UHierarchicalInstancedStaticMeshComponent*>
            NearBankComponents = {
                UnderstoryInstances,
                TemperateUnderstoryInstancesB,
                ShrubInstances,
                TemperateShrubInstancesB};
        for (int32 PatchIndex = 0;
             PatchIndex < TemperateNearBankEcologyTargetInstanceCount;
             ++PatchIndex)
        {
            const int32 SideIndex = PatchIndex % BankSideCount;
            const int32 AlongIndex = PatchIndex / BankSideCount;
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(PatchIndex, 10211)) /
                static_cast<float>(InstancesPerSide);
            const float BaseLogicalX = FMath::Lerp(-2380.0f, 25300.0f, AlongT);
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (VisibleRiverHalfWidth + 620.0f));
            float BestLogicalX = BaseLogicalX;
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestCenterlineDistanceCm = 0.0f;
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 64;
                 ++CandidateIndex)
            {
                const float CandidateLogicalX = BaseLogicalX + FMath::Lerp(
                    -150.0f,
                    150.0f,
                    ZambeziVegetationUnitRandom(
                        PatchIndex * 67 + CandidateIndex,
                        10223));
                const float AdditionalOffset = FMath::Lerp(
                    140.0f,
                    3600.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            PatchIndex * 71 + CandidateIndex,
                            10243),
                        1.55f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (VisibleRiverHalfWidth + AdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float CenterlineDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float HeightAboveWaterCm = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y) -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees > TemperateNearBankEcologySlopeCeilingDegrees ||
                    CenterlineDistanceCm < VisibleRiverHalfWidth + 100.0f ||
                    HeightAboveWaterCm < 15.0f ||
                    HeightAboveWaterCm > 1600.0f)
                {
                    continue;
                }
                const float TargetDryHeightCm = FMath::Lerp(
                    110.0f,
                    620.0f,
                    ZambeziVegetationUnitRandom(PatchIndex, 10247));
                const float Score =
                    0.60f * FMath::Abs(HeightAboveWaterCm - TargetDryHeightCm) /
                        1600.0f +
                    0.25f * AdditionalOffset / 3600.0f +
                    0.15f * SlopeDegrees /
                        TemperateNearBankEcologySlopeCeilingDegrees;
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestPoint = CandidatePoint;
                    BestLogicalX = CandidateLogicalX;
                    BestSlopeDegrees = SlopeDegrees;
                    BestCenterlineDistanceCm = CenterlineDistanceCm;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++TemperateNearBankRejectedPlacementCount;
                continue;
            }

            const bool bShrubPatch = PatchIndex % 6 == 0;
            const bool bSecondaryMorphology =
                ZambeziVegetationUnitRandom(PatchIndex, 10253) > 0.47f;
            const int32 FamilyIndex =
                (bShrubPatch ? 2 : 0) + (bSecondaryMorphology ? 1 : 0);
            UStaticMesh* PatchMesh = NearBankMeshes[FamilyIndex];
            UHierarchicalInstancedStaticMeshComponent* PatchComponent =
                NearBankComponents[FamilyIndex];
            const float TargetHeightCm = bShrubPatch
                ? FMath::Lerp(
                      155.0f,
                      295.0f,
                      ZambeziVegetationUnitRandom(PatchIndex, 10259))
                : FMath::Lerp(
                      58.0f,
                      138.0f,
                      ZambeziVegetationUnitRandom(PatchIndex, 10267));
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(PatchMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                PatchComponent,
                PatchMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.025f, 0.0f, 0.9f),
                    360.0f * ZambeziVegetationUnitRandom(PatchIndex, 10273),
                    0.6f * FMath::Sin(BestLogicalX * 0.001f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.76f,
                        1.28f,
                        ZambeziVegetationUnitRandom(PatchIndex, 10289)),
                    UniformScale * FMath::Lerp(
                        0.78f,
                        1.24f,
                        ZambeziVegetationUnitRandom(PatchIndex, 10291)),
                    UniformScale));
            ++TemperateNearBankPlacedCount;
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
            TemperateNearBankMinimumCenterlineDistanceCm = FMath::Min(
                TemperateNearBankMinimumCenterlineDistanceCm,
                BestCenterlineDistanceCm);
            TemperateNearBankMaximumSlopeDegrees = FMath::Max(
                TemperateNearBankMaximumSlopeDegrees,
                BestSlopeDegrees);
        }
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             NearBankComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimTemperateNearBankEcologyV4"));
                Owner->Tags.AddUnique(TEXT("RaftSimSourceLandscapeGrounded"));
                Owner->Tags.AddUnique(TEXT("RaftSimOutsideProtectedSolverStrip"));
                Owner->Tags.AddUnique(TEXT("RaftSimNoSpeciesOrEcologyAuthority"));
            }
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimTemperateNearBankEcologyV4"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimOutsideProtectedSolverStrip"));
            Component->MarkRenderStateDirty();
        }
        OutSummary += FString::Printf(
            TEXT("%s near-bank ecology V4: %d/%d source-grounded, dry, ")
            TEXT("non-colliding grass/forb/shrub patches; %d targets rejected ")
            TEXT("by full-route clearance, dry-height, or %.1f-degree slope ")
            TEXT("gates; minimum centerline distance %.1f cm and maximum placed ")
            TEXT("slope %.2f degrees. Procedural gap fill with no species, ")
            TEXT("survey, collision, hydraulic, or raft-force authority.\n"),
            *Spec.RiverId,
            TemperateNearBankPlacedCount,
            TemperateNearBankEcologyTargetInstanceCount,
            TemperateNearBankRejectedPlacementCount,
            TemperateNearBankEcologySlopeCeilingDegrees,
            TemperateNearBankMinimumCenterlineDistanceCm,
            TemperateNearBankMaximumSlopeDegrees);
    }
    OutResult.DressingTemperateNearBankTargetInstanceCount =
        bOpaqueTemperate ? TemperateNearBankEcologyTargetInstanceCount : 0;
    OutResult.DressingTemperateNearBankInstanceCount =
        TemperateNearBankPlacedCount;
    OutResult.DressingTemperateNearBankRejectedPlacementCount =
        TemperateNearBankRejectedPlacementCount;
    OutResult.DressingTemperateNearBankMinimumCenterlineDistanceCm =
        TemperateNearBankPlacedCount > 0
            ? TemperateNearBankMinimumCenterlineDistanceCm
            : 0.0f;
    OutResult.DressingTemperateNearBankMaximumSlopeDegrees =
        TemperateNearBankMaximumSlopeDegrees;

    int32 HanceDrylandGroundCoverPlacedCount = 0;
    int32 HanceDrylandGroundCoverRejectedCount = 0;
    int32 HanceDrylandShrubPlacedCount = 0;
    int32 HanceDrylandShrubRejectedCount = 0;
    float HanceDrylandMaximumSlopeDegrees = 0.0f;
    if (bColoradoHance && bPhysicalCorridor)
    {
        // The interpreted C3 channel is complete only to lateral +/-39 m.
        // Populate the procedural outer canyon, never the solver strip, with
        // countable opaque dryland patches. Candidate searches prefer lower
        // slopes and enforce dry-height limits so no instance can bridge the
        // water edge or paste across a cliff face.
        constexpr int32 BankSideCount = 2;
        const int32 GroundCoverPerSide =
            HanceDrylandGroundCoverInstanceCount / BankSideCount;
        for (int32 CoverIndex = 0;
             CoverIndex < HanceDrylandGroundCoverInstanceCount;
             ++CoverIndex)
        {
            const int32 SideIndex = CoverIndex % BankSideCount;
            const int32 AlongIndex = CoverIndex / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(CoverIndex, 10103)) /
                static_cast<float>(GroundCoverPerSide);
            const float BaseLogicalX = FMath::Lerp(-2300.0f, 25200.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float PreferredOffset = FMath::Lerp(
                4300.0f,
                15100.0f,
                FMath::Pow(
                    ZambeziVegetationUnitRandom(CoverIndex, 10107),
                    1.12f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * PreferredOffset);
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 36; ++CandidateIndex)
            {
                const int32 RandomIndex = CoverIndex * 43 + CandidateIndex;
                const float CandidateLogicalX = BaseLogicalX +
                    125.0f * FMath::Sin(
                        CoverIndex * 0.7548777f + CandidateIndex * 1.2207441f);
                const float CandidateOffset = FMath::Lerp(
                    4300.0f,
                    15100.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(RandomIndex, 10111),
                        1.34f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * CandidateOffset);
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees >
                        HanceDrylandGroundCoverSlopeCeilingDegrees ||
                    DryHeightAboveWaterCm < 90.0f ||
                    DryHeightAboveWaterCm > 7600.0f)
                {
                    continue;
                }
                const float Score =
                    0.040f * SlopeDegrees +
                    FMath::Abs(CandidateOffset - PreferredOffset) / 1300.0f +
                    0.11f * ZambeziVegetationUnitRandom(
                        RandomIndex,
                        10129);
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++HanceDrylandGroundCoverRejectedCount;
                continue;
            }

            const int32 VariantIndex = (CoverIndex / BankSideCount) % 2;
            UStaticMesh* GroundCoverMesh = VariantIndex == 0
                ? HanceDrylandGroundCoverMeshA
                : HanceDrylandGroundCoverMeshB;
            UHierarchicalInstancedStaticMeshComponent* GroundCoverInstances =
                VariantIndex == 0
                    ? HanceDrylandGroundCoverInstancesA
                    : HanceDrylandGroundCoverInstancesB;
            const float GroundCoverMeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(
                    GroundCoverMesh).GetSize().Z);
            const float TargetHeightCm = FMath::Lerp(
                32.0f,
                78.0f,
                ZambeziVegetationUnitRandom(CoverIndex, 10133));
            const float UniformScale = TargetHeightCm / GroundCoverMeshHeightCm;
            const float FootprintScale = FMath::Lerp(
                1.05f,
                1.82f,
                ZambeziVegetationUnitRandom(CoverIndex, 10151));
            AddGroundedInstance(
                GroundCoverInstances,
                GroundCoverMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.05f, 0.0f, 1.5f),
                    360.0f * ZambeziVegetationUnitRandom(CoverIndex, 10159),
                    0.8f * FMath::Sin(CoverIndex * 0.91f)),
                FVector(
                    UniformScale * FootprintScale,
                    UniformScale * FootprintScale * FMath::Lerp(
                        0.80f,
                        1.20f,
                        ZambeziVegetationUnitRandom(CoverIndex, 10177)),
                    UniformScale));
            HanceDrylandMaximumSlopeDegrees = FMath::Max(
                HanceDrylandMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++HanceDrylandGroundCoverPlacedCount;
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
        }

        constexpr int32 ShrubSpeciesLaneCount = BankSideCount;
        const int32 ShrubsPerSide =
            HanceDrylandShrubInstanceCount / ShrubSpeciesLaneCount;
        for (int32 ShrubIndex = 0;
             ShrubIndex < HanceDrylandShrubInstanceCount;
             ++ShrubIndex)
        {
            const int32 SideIndex = ShrubIndex % BankSideCount;
            const int32 AlongIndex = ShrubIndex / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(ShrubIndex, 10201)) /
                static_cast<float>(ShrubsPerSide);
            const float BaseLogicalX = FMath::Lerp(-2200.0f, 25100.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float PreferredOffset = FMath::Lerp(
                4700.0f,
                14900.0f,
                FMath::Pow(
                    ZambeziVegetationUnitRandom(ShrubIndex, 10207),
                    0.92f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * PreferredOffset);
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 64; ++CandidateIndex)
            {
                const int32 RandomIndex = ShrubIndex * 71 + CandidateIndex;
                const float CandidateLogicalX = BaseLogicalX +
                    155.0f * FMath::Sin(
                        ShrubIndex * 0.6180339f + CandidateIndex * 1.3247179f);
                const float CandidateOffset = FMath::Lerp(
                    4700.0f,
                    14900.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(RandomIndex, 10211),
                        1.18f));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * CandidateOffset);
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                if (SlopeDegrees > HanceDrylandShrubSlopeCeilingDegrees ||
                    DryHeightAboveWaterCm < 150.0f ||
                    DryHeightAboveWaterCm > 7200.0f)
                {
                    continue;
                }
                const float Score =
                    0.055f * SlopeDegrees +
                    FMath::Abs(CandidateOffset - PreferredOffset) / 1450.0f +
                    0.13f * ZambeziVegetationUnitRandom(
                        RandomIndex,
                        10231);
                if (Score < BestScore)
                {
                    BestScore = Score;
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestScore == TNumericLimits<float>::Max())
            {
                ++HanceDrylandShrubRejectedCount;
                continue;
            }

            const int32 VariantIndex = (ShrubIndex / BankSideCount) % 2;
            UStaticMesh* HanceShrubMesh = VariantIndex == 0
                ? HanceDrylandShrubMeshA
                : HanceDrylandShrubMeshB;
            UHierarchicalInstancedStaticMeshComponent* HanceShrubInstances =
                VariantIndex == 0
                    ? HanceDrylandShrubInstancesA
                    : HanceDrylandShrubInstancesB;
            const float ShrubMeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(
                    HanceShrubMesh).GetSize().Z);
            const float TargetHeightCm = FMath::Lerp(
                78.0f,
                195.0f,
                ZambeziVegetationUnitRandom(ShrubIndex, 10243));
            const float UniformScale = TargetHeightCm / ShrubMeshHeightCm;
            AddGroundedInstance(
                HanceShrubInstances,
                HanceShrubMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.04f, 0.0f, 1.2f),
                    360.0f * ZambeziVegetationUnitRandom(ShrubIndex, 10259),
                    0.9f * FMath::Sin(ShrubIndex * 0.73f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.78f,
                        1.22f,
                        ZambeziVegetationUnitRandom(ShrubIndex, 10267)),
                    UniformScale * FMath::Lerp(
                        0.80f,
                        1.20f,
                        ZambeziVegetationUnitRandom(ShrubIndex, 10271)),
                    UniformScale));
            HanceDrylandMaximumSlopeDegrees = FMath::Max(
                HanceDrylandMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++HanceDrylandShrubPlacedCount;
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
        }
        OutSummary += FString::Printf(
            TEXT("Colorado Hance dryland ecology: %d/%d opaque ground-cover "
                 "patches and %d/%d opaque shrubs grounded outside the protected "
                 "+/-39 m solver strip; %d/%d targets rejected by dry-height or "
                 "%.1f/%.1f-degree slope gates; maximum selected slope %.2f "
                 "degrees. Procedural visual gap fill only.\n"),
            HanceDrylandGroundCoverPlacedCount,
            HanceDrylandGroundCoverInstanceCount,
            HanceDrylandShrubPlacedCount,
            HanceDrylandShrubInstanceCount,
            HanceDrylandGroundCoverRejectedCount,
            HanceDrylandShrubRejectedCount,
            HanceDrylandGroundCoverSlopeCeilingDegrees,
            HanceDrylandShrubSlopeCeilingDegrees,
            HanceDrylandMaximumSlopeDegrees);
    }

    int32 CameraVisibleWoodyPlacedCount = 0;
    int32 CameraVisibleWoodyRejectedSlopeCount = 0;
    float CameraVisibleWoodyMaximumSlopeDegrees = 0.0f;
    if (bZambeziWoodland)
    {
        // The general 30 km dressing distribution is intentionally sparse,
        // but that made the two canonical downstream cameras read as bare DEM
        // terrain.  Add a separate low-profile mosaic on both dry banks in
        // front of those cameras.  The water half-width remains a hard inner
        // exclusion and the best of several candidates is chosen by DEM slope,
        // keeping this render-only layer out of the navigable channel.
        constexpr int32 ViewBandCount = 2;
        constexpr int32 BankSideCount = 2;
        const int32 InstancesPerLongitudinalLane =
            ZambeziEvidenceBankMosaicInstanceCount /
            (ViewBandCount * BankSideCount);
        const float GroundCoverMeshHeightCm = FMath::Max(
            1.0f,
            GetLandscapeCandidateEffectiveMeshBounds(UnderstoryMesh).GetSize().Z);
        for (int32 MosaicIndex = 0;
             MosaicIndex < ZambeziEvidenceBankMosaicInstanceCount;
             ++MosaicIndex)
        {
            const int32 ViewBand = MosaicIndex % ViewBandCount;
            const int32 SideIndex =
                (MosaicIndex / ViewBandCount) % BankSideCount;
            const int32 AlongIndex =
                MosaicIndex / (ViewBandCount * BankSideCount);
            const float AlongJitter =
                ZambeziVegetationUnitRandom(MosaicIndex, 7103);
            const float AlongT =
                (static_cast<float>(AlongIndex) + AlongJitter) /
                static_cast<float>(InstancesPerLongitudinalLane);
            // Physical-camera progress maps to logical X through
            // (X + 2500) / 27900.  Because that lookup spans the full 30 km
            // source centerline, a few hundred logical centimetres represent
            // hundreds of physical route metres.  These windows begin just
            // past each camera target and cover roughly the next 120-600 m of
            // visible bank without placing meshes around the raft.
            const float BaseLogicalX = ViewBand == 0
                ? FMath::Lerp(410.0f, 850.0f, AlongT)
                : FMath::Lerp(5580.0f, 6020.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float OffsetT = FMath::Pow(
                ZambeziVegetationUnitRandom(MosaicIndex, 7121),
                1.65f);
            const float BaseOffset = ActiveRiverHalfWidth +
                FMath::Lerp(280.0f, 4300.0f, OffsetT);
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * BaseOffset);
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 10; ++CandidateIndex)
            {
                const float CandidatePhase =
                    static_cast<float>(MosaicIndex) * 0.7548777f +
                    static_cast<float>(CandidateIndex) * 1.3247179f;
                const float CandidateLogicalX = BaseLogicalX +
                    18.0f * FMath::Sin(CandidatePhase);
                const float CandidateOffset = FMath::Clamp(
                    BaseOffset + 760.0f * FMath::Cos(CandidatePhase * 0.83f),
                    ActiveRiverHalfWidth + 240.0f,
                    ActiveRiverHalfWidth + 4700.0f);
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * CandidateOffset);
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                if (SlopeDegrees < BestSlopeDegrees)
                {
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }

            const float TargetHeightCm = FMath::Lerp(
                54.0f,
                96.0f,
                ZambeziVegetationUnitRandom(MosaicIndex, 7151));
            const float UniformScale = TargetHeightCm / GroundCoverMeshHeightCm;
            const float FootprintScale = FMath::Lerp(
                1.15f,
                1.82f,
                ZambeziVegetationUnitRandom(MosaicIndex, 7177));
            AddGroundedInstance(
                ZambeziBankMosaicInstances,
                UnderstoryMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.08f, 0.0f, 1.8f),
                    360.0f * ZambeziVegetationUnitRandom(MosaicIndex, 7193),
                    1.2f * FMath::Sin(static_cast<float>(MosaicIndex) * 0.91f)),
                FVector(
                    UniformScale * FootprintScale,
                    UniformScale * FootprintScale *
                        FMath::Lerp(
                            0.82f,
                            1.18f,
                            ZambeziVegetationUnitRandom(MosaicIndex, 7207)),
                    UniformScale));
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
        }
        OutSummary += FString::Printf(
            TEXT("Zambezi organic bank mosaic: %d opaque, grounded, non-colliding "
                 "instances in two camera-visible slope-screened bank windows.\n"),
            ZambeziEvidenceBankMosaicInstanceCount);
    }

    if (bZambeziWoodland)
    {
        // Low grass alone still leaves the canonical banks without a readable
        // woody silhouette.  Populate the same two evidence windows with a
        // bounded mix of the existing solid tree and thorn-scrub meshes.  The
        // dedicated components make this visual contract independently
        // countable and keep the sparse full-run distribution unchanged.
        constexpr int32 ViewBandCount = 2;
        constexpr int32 BankSideCount = 2;
        constexpr int32 WoodySpeciesSlotCount = 4;
        const int32 InstancesPerWoodyLane =
            ZambeziEvidenceWoodyInstanceCount /
            (ViewBandCount * BankSideCount * WoodySpeciesSlotCount);
        for (int32 WoodyIndex = 0;
             WoodyIndex < ZambeziEvidenceWoodyInstanceCount;
             ++WoodyIndex)
        {
            const int32 SpeciesSlot = WoodyIndex % WoodySpeciesSlotCount;
            const int32 ViewBand =
                (WoodyIndex / WoodySpeciesSlotCount) % ViewBandCount;
            const int32 SideIndex =
                (WoodyIndex / (WoodySpeciesSlotCount * ViewBandCount)) %
                BankSideCount;
            const int32 AlongIndex = WoodyIndex /
                (WoodySpeciesSlotCount * ViewBandCount * BankSideCount);
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(WoodyIndex, 8101)) /
                static_cast<float>(InstancesPerWoodyLane);
            const float BaseLogicalX = ViewBand == 0
                ? FMath::Lerp(450.0f, 1250.0f, AlongT)
                : FMath::Lerp(5620.0f, 6420.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float MaximumAdditionalOffset = FMath::Max(
                3000.0f,
                FMath::Min(
                    ViewBand == 0 ? 12000.0f : 10000.0f,
                    MaxBankOffset - ActiveRiverHalfWidth));
            const float BaseOffset = ActiveRiverHalfWidth + FMath::Lerp(
                2500.0f,
                MaximumAdditionalOffset,
                FMath::Pow(
                    ZambeziVegetationUnitRandom(WoodyIndex, 8111),
                    1.25f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * BaseOffset);
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 40; ++CandidateIndex)
            {
                const float CandidatePhase =
                    static_cast<float>(WoodyIndex) * 0.6180339f +
                    static_cast<float>(CandidateIndex) * 1.2207441f;
                const float CandidateLogicalX = BaseLogicalX +
                    76.0f * FMath::Sin(CandidatePhase);
                const float CandidateAdditionalOffset = FMath::Lerp(
                    2500.0f,
                    MaximumAdditionalOffset,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            WoodyIndex * 43 + CandidateIndex,
                            8129),
                        1.18f));
                const float CandidateOffset = ActiveRiverHalfWidth +
                    CandidateAdditionalOffset;
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * CandidateOffset);
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float PlacementScore = SlopeDegrees +
                    1.25f * CandidateAdditionalOffset /
                        FMath::Max(1.0f, MaximumAdditionalOffset);
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestSlopeDegrees > ZambeziEvidenceWoodySlopeCeilingDegrees)
            {
                ++CameraVisibleWoodyRejectedSlopeCount;
                continue;
            }

            UStaticMesh* WoodyMesh = ShrubMesh;
            UHierarchicalInstancedStaticMeshComponent* WoodyInstances =
                ZambeziCameraThornScrubInstances;
            bool bWoodyCanopy = false;
            float TargetHeightCm = FMath::Lerp(
                180.0f,
                330.0f,
                ZambeziVegetationUnitRandom(WoodyIndex, 8147));
            if (SpeciesSlot == 0)
            {
                WoodyMesh = BroadleafTreeMesh;
                WoodyInstances = ZambeziCameraRiparianTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    720.0f,
                    1100.0f,
                    ZambeziVegetationUnitRandom(WoodyIndex, 8161));
                bWoodyCanopy = true;
            }
            else if (SpeciesSlot == 1)
            {
                WoodyMesh = ConiferTreeMesh;
                WoodyInstances = ZambeziCameraUmbrellaTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    680.0f,
                    1000.0f,
                    ZambeziVegetationUnitRandom(WoodyIndex, 8167));
                bWoodyCanopy = true;
            }
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(WoodyMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            AddGroundedInstance(
                WoodyInstances,
                WoodyMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.035f, 0.0f, 1.2f),
                    360.0f * ZambeziVegetationUnitRandom(WoodyIndex, 8179),
                    0.8f * FMath::Sin(static_cast<float>(WoodyIndex) * 0.73f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.82f,
                        1.18f,
                        ZambeziVegetationUnitRandom(WoodyIndex, 8191)),
                    UniformScale * FMath::Lerp(
                        0.84f,
                        1.16f,
                        ZambeziVegetationUnitRandom(WoodyIndex, 8209)),
                    UniformScale));
            ++CameraVisibleWoodyPlacedCount;
            CameraVisibleWoodyMaximumSlopeDegrees = FMath::Max(
                CameraVisibleWoodyMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++OutResult.DressingFoliageInstanceCount;
            if (bWoodyCanopy)
            {
                ++OutResult.DressingCanopyTreeInstanceCount;
            }
            else
            {
                ++OutResult.DressingUnderstoryInstanceCount;
            }
        }
        OutSummary += FString::Printf(
            TEXT("Zambezi camera-visible woody ecology: %d/%d opaque, grounded, "
                 "non-colliding tree and thorn-scrub instances in two "
                 "downstream windows; %d candidates rejected above %.1f "
                 "degrees and maximum placed slope %.2f degrees.\n"),
            CameraVisibleWoodyPlacedCount,
            ZambeziEvidenceWoodyInstanceCount,
            CameraVisibleWoodyRejectedSlopeCount,
            ZambeziEvidenceWoodySlopeCeilingDegrees,
            CameraVisibleWoodyMaximumSlopeDegrees);
    }

    int32 RunnableLaunchGroundCoverPlacedCount = 0;
    int32 RunnableLaunchWoodyPlacedCount = 0;
    int32 RunnableLaunchWoodyRejectedSlopeCount = 0;
    float RunnableLaunchWoodyMaximumSlopeDegrees = 0.0f;
    int32 RunnableLaunchGroundCoverPlacedPerStratum[
        ZambeziRunnableLaunchEcologyStratumCount] = {};
    int32 RunnableLaunchWoodyPlacedPerStratum[
        ZambeziRunnableLaunchEcologyStratumCount] = {};
    bool bRunnableLaunchEcologyStrataValidated = !bZambeziWoodland;
    if (bZambeziWoodland)
    {
        // The actual runnable raft starts near station 75 m, far upstream of
        // both documentary capture windows and of the sparse full-reach
        // distribution. Give that gameplay window its own countable bank
        // ecology layer. It remains outside the active river, non-colliding,
        // source-Landscape grounded, and independent of all water/physics.
        constexpr int32 BankSideCount = 2;
        const int32 GroundCoverInstancesPerSide =
            ZambeziRunnableLaunchBankCoverInstanceCount / BankSideCount;
        int32 RunnableLaunchGroundCoverRejectedCount = 0;
        float RunnableLaunchGroundCoverMaximumSlopeDegrees = 0.0f;
        for (int32 CoverIndex = 0;
             CoverIndex < ZambeziRunnableLaunchBankCoverInstanceCount;
             ++CoverIndex)
        {
            const int32 SideIndex = CoverIndex % BankSideCount;
            const int32 AlongIndex = CoverIndex / BankSideCount;
            const int32 ElevationBand = AlongIndex %
                ZambeziRunnableLaunchEcologyElevationBandCount;
            const int32 StratumIndex = SideIndex *
                    ZambeziRunnableLaunchEcologyElevationBandCount +
                ElevationBand;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(CoverIndex, 9101)) /
                static_cast<float>(GroundCoverInstancesPerSide);
            // The launch mosaic begins ahead of the station-75 m camera and
            // continues through the first kilometre. Both morphology families
            // use a 1.2 km HISM cull range, so the far bench remains part of
            // the visible gorge instead of collapsing into one shoreline row.
            const float BaseLogicalX = FMath::Lerp(-2460.0f, -1560.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float BandOffsetMinimumCm = ElevationBand == 0
                ? 1200.0f
                : (ElevationBand == 1 ? 2500.0f : 5000.0f);
            const float BandOffsetMaximumCm = ElevationBand == 0
                ? 24000.0f
                : (ElevationBand == 1 ? 28000.0f : 36000.0f);
            const int32 PatchIndex = AlongIndex / 18;
            const float PatchOffsetT = ZambeziVegetationUnitRandom(
                PatchIndex + SideIndex * 10007 + ElevationBand * 701,
                9109);
            const float IndividualOffsetT = ZambeziVegetationUnitRandom(
                CoverIndex,
                9113);
            const float TargetAdditionalOffset = FMath::Lerp(
                BandOffsetMinimumCm,
                BandOffsetMaximumCm,
                FMath::Pow(
                    0.72f * PatchOffsetT + 0.28f * IndividualOffsetT,
                    1.18f));
            const float TargetSlopeDegrees = FMath::Lerp(
                ElevationBand == 0 ? 3.0f : (ElevationBand == 1 ? 10.0f : 17.0f),
                ElevationBand == 0 ? 18.0f : (ElevationBand == 1 ? 29.0f : 38.0f),
                FMath::Pow(
                    ZambeziVegetationUnitRandom(CoverIndex, 9117),
                    1.25f));
            const float TargetDryHeightAboveWaterCm = FMath::Lerp(
                ZambeziRunnableLaunchGroundCoverTargetMinimumDryHeightCm[
                    ElevationBand],
                ZambeziRunnableLaunchGroundCoverTargetMaximumDryHeightCm[
                    ElevationBand],
                FMath::Pow(
                    ZambeziVegetationUnitRandom(CoverIndex, 9119),
                    1.18f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (ActiveRiverHalfWidth + TargetAdditionalOffset));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 256; ++CandidateIndex)
            {
                const int32 CandidateSeedIndex =
                    CoverIndex * 193 + CandidateIndex;
                const float CandidateLogicalX = BaseLogicalX +
                    FMath::Lerp(
                        -140.0f,
                        140.0f,
                        ZambeziVegetationUnitRandom(
                            CandidateSeedIndex,
                            9121));
                const float CandidateAdditionalOffset = FMath::Lerp(
                    BandOffsetMinimumCm,
                    BandOffsetMaximumCm,
                    ZambeziVegetationUnitRandom(
                        CandidateSeedIndex,
                        9127));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (ActiveRiverHalfWidth + CandidateAdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                const float FullRouteDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                if (SlopeDegrees >
                        ZambeziRunnableLaunchGroundCoverSlopeCeilingDegrees ||
                    DryHeightAboveWaterCm <
                        ZambeziRunnableLaunchGroundCoverBandMinimumDryHeightCm[
                            ElevationBand] ||
                    DryHeightAboveWaterCm >
                        ZambeziRunnableLaunchGroundCoverBandMaximumDryHeightCm[
                            ElevationBand] ||
                    FullRouteDistanceCm < ActiveRiverHalfWidth + 1500.0f)
                {
                    continue;
                }
                // V19 distributes cover across dry benches and moderate
                // slopes. The former absolute-slope score selected the same
                // flattest contour repeatedly and read as a shoreline ribbon.
                const float PlacementScore =
                    0.72f * FMath::Abs(SlopeDegrees - TargetSlopeDegrees) +
                    0.00150f * FMath::Abs(
                        CandidateAdditionalOffset - TargetAdditionalOffset) +
                    0.00100f * FMath::Abs(
                        DryHeightAboveWaterCm -
                        TargetDryHeightAboveWaterCm) +
                    0.00030f * FMath::Abs(
                        CandidateLogicalX - BaseLogicalX);
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++RunnableLaunchGroundCoverRejectedCount;
                continue;
            }

            const float ElevationBandHeightScale = ElevationBand == 0
                ? 0.76f
                : (ElevationBand == 1 ? 1.0f : 1.18f);
            const float TargetHeightCm = ElevationBandHeightScale * FMath::Lerp(
                55.0f,
                155.0f,
                ZambeziVegetationUnitRandom(CoverIndex, 9133));
            UStaticMesh* GroundCoverMesh = UnderstoryMesh;
            UHierarchicalInstancedStaticMeshComponent* GroundCoverInstances =
                ZambeziRunnableLaunchGroundCoverInstances;
            if ((CoverIndex & 1) != 0)
            {
                GroundCoverMesh = ZambeziGroundCoverMeshB;
                GroundCoverInstances = ZambeziRunnableLaunchGroundCoverInstancesB;
            }
            const float SelectedMeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(
                    GroundCoverMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / SelectedMeshHeightCm;
            const float FootprintScale = FMath::Lerp(
                1.20f,
                2.45f,
                ZambeziVegetationUnitRandom(CoverIndex, 9151));
            const int32 InstanceIndex = AddGroundedInstance(
                GroundCoverInstances,
                GroundCoverMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.07f, 0.0f, 1.7f),
                    360.0f * ZambeziVegetationUnitRandom(CoverIndex, 9161),
                    1.1f * FMath::Sin(static_cast<float>(CoverIndex) * 0.91f)),
                FVector(
                    UniformScale * FootprintScale,
                    UniformScale * FootprintScale * FMath::Lerp(
                        0.80f,
                        1.20f,
                        ZambeziVegetationUnitRandom(CoverIndex, 9173)),
                    UniformScale));
            GroundCoverInstances->SetCustomDataValue(
                InstanceIndex,
                0,
                static_cast<float>(StratumIndex),
                false);
            RunnableLaunchGroundCoverMaximumSlopeDegrees = FMath::Max(
                RunnableLaunchGroundCoverMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++RunnableLaunchGroundCoverPlacedCount;
            ++RunnableLaunchGroundCoverPlacedPerStratum[StratumIndex];
            ++OutResult.DressingFoliageInstanceCount;
            ++OutResult.DressingUnderstoryInstanceCount;
        }
        OutSummary += FString::Printf(
            TEXT("Zambezi runnable-launch bank cover: %d/%d opaque, grounded, "
                 "non-colliding, non-shadow-casting instances across both "
                 "banks; %d candidates rejected by full-route distance, dry "
                 "height, or %.1f-degree slope gates; maximum selected slope "
                 "%.2f degrees.\n"),
            RunnableLaunchGroundCoverPlacedCount,
            ZambeziRunnableLaunchBankCoverInstanceCount,
            RunnableLaunchGroundCoverRejectedCount,
            ZambeziRunnableLaunchGroundCoverSlopeCeilingDegrees,
            RunnableLaunchGroundCoverMaximumSlopeDegrees);

        constexpr int32 WoodySpeciesSlotCount = 4;
        const int32 InstancesPerWoodyLane =
            ZambeziRunnableLaunchWoodyInstanceCount /
            (BankSideCount * WoodySpeciesSlotCount);
        for (int32 WoodyIndex = 0;
             WoodyIndex < ZambeziRunnableLaunchWoodyInstanceCount;
             ++WoodyIndex)
        {
            const int32 SpeciesSlot = WoodyIndex % WoodySpeciesSlotCount;
            const int32 SideIndex =
                (WoodyIndex / WoodySpeciesSlotCount) % BankSideCount;
            const int32 AlongIndex = WoodyIndex /
                (WoodySpeciesSlotCount * BankSideCount);
            const int32 ElevationBand = AlongIndex %
                ZambeziRunnableLaunchEcologyElevationBandCount;
            const int32 StratumIndex = SideIndex *
                    ZambeziRunnableLaunchEcologyElevationBandCount +
                ElevationBand;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(WoodyIndex, 9203)) /
                static_cast<float>(InstancesPerWoodyLane);
            // Woody forms begin ahead of the guide camera and fill the first
            // kilometre as a broad dry-bank mosaic instead of a ridge row.
            const float BaseLogicalX = FMath::Lerp(-2360.0f, -1560.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float BandOffsetMinimumCm = ElevationBand == 0
                ? 5000.0f
                : (ElevationBand == 1 ? 5000.0f : 8000.0f);
            const float BandOffsetMaximumCm = ElevationBand == 0
                ? 30000.0f
                : (ElevationBand == 1 ? 30000.0f : 38000.0f);
            const int32 PatchIndex = AlongIndex / 6;
            const float PatchOffsetT = ZambeziVegetationUnitRandom(
                PatchIndex + SideIndex * 12007 +
                    SpeciesSlot * 907 + ElevationBand * 503,
                9207);
            const float TargetAdditionalOffset = FMath::Lerp(
                BandOffsetMinimumCm,
                BandOffsetMaximumCm,
                FMath::Pow(
                    0.68f * PatchOffsetT +
                        0.32f * ZambeziVegetationUnitRandom(
                            WoodyIndex,
                            9211),
                    1.10f));
            const float TargetSlopeDegrees = FMath::Lerp(
                ElevationBand == 0 ? 3.0f : (ElevationBand == 1 ? 9.0f : 15.0f),
                ElevationBand == 0 ? 16.0f : (ElevationBand == 1 ? 25.0f : 32.0f),
                ZambeziVegetationUnitRandom(WoodyIndex, 9217));
            const float TargetDryHeightAboveWaterCm = FMath::Lerp(
                ZambeziRunnableLaunchWoodyTargetMinimumDryHeightCm[
                    ElevationBand],
                ZambeziRunnableLaunchWoodyTargetMaximumDryHeightCm[
                    ElevationBand],
                FMath::Pow(
                    ZambeziVegetationUnitRandom(WoodyIndex, 9219),
                    1.12f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (ActiveRiverHalfWidth + TargetAdditionalOffset));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 400; ++CandidateIndex)
            {
                const int32 CandidateSeedIndex =
                    WoodyIndex * 257 + CandidateIndex;
                const float CandidateLogicalX = BaseLogicalX +
                    FMath::Lerp(
                        -180.0f,
                        180.0f,
                        ZambeziVegetationUnitRandom(
                            CandidateSeedIndex,
                            9221));
                const float CandidateAdditionalOffset = FMath::Lerp(
                    BandOffsetMinimumCm,
                    BandOffsetMaximumCm,
                    ZambeziVegetationUnitRandom(
                        CandidateSeedIndex,
                        9227));
                const FVector2D CandidatePoint = ResolveLogicalRiverPoint(
                    CandidateLogicalX,
                    Side * (ActiveRiverHalfWidth + CandidateAdditionalOffset));
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float GroundZ = GetLandscapeHeight(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm = GroundZ -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                const float FullRouteDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                const float MinimumAdditionalRouteClearanceCm =
                    ElevationBand == 0 ? 3500.0f : 5000.0f;
                if (SlopeDegrees >
                        ZambeziRunnableLaunchWoodySlopeCeilingDegrees ||
                    DryHeightAboveWaterCm <
                        ZambeziRunnableLaunchWoodyBandMinimumDryHeightCm[
                            ElevationBand] ||
                    DryHeightAboveWaterCm >
                        ZambeziRunnableLaunchWoodyBandMaximumDryHeightCm[
                            ElevationBand] ||
                    FullRouteDistanceCm <
                        ActiveRiverHalfWidth +
                            MinimumAdditionalRouteClearanceCm)
                {
                    continue;
                }
                const float PlacementScore =
                    0.78f * FMath::Abs(
                        SlopeDegrees - TargetSlopeDegrees) +
                    0.00165f * FMath::Abs(
                        CandidateAdditionalOffset - TargetAdditionalOffset) +
                    0.00150f * FMath::Abs(
                        DryHeightAboveWaterCm -
                        TargetDryHeightAboveWaterCm) +
                    0.00035f * FMath::Abs(
                        CandidateLogicalX - BaseLogicalX);
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestSlopeDegrees = SlopeDegrees;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++RunnableLaunchWoodyRejectedSlopeCount;
                continue;
            }

            UStaticMesh* WoodyMesh = ShrubMesh;
            UHierarchicalInstancedStaticMeshComponent* WoodyInstances =
                ZambeziRunnableLaunchThornScrubInstances;
            bool bWoodyCanopy = false;
            float TargetHeightCm = FMath::Lerp(
                170.0f,
                390.0f,
                ZambeziVegetationUnitRandom(WoodyIndex, 9241));
            if (SpeciesSlot == 0)
            {
                WoodyMesh = BroadleafTreeMesh;
                WoodyInstances = ZambeziRunnableLaunchRiparianTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    ElevationBand == 0 ? 650.0f :
                        (ElevationBand == 1 ? 560.0f : 440.0f),
                    ElevationBand == 0 ? 1120.0f :
                        (ElevationBand == 1 ? 1020.0f : 880.0f),
                    ZambeziVegetationUnitRandom(WoodyIndex, 9257));
                bWoodyCanopy = true;
            }
            else if (SpeciesSlot == 1)
            {
                WoodyMesh = ConiferTreeMesh;
                WoodyInstances = ZambeziRunnableLaunchUmbrellaTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    ElevationBand == 0 ? 620.0f :
                        (ElevationBand == 1 ? 540.0f : 420.0f),
                    ElevationBand == 0 ? 1080.0f :
                        (ElevationBand == 1 ? 980.0f : 840.0f),
                    ZambeziVegetationUnitRandom(WoodyIndex, 9277));
                bWoodyCanopy = true;
            }
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(WoodyMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            const int32 InstanceIndex = AddGroundedInstance(
                WoodyInstances,
                WoodyMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(BestSlopeDegrees * 0.035f, 0.0f, 1.2f),
                    360.0f * ZambeziVegetationUnitRandom(WoodyIndex, 9283),
                    0.8f * FMath::Sin(static_cast<float>(WoodyIndex) * 0.73f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.82f,
                        1.18f,
                        ZambeziVegetationUnitRandom(WoodyIndex, 9293)),
                    UniformScale * FMath::Lerp(
                        0.84f,
                        1.16f,
                        ZambeziVegetationUnitRandom(WoodyIndex, 9311)),
                    UniformScale));
            WoodyInstances->SetCustomDataValue(
                InstanceIndex,
                0,
                static_cast<float>(StratumIndex),
                false);
            ++RunnableLaunchWoodyPlacedCount;
            ++RunnableLaunchWoodyPlacedPerStratum[StratumIndex];
            RunnableLaunchWoodyMaximumSlopeDegrees = FMath::Max(
                RunnableLaunchWoodyMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++OutResult.DressingFoliageInstanceCount;
            if (bWoodyCanopy)
            {
                ++OutResult.DressingCanopyTreeInstanceCount;
            }
            else
            {
                ++OutResult.DressingUnderstoryInstanceCount;
            }
        }

        // The centerline bends sharply at the launch. A purely cross-section
        // relative distribution leaves the outside wall behind the camera and
        // concentrates the remaining canopy on a distant skyline. Supplement
        // the two-bank strata with a deterministic, source-grounded patch
        // mosaic sampled through the actual launch view cone. This layer is
        // still dry-bank-only, non-colliding, and presentation-only; it cannot
        // change terrain, water, navigation, collision, or raft forces.
        int32 RunnableLaunchCameraFaceWoodyPlacedCount = 0;
        int32 RunnableLaunchCameraFaceWoodyRejectedCount = 0;
        const FVector2D LaunchViewCenter =
            ResolveLogicalRiverPoint(-2425.0f, 0.0f);
        const FVector2D LaunchViewAhead =
            ResolveLogicalRiverPoint(-2150.0f, 0.0f);
        const FVector2D LaunchViewForward =
            (LaunchViewAhead - LaunchViewCenter).GetSafeNormal();
        const FVector2D LaunchViewRight(
            -LaunchViewForward.Y,
            LaunchViewForward.X);
        for (int32 FaceIndex = 0;
             FaceIndex < ZambeziRunnableLaunchCameraFaceWoodyInstanceCount;
             ++FaceIndex)
        {
            const int32 SpeciesSlot = FaceIndex % WoodySpeciesSlotCount;
            const int32 ElevationBand =
                (FaceIndex / WoodySpeciesSlotCount) %
                ZambeziRunnableLaunchEcologyElevationBandCount;
            const int32 HorizontalLane = FaceIndex % 12;
            const int32 ForwardLane = (FaceIndex / 12) % 5;
            const int32 PatchIndex = FaceIndex / 20;
            const float TargetViewRatio = FMath::Lerp(
                -0.80f,
                0.80f,
                (static_cast<float>(HorizontalLane) +
                    0.22f + 0.56f * ZambeziVegetationUnitRandom(
                        PatchIndex,
                        9341)) /
                    12.0f);
            const float TargetForwardCm = FMath::Lerp(
                9000.0f,
                52000.0f,
                (static_cast<float>(ForwardLane) +
                    0.18f + 0.64f * ZambeziVegetationUnitRandom(
                        PatchIndex,
                        9343)) /
                    5.0f);
            const float TargetSlopeDegrees = FMath::Lerp(
                ElevationBand == 0 ? 4.0f :
                    (ElevationBand == 1 ? 10.0f : 16.0f),
                ElevationBand == 0 ? 17.0f :
                    (ElevationBand == 1 ? 26.0f : 33.0f),
                ZambeziVegetationUnitRandom(FaceIndex, 9349));
            const float TargetDryHeightAboveWaterCm = FMath::Lerp(
                ZambeziRunnableLaunchWoodyTargetMinimumDryHeightCm[
                    ElevationBand],
                ZambeziRunnableLaunchWoodyTargetMaximumDryHeightCm[
                    ElevationBand],
                ZambeziVegetationUnitRandom(FaceIndex, 9353));
            FVector2D BestPoint = LaunchViewCenter;
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestDryHeightAboveWaterCm = 0.0f;
            float BestViewRatio = 0.0f;
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0;
                 CandidateIndex < 320;
                 ++CandidateIndex)
            {
                const int32 CandidateSeedIndex =
                    FaceIndex * 353 + CandidateIndex;
                const float CandidateForwardCm = FMath::Clamp(
                    TargetForwardCm + FMath::Lerp(
                        -7000.0f,
                        7000.0f,
                        ZambeziVegetationUnitRandom(
                            CandidateSeedIndex,
                            9361)),
                    8000.0f,
                    56000.0f);
                const float CandidateViewRatio = FMath::Clamp(
                    TargetViewRatio + FMath::Lerp(
                        -0.20f,
                        0.20f,
                        ZambeziVegetationUnitRandom(
                            CandidateSeedIndex,
                            9371)),
                    -0.90f,
                    0.90f);
                const FVector2D CandidatePoint =
                    LaunchViewCenter +
                    LaunchViewForward * CandidateForwardCm +
                    LaunchViewRight *
                        (CandidateViewRatio * CandidateForwardCm);
                const float CandidateLogicalX =
                    -2425.0f + CandidateForwardCm / 100.0f;
                const float SlopeDegrees = GetLandscapeSlopeDegrees(
                    CandidatePoint.X,
                    CandidatePoint.Y);
                const float DryHeightAboveWaterCm =
                    GetLandscapeHeight(CandidatePoint.X, CandidatePoint.Y) -
                    GetConditionedWaterWorldZ(CandidateLogicalX);
                const float FullRouteDistanceCm =
                    GetMinimumCenterlineDistanceCm(CandidatePoint);
                if (SlopeDegrees >
                        ZambeziRunnableLaunchWoodySlopeCeilingDegrees ||
                    DryHeightAboveWaterCm <
                        ZambeziRunnableLaunchWoodyBandMinimumDryHeightCm[0] ||
                    DryHeightAboveWaterCm >
                        ZambeziRunnableLaunchWoodyBandMaximumDryHeightCm[2] ||
                    FullRouteDistanceCm <
                        ActiveRiverHalfWidth + 3500.0f)
                {
                    continue;
                }
                const float PlacementScore =
                    0.70f * FMath::Abs(
                        SlopeDegrees - TargetSlopeDegrees) +
                    18.0f * FMath::Abs(
                        CandidateViewRatio - TargetViewRatio) +
                    0.00040f * FMath::Abs(
                        CandidateForwardCm - TargetForwardCm) +
                    0.00150f * FMath::Abs(
                        DryHeightAboveWaterCm -
                            TargetDryHeightAboveWaterCm);
                if (PlacementScore < BestPlacementScore)
                {
                    BestPlacementScore = PlacementScore;
                    BestSlopeDegrees = SlopeDegrees;
                    BestDryHeightAboveWaterCm = DryHeightAboveWaterCm;
                    BestViewRatio = CandidateViewRatio;
                    BestPoint = CandidatePoint;
                }
            }
            if (BestPlacementScore == TNumericLimits<float>::Max())
            {
                ++RunnableLaunchCameraFaceWoodyRejectedCount;
                continue;
            }

            const int32 SideIndex = BestViewRatio < 0.0f ? 0 : 1;
            const int32 ActualElevationBand =
                BestDryHeightAboveWaterCm < 1800.0f
                ? 0
                : (BestDryHeightAboveWaterCm < 5000.0f ? 1 : 2);
            const int32 StratumIndex = SideIndex *
                    ZambeziRunnableLaunchEcologyElevationBandCount +
                ActualElevationBand;
            UStaticMesh* WoodyMesh = ShrubMesh;
            UHierarchicalInstancedStaticMeshComponent* WoodyInstances =
                ZambeziRunnableLaunchThornScrubInstances;
            bool bWoodyCanopy = false;
            float TargetHeightCm = FMath::Lerp(
                240.0f,
                480.0f,
                ZambeziVegetationUnitRandom(FaceIndex, 9383));
            if (SpeciesSlot == 0)
            {
                WoodyMesh = BroadleafTreeMesh;
                WoodyInstances = ZambeziRunnableLaunchRiparianTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    760.0f,
                    1320.0f,
                    ZambeziVegetationUnitRandom(FaceIndex, 9391));
                bWoodyCanopy = true;
            }
            else if (SpeciesSlot == 1)
            {
                WoodyMesh = ConiferTreeMesh;
                WoodyInstances = ZambeziRunnableLaunchUmbrellaTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    720.0f,
                    1240.0f,
                    ZambeziVegetationUnitRandom(FaceIndex, 9397));
                bWoodyCanopy = true;
            }
            const float MeshHeightCm = FMath::Max(
                1.0f,
                GetLandscapeCandidateEffectiveMeshBounds(
                    WoodyMesh).GetSize().Z);
            const float UniformScale = TargetHeightCm / MeshHeightCm;
            const int32 InstanceIndex = AddGroundedInstance(
                WoodyInstances,
                WoodyMesh,
                BestPoint,
                GetLandscapeHeight(BestPoint.X, BestPoint.Y),
                FRotator(
                    FMath::Clamp(
                        BestSlopeDegrees * 0.03f,
                        0.0f,
                        1.1f),
                    360.0f * ZambeziVegetationUnitRandom(
                        FaceIndex,
                        9403),
                    0.7f * FMath::Sin(
                        static_cast<float>(FaceIndex) * 0.67f)),
                FVector(
                    UniformScale * FMath::Lerp(
                        0.80f,
                        1.22f,
                        ZambeziVegetationUnitRandom(FaceIndex, 9413)),
                    UniformScale * FMath::Lerp(
                        0.82f,
                        1.18f,
                        ZambeziVegetationUnitRandom(FaceIndex, 9419)),
                    UniformScale));
            WoodyInstances->SetCustomDataValue(
                InstanceIndex,
                0,
                static_cast<float>(StratumIndex),
                false);
            ++RunnableLaunchWoodyPlacedCount;
            ++RunnableLaunchCameraFaceWoodyPlacedCount;
            ++RunnableLaunchWoodyPlacedPerStratum[StratumIndex];
            RunnableLaunchWoodyMaximumSlopeDegrees = FMath::Max(
                RunnableLaunchWoodyMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++OutResult.DressingFoliageInstanceCount;
            if (bWoodyCanopy)
            {
                ++OutResult.DressingCanopyTreeInstanceCount;
            }
            else
            {
                ++OutResult.DressingUnderstoryInstanceCount;
            }
        }
        OutSummary += FString::Printf(
            TEXT("Zambezi V19 launch-camera face mosaic: %d/%d opaque, "
                 "source-grounded, non-colliding woody instances; %d "
                 "candidates rejected by view-cone, route-clearance, dry-"
                 "height, or %.1f-degree slope gates.\n"),
            RunnableLaunchCameraFaceWoodyPlacedCount,
            ZambeziRunnableLaunchCameraFaceWoodyInstanceCount,
            RunnableLaunchCameraFaceWoodyRejectedCount,
            ZambeziRunnableLaunchWoodySlopeCeilingDegrees);
        OutSummary += FString::Printf(
            TEXT("Zambezi runnable-launch woody ecology: %d/%d opaque, grounded, "
                 "non-colliding instances; %d candidates rejected by full-route "
                 "distance, dry height, or %.1f-degree slope gates and maximum "
                 "placed slope %.2f degrees.\n"),
            RunnableLaunchWoodyPlacedCount,
            ZambeziRunnableLaunchWoodyInstanceCount +
                ZambeziRunnableLaunchCameraFaceWoodyInstanceCount,
            RunnableLaunchWoodyRejectedSlopeCount,
            ZambeziRunnableLaunchWoodySlopeCeilingDegrees,
            RunnableLaunchWoodyMaximumSlopeDegrees);

        bRunnableLaunchEcologyStrataValidated = true;
        for (int32 StratumIndex = 0;
             StratumIndex < ZambeziRunnableLaunchEcologyStratumCount;
             ++StratumIndex)
        {
            bRunnableLaunchEcologyStrataValidated &=
                RunnableLaunchGroundCoverPlacedPerStratum[StratumIndex] >=
                    ZambeziRunnableLaunchMinimumGroundCoverPerStratum &&
                RunnableLaunchWoodyPlacedPerStratum[StratumIndex] >=
                    ZambeziRunnableLaunchMinimumWoodyPerStratum;
        }
        bRunnableLaunchEcologyStrataValidated &=
            RunnableLaunchCameraFaceWoodyPlacedCount >=
                ZambeziRunnableLaunchMinimumCameraFaceWoodyInstanceCount;
        OutSummary += FString::Printf(
            TEXT("Zambezi V19 ecology strata (left low/mid/high, right "
                 "low/mid/high): cover=[%d,%d,%d,%d,%d,%d] woody="
                 "[%d,%d,%d,%d,%d,%d], minimums=%d/%d validated=%d.\n"),
            RunnableLaunchGroundCoverPlacedPerStratum[0],
            RunnableLaunchGroundCoverPlacedPerStratum[1],
            RunnableLaunchGroundCoverPlacedPerStratum[2],
            RunnableLaunchGroundCoverPlacedPerStratum[3],
            RunnableLaunchGroundCoverPlacedPerStratum[4],
            RunnableLaunchGroundCoverPlacedPerStratum[5],
            RunnableLaunchWoodyPlacedPerStratum[0],
            RunnableLaunchWoodyPlacedPerStratum[1],
            RunnableLaunchWoodyPlacedPerStratum[2],
            RunnableLaunchWoodyPlacedPerStratum[3],
            RunnableLaunchWoodyPlacedPerStratum[4],
            RunnableLaunchWoodyPlacedPerStratum[5],
            ZambeziRunnableLaunchMinimumGroundCoverPerStratum,
            ZambeziRunnableLaunchMinimumWoodyPerStratum,
            bRunnableLaunchEcologyStrataValidated);
    }

    const int32 ExpectedFoliageInstanceCount = FoliageClusterCount +
        PacuareShorelineGroundCoverPlacedCount +
        PacuareShorelineShrubPlacedCount +
        TemperateNearBankPlacedCount +
        ChilkoShorelineGroundCoverPlacedCount +
        HanceDrylandGroundCoverPlacedCount +
        HanceDrylandShrubPlacedCount +
        (bZambeziWoodland
             ? ZambeziEvidenceBankMosaicInstanceCount +
                 CameraVisibleWoodyPlacedCount +
                 RunnableLaunchGroundCoverPlacedCount +
                 RunnableLaunchWoodyPlacedCount
             : 0);
    OutResult.bDressingValidated =
        OutResult.DressingBoulderInstanceCount ==
            BoulderCount + TemperateWaterlinePlacedCount +
                ChilkoShorelineGravelPlacedCount +
                PacuareShorelineRockPlacedCount +
                RunnableLaunchTalusPlacedCount &&
        OutResult.DressingFoliageInstanceCount == ExpectedFoliageInstanceCount &&
        (!bPacuare ||
         PacuareShorelineRockPlacedCount >=
             PacuareOrganicShorelineRockMinimumInstanceCount) &&
        (!bPacuare ||
         PacuareShorelineGroundCoverPlacedCount >=
             PacuareOrganicShorelineGroundCoverMinimumInstanceCount) &&
        (!bPacuare ||
         PacuareShorelineShrubPlacedCount >=
             PacuareOrganicShorelineShrubMinimumInstanceCount) &&
        (!bOpaqueTemperate ||
         TemperateWaterlinePlacedCount >=
             TemperateWaterlineStructureMinimumInstanceCount) &&
        (!bOpaqueTemperate ||
         TemperateNearBankPlacedCount >=
             TemperateNearBankEcologyMinimumInstanceCount) &&
        (!bChilko ||
         ChilkoShorelineGravelPlacedCount >=
             ChilkoOrganicShorelineGravelMinimumInstanceCount) &&
        (!bChilko ||
         ChilkoShorelineGroundCoverPlacedCount >=
             ChilkoOrganicShorelineGroundCoverMinimumInstanceCount) &&
        ((Spec.bDesertCanyon && !bZambeziWoodland) ||
         OutResult.DressingCanopyTreeInstanceCount > 0) &&
        OutResult.DressingUnderstoryInstanceCount > 0 &&
        (!bColoradoHance ||
         HanceDrylandGroundCoverPlacedCount >=
             HanceDrylandMinimumGroundCoverInstanceCount) &&
        (!bColoradoHance ||
         HanceDrylandShrubPlacedCount >=
             HanceDrylandMinimumShrubInstanceCount) &&
        (!bZambeziWoodland ||
         RunnableLaunchGroundCoverPlacedCount >=
             ZambeziRunnableLaunchMinimumBankCoverInstanceCount) &&
        (!bZambeziWoodland ||
         RunnableLaunchWoodyPlacedCount >=
             ZambeziRunnableLaunchMinimumWoodyInstanceCount) &&
        bRunnableLaunchEcologyStrataValidated &&
        (!bZambeziWoodland || RunnableLaunchTalusPlacedCount >= 300) &&
        OutResult.bDressingFoliageMaterialsValidated;
    OutSummary += FString::Printf(
        TEXT("Landscape biome dressing for %s: %d %s, %d foliage instances (%d canopy, %d understory), %d %s foliage slots; Nanite mesh flags boulder=%d broadleaf=%d conifer=%d understory=%d.\n"),
        *Spec.RiverId,
        OutResult.DressingBoulderInstanceCount,
        ReviewedRockMeshes.Num() == 6
            ? TEXT("rights-reviewed six-variant Nanite rock instances")
            : TEXT("dense irregular procedural boulders"),
        OutResult.DressingFoliageInstanceCount,
        OutResult.DressingCanopyTreeInstanceCount,
        OutResult.DressingUnderstoryInstanceCount,
        OutResult.DressingFoliageMaterialBoundSlotCount,
        bUsesOpaqueVolumetricVegetation
            ? TEXT("project-owned opaque volumetric")
            : TEXT("river-specific PVE"),
        OutResult.bDressingBoulderMeshNaniteEnabled,
        OutResult.bDressingBroadleafMeshNaniteEnabled,
        OutResult.bDressingConiferMeshNaniteEnabled,
        OutResult.bDressingUnderstoryMeshNaniteEnabled);
    return OutResult.bDressingValidated;
}
} // namespace RaftSimEditorEnvironment
