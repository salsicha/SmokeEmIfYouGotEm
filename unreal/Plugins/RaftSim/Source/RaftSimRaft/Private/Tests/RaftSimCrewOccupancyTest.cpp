#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimCC0CrewVisualActor.h"
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
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "StaticMeshResources.h"
#include "Components/PoseableMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewOccupancyTest,
    "RaftSim.Crew.OccupancyControlsLoadsAndIntegratedMass",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCrewOccupancyTest::RunTest(const FString&)
{
    if (FParse::Param(FCommandLine::Get(), TEXT("RaftSimRequireBoardingTransferClearance")) &&
        !FParse::Param(FCommandLine::Get(), TEXT("RaftSimTimedReentryReview")))
    {
        AddError(TEXT("Strict boarding clearance requires RaftSimTimedReentryReview; no default-path substitute"));
        return false;
    }
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
            if (FParse::Param(FCommandLine::Get(), TEXT("RaftSimBoardingHandCapture")))
            {
                const FTransform HostTransform = BoardingAvatar->GetActorTransform();
                auto* Visual = BoardingAvatar->GetProductionVisualActor();
                auto* Mesh = Visual ? Visual->FindComponentByClass<UPoseableMeshComponent>() : nullptr;
                if (!TestNotNull(TEXT("close contact capture has production hand"), Mesh)) return;
                const FVector Aim = Mesh->GetBoneTransformByName(TEXT("thumb_03_r"), EBoneSpaces::WorldSpace).GetLocation();
                const FVector Eye = Aim + HostTransform.TransformVectorNoScale(FVector(45,70,40));
                Capture->SetWorldLocationAndRotation(Eye,(Aim-Eye).Rotation());
                Capture->FOVAngle = 40.f;
                Capture->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
                Capture->ClearShowOnlyComponents();
                Capture->ShowOnlyActorComponents(Raft, false);
                Capture->ShowOnlyActorComponents(BoardingAvatar, false);
                Capture->ShowOnlyActorComponents(Visual, true);
                Capture->ShowFlags.SetLighting(true);
                Capture->ShowFlags.SetMaterials(false);
                // Isolated right-hand/hull diagnostic: no normal shading or
                // crew-to-crew visibility/collision acceptance from these views.
                Capture->CaptureSource = SCS_Normal;
            }
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
        double MaxPullHandGapCm = 0., MaxPullLegSpanErrorCm = 0.;
        int32 PullSamples = 0;
        bool bCapturedPull = false;
        TArray<UStaticMeshComponent*> TransferBoots;
        TInlineComponentArray<UStaticMeshComponent*> StaticParts(BoardingAvatar);
        for (auto* Part : StaticParts)
            if (Part && Part->IsVisible() && (Part->GetFName() == TEXT("ProductionLeftBoot") ||
                Part->GetFName() == TEXT("ProductionRightBoot"))) TransferBoots.Add(Part);
        TestEqual(TEXT("transfer audit observes both production boots"), TransferBoots.Num(), 2);
        double MaximumBootTopEnvelopeDeficitCm = 0.;
        int32 BootClearanceSamples = 0, WorstBootFrame = -1;
        double MaximumBodyDeficitCm = 0.;
        int32 BodyClearanceSamples = 0, WorstBodyFrame = -1;
        FVector WorstBodyPoint = FVector::ZeroVector;
        FVector WorstBodyHostPoint = FVector::ZeroVector;
        int32 WorstBodyVertex = -1;
        double WorstBodySurfaceDistanceCm = 0., WorstBodyTubeWinding = 0.;
        FVector WorstBootPoint = FVector::ZeroVector;
        FString WorstBootName;
        const bool bStrictTransfer = FParse::Param(FCommandLine::Get(), TEXT("RaftSimRequireBoardingTransferClearance"));
        const int32 BootSampleStride = bStrictTransfer ? 1 : 6;
        const FVector FRaftSimCrewAvatarPose::* LegPoints[] = {
            &FRaftSimCrewAvatarPose::LeftKneeCm, &FRaftSimCrewAvatarPose::RightKneeCm,
            &FRaftSimCrewAvatarPose::LeftFootCm, &FRaftSimCrewAvatarPose::RightFootCm};
        FVector PreviousLegWorld[4];
        for (int32 P = 0; P < 4; ++P)
            PreviousLegWorld[P] = BoardingAvatar->GetActorTransform().TransformPosition(BoardingAvatar->GetPublishedCrewPose().*LegPoints[P]);
        double MaxLegPointStepCm = 0.;
        int32 WorstLegFrame = -1, WorstLegPoint = -1;
        auto* HandVisual = Cast<ARaftSimCC0CrewVisualActor>(BoardingAvatar->GetProductionVisualActor());
        auto* HandBody = HandVisual ? HandVisual->FindComponentByClass<UPoseableMeshComponent>() : nullptr;
        if (!TestNotNull(TEXT("handoff audit observes actual production bones"), HandBody)) return false;
        TArray<FName> HandBones;
        TArray<FTransform> PreviousHandWorld;
        for (const TCHAR* Side : {TEXT("l"), TEXT("r")})
        {
            HandBones.Add(FName(*FString::Printf(TEXT("hand_%s"), Side)));
            for (const TCHAR* Digit : {TEXT("thumb"), TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")})
                for (int32 Segment = 1; Segment <= 3; ++Segment)
                    HandBones.Add(FName(*FString::Printf(TEXT("%s_%02d_%s"), Digit, Segment, Side)));
        }
        for (FName Bone : HandBones)
        {
            TestTrue(TEXT("handoff bone exists"), HandBody->GetBoneIndex(Bone) != INDEX_NONE);
            PreviousHandWorld.Add(HandBody->GetBoneTransformByName(Bone, EBoneSpaces::WorldSpace));
        }
        double MaxHandStepCm = 0., MaxHandAngleDegrees = 0.;
        const int32 ThumbStarts[] = {1,2,17,18};
        double ThumbSupportLengths[4];
        for (int32 I = 0; I < 4; ++I)
            ThumbSupportLengths[I] = FVector::Distance(PreviousHandWorld[ThumbStarts[I]].GetLocation(),
                PreviousHandWorld[ThumbStarts[I]+1].GetLocation());
        double MaxThumbSupportLengthErrorCm = 0.;
        TSet<int32> ThumbVertices;
        if (const USkeletalMesh* Mesh = Cast<USkeletalMesh>(HandBody->GetSkinnedAsset()))
        {
            const auto* Data = Mesh->GetResourceForRendering();
            if (Data && !Data->LODRenderData.IsEmpty())
            {
                const auto& LOD = Data->LODRenderData[0];
                const auto* Weights = LOD.GetSkinWeightVertexBuffer();
                if (Weights)
                    for (uint32 V = 0; V < LOD.GetNumVertices(); ++V)
                    {
                        int32 Section = INDEX_NONE, SectionVertex = INDEX_NONE;
                        LOD.GetSectionFromVertexIndex(V, Section, SectionVertex);
                        if (!LOD.RenderSections.IsValidIndex(Section)) continue;
                        const auto& BoneMap = LOD.RenderSections[Section].BoneMap;
                        for (uint32 I = 0; I < Weights->GetMaxBoneInfluences(); ++I)
                        {
                            const uint32 Bone = Weights->GetBoneIndex(V,I);
                            if (Weights->GetBoneWeight(V,I) && Bone < uint32(BoneMap.Num()) &&
                                Mesh->GetRefSkeleton().GetBoneName(BoneMap[Bone]).ToString().StartsWith(TEXT("thumb_")))
                            { ThumbVertices.Add(V); break; }
                        }
                    }
            }
        }
        TestTrue(TEXT("thumb region has actual nonzero skin weights"), ThumbVertices.Num() > 0);
        double MaximumThumbDeficitCm = 0.;
        int32 ThumbClearanceSamples = 0, WorstThumbFrame = -1, WorstThumbVertex = -1;
        int32 WorstHandFrame = -1, GripHandoffSamples = 0;
        FName WorstHandBone;
        int32 WorstHandAngleFrame = -1;
        FName WorstHandAngleBone;
        Raft->UpdateRescueInteraction(-1.f);
        TestTrue(TEXT("negative time cannot move boarding root"), BoardingAvatar->GetActorLocation().Equals(PreviousPosition, .01));
        while (!Raft->BoardingPassenger.IsNone() && Frames < 720)
        {
            Raft->DriftSwimmers(1.f/60.f);
            Raft->UpdateCrew(1.f/60.f);
            Raft->UpdateRescueInteraction(1.f/60.f);
            BoardingAvatar->Tick(1.f/60.f);
            if (Frames+1 == 240 || Frames+1 == 258 || Frames+1 == 264 || Frames+1 == 270)
            {
                const auto& HandPose = BoardingAvatar->GetPublishedCrewPose();
                AddInfo(FString::Printf(TEXT("BOARDING_THUMB_PHASE frame=%d support=%.9f grip=%.9f palm_host=%s"),
                    Frames+1, HandPose.BoardingPalmSupportBlend, HandPose.BoardingPaddleGripBlend, *HandPose.RightHandCm.ToString()));
                for (const TCHAR* Bone : {TEXT("hand_r"), TEXT("thumb_01_r"), TEXT("thumb_02_r"), TEXT("thumb_03_r")})
                {
                    const FVector WorldPoint = HandBody->GetBoneTransformByName(FName(Bone), EBoneSpaces::WorldSpace).GetLocation();
                    const FVector Local = BoardingAvatar->GetActorTransform().InverseTransformPosition(WorldPoint);
                    const FVector HandLocal = HandBody->GetBoneTransformByName(TEXT("hand_r"), EBoneSpaces::WorldSpace).InverseTransformPosition(WorldPoint);
                    AddInfo(FString::Printf(TEXT("BOARDING_THUMB_JOINT frame=%d bone=%s host_cm=%s hand_local_units=%s surface_distance_cm=%.9f"),
                        Frames+1, Bone, *Local.ToString(), *HandLocal.ToString(), 100.*Raft->GetRenderedHullDistanceM(WorldPoint/100.)));
                }
            }
            for (int32 H = 0; H < HandBones.Num(); ++H)
            {
                const FTransform HandWorld = HandBody->GetBoneTransformByName(HandBones[H], EBoneSpaces::WorldSpace);
                TestFalse(TEXT("handoff bone transform is finite"), HandWorld.ContainsNaN());
                const double HandStep = FVector::Distance(HandWorld.GetLocation(), PreviousHandWorld[H].GetLocation());
                if (HandStep > MaxHandStepCm) { MaxHandStepCm = HandStep; WorstHandFrame = Frames+1; WorstHandBone = HandBones[H]; }
                const double HandAngle = FMath::RadiansToDegrees(
                    HandWorld.GetRotation().AngularDistance(PreviousHandWorld[H].GetRotation()));
                if (HandAngle > MaxHandAngleDegrees)
                { MaxHandAngleDegrees = HandAngle; WorstHandAngleFrame = Frames+1; WorstHandAngleBone = HandBones[H]; }
                PreviousHandWorld[H] = HandWorld;
            }
            if (!Raft->BoardingPassenger.IsNone())
            {
                const auto& HandPose = BoardingAvatar->GetPublishedCrewPose();
                if (HandPose.BoardingPaddleGripBlend == 0.f)
                    for (int32 I = 0; I < 4; ++I)
                        MaxThumbSupportLengthErrorCm = FMath::Max(MaxThumbSupportLengthErrorCm, FMath::Abs(
                            FVector::Distance(PreviousHandWorld[ThumbStarts[I]].GetLocation(),
                                PreviousHandWorld[ThumbStarts[I]+1].GetLocation()) - ThumbSupportLengths[I]));
                if (Raft->BoardingElapsed > Raft->BoardingDuration * ARaftSimCrewAvatarActor::BoardingLegOverFraction)
                {
                    ++GripHandoffSamples;
                    TestTrue(TEXT("handoff retains full palm anchoring while changing grip"),
                        FMath::IsNearlyEqual(HandPose.BoardingPalmSupportBlend + HandPose.BoardingPaddleGripBlend, 1.f, 1.e-5f));
                    TestFalse(TEXT("paddle prop remains hidden during handoff"), HandPose.bShowPaddle);
                }
                else
                    TestEqual(TEXT("paddle grip does not start before leg clearance"), HandPose.BoardingPaddleGripBlend, 0.f);
            }
            for (int32 P = 0; P < 4; ++P)
            {
                const FVector CurrentLeg = BoardingAvatar->GetActorTransform().TransformPosition(BoardingAvatar->GetPublishedCrewPose().*LegPoints[P]);
                const double LegStep = FVector::Distance(CurrentLeg,PreviousLegWorld[P]);
                if (LegStep > MaxLegPointStepCm) { MaxLegPointStepCm = LegStep; WorstLegFrame = Frames+1; WorstLegPoint = P; }
                PreviousLegWorld[P] = CurrentLeg;
            }
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
            if (Frames % BootSampleStride == 0 && (Raft->BoardingPassenger.IsNone() ||
                Raft->BoardingElapsed > Raft->BoardingDuration * ARaftSimCrewAvatarActor::BoardingPullFraction))
            {
                for (auto* Boot : TransferBoots)
                {
                    const UStaticMesh* Mesh = Boot->GetStaticMesh();
                    const auto* RenderData = Mesh ? Mesh->GetRenderData() : nullptr;
                    if (!TestTrue(TEXT("boot clearance has actual LOD0 render vertices"),
                        RenderData && RenderData->LODResources.Num() > 0)) continue;
                    const auto& Positions = RenderData->LODResources[0].VertexBuffers.PositionVertexBuffer;
                    if (!TestTrue(TEXT("boot CPU vertex buffer is available and nonempty"),
                        Positions.GetVertexData() != nullptr && Positions.GetNumVertices() > 0)) continue;
                    TArray<FVector> Points;
                    const FTransform ToRaft = Boot->GetComponentTransform().GetRelativeTransform(Raft->GetActorTransform());
                    for (uint32 V = 0; V < Positions.GetNumVertices(); ++V)
                        Points.Add(ToRaft.TransformPosition(FVector(Positions.VertexPosition(V))));
                    TArray<double> Floor, Solid;
                    // Conservative upper-envelope clearance, not signed solid
                    // containment. Outside-footprint points have no support.
                    Raft->SampleRenderedCrewSupport(Points, Floor, Solid, true);
                    if (!TestEqual(TEXT("boot support query covers every render vertex"), Solid.Num(), Points.Num())) continue;
                    for (int32 V = 0; V < Points.Num(); ++V)
                    {
                        if (Solid[V] == -DBL_MAX) continue;
                        ++BootClearanceSamples;
                        const double Deficit = Solid[V] - Points[V].Z;
                        if (Deficit > MaximumBootTopEnvelopeDeficitCm)
                        {
                            MaximumBootTopEnvelopeDeficitCm = Deficit;
                            WorstBootFrame = Frames; WorstBootPoint = Points[V]; WorstBootName = Boot->GetName();
                        }
                    }
                }
            }
            if (!Raft->BoardingPassenger.IsNone()) RecordHandSupport(Frames);
            if ((Frames % 6 == 0 || Raft->BoardingPassenger.IsNone()) &&
                (Raft->BoardingPassenger.IsNone() || Raft->BoardingElapsed >
                    Raft->BoardingDuration * ARaftSimCrewAvatarActor::BoardingPullFraction))
            {
                auto* Visual = Cast<ARaftSimCC0CrewVisualActor>(BoardingAvatar->GetProductionVisualActor());
                if (TestNotNull(TEXT("body clearance observes production CC0 visual"), Visual))
                {
                    auto Points = Visual->GetPosedBodyVerticesWorldCmForValidation();
                    TestTrue(TEXT("body clearance has CPU-skinned vertices"), !Points.IsEmpty());
                    for (auto& Point : Points)
                    {
                        TestFalse(TEXT("skinned body clearance point is finite"), Point.ContainsNaN());
                        Point = Raft->GetActorTransform().InverseTransformPosition(Point);
                    }
                    TArray<double> Floor, Solid;
                    Raft->SampleRenderedCrewSupport(Points, Floor, Solid, true);
                    if (TestEqual(TEXT("body support query covers skinned vertices"), Solid.Num(), Points.Num()))
                        for (int32 V = 0; V < Points.Num(); ++V)
                        {
                            if (Solid[V] == -DBL_MAX) continue;
                            ++BodyClearanceSamples;
                            const double Deficit = Solid[V] - Points[V].Z;
                            if (ThumbVertices.Contains(V))
                            {
                                ++ThumbClearanceSamples;
                                if (Deficit > MaximumThumbDeficitCm)
                                { MaximumThumbDeficitCm = Deficit; WorstThumbFrame = Frames; WorstThumbVertex = V; }
                            }
                            if (Deficit > MaximumBodyDeficitCm)
                            {
                                MaximumBodyDeficitCm = Deficit; WorstBodyFrame = Frames; WorstBodyPoint = Points[V];
                                WorstBodyVertex = V;
                                WorstBodyHostPoint = BoardingAvatar->GetActorTransform().InverseTransformPosition(
                                    Raft->GetActorTransform().TransformPosition(Points[V]));
                                const FVector WorldPoint = Raft->GetActorTransform().TransformPosition(Points[V]);
                                WorstBodySurfaceDistanceCm = 100. * Raft->GetRenderedHullDistanceM(WorldPoint / 100.);
                                // Raw solid-angle winding of the published tube section.
                                // Diagnostic only: not acceptance without closed/oriented mesh validation.
                                double Angle = 0.;
                                const auto* Tube = Raft->RaftVisual ? Raft->RaftVisual->GetProcMeshSection(0) : nullptr;
                                if (TestNotNull(TEXT("contact diagnostic has published tube section"), Tube))
                                {
                                    const FTransform TubeWorld = Raft->RaftVisual->GetComponentTransform();
                                    for (int32 I = 0; I + 2 < Tube->ProcIndexBuffer.Num(); I += 3)
                                    {
                                        const FVector A = TubeWorld.TransformPosition(Tube->ProcVertexBuffer[Tube->ProcIndexBuffer[I]].Position) - WorldPoint;
                                        const FVector B = TubeWorld.TransformPosition(Tube->ProcVertexBuffer[Tube->ProcIndexBuffer[I+1]].Position) - WorldPoint;
                                        const FVector C = TubeWorld.TransformPosition(Tube->ProcVertexBuffer[Tube->ProcIndexBuffer[I+2]].Position) - WorldPoint;
                                        const double LA = A.Size(), LB = B.Size(), LC = C.Size();
                                        Angle += 2. * FMath::Atan2(FVector::DotProduct(A,FVector::CrossProduct(B,C)),
                                            LA*LB*LC + FVector::DotProduct(A,B)*LC + FVector::DotProduct(B,C)*LA + FVector::DotProduct(C,A)*LB);
                                    }
                                }
                                WorstBodyTubeWinding = Angle / (4. * UE_DOUBLE_PI);
                            }
                        }
                }
            }
            if (!Raft->BoardingPassenger.IsNone() &&
                Raft->BoardingElapsed > Raft->BoardingDuration * ARaftSimCrewAvatarActor::BoardingReachFraction &&
                Raft->BoardingElapsed <= Raft->BoardingDuration * ARaftSimCrewAvatarActor::BoardingLegOverFraction)
            {
                ++PullSamples;
                const auto& P = BoardingAvatar->GetPublishedCrewPose();
                const FTransform W = BoardingAvatar->GetActorTransform();
                MaxPullHandGapCm = FMath::Max(MaxPullHandGapCm, 100. * FMath::Max(
                    Raft->GetRenderedHullDistanceM(W.TransformPosition(P.LeftHandCm)/100.),
                    Raft->GetRenderedHullDistanceM(W.TransformPosition(P.RightHandCm)/100.)));
                const double Errors[] = {
                    FMath::Abs(FVector::Distance(P.LeftHipCm,P.LeftKneeCm)-FVector::Distance(BeforeBoardingPose.LeftHipCm,BeforeBoardingPose.LeftKneeCm)),
                    FMath::Abs(FVector::Distance(P.LeftKneeCm,P.LeftFootCm)-FVector::Distance(BeforeBoardingPose.LeftKneeCm,BeforeBoardingPose.LeftFootCm)),
                    FMath::Abs(FVector::Distance(P.RightHipCm,P.RightKneeCm)-FVector::Distance(BeforeBoardingPose.RightHipCm,BeforeBoardingPose.RightKneeCm)),
                    FMath::Abs(FVector::Distance(P.RightKneeCm,P.RightFootCm)-FVector::Distance(BeforeBoardingPose.RightKneeCm,BeforeBoardingPose.RightFootCm))};
                for (double Error : Errors) MaxPullLegSpanErrorCm = FMath::Max(MaxPullLegSpanErrorCm, Error);
            }
            if (!bCapturedPull && !Raft->BoardingPassenger.IsNone() &&
                Raft->BoardingElapsed >= Raft->BoardingDuration * ARaftSimCrewAvatarActor::BoardingPullFraction)
            {
                bCapturedPull = true; SavePose(Frames);
                AddInfo(FString::Printf(TEXT("BOARDING_PULL frame=%d"), Frames));
            }
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
        TestTrue(TEXT("no foot or knee control teleport above 10cm per update"), MaxLegPointStepCm < 10.);
        TestTrue(TEXT("grip handoff was sampled"), GripHandoffSamples > 0);
        TestTrue(TEXT("thumb support preserves both shaft lengths within 0.001cm"), MaxThumbSupportLengthErrorCm <= .001);
        AddInfo(FString::Printf(TEXT("BOARDING_THUMB_LENGTH max_support_error_cm=%.9f"), MaxThumbSupportLengthErrorCm));
        TestTrue(TEXT("no wrist or finger teleport above 10cm per update"), MaxHandStepCm < 10.);
        TestTrue(TEXT("no wrist or finger rotation jump above 30 degrees per update"), MaxHandAngleDegrees <= 30.);
        AddInfo(FString::Printf(TEXT("BOARDING_HAND_CONTINUITY samples=%d max_step_cm=%.9f frame=%d bone=%s max_angle_deg=%.9f angle_frame=%d angle_bone=%s"),
            GripHandoffSamples, MaxHandStepCm, WorstHandFrame, *WorstHandBone.ToString(), MaxHandAngleDegrees,
            WorstHandAngleFrame, *WorstHandAngleBone.ToString()));
        AddInfo(FString::Printf(TEXT("BOARDING_LEG_CONTINUITY max_step_cm=%.9f boot_sample_stride=%d frame=%d point=%d"),
            MaxLegPointStepCm, BootSampleStride, WorstLegFrame, WorstLegPoint));
        TestTrue(TEXT("reach stage is sampled"), bCapturedReach);
        TestTrue(TEXT("pull stage is sampled"), bCapturedPull && PullSamples > 0);
        TestTrue(TEXT("transfer boot audit has supported vertex samples"), BootClearanceSamples > 0);
        TestTrue(TEXT("transfer body audit has supported vertex samples"), BodyClearanceSamples > 0);
        TestTrue(TEXT("thumb clearance audit has supported vertex samples"), ThumbClearanceSamples > 0);
        AddInfo(FString::Printf(TEXT("BOARDING_THUMB_CLEARANCE vertices=%d samples=%d max_top_envelope_deficit_cm=%.9f frame=%d vertex=%d"),
            ThumbVertices.Num(), ThumbClearanceSamples, MaximumThumbDeficitCm, WorstThumbFrame, WorstThumbVertex));
        AddInfo(FString::Printf(TEXT("BOARDING_BODY_CONTACT surface_distance_cm=%.9f tube_winding=%.9f"),
            WorstBodySurfaceDistanceCm, WorstBodyTubeWinding));
        if (WorstBodyVertex >= 0)
        {
            const auto* Visual = BoardingAvatar->GetProductionVisualActor();
            auto* PosedBody = Visual ? Visual->FindComponentByClass<UPoseableMeshComponent>() : nullptr;
            auto* Mesh = PosedBody ? Cast<USkeletalMesh>(PosedBody->GetSkinnedAsset()) : nullptr;
            const auto* Data = Mesh ? Mesh->GetResourceForRendering() : nullptr;
            const auto* Weights = PosedBody ? PosedBody->GetSkinWeightBuffer(0) : nullptr;
            if (TestTrue(TEXT("failing body vertex has skin influence data"),
                Data && !Data->LODRenderData.IsEmpty() && Weights))
            {
                const auto& LOD = Data->LODRenderData[0];
                int32 Section = INDEX_NONE, SectionVertex = INDEX_NONE;
                LOD.GetSectionFromVertexIndex(WorstBodyVertex, Section, SectionVertex);
                if (TestTrue(TEXT("failing vertex maps to render section"), LOD.RenderSections.IsValidIndex(Section)))
                {
                    const auto& BoneMap = LOD.RenderSections[Section].BoneMap;
                    for (uint32 I = 0; I < Weights->GetMaxBoneInfluences(); ++I)
                    {
                        const uint16 Weight = Weights->GetBoneWeight(WorstBodyVertex, I);
                        if (!Weight) continue;
                        const uint32 Bone = Weights->GetBoneIndex(WorstBodyVertex, I);
                        if (TestTrue(TEXT("vertex influence maps to skeleton"), BoneMap.IsValidIndex(Bone)))
                            AddInfo(FString::Printf(TEXT("BOARDING_BODY_INFLUENCE vertex=%d bone=%s weight_raw=%u"),
                                WorstBodyVertex, *Mesh->GetRefSkeleton().GetBoneName(BoneMap[Bone]).ToString(), Weight));
                    }
                }
            }
        }
        AddInfo(FString::Printf(TEXT("BOARDING_TRANSFER_BODY samples=%d max_top_envelope_deficit_cm=%.9f frame=%d vertex=%d point_local_cm=%s point_host_cm=%s"),
            BodyClearanceSamples, MaximumBodyDeficitCm, WorstBodyFrame, WorstBodyVertex, *WorstBodyPoint.ToString(), *WorstBodyHostPoint.ToString()));
        if (bStrictTransfer)
            TestTrue(TEXT("sampled skinned body remains above rendered raft envelope within 2cm"), MaximumBodyDeficitCm <= 2.);
        AddInfo(FString::Printf(TEXT("BOARDING_TRANSFER_BOOT samples=%d max_top_envelope_deficit_cm=%.9f frame=%d boot=%s point_local_cm=%s"),
            BootClearanceSamples, MaximumBootTopEnvelopeDeficitCm, WorstBootFrame, *WorstBootName, *WorstBootPoint.ToString()));
        if (FParse::Param(FCommandLine::Get(), TEXT("RaftSimRequireBoardingTransferClearance")))
            TestTrue(TEXT("transfer boot vertices remain above rendered upper envelope within 2cm"),
                MaximumBootTopEnvelopeDeficitCm <= 2.);
        TestTrue(TEXT("pull retains both hand controls at tube"), MaxPullHandGapCm < 5.);
        TestTrue(TEXT("pull preserves thigh and shin control spans"), MaxPullLegSpanErrorCm < .01);
        AddInfo(FString::Printf(TEXT("BOARDING_PULL_SUPPORT samples=%d max_both_gap_cm=%.9f max_leg_span_error_cm=%.9f"),
            PullSamples, MaxPullHandGapCm, MaxPullLegSpanErrorCm));
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
