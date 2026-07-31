#include "RaftSimMannyCrewVisualActor.h"

#include "Components/PoseableMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/Texture.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

namespace
{
const TCHAR* MannyMeshPath =
    TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple");

const FName MannyDrivenBones[] = {
    TEXT("pelvis"),
    TEXT("spine_01"),
    TEXT("spine_02"),
    TEXT("spine_03"),
    TEXT("neck_01"),
    TEXT("neck_02"),
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
}

ARaftSimMannyCrewVisualActor::ARaftSimMannyCrewVisualActor()
{
    PrimaryActorTick.bCanEverTick = false;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("MannyRoot"));
    SetRootComponent(Root);
    Body = CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("MannyBody"));
    Body->SetupAttachment(Root);
    Body->SetRelativeScale3D(FVector(BodyScale));
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Body->SetCastShadow(true);
}

bool ARaftSimMannyCrewVisualActor::EnsureBodyLoaded()
{
    if (!Body)
    {
        bBodyReady = false;
        return false;
    }
    if (!Body->GetSkinnedAsset())
    {
        USkeletalMesh* Mesh = LoadObject<USkeletalMesh>(nullptr, MannyMeshPath);
        if (!Mesh)
        {
            bBodyReady = false;
            Body->SetVisibility(false, true);
            return false;
        }
        Body->SetSkinnedAssetAndUpdate(Mesh);
        Body->SetRelativeScale3D(FVector(BodyScale));
        CacheReferencePose();
    }
    bBodyReady = ReferenceComponentTransforms.Num() >= 19;
    Body->SetVisibility(bBodyReady, true);
    return bBodyReady;
}

void ARaftSimMannyCrewVisualActor::CacheReferencePose()
{
    ReferenceComponentTransforms.Reset();
    if (!Body || !Body->GetSkinnedAsset())
    {
        return;
    }
    for (const FName BoneName : MannyDrivenBones)
    {
        if (Body->GetBoneIndex(BoneName) != INDEX_NONE)
        {
            ReferenceComponentTransforms.Add(
                BoneName,
                Body->GetBoneTransformByName(BoneName, EBoneSpaces::ComponentSpace));
        }
    }
}

void ARaftSimMannyCrewVisualActor::ConfigureCrewAppearance_Implementation(
    int32 VariantIndex,
    int32 SeatSide,
    bool bGuide)
{
    if (!EnsureBodyLoaded())
    {
        return;
    }

    const FLinearColor PaintTint = bGuide
        ? FLinearColor(0.004f, 0.022f, 0.035f, 1.0f)
        : (VariantIndex % 2 == 0
               ? FLinearColor(0.003f, 0.008f, 0.012f, 1.0f)
               : FLinearColor(0.002f, 0.003f, 0.004f, 1.0f));
    const FLinearColor LogoTint(0.004f, 0.006f, 0.008f, 1.0f);
    UTexture* NeutralBaseTexture = LoadObject<UTexture>(
        nullptr,
        TEXT("/Engine/EngineResources/Black.Black"));
    BodyMaterialInstances.Reset();
    const int32 MaterialCount = Body->GetNumMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
    {
        UMaterialInterface* Parent = Body->GetMaterial(MaterialIndex);
        if (UMaterialInstanceDynamic* Material =
                Parent ? UMaterialInstanceDynamic::Create(Parent, this) : nullptr)
        {
            if (NeutralBaseTexture)
            {
                // The template albedo bakes bright anatomical panel stripes.
                // A neutral black base lets Paint Tint read as continuous matte
                // river clothing while preserving the skeletal-safe parent,
                // normal response, and authored roughness parameters.
                Material->SetTextureParameterValue(TEXT("Base Texture"), NeutralBaseTexture);
            }
            Material->SetVectorParameterValue(TEXT("Paint Tint"), PaintTint);
            Material->SetVectorParameterValue(TEXT("LogoTint"), LogoTint);
            Material->SetVectorParameterValue(TEXT("Global BaseColor"), PaintTint);
            Material->SetVectorParameterValue(TEXT("Base Color"), PaintTint);
            Material->SetVectorParameterValue(TEXT("BaseColor"), PaintTint);
            Material->SetScalarParameterValue(TEXT("MetalPaintMetallic"), 0.0f);
            Material->SetScalarParameterValue(TEXT("MetalPaintRoughness"), 0.72f);
            Body->SetMaterial(MaterialIndex, Material);
            BodyMaterialInstances.Add(Material);
        }
    }

    ApplyCrewPose_Implementation(
        ERaftSimCrewAvatarAction::SeatedIdle,
        0.0f,
        1.0f,
        SeatSide);
}

void ARaftSimMannyCrewVisualActor::ApplyCrewPose_Implementation(
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

FVector ARaftSimMannyCrewVisualActor::ToMeshSpace(const FVector& PointCm) const
{
    return PointCm / BodyScale;
}

void ARaftSimMannyCrewVisualActor::SetBoneAtPoint(
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

void ARaftSimMannyCrewVisualActor::SetSegmentBone(
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
    const FVector ReferenceDirection =
        (ReferenceEnd->GetLocation() - Reference->GetLocation()).GetSafeNormal();
    const FVector DesiredDirection = (DesiredEndCm - DesiredStartCm).GetSafeNormal();
    if (ReferenceDirection.IsNearlyZero() || DesiredDirection.IsNearlyZero())
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

void ARaftSimMannyCrewVisualActor::ApplyBodyPose(const FRaftSimCrewAvatarPose& Pose)
{
    const FVector HipCenter = (Pose.LeftHipCm + Pose.RightHipCm) * 0.5f;
    const FVector ShoulderCenter = (Pose.LeftShoulderCm + Pose.RightShoulderCm) * 0.5f;
    const FVector TorsoUp = Pose.TorsoRotation.Quaternion().RotateVector(FVector::UpVector);
    const FVector LowerSpine = FMath::Lerp(HipCenter, Pose.TorsoCenterCm, 0.38f);
    const FVector MidSpine = FMath::Lerp(HipCenter, ShoulderCenter, 0.55f);
    const FVector UpperSpine = FMath::Lerp(Pose.TorsoCenterCm, ShoulderCenter, 0.78f);
    const FVector NeckBase = ShoulderCenter + TorsoUp * 4.0f;
    const FVector NeckTop = FMath::Lerp(NeckBase, Pose.HeadCenterCm, 0.58f);
    const FVector HeadTop = Pose.HeadCenterCm + TorsoUp * 16.0f;

    SetSegmentBone(TEXT("pelvis"), TEXT("spine_01"), HipCenter, LowerSpine);
    SetSegmentBone(TEXT("spine_01"), TEXT("spine_02"), LowerSpine, MidSpine);
    SetSegmentBone(TEXT("spine_02"), TEXT("spine_03"), MidSpine, UpperSpine);
    SetSegmentBone(TEXT("spine_03"), TEXT("neck_01"), UpperSpine, NeckBase);
    SetSegmentBone(TEXT("neck_01"), TEXT("neck_02"), NeckBase, NeckTop);
    SetSegmentBone(TEXT("neck_02"), TEXT("head"), NeckTop, Pose.HeadCenterCm);
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

    // Poseable meshes own their component-space transforms directly; the
    // generic skinned-component hidden-bone mask does not reliably remove
    // those surfaces after a pose write. Keep Manny's coherent head, neck,
    // and hands instead of layering the high-contrast procedural face over
    // them. Collapse only the feet because the host supplies river boots.
    const auto CollapseStockSurface = [this](const FName BoneName)
    {
        Body->SetBoneScaleByName(BoneName, FVector::ZeroVector, EBoneSpaces::ComponentSpace);
    };
    CollapseStockSurface(TEXT("foot_l"));
    CollapseStockSurface(TEXT("foot_r"));
}

bool ARaftSimMannyCrewVisualActor::HasFinitePose() const
{
    if (!bBodyReady || !Body || Body->GetComponentTransform().ContainsNaN())
    {
        return false;
    }
    for (const FName BoneName : MannyDrivenBones)
    {
        if (Body->GetBoneIndex(BoneName) != INDEX_NONE &&
            Body->GetBoneTransformByName(BoneName, EBoneSpaces::ComponentSpace).ContainsNaN())
        {
            return false;
        }
    }
    return true;
}
