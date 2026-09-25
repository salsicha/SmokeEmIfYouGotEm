#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "UObject/Script.h"
#include "ProceduralMeshComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Serialization/BufferArchive.h"
#include "HAL/FileManager.h"
#include "RenderingThread.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewOccupancyTest,
    "RaftSim.Crew.OccupancyControlsLoadsAndIntegratedMass",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCrewOccupancyTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard ScriptGuard;
    UWorld* World = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
        if (Context.WorldType == EWorldType::Editor) { World = Context.World(); break; }
    if (!TestNotNull(TEXT("editor world"), World)) return false;
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    if (!TestNotNull(TEXT("production raft"), Raft)) return false;
    ON_SCOPE_EXIT {
        TArray<AActor*> Owned;
        for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It)
            if (It->GetOwner() == Raft) Owned.Add(*It);
        for (auto* Actor : Owned) World->DestroyActor(Actor);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    Raft->SetActorRotation(FRotator(12.f, -137.f, 21.f));
    const auto* FirstAvatar = Raft->FindAvatar(TEXT("paddler_1"));
    if (!TestNotNull(TEXT("first seated avatar"), FirstAvatar)) return false;
    const float EjectionYaw = FirstAvatar->GetActorRotation().Yaw;
    auto* Adapter = NewObject<URaftSimChronoRuntimeAdapter>(Raft);
    Raft->RaftAdapter = Adapter;
    FRaftSimFlexParameters Flex;
    Flex.MassKg = 220.; Flex.PassengerCount = 4;
    FRaftSimRaftBodyConfig Body;
    Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg = float(Flex.TotalMassKg());
    Body.InertiaTensorKgM2 = FVector(300, 400, 700);
    Adapter->ConfigureRaftBody(Body);
    Adapter->ConfigureFlexibleRaftModel(Flex, RaftSimFlex::BuildDefaultCrewSeats(Flex), 18000., true);
    const auto Step = [&](double CrewMass) {
        const double ExpectedMass = 220. + CrewMass;
        Adapter->SetKinematicState(FRaftSimRaftKinematicState{});
        Adapter->AddExternalImpulse(FVector(ExpectedMass, 0, 0), FVector::ZeroVector);
        TestTrue(TEXT("real occupied-mass integration succeeds"), Adapter->StepRaftDynamics(1.f / 120.f));
        const auto& T = Adapter->GetLastFlexibleStepTelemetry();
        TestTrue(TEXT("seat-load occupied mass"), FMath::IsNearlyEqual(T.OccupiedCrewMassKg, CrewMass));
        TestTrue(TEXT("integrator uses dry plus occupied mass"), FMath::IsNearlyEqual(T.IntegratedMassKg, ExpectedMass));
        TestTrue(TEXT("impulse response uses actual mass, not merely telemetry"),
            FMath::IsNearlyEqual(Adapter->GetKinematicState().LinearVelocityMetersPerSecond.X, 1.0, 1.e-6));
        TestTrue(TEXT("hull buoyancy capacity does not lose crew-sized volume"),
            FMath::IsNearlyEqual(T.BuoyancyReferenceMassKg, 605.));
        TestTrue(TEXT("documented shape-inertia scale uses current mass"),
            T.IntegratedInertiaKgM2.Equals(Body.InertiaTensorKgM2 * (ExpectedMass / 605.), 1.e-6));
        AddInfo(FString::Printf(TEXT("OCCUPANCY crew=%.0f integrated=%.0f buoyancy_reference=%.0f"),
            T.OccupiedCrewMassKg, T.IntegratedMassKg, T.BuoyancyReferenceMassKg));
    };
    Step(385.);
    Raft->HandleHighSideResponse(-1);
    const auto Before = Adapter->GetKinematicState();
    Raft->ForceCrewOverboardForTesting(2);
    TestEqual(TEXT("two swimmers"), Raft->GetSwimmerCount(), 2);
    const auto* SwimmingAvatar = Raft->FindAvatar(TEXT("paddler_1"));
    TestTrue(TEXT("ejection preserves world heading instead of resetting to world +X"),
        FMath::Abs(FMath::FindDeltaAngleDegrees(SwimmingAvatar->GetActorRotation().Yaw, EjectionYaw)) < .001f);
    TestTrue(TEXT("ejection releases seat tilt for the authored horizontal swim"),
        FMath::Abs(SwimmingAvatar->GetActorRotation().Pitch) < .001f &&
        FMath::Abs(SwimmingAvatar->GetActorRotation().Roll) < .001f);
    const FBox HullBox = Raft->RaftVisual->CalcBounds(Raft->RaftVisual->GetComponentTransform()).GetBox();
    int32 CheckedParts = 0;
    TInlineComponentArray<UPrimitiveComponent*> Parts(SwimmingAvatar);
    for (const UPrimitiveComponent* Part : Parts)
    {
        if (!Part || !Part->IsRegistered() || !Part->IsVisible()) continue;
        const FBox PartBox = Part->CalcBounds(Part->GetComponentTransform()).GetBox();
        if (!PartBox.IsValid) continue;
        ++CheckedParts;
        // The first ejection is world +X. Check every visible component,
        // independently of the production aggregate-box projection.
        TestTrue(TEXT("whole posed swimmer starts beyond the rendered hull, including feet"),
            PartBox.Min.X >= HullBox.Max.X + 4.99);
    }
    TestTrue(TEXT("clearance test covers actual visible body components"), CheckedParts > 0);
    const double DriftZ=Raft->Swimmers[0].SwimmerWorldPositionMeters.Z;
    Raft->Swimmers[0].SwimmerWorldPositionMeters=Raft->GetActorLocation()/100.+FVector(.2,0,0);
    Raft->Swimmers[0].SwimmerWorldPositionMeters.Z=DriftZ;
    Raft->DriftSwimmers(0.f);
    TestEqual(TEXT("hull separation does not lift a swimmer"),Raft->Swimmers[0].SwimmerWorldPositionMeters.Z,DriftZ);
    for(const auto* Part:Parts)
        if(Part && Part->IsRegistered() && Part->IsVisible())
            TestTrue(TEXT("drift restores every visible part beyond the hull"),
                Part->CalcBounds(Part->GetComponentTransform()).GetBox().Min.X>=HullBox.Max.X+4.99);
    const FVector Separated=Raft->Swimmers[0].SwimmerWorldPositionMeters;
    Raft->DriftSwimmers(0.f);
    TestTrue(TEXT("repeated zero-step contact does not creep"),Raft->Swimmers[0].SwimmerWorldPositionMeters.Equals(Separated,1.e-6));
    FVector TubeTarget;
    const FVector StartM = Raft->Swimmers[0].SwimmerWorldPositionMeters;
    TestTrue(TEXT("published hull supplies a pulling target"),
        Raft->GetSwimmerTubeTarget(TEXT("paddler_1"), StartM, TubeTarget));
    TestTrue(TEXT("pull target preserves water elevation"), FMath::IsNearlyEqual(TubeTarget.Z, StartM.Z, 1.e-6));
    const auto* HullSection = Raft->RaftVisual->GetProcMeshSection(0);
    if (!TestNotNull(TEXT("rendered hull section"), HullSection)) return false;
    const FVector SurfaceM = Raft->RaftVisual->GetComponentTransform().TransformPosition(
        HullSection->ProcVertexBuffer[0].Position) / 100.0;
    TestTrue(TEXT("exact published surface has zero hull distance"), Raft->GetRenderedHullDistanceM(SurfaceM) < .0001);
    const auto SavedInteraction = Raft->RescueInteraction;
    Raft->RescueInteraction.TargetPassengerId = TEXT("paddler_1");
    Raft->RescueInteraction.Phase = ERaftSimRescueInteractionPhase::ReadyForReentry;
    Raft->Swimmers[0].SwimmerWorldPositionMeters = SurfaceM + FVector(100,0,0);
    TestFalse(TEXT("ready state cannot board from far outside the actual hull"), Raft->RequestSelectedReentry());
    TestEqual(TEXT("far reentry keeps both swimmers"), Raft->GetSwimmerCount(), 2);
    TestEqual(TEXT("physical distance failure asks for tube contact"),
        Raft->RescueInteraction.FeedbackCode, FName(TEXT("rescue_bring_to_tube")));
    Raft->Swimmers[0].SwimmerWorldPositionMeters = StartM;
    Raft->RescueInteraction = SavedInteraction;
    TestTrue(TEXT("occupancy change preserves body velocity"),
        Adapter->GetKinematicState().LinearVelocityMetersPerSecond == Before.LinearVelocityMetersPerSecond);
    TestFalse(TEXT("ejected seat loses stale action immediately"), Adapter->FlexActions.ContainsByPredicate(
        [](const auto& A) { return A.SeatId == TEXT("passenger_0"); }));
    Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
    Raft->UpdateCrew(1.f);
    Step(235.);
    Raft->Swimmers[0].TimeInWaterSeconds = 10.f;
    Raft->RescueInteraction.Phase = ERaftSimRescueInteractionPhase::Pulling;
    Raft->ForceCrewOverboardForTesting(1);
    Raft->ForceCrewOverboardForTesting(0);
    TestEqual(TEXT("repeated/zero ejection does not orphan another swimmer"), Raft->GetSwimmerCount(), 2);
    TestEqual(TEXT("existing rescue clock is preserved"), Raft->Swimmers[0].TimeInWaterSeconds, 10.f);
    TestEqual(TEXT("duplicate event preserves active rescue phase"),
        Raft->RescueInteraction.Phase, ERaftSimRescueInteractionPhase::Pulling);
    Step(235.);
    // Exercise the public successful boarding branch, not just its removal helper.
    // Capture discontinuity separately: occupancy correctness is not animation acceptance.
    const int32 BoardingIndex = Raft->FindSwimmerIndex(TEXT("paddler_1"));
    TestTrue(TEXT("boarding target remains present"), Raft->Swimmers.IsValidIndex(BoardingIndex));
    if (!Raft->Swimmers.IsValidIndex(BoardingIndex)) return false;
    auto* BoardingAvatar = Raft->FindAvatar(TEXT("paddler_1"));
    if (!TestNotNull(TEXT("boarding keeps the existing avatar"), BoardingAvatar)) return false;
    BoardingAvatar->SetAvatarAction(ERaftSimCrewAvatarAction::Reentry);
    TestTrue(TEXT("current reentry pose supplies current tube target"),
        Raft->GetSwimmerTubeTarget(TEXT("paddler_1"), Raft->Swimmers[BoardingIndex].SwimmerWorldPositionMeters, TubeTarget));
    Raft->Swimmers[BoardingIndex].SwimmerWorldPositionMeters = TubeTarget;
    BoardingAvatar->SetActorLocation(TubeTarget * 100.);
    AddInfo(FString::Printf(TEXT("REENTRY_TARGET hull_distance_m=%.9f"), Raft->GetRenderedHullDistanceM(TubeTarget)));
    const int32 PreviousRescues = Raft->GetCompletedRescueCount();
    Raft->RescueInteraction.TargetPassengerId = TEXT("paddler_1");
    Raft->RescueInteraction.Phase = ERaftSimRescueInteractionPhase::ReadyForReentry;
    const FVector ReadyPosition = BoardingAvatar->GetActorLocation();
    for (int32 Frame = 0; Frame < 8; ++Frame)
    {
        Raft->DriftSwimmers(0.f);
        TestEqual(TEXT("drift preserves selected ready swimmer reentry pose"),
            BoardingAvatar->GetAvatarAction(), ERaftSimCrewAvatarAction::Reentry);
        TestEqual(TEXT("unselected swimmer continues swimming"),
            Raft->FindAvatar(TEXT("paddler_2"))->GetAvatarAction(), ERaftSimCrewAvatarAction::Swimming);
        Raft->UpdateRescueInteraction(0.f);
        TestTrue(TEXT("zero-time ready drift/rescue cycle does not move the root"),
            BoardingAvatar->GetActorLocation().Equals(ReadyPosition, .01));
    }
    for (int32 Frame = 0; Frame < 12; ++Frame)
    {
        Raft->DriftSwimmers(1.f / 60.f);
        TestEqual(TEXT("elapsed drift preserves ready pose"), BoardingAvatar->GetAvatarAction(), ERaftSimCrewAvatarAction::Reentry);
        Raft->UpdateRescueInteraction(1.f / 60.f);
        BoardingAvatar->Tick(1.f / 60.f);
        TestTrue(TEXT("ready body remains finite during elapsed updates"), BoardingAvatar->HasFiniteVisualTransforms());
        TestTrue(TEXT("ready PFD follows rendered chest during elapsed updates"), BoardingAvatar->GetProductionPfdTorsoErrorCm() < .01f);
    }
    Step(235.); // Waiting at the tube has not silently occupied the seat.
    Raft->RescueInteraction.Phase = ERaftSimRescueInteractionPhase::Pulling;
    Raft->DriftSwimmers(0.f);
    TestEqual(TEXT("leaving ready state releases reentry pose"), BoardingAvatar->GetAvatarAction(), ERaftSimCrewAvatarAction::Swimming);
    Raft->RescueInteraction.Phase = ERaftSimRescueInteractionPhase::ReadyForReentry;
    Raft->UpdateRescueInteraction(0.f);
    const FVector BeforeBoarding = BoardingAvatar->GetActorLocation();
    const auto BeforeBoardingPose = BoardingAvatar->GetPublishedCrewPose();
    FVector LeftSupport, RightSupport;
    TestTrue(TEXT("published side tube supplies two palm supports"),
        Raft->FindBoardingTubeSupports(BeforeBoarding, 50., LeftSupport, RightSupport));
    for (const FVector& Support : {LeftSupport, RightSupport})
        TestTrue(TEXT("palm support lies on exact rendered hull"),
            Raft->GetRenderedHullDistanceM(Raft->GetActorTransform().TransformPosition(Support) / 100.) < 1.e-5);
    TestTrue(TEXT("palm supports remain distinct"), FVector::Distance(LeftSupport, RightSupport) >= 25.);
    const FTransform OriginalRaft = Raft->GetActorTransform();
    const FVector LocalSwimmer = OriginalRaft.InverseTransformPosition(BeforeBoarding);
    const FTransform MovedRaft(FRotator(-9, 63, -14), FVector(1400, -900, 350));
    Raft->SetActorTransform(MovedRaft);
    FVector MovedLeft, MovedRight;
    TestTrue(TEXT("moved tilted raft supplies supports"), Raft->FindBoardingTubeSupports(
        MovedRaft.TransformPosition(LocalSwimmer), 50., MovedLeft, MovedRight));
    TestTrue(TEXT("support selection is raft-local under rigid motion"),
        LeftSupport.Equals(MovedLeft, .001) && RightSupport.Equals(MovedRight, .001));
    Raft->SetActorTransform(OriginalRaft);
    FVector OppositeLeft, OppositeRight;
    TestTrue(TEXT("opposite side supplies supports"), Raft->FindBoardingTubeSupports(
        OriginalRaft.TransformPosition(FVector(LocalSwimmer.X, -LocalSwimmer.Y, LocalSwimmer.Z)),
        50., OppositeLeft, OppositeRight));
    TestTrue(TEXT("opposite side does not reuse same tube"), LeftSupport.Y * OppositeLeft.Y < 0.);
    TestFalse(TEXT("zero hand spacing fails closed"), Raft->FindBoardingTubeSupports(BeforeBoarding, 0., MovedLeft, MovedRight));
    AddInfo(FString::Printf(TEXT("BOARDING_SUPPORT left_local_cm=%s right_local_cm=%s"),
        *LeftSupport.ToString(), *RightSupport.ToString()));
    TestTrue(TEXT("ready swimmer at rendered tube boards through public request"), Raft->RequestSelectedReentry());
    double BoardingSimSeconds = 0.;
    if (FParse::Param(FCommandLine::Get(), TEXT("RaftSimTimedReentryReview")))
    {
        FString CaptureDir;
        FParse::Value(FCommandLine::Get(), TEXT("RaftSimBoardingCaptureDir="), CaptureDir);
        AActor* Camera = nullptr;
        USceneCaptureComponent2D* Capture = nullptr;
        UTextureRenderTarget2D* Target = nullptr;
        ON_SCOPE_EXIT { if (Camera) World->DestroyActor(Camera); FlushRenderingCommands(); };
        if (!CaptureDir.IsEmpty())
        {
            if (!TestFalse(TEXT("preserve prior boarding captures"), IFileManager::Get().DirectoryExists(*CaptureDir))) return false;
            IFileManager::Get().MakeDirectory(*CaptureDir, true);
            Camera = World->SpawnActor<AActor>();
            Capture = NewObject<USceneCaptureComponent2D>(Camera);
            Camera->SetRootComponent(Capture);
            Target = NewObject<UTextureRenderTarget2D>(Capture);
            Target->RenderTargetFormat = RTF_RGBA8;
            Target->InitAutoFormat(800, 600); Target->UpdateResourceImmediate(true);
            Capture->TextureTarget = Target; Capture->CaptureSource = SCS_FinalColorLDR;
            Capture->bCaptureEveryFrame = false; Capture->bCaptureOnMovement = false;
            Capture->ShowFlags.SetLighting(false); // Unlit geometry review, not shading acceptance.
            Capture->FOVAngle = 55.f; Capture->RegisterComponent();
            const FVector Eye = Raft->GetActorTransform().TransformPosition(FVector(600,850,500));
            const FVector Aim = Raft->GetActorTransform().TransformPosition(FVector(0,0,45));
            Capture->SetWorldLocationAndRotation(Eye, (Aim-Eye).Rotation());
        }
        const auto SavePose = [&](int32 Frame)
        {
            if (!Capture) return;
            World->SendAllEndOfFrameUpdates(); FlushRenderingCommands();
            Capture->CaptureScene(); FlushRenderingCommands();
            FBufferArchive Bytes;
            TestTrue(TEXT("export actual boarding key pose"), FImageUtils::ExportRenderTarget2DAsPNG(Target, Bytes) &&
                FFileHelper::SaveArrayToFile(Bytes, *FPaths::Combine(CaptureDir, FString::Printf(TEXT("frame_%03d.png"), Frame))));
        };
        SavePose(0);
        TestTrue(TEXT("accepted boarding starts without root teleport"), BoardingAvatar->GetActorLocation().Equals(BeforeBoarding, .01));
        TestEqual(TEXT("boarding has not completed the rescue"), Raft->GetCompletedRescueCount(), PreviousRescues);
        TestTrue(TEXT("boarding passenger is still unseated"), Raft->IsPassengerSwimming(TEXT("paddler_1")));
        TestFalse(TEXT("duplicate boarding request rejected during transition"), Raft->RequestSelectedReentry());
        Step(235.);
        FVector PreviousPosition = BoardingAvatar->GetActorLocation();
        double MaxStepCm = 0.;
        double MaxNearestHandGapCm = 0.;
        double MinBothHandGapCm = DBL_MAX;
        int32 UnsupportedFrames = 0;
        const auto RecordHandSupport = [&](int32 Frame)
        {
            // Published pose controls, not a claim about skin contact or grip forces.
            // Query the same visible triangles as the production distance gate.
            const auto& Pose = BoardingAvatar->GetPublishedCrewPose();
            const FTransform BodyTransform = BoardingAvatar->GetActorTransform();
            const double LeftCm = 100. * Raft->GetRenderedHullDistanceM(
                BodyTransform.TransformPosition(Pose.LeftHandCm) / 100.);
            const double RightCm = 100. * Raft->GetRenderedHullDistanceM(
                BodyTransform.TransformPosition(Pose.RightHandCm) / 100.);
            const double NearestCm = FMath::Min(LeftCm, RightCm);
            MaxNearestHandGapCm = FMath::Max(MaxNearestHandGapCm, NearestCm);
            MinBothHandGapCm = FMath::Min(MinBothHandGapCm, FMath::Max(LeftCm, RightCm));
            if (NearestCm > 10.) ++UnsupportedFrames;
            if (Frame % 30 == 0)
                AddInfo(FString::Printf(TEXT("BOARDING_HAND_GAP frame=%d left_cm=%.9f right_cm=%.9f"),
                    Frame, LeftCm, RightCm));
            TestTrue(TEXT("hand-to-rendered-hull measurements are finite"),
                FMath::IsFinite(LeftCm) && FMath::IsFinite(RightCm));
        };
        RecordHandSupport(0);
        int32 Frames = 0;
        bool bCapturedReach = false;
        double ReachBothHandGapCm = DBL_MAX;
        Raft->UpdateRescueInteraction(-1.f);
        TestTrue(TEXT("negative time cannot move boarding root"), BoardingAvatar->GetActorLocation().Equals(PreviousPosition, .01));
        while (!Raft->BoardingPassenger.IsNone() && Frames < 720)
        {
            Raft->DriftSwimmers(1.f/60.f);
            Raft->UpdateCrew(1.f/60.f);
            Raft->UpdateRescueInteraction(1.f/60.f);
            BoardingAvatar->Tick(1.f/60.f);
            const FVector Current = BoardingAvatar->GetActorLocation();
            MaxStepCm = FMath::Max(MaxStepCm, FVector::Distance(PreviousPosition, Current));
            PreviousPosition = Current;
            TestTrue(TEXT("timed body finite"), BoardingAvatar->HasFiniteVisualTransforms());
            TestTrue(TEXT("timed PFD tracks body"), BoardingAvatar->GetProductionPfdTorsoErrorCm() < .01f);
            if (!Raft->BoardingPassenger.IsNone())
            {
                TestTrue(TEXT("paddling cannot claim a boarding avatar"), BoardingAvatar->GetAttachParentActor() != Raft);
                TestEqual(TEXT("count changes only on completion"), Raft->GetCompletedRescueCount(), PreviousRescues);
            }
            ++Frames;
            if (!Raft->BoardingPassenger.IsNone()) RecordHandSupport(Frames);
            if (!bCapturedReach && !Raft->BoardingPassenger.IsNone() &&
                Raft->BoardingElapsed >= Raft->BoardingDuration * ARaftSimCrewAvatarActor::BoardingReachFraction)
            {
                bCapturedReach = true;
                const auto& ReachPose = BoardingAvatar->GetPublishedCrewPose();
                const FTransform ReachWorld = BoardingAvatar->GetActorTransform();
                ReachBothHandGapCm = 100. * FMath::Max(Raft->GetRenderedHullDistanceM(
                    ReachWorld.TransformPosition(ReachPose.LeftHandCm)/100.), Raft->GetRenderedHullDistanceM(
                    ReachWorld.TransformPosition(ReachPose.RightHandCm)/100.));
                TestTrue(TEXT("reach does not lengthen left shoulder-hand control span by over 2cm"),
                    FVector::Distance(ReachPose.LeftShoulderCm, ReachPose.LeftHandCm) <=
                    FVector::Distance(BeforeBoardingPose.LeftShoulderCm, BeforeBoardingPose.LeftHandCm) + 2.);
                TestTrue(TEXT("reach does not lengthen right shoulder-hand control span by over 2cm"),
                    FVector::Distance(ReachPose.RightShoulderCm, ReachPose.RightHandCm) <=
                    FVector::Distance(BeforeBoardingPose.RightShoulderCm, BeforeBoardingPose.RightHandCm) + 2.);
                SavePose(Frames);
                AddInfo(FString::Printf(TEXT("BOARDING_REACH frame=%d root_local_cm=%s"), Frames,
                    *Raft->GetActorTransform().InverseTransformPosition(Current).ToString()));
            }
            BoardingSimSeconds += 1. / 60.;
            if (Frames % 30 == 0 || Raft->BoardingPassenger.IsNone()) SavePose(Frames);
        }
        TestTrue(TEXT("timed boarding reaches completion"), Frames < 720 && Raft->BoardingPassenger.IsNone());
        TestTrue(TEXT("no large per-frame root teleport"), MaxStepCm < 10.);
        TestTrue(TEXT("reach stage is sampled"), bCapturedReach);
        TestTrue(TEXT("both hand controls at reach boundary are within authored palm clearance"), ReachBothHandGapCm < 5.);
        AddInfo(FString::Printf(TEXT("TIMED_REENTRY frames=%d max_step_cm=%.9f"), Frames, MaxStepCm));
        AddInfo(FString::Printf(TEXT("BOARDING_HAND_SUPPORT max_nearest_gap_cm=%.9f samples_both_over_10cm=%d"),
            MaxNearestHandGapCm, UnsupportedFrames));
        AddInfo(FString::Printf(TEXT("BOARDING_REACH_SUPPORT min_both_gap_cm=%.9f"), MinBothHandGapCm));
        AddInfo(FString::Printf(TEXT("BOARDING_REACH_BOUNDARY both_gap_cm=%.9f"), ReachBothHandGapCm));
    }
    TestTrue(TEXT("boarding preserves avatar identity"), Raft->FindAvatar(TEXT("paddler_1")) == BoardingAvatar);
    TestEqual(TEXT("successful public boarding counts exactly one rescue"), Raft->GetCompletedRescueCount(), PreviousRescues + 1);
    TestFalse(TEXT("boarded passenger leaves swimming state"), Raft->IsPassengerSwimming(TEXT("paddler_1")));
    TestTrue(TEXT("boarded visual remains finite"), BoardingAvatar->HasFiniteVisualTransforms());
    AddInfo(FString::Printf(TEXT("REENTRY_DISPLACEMENT elapsed_s=%.9f root_displacement_cm=%.9f"),
        BoardingSimSeconds, FVector::Distance(BeforeBoarding, BoardingAvatar->GetActorLocation())));
    TestFalse(TEXT("repeat boarding cannot rescue the already boarded passenger"), Raft->RequestSelectedReentry());
    TestEqual(TEXT("repeat boarding does not increment rescue count"), Raft->GetCompletedRescueCount(), PreviousRescues + 1);
    TestEqual(TEXT("one swimmer remains after single reseat"), Raft->GetSwimmerCount(), 1);
    Step(310.);
    if (FParse::Param(FCommandLine::Get(), TEXT("RaftSimTimedReentryReview")))
    {
        auto* InterruptedAvatar = Raft->FindAvatar(TEXT("paddler_2"));
        const int32 InterruptedIndex = Raft->FindSwimmerIndex(TEXT("paddler_2"));
        if (!TestNotNull(TEXT("interruption avatar"), InterruptedAvatar) ||
            !TestTrue(TEXT("interruption swimmer"), Raft->Swimmers.IsValidIndex(InterruptedIndex))) return false;
        InterruptedAvatar->SetAvatarAction(ERaftSimCrewAvatarAction::Reentry);
        TestTrue(TEXT("interruption target"), Raft->GetSwimmerTubeTarget(TEXT("paddler_2"),
            Raft->Swimmers[InterruptedIndex].SwimmerWorldPositionMeters, TubeTarget));
        Raft->Swimmers[InterruptedIndex].SwimmerWorldPositionMeters = TubeTarget;
        InterruptedAvatar->SetActorLocation(TubeTarget * 100.);
        Raft->RescueInteraction.TargetPassengerId = TEXT("paddler_2");
        Raft->RescueInteraction.Phase = ERaftSimRescueInteractionPhase::ReadyForReentry;
        if (!TestTrue(TEXT("second passenger starts timed boarding"), Raft->RequestSelectedReentry())) return false;
        Raft->UpdateTimedBoarding(.1f);
        const FVector InterruptedPosition = InterruptedAvatar->GetActorLocation();
        Raft->CancelTimedBoarding();
        TestTrue(TEXT("cancel releases boarding owner"), Raft->BoardingPassenger.IsNone());
        TestTrue(TEXT("cancel does not teleport the passenger"), InterruptedAvatar->GetActorLocation().Equals(InterruptedPosition, .01));
        Raft->UpdateRescueInteraction(0.f);
        TestEqual(TEXT("cancel cannot silently reacquire ready pose on next update"),
            InterruptedAvatar->GetAvatarAction(), ERaftSimCrewAvatarAction::Swimming);
        TestFalse(TEXT("cancel requires a new rescue interaction before boarding"), Raft->RequestSelectedReentry());
        TestEqual(TEXT("cancel does not complete another rescue"), Raft->GetCompletedRescueCount(), PreviousRescues + 1);
        TestTrue(TEXT("cancel retains swimmer occupancy"), Raft->IsPassengerSwimming(TEXT("paddler_2")));
        Step(310.);
    }
    Raft->RaftMode = ERaftSimRaftMode::Capsized;
    Adapter->SetFlexibleCapsized(true);
    Raft->SpawnSwimmers(5, true);
    TestEqual(TEXT("capsize adds missing crew without duplicate swimmers"), Raft->GetSwimmerCount(), 5);
    Step(0.);
    Raft->RequestReflip();
    TestEqual(TEXT("real reflip enters recovery"), Raft->GetRaftMode(), ERaftSimRaftMode::Recovering);
    Step(0.);
    Raft->RemoveSwimmerAt(Raft->FindSwimmerIndex(TEXT("guide")));
    Step(85.);
    TestTrue(TEXT("checkpoint restores seated roster"), Raft->TryRestoreCheckpoint(FTransform::Identity));
    TestEqual(TEXT("checkpoint clears swimmers"), Raft->GetSwimmerCount(), 0);
    Step(385.);
    TestFalse(TEXT("unknown physical seat rejected"), Adapter->SetFlexibleCrewSeatOccupied(TEXT("paddler_1"), false));
    Step(385.);
    // Malformed combined-body configuration must not integrate near-zero mass.
    Body.MassKg = 100.f;
    Adapter->ConfigureRaftBody(Body);
    AddExpectedError(TEXT("Invalid combined crew mass contract"), EAutomationExpectedErrorFlags::Contains, 1);
    Adapter->ConfigureFlexibleRaftModel(Flex, RaftSimFlex::BuildDefaultCrewSeats(Flex), 18000., true);
    TestFalse(TEXT("invalid combined mass fails closed"), Adapter->StepRaftDynamics(1.f / 120.f));
    return true;
}
#endif
