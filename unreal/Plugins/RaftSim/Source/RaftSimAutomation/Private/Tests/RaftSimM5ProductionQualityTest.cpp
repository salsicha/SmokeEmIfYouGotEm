#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimCrewStateContracts.h"
#include "RaftSimGuidePawn.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRaftCondition.h"
#include "RaftSimRaftMesh.h"
#include "Tests/AutomationCommon.h"
#include "UnrealClient.h"

#if WITH_AUTOMATION_TESTS

namespace
{
bool PoseIsFinite(const FRaftSimCrewAvatarPose& Pose)
{
    return !Pose.TorsoCenterCm.ContainsNaN() && !Pose.HeadCenterCm.ContainsNaN() &&
        !Pose.LeftHandCm.ContainsNaN() && !Pose.RightHandCm.ContainsNaN() &&
        !Pose.LeftFootCm.ContainsNaN() && !Pose.RightFootCm.ContainsNaN() &&
        !Pose.PaddleTopCm.ContainsNaN() && !Pose.PaddleBottomCm.ContainsNaN();
}

float RingPolygonArea(const TArray<FVector>& Vertices, int32 Start, int32 Count)
{
    FVector AreaVector = FVector::ZeroVector;
    for (int32 Index = 0; Index < Count; ++Index)
    {
        const FVector& A = Vertices[Start + Index];
        const FVector& B = Vertices[Start + (Index + 1) % Count];
        AreaVector += FVector::CrossProduct(A, B);
    }
    return 0.5f * AreaVector.Size();
}

UWorld* GetM5GameWorld()
{
    UWorld* Newest = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (Context.World() &&
            (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
        {
            Newest = Context.World();
        }
    }
    return Newest;
}

ARaftSimRaftActor* FindM5Raft()
{
    if (UWorld* World = GetM5GameWorld())
    {
        if (TActorIterator<ARaftSimRaftActor> It(World); It)
        {
            return *It;
        }
    }
    return nullptr;
}

ARaftSimGuidePawn* FindM5Guide()
{
    if (UWorld* World = GetM5GameWorld())
    {
        if (TActorIterator<ARaftSimGuidePawn> It(World); It)
        {
            return *It;
        }
    }
    return nullptr;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM5CrewAvatarPoseTest,
    "RaftSim.M5.CrewAvatarPoseProduction",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM5CrewAvatarPoseTest::RunTest(const FString&)
{
    constexpr int32 ActionCount = static_cast<int32>(ERaftSimCrewAvatarAction::Reentry) + 1;
    TSet<FString> PoseFingerprints;
    for (int32 ActionIndex = 0; ActionIndex < ActionCount; ++ActionIndex)
    {
        const ERaftSimCrewAvatarAction Action =
            static_cast<ERaftSimCrewAvatarAction>(ActionIndex);
        const FRaftSimCrewAvatarPose Pose =
            URaftSimCrewAvatarPoseLibrary::EvaluatePose(Action, 0.31f, -1);
        TestTrue(
            FString::Printf(TEXT("action %d pose is finite"), ActionIndex),
            PoseIsFinite(Pose));
        PoseFingerprints.Add(FString::Printf(
            TEXT("%.1f|%.1f|%.1f|%.1f|%.1f|%d"),
            Pose.TorsoCenterCm.X,
            Pose.TorsoCenterCm.Y,
            Pose.TorsoRotation.Pitch,
            Pose.LeftHandCm.X,
            Pose.RightHandCm.Y,
            Pose.bShowPaddle ? 1 : 0));
    }
    TestTrue(TEXT("animation library exposes distinct production poses"), PoseFingerprints.Num() >= 9);

    const FRaftSimCrewAvatarPose Swim = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::Swimming, 0.25f, 1);
    const FRaftSimCrewAvatarPose HighSide = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::HighSidePort, 0.25f, 1);
    TestFalse(TEXT("swimming hides the paddle"), Swim.bShowPaddle);
    TestTrue(TEXT("high-side visibly shifts the torso"), FMath::Abs(HighSide.TorsoCenterCm.Y) > 25.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM5AimedRescueTest,
    "RaftSim.M5.AimedRescuePaths",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM5AimedRescueTest::RunTest(const FString&)
{
    const FRaftSimSwimmingSkillProfile Skill =
        URaftSimSwimmingSkillLibrary::MakeSwimmingSkillProfile(
            ERaftSimSwimmingSkillLevel::AverageSwimmer);
    const FVector Start(0.0f, 0.0f, 0.0f);
    const FVector Target(5.0f, 0.0f, 0.0f);
    FRaftSimRescueInteractionState State =
        URaftSimSwimmerRescueLibrary::BeginRescueInteraction(
            TEXT("paddler_1"),
            ERaftSimRescueMethod::ThrowLine,
            Start,
            Target,
            FVector::ForwardVector,
            true,
            4.0f,
            Skill);
    TestEqual(
        TEXT("aligned throw enters flight"),
        static_cast<int32>(State.Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::LineInFlight));
    TestTrue(TEXT("throw line is visible"), State.bLineVisible);

    for (int32 Step = 0; Step < 28; ++Step)
    {
        State = URaftSimSwimmerRescueLibrary::AdvanceRescueInteraction(
            State, Start, Target, 0.25f);
    }
    TestEqual(
        TEXT("elapsed-time pull reaches re-entry"),
        static_cast<int32>(State.Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::ReadyForReentry));
    State = URaftSimSwimmerRescueLibrary::CompleteReseat(State, 0.9f);
    TestEqual(
        TEXT("tube-side reseat completes"),
        static_cast<int32>(State.Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::Completed));
    TestFalse(TEXT("line is stowed after reseat"), State.bLineVisible);

    auto TestContactRescue = [this, &Skill, &Start](
        const TCHAR* Label,
        ERaftSimRescueMethod Method,
        float DistanceM,
        int32 PullSteps)
    {
        FRaftSimRescueInteractionState ContactState =
            URaftSimSwimmerRescueLibrary::BeginRescueInteraction(
                TEXT("paddler_contact"), Method, Start, FVector(DistanceM, 0.0f, 0.0f),
                FVector::ForwardVector, true, 2.0f, Skill);
        TestEqual(
            FString::Printf(TEXT("%s establishes contact"), Label),
            static_cast<int32>(ContactState.Phase),
            static_cast<int32>(ERaftSimRescueInteractionPhase::Pulling));
        for (int32 Step = 0; Step < PullSteps; ++Step)
        {
            ContactState = URaftSimSwimmerRescueLibrary::AdvanceRescueInteraction(
                ContactState, Start, FVector(DistanceM, 0.0f, 0.0f), 0.25f);
        }
        TestEqual(
            FString::Printf(TEXT("%s completes its calibrated pull"), Label),
            static_cast<int32>(ContactState.Phase),
            static_cast<int32>(ERaftSimRescueInteractionPhase::ReadyForReentry));
    };
    TestContactRescue(TEXT("reach grab"), ERaftSimRescueMethod::ReachGrab, 1.0f, 10);
    TestContactRescue(TEXT("paddle grab"), ERaftSimRescueMethod::PaddleGrab, 1.8f, 14);

    const FRaftSimRescueInteractionState BadAim =
        URaftSimSwimmerRescueLibrary::BeginRescueInteraction(
            TEXT("paddler_1"), ERaftSimRescueMethod::ThrowLine,
            Start, Target, -FVector::ForwardVector, true, 4.0f, Skill);
    TestEqual(
        TEXT("bad throw remains in aiming feedback"),
        static_cast<int32>(BadAim.Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::Aiming));
    const FRaftSimRescueInteractionState OutOfRange =
        URaftSimSwimmerRescueLibrary::BeginRescueInteraction(
            TEXT("paddler_1"), ERaftSimRescueMethod::PaddleGrab,
            Start, Target, FVector::ForwardVector, true, 4.0f, Skill);
    TestEqual(
        TEXT("paddle grab enforces its physical reach"),
        static_cast<int32>(OutOfRange.Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::Failed));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM5FlexibleFabricConditionTest,
    "RaftSim.M5.FlexibleFabricCondition",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM5FlexibleFabricConditionTest::RunTest(const FString&)
{
    FRaftSimFlexVisualSegmentState Contact;
    Contact.SegmentId = TEXT("port_mid_wrap");
    Contact.LocalPositionM = FVector(0.6f, -0.72f, 0.28f);
    Contact.ContactNormalLocal = FVector(0.0f, 1.0f, 0.0f);
    Contact.CompressionM = 0.07;
    Contact.IndentationM = 0.14;
    Contact.FreeboardLossM = 0.05;
    Contact.bWrapping = true;
    Contact.bPinned = true;

    RaftSimRaftMesh::FMeshData RestTubes, RestFloor, BentTubes, BentFloor;
    RaftSimRaftMesh::BuildInflatableRaft(4.3f, 2.0f, 0.28f, RestTubes, RestFloor);
    RaftSimRaftMesh::BuildInflatableRaft(
        4.3f, 2.0f, 0.28f, BentTubes, BentFloor, {Contact});
    TestEqual(TEXT("tube topology remains stable"), BentTubes.Vertices.Num(), RestTubes.Vertices.Num());
    TestEqual(TEXT("floor topology remains stable"), BentFloor.Vertices.Num(), RestFloor.Vertices.Num());

    float MaxTubeMove = 0.0f;
    float MaxThwartMove = 0.0f;
    float MaxFloorMove = 0.0f;
    bool bFinite = true;
    for (int32 Index = 0; Index < RestTubes.Vertices.Num(); ++Index)
    {
        bFinite &= !BentTubes.Vertices[Index].ContainsNaN();
        const float Move = FVector::Distance(RestTubes.Vertices[Index], BentTubes.Vertices[Index]);
        MaxTubeMove = FMath::Max(MaxTubeMove, Move);
        if (Index >= RestTubes.Vertices.Num() - 220)
        {
            MaxThwartMove = FMath::Max(MaxThwartMove, Move);
        }
    }
    for (int32 Index = 0; Index < RestFloor.Vertices.Num(); ++Index)
    {
        bFinite &= !BentFloor.Vertices[Index].ContainsNaN();
        MaxFloorMove = FMath::Max(
            MaxFloorMove,
            FVector::Distance(RestFloor.Vertices[Index], BentFloor.Vertices[Index]));
    }
    TestTrue(TEXT("deformed fabric remains finite"), bFinite);
    TestTrue(TEXT("wrap creates a visible tube fold"), MaxTubeMove > 8.0f);
    TestTrue(TEXT("thwarts couple to the fold"), MaxThwartMove > 0.5f);
    TestTrue(TEXT("floor couples to the fold"), MaxFloorMove > 0.5f);

    // The first swept ring has fourteen vertices. Reciprocal contact axes
    // preserve its polygonal cross-sectional area within discretization error.
    const float RestArea = RingPolygonArea(RestTubes.Vertices, 0, 14);
    const float BentArea = RingPolygonArea(BentTubes.Vertices, 0, 14);
    TestTrue(
        FString::Printf(TEXT("inflated cross-section conserves area (ratio %.3f)"), BentArea / RestArea),
        FMath::Abs(BentArea / RestArea - 1.0f) < 0.06f);

    FRaftSimRaftConditionState Condition;
    FRaftSimRaftContactExposure Exposure;
    Exposure.DeltaSeconds = 0.25f;
    Exposure.MaximumIndentationM = 0.18f;
    Exposure.ContactCount = 5;
    Exposure.WrappingContactCount = 4;
    Exposure.PinnedObstacleCount = 1;
    for (int32 Step = 0; Step < 48; ++Step)
    {
        Condition = URaftSimRaftConditionLibrary::AdvanceCondition(Condition, Exposure);
    }
    TestTrue(TEXT("sustained pin damages fabric"), Condition.FabricIntegrity < 0.75f);
    TestTrue(TEXT("sustained deep pin leaks pressure"), Condition.PressureFraction < 0.90f);
    TestTrue(TEXT("wrap event is edge-counted once"), Condition.WrapEventCount == 1);
    TestTrue(
        TEXT("condition advances to punctured or critical"),
        Condition.DamageState == ERaftSimRaftDamageState::Punctured ||
            Condition.DamageState == ERaftSimRaftDamageState::Critical);
    const FRaftSimRaftConditionState Repaired =
        URaftSimRaftConditionLibrary::ApplyCheckpointRepair(Condition);
    TestEqual(TEXT("field repair restores nominal pressure"), Repaired.PressureFraction, 1.0f);
    TestTrue(TEXT("field repair preserves the crease history"),
             Repaired.PermanentCreaseAmplitudeM > 0.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM5RuntimeRescueLoopTest,
    "RaftSim.M5.RuntimeRescueLoop",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM5StartRescueCommand, FAutomationTestBase*, Test);
bool FRaftSimM5StartRescueCommand::Update()
{
    ARaftSimRaftActor* Raft = FindM5Raft();
    if (!Raft)
    {
        Test->AddError(TEXT("M5 test tank has no raft"));
        return true;
    }
    Test->TestEqual(TEXT("five procedural crew avatars spawned"), Raft->GetCrewAvatarCount(), 5);
    Test->TestFalse(TEXT("raft orientation is finite before rescue"),
                    Raft->GetActorQuat().ContainsNaN());
    Test->TestFalse(TEXT("raft position is finite before rescue"),
                    Raft->GetActorLocation().ContainsNaN());
    ARaftSimGuidePawn* Guide = FindM5Guide();
    Test->TestNotNull(TEXT("test tank has guide pawn"), Guide);
    if (Guide)
    {
        Test->TestTrue(TEXT("shipping rescue input bindings are complete"),
                       Guide->HasCompleteRescueInputBindings());
    }
    Raft->ForceCrewOverboardForTesting(1);
    FVector TargetCm;
    if (!Raft->GetSwimmerWorldPosition(TEXT("paddler_1"), TargetCm))
    {
        Test->AddError(TEXT("forced passenger did not become a swimmer"));
        return true;
    }
    Test->TestFalse(TEXT("spawned swimmer position is finite"), TargetCm.ContainsNaN());
    for (TActorIterator<ARaftSimCrewAvatarActor> It(GetM5GameWorld()); It; ++It)
    {
        Test->TestTrue(
            FString::Printf(TEXT("avatar %s starts rescue with finite transforms"), *It->GetName()),
            It->HasFiniteVisualTransforms());
    }
    Raft->AimRescue(TargetCm - Raft->GetActorLocation());
    Test->TestTrue(TEXT("aimed throw-line starts"), Raft->BeginRescue(ERaftSimRescueMethod::ThrowLine));
    if (Guide && Guide->GetGuideCamera())
    {
        Guide->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
        UCameraComponent* Camera = Guide->GetGuideCamera();
        Camera->bUsePawnControlRotation = false;
        const FVector ViewLocation = Raft->GetActorLocation() -
            Raft->GetActorForwardVector() * 520.0f +
            Raft->GetActorRightVector() * 360.0f + FVector(0.0f, 0.0f, 260.0f);
        Camera->SetWorldLocationAndRotation(
            ViewLocation,
            (Raft->GetActorLocation() + FVector(30.0f, 0.0f, 35.0f) - ViewLocation).Rotation());
    }
    FScreenshotRequest::RequestScreenshot(TEXT("M5_RescueProduction.png"), false, false);
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM5FinishRescueCommand, FAutomationTestBase*, Test);
bool FRaftSimM5FinishRescueCommand::Update()
{
    ARaftSimRaftActor* Raft = FindM5Raft();
    if (!Raft)
    {
        Test->AddError(TEXT("raft disappeared during M5 rescue"));
        return true;
    }
    Test->TestEqual(
        TEXT("runtime rescue reached re-entry"),
        static_cast<int32>(Raft->GetRescueInteractionState().Phase),
        static_cast<int32>(ERaftSimRescueInteractionPhase::ReadyForReentry));
    Test->TestTrue(TEXT("explicit reseat succeeds"), Raft->RequestSelectedReentry());
    Test->TestEqual(TEXT("no swimmer remains"), Raft->GetSwimmerCount(), 0);
    for (TActorIterator<ARaftSimCrewAvatarActor> It(GetM5GameWorld()); It; ++It)
    {
        Test->TestTrue(
            FString::Printf(TEXT("avatar %s keeps finite render transforms"), *It->GetName()),
            It->HasFiniteVisualTransforms());
    }
    return true;
}

bool FRaftSimM5RuntimeRescueLoopTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM5StartRescueCommand(this));
    // Offscreen screenshot capture can stall rendering for several wall-clock
    // seconds; leave six full simulated pull seconds after that evidence step.
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(13.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM5FinishRescueCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
