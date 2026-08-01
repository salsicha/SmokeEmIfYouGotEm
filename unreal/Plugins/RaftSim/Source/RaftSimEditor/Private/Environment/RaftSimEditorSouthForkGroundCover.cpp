#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/Material.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "UObject/SavePackage.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr TCHAR GroundCoverMaterialPath[] = TEXT(
    "/Game/RaftSim/Environment/SouthForkFullReach/Dressing/Materials/"
    "M_RaftSim_SouthForkGroundCover");
constexpr TCHAR GroundCoverMeshPath[] = TEXT(
    "/Game/RaftSim/Environment/SouthForkFullReach/Dressing/Meshes/"
    "SM_RaftSim_SouthForkGrassTuft_A");

float GroundCoverUnitRandom(int32 CoordinateIndex, int32 Column, int32 Salt)
{
    uint32 Hash = static_cast<uint32>(CoordinateIndex) * 0xD1B54A35u;
    Hash ^= static_cast<uint32>(Column) * 0x94D049BBu;
    Hash ^= static_cast<uint32>(Salt) * 0x369DEA0Fu;
    Hash ^= Hash >> 16;
    Hash *= 0x7FEB352Du;
    Hash ^= Hash >> 15;
    Hash *= 0x846CA68Bu;
    Hash ^= Hash >> 16;
    return static_cast<float>(Hash & 0x00FFFFFFu) / 16777215.0f;
}

UMaterial* CreateGroundCoverMaterial(FString& OutSummary)
{
    const FString AssetName = FPackageName::GetLongPackageAssetName(
        GroundCoverMaterialPath);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"), GroundCoverMaterialPath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material
        ? Material->GetOutermost()
        : CreatePackage(GroundCoverMaterialPath);
    if (!Package)
    {
        return nullptr;
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, *AssetName,
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
    Material->SetShadingModel(MSM_TwoSidedFoliage);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = true;
    Material->DitheredLODTransition = true;

    auto Add = [Material](auto* Expression)
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionVertexColor* VertexColor = Add(
        NewObject<UMaterialExpressionVertexColor>(Material));
    UMaterialExpressionConstant3Vector* Transmission = Add(
        NewObject<UMaterialExpressionConstant3Vector>(Material));
    Transmission->Constant = FLinearColor(0.045f, 0.075f, 0.018f, 1.0f);
    UMaterialExpressionConstant* Roughness = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    Roughness->R = 0.90f;
    UMaterialExpressionConstant* Specular = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    Specular->R = 0.06f;
    UMaterialExpressionConstant* AmbientOcclusion = Add(
        NewObject<UMaterialExpressionConstant>(Material));
    AmbientOcclusion->R = 0.86f;

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, VertexColor);
    ConnectPreviewMaterialColorInput(
        EditorOnlyData->SubsurfaceColor, Transmission);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    ConnectPreviewMaterialScalarInput(
        EditorOnlyData->AmbientOcclusion, AmbientOcclusion);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes))
    {
        OutSummary += TEXT(
            "Failed to enable instancing on the South Fork ground-cover material.\n");
        return nullptr;
    }
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
            "Generated South Fork ground-cover material shader gate failed.\n");
        return nullptr;
    }
    Material->MarkPackageDirty();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        GroundCoverMaterialPath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        return nullptr;
    }
    return Material;
}

UStaticMesh* CreateGrassTuftMesh(
    UWorld* World,
    UMaterialInterface* Material,
    FString& OutSummary)
{
    if (!World || !Material)
    {
        return nullptr;
    }
    // One instance represents a small, irregular patch rather than a radial
    // star of oversized blades.  The former 24-blade, 1.24 m diameter tuft
    // disappeared at guide-eye distance and left the four-metre DEM surface
    // visually bare between isolated yellow clumps.  Use many narrower blades
    // over a wider footprint, then mix in low litter/forb leaves that remain
    // close to the terrain.  This is presentation-only geometry; the source
    // density raster still decides where patches may exist.
    constexpr int32 BladeCount = 52;
    constexpr int32 LowLeafCount = 10;
    constexpr int32 ElementCount = BladeCount + LowLeafCount;
    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    TArray<FProcMeshTangent> Tangents;
    Vertices.Reserve(ElementCount * 5);
    Triangles.Reserve(ElementCount * 9);
    Uvs.Reserve(ElementCount * 5);
    Colors.Reserve(ElementCount * 5);
    Tangents.Reserve(ElementCount * 5);

    for (int32 Blade = 0; Blade < BladeCount; ++Blade)
    {
        const float Angle = UE_TWO_PI *
            GroundCoverUnitRandom(Blade, 17, 503);
        const FVector Forward(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector Right(-Forward.Y, Forward.X, 0.0f);
        const float RadiusCm = FMath::Lerp(
            6.0f, 116.0f, GroundCoverUnitRandom(Blade, 19, 509));
        const float WidthCm = FMath::Lerp(
            1.4f, 4.8f, GroundCoverUnitRandom(Blade, 23, 521));
        const float HeightCm = FMath::Lerp(
            28.0f, 104.0f, GroundCoverUnitRandom(Blade, 29, 523));
        const float LeanCm = FMath::Lerp(
            -18.0f, 36.0f, GroundCoverUnitRandom(Blade, 31, 541));
        const FVector Center = Forward * RadiusCm;
        const FVector BaseLeft = Center - Right * WidthCm * 0.5f;
        const FVector BaseRight = Center + Right * WidthCm * 0.5f;
        const FVector MiddleCenter =
            Center + Forward * LeanCm * 0.38f + FVector(0.0f, 0.0f, HeightCm * 0.56f);
        const FVector MiddleLeft = MiddleCenter - Right * WidthCm * 0.32f;
        const FVector MiddleRight = MiddleCenter + Right * WidthCm * 0.32f;
        const FVector Tip =
            Center + Forward * LeanCm + FVector(0.0f, 0.0f, HeightCm);
        const int32 VertexBase = Vertices.Num();
        Vertices.Append({BaseLeft, BaseRight, MiddleLeft, MiddleRight, Tip});
        Triangles.Append({
            VertexBase, VertexBase + 1, VertexBase + 2,
            VertexBase + 1, VertexBase + 3, VertexBase + 2,
            VertexBase + 2, VertexBase + 3, VertexBase + 4});
        Uvs.Append({
            FVector2D(0.0f, 1.0f), FVector2D(1.0f, 1.0f),
            FVector2D(0.18f, 0.44f), FVector2D(0.82f, 0.44f),
            FVector2D(0.5f, 0.0f)});
        const float Dryness = GroundCoverUnitRandom(Blade, 37, 547);
        const FLinearColor BaseColor = FMath::Lerp(
            FLinearColor(0.20f, 0.29f, 0.075f, 1.0f),
            FLinearColor(0.50f, 0.39f, 0.14f, 1.0f), Dryness);
        const FLinearColor TipColor = FMath::Lerp(
            BaseColor * 1.08f,
            FLinearColor(0.62f, 0.50f, 0.22f, 1.0f), Dryness);
        Colors.Append({
            BaseColor * 0.82f, BaseColor * 0.82f,
            BaseColor, BaseColor, TipColor});
        for (int32 Vertex = 0; Vertex < 5; ++Vertex)
        {
            Tangents.Add(FProcMeshTangent(Right, false));
        }
    }

    for (int32 Leaf = 0; Leaf < LowLeafCount; ++Leaf)
    {
        const int32 Element = BladeCount + Leaf;
        const float Angle = UE_TWO_PI *
            GroundCoverUnitRandom(Element, 41, 701);
        const FVector Forward(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector Right(-Forward.Y, Forward.X, 0.0f);
        const float RadiusCm = FMath::Lerp(
            12.0f, 94.0f, GroundCoverUnitRandom(Element, 43, 709));
        const float WidthCm = FMath::Lerp(
            7.0f, 16.0f, GroundCoverUnitRandom(Element, 47, 719));
        const float LengthCm = FMath::Lerp(
            30.0f, 74.0f, GroundCoverUnitRandom(Element, 53, 727));
        const float RiseCm = FMath::Lerp(
            5.0f, 20.0f, GroundCoverUnitRandom(Element, 59, 733));
        const FVector BaseCenter = Forward * RadiusCm;
        const FVector BaseLeft = BaseCenter - Right * WidthCm * 0.42f;
        const FVector BaseRight = BaseCenter + Right * WidthCm * 0.42f;
        const FVector MiddleCenter = BaseCenter + Forward * LengthCm * 0.56f +
            FVector(0.0f, 0.0f, RiseCm * 0.58f);
        const FVector MiddleLeft = MiddleCenter - Right * WidthCm * 0.50f;
        const FVector MiddleRight = MiddleCenter + Right * WidthCm * 0.50f;
        const FVector Tip = BaseCenter + Forward * LengthCm +
            FVector(0.0f, 0.0f, RiseCm);
        const int32 VertexBase = Vertices.Num();
        Vertices.Append({BaseLeft, BaseRight, MiddleLeft, MiddleRight, Tip});
        Triangles.Append({
            VertexBase, VertexBase + 1, VertexBase + 2,
            VertexBase + 1, VertexBase + 3, VertexBase + 2,
            VertexBase + 2, VertexBase + 3, VertexBase + 4});
        Uvs.Append({
            FVector2D(0.0f, 1.0f), FVector2D(1.0f, 1.0f),
            FVector2D(0.0f, 0.48f), FVector2D(1.0f, 0.48f),
            FVector2D(0.5f, 0.0f)});
        const float Dryness = GroundCoverUnitRandom(Element, 61, 739);
        const FLinearColor BaseColor = FMath::Lerp(
            FLinearColor(0.13f, 0.24f, 0.055f, 1.0f),
            FLinearColor(0.40f, 0.30f, 0.105f, 1.0f), Dryness);
        const FLinearColor TipColor = FMath::Lerp(
            BaseColor * 1.04f,
            FLinearColor(0.48f, 0.38f, 0.15f, 1.0f), Dryness);
        Colors.Append({
            BaseColor * 0.74f, BaseColor * 0.74f,
            BaseColor, BaseColor, TipColor});
        for (int32 Vertex = 0; Vertex < 5; ++Vertex)
        {
            Tangents.Add(FProcMeshTangent(Right, false));
        }
    }

    const TArray<FVector> Normals =
        ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* TemporaryActor = World->SpawnActor<AActor>(
        AActor::StaticClass(), FTransform::Identity);
    if (!TemporaryActor)
    {
        return nullptr;
    }
    TemporaryActor->SetActorLabel(TEXT("SouthForkGrassTuft_BuildSource"));
    USceneComponent* Root = NewObject<USceneComponent>(TemporaryActor, TEXT("Root"));
    TemporaryActor->AddInstanceComponent(Root);
    Root->RegisterComponent();
    TemporaryActor->SetRootComponent(Root);
    UProceduralMeshComponent* Procedural =
        NewObject<UProceduralMeshComponent>(TemporaryActor, TEXT("SourceMesh"));
    TemporaryActor->AddInstanceComponent(Procedural);
    Procedural->SetupAttachment(Root);
    Procedural->RegisterComponent();
    Procedural->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, Uvs, Colors, Tangents,
        /*bCreateCollision=*/false);
    Procedural->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Procedural->SetMaterial(0, Material);
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor, GroundCoverMeshPath, Material,
        /*bEnableNanite=*/false, ENaniteShapePreservation::None, OutSummary);
    TemporaryActor->Destroy();
    return Mesh;
}
} // namespace

bool CreateSouthForkGroundCoverAssets(
    UWorld* World,
    bool bReuseExistingAssets,
    UStaticMesh*& OutGrassTuftMesh,
    UMaterialInterface*& OutGrassMaterial,
    FString& OutSummary)
{
    const FString MaterialAssetName =
        FPackageName::GetLongPackageAssetName(GroundCoverMaterialPath);
    const FString MeshAssetName =
        FPackageName::GetLongPackageAssetName(GroundCoverMeshPath);
    OutGrassMaterial = bReuseExistingAssets
        ? LoadObject<UMaterialInterface>(nullptr, *FString::Printf(
            TEXT("%s.%s"), GroundCoverMaterialPath, *MaterialAssetName))
        : nullptr;
    if (!OutGrassMaterial)
    {
        OutGrassMaterial = CreateGroundCoverMaterial(OutSummary);
    }
    OutGrassTuftMesh = bReuseExistingAssets
        ? LoadObject<UStaticMesh>(nullptr, *FString::Printf(
            TEXT("%s.%s"), GroundCoverMeshPath, *MeshAssetName))
        : nullptr;
    if (!OutGrassTuftMesh && OutGrassMaterial)
    {
        OutGrassTuftMesh = CreateGrassTuftMesh(
            World, OutGrassMaterial, OutSummary);
    }
    if (!OutGrassTuftMesh || !OutGrassMaterial)
    {
        OutSummary += TEXT("Failed to prepare South Fork organic ground cover.\n");
        return false;
    }
    OutSummary += TEXT(
        "Prepared project-owned, non-colliding dry-grass ground cover.\n");
    return true;
}

FSouthForkGroundCoverPlacement ComputeSouthForkGroundCoverPlacement(
    int32 CoordinateIndex,
    int32 Column,
    float BankDistanceM,
    float LateralSlope,
    const FLinearColor& SourceDensity,
    const FVector& GroundLocation)
{
    FSouthForkGroundCoverPlacement Placement;
    if (BankDistanceM < 22.0f || BankDistanceM > 118.0f ||
        LateralSlope > 0.40f)
    {
        return Placement;
    }
    const float SourceSignal = FMath::Clamp(
        SourceDensity.A * 0.48f + SourceDensity.R * 0.12f +
            SourceDensity.G * 0.24f + SourceDensity.B * 0.16f,
        0.0f, 1.0f);
    const float PatchNoise = 0.5f + 0.5f * FMath::PerlinNoise2D(
        FVector2D(GroundLocation.X, GroundLocation.Y) / 2600.0f);
    const float ShoreFade = FMath::SmoothStep(
        22.0f, 33.0f, BankDistanceM);
    const float OuterBankFade = 1.0f - FMath::SmoothStep(
        102.0f, 118.0f, BankDistanceM);
    const float Probability = FMath::Clamp(
        (0.28f + SourceSignal * 0.48f) *
            FMath::Lerp(0.58f, 1.42f, PatchNoise) *
            ShoreFade * OuterBankFade,
        0.0f, 0.84f);
    if (GroundCoverUnitRandom(CoordinateIndex, Column, 601) > Probability)
    {
        return Placement;
    }
    Placement.bAccepted = true;
    // One accepted 8 m ecology sample represents a patch, not a single blade.
    // Several compact tufts keep the HISM count bounded while filling enough
    // of the bank to remain legible from guide-eye distance.
    Placement.ClusterCount = 3;
    Placement.ClusterCount +=
        GroundCoverUnitRandom(CoordinateIndex, Column, 607) <
            FMath::Lerp(0.45f, 0.88f, SourceSignal);
    Placement.ClusterCount +=
        GroundCoverUnitRandom(CoordinateIndex, Column, 613) <
            FMath::Lerp(0.30f, 0.72f, PatchNoise);
    Placement.ClusterCount +=
        GroundCoverUnitRandom(CoordinateIndex, Column, 615) <
            FMath::Lerp(0.12f, 0.48f, SourceSignal * PatchNoise);
    Placement.BaseScale = FMath::Lerp(
        0.76f, 1.18f,
        GroundCoverUnitRandom(CoordinateIndex, Column, 617));
    return Placement;
}

int32 AddSouthForkGroundCoverInstances(
    UHierarchicalInstancedStaticMeshComponent* GroundCover,
    const FVector& GroundLocation,
    const FVector& GroundNormal,
    const FVector2D& LeftNormal,
    int32 CoordinateIndex,
    int32 Column,
    float BankDistanceM,
    float LateralSlope,
    const FLinearColor& SourceDensity)
{
    if (!GroundCover)
    {
        return 0;
    }
    const FSouthForkGroundCoverPlacement Placement =
        ComputeSouthForkGroundCoverPlacement(
            CoordinateIndex, Column, BankDistanceM, LateralSlope,
            SourceDensity, GroundLocation);
    if (!Placement.bAccepted)
    {
        return 0;
    }

    const FVector SurfaceNormal = GroundNormal.GetSafeNormal(
        UE_SMALL_NUMBER, FVector::UpVector);
    const FVector Across(LeftNormal.X, LeftNormal.Y, 0.0f);
    const FVector Along(Across.Y, -Across.X, 0.0f);
    for (int32 Cluster = 0; Cluster < Placement.ClusterCount; ++Cluster)
    {
        const int32 Salt = 631 + Cluster * 29;
        FVector Jitter =
            Along * FMath::Lerp(
                -380.0f, 380.0f,
                GroundCoverUnitRandom(CoordinateIndex, Column, Salt)) +
            Across * FMath::Lerp(
                -340.0f, 340.0f,
                GroundCoverUnitRandom(CoordinateIndex, Column, Salt + 2));
        if (SurfaceNormal.Z > 0.25f)
        {
            // Project the jitter onto the locally smoothed terrain plane so
            // tufts remain grounded instead of floating above a coarse DEM
            // facet or disappearing into it.
            Jitter.Z = -(
                SurfaceNormal.X * Jitter.X + SurfaceNormal.Y * Jitter.Y) /
                SurfaceNormal.Z;
        }
        const float Scale = Placement.BaseScale * FMath::Lerp(
            0.82f, 1.18f,
            GroundCoverUnitRandom(CoordinateIndex, Column, Salt + 3));
        const FVector InstanceScale(
            Scale * FMath::Lerp(
                0.82f, 1.22f,
                GroundCoverUnitRandom(CoordinateIndex, Column, Salt + 5)),
            Scale * FMath::Lerp(
                0.84f, 1.18f,
                GroundCoverUnitRandom(CoordinateIndex, Column, Salt + 7)),
            Scale * FMath::Lerp(
                0.64f, 1.08f,
                GroundCoverUnitRandom(CoordinateIndex, Column, Salt + 11)));
        const FQuat SurfaceAlignment = FQuat::FindBetweenNormals(
            FVector::UpVector, SurfaceNormal);
        const FQuat OrganicRotation = FQuat(FRotator(
            FMath::Lerp(
                -4.0f, 4.0f,
                GroundCoverUnitRandom(CoordinateIndex, Column, Salt + 13)),
            GroundCoverUnitRandom(
                CoordinateIndex, Column, Salt + 17) * 360.0f,
            FMath::Lerp(
                -4.0f, 4.0f,
                GroundCoverUnitRandom(CoordinateIndex, Column, Salt + 19))));
        GroundCover->AddInstance(
            FTransform(
                SurfaceAlignment * OrganicRotation,
                GroundLocation + Jitter - SurfaceNormal * 6.0f,
                InstanceScale),
            /*bWorldSpace=*/true);
    }
    return Placement.ClusterCount;
}

TArray<FVector> BuildSouthForkSmoothedTerrainPresentationNormals(
    const TArray<FVector>& Vertices,
    int32 Width,
    int32 Height,
    int32 Radius)
{
    TArray<FVector> Normals;
    if (Width < 2 || Height < 2 || Radius < 1 ||
        Vertices.Num() != Width * Height)
    {
        return Normals;
    }
    Normals.SetNumUninitialized(Vertices.Num());
    for (int32 Row = 0; Row < Height; ++Row)
    {
        const int32 RowBefore = FMath::Max(Row - Radius, 0);
        const int32 RowAfter = FMath::Min(Row + Radius, Height - 1);
        for (int32 Column = 0; Column < Width; ++Column)
        {
            const int32 ColumnBefore = FMath::Max(Column - Radius, 0);
            const int32 ColumnAfter = FMath::Min(Column + Radius, Width - 1);
            const FVector Across =
                Vertices[Row * Width + ColumnAfter] -
                Vertices[Row * Width + ColumnBefore];
            const FVector Along =
                Vertices[RowAfter * Width + Column] -
                Vertices[RowBefore * Width + Column];
            FVector Normal = FVector::CrossProduct(Across, Along).GetSafeNormal(
                UE_SMALL_NUMBER, FVector::UpVector);
            if (Normal.Z < 0.0f)
            {
                Normal *= -1.0f;
            }
            Normals[Row * Width + Column] = Normal;
        }
    }
    return Normals;
}
} // namespace RaftSimEditorEnvironment
