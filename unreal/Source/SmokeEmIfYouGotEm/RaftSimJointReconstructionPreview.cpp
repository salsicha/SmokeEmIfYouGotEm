#include "RaftSimJointReconstructionPreview.h"
#include "RaftSimLiveWaterWindow.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/StrongObjectPtr.h"

namespace RaftSimJointReconstructionPreview
{
bool IsAllowed(const FString& MapName, bool bEphemeralProfile, bool bEditorBuild)
{
    return bEditorBuild && bEphemeralProfile &&
        MapName.EndsWith(TEXT("L_SouthForkAmerican_FullReach"));
}

#if WITH_EDITOR && RAFTSIM_HAS_LIVE_SOLVER
namespace
{
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
    if (!String(Root,TEXT("schema"),TEXT("raftsim.south_fork_joint_preview.v1")) ||
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
        TEXT("mesh_file"),TEXT("material_file"),TEXT("geometry_manifest"),TEXT("atlas_manifest"),
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
    const auto Atlas=Read(Resolve(Files[TEXT("atlas_manifest")]));
    const auto Render=Read(Resolve(Files[TEXT("render_stage")]));
    const auto Collision=Read(Resolve(Files[TEXT("collision_audit")]));
    const auto Snapshot=Read(Resolve(Files[TEXT("snapshot_audit")]));
    const auto Banks=Read(Resolve(Files[TEXT("bank_audit")]));
    const auto Coverage=Read(Resolve(Files[TEXT("coverage_audit")]));
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
        !String(Snapshot,TEXT("input_manifest_sha256"),InputHash) || !String(Banks,TEXT("input_manifest_sha256"),InputHash) ||
        !Atlas->TryGetNumberField(TEXT("source_time_seconds"),AtlasTime) ||
        !Snapshot->TryGetNumberField(TEXT("time_seconds"),SnapshotTime) || FMath::Abs(AtlasTime-SnapshotTime)>1.e-9) return false;
    const TSharedPtr<FJsonObject>* Arrays=nullptr;const TSharedPtr<FJsonObject>* H=nullptr;
    FString DepthHash;
    if (!Atlas->TryGetObjectField(TEXT("arrays"),Arrays) || !(*Arrays)->TryGetObjectField(TEXT("h"),H) ||
        !(*H)->TryGetStringField(TEXT("sha256"),DepthHash) || !String(Banks,TEXT("h_sha256"),DepthHash)) return false;
    ARaftSimRiverWaterConfig* Config=nullptr;int32 Count=0;
    for (TActorIterator<ARaftSimRiverWaterConfig> It(World);It;++It) { Config=*It;++Count; }
    if (Count!=1 || !Config->bMapProvidesTerrain || !Config->bEnableMovingWindowStreaming) return false;
    for (TActorIterator<AStaticMeshActor> It(World);It;++It)
        if (It->Tags.Contains(TEXT("RaftSimJointReconstructionPreview"))) return false;
    UStaticMesh* Mesh=LoadObject<UStaticMesh>(nullptr,*MeshPath);
    UMaterialInterface* Material=LoadObject<UMaterialInterface>(nullptr,*MaterialPath);
    if (!Mesh || !Material) { Error=TEXT("Missing verified preview mesh/material");return false; }
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
    Actor->Tags.Add(TEXT("RaftSimPhysicalGround"));Actor->Tags.Add(TEXT("RaftSimJointReconstructionPreview"));
    Actor->SetActorLabel(TEXT("UNACCEPTED joint source-rock / water preview"));
    Config->CookedFieldsDir=FieldsDir;Config->StreamingManifestPath=Files[TEXT("streaming_manifest")];
    Config->CoordinateMapPath=Files[TEXT("coordinate_map")];Config->WindowCenterM=FVector2D(Center[0],Center[1]);
    Config->WindowExtentM=224.f;Config->MovingWindowStationExtentM=224.f;Config->MovingWindowLateralExtentM=224.f;
    Config->FlowBand=TEXT("median_runnable");Config->bRecenterHydraulicCrux=false;
    UE_LOG(LogTemp,Display,TEXT("RaftSim joint reconstruction preview installed before BeginPlay: cap=%s source_time=%.9f actor=%s streaming=%s candidate_only=true"),
        *CapHash,AtlasTime,*Actor->GetName(),*Config->StreamingManifestPath);
    Error.Reset();return true;
#else
    Error=TEXT("Joint reconstruction preview is unavailable outside editor live-solver builds");return false;
#endif
}
}
