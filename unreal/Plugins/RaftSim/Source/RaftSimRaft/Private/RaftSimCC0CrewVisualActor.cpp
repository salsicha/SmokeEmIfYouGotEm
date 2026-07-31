#include "RaftSimCC0CrewVisualActor.h"

#include "Components/PoseableMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInterface.h"

namespace
{
const TCHAR* GuideMeshPath = TEXT(
    "/Game/RaftSim/Characters/Production/CC0/SK_RaftSim_CC0_Guide."
    "SK_RaftSim_CC0_Guide");

const TCHAR* CrewMeshPaths[] = {
    TEXT("/Game/RaftSim/Characters/Production/CC0/SK_RaftSim_CC0_Crew01."
         "SK_RaftSim_CC0_Crew01"),
    TEXT("/Game/RaftSim/Characters/Production/CC0/SK_RaftSim_CC0_Crew02."
         "SK_RaftSim_CC0_Crew02"),
    TEXT("/Game/RaftSim/Characters/Production/CC0/SK_RaftSim_CC0_Crew03."
         "SK_RaftSim_CC0_Crew03"),
    TEXT("/Game/RaftSim/Characters/Production/CC0/SK_RaftSim_CC0_Crew04."
         "SK_RaftSim_CC0_Crew04")};

const FName DrivenBones[] = {
    TEXT("pelvis"),
    TEXT("spine_01"),
    TEXT("spine_02"),
    TEXT("spine_03"),
    TEXT("neck_01"),
    TEXT("head"),
    TEXT("clavicle_l"),
    TEXT("upperarm_l"),
    TEXT("lowerarm_l"),
    TEXT("hand_l"),
    TEXT("clavicle_r"),
    TEXT("upperarm_r"),
    TEXT("lowerarm_r"),
    TEXT("hand_r"),
    TEXT("thigh_l"),
    TEXT("calf_l"),
    TEXT("foot_l"),
    TEXT("thigh_r"),
    TEXT("calf_r"),
    TEXT("foot_r")};

void ApplyProductionBodyMaterialOverrides(
    UPoseableMeshComponent* Body,
    const USkeletalMesh* Mesh)
{
    if (Body == nullptr || Mesh == nullptr)
    {
        return;
    }
    UMaterialInterface* ProductionWetsuit = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Wetsuit.M_RaftSim_Wetsuit"));
    if (ProductionWetsuit == nullptr)
    {
        return;
    }
    const TArray<FSkeletalMaterial>& Slots = Mesh->GetMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < Slots.Num(); ++MaterialIndex)
    {
        const FString SlotName = Slots[MaterialIndex].MaterialSlotName.ToString();
        if (SlotName.Contains(TEXT("Wetsuit"), ESearchCase::IgnoreCase) &&
            Body->GetMaterial(MaterialIndex) != ProductionWetsuit)
        {
            // Keep each variant's rights-tracked skin, eye and hair atlases,
            // but replace the FBX's flat glossy neoprene with the same
            // physically scaled generated textile used by the production
            // fallback wardrobe. This is a presentation-only override.
            Body->SetMaterial(MaterialIndex, ProductionWetsuit);
        }
    }
}
}

ARaftSimCC0CrewVisualActor::ARaftSimCC0CrewVisualActor()
{
    PrimaryActorTick.bCanEverTick = false;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("CC0Root"));
    SetRootComponent(Root);
    Body = CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("CC0Body"));
    Body->SetupAttachment(Root);
    Body->SetRelativeScale3D(FVector(BodyScale));
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Body->SetCastShadow(true);
}

FString ARaftSimCC0CrewVisualActor::GetSelectedMeshPath() const
{
    return bCurrentGuide
        ? FString(GuideMeshPath)
        : FString(CrewMeshPaths[FMath::Clamp(CurrentVariantIndex, 0, 3)]);
}

bool ARaftSimCC0CrewVisualActor::EnsureBodyLoaded()
{
    if (!Body)
    {
        bBodyReady = false;
        return false;
    }
    USkeletalMesh* Mesh = LoadObject<USkeletalMesh>(nullptr, *GetSelectedMeshPath());
    if (!Mesh)
    {
        bBodyReady = false;
        Body->SetVisibility(false, true);
        return false;
    }
    bool bMeshChanged = false;
    if (Body->GetSkinnedAsset() != Mesh)
    {
        Body->SetSkinnedAssetAndUpdate(Mesh);
        Body->SetRelativeScale3D(FVector(BodyScale));
        bMeshChanged = true;
    }
    const int32 BoneCount = Mesh->GetRefSkeleton().GetNum();
    if (Body->GetBoneSpaceTransforms().Num() != BoneCount)
    {
        Body->AllocateTransformData();
    }
    if (Body->GetBoneSpaceTransforms().Num() != BoneCount)
    {
        bBodyReady = false;
        Body->SetVisibility(false, true);
        return false;
    }
    if (bMeshChanged || ReferenceComponentTransforms.IsEmpty())
    {
        CacheReferencePose();
    }
    ApplyProductionBodyMaterialOverrides(Body, Mesh);
    bBodyReady = ReferenceComponentTransforms.Num() >= 19;
    Body->SetVisibility(bBodyReady, true);
    return bBodyReady;
}

void ARaftSimCC0CrewVisualActor::CacheReferencePose()
{
    ReferenceComponentTransforms.Reset();
    if (!Body || !Body->GetSkinnedAsset())
    {
        return;
    }
    for (const FName BoneName : DrivenBones)
    {
        if (Body->GetBoneIndex(BoneName) != INDEX_NONE)
        {
            ReferenceComponentTransforms.Add(
                BoneName,
                Body->GetBoneTransformByName(BoneName, EBoneSpaces::ComponentSpace));
        }
    }
}

void ARaftSimCC0CrewVisualActor::ConfigureCrewAppearance_Implementation(
    int32 VariantIndex,
    int32 SeatSide,
    bool bGuide)
{
    CurrentVariantIndex = FMath::Abs(VariantIndex) % 4;
    bCurrentGuide = bGuide;
    if (!EnsureBodyLoaded())
    {
        return;
    }
    ApplyCrewPose_Implementation(
        ERaftSimCrewAvatarAction::SeatedIdle,
        0.0f,
        1.0f,
        SeatSide);
}

void ARaftSimCC0CrewVisualActor::ApplyCrewPose_Implementation(
    ERaftSimCrewAvatarAction Action,
    float NormalizedPhase,
    float Intensity,
    int32 SeatSide)
{
    if (!EnsureBodyLoaded())
    {
        return;
    }
    const float SafePhase = FMath::IsFinite(NormalizedPhase)
        ? FMath::Frac(NormalizedPhase * FMath::Clamp(Intensity, 0.15f, 2.0f))
        : 0.0f;
    ApplyBodyPose(URaftSimCrewAvatarPoseLibrary::EvaluatePose(Action, SafePhase, SeatSide));
}

FVector ARaftSimCC0CrewVisualActor::ToMeshSpace(const FVector& PointCm) const
{
    return PointCm / BodyScale;
}

void ARaftSimCC0CrewVisualActor::SetBoneAtPoint(
    FName BoneName,
    const FVector& DesiredPointCm)
{
    if (!Body || DesiredPointCm.ContainsNaN())
    {
        return;
    }
    const FTransform* Reference = ReferenceComponentTransforms.Find(BoneName);
    if (!Reference)
    {
        return;
    }
    FTransform Target = *Reference;
    Target.SetLocation(ToMeshSpace(DesiredPointCm));
    Body->SetBoneTransformByName(BoneName, Target, EBoneSpaces::ComponentSpace);
}

void ARaftSimCC0CrewVisualActor::SetSegmentBone(
    FName BoneName,
    FName ReferenceEndBone,
    const FVector& DesiredStartCm,
    const FVector& DesiredEndCm)
{
    if (!Body || DesiredStartCm.ContainsNaN() || DesiredEndCm.ContainsNaN())
    {
        return;
    }
    const FTransform* Reference = ReferenceComponentTransforms.Find(BoneName);
    const FTransform* ReferenceEnd = ReferenceComponentTransforms.Find(ReferenceEndBone);
    if (!Reference || !ReferenceEnd)
    {
        return;
    }
    FVector ReferenceDirection =
        (ReferenceEnd->GetLocation() - Reference->GetLocation()).GetSafeNormal();
    const FVector DesiredDirection = (DesiredEndCm - DesiredStartCm).GetSafeNormal();
    if (DesiredDirection.IsNearlyZero())
    {
        SetBoneAtPoint(BoneName, DesiredStartCm);
        return;
    }
    if (ReferenceDirection.IsNearlyZero())
    {
        // A terminal bone such as `head` has no child endpoint when it is
        // deliberately passed as its own reference end. Its arbitrary local
        // roll axis is not an anatomical up direction: MakeHuman's game-engine
        // head bone has local +Z close to horizontal after FBX conversion. Use
        // the authored parent-to-head shaft instead. That preserves the rest
        // basis while rotating the skull through the same high-side direction
        // as the project-owned helmet.
        const FName ParentBoneName = Body->GetParentBone(BoneName);
        if (const FTransform* ReferenceParent =
                ReferenceComponentTransforms.Find(ParentBoneName))
        {
            ReferenceDirection =
                (Reference->GetLocation() - ReferenceParent->GetLocation()).GetSafeNormal();
        }
    }
    if (ReferenceDirection.IsNearlyZero())
    {
        SetBoneAtPoint(BoneName, DesiredStartCm);
        return;
    }
    const FQuat Swing = FQuat::FindBetweenNormals(ReferenceDirection, DesiredDirection);
    FTransform Target = *Reference;
    Target.SetLocation(ToMeshSpace(DesiredStartCm));
    Target.SetRotation((Swing * Reference->GetRotation()).GetNormalized());
    Body->SetBoneTransformByName(BoneName, Target, EBoneSpaces::ComponentSpace);
}

void ARaftSimCC0CrewVisualActor::ApplyBodyPose(const FRaftSimCrewAvatarPose& Pose)
{
    const FVector HipCenter = (Pose.LeftHipCm + Pose.RightHipCm) * 0.5f;
    const FVector ShoulderCenter = (Pose.LeftShoulderCm + Pose.RightShoulderCm) * 0.5f;
    const FVector TorsoUp = Pose.TorsoRotation.Quaternion().RotateVector(FVector::UpVector);
    const FVector LowerSpine = FMath::Lerp(HipCenter, Pose.TorsoCenterCm, 0.38f);
    const FVector MidSpine = FMath::Lerp(HipCenter, ShoulderCenter, 0.55f);
    const FVector UpperSpine = FMath::Lerp(Pose.TorsoCenterCm, ShoulderCenter, 0.78f);
    const FVector NeckBase = ShoulderCenter + TorsoUp * 4.0f;
    const FVector HeadTop = Pose.HeadCenterCm + TorsoUp * 16.0f;

    SetSegmentBone(TEXT("pelvis"), TEXT("spine_01"), HipCenter, LowerSpine);
    SetSegmentBone(TEXT("spine_01"), TEXT("spine_02"), LowerSpine, MidSpine);
    SetSegmentBone(TEXT("spine_02"), TEXT("spine_03"), MidSpine, UpperSpine);
    SetSegmentBone(TEXT("spine_03"), TEXT("neck_01"), UpperSpine, NeckBase);
    SetSegmentBone(TEXT("neck_01"), TEXT("head"), NeckBase, Pose.HeadCenterCm);
    SetSegmentBone(TEXT("head"), TEXT("head"), Pose.HeadCenterCm, HeadTop);

    const FVector LeftElbow =
        FMath::Lerp(Pose.LeftShoulderCm, Pose.LeftHandCm, 0.48f) + FVector(0.0f, -5.0f, -2.0f);
    const FVector RightElbow =
        FMath::Lerp(Pose.RightShoulderCm, Pose.RightHandCm, 0.48f) + FVector(0.0f, 5.0f, -2.0f);
    SetSegmentBone(TEXT("clavicle_l"), TEXT("upperarm_l"), UpperSpine, Pose.LeftShoulderCm);
    SetSegmentBone(TEXT("upperarm_l"), TEXT("lowerarm_l"), Pose.LeftShoulderCm, LeftElbow);
    SetSegmentBone(TEXT("lowerarm_l"), TEXT("hand_l"), LeftElbow, Pose.LeftHandCm);
    SetBoneAtPoint(TEXT("hand_l"), Pose.LeftHandCm);
    SetSegmentBone(TEXT("clavicle_r"), TEXT("upperarm_r"), UpperSpine, Pose.RightShoulderCm);
    SetSegmentBone(TEXT("upperarm_r"), TEXT("lowerarm_r"), Pose.RightShoulderCm, RightElbow);
    SetSegmentBone(TEXT("lowerarm_r"), TEXT("hand_r"), RightElbow, Pose.RightHandCm);
    SetBoneAtPoint(TEXT("hand_r"), Pose.RightHandCm);

    SetSegmentBone(TEXT("thigh_l"), TEXT("calf_l"), Pose.LeftHipCm, Pose.LeftKneeCm);
    SetSegmentBone(TEXT("calf_l"), TEXT("foot_l"), Pose.LeftKneeCm, Pose.LeftFootCm);
    SetBoneAtPoint(TEXT("foot_l"), Pose.LeftFootCm);
    SetSegmentBone(TEXT("thigh_r"), TEXT("calf_r"), Pose.RightHipCm, Pose.RightKneeCm);
    SetSegmentBone(TEXT("calf_r"), TEXT("foot_r"), Pose.RightKneeCm, Pose.RightFootCm);
    SetBoneAtPoint(TEXT("foot_r"), Pose.RightFootCm);

    Body->SetBoneScaleByName(TEXT("foot_l"), FVector::ZeroVector, EBoneSpaces::ComponentSpace);
    Body->SetBoneScaleByName(TEXT("foot_r"), FVector::ZeroVector, EBoneSpaces::ComponentSpace);
    Body->RefreshBoneTransforms();
}

bool ARaftSimCC0CrewVisualActor::HasFinitePose() const
{
    if (!bBodyReady || !Body || Body->GetComponentTransform().ContainsNaN())
    {
        return false;
    }
    for (const FName BoneName : DrivenBones)
    {
        if (Body->GetBoneIndex(BoneName) != INDEX_NONE &&
            Body->GetBoneTransformByName(BoneName, EBoneSpaces::ComponentSpace).ContainsNaN())
        {
            return false;
        }
    }
    return true;
}
