#include "RaftSimWaterSurfaceActor.h"

#include "Engine/GameInstance.h"
#include "Engine/Texture2D.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/UObjectGlobals.h"

namespace
{
constexpr float kSurfCmPerM = 100.0f;
constexpr float kGravity = 9.80665f;
// Static full-reach water uses one material repeat per approximately three
// river metres. Keep the moving solver patch in the same river-coordinate
// basis so normal-map scale does not stretch or pop as the grid recentres.
constexpr float kWaterTextureRepeatMeters = 3.0f;
// The opaque optical core is station-clipped before the rectangular moving
// window ends, but it reaches the complete sampled wet bank. Requiring four
// wet corners is the lateral mask; applying the combined alpha here instead
// would leave an artificial three-metre dry strip beside the water.
constexpr float kLiveVolumeCoreMinimumStationCoverage = 0.60f;
constexpr float kLiveVolumeCoreOffsetCm = 1.0f;
constexpr float kLiveVolumeCoreCalmDetailCoverage = 0.035f;
constexpr float kLiveVolumeCoreActiveDetailCoverage = 0.14f;
// Rivers that retain an authored Single Layer Water body still need the live
// mesh to expose the current. This bounded translucent skin carries only
// solver-velocity detail; the authored mesh remains the optical water volume.
constexpr float kAuthoredCarrierCalmDetailCoverage = 0.12f;
constexpr float kAuthoredCarrierActiveDetailCoverage = 0.42f;

TAutoConsoleVariable<int32> CVarRaftSimDownstreamBoilMicrorelief(
    TEXT("RaftSim.Water.DownstreamBoilMicrorelief"),
    1,
    TEXT("Enable solver-anchored presentation-only downstream boil microrelief. ")
    TEXT("Default 1; set 0 only for matched visual diagnostics."),
    ECVF_Default);


float ComputeStationEdgeCoverage(
    int32 StationIndex,
    int32 StationCount,
    float VertexSpacingMeters,
    float EdgeBlendMeters)
{
    const int32 EdgeSteps = FMath::Min(
        StationIndex, FMath::Max(StationCount - 1 - StationIndex, 0));
    const float EdgeDistanceMeters = EdgeSteps * FMath::Max(VertexSpacingMeters, 0.0f);
    const float LinearCoverage = FMath::Clamp(
        EdgeDistanceMeters / FMath::Max(EdgeBlendMeters, KINDA_SMALL_NUMBER),
        0.0f,
        1.0f);
    // Smoothstep prevents a visible alpha band where the surface-lit overlay
    // reaches full coverage while retaining deterministic vertex values.
    return LinearCoverage * LinearCoverage * (3.0f - 2.0f * LinearCoverage);
}

float ComputeLateralWetCoverage(
    int32 LateralIndex,
    int32 MinimumWetLateralIndex,
    int32 MaximumWetLateralIndex,
    float VertexSpacingMeters,
    float EdgeBlendMeters)
{
    const int32 EdgeSteps = FMath::Min(
        LateralIndex - MinimumWetLateralIndex,
        MaximumWetLateralIndex - LateralIndex);
    // The wet/dry transition lies between two sampled vertices. The outermost
    // wet vertex must be fully transparent; even a small residual opacity
    // becomes a sharp polygon against reflective authored water.
    const float EdgeDistanceMeters =
        FMath::Max(EdgeSteps, 0) * FMath::Max(VertexSpacingMeters, 0.0f);
    const float LinearCoverage = FMath::Clamp(
        EdgeDistanceMeters / FMath::Max(EdgeBlendMeters, KINDA_SMALL_NUMBER),
        0.0f,
        1.0f);
    return LinearCoverage * LinearCoverage * (3.0f - 2.0f * LinearCoverage);
}

float ComputePresentationBankProfile(float StationMeters, bool bRiverLeft)
{
    const float SidePhase = bRiverLeft ? 2.173f : -0.827f;
    return
        0.55f * FMath::Sin(StationMeters * 0.052f + SidePhase) +
        0.30f * FMath::Sin(StationMeters * 0.137f - SidePhase * 0.73f) +
        0.15f * FMath::Sin(StationMeters * 0.319f + SidePhase * 1.61f);
}
}

float ARaftSimWaterSurfaceActor::ComputePresentationSurfaceEdgeClearanceMeters(
    int32 StationIndex,
    int32 StationCount,
    int32 LateralIndex,
    int32 MinimumWetLateralIndex,
    int32 MaximumWetLateralIndex,
    float InVertexSpacingMeters)
{
    if (StationCount <= 0 || StationIndex < 0 || StationIndex >= StationCount ||
        MinimumWetLateralIndex < 0 ||
        MaximumWetLateralIndex < MinimumWetLateralIndex ||
        LateralIndex < MinimumWetLateralIndex ||
        LateralIndex > MaximumWetLateralIndex)
    {
        return 0.0f;
    }
    const int32 StationEdgeSteps = FMath::Min(
        StationIndex, StationCount - 1 - StationIndex);
    const int32 LateralEdgeSteps = FMath::Min(
        LateralIndex - MinimumWetLateralIndex,
        MaximumWetLateralIndex - LateralIndex);
    return FMath::Min(StationEdgeSteps, LateralEdgeSteps) *
        FMath::Max(InVertexSpacingMeters, 0.0f);
}

float ARaftSimWaterSurfaceActor::ComputePresentationBankCoverage(
    float StationMeters,
    int32 LateralIndex,
    int32 MinimumWetLateralIndex,
    int32 MaximumWetLateralIndex,
    float InVertexSpacingMeters,
    float EdgeBlendMeters,
    bool bEnableNaturalism,
    float NaturalismAmplitudeMeters)
{
    const float BaseCoverage = ComputeLateralWetCoverage(
        LateralIndex,
        MinimumWetLateralIndex,
        MaximumWetLateralIndex,
        InVertexSpacingMeters,
        EdgeBlendMeters);
    const int32 RiverRightSteps =
        LateralIndex - MinimumWetLateralIndex;
    const int32 RiverLeftSteps =
        MaximumWetLateralIndex - LateralIndex;
    const int32 EdgeSteps = FMath::Min(RiverRightSteps, RiverLeftSteps);
    if (!bEnableNaturalism || NaturalismAmplitudeMeters <= 0.0f ||
        EdgeSteps <= 0 || MinimumWetLateralIndex < 0 ||
        MaximumWetLateralIndex < MinimumWetLateralIndex)
    {
        return BaseCoverage;
    }

    // Anchor three incommensurate bands in global river station so the visual
    // contour is deterministic across moving-window recentres. Independent
    // side phases prevent the two banks from reading as a mirrored ribbon.
    const bool bNearestRiverLeft = RiverLeftSteps < RiverRightSteps;
    const float BankProfile = ComputePresentationBankProfile(
        StationMeters, bNearestRiverLeft);
    const float EdgeDistanceMeters =
        EdgeSteps * FMath::Max(InVertexSpacingMeters, 0.0f);
    const float ShiftedEdgeDistanceMeters = FMath::Max(
        EdgeDistanceMeters +
            BankProfile * FMath::Clamp(NaturalismAmplitudeMeters, 0.0f, 1.25f),
        0.0f);
    const float LinearCoverage = FMath::Clamp(
        ShiftedEdgeDistanceMeters /
            FMath::Max(EdgeBlendMeters, KINDA_SMALL_NUMBER),
        0.0f,
        1.0f);
    return LinearCoverage * LinearCoverage *
        (3.0f - 2.0f * LinearCoverage);
}

float ARaftSimWaterSurfaceActor::ComputePresentationBankRetreatMeters(
    float StationMeters,
    bool bRiverLeft,
    float InVertexSpacingMeters,
    bool bEnableNaturalism,
    float NaturalismAmplitudeMeters)
{
    if (!bEnableNaturalism || NaturalismAmplitudeMeters <= 0.0f ||
        InVertexSpacingMeters <= 0.0f)
    {
        return 0.0f;
    }
    const float BankProfile = FMath::Clamp(
        ComputePresentationBankProfile(StationMeters, bRiverLeft),
        -1.0f,
        1.0f);
    const float NormalizedRetreat =
        0.35f + 0.65f * (0.5f + 0.5f * BankProfile);
    return FMath::Min(
        FMath::Clamp(NaturalismAmplitudeMeters, 0.0f, 1.25f) *
            NormalizedRetreat,
        InVertexSpacingMeters * 0.80f);
}

ARaftSimWaterSurfaceActor::ARaftSimWaterSurfaceActor()
{
    PrimaryActorTick.bCanEverTick = true;

    SurfaceMesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("SurfaceMesh"));
    SetRootComponent(SurfaceMesh);
    SurfaceMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    // The authored river already receives terrain/sun shadows. This
    // translucent solver overlay must not cast a second hard rectangular
    // shadow from its moving grid or wet/dry boundary.
    SurfaceMesh->SetCastShadow(false);
    SurfaceMesh->SetCanEverAffectNavigation(false);
    SurfaceMesh->ComponentTags.AddUnique(
        TEXT("RaftSimSolverAnchoredDownstreamBoilMicroreliefV1"));
    SurfaceMesh->bUseAsyncCooking = true;

    LiveVolumeCoreMesh = CreateDefaultSubobject<UProceduralMeshComponent>(
        TEXT("LiveVolumeCoreMesh"));
    LiveVolumeCoreMesh->SetupAttachment(SurfaceMesh);
    LiveVolumeCoreMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    LiveVolumeCoreMesh->SetCastShadow(false);
    LiveVolumeCoreMesh->SetCanEverAffectNavigation(false);
    LiveVolumeCoreMesh->SetMobility(EComponentMobility::Movable);
    LiveVolumeCoreMesh->SetVisibility(false, true);
    LiveVolumeCoreMesh->ComponentTags.AddUnique(
        TEXT("RaftSimLiveSolverVolumeCore"));
    LiveVolumeCoreMesh->bUseAsyncCooking = true;

    BreakingLipMesh = CreateDefaultSubobject<UProceduralMeshComponent>(
        TEXT("BreakingLipMesh"));
    BreakingLipMesh->SetupAttachment(SurfaceMesh);
    BreakingLipMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BreakingLipMesh->SetCastShadow(false);
    BreakingLipMesh->SetCanEverAffectNavigation(false);
    BreakingLipMesh->SetMobility(EComponentMobility::Movable);
    BreakingLipMesh->SetTranslucentSortPriority(1);
    BreakingLipMesh->SetVisibility(false, true);
    BreakingLipMesh->bUseAsyncCooking = true;

    BreakingRollerVolumeMesh = CreateDefaultSubobject<UProceduralMeshComponent>(
        TEXT("BreakingRollerVolumeMesh"));
    BreakingRollerVolumeMesh->SetupAttachment(SurfaceMesh);
    BreakingRollerVolumeMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BreakingRollerVolumeMesh->SetCastShadow(false);
    BreakingRollerVolumeMesh->SetCanEverAffectNavigation(false);
    BreakingRollerVolumeMesh->SetMobility(EComponentMobility::Movable);
    BreakingRollerVolumeMesh->SetTranslucentSortPriority(2);
    BreakingRollerVolumeMesh->SetVisibility(false, true);
    BreakingRollerVolumeMesh->ComponentTags.AddUnique(
        TEXT("RaftSimSolverAnchoredAeratedCrestThicknessV1"));
    BreakingRollerVolumeMesh->bUseAsyncCooking = true;

    RapidFoamMesh = CreateDefaultSubobject<UProceduralMeshComponent>(
        TEXT("RapidFoamMesh"));
    RapidFoamMesh->SetupAttachment(SurfaceMesh);
    RapidFoamMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    RapidFoamMesh->SetCastShadow(false);
    RapidFoamMesh->SetCanEverAffectNavigation(false);
    RapidFoamMesh->SetMobility(EComponentMobility::Movable);
    RapidFoamMesh->SetTranslucentSortPriority(3);
    RapidFoamMesh->SetVisibility(false, true);
    RapidFoamMesh->ComponentTags.AddUnique(TEXT("RaftSimLiveSolverRapidFoam"));
    RapidFoamMesh->bUseAsyncCooking = true;

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> WaterMat(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_LiveRiverSurface.M_RaftSim_LiveRiverSurface"));
    if (WaterMat.Succeeded())
    {
        WaterMaterial = WaterMat.Object;
    }
    else
    {
        // Fallback before the presentation-safe live material is authored.
        static ConstructorHelpers::FObjectFinder<UMaterialInterface> FallbackMat(
            TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater."
                 "M_RaftSim_PhotorealRiverWater"));
        if (FallbackMat.Succeeded())
        {
            WaterMaterial = FallbackMat.Object;
        }
    }

    // This project-owned parent is the shared photoreal Single Layer Water
    // graph with the runtime raft-floor transmission aperture already wired.
    // Its legacy SouthFork path is retained for asset compatibility; all
    // river-specific optical values are supplied by the dynamic instance.
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> VolumeCoreMat(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
             "M_RaftSim_SouthForkRaftTransmissionWater."
             "M_RaftSim_SouthForkRaftTransmissionWater"));
    if (VolumeCoreMat.Succeeded())
    {
        LiveVolumeCoreMaterial = VolumeCoreMat.Object;
    }

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> BreakingWaterMat(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_BreakingWaterLip."
             "M_RaftSim_BreakingWaterLip"));
    if (BreakingWaterMat.Succeeded())
    {
        BreakingWaterMaterial = BreakingWaterMat.Object;
    }
    else
    {
        // Authoring-safe fallback: before the dedicated package exists, retain
        // the project-owned two-sided aerated-water material rather than a
        // default checkerboard. Release validation requires the production
        // package and never qualifies this fallback.
        static ConstructorHelpers::FObjectFinder<UMaterialInterface> FallbackBreakingWaterMat(
            TEXT("/Game/RaftSim/Materials/M_RaftSim_SprayMist.M_RaftSim_SprayMist"));
        if (FallbackBreakingWaterMat.Succeeded())
        {
            BreakingWaterMaterial = FallbackBreakingWaterMat.Object;
        }
    }

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> RapidFoamMat(
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "M_RaftSim_SolverFieldFoamCandidate."
             "M_RaftSim_SolverFieldFoamCandidate"));
    if (RapidFoamMat.Succeeded())
    {
        RapidFoamMaterial = RapidFoamMat.Object;
    }

    static ConstructorHelpers::FObjectFinder<UMaterialParameterCollection>
        FoamOcclusionCollection(
            TEXT("/Game/RaftSim/Materials/MPC_RaftSim_RaftFoamOcclusion."
                 "MPC_RaftSim_RaftFoamOcclusion"));
    if (FoamOcclusionCollection.Succeeded())
    {
        RaftFoamOcclusionCollection = FoamOcclusionCollection.Object;
    }
}

float ARaftSimWaterSurfaceActor::ComputePresentationStandingWaveDisplacementMeters(
    const FVector2D& RiverCoordinatesMeters,
    float SpeedMetersPerSecond,
    float DepthMeters)
{
    return URaftSimWaterRuntimeAdapter::ComputeCoupledStandingWave(
               RiverCoordinatesMeters,
               SpeedMetersPerSecond,
               DepthMeters)
        .DisplacementMeters;
}

float ARaftSimWaterSurfaceActor::ComputePresentationHydraulicReliefDisplacementMeters(
    float CenterSurfaceHeightMeters,
    float UpstreamFarSurfaceHeightMeters,
    float UpstreamNearSurfaceHeightMeters,
    float DownstreamNearSurfaceHeightMeters,
    float DownstreamFarSurfaceHeightMeters,
    float SpeedMetersPerSecond,
    float DepthMeters)
{
    return URaftSimWaterRuntimeAdapter::ComputeCoupledHydraulicReliefMeters(
        CenterSurfaceHeightMeters,
        UpstreamFarSurfaceHeightMeters,
        UpstreamNearSurfaceHeightMeters,
        DownstreamNearSurfaceHeightMeters,
        DownstreamFarSurfaceHeightMeters,
        SpeedMetersPerSecond,
        DepthMeters);
}

float ARaftSimWaterSurfaceActor::ComputePresentationSmoothedSurfaceHeightMeters(
    float CenterSurfaceHeightMeters,
    float UpstreamSurfaceHeightMeters,
    float DownstreamSurfaceHeightMeters,
    float RiverRightSurfaceHeightMeters,
    float RiverLeftSurfaceHeightMeters,
    float Strength)
{
    return URaftSimWaterRuntimeAdapter::
        ComputeCoupledSmoothedSurfaceHeightMeters(
            CenterSurfaceHeightMeters,
            UpstreamSurfaceHeightMeters, DownstreamSurfaceHeightMeters,
            RiverRightSurfaceHeightMeters, RiverLeftSurfaceHeightMeters,
            Strength);
}

float ARaftSimWaterSurfaceActor::ComputeRaftHullSurfaceExclusion(
    const FVector& WorldPositionCm,
    const FVector& RaftCenterCm,
    const FVector& RaftForward)
{
    FVector Forward = RaftForward.GetSafeNormal2D();
    if (Forward.IsNearlyZero())
    {
        Forward = FVector::ForwardVector;
    }
    const FVector Delta = WorldPositionCm - RaftCenterCm;
    const FVector Across(-Forward.Y, Forward.X, 0.0f);
    constexpr float HullHalfLengthCm = 320.0f;
    constexpr float HullHalfWidthCm = 190.0f;
    const float Along =
        FVector::DotProduct(Delta, Forward) / HullHalfLengthCm;
    const float AcrossDistance =
        FVector::DotProduct(Delta, Across) / HullHalfWidthCm;
    const float EllipseSquared = Along * Along + AcrossDistance * AcrossDistance;
    return FMath::SmoothStep(0.72f, 1.30f, EllipseSquared);
}

FVector2D ARaftSimWaterSurfaceActor::ComputeBreakingLipProfileCentimeters(
    float NormalizedCurl,
    float Intensity)
{
    const float SafeCurl = FMath::Clamp(NormalizedCurl, 0.0f, 1.0f);
    const float SafeIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
    // Resolved low/moderate jumps form an attached hydraulic roller rather
    // than a glassy cylindrical curl. Only strong jumps blend into the full
    // 240-degree overhang, preserving genuine multi-valued water without
    // exaggerating the common South Fork response used by the hero camera.
    // The moderate profile rises quickly, then decays into a long aerated tail.
    const float ArchTravelCm = FMath::Lerp(280.0f, 380.0f, SafeIntensity);
    const float ArchHeightCm = FMath::Lerp(30.0f, 105.0f, SafeIntensity);
    const float PrimaryRoller =
        FMath::Sin(PI * SafeCurl) * FMath::Lerp(1.0f, 0.58f, SafeCurl);
    const float DownstreamShoulder =
        0.34f * SafeCurl * FMath::Max(FMath::Sin(3.0f * PI * SafeCurl), 0.0f);
    const FVector2D ArchProfile(
        ArchTravelCm * SafeCurl,
        ArchHeightCm * (PrimaryRoller + DownstreamShoulder));
    const float Theta = -0.5f * PI + SafeCurl * (4.0f * PI / 3.0f);
    const float RadiusCm = FMath::Lerp(60.0f, 130.0f, SafeIntensity);
    const float HeightCm = FMath::Lerp(35.0f, 105.0f, SafeIntensity);
    const FVector2D CurlProfile(
        RadiusCm * (FMath::Sin(Theta) + 1.0f),
        HeightCm * FMath::Cos(Theta));
    float CurlBlend = FMath::Clamp(
        (SafeIntensity - 0.55f) / 0.30f, 0.0f, 1.0f);
    CurlBlend = CurlBlend * CurlBlend * (3.0f - 2.0f * CurlBlend);
    return FMath::Lerp(ArchProfile, CurlProfile, CurlBlend);
}

FVector2D ARaftSimWaterSurfaceActor::ComputeBreakingRollerVolumeProfileCentimeters(
    float NormalizedLoop,
    float Intensity,
    float LayerNormalized)
{
    const float SafeLoop = FMath::Clamp(NormalizedLoop, 0.0f, 1.0f);
    const float SafeIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
    const float SafeLayer = FMath::Clamp(LayerNormalized, 0.0f, 1.0f);
    // An open 270-degree loop follows the hydraulic roller circulation: the
    // first edge starts inside the downstream pile, the crown rises above the
    // sampled surface, and the last edge folds upstream into the plunge face.
    // LayerNormalized offsets the bounded fallback shells through the aerated
    // body; it never creates a gameplay volume or solver surface.
    const float Theta = -0.25f * PI + SafeLoop * 1.5f * PI;
    const float CenterTravelCm =
        FMath::Lerp(150.0f, 205.0f, SafeIntensity) +
        FMath::Lerp(-24.0f, 34.0f, SafeLayer);
    const float TravelRadiusCm =
        FMath::Lerp(78.0f, 142.0f, SafeIntensity) *
        FMath::Lerp(0.82f, 1.10f, SafeLayer);
    const float HeightRadiusCm =
        FMath::Lerp(60.0f, 120.0f, SafeIntensity) *
        FMath::Lerp(0.82f, 1.10f, SafeLayer);
    const float CenterLiftCm =
        FMath::Lerp(14.0f, 30.0f, SafeIntensity) + 7.0f * SafeLayer;
    return FVector2D(
        CenterTravelCm + TravelRadiusCm * FMath::Cos(Theta),
        CenterLiftCm + HeightRadiusCm * FMath::Sin(Theta));
}

FVector2D ARaftSimWaterSurfaceActor::ComputeBreakingPlungePocketPresentation(
    float DownstreamMeters,
    float AcrossMeters,
    float Intensity)
{
    const float SafeIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
    if (SafeIntensity <= KINDA_SMALL_NUMBER)
    {
        return FVector2D::ZeroVector;
    }

    // The accepted breaking site already proves a local supercritical-to-
    // subcritical transition. Shape only its render surface into the minimum
    // readable plan-view hydraulic structure: a compact dark plunge pocket,
    // irregular side shoulders, and an aerated downstream return. The shape
    // is sampled on the refined render grid and is not a claim about measured
    // Zambezi bathymetry or seasonal hydraulics.
    const float PlungeStation = (DownstreamMeters - 1.8f) / 2.2f;
    const float PlungeAcross = AcrossMeters / 2.8f;
    const float PlungeCore = FMath::Exp(
        -(PlungeStation * PlungeStation + PlungeAcross * PlungeAcross));

    const float ReturnStation = (DownstreamMeters - 5.0f) / 2.4f;
    const float ReturnAcross = AcrossMeters / 3.4f;
    const float AeratedReturn = FMath::Exp(
        -(ReturnStation * ReturnStation + ReturnAcross * ReturnAcross));

    const float ShoulderStation = (DownstreamMeters - 2.3f) / 3.2f;
    const float ShoulderAcross =
        (FMath::Abs(AcrossMeters) - 3.0f) / 1.15f;
    const float BrokenShoulder = FMath::Exp(
        -(ShoulderStation * ShoulderStation +
            ShoulderAcross * ShoulderAcross));
    const float ShoulderVariation = FMath::Clamp(
        0.72f +
            0.18f * FMath::Sin(DownstreamMeters * 2.17f + AcrossMeters * 1.31f) +
            0.10f * FMath::Sin(DownstreamMeters * 4.03f - AcrossMeters * 2.27f),
        0.36f,
        1.0f);

    const float DisplacementMeters = FMath::Clamp(
        SafeIntensity *
            (-0.30f * PlungeCore +
                0.14f * AeratedReturn +
                0.10f * BrokenShoulder * ShoulderVariation),
        -0.28f * SafeIntensity,
        0.16f * SafeIntensity);
    // An accepted hydraulic jump is already a binary breaking-water event.
    // Do not multiply its entire optical response by the raw detector score:
    // moderate but valid jumps then fell below river-specific lace thresholds
    // and appeared glassy. Intensity still controls the spread, while this
    // remap guarantees a white, perforated aerated core at every accepted jump.
    const float BreakingFrothStrength = FMath::Lerp(
        0.62f, 1.0f, FMath::Sqrt(SafeIntensity));
    const float FoamGeneration = FMath::Clamp(
        BreakingFrothStrength *
            (0.28f * PlungeCore +
                1.00f * AeratedReturn +
                0.78f * BrokenShoulder * ShoulderVariation),
        0.0f,
        1.0f);
    return FVector2D(DisplacementMeters, FoamGeneration);
}

FVector2D ARaftSimWaterSurfaceActor::ComputeBreakingDownstreamBoilPresentation(
    float DownstreamMeters,
    float AcrossMeters,
    float Intensity,
    float PhaseSeconds,
    float SitePhaseRadians)
{
    const float SafeIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
    if (SafeIntensity <= KINDA_SMALL_NUMBER ||
        DownstreamMeters <= 3.8f || DownstreamMeters >= 20.5f)
    {
        return FVector2D::ZeroVector;
    }

    // A hydraulic-jump site is required before this function is called. Three
    // differently sized, skewed cells then make the downstream return legible
    // on the refined render grid. Mexican-hat profiles provide a raised
    // upwelling and a shallow compensating trough; offset centres, unequal
    // radii, independent drift, and phase-warped shoulders prevent a repeated
    // bullseye pattern. This is a visual approximation, not recirculating
    // solver velocity or a claim about measured river bathymetry.
    float DisplacementMeters = 0.0f;
    float FoamGeneration = 0.0f;
    auto AccumulateCell = [&DisplacementMeters, &FoamGeneration,
                              DownstreamMeters, AcrossMeters, PhaseSeconds,
                              SitePhaseRadians](
                              float CenterDownstreamMeters,
                              float CenterAcrossMeters,
                              float DownstreamRadiusMeters,
                              float AcrossRadiusMeters,
                              float AmplitudeMeters,
                              float DriftSpeed,
                              float PhaseOffset,
                              float Shear,
                              float FoamWeight)
    {
        const float Phase =
            PhaseSeconds * DriftSpeed + SitePhaseRadians + PhaseOffset;
        const float DriftedDownstreamCenter =
            CenterDownstreamMeters + 0.38f * FMath::Sin(Phase * 0.71f);
        const float DriftedAcrossCenter =
            CenterAcrossMeters + 0.52f * FMath::Sin(Phase);
        const float LocalDownstream =
            (DownstreamMeters - DriftedDownstreamCenter) /
            DownstreamRadiusMeters;
        const float LocalAcross =
            (AcrossMeters - DriftedAcrossCenter -
                Shear * (DownstreamMeters - DriftedDownstreamCenter)) /
            AcrossRadiusMeters;
        const float RadiusSquared =
            LocalDownstream * LocalDownstream + LocalAcross * LocalAcross;
        const float RadialEnvelope = FMath::Exp(-RadiusSquared);
        const float ShoulderWarp = FMath::Clamp(
            0.78f +
                0.16f * FMath::Sin(
                    1.73f * LocalDownstream - 1.19f * LocalAcross + Phase) +
                0.08f * FMath::Sin(
                    3.11f * LocalDownstream + 2.37f * LocalAcross -
                    0.61f * Phase),
            0.46f,
            1.08f);
        DisplacementMeters += AmplitudeMeters *
            (1.0f - RadiusSquared) * RadialEnvelope * ShoulderWarp;

        // A broken, phase-varying rim is carried into the existing advected
        // foam field. It cannot create foam without a solver-accepted site.
        const float Rim = FMath::Exp(
            -FMath::Square((RadiusSquared - 0.88f) / 0.34f));
        const float RimBreakup = FMath::Clamp(
            0.58f + 0.34f * FMath::Sin(
                2.43f * LocalDownstream + 1.67f * LocalAcross + 1.21f * Phase),
            0.16f,
            0.92f);
        FoamGeneration = FMath::Max(
            FoamGeneration, FoamWeight * Rim * RimBreakup);
    };

    AccumulateCell(7.2f, -0.8f, 2.3f, 1.8f, 0.046f,
        1.03f, 0.0f, 0.18f, 0.34f);
    AccumulateCell(10.7f, 1.5f, 2.8f, 2.2f, 0.034f,
        0.79f, 2.11f, -0.12f, 0.29f);
    AccumulateCell(14.2f, -1.3f, 3.3f, 2.5f, 0.026f,
        1.31f, 4.73f, 0.09f, 0.23f);

    const float FadeIn = FMath::SmoothStep(
        0.0f, 1.0f, FMath::Clamp((DownstreamMeters - 3.8f) / 1.8f, 0.0f, 1.0f));
    const float FadeOut = FMath::SmoothStep(
        0.0f, 1.0f, FMath::Clamp((20.5f - DownstreamMeters) / 3.0f, 0.0f, 1.0f));
    const float TailEnvelope = FadeIn * FadeOut * SafeIntensity;
    return FVector2D(
        FMath::Clamp(
            DisplacementMeters * TailEnvelope,
            -0.045f * SafeIntensity,
            0.070f * SafeIntensity),
        FMath::Clamp(
            FoamGeneration * TailEnvelope,
            0.0f,
            0.38f * SafeIntensity));
}

void ARaftSimWaterSurfaceActor::BeginPlay()
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

    UpdateRaftFoamExclusionParameters();
    BuildGrid();
    RefreshSurface();
}

void ARaftSimWaterSurfaceActor::UpdateRaftFoamExclusionParameters()
{
    UWorld* World = GetWorld();
    if (!World || !RaftFoamOcclusionCollection)
    {
        return;
    }
    UMaterialParameterCollectionInstance* Parameters =
        World->GetParameterCollectionInstance(RaftFoamOcclusionCollection);
    if (!Parameters)
    {
        return;
    }
    if (!IsValid(FoamOcclusionRaft))
    {
        FoamOcclusionRaft = nullptr;
        if (TActorIterator<ARaftSimRaftActor> RaftIt(World); RaftIt)
        {
            FoamOcclusionRaft = *RaftIt;
        }
    }
    if (!FoamOcclusionRaft)
    {
        Parameters->SetScalarParameterValue(
            TEXT("RaftFoamExclusionEnabled"), 0.0f);
        Parameters->SetScalarParameterValue(
            TEXT("RaftInteriorWaterTransmissionEnabled"), 0.0f);
        return;
    }

    FVector Forward = FoamOcclusionRaft->GetActorForwardVector().GetSafeNormal2D();
    if (Forward.IsNearlyZero())
    {
        Forward = FVector::ForwardVector;
    }
    const FVector Center = FoamOcclusionRaft->GetActorLocation();
    // The inner 79% is fully clear and the remaining band feathers back to
    // whitewater. Extents include deformed tubes, seated legs, and paddles at
    // the waterline while keeping contact foam visible just outside the hull.
    constexpr float RaftFoamExclusionHalfWidthCm = 190.0f;
    constexpr float RaftFoamExclusionHalfLengthCm = 320.0f;
    Parameters->SetVectorParameterValue(
        TEXT("RaftFoamExclusionCenterAndHalfWidthCm"),
        FLinearColor(
            Center.X,
            Center.Y,
            Center.Z,
            RaftFoamExclusionHalfWidthCm));
    Parameters->SetVectorParameterValue(
        TEXT("RaftFoamExclusionForwardAndHalfLengthCm"),
        FLinearColor(
            Forward.X,
            Forward.Y,
            Forward.Z,
            RaftFoamExclusionHalfLengthCm));
    Parameters->SetScalarParameterValue(
        TEXT("RaftFoamExclusionEnabled"), 1.0f);
    // Single Layer Water is intentionally opaque enough to hold the river's
    // depth at guide-eye distance. When the physical waterline crosses the
    // open raft, however, that same response hides the self-bailing floor as
    // a flat slab. Drive a separate, floor-sized transmission window so the
    // water remains present while the submerged interior is optically legible.
    // The custom mask's fully clear core ends at 0.62^(1/4) ~= 0.887 of
    // these rounded-rectangle extents. 82 x 215 cm therefore clears the
    // complete 66 x 181 cm floor while its feather finishes beneath the tubes.
    constexpr float RaftInteriorWaterHalfWidthCm = 82.0f;
    constexpr float RaftInteriorWaterHalfLengthCm = 215.0f;
    Parameters->SetVectorParameterValue(
        TEXT("RaftInteriorWaterCenterAndHalfWidthCm"),
        FLinearColor(
            Center.X,
            Center.Y,
            Center.Z,
            RaftInteriorWaterHalfWidthCm));
    Parameters->SetVectorParameterValue(
        TEXT("RaftInteriorWaterForwardAndHalfLengthCm"),
        FLinearColor(
            Forward.X,
            Forward.Y,
            Forward.Z,
            RaftInteriorWaterHalfLengthCm));
    Parameters->SetScalarParameterValue(
        TEXT("RaftInteriorWaterTransmissionEnabled"), 1.0f);
    if (!bLoggedRaftInteriorWaterTransmission ||
        FVector::DistSquared2D(
            Center, LastLoggedRaftInteriorWaterCenter) > FMath::Square(10000.0f))
    {
        bLoggedRaftInteriorWaterTransmission = true;
        LastLoggedRaftInteriorWaterCenter = Center;
        UE_LOG(
            LogTemp,
            Display,
            TEXT("RaftSim raft-interior water transmission: enabled=1 "
                 "center=(%.1f,%.1f,%.1f) forward=(%.3f,%.3f) "
                 "half_width_cm=%.1f half_length_cm=%.1f"),
            Center.X,
            Center.Y,
            Center.Z,
            Forward.X,
            Forward.Y,
            RaftInteriorWaterHalfWidthCm,
            RaftInteriorWaterHalfLengthCm);
    }
}

void ARaftSimWaterSurfaceActor::BuildGrid()
{
    const ARaftSimRiverWaterConfig* RiverWaterConfig = nullptr;
    if (TActorIterator<ARaftSimRiverWaterConfig> ConfigIt(GetWorld()); ConfigIt)
    {
        RiverWaterConfig = *ConfigIt;
    }
    const bool bUsesAuthoredRiverPresentation = RiverWaterConfig != nullptr;
    bLiveSurfaceCarrierEnabled =
        RiverWaterConfig && RiverWaterConfig->bLiveSolverOwnsRuntimeRendering;
    if (!bLiveSurfaceCarrierEnabled)
    {
        // Backward-compatible migration for already-versioned physical maps:
        // older packages tagged and hid the capture ribbon but predate the
        // explicit config property. Never leave those rivers with neither a
        // static nor live visible carrier while they await regeneration.
        for (TActorIterator<AActor> ActorIt(GetWorld()); ActorIt; ++ActorIt)
        {
            if (ActorIt->IsHidden() && ActorIt->Tags.Contains(
                    TEXT("RaftSimLiveSolverWaterOwnsRuntimeRendering")))
            {
                bLiveSurfaceCarrierEnabled = RiverWaterConfig != nullptr;
                break;
            }
        }
    }
    ResolvedCalmLiveSurfaceCoverage = bLiveSurfaceCarrierEnabled
        ? FMath::Clamp(RiverWaterConfig->LiveSurfaceCalmCoverage, 0.0f, 1.0f)
        : (RiverWaterConfig ? kAuthoredCarrierCalmDetailCoverage : 0.0f);
    ResolvedActiveLiveSurfaceCoverage = bLiveSurfaceCarrierEnabled
        ? FMath::Clamp(RiverWaterConfig->LiveSurfaceActiveCoverage, 0.0f, 1.0f)
        : (RiverWaterConfig ? kAuthoredCarrierActiveDetailCoverage : 0.0f);
    const bool bUsesMigratedFutaleufuVolumeCore =
        RiverWaterConfig &&
        RiverWaterConfig->CookedFieldsDir.Contains(
            TEXT("futaleufu_river_chile"),
            ESearchCase::CaseSensitive);
    const bool bUsesMigratedChilkoVolumeCore =
        RiverWaterConfig &&
        RiverWaterConfig->CookedFieldsDir.Contains(
            TEXT("chilko_river_lava_canyon"),
            ESearchCase::CaseSensitive);
    const bool bUsesLegacyChilkoPresentationDefaults =
        bUsesMigratedChilkoVolumeCore &&
        !RiverWaterConfig->bEnableLiveSolverVolumeCore;
    const bool bUsesMigratedColoradoVolumeCore =
        RiverWaterConfig &&
        RiverWaterConfig->CookedFieldsDir.Contains(
            TEXT("colorado_river_grand_canyon_rowing"),
            ESearchCase::CaseSensitive);
    const bool bUsesMigratedColdWaterVolumeCore =
        // Backward-compatible rollout for already-versioned cold-water maps.
        // Future regeneration persists the explicit flag; unique cooked-field
        // identities keep Pacuare on its reviewed carrier until separate
        // visual acceptance.
        bUsesMigratedFutaleufuVolumeCore ||
        bUsesMigratedChilkoVolumeCore;
    const bool bUsesMigratedLiveVolumeCore =
        bUsesMigratedColdWaterVolumeCore ||
        bUsesMigratedColoradoVolumeCore;
    UMaterialInterface* ResolvedVolumeCoreMaterialOverride =
        RiverWaterConfig
            ? RiverWaterConfig->LiveVolumeCoreMaterialOverride.Get()
            : nullptr;
    UTexture2D* ResolvedLiveWaterFlowNormalTexture =
        RiverWaterConfig
            ? RiverWaterConfig->LiveWaterFlowNormalTexture.Get()
            : nullptr;
    UTexture2D* ResolvedLiveWaterFoamLaceTexture =
        RiverWaterConfig
            ? RiverWaterConfig->LiveWaterFoamLaceTexture.Get()
            : nullptr;
    if (bUsesMigratedFutaleufuVolumeCore)
    {
        // Keep the already-shipped Terminator map runnable without resaving
        // its binary package together with unrelated in-progress terrain art.
        // Newly generated maps persist the same references on the config;
        // this cooked-field-identity fallback is therefore byte-compatible
        // with both the old package and the regenerated V3 package.
        if (!ResolvedVolumeCoreMaterialOverride)
        {
            ResolvedVolumeCoreMaterialOverride = LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Materials/"
                     "MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3."
                     "MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3"));
        }
        if (!ResolvedLiveWaterFlowNormalTexture)
        {
            ResolvedLiveWaterFlowNormalTexture = LoadObject<UTexture2D>(
                nullptr,
                TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Textures/"
                     "T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal."
                     "T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal"));
        }
        if (!ResolvedLiveWaterFoamLaceTexture)
        {
            ResolvedLiveWaterFoamLaceTexture = LoadObject<UTexture2D>(
                nullptr,
                TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Textures/"
                     "T_RaftSim_FutaleufuTerminatorWaterV1_FoamLace."
                     "T_RaftSim_FutaleufuTerminatorWaterV1_FoamLace"));
        }
    }
    if (bUsesMigratedChilkoVolumeCore)
    {
        // Migrate an older Lava Canyon package to the river-local optical
        // assets by cooked-field identity. Regenerated maps serialize the
        // same references and do not depend on this compatibility path.
        if (!ResolvedVolumeCoreMaterialOverride)
        {
            ResolvedVolumeCoreMaterialOverride = LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Materials/"
                     "MI_RaftSim_ChilkoLavaCanyon_LiveVolumeWaterV2."
                     "MI_RaftSim_ChilkoLavaCanyon_LiveVolumeWaterV2"));
        }
        if (!ResolvedLiveWaterFlowNormalTexture)
        {
            ResolvedLiveWaterFlowNormalTexture = LoadObject<UTexture2D>(
                nullptr,
                TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Textures/"
                     "T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal."
                     "T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal"));
        }
        if (!ResolvedLiveWaterFoamLaceTexture)
        {
            ResolvedLiveWaterFoamLaceTexture = LoadObject<UTexture2D>(
                nullptr,
                TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Textures/"
                     "T_RaftSim_ChilkoLavaCanyonWaterV1_FoamLace."
                     "T_RaftSim_ChilkoLavaCanyonWaterV1_FoamLace"));
        }
    }
    if (bUsesMigratedColoradoVolumeCore)
    {
        // Preserve the reviewed L_Hance map binary while rolling out the
        // river-local transmitting carrier. Regenerated maps serialize these
        // same references; the cooked-field identity only migrates older maps.
        if (!ResolvedVolumeCoreMaterialOverride)
        {
            ResolvedVolumeCoreMaterialOverride = LoadObject<UMaterialInterface>(
                nullptr,
                TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Materials/"
                     "MI_RaftSim_ColoradoHance_LiveVolumeWaterV2."
                     "MI_RaftSim_ColoradoHance_LiveVolumeWaterV2"));
        }
        if (!ResolvedLiveWaterFlowNormalTexture)
        {
            ResolvedLiveWaterFlowNormalTexture = LoadObject<UTexture2D>(
                nullptr,
                TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
                     "T_RaftSim_ColoradoHanceWaterV1_FlowNormal."
                     "T_RaftSim_ColoradoHanceWaterV1_FlowNormal"));
        }
        if (!ResolvedLiveWaterFoamLaceTexture)
        {
            ResolvedLiveWaterFoamLaceTexture = LoadObject<UTexture2D>(
                nullptr,
                TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
                     "T_RaftSim_ColoradoHanceWaterV1_FoamLace."
                     "T_RaftSim_ColoradoHanceWaterV1_FoamLace"));
        }
    }
    if (ResolvedVolumeCoreMaterialOverride)
    {
        LiveVolumeCoreMaterial = ResolvedVolumeCoreMaterialOverride;
    }
    bLiveVolumeCoreEnabled =
        bLiveSurfaceCarrierEnabled &&
        (RiverWaterConfig->bEnableLiveSolverVolumeCore ||
            bUsesMigratedLiveVolumeCore) &&
        LiveVolumeCoreMaterial != nullptr;
    if (bLiveVolumeCoreEnabled)
    {
        // The core is the river body. Keep the Default Lit mesh as a thin
        // normal/colour detail skin even when migrating an older map whose
        // serialized carrier coverage predates the split architecture.
        ResolvedCalmLiveSurfaceCoverage = bUsesMigratedChilkoVolumeCore
            ? 0.0f
            : kLiveVolumeCoreCalmDetailCoverage;
        ResolvedActiveLiveSurfaceCoverage = bUsesMigratedChilkoVolumeCore
            ? 0.0f
            : kLiveVolumeCoreActiveDetailCoverage;
    }
    const FLinearColor ResolvedLiveShallowSurfaceColor =
        bUsesMigratedColoradoVolumeCore
            ? FLinearColor(0.070f, 0.110f, 0.080f, 1.0f)
            : bUsesLegacyChilkoPresentationDefaults
            ? FLinearColor(0.012f, 0.075f, 0.105f, 1.0f)
            : bUsesMigratedFutaleufuVolumeCore
            ? FLinearColor(0.008f, 0.055f, 0.130f, 1.0f)
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveShallowSurfaceColor
                   : FLinearColor(0.025f, 0.120f, 0.150f, 1.0f));
    const FLinearColor ResolvedLiveDeepSurfaceColor =
        bUsesMigratedColoradoVolumeCore
            ? FLinearColor(0.018f, 0.038f, 0.028f, 1.0f)
            : bUsesLegacyChilkoPresentationDefaults
            ? FLinearColor(0.002f, 0.018f, 0.032f, 1.0f)
            : bUsesMigratedFutaleufuVolumeCore
            ? FLinearColor(0.001f, 0.014f, 0.050f, 1.0f)
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveDeepSurfaceColor
                   : FLinearColor(0.004f, 0.028f, 0.045f, 1.0f));
    const FLinearColor ResolvedLiveReflectedSkyColor =
        bUsesMigratedColoradoVolumeCore
            ? FLinearColor(0.12f, 0.17f, 0.18f, 1.0f)
            : bUsesLegacyChilkoPresentationDefaults
            ? FLinearColor(0.045f, 0.090f, 0.135f, 1.0f)
            : bUsesMigratedFutaleufuVolumeCore
            ? FLinearColor(0.018f, 0.080f, 0.160f, 1.0f)
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveReflectedSkyColor
                   : FLinearColor(0.11f, 0.23f, 0.31f, 1.0f));
    // River-local depth transmission must also migrate older serialized maps.
    // The cooked-field identity is stable, so runtime and newly regenerated
    // packages receive the same render-only coefficients without moving any
    // solver, geometry, collision, buoyancy, or force authority.
    const FLinearColor ResolvedLiveWaterScattering =
        bUsesMigratedFutaleufuVolumeCore
            ? FLinearColor(0.000035f, 0.000070f, 0.000110f, 0.0f)
            : bUsesMigratedChilkoVolumeCore
            ? FLinearColor(0.00004f, 0.00009f, 0.00014f, 0.0f)
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveWaterScattering
                   : FLinearColor(0.00011f, 0.00015f, 0.00019f, 0.0f));
    const FLinearColor ResolvedLiveWaterAbsorption =
        bUsesMigratedFutaleufuVolumeCore
            ? FLinearColor(0.0120f, 0.0080f, 0.0060f, 0.0f)
            : bUsesMigratedChilkoVolumeCore
            ? FLinearColor(0.0110f, 0.0065f, 0.0045f, 0.0f)
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveWaterAbsorption
                   : FLinearColor(0.0075f, 0.0048f, 0.0032f, 0.0f));
    const FLinearColor ResolvedLiveRiverbedColorScale =
        bUsesMigratedFutaleufuVolumeCore
            ? FLinearColor(0.055f, 0.075f, 0.090f, 0.0f)
            : bUsesMigratedChilkoVolumeCore
            ? FLinearColor(0.060f, 0.080f, 0.095f, 0.0f)
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveRiverbedColorScale
                   : FLinearColor(0.13f, 0.17f, 0.20f, 0.0f));
    const float ResolvedLiveShallowWaterOpacity =
        bUsesMigratedFutaleufuVolumeCore
            ? 0.36f
            : bUsesMigratedChilkoVolumeCore
            ? 0.36f
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveShallowWaterOpacity
                   : 0.58f);
    const float ResolvedLiveOpticalDepthResponseExponent =
        (bUsesMigratedFutaleufuVolumeCore || bUsesMigratedChilkoVolumeCore)
            ? 0.25f
            : (RiverWaterConfig
                   ? FMath::Clamp(
                         RiverWaterConfig->LiveOpticalDepthResponseExponent,
                         0.25f,
                         2.0f)
                   : 1.0f);
    const float ResolvedLiveDeepWaterOpacity =
        bUsesMigratedFutaleufuVolumeCore
            ? 0.86f
            : bUsesMigratedChilkoVolumeCore
            ? 0.84f
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveDeepWaterOpacity
                   : 0.79f);
    const float ResolvedLiveFoamWaterOpacity =
        bUsesMigratedFutaleufuVolumeCore
            ? 0.88f
            : bUsesMigratedChilkoVolumeCore
            ? 0.86f
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveFoamWaterOpacity
                   : 0.91f);
    const float ResolvedSpeedAerationFraction =
        bUsesMigratedFutaleufuVolumeCore
            ? 0.025f
            : bUsesMigratedChilkoVolumeCore
            ? 0.020f
            : -1.0f;
    const float ResolvedLiveSurfaceSpecular =
        bUsesMigratedColoradoVolumeCore
            ? 0.30f
            : bUsesLegacyChilkoPresentationDefaults
            ? 0.26f
            : bUsesMigratedFutaleufuVolumeCore
            ? 0.18f
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveSurfaceSpecular
                   : 0.20f);
    const float ResolvedLiveSurfaceRoughness =
        bUsesMigratedColoradoVolumeCore
            ? 0.32f
            : bUsesLegacyChilkoPresentationDefaults
            ? 0.36f
            : bUsesMigratedFutaleufuVolumeCore
            ? 0.42f
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveSurfaceRoughness
                   : 0.085f);
    const float ResolvedLiveSkyReflectionStrength =
        bUsesMigratedColoradoVolumeCore
            ? 0.26f
            : bUsesLegacyChilkoPresentationDefaults
            ? 0.20f
            : bUsesMigratedFutaleufuVolumeCore
            ? 0.05f
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveSkyReflectionStrength
                   : 0.62f);
    const float ResolvedLiveRippleStrength =
        bUsesMigratedColoradoVolumeCore
            ? 0.24f
            : bUsesLegacyChilkoPresentationDefaults
            ? 0.24f
            : bUsesMigratedFutaleufuVolumeCore
            ? 0.72f
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveRippleStrength
                   : 0.18f);
    const float ResolvedLiveFoamIntensity =
        bUsesMigratedColoradoVolumeCore
            ? 0.55f
            : bUsesLegacyChilkoPresentationDefaults
            ? 0.56f
            : bUsesMigratedFutaleufuVolumeCore
            ? 0.58f
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveFoamIntensity
                   : 0.52f);
    bLivePresentationSurfaceSmoothingEnabled =
        bLiveSurfaceCarrierEnabled &&
        RiverWaterConfig->bEnableLivePresentationSurfaceSmoothing;
    ResolvedPresentationSurfaceSmoothingStrength =
        bLivePresentationSurfaceSmoothingEnabled
            ? FMath::Clamp(
                  RiverWaterConfig->LivePresentationSurfaceSmoothingStrength,
                  0.0f,
                  1.0f)
            : 0.0f;
    ResolvedPresentationStandingWaveScale = bLiveSurfaceCarrierEnabled
        ? FMath::Clamp(
              RiverWaterConfig->LivePresentationStandingWaveScale, 0.0f, 1.0f)
        : 1.0f;
    ResolvedPresentationHydraulicReliefScale = bLiveSurfaceCarrierEnabled
        ? FMath::Clamp(
              RiverWaterConfig->LivePresentationHydraulicReliefScale, 0.0f, 1.0f)
        : 1.0f;
    ResolvedRapidFoamFocusStart = bLiveSurfaceCarrierEnabled
        ? FMath::Clamp(RiverWaterConfig->LiveRapidFoamFocusStart, 0.0f, 0.95f)
        : 0.12f;
    ResolvedRapidFoamFocusEnd = bLiveSurfaceCarrierEnabled
        ? FMath::Clamp(
              RiverWaterConfig->LiveRapidFoamFocusEnd,
              ResolvedRapidFoamFocusStart + 0.05f,
              1.0f)
        : 0.72f;
    ResolvedRapidFoamCoverageGain = bLiveSurfaceCarrierEnabled
        ? FMath::Clamp(RiverWaterConfig->LiveRapidFoamCoverageGain, 0.0f, 1.0f)
        : 1.0f;
    bLivePresentationBankNaturalismEnabled =
        bLiveSurfaceCarrierEnabled &&
        (RiverWaterConfig->bEnableLivePresentationBankNaturalism ||
            bUsesMigratedColdWaterVolumeCore);
    ResolvedPresentationBankNaturalismAmplitudeMeters =
        bLivePresentationBankNaturalismEnabled
        ? FMath::Clamp(
              RiverWaterConfig->bEnableLivePresentationBankNaturalism
                  ? RiverWaterConfig->LivePresentationBankNaturalismAmplitudeMeters
                  : 0.90f,
              0.0f,
              1.25f)
        : 0.0f;
    if (bLiveSurfaceCarrierEnabled)
    {
        CurvedGridLateralEdgeBlendMeters = FMath::Clamp(
            RiverWaterConfig->LiveSurfaceBankBlendMeters,
            1.5f,
            12.0f);
    }
    if (WaterAdapter)
    {
        // The live mesh applies standing-wave and hydraulic-relief geometry in
        // both modes: as the sole river carrier and as a translucent detail
        // overlay above legacy authored water. Keying rigid support only to
        // carrier mode left older South Fork packages on the base solver plane
        // while their visible first-rapid surface rose over the raft.
        WaterAdapter->ConfigureRaftSupportSurface(
            bUsesAuthoredRiverPresentation,
            ResolvedPresentationSurfaceSmoothingStrength,
            ResolvedPresentationStandingWaveScale,
            ResolvedPresentationHydraulicReliefScale);
        // Legacy detail-overlay maps render the AUTHORED band water (baked
        // sculpt + band-gated WPO), which the live solver cannot reconstruct.
        // Mirror it into rigid support from the cooked band field the editor
        // export writes beside the flow fields; carrier maps render the live
        // mesh itself and need no mirror.
        if (bUsesAuthoredRiverPresentation && !bLiveSurfaceCarrierEnabled &&
            RiverWaterConfig)
        {
            const FString BandFieldPath = FPaths::ConvertRelativePathToFull(
                FPaths::Combine(
                    FPaths::ProjectDir(),
                    TEXT(".."),
                    RiverWaterConfig->CookedFieldsDir,
                    FString::Printf(
                        TEXT("support_band_field_%s.bin"),
                        *RiverWaterConfig->FlowBand.ToString())));
            WaterAdapter->LoadRaftSupportBandFieldFromFile(BandFieldPath);
        }
    }

    bUsesCurvedRiverCoordinates = WaterAdapter && WaterAdapter->HasRiverCoordinateMap();
    // Every shipped river map owns an explicit water configuration, including
    // the legacy straight-coordinate South Fork reach. Keep config-less test
    // tanks on the original three-metre mesh while refining production river
    // presentation independently of the adapter coordinate representation.
    const int32 ResolvedSubdivision = bUsesAuthoredRiverPresentation
        ? FMath::Clamp(RiverPresentationSubdivision, 1, 2)
        : 1;
    ResolvedVertexSpacingMeters =
        VertexSpacingMeters / static_cast<float>(ResolvedSubdivision);
    PresentationAnalysisStride = ResolvedSubdivision;
    GridStationN = FMath::Max(
        2, FMath::RoundToInt(
            (bUsesCurvedRiverCoordinates ? CurvedGridLengthMeters : GridSizeMeters) /
            ResolvedVertexSpacingMeters) + 1);
    GridLateralN = FMath::Max(
        2, FMath::RoundToInt(
            (bUsesCurvedRiverCoordinates ? CurvedGridWidthMeters : GridSizeMeters) /
            ResolvedVertexSpacingMeters) + 1);
    const int32 VertCount = GridStationN * GridLateralN;
    Vertices.SetNum(VertCount);
    RiverCoordinatesM.SetNum(VertCount);
    Normals.SetNum(VertCount);
    UVs.SetNum(VertCount);
    FlowVelocityMetersPerSecond.SetNumZeroed(VertCount);
    VertexColors.SetNum(VertCount);
    LiveVolumeCoreVertices.SetNum(VertCount);
    LiveVolumeCoreTriangles.Reset((GridStationN - 1) * (GridLateralN - 1) * 6);
    RapidFoamVertices.SetNum(VertCount);
    RapidFoamVertexColors.SetNum(VertCount);
    Tangents.SetNum(VertCount);
    Triangles.Reset((GridStationN - 1) * (GridLateralN - 1) * 6);
    FoamField.SetNumZeroed(VertCount);
    bFoamFieldValid = false;
    BreakingSites.Reset();

    // Grid actor sits at world origin; vertices are in world cm relative to it.
    SetActorLocation(FVector::ZeroVector);

    if (bUsesCurvedRiverCoordinates)
    {
        TActorIterator<ARaftSimRaftActor> RaftIt(GetWorld());
        if (RaftIt)
        {
            FVector2D RiverPosition;
            FVector Tangent;
            FVector LeftNormal;
            if (WaterAdapter->WorldToRiverCoordinates(
                    RaftIt->GetActorLocation(), RiverPosition, Tangent, LeftNormal))
            {
                CurvedGridCenterStationM = RiverPosition.X;
            }
        }
        ClampCurvedGridCenter();
    }

    for (int32 LateralIndex = 0; LateralIndex < GridLateralN; ++LateralIndex)
    {
        for (int32 StationIndex = 0; StationIndex < GridStationN; ++StationIndex)
        {
            const int32 Index = LateralIndex * GridStationN + StationIndex;
            if (bUsesCurvedRiverCoordinates)
            {
                const float StationM = CurvedGridCenterStationM - CurvedGridLengthMeters * 0.5f +
                    StationIndex * ResolvedVertexSpacingMeters;
                const float LateralM = -CurvedGridWidthMeters * 0.5f +
                    LateralIndex * ResolvedVertexSpacingMeters;
                RiverCoordinatesM[Index] = FVector2D(StationM, LateralM);
                // Populated in one pass below so tangents can be derived from
                // adjacent curved-world vertices as well as positions.
                Vertices[Index] = FVector::ZeroVector;
            }
            else
            {
                const float WorldX = GridOriginCm.X +
                    StationIndex * ResolvedVertexSpacingMeters * kSurfCmPerM;
                const float WorldY = GridOriginCm.Y +
                    LateralIndex * ResolvedVertexSpacingMeters * kSurfCmPerM;
                Vertices[Index] = FVector(WorldX, WorldY, 0.0f);
                RiverCoordinatesM[Index] = FVector2D(
                    WorldX / kSurfCmPerM, WorldY / kSurfCmPerM);
            }
            Normals[Index] = FVector::UpVector;
            UVs[Index] = RiverCoordinatesM[Index] / kWaterTextureRepeatMeters;
            FlowVelocityMetersPerSecond[Index] = FVector2D::ZeroVector;
            VertexColors[Index] = FLinearColor(
                0.0f,
                0.0f,
                0.0f,
                ComputeStationEdgeCoverage(
                    StationIndex,
                    GridStationN,
                    ResolvedVertexSpacingMeters,
                    CurvedGridEdgeBlendMeters));
            LiveVolumeCoreVertices[Index] = Vertices[Index];
            RapidFoamVertices[Index] = Vertices[Index];
            RapidFoamVertexColors[Index] = FLinearColor(
                0.62f, 0.68f, 0.66f, 0.0f);
            Tangents[Index] = FProcMeshTangent(1.0f, 0.0f, 0.0f);
        }
    }

    if (bUsesCurvedRiverCoordinates)
    {
        UpdateCurvedGridPlanarGeometry();
    }

    for (int32 Y = 0; Y < GridLateralN - 1; ++Y)
    {
        for (int32 X = 0; X < GridStationN - 1; ++X)
        {
            const int32 I0 = Y * GridStationN + X;
            const int32 I1 = I0 + 1;
            const int32 I2 = I0 + GridStationN;
            const int32 I3 = I2 + 1;
            Triangles.Add(I0); Triangles.Add(I2); Triangles.Add(I1);
            Triangles.Add(I1); Triangles.Add(I2); Triangles.Add(I3);
        }
    }

    const TArray<FVector2D> EmptyUVs;
    SurfaceMesh->CreateMeshSection_LinearColor(
        0,
        Vertices,
        Triangles,
        Normals,
        UVs,
        FlowVelocityMetersPerSecond,
        EmptyUVs,
        EmptyUVs,
        VertexColors,
        Tangents,
        /*bCreateCollision=*/false);
    LiveVolumeCoreMesh->SetVisibility(false, true);
    if (LiveVolumeCoreMaterial != nullptr)
    {
        LiveVolumeCoreMesh->SetMaterial(0, LiveVolumeCoreMaterial);
        if (bLiveVolumeCoreEnabled)
        {
            if (UMaterialInstanceDynamic* VolumeMaterial =
                    LiveVolumeCoreMesh->CreateDynamicMaterialInstance(
                        0, LiveVolumeCoreMaterial))
            {
                VolumeMaterial->SetVectorParameterValue(
                    TEXT("ShallowWaterColor"),
                    ResolvedLiveShallowSurfaceColor);
                VolumeMaterial->SetVectorParameterValue(
                    TEXT("DeepWaterColor"),
                    ResolvedLiveDeepSurfaceColor);
                VolumeMaterial->SetVectorParameterValue(
                    TEXT("ReflectedSkyColor"),
                    ResolvedLiveReflectedSkyColor);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("WaterRoughness"),
                    ResolvedLiveSurfaceRoughness);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("Specular"),
                    ResolvedLiveSurfaceSpecular);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("FallbackSkyReflectionStrength"),
                    ResolvedLiveSkyReflectionStrength);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("HydraulicFoamIntensity"),
                    ResolvedLiveFoamIntensity);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("CalmRippleStrength"),
                    0.025f + ResolvedLiveRippleStrength * 0.08f);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("FlowRippleStrength"),
                    0.035f + ResolvedLiveRippleStrength * 0.16f);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("ShallowWaterOpacity"),
                    ResolvedLiveShallowWaterOpacity);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("OpticalDepthResponseExponent"),
                    ResolvedLiveOpticalDepthResponseExponent);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("DeepWaterOpacity"),
                    ResolvedLiveDeepWaterOpacity);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("FoamWaterOpacity"),
                    ResolvedLiveFoamWaterOpacity);
                if (ResolvedSpeedAerationFraction >= 0.0f)
                {
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("SpeedAerationFraction"),
                        ResolvedSpeedAerationFraction);
                }
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("RaftInteriorSurfaceOpacityScale"), 0.0f);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("RaftInteriorOpticalDepthScale"), 0.0f);
                // River-local render-only optical coefficients. Defaults keep
                // the accepted cold-water calibration; sediment-bearing rivers
                // can transmit warmer bed light without changing hydraulics.
                VolumeMaterial->SetVectorParameterValue(
                    TEXT("WaterScattering"),
                    ResolvedLiveWaterScattering);
                VolumeMaterial->SetVectorParameterValue(
                    TEXT("WaterAbsorption"),
                    ResolvedLiveWaterAbsorption);
                VolumeMaterial->SetVectorParameterValue(
                    TEXT("RiverbedColorScale"),
                    ResolvedLiveRiverbedColorScale);
                if (ResolvedLiveWaterFlowNormalTexture)
                {
                    VolumeMaterial->SetTextureParameterValue(
                        TEXT("WaterFlowNormalPrimary"),
                        ResolvedLiveWaterFlowNormalTexture);
                    VolumeMaterial->SetTextureParameterValue(
                        TEXT("WaterFlowNormalCross"),
                        ResolvedLiveWaterFlowNormalTexture);
                }
                if (ResolvedLiveWaterFoamLaceTexture)
                {
                    VolumeMaterial->SetTextureParameterValue(
                        TEXT("WhitewaterFoamLace"),
                        ResolvedLiveWaterFoamLaceTexture);
                }
            }
        }
    }
    RapidFoamMesh->CreateMeshSection_LinearColor(
        0,
        RapidFoamVertices,
        Triangles,
        Normals,
        UVs,
        RapidFoamVertexColors,
        Tangents,
        /*bCreateCollision=*/false);
    if (RapidFoamMaterial != nullptr)
    {
        RapidFoamMesh->SetMaterial(0, RapidFoamMaterial);
        if (ResolvedLiveWaterFoamLaceTexture)
        {
            if (UMaterialInstanceDynamic* RapidFoamDynamic =
                    RapidFoamMesh->CreateDynamicMaterialInstance(
                        0, RapidFoamMaterial))
            {
                RapidFoamDynamic->SetTextureParameterValue(
                    TEXT("SolverOverlayFoamLace"),
                    ResolvedLiveWaterFoamLaceTexture);
            }
        }
    }
    if (WaterMaterial != nullptr)
    {
        // The authored seasonal surface remains directly below this moving
        // solver patch. Rendering two transmitting Single Layer Water volumes
        // 2 cm apart compounds refraction into a pale frosted sheet, so the
        // live patch uses a neutral, non-refracting surface-lit alpha overlay.
        // Solver mesh normals still carry the resolved flow shape; spray/mist
        // actors add aeration.
        SurfaceMesh->SetMaterial(0, WaterMaterial);
        // Most maps retain an authored Single Layer Water surface and use this
        // as a transparent hydraulic-detail overlay. Physical source-corridor
        // maps deliberately hide their capture ribbon during play; their
        // saved water config therefore promotes this same solver mesh to the
        // river-wide visible carrier with a bounded river-specific profile.
        if (WaterMaterial->GetPathName().Contains(TEXT("M_RaftSim_LiveRiverSurface")))
        {
            if (UMaterialInstanceDynamic* LiveWaterMaterial =
                    SurfaceMesh->CreateDynamicMaterialInstance(0, WaterMaterial))
            {
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("CalmLiveSurfaceCoverage"),
                    ResolvedCalmLiveSurfaceCoverage);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("ActiveLiveSurfaceCoverage"),
                    ResolvedActiveLiveSurfaceCoverage);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveWaterSpecular"),
                    bLiveSurfaceCarrierEnabled
                        ? ResolvedLiveSurfaceSpecular
                        : 0.20f);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveWaterRoughness"),
                    bLiveSurfaceCarrierEnabled
                        ? ResolvedLiveSurfaceRoughness
                        : 0.085f);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveSkyReflectionStrength"),
                    bLiveSurfaceCarrierEnabled
                        ? ResolvedLiveSkyReflectionStrength
                        : 0.62f);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveRippleStrength"),
                    bLiveSurfaceCarrierEnabled
                        ? ResolvedLiveRippleStrength
                        : 0.32f);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveFoamIntensity"),
                    bLiveSurfaceCarrierEnabled
                        ? ResolvedLiveFoamIntensity
                        : 0.52f);
                if (!RiverWaterConfig)
                {
                    // Training Eddy / dev tank: with no river volume core the
                    // calm overlay at coverage 0.0 reads as no water at all —
                    // confirmed by the first human playtest (2026-08-07).
                    // Give the tank an always-visible calm surface; river
                    // maps keep their authored coverage handoff untouched.
                    LiveWaterMaterial->SetScalarParameterValue(
                        TEXT("CalmLiveSurfaceCoverage"), 0.42f);
                    LiveWaterMaterial->SetScalarParameterValue(
                        TEXT("ActiveLiveSurfaceCoverage"), 0.55f);
                }
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveWetCoverageEnable"),
                    bUsesMigratedChilkoVolumeCore ? 1.0f : 0.0f);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveWetCoverageDepthGain"), 32.0f);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveRippleGrazingFloor"),
                    bUsesMigratedChilkoVolumeCore ? 0.85f : 0.50f);
                if (bLiveSurfaceCarrierEnabled)
                {
                    LiveWaterMaterial->SetVectorParameterValue(
                        TEXT("LiveShallowSurfaceColor"),
                        ResolvedLiveShallowSurfaceColor);
                    LiveWaterMaterial->SetVectorParameterValue(
                        TEXT("LiveDeepSurfaceColor"),
                        ResolvedLiveDeepSurfaceColor);
                    LiveWaterMaterial->SetVectorParameterValue(
                        TEXT("LiveReflectedSkyColor"),
                        ResolvedLiveReflectedSkyColor);
                    if (ResolvedLiveWaterFlowNormalTexture)
                    {
                        LiveWaterMaterial->SetTextureParameterValue(
                            TEXT("LiveWaterFlowNormalPrimary"),
                            ResolvedLiveWaterFlowNormalTexture);
                        LiveWaterMaterial->SetTextureParameterValue(
                            TEXT("LiveWaterFlowNormalCross"),
                            ResolvedLiveWaterFlowNormalTexture);
                    }
                }
            }
        }
    }
    if (BreakingWaterMaterial != nullptr)
    {
        BreakingLipMesh->SetMaterial(0, BreakingWaterMaterial);
        BreakingRollerVolumeMesh->SetMaterial(0, BreakingWaterMaterial);
        if (BreakingWaterMaterial->GetPathName().Contains(
                TEXT("M_RaftSim_BreakingWaterLip")))
        {
            if (UMaterialInstanceDynamic* BreakingMaterial =
                    BreakingLipMesh->CreateDynamicMaterialInstance(
                        0, BreakingWaterMaterial))
            {
                // The opaque portion is sparse aerated lace; the nearly clear
                // carrier keeps the mesh from reading as a translucent block.
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingWaterOpacity"), 0.035f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamOpacity"), 0.86f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamFloor"), 0.60f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamIntensityGain"), 0.90f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("PrimaryLaceGain"), 0.65f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("DetailLaceGain"), 0.35f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamCoreGain"), 1.45f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingWaterRoughness"), 0.16f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamRoughness"), 0.82f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingWaterSpecular"), 0.30f);
                BreakingMaterial->SetVectorParameterValue(
                    TEXT("BreakingWaterColor"),
                    FLinearColor(0.10f, 0.22f, 0.27f, 1.0f));
                BreakingMaterial->SetVectorParameterValue(
                    TEXT("BreakingFoamColor"),
                    FLinearColor(0.96f, 0.98f, 1.0f, 1.0f));
            }
            if (RapidFoamMaterial == nullptr)
            {
                if (UMaterialInstanceDynamic* RollerMaterial =
                        BreakingRollerVolumeMesh->CreateDynamicMaterialInstance(
                            0, BreakingWaterMaterial))
                {
                    // Authoring-safe fallback when the masked solver-foam
                    // material is absent. The release path below always
                    // replaces this translucent instance.
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("BreakingWaterOpacity"), 0.003f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("BreakingFoamOpacity"), 0.86f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("BreakingFoamFloor"), 0.60f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("BreakingFoamIntensityGain"), 0.90f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("PrimaryLaceGain"), 0.72f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("DetailLaceGain"), 0.42f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("BreakingFoamCoreGain"), 1.35f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("BreakingWaterRoughness"), 0.22f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("BreakingFoamRoughness"), 0.82f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("BreakingWaterSpecular"), 0.24f);
                    RollerMaterial->SetVectorParameterValue(
                        TEXT("BreakingWaterColor"),
                        FLinearColor(0.08f, 0.18f, 0.22f, 1.0f));
                    RollerMaterial->SetVectorParameterValue(
                        TEXT("BreakingFoamColor"),
                        FLinearColor(0.96f, 0.98f, 1.0f, 1.0f));
                }
            }
        }
    }
    if (RapidFoamMaterial != nullptr)
    {
        // The connected plunge face is an aerated boundary, not a transparent
        // water volume. Reuse the proven masked solver-foam lace so the face
        // has irregular opaque bubbles and real holes instead of translucent
        // shell shading. This material also carries the raft/crew exclusion.
        BreakingRollerVolumeMesh->SetMaterial(0, RapidFoamMaterial);
        if (ResolvedLiveWaterFoamLaceTexture)
        {
            if (UMaterialInstanceDynamic* RollerFoamMaterial =
                    BreakingRollerVolumeMesh->CreateDynamicMaterialInstance(
                        0, RapidFoamMaterial))
            {
                RollerFoamMaterial->SetTextureParameterValue(
                    TEXT("SolverOverlayFoamLace"),
                    ResolvedLiveWaterFoamLaceTexture);
            }
        }
    }
}

void ARaftSimWaterSurfaceActor::HideBreakingLipMesh()
{
    BreakingLipTriangleCount = 0;
    if (BreakingLipMesh)
    {
        BreakingLipMesh->ClearAllMeshSections();
        BreakingLipMesh->SetVisibility(false, true);
    }
}

void ARaftSimWaterSurfaceActor::RebuildBreakingLipMesh()
{
    if (!BreakingLipMesh || BreakingSites.IsEmpty())
    {
        HideBreakingLipMesh();
        return;
    }

    // Sixteen segments in each direction preserve the profile and provide a
    // gradual vertex-alpha falloff. The complete 24-site population remains a
    // bounded 12,288 triangles; a normal full-reach window presents far fewer.
    constexpr int32 kAcrossSegments = 16;
    constexpr int32 kCurlSegments = 16;
    TArray<FVector> LipVertices;
    TArray<int32> LipTriangles;
    TArray<FVector> LipNormals;
    TArray<FVector2D> LipUvs;
    TArray<FLinearColor> LipColors;
    TArray<FProcMeshTangent> LipTangents;
    const int32 VerticesPerSite = (kAcrossSegments + 1) * (kCurlSegments + 1);
    const int32 TrianglesPerSite = kAcrossSegments * kCurlSegments * 2;
    LipVertices.Reserve(BreakingSites.Num() * VerticesPerSite);
    LipTriangles.Reserve(BreakingSites.Num() * TrianglesPerSite * 3);
    LipNormals.Reserve(BreakingSites.Num() * VerticesPerSite);
    LipUvs.Reserve(BreakingSites.Num() * VerticesPerSite);
    LipColors.Reserve(BreakingSites.Num() * VerticesPerSite);
    LipTangents.Reserve(BreakingSites.Num() * VerticesPerSite);

    for (int32 SiteIndex = 0; SiteIndex < BreakingSites.Num(); ++SiteIndex)
    {
        const FBreakingSite& Site = BreakingSites[SiteIndex];
        const float Intensity = FMath::Clamp(Site.Intensity, 0.0f, 1.0f);
        FVector Downstream = Site.WorldVelocityMps.GetSafeNormal2D();
        if (Downstream.IsNearlyZero())
        {
            Downstream = FVector::ForwardVector;
        }
        const FVector Across(-Downstream.Y, Downstream.X, 0.0f);
        // A single centre-channel detection still represents a jump front,
        // not a point emitter. Fit its span to the clearance measured from the
        // sampled live-water ownership surface. The four-metre cap leaves
        // eleven metres of bank/background margin at the normal 15 m hero site while
        // the intensity floor keeps small resolved rollers legible.
        const float MinimumHalfWidthCm = FMath::Lerp(
            160.0f, 240.0f, Intensity);
        const float ClearanceBoundHalfWidthCm = FMath::Max(
            0.0f, Site.PresentationEdgeClearanceMeters * kSurfCmPerM - 1000.0f);
        const float HalfWidthCm = FMath::Clamp(
            ClearanceBoundHalfWidthCm,
            MinimumHalfWidthCm,
            400.0f);
        const int32 BaseVertex = LipVertices.Num();
        for (int32 AcrossIndex = 0; AcrossIndex <= kAcrossSegments; ++AcrossIndex)
        {
            const float AcrossT = static_cast<float>(AcrossIndex) / kAcrossSegments;
            const float SignedAcross = AcrossT * 2.0f - 1.0f;
            const float EdgeTaper = FMath::Pow(
                FMath::Max(0.0f, 1.0f - SignedAcross * SignedAcross), 1.5f);
            for (int32 CurlIndex = 0; CurlIndex <= kCurlSegments; ++CurlIndex)
            {
                const float CurlT = static_cast<float>(CurlIndex) / kCurlSegments;
                const float ProfileFeather = FMath::Pow(
                    FMath::Max(0.0f, FMath::Sin(PI * CurlT)), 1.5f);
                FVector2D Profile = ComputeBreakingLipProfileCentimeters(
                    CurlT, Intensity);
                Profile.Y *= EdgeTaper;
                const float OrganicFoldCm =
                    FMath::Sin(
                        SiteIndex * 1.73f + SignedAcross * 5.1f + CurlT * 8.7f) *
                    4.5f * Intensity * EdgeTaper * FMath::Sin(PI * CurlT);
                // Break both the visible boundary and dense aerated core at
                // two incommensurate lateral frequencies. This prevents a
                // moderate jump from reading as one channel-spanning white
                // oval while keeping every fragment on one connected sheet.
                const float BoundaryVariation = FMath::Clamp(
                    0.68f +
                        0.18f * FMath::Sin(
                            SiteIndex * 1.31f + SignedAcross * 7.7f +
                            CurlT * 11.3f) +
                        0.14f * FMath::Sin(
                            SiteIndex * 2.17f - SignedAcross * 13.1f +
                            CurlT * 5.3f),
                    0.22f,
                    1.0f);
                // Blue carries a dense aerated core around the roller crest.
                // The material combines it with project-owned lace breakup,
                // leaving the longer downstream shoulder visibly fragmented.
                const float CrestDistance = (CurlT - 0.28f) / 0.12f;
                const float CrestFragmentation = FMath::Clamp(
                    0.62f +
                        0.22f * FMath::Sin(
                            SiteIndex * 2.31f + SignedAcross * 9.7f) +
                        0.16f * FMath::Sin(
                            SiteIndex * 0.83f - SignedAcross * 17.3f),
                    0.24f,
                    1.0f);
                const float CrestCore = FMath::Exp(
                    -CrestDistance * CrestDistance) *
                    FMath::Lerp(0.52f, 0.92f, Intensity) *
                    BoundaryVariation * CrestFragmentation;
                // A real hydraulic jump is not a lathed ellipse. Offset the
                // lip phase along its span and modulate downstream travel to
                // break the silhouette into connected shoulders while keeping
                // every point attached to the solver-detected site.
                const float AcrossPhase =
                    SiteIndex * 1.19f + SignedAcross * 3.7f;
                const float CrestPhaseOffsetCm =
                    FMath::Sin(AcrossPhase) * 34.0f * Intensity * EdgeTaper;
                const float TravelVariation = FMath::Clamp(
                    0.90f + 0.10f * FMath::Sin(AcrossPhase + CurlT * 4.3f),
                    0.78f,
                    1.08f);
                const FVector Position =
                    Site.WorldPositionCm +
                    Downstream * (Profile.X * TravelVariation + CrestPhaseOffsetCm) +
                    Across * (SignedAcross * HalfWidthCm) +
                    FVector::UpVector * (Profile.Y + OrganicFoldCm + 3.0f);
                LipVertices.Add(Position);
                LipUvs.Add(FVector2D(AcrossT, CurlT));
                LipColors.Add(FLinearColor(
                    FMath::Lerp(0.68f, 1.0f, Intensity),
                    0.20f,
                    CrestCore,
                    EdgeTaper * ProfileFeather * BoundaryVariation));

                // Derive the normal from this exact blended profile. Reusing
                // the old circular-curl tangent made attached moderate tails
                // shade like translucent tubes even after their geometry was
                // flattened.
                constexpr float ProfileDerivativeStep = 0.01f;
                const float PreviousCurlT = FMath::Max(
                    0.0f, CurlT - ProfileDerivativeStep);
                const float NextCurlT = FMath::Min(
                    1.0f, CurlT + ProfileDerivativeStep);
                FVector2D PreviousProfile = ComputeBreakingLipProfileCentimeters(
                    PreviousCurlT, Intensity);
                FVector2D NextProfile = ComputeBreakingLipProfileCentimeters(
                    NextCurlT, Intensity);
                PreviousProfile.Y *= EdgeTaper;
                NextProfile.Y *= EdgeTaper;
                const FVector LongitudinalTangent =
                    Downstream * (NextProfile.X - PreviousProfile.X) +
                    FVector::UpVector * (NextProfile.Y - PreviousProfile.Y);
                LipNormals.Add(
                    FVector::CrossProduct(LongitudinalTangent, Across).GetSafeNormal());
                LipTangents.Add(FProcMeshTangent(Across, false));
            }
        }
        for (int32 AcrossIndex = 0; AcrossIndex < kAcrossSegments; ++AcrossIndex)
        {
            for (int32 CurlIndex = 0; CurlIndex < kCurlSegments; ++CurlIndex)
            {
                const int32 I0 = BaseVertex +
                    AcrossIndex * (kCurlSegments + 1) + CurlIndex;
                const int32 I1 = I0 + 1;
                const int32 I2 = I0 + (kCurlSegments + 1);
                const int32 I3 = I2 + 1;
                LipTriangles.Add(I0); LipTriangles.Add(I2); LipTriangles.Add(I1);
                LipTriangles.Add(I1); LipTriangles.Add(I2); LipTriangles.Add(I3);
            }
        }
    }

    BreakingLipMesh->CreateMeshSection_LinearColor(
        0,
        LipVertices,
        LipTriangles,
        LipNormals,
        LipUvs,
        LipColors,
        LipTangents,
        /*bCreateCollision=*/false);
    BreakingLipTriangleCount = LipTriangles.Num() / 3;
    BreakingLipMesh->SetVisibility(BreakingLipTriangleCount > 0, true);
}

void ARaftSimWaterSurfaceActor::HideBreakingRollerVolumeMesh()
{
    BreakingRollerVolumeTriangleCount = 0;
    BreakingRollerVolumeVertexCount = 0;
    BreakingRollerVolumeMaximumThicknessCm = 0.0f;
    if (BreakingRollerVolumeMesh)
    {
        BreakingRollerVolumeMesh->ClearAllMeshSections();
        BreakingRollerVolumeMesh->SetVisibility(false, true);
    }
}

void ARaftSimWaterSurfaceActor::RebuildBreakingRollerVolumeMesh()
{
    if (!bBreakingRollerVolumeRenderingEnabled ||
        !BreakingRollerVolumeMesh || BreakingSites.IsEmpty())
    {
        HideBreakingRollerVolumeMesh();
        return;
    }

    // One alpha-perforated, two-skin crest envelope supplies a connected
    // overturning body under production Niagara. This is not a return to the
    // rejected nested shells: both skins follow the same irregular plunge
    // profile, remain at most 40 cm apart, and connect only across the fully
    // masked plunge boundary. The visible crown and masked sides remain open,
    // avoiding any planar cross-section at the crest.
    // The component never owns collision or water samples.
    constexpr int32 kMaximumRollerSites = 3;
    constexpr int32 kSkinCount = 2;
    constexpr int32 kAcrossSegments = 18;
    constexpr int32 kLoopSegments = 14;
    TArray<FVector> RollerVertices;
    TArray<int32> RollerTriangles;
    TArray<FVector> RollerNormals;
    TArray<FVector2D> RollerUvs;
    TArray<FLinearColor> RollerColors;
    TArray<FProcMeshTangent> RollerTangents;
    const int32 VerticesPerSkin =
        (kAcrossSegments + 1) * (kLoopSegments + 1);
    const int32 SkinTrianglesPerSite =
        kSkinCount * kAcrossSegments * kLoopSegments * 2;
    const int32 MaskedConnectorTrianglesPerSite = kAcrossSegments * 2;
    const int32 MaximumTrianglesPerSite =
        SkinTrianglesPerSite + MaskedConnectorTrianglesPerSite;
    const int32 RollerSiteCount = FMath::Min(
        BreakingSites.Num(), kMaximumRollerSites);
    RollerVertices.Reserve(
        RollerSiteCount * kSkinCount * VerticesPerSkin);
    RollerTriangles.Reserve(
        RollerSiteCount * MaximumTrianglesPerSite * 3);
    RollerNormals.Reserve(
        RollerSiteCount * kSkinCount * VerticesPerSkin);
    RollerUvs.Reserve(
        RollerSiteCount * kSkinCount * VerticesPerSkin);
    RollerColors.Reserve(
        RollerSiteCount * kSkinCount * VerticesPerSkin);
    RollerTangents.Reserve(
        RollerSiteCount * kSkinCount * VerticesPerSkin);
    BreakingRollerVolumeVertexCount = 0;
    BreakingRollerVolumeMaximumThicknessCm = 0.0f;

    for (int32 SiteIndex = 0; SiteIndex < RollerSiteCount; ++SiteIndex)
    {
        const FBreakingSite& Site = BreakingSites[SiteIndex];
        const float Intensity = FMath::Clamp(Site.Intensity, 0.0f, 1.0f);
        FVector Downstream = Site.WorldVelocityMps.GetSafeNormal2D();
        if (Downstream.IsNearlyZero())
        {
            Downstream = FVector::ForwardVector;
        }
        const FVector Across(-Downstream.Y, Downstream.X, 0.0f);
        const float MinimumHalfWidthCm = FMath::Lerp(
            170.0f, 250.0f, Intensity);
        const float ClearanceBoundHalfWidthCm = FMath::Max(
            0.0f, Site.PresentationEdgeClearanceMeters * kSurfCmPerM - 1200.0f);
        const float SiteHalfWidthCm = FMath::Clamp(
            ClearanceBoundHalfWidthCm,
            MinimumHalfWidthCm,
            360.0f);

        int32 SkinBaseVertices[kSkinCount] = {INDEX_NONE, INDEX_NONE};
        for (int32 SkinIndex = 0; SkinIndex < kSkinCount; ++SkinIndex)
        {
            constexpr float ProfileLayerT = 0.45f;
            const float SkinSign = SkinIndex == 0 ? -1.0f : 1.0f;
            const int32 BaseVertex = RollerVertices.Num();
            SkinBaseVertices[SkinIndex] = BaseVertex;

            for (int32 AcrossIndex = 0;
                 AcrossIndex <= kAcrossSegments;
                 ++AcrossIndex)
            {
                const float AcrossT =
                    static_cast<float>(AcrossIndex) / kAcrossSegments;
                const float SignedAcross = AcrossT * 2.0f - 1.0f;
                // Preserve a broad crest through most of the span, then fade
                // only the outer quarter. A parabolic height taper across the
                // whole span made each site read as an isolated dome.
                const float EdgeCoordinate = FMath::Clamp(
                    (1.0f - FMath::Abs(SignedAcross)) / 0.24f,
                    0.0f,
                    1.0f);
                const float EdgeTaper =
                    EdgeCoordinate * EdgeCoordinate *
                    (3.0f - 2.0f * EdgeCoordinate);

                for (int32 LoopIndex = 0;
                     LoopIndex <= kLoopSegments;
                     ++LoopIndex)
                {
                    const float LoopT =
                        static_cast<float>(LoopIndex) / kLoopSegments;
                    // Render only the crest-to-plunge half of the circulation.
                    // The downstream back of the old 270-degree shell was
                    // visible through translucency and made every site look
                    // like a smooth dome. Niagara supplies the detached air on
                    // that side; this membrane depicts the multi-valued face.
                    const float ProfileLoopT = FMath::Lerp(0.48f, 1.0f, LoopT);
                    FVector2D Profile =
                        ComputeBreakingRollerVolumeProfileCentimeters(
                            ProfileLoopT, Intensity, ProfileLayerT);
                    Profile.Y *= FMath::Lerp(0.78f, 1.0f, EdgeTaper);
                    // The membrane starts at the visible crown, so it must not
                    // use a symmetric endpoint fade. Keep the crown fully
                    // aerated and dissolve only as the sheet folds beneath the
                    // sampled surface into the plunge.
                    const float LoopFeather = FMath::Pow(
                        FMath::Max(0.0f, FMath::Cos(0.5f * PI * LoopT)),
                        0.58f);
                    const float Breakup = FMath::Clamp(
                        0.62f +
                            0.20f * FMath::Sin(
                                SiteIndex * 1.67f + SignedAcross * 10.3f +
                                ProfileLoopT * 8.9f) +
                            0.18f * FMath::Sin(
                                SiteIndex * 2.43f - SignedAcross * 16.7f +
                                ProfileLoopT * 15.1f),
                        0.16f,
                        1.0f);
                    const float OrganicTravelCm =
                        FMath::Sin(
                            SiteIndex * 1.13f + SignedAcross * 4.7f +
                            ProfileLoopT * 6.3f) *
                        13.0f * Intensity * EdgeTaper * LoopFeather;
                    const float OrganicLiftCm =
                        FMath::Sin(
                            SiteIndex * 2.07f + SignedAcross * 7.1f +
                            ProfileLoopT * 11.7f) *
                        14.0f * Intensity * EdgeTaper * LoopFeather;

                    constexpr float ProfileDerivativeStep = 0.01f;
                    const float PreviousLoopT = FMath::Lerp(
                        0.48f,
                        1.0f,
                        FMath::Max(0.0f, LoopT - ProfileDerivativeStep));
                    const float NextLoopT = FMath::Lerp(
                        0.48f,
                        1.0f,
                        FMath::Min(1.0f, LoopT + ProfileDerivativeStep));
                    FVector2D PreviousProfile =
                        ComputeBreakingRollerVolumeProfileCentimeters(
                            PreviousLoopT, Intensity, ProfileLayerT);
                    FVector2D NextProfile =
                        ComputeBreakingRollerVolumeProfileCentimeters(
                            NextLoopT, Intensity, ProfileLayerT);
                    PreviousProfile.Y *= FMath::Lerp(0.78f, 1.0f, EdgeTaper);
                    NextProfile.Y *= FMath::Lerp(0.78f, 1.0f, EdgeTaper);
                    const FVector LongitudinalTangent =
                        Downstream * (NextProfile.X - PreviousProfile.X) +
                        FVector::UpVector * (NextProfile.Y - PreviousProfile.Y);
                    const FVector ProfileNormal = FVector::CrossProduct(
                        LongitudinalTangent, Across).GetSafeNormal();
                    // The envelope is thickest at the aerated crown and
                    // collapses toward fully masked boundaries. Breakup
                    // slightly modulates the thickness without detaching it
                    // from the solver-selected profile.
                    const float HalfThicknessCm =
                        FMath::Lerp(6.0f, 20.0f, Intensity) * EdgeTaper *
                        FMath::Lerp(0.35f, 1.0f, LoopFeather) *
                        FMath::Lerp(0.72f, 1.0f, Breakup);
                    BreakingRollerVolumeMaximumThicknessCm = FMath::Max(
                        BreakingRollerVolumeMaximumThicknessCm,
                        HalfThicknessCm * 2.0f);
                    const FVector CentrePosition =
                        Site.WorldPositionCm +
                        Downstream * (Profile.X + OrganicTravelCm) +
                        Across * (SignedAcross * SiteHalfWidthCm) +
                        FVector::UpVector * (Profile.Y + OrganicLiftCm + 4.0f);
                    RollerVertices.Add(
                        CentrePosition + ProfileNormal * SkinSign * HalfThicknessCm);
                    RollerUvs.Add(FVector2D(
                        AcrossT * 5.4f + ProfileLayerT * 0.31f,
                        LoopT * 3.6f + ProfileLayerT * 0.37f));
                    const float CoreDistance = (ProfileLoopT - 0.57f) / 0.18f;
                    const float AeratedCore =
                        FMath::Exp(-CoreDistance * CoreDistance) *
                        FMath::Lerp(0.52f, 0.95f, Intensity) * Breakup;
                    const float FoamBrightness = FMath::Lerp(
                        0.88f, 1.0f, AeratedCore);
                    RollerColors.Add(FLinearColor(
                        FoamBrightness * 0.94f,
                        FoamBrightness,
                        FoamBrightness * 0.98f,
                        EdgeTaper * LoopFeather *
                            FMath::Lerp(0.84f, 1.0f, AeratedCore)));

                    RollerNormals.Add(ProfileNormal * SkinSign);
                    RollerTangents.Add(FProcMeshTangent(Across, false));
                }
            }

            for (int32 AcrossIndex = 0;
                 AcrossIndex < kAcrossSegments;
                 ++AcrossIndex)
            {
                for (int32 LoopIndex = 0;
                     LoopIndex < kLoopSegments;
                     ++LoopIndex)
                {
                    const int32 I0 = BaseVertex +
                        AcrossIndex * (kLoopSegments + 1) + LoopIndex;
                    const int32 I1 = I0 + 1;
                    const int32 I2 = I0 + (kLoopSegments + 1);
                    const int32 I3 = I2 + 1;
                    if (((AcrossIndex + LoopIndex + SkinIndex + SiteIndex) & 1) == 0)
                    {
                        RollerTriangles.Add(I0);
                        RollerTriangles.Add(I2);
                        RollerTriangles.Add(I1);
                        RollerTriangles.Add(I1);
                        RollerTriangles.Add(I2);
                        RollerTriangles.Add(I3);
                    }
                    else
                    {
                        RollerTriangles.Add(I0);
                        RollerTriangles.Add(I2);
                        RollerTriangles.Add(I3);
                        RollerTriangles.Add(I0);
                        RollerTriangles.Add(I3);
                        RollerTriangles.Add(I1);
                    }
                }
            }
        }

        // Join the two skins only at the plunge row, where LoopFeather is
        // exactly zero. This makes the procedural mesh one connected surface
        // without introducing a visible planar cap or box cue at the crest.
        for (int32 AcrossIndex = 0;
             AcrossIndex < kAcrossSegments;
             ++AcrossIndex)
        {
            const int32 Inner0 = SkinBaseVertices[0] +
                AcrossIndex * (kLoopSegments + 1) + kLoopSegments;
            const int32 Inner1 = Inner0 + (kLoopSegments + 1);
            const int32 Outer0 = SkinBaseVertices[1] +
                AcrossIndex * (kLoopSegments + 1) + kLoopSegments;
            const int32 Outer1 = Outer0 + (kLoopSegments + 1);
            RollerTriangles.Add(Inner0);
            RollerTriangles.Add(Inner1);
            RollerTriangles.Add(Outer0);
            RollerTriangles.Add(Outer0);
            RollerTriangles.Add(Inner1);
            RollerTriangles.Add(Outer1);
        }
    }

    BreakingRollerVolumeMesh->CreateMeshSection_LinearColor(
        0, RollerVertices, RollerTriangles, RollerNormals, RollerUvs,
        RollerColors, RollerTangents, false);
    BreakingRollerVolumeTriangleCount = RollerTriangles.Num() / 3;
    BreakingRollerVolumeVertexCount = RollerVertices.Num();
    BreakingRollerVolumeMesh->SetVisibility(
        BreakingRollerVolumeTriangleCount > 0, true);
}

void ARaftSimWaterSurfaceActor::RecenterCurvedGrid()
{
    if (!bUsesCurvedRiverCoordinates || !WaterAdapter)
    {
        return;
    }
    float DesiredCenterStationM = CurvedGridCenterStationM;
    TActorIterator<ARaftSimRaftActor> RaftIt(GetWorld());
    if (RaftIt)
    {
        FVector2D RiverPosition;
        FVector Tangent;
        FVector LeftNormal;
        if (WaterAdapter->WorldToRiverCoordinates(
                RaftIt->GetActorLocation(), RiverPosition, Tangent, LeftNormal))
        {
            DesiredCenterStationM = RiverPosition.X;
        }
    }
    if (FMath::Abs(DesiredCenterStationM - CurvedGridCenterStationM) <
        CurvedGridRecenterDistanceMeters)
    {
        return;
    }
    CurvedGridCenterStationM = DesiredCenterStationM;
    ClampCurvedGridCenter();
    for (int32 LateralIndex = 0; LateralIndex < GridLateralN; ++LateralIndex)
    {
        for (int32 StationIndex = 0; StationIndex < GridStationN; ++StationIndex)
        {
            const int32 Index = LateralIndex * GridStationN + StationIndex;
            RiverCoordinatesM[Index] = FVector2D(
                CurvedGridCenterStationM - CurvedGridLengthMeters * 0.5f +
                    StationIndex * ResolvedVertexSpacingMeters,
                -CurvedGridWidthMeters * 0.5f +
                    LateralIndex * ResolvedVertexSpacingMeters);
            UVs[Index] = RiverCoordinatesM[Index] / kWaterTextureRepeatMeters;
        }
    }
    UpdateCurvedGridPlanarGeometry();
}

void ARaftSimWaterSurfaceActor::ClampCurvedGridCenter()
{
    float MinimumStationM = 0.0f;
    float MaximumStationM = 0.0f;
    if (!WaterAdapter ||
        !WaterAdapter->GetRiverStationRangeM(MinimumStationM, MaximumStationM))
    {
        return;
    }
    const float HalfLengthM = CurvedGridLengthMeters * 0.5f;
    if (MaximumStationM - MinimumStationM <= CurvedGridLengthMeters)
    {
        CurvedGridCenterStationM = 0.5f * (MinimumStationM + MaximumStationM);
        return;
    }
    CurvedGridCenterStationM = FMath::Clamp(
        CurvedGridCenterStationM,
        MinimumStationM + HalfLengthM,
        MaximumStationM - HalfLengthM);
}

void ARaftSimWaterSurfaceActor::UpdateCurvedGridPlanarGeometry()
{
    for (int32 LateralIndex = 0; LateralIndex < GridLateralN; ++LateralIndex)
    {
        for (int32 StationIndex = 0; StationIndex < GridStationN; ++StationIndex)
        {
            const int32 Index = LateralIndex * GridStationN + StationIndex;
            FVector WorldPosition;
            const bool bMapped = WaterAdapter && WaterAdapter->RiverToWorldPosition(
                RiverCoordinatesM[Index], WaterAdapter->GetRiverVerticalDatumM(),
                WorldPosition);
            checkf(bMapped, TEXT("Clamped curved water grid left its coordinate-map domain"));
            Vertices[Index].X = WorldPosition.X;
            Vertices[Index].Y = WorldPosition.Y;
        }
    }

    // The material's flow basis follows the river rather than world X, which
    // prevents visible UV/normal-map direction changes around tight bends.
    for (int32 LateralIndex = 0; LateralIndex < GridLateralN; ++LateralIndex)
    {
        for (int32 StationIndex = 0; StationIndex < GridStationN; ++StationIndex)
        {
            const int32 PreviousStationIndex = FMath::Max(StationIndex - 1, 0);
            const int32 NextStationIndex = FMath::Min(StationIndex + 1, GridStationN - 1);
            const FVector& Previous = Vertices[
                LateralIndex * GridStationN + PreviousStationIndex];
            const FVector& Next = Vertices[
                LateralIndex * GridStationN + NextStationIndex];
            const FVector FlowTangent = FVector(
                Next.X - Previous.X, Next.Y - Previous.Y, 0.0f).GetSafeNormal();
            Tangents[LateralIndex * GridStationN + StationIndex] =
                FProcMeshTangent(FlowTangent, false);
        }
    }
}

void ARaftSimWaterSurfaceActor::RefreshSurface()
{
    const double RefreshStartSeconds = FPlatformTime::Seconds();
    RecenterCurvedGrid();
    TArray<uint8> WetVertexMask;
    WetVertexMask.Init(0, Vertices.Num());
    TArray<FRaftSimWaterSample> WaterSamples;
    WaterSamples.SetNum(Vertices.Num());
    TArray<float> PresentationSurfaceHeightMeters;
    PresentationSurfaceHeightMeters.Init(0.0f, Vertices.Num());
    TArray<float> HydraulicReliefMeters;
    HydraulicReliefMeters.Init(0.0f, Vertices.Num());
    TArray<float> FroudeField;
    FroudeField.Init(0.0f, Vertices.Num());
    TArray<float> SourceFoam;
    SourceFoam.Init(0.0f, Vertices.Num());

    // Real elapsed time since the previous refresh drives foam advection and
    // decay; clamped so a hitch or the first refresh cannot teleport foam.
    const double NowRealSeconds = FPlatformTime::Seconds();
    const float FoamDeltaSeconds = bFoamFieldValid
        ? FMath::Clamp(
              static_cast<float>(NowRealSeconds - LastRefreshRealSeconds), 0.0f, 0.5f)
        : 0.0f;
    LastRefreshRealSeconds = NowRealSeconds;

    // Sample the live field once per vertex. A separate presentation pass can
    // then compare same-lateral station neighbours without multiplying runtime
    // adapter queries or reaching outside the active cooked window.
    if (WaterAdapter != nullptr)
    {
        for (int32 Y = 0; Y < GridLateralN; ++Y)
        {
            for (int32 X = 0; X < GridStationN; ++X)
            {
                const int32 Index = Y * GridStationN + X;
                const FVector& V = Vertices[Index];
                FRaftSimWaterSample& Sample = WaterSamples[Index];
                const bool bSampled = bUsesCurvedRiverCoordinates
                    ? WaterAdapter->SampleWaterFieldAtRiverCoordinates(
                        RiverCoordinatesM[Index], Sample)
                    : WaterAdapter->SampleWaterAtWorldPosition(
                        FVector(V.X, V.Y, 0.0f), Sample);
                WetVertexMask[Index] = bSampled && Sample.bWet ? 1 : 0;
                if (WetVertexMask[Index] != 0)
                {
                    PresentationSurfaceHeightMeters[Index] =
                        Sample.SurfaceHeightMeters;
                }
            }
        }
    }

    // Cooked visualization cells can otherwise read as broad transverse
    // steps. The optional cardinal filter retains the original three-metre
    // physical neighbourhood after render subdivision. It is Jacobi-style
    // (always reads the untouched sampled field), preserves a linear grade
    // exactly, and writes only this local render array.
    // WaterSamples remains the authority for gameplay.
    if (bLivePresentationSurfaceSmoothingEnabled &&
        ResolvedPresentationSurfaceSmoothingStrength > 0.0f)
    {
        const TArray<float> RawPresentationSurfaceHeightMeters =
            PresentationSurfaceHeightMeters;
        const int32 Stride = PresentationAnalysisStride;
        for (int32 Y = Stride; Y < GridLateralN - Stride; ++Y)
        {
            for (int32 X = Stride; X < GridStationN - Stride; ++X)
            {
                const int32 Index = Y * GridStationN + X;
                const int32 UpstreamIndex = Index - Stride;
                const int32 DownstreamIndex = Index + Stride;
                const int32 RiverRightIndex = Index - Stride * GridStationN;
                const int32 RiverLeftIndex = Index + Stride * GridStationN;
                if (WetVertexMask[Index] == 0 ||
                    WetVertexMask[UpstreamIndex] == 0 ||
                    WetVertexMask[DownstreamIndex] == 0 ||
                    WetVertexMask[RiverRightIndex] == 0 ||
                    WetVertexMask[RiverLeftIndex] == 0)
                {
                    continue;
                }
                PresentationSurfaceHeightMeters[Index] =
                    ComputePresentationSmoothedSurfaceHeightMeters(
                        RawPresentationSurfaceHeightMeters[Index],
                        RawPresentationSurfaceHeightMeters[UpstreamIndex],
                        RawPresentationSurfaceHeightMeters[DownstreamIndex],
                        RawPresentationSurfaceHeightMeters[RiverRightIndex],
                        RawPresentationSurfaceHeightMeters[RiverLeftIndex],
                        ResolvedPresentationSurfaceSmoothingStrength);
            }
        }
    }

    // Amplify only solver-resolved station curvature. The five analysis
    // samples retain their original 12 m span on the subdivided render grid,
    // large enough to describe a readable rapid crest/hole pair without
    // misclassifying the new short presentation bands as solver relief.
    const int32 AnalysisNearStride = PresentationAnalysisStride;
    const int32 AnalysisFarStride = 2 * PresentationAnalysisStride;
    for (int32 Y = 0; Y < GridLateralN; ++Y)
    {
        for (int32 X = AnalysisFarStride;
             X < GridStationN - AnalysisFarStride;
             ++X)
        {
            const int32 Index = Y * GridStationN + X;
            const int32 UpstreamFarIndex = Index - AnalysisFarStride;
            const int32 UpstreamNearIndex = Index - AnalysisNearStride;
            const int32 DownstreamNearIndex = Index + AnalysisNearStride;
            const int32 DownstreamFarIndex = Index + AnalysisFarStride;
            if (WetVertexMask[Index] == 0 ||
                WetVertexMask[UpstreamFarIndex] == 0 ||
                WetVertexMask[UpstreamNearIndex] == 0 ||
                WetVertexMask[DownstreamNearIndex] == 0 ||
                WetVertexMask[DownstreamFarIndex] == 0)
            {
                continue;
            }
            const FRaftSimWaterSample& Sample = WaterSamples[Index];
            HydraulicReliefMeters[Index] =
                URaftSimWaterRuntimeAdapter::ComputeCoupledHydraulicReliefMeters(
                PresentationSurfaceHeightMeters[Index],
                PresentationSurfaceHeightMeters[UpstreamFarIndex],
                PresentationSurfaceHeightMeters[UpstreamNearIndex],
                PresentationSurfaceHeightMeters[DownstreamNearIndex],
                PresentationSurfaceHeightMeters[DownstreamFarIndex],
                Sample.VelocityMetersPerSecond.Size2D(),
                Sample.DepthMeters) * ResolvedPresentationHydraulicReliefScale;
        }
    }
    TArray<float> StationWetSurfaceZSum;
    StationWetSurfaceZSum.Init(0.0f, GridStationN);
    TArray<int32> StationWetSurfaceCount;
    StationWetSurfaceCount.Init(0, GridStationN);
    TArray<int32> MinimumWetLateralIndex;
    MinimumWetLateralIndex.Init(GridLateralN, GridStationN);
    TArray<int32> MaximumWetLateralIndex;
    MaximumWetLateralIndex.Init(INDEX_NONE, GridStationN);
    int32 WetVertexCount = 0;
    float FoamSum = 0.0f;
    float MaximumFoam = 0.0f;
    float DepthSum = 0.0f;
    float SpeedSum = 0.0f;
    // SI companions to the 0-1 presentation normals above. The normalized
    // means were once logged under bare names and read as if they were
    // metres and m/s, which mis-diagnosed a healthy 0.81 m/s put-in pool
    // as dead water (2026-08-10).
    float DepthMetersSum = 0.0f;
    float SpeedMpsSum = 0.0f;
    float MaximumAbsoluteStandingWaveM = 0.0f;
    float MaximumAbsoluteHydraulicReliefM = 0.0f;
    for (int32 Y = 0; Y < GridLateralN; ++Y)
    {
        for (int32 X = 0; X < GridStationN; ++X)
        {
            const int32 Index = Y * GridStationN + X;
            // Wet/dry visibility is encoded in vertex alpha below. Dry and
            // out-of-crop vertices are levelled to the nearest same-station
            // wet surface in a second pass. Moving them far below the bed made
            // wet/dry boundary triangles into kilometre-tall translucent
            // curtains that occluded the raft and banks.
            float SurfaceZCm = 0.0f;
            FVector NormalOut = FVector::UpVector;
            float Foam = 0.0f;

            float DepthNorm = 0.0f;
            float SpeedNorm = 0.0f;
            FlowVelocityMetersPerSecond[Index] = FVector2D::ZeroVector;
            if (WetVertexMask[Index] != 0)
            {
                const FRaftSimWaterSample& Sample = WaterSamples[Index];
                const float Speed = Sample.VelocityMetersPerSecond.Size2D();
                // Curved-grid field samples are already (downstream,
                // river-left); legacy straight-grid samples are world XY,
                // which is also the UV0 basis there. UV1 therefore carries a
                // physical metres-per-second vector in the matching texture
                // coordinate frame for every supported live window.
                FlowVelocityMetersPerSecond[Index] = FVector2D(
                    Sample.VelocityMetersPerSecond.X,
                    Sample.VelocityMetersPerSecond.Y);
                const float Depth = FMath::Max(Sample.DepthMeters, 0.05f);
                const FRaftSimWaterStandingWave StandingWave =
                    URaftSimWaterRuntimeAdapter::ComputeCoupledStandingWave(
                        RiverCoordinatesM[Index], Speed, Depth);
                const float HydraulicRelief = HydraulicReliefMeters[Index];
                // The authored seasonal surface remains beneath this live
                // solver patch. Reapply its deterministic sub-grid ripple and
                // sharpen only the large-scale relief already present in the
                // sampled cooked surface. Standing-wave and relief terms also
                // drive rigid support; the 2 cm z-fight lift is render-only,
                // and flexible D3 keeps the unamplified water field.
                SurfaceZCm =
                    (PresentationSurfaceHeightMeters[Index] +
                        StandingWave.DisplacementMeters *
                            ResolvedPresentationStandingWaveScale +
                        HydraulicRelief) *
                        kSurfCmPerM +
                    GetLiveSurfaceRenderLiftCm();
                StationWetSurfaceZSum[X] += SurfaceZCm;
                ++StationWetSurfaceCount[X];
                MinimumWetLateralIndex[X] = FMath::Min(
                    MinimumWetLateralIndex[X], Y);
                MaximumWetLateralIndex[X] = FMath::Max(
                    MaximumWetLateralIndex[X], Y);
                const FVector SampleNormal = Sample.SurfaceNormal.GetSafeNormal();
                const float SafeNormalZ = FMath::Max(SampleNormal.Z, 0.1f);
                float BaseStationSlope = -SampleNormal.X / SafeNormalZ;
                float BaseLateralSlope = -SampleNormal.Y / SafeNormalZ;
                const int32 DerivativeStride = PresentationAnalysisStride;
                const float DerivativeSpanMeters = FMath::Max(
                    2.0f * DerivativeStride * ResolvedVertexSpacingMeters,
                    KINDA_SMALL_NUMBER);
                if (bLivePresentationSurfaceSmoothingEnabled &&
                    X >= DerivativeStride &&
                    X < GridStationN - DerivativeStride &&
                    Y >= DerivativeStride &&
                    Y < GridLateralN - DerivativeStride)
                {
                    const int32 UpstreamIndex = Index - DerivativeStride;
                    const int32 DownstreamIndex = Index + DerivativeStride;
                    const int32 RiverRightIndex =
                        Index - DerivativeStride * GridStationN;
                    const int32 RiverLeftIndex =
                        Index + DerivativeStride * GridStationN;
                    if (WetVertexMask[UpstreamIndex] != 0 &&
                        WetVertexMask[DownstreamIndex] != 0 &&
                        WetVertexMask[RiverRightIndex] != 0 &&
                        WetVertexMask[RiverLeftIndex] != 0)
                    {
                        BaseStationSlope =
                            (PresentationSurfaceHeightMeters[DownstreamIndex] -
                                PresentationSurfaceHeightMeters[UpstreamIndex]) /
                            DerivativeSpanMeters;
                        BaseLateralSlope =
                            (PresentationSurfaceHeightMeters[RiverLeftIndex] -
                                PresentationSurfaceHeightMeters[RiverRightIndex]) /
                            DerivativeSpanMeters;
                    }
                }

                float ReliefStationSlope = 0.0f;
                if (X >= DerivativeStride &&
                    X < GridStationN - DerivativeStride &&
                    WetVertexMask[Index - DerivativeStride] != 0 &&
                    WetVertexMask[Index + DerivativeStride] != 0)
                {
                    ReliefStationSlope =
                        (HydraulicReliefMeters[Index + DerivativeStride] -
                            HydraulicReliefMeters[Index - DerivativeStride]) /
                        DerivativeSpanMeters;
                }
                float ReliefLateralSlope = 0.0f;
                if (Y >= DerivativeStride &&
                    Y < GridLateralN - DerivativeStride)
                {
                    const int32 RiverRightIndex =
                        Index - DerivativeStride * GridStationN;
                    const int32 RiverLeftIndex =
                        Index + DerivativeStride * GridStationN;
                    if (WetVertexMask[RiverRightIndex] != 0 &&
                        WetVertexMask[RiverLeftIndex] != 0)
                    {
                        ReliefLateralSlope =
                            (HydraulicReliefMeters[RiverLeftIndex] -
                                HydraulicReliefMeters[RiverRightIndex]) /
                            DerivativeSpanMeters;
                    }
                }
                const FVector PresentationLocalNormal = FVector(
                    -(BaseStationSlope +
                        StandingWave.StationSlope *
                            ResolvedPresentationStandingWaveScale +
                        ReliefStationSlope),
                    -(BaseLateralSlope +
                        StandingWave.LateralSlope *
                            ResolvedPresentationStandingWaveScale +
                        ReliefLateralSlope),
                    1.0f).GetSafeNormal();
                if (bUsesCurvedRiverCoordinates)
                {
                    const FVector FlowTangent = Tangents[Index].TangentX;
                    const FVector LeftNormal(
                        -FlowTangent.Y, FlowTangent.X, 0.0f);
                    NormalOut = (
                        FlowTangent * PresentationLocalNormal.X +
                        LeftNormal * PresentationLocalNormal.Y +
                        FVector::UpVector * PresentationLocalNormal.Z).GetSafeNormal();
                }
                else
                {
                    NormalOut = PresentationLocalNormal;
                }
                // Froude number = speed / sqrt(g * depth). Instantaneous foam
                // generation only where the flow is genuinely supercritical
                // (the holes and wave crests); the persistent advected foam
                // field below carries it downstream and decays it.
                const float Froude = Speed / FMath::Sqrt(kGravity * Depth);
                FroudeField[Index] = Froude;
                // Breaking onset at Fr 0.78 with a wider ramp: steep riffle
                // and cascade waves (Fr 0.85-1.0 over rough beds) genuinely
                // break white in the field, and the 2026-08-10 cascade run
                // measured Fr 0.93 rendering clean under the former Fr>1.0
                // gate. Named-rapid pockets (Fr 1.3+) keep their character.
                Foam = FMath::Clamp((Froude - 0.78f) / 1.25f, 0.0f, 1.0f);
                SourceFoam[Index] = Foam;
                DepthNorm = FMath::Clamp(Sample.DepthMeters / 4.0f, 0.0f, 1.0f);
                SpeedNorm = FMath::Clamp(Speed / 8.0f, 0.0f, 1.0f);
                ++WetVertexCount;
                DepthSum += DepthNorm;
                SpeedSum += SpeedNorm;
                DepthMetersSum += Sample.DepthMeters;
                SpeedMpsSum += Speed;
                MaximumAbsoluteStandingWaveM = FMath::Max(
                    MaximumAbsoluteStandingWaveM,
                    FMath::Abs(StandingWave.DisplacementMeters));
                MaximumAbsoluteHydraulicReliefM = FMath::Max(
                    MaximumAbsoluteHydraulicReliefM,
                    FMath::Abs(HydraulicRelief));
            }

            Vertices[Index].Z = SurfaceZCm;
            Normals[Index] = NormalOut;
            // R = foam, G = depth, B = flow speed (consumed by the photoreal
            // water material for whitewater, depth colour, and flow response).
            VertexColors[Index] = FLinearColor(
                Foam,
                DepthNorm,
                SpeedNorm,
                WetVertexMask[Index] != 0
                    ? ComputeStationEdgeCoverage(
                        X,
                        GridStationN,
                        ResolvedVertexSpacingMeters,
                        CurvedGridEdgeBlendMeters)
                    : 0.0f);
        }
    }

    // --- Breaking water at hydraulic jumps -------------------------------
    // A supercritical station running into a subcritical neighbour is the
    // solver's own hydraulic jump. Presentation: lift the breaking crest so it
    // leans over its downstream pile, saturate foam generation through the
    // pile, and record the site for bounded aerosol/mist. Visual only.
    BreakingSites.Reset();
    TArray<FBreakingSite> CandidateSites;
    int32 EdgeRejectedSiteCount = 0;
    float MaximumEdgeRejectedIntensity = 0.0f;
    float StrongestEdgeRejectedCoverage = 0.0f;
    float StrongestEdgeRejectedClearanceMeters = 0.0f;
    FVector2D StrongestEdgeRejectedRiverCoordinates = FVector2D::ZeroVector;
    for (int32 Y = 0; Y < GridLateralN; ++Y)
    {
        for (int32 X = PresentationAnalysisStride; X < GridStationN; ++X)
        {
            const int32 Index = Y * GridStationN + X;
            const int32 ImmediateUpstreamIndex =
                Index - PresentationAnalysisStride;
            if (WetVertexMask[Index] == 0 ||
                WetVertexMask[ImmediateUpstreamIndex] == 0)
            {
                continue;
            }
            const float LocalFroude = FroudeField[Index];
            if (LocalFroude > 0.94f)
            {
                continue;
            }
            int32 UpstreamIndex = ImmediateUpstreamIndex;
            float UpstreamFroude = FroudeField[UpstreamIndex];
            // Cooked river fields and the presentation surface do not need to
            // share a vertex phase. Accept the same solver-owned jump across
            // at most two three-metre analysis edges, so a five-metre
            // hydraulic control cannot fall between samples and disappear.
            // This remains a strict local Froude transition; no marker, tag,
            // or art cue can create a breaking site by itself.
            if (UpstreamFroude < 1.12f &&
                X >= 2 * PresentationAnalysisStride)
            {
                const int32 FarUpstreamIndex =
                    Index - 2 * PresentationAnalysisStride;
                if (WetVertexMask[FarUpstreamIndex] != 0 &&
                    FroudeField[FarUpstreamIndex] > UpstreamFroude)
                {
                    UpstreamIndex = FarUpstreamIndex;
                    UpstreamFroude = FroudeField[UpstreamIndex];
                }
            }
            if (UpstreamFroude < 1.12f)
            {
                continue;
            }
            const float DepthScale = FMath::Clamp(
                WaterSamples[Index].DepthMeters / 0.6f, 0.3f, 1.0f);
            const float Intensity = FMath::Clamp(
                (UpstreamFroude - 0.85f) / 1.5f, 0.0f, 1.0f) * DepthScale;
            if (Intensity < 0.08f)
            {
                continue;
            }

            const int32 UpstreamStationIndex =
                X - (Index - UpstreamIndex);
            const float UpstreamStationCoverage = ComputeStationEdgeCoverage(
                UpstreamStationIndex,
                GridStationN,
                ResolvedVertexSpacingMeters,
                CurvedGridEdgeBlendMeters);
            const float LocalStationCoverage = ComputeStationEdgeCoverage(
                X,
                GridStationN,
                ResolvedVertexSpacingMeters,
                CurvedGridEdgeBlendMeters);
            const float UpstreamLateralCoverage = ComputeLateralWetCoverage(
                Y,
                MinimumWetLateralIndex[UpstreamStationIndex],
                MaximumWetLateralIndex[UpstreamStationIndex],
                ResolvedVertexSpacingMeters,
                CurvedGridLateralEdgeBlendMeters);
            const float LocalLateralCoverage = ComputeLateralWetCoverage(
                Y,
                MinimumWetLateralIndex[X],
                MaximumWetLateralIndex[X],
                ResolvedVertexSpacingMeters,
                CurvedGridLateralEdgeBlendMeters);
            const float PresentationCoverage = FMath::Min(
                UpstreamStationCoverage * UpstreamLateralCoverage,
                LocalStationCoverage * LocalLateralCoverage);
            const float PresentationEdgeClearanceMeters = FMath::Min(
                ComputePresentationSurfaceEdgeClearanceMeters(
                    UpstreamStationIndex,
                    GridStationN,
                    Y,
                    MinimumWetLateralIndex[UpstreamStationIndex],
                    MaximumWetLateralIndex[UpstreamStationIndex],
                    ResolvedVertexSpacingMeters),
                ComputePresentationSurfaceEdgeClearanceMeters(
                    X,
                    GridStationN,
                    Y,
                    MinimumWetLateralIndex[X],
                    MaximumWetLateralIndex[X],
                    ResolvedVertexSpacingMeters));
            // The base live-water surface deliberately fades at both its
            // moving-grid ends and sampled banks. Never bend that fading mesh
            // or attach a fully visible overhanging sheet to it: doing so
            // reveals the rectangular overlay/terrain boundary in hero views.
            // The configured clearance contains the bounded sheet plus at
            // least one sampled dry-bank cell. Solver jump detection remains
            // unchanged.
            constexpr float kMinimumFullCoverage = 0.999f;
            if (PresentationCoverage < kMinimumFullCoverage ||
                PresentationEdgeClearanceMeters <
                    BreakingSiteInteriorClearanceMeters)
            {
                ++EdgeRejectedSiteCount;
                if (Intensity > MaximumEdgeRejectedIntensity)
                {
                    MaximumEdgeRejectedIntensity = Intensity;
                    StrongestEdgeRejectedCoverage = PresentationCoverage;
                    StrongestEdgeRejectedClearanceMeters =
                        PresentationEdgeClearanceMeters;
                    StrongestEdgeRejectedRiverCoordinates =
                        RiverCoordinatesM[UpstreamIndex];
                }
                continue;
            }

            // Crest leans up; the first subcritical station dips, forming the
            // overturning face into the white pile.
            const float LiftCm = BreakingCrestLiftMeters * kSurfCmPerM * Intensity;
            Vertices[UpstreamIndex].Z += LiftCm;
            Vertices[Index].Z -= 0.45f * LiftCm;

            const float BreakingFrothStrength = FMath::Lerp(
                0.62f, 1.0f, FMath::Sqrt(Intensity));
            SourceFoam[UpstreamIndex] = FMath::Max(
                SourceFoam[UpstreamIndex], 0.75f * BreakingFrothStrength);
            SourceFoam[Index] = FMath::Max(
                SourceFoam[Index], 0.95f * BreakingFrothStrength);

            // Decaying tailwater wave train: the oscillatory surface every
            // hydraulic jump sheds downstream. Alternating, exponentially
            // decaying crests/troughs (bounded by the crest lift) give the
            // rapid readable hydraulic volume instead of a flat run-out, and
            // each surviving crest keeps generating a little foam.
            const int32 TailStepCount = FMath::Max(
                1,
                FMath::RoundToInt(18.0f / ResolvedVertexSpacingMeters));
            for (int32 TailStep = 1; TailStep <= TailStepCount; ++TailStep)
            {
                const int32 TailIndex = Index + TailStep;
                if (X + TailStep >= GridStationN ||
                    WetVertexMask[TailIndex] == 0)
                {
                    break;
                }
                const float TailDistanceMeters =
                    TailStep * ResolvedVertexSpacingMeters;
                const float Decay = FMath::Exp(-0.14f * TailDistanceMeters);
                const float Phase = FMath::Cos(
                    (2.05f / 3.0f) * TailDistanceMeters);
                Vertices[TailIndex].Z += 0.62f * LiftCm * Decay * Phase;
                SourceFoam[TailIndex] = FMath::Max(
                    SourceFoam[TailIndex],
                    Intensity * FMath::Max(Phase, 0.0f) * 0.65f * Decay + 0.38f * Decay);
            }

            FBreakingSite Site;
            Site.WorldPositionCm = Vertices[UpstreamIndex];
            Site.WorldVelocityMps = WaterSamples[UpstreamIndex].VelocityMetersPerSecond;
            Site.RiverCoordinatesMeters = RiverCoordinatesM[UpstreamIndex];
            Site.Intensity = Intensity;
            Site.PresentationCoverage = PresentationCoverage;
            Site.PresentationEdgeClearanceMeters =
                PresentationEdgeClearanceMeters;
            CandidateSites.Add(Site);
        }
    }
    // Strongest sites first, deduplicated to 6 m so one long jump line yields a
    // handful of overlapping crest lobes rather than a wall of emitters.
    CandidateSites.Sort([](const FBreakingSite& A, const FBreakingSite& B)
        { return A.Intensity > B.Intensity; });
    constexpr int32 kMaxBreakingSites = 24;
    constexpr float kMinSiteSpacingCm = 600.0f;
    for (const FBreakingSite& Candidate : CandidateSites)
    {
        if (BreakingSites.Num() >= kMaxBreakingSites)
        {
            break;
        }
        bool bTooClose = false;
        for (const FBreakingSite& Accepted : BreakingSites)
        {
            if (FVector::DistSquared2D(
                    Accepted.WorldPositionCm, Candidate.WorldPositionCm) <
                kMinSiteSpacingCm * kMinSiteSpacingCm)
            {
                bTooClose = true;
                break;
            }
        }
        if (!bTooClose)
        {
            BreakingSites.Add(Candidate);
        }
    }

    if (WaterAdapter)
    {
        // Mirror the accepted sites into rigid support so the ridden surface
        // rises with the rendered crest, dip, and tailwater train. The 2 cm
        // z-fight lift and the plunge-pocket pass below stay render-only.
        TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> SupportSites;
        SupportSites.Reserve(BreakingSites.Num());
        for (const FBreakingSite& Site : BreakingSites)
        {
            URaftSimWaterRuntimeAdapter::FSupportBreakingSite& SupportSite =
                SupportSites.AddDefaulted_GetRef();
            SupportSite.RiverCoordinatesMeters = Site.RiverCoordinatesMeters;
            SupportSite.Intensity = Site.Intensity;
        }
        WaterAdapter->ConfigureRaftSupportBreakingSites(
            SupportSites, BreakingCrestLiftMeters, ResolvedVertexSpacingMeters);
    }

    // Give the three strongest accepted interior jumps a coherent plan-view
    // plunge pocket beneath the connected crest-to-plunge membrane. The
    // solver selects every site; this pass only changes presentation vertices
    // and foam. A bounded combined displacement prevents nearby accepted sites
    // from stacking into fabricated cliffs, while the pocket centre stays
    // darker than its broken shoulders and downstream aerated return.
    constexpr int32 kMaximumBreakingPresentationSites = 3;
    TArray<uint8> BreakingPresentationVertexMask;
    BreakingPresentationVertexMask.Init(0, Vertices.Num());
    const int32 BreakingPresentationSiteCount = FMath::Min(
        BreakingSites.Num(), kMaximumBreakingPresentationSites);
    const bool bDownstreamBoilMicroreliefEnabled =
        CVarRaftSimDownstreamBoilMicrorelief.GetValueOnGameThread() != 0;
    ActiveDownstreamBoilSiteCount = bDownstreamBoilMicroreliefEnabled
        ? BreakingPresentationSiteCount
        : 0;
    MaximumAbsoluteDownstreamBoilDisplacementMeters = 0.0f;
    for (int32 VertexIndex = 0; VertexIndex < Vertices.Num(); ++VertexIndex)
    {
        if (WetVertexMask[VertexIndex] == 0)
        {
            continue;
        }
        float CombinedPocketDisplacementMeters = 0.0f;
        float CombinedBoilDisplacementMeters = 0.0f;
        float PocketFoam = 0.0f;
        float BoilFoam = 0.0f;
        for (int32 SiteIndex = 0;
             SiteIndex < BreakingPresentationSiteCount;
             ++SiteIndex)
        {
            const FBreakingSite& Site = BreakingSites[SiteIndex];
            const FVector2D RelativeRiverPosition =
                RiverCoordinatesM[VertexIndex] - Site.RiverCoordinatesMeters;
            const FVector2D Pocket =
                ComputeBreakingPlungePocketPresentation(
                    RelativeRiverPosition.X,
                    RelativeRiverPosition.Y,
                    Site.Intensity);
            CombinedPocketDisplacementMeters += Pocket.X;
            PocketFoam = FMath::Max(PocketFoam, Pocket.Y);

            const float SitePhaseRadians = FMath::Fmod(
                FMath::Abs(
                    Site.RiverCoordinatesMeters.X * 0.137f +
                    Site.RiverCoordinatesMeters.Y * 0.293f),
                2.0f * PI);
            const FVector2D Boil = bDownstreamBoilMicroreliefEnabled
                ? ComputeBreakingDownstreamBoilPresentation(
                      RelativeRiverPosition.X,
                      RelativeRiverPosition.Y,
                      Site.Intensity,
                      PresentationPhaseSeconds,
                      SitePhaseRadians)
                : FVector2D::ZeroVector;
            CombinedBoilDisplacementMeters += Boil.X;
            BoilFoam = FMath::Max(BoilFoam, Boil.Y);
        }
        CombinedPocketDisplacementMeters = FMath::Clamp(
            CombinedPocketDisplacementMeters, -0.30f, 0.18f);
        CombinedBoilDisplacementMeters = FMath::Clamp(
            CombinedBoilDisplacementMeters, -0.045f, 0.070f);
        MaximumAbsoluteDownstreamBoilDisplacementMeters = FMath::Max(
            MaximumAbsoluteDownstreamBoilDisplacementMeters,
            FMath::Abs(CombinedBoilDisplacementMeters));
        const float CombinedDisplacementMeters = FMath::Clamp(
            CombinedPocketDisplacementMeters + CombinedBoilDisplacementMeters,
            -0.31f,
            0.21f);
        Vertices[VertexIndex].Z +=
            CombinedDisplacementMeters * kSurfCmPerM;
        SourceFoam[VertexIndex] = FMath::Max(
            SourceFoam[VertexIndex], FMath::Max(PocketFoam, BoilFoam));
        if (FMath::Abs(CombinedDisplacementMeters) > 0.001f ||
            PocketFoam > 0.05f || BoilFoam > 0.05f)
        {
            BreakingPresentationVertexMask[VertexIndex] = 1;
        }
    }

    // Recompute normals only in and immediately around the modified pocket.
    // This makes the depression and return respond to light while leaving the
    // established river-wide surface presentation byte-for-byte untouched.
    for (int32 Y = 1; Y < GridLateralN - 1; ++Y)
    {
        for (int32 X = 1; X < GridStationN - 1; ++X)
        {
            const int32 Index = Y * GridStationN + X;
            const int32 UpstreamIndex = Index - 1;
            const int32 DownstreamIndex = Index + 1;
            const int32 RiverRightIndex = Index - GridStationN;
            const int32 RiverLeftIndex = Index + GridStationN;
            if (WetVertexMask[Index] == 0 ||
                WetVertexMask[UpstreamIndex] == 0 ||
                WetVertexMask[DownstreamIndex] == 0 ||
                WetVertexMask[RiverRightIndex] == 0 ||
                WetVertexMask[RiverLeftIndex] == 0)
            {
                continue;
            }
            const bool bBreakingPresentationNeighbourhood =
                BreakingPresentationVertexMask[Index] != 0 ||
                BreakingPresentationVertexMask[UpstreamIndex] != 0 ||
                BreakingPresentationVertexMask[DownstreamIndex] != 0 ||
                BreakingPresentationVertexMask[RiverRightIndex] != 0 ||
                BreakingPresentationVertexMask[RiverLeftIndex] != 0;
            if (!bBreakingPresentationNeighbourhood)
            {
                continue;
            }
            const FVector StationTangent =
                Vertices[DownstreamIndex] - Vertices[UpstreamIndex];
            const FVector LateralTangent =
                Vertices[RiverLeftIndex] - Vertices[RiverRightIndex];
            Normals[Index] = FVector::CrossProduct(
                StationTangent, LateralTangent).GetSafeNormal();
        }
    }
    RebuildBreakingLipMesh();
    RebuildBreakingRollerVolumeMesh();
    if (!bLoggedBreakingSiteDiagnostics &&
        (!BreakingSites.IsEmpty() || EdgeRejectedSiteCount > 0))
    {
        bLoggedBreakingSiteDiagnostics = true;
        const FBreakingSite* StrongestInteriorSite = BreakingSites.IsEmpty()
            ? nullptr
            : &BreakingSites[0];
        UE_LOG(
            LogTemp,
            Display,
            TEXT("RaftSim live breaking-water ownership: active_sites=%d "
                 "edge_rejected_sites=%d max_edge_rejected_intensity=%.3f "
                 "strongest_edge_rejected_station_m=%.1f "
                 "strongest_edge_rejected_lateral_m=%.1f "
                 "strongest_edge_rejected_coverage=%.3f "
                 "strongest_edge_rejected_clearance_m=%.1f "
                 "strongest_interior_intensity=%.3f "
                 "strongest_interior_coverage=%.3f "
                 "strongest_interior_clearance_m=%.1f minimum_clearance_m=%.1f"),
            BreakingSites.Num(),
            EdgeRejectedSiteCount,
            MaximumEdgeRejectedIntensity,
            StrongestEdgeRejectedRiverCoordinates.X,
            StrongestEdgeRejectedRiverCoordinates.Y,
            StrongestEdgeRejectedCoverage,
            StrongestEdgeRejectedClearanceMeters,
            StrongestInteriorSite ? StrongestInteriorSite->Intensity : 0.0f,
            StrongestInteriorSite
                ? StrongestInteriorSite->PresentationCoverage
                : 0.0f,
            StrongestInteriorSite
                ? StrongestInteriorSite->PresentationEdgeClearanceMeters
                : 0.0f,
            BreakingSiteInteriorClearanceMeters);
    }
    if (ActiveDownstreamBoilSiteCount > 0)
    {
        UE_LOG(
            LogTemp,
            VeryVerbose,
            TEXT("RaftSim solver-anchored downstream boil microrelief: "
                 "active_sites=%d abs_max_m=%.4f authority=presentation_only"),
            ActiveDownstreamBoilSiteCount,
            MaximumAbsoluteDownstreamBoilDisplacementMeters);
    }

    // --- Persistent advected foam ----------------------------------------
    // Semi-Lagrangian: each wet vertex looks upstream along the sampled flow
    // into the previous foam field, decays what it finds through the half-life,
    // and takes the maximum with this refresh's generation. Foam therefore
    // streaks downstream of every hole and wave train and pools into eddy
    // lines, instead of blinking in and out on the generation cells.
    const FVector2D CurrentFieldOriginM = bUsesCurvedRiverCoordinates
        ? FVector2D(
              CurvedGridCenterStationM - CurvedGridLengthMeters * 0.5f,
              -CurvedGridWidthMeters * 0.5f)
        : FVector2D(GridOriginCm.X / kSurfCmPerM, GridOriginCm.Y / kSurfCmPerM);
    const float DecayFactor = FoamDeltaSeconds > 0.0f
        ? FMath::Pow(0.5f, FoamDeltaSeconds / FMath::Max(FoamHalfLifeSeconds, 0.5f))
        : 0.0f;
    TArray<float> NewFoamField;
    NewFoamField.SetNumZeroed(Vertices.Num());
    float FoamAdvectionSum = 0.0f;
    float FoamAdvectionMax = 0.0f;
    for (int32 Y = 0; Y < GridLateralN; ++Y)
    {
        for (int32 X = 0; X < GridStationN; ++X)
        {
            const int32 Index = Y * GridStationN + X;
            if (WetVertexMask[Index] == 0)
            {
                continue;
            }
            float Advected = 0.0f;
            if (bFoamFieldValid && DecayFactor > 0.0f &&
                FoamField.Num() == NewFoamField.Num())
            {
                const FVector WorldVelocity =
                    WaterSamples[Index].VelocityMetersPerSecond;
                FVector2D FieldVelocity(WorldVelocity.X, WorldVelocity.Y);
                FVector2D FieldPosition(
                    Vertices[Index].X / kSurfCmPerM, Vertices[Index].Y / kSurfCmPerM);
                if (bUsesCurvedRiverCoordinates)
                {
                    const FVector FlowTangent = Tangents[Index].TangentX;
                    const FVector2D Tangent2D(FlowTangent.X, FlowTangent.Y);
                    const FVector2D Left2D(-FlowTangent.Y, FlowTangent.X);
                    FieldVelocity = FVector2D(
                        FVector2D::DotProduct(
                            FVector2D(WorldVelocity.X, WorldVelocity.Y), Tangent2D),
                        FVector2D::DotProduct(
                            FVector2D(WorldVelocity.X, WorldVelocity.Y), Left2D));
                    FieldPosition = RiverCoordinatesM[Index];
                }
                const FVector2D BackPosition =
                    FieldPosition - FieldVelocity * FoamDeltaSeconds;
                const float FractionalX =
                    (BackPosition.X - FoamFieldOriginM.X) /
                    ResolvedVertexSpacingMeters;
                const float FractionalY =
                    (BackPosition.Y - FoamFieldOriginM.Y) /
                    ResolvedVertexSpacingMeters;
                const int32 CellX = FMath::FloorToInt(FractionalX);
                const int32 CellY = FMath::FloorToInt(FractionalY);
                if (CellX >= 0 && CellX < GridStationN - 1 &&
                    CellY >= 0 && CellY < GridLateralN - 1)
                {
                    const float Fx = FractionalX - CellX;
                    const float Fy = FractionalY - CellY;
                    const float V00 = FoamField[CellY * GridStationN + CellX];
                    const float V01 = FoamField[CellY * GridStationN + CellX + 1];
                    const float V10 = FoamField[(CellY + 1) * GridStationN + CellX];
                    const float V11 = FoamField[(CellY + 1) * GridStationN + CellX + 1];
                    Advected = FMath::Lerp(
                        FMath::Lerp(V00, V01, Fx), FMath::Lerp(V10, V11, Fx), Fy);
                }
                Advected *= DecayFactor;
            }
            const float FinalFoam = FMath::Clamp(
                FMath::Max(SourceFoam[Index], Advected), 0.0f, 1.0f);
            NewFoamField[Index] = FinalFoam;
            VertexColors[Index].R = FinalFoam;
            FoamAdvectionSum += FinalFoam;
            FoamAdvectionMax = FMath::Max(FoamAdvectionMax, FinalFoam);
        }
    }
    FoamField = MoveTemp(NewFoamField);
    FoamFieldOriginM = CurrentFieldOriginM;
    bFoamFieldValid = true;
    FoamSum = FoamAdvectionSum;
    MaximumFoam = FoamAdvectionMax;

    // Keep fully transparent dry geometry coplanar with the local river
    // surface. At a shoreline the alpha-interpolated boundary triangles now
    // fade laterally without producing vertical skirts or black occluders.
    TArray<float> StationReferenceSurfaceZ;
    StationReferenceSurfaceZ.SetNumZeroed(GridStationN);
    for (int32 X = 0; X < GridStationN; ++X)
    {
        if (StationWetSurfaceCount[X] > 0)
        {
            StationReferenceSurfaceZ[X] =
                StationWetSurfaceZSum[X] / StationWetSurfaceCount[X];
            continue;
        }
        int32 NearestWetStation = INDEX_NONE;
        for (int32 Offset = 1; Offset < GridStationN; ++Offset)
        {
            const int32 Before = X - Offset;
            const int32 After = X + Offset;
            if (Before >= 0 && StationWetSurfaceCount[Before] > 0)
            {
                NearestWetStation = Before;
                break;
            }
            if (After < GridStationN && StationWetSurfaceCount[After] > 0)
            {
                NearestWetStation = After;
                break;
            }
        }
        if (NearestWetStation != INDEX_NONE)
        {
            StationReferenceSurfaceZ[X] =
                StationWetSurfaceZSum[NearestWetStation] /
                StationWetSurfaceCount[NearestWetStation];
        }
    }
    for (int32 Y = 0; Y < GridLateralN; ++Y)
    {
        for (int32 X = 0; X < GridStationN; ++X)
        {
            const int32 Index = Y * GridStationN + X;
            if (WetVertexMask[Index] == 0)
            {
                Vertices[Index].Z = StationReferenceSurfaceZ[X];
                Normals[Index] = FVector::UpVector;
                VertexColors[Index].A = 0.0f;
            }
            else
            {
                const float StationCoverage = ComputeStationEdgeCoverage(
                    X,
                    GridStationN,
                    ResolvedVertexSpacingMeters,
                    CurvedGridEdgeBlendMeters);
                const float LateralCoverage = ComputePresentationBankCoverage(
                    RiverCoordinatesM[Index].X,
                    Y,
                    MinimumWetLateralIndex[X],
                    MaximumWetLateralIndex[X],
                    ResolvedVertexSpacingMeters,
                    CurvedGridLateralEdgeBlendMeters,
                    bLivePresentationBankNaturalismEnabled,
                    ResolvedPresentationBankNaturalismAmplitudeMeters);
                VertexColors[Index].A = StationCoverage * LateralCoverage;
            }
        }
    }

    // Build the transmitting optical body only from quads whose four corners
    // are wet, then clip its moving-window ends with the station feather.
    // Topology changes only when the moving window recentres or a wet/dry
    // boundary changes; ordinary 15 Hz refreshes update vertices without
    // recooking the section. The core remains one centimetre under the detail
    // surface, has no collision, and cannot participate in sampling, buoyancy,
    // D3, or D4.
    if (bLiveVolumeCoreEnabled &&
        LiveVolumeCoreVertices.Num() == Vertices.Num())
    {
        TArray<int32> NewVolumeCoreTriangles;
        NewVolumeCoreTriangles.Reserve(Triangles.Num());
        for (int32 Y = 0; Y < GridLateralN - 1; ++Y)
        {
            for (int32 X = 0; X < GridStationN - 1; ++X)
            {
                const int32 I0 = Y * GridStationN + X;
                const int32 I1 = I0 + 1;
                const int32 I2 = I0 + GridStationN;
                const int32 I3 = I2 + 1;
                const bool bFullyWetCell =
                    WetVertexMask[I0] != 0 && WetVertexMask[I1] != 0 &&
                    WetVertexMask[I2] != 0 && WetVertexMask[I3] != 0;
                const float MinimumCellStationCoverage = FMath::Min(
                    ComputeStationEdgeCoverage(
                        X,
                        GridStationN,
                        ResolvedVertexSpacingMeters,
                        CurvedGridEdgeBlendMeters),
                    ComputeStationEdgeCoverage(
                        X + 1,
                        GridStationN,
                        ResolvedVertexSpacingMeters,
                        CurvedGridEdgeBlendMeters));
                if (!bFullyWetCell ||
                    MinimumCellStationCoverage <
                        kLiveVolumeCoreMinimumStationCoverage)
                {
                    continue;
                }
                NewVolumeCoreTriangles.Add(I0);
                NewVolumeCoreTriangles.Add(I2);
                NewVolumeCoreTriangles.Add(I1);
                NewVolumeCoreTriangles.Add(I1);
                NewVolumeCoreTriangles.Add(I2);
                NewVolumeCoreTriangles.Add(I3);
            }
        }
        for (int32 Index = 0; Index < Vertices.Num(); ++Index)
        {
            LiveVolumeCoreVertices[Index] =
                Vertices[Index] -
                Normals[Index].GetSafeNormal() * kLiveVolumeCoreOffsetCm;
        }
        if (bLivePresentationBankNaturalismEnabled)
        {
            // The Single Layer Water volume still shades at nearly zero
            // surface opacity, so alpha alone cannot break up its hard bank
            // silhouette. Retreat only each station's two outermost wet core
            // vertices toward their wet interior neighbour. The retreat is
            // always inward and stays inside one presentation cell; sampled
            // vertices, wet masks, topology, collision, and physics are not
            // changed.
            for (int32 X = 0; X < GridStationN; ++X)
            {
                const int32 MinimumY = MinimumWetLateralIndex[X];
                const int32 MaximumY = MaximumWetLateralIndex[X];
                if (MinimumY < 0 || MaximumY <= MinimumY + 1 ||
                    MaximumY >= GridLateralN)
                {
                    continue;
                }
                const int32 RiverRightIndex =
                    MinimumY * GridStationN + X;
                const int32 RiverRightInteriorIndex =
                    (MinimumY + 1) * GridStationN + X;
                const int32 RiverLeftIndex =
                    MaximumY * GridStationN + X;
                const int32 RiverLeftInteriorIndex =
                    (MaximumY - 1) * GridStationN + X;
                const float RiverRightRetreatMeters =
                    ComputePresentationBankRetreatMeters(
                        RiverCoordinatesM[RiverRightIndex].X,
                        false,
                        ResolvedVertexSpacingMeters,
                        true,
                        ResolvedPresentationBankNaturalismAmplitudeMeters);
                const float RiverLeftRetreatMeters =
                    ComputePresentationBankRetreatMeters(
                        RiverCoordinatesM[RiverLeftIndex].X,
                        true,
                        ResolvedVertexSpacingMeters,
                        true,
                        ResolvedPresentationBankNaturalismAmplitudeMeters);
                const float SafeSpacingMeters = FMath::Max(
                    ResolvedVertexSpacingMeters, KINDA_SMALL_NUMBER);
                LiveVolumeCoreVertices[RiverRightIndex] = FMath::Lerp(
                    LiveVolumeCoreVertices[RiverRightIndex],
                    LiveVolumeCoreVertices[RiverRightInteriorIndex],
                    RiverRightRetreatMeters / SafeSpacingMeters);
                LiveVolumeCoreVertices[RiverLeftIndex] = FMath::Lerp(
                    LiveVolumeCoreVertices[RiverLeftIndex],
                    LiveVolumeCoreVertices[RiverLeftInteriorIndex],
                    RiverLeftRetreatMeters / SafeSpacingMeters);
            }
        }
        const bool bTopologyChanged =
            LiveVolumeCoreTriangles != NewVolumeCoreTriangles;
        LiveVolumeCoreTriangles = MoveTemp(NewVolumeCoreTriangles);
        LiveVolumeCoreTriangleCount = LiveVolumeCoreTriangles.Num() / 3;
        if (LiveVolumeCoreTriangleCount > 0)
        {
            if (bTopologyChanged ||
                LiveVolumeCoreMesh->GetProcMeshSection(0) == nullptr)
            {
                LiveVolumeCoreMesh->ClearMeshSection(0);
                LiveVolumeCoreMesh->CreateMeshSection_LinearColor(
                    0,
                    LiveVolumeCoreVertices,
                    LiveVolumeCoreTriangles,
                    Normals,
                    UVs,
                    VertexColors,
                    Tangents,
                    /*bCreateCollision=*/false);
            }
            else
            {
                LiveVolumeCoreMesh->UpdateMeshSection_LinearColor(
                    0,
                    LiveVolumeCoreVertices,
                    Normals,
                    UVs,
                    VertexColors,
                    Tangents);
            }
        }
        else
        {
            LiveVolumeCoreMesh->ClearMeshSection(0);
        }
        LiveVolumeCoreMesh->SetVisibility(
            LiveVolumeCoreTriangleCount > 0, true);
    }
    else
    {
        LiveVolumeCoreTriangleCount = 0;
        LiveVolumeCoreTriangles.Reset();
        LiveVolumeCoreMesh->SetVisibility(false, true);
    }

    // Present solver-owned foam on a separate masked lace sheet. Vertex alpha
    // combines advected foam with the verified station/bank feather; the
    // material's runtime raft ellipse removes foam over the boat and crew at
    // pixel resolution. This mesh is presentation-only.
    VisibleRapidFoamVertexCount = 0;
    if (RapidFoamVertices.Num() == Vertices.Num() &&
        RapidFoamVertexColors.Num() == VertexColors.Num())
    {
        for (int32 Index = 0; Index < Vertices.Num(); ++Index)
        {
            RapidFoamVertices[Index] =
                Vertices[Index] + Normals[Index].GetSafeNormal() * 1.4f;
            // Suppress the broad low-energy haze while keeping the strongest
            // advected crests opaque enough to survive the material's lace
            // mask and gameplay-distance mips. This is a smooth response to
            // the solver-owned foam field, not an authored rapid marker.
            const float FocusedFoam = FMath::SmoothStep(
                ResolvedRapidFoamFocusStart,
                ResolvedRapidFoamFocusEnd,
                VertexColors[Index].R) * ResolvedRapidFoamCoverageGain;
            const float FoamCoverage = FMath::Clamp(
                FocusedFoam * VertexColors[Index].A,
                0.0f,
                1.0f);
            RapidFoamVertexColors[Index] = FLinearColor(
                0.96f, 0.98f, 1.0f, FoamCoverage);
            if (FoamCoverage >= 0.18f)
            {
                ++VisibleRapidFoamVertexCount;
            }
        }
        RapidFoamMesh->UpdateMeshSection_LinearColor(
            0,
            RapidFoamVertices,
            Normals,
            UVs,
            RapidFoamVertexColors,
            Tangents);
        RapidFoamMesh->SetVisibility(VisibleRapidFoamVertexCount > 0, true);
    }

    TArray<FLinearColor> SurfacePresentationColors = VertexColors;
    if (IsValid(FoamOcclusionRaft))
    {
        const FVector RaftCenterCm = FoamOcclusionRaft->GetActorLocation();
        const FVector RaftForward = FoamOcclusionRaft->GetActorForwardVector();
        const FTransform SurfaceTransform = GetActorTransform();
        for (int32 Index = 0; Index < SurfacePresentationColors.Num(); ++Index)
        {
            const FVector WorldPositionCm =
                SurfaceTransform.TransformPosition(Vertices[Index]);
            SurfacePresentationColors[Index].A *=
                ComputeRaftHullSurfaceExclusion(
                    WorldPositionCm,
                    RaftCenterCm,
                    RaftForward);
        }
    }

    const TArray<FVector2D> EmptyUVs;
    SurfaceMesh->UpdateMeshSection_LinearColor(
        0,
        Vertices,
        Normals,
        UVs,
        FlowVelocityMetersPerSecond,
        EmptyUVs,
        EmptyUVs,
        SurfacePresentationColors,
        Tangents);
    const double RefreshCpuMilliseconds =
        (FPlatformTime::Seconds() - RefreshStartSeconds) * 1000.0;
    if (!bLoggedPresentationDiagnostics && WetVertexCount > 0)
    {
        bLoggedPresentationDiagnostics = true;
        UE_LOG(
            LogTemp, Display,
            TEXT("RaftSim live water presentation: material=%s "
                 "surface_vertices=%d surface_triangles=%d "
                 "render_spacing_m=%.2f analysis_stride=%d refresh_cpu_ms=%.3f "
                 "wet_vertices=%d "
                 "foam_mean=%.4f foam_max=%.4f depth_mean_norm=%.4f speed_mean_norm=%.4f "
                 "depth_mean_m=%.3f speed_mean_mps=%.3f "
                 "standing_wave_abs_max_m=%.4f hydraulic_relief_abs_max_m=%.4f "
                 "volume_core_enabled=%d volume_core_triangles=%d "
                 "rapid_foam_vertices=%d rapid_foam_visible=%d "
                 "surface_smoothing=%d smoothing_strength=%.2f "
                 "standing_wave_scale=%.2f relief_scale=%.2f "
                 "foam_focus=[%.2f,%.2f] foam_coverage_gain=%.2f"),
            SurfaceMesh->GetMaterial(0)
                ? *SurfaceMesh->GetMaterial(0)->GetPathName()
                : TEXT("none"),
            Vertices.Num(),
            Triangles.Num() / 3,
            ResolvedVertexSpacingMeters,
            PresentationAnalysisStride,
            RefreshCpuMilliseconds,
            WetVertexCount,
            FoamSum / WetVertexCount,
            MaximumFoam,
            DepthSum / WetVertexCount,
            SpeedSum / WetVertexCount,
            DepthMetersSum / WetVertexCount,
            SpeedMpsSum / WetVertexCount,
            MaximumAbsoluteStandingWaveM,
            MaximumAbsoluteHydraulicReliefM,
            bLiveVolumeCoreEnabled ? 1 : 0,
            LiveVolumeCoreTriangleCount,
            VisibleRapidFoamVertexCount,
            IsRapidFoamMeshVisible() ? 1 : 0,
            bLivePresentationSurfaceSmoothingEnabled ? 1 : 0,
            ResolvedPresentationSurfaceSmoothingStrength,
            ResolvedPresentationStandingWaveScale,
            ResolvedPresentationHydraulicReliefScale,
            ResolvedRapidFoamFocusStart,
            ResolvedRapidFoamFocusEnd,
            ResolvedRapidFoamCoverageGain);
    }
    if (!bLoggedHydraulicReliefDiagnostics &&
        MaximumAbsoluteHydraulicReliefM > 0.01f)
    {
        bLoggedHydraulicReliefDiagnostics = true;
        UE_LOG(
            LogTemp,
            Display,
            TEXT("RaftSim live hydraulic relief activated: abs_max_m=%.4f "
                 "standing_wave_abs_max_m=%.4f wet_vertices=%d"),
            MaximumAbsoluteHydraulicReliefM,
            MaximumAbsoluteStandingWaveM,
            WetVertexCount);
    }
}

bool ARaftSimWaterSurfaceActor::IsRapidFoamMeshVisible() const
{
    return RapidFoamMesh &&
        RapidFoamMesh->IsVisible() &&
        VisibleRapidFoamVertexCount > 0;
}

bool ARaftSimWaterSurfaceActor::IsLiveVolumeCoreVisible() const
{
    return LiveVolumeCoreMesh &&
        LiveVolumeCoreMesh->IsVisible() &&
        LiveVolumeCoreTriangleCount > 0;
}

void ARaftSimWaterSurfaceActor::GetBreakingSites(TArray<FBreakingSite>& OutSites) const
{
    OutSites = BreakingSites;
}

bool ARaftSimWaterSurfaceActor::IsBreakingLipVisible() const
{
    return BreakingLipMesh && BreakingLipMesh->IsVisible() &&
        BreakingLipTriangleCount > 0;
}

bool ARaftSimWaterSurfaceActor::IsBreakingRollerVolumeVisible() const
{
    return BreakingRollerVolumeMesh && BreakingRollerVolumeMesh->IsVisible() &&
        BreakingRollerVolumeTriangleCount > 0;
}

void ARaftSimWaterSurfaceActor::SetBreakingRollerVolumeRenderingEnabled(
    bool bEnabled)
{
    bBreakingRollerVolumeRenderingEnabled = bEnabled;
    if (!bEnabled)
    {
        HideBreakingRollerVolumeMesh();
    }
}

void ARaftSimWaterSurfaceActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    PresentationPhaseSeconds = FMath::Fmod(
        PresentationPhaseSeconds + FMath::Max(DeltaSeconds, 0.0f),
        4096.0f);

    // Advance the shared flow-warped wave clock EVERY frame (the refresh
    // cadence below would stutter wave motion). Accumulating scale*dt keeps
    // phase continuous when the rate changes; scaling raw time would snap.
    // The same clock feeds the transmission WPO (via the collection) and the
    // adapter's coupled swell/band phases, so waves visibly accelerate into
    // rapids while render and rigid support stay paired.
    if (PresentationWaveClockSeconds < 0.0f)
    {
        PresentationWaveClockSeconds =
            GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
    }
    float TargetFlowClockScale = 1.0f;
    if (!IsValid(FoamOcclusionRaft))
    {
        FoamOcclusionRaft = nullptr;
        if (TActorIterator<ARaftSimRaftActor> RaftIt(GetWorld()); RaftIt)
        {
            FoamOcclusionRaft = *RaftIt;
        }
    }
    if (FoamOcclusionRaft && WaterAdapter)
    {
        FRaftSimWaterSample ClockSample;
        if (WaterAdapter->SampleWaterAtWorldPosition(
                FoamOcclusionRaft->GetActorLocation(), ClockSample) &&
            ClockSample.bWet)
        {
            // ~1.2 m/s calm current reads as the baseline cadence; a 3 m/s
            // rapid tongue runs the waves 2.5x. Clamped so pools never stall
            // and fast chutes never strobe.
            TargetFlowClockScale = FMath::Clamp(
                ClockSample.VelocityMetersPerSecond.Size2D() / 1.2f,
                0.75f,
                2.5f);
        }
    }
    SmoothedFlowClockScale += (TargetFlowClockScale - SmoothedFlowClockScale) *
        FMath::Clamp(2.0f * DeltaSeconds, 0.0f, 1.0f);
    PresentationWaveClockSeconds +=
        SmoothedFlowClockScale * FMath::Max(DeltaSeconds, 0.0f);
    if (WaterAdapter)
    {
        WaterAdapter->SetPresentationWaveClockSeconds(
            PresentationWaveClockSeconds);
    }
    if (RaftFoamOcclusionCollection && GetWorld())
    {
        if (UMaterialParameterCollectionInstance* ClockParameters =
                GetWorld()->GetParameterCollectionInstance(
                    RaftFoamOcclusionCollection))
        {
            ClockParameters->SetScalarParameterValue(
                TEXT("RaftSimWaveClockSeconds"), PresentationWaveClockSeconds);
        }
    }

    TimeSinceRefresh += DeltaSeconds;
    if (TimeSinceRefresh >= RefreshIntervalSeconds)
    {
        TimeSinceRefresh = 0.0f;
        UpdateRaftFoamExclusionParameters();
        RefreshSurface();
    }
}
