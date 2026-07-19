#include "RaftSimCrewAvatarActor.h"

#include "Components/SceneComponent.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"

namespace
{
constexpr float kBaseRadiusCm = 50.0f;

void BuildUnitOrganicMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents)
{
    constexpr int32 Rings = 10;
    constexpr int32 Sides = 14;
    for (int32 Ring = 0; Ring <= Rings; ++Ring)
    {
        const float V = static_cast<float>(Ring) / Rings;
        const float Phi = PI * V;
        const float Z = FMath::Cos(Phi);
        // Slightly relax the perfect sphere so limbs read as soft tissue.
        const float R = FMath::Pow(FMath::Max(FMath::Sin(Phi), 0.0f), 0.92f);
        for (int32 Side = 0; Side <= Sides; ++Side)
        {
            const float U = static_cast<float>(Side) / Sides;
            const float Theta = 2.0f * PI * U;
            const FVector Normal(R * FMath::Cos(Theta), R * FMath::Sin(Theta), Z);
            Vertices.Add(Normal * kBaseRadiusCm);
            Normals.Add(Normal.GetSafeNormal());
            UVs.Add(FVector2D(U, V));
            Tangents.Add(FProcMeshTangent(-FMath::Sin(Theta), FMath::Cos(Theta), 0.0f));
        }
    }
    for (int32 Ring = 0; Ring < Rings; ++Ring)
    {
        for (int32 Side = 0; Side < Sides; ++Side)
        {
            const int32 A = Ring * (Sides + 1) + Side;
            const int32 B = A + 1;
            const int32 C = A + Sides + 1;
            const int32 D = C + 1;
            Triangles.Append({A, C, B, B, C, D});
        }
    }
}

float StrokeWave(float Phase)
{
    return FMath::Sin(2.0f * PI * FMath::Frac(Phase));
}
}

FRaftSimCrewAvatarPose URaftSimCrewAvatarPoseLibrary::EvaluatePose(
    ERaftSimCrewAvatarAction Action,
    float NormalizedPhase,
    int32 SeatSide)
{
    const float Side = SeatSide < 0 ? -1.0f : 1.0f;
    const float Wave = StrokeWave(NormalizedPhase);
    FRaftSimCrewAvatarPose Pose;
    Pose.TorsoCenterCm = FVector(2.0f, 0.0f, 59.0f);
    Pose.HeadCenterCm = FVector(6.0f, 0.0f, 91.0f);
    Pose.LeftShoulderCm = FVector(4.0f, -17.0f, 76.0f);
    Pose.RightShoulderCm = FVector(4.0f, 17.0f, 76.0f);
    Pose.LeftHandCm = FVector(28.0f, -25.0f, 55.0f);
    Pose.RightHandCm = FVector(42.0f, 12.0f, 42.0f);
    Pose.LeftHipCm = FVector(-4.0f, -10.0f, 40.0f);
    Pose.RightHipCm = FVector(-4.0f, 10.0f, 40.0f);
    Pose.LeftKneeCm = FVector(22.0f, -14.0f, 21.0f);
    Pose.RightKneeCm = FVector(22.0f, 14.0f, 21.0f);
    Pose.LeftFootCm = FVector(45.0f, -17.0f, 8.0f);
    Pose.RightFootCm = FVector(45.0f, 17.0f, 8.0f);
    Pose.PaddleTopCm = FVector(25.0f, 25.0f * Side, 67.0f);
    Pose.PaddleBottomCm = FVector(65.0f, -42.0f * Side, -7.0f);

    switch (Action)
    {
        case ERaftSimCrewAvatarAction::ForwardStroke:
        {
            const float Reach = 14.0f * Wave;
            Pose.TorsoRotation.Pitch = -8.0f - 7.0f * Wave;
            Pose.TorsoCenterCm.X += 5.0f * Wave;
            Pose.LeftHandCm = Pose.PaddleTopCm + FVector(Reach, 0.0f, 0.0f);
            Pose.RightHandCm = FMath::Lerp(Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.43f) +
                FVector(Reach, 0.0f, 0.0f);
            Pose.PaddleTopCm.X += Reach;
            Pose.PaddleBottomCm.X -= 20.0f * Wave;
            break;
        }
        case ERaftSimCrewAvatarAction::BackStroke:
            Pose = EvaluatePose(ERaftSimCrewAvatarAction::ForwardStroke, -NormalizedPhase, SeatSide);
            Pose.TorsoRotation.Pitch *= -0.7f;
            break;
        case ERaftSimCrewAvatarAction::TurnLeft:
        case ERaftSimCrewAvatarAction::TurnRight:
        {
            const float Turn = Action == ERaftSimCrewAvatarAction::TurnLeft ? -1.0f : 1.0f;
            Pose.TorsoRotation.Yaw = Turn * (18.0f + 8.0f * Wave);
            Pose.PaddleBottomCm.Y = Turn * 58.0f;
            Pose.PaddleTopCm.Y = Turn * 20.0f;
            Pose.LeftHandCm = Pose.PaddleTopCm;
            Pose.RightHandCm = FMath::Lerp(Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.42f);
            break;
        }
        case ERaftSimCrewAvatarAction::Brace:
            Pose.TorsoCenterCm.Z -= 15.0f;
            Pose.HeadCenterCm.Z -= 15.0f;
            Pose.TorsoRotation.Pitch = 18.0f;
            Pose.PaddleTopCm = FVector(38.0f, -55.0f, 28.0f);
            Pose.PaddleBottomCm = FVector(38.0f, 55.0f, 20.0f);
            Pose.LeftHandCm = FMath::Lerp(Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.28f);
            Pose.RightHandCm = FMath::Lerp(Pose.PaddleTopCm, Pose.PaddleBottomCm, 0.72f);
            break;
        case ERaftSimCrewAvatarAction::HighSidePort:
        case ERaftSimCrewAvatarAction::HighSideStarboard:
        {
            const float Shift = Action == ERaftSimCrewAvatarAction::HighSidePort ? -1.0f : 1.0f;
            Pose.TorsoCenterCm.Y += Shift * 32.0f;
            Pose.HeadCenterCm.Y += Shift * 34.0f;
            Pose.TorsoRotation.Roll = -Shift * 28.0f;
            Pose.LeftHandCm.Y += Shift * 25.0f;
            Pose.RightHandCm.Y += Shift * 25.0f;
            Pose.bShowPaddle = false;
            break;
        }
        case ERaftSimCrewAvatarAction::Falling:
            Pose.TorsoCenterCm = FVector(18.0f, 0.0f, 48.0f);
            Pose.TorsoRotation = FRotator(55.0f, 10.0f * Wave, 38.0f);
            Pose.HeadCenterCm = FVector(34.0f, 4.0f, 52.0f);
            Pose.LeftHandCm = FVector(0.0f, -48.0f, 62.0f);
            Pose.RightHandCm = FVector(22.0f, 46.0f, 67.0f);
            Pose.bShowPaddle = false;
            break;
        case ERaftSimCrewAvatarAction::Swimming:
            Pose.TorsoCenterCm = FVector(0.0f, 0.0f, 12.0f + 2.0f * Wave);
            Pose.TorsoRotation = FRotator(0.0f, 88.0f, 0.0f);
            Pose.HeadCenterCm = FVector(28.0f, 0.0f, 18.0f + 2.0f * Wave);
            Pose.LeftShoulderCm = FVector(10.0f, -14.0f, 13.0f);
            Pose.RightShoulderCm = FVector(10.0f, 14.0f, 13.0f);
            Pose.LeftHandCm = FVector(35.0f + 18.0f * Wave, -25.0f, 8.0f);
            Pose.RightHandCm = FVector(35.0f - 18.0f * Wave, 25.0f, 8.0f);
            Pose.LeftHipCm = FVector(-22.0f, -8.0f, 10.0f);
            Pose.RightHipCm = FVector(-22.0f, 8.0f, 10.0f);
            Pose.LeftKneeCm = FVector(-48.0f, -13.0f, 7.0f + 8.0f * Wave);
            Pose.RightKneeCm = FVector(-48.0f, 13.0f, 7.0f - 8.0f * Wave);
            Pose.LeftFootCm = FVector(-75.0f, -14.0f, 8.0f);
            Pose.RightFootCm = FVector(-75.0f, 14.0f, 8.0f);
            Pose.bShowPaddle = false;
            break;
        case ERaftSimCrewAvatarAction::ReachRescue:
            Pose.TorsoRotation.Pitch = -28.0f;
            Pose.TorsoCenterCm.X += 12.0f;
            Pose.LeftHandCm = FVector(65.0f, -16.0f, 43.0f);
            Pose.RightHandCm = FVector(65.0f, 16.0f, 43.0f);
            Pose.bShowPaddle = false;
            break;
        case ERaftSimCrewAvatarAction::ThrowLine:
            Pose.TorsoRotation.Yaw = 18.0f * Side;
            Pose.LeftHandCm = FVector(18.0f, -10.0f * Side, 70.0f);
            Pose.RightHandCm = FVector(58.0f, 30.0f * Side, 86.0f + 8.0f * Wave);
            Pose.bShowPaddle = false;
            break;
        case ERaftSimCrewAvatarAction::Reentry:
            Pose.TorsoCenterCm = FVector(36.0f, 0.0f, 43.0f);
            Pose.TorsoRotation.Pitch = -58.0f;
            Pose.HeadCenterCm = FVector(55.0f, 0.0f, 57.0f);
            Pose.LeftHandCm = FVector(70.0f, -25.0f, 38.0f);
            Pose.RightHandCm = FVector(70.0f, 25.0f, 38.0f);
            Pose.bShowPaddle = false;
            break;
        case ERaftSimCrewAvatarAction::SeatedIdle:
        default:
            Pose.TorsoCenterCm.Z += 1.5f * Wave;
            Pose.HeadCenterCm.Z += 2.0f * Wave;
            break;
    }
    return Pose;
}

ARaftSimCrewAvatarActor::ARaftSimCrewAvatarActor()
{
    PrimaryActorTick.bCanEverTick = true;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("AvatarRoot"));
    SetRootComponent(Root);
}

void ARaftSimCrewAvatarActor::BeginPlay()
{
    Super::BeginPlay();
    BuildVisual();
}

void ARaftSimCrewAvatarActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const float CyclesPerSecond = CurrentAction == ERaftSimCrewAvatarAction::Swimming ? 0.8f : 1.25f;
    const float PhaseStep = DeltaSeconds * CyclesPerSecond * ActionIntensity;
    AnimationPhase = FMath::IsFinite(PhaseStep)
        ? FMath::Frac(AnimationPhase + PhaseStep)
        : 0.0f;
    ApplyPose(URaftSimCrewAvatarPoseLibrary::EvaluatePose(CurrentAction, AnimationPhase, SeatSide));
}

bool ARaftSimCrewAvatarActor::HasFiniteVisualTransforms() const
{
    if (GetActorTransform().ContainsNaN())
    {
        return false;
    }
    for (UProceduralMeshComponent* Part : BodyParts)
    {
        if (!Part || Part->GetRelativeTransform().ContainsNaN())
        {
            return false;
        }
        const FProcMeshSection* Section = Part->GetProcMeshSection(0);
        if (!Section)
        {
            return false;
        }
        for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
        {
            if (Vertex.Position.ContainsNaN() || Vertex.Normal.ContainsNaN() ||
                Vertex.Tangent.TangentX.ContainsNaN())
            {
                return false;
            }
        }
    }
    return true;
}

void ARaftSimCrewAvatarActor::SetAvatarAction(
    ERaftSimCrewAvatarAction NewAction,
    float Intensity)
{
    if (CurrentAction != NewAction)
    {
        CurrentAction = NewAction;
        AnimationPhase = 0.0f;
    }
    ActionIntensity = FMath::Clamp(Intensity, 0.15f, 2.0f);
}

void ARaftSimCrewAvatarActor::ConfigureAppearance(
    int32 InVariantIndex,
    int32 InSeatSide,
    bool bInGuide)
{
    VariantIndex = FMath::Abs(InVariantIndex) % 4;
    SeatSide = InSeatSide < 0 ? -1 : 1;
    bGuide = bInGuide;
    if (!bVisualBuilt)
    {
        return;
    }
    static const TCHAR* PfdPaths[] = {
        TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Red.M_RaftSim_PFD_Red"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Yellow.M_RaftSim_PFD_Yellow"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Blue.M_RaftSim_PFD_Blue")};
    if (Pfd)
    {
        Pfd->SetMaterial(0, LoadObject<UMaterialInterface>(nullptr, PfdPaths[VariantIndex]));
    }
}

UProceduralMeshComponent* ARaftSimCrewAvatarActor::CreateOrganicPart(
    const TCHAR* Name,
    UMaterialInterface* Material,
    int32 MaterialSlot)
{
    UProceduralMeshComponent* Part = NewObject<UProceduralMeshComponent>(this, FName(Name));
    Part->SetupAttachment(Root);
    Part->RegisterComponent();
    Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Part->SetCastShadow(true);
    Part->bUseAsyncCooking = true;
    TArray<FVector> Vertices, Normals;
    TArray<int32> Triangles;
    TArray<FVector2D> UVs;
    TArray<FProcMeshTangent> Tangents;
    TArray<FLinearColor> Colors;
    BuildUnitOrganicMesh(Vertices, Triangles, Normals, UVs, Tangents);
    Part->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, Colors, Tangents, false);
    if (Material)
    {
        Part->SetMaterial(MaterialSlot, Material);
    }
    BodyParts.Add(Part);
    return Part;
}

void ARaftSimCrewAvatarActor::BuildVisual()
{
    if (bVisualBuilt)
    {
        return;
    }
    auto Mat = [](const TCHAR* Path)
    { return LoadObject<UMaterialInterface>(nullptr, Path); };
    UMaterialInterface* Wetsuit = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_Wetsuit.M_RaftSim_Wetsuit"));
    UMaterialInterface* Skin = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_Skin.M_RaftSim_Skin"));
    UMaterialInterface* HelmetMat = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet.M_RaftSim_Helmet"));
    UMaterialInterface* Shaft = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft"));
    UMaterialInterface* Blade = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleBlade.M_RaftSim_PaddleBlade"));
    UMaterialInterface* DefaultPfd = Mat(TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD"));

    Pelvis = CreateOrganicPart(TEXT("Pelvis"), Wetsuit);
    Torso = CreateOrganicPart(TEXT("Torso"), Wetsuit);
    Pfd = CreateOrganicPart(TEXT("PFD"), DefaultPfd);
    Head = CreateOrganicPart(TEXT("Head"), Skin);
    Helmet = CreateOrganicPart(TEXT("Helmet"), HelmetMat);
    LeftUpperArm = CreateOrganicPart(TEXT("LeftUpperArm"), Wetsuit);
    LeftLowerArm = CreateOrganicPart(TEXT("LeftLowerArm"), Wetsuit);
    RightUpperArm = CreateOrganicPart(TEXT("RightUpperArm"), Wetsuit);
    RightLowerArm = CreateOrganicPart(TEXT("RightLowerArm"), Wetsuit);
    LeftThigh = CreateOrganicPart(TEXT("LeftThigh"), Wetsuit);
    LeftShin = CreateOrganicPart(TEXT("LeftShin"), Wetsuit);
    RightThigh = CreateOrganicPart(TEXT("RightThigh"), Wetsuit);
    RightShin = CreateOrganicPart(TEXT("RightShin"), Wetsuit);
    PaddleShaft = CreateOrganicPart(TEXT("PaddleShaft"), Shaft);
    PaddleBlade = CreateOrganicPart(TEXT("PaddleBlade"), Blade);
    bVisualBuilt = true;
    ConfigureAppearance(VariantIndex, SeatSide, bGuide);
    ApplyPose(URaftSimCrewAvatarPoseLibrary::EvaluatePose(CurrentAction, 0.0f, SeatSide));
}

void ARaftSimCrewAvatarActor::SetEllipsoid(
    UProceduralMeshComponent* Component,
    const FVector& CenterCm,
    const FRotator& Rotation,
    const FVector& RadiusCm)
{
    if (!Component)
    {
        return;
    }
    const FVector SafeCenter = CenterCm.ContainsNaN() ? FVector::ZeroVector : CenterCm;
    const FRotator SafeRotation = Rotation.ContainsNaN() ? FRotator::ZeroRotator : Rotation;
    const FVector SafeRadius(
        FMath::IsFinite(RadiusCm.X) ? FMath::Max(FMath::Abs(RadiusCm.X), 0.1f) : 1.0f,
        FMath::IsFinite(RadiusCm.Y) ? FMath::Max(FMath::Abs(RadiusCm.Y), 0.1f) : 1.0f,
        FMath::IsFinite(RadiusCm.Z) ? FMath::Max(FMath::Abs(RadiusCm.Z), 0.1f) : 1.0f);
    Component->SetRelativeLocationAndRotation(SafeCenter, SafeRotation);
    Component->SetRelativeScale3D(SafeRadius / kBaseRadiusCm);
}

void ARaftSimCrewAvatarActor::SetRoundedLimb(
    UProceduralMeshComponent* Component,
    const FVector& StartCm,
    const FVector& EndCm,
    float RadiusCm)
{
    const FVector Delta = EndCm - StartCm;
    const FVector SafeDirection = Delta.ContainsNaN() || Delta.IsNearlyZero()
        ? FVector::UpVector
        : Delta.GetSafeNormal();
    SetEllipsoid(
        Component,
        (StartCm + EndCm) * 0.5f,
        FRotationMatrix::MakeFromZ(SafeDirection).Rotator(),
        FVector(
            RadiusCm,
            RadiusCm,
            FMath::Max(Delta.ContainsNaN() ? RadiusCm : Delta.Size() * 0.5f, RadiusCm)));
}

void ARaftSimCrewAvatarActor::ApplyPose(const FRaftSimCrewAvatarPose& Pose)
{
    if (!bVisualBuilt)
    {
        return;
    }
    const FVector HipCenter = (Pose.LeftHipCm + Pose.RightHipCm) * 0.5f;
    SetEllipsoid(Pelvis, HipCenter, Pose.TorsoRotation, FVector(14.0f, 18.0f, 14.0f));
    SetEllipsoid(Torso, Pose.TorsoCenterCm, Pose.TorsoRotation, FVector(17.0f, 21.0f, 27.0f));
    SetEllipsoid(Pfd, Pose.TorsoCenterCm + FVector(1.5f, 0.0f, 2.0f), Pose.TorsoRotation,
                 FVector(20.0f, 24.0f, 21.0f));
    SetEllipsoid(Head, Pose.HeadCenterCm, Pose.TorsoRotation, FVector(11.0f, 10.0f, 13.0f));
    SetEllipsoid(Helmet, Pose.HeadCenterCm + FVector(0.0f, 0.0f, 5.0f), Pose.TorsoRotation,
                 FVector(12.5f, 11.5f, 10.5f));

    const FVector LeftElbow = FMath::Lerp(Pose.LeftShoulderCm, Pose.LeftHandCm, 0.48f) + FVector(0.0f, -5.0f, -2.0f);
    const FVector RightElbow = FMath::Lerp(Pose.RightShoulderCm, Pose.RightHandCm, 0.48f) + FVector(0.0f, 5.0f, -2.0f);
    SetRoundedLimb(LeftUpperArm, Pose.LeftShoulderCm, LeftElbow, 5.8f);
    SetRoundedLimb(LeftLowerArm, LeftElbow, Pose.LeftHandCm, 5.0f);
    SetRoundedLimb(RightUpperArm, Pose.RightShoulderCm, RightElbow, 5.8f);
    SetRoundedLimb(RightLowerArm, RightElbow, Pose.RightHandCm, 5.0f);
    SetRoundedLimb(LeftThigh, Pose.LeftHipCm, Pose.LeftKneeCm, 8.3f);
    SetRoundedLimb(LeftShin, Pose.LeftKneeCm, Pose.LeftFootCm, 6.7f);
    SetRoundedLimb(RightThigh, Pose.RightHipCm, Pose.RightKneeCm, 8.3f);
    SetRoundedLimb(RightShin, Pose.RightKneeCm, Pose.RightFootCm, 6.7f);

    PaddleShaft->SetVisibility(Pose.bShowPaddle);
    PaddleBlade->SetVisibility(Pose.bShowPaddle);
    if (Pose.bShowPaddle)
    {
        SetRoundedLimb(PaddleShaft, Pose.PaddleTopCm, Pose.PaddleBottomCm, 2.2f);
        const FVector Direction = (Pose.PaddleBottomCm - Pose.PaddleTopCm).GetSafeNormal();
        SetEllipsoid(
            PaddleBlade,
            Pose.PaddleBottomCm + Direction * 11.0f,
            FRotationMatrix::MakeFromZ(Direction).Rotator(),
            FVector(10.0f, 2.2f, 15.0f));
    }
}
