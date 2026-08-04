#include "RaftSimCC0CrewVisualActor.h"

#include "Components/PoseableMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInterface.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"

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

// Measured from the rigid eye surfaces in the hash-locked source FBXs. Whole
// head-section bounds include identity-dependent neck vertices and shift by
// more than 20 cm; the eye-line is stable and the host's authored 9.5 cm lift
// then places the whitewater shell at the crown.
const FVector GuideHeadLocalEyeCenterCm(0.0f, 3.810171f, 8.598805f);
const FVector CrewHeadLocalEyeCentersCm[] = {
    FVector(0.0f, 3.965670f, 7.931258f),
    FVector(0.0f, 3.460583f, 7.402065f),
    FVector(0.0f, 2.782320f, 7.364698f),
    FVector(0.0f, 4.179949f, 7.215961f)};

// Capture-fitted correction from the rendered eye-line to the helmet anchor.
// The guide and first crew identity have longer face-to-crown proportions than
// the common shell reference; the other three already seat at the brow.
constexpr float GuideHelmetAnchorDropCm = 5.0f;
const float CrewHelmetAnchorDropsCm[] = {6.0f, 9.0f, 9.0f, 7.0f};

constexpr float PaddlePalmAnchorAlongKnuckleFraction = 0.56f;

const TCHAR* CC0GripDigits[] = {
    TEXT("thumb"), TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")};

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

FVector ARaftSimCC0CrewVisualActor::GetSolvedHeadWorldLocation() const
{
    if (!bBodyReady || !Body || Body->GetBoneIndex(TEXT("head")) == INDEX_NONE)
    {
        return GetActorLocation();
    }
    FVector RenderedEyeCenterWorld;
    if (TryGetRenderedFaceEyeCenterWorld(RenderedEyeCenterWorld))
    {
        const float AnchorDropCm = bCurrentGuide
            ? GuideHelmetAnchorDropCm
            : CrewHelmetAnchorDropsCm[FMath::Clamp(CurrentVariantIndex, 0, 3)];
        return RenderedEyeCenterWorld -
            GetSolvedFaceUpWorldVector() * AnchorDropCm;
    }
    const FTransform HeadTransform = Body->GetBoneTransformByName(
        TEXT("head"), EBoneSpaces::ComponentSpace);
    const FVector LocalEyeCenterCm = bCurrentGuide
        ? GuideHeadLocalEyeCenterCm
        : CrewHeadLocalEyeCentersCm[FMath::Clamp(CurrentVariantIndex, 0, 3)];
    return Body->GetComponentTransform().TransformPosition(
        HeadTransform.TransformPosition(LocalEyeCenterCm / BodyScale));
}

FVector ARaftSimCC0CrewVisualActor::GetSolvedFaceForwardWorldVector() const
{
    if (!bBodyReady || !Body || Body->GetBoneIndex(TEXT("head")) == INDEX_NONE)
    {
        return GetActorForwardVector();
    }
    const FTransform HeadTransform = Body->GetBoneTransformByName(
        TEXT("head"), EBoneSpaces::ComponentSpace);
    // Unreal's FBX conversion makes MPFB head-local -Z point through the
    // rendered face and local -Y point through the crown. Publish that authored
    // frame so asymmetric helmet geometry cannot inherit torso-only yaw or
    // present its solid rear bowl toward the guide camera.
    return Body->GetComponentTransform().TransformVectorNoScale(
        HeadTransform.GetRotation().RotateVector(-FVector::UpVector)).GetSafeNormal();
}

FVector ARaftSimCC0CrewVisualActor::GetSolvedFaceUpWorldVector() const
{
    if (!bBodyReady || !Body || Body->GetBoneIndex(TEXT("head")) == INDEX_NONE)
    {
        return GetActorUpVector();
    }
    const FTransform HeadTransform = Body->GetBoneTransformByName(
        TEXT("head"), EBoneSpaces::ComponentSpace);
    return Body->GetComponentTransform().TransformVectorNoScale(
        HeadTransform.GetRotation().RotateVector(-FVector::YAxisVector)).GetSafeNormal();
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
    RenderedFaceAnchorVertexIndices.Reset();
    if (!Body || !Body->GetSkinnedAsset())
    {
        return;
    }
    const FReferenceSkeleton& ReferenceSkeleton =
        Body->GetSkinnedAsset()->GetRefSkeleton();
    for (int32 BoneIndex = 0; BoneIndex < ReferenceSkeleton.GetNum(); ++BoneIndex)
    {
        const FName BoneName = ReferenceSkeleton.GetBoneName(BoneIndex);
        if (Body->GetBoneIndex(BoneName) != INDEX_NONE)
        {
            ReferenceComponentTransforms.Add(
                BoneName,
                Body->GetBoneTransformByName(BoneName, EBoneSpaces::ComponentSpace));
        }
    }
    CacheRenderedFaceAnchorVertices();
}

bool ARaftSimCC0CrewVisualActor::HasArticulatedPaddleGripRig() const
{
    if (!bBodyReady || !Body)
    {
        return false;
    }
    for (const TCHAR* Side : {TEXT("l"), TEXT("r")})
    {
        for (const TCHAR* Digit : CC0GripDigits)
        {
            for (int32 Segment = 1; Segment <= 3; ++Segment)
            {
                const FName BoneName(*FString::Printf(
                    TEXT("%s_%02d_%s"), Digit, Segment, Side));
                if (!ReferenceComponentTransforms.Contains(BoneName))
                {
                    return false;
                }
            }
        }
    }
    return true;
}

void ARaftSimCC0CrewVisualActor::CacheRenderedFaceAnchorVertices()
{
    if (!Body)
    {
        return;
    }
    USkeletalMesh* Mesh = Cast<USkeletalMesh>(Body->GetSkinnedAsset());
    FSkeletalMeshRenderData* RenderData = Mesh ? Mesh->GetResourceForRendering() : nullptr;
    if (!Mesh || !RenderData || RenderData->LODRenderData.IsEmpty())
    {
        return;
    }

    int32 EyeMaterialIndex = INDEX_NONE;
    const TArray<FSkeletalMaterial>& Materials = Mesh->GetMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < Materials.Num(); ++MaterialIndex)
    {
        if (Materials[MaterialIndex].MaterialSlotName.ToString().Contains(
                TEXT("Eyes"), ESearchCase::IgnoreCase))
        {
            EyeMaterialIndex = MaterialIndex;
            break;
        }
    }
    if (EyeMaterialIndex == INDEX_NONE)
    {
        return;
    }

    const FSkeletalMeshLODRenderData& LODData = RenderData->LODRenderData[0];
    for (const FSkelMeshRenderSection& Section : LODData.RenderSections)
    {
        if (Section.MaterialIndex != EyeMaterialIndex)
        {
            continue;
        }
        const uint32 EndVertex = Section.BaseVertexIndex + Section.NumVertices;
        for (uint32 VertexIndex = Section.BaseVertexIndex; VertexIndex < EndVertex; ++VertexIndex)
        {
            RenderedFaceAnchorVertexIndices.Add(static_cast<int32>(VertexIndex));
        }
    }
}

bool ARaftSimCC0CrewVisualActor::TryGetRenderedFaceEyeCenterWorld(
    FVector& OutWorldLocation) const
{
    if (!Body || RenderedFaceAnchorVertexIndices.IsEmpty())
    {
        return false;
    }
    USkeletalMesh* Mesh = Cast<USkeletalMesh>(Body->GetSkinnedAsset());
    FSkeletalMeshRenderData* RenderData = Mesh ? Mesh->GetResourceForRendering() : nullptr;
    FSkinWeightVertexBuffer* SkinWeights = Body->GetSkinWeightBuffer(0);
    if (!RenderData || RenderData->LODRenderData.IsEmpty() || !SkinWeights)
    {
        return false;
    }
    const FSkeletalMeshLODRenderData& LODData = RenderData->LODRenderData[0];
    TArray<FMatrix44f> CachedRefToLocals;
    Body->CacheRefToLocalMatrices(CachedRefToLocals);
    FVector ComponentCenter = FVector::ZeroVector;
    for (const int32 VertexIndex : RenderedFaceAnchorVertexIndices)
    {
        ComponentCenter += FVector(USkinnedMeshComponent::GetSkinnedVertexPosition(
            Body,
            VertexIndex,
            LODData,
            *SkinWeights,
            CachedRefToLocals));
    }
    ComponentCenter /= RenderedFaceAnchorVertexIndices.Num();
    OutWorldLocation = Body->GetComponentTransform().TransformPosition(ComponentCenter);
    return !OutWorldLocation.ContainsNaN();
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

    // The pose contract publishes palm/grip targets while the imported hand
    // bone is a wrist pivot. Offset each wrist by its own hash-locked reference
    // palm vector so the visible knuckle plane, not the wrist, meets the
    // side-correct paddle handle.
    const FVector LeftWristCm = Pose.bShowPaddle
        ? ResolvePaddleGripWristCm(true, Pose, Pose.LeftHandCm)
        : Pose.LeftHandCm;
    const FVector RightWristCm = Pose.bShowPaddle
        ? ResolvePaddleGripWristCm(false, Pose, Pose.RightHandCm)
        : Pose.RightHandCm;
    const FVector LeftElbow =
        FMath::Lerp(Pose.LeftShoulderCm, LeftWristCm, 0.48f) +
        FVector(0.0f, -5.0f, -2.0f);
    const FVector RightElbow =
        FMath::Lerp(Pose.RightShoulderCm, RightWristCm, 0.48f) +
        FVector(0.0f, 5.0f, -2.0f);
    SetSegmentBone(TEXT("clavicle_l"), TEXT("upperarm_l"), UpperSpine, Pose.LeftShoulderCm);
    SetSegmentBone(TEXT("upperarm_l"), TEXT("lowerarm_l"), Pose.LeftShoulderCm, LeftElbow);
    SetSegmentBone(TEXT("lowerarm_l"), TEXT("hand_l"), LeftElbow, LeftWristCm);
    if (Pose.bShowPaddle)
    {
        SetPaddleGripHandTransform(true, Pose, LeftWristCm);
    }
    else
    {
        SetBoneAtPoint(TEXT("hand_l"), LeftWristCm);
    }
    SetSegmentBone(TEXT("clavicle_r"), TEXT("upperarm_r"), UpperSpine, Pose.RightShoulderCm);
    SetSegmentBone(TEXT("upperarm_r"), TEXT("lowerarm_r"), Pose.RightShoulderCm, RightElbow);
    SetSegmentBone(TEXT("lowerarm_r"), TEXT("hand_r"), RightElbow, RightWristCm);
    if (Pose.bShowPaddle)
    {
        SetPaddleGripHandTransform(false, Pose, RightWristCm);
    }
    else
    {
        SetBoneAtPoint(TEXT("hand_r"), RightWristCm);
    }

    SetSegmentBone(TEXT("thigh_l"), TEXT("calf_l"), Pose.LeftHipCm, Pose.LeftKneeCm);
    SetSegmentBone(TEXT("calf_l"), TEXT("foot_l"), Pose.LeftKneeCm, Pose.LeftFootCm);
    SetBoneAtPoint(TEXT("foot_l"), Pose.LeftFootCm);
    SetSegmentBone(TEXT("thigh_r"), TEXT("calf_r"), Pose.RightHipCm, Pose.RightKneeCm);
    SetSegmentBone(TEXT("calf_r"), TEXT("foot_r"), Pose.RightKneeCm, Pose.RightFootCm);
    SetBoneAtPoint(TEXT("foot_r"), Pose.RightFootCm);

    Body->SetBoneScaleByName(TEXT("foot_l"), FVector::ZeroVector, EBoneSpaces::ComponentSpace);
    Body->SetBoneScaleByName(TEXT("foot_r"), FVector::ZeroVector, EBoneSpaces::ComponentSpace);
    Body->RefreshBoneTransforms();
    ApplyPaddleGripPose(Pose);
    Body->RefreshBoneTransforms();
    bPaddleGripActive = Pose.bShowPaddle && HasArticulatedPaddleGripRig();
    MaximumPaddleGripAnchorErrorCm = bPaddleGripActive
        ? FMath::Max(
              MeasurePaddleGripAnchorErrorCm(true, Pose.LeftHandCm),
              MeasurePaddleGripAnchorErrorCm(false, Pose.RightHandCm))
        : 0.0f;
    MinimumUpperPaddleFingerClosureDegrees = bPaddleGripActive
        ? MeasureMinimumPaddleFingerClosureDegrees(Pose, true)
        : 0.0f;
    MinimumLowerPaddleFingerClosureDegrees = bPaddleGripActive
        ? MeasureMinimumPaddleFingerClosureDegrees(Pose, false)
        : 0.0f;
    MinimumPaddleThumbClosureDegrees = bPaddleGripActive
        ? MeasureMinimumPaddleThumbClosureDegrees()
        : 0.0f;
}

FVector ARaftSimCC0CrewVisualActor::ResolvePaddleGripWristCm(
    bool bLeft,
    const FRaftSimCrewAvatarPose& Pose,
    const FVector& DesiredGripCm) const
{
    const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
    const FName HandName(*FString::Printf(TEXT("hand_%s"), Side));
    const FName PalmAnchorName(*FString::Printf(TEXT("middle_01_%s"), Side));
    const FTransform* ReferenceHand = ReferenceComponentTransforms.Find(HandName);
    const FTransform* ReferencePalm = ReferenceComponentTransforms.Find(PalmAnchorName);
    if (!ReferenceHand || !ReferencePalm)
    {
        return DesiredGripCm;
    }
    const FVector ReferencePalmOffsetCm =
        (ReferencePalm->GetLocation() - ReferenceHand->GetLocation()) *
        BodyScale * PaddlePalmAnchorAlongKnuckleFraction;
    const FQuat TargetHandRotation = ResolvePaddleGripHandRotation(bLeft, Pose);
    const FQuat HandDelta =
        (TargetHandRotation * ReferenceHand->GetRotation().Inverse()).GetNormalized();
    return DesiredGripCm - HandDelta.RotateVector(ReferencePalmOffsetCm);
}

FQuat ARaftSimCC0CrewVisualActor::ResolvePaddleGripHandRotation(
    bool bLeft,
    const FRaftSimCrewAvatarPose& Pose) const
{
    const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
    const FName HandName(*FString::Printf(TEXT("hand_%s"), Side));
    const FName IndexName(*FString::Printf(TEXT("index_01_%s"), Side));
    const FName MiddleName(*FString::Printf(TEXT("middle_01_%s"), Side));
    const FName PinkyName(*FString::Printf(TEXT("pinky_01_%s"), Side));
    const FTransform* ReferenceHand = ReferenceComponentTransforms.Find(HandName);
    const FTransform* ReferenceIndex = ReferenceComponentTransforms.Find(IndexName);
    const FTransform* ReferenceMiddle = ReferenceComponentTransforms.Find(MiddleName);
    const FTransform* ReferencePinky = ReferenceComponentTransforms.Find(PinkyName);
    if (!ReferenceHand || !ReferenceIndex || !ReferenceMiddle || !ReferencePinky)
    {
        return ReferenceHand ? ReferenceHand->GetRotation() : FQuat::Identity;
    }
    const FVector ReferenceWidth =
        (ReferenceIndex->GetLocation() - ReferencePinky->GetLocation()).GetSafeNormal();
    const FVector ReferenceForward =
        (ReferenceMiddle->GetLocation() - ReferenceHand->GetLocation()).GetSafeNormal();
    const FVector ReferenceNormal = FVector::CrossProduct(
        ReferenceWidth, ReferenceForward).GetSafeNormal();
    const FVector GripCenterCm = bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
    FVector DesiredWidth = ResolvePaddleGripAxis(Pose, GripCenterCm).GetSafeNormal();
    const FVector ShoulderCm = bLeft ? Pose.LeftShoulderCm : Pose.RightShoulderCm;
    const FVector PalmApproachCm = IsUpperTGrip(Pose, GripCenterCm)
        ? ShoulderCm - GripCenterCm
        : GripCenterCm - ShoulderCm;
    FVector DesiredNormal = FVector::VectorPlaneProject(
        PalmApproachCm, DesiredWidth).GetSafeNormal();
    if (ReferenceWidth.IsNearlyZero() || ReferenceNormal.IsNearlyZero() ||
        DesiredWidth.IsNearlyZero())
    {
        return ReferenceHand->GetRotation();
    }
    if (DesiredNormal.IsNearlyZero())
    {
        DesiredNormal = FVector::VectorPlaneProject(
            FVector::UpVector, DesiredWidth).GetSafeNormal(
                SMALL_NUMBER, FVector::ForwardVector);
    }
    const FQuat ReferenceBasis = FRotationMatrix::MakeFromXZ(
        ReferenceWidth, ReferenceNormal).ToQuat();
    const FQuat DesiredBasis = FRotationMatrix::MakeFromXZ(
        DesiredWidth, DesiredNormal).ToQuat();
    const FQuat BasisDelta =
        (DesiredBasis * ReferenceBasis.Inverse()).GetNormalized();
    return (BasisDelta * ReferenceHand->GetRotation()).GetNormalized();
}

void ARaftSimCC0CrewVisualActor::SetPaddleGripHandTransform(
    bool bLeft,
    const FRaftSimCrewAvatarPose& Pose,
    const FVector& WristCm)
{
    if (!Body)
    {
        return;
    }
    const FName HandName(*FString::Printf(
        TEXT("hand_%s"), bLeft ? TEXT("l") : TEXT("r")));
    const FTransform* ReferenceHand = ReferenceComponentTransforms.Find(HandName);
    if (!ReferenceHand)
    {
        return;
    }
    FTransform Target = *ReferenceHand;
    Target.SetLocation(ToMeshSpace(WristCm));
    Target.SetRotation(ResolvePaddleGripHandRotation(bLeft, Pose));
    Body->SetBoneTransformByName(HandName, Target, EBoneSpaces::ComponentSpace);
}

FVector ARaftSimCC0CrewVisualActor::ResolvePaddleGripAxis(
    const FRaftSimCrewAvatarPose& Pose,
    const FVector& DesiredGripCm) const
{
    const FVector ShaftAxis =
        (Pose.PaddleBottomCm - Pose.PaddleTopCm).GetSafeNormal();
    if (ShaftAxis.IsNearlyZero())
    {
        return FVector::UpVector;
    }
    if (IsUpperTGrip(Pose, DesiredGripCm))
    {
        FVector TGripAxis = FVector::CrossProduct(ShaftAxis, FVector::UpVector)
            .GetSafeNormal();
        if (TGripAxis.IsNearlyZero())
        {
            TGripAxis = FVector::CrossProduct(ShaftAxis, FVector::ForwardVector)
                .GetSafeNormal();
        }
        return TGripAxis.IsNearlyZero() ? FVector::RightVector : TGripAxis;
    }
    return ShaftAxis;
}

bool ARaftSimCC0CrewVisualActor::IsUpperTGrip(
    const FRaftSimCrewAvatarPose& Pose,
    const FVector& DesiredGripCm) const
{
    return FVector::DistSquared(DesiredGripCm, Pose.PaddleTopCm) <= 4.0f;
}

float ARaftSimCC0CrewVisualActor::MeasurePaddleGripAnchorErrorCm(
    bool bLeft,
    const FVector& DesiredGripCm) const
{
    if (!Body)
    {
        return TNumericLimits<float>::Max();
    }
    const FName PalmAnchorName(*FString::Printf(
        TEXT("middle_01_%s"), bLeft ? TEXT("l") : TEXT("r")));
    if (Body->GetBoneIndex(PalmAnchorName) == INDEX_NONE)
    {
        return TNumericLimits<float>::Max();
    }
    const FName HandName(*FString::Printf(
        TEXT("hand_%s"), bLeft ? TEXT("l") : TEXT("r")));
    const FTransform* ReferenceHand = ReferenceComponentTransforms.Find(HandName);
    const FTransform* ReferencePalm = ReferenceComponentTransforms.Find(PalmAnchorName);
    if (!ReferenceHand || !ReferencePalm || Body->GetBoneIndex(HandName) == INDEX_NONE)
    {
        return TNumericLimits<float>::Max();
    }
    const FVector ReferencePalmOffsetCm =
        (ReferencePalm->GetLocation() - ReferenceHand->GetLocation()) *
        BodyScale * PaddlePalmAnchorAlongKnuckleFraction;
    const FTransform CurrentHand = Body->GetBoneTransformByName(
        HandName, EBoneSpaces::ComponentSpace);
    const FQuat HandDelta =
        (CurrentHand.GetRotation() * ReferenceHand->GetRotation().Inverse()).GetNormalized();
    const FVector RenderedGripCm =
        CurrentHand.GetLocation() * BodyScale +
        HandDelta.RotateVector(ReferencePalmOffsetCm);
    return FVector::Distance(RenderedGripCm, DesiredGripCm);
}

float ARaftSimCC0CrewVisualActor::MeasureMinimumPaddleFingerClosureDegrees(
    const FRaftSimCrewAvatarPose& Pose,
    bool bUpperTGrip) const
{
    if (!Body || !Pose.bShowPaddle)
    {
        return 0.0f;
    }
    float MinimumClosureDegrees = TNumericLimits<float>::Max();
    for (const bool bLeft : {true, false})
    {
        const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
        const FVector GripCenterCm = bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
        if (IsUpperTGrip(Pose, GripCenterCm) != bUpperTGrip)
        {
            continue;
        }
        for (const TCHAR* Digit : {
                 TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")})
        {
            FName ParentName(*FString::Printf(TEXT("hand_%s"), Side));
            float ChainClosureDegrees = 0.0f;
            for (int32 Segment = 1; Segment <= 3; ++Segment)
            {
                const FName BoneName(*FString::Printf(
                    TEXT("%s_%02d_%s"), Digit, Segment, Side));
                const FTransform* ReferenceBone =
                    ReferenceComponentTransforms.Find(BoneName);
                const FTransform* ReferenceParent =
                    ReferenceComponentTransforms.Find(ParentName);
                if (!ReferenceBone || !ReferenceParent ||
                    Body->GetBoneIndex(BoneName) == INDEX_NONE ||
                    Body->GetBoneIndex(ParentName) == INDEX_NONE)
                {
                    return 0.0f;
                }
                const FTransform CurrentBone = Body->GetBoneTransformByName(
                    BoneName, EBoneSpaces::ComponentSpace);
                const FTransform CurrentParent = Body->GetBoneTransformByName(
                    ParentName, EBoneSpaces::ComponentSpace);
                const FQuat ReferenceRelativeRotation =
                    ReferenceBone->GetRelativeTransform(*ReferenceParent).GetRotation();
                const FQuat CurrentRelativeRotation =
                    CurrentBone.GetRelativeTransform(CurrentParent).GetRotation();
                const FQuat ClosureDelta =
                    (CurrentRelativeRotation * ReferenceRelativeRotation.Inverse())
                        .GetNormalized();
                ChainClosureDegrees += FMath::RadiansToDegrees(ClosureDelta.GetAngle());
                ParentName = BoneName;
            }
            MinimumClosureDegrees = FMath::Min(
                MinimumClosureDegrees, ChainClosureDegrees);
        }
    }
    return MinimumClosureDegrees == TNumericLimits<float>::Max()
        ? 0.0f
        : MinimumClosureDegrees;
}

float ARaftSimCC0CrewVisualActor::MeasureMinimumPaddleThumbClosureDegrees() const
{
    if (!Body)
    {
        return 0.0f;
    }
    float MinimumClosureDegrees = TNumericLimits<float>::Max();
    for (const bool bLeft : {true, false})
    {
        const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
        FName ParentName(*FString::Printf(TEXT("hand_%s"), Side));
        float ChainClosureDegrees = 0.0f;
        for (int32 Segment = 1; Segment <= 3; ++Segment)
        {
            const FName BoneName(*FString::Printf(
                TEXT("thumb_%02d_%s"), Segment, Side));
            const FTransform* ReferenceBone =
                ReferenceComponentTransforms.Find(BoneName);
            const FTransform* ReferenceParent =
                ReferenceComponentTransforms.Find(ParentName);
            if (!ReferenceBone || !ReferenceParent ||
                Body->GetBoneIndex(BoneName) == INDEX_NONE ||
                Body->GetBoneIndex(ParentName) == INDEX_NONE)
            {
                return 0.0f;
            }
            const FTransform CurrentBone = Body->GetBoneTransformByName(
                BoneName, EBoneSpaces::ComponentSpace);
            const FTransform CurrentParent = Body->GetBoneTransformByName(
                ParentName, EBoneSpaces::ComponentSpace);
            const FQuat ReferenceRelativeRotation =
                ReferenceBone->GetRelativeTransform(*ReferenceParent).GetRotation();
            const FQuat CurrentRelativeRotation =
                CurrentBone.GetRelativeTransform(CurrentParent).GetRotation();
            const FQuat ClosureDelta =
                (CurrentRelativeRotation * ReferenceRelativeRotation.Inverse())
                    .GetNormalized();
            ChainClosureDegrees += FMath::RadiansToDegrees(ClosureDelta.GetAngle());
            ParentName = BoneName;
        }
        MinimumClosureDegrees = FMath::Min(
            MinimumClosureDegrees, ChainClosureDegrees);
    }
    return MinimumClosureDegrees == TNumericLimits<float>::Max()
        ? 0.0f
        : MinimumClosureDegrees;
}

void ARaftSimCC0CrewVisualActor::ApplyFingerChain(
    bool bLeft,
    const TCHAR* Digit,
    float GripAlpha)
{
    if (!Body || !Digit)
    {
        return;
    }
    const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
    FName ParentName(*FString::Printf(TEXT("hand_%s"), Side));
    FTransform ParentCurrent = Body->GetBoneTransformByName(
        ParentName, EBoneSpaces::ComponentSpace);
    if (!ReferenceComponentTransforms.Contains(ParentName) || ParentCurrent.ContainsNaN())
    {
        return;
    }
    static const float CurlDegrees[] = {42.0f, 62.0f, 42.0f};
    static const float ThumbCurlDegrees[] = {15.0f, 25.0f, 20.0f};
    for (int32 Segment = 1; Segment <= 3; ++Segment)
    {
        const FName BoneName(*FString::Printf(
            TEXT("%s_%02d_%s"), Digit, Segment, Side));
        const FTransform* Reference = ReferenceComponentTransforms.Find(BoneName);
        const FTransform* ReferenceParent = ReferenceComponentTransforms.Find(ParentName);
        if (!Reference || !ReferenceParent)
        {
            return;
        }
        FTransform Relative = Reference->GetRelativeTransform(*ReferenceParent);
        const float Curl = FCString::Strcmp(Digit, TEXT("thumb")) == 0
            ? ThumbCurlDegrees[Segment - 1]
            : CurlDegrees[Segment - 1];
        const bool bThumb = FCString::Strcmp(Digit, TEXT("thumb")) == 0;
        const FQuat LocalCurl(
            bThumb ? FVector::ZAxisVector : FVector::XAxisVector,
            FMath::DegreesToRadians(Curl * GripAlpha));
        Relative.SetRotation((Relative.GetRotation() * LocalCurl).GetNormalized());
        ParentCurrent = Relative * ParentCurrent;
        Body->SetBoneTransformByName(
            BoneName, ParentCurrent, EBoneSpaces::ComponentSpace);
        ParentName = BoneName;
    }
}

void ARaftSimCC0CrewVisualActor::ApplyPaddleGripPose(
    const FRaftSimCrewAvatarPose& Pose)
{
    if (!HasArticulatedPaddleGripRig())
    {
        return;
    }
    const float GripAlpha = Pose.bShowPaddle ? 1.0f : 0.16f;
    for (const bool bLeft : {true, false})
    {
        const FVector GripCenterCm = bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
        const float HandleCurlScale = Pose.bShowPaddle
            ? (IsUpperTGrip(Pose, GripCenterCm) ? 0.92f : 1.58f)
            : 1.0f;
        for (const TCHAR* Digit : CC0GripDigits)
        {
            ApplyFingerChain(bLeft, Digit, GripAlpha * HandleCurlScale);
        }
    }
    if (!Pose.bShowPaddle)
    {
        return;
    }
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
