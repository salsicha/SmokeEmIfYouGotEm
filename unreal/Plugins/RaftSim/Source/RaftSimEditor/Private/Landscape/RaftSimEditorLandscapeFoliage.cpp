#include "Environment/RaftSimEditorEnvironmentInternal.h"

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
constexpr int32 ZambeziEvidenceBankMosaicInstanceCount = 1200;
constexpr int32 ZambeziEvidenceWoodyInstanceCount = 240;
constexpr float ZambeziEvidenceWoodySlopeCeilingDegrees = 24.0f;
constexpr int32 ZambeziRunnableLaunchBankCoverInstanceCount = 1800;
constexpr float ZambeziRunnableLaunchGroundCoverSlopeCeilingDegrees = 32.0f;
constexpr int32 ZambeziRunnableLaunchWoodyInstanceCount = 192;
constexpr float ZambeziRunnableLaunchWoodySlopeCeilingDegrees = 24.0f;

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
    constexpr int32 RingCount = 8;
    constexpr int32 SegmentCount = 16;
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

UMaterial* CreateOpaqueVegetationMaterial(
    const TCHAR* MaterialPath,
    const TCHAR* ProfileLabel,
    float ShadowFillStrength,
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
    UMaterialExpressionMultiply* ShadowFill = Add(
        NewObject<UMaterialExpressionMultiply>(Material));
    ShadowFill->A.Expression = VertexColor;
    ShadowFill->B.Expression = ShadowFloor;

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, VertexColor);
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
        OutSummary);
}

UStaticMesh* CreateZambeziOpaqueVegetationMesh(
    UWorld* World,
    const TCHAR* AssetToken,
    EZambeziVegetationForm Form,
    int32 Seed,
    UMaterialInterface* Material,
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
    const FLinearColor BarkBase(0.175f, 0.125f, 0.070f, 1.0f);
    const FLinearColor BarkTip(0.215f, 0.155f, 0.082f, 1.0f);
    const FLinearColor LeafGreen = Form == EZambeziVegetationForm::UmbrellaTree
        ? FLinearColor(0.085f, 0.135f, 0.034f, 1.0f)
        : FLinearColor(0.072f, 0.122f, 0.030f, 1.0f);
    const FLinearColor ScrubGreen(0.082f, 0.132f, 0.038f, 1.0f);
    const FLinearColor DryGrass(0.29f, 0.225f, 0.070f, 1.0f);

    if (Form == EZambeziVegetationForm::SavannaGroundCover)
    {
        AppendZambeziOpaqueLobe(
            FVector(0.0f, 0.0f, 10.0f),
            FVector(46.0f, 38.0f, 15.0f),
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
        constexpr int32 BladeCount = 54;
        for (int32 BladeIndex = 0; BladeIndex < BladeCount; ++BladeIndex)
        {
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1201);
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Radius = FMath::Lerp(
                12.0f,
                240.0f,
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1213));
            const float Height = FMath::Lerp(
                24.0f,
                82.0f,
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1231));
            const float Lean = FMath::Lerp(
                5.0f,
                28.0f,
                ZambeziVegetationUnitRandom(BladeIndex + Seed, 1249));
            const FVector Start = Direction * Radius;
            const FVector End = Start + Direction * Lean + FVector::UpVector * Height;
            const float Dryness = ZambeziVegetationUnitRandom(
                BladeIndex + Seed, 1277);
            const FLinearColor BladeColor = FMath::Lerp(
                FLinearColor(0.19f, 0.30f, 0.075f, 1.0f),
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
        constexpr int32 LowForbCount = 11;
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
                FLinearColor(0.12f, 0.20f, 0.045f, 1.0f),
                DryGrass,
                ZambeziVegetationUnitRandom(RandomIndex, 1319));
            AppendZambeziOpaqueLobe(
                FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * Radius +
                    FVector::UpVector * (9.0f * Scale),
                FVector(21.0f, 17.0f, 11.0f) * Scale,
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
        constexpr int32 StemCount = 13;
        for (int32 StemIndex = 0; StemIndex < StemCount; ++StemIndex)
        {
            const float Angle = UE_TWO_PI *
                static_cast<float>(StemIndex) / static_cast<float>(StemCount) +
                Seed * 0.17f;
            const FVector Direction(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Length = 115.0f + 52.0f *
                ZambeziVegetationUnitRandom(StemIndex + Seed, 1601);
            const FVector Start = Direction * 9.0f;
            const FVector Mid = Direction * Length * 0.48f +
                FVector::UpVector * (75.0f + 18.0f * (StemIndex % 3));
            const FVector End = Direction * Length +
                FVector::UpVector * (125.0f + 32.0f * (StemIndex % 4));
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
                FVector(64.0f, 52.0f, 46.0f) *
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
            TEXT("Zambezi vegetation geometry contract failed for %s.\n"),
            AssetToken);
        return nullptr;
    }
    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* TemporaryActor = AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_Zambezi_%s_BuildSource"), AssetToken),
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
    const FString PackagePath = FString(ZambeziVegetationMeshRoot) + AssetToken;
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
            TEXT("Prepared Zambezi %s opaque volumetric vegetation: "
                 "vertices=%d triangles=%d Nanite=%d collision=false.\n"),
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
    UStaticMesh*& OutGroundCover,
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
        OutSummary);
    OutUmbrellaTree = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_UmbrellaTree_B_OpaqueV1"),
        EZambeziVegetationForm::UmbrellaTree,
        2713,
        OutMaterial,
        OutSummary);
    OutThornScrub = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_ThornScrub_A_OpaqueV1"),
        EZambeziVegetationForm::ThornScrub,
        3907,
        OutMaterial,
        OutSummary);
    OutGroundCover = CreateZambeziOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Zambezi_SavannaGroundCover_A_OpaqueV1"),
        EZambeziVegetationForm::SavannaGroundCover,
        4933,
        OutMaterial,
        OutSummary);
    const bool bComplete =
        OutRiparianTree && OutUmbrellaTree && OutThornScrub && OutGroundCover;
    if (!bComplete)
    {
        OutSummary += TEXT(
            "Failed to build the complete Zambezi opaque vegetation family.\n");
    }
    return bComplete;
}

UStaticMesh* CreateTemperateOpaqueVegetationMesh(
    UWorld* World,
    const TCHAR* AssetToken,
    ETemperateVegetationForm Form,
    int32 Seed,
    UMaterialInterface* Material,
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
    const FLinearColor BarkBase(0.060f, 0.040f, 0.025f, 1.0f);
    const FLinearColor BarkTip(0.082f, 0.058f, 0.035f, 1.0f);
    const FLinearColor BroadleafGreen(0.025f, 0.075f, 0.038f, 1.0f);
    const FLinearColor ConiferGreen(0.018f, 0.055f, 0.035f, 1.0f);
    const FLinearColor ShrubGreen(0.035f, 0.090f, 0.042f, 1.0f);
    const FLinearColor GroundGreen(0.040f, 0.100f, 0.045f, 1.0f);

    if (Form == ETemperateVegetationForm::GroundCover)
    {
        AppendZambeziOpaqueLobe(
            FVector(0.0f, 0.0f, 8.0f),
            FVector(74.0f, 60.0f, 16.0f),
            Seed,
            ScalePreviewColor(GroundGreen, 0.66f),
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
        constexpr int32 BladeCount = 58;
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
                FLinearColor(0.105f, 0.245f, 0.085f, 1.0f),
                FLinearColor(0.19f, 0.25f, 0.095f, 1.0f),
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
        constexpr int32 ForbCount = 18;
        for (int32 ForbIndex = 0; ForbIndex < ForbCount; ++ForbIndex)
        {
            const float Angle = UE_TWO_PI *
                ZambeziVegetationUnitRandom(Seed + ForbIndex, 5209);
            const float Radius = FMath::Lerp(
                28.0f,
                205.0f,
                ZambeziVegetationUnitRandom(Seed + ForbIndex, 5227));
            AppendZambeziOpaqueLobe(
                FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f) * Radius +
                    FVector::UpVector * 16.0f,
                FVector(28.0f, 20.0f, 13.0f),
                Seed + ForbIndex * 31,
                ScalePreviewColor(
                    GroundGreen,
                    0.76f + 0.28f * ZambeziVegetationUnitRandom(
                        Seed + ForbIndex, 5231)),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else if (Form == ETemperateVegetationForm::RiparianShrub)
    {
        constexpr int32 StemCount = 16;
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
            AppendZambeziOpaqueLobe(
                End,
                FVector(66.0f, 54.0f, 48.0f) *
                    (0.84f + 0.10f * static_cast<float>(StemIndex % 4)),
                Seed + StemIndex * 19,
                ShrubGreen,
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
    }
    else if (Form == ETemperateVegetationForm::ConiferTree)
    {
        constexpr float TreeHeightCm = 930.0f;
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
        constexpr int32 BranchesPerTier = 7;
        for (int32 TierIndex = 0; TierIndex < TierCount; ++TierIndex)
        {
            const float TierT = static_cast<float>(TierIndex) /
                static_cast<float>(TierCount - 1);
            const float TierZ = FMath::Lerp(170.0f, 845.0f, TierT);
            const float TierRadius = FMath::Lerp(300.0f, 62.0f, TierT);
            for (int32 BranchIndex = 0;
                 BranchIndex < BranchesPerTier;
                 ++BranchIndex)
            {
                const float Angle = UE_TWO_PI *
                        static_cast<float>(BranchIndex) /
                        static_cast<float>(BranchesPerTier) +
                    TierIndex * 0.43f + Seed * 0.017f;
                const FVector Direction(
                    FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
                const FVector Start(0.0f, 0.0f, TierZ);
                const FVector End = Direction * TierRadius +
                    FVector::UpVector * (TierZ + FMath::Lerp(12.0f, 55.0f, TierT));
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
                AppendZambeziOpaqueLobe(
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
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
                AppendZambeziOpaqueLobe(
                    End,
                    FVector(
                        FMath::Lerp(92.0f, 42.0f, TierT),
                        FMath::Lerp(60.0f, 32.0f, TierT),
                        FMath::Lerp(38.0f, 24.0f, TierT)),
                    Seed + TierIndex * 103 + BranchIndex * 17,
                    ConiferGreen,
                    Vertices,
                    Triangles,
                    Normals,
                    Uvs,
                    Colors);
            }
        }
        AppendZambeziOpaqueLobe(
            FVector(0.0f, 0.0f, 900.0f),
            FVector(54.0f, 48.0f, 92.0f),
            Seed + 991,
            ConiferGreen,
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Colors);
    }
    else
    {
        const FVector LowerTrunkEnd(-12.0f, 10.0f, 410.0f);
        const FVector UpperTrunkEnd(18.0f, -14.0f, 650.0f);
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
        constexpr int32 BranchCount = 13;
        for (int32 BranchIndex = 0; BranchIndex < BranchCount; ++BranchIndex)
        {
            const float Angle = FMath::Fmod(
                137.50776f * BranchIndex + Seed * 19.0f,
                360.0f) * PI / 180.0f;
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const float Radius = 225.0f + 35.0f * (BranchIndex % 5);
            const float StartZ = 390.0f + 27.0f * (BranchIndex % 6);
            const float EndZ = 605.0f + 46.0f * (BranchIndex % 5);
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
            AppendZambeziOpaqueLobe(
                End + FVector::UpVector * 26.0f,
                FVector(158.0f, 132.0f, 112.0f) *
                    (0.86f + 0.08f * static_cast<float>(BranchIndex % 4)),
                Seed + BranchIndex * 29,
                ScalePreviewColor(
                    BroadleafGreen,
                    0.84f + 0.14f * ZambeziVegetationUnitRandom(
                        Seed + BranchIndex, 5903)),
                Vertices,
                Triangles,
                Normals,
                Uvs,
                Colors);
        }
        constexpr int32 CrownFillCount = 6;
        for (int32 FillIndex = 0; FillIndex < CrownFillCount; ++FillIndex)
        {
            const float Angle = UE_TWO_PI * static_cast<float>(FillIndex) /
                static_cast<float>(CrownFillCount) + Seed * 0.05f;
            AppendZambeziOpaqueLobe(
                FVector(
                    FMath::Cos(Angle) * 94.0f,
                    FMath::Sin(Angle) * 94.0f,
                    700.0f + 28.0f * (FillIndex % 2)),
                FVector(172.0f, 145.0f, 126.0f),
                Seed + 700 + FillIndex * 37,
                BroadleafGreen,
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
    const FString PackagePath = FString(TemperateVegetationMeshRoot) + AssetToken;
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
            TEXT("Prepared temperate %s opaque volumetric vegetation: "
                 "vertices=%d triangles=%d Nanite=%d collision=false.\n"),
            AssetToken,
            Mesh->GetNumVertices(0),
            Mesh->GetNumTriangles(0),
            Mesh->IsNaniteEnabled());
    }
    return Mesh;
}

bool CreateTemperateOpaqueVegetationAssets(
    UWorld* World,
    UStaticMesh*& OutBroadleafTree,
    UStaticMesh*& OutConiferTree,
    UStaticMesh*& OutShrub,
    UStaticMesh*& OutGroundCover,
    UMaterialInterface*& OutMaterial,
    FString& OutSummary)
{
    OutMaterial = CreateOpaqueVegetationMaterial(
        TemperateVegetationMaterialPath,
        TEXT("temperate-river"),
        0.06f,
        OutSummary);
    if (!OutMaterial)
    {
        return false;
    }
    OutBroadleafTree = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_BroadleafTree_A_OpaqueV1"),
        ETemperateVegetationForm::BroadleafTree,
        6101,
        OutMaterial,
        OutSummary);
    OutConiferTree = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_ConiferTree_A_OpaqueV1"),
        ETemperateVegetationForm::ConiferTree,
        6203,
        OutMaterial,
        OutSummary);
    OutShrub = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_RiparianShrub_A_OpaqueV1"),
        ETemperateVegetationForm::RiparianShrub,
        6301,
        OutMaterial,
        OutSummary);
    OutGroundCover = CreateTemperateOpaqueVegetationMesh(
        World,
        TEXT("SM_RaftSim_Temperate_GroundCover_A_OpaqueV1"),
        ETemperateVegetationForm::GroundCover,
        6421,
        OutMaterial,
        OutSummary);
    const bool bComplete =
        OutBroadleafTree && OutConiferTree && OutShrub && OutGroundCover;
    if (!bComplete)
    {
        OutSummary += TEXT(
            "Failed to build the complete opaque temperate vegetation family.\n");
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
    const bool bFutaleufu = Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
    const bool bChilko =
        Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
    const bool bOpaqueTemperate = bFutaleufu || bChilko;
    const bool bUsesOpaqueVolumetricVegetation = bZambezi || bOpaqueTemperate;
    TArray<UStaticMesh*> ReviewedRockMeshes;
    if (bSouthFork || bZambezi || bFutaleufu)
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
    UMaterialInterface* ZambeziOpaqueVegetationMaterial = nullptr;
    UMaterialInterface* TemperateOpaqueVegetationMaterial = nullptr;
    if (bZambezi)
    {
        if (!CreateZambeziOpaqueVegetationAssets(
                World,
                BroadleafTreeMesh,
                ConiferTreeMesh,
                ShrubMesh,
                UnderstoryMesh,
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
    else if (bOpaqueTemperate)
    {
        if (!CreateTemperateOpaqueVegetationAssets(
                World,
                BroadleafTreeMesh,
                ConiferTreeMesh,
                ShrubMesh,
                UnderstoryMesh,
                TemperateOpaqueVegetationMaterial,
                OutSummary))
        {
            return false;
        }
        OutResult.DressingBroadleafAssetPath = BroadleafTreeMesh->GetPathName();
        OutResult.DressingConiferAssetPath = ConiferTreeMesh->GetPathName();
        OutResult.DressingShrubAssetPath = ShrubMesh->GetPathName();
        OutResult.DressingUnderstoryAssetPath = UnderstoryMesh->GetPathName();
        OutResult.DressingFoliageMaterialAssetPath =
            TemperateOpaqueVegetationMaterial->GetPathName();
        OutResult.bDressingUsesOpaqueVolumetricVegetation = true;
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
    for (UStaticMesh* Mesh : {BroadleafTreeMesh, ConiferTreeMesh, ShrubMesh, UnderstoryMesh})
    {
        OutResult.DressingAssetCount += Mesh ? 1 : 0;
        OutResult.DressingConvertedStaticMeshCount += Mesh ? 1 : 0;
    }
    OutResult.DressingAssetCount += ReviewedRockMeshes.Num() + ReviewedPineMeshes.Num();
    OutResult.bDressingAssetsLoaded = bUsesOpaqueVolumetricVegetation
        ? OutResult.DressingSourceSkeletalMeshCount == 0 &&
            OutResult.DressingConvertedStaticMeshCount == 4 &&
            ValidateZambeziOpaqueVegetationMaterial(
                bZambezi
                    ? ZambeziOpaqueVegetationMaterial
                    : TemperateOpaqueVegetationMaterial)
        : OutResult.DressingSourceSkeletalMeshCount == 4 &&
            OutResult.DressingConvertedStaticMeshCount == 4;
    if (!OutResult.bDressingAssetsLoaded)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s loaded %d source and %d/4 converted species meshes.\n"),
            *Candidate.PreviewSpec.RiverId,
            OutResult.DressingSourceSkeletalMeshCount,
            OutResult.DressingConvertedStaticMeshCount);
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
    else if (bOpaqueTemperate)
    {
        OutSummary += FString::Printf(
            TEXT("%s replaces repeated alpha-card PVE banks with four project-owned "
                 "opaque volumetric temperate forms. The deterministic conifer, "
                 "broadleaf, shrub, and ground-cover family is procedural infill, "
                 "not exact-species or photoreal approval.\n"),
            *Candidate.PreviewSpec.RiverId);
    }

    OutResult.bDressingBoulderMeshNaniteEnabled =
        ReviewedRockMeshes.Num() == 6 &&
        Algo::AllOf(ReviewedRockMeshes, [](UStaticMesh* Mesh)
        {
            return Mesh && Mesh->IsNaniteEnabled();
        });
    OutResult.bDressingBroadleafMeshNaniteEnabled =
        BroadleafTreeMesh->IsNaniteEnabled() && ShrubMesh->IsNaniteEnabled();
    OutResult.bDressingConiferMeshNaniteEnabled =
        ConiferTreeMesh->IsNaniteEnabled() &&
        (ReviewedPineMeshes.IsEmpty() ||
         Algo::AllOf(ReviewedPineMeshes, [](UStaticMesh* Mesh)
         {
             return Mesh && Mesh->IsNaniteEnabled();
         }));
    OutResult.bDressingUnderstoryMeshNaniteEnabled = UnderstoryMesh->IsNaniteEnabled();

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
        : TemperateOpaqueVegetationMaterial;
    UMaterialInterface* BroadleafFoliageMaterial = OpaqueVegetationMaterial;
    UMaterialInterface* ConiferFoliageMaterial = OpaqueVegetationMaterial;
    UMaterialInterface* UnderstoryFoliageMaterial = OpaqueVegetationMaterial;
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
    OutResult.DressingFoliageMaterialAssetCount = bUsesOpaqueVolumetricVegetation
        ? (OpaqueVegetationMaterial ? 1 : 0)
        : (BroadleafFoliageMaterial ? 1 : 0) +
            (ConiferFoliageMaterial ? 1 : 0) +
            (UnderstoryFoliageMaterial ? 1 : 0);
    const int32 ExpectedFoliageMaterialAssetCount =
        bUsesOpaqueVolumetricVegetation ? 1 : 3;
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
                : bOpaqueTemperate
                ? FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_TemperateOpaqueGroundCover_%s"),
                      *Candidate.PreviewSpec.RiverId)
                : FString::Printf(
                      TEXT("RaftSim_LandscapeCandidate_PveWholeUnderstory_%s"),
                      *Candidate.PreviewSpec.RiverId),
            true,
            bUsesOpaqueVolumetricVegetation ? OpaqueVegetationMaterial : nullptr);
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
        (bZambezi && !ZambeziBankMosaicInstances) ||
        (bZambezi &&
         (!ZambeziCameraRiparianTreeInstances ||
          !ZambeziCameraUmbrellaTreeInstances ||
          !ZambeziCameraThornScrubInstances ||
          !ZambeziRunnableLaunchGroundCoverInstances ||
          !ZambeziRunnableLaunchRiparianTreeInstances ||
          !ZambeziRunnableLaunchUmbrellaTreeInstances ||
          !ZambeziRunnableLaunchThornScrubInstances)) ||
        Algo::AnyOf(ReviewedRockInstances, [](UHierarchicalInstancedStaticMeshComponent* Component)
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
    if (bOpaqueTemperate)
    {
        const TArray<UHierarchicalInstancedStaticMeshComponent*> Components = {
            BroadleafTreeInstances,
            ConiferTreeInstances,
            ShrubInstances,
            UnderstoryInstances};
        for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimOpaqueVolumetricVegetation"));
                Owner->Tags.AddUnique(TEXT("RaftSimProceduralVegetationFallback"));
                Owner->Tags.AddUnique(TEXT("RaftSimSlopeScreenedPlacement"));
                Owner->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
                Owner->Tags.AddUnique(
                    bChilko ? TEXT("RaftSimChilkoLavaCanyonRun")
                            : TEXT("RaftSimFutaleufuTerminatorRun"));
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
            }
        }
        UnderstoryInstances->SetCastShadow(false);
        if (AActor* GroundOwner = UnderstoryInstances->GetOwner())
        {
            GroundOwner->Tags.AddUnique(TEXT("RaftSimOrganicBankGroundCover"));
            GroundOwner->Tags.AddUnique(
                TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
        }
        UnderstoryInstances->ComponentTags.AddUnique(
            TEXT("RaftSimOrganicBankGroundCover"));
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
                ZambeziRunnableLaunchRiparianTreeInstances,
                ZambeziRunnableLaunchUmbrellaTreeInstances,
                ZambeziRunnableLaunchThornScrubInstances};
        for (UHierarchicalInstancedStaticMeshComponent* Component :
             RunnableLaunchComponents)
        {
            if (AActor* Owner = Component ? Component->GetOwner() : nullptr)
            {
                Owner->Tags.AddUnique(TEXT("RaftSimRunnableLaunchBankEcologyV1"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchBankEcologyV1"));
            }
        }
        if (AActor* Owner = ZambeziRunnableLaunchGroundCoverInstances
                ? ZambeziRunnableLaunchGroundCoverInstances->GetOwner()
                : nullptr)
        {
            Owner->Tags.AddUnique(TEXT("RaftSimRunnableLaunchBankCover"));
            Owner->Tags.AddUnique(TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
        }
        ZambeziRunnableLaunchGroundCoverInstances->ComponentTags.AddUnique(
            TEXT("RaftSimRunnableLaunchBankCover"));
        ZambeziRunnableLaunchGroundCoverInstances->ComponentTags.AddUnique(
            TEXT("RaftSimGroundCoverSelfShadowSuppressed"));
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
                Owner->Tags.AddUnique(TEXT("RaftSimWoodySlopeCeiling24Degrees"));
                Owner->Tags.AddUnique(
                    TEXT("RaftSimRunnableLaunchWoodyShadowSuppressed"));
            }
            if (Component)
            {
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchWoodyEcology"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimWoodySlopeCeiling24Degrees"));
                Component->ComponentTags.AddUnique(
                    TEXT("RaftSimRunnableLaunchWoodyShadowSuppressed"));
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
            OutResult.DressingFoliageMaterialBoundSlotCount == 12 &&
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
    else if (bOpaqueTemperate)
    {
        const TArray<UHierarchicalInstancedStaticMeshComponent*> Components = {
            BroadleafTreeInstances,
            ConiferTreeInstances,
            ShrubInstances,
            UnderstoryInstances};
        const TArray<UStaticMesh*> Meshes = {
            BroadleafTreeMesh,
            ConiferTreeMesh,
            ShrubMesh,
            UnderstoryMesh};
        OutResult.DressingFoliageMaterialBoundSlotCount = 0;
        for (UStaticMesh* Mesh : Meshes)
        {
            OutResult.DressingFoliageMaterialBoundSlotCount +=
                Mesh && Mesh->GetStaticMaterials().Num() == 1 &&
                    Mesh->GetMaterial(0) == TemperateOpaqueVegetationMaterial
                ? 1
                : 0;
        }
        OutResult.DressingNativeFoliageMaterialFallbackSlotCount = 0;
        OutResult.bDressingFoliageMaterialsValidated =
            OutResult.DressingFoliageMaterialBoundSlotCount == 4 &&
            ValidateZambeziOpaqueVegetationMaterial(
                TemperateOpaqueVegetationMaterial) &&
            Algo::AllOf(
                Components,
                [TemperateOpaqueVegetationMaterial](
                    UHierarchicalInstancedStaticMeshComponent* Component)
                {
                    return Component &&
                        Component->GetCollisionEnabled() ==
                            ECollisionEnabled::NoCollision &&
                        Component->GetMaterial(0) ==
                            TemperateOpaqueVegetationMaterial;
                });
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
        Component->AddInstance(
            FTransform(
                Rotation,
                FVector(GroundLocation.X, GroundLocation.Y, GroundedPivotZ),
                Scale),
            true);
    };

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

    const int32 FoliageClusterCount = bPhysicalCorridor
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
                (bZambeziWoodland || bOpaqueTemperate)
                ? GetLandscapeSlopeDegrees(CandidateWorldX, CandidateWorldY)
                : 0.0f;
            const float SteepSlopePenalty = bZambeziWoodland
                ? 3.2f * SmoothPreviewStep(10.0f, 24.0f, SlopeDegrees)
                : bOpaqueTemperate
                ? 2.5f * SmoothPreviewStep(18.0f, 34.0f, SlopeDegrees)
                : 0.0f;
            const float Score = VegetationT *
                    (bRainforest ? 1.85f : (bZambeziWoodland ? 1.22f : (Spec.bDesertCanyon ? 0.58f : 1.34f))) -
                WaterT * 1.18f +
                ((bZambeziWoodland || bOpaqueTemperate)
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
            const int32 SpeciesSelector = ClusterIndex % 20;
            const int32 ConiferLimit = bChilko ? 12 : 8;
            const int32 BroadleafLimit = bChilko ? 15 : 15;
            if (SpeciesSelector < ConiferLimit)
            {
                SpeciesMesh = ConiferTreeMesh;
                SpeciesInstances = ConiferTreeInstances;
                TargetHeightCm = (bChilko ? 1120.0f : 980.0f) +
                    82.0f * static_cast<float>(ClusterIndex % 7);
                bCanopyTree = true;
            }
            else if (SpeciesSelector < BroadleafLimit)
            {
                SpeciesMesh = BroadleafTreeMesh;
                SpeciesInstances = BroadleafTreeInstances;
                TargetHeightCm = (bChilko ? 760.0f : 940.0f) +
                    74.0f * static_cast<float>(ClusterIndex % 6);
                bCanopyTree = true;
            }
            else if (SpeciesSelector < 18)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 205.0f +
                    28.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                SpeciesMesh = UnderstoryMesh;
                SpeciesInstances = UnderstoryInstances;
                TargetHeightCm = 92.0f +
                    14.0f * static_cast<float>(ClusterIndex % 5);
            }
        }
        else if (bRainforest)
        {
            const int32 SpeciesSelector = ClusterIndex % 5;
            if (SpeciesSelector <= 2)
            {
                SpeciesMesh = BroadleafTreeMesh;
                SpeciesInstances = BroadleafTreeInstances;
                TargetHeightCm = 980.0f + 105.0f * static_cast<float>(ClusterIndex % 7);
                bCanopyTree = true;
            }
            else if (SpeciesSelector == 3)
            {
                SpeciesMesh = ShrubMesh;
                SpeciesInstances = ShrubInstances;
                TargetHeightCm = 260.0f + 38.0f * static_cast<float>(ClusterIndex % 6);
            }
            else
            {
                TargetHeightCm = 145.0f + 22.0f * static_cast<float>(ClusterIndex % 6);
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
            UniformScale * (0.88f + 0.04f * static_cast<float>(ClusterIndex % 5)),
            UniformScale * (0.90f + 0.035f * static_cast<float>((ClusterIndex + 2) % 5)),
            UniformScale);
        AddGroundedInstance(
            SpeciesInstances,
            SpeciesMesh,
            FVector2D(BestX, BestY),
            GetLandscapeHeight(BestX, BestY),
            FRotator(
                1.4f * FMath::Sin(Phase * 0.73f),
                static_cast<float>((ClusterIndex * 137) % 360),
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
        const float GroundCoverMeshHeightCm = FMath::Max(
            1.0f,
            GetLandscapeCandidateEffectiveMeshBounds(UnderstoryMesh).GetSize().Z);
        int32 RunnableLaunchGroundCoverRejectedCount = 0;
        float RunnableLaunchGroundCoverMaximumSlopeDegrees = 0.0f;
        for (int32 CoverIndex = 0;
             CoverIndex < ZambeziRunnableLaunchBankCoverInstanceCount;
             ++CoverIndex)
        {
            const int32 SideIndex = CoverIndex % BankSideCount;
            const int32 AlongIndex = CoverIndex / BankSideCount;
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(CoverIndex, 9101)) /
                static_cast<float>(GroundCoverInstancesPerSide);
            // Logical X -2360..-1720 corresponds to approximately 151-842 m
            // down the source corridor. Keeping the layer ahead of the
            // station-75 m launch avoids camera-clipped plants while retaining
            // it inside the 600 m HISM cull range.
            const float BaseLogicalX = FMath::Lerp(-2360.0f, -1720.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            const float BaseOffset = ActiveRiverHalfWidth + FMath::Lerp(
                2500.0f,
                16000.0f,
                FMath::Pow(
                    ZambeziVegetationUnitRandom(CoverIndex, 9113),
                    1.35f));
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * BaseOffset);
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 96; ++CandidateIndex)
            {
                const float CandidatePhase =
                    static_cast<float>(CoverIndex) * 0.7548777f +
                    static_cast<float>(CandidateIndex) * 1.2207441f;
                const float CandidateLogicalX = BaseLogicalX +
                    20.0f * FMath::Sin(CandidatePhase);
                const float CandidateAdditionalOffset = FMath::Lerp(
                    1800.0f,
                    18000.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            CoverIndex * 101 + CandidateIndex,
                            9127),
                        1.22f));
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
                    DryHeightAboveWaterCm < 80.0f ||
                    DryHeightAboveWaterCm > 10000.0f ||
                    FullRouteDistanceCm < ActiveRiverHalfWidth + 1500.0f)
                {
                    continue;
                }
                const float PlacementScore = SlopeDegrees +
                    0.12f * CandidateAdditionalOffset / 18000.0f;
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

            const float TargetHeightCm = FMath::Lerp(
                72.0f,
                150.0f,
                ZambeziVegetationUnitRandom(CoverIndex, 9133));
            const float UniformScale = TargetHeightCm / GroundCoverMeshHeightCm;
            const float FootprintScale = FMath::Lerp(
                1.35f,
                2.40f,
                ZambeziVegetationUnitRandom(CoverIndex, 9151));
            AddGroundedInstance(
                ZambeziRunnableLaunchGroundCoverInstances,
                UnderstoryMesh,
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
            RunnableLaunchGroundCoverMaximumSlopeDegrees = FMath::Max(
                RunnableLaunchGroundCoverMaximumSlopeDegrees,
                BestSlopeDegrees);
            ++RunnableLaunchGroundCoverPlacedCount;
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
            const float AlongT =
                (static_cast<float>(AlongIndex) +
                 ZambeziVegetationUnitRandom(WoodyIndex, 9203)) /
                static_cast<float>(InstancesPerWoodyLane);
            // Woody crowns begin roughly 215 m downstream so no trunk or crown
            // can clip the guide camera at the launch itself.
            const float BaseLogicalX = FMath::Lerp(-2300.0f, -1700.0f, AlongT);
            const float Side = SideIndex == 0 ? -1.0f : 1.0f;
            FVector2D BestPoint = ResolveLogicalRiverPoint(
                BaseLogicalX,
                Side * (ActiveRiverHalfWidth + 2600.0f));
            float BestSlopeDegrees = TNumericLimits<float>::Max();
            float BestPlacementScore = TNumericLimits<float>::Max();
            for (int32 CandidateIndex = 0; CandidateIndex < 160; ++CandidateIndex)
            {
                const float CandidatePhase =
                    static_cast<float>(WoodyIndex) * 0.6180339f +
                    static_cast<float>(CandidateIndex) * 1.2207441f;
                const float CandidateLogicalX = BaseLogicalX +
                    58.0f * FMath::Sin(CandidatePhase);
                const float CandidateAdditionalOffset = FMath::Lerp(
                    6000.0f,
                    18000.0f,
                    FMath::Pow(
                        ZambeziVegetationUnitRandom(
                            WoodyIndex * 59 + CandidateIndex,
                            9221),
                        1.18f));
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
                        ZambeziRunnableLaunchWoodySlopeCeilingDegrees ||
                    DryHeightAboveWaterCm < 300.0f ||
                    DryHeightAboveWaterCm > 10000.0f ||
                    FullRouteDistanceCm < ActiveRiverHalfWidth + 5000.0f)
                {
                    continue;
                }
                const float PlacementScore = SlopeDegrees +
                    0.60f * CandidateAdditionalOffset / 18000.0f;
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
                220.0f,
                420.0f,
                ZambeziVegetationUnitRandom(WoodyIndex, 9241));
            if (SpeciesSlot == 0)
            {
                WoodyMesh = BroadleafTreeMesh;
                WoodyInstances = ZambeziRunnableLaunchRiparianTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    820.0f,
                    1380.0f,
                    ZambeziVegetationUnitRandom(WoodyIndex, 9257));
                bWoodyCanopy = true;
            }
            else if (SpeciesSlot == 1)
            {
                WoodyMesh = ConiferTreeMesh;
                WoodyInstances = ZambeziRunnableLaunchUmbrellaTreeInstances;
                TargetHeightCm = FMath::Lerp(
                    780.0f,
                    1320.0f,
                    ZambeziVegetationUnitRandom(WoodyIndex, 9277));
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
            ++RunnableLaunchWoodyPlacedCount;
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
            TEXT("Zambezi runnable-launch woody ecology: %d/%d opaque, grounded, "
                 "non-colliding instances; %d candidates rejected by full-route "
                 "distance, dry height, or %.1f-degree slope gates and maximum "
                 "placed slope %.2f degrees.\n"),
            RunnableLaunchWoodyPlacedCount,
            ZambeziRunnableLaunchWoodyInstanceCount,
            RunnableLaunchWoodyRejectedSlopeCount,
            ZambeziRunnableLaunchWoodySlopeCeilingDegrees,
            RunnableLaunchWoodyMaximumSlopeDegrees);
    }

    const int32 ExpectedFoliageInstanceCount = FoliageClusterCount +
        (bZambeziWoodland
             ? ZambeziEvidenceBankMosaicInstanceCount +
                 CameraVisibleWoodyPlacedCount +
                 RunnableLaunchGroundCoverPlacedCount +
                 RunnableLaunchWoodyPlacedCount
             : 0);
    OutResult.bDressingValidated =
        OutResult.DressingBoulderInstanceCount == BoulderCount &&
        OutResult.DressingFoliageInstanceCount == ExpectedFoliageInstanceCount &&
        ((Spec.bDesertCanyon && !bZambeziWoodland) ||
         OutResult.DressingCanopyTreeInstanceCount > 0) &&
        OutResult.DressingUnderstoryInstanceCount > 0 &&
        (!bZambeziWoodland ||
         RunnableLaunchGroundCoverPlacedCount >= 900) &&
        (!bZambeziWoodland || RunnableLaunchWoodyPlacedCount >= 96) &&
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
