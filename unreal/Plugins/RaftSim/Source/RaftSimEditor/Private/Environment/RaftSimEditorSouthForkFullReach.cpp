#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Engine/PostProcessVolume.h"
#include "Components/VolumetricCloudComponent.h"
#include "ContentStreaming.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "PhysicsEngine/BodySetup.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RenderingThread.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "StaticMeshResources.h"
#include "UObject/SavePackage.h"
#include "WorldPartition/HLOD/HLODLayer.h"
#include "WorldPartition/WorldPartition.h"
#include "WorldPartition/WorldPartitionRuntimeHash.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr TCHAR EnvironmentManifestRelativePath[] =
    TEXT("physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
         "photoreal_environment/manifest.json");
constexpr TCHAR FullReachMapPackagePath[] =
    TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach");
constexpr TCHAR FullReachInstancedHlodLayerPackagePath[] =
    TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach_HLODLayer_Instanced");
constexpr TCHAR BuildManifestRelativePath[] =
    TEXT("unreal/Content/RaftSim/Environment/SouthForkFullReach/"
         "full_reach_environment_build_manifest.json");
constexpr TCHAR CaptureDirectoryRelativePath[] =
    TEXT("docs/environment-captures/south_fork_full_reach");
constexpr TCHAR PonderosaBillboardSourceRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_PonderosaPine_Billboard.png");
constexpr TCHAR InteriorLiveOakBillboardSourceRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_Billboard.png");
constexpr float DetailedTerrainHalfWidthM = 64.0f;

struct FSouthForkCoordinatePoint
{
    double StationM = 0.0;
    FVector2D CenterM = FVector2D::ZeroVector;
    FVector2D LeftNormal = FVector2D::UnitY();
};

struct FSouthForkGray16Image
{
    int32 Width = 0;
    int32 Height = 0;
    TArray<uint16> Values;
};

struct FSouthForkBuildMetrics
{
    int32 TerrainTileCount = 0;
    int32 WaterTileCount = 0;
    int32 FarFieldPatchCount = 0;
    int32 FoliageInstanceCount = 0;
    int32 FarFieldFoliageInstanceCount = 0;
    int32 BoulderInstanceCount = 0;
    int32 ScenicRockInstanceCount = 0;
    int32 SprayMistInstanceCount = 0;
    int32 InfrastructureActorCount = 0;
    int64 TerrainTriangleCount = 0;
    int64 WaterTriangleCount = 0;
    int64 FarFieldTriangleCount = 0;
    TArray<float> MedianCenterWaterLocalZCm;
};

FString AbsoluteRepoPath(const FString& RelativePath)
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), RelativePath));
}

FLinearColor DecodePreviewSrgbColor(const FLinearColor& Encoded)
{
    const FColor Srgb(
        FMath::RoundToInt(FMath::Clamp(Encoded.R, 0.0f, 1.0f) * 255.0f),
        FMath::RoundToInt(FMath::Clamp(Encoded.G, 0.0f, 1.0f) * 255.0f),
        FMath::RoundToInt(FMath::Clamp(Encoded.B, 0.0f, 1.0f) * 255.0f),
        FMath::RoundToInt(FMath::Clamp(Encoded.A, 0.0f, 1.0f) * 255.0f));
    return FLinearColor::FromSRGBColor(Srgb);
}

bool LoadJsonObject(const FString& RelativePath, TSharedPtr<FJsonObject>& OutRoot)
{
    FString Text;
    if (!FFileHelper::LoadFileToString(Text, *AbsoluteRepoPath(RelativePath)))
    {
        return false;
    }
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
    return FJsonSerializer::Deserialize(Reader, OutRoot) && OutRoot.IsValid();
}

bool LoadGray16Png(const FString& RelativePath, FSouthForkGray16Image& OutImage)
{
    OutImage = FSouthForkGray16Image();
    TArray<uint8> Compressed;
    const FString AbsolutePath = AbsoluteRepoPath(RelativePath);
    if (!FFileHelper::LoadFileToArray(Compressed, *AbsolutePath))
    {
        return false;
    }
    IImageWrapperModule& WrapperModule =
        FModuleManager::LoadModuleChecked<IImageWrapperModule>(TEXT("ImageWrapper"));
    TSharedPtr<IImageWrapper> Wrapper =
        WrapperModule.CreateImageWrapper(EImageFormat::PNG, *AbsolutePath);
    if (!Wrapper.IsValid() ||
        !Wrapper->SetCompressed(Compressed.GetData(), Compressed.Num()))
    {
        return false;
    }
    TArray<uint8> Raw;
    if (!Wrapper->GetRaw(ERGBFormat::Gray, 16, Raw))
    {
        return false;
    }
    OutImage.Width = Wrapper->GetWidth();
    OutImage.Height = Wrapper->GetHeight();
    if (OutImage.Width <= 0 || OutImage.Height <= 0 ||
        Raw.Num() != OutImage.Width * OutImage.Height * 2)
    {
        return false;
    }
    OutImage.Values.SetNumUninitialized(OutImage.Width * OutImage.Height);
    FMemory::Memcpy(
        OutImage.Values.GetData(), Raw.GetData(),
        OutImage.Values.Num() * static_cast<int32>(sizeof(uint16)));
    // IImageWrapper returns host-order Gray16 samples. Keep this copy explicit:
    // applying PNG's network byte order a second time creates saw-tooth cliffs.
    int64 LargeNeighborJumpCount = 0;
    int64 NeighborPairCount = 0;
    for (int32 Y = 0; Y < OutImage.Height; ++Y)
    {
        for (int32 X = 0; X < OutImage.Width; ++X)
        {
            const int32 Index = Y * OutImage.Width + X;
            if (X + 1 < OutImage.Width)
            {
                LargeNeighborJumpCount += FMath::Abs(
                    static_cast<int32>(OutImage.Values[Index]) -
                    static_cast<int32>(OutImage.Values[Index + 1])) > 20000;
                ++NeighborPairCount;
            }
            if (Y + 1 < OutImage.Height)
            {
                LargeNeighborJumpCount += FMath::Abs(
                    static_cast<int32>(OutImage.Values[Index]) -
                    static_cast<int32>(OutImage.Values[Index + OutImage.Width])) > 20000;
                ++NeighborPairCount;
            }
        }
    }
    if (NeighborPairCount > 0 &&
        static_cast<double>(LargeNeighborJumpCount) / NeighborPairCount > 0.005)
    {
        UE_LOG(
            LogRaftSimEditorEnvironment, Error,
            TEXT("Rejected discontinuous 16-bit height product: %s"),
            *AbsolutePath);
        OutImage = FSouthForkGray16Image();
        return false;
    }
    return true;
}

float DecodeHeightM(uint16 Encoded, double MinimumM, double MaximumM)
{
    return static_cast<float>(
        MinimumM + (MaximumM - MinimumM) * static_cast<double>(Encoded) / 65535.0);
}

bool ParseCoordinateMap(
    const TSharedPtr<FJsonObject>& EnvironmentRoot,
    TArray<FSouthForkCoordinatePoint>& OutPoints,
    float& OutVerticalDatumM,
    FString& OutCoordinateMapPath)
{
    const TSharedPtr<FJsonObject>* CoordinateArtifact = nullptr;
    if (!EnvironmentRoot->TryGetObjectField(TEXT("coordinate_map"), CoordinateArtifact) ||
        CoordinateArtifact == nullptr ||
        !(*CoordinateArtifact)->TryGetStringField(TEXT("path"), OutCoordinateMapPath))
    {
        return false;
    }
    TSharedPtr<FJsonObject> Root;
    if (!LoadJsonObject(OutCoordinateMapPath, Root))
    {
        return false;
    }
    FString Schema;
    double VerticalDatumM = 0.0;
    const TArray<TSharedPtr<FJsonValue>>* PointValues = nullptr;
    if (!Root->TryGetStringField(TEXT("schema"), Schema) ||
        Schema != TEXT("raftsim.curved_river_coordinate_map.v1") ||
        !Root->TryGetNumberField(TEXT("vertical_datum_m"), VerticalDatumM) ||
        !Root->TryGetArrayField(TEXT("points"), PointValues) || PointValues == nullptr)
    {
        return false;
    }
    OutPoints.Reset(PointValues->Num());
    OutPoints.Reserve(PointValues->Num());
    for (const TSharedPtr<FJsonValue>& Value : *PointValues)
    {
        const TArray<TSharedPtr<FJsonValue>>* Point = nullptr;
        if (!Value.IsValid() || !Value->TryGetArray(Point) ||
            Point == nullptr || Point->Num() != 5)
        {
            return false;
        }
        FSouthForkCoordinatePoint Parsed;
        Parsed.StationM = (*Point)[0]->AsNumber();
        Parsed.CenterM = FVector2D((*Point)[1]->AsNumber(), (*Point)[2]->AsNumber());
        Parsed.LeftNormal = FVector2D(
            (*Point)[3]->AsNumber(), (*Point)[4]->AsNumber()).GetSafeNormal();
        OutPoints.Add(Parsed);
    }
    if (OutPoints.Num() < 2)
    {
        return false;
    }
    double WorldLengthM = 0.0;
    for (int32 Index = 1; Index < OutPoints.Num(); ++Index)
    {
        if (OutPoints[Index].StationM <= OutPoints[Index - 1].StationM)
        {
            return false;
        }
        const double CenterStepM = FVector2D::Distance(
            OutPoints[Index - 1].CenterM, OutPoints[Index].CenterM);
        WorldLengthM += CenterStepM;
        constexpr float CorridorHalfWidthM = 256.0f;
        const FVector2D PreviousLeft = OutPoints[Index - 1].CenterM +
            OutPoints[Index - 1].LeftNormal * CorridorHalfWidthM;
        const FVector2D CurrentLeft = OutPoints[Index].CenterM +
            OutPoints[Index].LeftNormal * CorridorHalfWidthM;
        const FVector2D PreviousRight = OutPoints[Index - 1].CenterM -
            OutPoints[Index - 1].LeftNormal * CorridorHalfWidthM;
        const FVector2D CurrentRight = OutPoints[Index].CenterM -
            OutPoints[Index].LeftNormal * CorridorHalfWidthM;
        const double CorridorEdgeStepM = FMath::Max(
            FVector2D::Distance(PreviousLeft, CurrentLeft),
            FVector2D::Distance(PreviousRight, CurrentRight));
        if (CorridorEdgeStepM > 16.0)
        {
            UE_LOG(
                LogRaftSimEditorEnvironment, Error,
                TEXT("Coordinate-map frame folds the terrain corridor at row %d: "
                     "edge step %.3f m for center step %.3f m."),
                Index, CorridorEdgeStepM, CenterStepM);
            return false;
        }
    }
    const double StationLengthM =
        OutPoints.Last().StationM - OutPoints[0].StationM;
    if (StationLengthM <= 0.0 ||
        FMath::Abs(WorldLengthM - StationLengthM) / StationLengthM > 0.005)
    {
        UE_LOG(
            LogRaftSimEditorEnvironment, Error,
            TEXT("Coordinate-map world length %.3f m does not match station length %.3f m."),
            WorldLengthM, StationLengthM);
        return false;
    }
    OutVerticalDatumM = static_cast<float>(VerticalDatumM);
    return true;
}

int32 ClosestCoordinateIndex(
    const TArray<FSouthForkCoordinatePoint>& Points, double StationM)
{
    int32 Low = 0;
    int32 High = Points.Num() - 1;
    while (Low + 1 < High)
    {
        const int32 Mid = Low + (High - Low) / 2;
        if (Points[Mid].StationM <= StationM)
        {
            Low = Mid;
        }
        else
        {
            High = Mid;
        }
    }
    return FMath::Abs(Points[Low].StationM - StationM) <=
            FMath::Abs(Points[High].StationM - StationM)
        ? Low
        : High;
}

FVector2D CoordinateWorldM(
    const FSouthForkCoordinatePoint& Point, float LateralM)
{
    return Point.CenterM + Point.LeftNormal * LateralM;
}

FVector CoordinateTangent(const TArray<FSouthForkCoordinatePoint>& Points, int32 Index)
{
    if (!Points.IsValidIndex(Index))
    {
        return FVector::ForwardVector;
    }
    // The terrain cross-sections use the conditioned frame stored in the
    // coordinate map. Camera and infrastructure orientation must use that
    // same frame; differentiating the unsmoothed NHD vertices can disagree by
    // more than 50 degrees at digitization corners and looks straight across
    // a bank ribbon instead of down the channel.
    const FVector2D Normal = Points[Index].LeftNormal.GetSafeNormal();
    const FVector2D Tangent(Normal.Y, -Normal.X);
    return FVector(Tangent.X, Tangent.Y, 0.0f);
}

void SetSpatiallyLoadedIfAllowed(AActor* Actor, bool bSpatiallyLoaded)
{
    if (Actor && Actor->CanChangeIsSpatiallyLoadedFlag())
    {
        Actor->SetIsSpatiallyLoaded(bSpatiallyLoaded);
    }
}

TArray<FProcMeshTangent> BuildFlowTangents(
    const TArray<FVector>& Vertices, int32 Width, int32 Height)
{
    TArray<FProcMeshTangent> Tangents;
    Tangents.SetNum(Vertices.Num());
    for (int32 Row = 0; Row < Height; ++Row)
    {
        const int32 PreviousRow = FMath::Max(Row - 1, 0);
        const int32 NextRow = FMath::Min(Row + 1, Height - 1);
        for (int32 Column = 0; Column < Width; ++Column)
        {
            const FVector Direction =
                (Vertices[NextRow * Width + Column] -
                 Vertices[PreviousRow * Width + Column]).GetSafeNormal();
            Tangents[Row * Width + Column] = FProcMeshTangent(Direction, false);
        }
    }
    return Tangents;
}

UStaticMesh* CreateMeshAsset(
    UWorld* World,
    const FString& AssetPackagePath,
    const FString& Label,
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles,
    const TArray<FVector>& Normals,
    const TArray<FVector2D>& UVs,
    const TArray<FLinearColor>& VertexColors,
    const TArray<FProcMeshTangent>& Tangents,
    UMaterialInterface* Material,
    bool bEnableNanite,
    bool bComplexCollision,
    FString& OutSummary)
{
    AActor* TemporaryActor = World->SpawnActor<AActor>(
        AActor::StaticClass(), FTransform::Identity);
    if (!TemporaryActor)
    {
        return nullptr;
    }
    TemporaryActor->SetActorLabel(Label + TEXT("_BuildSource"));
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
        0, Vertices, Triangles, Normals, UVs, VertexColors, Tangents,
        bComplexCollision);
    Procedural->SetCollisionEnabled(
        bComplexCollision
            ? ECollisionEnabled::QueryAndPhysics
            : ECollisionEnabled::NoCollision);
    Procedural->SetMaterial(0, Material);

    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor, AssetPackagePath, Material,
        bEnableNanite,
        ENaniteShapePreservation::None,
        OutSummary);
    TemporaryActor->Destroy();
    if (!Mesh)
    {
        return nullptr;
    }
    if (bComplexCollision)
    {
        Mesh->CreateBodySetup();
        if (UBodySetup* BodySetup = Mesh->GetBodySetup())
        {
            BodySetup->CollisionTraceFlag = CTF_UseComplexAsSimple;
            BodySetup->InvalidatePhysicsData();
            BodySetup->CreatePhysicsMeshes();
        }
        Mesh->MarkPackageDirty();
        const FString Filename = FPackageName::LongPackageNameToFilename(
            AssetPackagePath, FPackageName::GetAssetPackageExtension());
        FSavePackageArgs SaveArgs;
        SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
        SaveArgs.SaveFlags = SAVE_NoError;
        if (!UPackage::SavePackage(Mesh->GetOutermost(), Mesh, *Filename, SaveArgs))
        {
            return nullptr;
        }
    }
    return Mesh;
}

UTexture2D* CreateSouthForkCanopyTexture(
    const FString& SpeciesAssetName,
    const FString& SourceRelativePath,
    FString& OutSummary)
{
    FRaftSimFirstPartyMaterialTextureAssetSpec Spec;
    Spec.RiverId = TEXT("south_fork_generated_canopy");
    Spec.RiverAssetName = SpeciesAssetName;
    Spec.MapKey = TEXT("BillboardAlbedoOpacity");
    Spec.MapKind = TEXT("generated_canopy_albedo_opacity");
    Spec.SourceRelativePath = SourceRelativePath;
    Spec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Textures");
    Spec.CompressionSettings = TC_Default;
    Spec.bSRGB = true;
    Spec.LODGroup = TEXTUREGROUP_Impostor;
    Spec.AddressX = TA_Clamp;
    Spec.AddressY = TA_Clamp;
    Spec.bCompressionNoAlpha = false;
    bool bSaved = false;
    UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        Spec, OutSummary, bSaved);
    if (!Texture || !bSaved ||
        !RebuildAndValidateFirstPartyTexturePlatformData(Texture, Spec, OutSummary))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to build generated South Fork canopy texture %s.\n"),
            *SourceRelativePath);
        return nullptr;
    }
    return Texture;
}

UTexture2D* CreateSouthForkTerrainMacroTexture(
    const FString& TileId,
    const FString& SourceRelativePath,
    FString& OutSummary)
{
    FRaftSimFirstPartyMaterialTextureAssetSpec Spec;
    Spec.RiverId = TEXT("south_fork_full_reach");
    Spec.RiverAssetName = TileId;
    Spec.MapKey = TEXT("MacroAlbedo");
    Spec.MapKind = TEXT("source_conditioned_naip_macro_albedo");
    Spec.SourceRelativePath = SourceRelativePath;
    Spec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Terrain/MacroTextures");
    Spec.CompressionSettings = TC_Default;
    Spec.bSRGB = true;
    Spec.LODGroup = TEXTUREGROUP_World;
    Spec.AddressX = TA_Clamp;
    Spec.AddressY = TA_Clamp;
    Spec.bCompressionNoAlpha = true;
    bool bSaved = false;
    UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        Spec, OutSummary, bSaved);
    if (!Texture || !bSaved ||
        !RebuildAndValidateFirstPartyTexturePlatformData(Texture, Spec, OutSummary))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to build South Fork macro-albedo texture for %s.\n"),
            *TileId);
        return nullptr;
    }
    return Texture;
}

UMaterialInstanceConstant* CreateSouthForkTerrainMaterialInstance(
    const FString& TileId,
    UMaterialInterface* Parent,
    UTexture2D* SourceMacroTexture,
    bool bUseCorridorEdgeBlend,
    FString& OutSummary)
{
    if (!Parent || !SourceMacroTexture)
    {
        return nullptr;
    }
    const FString AssetName = TEXT("MI_RaftSim_") + TileId + TEXT("_Terrain");
    const FString PackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Terrain/Materials/") +
        AssetName;
    const FString ObjectPath = PackagePath + TEXT(".") + AssetName;
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(
        nullptr, *ObjectPath);
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package, *AssetName,
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
    Instance->SetTextureParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceMacroTexture")), SourceMacroTexture);
    const bool bForceVertexMacro = bUseCorridorEdgeBlend && FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimUseSouthForkVertexMacro"));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("UseSourceMacroTexture")),
        bForceVertexMacro ? 0.0f : 1.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("UseCorridorEdgeBlend")),
        bUseCorridorEdgeBlend ? 1.0f : 0.0f);
    Instance->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Instance, *Filename, SaveArgs))
    {
        return nullptr;
    }
    return Instance;
}

UMaterial* CreateSouthForkCanopyMaterial(
    const FString& SpeciesAssetName,
    UTexture2D* AlbedoOpacity,
    FString& OutSummary)
{
    if (!AlbedoOpacity)
    {
        return nullptr;
    }
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/"
             "M_RaftSim_%s_Billboard"),
        *SpeciesAssetName);
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"), *PackagePath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(*PackagePath);
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
    // Keep a small photographic fill term, but let the Two Sided Foliage model
    // respond to canyon light and shadow. Fully unlit cards preserved source
    // colour at the cost of reading as flat cut-outs in the guide-eye views.
    Material->SetShadingModel(MSM_TwoSidedFoliage);
    Material->BlendMode = BLEND_Masked;
    Material->TwoSided = true;
    Material->DitheredLODTransition = true;
    Material->OpacityMaskClipValue = 0.42f;

    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionTextureSampleParameter2D* CanopySample = AddExpression(
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -520, -140);
    CanopySample->ParameterName = TEXT("CanopyAlbedoOpacity");
    CanopySample->Texture = AlbedoOpacity;
    CanopySample->SamplerType = SAMPLERTYPE_Color;
    UMaterialExpressionConstant* Roughness = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -260, 150);
    Roughness->R = 0.84f;
    UMaterialExpressionConstant* Specular = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -260, 240);
    Specular->R = 0.08f;
    UMaterialExpressionConstant* AmbientOcclusion = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -260, 330);
    AmbientOcclusion->R = 1.0f;
    UMaterialExpressionConstant3Vector* CanopyTint = AddExpression(
        NewObject<UMaterialExpressionConstant3Vector>(Material), -260, -230);
    CanopyTint->Constant = SpeciesAssetName.Contains(TEXT("InteriorLiveOak"))
        ? FLinearColor(0.72f, 1.08f, 0.70f, 1.0f)
        : FLinearColor(0.82f, 1.02f, 0.78f, 1.0f);
    UMaterialExpressionMultiply* Fill = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), 0, -200);
    Fill->A.Expression = CanopySample;
    Fill->B.Expression = CanopyTint;
    UMaterialExpressionConstant* EmissiveFillScale = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -260, -320);
    // The source photo already contains branch self-shadow. Retain enough fill
    // to avoid black side-card silhouettes while Two Sided Foliage supplies
    // large-scale canyon lighting and cast-shadow response.
    EmissiveFillScale->R = 0.30f;
    UMaterialExpressionMultiply* EmissiveFill = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), 0, -300);
    EmissiveFill->A.Expression = CanopySample;
    EmissiveFill->B.Expression = EmissiveFillScale;
    UMaterialExpressionConstant* SubsurfaceScale = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -260, 420);
    SubsurfaceScale->R = 0.34f;
    UMaterialExpressionMultiply* Subsurface = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), 0, 410);
    Subsurface->A.Expression = CanopySample;
    Subsurface->B.Expression = SubsurfaceScale;

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, Fill);
    ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveFill);
    ConnectPreviewMaterialColorInput(EditorOnlyData->SubsurfaceColor, Subsurface);
    EditorOnlyData->OpacityMask.Connect(/*OutputIndex=*/4, CanopySample);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    ConnectPreviewMaterialScalarInput(
        EditorOnlyData->AmbientOcclusion, AmbientOcclusion);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to enable HISM usage for canopy material %s.\n"),
            *ObjectPath);
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
        OutSummary += FString::Printf(
            TEXT("Generated canopy material shader gate failed for %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    Material->MarkPackageDirty();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Saved generated South Fork canopy material %s.\n"), *ObjectPath);
    return Material;
}

UStaticMesh* CreateSouthForkCanopyCrossCardMesh(
    UWorld* World,
    const FString& SpeciesAssetName,
    float WidthCm,
    float HeightCm,
    UMaterialInterface* Material,
    FString& OutSummary)
{
    if (!World || !Material || WidthCm <= 0.0f || HeightCm <= 0.0f)
    {
        return nullptr;
    }
    const float HalfWidthCm = WidthCm * 0.5f;
    TArray<FVector> Vertices = {
        FVector(-HalfWidthCm, 0.0f, 0.0f),
        FVector(HalfWidthCm, 0.0f, 0.0f),
        FVector(-HalfWidthCm, 0.0f, HeightCm),
        FVector(HalfWidthCm, 0.0f, HeightCm),
        FVector(0.0f, -HalfWidthCm, 0.0f),
        FVector(0.0f, HalfWidthCm, 0.0f),
        FVector(0.0f, -HalfWidthCm, HeightCm),
        FVector(0.0f, HalfWidthCm, HeightCm)};
    const TArray<int32> Triangles = {
        0, 1, 2, 1, 3, 2,
        4, 5, 6, 5, 7, 6};
    TArray<FVector> Normals = {
        FVector::YAxisVector, FVector::YAxisVector,
        FVector::YAxisVector, FVector::YAxisVector,
        FVector::XAxisVector, FVector::XAxisVector,
        FVector::XAxisVector, FVector::XAxisVector};
    TArray<FVector2D> Uvs = {
        FVector2D(0.0f, 1.0f), FVector2D(1.0f, 1.0f),
        FVector2D(0.0f, 0.0f), FVector2D(1.0f, 0.0f),
        FVector2D(0.0f, 1.0f), FVector2D(1.0f, 1.0f),
        FVector2D(0.0f, 0.0f), FVector2D(1.0f, 0.0f)};
    TArray<FLinearColor> VertexColors;
    VertexColors.Init(FLinearColor::White, Vertices.Num());
    TArray<FProcMeshTangent> Tangents = {
        FProcMeshTangent(FVector::XAxisVector, false),
        FProcMeshTangent(FVector::XAxisVector, false),
        FProcMeshTangent(FVector::XAxisVector, false),
        FProcMeshTangent(FVector::XAxisVector, false),
        FProcMeshTangent(FVector::YAxisVector, false),
        FProcMeshTangent(FVector::YAxisVector, false),
        FProcMeshTangent(FVector::YAxisVector, false),
        FProcMeshTangent(FVector::YAxisVector, false)};
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
             "SM_RaftSim_%s_Billboard"),
        *SpeciesAssetName);
    return CreateMeshAsset(
        World, PackagePath, SpeciesAssetName + TEXT("_Billboard"),
        Vertices, Triangles, Normals, Uvs, VertexColors, Tangents, Material,
        /*bEnableNanite=*/false,
        /*bComplexCollision=*/false, OutSummary);
}

bool CreateSouthForkGeneratedCanopyAssets(
    UWorld* World,
    UStaticMesh*& OutPonderosaMesh,
    UStaticMesh*& OutInteriorLiveOakMesh,
    FString& OutSummary)
{
    OutPonderosaMesh = nullptr;
    OutInteriorLiveOakMesh = nullptr;
    UTexture2D* PonderosaTexture = CreateSouthForkCanopyTexture(
        TEXT("SouthForkPonderosaPine"), PonderosaBillboardSourceRelativePath,
        OutSummary);
    UTexture2D* OakTexture = CreateSouthForkCanopyTexture(
        TEXT("SouthForkInteriorLiveOak"), InteriorLiveOakBillboardSourceRelativePath,
        OutSummary);
    UMaterial* PonderosaMaterial = CreateSouthForkCanopyMaterial(
        TEXT("SouthForkPonderosaPine"), PonderosaTexture, OutSummary);
    UMaterial* OakMaterial = CreateSouthForkCanopyMaterial(
        TEXT("SouthForkInteriorLiveOak"), OakTexture, OutSummary);
    if (!PonderosaMaterial || !OakMaterial)
    {
        return false;
    }
    OutPonderosaMesh = CreateSouthForkCanopyCrossCardMesh(
        World, TEXT("SouthForkPonderosaPine"),
        /*WidthCm=*/800.0f, /*HeightCm=*/1200.0f,
        PonderosaMaterial, OutSummary);
    OutInteriorLiveOakMesh = CreateSouthForkCanopyCrossCardMesh(
        World, TEXT("SouthForkInteriorLiveOak"),
        /*WidthCm=*/1275.0f, /*HeightCm=*/850.0f,
        OakMaterial, OutSummary);
    const bool bCreated = OutPonderosaMesh && OutInteriorLiveOakMesh;
    OutSummary += bCreated
        ? TEXT("Created project-owned photoreal South Fork pine and live-oak canopy assets.\n")
        : TEXT("Failed to create project-owned South Fork canopy assets.\n");
    return bCreated;
}

AStaticMeshActor* PlaceStaticMeshActor(
    UWorld* World,
    UStaticMesh* Mesh,
    UMaterialInterface* Material,
    const FString& Label,
    const FTransform& Transform,
    FName Tag,
    ECollisionEnabled::Type Collision)
{
    AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(
        AStaticMeshActor::StaticClass(), Transform);
    if (!Actor)
    {
        return nullptr;
    }
    Actor->SetActorLabel(Label);
    Actor->Tags.AddUnique(Tag);
    SetSpatiallyLoadedIfAllowed(Actor, true);
    UStaticMeshComponent* Component = Actor->GetStaticMeshComponent();
    Component->SetMobility(EComponentMobility::Static);
    Component->SetStaticMesh(Mesh);
    Component->SetCollisionEnabled(Collision);
    if (Material)
    {
        Component->SetMaterial(0, Material);
    }
    return Actor;
}

UStaticMesh* LoadStaticMeshAsset(const FString& AssetPackagePath)
{
    const FString AssetName = FPackageName::GetLongPackageAssetName(AssetPackagePath);
    return LoadObject<UStaticMesh>(
        nullptr,
        *FString::Printf(TEXT("%s.%s"), *AssetPackagePath, *AssetName));
}

void LogStaticMeshVertexColorSummary(const FString& Label, UStaticMesh* Mesh)
{
    const FStaticMeshRenderData* RenderData = Mesh ? Mesh->GetRenderData() : nullptr;
    if (!RenderData || RenderData->LODResources.IsEmpty())
    {
        UE_LOG(LogTemp, Warning, TEXT("RaftSim color audit %s: no render data"), *Label);
        return;
    }
    const FColorVertexBuffer& Buffer =
        RenderData->LODResources[0].VertexBuffers.ColorVertexBuffer;
    const uint32 Count = Buffer.GetNumVertices();
    if (Count == 0)
    {
        UE_LOG(LogTemp, Warning, TEXT("RaftSim color audit %s: no vertex colors"), *Label);
        return;
    }
    uint64 Red = 0;
    uint64 Green = 0;
    uint64 Blue = 0;
    uint64 Alpha = 0;
    const uint32 Step = FMath::Max<uint32>(Count / 1024, 1);
    uint32 Samples = 0;
    for (uint32 Index = 0; Index < Count; Index += Step)
    {
        const FColor Color = Buffer.VertexColor(Index);
        Red += Color.R;
        Green += Color.G;
        Blue += Color.B;
        Alpha += Color.A;
        ++Samples;
    }
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim color audit %s: vertices=%u sampled=%u mean_rgba=(%.1f,%.1f,%.1f,%.1f)"),
        *Label, Count, Samples,
        static_cast<double>(Red) / Samples,
        static_cast<double>(Green) / Samples,
        static_cast<double>(Blue) / Samples,
        static_cast<double>(Alpha) / Samples);
}

UHierarchicalInstancedStaticMeshComponent* AddHism(
    AActor* Owner,
    USceneComponent* Root,
    const FName Name,
    UStaticMesh* Mesh,
    UMaterialInterface* OverrideMaterial,
    int32 CullStartCm,
    int32 CullEndCm,
    ECollisionEnabled::Type Collision)
{
    if (!Owner || !Mesh)
    {
        return nullptr;
    }
    UHierarchicalInstancedStaticMeshComponent* Component =
        NewObject<UHierarchicalInstancedStaticMeshComponent>(Owner, Name);
    Owner->AddInstanceComponent(Component);
    Component->SetupAttachment(Root);
    Component->SetStaticMesh(Mesh);
    Component->SetMobility(EComponentMobility::Static);
    Component->SetCollisionEnabled(Collision);
    Component->SetCullDistances(CullStartCm, CullEndCm);
    if (OverrideMaterial)
    {
        Component->SetMaterial(0, OverrideMaterial);
    }
    Component->RegisterComponent();
    return Component;
}

AActor* CreateInstancingActor(UWorld* World, const FString& Label, FName Tag)
{
    AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity);
    if (!Actor)
    {
        return nullptr;
    }
    Actor->SetActorLabel(Label);
    Actor->Tags.AddUnique(Tag);
    SetSpatiallyLoadedIfAllowed(Actor, true);
    USceneComponent* Root = NewObject<USceneComponent>(Actor, TEXT("Root"));
    Actor->AddInstanceComponent(Root);
    Root->SetMobility(EComponentMobility::Static);
    Root->RegisterComponent();
    Actor->SetRootComponent(Root);
    return Actor;
}

float StableUnitRandom(int32 A, int32 B, int32 C)
{
    uint32 Value = static_cast<uint32>(A) * 73856093u;
    Value ^= static_cast<uint32>(B) * 19349663u;
    Value ^= static_cast<uint32>(C) * 83492791u;
    Value ^= Value >> 13;
    Value *= 1274126177u;
    Value ^= Value >> 16;
    return static_cast<float>(Value & 0x00FFFFFFu) / 16777215.0f;
}

void AddSouthForkLighting(UWorld* World)
{
    ADirectionalLight* Sun = World->SpawnActor<ADirectionalLight>(
        ADirectionalLight::StaticClass(),
        FTransform(FRotator(-42.0f, -128.0f, 0.0f)));
    if (Sun)
    {
        Sun->SetActorLabel(TEXT("RaftSim_SouthFork_Sun"));
        Sun->GetLightComponent()->SetIntensity(6.5f);
        Sun->GetLightComponent()->SetLightColor(FLinearColor(1.0f, 0.93f, 0.82f));
        Sun->GetLightComponent()->SetCastShadows(true);
        SetSpatiallyLoadedIfAllowed(Sun, false);
    }
    ASkyLight* Sky = World->SpawnActor<ASkyLight>(
        ASkyLight::StaticClass(), FTransform::Identity);
    if (Sky)
    {
        Sky->SetActorLabel(TEXT("RaftSim_SouthFork_SkyLight"));
        Sky->GetLightComponent()->SetIntensity(0.82f);
        Sky->GetLightComponent()->SetMobility(EComponentMobility::Movable);
        Sky->GetLightComponent()->SetRealTimeCaptureEnabled(false);
        SetSpatiallyLoadedIfAllowed(Sky, false);
    }
    ASkyAtmosphere* Atmosphere = World->SpawnActor<ASkyAtmosphere>(
        ASkyAtmosphere::StaticClass(), FTransform::Identity);
    if (Atmosphere)
    {
        Atmosphere->SetActorLabel(TEXT("RaftSim_SouthFork_SkyAtmosphere"));
        SetSpatiallyLoadedIfAllowed(Atmosphere, false);
    }
    AExponentialHeightFog* Fog = World->SpawnActor<AExponentialHeightFog>(
        AExponentialHeightFog::StaticClass(), FTransform::Identity);
    if (Fog)
    {
        Fog->SetActorLabel(TEXT("RaftSim_SouthFork_RiverMist"));
        Fog->GetComponent()->SetFogDensity(0.009f);
        Fog->GetComponent()->SetFogHeightFalloff(0.18f);
        Fog->GetComponent()->SetVolumetricFog(true);
        SetSpatiallyLoadedIfAllowed(Fog, false);
    }
    AVolumetricCloud* Clouds = World->SpawnActor<AVolumetricCloud>(
        AVolumetricCloud::StaticClass(), FTransform::Identity);
    if (Clouds)
    {
        Clouds->SetActorLabel(TEXT("RaftSim_SouthFork_SeasonalClouds"));
        if (UVolumetricCloudComponent* Cloud =
                Clouds->FindComponentByClass<UVolumetricCloudComponent>())
        {
            Cloud->SetViewSampleCountScale(0.083333f);
            Cloud->SetReflectionViewSampleCountScale(0.4f);
            Cloud->SetShadowViewSampleCountScale(0.4f);
            Cloud->SetShadowReflectionViewSampleCountScale(0.2f);
        }
        SetSpatiallyLoadedIfAllowed(Clouds, false);
    }
    APostProcessVolume* Post = World->SpawnActor<APostProcessVolume>(
        APostProcessVolume::StaticClass(), FTransform::Identity);
    if (Post)
    {
        Post->SetActorLabel(TEXT("RaftSim_SouthFork_LumenColorGrade"));
        Post->bUnbound = true;
        Post->Settings.bOverride_AutoExposureBias = true;
        Post->Settings.AutoExposureBias = -0.25f;
        Post->Settings.bOverride_BloomIntensity = true;
        Post->Settings.BloomIntensity = 0.24f;
        Post->Settings.bOverride_LumenReflectionQuality = true;
        Post->Settings.LumenReflectionQuality = 2.0f;
        Post->Settings.bOverride_LumenFinalGatherQuality = true;
        Post->Settings.LumenFinalGatherQuality = 2.0f;
        SetSpatiallyLoadedIfAllowed(Post, false);
    }
}

bool SaveFullReachWorld(UWorld* World)
{
    const FString Filename = FPackageName::LongPackageNameToFilename(
        FullReachMapPackagePath, FPackageName::GetMapPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    return FEditorFileUtils::SaveMap(World, Filename);
}

UHLODLayer* ConfigureSouthForkInstancedHlodLayer(FString& OutSummary)
{
    const FString AssetName = FPackageName::GetLongPackageAssetName(
        FullReachInstancedHlodLayerPackagePath);
    UHLODLayer* Layer = LoadObject<UHLODLayer>(
        nullptr,
        *FString::Printf(
            TEXT("%s.%s"),
            FullReachInstancedHlodLayerPackagePath,
            *AssetName));
    if (!Layer)
    {
        OutSummary += TEXT(
            "The South Fork instanced HLOD layer asset is unavailable.\n");
        return nullptr;
    }
    Layer->Modify();
    Layer->SetLayerType(EHLODLayerType::Instancing);
    // A merged parent bakes an 8K material atlas for each large cell because
    // this map intentionally uses vertex colour and world-aligned materials.
    // Nanite already handles terrain reduction; an instanced terminal layer
    // provides the required streaming HLOD without destructive rebaking or a
    // multi-hour hierarchy build.
    Layer->SetParentLayer(nullptr);
    Layer->PostEditChange();
    UPackage* Package = Layer->GetOutermost();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        Package->GetName(), FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Layer, *Filename, SaveArgs))
    {
        OutSummary += TEXT("Failed to save the bounded South Fork HLOD layer.\n");
        return nullptr;
    }
    OutSummary += TEXT(
        "Configured the South Fork terminal instanced HLOD layer with no merged-atlas parent.\n");
    return Layer;
}

bool CaptureSouthForkView(
    UWorld* World,
    const FString& CaptureId,
    const FVector& CameraLocation,
    const FRotator& CameraRotation,
    FString& OutRelativePath,
    FString& OutSummary)
{
    FlushAsyncLoading();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    IStreamingManager::Get().StreamAllResources(12.0f);
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    UTextureRenderTarget2D* RenderTarget = NewObject<UTextureRenderTarget2D>(
        GetTransientPackage(), NAME_None, RF_Transient);
    if (!RenderTarget)
    {
        return false;
    }
    constexpr int32 Width = 1280;
    constexpr int32 Height = 720;
    RenderTarget->RenderTargetFormat = RTF_RGBA8_SRGB;
    RenderTarget->ClearColor = FLinearColor::Black;
    RenderTarget->InitAutoFormat(Width, Height);
    RenderTarget->UpdateResourceImmediate(true);

    ASceneCapture2D* Capture = World->SpawnActor<ASceneCapture2D>(
        ASceneCapture2D::StaticClass(), CameraLocation, CameraRotation);
    USceneCaptureComponent2D* Component =
        Capture ? Capture->GetCaptureComponent2D() : nullptr;
    if (!Component)
    {
        RenderTarget->ReleaseResource();
        return false;
    }
    Component->TextureTarget = RenderTarget;
    Component->CaptureSource = SCS_FinalColorLDR;
    Component->FOVAngle = 82.0f;
    Component->bCaptureEveryFrame = false;
    Component->bCaptureOnMovement = false;
    Component->bAlwaysPersistRenderingState = true;
    Component->ShowFlags.SetSelection(false);
    Component->ShowFlags.SetModeWidgets(false);
    Component->ShowFlags.SetCompositeEditorPrimitives(false);
    Component->CaptureScene();
    FlushRenderingCommands();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    FPlatformProcess::Sleep(0.03f);
    Component->CaptureScene();
    FlushRenderingCommands();

    TArray<FColor> Pixels;
    FTextureRenderTargetResource* Resource =
        RenderTarget->GameThread_GetRenderTargetResource();
    const bool bRead = Resource && Resource->ReadPixels(Pixels) &&
        Pixels.Num() == Width * Height;
    if (!bRead)
    {
        Capture->Destroy();
        RenderTarget->ReleaseResource();
        return false;
    }
    for (FColor& Pixel : Pixels)
    {
        Pixel.A = 255;
    }
    TArray64<uint8> Compressed;
    FImageUtils::PNGCompressImageArray(
        Width, Height, MakeArrayView(Pixels), Compressed);
    OutRelativePath = FString::Printf(
        TEXT("%s/%s.png"), CaptureDirectoryRelativePath, *CaptureId);
    const FString AbsolutePath = AbsoluteRepoPath(OutRelativePath);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(AbsolutePath), true);
    const bool bSaved = FFileHelper::SaveArrayToFile(Compressed, *AbsolutePath);
    Capture->Destroy();
    RenderTarget->ReleaseResource();
    OutSummary += FString::Printf(
        TEXT("%s full-reach capture %s -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"), *CaptureId, *AbsolutePath);
    return bSaved;
}

} // namespace

bool BuildSouthForkFullReachEnvironment(FString& OutSummary)
{
    FScopedPhotorealPreviewWorldGcLeakFatalOverride WorldGcLeakFatalOverride;
    TSharedPtr<FJsonObject> EnvironmentRoot;
    if (!LoadJsonObject(EnvironmentManifestRelativePath, EnvironmentRoot))
    {
        OutSummary += TEXT("Could not load the M4 South Fork environment manifest.\n");
        return false;
    }
    FString EnvironmentSchema;
    if (!EnvironmentRoot->TryGetStringField(TEXT("schema"), EnvironmentSchema) ||
        EnvironmentSchema != TEXT("raftsim.south_fork.photoreal_environment.v1"))
    {
        OutSummary += TEXT("The South Fork environment schema is unsupported.\n");
        return false;
    }

    TArray<FSouthForkCoordinatePoint> CoordinatePoints;
    float VerticalDatumM = 0.0f;
    FString CoordinateMapPath;
    if (!ParseCoordinateMap(
            EnvironmentRoot, CoordinatePoints, VerticalDatumM, CoordinateMapPath))
    {
        OutSummary += TEXT("Could not parse the full-reach curved coordinate map.\n");
        return false;
    }
    const bool bReuseExistingDetailedMeshes = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimReuseSouthForkFullReachMeshes"));
    const bool bReuseExistingDetailedTerrainMeshes = bReuseExistingDetailedMeshes ||
        FParse::Param(
            FCommandLine::Get(), TEXT("RaftSimReuseSouthForkDetailedTerrainMeshes"));
    const bool bReuseExistingWaterMeshes = bReuseExistingDetailedMeshes || FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimReuseSouthForkWaterMeshes"));
    const bool bReuseExistingFarFieldMeshes = bReuseExistingDetailedMeshes || FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimReuseSouthForkFarFieldMeshes"));
    if (bReuseExistingDetailedMeshes)
    {
        OutSummary += TEXT(
            "Reusing existing hash-validated detailed South Fork terrain and water meshes.\n");
    }

    const TSharedPtr<FJsonObject>* UnrealImport = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* TileValues = nullptr;
    if (!EnvironmentRoot->TryGetObjectField(TEXT("unreal_import"), UnrealImport) ||
        UnrealImport == nullptr ||
        !(*UnrealImport)->TryGetArrayField(TEXT("tiles"), TileValues) ||
        TileValues == nullptr || TileValues->Num() != 13)
    {
        OutSummary += TEXT("The full-reach manifest does not contain thirteen Unreal tiles.\n");
        return false;
    }

    IConsoleManager::Get().ProcessUserConsoleInput(
        TEXT("RaftSim.CreatePhotorealMaterials"), *GLog, nullptr);
    UMaterialInterface* TerrainMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain."
             "M_RaftSim_PhotorealRiverTerrain"));
    UMaterialInterface* WaterMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater."
             "M_RaftSim_PhotorealRiverWater"));
    if (!TerrainMaterial || !WaterMaterial)
    {
        OutSummary += TEXT("Photoreal terrain or water material is unavailable.\n");
        return false;
    }

    UWorld* World = GEditor ? GEditor->NewMap(/*bIsPartitionedWorld=*/true) : nullptr;
    if (!World || !World->GetWorldPartition())
    {
        OutSummary += TEXT("Failed to create a World Partition map.\n");
        return false;
    }

    // Establish the destination map package before assigning the project HLOD
    // layer. SaveMap duplicates a partitioned world's default HLOD setup when
    // it renames a transient map. Assigning the layer first therefore produces
    // a map-prefixed duplicate whose path is not registered with the runtime
    // hash partition policy, and the commandlet silently rejects every actor as
    // having an invalid layer. The empty bootstrap save prevents that Save-As
    // duplication; the populated save below is then an ordinary in-place save.
    World->GetWorldPartition()->SetDefaultHLODLayer(nullptr);
    if (!SaveFullReachWorld(World))
    {
        OutSummary += TEXT("Failed to establish the full-reach map package.\n");
        return false;
    }
    UHLODLayer* InstancedHlodLayer = ConfigureSouthForkInstancedHlodLayer(OutSummary);
    if (!InstancedHlodLayer)
    {
        return false;
    }
    UWorldPartition* WorldPartition = World->GetWorldPartition();
    WorldPartition->SetDefaultHLODLayer(InstancedHlodLayer);

    // Runtime Hash Set snapshots its valid HLOD partitions when it is created.
    // This new map was bootstrapped with no HLOD layer to avoid Save-As asset
    // duplication, so replace the still-empty hash now and let it initialize
    // against the terminal project layer. Without this, explicit layer
    // validation removes HLOD eligibility from every spatial actor.
    UWorldPartitionRuntimeHash* PreviousRuntimeHash = WorldPartition->RuntimeHash;
    if (!PreviousRuntimeHash)
    {
        OutSummary += TEXT("The full-reach World Partition runtime hash is unavailable.\n");
        return false;
    }
    WorldPartition->RuntimeHash = NewObject<UWorldPartitionRuntimeHash>(
        WorldPartition,
        PreviousRuntimeHash->GetClass(),
        NAME_None,
        RF_Transactional);
    if (!WorldPartition->RuntimeHash)
    {
        OutSummary += TEXT("Failed to rebuild the full-reach runtime hash for HLOD.\n");
        return false;
    }
    WorldPartition->RuntimeHash->SetDefaultValues();
    OutSummary += TEXT(
        "Rebuilt the empty runtime hash against the terminal South Fork HLOD layer.\n");
    World->GetWorldSettings()->DefaultGameMode = LoadClass<AGameModeBase>(
        nullptr, TEXT("/Script/SmokeEmIfYouGotEm.RaftSimVerticalSliceGameMode"));
    AddSouthForkLighting(World);

    FSouthForkBuildMetrics Metrics;
    Metrics.MedianCenterWaterLocalZCm.Init(-BIG_NUMBER, CoordinatePoints.Num());

    // The far-field terrain is intentionally a continuous underlay beneath the
    // detailed corridor, so its visibility mask cannot also be used as an
    // ecology mask. Index the conditioned river frame in world-space buckets
    // and keep far-field trees out of the navigable water/near-bank ribbon.
    constexpr float RiverEcologyBucketSizeM = 128.0f;
    // Detailed foliage reaches the fold-safe +/-64 m ribbon. Keep the
    // source-window dressing outside the water, but let it overlap that
    // ribbon slightly so canyon bends do not expose a conspicuous bare band.
    constexpr float FarFieldRiverExclusionM = 58.0f;
    TMap<FIntPoint, TArray<FVector2D>> RiverEcologyBuckets;
    auto RiverBucketKey = [](const FVector2D& PointM)
    {
        return FIntPoint(
            FMath::FloorToInt(PointM.X / RiverEcologyBucketSizeM),
            FMath::FloorToInt(PointM.Y / RiverEcologyBucketSizeM));
    };
    for (int32 CoordinateIndex = 0;
         CoordinateIndex < CoordinatePoints.Num();
         CoordinateIndex += 4)
    {
        const FVector2D& CenterM = CoordinatePoints[CoordinateIndex].CenterM;
        RiverEcologyBuckets.FindOrAdd(RiverBucketKey(CenterM)).Add(CenterM);
    }
    auto IsInsideFarFieldRiverExclusion =
        [&RiverEcologyBuckets, &RiverBucketKey](const FVector2D& PointM)
    {
        const FIntPoint CenterKey = RiverBucketKey(PointM);
        const float ExclusionSquared = FMath::Square(FarFieldRiverExclusionM);
        for (int32 DeltaY = -1; DeltaY <= 1; ++DeltaY)
        {
            for (int32 DeltaX = -1; DeltaX <= 1; ++DeltaX)
            {
                const TArray<FVector2D>* Bucket = RiverEcologyBuckets.Find(
                    CenterKey + FIntPoint(DeltaX, DeltaY));
                if (!Bucket)
                {
                    continue;
                }
                for (const FVector2D& RiverCenterM : *Bucket)
                {
                    if (FVector2D::DistSquared(PointM, RiverCenterM) < ExclusionSquared)
                    {
                        return true;
                    }
                }
            }
        }
        return false;
    };

    UStaticMesh* ReviewedTreeMesh = LoadObject<UStaticMesh>(nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/TreeSmall02_1K/"
             "SM_TreeSmall02.SM_TreeSmall02"));
    UStaticMesh* GeneratedPonderosaMesh = nullptr;
    UStaticMesh* GeneratedInteriorLiveOakMesh = nullptr;
    const bool bGeneratedCanopyReady = CreateSouthForkGeneratedCanopyAssets(
        World, GeneratedPonderosaMesh, GeneratedInteriorLiveOakMesh, OutSummary);
    if (!bGeneratedCanopyReady)
    {
        OutSummary += TEXT(
            "Generated canopy authoring failed; retaining the reviewed tree as a visible fallback.\n");
    }
    // Use the reviewed full-geometry Poly Haven canopy in the playable ribbon.
    // The project-owned generated cross cards remain valuable HLOD/far-field
    // assets, but selecting them for guide-eye distances made every trunk and
    // crown collapse to the same two intersecting planes.
    UStaticMesh* PineMeshes[3] = {};
    for (int32 PineIndex = 0; PineIndex < 3; ++PineIndex)
    {
        const TCHAR Variant = static_cast<TCHAR>('a' + PineIndex);
        const FString Name = FString::Printf(
            TEXT("SM_PineTree01_pine_tree_01_%c_LOD0"), Variant);
        PineMeshes[PineIndex] = LoadObject<UStaticMesh>(
            nullptr,
            *FString::Printf(
                TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                     "PineTree01_1K/%s.%s"), *Name, *Name));
        if (!PineMeshes[PineIndex])
        {
            PineMeshes[PineIndex] = ReviewedTreeMesh;
        }
    }
    UStaticMesh* BroadleafMesh = GeneratedInteriorLiveOakMesh
        ? GeneratedInteriorLiveOakMesh
        : ReviewedTreeMesh;
    UStaticMesh* FarPineMesh = GeneratedPonderosaMesh
        ? GeneratedPonderosaMesh
        : PineMeshes[0];
    UStaticMesh* FarBroadleafMesh = GeneratedInteriorLiveOakMesh
        ? GeneratedInteriorLiveOakMesh
        : BroadleafMesh;
    const float ConiferBaseScale = 1.0f;
    const float BroadleafBaseScale = 1.10f;
    const float RiparianBaseScale = 0.92f;
    UStaticMesh* ShrubMesh = LoadObject<UStaticMesh>(nullptr,
        TEXT("/Game/RaftSim/Environment/BiomeSpecies/"
             "SM_RaftSim_PVE_DeciduousShrub01_Static."
             "SM_RaftSim_PVE_DeciduousShrub01_Static"));
    UStaticMesh* RockMeshes[6] = {};
    UMaterialInterface* ReviewedRockMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockMossSet01_1K/"
             "M_RockMossSet01_ReviewLit.M_RockMossSet01_ReviewLit"));
    if (!ReviewedRockMaterial)
    {
        ReviewedRockMaterial = LoadObject<UMaterialInterface>(
            nullptr,
            TEXT("/Game/RaftSim/Materials/M_RaftSim_RiverBoulder."
                 "M_RaftSim_RiverBoulder"));
    }
    UStaticMesh* SprayMesh = LoadObject<UStaticMesh>(
        nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    UMaterialInterface* SprayMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_SprayMist."
             "M_RaftSim_SprayMist"));
    for (int32 RockIndex = 0; RockIndex < 6; ++RockIndex)
    {
        const FString Name = FString::Printf(
            TEXT("SM_RockMossSet01_rock_moss_set_01_rock%02d"), RockIndex + 1);
        RockMeshes[RockIndex] = LoadObject<UStaticMesh>(
            nullptr,
            *FString::Printf(
                TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
                     "RockMossSet01_1K/%s.%s"), *Name, *Name));
    }
    TSharedPtr<FJsonObject> BoulderRoot;
    TArray<TSharedPtr<FJsonValue>> EmptyBoulders;
    const TArray<TSharedPtr<FJsonValue>>* BoulderValues = &EmptyBoulders;
    const TSharedPtr<FJsonObject>* BoulderArtifact = nullptr;
    FString BoulderPath;
    if (EnvironmentRoot->TryGetObjectField(TEXT("boulder_catalog"), BoulderArtifact) &&
        BoulderArtifact != nullptr &&
        (*BoulderArtifact)->TryGetStringField(TEXT("path"), BoulderPath) &&
        LoadJsonObject(BoulderPath, BoulderRoot))
    {
        BoulderRoot->TryGetArrayField(TEXT("boulders"), BoulderValues);
    }

    for (int32 TileOrdinal = 0; TileOrdinal < TileValues->Num(); ++TileOrdinal)
    {
        const TSharedPtr<FJsonObject>* Tile = nullptr;
        if (!(*TileValues)[TileOrdinal]->TryGetObject(Tile) || Tile == nullptr)
        {
            return false;
        }
        FString TileId;
        const TArray<TSharedPtr<FJsonValue>>* RowRange = nullptr;
        const TSharedPtr<FJsonObject>* TerrainArtifact = nullptr;
        const TSharedPtr<FJsonObject>* TerrainEncoding = nullptr;
        const TSharedPtr<FJsonObject>* MacroArtifact = nullptr;
        const TSharedPtr<FJsonObject>* VfxArtifact = nullptr;
        if (!(*Tile)->TryGetStringField(TEXT("tile_id"), TileId) ||
            !(*Tile)->TryGetArrayField(TEXT("row_range"), RowRange) ||
            RowRange == nullptr || RowRange->Num() != 2 ||
            !(*Tile)->TryGetObjectField(TEXT("terrain_height"), TerrainArtifact) ||
            !(*Tile)->TryGetObjectField(TEXT("terrain_height_encoding"), TerrainEncoding) ||
            !(*Tile)->TryGetObjectField(TEXT("macro_albedo"), MacroArtifact) ||
            !(*Tile)->TryGetObjectField(TEXT("water_vfx_zones"), VfxArtifact))
        {
            return false;
        }
        const int32 GlobalRowStart = static_cast<int32>((*RowRange)[0]->AsNumber());
        FString TerrainPath;
        FString MacroPath;
        FString VfxPath;
        (*TerrainArtifact)->TryGetStringField(TEXT("path"), TerrainPath);
        (*MacroArtifact)->TryGetStringField(TEXT("path"), MacroPath);
        (*VfxArtifact)->TryGetStringField(TEXT("path"), VfxPath);
        double TerrainMinimumM = 0.0;
        double TerrainMaximumM = 0.0;
        (*TerrainEncoding)->TryGetNumberField(TEXT("minimum_elevation_m"), TerrainMinimumM);
        (*TerrainEncoding)->TryGetNumberField(TEXT("maximum_elevation_m"), TerrainMaximumM);
        FSouthForkGray16Image TerrainHeight;
        FRaftSimPreviewImage MacroImage;
        FRaftSimPreviewImage VfxImage;
        if (!LoadGray16Png(TerrainPath, TerrainHeight) ||
            !LoadPreviewPngImage(MacroPath, MacroImage) ||
            !LoadPreviewPngImage(VfxPath, VfxImage) ||
            TerrainHeight.Width != MacroImage.Width ||
            TerrainHeight.Height != MacroImage.Height ||
            VfxImage.Width != TerrainHeight.Width ||
            VfxImage.Height != TerrainHeight.Height)
        {
            OutSummary += FString::Printf(TEXT("Failed to decode tile %s.\n"), *TileId);
            return false;
        }
        UTexture2D* TileMacroTexture = CreateSouthForkTerrainMacroTexture(
            TileId, MacroPath, OutSummary);
        UMaterialInstanceConstant* TileTerrainMaterial =
            CreateSouthForkTerrainMaterialInstance(
                TileId, TerrainMaterial, TileMacroTexture,
                /*bUseCorridorEdgeBlend=*/true, OutSummary);
        if (!TileMacroTexture || !TileTerrainMaterial)
        {
            OutSummary += FString::Printf(
                TEXT("Failed to create textured Nanite terrain material for %s.\n"),
                *TileId);
            return false;
        }
        const int32 Width = TerrainHeight.Width;
        const int32 Height = TerrainHeight.Height;
        const int32 CenterCoordinateIndex = FMath::Clamp(
            GlobalRowStart + Height / 2, 0, CoordinatePoints.Num() - 1);
        const FVector2D TileOriginM = CoordinatePoints[CenterCoordinateIndex].CenterM;

        TArray<FVector> TerrainVertices;
        TArray<FVector2D> TerrainUvs;
        TArray<FLinearColor> TerrainColors;
        TerrainVertices.SetNum(Width * Height);
        TerrainUvs.SetNum(Width * Height);
        TerrainColors.SetNum(Width * Height);
        for (int32 Row = 0; Row < Height; ++Row)
        {
            const int32 CoordinateIndex = FMath::Clamp(
                GlobalRowStart + Row, 0, CoordinatePoints.Num() - 1);
            const FSouthForkCoordinatePoint& Point = CoordinatePoints[CoordinateIndex];
            for (int32 Column = 0; Column < Width; ++Column)
            {
                const int32 Index = Row * Width + Column;
                const float LateralM = -256.0f + 4.0f * Column;
                const FVector2D WorldM = CoordinateWorldM(Point, LateralM);
                const float ElevationM = DecodeHeightM(
                    TerrainHeight.Values[Index], TerrainMinimumM, TerrainMaximumM);
                TerrainVertices[Index] = FVector(
                    (WorldM.X - TileOriginM.X) * 100.0f,
                    (WorldM.Y - TileOriginM.Y) * 100.0f,
                    (ElevationM - VerticalDatumM) * 100.0f);
                TerrainUvs[Index] = FVector2D(
                    static_cast<float>(Column) / FMath::Max(Width - 1, 1),
                    static_cast<float>(Row) / FMath::Max(Height - 1, 1));
                TerrainColors[Index] = DecodePreviewSrgbColor(MacroImage.Pixels[Index]);
                TerrainColors[Index].A = VfxImage.Pixels[Index].R;
            }
        }
        TArray<int32> TerrainTriangles;
        TerrainTriangles.Reserve((Width - 1) * (Height - 1) * 6);
        for (int32 Row = 0; Row < Height - 1; ++Row)
        {
            for (int32 Column = 0; Column < Width - 1; ++Column)
            {
                const float CellCenterLateralM =
                    -256.0f + (static_cast<float>(Column) + 0.5f) * 4.0f;
                if (FMath::Abs(CellCenterLateralM) > DetailedTerrainHalfWidthM)
                {
                    continue;
                }
                const int32 I0 = Row * Width + Column;
                const int32 I1 = I0 + 1;
                const int32 I2 = I0 + Width;
                const int32 I3 = I2 + 1;
                // Unreal's procedural-mesh conversion treats clockwise index
                // order as the front face.  The prior counter-clockwise order
                // left the river corridor visible only through backfaces.
                TerrainTriangles.Append({I0, I1, I2, I1, I3, I2});
            }
        }
        const TArray<FVector> TerrainNormals =
            ComputePreviewMeshNormals(TerrainVertices, TerrainTriangles);
        const TArray<FProcMeshTangent> TerrainTangents =
            BuildFlowTangents(TerrainVertices, Width, Height);
        const FString TerrainAssetPath = FString::Printf(
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Terrain/SM_%s_Terrain"),
            *TileId);
        UStaticMesh* TerrainMesh = bReuseExistingDetailedTerrainMeshes
            ? LoadStaticMeshAsset(TerrainAssetPath)
            : nullptr;
        if (!TerrainMesh)
        {
            TerrainMesh = CreateMeshAsset(
                World, TerrainAssetPath, TileId + TEXT("_Terrain"),
                TerrainVertices, TerrainTriangles, TerrainNormals, TerrainUvs,
                TerrainColors, TerrainTangents, TileTerrainMaterial,
                /*bEnableNanite=*/true,
                /*bComplexCollision=*/true, OutSummary);
        }
        if (TileOrdinal == 0)
        {
            LogStaticMeshVertexColorSummary(TEXT("detailed_terrain_00"), TerrainMesh);
        }
        if (!TerrainMesh || !PlaceStaticMeshActor(
                World, TerrainMesh, TileTerrainMaterial,
                TEXT("RaftSim_SouthFork_Terrain_") + TileId,
                FTransform(FVector(TileOriginM.X * 100.0f, TileOriginM.Y * 100.0f, 0.0f)),
                TEXT("RaftSimFullReachTerrain"),
                ECollisionEnabled::QueryAndPhysics))
        {
            return false;
        }
        ++Metrics.TerrainTileCount;
        Metrics.TerrainTriangleCount += TerrainTriangles.Num() / 3;

        // Source-masked CC0/project-owned ecology, boulders, and aeration are
        // stored per tile as HISM clusters so World Partition can stream them.
        AActor* DressingActor = CreateInstancingActor(
            World, TEXT("RaftSim_SouthFork_Dressing_") + TileId,
            TEXT("RaftSimFullReachDressing"));
        USceneComponent* DressingRoot = DressingActor ? DressingActor->GetRootComponent() : nullptr;
        UHierarchicalInstancedStaticMeshComponent* Conifers[3] = {
            AddHism(DressingActor, DressingRoot, TEXT("ConiferA"), PineMeshes[0], nullptr,
                250000, 650000, ECollisionEnabled::QueryAndPhysics),
            AddHism(DressingActor, DressingRoot, TEXT("ConiferB"), PineMeshes[1], nullptr,
                250000, 650000, ECollisionEnabled::QueryAndPhysics),
            AddHism(DressingActor, DressingRoot, TEXT("ConiferC"), PineMeshes[2], nullptr,
                250000, 650000, ECollisionEnabled::QueryAndPhysics)};
        UHierarchicalInstancedStaticMeshComponent* Broadleaf = AddHism(
            DressingActor, DressingRoot, TEXT("OakBroadleafProxy"), BroadleafMesh, nullptr,
            220000, 550000, ECollisionEnabled::QueryAndPhysics);
        UHierarchicalInstancedStaticMeshComponent* Riparian = AddHism(
            DressingActor, DressingRoot, TEXT("WillowAlderProxy"), BroadleafMesh, nullptr,
            160000, 420000, ECollisionEnabled::QueryAndPhysics);
        UHierarchicalInstancedStaticMeshComponent* Understory = AddHism(
            DressingActor, DressingRoot, TEXT("Understory"), ShrubMesh, nullptr,
            90000, 250000, ECollisionEnabled::NoCollision);
        UHierarchicalInstancedStaticMeshComponent* Spray = AddHism(
            DressingActor, DressingRoot, TEXT("SolverAuthoredSprayMist"),
            SprayMesh, SprayMaterial, 90000, 260000,
            ECollisionEnabled::NoCollision);
        UHierarchicalInstancedStaticMeshComponent* RockComponents[6] = {};
        UHierarchicalInstancedStaticMeshComponent* ScenicRockComponents[6] = {};
        for (int32 RockIndex = 0; RockIndex < 6; ++RockIndex)
        {
            RockComponents[RockIndex] = AddHism(
                DressingActor, DressingRoot,
                *FString::Printf(TEXT("Boulder%02d"), RockIndex + 1),
                RockMeshes[RockIndex], ReviewedRockMaterial, 180000, 500000,
                ECollisionEnabled::QueryAndPhysics);
            ScenicRockComponents[RockIndex] = AddHism(
                DressingActor, DressingRoot,
                *FString::Printf(TEXT("ScenicBankRock%02d"), RockIndex + 1),
                RockMeshes[RockIndex], ReviewedRockMaterial, 140000, 420000,
                ECollisionEnabled::NoCollision);
        }

        const TSharedPtr<FJsonObject>* VegetationArtifact = nullptr;
        FString VegetationPath;
        FRaftSimPreviewImage VegetationImage;
        if (!(*Tile)->TryGetObjectField(
                TEXT("vegetation_species_density"), VegetationArtifact) ||
            VegetationArtifact == nullptr ||
            !(*VegetationArtifact)->TryGetStringField(TEXT("path"), VegetationPath) ||
            !LoadPreviewPngImage(VegetationPath, VegetationImage) ||
            VegetationImage.Width != Width || VegetationImage.Height != Height)
        {
            return false;
        }
        for (int32 Row = 2; Row < Height - 2; Row += 2)
        {
            const int32 CoordinateIndex = GlobalRowStart + Row;
            if (!CoordinatePoints.IsValidIndex(CoordinateIndex))
            {
                continue;
            }
            const FSouthForkCoordinatePoint& Point = CoordinatePoints[CoordinateIndex];
            for (int32 Column = 2; Column < Width - 2; Column += 2)
            {
                const int32 Index = Row * Width + Column;
                const float LateralM = -256.0f + 4.0f * Column;
                if (FMath::Abs(LateralM) < 34.0f ||
                    FMath::Abs(LateralM) > DetailedTerrainHalfWidthM ||
                    VfxImage.Pixels[Index].A > 0.1f)
                {
                    continue;
                }
                const FLinearColor Density = VegetationImage.Pixels[Index];
                const FVector2D WorldM = CoordinateWorldM(Point, LateralM);
                const float ElevationM = DecodeHeightM(
                    TerrainHeight.Values[Index], TerrainMinimumM, TerrainMaximumM);
                FVector Location(
                    WorldM.X * 100.0f, WorldM.Y * 100.0f,
                    (ElevationM - VerticalDatumM) * 100.0f);
                // The source products do not resolve individual bank stones.
                // Add explicitly non-colliding deterministic scree where the
                // near-bank terrain is exposed; collision-authority boulders
                // remain exclusively sourced from the catalog below.
                const int32 LeftHeightIndex = Row * Width + FMath::Max(Column - 1, 0);
                const int32 RightHeightIndex = Row * Width + FMath::Min(Column + 1, Width - 1);
                const float LateralSlope = FMath::Abs(
                    DecodeHeightM(TerrainHeight.Values[RightHeightIndex], TerrainMinimumM, TerrainMaximumM) -
                    DecodeHeightM(TerrainHeight.Values[LeftHeightIndex], TerrainMinimumM, TerrainMaximumM)) / 8.0f;
                const float BankDistanceM = FMath::Abs(LateralM);
                const float ScenicRockProbability =
                    (BankDistanceM >= 36.0f && BankDistanceM <= 92.0f)
                    ? FMath::Clamp(0.035f + LateralSlope * 0.18f, 0.035f, 0.22f)
                    : 0.0f;
                if (StableUnitRandom(CoordinateIndex, Column, 47) < ScenicRockProbability)
                {
                    const int32 RockIndex =
                        FMath::Abs(CoordinateIndex * 3 + Column * 11) % 6;
                    if (ScenicRockComponents[RockIndex])
                    {
                        const float RockScale = FMath::Lerp(
                            0.28f, 1.05f,
                            StableUnitRandom(CoordinateIndex, Column, 53));
                        ScenicRockComponents[RockIndex]->AddInstance(
                            FTransform(
                                FRotator(
                                    StableUnitRandom(CoordinateIndex, Column, 59) * 22.0f - 11.0f,
                                    StableUnitRandom(CoordinateIndex, Column, 61) * 360.0f,
                                    StableUnitRandom(CoordinateIndex, Column, 67) * 18.0f - 9.0f),
                                Location + FVector(0.0f, 0.0f, RockScale * 22.0f),
                                FVector(RockScale)),
                            /*bWorldSpace=*/true);
                        ++Metrics.ScenicRockInstanceCount;
                    }
                }
                const float Selection = StableUnitRandom(CoordinateIndex, Column, 19);
                UHierarchicalInstancedStaticMeshComponent* Target = nullptr;
                float Probability = 0.0f;
                float BaseScale = 1.0f;
                if (Density.B > 0.12f && FMath::Abs(LateralM) < 105.0f)
                {
                    Target = Riparian;
                    Probability = FMath::Clamp(0.12f + Density.B * 1.05f, 0.0f, 0.88f);
                    BaseScale = RiparianBaseScale;
                }
                else if (Density.R >= Density.G && Density.R > 0.12f)
                {
                    Target = Conifers[(CoordinateIndex + Column) % 3];
                    Probability = FMath::Clamp(0.10f + Density.R * 0.96f, 0.0f, 0.82f);
                    BaseScale = ConiferBaseScale;
                }
                else if (Density.G > 0.12f)
                {
                    Target = Broadleaf;
                    Probability = FMath::Clamp(0.10f + Density.G * 0.98f, 0.0f, 0.84f);
                    BaseScale = BroadleafBaseScale;
                }
                else if (Density.A > 0.15f)
                {
                    Target = Understory;
                    Probability = FMath::Clamp(0.08f + Density.A * 0.78f, 0.0f, 0.74f);
                    BaseScale = 0.75f;
                }
                else
                {
                    // Aerial species masks become sparse on shadowed, steep
                    // banks. Deterministic low understory prevents a bare
                    // procedural ribbon while retaining a much lower density
                    // than source-confirmed oak and pine pixels.
                    Target = Understory;
                    Probability = 0.17f;
                    BaseScale = 0.64f;
                }
                if (Target && Selection < Probability)
                {
                    const float Scale = BaseScale *
                        FMath::Lerp(0.78f, 1.22f,
                            StableUnitRandom(CoordinateIndex, Column, 23));
                    const float Yaw = StableUnitRandom(CoordinateIndex, Column, 29) * 360.0f;
                    Target->AddInstance(
                        FTransform(FRotator(0.0f, Yaw, 0.0f), Location,
                            FVector(Scale)),
                        /*bWorldSpace=*/true);
                    ++Metrics.FoliageInstanceCount;
                }
            }
        }

        if (BoulderValues)
        {
            for (const TSharedPtr<FJsonValue>& BoulderValue : *BoulderValues)
            {
                const TSharedPtr<FJsonObject>* Boulder = nullptr;
                if (!BoulderValue->TryGetObject(Boulder) || Boulder == nullptr)
                {
                    continue;
                }
                double StationM = 0.0;
                double LateralM = 0.0;
                double RadiusM = 1.0;
                double HeightM = 1.0;
                (*Boulder)->TryGetNumberField(TEXT("station_m"), StationM);
                (*Boulder)->TryGetNumberField(TEXT("lateral_offset_m"), LateralM);
                (*Boulder)->TryGetNumberField(TEXT("radius_m"), RadiusM);
                (*Boulder)->TryGetNumberField(TEXT("height_m"), HeightM);
                const int32 CoordinateIndex = ClosestCoordinateIndex(
                    CoordinatePoints, StationM);
                if (CoordinateIndex < GlobalRowStart ||
                    CoordinateIndex >= GlobalRowStart + Height)
                {
                    continue;
                }
                const int32 LocalRow = CoordinateIndex - GlobalRowStart;
                const int32 Column = FMath::Clamp(
                    FMath::RoundToInt((static_cast<float>(LateralM) + 256.0f) / 4.0f),
                    0, Width - 1);
                const int32 HeightIndex = LocalRow * Width + Column;
                const float BedM = DecodeHeightM(
                    TerrainHeight.Values[HeightIndex], TerrainMinimumM, TerrainMaximumM);
                const FVector2D WorldM = CoordinateWorldM(
                    CoordinatePoints[CoordinateIndex], static_cast<float>(LateralM));
                const int32 RockIndex =
                    FMath::Abs(CoordinateIndex + Column * 7) % 6;
                if (RockComponents[RockIndex])
                {
                    const float ScaleXY = static_cast<float>(RadiusM) * 0.58f;
                    const float ScaleZ = static_cast<float>(HeightM) * 0.72f;
                    RockComponents[RockIndex]->AddInstance(
                        FTransform(
                            FRotator(
                                StableUnitRandom(CoordinateIndex, Column, 31) * 18.0f - 9.0f,
                                StableUnitRandom(CoordinateIndex, Column, 37) * 360.0f,
                                StableUnitRandom(CoordinateIndex, Column, 41) * 14.0f - 7.0f),
                            FVector(
                                WorldM.X * 100.0f, WorldM.Y * 100.0f,
                                (BedM - VerticalDatumM + static_cast<float>(HeightM) * 0.80f) * 100.0f),
                            FVector(ScaleXY, ScaleXY, ScaleZ)),
                        /*bWorldSpace=*/true);
                    ++Metrics.BoulderInstanceCount;
                }
            }
        }

        const TSharedPtr<FJsonObject>* WaterBands = nullptr;
        if (!(*Tile)->TryGetObjectField(TEXT("water_bands"), WaterBands) ||
            WaterBands == nullptr)
        {
            return false;
        }
        const TSharedPtr<FJsonObject>* WaterEncoding = nullptr;
        if (!(*Tile)->TryGetObjectField(TEXT("water_height_encoding"), WaterEncoding) ||
            WaterEncoding == nullptr)
        {
            return false;
        }
        double WaterMinimumM = 0.0;
        double WaterMaximumM = 0.0;
        (*WaterEncoding)->TryGetNumberField(TEXT("minimum_elevation_m"), WaterMinimumM);
        (*WaterEncoding)->TryGetNumberField(TEXT("maximum_elevation_m"), WaterMaximumM);
        const TCHAR* FlowBands[] = {
            TEXT("low_runnable"), TEXT("median_runnable"), TEXT("high_runnable")};
        for (const TCHAR* FlowBand : FlowBands)
        {
            const TSharedPtr<FJsonObject>* Band = nullptr;
            const TSharedPtr<FJsonObject>* SurfaceArtifact = nullptr;
            const TSharedPtr<FJsonObject>* PresentationArtifact = nullptr;
            FString SurfacePath;
            FString PresentationPath;
            if (!(*WaterBands)->TryGetObjectField(FlowBand, Band) || Band == nullptr ||
                !(*Band)->TryGetObjectField(TEXT("surface_height"), SurfaceArtifact) ||
                !(*Band)->TryGetObjectField(TEXT("presentation"), PresentationArtifact) ||
                !(*SurfaceArtifact)->TryGetStringField(TEXT("path"), SurfacePath) ||
                !(*PresentationArtifact)->TryGetStringField(TEXT("path"), PresentationPath))
            {
                return false;
            }
            FSouthForkGray16Image WaterHeight;
            FRaftSimPreviewImage Presentation;
            if (!LoadGray16Png(SurfacePath, WaterHeight) ||
                !LoadPreviewPngImage(PresentationPath, Presentation) ||
                WaterHeight.Width != Presentation.Width ||
                WaterHeight.Height != Presentation.Height ||
                WaterHeight.Height != Height)
            {
                return false;
            }
            const int32 WaterWidth = WaterHeight.Width;
            TArray<FVector> WaterVertices;
            TArray<FVector2D> WaterUvs;
            TArray<FLinearColor> WaterColors;
            WaterVertices.SetNum(WaterWidth * Height);
            WaterUvs.SetNum(WaterWidth * Height);
            WaterColors.SetNum(WaterWidth * Height);
            for (int32 Row = 0; Row < Height; ++Row)
            {
                const int32 CoordinateIndex = FMath::Clamp(
                    GlobalRowStart + Row, 0, CoordinatePoints.Num() - 1);
                const FSouthForkCoordinatePoint& Point = CoordinatePoints[CoordinateIndex];
                for (int32 Column = 0; Column < WaterWidth; ++Column)
                {
                    const int32 Index = Row * WaterWidth + Column;
                    const float LateralM = -40.0f + 4.0f * Column;
                    const FVector2D WorldM = CoordinateWorldM(Point, LateralM);
                    const float ElevationM = DecodeHeightM(
                        WaterHeight.Values[Index], WaterMinimumM, WaterMaximumM);
                    const FLinearColor HydraulicPresentation =
                        Presentation.Pixels[Index];
                    const float HydraulicEnergy = FMath::Clamp(
                        HydraulicPresentation.R * 0.72f +
                        HydraulicPresentation.B * 0.48f,
                        0.0f, 1.0f);
                    // Presentation-only sub-grid surface displacement. The
                    // fixed-step shallow-water arrays remain authoritative;
                    // this deterministic visual layer resolves ripples and
                    // standing-wave shoulders below the 4 m solver mesh.
                    const float WavePhaseA =
                        Point.StationM * 0.19f + LateralM * 0.61f;
                    const float WavePhaseB =
                        Point.StationM * 0.071f - LateralM * 0.37f;
                    const float VisualDisplacementM =
                        0.012f * FMath::Sin(WavePhaseA) +
                        HydraulicEnergy *
                            (0.11f * FMath::Sin(WavePhaseA) +
                             0.065f * FMath::Sin(WavePhaseB));
                    WaterVertices[Index] = FVector(
                        (WorldM.X - TileOriginM.X) * 100.0f,
                        (WorldM.Y - TileOriginM.Y) * 100.0f,
                        (ElevationM + VisualDisplacementM - VerticalDatumM) * 100.0f);
                    WaterUvs[Index] = FVector2D(
                        Point.StationM / 3.0f,
                        LateralM / 3.0f);
                    WaterColors[Index] = Presentation.Pixels[Index];
                }
                if (FCString::Strcmp(FlowBand, TEXT("median_runnable")) == 0)
                {
                    Metrics.MedianCenterWaterLocalZCm[CoordinateIndex] =
                        WaterVertices[Row * WaterWidth + WaterWidth / 2].Z;
                }
            }
            TArray<int32> WaterTriangles;
            for (int32 Row = 0; Row < Height - 1; ++Row)
            {
                for (int32 Column = 0; Column < WaterWidth - 1; ++Column)
                {
                    const int32 I0 = Row * WaterWidth + Column;
                    const int32 I1 = I0 + 1;
                    const int32 I2 = I0 + WaterWidth;
                    const int32 I3 = I2 + 1;
                    if (WaterColors[I0].A > 0.5f && WaterColors[I1].A > 0.5f &&
                        WaterColors[I2].A > 0.5f && WaterColors[I3].A > 0.5f)
                    {
                        WaterTriangles.Append({I0, I1, I2, I1, I3, I2});
                    }
                }
            }
            const TArray<FVector> WaterNormals =
                ComputePreviewMeshNormals(WaterVertices, WaterTriangles);
            const TArray<FProcMeshTangent> WaterTangents =
                BuildFlowTangents(WaterVertices, WaterWidth, Height);
            const FString WaterAssetPath = FString::Printf(
                TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/SM_%s_Water_%s"),
                *TileId, FlowBand);
            UStaticMesh* WaterMesh = bReuseExistingWaterMeshes
                ? LoadStaticMeshAsset(WaterAssetPath)
                : nullptr;
            if (!WaterMesh)
            {
                WaterMesh = CreateMeshAsset(
                    World, WaterAssetPath,
                    FString::Printf(TEXT("%s_Water_%s"), *TileId, FlowBand),
                    WaterVertices, WaterTriangles, WaterNormals, WaterUvs,
                    WaterColors, WaterTangents, WaterMaterial,
                    /*bEnableNanite=*/false,
                    /*bComplexCollision=*/false, OutSummary);
            }
            AStaticMeshActor* WaterActor = WaterMesh ? PlaceStaticMeshActor(
                World, WaterMesh, WaterMaterial,
                FString::Printf(TEXT("RaftSim_SouthFork_Water_%s_%s"), *TileId, FlowBand),
                FTransform(FVector(TileOriginM.X * 100.0f, TileOriginM.Y * 100.0f, 0.0f)),
                *FString::Printf(TEXT("RaftSimFlowBand_%s"), FlowBand),
                ECollisionEnabled::NoCollision) : nullptr;
            if (!WaterActor)
            {
                return false;
            }
            const bool bMedian = FCString::Strcmp(FlowBand, TEXT("median_runnable")) == 0;
            WaterActor->SetActorHiddenInGame(!bMedian);
            ++Metrics.WaterTileCount;
            Metrics.WaterTriangleCount += WaterTriangles.Num() / 3;
        }

        if (Spray)
        {
            for (int32 Row = 4; Row < Height - 4; Row += 12)
            {
                const int32 CoordinateIndex = GlobalRowStart + Row;
                if (!CoordinatePoints.IsValidIndex(CoordinateIndex))
                {
                    continue;
                }
                const int32 VfxCenterIndex = Row * Width + Width / 2;
                const FLinearColor Zone = VfxImage.Pixels[VfxCenterIndex];
                if (Zone.G < 0.5f && Zone.B < 0.25f)
                {
                    continue;
                }
                const float SurfaceZCm = Metrics.MedianCenterWaterLocalZCm.IsValidIndex(CoordinateIndex)
                    ? Metrics.MedianCenterWaterLocalZCm[CoordinateIndex]
                    : TerrainVertices[Row * Width + Width / 2].Z + 120.0f;
                for (int32 Particle = 0; Particle < 3; ++Particle)
                {
                    const float LateralM = FMath::Lerp(
                        -18.0f, 18.0f,
                        StableUnitRandom(CoordinateIndex, Particle, 43));
                    const FVector2D WorldM = CoordinateWorldM(
                        CoordinatePoints[CoordinateIndex], LateralM);
                    const float Scale = FMath::Lerp(
                        0.012f, 0.045f,
                        StableUnitRandom(CoordinateIndex, Particle, 47));
                    Spray->AddInstance(
                        FTransform(
                            FRotator::ZeroRotator,
                            FVector(
                                WorldM.X * 100.0f, WorldM.Y * 100.0f,
                                SurfaceZCm + FMath::Lerp(35.0f, 190.0f,
                                    StableUnitRandom(CoordinateIndex, Particle, 53))),
                            FVector(Scale, Scale, Scale * 1.8f)),
                        /*bWorldSpace=*/true);
                    ++Metrics.SprayMistInstanceCount;
                }
            }
        }
    }

    const TSharedPtr<FJsonObject>* FarFieldRoot = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* FarFieldPatchValues = nullptr;
    if (!EnvironmentRoot->TryGetObjectField(TEXT("far_field"), FarFieldRoot) ||
        FarFieldRoot == nullptr ||
        !(*FarFieldRoot)->TryGetArrayField(TEXT("patches"), FarFieldPatchValues) ||
        FarFieldPatchValues == nullptr || FarFieldPatchValues->Num() != 8)
    {
        OutSummary += TEXT("The South Fork far-field geography is incomplete.\n");
        return false;
    }
    for (int32 PatchOrdinal = 0; PatchOrdinal < FarFieldPatchValues->Num(); ++PatchOrdinal)
    {
        const TSharedPtr<FJsonObject>* Patch = nullptr;
        const TArray<TSharedPtr<FJsonValue>>* Bounds = nullptr;
        const TSharedPtr<FJsonObject>* HeightArtifact = nullptr;
        const TSharedPtr<FJsonObject>* HeightEncoding = nullptr;
        const TSharedPtr<FJsonObject>* MacroArtifact = nullptr;
        const TSharedPtr<FJsonObject>* MaskArtifact = nullptr;
        const TSharedPtr<FJsonObject>* OwnershipArtifact = nullptr;
        FString PatchId;
        FString HeightPath;
        FString MacroPath;
        FString MaskPath;
        FString OwnershipPath;
        if (!(*FarFieldPatchValues)[PatchOrdinal]->TryGetObject(Patch) || Patch == nullptr ||
            !(*Patch)->TryGetStringField(TEXT("patch_id"), PatchId) ||
            !(*Patch)->TryGetArrayField(TEXT("bounds_local_m"), Bounds) ||
            Bounds == nullptr || Bounds->Num() != 4 ||
            !(*Patch)->TryGetObjectField(TEXT("height"), HeightArtifact) ||
            !(*Patch)->TryGetObjectField(TEXT("height_encoding"), HeightEncoding) ||
            !(*Patch)->TryGetObjectField(TEXT("macro_albedo"), MacroArtifact) ||
            !(*Patch)->TryGetObjectField(TEXT("corridor_exclusion_mask"), MaskArtifact) ||
            !(*Patch)->TryGetObjectField(
                TEXT("source_window_ownership_mask"), OwnershipArtifact) ||
            !(*HeightArtifact)->TryGetStringField(TEXT("path"), HeightPath) ||
            !(*MacroArtifact)->TryGetStringField(TEXT("path"), MacroPath) ||
            !(*MaskArtifact)->TryGetStringField(TEXT("path"), MaskPath) ||
            !(*OwnershipArtifact)->TryGetStringField(TEXT("path"), OwnershipPath))
        {
            return false;
        }
        double MinimumElevationM = 0.0;
        double MaximumElevationM = 0.0;
        (*HeightEncoding)->TryGetNumberField(
            TEXT("minimum_elevation_m"), MinimumElevationM);
        (*HeightEncoding)->TryGetNumberField(
            TEXT("maximum_elevation_m"), MaximumElevationM);
        FSouthForkGray16Image HeightImage;
        FRaftSimPreviewImage MacroImage;
        FRaftSimPreviewImage MaskImage;
        FRaftSimPreviewImage OwnershipImage;
        if (!LoadGray16Png(HeightPath, HeightImage) ||
            !LoadPreviewPngImage(MacroPath, MacroImage) ||
            !LoadPreviewPngImage(MaskPath, MaskImage) ||
            !LoadPreviewPngImage(OwnershipPath, OwnershipImage) ||
            HeightImage.Width != MacroImage.Width ||
            HeightImage.Height != MacroImage.Height ||
            MaskImage.Width != HeightImage.Width ||
            MaskImage.Height != HeightImage.Height ||
            OwnershipImage.Width != HeightImage.Width ||
            OwnershipImage.Height != HeightImage.Height)
        {
            OutSummary += FString::Printf(
                TEXT("Failed to decode far-field patch %s.\n"), *PatchId);
            return false;
        }
        UTexture2D* PatchMacroTexture = CreateSouthForkTerrainMacroTexture(
            PatchId, MacroPath, OutSummary);
        UMaterialInstanceConstant* PatchTerrainMaterial =
            CreateSouthForkTerrainMaterialInstance(
                PatchId, TerrainMaterial, PatchMacroTexture,
                /*bUseCorridorEdgeBlend=*/false, OutSummary);
        if (!PatchMacroTexture || !PatchTerrainMaterial)
        {
            OutSummary += FString::Printf(
                TEXT("Failed to create source-draped far-field material for %s.\n"),
                *PatchId);
            return false;
        }
        const double MinimumX = (*Bounds)[0]->AsNumber();
        const double MinimumY = (*Bounds)[1]->AsNumber();
        const double MaximumX = (*Bounds)[2]->AsNumber();
        const double MaximumY = (*Bounds)[3]->AsNumber();
        const FVector2D PatchOriginM(
            0.5 * (MinimumX + MaximumX), 0.5 * (MinimumY + MaximumY));
        const int32 Width = HeightImage.Width;
        const int32 Height = HeightImage.Height;
        TArray<FVector> Vertices;
        TArray<FVector2D> Uvs;
        TArray<FLinearColor> Colors;
        Vertices.SetNum(Width * Height);
        Uvs.SetNum(Width * Height);
        Colors.SetNum(Width * Height);
        for (int32 Row = 0; Row < Height; ++Row)
        {
            const double RowT = static_cast<double>(Row) / FMath::Max(Height - 1, 1);
            const double WorldY = FMath::Lerp(MaximumY, MinimumY, RowT);
            for (int32 Column = 0; Column < Width; ++Column)
            {
                const double ColumnT =
                    static_cast<double>(Column) / FMath::Max(Width - 1, 1);
                const double WorldX = FMath::Lerp(MinimumX, MaximumX, ColumnT);
                const int32 Index = Row * Width + Column;
                const float ElevationM = DecodeHeightM(
                    HeightImage.Values[Index], MinimumElevationM, MaximumElevationM);
                Vertices[Index] = FVector(
                    (WorldX - PatchOriginM.X) * 100.0,
                    (WorldY - PatchOriginM.Y) * 100.0,
                    (ElevationM - VerticalDatumM) * 100.0f - 75.0f);
                Uvs[Index] = FVector2D(ColumnT, RowT);
                Colors[Index] = DecodePreviewSrgbColor(MacroImage.Pixels[Index]);
            }
        }
        TArray<int32> Triangles;
        for (int32 Row = 0; Row < Height - 1; ++Row)
        {
            for (int32 Column = 0; Column < Width - 1; ++Column)
            {
                const int32 I0 = Row * Width + Column;
                const int32 I1 = I0 + 1;
                const int32 I2 = I0 + Width;
                const int32 I3 = I2 + 1;
                // Adjacent source-window DEM rectangles overlap around river
                // bends. Render only the deterministic nearest-station owner;
                // otherwise nearly coplanar source surfaces z-fight and form
                // kilometre-scale wedges. The ownership masks partition the
                // reach and each owned mesh remains a lowered underlay beneath
                // the detailed +/-64 m corridor.
                const int32 OwnedCornerCount =
                    (OwnershipImage.Pixels[I0].R > 0.5f ? 1 : 0) +
                    (OwnershipImage.Pixels[I1].R > 0.5f ? 1 : 0) +
                    (OwnershipImage.Pixels[I2].R > 0.5f ? 1 : 0) +
                    (OwnershipImage.Pixels[I3].R > 0.5f ? 1 : 0);
                const int32 VisibleCornerCount =
                    (MaskImage.Pixels[I0].R > 0.5f ? 1 : 0) +
                    (MaskImage.Pixels[I1].R > 0.5f ? 1 : 0) +
                    (MaskImage.Pixels[I2].R > 0.5f ? 1 : 0) +
                    (MaskImage.Pixels[I3].R > 0.5f ? 1 : 0);
                if (OwnedCornerCount >= 2 && VisibleCornerCount >= 2)
                {
                    Triangles.Append({I0, I1, I2, I1, I3, I2});
                }
            }
        }
        const FString AssetPath = FString::Printf(
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/FarField/SM_%s"),
            *PatchId);
        const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
        const TArray<FProcMeshTangent> Tangents =
            BuildFlowTangents(Vertices, Width, Height);
        UStaticMesh* Mesh = bReuseExistingFarFieldMeshes
            ? LoadStaticMeshAsset(AssetPath)
            : nullptr;
        if (!Mesh)
        {
            Mesh = CreateMeshAsset(
                World, AssetPath, PatchId, Vertices, Triangles, Normals, Uvs,
                Colors, Tangents, PatchTerrainMaterial,
                /*bEnableNanite=*/false,
                /*bComplexCollision=*/false, OutSummary);
        }
        if (PatchOrdinal == 0)
        {
            LogStaticMeshVertexColorSummary(TEXT("far_field_00"), Mesh);
        }
        if (!Mesh || !PlaceStaticMeshActor(
                World, Mesh, PatchTerrainMaterial,
                TEXT("RaftSim_SouthFork_FarField_") + PatchId,
                FTransform(FVector(PatchOriginM.X * 100.0, PatchOriginM.Y * 100.0, 0.0)),
                TEXT("RaftSimFullReachFarField"), ECollisionEnabled::NoCollision))
        {
            return false;
        }
        ++Metrics.FarFieldPatchCount;
        Metrics.FarFieldTriangleCount += Triangles.Num() / 3;

        AActor* FarDressing = CreateInstancingActor(
            World, TEXT("RaftSim_SouthFork_FarFieldDressing_") + PatchId,
            TEXT("RaftSimFullReachFarFieldDressing"));
        USceneComponent* FarRoot = FarDressing ? FarDressing->GetRootComponent() : nullptr;
        UHierarchicalInstancedStaticMeshComponent* FarConifer = AddHism(
            FarDressing, FarRoot, TEXT("FarConifer"), FarPineMesh,
            nullptr, 300000, 900000, ECollisionEnabled::NoCollision);
        UHierarchicalInstancedStaticMeshComponent* FarBroadleaf = AddHism(
            FarDressing, FarRoot, TEXT("FarBroadleaf"), FarBroadleafMesh,
            nullptr, 250000, 750000, ECollisionEnabled::NoCollision);
        for (int32 Row = 1; Row < Height - 1; ++Row)
        {
            const double RowT = static_cast<double>(Row) / FMath::Max(Height - 1, 1);
            const double WorldY = FMath::Lerp(MaximumY, MinimumY, RowT);
            for (int32 Column = 1; Column < Width - 1; ++Column)
            {
                const int32 Index = Row * Width + Column;
                if (MaskImage.Pixels[Index].R <= 0.5f ||
                    OwnershipImage.Pixels[Index].R <= 0.5f)
                {
                    continue;
                }
                const FLinearColor Color = MacroImage.Pixels[Index];
                const float Greenness = Color.G - 0.5f * (Color.R + Color.B);
                const float Probability = FMath::Clamp(
                    0.36f + Greenness * 1.6f, 0.12f, 0.86f);
                if (StableUnitRandom(PatchOrdinal * 997 + Row, Column, 71) > Probability)
                {
                    continue;
                }
                const double ColumnT =
                    static_cast<double>(Column) / FMath::Max(Width - 1, 1);
                const double WorldX = FMath::Lerp(MinimumX, MaximumX, ColumnT);
                if (IsInsideFarFieldRiverExclusion(
                        FVector2D(WorldX, WorldY)))
                {
                    continue;
                }
                const float ElevationM = DecodeHeightM(
                    HeightImage.Values[Index], MinimumElevationM, MaximumElevationM);
                const bool bChooseConifer = Greenness > 0.025f;
                UHierarchicalInstancedStaticMeshComponent* Target =
                    bChooseConifer ? FarConifer : FarBroadleaf;
                if (!Target)
                {
                    continue;
                }
                const float Yaw = StableUnitRandom(Row, Column, PatchOrdinal + 83) * 360.0f;
                const float MinimumScale = bChooseConifer
                    ? (GeneratedPonderosaMesh ? 0.70f : 0.95f)
                    : (GeneratedInteriorLiveOakMesh ? 0.74f : 0.95f);
                const float MaximumScale = bChooseConifer
                    ? (GeneratedPonderosaMesh ? 1.32f : 1.80f)
                    : (GeneratedInteriorLiveOakMesh ? 1.38f : 1.80f);
                const float Scale = FMath::Lerp(
                    MinimumScale, MaximumScale,
                    StableUnitRandom(Row, Column, PatchOrdinal + 89));
                Target->AddInstance(
                    FTransform(
                        FRotator(0.0f, Yaw, 0.0f),
                        FVector(
                            WorldX * 100.0, WorldY * 100.0,
                            (ElevationM - VerticalDatumM) * 100.0f),
                        FVector(Scale)),
                    /*bWorldSpace=*/true);
                ++Metrics.FarFieldFoliageInstanceCount;
            }
        }
    }

    // Runtime configuration and the playable start are stationed on the same
    // curved map as terrain, water, captures, and physics.
    constexpr float StartStationM = 120.0f;
    const int32 StartIndex = ClosestCoordinateIndex(CoordinatePoints, StartStationM);
    const FVector2D StartWorldM = CoordinateWorldM(CoordinatePoints[StartIndex], 0.0f);
    const FVector StartTangent = CoordinateTangent(CoordinatePoints, StartIndex);
    const float StartWaterZCm = Metrics.MedianCenterWaterLocalZCm[StartIndex] > -BIG_NUMBER * 0.5f
        ? Metrics.MedianCenterWaterLocalZCm[StartIndex]
        : 52000.0f;
    ARaftSimRiverWaterConfig* WaterConfig = World->SpawnActor<ARaftSimRiverWaterConfig>(
        ARaftSimRiverWaterConfig::StaticClass(), FTransform::Identity);
    if (!WaterConfig)
    {
        return false;
    }
    WaterConfig->SetActorLabel(TEXT("RaftSim_SouthFork_FullReachWaterConfig"));
    WaterConfig->CookedFieldsDir =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/"
             "full_reach_transit_seed");
    WaterConfig->FlowBand = TEXT("median_runnable");
    WaterConfig->WindowCenterM = FVector2D(StartStationM, 0.0f);
    WaterConfig->CoordinateMapPath = CoordinateMapPath;
    WaterConfig->StreamingManifestPath =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/"
             "full_hydraulics/streaming_manifest.json");
    WaterConfig->bEnableMovingWindowStreaming = true;
    WaterConfig->MovingWindowStationExtentM = 320.0f;
    WaterConfig->MovingWindowLateralExtentM = 80.0f;
    WaterConfig->MovingWindowAdvanceM = 80.0f;
    WaterConfig->bMapProvidesTerrain = true;
    SetSpatiallyLoadedIfAllowed(WaterConfig, false);

    const FRotator StartRotation = StartTangent.Rotation();
    ARaftSimRaftActor* Raft = World->SpawnActor<ARaftSimRaftActor>(
        ARaftSimRaftActor::StaticClass(),
        FVector(StartWorldM.X * 100.0f, StartWorldM.Y * 100.0f, StartWaterZCm + 58.0f),
        StartRotation);
    if (Raft)
    {
        Raft->SetActorLabel(TEXT("RaftSim_SouthFork_PlayerRaft"));
        SetSpatiallyLoadedIfAllowed(Raft, false);
    }
    APlayerStart* PlayerStart = World->SpawnActor<APlayerStart>(
        APlayerStart::StaticClass(),
        FVector(
            (StartWorldM.X - StartTangent.X * 4.0f) * 100.0f,
            (StartWorldM.Y - StartTangent.Y * 4.0f) * 100.0f,
            StartWaterZCm + 170.0f),
        StartRotation);
    if (PlayerStart)
    {
        PlayerStart->SetActorLabel(TEXT("RaftSim_SouthFork_PlayerStart"));
        SetSpatiallyLoadedIfAllowed(PlayerStart, false);
    }

    // Finished procedural access context. The bridge and landings are tagged
    // as game-context infill and never presented as real navigation guidance.
    UStaticMesh* CubeMesh = LoadObject<UStaticMesh>(
        nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    UMaterialInterface* Timber = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_Timber.M_RaftSim_Timber"));
    UMaterialInterface* Steel = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_GalvanizedSteel."
             "M_RaftSim_GalvanizedSteel"));
    UMaterialInterface* Asphalt = LoadObject<UMaterialInterface>(
        nullptr, TEXT("/Game/RaftSim/Materials/M_RaftSim_Asphalt.M_RaftSim_Asphalt"));
    UMaterialInterface* Concrete = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_WeatheredConcrete."
             "M_RaftSim_WeatheredConcrete"));
    auto AddInfrastructureCube = [&](const FString& Label, const FVector& Location,
                                     const FRotator& Rotation, const FVector& Scale,
                                     UMaterialInterface* Material)
    {
        AStaticMeshActor* Actor = PlaceStaticMeshActor(
            World, CubeMesh, Material, Label,
            FTransform(Rotation, Location, Scale),
            TEXT("RaftSimProceduralInfrastructureNotForNavigation"),
            ECollisionEnabled::QueryAndPhysics);
        if (Actor)
        {
            ++Metrics.InfrastructureActorCount;
        }
        return Actor;
    };
    auto AddInfrastructureBeam = [&](const FString& Label, const FVector& Start,
                                     const FVector& End, float ThicknessCm,
                                     UMaterialInterface* Material)
    {
        const FVector Delta = End - Start;
        const float LengthCm = Delta.Size();
        if (LengthCm < 1.0f)
        {
            return static_cast<AStaticMeshActor*>(nullptr);
        }
        return AddInfrastructureCube(
            Label, (Start + End) * 0.5f, Delta.Rotation(),
            FVector(LengthCm / 100.0f, ThicknessCm / 100.0f,
                    ThicknessCm / 100.0f),
            Material);
    };
    const int32 BridgeIndex = ClosestCoordinateIndex(CoordinatePoints, 5200.0);
    const FVector BridgeTangent = CoordinateTangent(CoordinatePoints, BridgeIndex);
    const FVector2D BridgeWorldM = CoordinateWorldM(CoordinatePoints[BridgeIndex], 0.0f);
    const float BridgeWaterZCm = Metrics.MedianCenterWaterLocalZCm[BridgeIndex];
    const FVector BridgeCenter(
        BridgeWorldM.X * 100.0f, BridgeWorldM.Y * 100.0f, BridgeWaterZCm + 560.0f);
    const FVector BridgeNormal(
        CoordinatePoints[BridgeIndex].LeftNormal.X,
        CoordinatePoints[BridgeIndex].LeftNormal.Y, 0.0f);
    const FRotator BridgeRotation = BridgeNormal.Rotation();
    AddInfrastructureCube(
        TEXT("RaftSim_ColomaContextBridge_Deck_Procedural"), BridgeCenter,
        BridgeRotation, FVector(74.0f, 4.8f, 0.55f), Timber);
    for (float Side : {-1.0f, 1.0f})
    {
        AddInfrastructureCube(
            FString::Printf(TEXT("RaftSim_ColomaBridge_UpperRail_%d"), Side > 0 ? 1 : 0),
            BridgeCenter + BridgeTangent * Side * 225.0f + FVector(0.0f, 0.0f, 190.0f),
            BridgeRotation, FVector(74.0f, 0.12f, 0.14f), Steel);
        AddInfrastructureCube(
            FString::Printf(TEXT("RaftSim_ColomaBridge_LowerRail_%d"), Side > 0 ? 1 : 0),
            BridgeCenter + BridgeTangent * Side * 225.0f + FVector(0.0f, 0.0f, 72.0f),
            BridgeRotation, FVector(74.0f, 0.10f, 0.10f), Steel);

        // A deterministic through-truss silhouette gives the procedural
        // crossing believable structure at guide-eye distance. It is context
        // infill only; labels and tags continue to prohibit navigational use.
        constexpr float HalfSpanCm = 3500.0f;
        constexpr float BayCm = 500.0f;
        for (int32 Bay = 0; Bay <= 14; ++Bay)
        {
            const float AlongCm = -HalfSpanCm + Bay * BayCm;
            const FVector PostCenter =
                BridgeCenter + BridgeNormal * AlongCm +
                BridgeTangent * Side * 225.0f + FVector(0.0f, 0.0f, 128.0f);
            AddInfrastructureCube(
                FString::Printf(
                    TEXT("RaftSim_ColomaBridge_TrussPost_%d_%02d"),
                    Side > 0 ? 1 : 0, Bay),
                PostCenter, BridgeRotation, FVector(0.09f, 0.09f, 1.28f), Steel);
            if (Bay < 14)
            {
                const bool bRises = (Bay % 2) == 0;
                const FVector BayStart =
                    BridgeCenter + BridgeNormal * AlongCm +
                    BridgeTangent * Side * 225.0f +
                    FVector(0.0f, 0.0f, bRises ? 48.0f : 202.0f);
                const FVector BayEnd =
                    BridgeCenter + BridgeNormal * (AlongCm + BayCm) +
                    BridgeTangent * Side * 225.0f +
                    FVector(0.0f, 0.0f, bRises ? 202.0f : 48.0f);
                AddInfrastructureBeam(
                    FString::Printf(
                        TEXT("RaftSim_ColomaBridge_TrussDiagonal_%d_%02d"),
                        Side > 0 ? 1 : 0, Bay),
                    BayStart, BayEnd, 12.0f, Steel);
            }
        }
    }
    for (float Lateral : {-24.0f, 0.0f, 24.0f})
    {
        const FVector2D PierWorldM = CoordinateWorldM(
            CoordinatePoints[BridgeIndex], Lateral);
        AddInfrastructureCube(
            FString::Printf(TEXT("RaftSim_ColomaBridge_Pier_%d"),
                FMath::RoundToInt(Lateral)),
            FVector(PierWorldM.X * 100.0f, PierWorldM.Y * 100.0f,
                BridgeWaterZCm + 250.0f),
            BridgeRotation, FVector(1.7f, 1.7f, 5.0f),
            Concrete ? Concrete : Steel);
    }
    struct FAccessSite
    {
        const TCHAR* Label;
        float StationM;
        float LateralM;
    };
    const FAccessSite AccessSites[] = {
        {TEXT("ChiliBarPutIn"), 0.0f, 58.0f},
        {TEXT("ColomaAccess"), 5200.0f, -62.0f},
        {TEXT("SalmonFallsTakeout"), 49077.732f, 54.0f}};
    for (const FAccessSite& Site : AccessSites)
    {
        const int32 SiteIndex = ClosestCoordinateIndex(CoordinatePoints, Site.StationM);
        const FVector SiteTangent = CoordinateTangent(CoordinatePoints, SiteIndex);
        const FVector2D SiteWorldM = CoordinateWorldM(
            CoordinatePoints[SiteIndex], Site.LateralM);
        const float SiteZCm = Metrics.MedianCenterWaterLocalZCm[SiteIndex] > -BIG_NUMBER * 0.5f
            ? Metrics.MedianCenterWaterLocalZCm[SiteIndex] + 130.0f
            : 500.0f;
        AddInfrastructureCube(
            FString::Printf(TEXT("RaftSim_%s_GravelRamp_Procedural"), Site.Label),
            FVector(SiteWorldM.X * 100.0f, SiteWorldM.Y * 100.0f, SiteZCm),
            SiteTangent.Rotation(), FVector(22.0f, 7.0f, 0.28f), Asphalt);
        AddInfrastructureCube(
            FString::Printf(TEXT("RaftSim_%s_SignPost_NotForNavigation"), Site.Label),
            FVector(
                (SiteWorldM.X + CoordinatePoints[SiteIndex].LeftNormal.X * 5.0f) * 100.0f,
                (SiteWorldM.Y + CoordinatePoints[SiteIndex].LeftNormal.Y * 5.0f) * 100.0f,
                SiteZCm + 160.0f),
            SiteTangent.Rotation(), FVector(0.14f, 0.14f, 3.2f), Timber);
    }

    if (!SaveFullReachWorld(World))
    {
        OutSummary += TEXT("Failed to save the full-reach gameplay map.\n");
        return false;
    }

    // A capture-only isolation switch makes visual regressions attributable
    // without changing the saved gameplay map. It is intentionally omitted
    // from normal builds and only hides far-field actors after the map save.
    const bool bDiagnosticHideFarField = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimDiagnosticHideSouthForkFarField"));
    const bool bDiagnosticHideWater = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimDiagnosticHideSouthForkWater"));
    TArray<TWeakObjectPtr<AActor>> DiagnosticHiddenActors;
    if (bDiagnosticHideFarField || bDiagnosticHideWater)
    {
        const FName FarFieldTag(TEXT("RaftSimFullReachFarField"));
        const FName FarFieldDressingTag(TEXT("RaftSimFullReachFarFieldDressing"));
        const FName MedianWaterTag(TEXT("RaftSimFlowBand_median_runnable"));
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            const bool bHideActor = Actor && (
                (bDiagnosticHideFarField &&
                    (Actor->ActorHasTag(FarFieldTag) ||
                     Actor->ActorHasTag(FarFieldDressingTag))) ||
                (bDiagnosticHideWater && Actor->ActorHasTag(MedianWaterTag)));
            if (bHideActor)
            {
                Actor->SetActorHiddenInGame(true);
                DiagnosticHiddenActors.Add(Actor);
            }
        }
        OutSummary += FString::Printf(
            TEXT("Capture diagnostic hid %d actors after map save (far field %s, water %s).\n"),
            DiagnosticHiddenActors.Num(),
            bDiagnosticHideFarField ? TEXT("yes") : TEXT("no"),
            bDiagnosticHideWater ? TEXT("yes") : TEXT("no"));
    }

    const struct FCaptureSpec
    {
        const TCHAR* Id;
        float StationM;
        float LateralM;
        float HeightM;
    } CaptureSpecs[] = {
        {TEXT("chili_bar_launch_downstream"), 120.0f, -4.0f, 2.4f},
        {TEXT("meat_grinder_guide_eye"), 920.0f, 1.0f, 2.0f},
        {TEXT("troublemaker_approach"), 8280.0f, -2.0f, 2.2f},
        {TEXT("coloma_bridge_context"), 5100.0f, 8.0f, 3.0f},
        {TEXT("salmon_falls_takeout"), 48940.0f, 2.0f, 2.5f}};
    TArray<FString> CapturePaths;
    bool bAllCapturesSaved = true;
    for (const FCaptureSpec& Spec : CaptureSpecs)
    {
        const int32 Index = ClosestCoordinateIndex(CoordinatePoints, Spec.StationM);
        const FVector2D WorldM = CoordinateWorldM(CoordinatePoints[Index], Spec.LateralM);
        const FVector Tangent = CoordinateTangent(CoordinatePoints, Index);
        const float SurfaceZCm = Metrics.MedianCenterWaterLocalZCm[Index] > -BIG_NUMBER * 0.5f
            ? Metrics.MedianCenterWaterLocalZCm[Index]
            : 500.0f;
        OutSummary += FString::Printf(
            TEXT("Capture diagnostic %s: station %.1f m, coordinate row %d, "
                 "world XY (%.1f, %.1f) m, decoded surface %.3f m absolute "
                 "(local Z %.1f cm).\n"),
            Spec.Id, Spec.StationM, Index, WorldM.X, WorldM.Y,
            VerticalDatumM + SurfaceZCm / 100.0f, SurfaceZCm);
        FString CapturePath;
        bAllCapturesSaved &= CaptureSouthForkView(
            World, Spec.Id,
            FVector(WorldM.X * 100.0f, WorldM.Y * 100.0f,
                SurfaceZCm + Spec.HeightM * 100.0f),
            FRotator(-5.0f, Tangent.Rotation().Yaw, 0.0f),
            CapturePath, OutSummary);
        CapturePaths.Add(CapturePath);
    }
    for (const TWeakObjectPtr<AActor>& Actor : DiagnosticHiddenActors)
    {
        if (Actor.IsValid())
        {
            Actor->SetActorHiddenInGame(false);
        }
    }

    TSharedRef<FJsonObject> BuildRoot = MakeShared<FJsonObject>();
    BuildRoot->SetStringField(
        TEXT("schema"), TEXT("raftsim.unreal.south_fork_full_reach_build.v1"));
    BuildRoot->SetStringField(TEXT("generated_on"), TEXT("2026-07-19"));
    BuildRoot->SetStringField(TEXT("map"), FullReachMapPackagePath);
    BuildRoot->SetBoolField(TEXT("world_partition"), World->GetWorldPartition() != nullptr);
    BuildRoot->SetBoolField(TEXT("nanite_terrain"), Metrics.TerrainTileCount == 13);
    BuildRoot->SetBoolField(TEXT("spatial_streaming_actors"), true);
    BuildRoot->SetBoolField(TEXT("moving_live_water_configured"), true);
    BuildRoot->SetBoolField(TEXT("source_conditioned_vertex_materials"), true);
    BuildRoot->SetBoolField(TEXT("wet_bank_material_response"), true);
    BuildRoot->SetBoolField(TEXT("three_flow_presentations"), Metrics.WaterTileCount == 39);
    BuildRoot->SetBoolField(TEXT("far_field_geography_complete"),
        Metrics.FarFieldPatchCount == 8);
    BuildRoot->SetBoolField(TEXT("detailed_mesh_reuse_requested"),
        bReuseExistingDetailedMeshes);
    BuildRoot->SetBoolField(TEXT("capture_set_complete"), bAllCapturesSaved);
    BuildRoot->SetBoolField(TEXT("hlod_generation_complete"), false);
    BuildRoot->SetStringField(
        TEXT("hlod_status"), TEXT("ready_for_WorldPartitionHLODsBuilder_commandlet"));
    BuildRoot->SetBoolField(TEXT("owner_art_and_readability_review_passed"), false);
    BuildRoot->SetStringField(
        TEXT("authority"),
        TEXT("authoritative sources where present; deterministic procedural infill explicitly labelled; not for navigation"));
    TSharedRef<FJsonObject> MetricRoot = MakeShared<FJsonObject>();
    MetricRoot->SetNumberField(TEXT("terrain_tiles"), Metrics.TerrainTileCount);
    MetricRoot->SetNumberField(TEXT("water_tiles"), Metrics.WaterTileCount);
    MetricRoot->SetNumberField(TEXT("far_field_patches"), Metrics.FarFieldPatchCount);
    MetricRoot->SetNumberField(TEXT("terrain_triangles"), Metrics.TerrainTriangleCount);
    MetricRoot->SetNumberField(TEXT("water_triangles"), Metrics.WaterTriangleCount);
    MetricRoot->SetNumberField(TEXT("far_field_triangles"), Metrics.FarFieldTriangleCount);
    MetricRoot->SetNumberField(TEXT("foliage_instances"), Metrics.FoliageInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("far_field_foliage_instances"), Metrics.FarFieldFoliageInstanceCount);
    MetricRoot->SetNumberField(TEXT("boulder_instances"), Metrics.BoulderInstanceCount);
    MetricRoot->SetNumberField(
        TEXT("scenic_noncolliding_bank_rock_instances"),
        Metrics.ScenicRockInstanceCount);
    MetricRoot->SetNumberField(TEXT("spray_mist_instances"), Metrics.SprayMistInstanceCount);
    MetricRoot->SetNumberField(TEXT("infrastructure_actors"), Metrics.InfrastructureActorCount);
    BuildRoot->SetObjectField(TEXT("metrics"), MetricRoot);
    TArray<TSharedPtr<FJsonValue>> CaptureJson;
    for (const FString& Path : CapturePaths)
    {
        CaptureJson.Add(MakeShared<FJsonValueString>(Path));
    }
    BuildRoot->SetArrayField(TEXT("captures"), CaptureJson);
    FString BuildText;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&BuildText);
    FJsonSerializer::Serialize(BuildRoot, Writer);
    BuildText += TEXT("\n");
    const FString BuildManifestAbsolute = AbsoluteRepoPath(BuildManifestRelativePath);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(BuildManifestAbsolute), true);
    const bool bBuildManifestSaved = FFileHelper::SaveStringToFile(
        BuildText, *BuildManifestAbsolute, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
    OutSummary += FString::Printf(
        TEXT("Full reach: %d terrain tiles, %d water tiles, %d foliage, %d boulders, "
             "%d spray/mist instances, %d infrastructure actors.\n"),
        Metrics.TerrainTileCount, Metrics.WaterTileCount,
        Metrics.FoliageInstanceCount, Metrics.BoulderInstanceCount,
        Metrics.SprayMistInstanceCount, Metrics.InfrastructureActorCount);
    return bAllCapturesSaved && bBuildManifestSaved;
}

} // namespace RaftSimEditorEnvironment

bool FRaftSimEditorModule::CreateSouthForkFullReachEnvironment(FString& OutSummary)
{
    return RaftSimEditorEnvironment::BuildSouthForkFullReachEnvironment(OutSummary);
}
