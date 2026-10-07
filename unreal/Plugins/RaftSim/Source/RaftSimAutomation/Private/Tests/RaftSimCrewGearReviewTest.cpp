// Rendered close-up review of the paddling crew's gear and grips in the
// normal game world: each paddler's face and chin strap, shaft and T-grip
// hands, shoulders, feet and seat, plus the guide's own view and the stern
// where the throw bag rides. Frames are written only when
// -RaftSimCrewReviewDir= is given; the stroke and framing checks always run.
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"
#include "Components/PoseableMeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Engine/SkeletalMesh.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "RaftSimCC0CrewVisualActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "Tests/AutomationCommon.h"
#include "UnrealClient.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewGearReviewTest,
    "RaftSim.Crew.GearReview",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::ProductFilter)
namespace
{
UWorld* FindGameWorld()
{
    for (const auto& Context : GEngine->GetWorldContexts())
        if (Context.World() && (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
            return Context.World();
    return nullptr;
}

enum class EShot : uint8 { Face, Chin, GripOutboard, GripFront, TGrip, Shoulders, Feet, Seat, HipsBack, HipsOutboard, TopHand, ShaftHand, NeckBack, Count };
const TCHAR* ShotName(EShot Shot)
{
    static const TCHAR* Names[] = {TEXT("face"), TEXT("chin"), TEXT("grip-outboard"), TEXT("grip-front"),
        TEXT("tgrip"), TEXT("shoulders"), TEXT("feet"), TEXT("seat"), TEXT("hips-back"), TEXT("hips-outboard"),
        TEXT("top-hand"), TEXT("shaft-hand"), TEXT("neck-back")};
    return Names[uint8(Shot)];
}

// Whole-body framings of one seated crew member, all from out over the water
// so no other paddler stands between camera and subject: front three-quarter,
// side, rear three-quarter and high.
constexpr int32 PortraitShots = 4;
const TCHAR* PortraitName(int32 Shot)
{
    static const TCHAR* Names[] = {TEXT("front3q"), TEXT("side"), TEXT("rear3q"), TEXT("high")};
    return Names[Shot % PortraitShots];
}
// Torso is the pose's torso centre; the frame (45 deg FOV) runs from the seat
// to the helmet.
void FramePortrait(int32 Shot, const FVector& Torso, const FVector& Fwd, const FVector& Out, const FVector& Up,
    FVector& Eye, FVector& Focus)
{
    Focus = Torso + Up * 22.;
    switch (Shot % PortraitShots)
    {
    case 0: Eye = Focus + Fwd * 150. + Out * 130. + Up * 30.; break;
    case 1: Eye = Focus + Out * 205. + Fwd * 12. + Up * 12.; break;
    case 2: Eye = Focus - Fwd * 145. + Out * 145. + Up * 40.; break;
    default: Eye = Focus + Fwd * 95. + Out * 85. + Up * 170.; break;
    }
}

// Posed vertices whose strongest skin weight is on a bone Keep accepts.
TArray<FVector> DominantBoneVertices(const ARaftSimCC0CrewVisualActor* Visual, TFunctionRef<bool(const FString&)> Keep)
{
    TArray<FVector> Out;
    UPoseableMeshComponent* Body = Visual
        ? const_cast<ARaftSimCC0CrewVisualActor*>(Visual)->FindComponentByClass<UPoseableMeshComponent>() : nullptr;
    const USkeletalMesh* Mesh = Body ? Cast<USkeletalMesh>(Body->GetSkinnedAsset()) : nullptr;
    const FSkeletalMeshRenderData* Data = Mesh ? Mesh->GetResourceForRendering() : nullptr;
    const FSkinWeightVertexBuffer* Weights = Body ? Body->GetSkinWeightBuffer(0) : nullptr;
    if (!Data || Data->LODRenderData.IsEmpty() || !Weights) return Out;
    const FReferenceSkeleton& Ref = Mesh->GetRefSkeleton();
    const TArray<FVector> Posed = Visual->GetPosedBodyVerticesWorldCmForValidation();
    for (const FSkelMeshRenderSection& Section : Data->LODRenderData[0].RenderSections)
        for (uint32 V = Section.BaseVertexIndex; V < Section.BaseVertexIndex + Section.NumVertices && V < uint32(Posed.Num()); ++V)
        {
            int32 Best = INDEX_NONE; float BestWeight = 0.f;
            for (uint32 I = 0; I < Weights->GetMaxBoneInfluences(); ++I)
            {
                const float W = Weights->GetBoneWeight(V, I) / 65535.f;
                if (W > BestWeight) { BestWeight = W; Best = Weights->GetBoneIndex(V, I); }
            }
            if (Best != INDEX_NONE && Section.BoneMap.IsValidIndex(Best) && Keep(Ref.GetBoneName(Section.BoneMap[Best]).ToString()))
                Out.Add(Posed[V]);
        }
    return Out;
}

// Smallest gap (cm) between the skin of the T-grip hand and forearm and the
// skin of the head. Meshes that interpenetrate leave vertex pairs closer than
// their own spacing, so under about 1 cm reads as touching or inside.
double TopHandFaceGapCm(const ARaftSimCrewAvatarActor* Avatar)
{
    const auto* Visual = Cast<ARaftSimCC0CrewVisualActor>(Avatar->GetProductionVisualActor());
    if (!Visual) return TNumericLimits<double>::Max();
    const FRaftSimCrewAvatarPose& Pose = Avatar->GetPublishedCrewPose();
    const FString Suffix = FVector::DistSquared(Pose.LeftHandCm, Pose.PaddleTopCm) < FVector::DistSquared(Pose.RightHandCm, Pose.PaddleTopCm)
        ? TEXT("_l") : TEXT("_r");
    const TArray<FVector> Arm = DominantBoneVertices(Visual, [&Suffix](const FString& Bone)
    {
        return Bone.EndsWith(Suffix) && (Bone.StartsWith(TEXT("hand")) || Bone.StartsWith(TEXT("lowerarm")) ||
            Bone.StartsWith(TEXT("thumb")) || Bone.StartsWith(TEXT("index")) || Bone.StartsWith(TEXT("middle")) ||
            Bone.StartsWith(TEXT("ring")) || Bone.StartsWith(TEXT("pinky")));
    });
    const TArray<FVector> Head = DominantBoneVertices(Visual, [](const FString& Bone) { return Bone == TEXT("head"); });
    FBox ArmBox(Arm);
    ArmBox = ArmBox.ExpandBy(6.);
    double Gap = TNumericLimits<double>::Max();
    for (const FVector& H : Head)
    {
        if (!ArmBox.IsInside(H)) continue;
        for (const FVector& A : Arm) Gap = FMath::Min(Gap, FVector::Distance(H, A));
    }
    return Gap;
}

class FCrewGearReview final : public IAutomationLatentCommand
{
public:
    explicit FCrewGearReview(FAutomationTestBase* InTest) : Test(InTest) {}

    bool Update() override
    {
        UWorld* World = FindGameWorld();
        ARaftSimRaftActor* Raft = nullptr;
        if (World) for (TActorIterator<ARaftSimRaftActor> It(World); It; ++It) { Raft = *It; break; }
        APlayerController* Player = World ? UGameplayStatics::GetPlayerController(World, 0) : nullptr;
        if (!Raft || !Player) { Test->AddError(TEXT("Missing playable raft/controller")); return true; }
        const double Now = World->GetTimeSeconds();
        if (Start < 0.) Start = Now;
        if (!Camera)
        {
            Camera = World->SpawnActor<ACameraActor>();
            Player->SetViewTarget(Camera);
        }
        // Paddlers ordered bow to stern, then the guide (furthest aft).
        TArray<ARaftSimCrewAvatarActor*> Crew;
        for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It) Crew.Add(*It);
        const FTransform RaftFrame = Raft->GetActorTransform();
        Crew.Sort([&RaftFrame](const ARaftSimCrewAvatarActor& A, const ARaftSimCrewAvatarActor& B)
        { return RaftFrame.InverseTransformPosition(A.GetActorLocation()).X > RaftFrame.InverseTransformPosition(B.GetActorLocation()).X; });
        if (Crew.Num() < 5) { Test->AddError(FString::Printf(TEXT("Expected five crew, found %d"), Crew.Num())); return true; }
        if (Now - Start < 2.) { Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest); return false; }
        if (!bPaddling) { Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward); bPaddling = true; PaddleStart = Now; }
        if (Now - PaddleStart < 2.5) return false;

        FString Dir;
        const bool bCapture = FParse::Value(FCommandLine::Get(), TEXT("RaftSimCrewReviewDir="), Dir);
        const int32 PaddlerShots = 4 * int32(EShot::Count);
        // Whole-boat views after the per-paddler sweep: the guide's seat
        // looking forward (the default play view), the stern beside it, the
        // stowed throw bag (wide and close), the tied-off bow line (the hank
        // and the knot) and a side-tube D-ring.
        const int32 Total = PaddlerShots + 7;
        // Mid-stroke close-ups: every paddler held at the middle of the
        // power phase, with world time slowed to a crawl so all frames show
        // the same instant. (A paused world also stops the view following
        // the review camera.) Each hand from out over the water and from
        // ahead or above, then both hands together, then the whole paddler.
        constexpr int32 MidStrokeShots = 5 + PortraitShots;
        // Stroke sweep: every paddler held at twenty points round the forward
        // stroke, measuring how close the T-grip hand and forearm come to the
        // face. The hand must ride beside the face, never into the jaw.
        constexpr int32 SweepPhases = 20;
        // The guide's own first-person view while paddling: the player's
        // camera itself, in the guide's eye with the head hidden as in play,
        // with each stroke started through the same call the player's keys
        // make and filmed live. (The whole-boat "guide-view" sits 20 cm ahead
        // of the face, so it never showed an arm passing close to the eye.)
        struct FFirstPersonStroke { const TCHAR* Name; int32 Kind; float Scale; };
        static const FFirstPersonStroke FirstPersonStrokes[] = {
            {TEXT("forward"), 0, 1.0f}, {TEXT("back"), 0, -1.0f},
            {TEXT("steer-left"), 1, -1.0f}, {TEXT("steer-right"), 1, 1.0f}};
        constexpr int32 FirstPersonStrokeCount = UE_ARRAY_COUNT(FirstPersonStrokes);
        constexpr int32 FirstPersonFrames = 42, FirstPersonCaptureEvery = 6;
        if (ShotIndex >= Total && FirstPersonIndex <= FirstPersonStrokeCount)
        {
            UGameplayStatics::SetGlobalTimeDilation(World, 1.0f);
            ARaftSimCrewAvatarActor* Guide = Crew.Last();
            if (FirstPersonIndex == FirstPersonStrokeCount || !Player->GetPawn())
            {
                if (FramesOnShot == 0)
                {
                    for (int32 Stroke = 0; Stroke < FirstPersonStrokeCount; ++Stroke)
                        UE_LOG(LogTemp, Display, TEXT("CREW_FP_AUDIT stroke=%s max_arm_coverage=%.3f nearest_arm_cm=%.1f"),
                            FirstPersonStrokes[Stroke].Name, MaxFirstPersonCoverage[Stroke],
                            NearestFirstPersonArmCm[Stroke] == TNumericLimits<double>::Max() ? -1. : NearestFirstPersonArmCm[Stroke]);
                    Player->SetViewTarget(Camera);
                    Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
                }
                // Let the crew's reaction delay run out in live time: the held
                // stages after this freeze the clock, and an order still
                // pending then never lands (the crew sat at rest through them).
                if (++FramesOnShot >= 60)
                {
                    FirstPersonIndex = FirstPersonStrokeCount + 1;
                    FramesOnShot = 0;
                }
                return false;
            }
            const FFirstPersonStroke& Stroke = FirstPersonStrokes[FirstPersonIndex];
            if (Player->GetViewTarget() != Player->GetPawn()) Player->SetViewTarget(Player->GetPawn());
            Player->SetControlRotation(FRotator(-8., RaftFrame.Rotator().Yaw, 0.));
            if (FramesOnShot == 0)
            {
                Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
                if (Stroke.Kind == 0) Raft->ApplyPaddleStroke(ERaftSimPaddleSide::Both, Stroke.Scale);
                else Raft->ApplyGuideSteerStroke(Stroke.Scale);
            }
            // How much of the frame the guide's own arms fill, and how close
            // they come to the lens: each arm vertex in view splats a disc its
            // skin spacing wide onto a 48x27 grid.
            const FVector Eye = Player->PlayerCameraManager->GetCameraLocation();
            const FRotator View = Player->PlayerCameraManager->GetCameraRotation();
            const double HalfTan = FMath::Tan(FMath::DegreesToRadians(Player->PlayerCameraManager->GetFOVAngle() * 0.5));
            const auto* Visual = Cast<ARaftSimCC0CrewVisualActor>(Guide->GetProductionVisualActor());
            const TArray<FVector> Arms = DominantBoneVertices(Visual, [](const FString& Bone)
            {
                return Bone.StartsWith(TEXT("upperarm")) || Bone.StartsWith(TEXT("lowerarm")) || Bone.StartsWith(TEXT("hand")) ||
                    Bone.StartsWith(TEXT("thumb")) || Bone.StartsWith(TEXT("index")) || Bone.StartsWith(TEXT("middle")) ||
                    Bone.StartsWith(TEXT("ring")) || Bone.StartsWith(TEXT("pinky")) || Bone.StartsWith(TEXT("clavicle"));
            });
            const FMatrix ViewAxes = FRotationMatrix(View);
            const FVector F = ViewAxes.GetUnitAxis(EAxis::X), R = ViewAxes.GetUnitAxis(EAxis::Y), U = ViewAxes.GetUnitAxis(EAxis::Z);
            constexpr int32 GridW = 48, GridH = 27;
            TBitArray<> Covered(false, GridW * GridH);
            double Nearest = TNumericLimits<double>::Max();
            for (const FVector& P : Arms)
            {
                const FVector D = P - Eye;
                const double Depth = FVector::DotProduct(D, F);
                if (Depth < 1.) continue;
                // Screen x in [-1, 1] across the width; y scaled to 16:9.
                const double X = FVector::DotProduct(D, R) / Depth / HalfTan, Y = FVector::DotProduct(D, U) / Depth / HalfTan * (16. / 9.);
                if (FMath::Abs(X) > 1.05 || FMath::Abs(Y) > 1.05) continue;
                Nearest = FMath::Min(Nearest, D.Size());
                const double Splat = 1.6 / Depth / HalfTan * 0.5 * GridW;
                const int32 CX = int32((X * 0.5 + 0.5) * GridW), CY = int32((0.5 - Y * 0.5) * GridH);
                const int32 Reach = FMath::Clamp(int32(Splat), 0, 12);
                for (int32 GY = CY - Reach; GY <= CY + Reach; ++GY)
                    for (int32 GX = CX - Reach; GX <= CX + Reach; ++GX)
                        if (GX >= 0 && GX < GridW && GY >= 0 && GY < GridH && FMath::Square(GX - CX) + FMath::Square(GY - CY) <= FMath::Square(Reach) + 1)
                            Covered[GY * GridW + GX] = true;
            }
            int32 Cells = 0;
            for (int32 Cell = 0; Cell < GridW * GridH; ++Cell) Cells += Covered[Cell] ? 1 : 0;
            const double Coverage = Cells / double(GridW * GridH);
            MaxFirstPersonCoverage[FirstPersonIndex] = FMath::Max(MaxFirstPersonCoverage[FirstPersonIndex], Coverage);
            NearestFirstPersonArmCm[FirstPersonIndex] = FMath::Min(NearestFirstPersonArmCm[FirstPersonIndex], Nearest);
            if (FramesOnShot % FirstPersonCaptureEvery == 3)
            {
                UE_LOG(LogTemp, Display, TEXT("CREW_FP_FRAME stroke=%s frame=%d action=%d eye_lag_cm=%.1f arm_coverage=%.3f nearest_arm_cm=%.1f"),
                    Stroke.Name, FramesOnShot, int32(Guide->GetAvatarAction()),
                    FVector::Distance(Eye, Guide->GetFirstPersonEyeWorldLocationCm()), Coverage,
                    Nearest == TNumericLimits<double>::Max() ? -1. : Nearest);
                if (bCapture)
                {
                    IFileManager::Get().MakeDirectory(*Dir, true);
                    FScreenshotRequest::RequestScreenshot(
                        Dir / FString::Printf(TEXT("guide-fp-%s-%02d.png"), Stroke.Name, FramesOnShot), true, false);
                }
            }
            if (++FramesOnShot >= FirstPersonFrames) { FramesOnShot = 0; ++FirstPersonIndex; }
            return false;
        }
        if (ShotIndex >= Total && SweepIndex <= SweepPhases)
        {
            UGameplayStatics::SetGlobalTimeDilation(World, 0.0001f);
            if (SweepIndex == SweepPhases)
            {
                for (int32 Index = 0; Index < 4; ++Index)
                {
                    UE_LOG(LogTemp, Display, TEXT("CREW_FACE_AUDIT paddler=%d min_hand_face_gap_cm=%.2f at_phase=%.2f"),
                        Index + 1, MinHandFaceGapCm[Index], WorstHandFacePhase[Index]);
                    Test->TestTrue(FString::Printf(TEXT("paddler %d's T-grip hand stays out of the face through the stroke (%.2f cm at phase %.2f)"),
                        Index + 1, MinHandFaceGapCm[Index], WorstHandFacePhase[Index]), MinHandFaceGapCm[Index] > 1.0);
                }
                ++SweepIndex;
                return false;
            }
            const float Phase = SweepIndex / float(SweepPhases);
            for (int32 Index = 0; Index < 4; ++Index)
                Crew[Index]->SetAvatarActionPhaseForValidation(ERaftSimCrewAvatarAction::ForwardStroke, Phase);
            if (++FramesOnShot >= 2)
            {
                double Gaps[4];
                for (int32 Index = 0; Index < 4; ++Index)
                {
                    const double Gap = Gaps[Index] = TopHandFaceGapCm(Crew[Index]);
                    if (Gap < MinHandFaceGapCm[Index]) { MinHandFaceGapCm[Index] = Gap; WorstHandFacePhase[Index] = Phase; }
                }
                UE_LOG(LogTemp, Display, TEXT("CREW_FACE_SWEEP phase=%.2f gaps_cm=%.1f,%.1f,%.1f,%.1f"),
                    Phase, Gaps[0], Gaps[1], Gaps[2], Gaps[3]);
                FramesOnShot = 0;
                ++SweepIndex;
            }
            return false;
        }
        if (ShotIndex >= Total && !bMidStrokeDone)
        {
            const float Mid = 0.5f * (URaftSimCrewAvatarPoseLibrary::GetPaddlePowerPhaseStart() +
                URaftSimCrewAvatarPoseLibrary::GetPaddlePowerPhaseEnd());
            for (int32 Index = 0; Index < 4; ++Index)
                Crew[Index]->SetAvatarActionPhaseForValidation(ERaftSimCrewAvatarAction::ForwardStroke, Mid);
            if (!bMidStrokeHeld)
            {
                UGameplayStatics::SetGlobalTimeDilation(World, 0.0001f);
                bMidStrokeHeld = true;
            }
            if (MidStrokeShotIndex >= 4 * MidStrokeShots)
            {
                UGameplayStatics::SetGlobalTimeDilation(World, 1.f);
                bMidStrokeDone = true;
                return false;
            }
            const ARaftSimCrewAvatarActor* Avatar = Crew[MidStrokeShotIndex / MidStrokeShots];
            const auto* Visual = Cast<ARaftSimCC0CrewVisualActor>(Avatar->GetProductionVisualActor());
            UPoseableMeshComponent* Body = Visual ? Visual->FindComponentByClass<UPoseableMeshComponent>() : nullptr;
            const FRaftSimCrewAvatarPose& Pose = Avatar->GetPublishedCrewPose();
            const FVector Fwd = RaftFrame.GetUnitAxis(EAxis::X), Up = RaftFrame.GetUnitAxis(EAxis::Z);
            const double Side = RaftFrame.InverseTransformPosition(Avatar->GetActorLocation()).Y >= 0. ? 1. : -1.;
            const FVector Out = RaftFrame.GetUnitAxis(EAxis::Y) * Side;
            const bool bLeftTop = FVector::DistSquared(Pose.LeftHandCm, Pose.PaddleTopCm) < FVector::DistSquared(Pose.RightHandCm, Pose.PaddleTopCm);
            // The rendered hands: between each wrist and its middle knuckle.
            const auto HandAt = [&](bool bLeft)
            {
                if (!Body) return Avatar->GetActorTransform().TransformPosition(bLeft ? Pose.LeftHandCm : Pose.RightHandCm);
                const TCHAR* S = bLeft ? TEXT("l") : TEXT("r");
                return (Body->GetBoneLocationByName(FName(*FString::Printf(TEXT("hand_%s"), S)), EBoneSpaces::WorldSpace) +
                    Body->GetBoneLocationByName(FName(*FString::Printf(TEXT("middle_01_%s"), S)), EBoneSpaces::WorldSpace)) * .5;
            };
            const FVector Top = HandAt(bLeftTop), Shaft = HandAt(!bLeftTop);
            static const TCHAR* Names[] = {TEXT("top-hand-outboard"), TEXT("top-hand-above"), TEXT("shaft-hand-outboard"),
                TEXT("shaft-hand-front"), TEXT("top-hand-face")};
            FVector Eye, Focus;
            float Fov = 32.f;
            const int32 Shot = MidStrokeShotIndex % MidStrokeShots;
            FString ShotLabel = Shot < 5 ? FString(Names[Shot]) : FString::Printf(TEXT("body-%s"), PortraitName(Shot - 5));
            switch (Shot)
            {
            case 0: Focus = Top; Eye = Top + Out * 40. + Fwd * 30. + Up * 10.; break;
            case 1: Focus = Top; Eye = Top + Up * 42. + Fwd * 22. - Out * 12.; break;
            case 2: Focus = Shaft; Eye = Shaft + Out * 40. + Fwd * 24. + Up * 8.; break;
            case 3: Focus = Shaft; Eye = Shaft + Fwd * 42. + Out * 12. + Up * 6.; break;
            case 4:
            {
                // Straight in front of the face at hand height: the gap
                // between the T-grip hand and the jaw shows across the frame.
                const FVector Head = Avatar->GetActorTransform().TransformPosition(Pose.HeadCenterCm);
                Focus = (Top + Head) * .5;
                Eye = Focus + Fwd * 65. + Up * 4.;
                Fov = 40.f;
                break;
            }
            default:
                FramePortrait(Shot - 5, Avatar->GetActorTransform().TransformPosition(Pose.TorsoCenterCm),
                    Fwd, Out, Up, Eye, Focus);
                Fov = 45.f;
                break;
            }
            Camera->GetCameraComponent()->SetFieldOfView(Fov);
            Camera->SetActorLocationAndRotation(Eye, (Focus - Eye).Rotation());
            if (++FramesOnShot == 3 && bCapture)
            {
                IFileManager::Get().MakeDirectory(*Dir, true);
                FScreenshotRequest::RequestScreenshot(Dir / FString::Printf(TEXT("paddler%d-midstroke-%s.png"),
                    MidStrokeShotIndex / MidStrokeShots + 1, *ShotLabel), true, false);
            }
            if (FramesOnShot >= 5) { FramesOnShot = 0; ++MidStrokeShotIndex; }
            return false;
        }
        if (ShotIndex >= Total && !bResting)
        {
            Test->TestTrue(TEXT("crew kept stroking through the review"), Raft->GetCrewStrokeCatchCount() > 0);
            for (int32 Arm = 0; Arm < 8; ++Arm)
                UE_LOG(LogTemp, Display, TEXT("CREW_ARM_AUDIT paddler=%d hand=%s max_upper_stretch_cm=%.2f max_forearm_stretch_cm=%.2f"),
                    Arm / 2 + 1, Arm % 2 ? TEXT("r") : TEXT("l"), MaxUpperStretchCm[Arm], MaxForearmStretchCm[Arm]);
            // Then the crew rest, paddles across their laps.
            Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
            bResting = true;
            RestStart = Now;
            return false;
        }
        if (bResting)
        {
            if (Now - RestStart < 3.) return false;
            // Per paddler: the lap from above, the thighs from inboard, the
            // seat from behind and from outboard, then the whole paddler; then
            // the rear seats as the guide sees them over the stern.
            constexpr int32 RestShotsEach = 5 + PortraitShots;
            constexpr int32 RestPaddlerShots = 4 * RestShotsEach;
            if (RestShotIndex <= RestPaddlerShots)
            {
                FVector Eye, Focus;
                FString Name;
                const FVector Fwd = RaftFrame.GetUnitAxis(EAxis::X), Up = RaftFrame.GetUnitAxis(EAxis::Z);
                if (RestShotIndex < RestPaddlerShots)
                {
                    const ARaftSimCrewAvatarActor* Avatar = Crew[RestShotIndex / RestShotsEach];
                    const FTransform Frame = Avatar->GetActorTransform();
                    const FRaftSimCrewAvatarPose& Pose = Avatar->GetPublishedCrewPose();
                    const double Side = RaftFrame.InverseTransformPosition(Avatar->GetActorLocation()).Y >= 0. ? 1. : -1.;
                    const FVector Out = RaftFrame.GetUnitAxis(EAxis::Y) * Side;
                    const FVector Lap = Frame.TransformPosition((Pose.PaddleTopCm + Pose.PaddleBottomCm) * .5);
                    const FVector Seat = Frame.TransformPosition(Pose.TorsoCenterCm) - Up * 22.;
                    static const TCHAR* Names[] = {TEXT("rest-lap"), TEXT("rest-thighs"), TEXT("rest-hips-back"), TEXT("rest-hips-outboard"),
                        TEXT("rest-neck-back")};
                    const FVector Head = Frame.TransformPosition(Pose.HeadCenterCm);
                    const int32 Shot = RestShotIndex % RestShotsEach;
                    switch (Shot)
                    {
                    case 0: Focus = Lap; Eye = Lap + Fwd * 60. + Up * 55. - Out * 10.; break;
                    case 1: Focus = Lap - Up * 4.; Eye = Focus - Out * 70. + Fwd * 15. + Up * 6.; break;
                    case 2: Focus = Seat; Eye = Seat - Fwd * 75. + Up * 6.; break;
                    case 3: Focus = Seat; Eye = Seat + Out * 75. - Fwd * 12. + Up * 6.; break;
                    case 4: Focus = Head - Up * 12. - Fwd * 3.; Eye = Head - Fwd * 32. + Up * 38. + Out * 12.; break;
                    default:
                        FramePortrait(Shot - 5, Frame.TransformPosition(Pose.TorsoCenterCm), Fwd, Out, Up, Eye, Focus);
                        break;
                    }
                    Name = FString::Printf(TEXT("paddler%d-%s"), RestShotIndex / RestShotsEach + 1,
                        Shot < 5 ? Names[Shot] : *FString::Printf(TEXT("rest-body-%s"), PortraitName(Shot - 5)));
                }
                else
                {
                    const FVector Rear = (Crew[2]->GetActorLocation() + Crew[3]->GetActorLocation()) * .5 + Up * 45.;
                    Focus = Rear + Fwd * 70.; Eye = Rear - Fwd * 150. + Up * 85.;
                    Name = TEXT("rest-rear");
                }
                Camera->GetCameraComponent()->SetFieldOfView(45.f);
                Camera->SetActorLocationAndRotation(Eye, (Focus - Eye).Rotation());
                if (++FramesOnShot == 3 && bCapture)
                {
                    IFileManager::Get().MakeDirectory(*Dir, true);
                    FScreenshotRequest::RequestScreenshot(Dir / (Name + TEXT(".png")), true, false);
                }
                if (FramesOnShot >= 5) { FramesOnShot = 0; ++RestShotIndex; }
                return false;
            }
            // Resting lap clearance: how far the shaft and each hand's
            // fingertips sit above the thighs beneath them. Only vertices the
            // thighs carry count, so the forearms lying over the shaft do not.
            for (int32 Index = 0; Index < 4; ++Index)
            {
                const auto* Visual = Cast<ARaftSimCC0CrewVisualActor>(Crew[Index]->GetProductionVisualActor());
                UPoseableMeshComponent* Body = Visual ? const_cast<ARaftSimCC0CrewVisualActor*>(Visual)->FindComponentByClass<UPoseableMeshComponent>() : nullptr;
                const USkeletalMesh* Mesh = Body ? Cast<USkeletalMesh>(Body->GetSkinnedAsset()) : nullptr;
                const FSkeletalMeshRenderData* Data = Mesh ? Mesh->GetResourceForRendering() : nullptr;
                const FSkinWeightVertexBuffer* Weights = Body ? Body->GetSkinWeightBuffer(0) : nullptr;
                if (!Data || Data->LODRenderData.IsEmpty() || !Weights) continue;
                const FSkeletalMeshLODRenderData& LOD = Data->LODRenderData[0];
                const FReferenceSkeleton& Ref = Mesh->GetRefSkeleton();
                const TArray<FVector> Posed = Visual->GetPosedBodyVerticesWorldCmForValidation();
                TArray<FVector> Thigh;
                for (const FSkelMeshRenderSection& Section : LOD.RenderSections)
                    for (uint32 V = Section.BaseVertexIndex; V < Section.BaseVertexIndex + Section.NumVertices && V < uint32(Posed.Num()); ++V)
                    {
                        int32 Best = INDEX_NONE; float BestWeight = 0.f;
                        for (uint32 I = 0; I < Weights->GetMaxBoneInfluences(); ++I)
                        {
                            const float W = Weights->GetBoneWeight(V, I) / 65535.f;
                            if (W > BestWeight) { BestWeight = W; Best = Weights->GetBoneIndex(V, I); }
                        }
                        if (Best == INDEX_NONE || !Section.BoneMap.IsValidIndex(Best)) continue;
                        if (Ref.GetBoneName(Section.BoneMap[Best]).ToString().StartsWith(TEXT("thigh"))) Thigh.Add(Posed[V]);
                    }
                const FRaftSimCrewAvatarPose& Pose = Crew[Index]->GetPublishedCrewPose();
                const FTransform Frame = Crew[Index]->GetActorTransform();
                const FVector Up = RaftFrame.GetUnitAxis(EAxis::Z);
                // Height of a point above the thigh surface directly beneath it.
                const auto AboveThigh = [&Thigh, &Up](const FVector& P, double Radius)
                {
                    double Highest = -TNumericLimits<double>::Max();
                    for (const FVector& V : Thigh)
                    {
                        const FVector D = V - P;
                        const double H = FVector::DotProduct(D, Up);
                        if (H > -30. && H < 30. && (D - Up * H).Size() < Radius) Highest = FMath::Max(Highest, H);
                    }
                    return Highest > -TNumericLimits<double>::Max() ? -Highest : TNumericLimits<double>::Max();
                };
                const FVector Top = Frame.TransformPosition(Pose.PaddleTopCm), Bottom = Frame.TransformPosition(Pose.PaddleBottomCm);
                double Shaft = TNumericLimits<double>::Max();
                for (int32 Sample = 0; Sample <= 40; ++Sample)
                    Shaft = FMath::Min(Shaft, AboveThigh(FMath::Lerp(Top, Bottom, Sample / 40.), 2.5) - 1.65);
                double Fingers = TNumericLimits<double>::Max();
                for (const TCHAR* S : {TEXT("l"), TEXT("r")})
                    for (const TCHAR* Digit : {TEXT("thumb"), TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")})
                        for (int32 Segment = 1; Segment <= 3; ++Segment)
                            Fingers = FMath::Min(Fingers, AboveThigh(Body->GetBoneLocationByName(
                                FName(*FString::Printf(TEXT("%s_%02d_%s"), Digit, Segment, S)), EBoneSpaces::WorldSpace), 1.5) - 0.9);
                const FString FingerText = Fingers < 1.e6 ? FString::Printf(TEXT("%.2f"), Fingers) : FString(TEXT("none_over_thigh"));
                UE_LOG(LogTemp, Display, TEXT("CREW_REST_AUDIT paddler=%d shaft_above_thighs_cm=%.2f fingers_above_thighs_cm=%s"), Index + 1, Shaft, *FingerText);
                UE_LOG(LogTemp, Display, TEXT("CREW_GRIP_SOLVE rest paddler=%d palm_facing=%.3f finger_curl=%.3f wrist_twist_deg=%.1f anchor_cm=%.2f pad_cm=%.2f thumb_cm=%.2f"),
                    Index + 1, Visual->GetMinimumPaddlePalmFacingDot(), Visual->GetMinimumPaddleFingerCurlTowardPalm(),
                    Visual->GetMaximumGripWristTwistDegrees(), Visual->GetMaximumPaddleGripAnchorErrorCm(),
                    Visual->GetMaximumPaddleFingerContactErrorCm(), Visual->GetMaximumPaddleThumbContactErrorCm());
                Test->TestTrue(FString::Printf(TEXT("paddler %d's resting paddle lies on, not in, the thighs (%.2f cm)"), Index + 1, Shaft), Shaft > 0.);
                Test->TestTrue(FString::Printf(TEXT("paddler %d's resting hands stay out of the thighs (%.2f cm)"), Index + 1, Fingers), Fingers > 0.);
            }
            if (bCapture)
            {
                // Each rendered head in its fitted helmet's mesh frame, so the
                // retention straps can be routed clear of every face.
                for (int32 Index = 0; Index < Crew.Num(); ++Index)
                {
                    const auto* Visual = Cast<ARaftSimCC0CrewVisualActor>(Crew[Index]->GetProductionVisualActor());
                    TArray<UStaticMeshComponent*> Meshes;
                    Crew[Index]->GetComponents(Meshes);
                    UStaticMeshComponent** Helmet = Meshes.FindByPredicate([](const UStaticMeshComponent* M)
                    { return M->GetStaticMesh() && M->GetStaticMesh()->GetName() == TEXT("SM_RaftSim_WhitewaterHelmet"); });
                    if (!Visual || !Helmet) continue;
                    FString Csv = TEXT("x,y,z\n");
                    for (const FVector& P : Visual->GetPosedBodyVerticesWorldCmForValidation())
                    {
                        const FVector L = (*Helmet)->GetComponentTransform().InverseTransformPosition(P);
                        if (L.Size() < 26.) Csv += FString::Printf(TEXT("%.3f,%.3f,%.3f\n"), L.X, L.Y, L.Z);
                    }
                    FFileHelper::SaveStringToFile(Csv, *(Dir / FString::Printf(TEXT("head-vertices-%d.csv"), Index + 1)));
                    // The seated torso and waist in the vest mesh's own frame
                    // (scale included), so a vest or waist line can be fitted
                    // to every body: any vest surface must stay outside these.
                    UStaticMeshComponent** Vest = Meshes.FindByPredicate([](const UStaticMeshComponent* M)
                    { return M->GetStaticMesh() && M->GetStaticMesh()->GetName() == TEXT("SM_RaftSim_WhitewaterRescuePfd"); });
                    if (Vest)
                    {
                        const FBox VestBox = (*Vest)->GetStaticMesh()->GetBoundingBox().ExpandBy(FVector(10., 10., 16.));
                        FString Torso = TEXT("x,y,z\n");
                        for (const FVector& P : Visual->GetPosedBodyVerticesWorldCmForValidation())
                        {
                            const FVector L = (*Vest)->GetComponentTransform().InverseTransformPosition(P);
                            if (VestBox.IsInside(L)) Torso += FString::Printf(TEXT("%.3f,%.3f,%.3f\n"), L.X, L.Y, L.Z);
                        }
                        FFileHelper::SaveStringToFile(Torso, *(Dir / FString::Printf(TEXT("torso-vertices-%d.csv"), Index + 1)));
                        UE_LOG(LogTemp, Display, TEXT("CREW_VEST_FRAME paddler=%d scale=%s location=%s rotation=%s"), Index + 1,
                            *(*Vest)->GetRelativeScale3D().ToString(), *(*Vest)->GetRelativeLocation().ToString(), *(*Vest)->GetRelativeRotation().ToString());
                    }
                    // Hip-region skin and clothing: posed in the avatar frame
                    // beside each vertex's rest position, so a stray vertex can
                    // be traced back to its source mesh and weights.
                    UPoseableMeshComponent* Body = const_cast<ARaftSimCC0CrewVisualActor*>(Visual)->FindComponentByClass<UPoseableMeshComponent>();
                    const USkeletalMesh* Mesh = Body ? Cast<USkeletalMesh>(Body->GetSkinnedAsset()) : nullptr;
                    const FSkeletalMeshRenderData* Data = Mesh ? Mesh->GetResourceForRendering() : nullptr;
                    if (!Data || Data->LODRenderData.IsEmpty()) continue;
                    const FSkeletalMeshLODRenderData& LOD = Data->LODRenderData[0];
                    const TArray<FVector> Posed = Visual->GetPosedBodyVerticesWorldCmForValidation();
                    const FTransform AvatarFrame = Crew[Index]->GetActorTransform();
                    const FVector Pelvis = Crew[Index]->GetPublishedCrewPose().TorsoCenterCm - FVector(0, 0, 22);
                    FString Hips = TEXT("index,section,px,py,pz,rx,ry,rz\n");
                    for (const FSkelMeshRenderSection& Section : LOD.RenderSections)
                        for (uint32 V = Section.BaseVertexIndex; V < Section.BaseVertexIndex + Section.NumVertices && V < uint32(Posed.Num()); ++V)
                        {
                            const FVector P = AvatarFrame.InverseTransformPosition(Posed[V]);
                            if (FVector::Distance(P, Pelvis) > 45.) continue;
                            const FVector R(LOD.StaticVertexBuffers.PositionVertexBuffer.VertexPosition(V));
                            Hips += FString::Printf(TEXT("%u,%d,%.2f,%.2f,%.2f,%.3f,%.3f,%.3f\n"), V, Section.MaterialIndex, P.X, P.Y, P.Z, R.X, R.Y, R.Z);
                        }
                    FFileHelper::SaveStringToFile(Hips, *(Dir / FString::Printf(TEXT("hip-vertices-%d.csv"), Index + 1)));
                    // Every visible part's extent in the avatar frame, to tell
                    // which component reaches where the body does not.
                    TArray<UPrimitiveComponent*> Parts;
                    Crew[Index]->GetComponents(Parts);
                    TArray<UPrimitiveComponent*> VisualParts;
                    const_cast<ARaftSimCC0CrewVisualActor*>(Visual)->GetComponents(VisualParts);
                    Parts.Append(VisualParts);
                    for (const UPrimitiveComponent* Part : Parts)
                    {
                        if (!Part->IsVisible()) continue;
                        const FBox Box = Part->Bounds.GetBox().TransformBy(AvatarFrame.Inverse());
                        UE_LOG(LogTemp, Display, TEXT("CREW_PART paddler=%d part=%s class=%s min=%s max=%s"), Index + 1,
                            *Part->GetName(), *Part->GetClass()->GetName(), *Box.Min.ToCompactString(), *Box.Max.ToCompactString());
                    }
                }
            }
            return true;
        }
        {
            // Grip audit: which hand caps the T-grip, which way each rendered
            // palm faces, and whether the shaft hand's thumb points up the
            // shaft. Arm stretch is tracked over every paddling frame.
            const bool bLogGrip = ShotIndex == 0 && FramesOnShot == 0;
            if (bLogGrip)
                for (int32 Index = 0; Index + 1 < Crew.Num() && Index < 4; ++Index)
                    if (const auto* Visual = Cast<ARaftSimCC0CrewVisualActor>(Crew[Index]->GetProductionVisualActor()))
                        UE_LOG(LogTemp, Display, TEXT("CREW_GRIP_SOLVE paddler=%d palm_facing=%.3f finger_curl=%.3f wrist_twist_deg=%.1f anchor_cm=%.2f pad_cm=%.2f thumb_cm=%.2f"),
                            Index + 1, Visual->GetMinimumPaddlePalmFacingDot(), Visual->GetMinimumPaddleFingerCurlTowardPalm(),
                            Visual->GetMaximumGripWristTwistDegrees(), Visual->GetMaximumPaddleGripAnchorErrorCm(),
                            Visual->GetMaximumPaddleFingerContactErrorCm(), Visual->GetMaximumPaddleThumbContactErrorCm());
            for (int32 Index = 0; Index + 1 < Crew.Num() && Index < 4; ++Index)
            {
                const auto* Visual = Cast<ARaftSimCC0CrewVisualActor>(Crew[Index]->GetProductionVisualActor());
                UPoseableMeshComponent* Body = Visual ? Visual->FindComponentByClass<UPoseableMeshComponent>() : nullptr;
                if (!Body) continue;
                const FRaftSimCrewAvatarPose& Pose = Crew[Index]->GetPublishedCrewPose();
                const FTransform Frame = Crew[Index]->GetActorTransform();
                const FVector PaddleUp = Frame.TransformVector(Pose.PaddleTopCm - Pose.PaddleBottomCm).GetSafeNormal();
                for (const bool bLeft : {true, false})
                {
                    const TCHAR* S = bLeft ? TEXT("l") : TEXT("r");
                    const auto Bone = [Body, S](const TCHAR* Name)
                    { return Body->GetBoneLocationByName(FName(*FString::Printf(TEXT("%s_%s"), Name, S)), EBoneSpaces::WorldSpace); };
                    const FVector Width = (Bone(TEXT("index_01")) - Bone(TEXT("pinky_01"))).GetSafeNormal();
                    const FVector Fingers = (Bone(TEXT("middle_01")) - Bone(TEXT("hand"))).GetSafeNormal();
                    const FVector Palm = (bLeft ? FVector::CrossProduct(Width, Fingers) : FVector::CrossProduct(Fingers, Width)).GetSafeNormal();
                    const FVector Curl = (Bone(TEXT("middle_03")) - Bone(TEXT("middle_02"))).GetSafeNormal() -
                        (Bone(TEXT("middle_02")) - Bone(TEXT("middle_01"))).GetSafeNormal();
                    const FVector Hand = bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
                    if (bLogGrip)
                        UE_LOG(LogTemp, Display, TEXT("CREW_GRIP_AUDIT paddler=%d hand=%s to_tgrip_cm=%.2f palm_down=%.3f palm_curl=%.3f thumb_up_shaft=%.3f"),
                            Index + 1, S, FVector::Distance(Hand, Pose.PaddleTopCm), -Palm.Z, FVector::DotProduct(Palm, Curl),
                            FVector::DotProduct(Width, PaddleUp));
                    // How far each arm is pulled past its rest bone lengths.
                    const FReferenceSkeleton& Ref = Body->GetSkinnedAsset()->GetRefSkeleton();
                    TArray<FTransform> RefComponent;
                    for (int32 B = 0; B < Ref.GetNum(); ++B)
                    {
                        const int32 Parent = Ref.GetParentIndex(B);
                        RefComponent.Add(Parent == INDEX_NONE ? Ref.GetRefBonePose()[B] : Ref.GetRefBonePose()[B] * RefComponent[Parent]);
                    }
                    const auto RestCm = [&](const TCHAR* A, const TCHAR* Bn)
                    {
                        const int32 IA = Ref.FindBoneIndex(FName(*FString::Printf(TEXT("%s_%s"), A, S)));
                        const int32 IB = Ref.FindBoneIndex(FName(*FString::Printf(TEXT("%s_%s"), Bn, S)));
                        return IA == INDEX_NONE || IB == INDEX_NONE ? 0. : FVector::Distance(RefComponent[IA].GetLocation(), RefComponent[IB].GetLocation());
                    };
                    const int32 Arm = Index * 2 + (bLeft ? 0 : 1);
                    MaxUpperStretchCm[Arm] = FMath::Max(MaxUpperStretchCm[Arm], float(
                        FVector::Distance(Bone(TEXT("upperarm")), Bone(TEXT("lowerarm"))) - RestCm(TEXT("upperarm"), TEXT("lowerarm"))));
                    MaxForearmStretchCm[Arm] = FMath::Max(MaxForearmStretchCm[Arm], float(
                        FVector::Distance(Bone(TEXT("lowerarm")), Bone(TEXT("hand"))) - RestCm(TEXT("lowerarm"), TEXT("hand"))));
                }
            }
        }
        FVector Eye, Focus;
        float Fov = 40.f;
        FString Name;
        if (ShotIndex < PaddlerShots)
        {
            const ARaftSimCrewAvatarActor* Avatar = Crew[ShotIndex / int32(EShot::Count)];
            const EShot Shot = EShot(ShotIndex % int32(EShot::Count));
            const FTransform Frame = Avatar->GetActorTransform();
            const FRaftSimCrewAvatarPose& Pose = Avatar->GetPublishedCrewPose();
            const auto W = [&Frame](const FVector& Local) { return Frame.TransformPosition(Local); };
            const FVector Fwd = RaftFrame.GetUnitAxis(EAxis::X), Up = RaftFrame.GetUnitAxis(EAxis::Z);
            const double Side = RaftFrame.InverseTransformPosition(Avatar->GetActorLocation()).Y >= 0. ? 1. : -1.;
            const FVector Out = RaftFrame.GetUnitAxis(EAxis::Y) * Side;
            const FVector Head = W(Pose.HeadCenterCm), Torso = W(Pose.TorsoCenterCm);
            const FVector Hands = (W(Pose.LeftHandCm) + W(Pose.RightHandCm)) * .5;
            const FVector Feet = (W(Pose.LeftFootCm) + W(Pose.RightFootCm)) * .5;
            switch (Shot)
            {
            case EShot::Face: Focus = Head; Eye = Head + Fwd * 70. + Up * 4.; Fov = 30.f; break;
            case EShot::Chin: Focus = Head - Up * 9.; Eye = Head + Fwd * 45. - Up * 30. + Out * 10.; Fov = 35.f; break;
            case EShot::GripOutboard: Focus = Hands; Eye = Hands + Out * 120. + Fwd * 25. + Up * 15.; Fov = 45.f; break;
            case EShot::GripFront: Focus = Hands; Eye = Hands + Fwd * 115. + Out * 35. + Up * 25.; Fov = 45.f; break;
            case EShot::TGrip: Focus = W(Pose.PaddleTopCm); Eye = Focus + Up * 70. + Fwd * 35. - Out * 10.; Fov = 35.f; break;
            case EShot::Shoulders: Focus = Torso + Up * 20.; Eye = Torso - Fwd * 120. + Up * 85. - Out * 25.; Fov = 45.f; break;
            case EShot::Feet: Focus = Feet; Eye = Feet + Up * 75. - Out * 45. + Fwd * 20.; Fov = 40.f; break;
            case EShot::Seat: Focus = Torso - Up * 25.; Eye = Torso - Fwd * 85. - Up * 5. + Out * 35.; Fov = 45.f; break;
            case EShot::TopHand:
            case EShot::ShaftHand:
            {
                // Close on each hand from out over the water and a little ahead.
                const bool bLeftTop = FVector::DistSquared(Pose.LeftHandCm, Pose.PaddleTopCm) < FVector::DistSquared(Pose.RightHandCm, Pose.PaddleTopCm);
                const bool bLeftHand = (Shot == EShot::TopHand) == bLeftTop;
                Focus = W(bLeftHand ? Pose.LeftHandCm : Pose.RightHandCm);
                Eye = Focus + Out * 42. + Fwd * 28. + Up * 12.; Fov = 32.f;
                break;
            }
            case EShot::HipsBack: Focus = Torso - Up * 22.; Eye = Focus - Fwd * 75. + Up * 6.; Fov = 40.f; break;
            // The back of the neck where it meets the shoulders, as the guide
            // sees it from the stern.
            // Steeply down over the vest's back collar onto the nape; from
            // lower the vest hides the neck.
            case EShot::NeckBack: Focus = Head - Up * 12. - Fwd * 3.; Eye = Head - Fwd * 32. + Up * 38. + Out * 12.; Fov = 35.f; break;
            default: Focus = Torso - Up * 22.; Eye = Focus + Out * 75. - Fwd * 12. + Up * 6.; Fov = 40.f; break;
            }
            Name = FString::Printf(TEXT("paddler%d-%s"), ShotIndex / int32(EShot::Count) + 1, ShotName(Shot));
        }
        else
        {
            const ARaftSimCrewAvatarActor* Guide = Crew.Last();
            const FTransform Frame = Guide->GetActorTransform();
            const FRaftSimCrewAvatarPose& Pose = Guide->GetPublishedCrewPose();
            const FVector Fwd = RaftFrame.GetUnitAxis(EAxis::X), Up = RaftFrame.GetUnitAxis(EAxis::Z);
            const FVector Head = Frame.TransformPosition(Pose.HeadCenterCm);
            // Centre of one RaftGear section in the world.
            const auto GearCentre = [Raft](int32 SectionIndex, FVector Fallback)
            {
                TArray<UProceduralMeshComponent*> Gear;
                Raft->GetComponents(Gear);
                for (UProceduralMeshComponent* Mesh : Gear)
                {
                    const FProcMeshSection* Section = Mesh->GetName() == TEXT("RaftGear") ? Mesh->GetProcMeshSection(SectionIndex) : nullptr;
                    if (!Section || Section->ProcVertexBuffer.IsEmpty()) continue;
                    FVector Sum = FVector::ZeroVector;
                    for (const FProcMeshVertex& V : Section->ProcVertexBuffer) Sum += FVector(V.Position);
                    Fallback = Mesh->GetComponentTransform().TransformPosition(Sum / Section->ProcVertexBuffer.Num());
                }
                return Fallback;
            };
            if (ShotIndex == PaddlerShots)
            {
                Eye = Head + Fwd * 20. + Up * 12.; Focus = Eye + Fwd * 300. - Up * 70.; Fov = 70.f;
                Name = TEXT("guide-view");
            }
            else if (ShotIndex == PaddlerShots + 1)
            {
                Focus = Frame.TransformPosition(Pose.TorsoCenterCm) - Up * 35.;
                Eye = Focus + Fwd * 130. + Up * 95.; Fov = 50.f;
                Name = TEXT("stern");
            }
            else if (ShotIndex == PaddlerShots + 4)
            {
                // The bow line is section 3 of the raft's rigged gear.
                Focus = GearCentre(3, RaftFrame.TransformPosition(FVector(190., 0., 45.)));
                Eye = Focus - Fwd * 70. + Up * 45. + RaftFrame.GetUnitAxis(EAxis::Y) * 35.; Fov = 45.f;
                Name = TEXT("bowline");
            }
            else if (ShotIndex == PaddlerShots + 5)
            {
                // The standing part down the bow face to its knot on the grab line.
                Focus = GearCentre(3, RaftFrame.TransformPosition(FVector(190., 0., 45.))) + Fwd * 22. - Up * 14.;
                Eye = Focus + Fwd * 75. + Up * 20. + RaftFrame.GetUnitAxis(EAxis::Y) * 30.; Fov = 40.f;
                Name = TEXT("bowline-knot");
            }
            else if (ShotIndex == PaddlerShots + 6)
            {
                // A D-ring on the starboard tube: on its pad, webbing tabs
                // round its bar, the perimeter line through it.
                Focus = RaftFrame.TransformPosition(FVector(30., 98., 10.));
                Eye = Focus - Fwd * 30. + RaftFrame.GetUnitAxis(EAxis::Y) * 55. + Up * 18.; Fov = 40.f;
                Name = TEXT("dring");
            }
            else
            {
                // The stowed bag is section 0 of the raft's rigged gear: with
                // the guide, then close from inboard.
                const FVector Bag = GearCentre(0, Frame.TransformPosition(Pose.TorsoCenterCm));
                const double Side = RaftFrame.InverseTransformPosition(Bag).Y >= 0. ? 1. : -1.;
                const FVector Out = RaftFrame.GetUnitAxis(EAxis::Y) * Side;
                if (ShotIndex == PaddlerShots + 2)
                {
                    Focus = (Bag + Frame.TransformPosition(Pose.TorsoCenterCm)) * .5;
                    Eye = Focus + Fwd * 110. + Up * 80. - Out * 60.; Fov = 50.f;
                    Name = TEXT("throwbag");
                }
                else
                {
                    // Down from inboard, clear of the guide's legs.
                    Focus = Bag + Up * 4.;
                    Eye = Focus + Fwd * 18. + Up * 55. - Out * 42.; Fov = 45.f;
                    Name = TEXT("throwbag-close");
                }
            }
        }
        Camera->GetCameraComponent()->SetFieldOfView(Fov);
        Camera->SetActorLocationAndRotation(Eye, (Focus - Eye).Rotation());
        // Hold each framing a few frames so the screenshot sees it settled.
        if (++FramesOnShot == 3 && bCapture)
        {
            IFileManager::Get().MakeDirectory(*Dir, true);
            FScreenshotRequest::RequestScreenshot(Dir / (Name + TEXT(".png")), true, false);
        }
        if (FramesOnShot >= 5) { FramesOnShot = 0; ++ShotIndex; }
        return false;
    }

private:
    FAutomationTestBase* Test;
    ACameraActor* Camera = nullptr;
    double Start = -1., PaddleStart = 0.;
    bool bPaddling = false;
    int32 ShotIndex = 0, FramesOnShot = 0, RestShotIndex = 0, MidStrokeShotIndex = 0, SweepIndex = 0, FirstPersonIndex = 0;
    double MaxFirstPersonCoverage[4] = {}, NearestFirstPersonArmCm[4] = {TNumericLimits<double>::Max(), TNumericLimits<double>::Max(),
        TNumericLimits<double>::Max(), TNumericLimits<double>::Max()};
    double MinHandFaceGapCm[4] = {TNumericLimits<double>::Max(), TNumericLimits<double>::Max(),
        TNumericLimits<double>::Max(), TNumericLimits<double>::Max()};
    float WorstHandFacePhase[4] = {};
    bool bResting = false, bMidStrokeHeld = false, bMidStrokeDone = false;
    double RestStart = 0.;
    float MaxUpperStretchCm[8] = {}, MaxForearmStretchCm[8] = {};
};
}

bool FRaftSimCrewGearReviewTest::RunTest(const FString&)
{
    if (!AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"))) return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(4.f));
    FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FCrewGearReview>(this));
    return true;
}
#endif
