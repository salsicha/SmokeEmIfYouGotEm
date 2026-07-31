#include "RaftSimWaterVfxActor.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/MeshComponent.h"
#include "Components/PostProcessComponent.h"
#include "ProceduralMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Math/RotationMatrix.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimWaterSurfaceActor.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
constexpr float CmPerM = 100.0f;
constexpr float GravityMps2 = 9.80665f;
// Translucent whitewater is deliberately local. Rendering every detected
// hydraulic jump along the kilometre-scale reach spends fill rate on effects
// that contribute only a few pixels (or are fully hidden by the canyon). Keep
// the preallocated fail-closed pool, but feed only the nearest useful sites.
constexpr int32 MaxActiveRapidNiagaraSites = 2;
constexpr float ContactNiagaraCullDistanceCm = 4500.0f;
constexpr float RapidNiagaraFullDensityDistanceCm = 6000.0f;
constexpr float RapidNiagaraCullDistanceCm = 12000.0f;
constexpr int32 DepthBearingContactWaterV10FrameCount = 6;
constexpr float DepthBearingContactWaterV10FrameSeconds = 0.12f;

float EvaluateDepthBearingContactWaterV10Field(
    const FVector& LocalMeters,
    float Phase)
{
    // Positive values are liquid. The superelliptic footprint closes a broad
    // basal body, while two overlapping asymmetric shoulders produce one
    // connected hydraulic mass instead of repeated lobes or a vertical sheet.
    const float X = LocalMeters.X;
    const float Y = LocalMeters.Y;
    const float Z = LocalMeters.Z;
    const float LateralDrift = 0.08f * FMath::Sin(Phase * 0.83f);
    const float WarpedY = Y - LateralDrift +
        0.07f * FMath::Sin(X * 3.0f + Phase * 0.91f);
    const float XRadius = 1.35f *
        (1.0f + 0.06f * FMath::Sin(Y * 4.3f + Phase * 1.1f));
    const float YRadius = 0.75f *
        (1.0f + 0.10f * FMath::Sin(X * 3.6f - Phase * 0.7f));
    const float Footprint = 1.0f -
        FMath::Pow(FMath::Abs((X + 0.04f) / XRadius), 4.0f) -
        FMath::Pow(FMath::Abs(WarpedY / YRadius), 4.0f);
    const float FootprintEnvelope = FMath::Clamp(Footprint, 0.0f, 1.0f);
    const float CrestCenterX = -0.28f + 0.07f * FMath::Sin(Phase);
    const float Crest = 0.30f * FMath::Exp(
        -FMath::Square((X - CrestCenterX) / 0.45f) -
        FMath::Square((Y + 0.08f) / 0.62f));
    const float OffsetBoil = 0.12f * FMath::Exp(
        -FMath::Square((X - 0.08f) / 0.46f) -
        FMath::Square(
            (Y - 0.22f - 0.06f * FMath::Sin(Phase * 1.37f)) / 0.38f));
    const float DownstreamShoulder = 0.06f * FMath::Exp(
        -FMath::Square((X - 0.48f) / 0.62f) -
        FMath::Square((Y - 0.06f * FMath::Sin(Phase * 1.37f)) / 0.52f));
    const float UpstreamRamp = 0.04f * FMath::Exp(
        -FMath::Square((X + 0.70f) / 0.62f) -
        FMath::Square((Y + 0.06f * FMath::Cos(Phase)) / 0.64f));
    const float TurbulentTop =
        0.025f * FMath::Sin(X * 4.1f - Phase * 1.9f + Y * 1.7f) +
        0.015f * FMath::Sin(X * 7.3f + Phase * 2.7f - Y * 4.6f);
    // Sink the perimeter beneath the sampled river and lift the interior.
    // This makes the visible hydraulic shoulder join the live surface without
    // exposing a flat translucent wall, while the implicit body remains a
    // genuinely closed, depth-bearing volume below it.
    const float TopEnvelope = FMath::Pow(FootprintEnvelope, 0.42f);
    const float Top = -0.04f + 0.07f * TopEnvelope +
        (Crest + OffsetBoil + DownstreamShoulder + UpstreamRamp) *
            FMath::Pow(FootprintEnvelope, 0.34f) +
        TurbulentTop * FootprintEnvelope;
    const float Bottom = -0.60f +
        0.018f * FMath::Sin(X * 2.2f + Phase * 0.7f) *
            FMath::Cos(Y * 2.8f - Phase * 0.4f);
    return FMath::Min3(
        Top - Z,
        Z - Bottom,
        Footprint * 0.42f);
}

FVector EvaluateDepthBearingContactWaterV10OutwardNormal(
    const FVector& LocalMeters,
    float Phase)
{
    constexpr float EpsilonM = 0.008f;
    const FVector Dx(EpsilonM, 0.0f, 0.0f);
    const FVector Dy(0.0f, EpsilonM, 0.0f);
    const FVector Dz(0.0f, 0.0f, EpsilonM);
    const FVector Gradient(
        EvaluateDepthBearingContactWaterV10Field(
            LocalMeters + Dx, Phase) -
            EvaluateDepthBearingContactWaterV10Field(
                LocalMeters - Dx, Phase),
        EvaluateDepthBearingContactWaterV10Field(
            LocalMeters + Dy, Phase) -
            EvaluateDepthBearingContactWaterV10Field(
                LocalMeters - Dy, Phase),
        EvaluateDepthBearingContactWaterV10Field(
            LocalMeters + Dz, Phase) -
            EvaluateDepthBearingContactWaterV10Field(
                LocalMeters - Dz, Phase));
    // The scalar field is positive inside liquid, so negative gradient points
    // outward. Scale is irrelevant because the result is normalized.
    return (-Gradient).GetSafeNormal(SMALL_NUMBER, FVector::UpVector);
}

float DeterministicWave(int32 Index, float Phase, float Frequency)
{
    return 0.5f + 0.5f * FMath::Sin(
        Phase * Frequency + static_cast<float>(Index) * 2.39996323f);
}

void ConfigureVfxComponent(
    UInstancedStaticMeshComponent* Component,
    UStaticMesh* Mesh,
    UMaterialInterface* Material)
{
    if (!Component)
    {
        return;
    }
    Component->SetStaticMesh(Mesh);
    Component->SetMaterial(0, Material);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCastShadow(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetTranslucentSortPriority(2);
}

void ConfigureNiagaraComponent(
    UNiagaraComponent* Component,
    UNiagaraSystem* System,
    int32 SortPriority,
    float CullDistanceCm)
{
    if (!Component)
    {
        return;
    }
    Component->SetAsset(System);
    // Auto-activation is a construction-time property. BeginPlay reuses this
    // helper only to bind the late-loaded cooked Niagara asset; calling
    // SetAutoActivate after the component has begun play produces one warning
    // per pooled component even though the value is already false.
    if (!Component->HasBegunPlay())
    {
        Component->SetAutoActivate(false);
    }
    Component->SetCastShadow(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetTranslucentSortPriority(SortPriority);
    Component->SetCullDistance(CullDistanceCm);
}

void SetNiagaraEmission(
    UNiagaraComponent* Component,
    bool bEnabled,
    const FVector& Location,
    const FVector& Direction,
    float UniformScale,
    float SpawnRate)
{
    if (!Component || !Component->GetAsset())
    {
        return;
    }
    if (!bEnabled || SpawnRate <= KINDA_SMALL_NUMBER)
    {
        Component->SetVariableFloat(TEXT("User.SpawnRate"), 0.0f);
        if (Component->IsActive())
        {
            Component->Deactivate();
        }
        return;
    }

    FVector LaunchDirection = Direction.GetSafeNormal();
    if (LaunchDirection.IsNearlyZero())
    {
        LaunchDirection = FVector::ForwardVector;
    }
    Component->SetWorldLocation(Location);
    Component->SetWorldRotation(
        FRotationMatrix::MakeFromX(LaunchDirection).Rotator());
    Component->SetWorldScale3D(FVector(FMath::Max(UniformScale, 0.05f)));
    Component->SetVariableFloat(TEXT("User.SpawnRate"), SpawnRate);
    if (!Component->IsActive())
    {
        Component->Activate(true);
    }
}

FRotator MakeCameraFacingCardRotation(
    const FVector& Location,
    const FVector& CameraLocation)
{
    // Preserve the camera's elevation. The former 2D normal faced cards only
    // in yaw, so guide-height and contact-review cameras saw every spray plane
    // nearly edge-on as a dotted arc instead of a thin water streak.
    FVector ViewNormal = (CameraLocation - Location).GetSafeNormal();
    if (ViewNormal.IsNearlyZero())
    {
        ViewNormal = FVector::ForwardVector;
    }
    // The engine plane lies in local XY with +Z as its normal. Keep local X
    // vertical and rotate +Z toward the camera so elongated cards read as
    // water streaks rather than horizontal glass shards.
    return FRotationMatrix::MakeFromZX(ViewNormal, FVector::UpVector).Rotator();
}
}

ARaftSimWaterVfxActor::ARaftSimWaterVfxActor()
{
    PrimaryActorTick.bCanEverTick = true;

    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);

    SprayInstances = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("SolverSpray"));
    SprayInstances->SetupAttachment(Root);
    MistInstances = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("AeratedMist"));
    MistInstances->SetupAttachment(Root);
    SheetInstances = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("RaftImpactSheets"));
    SheetInstances->SetupAttachment(Root);
    DropletInstances = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("ContactDroplets"));
    DropletInstances->SetupAttachment(Root);
    RapidAerosolInstances = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("RapidAerosol"));
    RapidAerosolInstances->SetupAttachment(Root);
    SolverSprayNiagara = CreateDefaultSubobject<UNiagaraComponent>(
        TEXT("ProductionSolverSpray"));
    SolverSprayNiagara->SetupAttachment(Root);
    ContactDropletNiagara = CreateDefaultSubobject<UNiagaraComponent>(
        TEXT("ProductionContactDroplets"));
    ContactDropletNiagara->SetupAttachment(Root);
    AeratedMistNiagara = CreateDefaultSubobject<UNiagaraComponent>(
        TEXT("ProductionAeratedMist"));
    AeratedMistNiagara->SetupAttachment(Root);
    constexpr int32 RapidNiagaraPoolSize = 8;
    RapidAerosolNiagara.Reserve(RapidNiagaraPoolSize);
    for (int32 Index = 0; Index < RapidNiagaraPoolSize; ++Index)
    {
        UNiagaraComponent* Component = CreateDefaultSubobject<UNiagaraComponent>(
            *FString::Printf(TEXT("ProductionRapidAerosol_%02d"), Index));
        Component->SetupAttachment(Root);
        RapidAerosolNiagara.Add(Component);
        UNiagaraComponent* RollerComponent =
            CreateDefaultSubobject<UNiagaraComponent>(
                *FString::Printf(TEXT("ProductionRapidRoller_%02d"), Index));
        RollerComponent->SetupAttachment(Root);
        RapidRollerNiagara.Add(RollerComponent);
    }
    ContactWaterPatch = CreateDefaultSubobject<UProceduralMeshComponent>(
        TEXT("ContactWaterPatch"));
    ContactWaterPatch->SetupAttachment(Root);
    ContactWaterPatch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ContactWaterPatch->SetCastShadow(false);
    ContactWaterPatch->SetCanEverAffectNavigation(false);
    ContactWaterPatch->SetMobility(EComponentMobility::Movable);
    ContactWaterPatch->SetTranslucentSortPriority(2);
    ContactWaterPatch->SetVisibility(false, true);
    ConnectedContactWaterV6Review =
        CreateDefaultSubobject<UProceduralMeshComponent>(
            TEXT("ConnectedContactWaterV6Review"));
    ConnectedContactWaterV6Review->SetupAttachment(Root);
    ConnectedContactWaterV6Review->SetCollisionEnabled(
        ECollisionEnabled::NoCollision);
    ConnectedContactWaterV6Review->SetCastShadow(false);
    ConnectedContactWaterV6Review->SetCanEverAffectNavigation(false);
    ConnectedContactWaterV6Review->SetMobility(EComponentMobility::Movable);
    ConnectedContactWaterV6Review->SetTranslucentSortPriority(3);
    ConnectedContactWaterV6Review->SetVisibility(false, true);
    ConnectedContactWaterV7Review =
        CreateDefaultSubobject<UProceduralMeshComponent>(
            TEXT("ConnectedContactWaterV7Review"));
    ConnectedContactWaterV7Review->SetupAttachment(Root);
    ConnectedContactWaterV7Review->SetCollisionEnabled(
        ECollisionEnabled::NoCollision);
    ConnectedContactWaterV7Review->SetCastShadow(false);
    ConnectedContactWaterV7Review->SetCanEverAffectNavigation(false);
    ConnectedContactWaterV7Review->SetMobility(EComponentMobility::Movable);
    ConnectedContactWaterV7Review->SetTranslucentSortPriority(4);
    ConnectedContactWaterV7Review->SetVisibility(false, true);
    ConnectedContactWaterV8Review =
        CreateDefaultSubobject<UProceduralMeshComponent>(
            TEXT("ConnectedContactWaterV8Review"));
    ConnectedContactWaterV8Review->SetupAttachment(Root);
    ConnectedContactWaterV8Review->SetCollisionEnabled(
        ECollisionEnabled::NoCollision);
    ConnectedContactWaterV8Review->SetCastShadow(false);
    ConnectedContactWaterV8Review->SetCanEverAffectNavigation(false);
    ConnectedContactWaterV8Review->SetMobility(EComponentMobility::Movable);
    ConnectedContactWaterV8Review->SetTranslucentSortPriority(5);
    ConnectedContactWaterV8Review->SetVisibility(false, true);
    DepthBearingContactWaterV10Review =
        CreateDefaultSubobject<UProceduralMeshComponent>(
            TEXT("DepthBearingContactWaterV10Review"));
    DepthBearingContactWaterV10Review->SetupAttachment(Root);
    DepthBearingContactWaterV10Review->SetCollisionEnabled(
        ECollisionEnabled::NoCollision);
    DepthBearingContactWaterV10Review->SetCastShadow(false);
    DepthBearingContactWaterV10Review->SetCanEverAffectNavigation(false);
    DepthBearingContactWaterV10Review->SetMobility(EComponentMobility::Movable);
    DepthBearingContactWaterV10Review->SetTranslucentSortPriority(6);
    DepthBearingContactWaterV10Review->SetVisibility(false, true);
    UnderwaterPostProcess = CreateDefaultSubobject<UPostProcessComponent>(
        TEXT("UnderwaterPostProcess"));
    UnderwaterPostProcess->SetupAttachment(Root);
    UnderwaterPostProcess->bUnbound = true;
    UnderwaterPostProcess->BlendWeight = 0.0f;
    FPostProcessSettings& Underwater = UnderwaterPostProcess->Settings;
    Underwater.bOverride_SceneColorTint = true;
    Underwater.SceneColorTint = FLinearColor(0.34f, 0.62f, 0.64f, 1.0f);
    Underwater.bOverride_ColorSaturation = true;
    Underwater.ColorSaturation = FVector4(0.48f, 0.72f, 0.78f, 1.0f);
    Underwater.bOverride_ColorContrast = true;
    Underwater.ColorContrast = FVector4(0.82f, 0.88f, 0.92f, 1.0f);
    Underwater.bOverride_VignetteIntensity = true;
    Underwater.VignetteIntensity = 0.52f;
    Underwater.bOverride_SceneFringeIntensity = true;
    Underwater.SceneFringeIntensity = 1.6f;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> Plane(
        TEXT("/Engine/BasicShapes/Plane.Plane"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SprayMaterial(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_SprayMist.M_RaftSim_SprayMist"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> ContactWaterMaterial(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_BreakingWaterLip."
             "M_RaftSim_BreakingWaterLip"));
    UStaticMesh* PlaneMesh = Plane.Succeeded() ? Plane.Object : nullptr;
    UMaterialInterface* Material =
        SprayMaterial.Succeeded() ? SprayMaterial.Object : nullptr;
    // A sphere remains visibly geometric even at low opacity and needs enough
    // scale to look like a soap bubble. Soft alpha cards are both cheaper and
    // closer to the thin optical depth of real spray, mist, foam and droplets.
    ConfigureVfxComponent(SprayInstances, PlaneMesh, Material);
    ConfigureVfxComponent(MistInstances, PlaneMesh, Material);
    ConfigureVfxComponent(SheetInstances, PlaneMesh, Material);
    ConfigureVfxComponent(DropletInstances, PlaneMesh, Material);
    ConfigureVfxComponent(RapidAerosolInstances, PlaneMesh, Material);
    // Keep the component pool configured but asset-free on the native CDO.
    // Cooked stateless Niagara emitters rebuild stripped modules from their
    // template CDO while loading. Loading them through ConstructorHelpers here
    // re-enters that path during ProcessNewlyLoadedUObjects, before Niagara's
    // stateless template has completed module startup, and crashes Shipping.
    // BeginPlay performs the same bounded loads after engine/module startup.
    ConfigureNiagaraComponent(
        SolverSprayNiagara, nullptr, 3, ContactNiagaraCullDistanceCm);
    ConfigureNiagaraComponent(
        ContactDropletNiagara, nullptr, 4, ContactNiagaraCullDistanceCm);
    ConfigureNiagaraComponent(
        AeratedMistNiagara, nullptr, 1, ContactNiagaraCullDistanceCm);
    for (UNiagaraComponent* Component : RapidAerosolNiagara)
    {
        ConfigureNiagaraComponent(
            Component, nullptr, 0, RapidNiagaraCullDistanceCm);
    }
    for (UNiagaraComponent* Component : RapidRollerNiagara)
    {
        ConfigureNiagaraComponent(
            Component, nullptr, 2, RapidNiagaraCullDistanceCm);
    }
    ContactWaterPatch->SetMaterial(
        0,
        ContactWaterMaterial.Succeeded()
            ? ContactWaterMaterial.Object.Get()
            : Material);
    ConnectedContactWaterV6Review->SetMaterial(
        0,
        ContactWaterMaterial.Succeeded()
            ? ContactWaterMaterial.Object.Get()
            : Material);
    for (int32 SectionIndex = 0; SectionIndex < 3; ++SectionIndex)
    {
        ConnectedContactWaterV7Review->SetMaterial(
            SectionIndex,
            ContactWaterMaterial.Succeeded()
                ? ContactWaterMaterial.Object.Get()
                : Material);
    }
    for (int32 SectionIndex = 0; SectionIndex < 7; ++SectionIndex)
    {
        ConnectedContactWaterV8Review->SetMaterial(
            SectionIndex,
            ContactWaterMaterial.Succeeded()
                ? ContactWaterMaterial.Object.Get()
                : Material);
    }
    RapidAerosolInstances->SetTranslucentSortPriority(0);
    MistInstances->SetTranslucentSortPriority(1);
    SheetInstances->SetTranslucentSortPriority(2);
    SprayInstances->SetTranslucentSortPriority(3);
    DropletInstances->SetTranslucentSortPriority(4);
}

void ARaftSimWaterVfxActor::BeginPlay()
{
    Super::BeginPlay();
    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        if (URaftSimPhysicsBridgeSubsystem* Bridge =
                GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        {
            WaterAdapter = Bridge->GetWaterRuntime();
        }
    }
    if (UWorld* World = GetWorld())
    {
        if (TActorIterator<ARaftSimRaftActor> It(World); It)
        {
            TrackedRaft = *It;
        }
    }

    auto ConfigureCardMaterial = [this](
        UMeshComponent* Component,
        float Opacity,
        const FLinearColor& Color,
        float Roughness,
        float Emissive)
    {
        if (!Component || !Component->GetMaterial(0))
        {
            return;
        }
        UMaterialInstanceDynamic* Dynamic = UMaterialInstanceDynamic::Create(
            Component->GetMaterial(0), this);
        if (!Dynamic)
        {
            return;
        }
        Dynamic->SetScalarParameterValue(TEXT("VfxOpacity"), Opacity);
        Dynamic->SetVectorParameterValue(TEXT("VfxColor"), Color);
        Dynamic->SetScalarParameterValue(TEXT("VfxRoughness"), Roughness);
        Dynamic->SetScalarParameterValue(TEXT("VfxEmissive"), Emissive);
        Component->SetMaterial(0, Dynamic);
    };
    ConfigureCardMaterial(
        SprayInstances, 0.115f, FLinearColor(0.58f, 0.70f, 0.74f, 1.0f), 0.44f, 0.012f);
    ConfigureCardMaterial(
        MistInstances, 0.032f, FLinearColor(0.50f, 0.61f, 0.64f, 1.0f), 0.72f, 0.010f);
    // River aerosol reads as thin suspended vapour: the faintest population,
    // cool-white, so distant rapids gain atmosphere without a fog wall.
    ConfigureCardMaterial(
        RapidAerosolInstances, 0.024f, FLinearColor(0.56f, 0.64f, 0.68f, 1.0f), 0.78f, 0.007f);
    ConfigureCardMaterial(
        SheetInstances, 0.48f, FLinearColor(0.62f, 0.69f, 0.69f, 1.0f), 0.63f, 0.018f);
    ConfigureCardMaterial(
        DropletInstances, 0.18f, FLinearColor(0.62f, 0.74f, 0.78f, 1.0f), 0.32f, 0.014f);

    // These systems are deliberately loaded after engine/module startup. The
    // VFX directory is an explicit always-cook root, so a failed load means an
    // invalid platform/runtime asset and cleanly retains the deterministic
    // card renderer instead of crashing or silently removing water feedback.
    // The photographic atlas is opt-in and resolves to separately authored
    // packages. Production maps/assets remain byte-identical until a matched
    // renderer review explicitly promotes the candidate.
    const bool bPhotographicV4ReviewRequested = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimPhotographicWaterAtlasV4Review"));
    const bool bPhotographicV5ReviewRequested = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimPhotographicWaterAtlasV5Review"));
    const bool bConnectedContactWaterV6ReviewRequested = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimConnectedContactWaterV6Review"));
    const bool bConnectedContactWaterV7ReviewRequested = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimConnectedContactWaterV7Review"));
    const bool bConnectedContactWaterV8ReviewRequested = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimConnectedContactWaterV8Review"));
    const bool bDepthBearingContactWaterV10ReviewRequested = FParse::Param(
        FCommandLine::Get(),
        TEXT("RaftSimDepthBearingContactWaterV10Review"));
    const bool bDepthBearingContactWaterV10OpaqueDiagnostic = FParse::Param(
        FCommandLine::Get(),
        TEXT("RaftSimDepthBearingContactWaterV10OpaqueDiagnostic"));
    const bool bInvalidPhotographicReviewSelection =
        bPhotographicV4ReviewRequested && bPhotographicV5ReviewRequested;
    const bool bAnyPhotographicReviewRequested =
        bPhotographicV4ReviewRequested || bPhotographicV5ReviewRequested;
    const int32 ConnectedReviewRequestCount =
        (bConnectedContactWaterV6ReviewRequested ? 1 : 0) +
        (bConnectedContactWaterV7ReviewRequested ? 1 : 0) +
        (bConnectedContactWaterV8ReviewRequested ? 1 : 0) +
        (bDepthBearingContactWaterV10ReviewRequested ? 1 : 0);
    const bool bInvalidConnectedReviewSelection =
        ConnectedReviewRequestCount > 1 ||
        (ConnectedReviewRequestCount > 0 && bAnyPhotographicReviewRequested);
    const int32 PhotographicReviewVersion =
        (bInvalidPhotographicReviewSelection ||
         bInvalidConnectedReviewSelection)
        ? 0
        : (bPhotographicV5ReviewRequested
            ? 5
            : (bPhotographicV4ReviewRequested ? 4 : 0));
    if (bInvalidPhotographicReviewSelection)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("RaftSim water VFX: both photographic review switches were supplied; failing closed to production assets"));
    }
    bConnectedContactWaterV6Review =
        bConnectedContactWaterV6ReviewRequested &&
        !bInvalidConnectedReviewSelection;
    bConnectedContactWaterV7Review =
        bConnectedContactWaterV7ReviewRequested &&
        !bInvalidConnectedReviewSelection;
    bConnectedContactWaterV8Review =
        bConnectedContactWaterV8ReviewRequested &&
        !bInvalidConnectedReviewSelection;
    bDepthBearingContactWaterV10Review =
        bDepthBearingContactWaterV10ReviewRequested &&
        !bInvalidConnectedReviewSelection;
    if (bInvalidConnectedReviewSelection)
    {
        if (bConnectedContactWaterV6ReviewRequested &&
            bAnyPhotographicReviewRequested)
        {
            UE_LOG(LogTemp, Warning,
                TEXT("RaftSim water VFX: connected V6 and photographic atlas review switches cannot be combined; failing the connected sheet closed"));
        }
        UE_LOG(LogTemp, Warning,
            TEXT("RaftSim water VFX: connected V6/V7/V8/V10 and photographic review switches are mutually exclusive; failing closed to production"));
    }
    if (bConnectedContactWaterV6Review)
    {
        UMaterialInterface* ConnectedReviewMaterial =
            LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/VFX/Water/ConnectedContactWaterV6Review/"
                     "M_RaftSim_ConnectedContactWater_V6Review."
                     "M_RaftSim_ConnectedContactWater_V6Review"));
        if (ConnectedReviewMaterial)
        {
            ConnectedContactWaterV6Review->SetMaterial(
                0, ConnectedReviewMaterial);
        }
        else
        {
            UE_LOG(
                LogTemp, Error,
                TEXT("RaftSim water VFX: connected V6 review material missing; failing the connected sheet closed"));
            bConnectedContactWaterV6Review = false;
        }
    }
    if (bConnectedContactWaterV7Review)
    {
        // V7 deliberately shares V6's isolated breakup shader while testing a
        // new multi-layer geometry architecture. No production material is
        // changed or used as the experiment's authoring target.
        UMaterialInterface* ConnectedReviewMaterial =
            LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/VFX/Water/ConnectedContactWaterV6Review/"
                     "M_RaftSim_ConnectedContactWater_V6Review."
                     "M_RaftSim_ConnectedContactWater_V6Review"));
        if (ConnectedReviewMaterial)
        {
            for (int32 SectionIndex = 0; SectionIndex < 3; ++SectionIndex)
            {
                ConnectedContactWaterV7Review->SetMaterial(
                    SectionIndex, ConnectedReviewMaterial);
            }
        }
        else
        {
            UE_LOG(
                LogTemp, Error,
                TEXT("RaftSim water VFX: connected V7 review material missing; failing all V7 layers closed"));
            bConnectedContactWaterV7Review = false;
        }
    }
    if (bConnectedContactWaterV8Review)
    {
        // V8 isolates the closed-lobe geometry hypothesis and reuses the
        // existing review-only shader. Production material assets are never
        // selected as an authoring target for this experiment.
        UMaterialInterface* ConnectedReviewMaterial =
            LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/VFX/Water/ConnectedContactWaterV6Review/"
                     "M_RaftSim_ConnectedContactWater_V6Review."
                     "M_RaftSim_ConnectedContactWater_V6Review"));
        if (ConnectedReviewMaterial)
        {
            for (int32 SectionIndex = 0; SectionIndex < 7; ++SectionIndex)
            {
                ConnectedContactWaterV8Review->SetMaterial(
                    SectionIndex, ConnectedReviewMaterial);
            }
        }
        else
        {
            UE_LOG(
                LogTemp, Error,
                TEXT("RaftSim water VFX: connected V8 review material missing; failing all V8 layers closed"));
            bConnectedContactWaterV8Review = false;
        }
    }
    if (bDepthBearingContactWaterV10Review)
    {
        UMaterialInterface* DepthBearingParent =
            LoadObject<UMaterialInterface>(
                nullptr,
                bDepthBearingContactWaterV10OpaqueDiagnostic
                    ? TEXT("/Engine/EngineMaterials/WorldGridMaterial."
                           "WorldGridMaterial")
                    : TEXT("/Game/RaftSim/Materials/"
                           "M_RaftSim_BreakingWaterLip."
                           "M_RaftSim_BreakingWaterLip"));
        UMaterialInstanceDynamic* DepthBearingMaterial =
            DepthBearingParent
                ? UMaterialInstanceDynamic::Create(DepthBearingParent, this)
                : nullptr;
        if (DepthBearingMaterial && DepthBearingContactWaterV10Review)
        {
            // Reuse the production-proven project water shader family, with
            // V10-specific optical density over the cached closed volume.
            // Vertex alpha still restricts pixels to the exposed crest; R/B
            // carry deterministic breakup and aeration for each cached frame.
            DepthBearingMaterial->SetScalarParameterValue(
                TEXT("BreakingWaterOpacity"), 0.035f);
            DepthBearingMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamOpacity"), 0.72f);
            DepthBearingMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamFloor"), 0.72f);
            DepthBearingMaterial->SetScalarParameterValue(
                TEXT("PhotographicBreakupGain"), 0.90f);
            DepthBearingMaterial->SetScalarParameterValue(
                TEXT("PrimaryLaceGain"), 0.70f);
            DepthBearingMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamCoreGain"), 1.00f);
            DepthBearingMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamBaseGain"), 0.60f);
            DepthBearingMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamIntensityGain"), 0.50f);
            DepthBearingMaterial->SetVectorParameterValue(
                TEXT("BreakingWaterColor"),
                FLinearColor(0.11f, 0.28f, 0.32f, 1.0f));
            DepthBearingMaterial->SetVectorParameterValue(
                TEXT("BreakingFoamColor"),
                FLinearColor(0.86f, 0.89f, 0.87f, 1.0f));
            for (int32 SectionIndex = 0;
                 SectionIndex < DepthBearingContactWaterV10FrameCount;
                 ++SectionIndex)
            {
                DepthBearingContactWaterV10Review->SetMaterial(
                    SectionIndex, DepthBearingMaterial);
            }
            bDepthBearingContactWaterV10Review =
                BuildDepthBearingContactWaterV10Cache();
        }
        else
        {
            UE_LOG(
                LogTemp, Error,
                TEXT("RaftSim water VFX: depth-bearing V10 material missing; failing the six-frame volume cache closed"));
            bDepthBearingContactWaterV10Review = false;
        }
    }
    auto LoadWaterSystem = [PhotographicReviewVersion](const TCHAR* BaseName)
        -> UNiagaraSystem*
    {
        const FString AssetName = PhotographicReviewVersion > 0
            ? FString::Printf(
                TEXT("%s_V%dReview"), BaseName, PhotographicReviewVersion)
            : FString(BaseName);
        const FString ObjectPath = PhotographicReviewVersion > 0
            ? FString::Printf(
                TEXT("/Game/RaftSim/VFX/Water/PhotographicSubUVV%dReview/%s.%s"),
                PhotographicReviewVersion,
                *AssetName,
                *AssetName)
            : FString::Printf(
                TEXT("/Game/RaftSim/VFX/Water/%s.%s"),
                *AssetName,
                *AssetName);
        return LoadObject<UNiagaraSystem>(nullptr, *ObjectPath);
    };
    UNiagaraSystem* SolverSpraySystem =
        LoadWaterSystem(TEXT("NS_RaftSim_SolverSpray"));
    UNiagaraSystem* ContactDropletSystem =
        LoadWaterSystem(TEXT("NS_RaftSim_ContactDroplets"));
    UNiagaraSystem* AeratedMistSystem =
        LoadWaterSystem(TEXT("NS_RaftSim_AeratedMist"));
    UNiagaraSystem* RapidAerosolSystem =
        LoadWaterSystem(TEXT("NS_RaftSim_RapidAerosol"));
    UNiagaraSystem* RapidRollerSystem =
        LoadWaterSystem(TEXT("NS_RaftSim_RapidRoller"));
    ConfigureNiagaraComponent(
        SolverSprayNiagara, SolverSpraySystem, 3,
        ContactNiagaraCullDistanceCm);
    ConfigureNiagaraComponent(
        ContactDropletNiagara, ContactDropletSystem, 4,
        ContactNiagaraCullDistanceCm);
    ConfigureNiagaraComponent(
        AeratedMistNiagara, AeratedMistSystem, 1,
        ContactNiagaraCullDistanceCm);
    for (UNiagaraComponent* Component : RapidAerosolNiagara)
    {
        ConfigureNiagaraComponent(
            Component, RapidAerosolSystem, 0,
            RapidNiagaraCullDistanceCm);
    }
    for (UNiagaraComponent* Component : RapidRollerNiagara)
    {
        ConfigureNiagaraComponent(
            Component, RapidRollerSystem, 2,
            RapidNiagaraCullDistanceCm);
    }
    bProductionNiagaraReady = SolverSprayNiagara &&
        SolverSprayNiagara->GetAsset() && ContactDropletNiagara &&
        ContactDropletNiagara->GetAsset() && AeratedMistNiagara &&
        AeratedMistNiagara->GetAsset() && !RapidAerosolNiagara.IsEmpty() &&
        !RapidRollerNiagara.IsEmpty();
    for (const UNiagaraComponent* Component : RapidAerosolNiagara)
    {
        bProductionNiagaraReady = bProductionNiagaraReady &&
            Component && Component->GetAsset();
    }
    for (const UNiagaraComponent* Component : RapidRollerNiagara)
    {
        bProductionNiagaraReady = bProductionNiagaraReady &&
            Component && Component->GetAsset();
    }
    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim Niagara water atlas mode=%s ready=%d components=%d connectedV6=%d connectedV7=%d connectedV8=%d depthV10=%d depthV10Frames=%d"),
        PhotographicReviewVersion == 5
            ? TEXT("photographic_v5_review")
            : (PhotographicReviewVersion == 4
                ? TEXT("photographic_v4_review")
                : TEXT("production")),
        bProductionNiagaraReady ? 1 : 0,
        GetProductionNiagaraComponentCount(),
        bConnectedContactWaterV6Review ? 1 : 0,
        bConnectedContactWaterV7Review ? 1 : 0,
        bConnectedContactWaterV8Review ? 1 : 0,
        bDepthBearingContactWaterV10Review ? 1 : 0,
        DepthBearingContactWaterV10FrameTriangleCounts.Num());
    // The exact card populations continue to update for deterministic tests
    // and unsupported hardware, but never double-render over Niagara.
    for (UInstancedStaticMeshComponent* CardPool : {
             SprayInstances.Get(), MistInstances.Get(), SheetInstances.Get(),
             DropletInstances.Get(), RapidAerosolInstances.Get()})
    {
        CardPool->SetVisibility(!bProductionNiagaraReady, true);
    }
    if (ContactWaterPatch && ContactWaterPatch->GetMaterial(0))
    {
        UMaterialInterface* ContactParent = ContactWaterPatch->GetMaterial(0);
        UMaterialInstanceDynamic* ContactMaterial =
            UMaterialInstanceDynamic::Create(ContactParent, this);
        if (ContactMaterial)
        {
            ContactWaterPatch->SetMaterial(0, ContactMaterial);
            if (ContactParent->GetPathName().Contains(
                    TEXT("M_RaftSim_BreakingWaterLip")))
            {
                // The continuous patch uses the same project-owned flow-lace
                // family as live breaking water, at lower optical depth and
                // core energy. This removes the crossed card-shader quilt
                // while retaining solver/contact-only presentation authority.
                ContactMaterial->SetScalarParameterValue(
                    TEXT("BreakingWaterOpacity"), 0.020f);
                ContactMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamOpacity"), 0.58f);
                ContactMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamFloor"), 0.02f);
                ContactMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamIntensityGain"), 0.42f);
                ContactMaterial->SetScalarParameterValue(
                    TEXT("PrimaryLaceGain"), 0.48f);
                ContactMaterial->SetScalarParameterValue(
                    TEXT("DetailLaceGain"), 0.28f);
                ContactMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamCoreGain"), 0.62f);
                ContactMaterial->SetScalarParameterValue(
                    TEXT("BreakingWaterRoughness"), 0.18f);
                ContactMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamRoughness"), 0.76f);
                ContactMaterial->SetScalarParameterValue(
                    TEXT("BreakingWaterSpecular"), 0.28f);
                ContactMaterial->SetVectorParameterValue(
                    TEXT("BreakingWaterColor"),
                    FLinearColor(0.10f, 0.22f, 0.27f, 1.0f));
                ContactMaterial->SetVectorParameterValue(
                    TEXT("BreakingFoamColor"),
                    FLinearColor(0.60f, 0.67f, 0.67f, 1.0f));
            }
            else
            {
                ContactMaterial->SetScalarParameterValue(TEXT("VfxOpacity"), 0.16f);
                ContactMaterial->SetVectorParameterValue(
                    TEXT("VfxColor"), FLinearColor(0.56f, 0.67f, 0.69f, 1.0f));
                ContactMaterial->SetScalarParameterValue(TEXT("VfxRoughness"), 0.66f);
                ContactMaterial->SetScalarParameterValue(TEXT("VfxEmissive"), 0.010f);
            }
        }
    }
    if (ConnectedContactWaterV6Review &&
        ConnectedContactWaterV6Review->GetMaterial(0))
    {
        UMaterialInterface* ConnectedParent =
            ConnectedContactWaterV6Review->GetMaterial(0);
        UMaterialInstanceDynamic* ConnectedMaterial =
            UMaterialInstanceDynamic::Create(ConnectedParent, this);
        if (ConnectedMaterial)
        {
            ConnectedContactWaterV6Review->SetMaterial(0, ConnectedMaterial);
            // The review-only material uses photographic breakup over this
            // solver-shaped sheet. Keep a faint connected water body beneath
            // the breakup so its coverage does not collapse back into a tuft.
            ConnectedMaterial->SetScalarParameterValue(
                TEXT("BreakingWaterOpacity"), 0.075f);
            ConnectedMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamOpacity"), 0.78f);
            ConnectedMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamFloor"), 0.055f);
            ConnectedMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamIntensityGain"), 0.50f);
            ConnectedMaterial->SetScalarParameterValue(
                TEXT("PrimaryLaceGain"), 0.42f);
            ConnectedMaterial->SetScalarParameterValue(
                TEXT("DetailLaceGain"), 0.0f);
            ConnectedMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamCoreGain"), 0.65f);
            ConnectedMaterial->SetScalarParameterValue(
                TEXT("BreakingWaterRoughness"), 0.16f);
            ConnectedMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamRoughness"), 0.72f);
            ConnectedMaterial->SetScalarParameterValue(
                TEXT("BreakingWaterSpecular"), 0.34f);
            ConnectedMaterial->SetVectorParameterValue(
                TEXT("BreakingWaterColor"),
                FLinearColor(0.10f, 0.24f, 0.29f, 1.0f));
            ConnectedMaterial->SetVectorParameterValue(
                TEXT("BreakingFoamColor"),
                FLinearColor(0.69f, 0.76f, 0.77f, 1.0f));
        }
    }
    if (bConnectedContactWaterV7Review && ConnectedContactWaterV7Review)
    {
        auto ConfigureV7Layer = [this](
            int32 SectionIndex,
            float WaterOpacity,
            float FoamOpacity,
            float FoamFloor,
            float PhotoGain,
            float LaceGain,
            float CoreGain,
            float WaterRoughness,
            float FoamRoughness,
            float Specular,
            const FLinearColor& WaterColor,
            const FLinearColor& FoamColor)
        {
            UMaterialInterface* Parent =
                ConnectedContactWaterV7Review->GetMaterial(SectionIndex);
            UMaterialInstanceDynamic* LayerMaterial = Parent
                ? UMaterialInstanceDynamic::Create(Parent, this)
                : nullptr;
            if (!LayerMaterial)
            {
                return;
            }
            ConnectedContactWaterV7Review->SetMaterial(
                SectionIndex, LayerMaterial);
            LayerMaterial->SetScalarParameterValue(
                TEXT("BreakingWaterOpacity"), WaterOpacity);
            LayerMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamOpacity"), FoamOpacity);
            LayerMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamFloor"), FoamFloor);
            LayerMaterial->SetScalarParameterValue(
                TEXT("PhotographicBreakupGain"), PhotoGain);
            LayerMaterial->SetScalarParameterValue(
                TEXT("PrimaryLaceGain"), LaceGain);
            LayerMaterial->SetScalarParameterValue(
                TEXT("DetailLaceGain"), 0.0f);
            LayerMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamCoreGain"), CoreGain);
            LayerMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamIntensityGain"), 0.42f);
            LayerMaterial->SetScalarParameterValue(
                TEXT("BreakingWaterRoughness"), WaterRoughness);
            LayerMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamRoughness"), FoamRoughness);
            LayerMaterial->SetScalarParameterValue(
                TEXT("BreakingWaterSpecular"), Specular);
            LayerMaterial->SetVectorParameterValue(
                TEXT("BreakingWaterColor"), WaterColor);
            LayerMaterial->SetVectorParameterValue(
                TEXT("BreakingFoamColor"), FoamColor);
        };

        // Layer 0 is a horizontal, mask-independent attachment body. Layer 1
        // carries the solver-contoured aerated crest. Layer 2 supplies two
        // smaller photographic breakup lobes. Independent optical budgets
        // prevent one mask from turning the whole contact into a wall or tuft.
        ConfigureV7Layer(
            0, 0.14f, 0.16f, 0.06f, 0.0f, 0.28f, 0.18f,
            0.12f, 0.70f, 0.42f,
            FLinearColor(0.075f, 0.205f, 0.255f, 1.0f),
            FLinearColor(0.57f, 0.65f, 0.66f, 1.0f));
        ConfigureV7Layer(
            1, 0.040f, 0.80f, 0.10f, 0.0f, 0.82f, 1.00f,
            0.16f, 0.76f, 0.32f,
            FLinearColor(0.09f, 0.225f, 0.275f, 1.0f),
            FLinearColor(0.75f, 0.80f, 0.80f, 1.0f));
        ConfigureV7Layer(
            2, 0.008f, 0.86f, 0.060f, 0.32f, 0.62f, 1.00f,
            0.18f, 0.79f, 0.28f,
            FLinearColor(0.10f, 0.235f, 0.285f, 1.0f),
            FLinearColor(0.79f, 0.83f, 0.83f, 1.0f));
    }
    if (bConnectedContactWaterV8Review && ConnectedContactWaterV8Review)
    {
        auto ConfigureV8Section = [this](
            int32 SectionIndex,
            float WaterOpacity,
            float FoamOpacity,
            float FoamFloor,
            float PhotoGain,
            float LaceGain,
            float CoreGain)
        {
            UMaterialInterface* Parent =
                ConnectedContactWaterV8Review->GetMaterial(SectionIndex);
            UMaterialInstanceDynamic* SectionMaterial = Parent
                ? UMaterialInstanceDynamic::Create(Parent, this)
                : nullptr;
            if (!SectionMaterial)
            {
                return;
            }
            ConnectedContactWaterV8Review->SetMaterial(
                SectionIndex, SectionMaterial);
            SectionMaterial->SetScalarParameterValue(
                TEXT("BreakingWaterOpacity"), WaterOpacity);
            SectionMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamOpacity"), FoamOpacity);
            SectionMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamFloor"), FoamFloor);
            SectionMaterial->SetScalarParameterValue(
                TEXT("PhotographicBreakupGain"), PhotoGain);
            SectionMaterial->SetScalarParameterValue(
                TEXT("PrimaryLaceGain"), LaceGain);
            SectionMaterial->SetScalarParameterValue(
                TEXT("DetailLaceGain"), 0.0f);
            SectionMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamCoreGain"), CoreGain);
            SectionMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamIntensityGain"), 0.36f);
            SectionMaterial->SetScalarParameterValue(
                TEXT("BreakingWaterRoughness"), 0.18f);
            SectionMaterial->SetScalarParameterValue(
                TEXT("BreakingFoamRoughness"), 0.82f);
            SectionMaterial->SetScalarParameterValue(
                TEXT("BreakingWaterSpecular"), 0.25f);
            SectionMaterial->SetVectorParameterValue(
                TEXT("BreakingWaterColor"),
                FLinearColor(0.07f, 0.19f, 0.24f, 1.0f));
            SectionMaterial->SetVectorParameterValue(
                TEXT("BreakingFoamColor"),
                FLinearColor(0.74f, 0.79f, 0.79f, 1.0f));
        };

        // The sampled horizontal attachment stays optically quiet. Six
        // separate closed bodies carry aeration with lower opacity and no
        // broad shared crest surface, preventing one sheet-like silhouette.
        ConfigureV8Section(0, 0.10f, 0.13f, 0.04f, 0.0f, 0.20f, 0.12f);
        for (int32 SectionIndex = 1; SectionIndex < 7; ++SectionIndex)
        {
            ConfigureV8Section(
                SectionIndex, 0.028f, 0.38f, 0.015f,
                0.22f, 0.30f, 0.42f);
        }
    }
}

float ARaftSimWaterVfxActor::GetUnderwaterBlendWeight() const
{
    return UnderwaterPostProcess ? UnderwaterPostProcess->BlendWeight : 0.0f;
}

int32 ARaftSimWaterVfxActor::GetSprayInstanceCount() const
{
    return SprayInstances ? SprayInstances->GetInstanceCount() : 0;
}

int32 ARaftSimWaterVfxActor::GetMistInstanceCount() const
{
    return MistInstances ? MistInstances->GetInstanceCount() : 0;
}

int32 ARaftSimWaterVfxActor::GetImpactFoamInstanceCount() const
{
    return SheetInstances ? SheetInstances->GetInstanceCount() : 0;
}

int32 ARaftSimWaterVfxActor::GetDropletInstanceCount() const
{
    return DropletInstances ? DropletInstances->GetInstanceCount() : 0;
}

int32 ARaftSimWaterVfxActor::GetRapidAerosolInstanceCount() const
{
    return RapidAerosolInstances ? RapidAerosolInstances->GetInstanceCount() : 0;
}

int32 ARaftSimWaterVfxActor::GetProductionNiagaraComponentCount() const
{
    int32 Count = SolverSprayNiagara && SolverSprayNiagara->GetAsset() ? 1 : 0;
    Count += ContactDropletNiagara && ContactDropletNiagara->GetAsset() ? 1 : 0;
    Count += AeratedMistNiagara && AeratedMistNiagara->GetAsset() ? 1 : 0;
    for (const UNiagaraComponent* Component : RapidAerosolNiagara)
    {
        Count += Component && Component->GetAsset() ? 1 : 0;
    }
    for (const UNiagaraComponent* Component : RapidRollerNiagara)
    {
        Count += Component && Component->GetAsset() ? 1 : 0;
    }
    return Count;
}

bool ARaftSimWaterVfxActor::IsContactWaterPatchVisible() const
{
    return ContactWaterPatch && ContactWaterPatch->IsVisible() &&
        ContactWaterPatchTriangleCount > 0;
}

bool ARaftSimWaterVfxActor::IsConnectedContactWaterV6Visible() const
{
    return ConnectedContactWaterV6Review &&
        ConnectedContactWaterV6Review->IsVisible() &&
        ConnectedContactWaterV6TriangleCount > 0;
}

bool ARaftSimWaterVfxActor::IsConnectedContactWaterV7Visible() const
{
    return ConnectedContactWaterV7Review &&
        ConnectedContactWaterV7Review->IsVisible() &&
        ConnectedContactWaterV7TriangleCount > 0;
}

bool ARaftSimWaterVfxActor::IsConnectedContactWaterV8Visible() const
{
    return ConnectedContactWaterV8Review &&
        ConnectedContactWaterV8Review->IsVisible() &&
        ConnectedContactWaterV8TriangleCount > 0;
}

bool ARaftSimWaterVfxActor::IsDepthBearingContactWaterV10Visible() const
{
    return DepthBearingContactWaterV10Review &&
        DepthBearingContactWaterV10Review->IsVisible() &&
        DepthBearingContactWaterV10TriangleCount > 0 &&
        DepthBearingContactWaterV10CurrentFrame >= 0;
}

FRaftSimWaterVfxState ARaftSimWaterVfxActor::EvaluatePresentation(
    const FRaftSimWaterSample& Sample,
    const FVector& RaftVelocityMps,
    int32 ContactCount,
    float MaximumIndentationM,
    bool bCameraUnderwater)
{
    FRaftSimWaterVfxState Result;
    if (!Sample.bWet)
    {
        Result.Underwater = bCameraUnderwater ? 1.0f : 0.0f;
        return Result;
    }

    const float DepthM = FMath::Max(Sample.DepthMeters, 0.05f);
    const float WaterSpeedMps = Sample.VelocityMetersPerSecond.Size2D();
    const float Froude = WaterSpeedMps / FMath::Sqrt(GravityMps2 * DepthM);
    const float HydraulicAeration = FMath::Clamp((Froude - 0.72f) / 1.05f, 0.0f, 1.0f);
    const float RelativeImpact = FMath::Clamp(
        (Sample.VelocityMetersPerSecond - RaftVelocityMps).Size() / 6.5f,
        0.0f, 1.0f);
    const float Contact = FMath::Clamp(
        static_cast<float>(ContactCount) / 5.0f + MaximumIndentationM / 0.22f,
        0.0f, 1.0f);

    Result.Spray = FMath::Clamp(
        HydraulicAeration * 0.72f + RelativeImpact * 0.42f + Contact * 0.66f,
        0.0f, 1.0f);
    Result.Mist = FMath::Clamp(
        HydraulicAeration * 0.64f + Result.Spray * 0.24f,
        0.0f, 1.0f);
    Result.ImpactSheet = FMath::Clamp(
        RelativeImpact * 0.46f + Contact * 0.86f,
        0.0f, 1.0f);
    Result.Droplets = FMath::Clamp(
        Result.Spray * 0.74f + Result.ImpactSheet * 0.48f,
        0.0f, 1.0f);
    Result.Underwater = bCameraUnderwater ? 1.0f : 0.0f;
    return Result;
}

bool ARaftSimWaterVfxActor::SampleCameraUnderwater() const
{
    const UWorld* World = GetWorld();
    if (!World || !WaterAdapter)
    {
        return false;
    }
    const APlayerController* Controller = World->GetFirstPlayerController();
    const APlayerCameraManager* Camera = Controller ? Controller->PlayerCameraManager : nullptr;
    if (!Camera)
    {
        return false;
    }
    FRaftSimWaterSample CameraSample;
    const FVector CameraLocation = Camera->GetCameraLocation();
    return WaterAdapter->SampleWaterAtWorldPosition(CameraLocation, CameraSample) &&
        CameraSample.bWet &&
        CameraLocation.Z < CameraSample.SurfaceHeightMeters * CmPerM - 4.0f;
}

void ARaftSimWaterVfxActor::ClearInstances()
{
    SprayInstances->ClearInstances();
    MistInstances->ClearInstances();
    SheetInstances->ClearInstances();
    DropletInstances->ClearInstances();
}

void ARaftSimWaterVfxActor::HideContactWaterPatch()
{
    ContactWaterPatchTriangleCount = 0;
    if (ContactWaterPatch)
    {
        ContactWaterPatch->SetVisibility(false, true);
    }
}

void ARaftSimWaterVfxActor::HideConnectedContactWaterV6Review()
{
    ConnectedContactWaterV6TriangleCount = 0;
    if (ConnectedContactWaterV6Review)
    {
        ConnectedContactWaterV6Review->SetVisibility(false, true);
    }
}

void ARaftSimWaterVfxActor::HideConnectedContactWaterV7Review()
{
    ConnectedContactWaterV7TriangleCount = 0;
    if (ConnectedContactWaterV7Review)
    {
        ConnectedContactWaterV7Review->SetVisibility(false, true);
    }
}

void ARaftSimWaterVfxActor::HideConnectedContactWaterV8Review()
{
    ConnectedContactWaterV8TriangleCount = 0;
    if (ConnectedContactWaterV8Review)
    {
        ConnectedContactWaterV8Review->SetVisibility(false, true);
    }
}

void ARaftSimWaterVfxActor::HideDepthBearingContactWaterV10Review()
{
    DepthBearingContactWaterV10TriangleCount = 0;
    DepthBearingContactWaterV10CurrentFrame = -1;
    if (!DepthBearingContactWaterV10Review)
    {
        return;
    }
    for (int32 SectionIndex = 0;
         SectionIndex < DepthBearingContactWaterV10FrameCount;
         ++SectionIndex)
    {
        DepthBearingContactWaterV10Review->SetMeshSectionVisible(
            SectionIndex, false);
    }
    DepthBearingContactWaterV10Review->SetVisibility(false, true);
}

bool ARaftSimWaterVfxActor::BuildDepthBearingContactWaterV10Cache()
{
    if (!DepthBearingContactWaterV10Review)
    {
        return false;
    }

    // V10 is a deterministic, project-authored implicit-volume mesh cache.
    // Each frame is built once through marching tetrahedra and kept as a
    // separate render section. Runtime animation only toggles sections; it
    // never rebuilds geometry, reads a third-party template, or mutates any
    // solver/collision state. Local +X follows the contact escape direction,
    // +Y spans the flow, and Z is true depth above/below the sampled surface.
    constexpr int32 GridX = 37;
    constexpr int32 GridY = 29;
    constexpr int32 GridZ = 26;
    const FVector GridMinM(-2.48f, -1.38f, -0.70f);
    const FVector GridMaxM(2.48f, 1.38f, 0.78f);
    const FVector GridStepM(
        (GridMaxM.X - GridMinM.X) / static_cast<float>(GridX - 1),
        (GridMaxM.Y - GridMinM.Y) / static_cast<float>(GridY - 1),
        (GridMaxM.Z - GridMinM.Z) / static_cast<float>(GridZ - 1));
    const int32 CubeCorners[8][3] = {
        {0, 0, 0}, {1, 0, 0}, {1, 1, 0}, {0, 1, 0},
        {0, 0, 1}, {1, 0, 1}, {1, 1, 1}, {0, 1, 1}};
    const int32 Tetrahedra[6][4] = {
        {0, 5, 1, 6}, {0, 1, 2, 6}, {0, 2, 3, 6},
        {0, 3, 7, 6}, {0, 7, 4, 6}, {0, 4, 5, 6}};
    const int32 GridPointCount = GridX * GridY * GridZ;
    auto GridIndex = [=](int32 X, int32 Y, int32 Z)
    {
        return (Z * GridY + Y) * GridX + X;
    };

    DepthBearingContactWaterV10Review->ClearAllMeshSections();
    DepthBearingContactWaterV10FrameTriangleCounts.Reset(
        DepthBearingContactWaterV10FrameCount);
    float MinimumGeneratedZCm = TNumericLimits<float>::Max();
    float MaximumGeneratedZCm = TNumericLimits<float>::Lowest();

    for (int32 FrameIndex = 0;
         FrameIndex < DepthBearingContactWaterV10FrameCount;
         ++FrameIndex)
    {
        const float Phase =
            2.0f * PI * static_cast<float>(FrameIndex) /
            static_cast<float>(DepthBearingContactWaterV10FrameCount);
        TArray<FVector> GridPositionsM;
        TArray<float> GridValues;
        GridPositionsM.SetNumUninitialized(GridPointCount);
        GridValues.SetNumUninitialized(GridPointCount);
        for (int32 Z = 0; Z < GridZ; ++Z)
        {
            for (int32 Y = 0; Y < GridY; ++Y)
            {
                for (int32 X = 0; X < GridX; ++X)
                {
                    const int32 Index = GridIndex(X, Y, Z);
                    const FVector PositionM = GridMinM + FVector(
                        GridStepM.X * X,
                        GridStepM.Y * Y,
                        GridStepM.Z * Z);
                    GridPositionsM[Index] = PositionM;
                    GridValues[Index] =
                        EvaluateDepthBearingContactWaterV10Field(
                            PositionM, Phase);
                }
            }
        }

        TArray<FVector> Vertices;
        TArray<int32> Triangles;
        TArray<FVector> Normals;
        TArray<FVector2D> Uvs;
        TArray<FLinearColor> Colors;
        TArray<FProcMeshTangent> Tangents;
        float MaximumClosedVolumeCoverage = 0.0f;
        int32 CoveredVertexCount = 0;
        Vertices.Reserve(18000);
        Triangles.Reserve(18000);
        Normals.Reserve(18000);
        Uvs.Reserve(18000);
        Colors.Reserve(18000);
        Tangents.Reserve(18000);

        auto InterpolateIsoPoint = [](
            const FVector& A,
            float AValue,
            const FVector& B,
            float BValue)
        {
            const float Denominator = AValue - BValue;
            const float T = FMath::Abs(Denominator) > SMALL_NUMBER
                ? FMath::Clamp(AValue / Denominator, 0.0f, 1.0f)
                : 0.5f;
            return FMath::Lerp(A, B, T);
        };
        auto AppendTriangle = [&](FVector P0M, FVector P1M, FVector P2M)
        {
            FVector N0 = EvaluateDepthBearingContactWaterV10OutwardNormal(
                P0M, Phase);
            FVector N1 = EvaluateDepthBearingContactWaterV10OutwardNormal(
                P1M, Phase);
            FVector N2 = EvaluateDepthBearingContactWaterV10OutwardNormal(
                P2M, Phase);
            const FVector GeometricNormal = FVector::CrossProduct(
                P1M - P0M, P2M - P0M);
            // Unreal renders clockwise front faces in its left-handed world.
            // Keep shading normals outward, but wind the geometric cross in
            // the opposite direction so the near outer shell renders and the
            // far internal shell is culled by the one-sided water material.
            if (FVector::DotProduct(
                    GeometricNormal, N0 + N1 + N2) > 0.0f)
            {
                Swap(P1M, P2M);
                Swap(N1, N2);
            }
            const FVector PointsM[3] = {P0M, P1M, P2M};
            const FVector PointNormals[3] = {N0, N1, N2};
            for (int32 Corner = 0; Corner < 3; ++Corner)
            {
                const FVector& PointM = PointsM[Corner];
                const FVector& Normal = PointNormals[Corner];
                const int32 VertexIndex = Vertices.Add(PointM * CmPerM);
                Triangles.Add(VertexIndex);
                Normals.Add(Normal);
                Uvs.Add(FVector2D(
                    (PointM.X - GridMinM.X) /
                        (GridMaxM.X - GridMinM.X),
                    (PointM.Y - GridMinM.Y) /
                        (GridMaxM.Y - GridMinM.Y)));
                const float HeightWeight = FMath::Clamp(
                    (PointM.Z + 0.05f) / 0.95f, 0.0f, 1.0f);
                const float SlopeWeight = FMath::Clamp(
                    1.0f - FMath::Abs(Normal.Z), 0.0f, 1.0f);
                const float PhaseBreakup = 0.5f + 0.5f * FMath::Sin(
                    PointM.X * 5.2f - PointM.Y * 4.4f + Phase * 2.0f);
                const float CoverageBreakup = FMath::Clamp(
                    0.50f +
                    0.25f * FMath::Sin(
                        PointM.X * 13.7f + PointM.Y * 7.9f - Phase * 2.3f) +
                    0.25f * FMath::Sin(
                        PointM.X * 6.1f - PointM.Y * 16.3f + Phase * 3.1f),
                    0.0f, 1.0f);
                const float Aeration = FMath::Clamp(
                    0.02f + 0.24f * SlopeWeight +
                    0.18f * HeightWeight + 0.06f * PhaseBreakup,
                    0.0f, 1.0f);
                // Translucent sorting cannot use the authored river as a
                // depth mask. Keep the mesh physically closed, but allow
                // only its above-surface, upward-facing crest to contribute
                // pixels; submerged sides and the keel remain evidence of
                // volume, never a pale dome drawn over the river.
                const float AboveSurfaceCoverage = FMath::Clamp(
                    (PointM.Z + 0.04f) / 0.22f, 0.0f, 1.0f);
                const float UpwardFacingCoverage = FMath::Clamp(
                    (Normal.Z - 0.05f) / 0.35f, 0.0f, 1.0f);
                const float ClosedVolumeCoverage =
                    AboveSurfaceCoverage * UpwardFacingCoverage;
                const float VisibleCoverage = ClosedVolumeCoverage *
                    FMath::Lerp(0.40f, 1.0f, CoverageBreakup);
                MaximumClosedVolumeCoverage = FMath::Max(
                    MaximumClosedVolumeCoverage, ClosedVolumeCoverage);
                CoveredVertexCount += ClosedVolumeCoverage >= 0.05f ? 1 : 0;
                Colors.Add(FLinearColor(
                    CoverageBreakup,
                    HeightWeight,
                    Aeration,
                    VisibleCoverage));
                Tangents.Add(FProcMeshTangent(FVector::ForwardVector, false));
                MinimumGeneratedZCm = FMath::Min(
                    MinimumGeneratedZCm, PointM.Z * CmPerM);
                MaximumGeneratedZCm = FMath::Max(
                    MaximumGeneratedZCm, PointM.Z * CmPerM);
            }
        };

        for (int32 Z = 0; Z < GridZ - 1; ++Z)
        {
            for (int32 Y = 0; Y < GridY - 1; ++Y)
            {
                for (int32 X = 0; X < GridX - 1; ++X)
                {
                    FVector CornerPositionsM[8];
                    float CornerValues[8];
                    for (int32 Corner = 0; Corner < 8; ++Corner)
                    {
                        const int32 Index = GridIndex(
                            X + CubeCorners[Corner][0],
                            Y + CubeCorners[Corner][1],
                            Z + CubeCorners[Corner][2]);
                        CornerPositionsM[Corner] = GridPositionsM[Index];
                        CornerValues[Corner] = GridValues[Index];
                    }
                    for (const int32* Tetrahedron : Tetrahedra)
                    {
                        int32 Inside[4];
                        int32 Outside[4];
                        int32 InsideCount = 0;
                        int32 OutsideCount = 0;
                        for (int32 Corner = 0; Corner < 4; ++Corner)
                        {
                            const int32 CubeCorner = Tetrahedron[Corner];
                            if (CornerValues[CubeCorner] >= 0.0f)
                            {
                                Inside[InsideCount++] = CubeCorner;
                            }
                            else
                            {
                                Outside[OutsideCount++] = CubeCorner;
                            }
                        }
                        if (InsideCount == 0 || InsideCount == 4)
                        {
                            continue;
                        }
                        auto EdgePoint = [&](int32 A, int32 B)
                        {
                            return InterpolateIsoPoint(
                                CornerPositionsM[A], CornerValues[A],
                                CornerPositionsM[B], CornerValues[B]);
                        };
                        if (InsideCount == 1)
                        {
                            AppendTriangle(
                                EdgePoint(Inside[0], Outside[0]),
                                EdgePoint(Inside[0], Outside[1]),
                                EdgePoint(Inside[0], Outside[2]));
                        }
                        else if (InsideCount == 3)
                        {
                            AppendTriangle(
                                EdgePoint(Outside[0], Inside[0]),
                                EdgePoint(Outside[0], Inside[1]),
                                EdgePoint(Outside[0], Inside[2]));
                        }
                        else
                        {
                            const FVector P00 = EdgePoint(
                                Inside[0], Outside[0]);
                            const FVector P01 = EdgePoint(
                                Inside[0], Outside[1]);
                            const FVector P10 = EdgePoint(
                                Inside[1], Outside[0]);
                            const FVector P11 = EdgePoint(
                                Inside[1], Outside[1]);
                            AppendTriangle(P00, P10, P11);
                            AppendTriangle(P00, P11, P01);
                        }
                    }
                }
            }
        }

        const int32 TriangleCount = Triangles.Num() / 3;
        if (TriangleCount <= 0)
        {
            UE_LOG(
                LogTemp, Error,
                TEXT("RaftSim water VFX: depth-bearing V10 frame %d generated no triangles"),
                FrameIndex);
            DepthBearingContactWaterV10Review->ClearAllMeshSections();
            DepthBearingContactWaterV10FrameTriangleCounts.Reset();
            DepthBearingContactWaterV10DepthCm = 0.0f;
            return false;
        }
        DepthBearingContactWaterV10Review->CreateMeshSection_LinearColor(
            FrameIndex, Vertices, Triangles, Normals, Uvs, Colors,
            Tangents, false);
        DepthBearingContactWaterV10Review->SetMeshSectionVisible(
            FrameIndex, false);
        DepthBearingContactWaterV10FrameTriangleCounts.Add(TriangleCount);
        UE_LOG(
            LogTemp, Display,
            TEXT("RaftSim water VFX: depth-bearing V10 frame=%d maxCoverage=%.3f coveredVertices=%d totalVertices=%d"),
            FrameIndex,
            MaximumClosedVolumeCoverage,
            CoveredVertexCount,
            Vertices.Num());
    }

    DepthBearingContactWaterV10DepthCm =
        MaximumGeneratedZCm - MinimumGeneratedZCm;
    HideDepthBearingContactWaterV10Review();
    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim water VFX: depth-bearing V10 cache built frames=%d depthCm=%.2f triangles=%s"),
        DepthBearingContactWaterV10FrameTriangleCounts.Num(),
        DepthBearingContactWaterV10DepthCm,
        *FString::JoinBy(
            DepthBearingContactWaterV10FrameTriangleCounts,
            TEXT(","),
            [](int32 Count) { return FString::FromInt(Count); }));
    return
        DepthBearingContactWaterV10FrameTriangleCounts.Num() ==
            DepthBearingContactWaterV10FrameCount &&
        DepthBearingContactWaterV10DepthCm >= 100.0f;
}

void ARaftSimWaterVfxActor::UpdateContactWaterPatch(
    const FVector& SurfaceCenterCm,
    const FVector& FlowDirection,
    const FVector& AcrossDirection,
    float ImpactEnergy,
    float ContactScale)
{
    if (!ContactWaterPatch || !WaterAdapter)
    {
        HideContactWaterPatch();
        return;
    }

    // A 9 x 7 grid resolves a 2.2 x 1.4 m contact shoulder at roughly 25 cm.
    // It is presentation-only: every base vertex samples the authoritative
    // live free surface, has no collision, and fades back to that surface at
    // all four edges. D4 supplies only the bounded aerated pile-up amplitude.
    constexpr int32 LongitudinalVertexCount = 9;
    constexpr int32 LateralVertexCount = 7;
    constexpr int32 VertexCount = LongitudinalVertexCount * LateralVertexCount;
    const float HalfLengthCm = 110.0f * ContactScale;
    const float HalfWidthCm = 70.0f * ContactScale;
    const float Strength = FMath::Clamp(ImpactEnergy * ContactScale, 0.0f, 1.2f);

    TArray<FVector> PatchVertices;
    TArray<FVector2D> PatchUvs;
    TArray<FLinearColor> PatchColors;
    TArray<FVector> PatchNormals;
    TArray<FProcMeshTangent> PatchTangents;
    PatchVertices.SetNumUninitialized(VertexCount);
    PatchUvs.SetNumUninitialized(VertexCount);
    PatchColors.SetNumUninitialized(VertexCount);
    PatchNormals.Init(FVector::UpVector, VertexCount);
    PatchTangents.Init(FProcMeshTangent(FlowDirection, false), VertexCount);

    const FTransform ActorTransform = GetActorTransform();
    for (int32 LateralIndex = 0; LateralIndex < LateralVertexCount; ++LateralIndex)
    {
        const float V = static_cast<float>(LateralIndex) /
            static_cast<float>(LateralVertexCount - 1);
        const float AcrossUnit = V * 2.0f - 1.0f;
        for (int32 LongitudinalIndex = 0;
             LongitudinalIndex < LongitudinalVertexCount;
             ++LongitudinalIndex)
        {
            const float U = static_cast<float>(LongitudinalIndex) /
                static_cast<float>(LongitudinalVertexCount - 1);
            const float FlowUnit = U * 2.0f - 1.0f;
            const int32 Index =
                LateralIndex * LongitudinalVertexCount + LongitudinalIndex;
            FVector WorldPosition = SurfaceCenterCm +
                FlowDirection * (FlowUnit * HalfLengthCm) +
                AcrossDirection * (AcrossUnit * HalfWidthCm);

            FRaftSimWaterSample VertexSample;
            if (WaterAdapter->SampleWaterAtWorldPosition(WorldPosition, VertexSample) &&
                VertexSample.bWet)
            {
                WorldPosition.Z = VertexSample.SurfaceHeightMeters * CmPerM + 5.0f;
            }
            else
            {
                WorldPosition.Z = SurfaceCenterCm.Z - 3.0f;
            }

            const float EdgeFeather = FMath::Max(
                0.0f,
                FMath::Sin(PI * U) * FMath::Sin(PI * V));
            const float Shoulder = FMath::Exp(
                -5.2f * FMath::Square(FlowUnit + 0.18f) -
                4.4f * FMath::Square(AcrossUnit));
            const float DownstreamTongue = FMath::Exp(
                -3.4f * FMath::Square(FlowUnit - 0.34f) -
                5.0f * FMath::Square(AcrossUnit));
            const float DownstreamTrough = FMath::Exp(
                -8.0f * FMath::Square(FlowUnit - 0.68f) -
                4.0f * FMath::Square(AcrossUnit));
            const float SurfaceFlutter = FMath::Sin(
                SimulationPhase * 5.1f + FlowUnit * 7.0f + AcrossUnit * 3.5f);
            const float DisplacementCm = EdgeFeather * Strength * (
                (18.0f + 12.0f * Strength) * Shoulder +
                6.0f * DownstreamTongue -
                3.5f * DownstreamTrough +
                2.0f * SurfaceFlutter * Shoulder);
            WorldPosition.Z += DisplacementCm;

            PatchVertices[Index] = ActorTransform.InverseTransformPosition(WorldPosition);
            PatchUvs[Index] = FVector2D(U, V);
            const float AeratedCore = FMath::Clamp(
                0.14f + Shoulder * 0.86f + DownstreamTongue * 0.38f,
                0.0f,
                1.0f);
            PatchColors[Index] = FLinearColor(
                FMath::Clamp(0.42f + Strength * 0.34f, 0.0f, 1.0f),
                0.20f,
                AeratedCore,
                FMath::Pow(EdgeFeather, 1.65f) * AeratedCore *
                    FMath::Clamp(0.42f + Strength * 0.38f, 0.0f, 1.0f));
        }
    }

    for (int32 LateralIndex = 0; LateralIndex < LateralVertexCount; ++LateralIndex)
    {
        for (int32 LongitudinalIndex = 0;
             LongitudinalIndex < LongitudinalVertexCount;
             ++LongitudinalIndex)
        {
            const int32 PreviousLongitudinal = FMath::Max(LongitudinalIndex - 1, 0);
            const int32 NextLongitudinal = FMath::Min(
                LongitudinalIndex + 1, LongitudinalVertexCount - 1);
            const int32 PreviousLateral = FMath::Max(LateralIndex - 1, 0);
            const int32 NextLateral = FMath::Min(
                LateralIndex + 1, LateralVertexCount - 1);
            const FVector LongitudinalTangent =
                PatchVertices[LateralIndex * LongitudinalVertexCount + NextLongitudinal] -
                PatchVertices[LateralIndex * LongitudinalVertexCount + PreviousLongitudinal];
            const FVector LateralTangent =
                PatchVertices[NextLateral * LongitudinalVertexCount + LongitudinalIndex] -
                PatchVertices[PreviousLateral * LongitudinalVertexCount + LongitudinalIndex];
            const int32 Index =
                LateralIndex * LongitudinalVertexCount + LongitudinalIndex;
            PatchNormals[Index] = FVector::CrossProduct(
                LongitudinalTangent,
                LateralTangent).GetSafeNormal(SMALL_NUMBER, FVector::UpVector);
            PatchTangents[Index] = FProcMeshTangent(
                LongitudinalTangent.GetSafeNormal(), false);
        }
    }

    TArray<int32> PatchTriangles;
    PatchTriangles.Reserve(
        (LongitudinalVertexCount - 1) * (LateralVertexCount - 1) * 6);
    for (int32 LateralIndex = 0; LateralIndex < LateralVertexCount - 1; ++LateralIndex)
    {
        for (int32 LongitudinalIndex = 0;
             LongitudinalIndex < LongitudinalVertexCount - 1;
             ++LongitudinalIndex)
        {
            const int32 I0 =
                LateralIndex * LongitudinalVertexCount + LongitudinalIndex;
            const int32 I1 = I0 + 1;
            const int32 I2 = I0 + LongitudinalVertexCount;
            const int32 I3 = I2 + 1;
            PatchTriangles.Add(I0);
            PatchTriangles.Add(I1);
            PatchTriangles.Add(I3);
            PatchTriangles.Add(I0);
            PatchTriangles.Add(I3);
            PatchTriangles.Add(I2);
        }
    }

    if (ContactWaterPatch->GetNumSections() == 0)
    {
        ContactWaterPatch->CreateMeshSection_LinearColor(
            0,
            PatchVertices,
            PatchTriangles,
            PatchNormals,
            PatchUvs,
            PatchColors,
            PatchTangents,
            false);
    }
    else
    {
        ContactWaterPatch->UpdateMeshSection_LinearColor(
            0,
            PatchVertices,
            PatchNormals,
            PatchUvs,
            PatchColors,
            PatchTangents);
    }
    ContactWaterPatchTriangleCount = PatchTriangles.Num() / 3;
    ContactWaterPatch->SetVisibility(true, true);
}

void ARaftSimWaterVfxActor::UpdateConnectedContactWaterV6Review(
    const FVector& SurfaceCenterCm,
    const FVector& FlowDirection,
    const FVector& AcrossDirection,
    const FVector& ContactOutward,
    const FVector& ImpactDirection,
    float ImpactEnergy,
    float ContactScale)
{
    if (!bConnectedContactWaterV6Review ||
        !ConnectedContactWaterV6Review || !WaterAdapter)
    {
        HideConnectedContactWaterV6Review();
        return;
    }

    // Geometry-first V6 review: an 11 x 9 non-colliding sheet grows from the
    // same solver-sampled D4 shoulder as the production contact patch. It is
    // continuously triangulated from the free surface to a narrow aerated
    // crest. The sheet changes no forces, collision, water samples, map state,
    // scoring, or progression, and is disabled unless the explicit review
    // switch is present.
    constexpr int32 AcrossVertexCount = 11;
    constexpr int32 ArcVertexCount = 9;
    constexpr int32 VertexCount = AcrossVertexCount * ArcVertexCount;
    const float Strength = FMath::Clamp(
        ImpactEnergy * ContactScale, 0.0f, 1.2f);
    const float HalfWidthCm =
        FMath::Lerp(58.0f, 82.0f, Strength / 1.2f) * ContactScale;
    const float CrestHeightCm =
        FMath::Lerp(38.0f, 78.0f, Strength / 1.2f) * ContactScale;
    const float CrestReachCm =
        FMath::Lerp(38.0f, 70.0f, Strength / 1.2f) * ContactScale;
    FVector ExposedOutward = ContactOutward.GetSafeNormal2D();
    if (ExposedOutward.IsNearlyZero())
    {
        ExposedOutward = ImpactDirection.GetSafeNormal2D();
    }
    // Put the atlas breakup center beyond the occluding boulder rather than
    // centering its strongest coverage inside the rock silhouette.
    const FVector ExposedSurfaceCenterCm = SurfaceCenterCm +
        ExposedOutward * 115.0f * ContactScale;
    const FVector SheetReachDirection =
        (ExposedOutward * 0.72f - FlowDirection * 0.28f).GetSafeNormal2D();

    TArray<FVector> Vertices;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> Colors;
    TArray<FVector> Normals;
    TArray<FProcMeshTangent> Tangents;
    Vertices.SetNumUninitialized(VertexCount);
    Uvs.SetNumUninitialized(VertexCount);
    Colors.SetNumUninitialized(VertexCount);
    Normals.Init(FVector::UpVector, VertexCount);
    Tangents.Init(FProcMeshTangent(ImpactDirection, false), VertexCount);

    const FTransform ActorTransform = GetActorTransform();
    for (int32 AcrossIndex = 0;
         AcrossIndex < AcrossVertexCount;
         ++AcrossIndex)
    {
        const float AcrossUv = static_cast<float>(AcrossIndex) /
            static_cast<float>(AcrossVertexCount - 1);
        const float AcrossUnit = AcrossUv * 2.0f - 1.0f;
        const float AcrossFeather = FMath::Max(0.0f, FMath::Sin(PI * AcrossUv));
        for (int32 ArcIndex = 0; ArcIndex < ArcVertexCount; ++ArcIndex)
        {
            const float ArcUv = static_cast<float>(ArcIndex) /
                static_cast<float>(ArcVertexCount - 1);
            const int32 Index = AcrossIndex * ArcVertexCount + ArcIndex;
            const float WidthScale = FMath::Lerp(1.0f, 0.64f, ArcUv);
            const float SurfaceAttach = FMath::Clamp(ArcUv / 0.16f, 0.0f, 1.0f);
            const float CrestShape = FMath::Sin(ArcUv * PI * 0.58f);
            const float CurlShape = FMath::Square(
                FMath::Clamp((ArcUv - 0.58f) / 0.42f, 0.0f, 1.0f));
            const float LateralFlutter = FMath::Sin(
                SimulationPhase * 4.2f + AcrossUnit * 5.6f + ArcUv * 7.4f);
            const float CrestVariation = FMath::Clamp(
                0.72f + AcrossFeather * 0.28f +
                    LateralFlutter * AcrossFeather * 0.10f,
                0.58f,
                1.08f);
            const float EdgeFlutter =
                LateralFlutter * AcrossFeather * ArcUv * 4.5f * Strength;

            FVector WorldPosition = ExposedSurfaceCenterCm +
                AcrossDirection *
                    (AcrossUnit * HalfWidthCm * WidthScale + EdgeFlutter) +
                SheetReachDirection * (ArcUv * CrestReachCm) +
                FlowDirection * (CurlShape * 34.0f * ContactScale);

            FRaftSimWaterSample VertexSample;
            if (WaterAdapter->SampleWaterAtWorldPosition(
                    WorldPosition, VertexSample) && VertexSample.bWet)
            {
                WorldPosition.Z = VertexSample.SurfaceHeightMeters * CmPerM + 4.0f;
            }
            else
            {
                WorldPosition.Z = ExposedSurfaceCenterCm.Z - 4.0f;
            }
            WorldPosition.Z += CrestShape * CrestHeightCm * CrestVariation +
                LateralFlutter * AcrossFeather * ArcUv * 3.0f * Strength;

            Vertices[Index] = ActorTransform.InverseTransformPosition(WorldPosition);
            Uvs[Index] = FVector2D(AcrossUv, ArcUv);
            const float AeratedCore = FMath::Clamp(
                AcrossFeather * (0.30f + CrestShape * 0.82f) *
                    (0.58f + Strength * 0.34f),
                0.0f,
                1.0f);
            Colors[Index] = FLinearColor(
                FMath::Clamp(0.36f + Strength * 0.42f, 0.0f, 1.0f),
                ArcUv,
                AeratedCore,
                AcrossFeather * SurfaceAttach *
                    FMath::Lerp(0.72f, 0.42f, CurlShape));
        }
    }

    for (int32 AcrossIndex = 0;
         AcrossIndex < AcrossVertexCount;
         ++AcrossIndex)
    {
        for (int32 ArcIndex = 0; ArcIndex < ArcVertexCount; ++ArcIndex)
        {
            const int32 PreviousAcross = FMath::Max(AcrossIndex - 1, 0);
            const int32 NextAcross = FMath::Min(
                AcrossIndex + 1, AcrossVertexCount - 1);
            const int32 PreviousArc = FMath::Max(ArcIndex - 1, 0);
            const int32 NextArc = FMath::Min(ArcIndex + 1, ArcVertexCount - 1);
            const FVector AcrossTangent =
                Vertices[NextAcross * ArcVertexCount + ArcIndex] -
                Vertices[PreviousAcross * ArcVertexCount + ArcIndex];
            const FVector ArcTangent =
                Vertices[AcrossIndex * ArcVertexCount + NextArc] -
                Vertices[AcrossIndex * ArcVertexCount + PreviousArc];
            const int32 Index = AcrossIndex * ArcVertexCount + ArcIndex;
            Normals[Index] = FVector::CrossProduct(
                ArcTangent, AcrossTangent).GetSafeNormal(
                    SMALL_NUMBER, FVector::UpVector);
            Tangents[Index] = FProcMeshTangent(
                AcrossTangent.GetSafeNormal(), false);
        }
    }

    TArray<int32> Triangles;
    Triangles.Reserve(
        (AcrossVertexCount - 1) * (ArcVertexCount - 1) * 6);
    for (int32 AcrossIndex = 0;
         AcrossIndex < AcrossVertexCount - 1;
         ++AcrossIndex)
    {
        for (int32 ArcIndex = 0; ArcIndex < ArcVertexCount - 1; ++ArcIndex)
        {
            const int32 I0 = AcrossIndex * ArcVertexCount + ArcIndex;
            const int32 I1 = I0 + 1;
            const int32 I2 = I0 + ArcVertexCount;
            const int32 I3 = I2 + 1;
            Triangles.Add(I0);
            Triangles.Add(I1);
            Triangles.Add(I3);
            Triangles.Add(I0);
            Triangles.Add(I3);
            Triangles.Add(I2);
        }
    }

    if (ConnectedContactWaterV6Review->GetNumSections() == 0)
    {
        ConnectedContactWaterV6Review->CreateMeshSection_LinearColor(
            0, Vertices, Triangles, Normals, Uvs, Colors, Tangents, false);
    }
    else
    {
        ConnectedContactWaterV6Review->UpdateMeshSection_LinearColor(
            0, Vertices, Normals, Uvs, Colors, Tangents);
    }
    ConnectedContactWaterV6TriangleCount = Triangles.Num() / 3;
    ConnectedContactWaterV6Review->SetVisibility(true, true);
}

void ARaftSimWaterVfxActor::UpdateConnectedContactWaterV7Review(
    const FVector& SurfaceCenterCm,
    const FVector& FlowDirection,
    const FVector& AcrossDirection,
    const FVector& ContactOutward,
    const FVector& ImpactDirection,
    float ImpactEnergy,
    float ContactScale)
{
    if (!bConnectedContactWaterV7Review ||
        !ConnectedContactWaterV7Review || !WaterAdapter)
    {
        HideConnectedContactWaterV7Review();
        return;
    }

    // V7 is a presentation-only three-layer solver-contoured contact volume:
    // section 0 is a mask-independent surface attachment, section 1 is an
    // aerated crest, and section 2 is a pair of smaller breakup lobes. Every
    // layer derives from the same solver-sampled D4 shoulder and live-water
    // surface. It changes no forces, collision, water samples, map state,
    // scoring, or progression and exists only behind the explicit V7 switch.
    const float Strength = FMath::Clamp(
        ImpactEnergy * ContactScale, 0.0f, 1.2f);
    const float StrengthUnit = Strength / 1.2f;
    // ContactOutward points from the raft centre toward the compressed tube
    // and obstacle. The visible escape face is on the opposite side of that
    // contact: V6's additional positive offset put its review mesh behind the
    // boulder. Build V7 back from the already offset patch anchor toward the
    // exposed water/raft face so the three layers actually bridge the pin.
    FVector ExposedOutward = -ContactOutward.GetSafeNormal2D();
    if (ExposedOutward.IsNearlyZero())
    {
        ExposedOutward = -ImpactDirection.GetSafeNormal2D();
    }
    if (ExposedOutward.IsNearlyZero())
    {
        ExposedOutward = AcrossDirection;
    }
    const FVector ReachDirection =
        (ExposedOutward * 0.84f - FlowDirection * 0.16f).GetSafeNormal2D();
    const FTransform ActorTransform = GetActorTransform();

    auto SampleSurfaceHeight = [this, &SurfaceCenterCm](FVector& Position)
    {
        FRaftSimWaterSample VertexSample;
        if (WaterAdapter->SampleWaterAtWorldPosition(
                Position, VertexSample) && VertexSample.bWet)
        {
            Position.Z = VertexSample.SurfaceHeightMeters * CmPerM;
        }
        else
        {
            Position.Z = SurfaceCenterCm.Z - 8.0f;
        }
    };

    auto BuildLayer = [this, &ActorTransform](
        int32 SectionIndex,
        int32 AcrossVertexCount,
        int32 ArcVertexCount,
        const TFunction<FVector(float, float)>& MakeWorldPosition,
        const TFunction<FLinearColor(float, float)>& MakeColor)
        -> int32
    {
        const int32 VertexCount = AcrossVertexCount * ArcVertexCount;
        TArray<FVector> Vertices;
        TArray<FVector2D> Uvs;
        TArray<FLinearColor> Colors;
        TArray<FVector> Normals;
        TArray<FProcMeshTangent> Tangents;
        Vertices.SetNumUninitialized(VertexCount);
        Uvs.SetNumUninitialized(VertexCount);
        Colors.SetNumUninitialized(VertexCount);
        Normals.Init(FVector::UpVector, VertexCount);
        Tangents.Init(FProcMeshTangent(FVector::ForwardVector, false), VertexCount);

        for (int32 AcrossIndex = 0;
             AcrossIndex < AcrossVertexCount;
             ++AcrossIndex)
        {
            const float AcrossUv = static_cast<float>(AcrossIndex) /
                static_cast<float>(AcrossVertexCount - 1);
            for (int32 ArcIndex = 0;
                 ArcIndex < ArcVertexCount;
                 ++ArcIndex)
            {
                const float ArcUv = static_cast<float>(ArcIndex) /
                    static_cast<float>(ArcVertexCount - 1);
                const int32 Index =
                    AcrossIndex * ArcVertexCount + ArcIndex;
                Vertices[Index] = ActorTransform.InverseTransformPosition(
                    MakeWorldPosition(AcrossUv, ArcUv));
                Uvs[Index] = FVector2D(AcrossUv, ArcUv);
                Colors[Index] = MakeColor(AcrossUv, ArcUv);
            }
        }

        for (int32 AcrossIndex = 0;
             AcrossIndex < AcrossVertexCount;
             ++AcrossIndex)
        {
            for (int32 ArcIndex = 0;
                 ArcIndex < ArcVertexCount;
                 ++ArcIndex)
            {
                const int32 PreviousAcross = FMath::Max(AcrossIndex - 1, 0);
                const int32 NextAcross = FMath::Min(
                    AcrossIndex + 1, AcrossVertexCount - 1);
                const int32 PreviousArc = FMath::Max(ArcIndex - 1, 0);
                const int32 NextArc = FMath::Min(
                    ArcIndex + 1, ArcVertexCount - 1);
                const FVector AcrossTangent =
                    Vertices[NextAcross * ArcVertexCount + ArcIndex] -
                    Vertices[PreviousAcross * ArcVertexCount + ArcIndex];
                const FVector ArcTangent =
                    Vertices[AcrossIndex * ArcVertexCount + NextArc] -
                    Vertices[AcrossIndex * ArcVertexCount + PreviousArc];
                const int32 Index =
                    AcrossIndex * ArcVertexCount + ArcIndex;
                Normals[Index] = FVector::CrossProduct(
                    ArcTangent, AcrossTangent).GetSafeNormal(
                        SMALL_NUMBER, FVector::UpVector);
                Tangents[Index] = FProcMeshTangent(
                    AcrossTangent.GetSafeNormal(), false);
            }
        }

        TArray<int32> Triangles;
        Triangles.Reserve(
            (AcrossVertexCount - 1) * (ArcVertexCount - 1) * 6);
        for (int32 AcrossIndex = 0;
             AcrossIndex < AcrossVertexCount - 1;
             ++AcrossIndex)
        {
            for (int32 ArcIndex = 0;
                 ArcIndex < ArcVertexCount - 1;
                 ++ArcIndex)
            {
                const int32 I0 =
                    AcrossIndex * ArcVertexCount + ArcIndex;
                const int32 I1 = I0 + 1;
                const int32 I2 = I0 + ArcVertexCount;
                const int32 I3 = I2 + 1;
                Triangles.Append({I0, I1, I3, I0, I3, I2});
            }
        }

        if (ConnectedContactWaterV7Review->GetNumSections() <= SectionIndex)
        {
            ConnectedContactWaterV7Review->CreateMeshSection_LinearColor(
                SectionIndex, Vertices, Triangles, Normals, Uvs, Colors,
                Tangents, false);
        }
        else
        {
            ConnectedContactWaterV7Review->UpdateMeshSection_LinearColor(
                SectionIndex, Vertices, Normals, Uvs, Colors, Tangents);
        }
        return Triangles.Num() / 3;
    };

    const FVector AttachmentCenter =
        SurfaceCenterCm + ExposedOutward * 40.0f * ContactScale;
    const float AttachmentHalfWidthCm =
        FMath::Lerp(78.0f, 104.0f, StrengthUnit) * ContactScale;
    const float AttachmentReachCm =
        FMath::Lerp(118.0f, 162.0f, StrengthUnit) * ContactScale;
    const int32 AttachmentTriangles = BuildLayer(
        0, 9, 6,
        [&](float AcrossUv, float ReachUv)
        {
            const float AcrossUnit = AcrossUv * 2.0f - 1.0f;
            const float WidthScale = FMath::Lerp(0.78f, 1.0f, ReachUv);
            FVector Position = AttachmentCenter +
                AcrossDirection *
                    (AcrossUnit * AttachmentHalfWidthCm * WidthScale) +
                ReachDirection * (ReachUv * AttachmentReachCm) -
                FlowDirection *
                    (FMath::Sin(AcrossUnit * PI) * 8.0f * Strength);
            SampleSurfaceHeight(Position);
            Position.Z += 2.5f +
                FMath::Sin(
                    SimulationPhase * 2.3f + AcrossUnit * 3.2f +
                    ReachUv * 4.1f) * 1.5f * Strength;
            return Position;
        },
        [&](float AcrossUv, float ReachUv)
        {
            const float AcrossFeather =
                FMath::Max(0.0f, FMath::Sin(PI * AcrossUv));
            return FLinearColor(
                FMath::Clamp(0.34f + Strength * 0.34f, 0.0f, 1.0f),
                ReachUv,
                0.08f + Strength * 0.06f,
                AcrossFeather * FMath::Lerp(0.90f, 0.58f, ReachUv));
        });

    const FVector CrestCenter =
        SurfaceCenterCm + ExposedOutward * 50.0f * ContactScale;
    const float CrestHalfWidthCm =
        FMath::Lerp(50.0f, 68.0f, StrengthUnit) * ContactScale;
    const float CrestReachCm =
        FMath::Lerp(70.0f, 100.0f, StrengthUnit) * ContactScale;
    const float CrestHeightCm =
        FMath::Lerp(24.0f, 40.0f, StrengthUnit) * ContactScale;
    const int32 CrestTriangles = BuildLayer(
        1, 11, 7,
        [&](float AcrossUv, float ArcUv)
        {
            const float AcrossUnit = AcrossUv * 2.0f - 1.0f;
            const float AcrossFeather =
                FMath::Max(0.0f, FMath::Sin(PI * AcrossUv));
            const float CrestShape = FMath::Sin(ArcUv * PI * 0.62f);
            const float CurlShape = FMath::Square(
                FMath::Clamp((ArcUv - 0.54f) / 0.46f, 0.0f, 1.0f));
            const float Flutter = FMath::Sin(
                SimulationPhase * 4.0f + AcrossUnit * 5.2f + ArcUv * 6.1f);
            FVector Position = CrestCenter +
                AcrossDirection *
                    (AcrossUnit * CrestHalfWidthCm *
                     FMath::Lerp(1.0f, 0.68f, ArcUv)) +
                ReachDirection * (ArcUv * CrestReachCm) +
                FlowDirection * (CurlShape * 24.0f * ContactScale);
            SampleSurfaceHeight(Position);
            Position.Z += CrestShape * CrestHeightCm *
                (0.72f + AcrossFeather * 0.28f) +
                Flutter * AcrossFeather * ArcUv * 3.0f * Strength;
            return Position;
        },
        [&](float AcrossUv, float ArcUv)
        {
            const float AcrossFeather =
                FMath::Max(0.0f, FMath::Sin(PI * AcrossUv));
            const float CrestShape = FMath::Sin(ArcUv * PI * 0.62f);
            const float SurfaceAttach =
                FMath::Clamp(ArcUv / 0.18f, 0.0f, 1.0f);
            return FLinearColor(
                FMath::Clamp(0.38f + Strength * 0.40f, 0.0f, 1.0f),
                ArcUv,
                FMath::Clamp(
                    AcrossFeather * (0.34f + CrestShape * 0.74f),
                    0.0f, 1.0f),
                AcrossFeather * SurfaceAttach *
                    FMath::Lerp(0.86f, 0.48f, ArcUv));
        });

    const FVector BreakupCenter =
        SurfaceCenterCm + ExposedOutward * 65.0f * ContactScale;
    const float BreakupHalfWidthCm =
        FMath::Lerp(60.0f, 80.0f, StrengthUnit) * ContactScale;
    const float BreakupReachCm =
        FMath::Lerp(54.0f, 82.0f, StrengthUnit) * ContactScale;
    const int32 BreakupTriangles = BuildLayer(
        2, 13, 5,
        [&](float AcrossUv, float ArcUv)
        {
            const float AcrossUnit = AcrossUv * 2.0f - 1.0f;
            const float LeftLobe = FMath::Exp(
                -FMath::Square((AcrossUnit + 0.46f) / 0.27f));
            const float RightLobe = FMath::Exp(
                -FMath::Square((AcrossUnit - 0.38f) / 0.31f));
            const float Lobe = FMath::Clamp(
                FMath::Max(LeftLobe, RightLobe) - 0.06f, 0.0f, 1.0f);
            const float ArcShape = FMath::Sin(ArcUv * PI * 0.78f);
            const float Flutter = FMath::Sin(
                SimulationPhase * 5.1f + AcrossUnit * 7.2f + ArcUv * 8.0f);
            FVector Position = BreakupCenter +
                AcrossDirection * (AcrossUnit * BreakupHalfWidthCm) +
                ReachDirection * (ArcUv * BreakupReachCm) +
                FlowDirection *
                    (FMath::Square(ArcUv) * 18.0f * ContactScale);
            SampleSurfaceHeight(Position);
            Position.Z += ArcShape * Lobe *
                FMath::Lerp(18.0f, 34.0f, StrengthUnit) * ContactScale +
                Flutter * Lobe * ArcUv * 5.0f * Strength;
            return Position;
        },
        [&](float AcrossUv, float ArcUv)
        {
            const float AcrossUnit = AcrossUv * 2.0f - 1.0f;
            const float LeftLobe = FMath::Exp(
                -FMath::Square((AcrossUnit + 0.46f) / 0.27f));
            const float RightLobe = FMath::Exp(
                -FMath::Square((AcrossUnit - 0.38f) / 0.31f));
            const float Lobe = FMath::Clamp(
                FMath::Max(LeftLobe, RightLobe) - 0.06f, 0.0f, 1.0f);
            const float ArcShape = FMath::Sin(ArcUv * PI * 0.78f);
            const float SurfaceAttach =
                FMath::Clamp(ArcUv / 0.20f, 0.0f, 1.0f);
            return FLinearColor(
                FMath::Clamp(0.42f + Strength * 0.44f, 0.0f, 1.0f),
                ArcUv,
                FMath::Clamp(Lobe * (0.50f + ArcShape * 0.62f), 0.0f, 1.0f),
                Lobe * SurfaceAttach * FMath::Lerp(0.78f, 0.34f, ArcUv));
        });

    ConnectedContactWaterV7TriangleCount =
        AttachmentTriangles + CrestTriangles + BreakupTriangles;
    ConnectedContactWaterV7Review->SetVisibility(true, true);
}

void ARaftSimWaterVfxActor::UpdateConnectedContactWaterV8Review(
    const FVector& SurfaceCenterCm,
    const FVector& FlowDirection,
    const FVector& AcrossDirection,
    const FVector& ContactOutward,
    const FVector& ImpactDirection,
    float ImpactEnergy,
    float ContactScale)
{
    if (!bConnectedContactWaterV8Review ||
        !ConnectedContactWaterV8Review || !WaterAdapter)
    {
        HideConnectedContactWaterV8Review();
        return;
    }

    // V8 is a presentation-only sampled attachment plus six short closed,
    // flow-aligned entrained-air lobes. Unlike V7 there is no shared vertical
    // crest sheet: each body has a sealed cross-section, independent length,
    // phase and lateral path. The geometry consumes the existing D4 contact
    // shoulder and live-water samples but changes no forces, collision, water
    // samples, map state, scoring or progression.
    const float Strength = FMath::Clamp(
        ImpactEnergy * ContactScale, 0.0f, 1.2f);
    const float StrengthUnit = Strength / 1.2f;
    FVector ExposedOutward = -ContactOutward.GetSafeNormal2D();
    if (ExposedOutward.IsNearlyZero())
    {
        ExposedOutward = -ImpactDirection.GetSafeNormal2D();
    }
    if (ExposedOutward.IsNearlyZero())
    {
        ExposedOutward = AcrossDirection;
    }
    const FVector ReachDirection =
        (ExposedOutward * 0.82f - FlowDirection * 0.18f).GetSafeNormal2D();
    const FTransform ActorTransform = GetActorTransform();

    auto SampleSurfaceHeight = [this, &SurfaceCenterCm](FVector& Position)
    {
        FRaftSimWaterSample VertexSample;
        if (WaterAdapter->SampleWaterAtWorldPosition(
                Position, VertexSample) && VertexSample.bWet)
        {
            Position.Z = VertexSample.SurfaceHeightMeters * CmPerM;
        }
        else
        {
            Position.Z = SurfaceCenterCm.Z - 8.0f;
        }
    };

    auto SubmitSection = [this](
        int32 SectionIndex,
        const TArray<FVector>& Vertices,
        const TArray<int32>& Triangles,
        const TArray<FVector>& Normals,
        const TArray<FVector2D>& Uvs,
        const TArray<FLinearColor>& Colors,
        const TArray<FProcMeshTangent>& Tangents)
    {
        if (ConnectedContactWaterV8Review->GetNumSections() <= SectionIndex)
        {
            ConnectedContactWaterV8Review->CreateMeshSection_LinearColor(
                SectionIndex, Vertices, Triangles, Normals, Uvs, Colors,
                Tangents, false);
        }
        else
        {
            ConnectedContactWaterV8Review->UpdateMeshSection_LinearColor(
                SectionIndex, Vertices, Normals, Uvs, Colors, Tangents);
        }
    };

    // Section 0 preserves a thin sampled connection between the base river
    // and every closed lobe. It never rises into a camera-facing wall.
    constexpr int32 AttachmentAcrossCount = 9;
    constexpr int32 AttachmentReachCount = 5;
    constexpr int32 AttachmentVertexCount =
        AttachmentAcrossCount * AttachmentReachCount;
    TArray<FVector> AttachmentVertices;
    TArray<FVector2D> AttachmentUvs;
    TArray<FLinearColor> AttachmentColors;
    TArray<FVector> AttachmentNormals;
    TArray<FProcMeshTangent> AttachmentTangents;
    AttachmentVertices.SetNumUninitialized(AttachmentVertexCount);
    AttachmentUvs.SetNumUninitialized(AttachmentVertexCount);
    AttachmentColors.SetNumUninitialized(AttachmentVertexCount);
    AttachmentNormals.Init(FVector::UpVector, AttachmentVertexCount);
    AttachmentTangents.Init(
        FProcMeshTangent(FVector::ForwardVector, false),
        AttachmentVertexCount);
    const FVector AttachmentCenter =
        SurfaceCenterCm + ExposedOutward * 30.0f * ContactScale;
    const float AttachmentHalfWidthCm =
        FMath::Lerp(82.0f, 104.0f, StrengthUnit) * ContactScale;
    const float AttachmentReachCm =
        FMath::Lerp(96.0f, 128.0f, StrengthUnit) * ContactScale;
    for (int32 AcrossIndex = 0;
         AcrossIndex < AttachmentAcrossCount;
         ++AcrossIndex)
    {
        const float AcrossUv = static_cast<float>(AcrossIndex) /
            static_cast<float>(AttachmentAcrossCount - 1);
        const float AcrossUnit = AcrossUv * 2.0f - 1.0f;
        for (int32 ReachIndex = 0;
             ReachIndex < AttachmentReachCount;
             ++ReachIndex)
        {
            const float ReachUv = static_cast<float>(ReachIndex) /
                static_cast<float>(AttachmentReachCount - 1);
            const int32 Index =
                AcrossIndex * AttachmentReachCount + ReachIndex;
            FVector Position = AttachmentCenter +
                AcrossDirection *
                    (AcrossUnit * AttachmentHalfWidthCm *
                     FMath::Lerp(0.72f, 1.0f, ReachUv)) +
                ReachDirection * (ReachUv * AttachmentReachCm);
            SampleSurfaceHeight(Position);
            Position.Z += 1.5f + FMath::Sin(
                SimulationPhase * 2.0f + AcrossUnit * 3.7f +
                ReachUv * 4.9f) * Strength;
            AttachmentVertices[Index] =
                ActorTransform.InverseTransformPosition(Position);
            AttachmentUvs[Index] = FVector2D(AcrossUv, ReachUv);
            const float EdgeFeather =
                FMath::Max(0.0f, FMath::Sin(PI * AcrossUv));
            AttachmentColors[Index] = FLinearColor(
                0.30f + Strength * 0.24f,
                ReachUv,
                0.05f + Strength * 0.04f,
                EdgeFeather * FMath::Lerp(0.82f, 0.48f, ReachUv));
        }
    }
    for (int32 AcrossIndex = 0;
         AcrossIndex < AttachmentAcrossCount;
         ++AcrossIndex)
    {
        for (int32 ReachIndex = 0;
             ReachIndex < AttachmentReachCount;
             ++ReachIndex)
        {
            const int32 PreviousAcross = FMath::Max(AcrossIndex - 1, 0);
            const int32 NextAcross = FMath::Min(
                AcrossIndex + 1, AttachmentAcrossCount - 1);
            const int32 PreviousReach = FMath::Max(ReachIndex - 1, 0);
            const int32 NextReach = FMath::Min(
                ReachIndex + 1, AttachmentReachCount - 1);
            const FVector AcrossTangent =
                AttachmentVertices[
                    NextAcross * AttachmentReachCount + ReachIndex] -
                AttachmentVertices[
                    PreviousAcross * AttachmentReachCount + ReachIndex];
            const FVector ReachTangent =
                AttachmentVertices[
                    AcrossIndex * AttachmentReachCount + NextReach] -
                AttachmentVertices[
                    AcrossIndex * AttachmentReachCount + PreviousReach];
            const int32 Index =
                AcrossIndex * AttachmentReachCount + ReachIndex;
            AttachmentNormals[Index] = FVector::CrossProduct(
                ReachTangent, AcrossTangent).GetSafeNormal(
                    SMALL_NUMBER, FVector::UpVector);
            AttachmentTangents[Index] = FProcMeshTangent(
                AcrossTangent.GetSafeNormal(), false);
        }
    }
    TArray<int32> AttachmentTriangles;
    AttachmentTriangles.Reserve(
        (AttachmentAcrossCount - 1) *
        (AttachmentReachCount - 1) * 6);
    for (int32 AcrossIndex = 0;
         AcrossIndex < AttachmentAcrossCount - 1;
         ++AcrossIndex)
    {
        for (int32 ReachIndex = 0;
             ReachIndex < AttachmentReachCount - 1;
             ++ReachIndex)
        {
            const int32 I0 =
                AcrossIndex * AttachmentReachCount + ReachIndex;
            const int32 I1 = I0 + 1;
            const int32 I2 = I0 + AttachmentReachCount;
            const int32 I3 = I2 + 1;
            AttachmentTriangles.Append({I0, I1, I3, I0, I3, I2});
        }
    }
    SubmitSection(
        0, AttachmentVertices, AttachmentTriangles, AttachmentNormals,
        AttachmentUvs, AttachmentColors, AttachmentTangents);

    constexpr int32 LobeCount = 6;
    constexpr int32 AlongSegments = 8;
    constexpr int32 RadialSegments = 8;
    constexpr int32 InternalRingCount = AlongSegments - 1;
    constexpr int32 LobeVertexCount =
        2 + InternalRingCount * RadialSegments;
    const float AcrossOffsets[LobeCount] =
        {-0.78f, -0.47f, -0.16f, 0.18f, 0.49f, 0.76f};
    const float LengthScales[LobeCount] =
        {0.72f, 0.96f, 0.81f, 1.00f, 0.76f, 0.88f};
    const float RadiusScales[LobeCount] =
        {0.70f, 1.00f, 0.82f, 0.94f, 0.74f, 0.66f};
    const float PhaseOffsets[LobeCount] =
        {0.15f, 1.70f, 3.10f, 4.45f, 5.65f, 2.35f};
    int32 LobeTriangleTotal = 0;
    for (int32 LobeIndex = 0; LobeIndex < LobeCount; ++LobeIndex)
    {
        TArray<FVector> Vertices;
        TArray<FVector2D> Uvs;
        TArray<FLinearColor> Colors;
        TArray<FVector> Normals;
        TArray<FProcMeshTangent> Tangents;
        Vertices.SetNumUninitialized(LobeVertexCount);
        Uvs.SetNumUninitialized(LobeVertexCount);
        Colors.SetNumUninitialized(LobeVertexCount);
        Normals.SetNumUninitialized(LobeVertexCount);
        Tangents.SetNumUninitialized(LobeVertexCount);

        const float Phase = PhaseOffsets[LobeIndex];
        const float LobeLengthCm =
            FMath::Lerp(62.0f, 94.0f, StrengthUnit) *
            LengthScales[LobeIndex] * ContactScale;
        const float AcrossRadiusCm =
            FMath::Lerp(18.0f, 28.0f, StrengthUnit) *
            RadiusScales[LobeIndex] * ContactScale;
        const float VerticalRadiusCm = AcrossRadiusCm *
            FMath::Lerp(0.26f, 0.36f, StrengthUnit);
        const FVector LobeAnchor = SurfaceCenterCm +
            ExposedOutward * (42.0f + 7.0f * (LobeIndex % 2)) * ContactScale +
            AcrossDirection *
                (AcrossOffsets[LobeIndex] * AttachmentHalfWidthCm * 0.82f) -
            FlowDirection *
                (6.0f + 4.0f * (LobeIndex % 3)) * ContactScale;

        auto MakeCenter = [&](float AlongUv)
        {
            const float Bend = FMath::Sin(
                SimulationPhase * (2.4f + 0.12f * LobeIndex) +
                Phase + AlongUv * PI * 1.4f);
            FVector Center = LobeAnchor +
                ReachDirection * (AlongUv * LobeLengthCm) +
                AcrossDirection *
                    (Bend * AlongUv * AcrossRadiusCm * 0.30f) +
                FlowDirection *
                    (FMath::Sin(AlongUv * PI) * 8.0f *
                     ((LobeIndex % 2) == 0 ? -1.0f : 1.0f));
            SampleSurfaceHeight(Center);
            Center.Z += 1.0f +
                FMath::Sin(AlongUv * PI) *
                    FMath::Lerp(2.0f, 5.0f, StrengthUnit) *
                    RadiusScales[LobeIndex] +
                Bend * AlongUv * Strength;
            return Center;
        };

        const FVector StartCenter = MakeCenter(0.0f);
        const FVector EndCenter = MakeCenter(1.0f);
        Vertices[0] = ActorTransform.InverseTransformPosition(StartCenter);
        Uvs[0] = FVector2D(0.5f, 0.0f);
        Colors[0] = FLinearColor(
            0.40f + Strength * 0.34f, 0.0f, 0.58f, 0.0f);
        Normals[0] = ActorTransform.InverseTransformVectorNoScale(
            -ReachDirection).GetSafeNormal();
        Tangents[0] = FProcMeshTangent(
            ActorTransform.InverseTransformVectorNoScale(
                AcrossDirection).GetSafeNormal(),
            false);
        for (int32 AlongIndex = 1;
             AlongIndex < AlongSegments;
             ++AlongIndex)
        {
            const float AlongUv = static_cast<float>(AlongIndex) /
                static_cast<float>(AlongSegments);
            const float Envelope = FMath::Pow(
                FMath::Max(0.0f, FMath::Sin(AlongUv * PI)), 0.68f);
            const float Irregularity = FMath::Clamp(
                1.0f + 0.10f * FMath::Sin(
                    AlongUv * 9.0f + Phase + SimulationPhase * 3.1f),
                0.82f, 1.14f);
            const FVector Center = MakeCenter(AlongUv);
            for (int32 RadialIndex = 0;
                 RadialIndex < RadialSegments;
                 ++RadialIndex)
            {
                const float RadialUv = static_cast<float>(RadialIndex) /
                    static_cast<float>(RadialSegments);
                const float Theta = RadialUv * 2.0f * PI;
                const float AcrossCos = FMath::Cos(Theta);
                const float VerticalSin = FMath::Sin(Theta);
                const int32 Index = 1 +
                    (AlongIndex - 1) * RadialSegments + RadialIndex;
                const FVector Offset =
                    AcrossDirection *
                        (AcrossCos * AcrossRadiusCm * Envelope *
                         Irregularity) +
                    FVector::UpVector *
                        (VerticalSin * VerticalRadiusCm * Envelope *
                         FMath::Lerp(0.92f, 1.08f,
                             0.5f + 0.5f * FMath::Sin(Phase + Theta * 2.0f)));
                Vertices[Index] = ActorTransform.InverseTransformPosition(
                    Center + Offset);
                Uvs[Index] = FVector2D(RadialUv, AlongUv);
                const float FoamDensity = FMath::Clamp(
                    0.38f + Envelope * 0.55f +
                    0.12f * FMath::Sin(Theta * 3.0f + Phase),
                    0.0f, 1.0f);
                Colors[Index] = FLinearColor(
                    0.40f + Strength * 0.34f,
                    AlongUv,
                    FoamDensity,
                    Envelope * FMath::Lerp(0.76f, 0.40f, AlongUv));
                const FVector WorldNormal =
                    AcrossDirection * AcrossCos +
                    FVector::UpVector * VerticalSin;
                Normals[Index] =
                    ActorTransform.InverseTransformVectorNoScale(
                        WorldNormal).GetSafeNormal();
                Tangents[Index] = FProcMeshTangent(
                    ActorTransform.InverseTransformVectorNoScale(
                        ReachDirection).GetSafeNormal(),
                    false);
            }
        }
        const int32 EndIndex = LobeVertexCount - 1;
        Vertices[EndIndex] =
            ActorTransform.InverseTransformPosition(EndCenter);
        Uvs[EndIndex] = FVector2D(0.5f, 1.0f);
        Colors[EndIndex] = FLinearColor(
            0.40f + Strength * 0.34f, 1.0f, 0.44f, 0.0f);
        Normals[EndIndex] = ActorTransform.InverseTransformVectorNoScale(
            ReachDirection).GetSafeNormal();
        Tangents[EndIndex] = FProcMeshTangent(
            ActorTransform.InverseTransformVectorNoScale(
                AcrossDirection).GetSafeNormal(),
            false);

        TArray<int32> Triangles;
        Triangles.Reserve(AlongSegments * RadialSegments * 6);
        const int32 FirstRing = 1;
        for (int32 RadialIndex = 0;
             RadialIndex < RadialSegments;
             ++RadialIndex)
        {
            const int32 NextRadial =
                (RadialIndex + 1) % RadialSegments;
            Triangles.Append(
                {0, FirstRing + RadialIndex, FirstRing + NextRadial});
        }
        for (int32 RingIndex = 0;
             RingIndex < InternalRingCount - 1;
             ++RingIndex)
        {
            const int32 RingStart = 1 + RingIndex * RadialSegments;
            const int32 NextRingStart = RingStart + RadialSegments;
            for (int32 RadialIndex = 0;
                 RadialIndex < RadialSegments;
                 ++RadialIndex)
            {
                const int32 NextRadial =
                    (RadialIndex + 1) % RadialSegments;
                const int32 I0 = RingStart + RadialIndex;
                const int32 I1 = RingStart + NextRadial;
                const int32 I2 = NextRingStart + RadialIndex;
                const int32 I3 = NextRingStart + NextRadial;
                Triangles.Append({I0, I2, I3, I0, I3, I1});
            }
        }
        const int32 LastRing =
            1 + (InternalRingCount - 1) * RadialSegments;
        for (int32 RadialIndex = 0;
             RadialIndex < RadialSegments;
             ++RadialIndex)
        {
            const int32 NextRadial =
                (RadialIndex + 1) % RadialSegments;
            Triangles.Append(
                {LastRing + NextRadial, LastRing + RadialIndex, EndIndex});
        }

        SubmitSection(
            LobeIndex + 1, Vertices, Triangles, Normals, Uvs, Colors,
            Tangents);
        LobeTriangleTotal += Triangles.Num() / 3;
    }

    ConnectedContactWaterV8TriangleCount =
        AttachmentTriangles.Num() / 3 + LobeTriangleTotal;
    ConnectedContactWaterV8Review->SetVisibility(true, true);
}

void ARaftSimWaterVfxActor::UpdateDepthBearingContactWaterV10Review(
    const FVector& SurfaceCenterCm,
    const FVector& FlowDirection,
    const FVector& AcrossDirection,
    const FVector& ContactOutward,
    const FVector& ImpactDirection,
    float ImpactEnergy,
    float ContactScale)
{
    if (!bDepthBearingContactWaterV10Review ||
        !DepthBearingContactWaterV10Review ||
        DepthBearingContactWaterV10FrameTriangleCounts.Num() !=
            DepthBearingContactWaterV10FrameCount)
    {
        HideDepthBearingContactWaterV10Review();
        return;
    }

    // V10 consumes only the already-authoritative D4 presentation frame. The
    // six cached closed volumes are visual geometry: no force, collision,
    // water sample, map, scoring, rescue, or progression path reads them.
    const float Strength = FMath::Clamp(
        ImpactEnergy * ContactScale, 0.0f, 1.2f);
    const float StrengthUnit = Strength / 1.2f;
    FVector EscapeDirection = FlowDirection.GetSafeNormal2D();
    if (EscapeDirection.IsNearlyZero())
    {
        EscapeDirection = -ImpactDirection.GetSafeNormal2D();
    }
    if (EscapeDirection.IsNearlyZero())
    {
        EscapeDirection = AcrossDirection;
    }
    const FVector CacheCenter = SurfaceCenterCm +
        ContactOutward.GetSafeNormal2D() * (10.0f * ContactScale) -
        FlowDirection * (8.0f * ContactScale) -
        FVector::UpVector * 2.0f;
    DepthBearingContactWaterV10Review->SetWorldLocationAndRotation(
        CacheCenter,
        FRotationMatrix::MakeFromXZ(
            EscapeDirection, FVector::UpVector).Rotator());
    const float UniformStrengthScale =
        FMath::Lerp(0.88f, 1.04f, StrengthUnit) * ContactScale;
    DepthBearingContactWaterV10Review->SetWorldScale3D(FVector(
        0.58f * UniformStrengthScale,
        0.60f * UniformStrengthScale,
        FMath::Lerp(0.96f, 1.04f, StrengthUnit) * ContactScale));

    int32 ForcedFrame = -1;
    FParse::Value(
        FCommandLine::Get(),
        TEXT("RaftSimDepthBearingContactWaterV10Frame="),
        ForcedFrame);
    const int32 FrameIndex = ForcedFrame >= 0
        ? FMath::Clamp(
            ForcedFrame, 0, DepthBearingContactWaterV10FrameCount - 1)
        : FMath::FloorToInt(
            SimulationPhase / DepthBearingContactWaterV10FrameSeconds) %
            DepthBearingContactWaterV10FrameCount;
    if (FrameIndex != DepthBearingContactWaterV10CurrentFrame)
    {
        for (int32 SectionIndex = 0;
             SectionIndex < DepthBearingContactWaterV10FrameCount;
             ++SectionIndex)
        {
            DepthBearingContactWaterV10Review->SetMeshSectionVisible(
                SectionIndex, SectionIndex == FrameIndex);
        }
        DepthBearingContactWaterV10CurrentFrame = FrameIndex;
        DepthBearingContactWaterV10TriangleCount =
            DepthBearingContactWaterV10FrameTriangleCounts[FrameIndex];
    }
    DepthBearingContactWaterV10Review->SetVisibility(true, true);
}

void ARaftSimWaterVfxActor::RefreshRapidAerosol()
{
    if (!RapidAerosolInstances)
    {
        return;
    }
    RapidAerosolInstances->ClearInstances();
    if (!BreakingSurface.IsValid())
    {
        if (TActorIterator<ARaftSimWaterSurfaceActor> It(GetWorld()); It)
        {
            BreakingSurface = *It;
        }
    }
    if (!BreakingSurface.IsValid())
    {
        for (UNiagaraComponent* Component : RapidAerosolNiagara)
        {
            SetNiagaraEmission(
                Component, false, FVector::ZeroVector, FVector::ForwardVector,
                1.0f, 0.0f);
        }
        for (UNiagaraComponent* Component : RapidRollerNiagara)
        {
            SetNiagaraEmission(
                Component, false, FVector::ZeroVector, FVector::ForwardVector,
                1.0f, 0.0f);
        }
        ActiveRapidNiagaraCount = 0;
        ActiveRapidRollerNiagaraCount = 0;
        return;
    }
    BreakingSurface->SetBreakingRollerVolumeRenderingEnabled(
        !bProductionNiagaraReady);
    TArray<ARaftSimWaterSurfaceActor::FBreakingSite> Sites;
    BreakingSurface->GetBreakingSites(Sites);
    if (Sites.IsEmpty())
    {
        for (UNiagaraComponent* Component : RapidAerosolNiagara)
        {
            SetNiagaraEmission(
                Component, false, FVector::ZeroVector, FVector::ForwardVector,
                1.0f, 0.0f);
        }
        for (UNiagaraComponent* Component : RapidRollerNiagara)
        {
            SetNiagaraEmission(
                Component, false, FVector::ZeroVector, FVector::ForwardVector,
                1.0f, 0.0f);
        }
        ActiveRapidNiagaraCount = 0;
        ActiveRapidRollerNiagaraCount = 0;
        return;
    }

    FVector CameraLocation = FVector::ZeroVector;
    bool bHasCamera = false;
    if (const APlayerController* Controller = GetWorld()->GetFirstPlayerController())
    {
        if (const APlayerCameraManager* Camera = Controller->PlayerCameraManager)
        {
            CameraLocation = Camera->GetCameraLocation();
            bHasCamera = true;
        }
    }

    // Bounded population: a few slowly rising, downstream-drifting vapour
    // puffs per breaking site. Every value is deterministic in site/instance
    // index and SimulationPhase, matching the other card populations.
    constexpr int32 kMaxAerosolInstances = 90;
    int32 Budget = kMaxAerosolInstances;
    for (int32 SiteIndex = 0; SiteIndex < Sites.Num() && Budget > 0; ++SiteIndex)
    {
        const ARaftSimWaterSurfaceActor::FBreakingSite& Site = Sites[SiteIndex];
        FVector Downstream = Site.WorldVelocityMps.GetSafeNormal2D();
        if (Downstream.IsNearlyZero())
        {
            Downstream = FVector(1.0f, 0.0f, 0.0f);
        }
        const FVector Across(-Downstream.Y, Downstream.X, 0.0f);
        const int32 PuffCount = FMath::Min(
            2 + FMath::RoundToInt(5.0f * Site.Intensity), Budget);
        for (int32 Puff = 0; Puff < PuffCount; ++Puff)
        {
            const int32 Seed = SiteIndex * 17 + Puff;
            const float Rate = FMath::Lerp(
                0.05f, 0.11f, DeterministicWave(Seed + 23, 0.0f, 1.0f));
            const float Rise = FMath::Fmod(
                SimulationPhase * Rate + Puff * 0.317f +
                    DeterministicWave(Seed + 47, 0.0f, 1.0f),
                1.0f);
            const float Sideways =
                (DeterministicWave(Seed + 71, SimulationPhase, 0.19f) - 0.5f) * 210.0f;
            const FVector Location = Site.WorldPositionCm +
                Downstream * (40.0f + 430.0f * Rise) +
                Across * Sideways +
                FVector::UpVector * (26.0f + 200.0f * Rise);
            // Puffs expand and thin as they rise; scale carries the expansion
            // while the shared card material's opacity stays constant.
            const float Grow = FMath::Lerp(0.28f, 0.95f, Rise) *
                FMath::Lerp(0.7f, 1.25f, Site.Intensity);
            const FRotator Rotation = bHasCamera
                ? MakeCameraFacingCardRotation(Location, CameraLocation)
                : FRotator(90.0f, 0.0f, 0.0f);
            RapidAerosolInstances->AddInstance(
                FTransform(
                    Rotation,
                    Location,
                    FVector(
                        Grow * FMath::Lerp(0.8f, 1.3f, DeterministicWave(Seed + 5, 0.0f, 1.0f)),
                        Grow,
                        1.0f)),
                true);
            --Budget;
        }
    }

    ActiveRapidNiagaraCount = 0;
    ActiveRapidRollerNiagaraCount = 0;
    if (bProductionNiagaraReady)
    {
        TArray<int32> RankedSiteIndices;
        RankedSiteIndices.Reserve(Sites.Num());
        for (int32 SiteIndex = 0; SiteIndex < Sites.Num(); ++SiteIndex)
        {
            const float DistanceSquared = bHasCamera
                ? FVector::DistSquared(
                    CameraLocation, Sites[SiteIndex].WorldPositionCm)
                : 0.0f;
            if (!bHasCamera ||
                DistanceSquared <= FMath::Square(RapidNiagaraCullDistanceCm))
            {
                RankedSiteIndices.Add(SiteIndex);
            }
        }
        if (bHasCamera)
        {
            RankedSiteIndices.Sort(
                [&Sites, &CameraLocation](int32 Left, int32 Right)
                {
                    return FVector::DistSquared(
                               CameraLocation, Sites[Left].WorldPositionCm) <
                        FVector::DistSquared(
                               CameraLocation, Sites[Right].WorldPositionCm);
                });
        }

        const int32 ActiveSiteBudget = FMath::Min3(
            MaxActiveRapidNiagaraSites,
            RankedSiteIndices.Num(),
            FMath::Min(
                RapidAerosolNiagara.Num(), RapidRollerNiagara.Num()));
        for (int32 PoolIndex = 0;
             PoolIndex < ActiveSiteBudget;
             ++PoolIndex)
        {
            const ARaftSimWaterSurfaceActor::FBreakingSite& Site =
                Sites[RankedSiteIndices[PoolIndex]];
            FVector Downstream = Site.WorldVelocityMps.GetSafeNormal2D();
            if (Downstream.IsNearlyZero())
            {
                Downstream = FVector::ForwardVector;
            }
            const float Intensity = FMath::Clamp(Site.Intensity, 0.0f, 1.0f);
            const float DistanceCm = bHasCamera
                ? FVector::Distance(CameraLocation, Site.WorldPositionCm)
                : 0.0f;
            const float DistanceDensity = bHasCamera
                ? 1.0f - FMath::Clamp(
                    (DistanceCm - RapidNiagaraFullDensityDistanceCm) /
                        (RapidNiagaraCullDistanceCm -
                         RapidNiagaraFullDensityDistanceCm),
                    0.0f,
                    1.0f)
                : 1.0f;
            const FVector Origin = Site.WorldPositionCm +
                Downstream * 35.0f + FVector::UpVector * 34.0f;
            const FVector DriftDirection =
                (Downstream * 0.86f + FVector::UpVector * 0.28f).GetSafeNormal();
            const bool bEnabled = Intensity > 0.12f;
            SetNiagaraEmission(
                RapidAerosolNiagara[PoolIndex],
                bEnabled,
                Origin,
                DriftDirection,
                FMath::Lerp(0.70f, 1.18f, Intensity),
                FMath::Lerp(6.0f, 28.0f, Intensity) * DistanceDensity);
            ActiveRapidNiagaraCount += bEnabled ? 1 : 0;

            const FVector RollerOrigin = Site.WorldPositionCm +
                Downstream * 48.0f + FVector::UpVector * 12.0f;
            const FVector RollerDirection =
                (Downstream * 0.68f + FVector::UpVector * 0.73f)
                    .GetSafeNormal();
            SetNiagaraEmission(
                RapidRollerNiagara[PoolIndex],
                bEnabled,
                RollerOrigin,
                RollerDirection,
                FMath::Lerp(0.78f, 1.15f, Intensity),
                FMath::Lerp(24.0f, 90.0f, Intensity) * DistanceDensity);
            ActiveRapidRollerNiagaraCount += bEnabled ? 1 : 0;
        }
        for (int32 PoolIndex = ActiveSiteBudget;
             PoolIndex < RapidAerosolNiagara.Num();
             ++PoolIndex)
        {
            SetNiagaraEmission(
                RapidAerosolNiagara[PoolIndex], false, FVector::ZeroVector,
                FVector::ForwardVector, 1.0f, 0.0f);
        }
        for (int32 PoolIndex = ActiveSiteBudget;
             PoolIndex < RapidRollerNiagara.Num();
             ++PoolIndex)
        {
            SetNiagaraEmission(
                RapidRollerNiagara[PoolIndex], false, FVector::ZeroVector,
                FVector::ForwardVector, 1.0f, 0.0f);
        }
    }
}

void ARaftSimWaterVfxActor::RefreshVfx(float DeltaSeconds)
{
    SimulationPhase += DeltaSeconds;
    // River aerosol is sourced from the live water surface's breaking sites,
    // not raft contact, so it refreshes before any raft-dependent early-out.
    RefreshRapidAerosol();
    if (!TrackedRaft || !WaterAdapter)
    {
        SetNiagaraEmission(
            SolverSprayNiagara, false, FVector::ZeroVector,
            FVector::ForwardVector, 1.0f, 0.0f);
        SetNiagaraEmission(
            ContactDropletNiagara, false, FVector::ZeroVector,
            FVector::ForwardVector, 1.0f, 0.0f);
        SetNiagaraEmission(
            AeratedMistNiagara, false, FVector::ZeroVector,
            FVector::ForwardVector, 1.0f, 0.0f);
        ClearInstances();
        HideContactWaterPatch();
        HideConnectedContactWaterV6Review();
        HideConnectedContactWaterV7Review();
        HideConnectedContactWaterV8Review();
        HideDepthBearingContactWaterV10Review();
        LastPresentationState = FRaftSimWaterVfxState();
        UnderwaterPostProcess->BlendWeight = 0.0f;
        return;
    }

    const FVector RaftLocationCm = TrackedRaft->GetActorLocation();
    FRaftSimWaterSample Sample;
    if (!WaterAdapter->SampleWaterAtWorldPosition(RaftLocationCm, Sample))
    {
        ClearInstances();
        HideContactWaterPatch();
        HideConnectedContactWaterV6Review();
        HideConnectedContactWaterV7Review();
        HideConnectedContactWaterV8Review();
        HideDepthBearingContactWaterV10Review();
        return;
    }
    const bool bCameraUnderwater = SampleCameraUnderwater();
    LastPresentationState = EvaluatePresentation(
        Sample,
        TrackedRaft->GetRaftVelocity(),
        TrackedRaft->GetActiveWaterContactCount(),
        TrackedRaft->GetMaximumWaterContactIndentationM(),
        bCameraUnderwater);
    UnderwaterPostProcess->BlendWeight = FMath::FInterpTo(
        UnderwaterPostProcess->BlendWeight,
        LastPresentationState.Underwater,
        FMath::Max(DeltaSeconds, RefreshIntervalSeconds),
        LastPresentationState.Underwater > 0.5f ? 9.0f : 4.5f);

    ClearInstances();
    if (!Sample.bWet)
    {
        SetNiagaraEmission(
            SolverSprayNiagara, false, FVector::ZeroVector,
            FVector::ForwardVector, 1.0f, 0.0f);
        SetNiagaraEmission(
            ContactDropletNiagara, false, FVector::ZeroVector,
            FVector::ForwardVector, 1.0f, 0.0f);
        SetNiagaraEmission(
            AeratedMistNiagara, false, FVector::ZeroVector,
            FVector::ForwardVector, 1.0f, 0.0f);
        HideContactWaterPatch();
        HideConnectedContactWaterV6Review();
        HideConnectedContactWaterV7Review();
        HideConnectedContactWaterV8Review();
        HideDepthBearingContactWaterV10Review();
        return;
    }

    FVector FlowDirection = Sample.VelocityMetersPerSecond.GetSafeNormal2D();
    if (FlowDirection.IsNearlyZero())
    {
        FlowDirection = TrackedRaft->GetActorForwardVector();
    }
    const FVector AcrossDirection(-FlowDirection.Y, FlowDirection.X, 0.0f);

    FVector DominantContactWorldCm = RaftLocationCm;
    FVector DominantContactNormal = AcrossDirection;
    float DominantIndentationM = 0.0f;
    const bool bHasDominantContact =
        TrackedRaft->GetDominantWaterContactPresentation(
            DominantContactWorldCm,
            DominantContactNormal,
            DominantIndentationM);
    const float ContactScale = FMath::Lerp(
        0.88f,
        1.12f,
        FMath::Clamp(DominantIndentationM / 0.22f, 0.0f, 1.0f));
    FRaftSimWaterSample ContactWaterSample;
    const bool bContactSampled = bHasDominantContact &&
        WaterAdapter->SampleWaterAtWorldPosition(
            DominantContactWorldCm, ContactWaterSample) &&
        ContactWaterSample.bWet;
    const float SurfaceZCm =
        (bContactSampled ? ContactWaterSample.SurfaceHeightMeters
                         : Sample.SurfaceHeightMeters) * CmPerM + 8.0f;
    FVector ContactOutward =
        (DominantContactWorldCm - RaftLocationCm).GetSafeNormal2D();
    if (ContactOutward.IsNearlyZero())
    {
        ContactOutward = -DominantContactNormal.GetSafeNormal2D();
    }
    if (ContactOutward.IsNearlyZero())
    {
        ContactOutward = AcrossDirection;
    }
    // A contacted tube segment is partly below the raft shell and beside the
    // obstacle. Move only the presentation anchor to the exposed upstream
    // hydraulic face of the same D4 contact. This does not change the solver,
    // water surface or collision pose.
    const float UpstreamPresentationOffsetCm = bHasDominantContact ? -65.0f : 0.0f;
    // DominantContactWorldCm is the contacted raft segment, not the exposed
    // outer face of the obstacle. Centering the 2.2 x 1.4 m visual shoulder
    // there left all 96 triangles beneath the production 1.2 m-radius rock.
    // Move only the continuous patch across that approximate radius so the
    // pile appears on visible water outside the pin. Spray and droplets keep
    // their physical contact origin; the sampled contact, D4 geometry, rock
    // transform, collision and forces are unchanged.
    const float OutwardPresentationOffsetCm =
        bHasDominantContact ? 55.0f : 0.0f;
    const FVector SurfaceCenter(
        (bHasDominantContact ? DominantContactWorldCm.X : RaftLocationCm.X) +
            FlowDirection.X * UpstreamPresentationOffsetCm,
        (bHasDominantContact ? DominantContactWorldCm.Y : RaftLocationCm.Y) +
            FlowDirection.Y * UpstreamPresentationOffsetCm,
        SurfaceZCm);
    const FVector ContactPatchCenter = SurfaceCenter +
        ContactOutward * OutwardPresentationOffsetCm;
    FVector ImpactDirection =
        (ContactOutward * 0.28f - FlowDirection * 0.72f).GetSafeNormal2D();
    if (ImpactDirection.IsNearlyZero())
    {
        ImpactDirection = -FlowDirection;
    }

    if (bProductionNiagaraReady)
    {
        // The D4 point is the compressed tube segment and can sit almost one
        // rock radius inside the review boulder. Launch particles from the
        // exposed edge of the already sampled contact shoulder so the volume
        // appears where displaced water actually escapes, while all force,
        // contact, water and scoring authority remains unchanged.
        const FVector ParticleSurfaceCenter = ContactPatchCenter +
            ContactOutward * (bHasDominantContact ? 78.0f : 0.0f);
        const FVector SprayDirection =
            (ImpactDirection * 0.46f + FVector::UpVector * 0.89f).GetSafeNormal();
        const FVector DropletDirection =
            (ImpactDirection * 0.32f + FVector::UpVector * 0.95f).GetSafeNormal();
        const FVector MistDirection =
            (FlowDirection * 0.76f + FVector::UpVector * 0.65f).GetSafeNormal();
        SetNiagaraEmission(
            SolverSprayNiagara,
            LastPresentationState.Spray > 0.08f,
            ParticleSurfaceCenter + FVector::UpVector * 8.0f,
            SprayDirection,
            FMath::Lerp(0.72f, 1.06f, LastPresentationState.Spray) * ContactScale,
            156.0f * LastPresentationState.Spray);
        SetNiagaraEmission(
            ContactDropletNiagara,
            LastPresentationState.Droplets > 0.10f,
            ParticleSurfaceCenter + FVector::UpVector * 12.0f,
            DropletDirection,
            FMath::Lerp(0.74f, 1.04f, LastPresentationState.Droplets) * ContactScale,
            176.0f * LastPresentationState.Droplets);
        const float NiagaraVisibleMist = FMath::Clamp(
            (LastPresentationState.Mist - 0.18f) / 0.82f, 0.0f, 1.0f);
        SetNiagaraEmission(
            AeratedMistNiagara,
            NiagaraVisibleMist > 0.02f,
            ParticleSurfaceCenter + FlowDirection * 70.0f +
                FVector::UpVector * 52.0f,
            MistDirection,
            FMath::Lerp(0.70f, 1.08f, NiagaraVisibleMist),
            34.0f * NiagaraVisibleMist);
    }

    if (bHasDominantContact && bContactSampled &&
        LastPresentationState.ImpactSheet > 0.24f)
    {
        UpdateContactWaterPatch(
            ContactPatchCenter,
            FlowDirection,
            AcrossDirection,
            LastPresentationState.ImpactSheet,
            ContactScale);
        if (bConnectedContactWaterV6Review)
        {
            UpdateConnectedContactWaterV6Review(
                ContactPatchCenter,
                FlowDirection,
                AcrossDirection,
                ContactOutward,
                ImpactDirection,
                LastPresentationState.ImpactSheet,
                ContactScale);
        }
        else
        {
            HideConnectedContactWaterV6Review();
        }
        if (bConnectedContactWaterV7Review)
        {
            UpdateConnectedContactWaterV7Review(
                ContactPatchCenter,
                FlowDirection,
                AcrossDirection,
                ContactOutward,
                ImpactDirection,
                LastPresentationState.ImpactSheet,
                ContactScale);
        }
        else
        {
            HideConnectedContactWaterV7Review();
        }
        if (bConnectedContactWaterV8Review)
        {
            UpdateConnectedContactWaterV8Review(
                ContactPatchCenter,
                FlowDirection,
                AcrossDirection,
                ContactOutward,
                ImpactDirection,
                LastPresentationState.ImpactSheet,
                ContactScale);
        }
        else
        {
            HideConnectedContactWaterV8Review();
        }
        if (bDepthBearingContactWaterV10Review)
        {
            UpdateDepthBearingContactWaterV10Review(
                ContactPatchCenter,
                FlowDirection,
                AcrossDirection,
                ContactOutward,
                ImpactDirection,
                LastPresentationState.ImpactSheet,
                ContactScale);
        }
        else
        {
            HideDepthBearingContactWaterV10Review();
        }
    }
    else
    {
        HideContactWaterPatch();
        HideConnectedContactWaterV6Review();
        HideConnectedContactWaterV7Review();
        HideConnectedContactWaterV8Review();
        HideDepthBearingContactWaterV10Review();
    }

    FVector CameraLocation = SurfaceCenter - FlowDirection * 500.0f +
        FVector::UpVector * 280.0f;
    if (const UWorld* World = GetWorld())
    {
        const APlayerController* Controller = World->GetFirstPlayerController();
        const APlayerCameraManager* Camera =
            Controller ? Controller->PlayerCameraManager : nullptr;
        if (Camera)
        {
            CameraLocation = Camera->GetCameraLocation();
        }
    }

    // Fine spray reads as a volume only when no billboard dominates. Spend the
    // same bounded presentation budget on more, smaller, lower-opacity cards;
    // deterministic low-discrepancy phase, source-width and arc variation keep
    // the cloud from becoming a necklace. D4 and water authority are untouched.
    const int32 SprayCount = FMath::RoundToInt(
        74.0f * LastPresentationState.Spray +
        22.0f * LastPresentationState.ImpactSheet);
    for (int32 Index = 0; Index < SprayCount; ++Index)
    {
        const float Rate = FMath::Lerp(
            0.43f,
            0.73f,
            DeterministicWave(Index + 113, 0.0f, 1.0f));
        const float PhaseJitter =
            DeterministicWave(Index + 197, 0.0f, 1.0f) * 0.37f;
        const float Travel = FMath::Fmod(
            SimulationPhase * Rate +
                static_cast<float>(Index) * 0.61803398875f +
                PhaseJitter,
            1.0f);
        const float ArcBase = FMath::Max(
            4.0f * Travel * (1.0f - Travel), 0.0f);
        const float Arc = FMath::Pow(
            ArcBase,
            FMath::Lerp(
                0.76f,
                1.32f,
                DeterministicWave(Index + 151, 0.0f, 1.0f)));
        const float SourceAcross =
            (DeterministicWave(Index + 31, 0.0f, 1.0f) - 0.5f) * 46.0f;
        const float TurbulentAcross =
            (DeterministicWave(Index + 61, SimulationPhase, 0.71f) - 0.5f) *
            FMath::Lerp(24.0f, 86.0f, Travel);
        const float JetReach = FMath::Lerp(
            48.0f,
            92.0f,
            DeterministicWave(Index + 83, 0.0f, 1.0f));
        const float JetHeight = FMath::Lerp(
            36.0f,
            72.0f,
            DeterministicWave(Index + 137, 0.0f, 1.0f));
        const FVector Location = SurfaceCenter +
            ImpactDirection * (8.0f + JetReach * Travel) +
            AcrossDirection * (SourceAcross + TurbulentAcross) +
            FVector::UpVector * (5.0f + JetHeight * Arc);
        const float Shape = DeterministicWave(Index + 73, 0.0f, 1.0f);
        const float Streak = FMath::Pow(
            DeterministicWave(Index + 211, 0.0f, 1.0f), 3.0f);
        const float HeightScale = FMath::Lerp(
            0.008f,
            FMath::Lerp(0.038f, 0.075f, Streak),
            Arc) * ContactScale *
            FMath::Lerp(0.90f, 1.12f, LastPresentationState.Spray);
        const float WidthScale = FMath::Lerp(0.004f, 0.022f, Shape);
        SprayInstances->AddInstance(
            FTransform(
                MakeCameraFacingCardRotation(Location, CameraLocation),
                Location,
                FVector(HeightScale, WidthScale, 1.0f)),
            true);
    }

    const int32 DropletCount = FMath::RoundToInt(
        112.0f * LastPresentationState.Droplets +
        32.0f * LastPresentationState.ImpactSheet);
    for (int32 Index = 0; Index < DropletCount; ++Index)
    {
        const float Travel = FMath::Fmod(
            SimulationPhase * 0.92f + Index * 0.137f, 1.0f);
        const float Arc = 4.0f * Travel * (1.0f - Travel);
        const FVector Location = SurfaceCenter +
            ImpactDirection * (15.0f + 80.0f * Travel) +
            AcrossDirection *
                ((DeterministicWave(Index + 17, 0.0f, 1.0f) - 0.5f) * 90.0f) +
            FVector::UpVector * (8.0f + 65.0f * Arc);
        const float Shape = DeterministicWave(Index + 9, 0.0f, 1.0f);
        const float HeightScale = FMath::Lerp(0.003f, 0.014f, Arc);
        const float WidthScale = FMath::Lerp(0.002f, 0.007f, Shape);
        DropletInstances->AddInstance(
            FTransform(
                MakeCameraFacingCardRotation(Location, CameraLocation),
                Location,
                FVector(HeightScale, WidthScale, 1.0f)),
            true);
    }

    // Calm-water classifier residue must not create a single opaque-looking
    // sphere beside the raft. Mist begins only once hydraulic aeration is
    // visually meaningful, then uses more, much smaller anisotropic puffs so
    // the cluster reads as suspended spray rather than floating white discs.
    const float VisibleMist = FMath::Clamp(
        (LastPresentationState.Mist - 0.18f) / 0.82f, 0.0f, 1.0f);
    const int32 MistCount = FMath::RoundToInt(28.0f * VisibleMist);
    for (int32 Index = 0; Index < MistCount; ++Index)
    {
        const float Drift = FMath::Fmod(SimulationPhase * 0.12f + Index * 0.173f, 1.0f);
        const FVector Location = SurfaceCenter +
            FlowDirection * (70.0f + Drift * 390.0f) +
            AcrossDirection *
                ((DeterministicWave(Index + 5, 0.0f, 1.0f) - 0.5f) * 360.0f) +
            FVector::UpVector * (72.0f + Drift * 145.0f);
        const float Shape = DeterministicWave(Index + 19, 0.0f, 1.0f);
        MistInstances->AddInstance(
            FTransform(
                MakeCameraFacingCardRotation(Location, CameraLocation),
                Location,
                FVector(
                    FMath::Lerp(0.12f, 0.30f, Shape),
                    FMath::Lerp(0.18f, 0.42f, Shape),
                    1.0f)),
            true);
    }

    // Soft horizontal foam cards make the contact-water footprint readable
    // without lifting or replacing the authoritative free surface. Placement
    // follows the dominant D4 segment, flow direction and ImpactSheet energy;
    // the fixed upper bound remains cheaper than the former sphere pools.
    const int32 ImpactFoamCount = FMath::RoundToInt(
        6.0f * LastPresentationState.ImpactSheet +
        3.0f * LastPresentationState.Spray);
    for (int32 Index = 0; Index < ImpactFoamCount; ++Index)
    {
        const float Travel = FMath::Fmod(
            SimulationPhase * 0.18f + Index * 0.193f, 1.0f);
        const float Shape = DeterministicWave(Index + 41, 0.0f, 1.0f);
        const float Side =
            (DeterministicWave(Index + 67, 0.0f, 1.0f) - 0.5f) * 100.0f;
        const FVector Location = SurfaceCenter +
            FlowDirection * (-25.0f + 125.0f * Travel) +
            AcrossDirection * Side +
            FVector::UpVector * (4.0f + static_cast<float>(Index % 3) * 1.5f);
        const float YawJitter =
            (DeterministicWave(Index + 89, 0.0f, 1.0f) - 0.5f) * 34.0f;
        SheetInstances->AddInstance(
            FTransform(
                FRotator(0.0f, FlowDirection.Rotation().Yaw + YawJitter, 0.0f),
                Location,
                FVector(
                    FMath::Lerp(0.35f, 1.00f, Shape) * ContactScale,
                    FMath::Lerp(0.12f, 0.28f, 1.0f - Shape),
                    1.0f)),
            true);
    }
}

void ARaftSimWaterVfxActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    TimeSinceRefresh += DeltaSeconds;
    if (TimeSinceRefresh >= RefreshIntervalSeconds)
    {
        const float RefreshDelta = TimeSinceRefresh;
        TimeSinceRefresh = 0.0f;
        RefreshVfx(RefreshDelta);
    }
}
