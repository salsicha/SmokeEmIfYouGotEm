#include "RaftSimWaterSurfaceActor.h"

#include "Engine/GameInstance.h"
#include "Engine/Texture2D.h"
#include "EngineUtils.h"
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
constexpr float kPresentationFoamFroudeStart = 0.72f;
constexpr float kPresentationFoamFroudeRange = 1.18f;
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

struct FPresentationStandingWave
{
    float DisplacementMeters = 0.0f;
    float StationSlope = 0.0f;
    float LateralSlope = 0.0f;
};

FPresentationStandingWave ComputePresentationStandingWave(
    const FVector2D& RiverCoordinatesMeters,
    float SpeedMetersPerSecond,
    float DepthMeters)
{
    const float SafeSpeed = FMath::Max(SpeedMetersPerSecond, 0.0f);
    const float SafeDepth = FMath::Max(DepthMeters, 0.05f);
    const float Froude = SafeSpeed / FMath::Sqrt(kGravity * SafeDepth);
    // This intentionally matches the full-reach water authoring contract in
    // south_fork_photoreal_environment.py. Runtime whitewater colour remains
    // on the stricter supercritical threshold below; the earlier response here
    // only restores the geometric shoulders hidden by the moving overlay.
    const float PresentationFoam = FMath::Clamp(
        (Froude - kPresentationFoamFroudeStart) /
            kPresentationFoamFroudeRange,
        0.0f,
        1.0f);
    const float SpeedNorm = FMath::Clamp(SafeSpeed / 8.0f, 0.0f, 1.0f);
    const float HydraulicEnergy = FMath::Clamp(
        PresentationFoam * 0.72f + SpeedNorm * 0.48f,
        0.0f,
        1.0f);

    FPresentationStandingWave Result;
    auto AccumulateBand = [&Result](
                              float AmplitudeMeters,
                              float Envelope,
                              float EnvelopeStationDerivative,
                              float EnvelopeLateralDerivative,
                              float Phase,
                              float PhaseStationDerivative,
                              float PhaseLateralDerivative)
    {
        const float SinPhase = FMath::Sin(Phase);
        const float CosPhase = FMath::Cos(Phase);
        Result.DisplacementMeters +=
            AmplitudeMeters * Envelope * SinPhase;
        Result.StationSlope +=
            AmplitudeMeters *
            (EnvelopeStationDerivative * SinPhase +
                Envelope * CosPhase * PhaseStationDerivative);
        Result.LateralSlope +=
            AmplitudeMeters *
            (EnvelopeLateralDerivative * SinPhase +
                Envelope * CosPhase * PhaseLateralDerivative);
    };

    const float StationM = RiverCoordinatesMeters.X;
    const float LateralM = RiverCoordinatesMeters.Y;

    // Calm water retains two small phase-warped ripples instead of sharing a
    // large diagonal phase with the rapid response. Their combined envelope
    // remains the authored 1.8 cm maximum.
    const float CalmWarpA = StationM * 0.11f - LateralM * 0.19f;
    const float CalmPhaseA =
        StationM * 0.73f + LateralM * 0.27f +
        0.16f * FMath::Sin(CalmWarpA);
    AccumulateBand(
        0.011f,
        1.0f,
        0.0f,
        0.0f,
        CalmPhaseA,
        0.73f + 0.16f * 0.11f * FMath::Cos(CalmWarpA),
        0.27f - 0.16f * 0.19f * FMath::Cos(CalmWarpA));

    const float CalmWarpB = StationM * 0.23f + LateralM * 0.13f;
    const float CalmPhaseB =
        StationM * 1.21f - LateralM * 0.33f +
        0.10f * FMath::Sin(CalmWarpB);
    AccumulateBand(
        0.007f,
        1.0f,
        0.0f,
        0.0f,
        CalmPhaseB,
        1.21f + 0.10f * 0.23f * FMath::Cos(CalmWarpB),
        -0.33f + 0.10f * 0.13f * FMath::Cos(CalmWarpB));

    // Build the energetic surface from flow-aligned, phase-warped crest
    // packets. The former dominant band put 11.5 cm into one continuous
    // diagonal sinusoid. This field limits every individual rapid band to
    // 6.5 cm, varies its energy over the reach, and uses incommensurate warps
    // so the pattern does not visibly tile at playable scales.
    const float PacketWarp = StationM * 0.013f - LateralM * 0.091f;
    const float PacketPhase =
        StationM * 0.041f + LateralM * 0.067f +
        0.60f * FMath::Sin(PacketWarp);
    const float PacketPhaseStationDerivative =
        0.041f + 0.60f * 0.013f * FMath::Cos(PacketWarp);
    const float PacketPhaseLateralDerivative =
        0.067f - 0.60f * 0.091f * FMath::Cos(PacketWarp);
    const float PacketSignal = 0.5f + 0.5f * FMath::Sin(PacketPhase);
    const float PacketSignalStationDerivative =
        0.5f * FMath::Cos(PacketPhase) * PacketPhaseStationDerivative;
    const float PacketSignalLateralDerivative =
        0.5f * FMath::Cos(PacketPhase) * PacketPhaseLateralDerivative;
    const float PrimaryPacket =
        0.18f + 0.82f * PacketSignal * PacketSignal;
    const float PrimaryPacketStationDerivative =
        1.64f * PacketSignal * PacketSignalStationDerivative;
    const float PrimaryPacketLateralDerivative =
        1.64f * PacketSignal * PacketSignalLateralDerivative;
    const float SecondaryPacket = 1.0f - 0.45f * PacketSignal;
    const float SecondaryPacketStationDerivative =
        -0.45f * PacketSignalStationDerivative;
    const float SecondaryPacketLateralDerivative =
        -0.45f * PacketSignalLateralDerivative;

    const float PrimaryWarpA = StationM * 0.063f - LateralM * 0.14f;
    const float PrimaryWarpB = StationM * 0.017f + LateralM * 0.23f;
    const float PrimaryPhase =
        StationM * 0.58f + LateralM * 0.09f +
        0.35f * FMath::Sin(PrimaryWarpA) +
        0.22f * FMath::Sin(PrimaryWarpB);
    AccumulateBand(
        0.065f,
        HydraulicEnergy * PrimaryPacket,
        HydraulicEnergy * PrimaryPacketStationDerivative,
        HydraulicEnergy * PrimaryPacketLateralDerivative,
        PrimaryPhase,
        0.58f + 0.35f * 0.063f * FMath::Cos(PrimaryWarpA) +
            0.22f * 0.017f * FMath::Cos(PrimaryWarpB),
        0.09f - 0.35f * 0.14f * FMath::Cos(PrimaryWarpA) +
            0.22f * 0.23f * FMath::Cos(PrimaryWarpB));

    const float SecondaryWarp = StationM * 0.033f + LateralM * 0.17f;
    const float SecondaryPhase =
        StationM * 1.03f - LateralM * 0.12f +
        0.28f * FMath::Sin(SecondaryWarp);
    AccumulateBand(
        0.043f,
        HydraulicEnergy * SecondaryPacket,
        HydraulicEnergy * SecondaryPacketStationDerivative,
        HydraulicEnergy * SecondaryPacketLateralDerivative,
        SecondaryPhase,
        1.03f + 0.28f * 0.033f * FMath::Cos(SecondaryWarp),
        -0.12f + 0.28f * 0.17f * FMath::Cos(SecondaryWarp));

    const float DetailWarp = StationM * 0.12f - LateralM * 0.33f;
    const float DetailPhase =
        StationM * 1.47f + LateralM * 0.21f +
        0.16f * FMath::Sin(DetailWarp);
    AccumulateBand(
        0.026f,
        HydraulicEnergy,
        0.0f,
        0.0f,
        DetailPhase,
        1.47f + 0.16f * 0.12f * FMath::Cos(DetailWarp),
        0.21f - 0.16f * 0.33f * FMath::Cos(DetailWarp));

    const float CrossWarp = StationM * 0.027f + LateralM * 0.19f;
    const float CrossPhase =
        StationM * 0.36f - LateralM * 0.31f +
        0.25f * FMath::Sin(CrossWarp);
    AccumulateBand(
        0.016f,
        HydraulicEnergy,
        0.0f,
        0.0f,
        CrossPhase,
        0.36f + 0.25f * 0.027f * FMath::Cos(CrossWarp),
        -0.31f + 0.25f * 0.19f * FMath::Cos(CrossWarp));
    return Result;
}

float ComputePresentationHydraulicRelief(
    float CenterSurfaceHeightMeters,
    float UpstreamFarSurfaceHeightMeters,
    float UpstreamNearSurfaceHeightMeters,
    float DownstreamNearSurfaceHeightMeters,
    float DownstreamFarSurfaceHeightMeters,
    float SpeedMetersPerSecond,
    float DepthMeters)
{
    const float SafeSpeed = FMath::Max(SpeedMetersPerSecond, 0.0f);
    const float SafeDepth = FMath::Max(DepthMeters, 0.05f);
    const float Froude = SafeSpeed / FMath::Sqrt(kGravity * SafeDepth);
    const float NearCriticalActivation = FMath::Clamp(
        (Froude - 0.55f) / 0.85f,
        0.0f,
        1.0f);
    const float SpeedActivation = FMath::Clamp(SafeSpeed / 4.0f, 0.0f, 1.0f);
    const float HydraulicActivation = FMath::Clamp(
        NearCriticalActivation * 0.82f + SpeedActivation * 0.18f,
        0.0f,
        1.0f);

    // Symmetric weights reproduce any local linear river grade exactly. The
    // residual therefore responds to solver-resolved convex crests and
    // concave holes rather than inventing relief on planar reaches.
    const float NeighbourSurfaceMeters =
        UpstreamFarSurfaceHeightMeters * 0.125f +
        UpstreamNearSurfaceHeightMeters * 0.375f +
        DownstreamNearSurfaceHeightMeters * 0.375f +
        DownstreamFarSurfaceHeightMeters * 0.125f;
    const float SolverReliefMeters =
        CenterSurfaceHeightMeters - NeighbourSurfaceMeters;
    const float MaximumReliefMeters =
        0.22f + 0.18f * FMath::Clamp(SafeDepth / 2.0f, 0.0f, 1.0f);
    return FMath::Clamp(
        SolverReliefMeters * 1.25f * HydraulicActivation,
        -MaximumReliefMeters,
        MaximumReliefMeters);
}

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
    return ComputePresentationStandingWave(
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
    return ComputePresentationHydraulicRelief(
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
    const float FilteredSurfaceHeightMeters =
        CenterSurfaceHeightMeters * 0.44f +
        (UpstreamSurfaceHeightMeters + DownstreamSurfaceHeightMeters +
            RiverRightSurfaceHeightMeters + RiverLeftSurfaceHeightMeters) * 0.14f;
    return FMath::Lerp(
        CenterSurfaceHeightMeters,
        FilteredSurfaceHeightMeters,
        FMath::Clamp(Strength, 0.0f, 1.0f));
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
        : 0.0f;
    ResolvedActiveLiveSurfaceCoverage = bLiveSurfaceCarrierEnabled
        ? FMath::Clamp(RiverWaterConfig->LiveSurfaceActiveCoverage, 0.0f, 1.0f)
        : 0.0f;
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
            ? 0.68f
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
            ? 0.55f
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
    if (bLiveSurfaceCarrierEnabled)
    {
        CurvedGridLateralEdgeBlendMeters = FMath::Clamp(
            RiverWaterConfig->LiveSurfaceBankBlendMeters,
            1.5f,
            12.0f);
    }

    bUsesCurvedRiverCoordinates = WaterAdapter && WaterAdapter->HasRiverCoordinateMap();
    // Every shipped river map owns an explicit water configuration, including
    // the legacy straight-coordinate South Fork reach. Keep config-less test
    // tanks on the original three-metre mesh while refining production river
    // presentation independently of the adapter coordinate representation.
    const bool bUsesAuthoredRiverPresentation = RiverWaterConfig != nullptr;
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

    SurfaceMesh->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, VertexColors, Tangents,
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
                    RiverWaterConfig->LiveShallowWaterOpacity);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("DeepWaterOpacity"),
                    RiverWaterConfig->LiveDeepWaterOpacity);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("FoamWaterOpacity"),
                    RiverWaterConfig->LiveFoamWaterOpacity);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("RaftInteriorSurfaceOpacityScale"), 0.0f);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("RaftInteriorOpticalDepthScale"), 0.0f);
                // River-local render-only optical coefficients. Defaults keep
                // the accepted cold-water calibration; sediment-bearing rivers
                // can transmit warmer bed light without changing hydraulics.
                VolumeMaterial->SetVectorParameterValue(
                    TEXT("WaterScattering"),
                    RiverWaterConfig->LiveWaterScattering);
                VolumeMaterial->SetVectorParameterValue(
                    TEXT("WaterAbsorption"),
                    RiverWaterConfig->LiveWaterAbsorption);
                VolumeMaterial->SetVectorParameterValue(
                    TEXT("RiverbedColorScale"),
                    RiverWaterConfig->LiveRiverbedColorScale);
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
                        : 0.18f);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveFoamIntensity"),
                    bLiveSurfaceCarrierEnabled
                        ? ResolvedLiveFoamIntensity
                        : 0.52f);
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
                    TEXT("BreakingFoamFloor"), 0.02f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamIntensityGain"), 0.62f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("PrimaryLaceGain"), 0.45f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("DetailLaceGain"), 0.20f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamCoreGain"), 1.25f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingWaterRoughness"), 0.16f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingFoamRoughness"), 0.78f);
                BreakingMaterial->SetScalarParameterValue(
                    TEXT("BreakingWaterSpecular"), 0.30f);
                BreakingMaterial->SetVectorParameterValue(
                    TEXT("BreakingWaterColor"),
                    FLinearColor(0.10f, 0.22f, 0.27f, 1.0f));
                BreakingMaterial->SetVectorParameterValue(
                    TEXT("BreakingFoamColor"),
                    FLinearColor(0.64f, 0.69f, 0.68f, 1.0f));
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
                        TEXT("BreakingFoamFloor"), 0.010f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("BreakingFoamIntensityGain"), 0.44f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("PrimaryLaceGain"), 0.68f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("DetailLaceGain"), 0.38f);
                    RollerMaterial->SetScalarParameterValue(
                        TEXT("BreakingFoamCoreGain"), 1.12f);
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
                        FLinearColor(0.62f, 0.68f, 0.67f, 1.0f));
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

    // One alpha-perforated curtain supplies a connected overturning body under
    // production Niagara. The former three-shell fallback read as a repeated
    // translucent dome when it was visible beside particles. Keeping only one
    // irregular plunge membrane at the three strongest solver sites removes
    // that nested volume cue and bounds the population to 1,512 triangles.
    // The component never owns collision or water samples.
    constexpr int32 kMaximumRollerSites = 3;
    constexpr int32 kLayerCount = 1;
    constexpr int32 kAcrossSegments = 18;
    constexpr int32 kLoopSegments = 14;
    TArray<FVector> RollerVertices;
    TArray<int32> RollerTriangles;
    TArray<FVector> RollerNormals;
    TArray<FVector2D> RollerUvs;
    TArray<FLinearColor> RollerColors;
    TArray<FProcMeshTangent> RollerTangents;
    const int32 VerticesPerLayer =
        (kAcrossSegments + 1) * (kLoopSegments + 1);
    const int32 MaximumTrianglesPerSite =
        kLayerCount * kAcrossSegments * kLoopSegments * 2;
    const int32 RollerSiteCount = FMath::Min(
        BreakingSites.Num(), kMaximumRollerSites);
    RollerVertices.Reserve(
        RollerSiteCount * kLayerCount * VerticesPerLayer);
    RollerTriangles.Reserve(
        RollerSiteCount * MaximumTrianglesPerSite * 3);
    RollerNormals.Reserve(
        RollerSiteCount * kLayerCount * VerticesPerLayer);
    RollerUvs.Reserve(
        RollerSiteCount * kLayerCount * VerticesPerLayer);
    RollerColors.Reserve(
        RollerSiteCount * kLayerCount * VerticesPerLayer);
    RollerTangents.Reserve(
        RollerSiteCount * kLayerCount * VerticesPerLayer);

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

        for (int32 LayerIndex = 0; LayerIndex < kLayerCount; ++LayerIndex)
        {
            const float LayerT = 0.45f;
            const float LayerHalfWidthCm = SiteHalfWidthCm;
            const int32 BaseVertex = RollerVertices.Num();

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
                            ProfileLoopT, Intensity, LayerT);
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
                                SiteIndex * 1.67f + LayerIndex * 2.11f +
                            SignedAcross * 10.3f + ProfileLoopT * 8.9f) +
                            0.18f * FMath::Sin(
                                SiteIndex * 2.43f - LayerIndex * 1.37f -
                                SignedAcross * 16.7f + ProfileLoopT * 15.1f),
                        0.16f,
                        1.0f);
                    const float OrganicTravelCm =
                        FMath::Sin(
                            SiteIndex * 1.13f + LayerIndex * 0.91f +
                            SignedAcross * 4.7f + ProfileLoopT * 6.3f) *
                        13.0f * Intensity * EdgeTaper * LoopFeather;
                    const float OrganicLiftCm =
                        FMath::Sin(
                            SiteIndex * 2.07f - LayerIndex * 1.29f +
                            SignedAcross * 7.1f + ProfileLoopT * 11.7f) *
                        14.0f * Intensity * EdgeTaper * LoopFeather;
                    const FVector Position =
                        Site.WorldPositionCm +
                        Downstream * (Profile.X + OrganicTravelCm) +
                        Across * (SignedAcross * LayerHalfWidthCm) +
                        FVector::UpVector * (Profile.Y + OrganicLiftCm + 4.0f);
                    RollerVertices.Add(Position);
                    RollerUvs.Add(FVector2D(
                        AcrossT * 5.4f + LayerT * 0.31f,
                        LoopT * 3.6f + LayerT * 0.37f));
                    const float CoreDistance = (ProfileLoopT - 0.57f) / 0.18f;
                    const float AeratedCore =
                        FMath::Exp(-CoreDistance * CoreDistance) *
                        FMath::Lerp(0.52f, 0.95f, Intensity) * Breakup;
                    const float FoamBrightness = FMath::Lerp(
                        0.62f, 0.86f, AeratedCore);
                    RollerColors.Add(FLinearColor(
                        FoamBrightness * 0.94f,
                        FoamBrightness,
                        FoamBrightness * 0.98f,
                        EdgeTaper * LoopFeather *
                            FMath::Lerp(0.84f, 1.0f, AeratedCore)));

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
                            PreviousLoopT, Intensity, LayerT);
                    FVector2D NextProfile =
                        ComputeBreakingRollerVolumeProfileCentimeters(
                            NextLoopT, Intensity, LayerT);
                    PreviousProfile.Y *= FMath::Lerp(0.78f, 1.0f, EdgeTaper);
                    NextProfile.Y *= FMath::Lerp(0.78f, 1.0f, EdgeTaper);
                    const FVector LongitudinalTangent =
                        Downstream * (NextProfile.X - PreviousProfile.X) +
                        FVector::UpVector * (NextProfile.Y - PreviousProfile.Y);
                    RollerNormals.Add(
                        FVector::CrossProduct(LongitudinalTangent, Across)
                            .GetSafeNormal());
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
                    if (((AcrossIndex + LoopIndex + LayerIndex + SiteIndex) & 1) == 0)
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
    }

    BreakingRollerVolumeMesh->CreateMeshSection_LinearColor(
        0, RollerVertices, RollerTriangles, RollerNormals, RollerUvs,
        RollerColors, RollerTangents, false);
    BreakingRollerVolumeTriangleCount = RollerTriangles.Num() / 3;
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
            HydraulicReliefMeters[Index] = ComputePresentationHydraulicRelief(
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
            if (WetVertexMask[Index] != 0)
            {
                const FRaftSimWaterSample& Sample = WaterSamples[Index];
                const float Speed = Sample.VelocityMetersPerSecond.Size2D();
                const float Depth = FMath::Max(Sample.DepthMeters, 0.05f);
                const FPresentationStandingWave StandingWave =
                    ComputePresentationStandingWave(
                        RiverCoordinatesM[Index], Speed, Depth);
                const float HydraulicRelief = HydraulicReliefMeters[Index];
                // The authored seasonal surface remains beneath this live
                // solver patch. Reapply its deterministic sub-grid ripple and
                // sharpen only the large-scale relief already present in the
                // sampled cooked surface. A 2 cm presentation lift prevents
                // depth fighting. None of these terms changes physics.
                SurfaceZCm =
                    (PresentationSurfaceHeightMeters[Index] +
                        StandingWave.DisplacementMeters *
                            ResolvedPresentationStandingWaveScale +
                        HydraulicRelief) *
                        kSurfCmPerM +
                    2.0f;
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
                Foam = FMath::Clamp((Froude - 1.0f) / 1.1f, 0.0f, 1.0f);
                SourceFoam[Index] = Foam;
                DepthNorm = FMath::Clamp(Sample.DepthMeters / 4.0f, 0.0f, 1.0f);
                SpeedNorm = FMath::Clamp(Speed / 8.0f, 0.0f, 1.0f);
                ++WetVertexCount;
                DepthSum += DepthNorm;
                SpeedSum += SpeedNorm;
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
                (UpstreamFroude - 1.0f) / 1.4f, 0.0f, 1.0f) * DepthScale;
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

            SourceFoam[UpstreamIndex] = FMath::Max(
                SourceFoam[UpstreamIndex], 0.55f * Intensity + 0.15f);
            SourceFoam[Index] = FMath::Max(
                SourceFoam[Index], 0.85f * Intensity + 0.15f);

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
                    Intensity * FMath::Max(Phase, 0.0f) * 0.55f * Decay + 0.30f * Decay);
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
                const float LateralCoverage = ComputeLateralWetCoverage(
                    Y,
                    MinimumWetLateralIndex[X],
                    MaximumWetLateralIndex[X],
                    ResolvedVertexSpacingMeters,
                    CurvedGridLateralEdgeBlendMeters);
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
                0.62f, 0.68f, 0.66f, FoamCoverage);
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

    SurfaceMesh->UpdateMeshSection_LinearColor(
        0, Vertices, Normals, UVs, VertexColors, Tangents);
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
                 "foam_mean=%.4f foam_max=%.4f depth_mean=%.4f speed_mean=%.4f "
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
    TimeSinceRefresh += DeltaSeconds;
    if (TimeSinceRefresh >= RefreshIntervalSeconds)
    {
        TimeSinceRefresh = 0.0f;
        UpdateRaftFoamExclusionParameters();
        RefreshSurface();
    }
}
