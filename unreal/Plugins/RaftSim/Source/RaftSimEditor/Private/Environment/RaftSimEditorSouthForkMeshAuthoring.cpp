#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "PhysicsEngine/BodySetup.h"
#include "UObject/SavePackage.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr TCHAR FullReachMapPackagePath[] =
    TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach");

FGuid SouthForkMeshActorGuid(UClass* ActorClass, const FString& Label)
{
    const FString StableKey = FString::Printf(
        TEXT("%s|%s|%s"),
        FullReachMapPackagePath,
        ActorClass ? *ActorClass->GetPathName() : TEXT("None"),
        *Label);
    return FGuid::NewDeterministicGuid(StableKey);
}

FName SouthForkMeshActorObjectName(UClass* ActorClass, const FString& Label)
{
    return FName(*FString::Printf(
        TEXT("RaftSim_%s"),
        *SouthForkMeshActorGuid(ActorClass, Label).ToString(EGuidFormats::Digits)));
}

AStaticMeshActor* SpawnStableSouthForkStaticMeshActor(
    UWorld* World,
    const FTransform& Transform,
    const FString& Label)
{
    if (!World)
    {
        return nullptr;
    }
    FActorSpawnParameters SpawnParameters;
    SpawnParameters.InitialActorLabel = Label;
    SpawnParameters.OverrideActorGuid =
        SouthForkMeshActorGuid(AStaticMeshActor::StaticClass(), Label);
    SpawnParameters.Name =
        SouthForkMeshActorObjectName(AStaticMeshActor::StaticClass(), Label);
    return World->SpawnActor<AStaticMeshActor>(
        AStaticMeshActor::StaticClass(), Transform, SpawnParameters);
}

void SetSouthForkMeshActorSpatiallyLoaded(AActor* Actor, bool bSpatiallyLoaded)
{
    if (Actor && Actor->CanChangeIsSpatiallyLoadedFlag())
    {
        Actor->SetIsSpatiallyLoaded(bSpatiallyLoaded);
    }
}
} // namespace

TArray<FProcMeshTangent> BuildSouthForkFlowTangents(
    const TArray<FVector>& Vertices,
    int32 Width,
    int32 Height)
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

UStaticMesh* CreateSouthForkMeshAsset(
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
    FString& OutSummary,
    bool bPreserveNaniteFallbackTopology)
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
        0,
        Vertices,
        Triangles,
        Normals,
        UVs,
        VertexColors,
        Tangents,
        bComplexCollision);
    // Far-field terrain remains non-colliding on its placed actor, but its
    // winding cutout requires a complete Nanite fallback. The shared native
    // converter retains that fallback for collision-enabled source geometry.
    Procedural->SetCollisionEnabled(
        (bComplexCollision || bPreserveNaniteFallbackTopology)
            ? ECollisionEnabled::QueryAndPhysics
            : ECollisionEnabled::NoCollision);
    Procedural->SetMaterial(0, Material);

    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor,
        AssetPackagePath,
        Material,
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
        if (!UPackage::SavePackage(
                Mesh->GetOutermost(), Mesh, *Filename, SaveArgs))
        {
            return nullptr;
        }
    }
    return Mesh;
}

AStaticMeshActor* PlaceSouthForkStaticMeshActor(
    UWorld* World,
    UStaticMesh* Mesh,
    UMaterialInterface* Material,
    const FString& Label,
    const FTransform& Transform,
    FName Tag,
    ECollisionEnabled::Type Collision)
{
    AStaticMeshActor* Actor =
        SpawnStableSouthForkStaticMeshActor(World, Transform, Label);
    if (!Actor)
    {
        return nullptr;
    }
    Actor->SetActorLabel(Label);
    Actor->Tags.AddUnique(Tag);
    SetSouthForkMeshActorSpatiallyLoaded(Actor, true);
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

void ConfigureSouthForkSingleLayerWaterActor(AStaticMeshActor* Actor)
{
    UStaticMeshComponent* Component = Actor
        ? Actor->GetStaticMeshComponent()
        : nullptr;
    if (!Component)
    {
        return;
    }
    // Single Layer Water uses an opaque render pass, but it is not an opaque
    // occluder; disabling the static-mesh shadow preserves riverbed lighting.
    Actor->Modify();
    Component->Modify();
    Component->SetCastShadow(false);
    Actor->MarkPackageDirty();
}

UStaticMesh* LoadSouthForkStaticMeshAsset(const FString& AssetPackagePath)
{
    const FString AssetName =
        FPackageName::GetLongPackageAssetName(AssetPackagePath);
    return LoadObject<UStaticMesh>(
        nullptr,
        *FString::Printf(TEXT("%s.%s"), *AssetPackagePath, *AssetName));
}

void LogStaticMeshVertexColorSummary(const FString& Label, UStaticMesh* Mesh)
{
    const FStaticMeshRenderData* RenderData = Mesh ? Mesh->GetRenderData() : nullptr;
    if (!RenderData || RenderData->LODResources.IsEmpty())
    {
        UE_LOG(LogTemp, Warning,
            TEXT("RaftSim color audit %s: no render data"), *Label);
        return;
    }
    const FColorVertexBuffer& Buffer =
        RenderData->LODResources[0].VertexBuffers.ColorVertexBuffer;
    const uint32 Count = Buffer.GetNumVertices();
    if (Count == 0)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("RaftSim color audit %s: no vertex colors"), *Label);
        return;
    }
    uint64 Red = 0;
    uint64 Green = 0;
    uint64 Blue = 0;
    uint64 Alpha = 0;
    uint8 MaximumAlpha = 0;
    const uint32 Step = FMath::Max<uint32>(Count / 1024, 1);
    uint32 Samples = 0;
    for (uint32 Index = 0; Index < Count; Index += Step)
    {
        const FColor Color = Buffer.VertexColor(Index);
        Red += Color.R;
        Green += Color.G;
        Blue += Color.B;
        Alpha += Color.A;
        MaximumAlpha = FMath::Max(MaximumAlpha, Color.A);
        ++Samples;
    }
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim color audit %s: vertices=%u sampled=%u "
             "mean_rgba=(%.1f,%.1f,%.1f,%.1f) max_alpha=%u"),
        *Label, Count, Samples,
        static_cast<double>(Red) / Samples,
        static_cast<double>(Green) / Samples,
        static_cast<double>(Blue) / Samples,
        static_cast<double>(Alpha) / Samples,
        MaximumAlpha);
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
        !RebuildAndValidateFirstPartyTexturePlatformData(
            Texture, Spec, OutSummary))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to build South Fork macro-albedo texture for %s.\n"),
            *TileId);
        return nullptr;
    }
    // Pin these small source-backed textures for the bounded automation window
    // so a freshly reopened map cannot capture before its first mip is resident.
    Texture->SetForceMipLevelsToBeResident(120.0f);
    Texture->WaitForStreaming();
    return Texture;
}
} // namespace RaftSimEditorEnvironment
