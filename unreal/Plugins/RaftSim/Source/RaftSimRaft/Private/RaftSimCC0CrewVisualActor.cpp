#include "RaftSimCC0CrewVisualActor.h"

#include "Components/PoseableMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/SkeletalMesh.h"
#include "HAL/IConsoleManager.h"
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
constexpr float ProductionHeadClearanceLiftCm = 5.0f;
// The CC0 bodies are exported with Blender's identity axes
// (build_cc0_production_character.py: axis_forward="-Y"), which lands the
// mesh facing Unreal +Y. Swing-only bone driving preserves that rest yaw,
// so every pelvis/spine/neck/head kept facing +Y — the 2026-08-07 playtest
// "all heads face right" and the 90-degree PFD-through-chest offset. This
// twist turns the axial chain to the host's forward axis; limbs are driven
// to explicit endpoints and keep their authored twist.
constexpr float ProductionAxialFacingTwistDegrees = -90.0f;
// The legs need the SAME facing correction as the axial chain: glute flesh
// weighted to the twisted pelvis rotates -90 degrees about the vertical
// while thigh-weighted flesh kept the authored +Y facing, and the blend
// band across each cheek smeared that disagreement into a sheared fold
// (player "gash in the right butt cheek" report, 2026-08-30 — the stretch
// side reads as a groove; the compressed left side hides as a bulge).
// The rest thigh/calf shaft points DOWN while the pelvis shaft points UP,
// so matching the axial -90-about-up needs +90 about the leg shafts. The
// calves follow the thighs so the seam moves to the zero-scaled foot
// boundary inside the production boots instead of the visible knee.
// Sweepable at runtime for diagnosis.
static TAutoConsoleVariable<float> CVarRaftSimCC0LegFacingTwistDegrees(
    TEXT("raftsim.CC0LegFacingTwistDegrees"),
    90.0f,
    TEXT("Facing pre-twist (degrees) applied about each rest leg shaft when "
         "driving CC0 thigh/calf segment bones. 90 matches the axial "
         "-90-about-up facing correction; 0 restores the sheared legacy look."),
    ECVF_Default);
// Keep the imported garment's inner shoulder weights distributed across the
// upper chest. Driving both clavicle roots to one spine point pinched those
// weights into a hard central ridge and stretched the remaining wetsuit into
// broad triangular wings. The outer upper-arm joints remain on the gameplay
// pose; only the render skeleton's inner clavicle roots use this bounded span.
constexpr float ProductionClavicleRootLateralFraction = 0.32f;

const TCHAR* CC0GripDigits[] = {
    TEXT("thumb"), TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")};

constexpr float PaddleShaftThumbPadCenterRadiusCm = 2.20f;
constexpr float PaddleTGripPadCenterRadiusCm = 2.95f;
constexpr float PaddleTGripUsableHalfLengthCm = 5.65f;

struct FCC0GripDigitProfile
{
    float EntrySweepDegrees;
    float MiddleSweepDegrees;
    float TipSweepDegrees;
    float ProximalRadiusCm;
    float PadCenterRadiusCm;
    float TipCenterRadiusCm;
    float FanDegrees;
};

bool ResolveCC0GripDigitProfile(
    const TCHAR* Digit,
    FCC0GripDigitProfile& OutProfile)
{
    // Asymmetric C-grips keep the four digits distinct while placing their
    // distal pads on the handle. The old shared local-X curl could rotate a
    // mirrored chain away from the paddle and still pass its angle-only test.
    if (FCString::Strcmp(Digit, TEXT("index")) == 0)
    {
        OutProfile = {30.0f, 42.0f, 28.0f, 3.25f, 2.45f, 1.95f, 12.0f};
        return true;
    }
    if (FCString::Strcmp(Digit, TEXT("middle")) == 0)
    {
        OutProfile = {32.0f, 46.0f, 30.0f, 3.30f, 2.50f, 1.98f, 4.0f};
        return true;
    }
    if (FCString::Strcmp(Digit, TEXT("ring")) == 0)
    {
        OutProfile = {30.0f, 44.0f, 30.0f, 3.18f, 2.45f, 1.95f, -5.0f};
        return true;
    }
    if (FCString::Strcmp(Digit, TEXT("pinky")) == 0)
    {
        OutProfile = {28.0f, 40.0f, 28.0f, 3.00f, 2.35f, 1.90f, -12.0f};
        return true;
    }
    return false;
}

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
    // MPFB head-local +Z points through the rendered face (local -Y stays
    // the crown). The original -Z reading was 180 degrees off and was only
    // ever validated against itself via the helmet-alignment dot product;
    // the 2026-08-07 instrumented roster session measured the published
    // vector at -X world while the rendered face and the front-authored
    // vest demonstrably faced +X. Every asymmetric headgear placement had
    // presented its rear bowl forward as a result.
    return Body->GetComponentTransform().TransformVectorNoScale(
        HeadTransform.GetRotation().RotateVector(FVector::UpVector)).GetSafeNormal();
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

bool ARaftSimCC0CrewVisualActor::GetSolvedChestWorldTransform(
    FTransform& OutWorld) const
{
    if (!bBodyReady || !Body ||
        Body->GetBoneIndex(TEXT("spine_01")) == INDEX_NONE ||
        Body->GetBoneIndex(TEXT("spine_02")) == INDEX_NONE ||
        Body->GetBoneIndex(TEXT("spine_03")) == INDEX_NONE ||
        Body->GetBoneIndex(TEXT("neck_01")) == INDEX_NONE)
    {
        return false;
    }
    const auto BoneComponentLocation = [this](const TCHAR* BoneName)
    {
        return Body->GetBoneTransformByName(
            FName(BoneName), EBoneSpaces::ComponentSpace).GetLocation();
    };
    const FVector Spine01 = BoneComponentLocation(TEXT("spine_01"));
    const FVector Spine02 = BoneComponentLocation(TEXT("spine_02"));
    const FVector Spine03 = BoneComponentLocation(TEXT("spine_03"));
    const FVector NeckBase = BoneComponentLocation(TEXT("neck_01"));
    const FTransform& ComponentTransform = Body->GetComponentTransform();
    const FVector SpineUp = ComponentTransform.TransformVectorNoScale(
        NeckBase - Spine01).GetSafeNormal();
    if (SpineUp.IsNearlyZero())
    {
        return false;
    }
    const FVector FaceForward = GetSolvedFaceForwardWorldVector();
    const FVector ChestForward = (FaceForward -
        SpineUp * FVector::DotProduct(FaceForward, SpineUp)).GetSafeNormal();
    if (ChestForward.IsNearlyZero())
    {
        return false;
    }
    // ApplyBodyPose maps the host torso anchor between spine_02 and
    // spine_03 in HEIGHT, but the spinal column runs along the back of the
    // body while the host anchor is the torso volume centre — the vest mesh
    // is authored around the latter. Push the origin forward by the
    // spine-to-chest-centre depth or the vest slides rearward off the body.
    constexpr float ChestCenterForwardOfSpineCm = 9.0f;
    OutWorld = FTransform(
        FRotationMatrix::MakeFromZX(SpineUp, ChestForward).ToQuat(),
        ComponentTransform.TransformPosition(
            FMath::Lerp(Spine02, Spine03, 0.45f)) +
            ChestForward * ChestCenterForwardOfSpineCm);
    return true;
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
    const FVector& DesiredEndCm,
    float ShaftTwistDegrees)
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
    // FindBetweenNormals is minimal-arc: it aligns the shaft but has no
    // authority over rotation ABOUT the shaft, so a bone keeps its authored
    // rest twist. The optional pre-twist spins the bone about its rest shaft
    // before the swing, which is how the axial chain cancels the imported
    // MPFB facing (see ProductionAxialFacingTwistDegrees).
    const FQuat Twist = FMath::IsNearlyZero(ShaftTwistDegrees)
        ? FQuat::Identity
        : FQuat(ReferenceDirection,
              FMath::DegreesToRadians(ShaftTwistDegrees));
    FTransform Target = *Reference;
    Target.SetLocation(ToMeshSpace(DesiredStartCm));
    Target.SetRotation((Swing * Twist * Reference->GetRotation()).GetNormalized());
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
    const FVector LeftClavicleRoot = UpperSpine +
        (Pose.LeftShoulderCm - ShoulderCenter) *
            ProductionClavicleRootLateralFraction;
    const FVector RightClavicleRoot = UpperSpine +
        (Pose.RightShoulderCm - ShoulderCenter) *
            ProductionClavicleRootLateralFraction;
    // The MakeHuman body owns a longer anatomical neck than the compact host
    // collision pose. Driving its skull directly to the host head point left
    // only about 3 cm between the jaw and shoulder line in seated views, so
    // the wetsuit shoulder envelope read as a black bib covering the neck.
    // Lift only the render skeleton along the solved torso-up axis. Helmet fit
    // still comes from the live rendered eyes, while gameplay, collision,
    // crew mass, hand targets, paddle, raft, and rescue authority stay put.
    const FVector PresentedHeadCenter =
        Pose.HeadCenterCm + TorsoUp * ProductionHeadClearanceLiftCm;
    const FVector HeadTop = PresentedHeadCenter + TorsoUp * 16.0f;
    PresentedHeadShoulderClearanceCm = FVector::DotProduct(
        PresentedHeadCenter - ShoulderCenter,
        TorsoUp);

    SetSegmentBone(TEXT("pelvis"), TEXT("spine_01"), HipCenter, LowerSpine,
        ProductionAxialFacingTwistDegrees);
    SetSegmentBone(TEXT("spine_01"), TEXT("spine_02"), LowerSpine, MidSpine,
        ProductionAxialFacingTwistDegrees);
    SetSegmentBone(TEXT("spine_02"), TEXT("spine_03"), MidSpine, UpperSpine,
        ProductionAxialFacingTwistDegrees);
    SetSegmentBone(TEXT("spine_03"), TEXT("neck_01"), UpperSpine, NeckBase,
        ProductionAxialFacingTwistDegrees);
    SetSegmentBone(TEXT("neck_01"), TEXT("head"), NeckBase, PresentedHeadCenter,
        ProductionAxialFacingTwistDegrees);
    SetSegmentBone(TEXT("head"), TEXT("head"), PresentedHeadCenter, HeadTop,
        ProductionAxialFacingTwistDegrees);

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
    FVector LeftElbow =
        FMath::Lerp(Pose.LeftShoulderCm, LeftWristCm, 0.48f) +
        FVector(0.0f, -5.0f, -2.0f);
    FVector RightElbow =
        FMath::Lerp(Pose.RightShoulderCm, RightWristCm, 0.48f) +
        FVector(0.0f, 5.0f, -2.0f);
    // Swinging the upper-arm bone steeply DOWN from the rig's near-lateral
    // rest pose rolls the deltoid/trapezius skin up beside the neck — with
    // lap-resting hands every idle paddler wore a black shoulder yoke
    // reaching the chin ("what is the black material sticking out the top
    // of the life jacket? it seems much to high to be shoulders",
    // 2026-09-02, confirmed skeletal by a show-SkeletalMeshes A/B). Cap
    // the elbow's drop below the shoulder; the forearm still reaches the
    // true wrist, so hands stay put and the arm simply bends more.
    const auto ClampElbowDrop = [](const FVector& ShoulderCm, FVector ElbowCm)
    {
        // 14 still left visible skin flaps once the shoulders themselves
        // dropped to 73; 12 keeps the deltoid mass at the vest line.
        constexpr float kMaxElbowDropCm = 12.0f;
        ElbowCm.Z = FMath::Max(ElbowCm.Z, ShoulderCm.Z - kMaxElbowDropCm);
        return ElbowCm;
    };
    LeftElbow = ClampElbowDrop(Pose.LeftShoulderCm, LeftElbow);
    RightElbow = ClampElbowDrop(Pose.RightShoulderCm, RightElbow);
    SetSegmentBone(
        TEXT("clavicle_l"),
        TEXT("upperarm_l"),
        LeftClavicleRoot,
        Pose.LeftShoulderCm);
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
    SetSegmentBone(
        TEXT("clavicle_r"),
        TEXT("upperarm_r"),
        RightClavicleRoot,
        Pose.RightShoulderCm);
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

    const float LegFacingTwistDegrees =
        CVarRaftSimCC0LegFacingTwistDegrees.GetValueOnGameThread();
    // Leg skin squashes between explicitly placed bone heads (the foot
    // bone is pinned at the pose foot target and scaled to zero), so pose
    // spans are free of the source rig's limb lengths. Log the source
    // lengths once anyway — they document how far the skin is being
    // compressed, which matters when diagnosing shin/boot junctions
    // ("the feet seem to be coming out of the shins", 2026-09-01: the
    // real cause was a 10 cm shin drop inside a 12 cm boot cuff).
    static bool bLoggedLegSegmentLengths = false;
    if (!bLoggedLegSegmentLengths)
    {
        bLoggedLegSegmentLengths = true;
        const FTransform* RefThigh = ReferenceComponentTransforms.Find(TEXT("thigh_l"));
        const FTransform* RefCalf = ReferenceComponentTransforms.Find(TEXT("calf_l"));
        const FTransform* RefFoot = ReferenceComponentTransforms.Find(TEXT("foot_l"));
        if (RefThigh && RefCalf && RefFoot)
        {
            UE_LOG(LogTemp, Display,
                TEXT("RaftSim CC0 leg segments: thigh=%.1fcm calf=%.1fcm (pose frame)"),
                FVector::Distance(RefThigh->GetLocation(), RefCalf->GetLocation()) *
                    BodyScale,
                FVector::Distance(RefCalf->GetLocation(), RefFoot->GetLocation()) *
                    BodyScale);
        }
    }
    SetSegmentBone(TEXT("thigh_l"), TEXT("calf_l"), Pose.LeftHipCm, Pose.LeftKneeCm,
        LegFacingTwistDegrees);
    SetSegmentBone(TEXT("calf_l"), TEXT("foot_l"), Pose.LeftKneeCm, Pose.LeftFootCm,
        LegFacingTwistDegrees);
    SetBoneAtPoint(TEXT("foot_l"), Pose.LeftFootCm);
    SetSegmentBone(TEXT("thigh_r"), TEXT("calf_r"), Pose.RightHipCm, Pose.RightKneeCm,
        LegFacingTwistDegrees);
    SetSegmentBone(TEXT("calf_r"), TEXT("foot_r"), Pose.RightKneeCm, Pose.RightFootCm,
        LegFacingTwistDegrees);
    SetBoneAtPoint(TEXT("foot_r"), Pose.RightFootCm);

    // Not zero: fully collapsing the foot bone yanks every ankle-blend
    // vertex onto one point, chopping the calf into a featureless tube with
    // no taper ("their ankles look like cylindars", 2026-09-02). A third of
    // the rest scale keeps a short tapering ankle cone that disappears into
    // the production boot cuff, while the shrunken foot mesh itself stays
    // hidden inside the boot volume.
    constexpr float kHiddenFootBoneScale = 0.35f;
    Body->SetBoneScaleByName(
        TEXT("foot_l"), FVector(kHiddenFootBoneScale), EBoneSpaces::ComponentSpace);
    Body->SetBoneScaleByName(
        TEXT("foot_r"), FVector(kHiddenFootBoneScale), EBoneSpaces::ComponentSpace);
    Body->SetBoneScaleByName(
        TEXT("head"),
        bHeadHiddenForFirstPerson ? FVector::ZeroVector : FVector::OneVector,
        EBoneSpaces::ComponentSpace);
    Body->RefreshBoneTransforms();
    ApplyPaddleGripPose(Pose);
    Body->RefreshBoneTransforms();
    const FVector PresentedLeftClavicleRootCm =
        Body->GetBoneTransformByName(
            TEXT("clavicle_l"), EBoneSpaces::ComponentSpace).GetLocation() *
        BodyScale;
    const FVector PresentedRightClavicleRootCm =
        Body->GetBoneTransformByName(
            TEXT("clavicle_r"), EBoneSpaces::ComponentSpace).GetLocation() *
        BodyScale;
    const FVector PresentedLeftShoulderCm =
        Body->GetBoneTransformByName(
            TEXT("upperarm_l"), EBoneSpaces::ComponentSpace).GetLocation() *
        BodyScale;
    const FVector PresentedRightShoulderCm =
        Body->GetBoneTransformByName(
            TEXT("upperarm_r"), EBoneSpaces::ComponentSpace).GetLocation() *
        BodyScale;
    PresentedClavicleRootSpanCm = FVector::Distance(
        PresentedLeftClavicleRootCm,
        PresentedRightClavicleRootCm);
    MaximumPresentedShoulderAnchorErrorCm = FMath::Max(
        FVector::Distance(PresentedLeftShoulderCm, Pose.LeftShoulderCm),
        FVector::Distance(PresentedRightShoulderCm, Pose.RightShoulderCm));
    bPaddleGripActive = Pose.bShowPaddle && HasArticulatedPaddleGripRig();
    MaximumPaddleGripAnchorErrorCm = bPaddleGripActive
        ? FMath::Max(
              MeasurePaddleGripAnchorErrorCm(true, Pose.LeftHandCm),
              MeasurePaddleGripAnchorErrorCm(false, Pose.RightHandCm))
        : 0.0f;
    MaximumPaddleFingerContactErrorCm = bPaddleGripActive
        ? MeasureMaximumPaddleFingerContactErrorCm(Pose)
        : 0.0f;
    MaximumPaddleThumbContactErrorCm = bPaddleGripActive
        ? MeasureMaximumPaddleThumbContactErrorCm(Pose)
        : 0.0f;
    MaximumPaddleThumbOppositionDot = bPaddleGripActive
        ? MeasureMaximumPaddleThumbOppositionDot(Pose)
        : -1.0f;
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
    // The reference basis must be the PALM normal on BOTH hands, and the
    // cross order that achieves it mirrors with the hand: anatomical
    // finger positions flip the product's sense between left and right.
    // First pass used one shared order (left grip solved backwards,
    // 2026-08-31); the "consistent" swap then chose the back-of-hand
    // sense for BOTH — every resting hand lay palm-up under the shaft
    // ("the hands look twisted", 2026-09-01). This orientation is the
    // empirically verified palm sense for this rig.
    const FVector ReferenceNormal =
        (bLeft ? FVector::CrossProduct(ReferenceWidth, ReferenceForward)
               : FVector::CrossProduct(ReferenceForward, ReferenceWidth))
            .GetSafeNormal();
    const FVector GripCenterCm = bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
    // The knuckle line mirrors too: on a shared shaft axis the left hand's
    // index-to-pinky direction runs opposite the right's, otherwise the
    // left grip lands thumb-down (upside down).
    FVector DesiredWidth = ResolvePaddleGripAxis(Pose, GripCenterCm).GetSafeNormal();
    if (bLeft)
    {
        DesiredWidth = -DesiredWidth;
    }
    const FVector ShoulderCm = bLeft ? Pose.LeftShoulderCm : Pose.RightShoulderCm;
    // Both grips approach palm-first from the shoulder side: the shaft hand
    // wraps the far side of the shaft, and the T-grip hand caps the grip
    // from above (palm away from the shoulder, never underhand).
    const FVector PalmApproachCm = GripCenterCm - ShoulderCm;
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

float ARaftSimCC0CrewVisualActor::MeasureMaximumPaddleFingerContactErrorCm(
    const FRaftSimCrewAvatarPose& Pose) const
{
    if (!Body || !Pose.bShowPaddle)
    {
        return 0.0f;
    }
    float MaximumErrorCm = 0.0f;
    for (const bool bLeft : {true, false})
    {
        const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
        const FVector GripCenterCm =
            bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
        const FVector GripAxis =
            ResolvePaddleGripAxis(Pose, GripCenterCm);
        const bool bUpperTGrip =
            IsUpperTGrip(Pose, GripCenterCm);
        for (const TCHAR* Digit : {
                 TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")})
        {
            FCC0GripDigitProfile Profile;
            const FName PadName(*FString::Printf(
                TEXT("%s_03_%s"), Digit, Side));
            if (!ResolveCC0GripDigitProfile(Digit, Profile) ||
                Body->GetBoneIndex(PadName) == INDEX_NONE)
            {
                return TNumericLimits<float>::Max();
            }
            const FVector PadCm = Body->GetBoneTransformByName(
                PadName, EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
            const FVector OffsetCm = PadCm - GripCenterCm;
            const float RadialDistanceCm =
                FVector::VectorPlaneProject(OffsetCm, GripAxis).Size();
            const float TargetRadiusCm = bUpperTGrip
                ? PaddleTGripPadCenterRadiusCm
                : Profile.PadCenterRadiusCm;
            float ErrorCm = FMath::Abs(
                RadialDistanceCm - TargetRadiusCm);
            if (bUpperTGrip)
            {
                ErrorCm = FMath::Max(
                    ErrorCm,
                    FMath::Max(
                        FMath::Abs(FVector::DotProduct(OffsetCm, GripAxis)) -
                            PaddleTGripUsableHalfLengthCm,
                        0.0f));
            }
            MaximumErrorCm = FMath::Max(MaximumErrorCm, ErrorCm);
        }
    }
    return MaximumErrorCm;
}

float ARaftSimCC0CrewVisualActor::MeasureMaximumPaddleThumbContactErrorCm(
    const FRaftSimCrewAvatarPose& Pose) const
{
    if (!Body || !Pose.bShowPaddle)
    {
        return 0.0f;
    }
    float MaximumErrorCm = 0.0f;
    for (const bool bLeft : {true, false})
    {
        const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
        const FName PadName(*FString::Printf(TEXT("thumb_03_%s"), Side));
        if (Body->GetBoneIndex(PadName) == INDEX_NONE)
        {
            return TNumericLimits<float>::Max();
        }
        const FVector GripCenterCm =
            bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
        const FVector GripAxis =
            ResolvePaddleGripAxis(Pose, GripCenterCm);
        const bool bUpperTGrip =
            IsUpperTGrip(Pose, GripCenterCm);
        const FVector PadCm = Body->GetBoneTransformByName(
            PadName, EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
        const FVector OffsetCm = PadCm - GripCenterCm;
        const float TargetRadiusCm = bUpperTGrip
            ? PaddleTGripPadCenterRadiusCm
            : PaddleShaftThumbPadCenterRadiusCm;
        float ErrorCm = FMath::Abs(
            FVector::VectorPlaneProject(OffsetCm, GripAxis).Size() -
            TargetRadiusCm);
        if (bUpperTGrip)
        {
            ErrorCm = FMath::Max(
                ErrorCm,
                FMath::Max(
                    FMath::Abs(FVector::DotProduct(OffsetCm, GripAxis)) -
                        PaddleTGripUsableHalfLengthCm,
                    0.0f));
        }
        MaximumErrorCm = FMath::Max(MaximumErrorCm, ErrorCm);
    }
    return MaximumErrorCm;
}

float ARaftSimCC0CrewVisualActor::MeasureMaximumPaddleThumbOppositionDot(
    const FRaftSimCrewAvatarPose& Pose) const
{
    if (!Body || !Pose.bShowPaddle)
    {
        return -1.0f;
    }
    float MaximumDot = -1.0f;
    for (const bool bLeft : {true, false})
    {
        const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
        const FName MiddleName(*FString::Printf(TEXT("middle_03_%s"), Side));
        const FName ThumbName(*FString::Printf(TEXT("thumb_03_%s"), Side));
        if (Body->GetBoneIndex(MiddleName) == INDEX_NONE ||
            Body->GetBoneIndex(ThumbName) == INDEX_NONE)
        {
            return 1.0f;
        }
        const FVector GripCenterCm =
            bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
        const FVector GripAxis =
            ResolvePaddleGripAxis(Pose, GripCenterCm);
        const FVector MiddleRadial = FVector::VectorPlaneProject(
            Body->GetBoneTransformByName(
                MiddleName, EBoneSpaces::ComponentSpace).GetLocation() *
                BodyScale - GripCenterCm,
            GripAxis).GetSafeNormal();
        const FVector ThumbRadial = FVector::VectorPlaneProject(
            Body->GetBoneTransformByName(
                ThumbName, EBoneSpaces::ComponentSpace).GetLocation() *
                BodyScale - GripCenterCm,
            GripAxis).GetSafeNormal();
        MaximumDot = FMath::Max(
            MaximumDot,
            FVector::DotProduct(MiddleRadial, ThumbRadial));
    }
    return MaximumDot;
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

void ARaftSimCC0CrewVisualActor::ApplyFingerChainAroundGrip(
    bool bLeft,
    const TCHAR* Digit,
    const FVector& GripCenterCm,
    const FVector& GripAxis,
    bool bUpperTGrip)
{
    if (!Body || !Digit)
    {
        return;
    }
    FCC0GripDigitProfile Profile;
    if (!ResolveCC0GripDigitProfile(Digit, Profile))
    {
        return;
    }
    const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
    const FName HandName(*FString::Printf(TEXT("hand_%s"), Side));
    const FName FirstName(*FString::Printf(TEXT("%s_01_%s"), Digit, Side));
    const FName SecondName(*FString::Printf(TEXT("%s_02_%s"), Digit, Side));
    const FName ThirdName(*FString::Printf(TEXT("%s_03_%s"), Digit, Side));
    if (Body->GetBoneIndex(HandName) == INDEX_NONE ||
        Body->GetBoneIndex(FirstName) == INDEX_NONE ||
        Body->GetBoneIndex(SecondName) == INDEX_NONE ||
        Body->GetBoneIndex(ThirdName) == INDEX_NONE)
    {
        return;
    }

    const FVector SafeGripAxis = GripAxis.GetSafeNormal();
    FVector SegmentStartCm = Body->GetBoneTransformByName(
        FirstName, EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
    const FVector NaturalSecondCm = Body->GetBoneTransformByName(
        SecondName, EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
    FVector RadialDirection = FVector::VectorPlaneProject(
        SegmentStartCm - GripCenterCm, SafeGripAxis).GetSafeNormal();
    const FVector NaturalTangent = FVector::VectorPlaneProject(
        NaturalSecondCm - SegmentStartCm, SafeGripAxis).GetSafeNormal();
    if (SafeGripAxis.IsNearlyZero() || RadialDirection.IsNearlyZero())
    {
        return;
    }

    // Choose the sweep from the imported chain's forward direction. This is
    // the mirror-safe part the old local-X curl lacked: both hands now close
    // toward their handle instead of one side being allowed to bend backward.
    const float NaturalOrientation = FVector::DotProduct(
        SafeGripAxis,
        FVector::CrossProduct(RadialDirection, NaturalTangent));
    float WrapSign = FMath::Abs(NaturalOrientation) > KINDA_SMALL_NUMBER
        ? FMath::Sign(NaturalOrientation)
        : (bLeft ? -1.0f : 1.0f);
    RadialDirection = RadialDirection.RotateAngleAxis(
        Profile.FanDegrees * WrapSign, SafeGripAxis);

    float AxialOffsetCm = FVector::DotProduct(
        SegmentStartCm - GripCenterCm, SafeGripAxis);
    if (bUpperTGrip)
    {
        AxialOffsetCm = FMath::Clamp(
            AxialOffsetCm,
            -PaddleTGripUsableHalfLengthCm,
            PaddleTGripUsableHalfLengthCm);
    }
    const float WrapAnglesDegrees[] = {
        Profile.EntrySweepDegrees,
        Profile.MiddleSweepDegrees,
        Profile.TipSweepDegrees};
    const float JointRadiiCm[] = {
        bUpperTGrip ? 3.85f : Profile.ProximalRadiusCm,
        bUpperTGrip ? PaddleTGripPadCenterRadiusCm : Profile.PadCenterRadiusCm,
        bUpperTGrip ? 2.45f : Profile.TipCenterRadiusCm};
    const FName BoneNames[] = {FirstName, SecondName, ThirdName};
    float CumulativeAngleDegrees = 0.0f;
    for (int32 SegmentIndex = 0; SegmentIndex < 3; ++SegmentIndex)
    {
        CumulativeAngleDegrees +=
            WrapAnglesDegrees[SegmentIndex] * WrapSign;
        const FVector TargetRadial = RadialDirection.RotateAngleAxis(
            CumulativeAngleDegrees, SafeGripAxis);
        const FVector SegmentEndCm =
            GripCenterCm + SafeGripAxis * AxialOffsetCm +
            TargetRadial * JointRadiiCm[SegmentIndex];
        SetSegmentBone(
            BoneNames[SegmentIndex],
            SegmentIndex < 2
                ? BoneNames[SegmentIndex + 1]
                : BoneNames[SegmentIndex],
            SegmentStartCm,
            SegmentEndCm);
        SegmentStartCm = SegmentEndCm;
    }
}

void ARaftSimCC0CrewVisualActor::ApplyOpposedThumbPadToGrip(
    bool bLeft,
    const FVector& GripCenterCm,
    const FVector& GripAxis,
    bool bUpperTGrip)
{
    if (!Body)
    {
        return;
    }
    const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
    const FName MiddlePadName(*FString::Printf(TEXT("middle_03_%s"), Side));
    const FName SecondName(*FString::Printf(TEXT("thumb_02_%s"), Side));
    const FName ThirdName(*FString::Printf(TEXT("thumb_03_%s"), Side));
    if (Body->GetBoneIndex(MiddlePadName) == INDEX_NONE ||
        Body->GetBoneIndex(SecondName) == INDEX_NONE ||
        Body->GetBoneIndex(ThirdName) == INDEX_NONE)
    {
        return;
    }
    const FVector SafeGripAxis = GripAxis.GetSafeNormal();
    const FVector MiddlePadCm = Body->GetBoneTransformByName(
        MiddlePadName, EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
    const FTransform CurrentSecond = Body->GetBoneTransformByName(
        SecondName, EBoneSpaces::ComponentSpace);
    const FTransform CurrentThird = Body->GetBoneTransformByName(
        ThirdName, EBoneSpaces::ComponentSpace);
    const FVector SecondCm = CurrentSecond.GetLocation() * BodyScale;
    const FVector CurrentPadCm = CurrentThird.GetLocation() * BodyScale;
    FVector OpposedRadial = -FVector::VectorPlaneProject(
        MiddlePadCm - GripCenterCm, SafeGripAxis).GetSafeNormal();
    if (OpposedRadial.IsNearlyZero())
    {
        OpposedRadial = FVector::VectorPlaneProject(
            CurrentPadCm - GripCenterCm, SafeGripAxis).GetSafeNormal();
    }
    if (SafeGripAxis.IsNearlyZero() || OpposedRadial.IsNearlyZero())
    {
        return;
    }
    float AxialOffsetCm = FVector::DotProduct(
        CurrentPadCm - GripCenterCm, SafeGripAxis);
    if (bUpperTGrip)
    {
        AxialOffsetCm = FMath::Clamp(
            AxialOffsetCm,
            -PaddleTGripUsableHalfLengthCm,
            PaddleTGripUsableHalfLengthCm);
    }
    const float PadRadiusCm = bUpperTGrip
        ? PaddleTGripPadCenterRadiusCm
        : PaddleShaftThumbPadCenterRadiusCm;
    const FVector TargetPadCm =
        GripCenterCm + SafeGripAxis * AxialOffsetCm +
        OpposedRadial * PadRadiusCm;
    SetSegmentBone(SecondName, ThirdName, SecondCm, TargetPadCm);
    FTransform TargetThird = CurrentThird;
    TargetThird.SetLocation(ToMeshSpace(TargetPadCm));
    Body->SetBoneTransformByName(
        ThirdName, TargetThird, EBoneSpaces::ComponentSpace);
}

void ARaftSimCC0CrewVisualActor::ApplyPaddleGripPose(
    const FRaftSimCrewAvatarPose& Pose)
{
    if (!HasArticulatedPaddleGripRig())
    {
        return;
    }
    const float GripAlpha = Pose.bShowPaddle ? 0.32f : 0.16f;
    for (const bool bLeft : {true, false})
    {
        for (const TCHAR* Digit : CC0GripDigits)
        {
            ApplyFingerChain(bLeft, Digit, GripAlpha);
        }
    }
    if (!Pose.bShowPaddle)
    {
        return;
    }
    Body->RefreshBoneTransforms();
    for (const bool bLeft : {true, false})
    {
        const FVector GripCenterCm =
            bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
        const FVector GripAxis =
            ResolvePaddleGripAxis(Pose, GripCenterCm);
        const bool bUpperTGrip =
            IsUpperTGrip(Pose, GripCenterCm);
        for (const TCHAR* Digit : {
                 TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")})
        {
            ApplyFingerChainAroundGrip(
                bLeft,
                Digit,
                GripCenterCm,
                GripAxis,
                bUpperTGrip);
        }
        Body->RefreshBoneTransforms();
        ApplyOpposedThumbPadToGrip(
            bLeft,
            GripCenterCm,
            GripAxis,
            bUpperTGrip);
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
