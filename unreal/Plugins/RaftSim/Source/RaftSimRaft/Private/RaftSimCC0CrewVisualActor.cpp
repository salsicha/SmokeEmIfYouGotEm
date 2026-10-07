#include "RaftSimCC0CrewVisualActor.h"

#include "Components/PoseableMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/SkeletalMesh.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimAccessoryMesh.h"
#include "RaftSimCrewRoster.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"

namespace
{
// Both hands hold equipment: the crew paddle, or an oar rower's two handles.
bool HasHeldGrip(const FRaftSimCrewAvatarPose& Pose)
{
    return Pose.bShowPaddle || Pose.bOarGrip;
}

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
// Full-detail front/profile/rear review: the former eye-line drops pushed
// the brow over the eyes and let the crown exit the rear of the bowl.
const float CrewHelmetAnchorDropsCm[] = {3.0f, 4.0f, 4.0f, 4.0f};
const float CrewHelmetAnchorBackCm[] = {5.0f, 5.5f, 5.0f, 5.0f};
// The guide skull is the deepest of the five (eyes 8.7 cm ahead of the head
// joint against 6.7-7.9 cm for the crew, forensics 2026-09-03) and the
// common eye-line anchor left the shell seated forward on it: the rear rim
// crossed mid-skull with the occiput bare ("the guide's helmet is not
// centered on his head"). Pull the guide anchor back along the face and
// size the shell for that skull.
constexpr float GuideHelmetAnchorBackCm = 5.5f;
// The authored shell is already 25.7 cm wide. The former 1.08/1.02
// enlargement left several centimetres of daylight at each temple. Fit the
// shell to the head, retaining the head-local anchor and rear coverage.
constexpr float GuideHelmetFitScale = 0.90f;
constexpr float CrewHelmetFitScale = 0.84f;

constexpr float PaddlePalmAnchorAlongKnuckleFraction = 0.56f;
// The CC0 bodies are exported with Blender's identity axes
// (build_cc0_production_character.py: axis_forward="-Y"), which lands the
// mesh facing Unreal +Y. Swing-only bone driving preserves that rest yaw,
// so every pelvis/spine/neck/head kept facing +Y — the 2026-08-07 playtest
// "all heads face right" and the 90-degree PFD-through-chest offset. This
// twist turns the axial chain to the host's forward axis; limbs are driven
// to explicit endpoints and keep their authored twist.
constexpr float ProductionAxialFacingTwistDegrees = -90.0f;
// Forward crown tip that levels the rendered gaze (see ApplyBodyPose).
constexpr float ProductionHeadLevelPitchDegrees = 20.0f;
// The vest mesh is authored around a torso whose shoulders sit closer to
// the chest anchor than this rig's; lift it along the spine so its top
// reaches the collarbones instead of the armpits.
constexpr float ProductionVestLiftAlongSpineCm = 8.0f;
static TAutoConsoleVariable<float> CVarCC0VestForwardOfSpineCm(
    TEXT("raftsim.CC0VestForwardOfSpineCm"),
    4.5f,
    TEXT("Rendered vest centre forward of the solved spine, in centimetres; fit review control."));
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
// Fraction of the rig's 37.5 cm shoulder span that spreads the inner
// clavicle roots (the authored roots sit 4.8 cm apart); 0.28 keeps the
// rendered span near 10.5 cm, inside the anatomical gate.
constexpr float ProductionClavicleRootLateralFraction = 0.28f;

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

// Diagnostic: log where the driven axial joints land and which bones move
// the highest wetsuit vertex (raftsim.CC0PoseForensics 1).
TAutoConsoleVariable<int32> CVarCC0PoseForensics(
    TEXT("raftsim.CC0PoseForensics"),
    0,
    TEXT("Log driven joint heights and the wetsuit apex influences once per body."));

// Review overrides for the guide helmet seat (-1 keeps the authored value).
TAutoConsoleVariable<float> CVarCC0GuideHelmetBackCm(
    TEXT("raftsim.CC0GuideHelmetBackCm"),
    -1.0f,
    TEXT("Guide helmet anchor pull-back along the face in cm (-1 = authored)."));
TAutoConsoleVariable<float> CVarCC0GuideHelmetScale(
    TEXT("raftsim.CC0GuideHelmetScale"),
    -1.0f,
    TEXT("Guide helmet shell scale (-1 = authored)."));

float ResolvedGuideHelmetBackCm()
{
    const float Override = CVarCC0GuideHelmetBackCm.GetValueOnGameThread();
    return Override >= 0.0f ? Override : GuideHelmetAnchorBackCm;
}

float ResolvedGuideHelmetScale()
{
    const float Override = CVarCC0GuideHelmetScale.GetValueOnGameThread();
    return Override > 0.0f ? Override : GuideHelmetFitScale;
}

// Diagnostic: draw the CC0 wetsuit section with another material so its
// geometry can be told apart from every other charcoal surface in a capture.
TAutoConsoleVariable<int32> CVarCC0CrewGaze(
    TEXT("RaftSim.CC0CrewGaze"),
    1,
    TEXT("1 lets each seated CC0 rafter look about in their own way (URaftSimCrewRoster gaze); 0 holds every head on the line ahead."));
TAutoConsoleVariable<int32> CVarCC0NeckCollar(
    TEXT("RaftSim.CC0NeckCollar"),
    1,
    TEXT("1 shows the fitted neoprene collar over the CC0 wetsuit neckline."));
TAutoConsoleVariable<FString> CVarCC0WetsuitDebugMaterial(
    TEXT("raftsim.CC0WetsuitDebugMaterial"),
    TEXT(""),
    TEXT("Object path of a material to draw the CC0 wetsuit section with (debug only)."));

// The dressed bodies' garment slots end in _Top and _Bottom.
const FRaftSimCrewGarmentLook* GarmentForSlot(
    const FString& SlotName,
    const FRaftSimCrewIdentity& Identity)
{
    if (SlotName.EndsWith(TEXT("_Top"), ESearchCase::IgnoreCase))
    {
        return &Identity.Top;
    }
    if (SlotName.EndsWith(TEXT("_Bottom"), ESearchCase::IgnoreCase))
    {
        return &Identity.Bottom;
    }
    return nullptr;
}

// Each person's own clothes on the shared river-clothing material the
// importer assigns to the garment slots.
void ApplyGarmentLooks(
    UPoseableMeshComponent* Body,
    const USkeletalMesh* Mesh,
    const FRaftSimCrewIdentity& Identity)
{
    const TArray<FSkeletalMaterial>& Slots = Mesh->GetMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < Slots.Num(); ++MaterialIndex)
    {
        const FRaftSimCrewGarmentLook* Look =
            GarmentForSlot(Slots[MaterialIndex].MaterialSlotName.ToString(), Identity);
        UMaterialInterface* Clothing = Slots[MaterialIndex].MaterialInterface;
        if (Look == nullptr || Clothing == nullptr)
        {
            continue;
        }
        UMaterialInstanceDynamic* Dressed = Cast<UMaterialInstanceDynamic>(Body->GetMaterial(MaterialIndex));
        if (!Dressed || Dressed->Parent != Clothing)
        {
            Dressed = UMaterialInstanceDynamic::Create(
                Clothing, Body, MakeUniqueObjectName(Body, UMaterialInstanceDynamic::StaticClass(),
                    TEXT("M_RaftSim_CC0_RiverClothing_Dressed")));
            Body->SetMaterial(MaterialIndex, Dressed);
        }
        Dressed->SetVectorParameterValue(TEXT("BaseColor"), Look->BaseColor);
        Dressed->SetVectorParameterValue(TEXT("AccentColor"), Look->AccentColor);
        Dressed->SetScalarParameterValue(TEXT("StripeAmount"), Look->StripeAmount);
        Dressed->SetScalarParameterValue(TEXT("StripePeriodCm"), Look->StripePeriodCm);
        Dressed->SetScalarParameterValue(TEXT("PrintAmount"), Look->PrintAmount);
        Dressed->SetScalarParameterValue(TEXT("PrintScaleCm"), Look->PrintScaleCm);
        Dressed->SetScalarParameterValue(TEXT("HeatherAmount"), Look->HeatherAmount);
        Dressed->SetScalarParameterValue(TEXT("Roughness"), Look->Roughness);
    }
}

void ApplyProductionBodyMaterialOverrides(
    UPoseableMeshComponent* Body,
    const USkeletalMesh* Mesh,
    const FRaftSimCrewIdentity& Identity)
{
    if (Body == nullptr || Mesh == nullptr)
    {
        return;
    }
    ApplyGarmentLooks(Body, Mesh, Identity);
    UMaterialInterface* ProductionWetsuit = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Wetsuit.M_RaftSim_Wetsuit"));
    const FString DebugWetsuitPath = CVarCC0WetsuitDebugMaterial.GetValueOnGameThread();
    if (!DebugWetsuitPath.IsEmpty())
    {
        if (UMaterialInterface* DebugWetsuit =
                LoadObject<UMaterialInterface>(nullptr, *DebugWetsuitPath))
        {
            ProductionWetsuit = DebugWetsuit;
        }
    }
    if (ProductionWetsuit == nullptr)
    {
        return;
    }
    const TArray<FSkeletalMaterial>& Slots = Mesh->GetMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < Slots.Num(); ++MaterialIndex)
    {
        const FString SlotName = Slots[MaterialIndex].MaterialSlotName.ToString();
        if (!SlotName.Contains(TEXT("Wetsuit"), ESearchCase::IgnoreCase))
        {
            continue;
        }
        // Keep each variant's rights-tracked skin, eye and hair atlases,
        // but replace the FBX's flat glossy neoprene with the same
        // physically scaled generated textile used by the production
        // fallback wardrobe, tinted per person (their own wetsuit). This is
        // a presentation-only override.
        UMaterialInstanceDynamic* Tinted = Cast<UMaterialInstanceDynamic>(Body->GetMaterial(MaterialIndex));
        if (!DebugWetsuitPath.IsEmpty())
        {
            if (Body->GetMaterial(MaterialIndex) != ProductionWetsuit)
            {
                Body->SetMaterial(MaterialIndex, ProductionWetsuit);
            }
            continue;
        }
        if (!Tinted || Tinted->Parent != ProductionWetsuit)
        {
            Tinted = UMaterialInstanceDynamic::Create(
                ProductionWetsuit, Body, MakeUniqueObjectName(Body, UMaterialInstanceDynamic::StaticClass(),
                    TEXT("M_RaftSim_Wetsuit_Tinted")));
            Body->SetMaterial(MaterialIndex, Tinted);
        }
        Tinted->SetVectorParameterValue(TEXT("BaseTint"), Identity.WetsuitTint);
    }
    // Slot forensics ("I still don't see faces inside the helmets",
    // 2026-09-02): which material each CC0 section actually renders with.
    for (int32 MaterialIndex = 0; MaterialIndex < Slots.Num(); ++MaterialIndex)
    {
        const UMaterialInterface* Assigned = Body->GetMaterial(MaterialIndex);
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim CC0 slot %d '%s' -> %s"),
            MaterialIndex,
            *Slots[MaterialIndex].MaterialSlotName.ToString(),
            Assigned ? *Assigned->GetPathName() : TEXT("<none>"));
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
            GetSolvedFaceUpWorldVector() * AnchorDropCm -
            GetSolvedFaceForwardWorldVector() * (bCurrentGuide ? ResolvedGuideHelmetBackCm()
                : CrewHelmetAnchorBackCm[FMath::Clamp(CurrentVariantIndex, 0, 3)]);
    }
    const FTransform HeadTransform = Body->GetBoneTransformByName(
        TEXT("head"), EBoneSpaces::ComponentSpace);
    const FVector LocalEyeCenterCm = bCurrentGuide
        ? GuideHeadLocalEyeCenterCm
        : CrewHeadLocalEyeCentersCm[FMath::Clamp(CurrentVariantIndex, 0, 3)];
    // Rotate-and-translate only: the head's component transform carries the
    // importer's 100x unit scale, which would blow the offset up 100-fold.
    return Body->GetComponentTransform().TransformPosition(
        HeadTransform.GetLocation() +
        HeadTransform.GetRotation().RotateVector(LocalEyeCenterCm / BodyScale)) -
        GetSolvedFaceForwardWorldVector() * (bCurrentGuide ? ResolvedGuideHelmetBackCm()
            : CrewHelmetAnchorBackCm[FMath::Clamp(CurrentVariantIndex, 0, 3)]);
}

float ARaftSimCC0CrewVisualActor::GetRecommendedWhitewaterHelmetScale() const
{
    return bCurrentGuide ? ResolvedGuideHelmetScale() : CrewHelmetFitScale;
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
    // The review CVar overrides the fit when moved off its 4.5 cm default.
    const float ReviewForwardCm = CVarCC0VestForwardOfSpineCm.GetValueOnGameThread();
    return ComputeChestWorldTransform(
        bVestFitMeasured && FMath::IsNearlyEqual(ReviewForwardCm, 4.5f)
            ? FittedVestForwardOfSpineCm
            : ReviewForwardCm,
        OutWorld);
}

bool ARaftSimCC0CrewVisualActor::ComputeChestWorldTransform(
    float ForwardOfSpineCm,
    FTransform& OutWorld) const
{
    if (!bBodyReady || !Body ||
        Body->GetBoneIndex(TEXT("spine_01")) == INDEX_NONE ||
        Body->GetBoneIndex(TEXT("spine_02")) == INDEX_NONE ||
        Body->GetBoneIndex(TEXT("spine_03")) == INDEX_NONE ||
        Body->GetBoneIndex(TEXT("neck_01")) == INDEX_NONE ||
        Body->GetBoneIndex(TEXT("upperarm_l")) == INDEX_NONE ||
        Body->GetBoneIndex(TEXT("upperarm_r")) == INDEX_NONE)
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
    // Worn torso gear must not follow the head. Projecting the face direction
    // onto the chest plane spun the whole vest sideways in reentry and becomes
    // ill-conditioned when looking down along the spine. The rendered shoulder
    // line and spine define the chest independently of gaze.
    const FVector ShoulderRight = ComponentTransform.TransformVectorNoScale(
        BoneComponentLocation(TEXT("upperarm_r")) -
        BoneComponentLocation(TEXT("upperarm_l")));
    const FVector ChestForward = FVector::CrossProduct(ShoulderRight, SpineUp).GetSafeNormal();
    if (ChestForward.IsNearlyZero())
    {
        return false;
    }
    // ApplyBodyPose maps the host torso anchor between spine_02 and
    // spine_03 in HEIGHT, but the spinal column runs along the back of the
    // body while the host anchor is the torso volume centre — the vest mesh
    // is authored around the latter. Push the origin forward by the
    // spine-to-chest-centre depth. Posed central torso measurements and all-five
    // front/profile/rear captures place it at 4.5 cm: the former 9 cm floated
    // the chest panels forward while burying the rear flotation in the back.
    const float ChestCenterForwardOfSpineCm = ForwardOfSpineCm;
    OutWorld = FTransform(
        FRotationMatrix::MakeFromZX(SpineUp, ChestForward).ToQuat(),
        ComponentTransform.TransformPosition(
            FMath::Lerp(Spine02, Spine03, 0.45f)) +
            ChestForward * ChestCenterForwardOfSpineCm +
            SpineUp * ProductionVestLiftAlongSpineCm);
    return true;
}

bool ARaftSimCC0CrewVisualActor::EnsureBodyLoaded()
{
    if (!Body)
    {
        bBodyReady = false;
        return false;
    }
    const FString SelectedMeshPath = GetSelectedMeshPath();
    if (bBodyReady && Body->GetSkinnedAsset() &&
        Body->GetSkinnedAsset()->GetPathName().Equals(
            SelectedMeshPath, ESearchCase::CaseSensitive))
    {
        // ApplyCrewPose reaches this function for every visible rafter every
        // frame. Reloading the already-resident mesh, walking every material
        // slot, resetting visibility, and printing the slot table here made
        // the five-person South Fork raft run at roughly one frame per
        // second. Mesh/material setup belongs to the appearance transition;
        // the pose path only needs the cached reference transforms below.
        return true;
    }
    USkeletalMesh* Mesh = LoadObject<USkeletalMesh>(nullptr, *SelectedMeshPath);
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
    ApplyProductionBodyMaterialOverrides(
        Body, Mesh, URaftSimCrewRoster::GetIdentityForVariant(CurrentVariantIndex, bCurrentGuide));
    bBodyReady = ReferenceComponentTransforms.Num() >= 19;
    Body->SetVisibility(bBodyReady, true);
    if (bBodyReady && (bMeshChanged || !bNeckCollarBuilt))
    {
        BuildNeckCollar();
    }
    if (bMeshChanged)
    {
        bVestFitMeasured = false;
    }
    return bBodyReady;
}

void ARaftSimCC0CrewVisualActor::CacheReferencePose()
{
    ReferenceComponentTransforms.Reset();
    RenderedFaceAnchorVertexIndices.Reset();
    RenderedFaceAnchorHeadLocal = FVector::ZeroVector;
    bHasRenderedFaceAnchorHeadLocal = false;
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

void ARaftSimCC0CrewVisualActor::LogPoseForensics(
    const FVector& NeckBaseCm,
    const FVector& HeadCenterCm) const
{
    if (!Body)
    {
        return;
    }
    USkeletalMesh* Mesh = Cast<USkeletalMesh>(Body->GetSkinnedAsset());
    FSkeletalMeshRenderData* RenderData = Mesh ? Mesh->GetResourceForRendering() : nullptr;
    FSkinWeightVertexBuffer* SkinWeights = Body->GetSkinWeightBuffer(0);
    if (!Mesh || !RenderData || RenderData->LODRenderData.IsEmpty() || !SkinWeights)
    {
        return;
    }
    const FSkeletalMeshLODRenderData& LODData = RenderData->LODRenderData[0];
    const TArray<FSkeletalMaterial>& Materials = Mesh->GetMaterials();
    const FReferenceSkeleton& RefSkeleton = Mesh->GetRefSkeleton();
    TArray<FMatrix44f> CachedRefToLocals;
    Body->CacheRefToLocalMatrices(CachedRefToLocals);
    auto DrivenZ = [this](const TCHAR* BoneName)
    {
        return Body->GetBoneTransformByName(
            FName(BoneName), EBoneSpaces::ComponentSpace).GetLocation().Z * BodyScale;
    };
    auto RestZ = [this](const TCHAR* BoneName)
    {
        const FTransform* Reference = ReferenceComponentTransforms.Find(BoneName);
        return Reference ? Reference->GetLocation().Z * BodyScale : -1.0f;
    };
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim CC0 pose forensics %s: rest z pelvis=%.1f spine_03=%.1f neck_01=%.1f head=%.1f upperarm_l=%.1f | driven z pelvis=%.1f spine_03=%.1f neck_01=%.1f head=%.1f upperarm_l=%.1f | targets neck base=%.1f head=%.1f"),
        *Mesh->GetName(),
        RestZ(TEXT("pelvis")), RestZ(TEXT("spine_03")), RestZ(TEXT("neck_01")),
        RestZ(TEXT("head")), RestZ(TEXT("upperarm_l")),
        DrivenZ(TEXT("pelvis")), DrivenZ(TEXT("spine_03")), DrivenZ(TEXT("neck_01")),
        DrivenZ(TEXT("head")), DrivenZ(TEXT("upperarm_l")),
        NeckBaseCm.Z, HeadCenterCm.Z);
    const FTransform DrivenHead = Body->GetBoneTransformByName(
        TEXT("head"), EBoneSpaces::ComponentSpace);
    const FTransform* RestHead = ReferenceComponentTransforms.Find(TEXT("head"));
    if (RestHead)
    {
        auto Axes = [](const FTransform& Transform)
        {
            const FVector X = Transform.GetRotation().RotateVector(FVector::XAxisVector);
            const FVector Y = Transform.GetRotation().RotateVector(FVector::YAxisVector);
            const FVector Z = Transform.GetRotation().RotateVector(FVector::ZAxisVector);
            return FString::Printf(TEXT("X=(%.2f,%.2f,%.2f) Y=(%.2f,%.2f,%.2f) Z=(%.2f,%.2f,%.2f)"),
                X.X, X.Y, X.Z, Y.X, Y.Y, Y.Z, Z.X, Z.Y, Z.Z);
        };
        FVector DrivenEyes = FVector::ZeroVector;
        FVector RestEyes = FVector::ZeroVector;
        for (const int32 VertexIndex : RenderedFaceAnchorVertexIndices)
        {
            DrivenEyes += FVector(USkinnedMeshComponent::GetSkinnedVertexPosition(
                Body, VertexIndex, LODData, *SkinWeights, CachedRefToLocals));
            RestEyes += FVector(
                LODData.StaticVertexBuffers.PositionVertexBuffer.VertexPosition(VertexIndex));
        }
        if (RenderedFaceAnchorVertexIndices.Num() > 0)
        {
            DrivenEyes /= RenderedFaceAnchorVertexIndices.Num();
            RestEyes /= RenderedFaceAnchorVertexIndices.Num();
        }
        const FVector DrivenEyeOffset = DrivenEyes - DrivenHead.GetLocation();
        const FVector RestEyeOffset = RestEyes - RestHead->GetLocation();
        auto ScaleString = [](const FVector& Scale)
        {
            return FString::Printf(TEXT("(%.2f,%.2f,%.2f)"), Scale.X, Scale.Y, Scale.Z);
        };
        const int32 HeadIndex = RefSkeleton.FindBoneIndex(TEXT("head"));
        const FVector RefPoseHeadScale = RefSkeleton.GetRefBonePose().IsValidIndex(HeadIndex)
            ? RefSkeleton.GetRefBonePose()[HeadIndex].GetScale3D()
            : FVector::ZeroVector;
        const FVector LocalHeadScale = Body->GetBoneSpaceTransforms().IsValidIndex(HeadIndex)
            ? Body->GetBoneSpaceTransforms()[HeadIndex].GetScale3D()
            : FVector::ZeroVector;
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim CC0 pose forensics %s: scales head driven=%s rest=%s local=%s refpose=%s | neck_01 driven=%s | spine_03 driven=%s | head-hidden=%d"),
            *Mesh->GetName(),
            *ScaleString(DrivenHead.GetScale3D()),
            *ScaleString(RestHead->GetScale3D()),
            *ScaleString(LocalHeadScale),
            *ScaleString(RefPoseHeadScale),
            *ScaleString(Body->GetBoneTransformByName(
                TEXT("neck_01"), EBoneSpaces::ComponentSpace).GetScale3D()),
            *ScaleString(Body->GetBoneTransformByName(
                TEXT("spine_03"), EBoneSpaces::ComponentSpace).GetScale3D()),
            bHeadHiddenForFirstPerson ? 1 : 0);
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim CC0 pose forensics %s: head joint driven=(%.1f, %.1f, %.1f) axes %s | rest axes %s | eyes minus joint driven=(%.1f, %.1f, %.1f) rest=(%.1f, %.1f, %.1f)"),
            *Mesh->GetName(),
            DrivenHead.GetLocation().X, DrivenHead.GetLocation().Y, DrivenHead.GetLocation().Z,
            *Axes(DrivenHead),
            *Axes(*RestHead),
            DrivenEyeOffset.X, DrivenEyeOffset.Y, DrivenEyeOffset.Z,
            RestEyeOffset.X, RestEyeOffset.Y, RestEyeOffset.Z);
    }
    for (const FSkelMeshRenderSection& Section : LODData.RenderSections)
    {
        if (!Materials.IsValidIndex(Section.MaterialIndex) ||
            !Materials[Section.MaterialIndex].MaterialSlotName.ToString().Contains(
                TEXT("Wetsuit"), ESearchCase::IgnoreCase))
        {
            continue;
        }
        float ApexZ = TNumericLimits<float>::Lowest();
        uint32 ApexVertex = Section.BaseVertexIndex;
        FVector ApexDriven = FVector::ZeroVector;
        const uint32 EndVertex = Section.BaseVertexIndex + Section.NumVertices;
        // Measure the rendered central torso, not bone anchors or the vest
        // against its own transform. Narrow lateral bands exclude the arms.
        FTransform ChestWorld;
        const bool HasChest = GetSolvedChestWorldTransform(ChestWorld);
        FBox TorsoBands[3] = {FBox(ForceInit), FBox(ForceInit), FBox(ForceInit)};
        int32 BandCounts[3] = {0, 0, 0};
        for (uint32 VertexIndex = Section.BaseVertexIndex; VertexIndex < EndVertex; ++VertexIndex)
        {
            const FVector Driven(USkinnedMeshComponent::GetSkinnedVertexPosition(
                Body, VertexIndex, LODData, *SkinWeights, CachedRefToLocals));
            if (HasChest)
            {
                const FVector P = ChestWorld.InverseTransformPosition(
                    Body->GetComponentTransform().TransformPosition(Driven));
                if (FMath::Abs(P.Y) <= 8.0 && P.Z >= -12.0 && P.Z < 18.0)
                {
                    const int32 Band = FMath::FloorToInt((P.Z + 12.0) / 10.0);
                    TorsoBands[Band] += P;
                    ++BandCounts[Band];
                }
            }
            if (Driven.Z > ApexZ)
            {
                ApexZ = Driven.Z;
                ApexVertex = VertexIndex;
                ApexDriven = Driven;
            }
        }
        for (int32 Band = 0; Band < 3; ++Band)
        {
            if (BandCounts[Band] > 0)
            {
                UE_LOG(LogTemp, Display,
                    TEXT("CC0_VEST_BODY_BAND mesh=%s band=%d count=%d forward=%.4f min_x=%.4f max_x=%.4f min_z=%.4f max_z=%.4f"),
                    *Mesh->GetName(), Band, BandCounts[Band],
                    CVarCC0VestForwardOfSpineCm.GetValueOnGameThread(),
                    TorsoBands[Band].Min.X, TorsoBands[Band].Max.X,
                    TorsoBands[Band].Min.Z, TorsoBands[Band].Max.Z);
            }
        }
        FString Influences;
        const FSkinWeightInfo ApexWeights = SkinWeights->GetVertexSkinWeights(ApexVertex);
        for (int32 Influence = 0; Influence < MAX_TOTAL_INFLUENCES; ++Influence)
        {
            if (ApexWeights.InfluenceWeights[Influence] == 0)
            {
                continue;
            }
            const int32 LocalBone = ApexWeights.InfluenceBones[Influence];
            const int32 SkeletonBone = Section.BoneMap.IsValidIndex(LocalBone)
                ? Section.BoneMap[LocalBone]
                : INDEX_NONE;
            Influences += FString::Printf(TEXT(" %s:%.2f"),
                SkeletonBone != INDEX_NONE
                    ? *RefSkeleton.GetBoneName(SkeletonBone).ToString()
                    : TEXT("?"),
                ApexWeights.InfluenceWeights[Influence] / 65535.0f);
        }
        const FVector RestPosition(
            LODData.StaticVertexBuffers.PositionVertexBuffer.VertexPosition(ApexVertex));
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim CC0 pose forensics %s: wetsuit apex driven=(%.1f, %.1f, %.1f) rest=(%.1f, %.1f, %.1f) influences:%s"),
            *Mesh->GetName(),
            ApexDriven.X * BodyScale, ApexDriven.Y * BodyScale, ApexDriven.Z * BodyScale,
            RestPosition.X, RestPosition.Y, RestPosition.Z,
            *Influences);
    }
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

    const FTransform* ReferenceHead = ReferenceComponentTransforms.Find(TEXT("head"));
    if (ReferenceHead == nullptr || RenderedFaceAnchorVertexIndices.IsEmpty())
    {
        return;
    }
    FVector RestEyeCenter = FVector::ZeroVector;
    for (const int32 VertexIndex : RenderedFaceAnchorVertexIndices)
    {
        RestEyeCenter += FVector(
            LODData.StaticVertexBuffers.PositionVertexBuffer.VertexPosition(VertexIndex));
    }
    RestEyeCenter /= RenderedFaceAnchorVertexIndices.Num();
    RenderedFaceAnchorHeadLocal = ReferenceHead->InverseTransformPosition(RestEyeCenter);
    bHasRenderedFaceAnchorHeadLocal = !RenderedFaceAnchorHeadLocal.ContainsNaN();
}

bool ARaftSimCC0CrewVisualActor::GetViewEyeCenterWorld(FVector& OutWorldLocation) const
{
    const FTransform* ReferenceHead = ReferenceComponentTransforms.Find(TEXT("head"));
    if (!bBodyReady || !Body || !bHasRenderedFaceAnchorHeadLocal || !ReferenceHead ||
        Body->GetBoneIndex(TEXT("head")) == INDEX_NONE)
    {
        return false;
    }
    FTransform HeadTransform = Body->GetBoneTransformByName(
        TEXT("head"), EBoneSpaces::ComponentSpace);
    // First-person visibility collapses this bone to zero scale. Recover the
    // anatomical landmark in a copy; never unhide/mutate the rendered head.
    HeadTransform.SetScale3D(ReferenceHead->GetScale3D());
    OutWorldLocation = Body->GetComponentTransform().TransformPosition(
        HeadTransform.TransformPosition(RenderedFaceAnchorHeadLocal));
    return !OutWorldLocation.ContainsNaN();
}

bool ARaftSimCC0CrewVisualActor::TryGetRenderedFaceEyeCenterWorld(
    FVector& OutWorldLocation) const
{
    if (!Body || !bHasRenderedFaceAnchorHeadLocal ||
        Body->GetBoneIndex(TEXT("head")) == INDEX_NONE)
    {
        return false;
    }
    const FTransform HeadTransform = Body->GetBoneTransformByName(
        TEXT("head"), EBoneSpaces::ComponentSpace);
    const FVector ComponentCenter =
        HeadTransform.TransformPosition(RenderedFaceAnchorHeadLocal);
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
    FRaftSimCrewAvatarPose Pose;
    const ARaftSimCrewAvatarActor* Host = Cast<ARaftSimCrewAvatarActor>(GetParentActor());
    if (!Host || !Host->TryGetRenderedPose(Action, NormalizedPhase, Pose))
    {
        Pose = URaftSimCrewAvatarPoseLibrary::EvaluatePose(Action, SafePhase, SeatSide);
    }
    UpdateGaze(Action);
    ApplyBodyPose(Pose);
    if (!bVestFitMeasured && Action == ERaftSimCrewAvatarAction::SeatedIdle)
    {
        MeasureVestFit();
    }
}

bool ARaftSimCC0CrewVisualActor::GetRestFootMeasurementsCm(
    float& OutAnkleToBallCm,
    float& OutAnkleHeightCm) const
{
    const FTransform* Foot = ReferenceComponentTransforms.Find(TEXT("foot_l"));
    const FTransform* Ball = ReferenceComponentTransforms.Find(TEXT("ball_l"));
    if (!bBodyReady || !Foot || !Ball)
    {
        return false;
    }
    const FVector AnkleToBall = (Ball->GetLocation() - Foot->GetLocation()) * BodyScale;
    // The ball joint sits 0.88 cm above the sole in every CC0 foot
    // (build_production_river_sandal.py), so the ankle height follows it.
    OutAnkleToBallCm = AnkleToBall.Size2D();
    OutAnkleHeightCm = -AnkleToBall.Z + 0.88f * BodyScale;
    return OutAnkleToBallCm > 5.0f && OutAnkleHeightCm > 3.0f;
}

FVector ARaftSimCC0CrewVisualActor::ToMeshSpace(const FVector& PointCm) const
{
    return PointCm / BodyScale;
}

TArray<FVector> ARaftSimCC0CrewVisualActor::GetPosedBodyVerticesWorldCmForValidation() const
{
    TArray<FVector> Result;
    USkeletalMesh* Mesh = Body ? Cast<USkeletalMesh>(Body->GetSkinnedAsset()) : nullptr;
    FSkeletalMeshRenderData* Data = Mesh ? Mesh->GetResourceForRendering() : nullptr;
    FSkinWeightVertexBuffer* Weights = Body ? Body->GetSkinWeightBuffer(0) : nullptr;
    if (!bBodyReady || !Data || Data->LODRenderData.IsEmpty() || !Weights) return Result;
    const FSkeletalMeshLODRenderData& LOD = Data->LODRenderData[0];
    if (!LOD.StaticVertexBuffers.PositionVertexBuffer.GetVertexData() ||
        !Weights->GetDataVertexBuffer()->GetWeightData()) return Result;
    TArray<FMatrix44f> Matrices;
    Body->CacheRefToLocalMatrices(Matrices);
    const FTransform BodyWorld = Body->GetComponentTransform();
    Result.Reserve(LOD.GetNumVertices());
    for (uint32 Index = 0; Index < LOD.GetNumVertices(); ++Index)
        Result.Add(BodyWorld.TransformPosition(FVector(USkinnedMeshComponent::GetSkinnedVertexPosition(
            Body, Index, LOD, *Weights, Matrices))));
    return Result;
}

TArray<FVector> ARaftSimCC0CrewVisualActor::GetSeatedContactPointsLocalCm() const
{
    TArray<FVector> Result;
    const AActor* Host = GetParentActor();
    USkeletalMesh* Mesh = Body ? Cast<USkeletalMesh>(Body->GetSkinnedAsset()) : nullptr;
    FSkeletalMeshRenderData* Data = Mesh ? Mesh->GetResourceForRendering() : nullptr;
    FSkinWeightVertexBuffer* Weights = Body ? Body->GetSkinWeightBuffer(0) : nullptr;
    if (!bBodyReady || !Host || !Data || Data->LODRenderData.IsEmpty() || !Weights)
    {
        return Result;
    }
    const FSkeletalMeshLODRenderData& LOD = Data->LODRenderData[0];
    if (!LOD.StaticVertexBuffers.PositionVertexBuffer.GetVertexData() ||
        !Weights->GetDataVertexBuffer()->GetWeightData())
    {
        return Result;
    }
    TArray<FMatrix44f> Matrices;
    Body->CacheRefToLocalMatrices(Matrices);
    const FTransform BodyWorld = Body->GetComponentTransform();
    const FTransform HostWorld = Host->GetActorTransform();
    // Keep the lowest vertex in each 2 cm cell of the glute footprint.
    // This excludes the forward knees/boots and costs nothing per frame.
    TMap<FIntPoint, FVector> Underside;
    for (uint32 Index = 0; Index < LOD.GetNumVertices(); ++Index)
    {
        const FVector MeshPoint(USkinnedMeshComponent::GetSkinnedVertexPosition(
            Body, Index, LOD, *Weights, Matrices));
        const FVector P = HostWorld.InverseTransformPosition(
            BodyWorld.TransformPosition(MeshPoint));
        if (P.ContainsNaN() || P.X < -24.0 || P.X > 6.0 ||
            FMath::Abs(P.Y) > 22.0 || P.Z < 12.0 || P.Z > 40.0)
        {
            continue;
        }
        const FIntPoint Cell(FMath::FloorToInt(P.X / 2.0), FMath::FloorToInt(P.Y / 2.0));
        FVector* Existing = Underside.Find(Cell);
        if (!Existing || P.Z < Existing->Z)
        {
            Underside.Add(Cell, P);
        }
    }
    Underside.GenerateValueArray(Result);
    return Result;
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
    const bool bCalf = BoneName == TEXT("calf_l") || BoneName == TEXT("calf_r");
    const bool bThigh = BoneName == TEXT("thigh_l") || BoneName == TEXT("thigh_r");
    if (bCalf || bThigh)
    {
        const FVector LocalAxis = Reference->GetRotation().UnrotateVector(ReferenceDirection);
        const FVector AbsAxis = LocalAxis.GetAbs();
        const int32 Axis = AbsAxis.X > AbsAxis.Y ? (AbsAxis.X > AbsAxis.Z ? 0 : 2) : (AbsAxis.Y > AbsAxis.Z ? 1 : 2);
        const FVector SourceEndLocal = Reference->InverseTransformPosition(ReferenceEnd->GetLocation());
        const double BeforeError = FVector::Distance(Target.TransformPosition(SourceEndLocal), ToMeshSpace(DesiredEndCm));
        static const bool bFitCalf = FParse::Param(FCommandLine::Get(), TEXT("RaftSimFitCalfSpanReview"));
        static const bool bFitLeg = FParse::Param(FCommandLine::Get(), TEXT("RaftSimFitLegSpanReview"));
        const bool bFit = bFitLeg || (bCalf && bFitCalf);
        if (bFit && AbsAxis[Axis] > .9999)
        {
            FVector Scale = Target.GetScale3D();
            Scale[Axis] *= FVector::Distance(ToMeshSpace(DesiredStartCm), ToMeshSpace(DesiredEndCm)) /
                FVector::Distance(Reference->GetLocation(), ReferenceEnd->GetLocation());
            Target.SetScale3D(Scale);
        }
        static TSet<FName> LoggedLegSpans;
        if (!LoggedLegSpans.Contains(BoneName))
        {
            LoggedLegSpans.Add(BoneName);
            UE_LOG(LogTemp, Display, TEXT("LEG_SPAN_REVIEW bone=%s fit=%d axis=%s source_cm=%.9f target_cm=%.9f endpoint_before_cm=%.9f endpoint_after_cm=%.9f"),
                *BoneName.ToString(), bFit, *LocalAxis.ToString(), FVector::Distance(Reference->GetLocation(), ReferenceEnd->GetLocation()),
                FVector::Distance(ToMeshSpace(DesiredStartCm), ToMeshSpace(DesiredEndCm)), BeforeError,
                FVector::Distance(Target.TransformPosition(SourceEndLocal), ToMeshSpace(DesiredEndCm)));
        }
    }
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
    // The host pose is a compact collision silhouette: hips to neck base
    // span about 35 cm where this rig's spine runs about 57. Skin keeps its
    // rest offset from each bone origin, so driving the spine bones to the
    // host's interpolated points stacked the chest on top of itself —
    // spine_03 alone carries 35 cm of upper chest and collar, which landed
    // at chin height: the neoprene collar spiked over every face ("I still
    // don't see faces inside the helmets") and the chest top stood above
    // the vest ("black material ... much too high to be shoulders",
    // 2026-09-02; the collar took the wetsuit slot's material when that
    // slot was swapped, and its apex vertex was 99% spine_03). Walk the
    // axial chain with the rig's own rest lengths from the hips, borrowing
    // only the host's segment directions; helmet fit still follows the
    // rendered eyes and gameplay authority stays with the host pose.
    auto RestLengthCm = [this](const TCHAR* FromBone, const TCHAR* ToBone)
    {
        const FTransform* From = ReferenceComponentTransforms.Find(FromBone);
        const FTransform* To = ReferenceComponentTransforms.Find(ToBone);
        return (From && To)
            ? static_cast<float>(
                  FVector::Distance(From->GetLocation(), To->GetLocation())) * BodyScale
            : 0.0f;
    };
    auto Advance = [&TorsoUp](
        const FVector& StartCm, const FVector& HostDirection, float LengthCm)
    {
        FVector Direction = HostDirection.GetSafeNormal();
        if (Direction.IsNearlyZero())
        {
            Direction = TorsoUp;
        }
        return StartCm + Direction * LengthCm;
    };
    const FVector PelvisCm = HipCenter;
    const FVector Spine01Cm = Advance(
        PelvisCm, LowerSpine - HipCenter, RestLengthCm(TEXT("pelvis"), TEXT("spine_01")));
    const FVector Spine02Cm = Advance(
        Spine01Cm, MidSpine - LowerSpine, RestLengthCm(TEXT("spine_01"), TEXT("spine_02")));
    const FVector Spine03Cm = Advance(
        Spine02Cm, UpperSpine - MidSpine, RestLengthCm(TEXT("spine_02"), TEXT("spine_03")));
    const FVector NeckBaseCm = Advance(
        Spine03Cm, NeckBase - UpperSpine, RestLengthCm(TEXT("spine_03"), TEXT("neck_01")));
    const FVector PresentedHeadCenter = Advance(
        NeckBaseCm, Pose.HeadCenterCm - NeckBase, RestLengthCm(TEXT("neck_01"), TEXT("head")));
    // Aligning the authored neck-to-head shaft with the torso-up axis leaves
    // the rendered face pitched about 20 degrees skyward (forensics: face
    // vector (0.94, 0, 0.35)); tip the crown forward by that much so the
    // gaze runs level downriver and the helmet brim sits over the brow.
    const FVector TorsoRight = Pose.TorsoRotation.Quaternion().RotateVector(FVector::RightVector);
    // Personal idle gaze: the skull turns about the neck (the neck takes a
    // share of the yaw so the skin between does not wring) and dips toward
    // the water. Headgear and eyewear read the solved head, so they follow.
    const float GazeYaw = GazeYawDegrees * GazeWeight;
    const float GazePitch = GazePitchDegrees * GazeWeight;
    const FVector HeadUp = TorsoUp.RotateAngleAxis(
        ProductionHeadLevelPitchDegrees + GazePitch, TorsoRight);
    const FVector HeadTop = PresentedHeadCenter + HeadUp * 16.0f;

    SetSegmentBone(TEXT("pelvis"), TEXT("spine_01"), PelvisCm, Spine01Cm,
        ProductionAxialFacingTwistDegrees);
    SetSegmentBone(TEXT("spine_01"), TEXT("spine_02"), Spine01Cm, Spine02Cm,
        ProductionAxialFacingTwistDegrees);
    SetSegmentBone(TEXT("spine_02"), TEXT("spine_03"), Spine02Cm, Spine03Cm,
        ProductionAxialFacingTwistDegrees);
    SetSegmentBone(TEXT("spine_03"), TEXT("neck_01"), Spine03Cm, NeckBaseCm,
        ProductionAxialFacingTwistDegrees);
    SetSegmentBone(TEXT("neck_01"), TEXT("head"), NeckBaseCm, PresentedHeadCenter,
        ProductionAxialFacingTwistDegrees + GazeYaw * 0.45f);
    SetSegmentBone(TEXT("head"), TEXT("head"), PresentedHeadCenter, HeadTop,
        ProductionAxialFacingTwistDegrees + GazeYaw);

    // The shoulders hang from the rig's chest top, not the host shoulder
    // line: children of the driven spine already sit at their rest offsets,
    // so read them back rather than pulling the deltoids down to the
    // host's compact silhouette. Return the shoulder girdle to its rest
    // offsets first: the bones keep last frame's local transforms, so the
    // girdle's moved shoulder below would otherwise be read back as the next
    // frame's rest shoulder and walk further every frame.
    for (const TCHAR* Bone : {TEXT("clavicle_l"), TEXT("upperarm_l"), TEXT("clavicle_r"), TEXT("upperarm_r")})
    {
        Body->ResetBoneTransformByName(FName(Bone));
    }
    Body->RefreshBoneTransforms();
    auto DrivenBoneCm = [this](const TCHAR* BoneName)
    {
        return Body->GetBoneTransformByName(
            FName(BoneName), EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
    };
    const FVector LeftShoulderCm = DrivenBoneCm(TEXT("upperarm_l"));
    const FVector RightShoulderCm = DrivenBoneCm(TEXT("upperarm_r"));
    const FVector RigShoulderCenterCm = (LeftShoulderCm + RightShoulderCm) * 0.5f;
    const FVector RigClavicleCenterCm =
        (DrivenBoneCm(TEXT("clavicle_l")) + DrivenBoneCm(TEXT("clavicle_r"))) * 0.5f;
    const FVector LeftClavicleRoot = RigClavicleCenterCm +
        (LeftShoulderCm - RigShoulderCenterCm) * ProductionClavicleRootLateralFraction;
    const FVector RightClavicleRoot = RigClavicleCenterCm +
        (RightShoulderCm - RigShoulderCenterCm) * ProductionClavicleRootLateralFraction;
    PresentedHeadShoulderClearanceCm = FVector::DotProduct(
        PresentedHeadCenter - RigShoulderCenterCm,
        TorsoUp);

    // The pose contract publishes palm/grip targets while the imported hand
    // bone is a wrist pivot. Offset each wrist by its own hash-locked reference
    // palm vector so the visible knuckle plane, not the wrist, meets the
    // side-correct paddle handle.
    const bool bPalmTarget = HasHeldGrip(Pose) || Pose.BoardingPalmSupportBlend > 0.f ||
        Pose.BoardingPaddleGripBlend > 0.f;
    const FVector LeftWristCm = bPalmTarget
        ? ResolvePaddleGripWristCm(true, Pose, Pose.LeftHandCm)
        : Pose.LeftHandCm;
    const FVector RightWristCm = bPalmTarget
        ? ResolvePaddleGripWristCm(false, Pose, Pose.RightHandCm)
        : Pose.RightHandCm;
    // The shoulder girdle follows a reaching arm. The rig's shoulder joint is
    // read back from the driven chest, so a hand near full reach (the top
    // hand driving the T-grip out over the water at the catch) pulled the
    // arm out of its socket and folded the skin over the shoulder ("the arm
    // seems to pull out of position making the shoulder fold over",
    // 2026-10-05). As a paddler's shoulder blade slides forward and rises,
    // move the joint toward the hand as the reach nears full extension, and
    // up as the hand rises above it; the clavicle swings to follow. The
    // first-person guide keeps a still shoulder: the fold is out of their own
    // view, and a shoulder sliding beside the eye camera filled its corner.
    const bool bStillShoulders = bHeadHiddenForFirstPerson;
    const auto GirdleShoulder = [&RestLengthCm, &TorsoUp, bStillShoulders](
        bool bLeftArm, const FVector& RestShoulderCm, const FVector& WristCm)
    {
        if (bStillShoulders)
        {
            return RestShoulderCm;
        }
        const float ArmCm = bLeftArm
            ? RestLengthCm(TEXT("upperarm_l"), TEXT("lowerarm_l")) + RestLengthCm(TEXT("lowerarm_l"), TEXT("hand_l"))
            : RestLengthCm(TEXT("upperarm_r"), TEXT("lowerarm_r")) + RestLengthCm(TEXT("lowerarm_r"), TEXT("hand_r"));
        const FVector ToWrist = WristCm - RestShoulderCm;
        const float ReachCm = ToWrist.Size();
        if (ArmCm <= 1.0f || ReachCm <= KINDA_SMALL_NUMBER)
        {
            return RestShoulderCm;
        }
        constexpr float kMaxProtractionCm = 11.0f;
        constexpr float kMaxElevationCm = 4.0f;
        const float Protraction = FMath::Clamp(ReachCm - 0.84f * ArmCm, 0.0f, kMaxProtractionCm);
        const float Rise = FMath::Clamp(FVector::DotProduct(ToWrist, TorsoUp) / ReachCm, 0.0f, 1.0f);
        return RestShoulderCm + ToWrist / ReachCm * Protraction + TorsoUp * (kMaxElevationCm * Rise);
    };
    const FVector LeftArmShoulderCm = GirdleShoulder(true, LeftShoulderCm, LeftWristCm);
    const FVector RightArmShoulderCm = GirdleShoulder(false, RightShoulderCm, RightWristCm);
    // Two-bone elbows on the rig's own upper-arm and forearm lengths. The
    // former elbow, 48 % of the way to the wrist, kept every arm straight:
    // a hand brought in toward the chin (the T-grip) compressed the whole
    // arm, skin and all, instead of bending it. Elbows hang down, out from
    // the body and a little back, as when holding a paddle; a target beyond
    // reach leaves the arm straight and the forearm takes the difference.
    const auto SolveElbow = [&RestLengthCm, &TorsoRight, &PresentedHeadCenter, &HeadUp](
        bool bLeftArm, const FVector& ShoulderCm, const FVector& WristCm)
    {
        const float UpperCm = bLeftArm ? RestLengthCm(TEXT("upperarm_l"), TEXT("lowerarm_l"))
                                       : RestLengthCm(TEXT("upperarm_r"), TEXT("lowerarm_r"));
        const float LowerCm = bLeftArm ? RestLengthCm(TEXT("lowerarm_l"), TEXT("hand_l"))
                                       : RestLengthCm(TEXT("lowerarm_r"), TEXT("hand_r"));
        const FVector ToWrist = WristCm - ShoulderCm;
        const float ReachCm = ToWrist.Size();
        if (UpperCm <= 1.0f || LowerCm <= 1.0f || ReachCm <= KINDA_SMALL_NUMBER)
        {
            return FMath::Lerp(ShoulderCm, WristCm, 0.48f);
        }
        const FVector Along = ToWrist / ReachCm;
        // A hand reaching across the chest (the top hand on a T-grip held out
        // over the far side) leads with the elbow out and down, a little
        // forward. Swinging that elbow out and BACK like the shaft arm's
        // rolled the upper arm behind the shoulder and folded the shoulder and
        // sleeve ("the left shoulder is folded unnaturally", 2026-10-05).
        const float AcrossCm = FVector::DotProduct(ToWrist, TorsoRight) * (bLeftArm ? 1.0f : -1.0f);
        const float Across = FMath::SmoothStep(0.0f, 22.0f, AcrossCm);
        const float Out = bLeftArm ? -1.0f : 1.0f;
        const FVector PreferredPole = FVector::VectorPlaneProject(
            FMath::Lerp(FVector(-0.35f, 0.55f * Out, -1.0f), FVector(0.2f, 0.6f * Out, -0.8f), Across), Along)
            .GetSafeNormal(SMALL_NUMBER, -FVector::UpVector);
        const float SolvedReachCm = FMath::Clamp(
            ReachCm, FMath::Abs(UpperCm - LowerCm) + 0.5f, UpperCm + LowerCm - 0.05f);
        const float AlongCm = (UpperCm * UpperCm - LowerCm * LowerCm + SolvedReachCm * SolvedReachCm) /
            (2.0f * SolvedReachCm);
        const float OutCm = FMath::Sqrt(FMath::Max(0.0f, UpperCm * UpperCm - AlongCm * AlongCm));
        const auto ElbowFor = [&](const FVector& Pole) { return ShoulderCm + Along * AlongCm + Pole * OutCm; };
        // Keep the forearm off the face. A top hand held out in front of the
        // face must not drag its forearm through the chin, so turn the elbow
        // about the shoulder-wrist line, the shorter way first, until the
        // forearm clears a capsule round the head (a dropped, forward elbow
        // ran the forearm up through the mouth, 2026-10-05).
        const auto HeadClearanceCm = [&](const FVector& Elbow)
        {
            FVector OnForearm, OnHead;
            FMath::SegmentDistToSegmentSafe(Elbow, WristCm, PresentedHeadCenter,
                PresentedHeadCenter + HeadUp * 14.0f, OnForearm, OnHead);
            return FVector::Distance(OnForearm, OnHead);
        };
        constexpr float kForearmHeadClearanceCm = 14.5f;
        FVector BestPole = PreferredPole;
        float BestClearance = HeadClearanceCm(ElbowFor(PreferredPole));
        for (float Step = 15.0f; Step <= 180.0f && BestClearance < kForearmHeadClearanceCm; Step += 15.0f)
        {
            for (const float Sign : {1.0f, -1.0f})
            {
                const FVector Candidate = PreferredPole.RotateAngleAxis(Sign * Step, Along);
                const float Clearance = HeadClearanceCm(ElbowFor(Candidate));
                if (Clearance > BestClearance)
                {
                    BestPole = Candidate;
                    BestClearance = Clearance;
                }
            }
        }
        return ElbowFor(BestPole);
    };
    FVector LeftElbow = SolveElbow(true, LeftArmShoulderCm, LeftWristCm);
    FVector RightElbow = SolveElbow(false, RightArmShoulderCm, RightWristCm);
    // Swinging the upper-arm bone steeply DOWN from the rig's near-lateral
    // rest pose rolls the deltoid skin up beside the neck, so keep a bound
    // on the elbow's drop below the shoulder; the forearm still reaches the
    // true wrist, so hands stay put and the arm simply bends more. The old
    // 9 cm bound was fighting the compressed-torso chest, not the deltoid.
    const auto ClampElbowDrop = [](const FVector& ShoulderCm, FVector ElbowCm)
    {
        constexpr float kMaxElbowDropCm = 24.0f;
        ElbowCm.Z = FMath::Max(ElbowCm.Z, ShoulderCm.Z - kMaxElbowDropCm);
        return ElbowCm;
    };
    LeftElbow = ClampElbowDrop(LeftArmShoulderCm, LeftElbow);
    RightElbow = ClampElbowDrop(RightArmShoulderCm, RightElbow);
    SetSegmentBone(
        TEXT("clavicle_l"),
        TEXT("upperarm_l"),
        LeftClavicleRoot,
        LeftArmShoulderCm);
    SetSegmentBone(TEXT("upperarm_l"), TEXT("lowerarm_l"), LeftArmShoulderCm, LeftElbow);
    SetSegmentBone(TEXT("lowerarm_l"), TEXT("hand_l"), LeftElbow, LeftWristCm);
    if (bPalmTarget)
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
        RightArmShoulderCm);
    SetSegmentBone(TEXT("upperarm_r"), TEXT("lowerarm_r"), RightArmShoulderCm, RightElbow);
    SetSegmentBone(TEXT("lowerarm_r"), TEXT("hand_r"), RightElbow, RightWristCm);
    if (bPalmTarget)
    {
        SetPaddleGripHandTransform(false, Pose, RightWristCm);
    }
    else
    {
        SetBoneAtPoint(TEXT("hand_r"), RightWristCm);
    }

    const float LegFacingTwistDegrees =
        CVarRaftSimCC0LegFacingTwistDegrees.GetValueOnGameThread();
    // Explicit joint heads do not by themselves fit a source bone shaft:
    // without longitudinal fitting, blended skin can extend beyond its
    // posed child joint. Log source lengths for the endpoint audit. The
    // review-only fit corrects that mismatch; whole-skin hull clearance
    // and the normal-play promotion gate remain separate requirements.
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
    SetSegmentBone(TEXT("thigh_r"), TEXT("calf_r"), Pose.RightHipCm, Pose.RightKneeCm,
        LegFacingTwistDegrees);
    SetSegmentBone(TEXT("calf_r"), TEXT("foot_r"), Pose.RightKneeCm, Pose.RightFootCm,
        LegFacingTwistDegrees);
    // In river sandals the bare foot stands at its rest size on the footbed,
    // turned with its sandal (both read the host's footwear yaw). Under the
    // river boot it keeps its rest orientation and shrinks inside the boot.
    const ARaftSimCrewAvatarActor* FootwearHost = Cast<ARaftSimCrewAvatarActor>(GetParentActor());
    const bool bBareFeet = FootwearHost && FootwearHost->UsesProductionRiverSandals();
    const auto PlaceFoot = [this, &Pose, FootwearHost, bBareFeet](bool bLeft)
    {
        const FName FootName(bLeft ? TEXT("foot_l") : TEXT("foot_r"));
        const FName BallName(bLeft ? TEXT("ball_l") : TEXT("ball_r"));
        const FVector& FootCm = bLeft ? Pose.LeftFootCm : Pose.RightFootCm;
        SetBoneAtPoint(FootName, FootCm);
        const FTransform* RestFoot = ReferenceComponentTransforms.Find(FootName);
        const FTransform* RestBall = ReferenceComponentTransforms.Find(BallName);
        if (!bBareFeet || !RestFoot || !RestBall || FootCm.ContainsNaN())
        {
            return;
        }
        const FVector RestToe = (RestBall->GetLocation() - RestFoot->GetLocation()).GetSafeNormal2D();
        const FVector Toe = FRotator(0.0f, FootwearHost->GetFootwearYawDegrees(Pose, bLeft), 0.0f)
            .RotateVector(FVector::ForwardVector);
        if (RestToe.IsNearlyZero())
        {
            return;
        }
        FTransform Target = *RestFoot;
        Target.SetLocation(ToMeshSpace(FootCm));
        Target.SetRotation((FQuat::FindBetweenNormals(RestToe, Toe) * RestFoot->GetRotation()).GetNormalized());
        Body->SetBoneTransformByName(FootName, Target, EBoneSpaces::ComponentSpace);
    };
    PlaceFoot(true);
    PlaceFoot(false);

    // Not zero: fully collapsing the foot bone yanks every ankle-blend
    // vertex onto one point, chopping the calf into a featureless tube with
    // no taper ("their ankles look like cylindars", 2026-09-02). A third of
    // the rest scale keeps a short tapering ankle cone that disappears into
    // the production boot cuff, while the shrunken foot mesh itself stays
    // hidden inside the boot volume.
    constexpr float kHiddenFootBoneScale = 0.35f;
    // Bone scales are RELATIVE TO THE REST SCALE: the importer applies the
    // FBX metre-to-centimetre conversion as a 100x root scale, so every
    // rest component-space bone scale is (100,100,100). Restoring the
    // head with FVector::OneVector after the first-person hide made it
    // 1 % of rest — the skull, eyes and brows collapsed onto the head
    // joint and the collar's head-rigid ring stretched into a spike from
    // the chest to that point ("the crew don't have heads, you can see the
    // back of the helmet", 2026-09-02; forensics: rendered eye centroid
    // sat 0.1 cm from the joint against a 8.9 cm rest offset).
    auto RestScale = [this](const TCHAR* BoneName)
    {
        const FTransform* Reference = ReferenceComponentTransforms.Find(BoneName);
        return Reference ? Reference->GetScale3D() : FVector::OneVector;
    };
    const float FootBoneScale = bBareFeet ? 1.0f : kHiddenFootBoneScale;
    Body->SetBoneScaleByName(
        TEXT("foot_l"), RestScale(TEXT("foot_l")) * FootBoneScale,
        EBoneSpaces::ComponentSpace);
    Body->SetBoneScaleByName(
        TEXT("foot_r"), RestScale(TEXT("foot_r")) * FootBoneScale,
        EBoneSpaces::ComponentSpace);
    Body->SetBoneScaleByName(
        TEXT("head"),
        bHeadHiddenForFirstPerson ? FVector::ZeroVector : RestScale(TEXT("head")),
        EBoneSpaces::ComponentSpace);
    // Do NOT bone-scale neck_01/spine_03 to tame the wetsuit's scalloped
    // neckline: component-space scales there crush every vertex weighted
    // downstream — chest, shoulders, and arm roots collapsed while the
    // separately-placed helmets stayed put (tried and reverted,
    // 2026-09-02). The source generator assigns wetsuit/skin materials to
    // the same body surface by skin-bone weight, not a separate cloth shell.
    // Diagnose material boundaries and posed body deformation before editing
    // topology; trimming this region can remove anatomy rather than cloth.
    Body->RefreshBoneTransforms();
    ApplyPaddleGripPose(Pose);
    Body->RefreshBoneTransforms();
    UpdateNeckCollar();
    if (CVarCC0PoseForensics.GetValueOnGameThread() && !bLoggedPoseForensics)
    {
        bLoggedPoseForensics = true;
        LogPoseForensics(NeckBaseCm, PresentedHeadCenter);
    }
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
        FVector::Distance(PresentedLeftShoulderCm, LeftArmShoulderCm),
        FVector::Distance(PresentedRightShoulderCm, RightArmShoulderCm));
    bPaddleGripActive = HasHeldGrip(Pose) && HasArticulatedPaddleGripRig();
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
    const float PalmWeight = HasHeldGrip(Pose) ? 1.f :
        FMath::Clamp(Pose.BoardingPalmSupportBlend + Pose.BoardingPaddleGripBlend, 0.f, 1.f);
    return DesiredGripCm - HandDelta.RotateVector(ReferencePalmOffsetCm) * PalmWeight;
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
    // The reference normal must have the SAME sense on both hands, and the
    // cross order that achieves it mirrors with the hand: anatomical
    // finger positions flip the product's sense between left and right.
    // First pass used one shared order (left grip solved backwards,
    // 2026-08-31); the "consistent" swap then mixed senses and every
    // resting hand lay palm-up under the shaft ("the hands look twisted",
    // 2026-09-01). Measured on the rendered fingers, this order gives the
    // BACK-of-hand normal on both hands (CREW_GRIP_AUDIT, 2026-10-05); the
    // approach vectors below are written for that sense.
    const FVector ReferenceNormal =
        (bLeft ? FVector::CrossProduct(ReferenceWidth, ReferenceForward)
               : FVector::CrossProduct(ReferenceForward, ReferenceWidth))
            .GetSafeNormal();
    if (!HasHeldGrip(Pose) && Pose.BoardingPalmSupportBlend > 0.f)
    {
        // Boarding frame faces into the raft. Fingers point inward (+X),
        // palm faces the upper tube (-Z); mirrored knuckle widths preserve
        // anatomical handedness. Blend both wrist offset and orientation.
        const FQuat ReferenceBasis = FRotationMatrix::MakeFromXZ(ReferenceWidth, ReferenceNormal).ToQuat();
        const FQuat SupportBasis = FRotationMatrix::MakeFromXZ(
            bLeft ? FVector::RightVector : -FVector::RightVector, -FVector::UpVector).ToQuat();
        const FQuat SupportRotation = (SupportBasis * ReferenceBasis.Inverse() * ReferenceHand->GetRotation()).GetNormalized();
        if (Pose.BoardingPaddleGripBlend > 0.f)
        {
            // The final controls target a seated paddle grip, not reference
            // wrists. Keep the palm offset and blend toward that same basis.
            FRaftSimCrewAvatarPose GripPose = Pose;
            if (const auto* Host = Cast<ARaftSimCrewAvatarActor>(GetParentActor()))
                Host->TryGetBoardingGripDestination(GripPose);
            GripPose.bShowPaddle = true;
            return FQuat::Slerp(ResolvePaddleGripHandRotation(bLeft, GripPose),
                SupportRotation, Pose.BoardingPalmSupportBlend).GetNormalized();
        }
        return FQuat::Slerp(ReferenceHand->GetRotation(), SupportRotation, Pose.BoardingPalmSupportBlend).GetNormalized();
    }
    const FVector GripCenterCm = bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
    // The shaft hand below a capped T-grip holds the paddle thumb-up on
    // either side of the boat: its index (thumb) side points up the shaft
    // toward the T-grip, as in a handshake. Mirroring the knuckle line with
    // the hand turned every right-side paddler's shaft fist thumb-down ("the
    // right hand is gripping the paddle shaft upside down", 2026-10-05).
    const bool bUpperTGrip = IsUpperTGrip(Pose, GripCenterCm);
    const bool bShaftBelowTGrip = !Pose.bOarGrip && !bUpperTGrip &&
        IsUpperTGrip(Pose, bLeft ? Pose.RightHandCm : Pose.LeftHandCm);
    // Elsewhere the knuckle line mirrors with the hand: two hands overhand
    // on one shaft hold it thumbs toward each other.
    FVector DesiredWidth = ResolvePaddleGripAxis(Pose, GripCenterCm).GetSafeNormal();
    if (bLeft || bShaftBelowTGrip)
    {
        DesiredWidth = -DesiredWidth;
    }
    const FVector ShoulderCm = bLeft ? Pose.LeftShoulderCm : Pose.RightShoulderCm;
    // The basis normal above is the BACK of the hand in this rig: the
    // rendered fingers curl against it on every grip (CREW_GRIP_AUDIT,
    // RaftSim.Crew.GearReview, 2026-10-05). So each approach below is the
    // way the back of the hand faces. The shaft hand's back faces away from
    // the shoulder: palm toward the paddler, knuckles out over the water.
    // The T-grip hand caps the grip from above, the back of the hand up the
    // shaft and the palm pressing down toward the blade; pointing the back
    // of the hand down the shaft had every T-grip hand palm-up under the
    // crossbar ("the left hand is gripping the t-grip of the paddle upside
    // down", 2026-10-05). (Approaching it from the shoulder left the hand
    // pushing the T like a door handle.)
    // An oar handle is held overhand: the palm comes over the top of the
    // handle from the shoulder, wrist flat, knuckles up.
    const FVector PalmApproachCm = Pose.bOarGrip
        ? (GripCenterCm - ShoulderCm).GetSafeNormal() - 0.6f * FVector::UpVector
        : bUpperTGrip
        ? (Pose.PaddleTopCm - Pose.PaddleBottomCm)
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
    if (Pose.bOarGrip)
    {
        // Each hand on its own oar, its axis from the handle toward the
        // blade, as the paddle shaft runs from the top hand toward its blade.
        return FVector::DistSquared(DesiredGripCm, Pose.LeftHandCm) <=
                FVector::DistSquared(DesiredGripCm, Pose.RightHandCm)
            ? Pose.LeftOarAxis
            : Pose.RightOarAxis;
    }
    const FVector ShaftAxis =
        (Pose.PaddleBottomCm - Pose.PaddleTopCm).GetSafeNormal();
    if (ShaftAxis.IsNearlyZero())
    {
        return FVector::UpVector;
    }
    if (IsUpperTGrip(Pose, DesiredGripCm))
    {
        // Along the crossbar, which parallels the blade's width (the host
        // draws the same axis); oriented toward -Y so either top hand caps
        // it palm-down with its fingers forward.
        return URaftSimCrewAvatarPoseLibrary::GetPaddleBladeWidthAxis(ShaftAxis, false);
    }
    return ShaftAxis;
}

bool ARaftSimCC0CrewVisualActor::IsUpperTGrip(
    const FRaftSimCrewAvatarPose& Pose,
    const FVector& DesiredGripCm) const
{
    return !Pose.bOarGrip && FVector::DistSquared(DesiredGripCm, Pose.PaddleTopCm) <= 4.0f;
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
    if (!Body || !HasHeldGrip(Pose))
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
    if (!Body || !HasHeldGrip(Pose))
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
    if (!Body || !HasHeldGrip(Pose))
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
    if (!Body || !HasHeldGrip(Pose))
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
    const float GripWeight = HasHeldGrip(Pose) ? 1.f : FMath::Clamp(Pose.BoardingPaddleGripBlend, 0.f, 1.f);
    // A fist round a rope, strap or line closes much further than the
    // paddle shaft's shaped wrap; it has no prop for the shaft solve below.
    const float GripAlpha = FMath::Lerp(FMath::Lerp(0.16f, 0.32f, GripWeight), 0.95f,
        FMath::Clamp(Pose.FistGripBlend, 0.f, 1.f));
    for (const bool bLeft : {true, false})
    {
        for (const TCHAR* Digit : CC0GripDigits)
        {
            ApplyFingerChain(bLeft, Digit, GripAlpha);
        }
        if (!HasHeldGrip(Pose) && Pose.BoardingPalmSupportBlend > 0.f)
        {
            // The reference thumb is opposed below the knuckle plane. A
            // supported open palm needs thumb abduction into that plane,
            // not its curled grip posture embedded in the tube. Rotate the
            // shafts without changing their lengths, wrist or palm target.
            const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
            const FName Hand(*FString::Printf(TEXT("hand_%s"), Side));
            const auto* RefHand = ReferenceComponentTransforms.Find(Hand);
            const auto* RefIndex = ReferenceComponentTransforms.Find(FName(*FString::Printf(TEXT("index_01_%s"), Side)));
            const auto* RefMiddle = ReferenceComponentTransforms.Find(FName(*FString::Printf(TEXT("middle_01_%s"), Side)));
            const auto* RefPinky = ReferenceComponentTransforms.Find(FName(*FString::Printf(TEXT("pinky_01_%s"), Side)));
            if (RefHand && RefIndex && RefMiddle && RefPinky)
            {
                const FVector Width = RefIndex->GetLocation()-RefPinky->GetLocation();
                const FVector Forward = RefMiddle->GetLocation()-RefHand->GetLocation();
                const FVector Normal = (bLeft ? FVector::CrossProduct(Width,Forward) :
                    FVector::CrossProduct(Forward,Width)).GetSafeNormal();
                const FQuat HandDelta = Body->GetBoneTransformByName(Hand, EBoneSpaces::ComponentSpace).GetRotation() *
                    RefHand->GetRotation().Inverse();
                const FVector PlaneNormal = HandDelta.RotateVector(Normal).GetSafeNormal();
                FName Bones[3]; FTransform Current[3];
                for (int32 I = 0; I < 3; ++I)
                {
                    Bones[I] = FName(*FString::Printf(TEXT("thumb_%02d_%s"), I+1, Side));
                    Current[I] = Body->GetBoneTransformByName(Bones[I], EBoneSpaces::ComponentSpace);
                }
                FVector Start = Current[0].GetLocation();
                for (int32 I = 0; I < 3; ++I)
                {
                    FVector Shaft = I < 2 ? Current[I+1].GetLocation()-Current[I].GetLocation() :
                        Current[2].GetLocation()-Current[1].GetLocation();
                    if (I == 2)
                    {
                        const auto* RefTip = ReferenceComponentTransforms.Find(Bones[2]);
                        const auto* RefParent = ReferenceComponentTransforms.Find(Bones[1]);
                        if (RefTip && RefParent)
                            Shaft = (Current[2].GetRotation()*RefTip->GetRotation().Inverse()).RotateVector(
                                RefTip->GetLocation()-RefParent->GetLocation());
                    }
                    const FVector Flat = FVector::VectorPlaneProject(Shaft,PlaneNormal).GetSafeNormal();
                    const FQuat Swing = Flat.IsNearlyZero() || Shaft.IsNearlyZero() ? FQuat::Identity :
                        FQuat::Slerp(FQuat::Identity,FQuat::FindBetweenNormals(Shaft.GetSafeNormal(),Flat),
                            Pose.BoardingPalmSupportBlend).GetNormalized();
                    FTransform Target = Current[I];
                    Target.SetLocation(Start);
                    Target.SetRotation((Swing*Current[I].GetRotation()).GetNormalized());
                    Body->SetBoneTransformByName(Bones[I],Target,EBoneSpaces::ComponentSpace);
                    Start += Swing.RotateVector(Shaft);
                }
            }
        }
    }
    if (GripWeight <= 0.f)
    {
        return;
    }
    // Solve the existing seated contact pose, then blend each digit in its
    // parent frame. Component-position lerps would shorten finger segments.
    // Ordinary paddle poses take the unchanged full-grip path without arrays.
    TArray<FName> BlendBones, BlendParents;
    TArray<FTransform> OpenLocal;
    FRaftSimCrewAvatarPose GripPose = Pose;
    FTransform TransferHands[2];
    if (GripWeight < 1.f)
    {
        for (const bool bLeft : {true, false})
        {
            const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
            for (const TCHAR* Digit : CC0GripDigits)
            {
                FName Parent(*FString::Printf(TEXT("hand_%s"), Side));
                for (int32 Segment = 1; Segment <= 3; ++Segment)
                {
                    const FName Bone(*FString::Printf(TEXT("%s_%02d_%s"), Digit, Segment, Side));
                    BlendBones.Add(Bone); BlendParents.Add(Parent);
                    OpenLocal.Add(Body->GetBoneTransformByName(Bone, EBoneSpaces::ComponentSpace).GetRelativeTransform(
                        Body->GetBoneTransformByName(Parent, EBoneSpaces::ComponentSpace)));
                    Parent = Bone;
                }
            }
        }
    }
    if (!BlendBones.IsEmpty())
    {
        if (const auto* Host = Cast<ARaftSimCrewAvatarActor>(GetParentActor()))
            Host->TryGetBoardingGripDestination(GripPose);
        GripPose.bShowPaddle = true;
        for (const bool bLeft : {true, false})
        {
            const FName Hand(bLeft ? TEXT("hand_l") : TEXT("hand_r"));
            TransferHands[bLeft ? 0 : 1] = Body->GetBoneTransformByName(Hand, EBoneSpaces::ComponentSpace);
            const FVector Center = bLeft ? GripPose.LeftHandCm : GripPose.RightHandCm;
            SetPaddleGripHandTransform(bLeft, GripPose, ResolvePaddleGripWristCm(bLeft, GripPose, Center));
            for (const TCHAR* Digit : CC0GripDigits) ApplyFingerChain(bLeft, Digit, 0.32f);
        }
    }
    Body->RefreshBoneTransforms();
    for (const bool bLeft : {true, false})
    {
        const FVector GripCenterCm =
            bLeft ? GripPose.LeftHandCm : GripPose.RightHandCm;
        const FVector GripAxis =
            ResolvePaddleGripAxis(GripPose, GripCenterCm);
        const bool bUpperTGrip =
            IsUpperTGrip(GripPose, GripCenterCm);
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
    TArray<FTransform> ClosedLocal;
    for (int32 Index = 0; Index < BlendBones.Num(); ++Index)
        ClosedLocal.Add(Body->GetBoneTransformByName(BlendBones[Index], EBoneSpaces::ComponentSpace).GetRelativeTransform(
            Body->GetBoneTransformByName(BlendParents[Index], EBoneSpaces::ComponentSpace)));
    if (!BlendBones.IsEmpty())
    {
        // Only the destination's hand-local finger shape is used. Restore the
        // actual moving wrists before applying that shape; do not solve grip
        // wrap directions against interpolated, not-yet-grasped paddle points.
        Body->SetBoneTransformByName(TEXT("hand_l"), TransferHands[0], EBoneSpaces::ComponentSpace);
        Body->SetBoneTransformByName(TEXT("hand_r"), TransferHands[1], EBoneSpaces::ComponentSpace);
    }
    for (int32 Index = 0; Index < BlendBones.Num(); ++Index)
    {
        FTransform Local;
        Local.Blend(OpenLocal[Index], ClosedLocal[Index], GripWeight);
        Body->SetBoneTransformByName(BlendBones[Index], Local *
            Body->GetBoneTransformByName(BlendParents[Index], EBoneSpaces::ComponentSpace), EBoneSpaces::ComponentSpace);
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

void ARaftSimCC0CrewVisualActor::UpdateGaze(ERaftSimCrewAvatarAction Action)
{
    const FRaftSimCrewIdentity& Identity =
        URaftSimCrewRoster::GetIdentityForVariant(CurrentVariantIndex, bCurrentGuide);
    // Seated people look about; paddlers mostly watch the water; bracing,
    // high-siding, swimming and rescues hold the head on the job.
    float TargetWeight = 0.0f;
    switch (Action)
    {
    case ERaftSimCrewAvatarAction::SeatedIdle:
        TargetWeight = 1.0f;
        break;
    case ERaftSimCrewAvatarAction::ForwardStroke:
    case ERaftSimCrewAvatarAction::BackStroke:
    case ERaftSimCrewAvatarAction::TurnLeft:
    case ERaftSimCrewAvatarAction::TurnRight:
        TargetWeight = 0.35f;
        break;
    default:
        break;
    }
    // The first-person guide's camera sits in the eye socket: never turn it.
    if (bHeadHiddenForFirstPerson || CVarCC0CrewGaze.GetValueOnGameThread() == 0)
    {
        TargetWeight = 0.0f;
    }
    const UWorld* World = GetWorld();
    const double Now = World ? World->GetTimeSeconds() : 0.0;
    if (GazeLastSeconds < 0.0)
    {
        GazeRandom.Initialize(9173 + CurrentVariantIndex * 131 + (bCurrentGuide ? 57 : 0));
        GazeNextChangeSeconds = Now + GazeRandom.FRandRange(0.5f, 2.0f);
    }
    const float Dt = GazeLastSeconds < 0.0
        ? 0.0f
        : FMath::Clamp(static_cast<float>(Now - GazeLastSeconds), 0.0f, 0.25f);
    GazeLastSeconds = Now;
    if (Now >= GazeNextChangeSeconds)
    {
        // A new look, held a while; about a third come back to the line ahead.
        const float Range = FMath::Max(Identity.GazeRangeDeg, 0.0f);
        GazeTargetYawDegrees = GazeRandom.FRand() < 0.35f
            ? GazeRandom.FRandRange(-0.15f, 0.15f) * Range
            : GazeRandom.FRandRange(-Range, Range);
        GazeTargetPitchDegrees = Identity.GazeDownDeg + GazeRandom.FRandRange(-2.5f, 2.5f);
        GazeNextChangeSeconds =
            Now + FMath::Max(Identity.GazeHoldSeconds, 0.3f) * GazeRandom.FRandRange(0.55f, 1.6f);
    }
    // Head turns are quick, holds are still.
    GazeYawDegrees = FMath::FInterpTo(GazeYawDegrees, GazeTargetYawDegrees, Dt, 5.0f);
    GazePitchDegrees = FMath::FInterpTo(GazePitchDegrees, GazeTargetPitchDegrees, Dt, 4.0f);
    GazeWeight = FMath::FInterpTo(GazeWeight, TargetWeight, Dt, 3.0f);
}

void ARaftSimCC0CrewVisualActor::BuildNeckCollar()
{
    bNeckCollarBuilt = true;
    if (!NeckCollar)
    {
        NeckCollar = NewObject<UProceduralMeshComponent>(this, TEXT("NeckCollar"));
        NeckCollar->SetupAttachment(Root);
        NeckCollar->RegisterComponent();
        NeckCollar->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        NeckCollar->SetUsingAbsoluteLocation(true);
        NeckCollar->SetUsingAbsoluteRotation(true);
        NeckCollar->SetUsingAbsoluteScale(true);
        NeckCollar->SetCastShadow(true);
    }
    NeckCollar->ClearAllMeshSections();
    NeckCollarRestPositions.Reset();
    NeckCollarRestNormals.Reset();
    NeckCollarNeckWeights.Reset();
    USkeletalMesh* Mesh = Body ? Cast<USkeletalMesh>(Body->GetSkinnedAsset()) : nullptr;
    FSkeletalMeshRenderData* RenderData = Mesh ? Mesh->GetResourceForRendering() : nullptr;
    const FTransform* RefSpine = ReferenceComponentTransforms.Find(TEXT("spine_03"));
    const FTransform* RefNeck = ReferenceComponentTransforms.Find(TEXT("neck_01"));
    const FTransform* RefHead = ReferenceComponentTransforms.Find(TEXT("head"));
    if (!RenderData || RenderData->LODRenderData.IsEmpty() || !RefSpine || !RefNeck || !RefHead)
    {
        return;
    }
    const FSkeletalMeshLODRenderData& LOD = RenderData->LODRenderData[0];
    const FPositionVertexBuffer& Positions = LOD.StaticVertexBuffers.PositionVertexBuffer;
    if (!Positions.GetVertexData())
    {
        return;
    }
    int32 SkinIndex = INDEX_NONE;
    int32 WetsuitIndex = INDEX_NONE;
    const TArray<FSkeletalMaterial>& Materials = Mesh->GetMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < Materials.Num(); ++MaterialIndex)
    {
        const FString SlotName = Materials[MaterialIndex].MaterialSlotName.ToString();
        if (SkinIndex == INDEX_NONE && SlotName.Contains(TEXT("Skin"), ESearchCase::IgnoreCase))
        {
            SkinIndex = MaterialIndex;
        }
        if (WetsuitIndex == INDEX_NONE && SlotName.Contains(TEXT("Wetsuit"), ESearchCase::IgnoreCase))
        {
            WetsuitIndex = MaterialIndex;
        }
    }
    if (SkinIndex == INDEX_NONE || WetsuitIndex == INDEX_NONE)
    {
        return;
    }

    // Rest-pose neck frame in cm: origin at neck_01, A up the neck shaft.
    const FVector NeckOrigin = RefNeck->GetLocation() * BodyScale;
    const FVector Axis = (RefHead->GetLocation() - RefNeck->GetLocation()).GetSafeNormal();
    FVector X0 = FVector::VectorPlaneProject(FVector::ForwardVector, Axis);
    if (X0.SizeSquared() < 0.01)
    {
        X0 = FVector::VectorPlaneProject(FVector::RightVector, Axis);
    }
    X0.Normalize();
    const FVector Y0 = FVector::CrossProduct(Axis, X0);
    // The rest neck leans toward the face: its lean, flattened onto the
    // collar plane, is the front of the neck.
    const FVector Front = FVector::VectorPlaneProject(FVector(Axis.X, Axis.Y, 0.0f), Axis).GetSafeNormal();
    constexpr int32 Bins = 36;
    constexpr float NearNeckCm = 17.0f;
    auto BinOf = [&](const FVector& Radial)
    {
        const float Theta = FMath::Atan2(
            FVector::DotProduct(Radial, Y0), FVector::DotProduct(Radial, X0));
        return FMath::Clamp(FMath::FloorToInt((Theta + UE_PI) / UE_TWO_PI * Bins), 0, Bins - 1);
    };
    auto KeyOf = [](const FVector& P)
    {
        return FIntVector(
            FMath::RoundToInt(P.X * 50.0), FMath::RoundToInt(P.Y * 50.0), FMath::RoundToInt(P.Z * 50.0));
    };

    // The seam: positions present in both the skin and wetsuit sections.
    struct FSample
    {
        float A;
        float R;
        int32 Bin;
    };
    TSet<FIntVector> WetsuitKeys;
    TArray<FSample> Surface;
    TArray<FSample> Seam;
    for (int32 Pass = 0; Pass < 2; ++Pass)
    {
        const int32 Wanted = Pass == 0 ? WetsuitIndex : SkinIndex;
        for (const FSkelMeshRenderSection& Section : LOD.RenderSections)
        {
            if (Section.MaterialIndex != Wanted)
            {
                continue;
            }
            const uint32 End = Section.BaseVertexIndex + Section.NumVertices;
            for (uint32 Vertex = Section.BaseVertexIndex; Vertex < End; ++Vertex)
            {
                const FVector P = FVector(Positions.VertexPosition(Vertex)) * BodyScale;
                const FVector D = P - NeckOrigin;
                if (D.Size() > NearNeckCm)
                {
                    continue;
                }
                const float A = FVector::DotProduct(D, Axis);
                const FVector Radial = D - Axis * A;
                const float R = Radial.Size();
                if (R < 2.0f)
                {
                    continue;
                }
                const FSample Sample{A, R, BinOf(Radial)};
                Surface.Add(Sample);
                if (Pass == 0)
                {
                    WetsuitKeys.Add(KeyOf(P));
                }
                else if (WetsuitKeys.Contains(KeyOf(P)))
                {
                    Seam.Add(Sample);
                }
            }
        }
    }
    if (Seam.Num() < 16)
    {
        UE_LOG(LogTemp, Display, TEXT("RaftSim CC0 neck collar: no neckline seam on %s (%d points)"),
            *GetNameSafe(Mesh), Seam.Num());
        return;
    }

    // Per bin: the lowest and highest seam point (the saw-tooth's troughs and
    // tips), then fill gaps and smooth round the neck.
    TArray<float> Low, High;
    TArray<bool> Has;
    Low.Init(TNumericLimits<float>::Max(), Bins);
    High.Init(-TNumericLimits<float>::Max(), Bins);
    Has.Init(false, Bins);
    for (const FSample& Sample : Seam)
    {
        Low[Sample.Bin] = FMath::Min(Low[Sample.Bin], Sample.A);
        High[Sample.Bin] = FMath::Max(High[Sample.Bin], Sample.A);
        Has[Sample.Bin] = true;
    }
    for (int32 Bin = 0; Bin < Bins; ++Bin)
    {
        if (Has[Bin])
        {
            continue;
        }
        int32 Prev = Bin, Next = Bin, PrevSteps = 0, NextSteps = 0;
        do { Prev = (Prev + Bins - 1) % Bins; ++PrevSteps; } while (!Has[Prev] && PrevSteps < Bins);
        do { Next = (Next + 1) % Bins; ++NextSteps; } while (!Has[Next] && NextSteps < Bins);
        const float T = float(PrevSteps) / float(PrevSteps + NextSteps);
        Low[Bin] = FMath::Lerp(Low[Prev], Low[Next], T);
        High[Bin] = FMath::Lerp(High[Prev], High[Next], T);
    }
    auto Smooth = [](TArray<float>& Values)
    {
        const int32 Count = Values.Num();
        for (int32 Iteration = 0; Iteration < 2; ++Iteration)
        {
            const TArray<float> Copy = Values;
            for (int32 Bin = 0; Bin < Count; ++Bin)
            {
                Values[Bin] = 0.25f * Copy[(Bin + Count - 1) % Count] + 0.5f * Copy[Bin] +
                    0.25f * Copy[(Bin + 1) % Count];
            }
        }
    };
    if (CVarCC0PoseForensics.GetValueOnGameThread())
    {
        FString Row;
        for (int32 Bin = 0; Bin < Bins; ++Bin)
        {
            const float Theta = -UE_PI + (float(Bin) + 0.5f) * UE_TWO_PI / Bins;
            const FVector Dir = X0 * FMath::Cos(Theta) + Y0 * FMath::Sin(Theta);
            Row += FString::Printf(TEXT(" [%d %s dir=(%.2f,%.2f,%.2f) a=%.1f..%.1f]"), Bin, Has[Bin] ? TEXT("seam") : TEXT("fill"),
                Dir.X, Dir.Y, Dir.Z, Low[Bin], High[Bin]);
        }
        UE_LOG(LogTemp, Display, TEXT("RaftSim CC0 neck seam %s axis=(%.2f,%.2f,%.2f):%s"), *GetNameSafe(Mesh),
            Axis.X, Axis.Y, Axis.Z, *Row);
    }
    Smooth(Low);
    Smooth(High);
    // A band at least 3.5 cm tall standing over the seam. The posed head
    // tips about 20 degrees forward, which drags the front-of-neck skin down
    // through the suit, so the front of the band reaches 3 cm lower.
    auto FrontOf = [&](int32 Bin)
    {
        const float Theta = -UE_PI + (float(Bin) + 0.5f) * UE_TWO_PI / Bins;
        const FVector Dir = X0 * FMath::Cos(Theta) + Y0 * FMath::Sin(Theta);
        return Front.IsNearlyZero() ? 0.0f : FMath::Max(FVector::DotProduct(Dir, Front), 0.0f);
    };
    for (int32 Bin = 0; Bin < Bins; ++Bin)
    {
        Low[Bin] -= 1.2f + 3.0f * FrontOf(Bin);
        High[Bin] += 0.9f;
        if (High[Bin] - Low[Bin] < 3.5f)
        {
            Low[Bin] = High[Bin] - 3.5f;
        }
    }
    // Body surface radius at a height in a bin (and its neighbours).
    auto SurfaceRadius = [&](int32 Bin, float A)
    {
        float Best = 0.0f;
        for (const FSample& Sample : Surface)
        {
            const int32 Delta = FMath::Abs(Sample.Bin - Bin);
            if ((Delta <= 1 || Delta == Bins - 1) && FMath::Abs(Sample.A - A) < 0.9f)
            {
                Best = FMath::Max(Best, Sample.R);
            }
        }
        return Best;
    };
    // Rings, bottom to top: tucked base, outer face, rolled lip (outer, crest)
    // and the inner lip against the neck. Clearance is cm off the body.
    struct FRingSpec
    {
        float Height01;
        float HeightOffset;
        float Clearance;
    };
    const FRingSpec Rings[] = {
        {0.0f, 0.0f, 0.35f},
        {0.5f, 0.0f, 0.55f},
        {1.0f, -0.35f, 0.60f},
        {1.0f, 0.15f, 0.30f},
        {1.0f, -0.05f, -0.15f},
    };
    constexpr int32 RingCount = UE_ARRAY_COUNT(Rings);
    TArray<float> RingRadius[RingCount];
    TArray<float> RingHeight[RingCount];
    for (int32 Ring = 0; Ring < RingCount; ++Ring)
    {
        RingRadius[Ring].SetNum(Bins);
        RingHeight[Ring].SetNum(Bins);
        for (int32 Bin = 0; Bin < Bins; ++Bin)
        {
            const float A = FMath::Lerp(Low[Bin], High[Bin], Rings[Ring].Height01) + Rings[Ring].HeightOffset;
            RingHeight[Ring][Bin] = A;
            // The lip rings hug the neck just below the band's top.
            const float SampleA = Rings[Ring].Height01 >= 1.0f ? High[Bin] - 0.4f : A;
            RingRadius[Ring][Bin] = SurfaceRadius(Bin, SampleA);
        }
        for (int32 Bin = 0; Bin < Bins; ++Bin)
        {
            if (RingRadius[Ring][Bin] <= 0.0f)
            {
                RingRadius[Ring][Bin] = FMath::Max(
                    RingRadius[Ring][(Bin + Bins - 1) % Bins], RingRadius[Ring][(Bin + 1) % Bins]);
            }
        }
        Smooth(RingRadius[Ring]);
        for (int32 Bin = 0; Bin < Bins; ++Bin)
        {
            // The dragged-down skin pokes out of the suit at the front.
            RingRadius[Ring][Bin] += Rings[Ring].Clearance + (Ring <= 1 ? 0.5f * FrontOf(Bin) : 0.0f);
        }
    }
    // The outer face never pinches in below the lip.
    for (int32 Bin = 0; Bin < Bins; ++Bin)
    {
        RingRadius[1][Bin] = FMath::Max(
            RingRadius[1][Bin], FMath::Lerp(RingRadius[0][Bin], RingRadius[2][Bin], 0.5f));
    }

    // Rest mesh in component cm; UpdateNeckCollar poses it every frame.
    // Neck weight per ring: the base rides the suit, the lip the neck.
    const float NeckWeights[RingCount] = {0.0f, 0.4f, 0.9f, 1.0f, 1.0f};
    RaftSimAccessoryMesh::FAccessoryMesh Collar;
    for (int32 Ring = 0; Ring < RingCount; ++Ring)
    {
        for (int32 Bin = 0; Bin <= Bins; ++Bin)
        {
            const int32 B = Bin % Bins;
            const float Theta = -UE_PI + (float(B) + 0.5f) * UE_TWO_PI / Bins;
            const FVector Dir = X0 * FMath::Cos(Theta) + Y0 * FMath::Sin(Theta);
            const FVector P = NeckOrigin + Axis * RingHeight[Ring][B] + Dir * RingRadius[Ring][B];
            const FVector N = Ring <= 1 ? Dir
                : Ring == 2 ? (Dir + Axis).GetSafeNormal()
                : Ring == 3 ? Axis
                : (Axis - Dir).GetSafeNormal();
            Collar.Add(P, N, FVector2D(float(Bin) / Bins * 0.30f, RingHeight[Ring][B] / 140.0f + Ring * 0.004f));
            NeckCollarNeckWeights.Add(NeckWeights[Ring]);
        }
    }
    const int32 Stride = Bins + 1;
    for (int32 Ring = 0; Ring + 1 < RingCount; ++Ring)
    {
        for (int32 Bin = 0; Bin < Bins; ++Bin)
        {
            const int32 A0 = Ring * Stride + Bin;
            const int32 A1 = A0 + 1;
            const int32 B0 = A0 + Stride;
            const int32 B1 = B0 + 1;
            Collar.Triangles.Append({A0, B0, A1, A1, B0, B1});
        }
    }
    NeckCollarRestPositions = Collar.Vertices;
    NeckCollarRestNormals = Collar.Normals;
    Collar.Commit(NeckCollar, 0);
    NeckCollar->SetMaterial(0, Body->GetMaterial(WetsuitIndex));
    UE_LOG(LogTemp, Display, TEXT("RaftSim CC0 neck collar: %s seam=%d band %.1f..%.1f cm"),
        *GetNameSafe(Mesh), Seam.Num(), Low[0], High[0]);
    UpdateNeckCollar();
}

void ARaftSimCC0CrewVisualActor::UpdateNeckCollar()
{
    if (!NeckCollar)
    {
        return;
    }
    const bool bShow = bBodyReady && Body && Body->IsVisible() && NeckCollar->GetNumSections() > 0 &&
        !bHeadHiddenForFirstPerson && CVarCC0NeckCollar.GetValueOnGameThread() != 0;
    NeckCollar->SetVisibility(bShow);
    if (!bShow)
    {
        return;
    }
    const FTransform* RefSpine = ReferenceComponentTransforms.Find(TEXT("spine_03"));
    const FTransform* RefNeck = ReferenceComponentTransforms.Find(TEXT("neck_01"));
    if (!RefSpine || !RefNeck || NeckCollarRestPositions.Num() != NeckCollarNeckWeights.Num())
    {
        return;
    }
    // Rotation and translation only, like the eye anchor: the bones'
    // component transforms carry the importer's unit scale.
    const FTransform Spine = Body->GetBoneTransformByName(TEXT("spine_03"), EBoneSpaces::ComponentSpace);
    const FTransform Neck = Body->GetBoneTransformByName(TEXT("neck_01"), EBoneSpaces::ComponentSpace);
    const FQuat SpineDelta = Spine.GetRotation() * RefSpine->GetRotation().Inverse();
    const FQuat NeckDelta = Neck.GetRotation() * RefNeck->GetRotation().Inverse();
    const FVector SpineRest = RefSpine->GetLocation() * BodyScale;
    const FVector NeckRest = RefNeck->GetLocation() * BodyScale;
    const FVector SpineNow = Spine.GetLocation() * BodyScale;
    const FVector NeckNow = Neck.GetLocation() * BodyScale;
    const int32 Count = NeckCollarRestPositions.Num();
    NeckCollarPosedPositions.SetNum(Count);
    NeckCollarPosedNormals.SetNum(Count);
    for (int32 Index = 0; Index < Count; ++Index)
    {
        const FVector& Rest = NeckCollarRestPositions[Index];
        const float W = NeckCollarNeckWeights[Index];
        const FVector BySpine = SpineNow + SpineDelta.RotateVector(Rest - SpineRest);
        const FVector ByNeck = NeckNow + NeckDelta.RotateVector(Rest - NeckRest);
        NeckCollarPosedPositions[Index] = FMath::Lerp(BySpine, ByNeck, W);
        NeckCollarPosedNormals[Index] = FQuat::Slerp(SpineDelta, NeckDelta, W)
            .RotateVector(NeckCollarRestNormals[Index]);
    }
    NeckCollar->UpdateMeshSection_LinearColor(0, NeckCollarPosedPositions, NeckCollarPosedNormals, {}, {}, {});
    const FTransform& BodyWorld = Body->GetComponentTransform();
    NeckCollar->SetWorldLocationAndRotation(BodyWorld.GetLocation(), BodyWorld.GetRotation());
}

void ARaftSimCC0CrewVisualActor::MeasureVestFit()
{
    // Measured once per body, seated: the vest is a rigid shell, so it fits
    // the resting chest and follows the chest frame from then on.
    bVestFitMeasured = true;
    FittedVestForwardOfSpineCm = 4.5f;
    FittedVestDepthScale = 1.0f;
    FTransform SpineFrame;
    if (!ComputeChestWorldTransform(0.0f, SpineFrame))
    {
        bVestFitMeasured = false;
        return;
    }
    const TArray<FVector> Points = GetPosedBodyVerticesWorldCmForValidation();
    // Front and back of the torso in a central 18 cm strip over the vest's
    // height, in the chest frame (X toward the face, Z up the spine). Arms
    // and the paddle hands sit outside the strip or far in front of it.
    TArray<float> Front;
    TArray<float> Back;
    for (const FVector& Point : Points)
    {
        const FVector Local = SpineFrame.InverseTransformPositionNoScale(Point);
        if (FMath::Abs(Local.Y) > 9.0f || Local.Z < -12.0f || Local.Z > 14.0f)
        {
            continue;
        }
        // Compared against the vest's untapered carriers: the front's inner
        // face leans in by FrontTaperCm above mid-chest and the back's moves
        // in by BackTaperCm over the lumbar curve (RaftSimVestShape).
        if (Local.X > 0.0f && Local.X < 24.0f)
        {
            Front.Add(Local.X + RaftSimVestShape::FrontTaperCm(Local.Z));
        }
        else if (Local.X <= 0.0f && Local.X > -26.0f)
        {
            Back.Add(Local.X - RaftSimVestShape::BackTaperCm(Local.Z));
        }
    }
    if (Front.Num() < 30 || Back.Num() < 30)
    {
        UE_LOG(LogTemp, Display, TEXT("RaftSim CC0 vest fit: too few torso samples (%d front, %d back); default fit"),
            Front.Num(), Back.Num());
        return;
    }
    if (CVarCC0PoseForensics.GetValueOnGameThread())
    {
        // Chest-front and back depth by height band (vest taper review).
        FString Row;
        for (float Z0 = -18.0f; Z0 < 24.0f; Z0 += 6.0f)
        {
            TArray<float> F, B;
            for (const FVector& Point : Points)
            {
                const FVector L = SpineFrame.InverseTransformPositionNoScale(Point);
                if (FMath::Abs(L.Y) <= 12.0f && L.Z >= Z0 && L.Z < Z0 + 6.0f)
                {
                    if (L.X > 0.0f && L.X < 24.0f) F.Add(L.X);
                    else if (L.X <= 0.0f && L.X > -26.0f) B.Add(L.X);
                }
            }
            F.Sort();
            B.Sort();
            Row += FString::Printf(TEXT(" z%.0f:%.1f/%.1f"), Z0 + 3.0f,
                F.Num() ? F[FMath::Min(FMath::FloorToInt(F.Num() * 0.95f), F.Num() - 1)] : 0.0f,
                B.Num() ? B[FMath::FloorToInt(B.Num() * 0.05f)] : 0.0f);
        }
        UE_LOG(LogTemp, Display, TEXT("RaftSim CC0 vest bands %s:%s"),
            *GetNameSafe(Body ? Body->GetSkinnedAsset() : nullptr), *Row);
    }
    Front.Sort();
    Back.Sort();
    // The 95th-percentile chest and 5th-percentile back: the few points past
    // them sit inside the foam cells in front of and behind the carriers.
    // (Fitted over z -12..14; the taper fits the upper chest and lower back.)
    const float BodyFrontCm = Front[FMath::Clamp(FMath::FloorToInt(Front.Num() * 0.95f), 0, Front.Num() - 1)];
    const float BodyBackCm = Back[FMath::Clamp(FMath::FloorToInt(Back.Num() * 0.05f), 0, Back.Num() - 1)];
    // Carrier inner faces of SM_RaftSim_WhitewaterRescuePfd (vest local cm,
    // build_production_whitewater_pfd.py): front 12.15, rear -11.4.
    constexpr float VestInnerFrontCm = 12.15f;
    constexpr float VestInnerBackCm = -11.4f;
    constexpr float ClearanceCm = 0.5f;
    const float FrontTargetCm = BodyFrontCm + ClearanceCm;
    const float BackTargetCm = BodyBackCm - ClearanceCm;
    FittedVestDepthScale = FMath::Clamp(
        (FrontTargetCm - BackTargetCm) / (VestInnerFrontCm - VestInnerBackCm), 0.80f, 1.15f);
    FittedVestForwardOfSpineCm = FMath::Clamp(
        0.5f * (FrontTargetCm + BackTargetCm) -
            0.5f * (VestInnerFrontCm + VestInnerBackCm) * FittedVestDepthScale,
        0.0f, 9.0f);
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim CC0 vest fit %s: chest %.1f / back %.1f cm from the spine frame -> depth x%.3f, centre %.2f cm ahead"),
        *GetNameSafe(Body ? Body->GetSkinnedAsset() : nullptr), BodyFrontCm, BodyBackCm, FittedVestDepthScale,
        FittedVestForwardOfSpineCm);
}
