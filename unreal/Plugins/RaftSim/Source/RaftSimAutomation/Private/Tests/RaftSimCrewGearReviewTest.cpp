// Rendered close-up review of the paddling crew's gear and grips in the
// normal game world: each paddler's face and chin strap, shaft and T-grip
// hands, shoulders, feet and seat, plus the guide's own view and the stern
// where the throw bag rides. Frames are written only when
// -RaftSimCrewReviewDir= is given; the stroke and framing checks always run.
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
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

enum class EShot : uint8 { Face, Chin, GripOutboard, GripFront, TGrip, Shoulders, Feet, Seat, HipsBack, HipsOutboard, TopHand, ShaftHand, Count };
const TCHAR* ShotName(EShot Shot)
{
    static const TCHAR* Names[] = {TEXT("face"), TEXT("chin"), TEXT("grip-outboard"), TEXT("grip-front"),
        TEXT("tgrip"), TEXT("shoulders"), TEXT("feet"), TEXT("seat"), TEXT("hips-back"), TEXT("hips-outboard"),
        TEXT("top-hand"), TEXT("shaft-hand")};
    return Names[uint8(Shot)];
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
        // looking forward (the default play view), the stern beside it, and
        // the stowed throw bag.
        const int32 Total = PaddlerShots + 3;
        // Mid-stroke close-ups: every paddler held at the middle of the
        // power phase, with world time slowed to a crawl so all frames show
        // the same instant. (A paused world also stops the view following
        // the review camera.) Each hand from out over the water and from
        // ahead or above, then both hands together.
        constexpr int32 MidStrokeShots = 5;
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
                TEXT("shaft-hand-front"), TEXT("hands")};
            FVector Eye, Focus;
            float Fov = 32.f;
            switch (MidStrokeShotIndex % MidStrokeShots)
            {
            case 0: Focus = Top; Eye = Top + Out * 40. + Fwd * 30. + Up * 10.; break;
            case 1: Focus = Top; Eye = Top + Up * 42. + Fwd * 22. - Out * 12.; break;
            case 2: Focus = Shaft; Eye = Shaft + Out * 40. + Fwd * 24. + Up * 8.; break;
            case 3: Focus = Shaft; Eye = Shaft + Fwd * 42. + Out * 12. + Up * 6.; break;
            default: Focus = (Top + Shaft) * .5; Eye = Focus + Out * 95. + Fwd * 55. + Up * 20.; Fov = 42.f; break;
            }
            Camera->GetCameraComponent()->SetFieldOfView(Fov);
            Camera->SetActorLocationAndRotation(Eye, (Focus - Eye).Rotation());
            if (++FramesOnShot == 3 && bCapture)
            {
                IFileManager::Get().MakeDirectory(*Dir, true);
                FScreenshotRequest::RequestScreenshot(Dir / FString::Printf(TEXT("paddler%d-midstroke-%s.png"),
                    MidStrokeShotIndex / MidStrokeShots + 1, Names[MidStrokeShotIndex % MidStrokeShots]), true, false);
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
            // seat from behind and from outboard; then the rear seats as the
            // guide sees them over the stern.
            constexpr int32 RestPaddlerShots = 4 * 4;
            if (RestShotIndex <= RestPaddlerShots)
            {
                FVector Eye, Focus;
                FString Name;
                const FVector Fwd = RaftFrame.GetUnitAxis(EAxis::X), Up = RaftFrame.GetUnitAxis(EAxis::Z);
                if (RestShotIndex < RestPaddlerShots)
                {
                    const ARaftSimCrewAvatarActor* Avatar = Crew[RestShotIndex / 4];
                    const FTransform Frame = Avatar->GetActorTransform();
                    const FRaftSimCrewAvatarPose& Pose = Avatar->GetPublishedCrewPose();
                    const double Side = RaftFrame.InverseTransformPosition(Avatar->GetActorLocation()).Y >= 0. ? 1. : -1.;
                    const FVector Out = RaftFrame.GetUnitAxis(EAxis::Y) * Side;
                    const FVector Lap = Frame.TransformPosition((Pose.PaddleTopCm + Pose.PaddleBottomCm) * .5);
                    const FVector Seat = Frame.TransformPosition(Pose.TorsoCenterCm) - Up * 22.;
                    static const TCHAR* Names[] = {TEXT("rest-lap"), TEXT("rest-thighs"), TEXT("rest-hips-back"), TEXT("rest-hips-outboard")};
                    switch (RestShotIndex % 4)
                    {
                    case 0: Focus = Lap; Eye = Lap + Fwd * 60. + Up * 55. - Out * 10.; break;
                    case 1: Focus = Lap - Up * 4.; Eye = Focus - Out * 70. + Fwd * 15. + Up * 6.; break;
                    case 2: Focus = Seat; Eye = Seat - Fwd * 75. + Up * 6.; break;
                    default: Focus = Seat; Eye = Seat + Out * 75. - Fwd * 12. + Up * 6.; break;
                    }
                    Name = FString::Printf(TEXT("paddler%d-%s"), RestShotIndex / 4 + 1, Names[RestShotIndex % 4]);
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
            else
            {
                // The stowed bag is section 0 of the raft's rigged gear.
                FVector Bag = Frame.TransformPosition(Pose.TorsoCenterCm);
                TArray<UProceduralMeshComponent*> Gear;
                Raft->GetComponents(Gear);
                for (UProceduralMeshComponent* Mesh : Gear)
                {
                    const FProcMeshSection* Section = Mesh->GetName() == TEXT("RaftGear") ? Mesh->GetProcMeshSection(0) : nullptr;
                    if (!Section || Section->ProcVertexBuffer.IsEmpty()) continue;
                    FVector Sum = FVector::ZeroVector;
                    for (const FProcMeshVertex& V : Section->ProcVertexBuffer) Sum += FVector(V.Position);
                    Bag = Mesh->GetComponentTransform().TransformPosition(Sum / Section->ProcVertexBuffer.Num());
                }
                Focus = (Bag + Frame.TransformPosition(Pose.TorsoCenterCm)) * .5;
                Eye = Focus + Fwd * 110. + Up * 80. - RaftFrame.GetUnitAxis(EAxis::Y) * 60.; Fov = 50.f;
                Name = TEXT("throwbag");
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
    int32 ShotIndex = 0, FramesOnShot = 0, RestShotIndex = 0, MidStrokeShotIndex = 0;
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
