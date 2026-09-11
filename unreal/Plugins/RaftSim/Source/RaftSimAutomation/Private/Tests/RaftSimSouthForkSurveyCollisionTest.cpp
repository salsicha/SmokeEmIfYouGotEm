// Uses the real review mesh and the bridge's installed ground sampler.
// This is a contact regression, not full-route or visual acceptance.
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "CollisionQueryParams.h"
#include "UObject/UnrealType.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimRaftActor.h"
#include "RaftSimGuidePawn.h"
#include "GameFramework/PlayerController.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSouthForkSurveyCollisionTest,
    "RaftSim.Survey.SouthForkCapturedGroundContact",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimCheckCapturedGroundContact, FAutomationTestBase*, Test);

bool FRaftSimCheckCapturedGroundContact::Update()
{
    UWorld* World = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game)
        {
            World = Context.World();
            break;
        }
    }
    if (!World || !World->GetGameInstance())
    {
        Test->AddError(TEXT("No running survey review world"));
        return true;
    }
    UStaticMeshComponent* Ground = nullptr;
    int32 GroundOwners = 0;
    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        if (It->ActorHasTag(TEXT("RaftSimPhysicalGround")))
        {
            Ground = It->GetStaticMeshComponent();
            ++GroundOwners;
        }
    }
    URaftSimPhysicsBridgeSubsystem* Bridge = World->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    URaftSimChronoRuntimeAdapter* Adapter = Bridge ? Bridge->GetRaftRuntime() : nullptr;
    Test->TestEqual(TEXT("exactly one authoritative captured mesh"), GroundOwners, 1);
    if (!Ground || !Adapter)
    {
        Test->AddError(TEXT("Missing captured ground or live raft adapter"));
        return true;
    }

    ARaftSimRaftActor* Raft = nullptr;
    for (TActorIterator<ARaftSimRaftActor> It(World); It; ++It) { Raft = *It; break; }
    if (!Raft) { Test->AddError(TEXT("Missing survey raft")); return true; }
    APlayerController* Controller = World->GetFirstPlayerController();
    ARaftSimGuidePawn* Guide = Controller ? Cast<ARaftSimGuidePawn>(Controller->GetPawn()) : nullptr;
    Test->TestNotNull(TEXT("review player possesses the actual gameplay guide"), Guide);
    if (Guide)
    {
        Test->TestTrue(TEXT("guide is attached to the live raft"), Guide->GetAttachParentActor() == Raft);
        Test->TestTrue(TEXT("guide is above the local datum, not at underground world origin"), Guide->GetActorLocation().Z > 300.0);
    }
    const FRaftSimRaftKinematicState SavedState = Adapter->GetKinematicState();
    const FFloatProperty* LengthProperty = FindFProperty<FFloatProperty>(Raft->GetClass(), TEXT("FootprintLengthM"));
    const FFloatProperty* WidthProperty = FindFProperty<FFloatProperty>(Raft->GetClass(), TEXT("FootprintWidthM"));
    const FFloatProperty* RadiusProperty = FindFProperty<FFloatProperty>(Raft->GetClass(), TEXT("TubeRadiusM"));
    if (!LengthProperty || !WidthProperty || !RadiusProperty)
    {
        Test->AddError(TEXT("Cannot inspect the actual raft footprint"));
        return true;
    }
    const double HalfLength = LengthProperty->GetPropertyValue_InContainer(Raft) * 0.5;
    const double HalfWidth = WidthProperty->GetPropertyValue_InContainer(Raft) * 0.5;
    const double TubeRadiusM = RadiusProperty->GetPropertyValue_InContainer(Raft);
    const double EndX = FMath::Max(HalfLength - 0.3, 0.1);
    const double EndY = FMath::Max(HalfWidth - 0.15, 0.1);
    const TArray<FVector> Samples = {
        FVector(EndX,-EndY,0), FVector(EndX,EndY,0),
        FVector(0,-HalfWidth,0), FVector(0,HalfWidth,0),
        FVector(-EndX,-EndY,0), FVector(-EndX,EndY,0)};
    const FBox Bounds = Ground->Bounds.GetBox();
    auto GroundAt = [World, Ground, Bounds, Raft](const FVector& Point, float& Height)
    {
        FHitResult Hit;
        FCollisionQueryParams Params(SCENE_QUERY_STAT(RaftSimSurveyContactTest), true);
        Params.AddIgnoredActor(Raft);
        // Independently validate the bridge's component-query result against
        // the world's blocking collision query, not the same helper twice.
        if (!World->LineTraceSingleByChannel(Hit,
                FVector(Point.X,Point.Y,Bounds.Max.Z+100),
                FVector(Point.X,Point.Y,Bounds.Min.Z-100),ECC_WorldStatic,Params) ||
            !Hit.bBlockingHit || Hit.GetComponent() != Ground) return false;
        Height = Hit.ImpactPoint.Z;
        return true;
    };
    // Four original-return rock probes and one captured bank outside the
    // hydraulic window. Coordinates come from the imported mesh manifest.
    const TArray<FVector> Sites = {
        FVector(-9388.363,5130.241,763.881), FVector(-8938.363,3580.241,865.685),
        FVector(711.637,830.241,848.677), FVector(7561.637,-4419.759,1026.375),
        FVector(-11738.363,6280.241,811.574)};
    int32 ContactCases = 0;
    double WorstClearanceCm = 0.0;
    bool bFinite = true;
    int32 MissedGroundSamples = 0;
    for (const FVector& Site : Sites)
    {
        for (const double Yaw : {0.0, 90.0, 180.0, 270.0})
        {
            FRaftSimRaftKinematicState State;
            State.WorldTransform = FTransform(FRotator(0,Yaw,0), Site - FVector(0,0,75));
            State.LinearVelocityMetersPerSecond = FRotator(0,Yaw,0).Vector() * 3.0 + FVector(0,0,-2);
            Adapter->SetKinematicState(State);
            Adapter->ResetFlexiblePersistentState();
            bool bMadeContact = false;
            for (int32 Step = 0; Step < 120; ++Step)
            {
                bFinite &= Adapter->StepRaftDynamics(1.0f / 120.0f);
                const FRaftSimRaftKinematicState& Current = Adapter->GetKinematicState();
                bFinite &= Current.WorldTransform.IsValid() && !Current.LinearVelocityMetersPerSecond.ContainsNaN();
                bMadeContact |= Adapter->GetLastGroundedSupportPointCount() > 0;
                for (const FVector& Sample : Samples)
                {
                    const FVector Point = Current.WorldTransform.TransformPosition(Sample * 100.0);
                    float Height = 0;
                    if (!GroundAt(Point, Height)) { ++MissedGroundSamples; continue; }
                    WorstClearanceCm = FMath::Min(WorstClearanceCm,
                        Point.Z - TubeRadiusM * 100.0 - Height);
                }
            }
            ContactCases += bMadeContact ? 1 : 0;
        }
    }
    Adapter->SetKinematicState(SavedState);
    Adapter->ResetFlexiblePersistentState();
    Test->TestTrue(TEXT("all captured contact steps stay finite"), bFinite);
    Test->TestEqual(TEXT("all five sites and four headings make physical contact"), ContactCases, 20);
    Test->TestEqual(TEXT("all sampled tube points stay on captured geometry"), MissedGroundSamples, 0);
    Test->TestTrue(FString::Printf(TEXT("minimum tube clearance %.4f cm"), WorstClearanceCm), WorstClearanceCm >= -0.1);
    Test->AddInfo(FString::Printf(TEXT("Captured ground: %d/20 contact cases, 2400 substeps, minimum clearance %.4f cm"),
        ContactCases, WorstClearanceCm));
    return true;
}

bool FRaftSimSouthForkSurveyCollisionTest::RunTest(const FString&)
{
    if (!AutomationOpenMap(TEXT("/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable"))) return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimCheckCapturedGroundContact(this));
    return true;
}
#endif
