#include "RaftSimJointReconstructionPreview.h"
#include "RaftSimLiveWaterWindow.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimGroundSourceLibrary.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "StaticMeshResources.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/StrongObjectPtr.h"
#include "WorldPartition/WorldPartitionStreamingSource.h"
#include "WorldPartition/WorldPartitionSubsystem.h"

namespace RaftSimJointReconstructionPreview
{
bool IsAllowed(const FString& MapName, bool bEphemeralProfile, bool bEditorBuild)
{
    return bEditorBuild && bEphemeralProfile &&
        MapName.EndsWith(TEXT("L_SouthForkAmerican_FullReach"));
}

bool HasFullTerrainFallback(const UStaticMesh* Mesh,int64 VerifiedTriangles)
{
    // The separately hash-verified collision source must also be the only
    // rendered fallback LOD. Never substitute a reduced proxy for that source.
    const FStaticMeshRenderData* Data=Mesh ? Mesh->GetRenderData() : nullptr;
    return VerifiedTriangles>0 && Data && Mesh->LODForCollision==0 &&
        Data->LODResources.Num()==1 && Data->LODResources[0].GetNumTriangles()==VerifiedTriangles;
}

bool MakeTerrainResidencySource(const FBox& WorldBounds,FWorldPartitionStreamingSource& Source)
{
    if (!WorldBounds.IsValid || WorldBounds.Min.ContainsNaN() || WorldBounds.Max.ContainsNaN()) return false;
    const FVector Extent=WorldBounds.GetExtent();
    const double Radius=Extent.Size2D()+1.;
    if (Extent.X<=0. || Extent.Y<=0. || !FMath::IsFinite(Radius) || Radius>MAX_flt) return false;
    Source=FWorldPartitionStreamingSource();
    Source.Name=TEXT("RaftSimVerifiedTerrainResidency");
    Source.Location=WorldBounds.GetCenter();
    Source.TargetState=EStreamingSourceTargetState::Activated;
    Source.bBlockOnSlowLoading=true;
    Source.bForce2D=true;
    FStreamingSourceShape Shape;
    Shape.bUseGridLoadingRange=false;
    Shape.Radius=static_cast<float>(Radius);
    Source.Shapes.Add(Shape);
    return true;
}

#if WITH_EDITOR && RAFTSIM_HAS_LIVE_SOLVER
namespace
{
// Runtime cell reloads would otherwise restore the saved old mesh. Retain the
// verified terrain footprint for this ephemeral world's entire lifetime; no
// saved actor, normal player streaming source, or global loading range changes.
class FTerrainResidency final : public IWorldPartitionStreamingSourceProvider
{
public:
    FTerrainResidency(UWorldPartitionSubsystem* InSubsystem,const FWorldPartitionStreamingSource& InSource)
        : Subsystem(InSubsystem),Source(InSource)
    { InSubsystem->RegisterStreamingSourceProvider(this); }
    ~FTerrainResidency()
    { if (auto* Value=Subsystem.Get()) Value->UnregisterStreamingSourceProvider(this); }
    bool GetStreamingSource(FWorldPartitionStreamingSource& OutSource) const override
    { OutSource=Source;return Subsystem.IsValid(); }
    const UObject* GetStreamingSourceOwner() const override { return Subsystem.Get(); }
private:
    TWeakObjectPtr<UWorldPartitionSubsystem> Subsystem;
    FWorldPartitionStreamingSource Source;
};

struct FTerrainResidencyRegistry
{
    TMap<TWeakObjectPtr<UWorld>,TUniquePtr<FTerrainResidency>> Sources;
    FDelegateHandle CleanupHandle;
    FTerrainResidencyRegistry()
    { CleanupHandle=FWorldDelegates::OnWorldCleanup.AddRaw(this,&FTerrainResidencyRegistry::Cleanup); }
    ~FTerrainResidencyRegistry()
    { FWorldDelegates::OnWorldCleanup.Remove(CleanupHandle);Sources.Empty(); }
    void Cleanup(UWorld* World,bool,bool) { Sources.Remove(World); }
};

FTerrainResidencyRegistry& TerrainResidencies()
{
    static FTerrainResidencyRegistry Registry;
    return Registry;
}

FString Resolve(const FString& Relative)
{
    if (Relative.IsEmpty() || !FPaths::IsRelative(Relative) || Relative.Contains(TEXT(".."))) return {};
    return FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("..")/Relative);
}

TSharedPtr<FJsonObject> Read(const FString& Path)
{
    FString Text; TSharedPtr<FJsonObject> Value;
    if (!FFileHelper::LoadFileToString(Text,*Path) ||
        !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Value)) return nullptr;
    return Value;
}

bool Flag(const TSharedPtr<FJsonObject>& Object,const TCHAR* Key,bool Expected)
{
    bool Value=false;
    return Object.IsValid() && Object->TryGetBoolField(Key,Value) && Value==Expected;
}

bool String(const TSharedPtr<FJsonObject>& Object,const TCHAR* Key,const FString& Expected)
{
    FString Value;
    return Object.IsValid() && Object->TryGetStringField(Key,Value) && Value==Expected;
}

bool Vector(const TSharedPtr<FJsonObject>& Object,const TCHAR* Key,TArray<double>& Result,int32 Count)
{
    const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
    if (!Object.IsValid() || !Object->TryGetArrayField(Key,Values) || Values->Num()!=Count) return false;
    Result.Reset();
    for (const auto& Value:*Values)
    {
        double Number=0.;
        if (!Value.IsValid() || !Value->TryGetNumber(Number) || !FMath::IsFinite(Number)) return false;
        Result.Add(Number);
    }
    return true;
}

bool NativeSourceMatches(UStaticMesh* Mesh,const TSharedPtr<FJsonObject>& Expected,double TriangleCount)
{
    if (!Mesh || !Expected.IsValid()) return false;
    const FString Text=URaftSimGroundSourceLibrary::AuditCollisionSource(Mesh);
    TSharedPtr<FJsonObject> Actual;FString Digest;double ActualCount=0.;
    return FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Actual) &&
        Flag(Actual,TEXT("available"),true) && Flag(Actual,TEXT("allow_cpu_access"),true) &&
        Expected->TryGetStringField(TEXT("collision_source_sha256"),Digest) && Digest.Len()==64 &&
        String(Actual,TEXT("collision_source_sha256"),Digest) &&
        Actual->TryGetNumberField(TEXT("triangle_count"),ActualCount) && ActualCount==TriangleCount;
}
}
#endif

bool Apply(UWorld* World,const FString& ManifestPath,bool bEphemeralProfile,FString& Error)
{
    Error=TEXT("Joint reconstruction preview requires the existing South Fork map, an editor build and an ephemeral profile");
    if (!World || !IsAllowed(World->GetMapName(),bEphemeralProfile,WITH_EDITOR!=0)) return false;
#if WITH_EDITOR && RAFTSIM_HAS_LIVE_SOLVER
    Error=TEXT("Invalid joint-preview manifest; nothing installed");
    const FString Resolved=Resolve(ManifestPath);
    const auto Root=Read(Resolved);
    const bool bTerrainRevision=String(Root,TEXT("schema"),TEXT("raftsim.south_fork_joint_preview.v2"));
    if ((!bTerrainRevision && !String(Root,TEXT("schema"),TEXT("raftsim.south_fork_joint_preview.v1"))) ||
        !Flag(Root,TEXT("candidate"),true) || !Flag(Root,TEXT("production_promoted"),false) ||
        !String(Root,TEXT("target_level"),TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"))) return false;
    const TSharedPtr<FJsonObject>* Dependencies=nullptr;
    if (!Root->TryGetObjectField(TEXT("dependencies"),Dependencies) || !Dependencies->IsValid()) return false;
    TMap<FString,FString> Hashes;
    for (const auto& Pair:(*Dependencies)->Values)
    {
        const FString Key(*Pair.Key);
        FString Expected;TArray<uint8> Bytes;const FString Path=Resolve(Key);
        if (Path.IsEmpty() || !Pair.Value->TryGetString(Expected) || Expected.Len()!=64 ||
            !FFileHelper::LoadFileToArray(Bytes,*Path) || RaftSimCookedArtifactSha256(Bytes)!=Expected)
        { Error=TEXT("Joint-preview dependency changed: ")+Key;return false; }
        Hashes.Add(Key,Expected);
    }
    TMap<FString,FString> Files;
    for (const TCHAR* Key:{TEXT("streaming_manifest"),TEXT("initial_fields_manifest"),TEXT("coordinate_map"),
        TEXT("mesh_file"),TEXT("material_file"),TEXT("geometry_manifest"),TEXT("flow_input_manifest"),TEXT("atlas_manifest"),
        TEXT("snapshot_audit"),TEXT("bank_audit"),TEXT("coverage_audit"),TEXT("render_stage"),TEXT("collision_audit")})
    {
        FString File;
        if (!Root->TryGetStringField(Key,File) || !Hashes.Contains(File)) return false;
        Files.Add(Key,File);
    }
    FString MeshPath,MaterialPath,CapHash;
    TArray<double> Translation,Scale,Center;
    if (!Root->TryGetStringField(TEXT("mesh_asset"),MeshPath) ||
        !Root->TryGetStringField(TEXT("material_asset"),MaterialPath) ||
        !Root->TryGetStringField(TEXT("source_cap_sha256"),CapHash) || CapHash.Len()!=64 ||
        !MeshPath.StartsWith(TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/")) ||
        MaterialPath!=TEXT("/Game/RaftSim/Environment/SouthForkReconstruction/FullReach/MI_SouthForkCompositeGround.MI_SouthForkCompositeGround") ||
        !Vector(Root,TEXT("translation_cm"),Translation,3) || !Vector(Root,TEXT("scale"),Scale,3) ||
        Scale[0]!=1. || Scale[1]!=-1. || Scale[2]!=1. || !Vector(Root,TEXT("window_center_m"),Center,2)) return false;
    const auto Geometry=Read(Resolve(Files[TEXT("geometry_manifest")]));
    const auto Input=Read(Resolve(Files[TEXT("flow_input_manifest")]));
    const auto Atlas=Read(Resolve(Files[TEXT("atlas_manifest")]));
    const auto Render=Read(Resolve(Files[TEXT("render_stage")]));
    const auto Collision=Read(Resolve(Files[TEXT("collision_audit")]));
    const auto Snapshot=Read(Resolve(Files[TEXT("snapshot_audit")]));
    const auto Banks=Read(Resolve(Files[TEXT("bank_audit")]));
    const auto Coverage=Read(Resolve(Files[TEXT("coverage_audit")]));
    if (!Geometry.IsValid() || Geometry->HasField(TEXT("terrain_revision"))!=bTerrainRevision) return false;
    const TSharedPtr<FJsonObject>* Union=nullptr;const TSharedPtr<FJsonObject>* AtlasUnion=nullptr;
    TArray<double> VerifiedTranslation;
    if (!Geometry.IsValid() || !Atlas.IsValid() || !Geometry->TryGetObjectField(TEXT("terrain_union"),Union) ||
        !Atlas->TryGetObjectField(TEXT("terrain_union"),AtlasUnion) || !String(*Union,TEXT("cap_sha256"),CapHash) ||
        !String(*AtlasUnion,TEXT("cap_sha256"),CapHash) || !String(Render,TEXT("source_cap_sha256"),CapHash) ||
        !String(Render,TEXT("mesh_asset"),MeshPath) || !String(Render,TEXT("material_asset"),MaterialPath) ||
        !String(Render,TEXT("mesh_sha256"),Hashes[Files[TEXT("mesh_file")]]) ||
        !String(Render,TEXT("material_sha256"),Hashes[Files[TEXT("material_file")]]) ||
        !Flag(Render,TEXT("world_position_offset"),false) ||
        !Vector(Render,TEXT("translation_cm"),VerifiedTranslation,3) || VerifiedTranslation!=Translation ||
        !String(Collision,TEXT("source_cap_sha256"),CapHash) || !Flag(Collision,TEXT("sampled_full_map_union_verified"),true) ||
        !Flag(Snapshot,TEXT("passed"),true) || !Flag(Banks,TEXT("all_artificial_banks_exactly_dry"),true) ||
        !Flag(Coverage,TEXT("passed"),true) ||
        !String(Coverage,TEXT("atlas_manifest_sha256"),Hashes[Files[TEXT("atlas_manifest")]]) ||
        !String(Coverage,TEXT("repaired_streaming_manifest_sha256"),Hashes[Files[TEXT("streaming_manifest")]])) return false;
    FString InputHash;double SnapshotTime=0.,AtlasTime=0.;
    if (!Atlas->TryGetStringField(TEXT("input_manifest_sha256"),InputHash) ||
        InputHash!=Hashes[Files[TEXT("flow_input_manifest")]] ||
        !String(Input,TEXT("geometry_manifest_sha256"),Hashes[Files[TEXT("geometry_manifest")]]) ||
        !String(Snapshot,TEXT("input_manifest_sha256"),InputHash) || !String(Banks,TEXT("input_manifest_sha256"),InputHash) ||
        !Atlas->TryGetNumberField(TEXT("source_time_seconds"),AtlasTime) ||
        !Snapshot->TryGetNumberField(TEXT("time_seconds"),SnapshotTime) || FMath::Abs(AtlasTime-SnapshotTime)>1.e-9) return false;
    const TSharedPtr<FJsonObject>* Arrays=nullptr;const TSharedPtr<FJsonObject>* SnapshotArrays=nullptr;
    if (!Atlas->TryGetObjectField(TEXT("arrays"),Arrays) || !Arrays->IsValid() ||
        !Snapshot->TryGetObjectField(TEXT("arrays"),SnapshotArrays) || !SnapshotArrays->IsValid()) return false;
    for (const TCHAR* Name:{TEXT("h"),TEXT("u"),TEXT("v")})
    {
        const TSharedPtr<FJsonObject>* Actual=nullptr;const TSharedPtr<FJsonObject>* Audited=nullptr;
        FString Digest;
        if (!(*Arrays)->TryGetObjectField(Name,Actual) || !Actual->IsValid() ||
            !(*SnapshotArrays)->TryGetObjectField(Name,Audited) ||
            !(*Actual)->TryGetStringField(TEXT("sha256"),Digest) || !String(*Audited,TEXT("sha256"),Digest)) return false;
        if (FString(Name)==TEXT("h") && !String(Banks,TEXT("h_sha256"),Digest)) return false;
    }
    // A valid but unrelated packet must not satisfy preflight by loading a
    // different atlas successfully. Bind the actual initial loader reference.
    const FString InitialPath=Resolve(Files[TEXT("initial_fields_manifest")]);
    const auto Initial=Read(InitialPath);
    const TArray<TSharedPtr<FJsonValue>>* Bands=nullptr;
    if (!Initial.IsValid() || !Initial->TryGetArrayField(TEXT("bands"),Bands) || Bands->Num()!=1) return false;
    const TSharedPtr<FJsonObject>* Band=nullptr;const TSharedPtr<FJsonObject>* Shared=nullptr;
    FString SharedFile;
    if (!(*Bands)[0]->TryGetObject(Band) || !String(*Band,TEXT("band_id"),TEXT("median_runnable")) ||
        !(*Band)->TryGetObjectField(TEXT("shared_cartesian_state"),Shared) || !Shared->IsValid() ||
        !String(*Shared,TEXT("sha256"),Hashes[Files[TEXT("atlas_manifest")]]) ||
        !(*Shared)->TryGetStringField(TEXT("manifest"),SharedFile) ||
        FPaths::ConvertRelativePathToFull(FPaths::GetPath(InitialPath)/SharedFile)!=Resolve(Files[TEXT("atlas_manifest")])) return false;
    ARaftSimRiverWaterConfig* Config=nullptr;int32 Count=0;
    for (TActorIterator<ARaftSimRiverWaterConfig> It(World);It;++It) { Config=*It;++Count; }
    if (Count!=1 || !Config->bMapProvidesTerrain || !Config->bEnableMovingWindowStreaming) return false;
    for (TActorIterator<AStaticMeshActor> It(World);It;++It)
        if (It->Tags.Contains(TEXT("RaftSimJointReconstructionPreview"))) return false;
    UStaticMesh* Mesh=LoadObject<UStaticMesh>(nullptr,*MeshPath);
    UMaterialInterface* Material=LoadObject<UMaterialInterface>(nullptr,*MaterialPath);
    if (!Mesh || !Material) { Error=TEXT("Missing verified preview mesh/material");return false; }
    AStaticMeshActor* TerrainActor=nullptr;UStaticMesh* RevisedTerrain=nullptr;
    TUniquePtr<FTerrainResidency> TerrainResidency;
    if (bTerrainRevision)
    {
        const TSharedPtr<FJsonObject>* Terrain=nullptr;
        const TSharedPtr<FJsonObject>* Revision=nullptr;const TSharedPtr<FJsonObject>* SourceRevision=nullptr;
        const TSharedPtr<FJsonObject>* AtlasRevision=nullptr;const TSharedPtr<FJsonObject>* OriginalSource=nullptr;
        const TSharedPtr<FJsonObject>* RevisedSource=nullptr;const TSharedPtr<FJsonObject>* Proof=nullptr;
        FString RevisedPath,RevisedFile,RevisedHash,OriginalHash,SourceHash,OriginalSourceHash;
        double Triangles=0.,Compared=0.;TArray<double> TerrainTranslation,TerrainScale;
        const FString OriginalPath=TEXT("/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround");
        const FString OriginalFile=TEXT("unreal/Content/")+OriginalPath.RightChop(6)+TEXT(".uasset");
        if (!Collision->TryGetObjectField(TEXT("terrain_replacement"),Terrain) || !Terrain->IsValid() ||
            !Flag(*Terrain,TEXT("saved_mesh_verified"),true) ||
            !Flag(*Terrain,TEXT("original_actor_reused"),true) ||
            !Flag(*Terrain,TEXT("second_ground_actor_added"),false) ||
            !Flag(*Terrain,TEXT("original_material_preserved"),true) ||
            !String(*Terrain,TEXT("original_mesh_asset"),OriginalPath) ||
            !String(*Terrain,TEXT("material_asset"),MaterialPath) ||
            !(*Terrain)->TryGetStringField(TEXT("mesh_asset"),RevisedPath) ||
            !RevisedPath.StartsWith(TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/")) ||
            !(*Terrain)->TryGetStringField(TEXT("mesh_file"),RevisedFile) ||
            RevisedFile!=TEXT("unreal/Content/")+RevisedPath.RightChop(6)+TEXT(".uasset") ||
            !(*Terrain)->TryGetStringField(TEXT("mesh_sha256"),RevisedHash) ||
            !(*Terrain)->TryGetStringField(TEXT("original_mesh_sha256"),OriginalHash) ||
            !Hashes.Contains(RevisedFile) || Hashes[RevisedFile]!=RevisedHash ||
            !Hashes.Contains(OriginalFile) || Hashes[OriginalFile]!=OriginalHash ||
            !Vector(*Terrain,TEXT("translation_cm"),TerrainTranslation,3) || TerrainTranslation!=Translation ||
            !Vector(*Terrain,TEXT("scale"),TerrainScale,3) || TerrainScale!=Scale ||
            !Geometry->TryGetObjectField(TEXT("terrain_revision"),Revision) || !Revision->IsValid() ||
            !(*Terrain)->TryGetObjectField(TEXT("source_revision"),SourceRevision) ||
            !(*AtlasUnion)->TryGetObjectField(TEXT("terrain_revision"),AtlasRevision) ||
            !(*Revision)->TryGetStringField(TEXT("revised_geometry_sha256"),SourceHash) ||
            !(*Revision)->TryGetStringField(TEXT("original_geometry_sha256"),OriginalSourceHash) ||
            !String(*SourceRevision,TEXT("revised_geometry_sha256"),SourceHash) ||
            !String(*SourceRevision,TEXT("original_geometry_sha256"),OriginalSourceHash) ||
            !String(*AtlasRevision,TEXT("revised_geometry_sha256"),SourceHash) ||
            !String(*AtlasRevision,TEXT("original_geometry_sha256"),OriginalSourceHash) ||
            !(*Terrain)->TryGetObjectField(TEXT("original_native_source"),OriginalSource) ||
            !(*Terrain)->TryGetObjectField(TEXT("revised_native_source"),RevisedSource) ||
            !(*Terrain)->TryGetNumberField(TEXT("triangle_count"),Triangles) || Triangles<=0. ||
            !(*Terrain)->TryGetObjectField(TEXT("exact_native_replacement"),Proof) || !Proof->IsValid() ||
            !Flag(*Proof,TEXT("unmodified_native_corners_bit_exact"),true) ||
            !Flag(*Proof,TEXT("registered_xy_and_winding_bit_exact"),true) ||
            !(*Proof)->TryGetNumberField(TEXT("all_directed_triangles_compared"),Compared) || Compared!=Triangles)
        { Error=TEXT("Missing or inconsistent source-matched terrain replacement");return false; }
        UStaticMesh* OriginalTerrain=LoadObject<UStaticMesh>(nullptr,*OriginalPath);
        RevisedTerrain=LoadObject<UStaticMesh>(nullptr,*RevisedPath);
        if (!NativeSourceMatches(OriginalTerrain,*OriginalSource,Triangles) ||
            !NativeSourceMatches(RevisedTerrain,*RevisedSource,Triangles))
        { Error=TEXT("Native terrain source differs from verified collision geometry");return false; }
        if (Triangles>double(MAX_int32) || Triangles!=FMath::FloorToDouble(Triangles) ||
            !HasFullTerrainFallback(RevisedTerrain,static_cast<int64>(Triangles)))
        { Error=TEXT("Verified terrain lacks its complete collision-matched render fallback");return false; }
        if (World->HasBegunPlay() || !World->IsGameWorld() || !World->GetWorldPartition() ||
            TerrainResidencies().Sources.Contains(World))
        { Error=TEXT("Paired terrain residency must be established once before game BeginPlay");return false; }
        const FTransform Expected(FQuat::Identity,FVector(Translation[0],Translation[1],Translation[2]),FVector(1.,-1.,1.));
        FWorldPartitionStreamingSource ResidencySource;
        auto* Partition=World->GetSubsystem<UWorldPartitionSubsystem>();
        if (!Partition || !MakeTerrainResidencySource(OriginalTerrain->GetBoundingBox().TransformBy(Expected),ResidencySource))
        { Error=TEXT("Verified terrain has no valid streaming footprint");return false; }
        TerrainResidency=MakeUnique<FTerrainResidency>(Partition,ResidencySource);
        World->BlockTillLevelStreamingCompleted();
        if (World->HasBegunPlay() || !Partition->IsStreamingCompleted(TerrainResidency.Get()))
        { Error=TEXT("Verified terrain streaming did not complete before paired activation");return false; }
        int32 TerrainCount=0;
        for (TActorIterator<AStaticMeshActor> It(World);It;++It)
        {
            if (It->Tags.Contains(TEXT("RaftSimPhysicalGround")) && It->GetStaticMeshComponent()->GetStaticMesh()==OriginalTerrain)
            { TerrainActor=*It;++TerrainCount; }
        }
        if (TerrainCount!=1 || !TerrainActor->GetActorTransform().Equals(Expected,.001) ||
            TerrainActor->GetStaticMeshComponent()->GetMaterial(0)!=Material)
        { Error=TEXT("Verified original rapid actor must be loaded before paired terrain/water activation");return false; }
        UE_LOG(LogTemp,Display,TEXT("RaftSim verified terrain resident before BeginPlay: actor=%s source_center_cm=%s radius_cm=%.3f; normal player streaming unchanged"),
            *TerrainActor->GetName(),*ResidencySource.Location.ToCompactString(),ResidencySource.Shapes[0].Radius);
    }
    // Exercise the real loader before touching the saved-map configuration.
    TStrongObjectPtr<URaftSimWaterRuntimeAdapter> Trial(NewObject<URaftSimWaterRuntimeAdapter>());
    FRaftSimWaterRuntimeConfig Runtime;Runtime.bRequireAcceptedReportManifest=false;
    Runtime.bEnableDeterministicCapture=false;Trial->Configure(Runtime);
    const FString FieldsDir=FPaths::GetPath(Files[TEXT("initial_fields_manifest")]);
    if (!Trial->ConfigureRiverCoordinateMap(Files[TEXT("coordinate_map")]) ||
        !Trial->ConfigureMovingRiverWindow(FieldsDir,TEXT("median_runnable"),FVector2D(Center[0],Center[1]),FVector2D(224.,224.),.035f))
    { Error=TEXT("Joint-preview source-matched native window refused to load");return false; }
    FActorSpawnParameters Params;Params.ObjectFlags|=RF_Transient;
    Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    const FTransform Transform(FQuat::Identity,FVector(Translation[0],Translation[1],Translation[2]),FVector(1.,-1.,1.));
    auto* Actor=World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(),Transform,Params);
    if (!Actor) { Error=TEXT("Could not create joint-preview source solid");return false; }
    auto* Component=Actor->GetStaticMeshComponent();
    if (!Component->SetStaticMesh(Mesh)) { Actor->Destroy();return false; }
    Component->SetMaterial(0,Material);Component->SetCollisionProfileName(TEXT("BlockAll"));
    if (TerrainActor && !TerrainActor->GetStaticMeshComponent()->SetStaticMesh(RevisedTerrain))
    { Actor->Destroy();Error=TEXT("Could not replace original terrain; paired water not installed");return false; }
    if (TerrainActor)
    {
        // The normal-map fix is scoped to the original asset name, so it
        // cannot recognize this ephemeral, hash-verified replacement. Preserve
        // its exact-source rendering policy here, without broadening that rule
        // to arbitrary GeneratedLocalReview assets or changing saved packages.
        auto* TerrainComponent=TerrainActor->GetStaticMeshComponent();
        TerrainComponent->bDisallowNanite=true;
        TerrainComponent->MarkRenderStateDirty();
        UE_LOG(LogTemp,Display,TEXT("RaftSim verified replacement exact fallback enabled: mesh=%s triangles=%u"),
            *RevisedTerrain->GetPathName(),RevisedTerrain->GetRenderData()->LODResources[0].GetNumTriangles());
    }
    Actor->Tags.Add(TEXT("RaftSimPhysicalGround"));Actor->Tags.Add(TEXT("RaftSimJointReconstructionPreview"));
    Actor->SetActorLabel(TEXT("UNACCEPTED joint source-rock / water preview"));
    Config->CookedFieldsDir=FieldsDir;Config->StreamingManifestPath=Files[TEXT("streaming_manifest")];
    Config->CoordinateMapPath=Files[TEXT("coordinate_map")];Config->WindowCenterM=FVector2D(Center[0],Center[1]);
    Config->WindowExtentM=224.f;Config->MovingWindowStationExtentM=224.f;Config->MovingWindowLateralExtentM=224.f;
    Config->FlowBand=TEXT("median_runnable");Config->bRecenterHydraulicCrux=false;
    if (TerrainResidency) TerrainResidencies().Sources.Add(World,MoveTemp(TerrainResidency));
    if (TerrainActor)
        UE_LOG(LogTemp,Display,TEXT("RaftSim verified terrain replacement installed on original actor=%s mesh=%s before paired water BeginPlay"),
            *TerrainActor->GetName(),*RevisedTerrain->GetPathName());
    UE_LOG(LogTemp,Display,TEXT("RaftSim joint reconstruction preview installed before BeginPlay: cap=%s source_time=%.9f actor=%s streaming=%s candidate_only=true"),
        *CapHash,AtlasTime,*Actor->GetName(),*Config->StreamingManifestPath);
    Error.Reset();return true;
#else
    Error=TEXT("Joint reconstruction preview is unavailable outside editor live-solver builds");return false;
#endif
}
}
