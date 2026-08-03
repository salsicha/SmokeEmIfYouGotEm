#include "RaftSimMetaHumanCrewVisualActor.h"

#include "Components/ChildActorComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "GroomComponent.h"
#include "GroomAsset.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "Components/StaticMeshComponent.h"

namespace
{
const TCHAR* BodyMeshPath = TEXT(
    "/MetaHumanCharacter/Body/IdentityTemplate/SKM_Body.SKM_Body");
const TCHAR* FaceMeshPath = TEXT(
    "/MetaHumanCharacter/Face/SKM_Face.SKM_Face");
const TCHAR* SkinMaterialPath = TEXT(
    "/Game/RaftSim/Materials/M_RaftSim_MetaHuman_Skin.M_RaftSim_MetaHuman_Skin");
const TCHAR* WetsuitMaterialPath = TEXT(
    "/Game/RaftSim/Materials/M_RaftSim_Wetsuit.M_RaftSim_Wetsuit");
const TCHAR* TeethMaterialPath = TEXT(
    "/MetaHumanCharacter/Materials/MI_Teeth_MHC_UI.MI_Teeth_MHC_UI");
const TCHAR* EyeMaterialPath = TEXT(
    "/MetaHumanCharacter/Lookdev_UHM/Eye/Materials/"
    "MI_eye_eyeball_unified_MH_preset_left_right."
    "MI_eye_eyeball_unified_MH_preset_left_right");
const TCHAR* ProductionBuildRoot = TEXT(
    "/Game/RaftSim/Characters/Production/MetaHumans");
constexpr float PaddleThumbPadCenterRadiusCm = 2.20f;
// MetaHuman identity templates face +Y; RaftSim avatars, strokes and safety
// gear face +X. Rotate the reference bone bases without rotating solved joint
// locations, preserving the host's centimetre-space pose contract.
const FQuat MeshToAvatarRotation = FRotator(0.0f, -90.0f, 0.0f).Quaternion();

const FName MetaHumanDrivenBones[] = {
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

const TCHAR* GripDigits[] = {
    TEXT("thumb"), TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")};

struct FAnatomicalGripDigitProfile
{
    float EntrySweepDegrees;
    float MiddleSweepDegrees;
    float TipSweepDegrees;
    float ProximalRadiusCm;
    float PadCenterRadiusCm;
    float TipCenterRadiusCm;
    float FanDegrees;
};

bool ResolveAnatomicalGripDigitProfile(
    const TCHAR* Digit,
    FAnatomicalGripDigitProfile& OutProfile)
{
    // The previous identical 50/68/52-degree arcs made all four fingers read
    // as one circular ring. These asymmetric C-grips preserve the source
    // skeleton's authored finger lengths and fan each digit slightly. The
    // thumb keeps its authored curl: forcing it onto the same radial solver
    // produced an artificial oval loop around the lower shaft.
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

FLinearColor ResolveSkinTone(int32 VariantIndex, bool bGuide)
{
    if (bGuide)
    {
        return FLinearColor(0.54f, 0.31f, 0.20f, 1.0f);
    }
    static const FLinearColor Tones[] = {
        FLinearColor(0.24f, 0.105f, 0.055f, 1.0f),
        FLinearColor(0.68f, 0.43f, 0.29f, 1.0f),
        FLinearColor(0.80f, 0.57f, 0.41f, 1.0f),
        FLinearColor(0.39f, 0.19f, 0.105f, 1.0f)};
    return Tones[FMath::Clamp(VariantIndex, 0, 3)];
}
}

ARaftSimMetaHumanCrewVisualActor::ARaftSimMetaHumanCrewVisualActor()
{
    PrimaryActorTick.bCanEverTick = false;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("MetaHumanRoot"));
    SetRootComponent(Root);

    Body = CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("MetaHumanBody"));
    Body->SetupAttachment(Root);
    Body->SetRelativeScale3D(FVector(BodyScale));
    Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Body->SetCastShadow(true);

    Face = CreateDefaultSubobject<UPoseableMeshComponent>(TEXT("MetaHumanFace"));
    Face->SetupAttachment(Root);
    Face->SetRelativeScale3D(FVector(BodyScale));
    Face->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Face->SetCastShadow(true);

    AssembledCharacter = CreateDefaultSubobject<UChildActorComponent>(
        TEXT("AssembledMetaHuman"));
    AssembledCharacter->SetupAttachment(Root);
}

void ARaftSimMetaHumanCrewVisualActor::SetBodyOnlyShadowMode(bool bEnabled)
{
    // Body and Face are hidden deterministic pose leaders while an assembled
    // character is active. They must not become redundant hidden casters.
    Body->SetCastShadow(!bUsingAssembledCharacter && !bEnabled);
    Face->SetCastShadow(!bUsingAssembledCharacter && !bEnabled);

    if (AssembledBody)
    {
        // Keep one articulated full-body caster so each paddler remains
        // grounded on the raft and shoreline in every gameplay pose.
        AssembledBody->SetCastShadow(true);
    }
    if (AssembledFace)
    {
        AssembledFace->SetCastShadow(!bEnabled);
    }

    if (AActor* CharacterActor = GetAssembledCharacterActor())
    {
        TInlineComponentArray<USkeletalMeshComponent*> SkeletalComponents(
            CharacterActor);
        for (USkeletalMeshComponent* Component : SkeletalComponents)
        {
            if (Component && Component != AssembledBody &&
                Component != AssembledFace)
            {
                // Wardrobe and grooms are already suppressed behind rafting
                // PPE, so they should never emit invisible VSM silhouettes.
                Component->SetCastShadow(false);
            }
        }
    }
    if (HairMeshFallback)
    {
        HairMeshFallback->SetCastShadow(false);
    }
}

FString ARaftSimMetaHumanCrewVisualActor::GetAssembledBlueprintClassPath(
    bool bGuide,
    int32 VariantIndex)
{
    const FString CharacterName = bGuide
        ? TEXT("MHC_RaftSim_Guide")
        : FString::Printf(
              TEXT("MHC_RaftSim_Crew_%02d"),
              FMath::Clamp(FMath::Abs(VariantIndex), 0, 3) + 1);
    return FString::Printf(
        TEXT("%s/%s/BP_%s.BP_%s_C"),
        ProductionBuildRoot,
        *CharacterName,
        *CharacterName,
        *CharacterName);
}

bool ARaftSimMetaHumanCrewVisualActor::AreAllProductionCharactersAvailable()
{
    for (int32 RosterIndex = 0; RosterIndex < 5; ++RosterIndex)
    {
        const FString ClassPath = GetAssembledBlueprintClassPath(
            RosterIndex == 0,
            FMath::Max(RosterIndex - 1, 0));
        const FString PackageName = FPackageName::ObjectPathToPackageName(ClassPath);
        if (PackageName.IsEmpty() || !FPackageName::DoesPackageExist(PackageName))
        {
            return false;
        }
    }
    return true;
}

AActor* ARaftSimMetaHumanCrewVisualActor::GetAssembledCharacterActor() const
{
    return AssembledCharacter ? AssembledCharacter->GetChildActor() : nullptr;
}

int32 ARaftSimMetaHumanCrewVisualActor::GetAssembledHairForcedLOD() const
{
    AActor* CharacterActor = GetAssembledCharacterActor();
    if (!CharacterActor)
    {
        return INDEX_NONE;
    }
    TArray<UGroomComponent*> GroomComponents;
    CharacterActor->GetComponents<UGroomComponent>(GroomComponents);
    for (const UGroomComponent* Component : GroomComponents)
    {
        if (Component && Component->GroomAsset &&
            Component->GetFName().IsEqual(FName(TEXT("Hair")), ENameCase::IgnoreCase))
        {
            return Component->GetForcedLOD();
        }
    }
    return INDEX_NONE;
}

bool ARaftSimMetaHumanCrewVisualActor::
    IsAssembledWardrobeSuppressedForSafetyGear() const
{
    return bAssembledWardrobeSuppressedForSafetyGear;
}

bool ARaftSimMetaHumanCrewVisualActor::IsAssembledBodyUsingWetsuit() const
{
    return bAssembledBodyUsesWetsuit;
}

bool ARaftSimMetaHumanCrewVisualActor::
    IsHairMeshFallbackSuppressedForHelmet() const
{
    return HairMeshFallback && !HairMeshFallback->IsVisible();
}

bool ARaftSimMetaHumanCrewVisualActor::
    IsAssembledHairGroomSuppressedForHelmet() const
{
    AActor* CharacterActor = GetAssembledCharacterActor();
    if (!CharacterActor)
    {
        return false;
    }
    TArray<UGroomComponent*> GroomComponents;
    CharacterActor->GetComponents<UGroomComponent>(GroomComponents);
    bool bFoundHair = false;
    for (const UGroomComponent* Component : GroomComponents)
    {
        if (Component && Component->GroomAsset &&
            Component->GetFName().IsEqual(FName(TEXT("Hair")), ENameCase::IgnoreCase))
        {
            bFoundHair = true;
            if (Component->IsVisible())
            {
                return false;
            }
        }
    }
    return bFoundHair;
}

bool ARaftSimMetaHumanCrewVisualActor::
    AreAssembledGroomsSuppressedForGameplay() const
{
    AActor* CharacterActor = GetAssembledCharacterActor();
    if (!CharacterActor)
    {
        return false;
    }
    TArray<UGroomComponent*> GroomComponents;
    CharacterActor->GetComponents<UGroomComponent>(GroomComponents);
    bool bFoundReviewedGroom = false;
    for (const UGroomComponent* Component : GroomComponents)
    {
        if (Component && Component->GroomAsset)
        {
            bFoundReviewedGroom = true;
            if (Component->IsVisible())
            {
                return false;
            }
        }
    }
    return bFoundReviewedGroom;
}

float ARaftSimMetaHumanCrewVisualActor::GetHairMeshFallbackHeadErrorCm() const
{
    if (!HairMeshFallback || !HairMeshFallback->GetStaticMesh() || !Body ||
        Body->GetBoneIndex(TEXT("head")) == INDEX_NONE)
    {
        return TNumericLimits<float>::Max();
    }
    const FVector RenderedBoundsCenter =
        HairMeshFallback->GetComponentTransform().TransformPosition(
            HairMeshFallback->GetStaticMesh()->GetBounds().Origin);
    return FVector::Distance(
        RenderedBoundsCenter,
        Body->GetBoneTransformByName(TEXT("head"), EBoneSpaces::WorldSpace)
            .GetLocation());
}

FVector ARaftSimMetaHumanCrewVisualActor::GetSolvedHeadWorldLocation() const
{
    if (!Body || Body->GetBoneIndex(TEXT("head")) == INDEX_NONE)
    {
        return GetActorLocation();
    }
    return Body->GetBoneTransformByName(
        TEXT("head"), EBoneSpaces::WorldSpace).GetLocation();
}

FVector ARaftSimMetaHumanCrewVisualActor::GetSolvedFaceForwardWorldVector() const
{
    const USceneComponent* RenderedFace = bUsingAssembledCharacter && AssembledFace
        ? static_cast<const USceneComponent*>(AssembledFace.Get())
        : static_cast<const USceneComponent*>(Face.Get());
    if (!RenderedFace)
    {
        return GetActorForwardVector();
    }
    // MetaHuman face assets author their gaze along local +Y. The assembled
    // face component carries the solved head delta and the -90-degree
    // mesh-to-avatar correction, so this vector is the actual rendered gaze.
    return RenderedFace->GetComponentQuat()
        .RotateVector(FVector::YAxisVector)
        .GetSafeNormal();
}

FVector ARaftSimMetaHumanCrewVisualActor::GetSolvedFaceUpWorldVector() const
{
    const USceneComponent* RenderedFace = bUsingAssembledCharacter && AssembledFace
        ? static_cast<const USceneComponent*>(AssembledFace.Get())
        : static_cast<const USceneComponent*>(Face.Get());
    if (!RenderedFace)
    {
        return GetActorUpVector();
    }
    return RenderedFace->GetComponentQuat()
        .RotateVector(FVector::UpVector)
        .GetSafeNormal();
}

float ARaftSimMetaHumanCrewVisualActor::GetRecommendedWhitewaterHelmetScale() const
{
    if (!AssembledFace)
    {
        return 0.96f;
    }
    FBoxSphereBounds Bounds;
    AssembledFace->GetPreSkinnedLocalBounds(Bounds);
    // The guide identity is the reviewed 0.96 reference fit. Scale the shell
    // by the geometric mean of each identity's lateral and fore/aft face
    // bounds, then keep the result inside the authored helmet size run. This
    // prevents the narrow identities from inheriting the broadest shell.
    constexpr float ReferenceFaceHalfWidthCm = 18.61654f;
    constexpr float ReferenceFaceHalfDepthCm = 12.91950f;
    const float WidthRatio = Bounds.BoxExtent.X / ReferenceFaceHalfWidthCm;
    const float DepthRatio = Bounds.BoxExtent.Y / ReferenceFaceHalfDepthCm;
    const float IdentityScale = FMath::Sqrt(
        FMath::Max(WidthRatio * DepthRatio, 0.01f));
    return FMath::Clamp(0.96f * IdentityScale, 0.90f, 1.02f);
}

FVector ARaftSimMetaHumanCrewVisualActor::
    GetAssembledFacePreSkinnedBoundsOrigin() const
{
    if (!AssembledFace)
    {
        return FVector::ZeroVector;
    }
    FBoxSphereBounds Bounds;
    AssembledFace->GetPreSkinnedLocalBounds(Bounds);
    return Bounds.Origin;
}

FVector ARaftSimMetaHumanCrewVisualActor::
    GetAssembledFacePreSkinnedBoundsExtent() const
{
    if (!AssembledFace)
    {
        return FVector::ZeroVector;
    }
    FBoxSphereBounds Bounds;
    AssembledFace->GetPreSkinnedLocalBounds(Bounds);
    return Bounds.BoxExtent;
}

void ARaftSimMetaHumanCrewVisualActor::ResetAssembledCharacter()
{
    bBodyReady = false;
    bUsingAssembledCharacter = false;
    bAssembledPresentationReady = false;
    bAssembledWardrobeSuppressedForSafetyGear = false;
    bAssembledBodyUsesWetsuit = false;
    bLocalizedPaddleGlovesReady = false;
    bAssembledFaceUsesCroppedSkin = false;
    AssembledFaceCropHeightCm = 0.0f;
    AssembledBody = nullptr;
    AssembledFace = nullptr;
    ReferenceAssembledFaceHeadComponentTransform = FTransform::Identity;
    AssembledFaceComponentScale = FVector::OneVector;
    CroppedFaceSkins.Reset();
    WetsuitPresentationMaterial = nullptr;
    if (Face)
    {
        Face->SetVisibility(false, true);
    }
    if (HairMeshFallback)
    {
        HairMeshFallback->DestroyComponent();
        HairMeshFallback = nullptr;
    }
    if (AssembledCharacter)
    {
        AssembledCharacter->SetChildActorClass(nullptr);
        AssembledCharacter->SetVisibility(false, true);
    }
}

bool ARaftSimMetaHumanCrewVisualActor::TryActivateAssembledCharacter()
{
    if (!AssembledCharacter || !AreAllProductionCharactersAvailable())
    {
        ResetAssembledCharacter();
        return false;
    }

    const FString ClassPath = GetAssembledBlueprintClassPath(
        bCurrentGuide,
        CurrentVariantIndex);
    UClass* CharacterClass = FSoftClassPath(ClassPath).TryLoadClass<AActor>();
    if (!CharacterClass)
    {
        ResetAssembledCharacter();
        return false;
    }
    if (bUsingAssembledCharacter &&
        AssembledCharacter->GetChildActorClass() == CharacterClass &&
        AssembledCharacter->GetChildActor() && AssembledBody && AssembledFace &&
        bAssembledPresentationReady)
    {
        bBodyReady = true;
        return true;
    }
    if (AssembledCharacter->GetChildActorClass() != CharacterClass)
    {
        AssembledCharacter->SetChildActorClass(CharacterClass);
    }
    AActor* CharacterActor = AssembledCharacter->GetChildActor();
    if (!CharacterActor)
    {
        ResetAssembledCharacter();
        return false;
    }

    TArray<USkeletalMeshComponent*> SkeletalComponents;
    CharacterActor->GetComponents<USkeletalMeshComponent>(SkeletalComponents);
    USkeletalMeshComponent* BodyCandidate = nullptr;
    USkeletalMeshComponent* FaceCandidate = nullptr;
    for (USkeletalMeshComponent* Component : SkeletalComponents)
    {
        if (!Component || !Component->GetSkeletalMeshAsset())
        {
            continue;
        }
        if (Component->GetFName().IsEqual(FName(TEXT("Face")), ENameCase::IgnoreCase))
        {
            FaceCandidate = Component;
        }
        else if (Component->GetFName().IsEqual(FName(TEXT("Body")), ENameCase::IgnoreCase))
        {
            BodyCandidate = Component;
        }
    }
    for (USkeletalMeshComponent* Component : SkeletalComponents)
    {
        if ((!BodyCandidate || !FaceCandidate) && Component &&
            Component->GetSkeletalMeshAsset())
        {
            const FString Identity = FString::Printf(
                TEXT("%s %s"),
                *Component->GetName(),
                *Component->GetSkeletalMeshAsset()->GetPathName());
            if (!FaceCandidate && Identity.Contains(TEXT("Face"), ESearchCase::IgnoreCase))
            {
                FaceCandidate = Component;
            }
            else if (!BodyCandidate &&
                     Identity.Contains(TEXT("Body"), ESearchCase::IgnoreCase))
            {
                BodyCandidate = Component;
            }
        }
    }
    if (!BodyCandidate || !FaceCandidate)
    {
        ResetAssembledCharacter();
        return false;
    }

    bool bHasWardrobe = false;
    for (USkeletalMeshComponent* Component : SkeletalComponents)
    {
        if (Component && Component != BodyCandidate && Component != FaceCandidate &&
            Component->GetSkeletalMeshAsset())
        {
            bHasWardrobe = true;
            break;
        }
    }
    bool bHasHair = false;
    bool bHasEyebrows = false;
    bool bHasEyelashes = false;
    TArray<UGroomComponent*> GroomComponents;
    UStaticMesh* ReviewedHairMesh = nullptr;
    CharacterActor->GetComponents<UGroomComponent>(GroomComponents);
    for (UGroomComponent* Component : GroomComponents)
    {
        if (!Component || !Component->GroomAsset)
        {
            continue;
        }
        const FString ComponentName = Component->GetName();
        if (ComponentName.Equals(TEXT("Hair"), ESearchCase::IgnoreCase))
        {
            // Every reviewed production style includes generated card and
            // conventional mesh fallbacks. Metal SceneCapture does not render
            // the generated card path reliably, so use the audited mesh LOD.
            Component->SetUseCards(true);
            Component->SetForcedLOD(5);
            for (const FHairGroupsMeshesSourceDescription& Source :
                 Component->GroomAsset->GetHairGroupsMeshes())
            {
                if (Source.GroupIndex == 0 && Source.LODIndex == 5 &&
                    Source.ImportedMesh)
                {
                    ReviewedHairMesh = Source.ImportedMesh;
                    break;
                }
            }
            // Groom mesh deformation is unreliable in Metal SceneCapture and
            // can leave the LOD-5 helmet at component origin. Render the same
            // reviewed asset as a deterministic head-bone attachment instead.
            Component->SetVisibility(false, true);
        }
        bHasHair |= ComponentName.Equals(TEXT("Hair"), ESearchCase::IgnoreCase);
        bHasEyebrows |= ComponentName.Equals(TEXT("Eyebrows"), ESearchCase::IgnoreCase);
        bHasEyelashes |= ComponentName.Equals(TEXT("Eyelashes"), ESearchCase::IgnoreCase);
    }
    // UE 5.8 optimized Medium builds bake the selected eyelashes into the
    // face representation and leave the conventional Eyelashes groom
    // component empty. Accept only the explicit face eyelash material as the
    // optimized alternative; an empty component by itself is not sufficient.
    if (!bHasEyelashes)
    {
        for (int32 MaterialIndex = 0;
             MaterialIndex < FaceCandidate->GetNumMaterials();
             ++MaterialIndex)
        {
            const UMaterialInterface* Material =
                FaceCandidate->GetMaterial(MaterialIndex);
            if (Material &&
                Material->GetPathName().Contains(
                    TEXT("Eyelash"), ESearchCase::IgnoreCase))
            {
                bHasEyelashes = true;
                break;
            }
        }
    }
    bAssembledPresentationReady = bHasWardrobe && bHasHair && ReviewedHairMesh &&
        bHasEyebrows && bHasEyelashes;
    if (!bAssembledPresentationReady)
    {
        ResetAssembledCharacter();
        return false;
    }

    USkeletalMesh* BodyMesh = BodyCandidate->GetSkeletalMeshAsset();
    if (Body->GetSkinnedAsset() != BodyMesh)
    {
        Body->SetSkinnedAssetAndUpdate(BodyMesh);
        Body->AllocateTransformData();
        ReferenceBodyTransforms.Reset();
    }
    if (Body->GetBoneSpaceTransforms().Num() != BodyMesh->GetRefSkeleton().GetNum())
    {
        Body->AllocateTransformData();
    }
    if (Body->GetBoneSpaceTransforms().Num() != BodyMesh->GetRefSkeleton().GetNum())
    {
        ResetAssembledCharacter();
        return false;
    }

    AssembledBody = BodyCandidate;
    AssembledFace = FaceCandidate;
    AssembledBody->SetLeaderPoseComponent(Body, true, false);
    // Keep every facial joint in the generated mesh's untouched neutral pose.
    // The face component itself is moved so its reference head pivot matches
    // the driven head; this avoids every partial-skeleton follower-map failure.
    AssembledFace->SetLeaderPoseComponent(nullptr, true, false);
    AssembledFace->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    AssembledFace->SetAnimInstanceClass(nullptr);
    AssembledFace->SetComponentTickEnabled(false);
    AssembledFace->RefreshBoneTransforms();
    ReferenceAssembledFaceHeadComponentTransform =
        AssembledFace->GetBoneTransform(
            TEXT("head"), ERelativeTransformSpace::RTS_Component);
    AssembledFaceComponentScale = AssembledFace->GetComponentScale();
    AssembledFace->SetBoundsScale(8.0f);
    AssembledFace->VisibilityBasedAnimTickOption =
        EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    AssembledBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    AssembledFace->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    UMaterialInterface* ProductionWetsuit =
        LoadObject<UMaterialInterface>(nullptr, WetsuitMaterialPath);
    if (!ProductionWetsuit || AssembledBody->GetNumMaterials() < 1)
    {
        ResetAssembledCharacter();
        return false;
    }
    WetsuitPresentationMaterial = UMaterialInstanceDynamic::Create(
        ProductionWetsuit,
        this,
        TEXT("RaftSimWetsuitWithPaddleGloves"));
    if (!WetsuitPresentationMaterial)
    {
        ResetAssembledCharacter();
        return false;
    }
    for (int32 MaterialIndex = 0;
         MaterialIndex < AssembledBody->GetNumMaterials();
         ++MaterialIndex)
    {
        AssembledBody->SetMaterial(MaterialIndex, WetsuitPresentationMaterial);
    }
    bAssembledBodyUsesWetsuit =
        AssembledBody->GetMaterial(0) == WetsuitPresentationMaterial &&
        WetsuitPresentationMaterial->Parent == ProductionWetsuit;
    int32 CroppedSkinSlotCount = 0;
    const float CropHeightCm =
        ReferenceAssembledFaceHeadComponentTransform.GetLocation().Z - 10.0f;
    AssembledFaceCropHeightCm = CropHeightCm;
    for (int32 MaterialIndex = 0;
         MaterialIndex < AssembledFace->GetNumMaterials();
         ++MaterialIndex)
    {
        UMaterialInterface* SourceMaterial = AssembledFace->GetMaterial(MaterialIndex);
        if (!SourceMaterial ||
            !SourceMaterial->GetPathName().Contains(
                TEXT("Face_Skin"), ESearchCase::IgnoreCase))
        {
            continue;
        }
        const FString CharacterName = bCurrentGuide
            ? TEXT("MHC_RaftSim_Guide")
            : FString::Printf(
                  TEXT("MHC_RaftSim_Crew_%02d"),
                  FMath::Clamp(FMath::Abs(CurrentVariantIndex), 0, 3) + 1);
        const bool bLowestLods = SourceMaterial->GetPathName().Contains(
            TEXT("LOD5to7"), ESearchCase::IgnoreCase);
        const FString CroppedInstanceName = FString::Printf(
            TEXT("MI_%s_FaceCropped_%s"),
            *CharacterName,
            bLowestLods ? TEXT("LOD5to7") : TEXT("LOD3"));
        const FString CroppedInstancePath = FString::Printf(
            TEXT("/Game/RaftSim/Materials/MetaHumanFaceCropV2/%s/%s.%s"),
            *CharacterName,
            *CroppedInstanceName,
            *CroppedInstanceName);
        UMaterialInterface* CroppedFaceInstance =
            LoadObject<UMaterialInterface>(nullptr, *CroppedInstancePath);
        if (!CroppedFaceInstance)
        {
            ResetAssembledCharacter();
            return false;
        }
        UMaterialInstanceDynamic* CroppedSkin = UMaterialInstanceDynamic::Create(
            CroppedFaceInstance,
            this,
            *FString::Printf(TEXT("RaftSimCroppedFaceSkin_%d"), MaterialIndex));
        if (!CroppedSkin)
        {
            ResetAssembledCharacter();
            return false;
        }
        CroppedSkin->SetScalarParameterValue(
            TEXT("RaftSimFaceCropHeightCm"), CropHeightCm);
        AssembledFace->SetMaterial(MaterialIndex, CroppedSkin);
        CroppedFaceSkins.Add(CroppedSkin);
        ++CroppedSkinSlotCount;
    }
    bAssembledFaceUsesCroppedSkin = CroppedSkinSlotCount >= 2;
    if (!bAssembledFaceUsesCroppedSkin)
    {
        ResetAssembledCharacter();
        return false;
    }
    HairMeshFallback = NewObject<UStaticMeshComponent>(
        this, TEXT("AssembledHairMeshFallback"));
    if (!HairMeshFallback)
    {
        ResetAssembledCharacter();
        return false;
    }
    HairMeshFallback->SetStaticMesh(ReviewedHairMesh);
    HairMeshFallback->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    HairMeshFallback->SetCastShadow(false);
    HairMeshFallback->RegisterComponent();
    HairMeshFallback->AttachToComponent(
        Root, FAttachmentTransformRules::KeepRelativeTransform);
    HairMeshFallback->SetRelativeTransform(FTransform::Identity);
    AssembledCharacter->SetVisibility(true, true);
    // SetVisibility on the child actor restores all authored descendants, so
    // reapply the deterministic gameplay contract after the hierarchy is
    // visible. The optimized face materials already carry the reviewed brow
    // and lash representations; live groom cards deform away from the driven
    // head under Metal SceneCapture and create false strips beside the ears.
    for (UGroomComponent* Component : GroomComponents)
    {
        if (Component && Component->GroomAsset)
        {
            Component->SetVisibility(false, true);
            Component->SetCastShadow(false);
        }
    }
    // The generated garments are complete authoring evidence, but their
    // skeleton contract is not compatible with the deterministic gameplay
    // pose leader: forcing them to follow inflates the collar and shorts over
    // the face. Suppress them and let the host render its pose-matched wetsuit,
    // splash jacket and certified-silhouette PFD instead.
    bAssembledWardrobeSuppressedForSafetyGear = true;
    for (USkeletalMeshComponent* Component : SkeletalComponents)
    {
        if (Component && Component != AssembledBody && Component != AssembledFace &&
            Component->GetSkeletalMeshAsset())
        {
            Component->SetVisibility(false, true);
            Component->SetCastShadow(false);
            bAssembledWardrobeSuppressedForSafetyGear &= !Component->IsVisible();
        }
    }
    // Hair remains provenance-checked and head-aligned, but a guide/guest must
    // wear a helmet on whitewater. Rendering both shells creates clipping and
    // a false oversized silhouette, so the gameplay helmet owns the pixels.
    HairMeshFallback->SetVisibility(false, true);
    // The assembled anatomical body is the single wetsuit layer; the generated
    // shirt/shorts remain hidden and the poseable component is only its leader.
    AssembledBody->SetVisibility(true, false);
    AssembledBody->SetCastShadow(true);
    // Do not recursively re-enable the Hair groom attached beneath Face.
    AssembledFace->SetVisibility(true, false);
    Body->SetVisibility(false, true);
    Face->SetVisibility(false, true);
    if (ReferenceBodyTransforms.IsEmpty())
    {
        CacheReferencePose();
    }
    bUsingAssembledCharacter = ReferenceBodyTransforms.Num() >= 19 &&
        AssembledFace->GetBoneIndex(TEXT("head")) != INDEX_NONE &&
        bAssembledBodyUsesWetsuit &&
        bAssembledFaceUsesCroppedSkin &&
        bAssembledPresentationReady;
    bBodyReady = bUsingAssembledCharacter;
    if (!bUsingAssembledCharacter)
    {
        ResetAssembledCharacter();
    }
    return bUsingAssembledCharacter;
}

bool ARaftSimMetaHumanCrewVisualActor::EnsureAssetsLoaded()
{
    if (!Body || !Face)
    {
        bBodyReady = false;
        return false;
    }

    const bool bProductionRosterDeclared = AreAllProductionCharactersAvailable();
    if (TryActivateAssembledCharacter())
    {
        return true;
    }
    // A complete set of package names is a release-art declaration. If any
    // assembled entry is corrupt or incomplete, fail back through the host to
    // the complete CC0 roster; never disguise it with this blank diagnostic.
    if (bProductionRosterDeclared)
    {
        bBodyReady = false;
        Body->SetVisibility(false, true);
        Face->SetVisibility(false, true);
        return false;
    }

    USkeletalMesh* BodyMesh = LoadObject<USkeletalMesh>(nullptr, BodyMeshPath);
    USkeletalMesh* FaceMesh = LoadObject<USkeletalMesh>(nullptr, FaceMeshPath);
    UMaterialInterface* SkinMaterial = LoadObject<UMaterialInterface>(nullptr, SkinMaterialPath);
    UMaterialInterface* WetsuitMaterial =
        LoadObject<UMaterialInterface>(nullptr, WetsuitMaterialPath);
    if (!BodyMesh || !FaceMesh || !SkinMaterial || !WetsuitMaterial)
    {
        bBodyReady = false;
        Body->SetVisibility(false, true);
        Face->SetVisibility(false, true);
        return false;
    }

    bool bMeshChanged = false;
    if (Body->GetSkinnedAsset() != BodyMesh)
    {
        Body->SetSkinnedAssetAndUpdate(BodyMesh);
        bMeshChanged = true;
    }
    if (Face->GetSkinnedAsset() != FaceMesh)
    {
        Face->SetSkinnedAssetAndUpdate(FaceMesh);
        bMeshChanged = true;
    }

    // SetSkinnedAssetAndUpdate can leave a newly loaded poseable mesh without
    // its local-pose buffer until the first component refresh. Bone writes made
    // during that gap are silently ignored by UPoseableMeshComponent. Allocate
    // synchronously so the initial seated pose is valid even when this adapter
    // is driven directly (capture tools and deterministic tests do not tick a
    // production host before inspecting it).
    const int32 BodyBoneCount = BodyMesh->GetRefSkeleton().GetNum();
    const int32 FaceBoneCount = FaceMesh->GetRefSkeleton().GetNum();
    if (Body->GetBoneSpaceTransforms().Num() != BodyBoneCount)
    {
        Body->AllocateTransformData();
    }
    if (Face->GetBoneSpaceTransforms().Num() != FaceBoneCount)
    {
        Face->AllocateTransformData();
    }
    const bool bPoseBuffersReady =
        Body->GetBoneSpaceTransforms().Num() == BodyBoneCount &&
        Face->GetBoneSpaceTransforms().Num() == FaceBoneCount;
    if (!bPoseBuffersReady)
    {
        bBodyReady = false;
        Body->SetVisibility(false, true);
        Face->SetVisibility(false, true);
        return false;
    }
    if (!WetsuitPresentationMaterial ||
        WetsuitPresentationMaterial->Parent != WetsuitMaterial)
    {
        WetsuitPresentationMaterial = UMaterialInstanceDynamic::Create(
            WetsuitMaterial,
            this,
            TEXT("RaftSimDiagnosticWetsuitWithPaddleGloves"));
    }
    Body->SetMaterial(
        0,
        WetsuitPresentationMaterial
            ? static_cast<UMaterialInterface*>(WetsuitPresentationMaterial.Get())
            : WetsuitMaterial);

    if (!FaceSkin || FaceSkin->Parent != SkinMaterial)
    {
        FaceSkin = UMaterialInstanceDynamic::Create(SkinMaterial, this);
    }
    if (!FaceSkin)
    {
        bBodyReady = false;
        Body->SetVisibility(false, true);
        Face->SetVisibility(false, true);
        return false;
    }
    const FLinearColor SkinTone = ResolveSkinTone(CurrentVariantIndex, bCurrentGuide);
    FaceSkin->SetVectorParameterValue(TEXT("SkinTone"), SkinTone);

    UMaterialInterface* TeethMaterial =
        LoadObject<UMaterialInterface>(nullptr, TeethMaterialPath);
    UMaterialInterface* EyeMaterial =
        LoadObject<UMaterialInterface>(nullptr, EyeMaterialPath);
    const TArray<FSkeletalMaterial>& FaceSlots = FaceMesh->GetMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < FaceSlots.Num(); ++MaterialIndex)
    {
        const FString SlotName = FaceSlots[MaterialIndex].MaterialSlotName.ToString();
        if (SlotName.StartsWith(TEXT("head"), ESearchCase::IgnoreCase))
        {
            Face->SetMaterial(MaterialIndex, FaceSkin);
        }
        else if (TeethMaterial && SlotName.Contains(TEXT("teeth"), ESearchCase::IgnoreCase))
        {
            Face->SetMaterial(MaterialIndex, TeethMaterial);
        }
        else if (EyeMaterial &&
                 (SlotName.Contains(TEXT("eyeLeft"), ESearchCase::IgnoreCase) ||
                  SlotName.Contains(TEXT("eyeRight"), ESearchCase::IgnoreCase)))
        {
            Face->SetMaterial(MaterialIndex, EyeMaterial);
        }
    }

    if (bMeshChanged || ReferenceBodyTransforms.IsEmpty())
    {
        CacheReferencePose();
    }
    bBodyReady = ReferenceBodyTransforms.Num() >= 19 &&
        Face->GetBoneIndex(TEXT("head")) != INDEX_NONE;
    Body->SetVisibility(bBodyReady, true);
    Face->SetVisibility(bBodyReady, true);
    return bBodyReady;
}

void ARaftSimMetaHumanCrewVisualActor::CacheReferencePose()
{
    ReferenceBodyTransforms.Reset();
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
            ReferenceBodyTransforms.Add(
                BoneName,
                Body->GetBoneTransformByName(BoneName, EBoneSpaces::ComponentSpace));
        }
    }
}

bool ARaftSimMetaHumanCrewVisualActor::HasArticulatedPaddleGripRig() const
{
    if (!bBodyReady || !Body)
    {
        return false;
    }
    for (const TCHAR* Side : {TEXT("l"), TEXT("r")})
    {
        for (const TCHAR* Digit : GripDigits)
        {
            if (FCString::Strcmp(Digit, TEXT("thumb")) != 0)
            {
                const FName Metacarpal(*FString::Printf(
                    TEXT("%s_metacarpal_%s"), Digit, Side));
                if (!ReferenceBodyTransforms.Contains(Metacarpal))
                {
                    return false;
                }
            }
            for (int32 Segment = 1; Segment <= 3; ++Segment)
            {
                const FName BoneName(*FString::Printf(
                    TEXT("%s_%02d_%s"), Digit, Segment, Side));
                if (!ReferenceBodyTransforms.Contains(BoneName))
                {
                    return false;
                }
            }
        }
    }
    return true;
}

void ARaftSimMetaHumanCrewVisualActor::ConfigureCrewAppearance_Implementation(
    int32 VariantIndex,
    int32 SeatSide,
    bool bGuide)
{
    CurrentVariantIndex = FMath::Abs(VariantIndex) % 4;
    bCurrentGuide = bGuide;
    if (!EnsureAssetsLoaded())
    {
        return;
    }
    ApplyCrewPose_Implementation(
        ERaftSimCrewAvatarAction::SeatedIdle,
        0.0f,
        1.0f,
        SeatSide);
}

void ARaftSimMetaHumanCrewVisualActor::ApplyCrewPose_Implementation(
    ERaftSimCrewAvatarAction Action,
    float NormalizedPhase,
    float Intensity,
    int32 SeatSide)
{
    if (!EnsureAssetsLoaded())
    {
        return;
    }
    const float SafePhase = FMath::IsFinite(NormalizedPhase)
        ? FMath::Frac(NormalizedPhase * FMath::Clamp(Intensity, 0.15f, 2.0f))
        : 0.0f;
    ApplyBodyPose(URaftSimCrewAvatarPoseLibrary::EvaluatePose(Action, SafePhase, SeatSide));
}

FVector ARaftSimMetaHumanCrewVisualActor::ToMeshSpace(const FVector& PointCm) const
{
    return PointCm / BodyScale;
}

void ARaftSimMetaHumanCrewVisualActor::SetDrivenBoneTransform(
    FName BoneName,
    const FTransform& Transform)
{
    if (Body && Body->GetBoneIndex(BoneName) != INDEX_NONE)
    {
        Body->SetBoneTransformByName(BoneName, Transform, EBoneSpaces::ComponentSpace);
    }
    // The MetaHuman face reference skeleton contains the shared body chain.
    // Mirroring the authored rafting solve into those shared bones keeps the
    // high-resolution head attached while all unmatched facial bones retain
    // their reference-pose local transforms.
    if (!bUsingAssembledCharacter && Face &&
        Face->GetBoneIndex(BoneName) != INDEX_NONE)
    {
        Face->SetBoneTransformByName(BoneName, Transform, EBoneSpaces::ComponentSpace);
    }
}

void ARaftSimMetaHumanCrewVisualActor::SetBoneAtPoint(
    FName BoneName,
    const FVector& DesiredPointCm)
{
    if (!Body || DesiredPointCm.ContainsNaN())
    {
        return;
    }
    const FTransform* Reference = ReferenceBodyTransforms.Find(BoneName);
    if (!Reference)
    {
        return;
    }
    FTransform Target = *Reference;
    Target.SetLocation(ToMeshSpace(DesiredPointCm));
    Target.SetRotation((MeshToAvatarRotation * Reference->GetRotation()).GetNormalized());
    SetDrivenBoneTransform(BoneName, Target);
}

void ARaftSimMetaHumanCrewVisualActor::SetSegmentBone(
    FName BoneName,
    FName ReferenceEndBone,
    const FVector& DesiredStartCm,
    const FVector& DesiredEndCm)
{
    if (!Body || DesiredStartCm.ContainsNaN() || DesiredEndCm.ContainsNaN())
    {
        return;
    }
    const FTransform* Reference = ReferenceBodyTransforms.Find(BoneName);
    const FTransform* ReferenceEnd = ReferenceBodyTransforms.Find(ReferenceEndBone);
    if (!Reference || !ReferenceEnd)
    {
        return;
    }
    FVector ReferenceDirection = MeshToAvatarRotation.RotateVector(
        (ReferenceEnd->GetLocation() - Reference->GetLocation()).GetSafeNormal());
    const FVector DesiredDirection = (DesiredEndCm - DesiredStartCm).GetSafeNormal();
    if (DesiredDirection.IsNearlyZero())
    {
        SetBoneAtPoint(BoneName, DesiredStartCm);
        return;
    }
    if (ReferenceDirection.IsNearlyZero())
    {
        const FName ParentBoneName = Body->GetParentBone(BoneName);
        if (const FTransform* ReferenceParent = ReferenceBodyTransforms.Find(ParentBoneName))
        {
            ReferenceDirection = MeshToAvatarRotation.RotateVector(
                (Reference->GetLocation() - ReferenceParent->GetLocation()).GetSafeNormal());
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
    Target.SetRotation(
        (Swing * MeshToAvatarRotation * Reference->GetRotation()).GetNormalized());
    SetDrivenBoneTransform(BoneName, Target);
}

void ARaftSimMetaHumanCrewVisualActor::ApplyBodyPose(const FRaftSimCrewAvatarPose& Pose)
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

    // Pose hand points describe the visible grip/contact target. A skeletal
    // MetaHuman hand bone is the wrist pivot, so placing that pivot directly
    // on the shaft leaves the palm and curled digits visibly detached. For
    // paddle-bearing actions only, offset the wrist by the reference
    // hand-to-middle-palm vector while preserving the authored grip target.
    FVector LeftWristCm = Pose.bShowPaddle
        ? ResolvePaddleGripWristCm(true, Pose.LeftHandCm)
        : Pose.LeftHandCm;
    FVector RightWristCm = Pose.bShowPaddle
        ? ResolvePaddleGripWristCm(false, Pose.RightHandCm)
        : Pose.RightHandCm;
    const auto ApplyArmPose = [&]()
    {
        const FVector LeftElbow =
            FMath::Lerp(Pose.LeftShoulderCm, LeftWristCm, 0.48f) +
            FVector(0.0f, -5.0f, -2.0f);
        const FVector RightElbow =
            FMath::Lerp(Pose.RightShoulderCm, RightWristCm, 0.48f) +
            FVector(0.0f, 5.0f, -2.0f);
        SetSegmentBone(
            TEXT("clavicle_l"), TEXT("upperarm_l"), UpperSpine, Pose.LeftShoulderCm);
        SetSegmentBone(
            TEXT("upperarm_l"), TEXT("lowerarm_l"), Pose.LeftShoulderCm, LeftElbow);
        SetSegmentBone(TEXT("lowerarm_l"), TEXT("hand_l"), LeftElbow, LeftWristCm);
        SetBoneAtPoint(TEXT("hand_l"), LeftWristCm);
        SetSegmentBone(
            TEXT("clavicle_r"), TEXT("upperarm_r"), UpperSpine, Pose.RightShoulderCm);
        SetSegmentBone(
            TEXT("upperarm_r"), TEXT("lowerarm_r"), Pose.RightShoulderCm, RightElbow);
        SetSegmentBone(TEXT("lowerarm_r"), TEXT("hand_r"), RightElbow, RightWristCm);
        SetBoneAtPoint(TEXT("hand_r"), RightWristCm);
    };
    ApplyArmPose();

    SetSegmentBone(TEXT("thigh_l"), TEXT("calf_l"), Pose.LeftHipCm, Pose.LeftKneeCm);
    SetSegmentBone(TEXT("calf_l"), TEXT("foot_l"), Pose.LeftKneeCm, Pose.LeftFootCm);
    SetBoneAtPoint(TEXT("foot_l"), Pose.LeftFootCm);
    SetSegmentBone(TEXT("thigh_r"), TEXT("calf_r"), Pose.RightHipCm, Pose.RightKneeCm);
    SetSegmentBone(TEXT("calf_r"), TEXT("foot_r"), Pose.RightKneeCm, Pose.RightFootCm);
    SetBoneAtPoint(TEXT("foot_r"), Pose.RightFootCm);

    Body->SetBoneScaleByName(TEXT("foot_l"), FVector::ZeroVector, EBoneSpaces::ComponentSpace);
    Body->SetBoneScaleByName(TEXT("foot_r"), FVector::ZeroVector, EBoneSpaces::ComponentSpace);

    // Publish the authored local transforms immediately. The host will keep
    // driving this pose every frame, but direct visual tools must see the same
    // body on the first frame rather than a one-frame standing reference pose.
    Body->RefreshBoneTransforms();
    ApplyPaddleGripPose(Pose);
    Body->RefreshBoneTransforms();
    MaximumPaddleGripAnchorErrorCm = Pose.bShowPaddle
        ? FMath::Max(
              MeasurePaddleGripAnchorErrorCm(true, Pose.LeftHandCm),
              MeasurePaddleGripAnchorErrorCm(false, Pose.RightHandCm))
        : 0.0f;
    MaximumPaddleGripContactErrorCm = Pose.bShowPaddle
        ? MeasurePaddleFingerContactErrorCm(Pose)
        : 0.0f;
    MaximumPaddleThumbContactErrorCm = Pose.bShowPaddle
        ? MeasurePaddleThumbContactErrorCm(Pose)
        : 0.0f;
    UpdatePaddleGloveMaterial();
    if (bUsingAssembledCharacter)
    {
        UpdateRigidAssembledFace();
    }
    if (HairMeshFallback)
    {
        const FTransform CurrentHead =
            Body->GetBoneTransformByName(TEXT("head"), EBoneSpaces::ComponentSpace);
        FQuat HeadDelta = FQuat::Identity;
        if (const FTransform* ReferenceHead = ReferenceBodyTransforms.Find(TEXT("head")))
        {
            HeadDelta = (CurrentHead.GetRotation() *
                         ReferenceHead->GetRotation().Inverse())
                            .GetNormalized();
        }
        FTransform HairTransform(
            (Body->GetComponentQuat() * HeadDelta).GetNormalized(),
            Body->GetComponentTransform().TransformPosition(
                CurrentHead.GetLocation()),
            Body->GetComponentScale());
        if (const UStaticMesh* HairMesh = HairMeshFallback->GetStaticMesh())
        {
            const FVector WorldBoundsOffset = HairTransform.TransformVector(
                HairMesh->GetBounds().Origin);
            HairTransform.SetLocation(
                HairTransform.GetLocation() - WorldBoundsOffset);
        }
        HairMeshFallback->SetWorldTransform(HairTransform);
        HairMeshFallback->UpdateBounds();
    }
    if (bUsingAssembledCharacter)
    {
        SynchronizeAssembledFollowers();
    }
    else
    {
        Face->RefreshBoneTransforms();
    }
}

FVector ARaftSimMetaHumanCrewVisualActor::ResolvePaddleGripWristCm(
    bool bLeft,
    const FVector& DesiredGripCm) const
{
    const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
    const FName HandName(*FString::Printf(TEXT("hand_%s"), Side));
    const FName PalmAnchorName(*FString::Printf(TEXT("middle_metacarpal_%s"), Side));
    const FTransform* ReferenceHand = ReferenceBodyTransforms.Find(HandName);
    const FTransform* ReferencePalm = ReferenceBodyTransforms.Find(PalmAnchorName);
    if (!ReferenceHand || !ReferencePalm)
    {
        return DesiredGripCm;
    }
    const FVector ReferencePalmOffsetCm = MeshToAvatarRotation.RotateVector(
        ReferencePalm->GetLocation() - ReferenceHand->GetLocation()) * BodyScale;
    return DesiredGripCm - ReferencePalmOffsetCm;
}

FVector ARaftSimMetaHumanCrewVisualActor::ResolvePaddleGripAxis(
    const FRaftSimCrewAvatarPose& Pose,
    const FVector& DesiredGripCm) const
{
    const FVector ShaftAxis =
        (Pose.PaddleBottomCm - Pose.PaddleTopCm).GetSafeNormal();
    if (ShaftAxis.IsNearlyZero())
    {
        return FVector::UpVector;
    }
    if (FVector::DistSquared(DesiredGripCm, Pose.PaddleTopCm) <= 4.0f)
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

float ARaftSimMetaHumanCrewVisualActor::MeasurePaddleGripAnchorErrorCm(
    bool bLeft,
    const FVector& DesiredGripCm) const
{
    if (!Body)
    {
        return TNumericLimits<float>::Max();
    }
    const FName PalmAnchorName(*FString::Printf(
        TEXT("middle_metacarpal_%s"), bLeft ? TEXT("l") : TEXT("r")));
    if (Body->GetBoneIndex(PalmAnchorName) == INDEX_NONE)
    {
        return TNumericLimits<float>::Max();
    }
    const FVector RenderedGripCm =
        Body->GetBoneTransformByName(PalmAnchorName, EBoneSpaces::ComponentSpace)
            .GetLocation() * BodyScale;
    return FVector::Distance(RenderedGripCm, DesiredGripCm);
}

float ARaftSimMetaHumanCrewVisualActor::MeasurePaddleFingerContactErrorCm(
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
        const FVector GripCenterCm = bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
        // The top hand closes over the transverse T-grip with its authored
        // skeletal curl. Projecting that short handle toward a head-on camera
        // and forcing every joint onto a radial contact arc creates a false
        // donut silhouette. The lower hand is the shaft-contact hand and is
        // the one that must satisfy the deterministic radial contact metric.
        if (FVector::DistSquared(GripCenterCm, Pose.PaddleTopCm) <= 4.0f)
        {
            continue;
        }
        const FVector GripAxis = ResolvePaddleGripAxis(Pose, GripCenterCm);
        for (const TCHAR* Digit : {TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")})
        {
            FAnatomicalGripDigitProfile Profile;
            if (!ResolveAnatomicalGripDigitProfile(Digit, Profile))
            {
                return TNumericLimits<float>::Max();
            }
            const FName DistalName(*FString::Printf(TEXT("%s_03_%s"), Digit, Side));
            if (Body->GetBoneIndex(DistalName) == INDEX_NONE)
            {
                return TNumericLimits<float>::Max();
            }
            const FVector DistalCm = Body->GetBoneTransformByName(
                DistalName,
                EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
            const FVector OffsetCm = DistalCm - GripCenterCm;
            const float RadialDistanceCm = FVector::VectorPlaneProject(
                OffsetCm,
                GripAxis).Size();
            MaximumErrorCm = FMath::Max(
                MaximumErrorCm,
                FMath::Abs(RadialDistanceCm - Profile.PadCenterRadiusCm));
        }
    }
    return MaximumErrorCm;
}

float ARaftSimMetaHumanCrewVisualActor::MeasurePaddleThumbContactErrorCm(
    const FRaftSimCrewAvatarPose& Pose) const
{
    if (!Body || !Pose.bShowPaddle)
    {
        return 0.0f;
    }
    float MaximumErrorCm = 0.0f;
    for (const bool bLeft : {true, false})
    {
        const FVector GripCenterCm = bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
        if (FVector::DistSquared(GripCenterCm, Pose.PaddleTopCm) <= 4.0f)
        {
            continue;
        }
        const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
        const FName ThumbPadName(*FString::Printf(TEXT("thumb_03_%s"), Side));
        if (Body->GetBoneIndex(ThumbPadName) == INDEX_NONE)
        {
            return TNumericLimits<float>::Max();
        }
        const FVector GripAxis = ResolvePaddleGripAxis(Pose, GripCenterCm);
        const FVector ThumbPadCm = Body->GetBoneTransformByName(
            ThumbPadName,
            EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
        const float RadialDistanceCm = FVector::VectorPlaneProject(
            ThumbPadCm - GripCenterCm,
            GripAxis).Size();
        MaximumErrorCm = FMath::Max(
            MaximumErrorCm,
            FMath::Abs(RadialDistanceCm - PaddleThumbPadCenterRadiusCm));
    }
    return MaximumErrorCm;
}

void ARaftSimMetaHumanCrewVisualActor::ApplyFingerChain(
    bool bLeft,
    const TCHAR* Digit,
    bool bHasMetacarpal,
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
    const FTransform* ParentReference = ReferenceBodyTransforms.Find(ParentName);
    if (!ParentReference || ParentCurrent.ContainsNaN())
    {
        return;
    }

    const auto ApplyRelativeBone = [this, GripAlpha](
        const FName BoneName,
        const FName ReferenceParentName,
        const FTransform& CurrentParent,
        const float CurlDegrees) -> FTransform
    {
        const FTransform* Reference = ReferenceBodyTransforms.Find(BoneName);
        const FTransform* ReferenceParent =
            ReferenceBodyTransforms.Find(ReferenceParentName);
        if (!Reference || !ReferenceParent)
        {
            return CurrentParent;
        }
        FTransform Relative = Reference->GetRelativeTransform(*ReferenceParent);
        const FQuat LocalCurl(
            FVector::YAxisVector,
            FMath::DegreesToRadians(CurlDegrees * GripAlpha));
        Relative.SetRotation(
            (Relative.GetRotation() * LocalCurl).GetNormalized());
        const FTransform Target = Relative * CurrentParent;
        SetDrivenBoneTransform(BoneName, Target);
        return Target;
    };

    if (bHasMetacarpal)
    {
        const FName MetacarpalName(*FString::Printf(
            TEXT("%s_metacarpal_%s"), Digit, Side));
        ParentCurrent = ApplyRelativeBone(
            MetacarpalName, ParentName, ParentCurrent, 8.0f);
        ParentName = MetacarpalName;
    }

    // These values close the distal pads around the 3.3 cm production shaft;
    // the previous 30/48/34 profile left a conspicuous open-finger silhouette.
    static const float CurlDegrees[] = {58.0f, 72.0f, 50.0f};
    static const float ThumbCurlDegrees[] = {34.0f, 50.0f, 38.0f};
    for (int32 Segment = 1; Segment <= 3; ++Segment)
    {
        const FName BoneName(*FString::Printf(
            TEXT("%s_%02d_%s"), Digit, Segment, Side));
        const float Curl = FCString::Strcmp(Digit, TEXT("thumb")) == 0
            ? ThumbCurlDegrees[Segment - 1]
            : CurlDegrees[Segment - 1];
        ParentCurrent = ApplyRelativeBone(
            BoneName, ParentName, ParentCurrent, Curl);
        ParentName = BoneName;
    }
}

void ARaftSimMetaHumanCrewVisualActor::ApplyFingerChainAroundGrip(
    bool bLeft,
    const TCHAR* Digit,
    const FVector& GripCenterCm,
    const FVector& GripAxis)
{
    if (!Body || !Digit)
    {
        return;
    }
    FAnatomicalGripDigitProfile Profile;
    if (!ResolveAnatomicalGripDigitProfile(Digit, Profile))
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
        FirstName,
        EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
    FVector RadialDirection = FVector::VectorPlaneProject(
        SegmentStartCm - GripCenterCm,
        SafeGripAxis).GetSafeNormal();
    const FVector WristCm = Body->GetBoneTransformByName(
        HandName,
        EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
    const FVector WristRadial = FVector::VectorPlaneProject(
        WristCm - GripCenterCm,
        SafeGripAxis).GetSafeNormal();
    if (SafeGripAxis.IsNearlyZero() || RadialDirection.IsNearlyZero())
    {
        return;
    }
    float WrapSign = FVector::DotProduct(
        SafeGripAxis,
        FVector::CrossProduct(RadialDirection, WristRadial)) >= 0.0f
        ? 1.0f
        : -1.0f;
    if (WristRadial.IsNearlyZero())
    {
        WrapSign = bLeft ? -1.0f : 1.0f;
    }
    RadialDirection = RadialDirection.RotateAngleAxis(
        Profile.FanDegrees * WrapSign,
        SafeGripAxis);
    const float AxialOffsetCm = FVector::DotProduct(
        SegmentStartCm - GripCenterCm,
        SafeGripAxis);
    const float WrapAnglesDegrees[] = {
        Profile.EntrySweepDegrees,
        Profile.MiddleSweepDegrees,
        Profile.TipSweepDegrees};
    const float JointRadiiCm[] = {
        Profile.ProximalRadiusCm,
        Profile.PadCenterRadiusCm,
        Profile.TipCenterRadiusCm};
    const FName BoneNames[] = {FirstName, SecondName, ThirdName};
    float CumulativeAngleDegrees = 0.0f;
    for (int32 SegmentIndex = 0; SegmentIndex < 3; ++SegmentIndex)
    {
        CumulativeAngleDegrees += WrapAnglesDegrees[SegmentIndex] * WrapSign;
        const FVector TargetRadial = RadialDirection.RotateAngleAxis(
            CumulativeAngleDegrees,
            SafeGripAxis);
        const FVector SegmentEndCm =
            GripCenterCm + SafeGripAxis * AxialOffsetCm +
            TargetRadial * JointRadiiCm[SegmentIndex];
        const FName ReferenceEnd = SegmentIndex < 2
            ? BoneNames[SegmentIndex + 1]
            : BoneNames[SegmentIndex];
        SetSegmentBone(
            BoneNames[SegmentIndex],
            ReferenceEnd,
            SegmentStartCm,
            SegmentEndCm);
        SegmentStartCm = SegmentEndCm;
    }
}

void ARaftSimMetaHumanCrewVisualActor::ApplyOpposedThumbPadToGrip(
    bool bLeft,
    const FVector& GripCenterCm,
    const FVector& GripAxis)
{
    if (!Body)
    {
        return;
    }
    const TCHAR* Side = bLeft ? TEXT("l") : TEXT("r");
    const FName SecondName(*FString::Printf(TEXT("thumb_02_%s"), Side));
    const FName ThirdName(*FString::Printf(TEXT("thumb_03_%s"), Side));
    if (Body->GetBoneIndex(SecondName) == INDEX_NONE ||
        Body->GetBoneIndex(ThirdName) == INDEX_NONE)
    {
        return;
    }
    const FVector SafeGripAxis = GripAxis.GetSafeNormal();
    const FTransform CurrentSecond = Body->GetBoneTransformByName(
        SecondName,
        EBoneSpaces::ComponentSpace);
    const FTransform CurrentThird = Body->GetBoneTransformByName(
        ThirdName,
        EBoneSpaces::ComponentSpace);
    const FVector SecondCm = CurrentSecond.GetLocation() * BodyScale;
    const FVector CurrentPadCm = CurrentThird.GetLocation() * BodyScale;
    FVector PadRadialDirection = FVector::VectorPlaneProject(
        CurrentPadCm - GripCenterCm,
        SafeGripAxis).GetSafeNormal();
    if (SafeGripAxis.IsNearlyZero() || PadRadialDirection.IsNearlyZero())
    {
        return;
    }

    // Preserve the authored thumb base and its side of the shaft, then bring
    // only the distal pad onto the neoprene/paddle contact radius. Solving one
    // distal segment avoids the rejected full radial thumb cage, which read as
    // an oval loop, while retaining an unmistakably opposed fifth digit.
    const float AxialOffsetCm = FVector::DotProduct(
        CurrentPadCm - GripCenterCm,
        SafeGripAxis);
    const FVector TargetPadCm =
        GripCenterCm + SafeGripAxis * AxialOffsetCm +
        PadRadialDirection * PaddleThumbPadCenterRadiusCm;
    SetSegmentBone(SecondName, ThirdName, SecondCm, TargetPadCm);
    FTransform TargetThird = CurrentThird;
    TargetThird.SetLocation(ToMeshSpace(TargetPadCm));
    SetDrivenBoneTransform(ThirdName, TargetThird);
}

void ARaftSimMetaHumanCrewVisualActor::UpdatePaddleGloveMaterial()
{
    bLocalizedPaddleGlovesReady = false;
    if (!Body || !WetsuitPresentationMaterial)
    {
        return;
    }
    const FName LeftPalmName(TEXT("middle_metacarpal_l"));
    const FName RightPalmName(TEXT("middle_metacarpal_r"));
    if (Body->GetBoneIndex(LeftPalmName) == INDEX_NONE ||
        Body->GetBoneIndex(RightPalmName) == INDEX_NONE)
    {
        return;
    }
    const FVector LeftCenterWorld = Body->GetBoneTransformByName(
        LeftPalmName,
        EBoneSpaces::WorldSpace).GetLocation();
    const FVector RightCenterWorld = Body->GetBoneTransformByName(
        RightPalmName,
        EBoneSpaces::WorldSpace).GetLocation();
    if (LeftCenterWorld.ContainsNaN() || RightCenterWorld.ContainsNaN())
    {
        return;
    }
    WetsuitPresentationMaterial->SetVectorParameterValue(
        TEXT("LeftPaddleGloveCenterWS"),
        FLinearColor(LeftCenterWorld.X, LeftCenterWorld.Y, LeftCenterWorld.Z, 1.0f));
    WetsuitPresentationMaterial->SetVectorParameterValue(
        TEXT("RightPaddleGloveCenterWS"),
        FLinearColor(RightCenterWorld.X, RightCenterWorld.Y, RightCenterWorld.Z, 1.0f));
    bLocalizedPaddleGlovesReady = true;
}

void ARaftSimMetaHumanCrewVisualActor::ApplyPaddleGripPose(
    const FRaftSimCrewAvatarPose& Pose)
{
    if (!HasArticulatedPaddleGripRig())
    {
        return;
    }
    // A visible paddle uses a firm but not fist-like curl; rescue and swim
    // states retain relaxed natural flex rather than the imported flat palm.
    const float GripAlpha = Pose.bShowPaddle ? 1.0f : 0.16f;
    for (const bool bLeft : {true, false})
    {
        ApplyFingerChain(bLeft, TEXT("thumb"), false, GripAlpha);
        ApplyFingerChain(bLeft, TEXT("index"), true, GripAlpha);
        ApplyFingerChain(bLeft, TEXT("middle"), true, GripAlpha);
        ApplyFingerChain(bLeft, TEXT("ring"), true, GripAlpha);
        ApplyFingerChain(bLeft, TEXT("pinky"), true, GripAlpha);
    }
    if (!Pose.bShowPaddle)
    {
        return;
    }
    Body->RefreshBoneTransforms();
    for (const bool bLeft : {true, false})
    {
        const FVector GripCenterCm = bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
        if (FVector::DistSquared(GripCenterCm, Pose.PaddleTopCm) <= 4.0f)
        {
            continue;
        }
        const FVector GripAxis = ResolvePaddleGripAxis(Pose, GripCenterCm);
        for (const TCHAR* Digit : {TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")})
        {
            ApplyFingerChainAroundGrip(
                bLeft, Digit, GripCenterCm, GripAxis);
        }
        Body->RefreshBoneTransforms();
        ApplyOpposedThumbPadToGrip(
            bLeft, GripCenterCm, GripAxis);
    }
}

void ARaftSimMetaHumanCrewVisualActor::UpdateRigidAssembledFace()
{
    if (!AssembledFace || !Body ||
        Body->GetBoneIndex(TEXT("head")) == INDEX_NONE)
    {
        return;
    }
    const FTransform CurrentHeadWorld =
        Body->GetBoneTransformByName(TEXT("head"), EBoneSpaces::WorldSpace);
    const FQuat ComponentRotation =
        (CurrentHeadWorld.GetRotation() *
         ReferenceAssembledFaceHeadComponentTransform.GetRotation().Inverse())
            .GetNormalized();
    const FVector ReferenceHeadOffset =
        ReferenceAssembledFaceHeadComponentTransform.GetLocation() *
        AssembledFaceComponentScale;
    const FVector ComponentLocation = CurrentHeadWorld.GetLocation() -
        ComponentRotation.RotateVector(ReferenceHeadOffset);
    AssembledFace->SetWorldTransform(FTransform(
        ComponentRotation,
        ComponentLocation,
        AssembledFaceComponentScale));
    AssembledFace->UpdateBounds();
}

void ARaftSimMetaHumanCrewVisualActor::SynchronizeAssembledFollowers()
{
    AActor* CharacterActor = GetAssembledCharacterActor();
    if (!CharacterActor || !AssembledBody || !AssembledFace)
    {
        return;
    }

    // The poseable leader publishes synchronously, while the generated face
    // and wardrobe AnimBPs normally consume it on the next world tick. Tooling
    // and first-frame gameplay both require a coherent character immediately.
    AssembledBody->RefreshBoneTransforms();
    TArray<USkeletalMeshComponent*> SkeletalComponents;
    CharacterActor->GetComponents<USkeletalMeshComponent>(SkeletalComponents);
    for (USkeletalMeshComponent* Component : SkeletalComponents)
    {
        if (!Component || Component == AssembledBody)
        {
            continue;
        }
        if (Component == AssembledFace)
        {
            continue;
        }
        Component->TickAnimation(0.0f, false);
        Component->RefreshBoneTransforms();
    }
}

bool ARaftSimMetaHumanCrewVisualActor::HasFinitePose() const
{
    if (!bBodyReady || !Body || Body->GetComponentTransform().ContainsNaN())
    {
        return false;
    }
    if (bUsingAssembledCharacter)
    {
        if (!AssembledCharacter || !AssembledCharacter->GetChildActor() ||
            !AssembledBody || !AssembledFace ||
            AssembledBody->GetComponentTransform().ContainsNaN() ||
            AssembledFace->GetComponentTransform().ContainsNaN())
        {
            return false;
        }
    }
    else if (!Face || Face->GetComponentTransform().ContainsNaN())
    {
        return false;
    }
    for (const FName BoneName : MetaHumanDrivenBones)
    {
        if (Body->GetBoneIndex(BoneName) != INDEX_NONE &&
            Body->GetBoneTransformByName(BoneName, EBoneSpaces::ComponentSpace).ContainsNaN())
        {
            return false;
        }
    }
    const USkinnedMeshComponent* HeadComponent = bUsingAssembledCharacter
        ? static_cast<const USkinnedMeshComponent*>(AssembledFace.Get())
        : static_cast<const USkinnedMeshComponent*>(Face.Get());
    return HeadComponent &&
        !HeadComponent->GetBoneTransform(TEXT("head")).ContainsNaN();
}
