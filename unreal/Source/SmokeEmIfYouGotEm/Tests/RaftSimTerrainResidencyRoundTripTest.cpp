// Real-tick World Partition residency test, not a physical raft traversal.
// Only an ephemeral camera moves; no saved actors, player source settings,
// hydraulic state, terrain geometry or global streaming ranges are changed.
#include "Misc/AutomationTest.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "Camera/CameraActor.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "WorldPartition/WorldPartitionSubsystem.h"

#if WITH_AUTOMATION_TESTS
namespace
{
class FPairedTerrainRoundTrip final : public IAutomationLatentCommand
{
public:
    explicit FPairedTerrainRoundTrip(FAutomationTestBase* InTest) : Test(InTest) {}
    bool Update() override;
    ~FPairedTerrainRoundTrip() { RestoreView(); }
private:
    FAutomationTestBase* Test;
    TWeakObjectPtr<UWorld> World;
    TWeakObjectPtr<APlayerController> Player;
    TWeakObjectPtr<AActor> OriginalView;
    TWeakObjectPtr<ACameraActor> Camera;
    TWeakObjectPtr<AStaticMeshActor> Terrain;
    TWeakObjectPtr<UStaticMesh> Mesh;
    TWeakObjectPtr<UMaterialInterface> Material;
    FTransform TerrainTransform;
    FVector StartView;
    double WallStart=FPlatformTime::Seconds(),PhaseStart=0.;
    int32 Phase=0;
    TArray<TSharedPtr<FJsonValue>> Samples;
    void RestoreView()
    {
        if (Player.IsValid() && OriginalView.IsValid()) Player->SetViewTarget(OriginalView.Get());
        if (Camera.IsValid()) Camera->Destroy();
        Camera.Reset();
    }
    bool Fail(const TCHAR* Error) { Test->AddError(Error);RestoreView();return true; }
    bool Check(const TCHAR* Label,bool bAway);
};

bool FPairedTerrainRoundTrip::Check(const TCHAR* Label,bool bAway)
{
    auto* Partition=World->GetSubsystem<UWorldPartitionSubsystem>();
    auto* Actor=Terrain.Get();
    auto* Component=Actor ? Actor->GetStaticMeshComponent() : nullptr;
    if (!Partition || !Component || !Component->IsRegistered() ||
        Component->GetStaticMesh()!=Mesh.Get() || Component->GetMaterial(0)!=Material.Get() ||
        !Actor->GetActorTransform().Equals(TerrainTransform,.001) ||
        Component->GetCollisionEnabled()==ECollisionEnabled::NoCollision)
    { Test->AddError(TEXT("Revised original terrain actor, mesh, transform, material or collision residency changed"));return false; }
    int32 Revised=0,Original=0;
    for (TActorIterator<AStaticMeshActor> It(World.Get());It;++It)
    {
        const UStaticMesh* Current=It->GetStaticMeshComponent()->GetStaticMesh();
        if (Current==Mesh.Get()) ++Revised;
        if (Current && Current->GetName()==TEXT("SM_TroublemakerCapturedGround")) ++Original;
    }
    if (Revised!=1 || Original!=0)
    { Test->AddError(TEXT("Duplicate revised terrain or reloaded old terrain"));return false; }
    TArray<FWorldPartitionStreamingSource> PlayerSources,AllSources;
    Player->GetStreamingSources(PlayerSources);
    for (const auto* Provider:Partition->GetStreamingSourceProviders())
        Provider->GetStreamingSources(AllSources);
    bool bPlayerPosition=false,bResidency=false;
    const FVector ExpectedView=bAway ? StartView+FVector(1000000.,0.,0.) : StartView;
    for (const auto& Source:PlayerSources)
        bPlayerPosition|=FVector::Dist(Source.Location,ExpectedView)<100.;
    for (const auto& Source:AllSources)
        bResidency|=Source.Name==TEXT("RaftSimVerifiedTerrainResidency");
    if (!bPlayerPosition || !bResidency || !Partition->IsStreamingCompleted())
    { Test->AddError(TEXT("Actual player streaming location, retained provider or streaming completion not verified"));return false; }
    auto Row=MakeShared<FJsonObject>();
    Row->SetStringField(TEXT("phase"),Label);
    Row->SetNumberField(TEXT("world_seconds"),World->GetTimeSeconds());
    Row->SetStringField(TEXT("actor"),Actor->GetPathName());
    Row->SetStringField(TEXT("mesh"),Mesh->GetPathName());
    Row->SetNumberField(TEXT("player_source_count"),PlayerSources.Num());
    Row->SetNumberField(TEXT("registered_provider_source_count"),AllSources.Num());
    Row->SetNumberField(TEXT("view_distance_from_start_cm"),FVector::Dist(ExpectedView,StartView));
    Row->SetBoolField(TEXT("same_original_actor_mesh_transform_material_collision"),true);
    Row->SetBoolField(TEXT("streaming_completed"),true);
    Samples.Add(MakeShared<FJsonValueObject>(Row));
    UE_LOG(LogTemp,Display,TEXT("TERRAIN_RESIDENCY_ROUND_TRIP phase=%s world=%.6f view_distance_cm=%.3f same_actor=%s passed=true"),
        Label,World->GetTimeSeconds(),FVector::Dist(ExpectedView,StartView),*Actor->GetName());
    return true;
}

bool FPairedTerrainRoundTrip::Update()
{
    if (FPlatformTime::Seconds()-WallStart>300.) return Fail(TEXT("Terrain residency round trip exceeded 300 wall seconds"));
    if (!World.IsValid())
    {
        for (const auto& Context:GEngine->GetWorldContexts())
            if (Context.World() && Context.World()->IsGameWorld() &&
                Context.World()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")))
            { World=Context.World();break; }
        if (!World.IsValid()) return false;
    }
    if (!World->HasBegunPlay() || World->GetTimeSeconds()<10.) return false;
    if (Phase==0)
    {
        Player=World->GetFirstPlayerController();
        if (!Player.IsValid() || !Player->IsStreamingSourceEnabled()) return Fail(TEXT("Normal player streaming source required"));
        OriginalView=Player->GetViewTarget();
        FRotator Rotation;Player->GetPlayerViewPoint(StartView,Rotation);
        for (TActorIterator<AStaticMeshActor> It(World.Get());It;++It)
        {
            UStaticMesh* Current=It->GetStaticMeshComponent()->GetStaticMesh();
            if (Current && Current->GetName()==TEXT("SM_TroublemakerRevisedGround"))
            { Terrain=*It;Mesh=Current;Material=It->GetStaticMeshComponent()->GetMaterial(0);TerrainTransform=It->GetActorTransform();break; }
        }
        if (!Terrain.IsValid() || !OriginalView.IsValid()) return Fail(TEXT("Verified paired terrain and original view required"));
        FActorSpawnParameters Params;Params.ObjectFlags|=RF_Transient;
        Camera=World->SpawnActor<ACameraActor>(StartView,Rotation,Params);
        if (!Camera.IsValid()) return Fail(TEXT("Cannot create ephemeral streaming-view camera"));
        Player->SetViewTarget(Camera.Get());
        PhaseStart=World->GetTimeSeconds();Phase=1;return false;
    }
    if (World->GetTimeSeconds()-PhaseStart<5.) return false;
    World->BlockTillLevelStreamingCompleted();
    if (!Check(Phase==1 ? TEXT("initial") : Phase==2 ? TEXT("away_10km") : TEXT("returned"),Phase==2))
    { RestoreView();return true; }
    if (Phase<3)
    {
        Camera->SetActorLocation(Phase==1 ? StartView+FVector(1000000.,0.,0.) : StartView);
        PhaseStart=World->GetTimeSeconds();++Phase;return false;
    }
    FString Report;
    if (!FParse::Value(FCommandLine::Get(),TEXT("RaftSimTerrainRoundTripReport="),Report))
        return Fail(TEXT("Explicit fresh round-trip report path required"));
    if (FPaths::FileExists(Report)) return Fail(TEXT("Refusing to overwrite round-trip evidence"));
    auto Result=MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("schema"),TEXT("raftsim.terrain_residency_round_trip.v1"));
    Result->SetBoolField(TEXT("passed"),true);Result->SetArrayField(TEXT("samples"),Samples);
    Result->SetBoolField(TEXT("physical_raft_traversal"),false);
    Result->SetBoolField(TEXT("visual_acceptance"),false);
    Result->SetBoolField(TEXT("normal_project_dll_verified"),false);
    FString Json;FJsonSerializer::Serialize(Result,TJsonWriterFactory<>::Create(&Json));
    if (!FFileHelper::SaveStringToFile(Json,*Report)) return Fail(TEXT("Could not save round-trip evidence"));
    RestoreView();return true;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimTerrainResidencyRoundTripTest,
    "RaftSim.M3.TerrainResidencyRoundTrip",EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimTerrainResidencyRoundTripTest::RunTest(const FString&)
{
    FString Descriptor,Report;
    if (!FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")) ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimNativeTerrainPair="),Descriptor) ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimTerrainRoundTripReport="),Report))
    { AddError(TEXT("Explicit ephemeral paired native test and fresh report required"));return false; }
    ADD_LATENT_AUTOMATION_COMMAND(FPairedTerrainRoundTrip(this));return true;
}
#endif
