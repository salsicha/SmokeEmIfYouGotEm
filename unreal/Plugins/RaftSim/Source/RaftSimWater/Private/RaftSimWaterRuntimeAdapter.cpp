#include "RaftSimWaterRuntimeAdapter.h"

#include "RaftSimLiveWaterWindow.h"

URaftSimWaterRuntimeAdapter::~URaftSimWaterRuntimeAdapter() = default;

#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformTime.h"
#include "Misc/Crc.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

void URaftSimWaterRuntimeAdapter::Configure(const FRaftSimWaterRuntimeConfig& InConfig)
{
    Config = InConfig;
    CaptureState = FRaftSimWaterDeterministicCaptureState();
    CaptureState.CapturePath = Config.DeterministicCapturePath;
    CaptureState.bEnabled = Config.bEnableDeterministicCapture;
    CommittedWaterFrame = 0;
    SimTimeSeconds = 0.0;
    LastHandoffTransferredCellCount = 0;
    MovingWindowHandoffCount = 0;
    bLastHandoffPreservedState = false;
    TotalSolverStepMilliseconds = 0.0;
    LastSolverStepMillisecondsValue = 0.0;
    MaxSolverStepMilliseconds = 0.0;
    TimedSolverStepCount = 0;
    RiverCoordinatePoints.Reset();
    RiverSpatialHash.Reset();
    LastWorldToRiverSegment = INDEX_NONE;
    LastWorldToRiverPositionM = FVector2D::ZeroVector;
    bHasLastWorldToRiverQuery = false;
    RiverVerticalDatumM = 0.0f;
    RiverCoordinateMapPath.Reset();
    bRaftSupportSurfaceEnabled = false;
    RaftSupportSurfaceSmoothingStrength = 0.0f;
    RaftSupportStandingWaveScale = 0.0f;
    RaftSupportHydraulicReliefScale = 0.0f;

    bool bManifestReady = !Config.bRequireAcceptedReportManifest;
    if (!Config.AcceptedReportSetManifestPath.IsEmpty())
    {
        bManifestReady = LoadAcceptedReportManifest(Config.AcceptedReportSetManifestPath);
    }

    Status = (!Config.ScenarioPackagePath.IsEmpty() && bManifestReady)
        ? ERaftSimWaterRuntimeStatus::ScenarioBound
        : ERaftSimWaterRuntimeStatus::Uninitialized;
}

bool URaftSimWaterRuntimeAdapter::LoadAcceptedReportManifest(const FString& ManifestPath)
{
    ReportManifestState = FRaftSimWaterReportManifestState();
    ReportManifestState.ManifestPath = ManifestPath;

    FString ManifestText;
    const FString FullPath = ResolveRuntimeDataPath(ManifestPath);
    if (!FFileHelper::LoadFileToString(ManifestText, *FullPath))
    {
        Status = ERaftSimWaterRuntimeStatus::Faulted;
        return false;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ManifestText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        Status = ERaftSimWaterRuntimeStatus::Faulted;
        return false;
    }

    FString Schema;
    const bool bSchemaOk = Root->TryGetStringField(TEXT("schema"), Schema)
        && Schema == TEXT("raftsim.milestone20.report_set_lock.v1");
    bool bPassed = false;
    Root->TryGetBoolField(TEXT("passed"), bPassed);

    const TSharedPtr<FJsonObject>* LockObject = nullptr;
    if (Root->TryGetObjectField(TEXT("lock"), LockObject)
        && LockObject != nullptr
        && LockObject->IsValid())
    {
        (*LockObject)->TryGetStringField(TEXT("lock_hash"), ReportManifestState.LockHash);
        ReportManifestState.LockedArtifactCount = (*LockObject)->GetIntegerField(TEXT("artifact_count"));
    }

    const TSharedPtr<FJsonObject>* ProductionUse = nullptr;
    bool bLiveWaterBridgeUnblocked = false;
    if (Root->TryGetObjectField(TEXT("production_use"), ProductionUse)
        && ProductionUse != nullptr
        && ProductionUse->IsValid())
    {
        (*ProductionUse)->TryGetBoolField(
            TEXT("live_water_unreal_bridge_foundation_unblocked"),
            bLiveWaterBridgeUnblocked
        );
    }

    const bool bLockMatches = Config.ExpectedReportSetLockHash.IsEmpty()
        || Config.ExpectedReportSetLockHash == ReportManifestState.LockHash;
    ReportManifestState.bLoaded = true;
    ReportManifestState.bAccepted = bSchemaOk && bPassed && bLockMatches;
    ReportManifestState.bLiveWaterBridgeUnblocked =
        ReportManifestState.bAccepted && bLiveWaterBridgeUnblocked;
    return ReportManifestState.bLiveWaterBridgeUnblocked;
}

bool URaftSimWaterRuntimeAdapter::StepWater(float DeltaSeconds)
{
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized || DeltaSeconds <= 0.0f)
    {
        return false;
    }

    if (Config.bRequireAcceptedReportManifest && !ReportManifestState.bLiveWaterBridgeUnblocked)
    {
        Status = ERaftSimWaterRuntimeStatus::Faulted;
        return false;
    }

    Status = ERaftSimWaterRuntimeStatus::Running;
#if RAFTSIM_HAS_LIVE_SOLVER
    if (LiveWindow.IsValid())
    {
        const double StartSeconds = FPlatformTime::Seconds();
        LiveWindow->Step(DeltaSeconds);
        const double ElapsedMilliseconds =
            (FPlatformTime::Seconds() - StartSeconds) * 1000.0;
        LastSolverStepMillisecondsValue = ElapsedMilliseconds;
        TotalSolverStepMilliseconds += ElapsedMilliseconds;
        MaxSolverStepMilliseconds = FMath::Max(
            MaxSolverStepMilliseconds, ElapsedMilliseconds);
        ++TimedSolverStepCount;
    }
#endif
    SimTimeSeconds += DeltaSeconds;
    ++CommittedWaterFrame;
    AppendDeterministicCaptureFrame();
    return true;
}

namespace
{
constexpr float kCoupledSurfaceGravity = 9.80665f;
constexpr float kCoupledFoamFroudeStart = 0.72f;
constexpr float kCoupledFoamFroudeRange = 1.18f;
// Mirror of the render-side travelling wave. The band bake
// (RaftSimEditorSouthForkFullReach.cpp) plus the transmission material's
// RaftSimTravelingBakeWaveWPO block present this moving field; coupling it
// into sampled surface heights makes the raft — rigid support, flex
// segments (which is what lets the soft hull CURVE over wave shapes),
// overwash, audio, and telemetry — feel the same waves the camera sees
// (2026-08-10 playtest: "the water level goes up and down in the boat,
// but the boat doesn't ride over the waves"). Constants must stay paired
// with the WPO block; energy is recomputed from Froude and speed, the
// same quantities the bake's vertex colours encoded.
float PresentationTravelingWaveM(
    float StationM, float LateralM, float TimeSeconds,
    float SpeedMps, float DepthM)
{
    // Base swell only. The energetic term's render amplitude derives from
    // BAKED band colours while a physics-side reconstruction can only use
    // LIVE solver energy — the two diverge in exactly the water where the
    // waves are big, and the 2026-08-10 playtest saw the hull visually
    // buried under rendered crests it correctly was not riding ("the boat
    // went below the water surface for no apparent reason"; drift
    // telemetry showed constant 21 cm draft throughout). The universal
    // base term is identical on both sides, so coupling it is exact; the
    // energetic mismatch is bounded separately by halving the rendered
    // energetic amplitude in the WPO block.
    (void)SpeedMps;
    (void)DepthM;
    const float PhaseA =
        StationM * 0.19f + LateralM * 0.61f - TimeSeconds * 0.90f;
    return 0.030f * FMath::Sin(PhaseA);
}

static TAutoConsoleVariable<int32> CVarRaftSimPresentationWaveCoupling(
    TEXT("RaftSim.Water.PresentationWaveCoupling"), 1,
    TEXT("1: sampled water heights include the rendered travelling wave, and "
         "rigid support also follows the shared standing-wave and hydraulic-"
         "relief surface; 0: matched-baseline solver heights only."));
}
FRaftSimWaterStandingWave URaftSimWaterRuntimeAdapter::ComputeCoupledStandingWave(
    const FVector2D& RiverCoordinatesMeters,
    float SpeedMetersPerSecond,
    float DepthMeters)
{
    const float SafeSpeed = FMath::Max(SpeedMetersPerSecond, 0.0f);
    const float SafeDepth = FMath::Max(DepthMeters, 0.05f);
    const float Froude =
        SafeSpeed / FMath::Sqrt(kCoupledSurfaceGravity * SafeDepth);
    const float PresentationFoam = FMath::Clamp(
        (Froude - kCoupledFoamFroudeStart) / kCoupledFoamFroudeRange,
        0.0f,
        1.0f);
    const float SpeedNorm = FMath::Clamp(SafeSpeed / 8.0f, 0.0f, 1.0f);
    const float HydraulicEnergy = FMath::Clamp(
        PresentationFoam * 0.72f + SpeedNorm * 0.48f,
        0.0f,
        1.0f);

    FRaftSimWaterStandingWave Result;
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
    const float CalmWarpA = StationM * 0.11f - LateralM * 0.19f;
    const float CalmPhaseA =
        StationM * 0.73f + LateralM * 0.27f +
        0.16f * FMath::Sin(CalmWarpA);
    AccumulateBand(
        0.011f, 1.0f, 0.0f, 0.0f, CalmPhaseA,
        0.73f + 0.16f * 0.11f * FMath::Cos(CalmWarpA),
        0.27f - 0.16f * 0.19f * FMath::Cos(CalmWarpA));

    const float CalmWarpB = StationM * 0.23f + LateralM * 0.13f;
    const float CalmPhaseB =
        StationM * 1.21f - LateralM * 0.33f +
        0.10f * FMath::Sin(CalmWarpB);
    AccumulateBand(
        0.007f, 1.0f, 0.0f, 0.0f, CalmPhaseB,
        1.21f + 0.10f * 0.23f * FMath::Cos(CalmWarpB),
        -0.33f + 0.10f * 0.13f * FMath::Cos(CalmWarpB));

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
        0.026f, HydraulicEnergy, 0.0f, 0.0f, DetailPhase,
        1.47f + 0.16f * 0.12f * FMath::Cos(DetailWarp),
        0.21f - 0.16f * 0.33f * FMath::Cos(DetailWarp));

    const float CrossWarp = StationM * 0.027f + LateralM * 0.19f;
    const float CrossPhase =
        StationM * 0.36f - LateralM * 0.31f +
        0.25f * FMath::Sin(CrossWarp);
    AccumulateBand(
        0.016f, HydraulicEnergy, 0.0f, 0.0f, CrossPhase,
        0.36f + 0.25f * 0.027f * FMath::Cos(CrossWarp),
        -0.31f + 0.25f * 0.19f * FMath::Cos(CrossWarp));
    return Result;
}

float URaftSimWaterRuntimeAdapter::ComputeCoupledHydraulicReliefMeters(
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
    const float Froude =
        SafeSpeed / FMath::Sqrt(kCoupledSurfaceGravity * SafeDepth);
    const float NearCriticalActivation = FMath::Clamp(
        (Froude - 0.55f) / 0.85f, 0.0f, 1.0f);
    const float SpeedActivation =
        FMath::Clamp(SafeSpeed / 4.0f, 0.0f, 1.0f);
    const float HydraulicActivation = FMath::Clamp(
        NearCriticalActivation * 0.82f + SpeedActivation * 0.18f,
        0.0f,
        1.0f);
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

float URaftSimWaterRuntimeAdapter::ComputeCoupledSmoothedSurfaceHeightMeters(
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
            RiverRightSurfaceHeightMeters + RiverLeftSurfaceHeightMeters) *
            0.14f;
    return FMath::Lerp(
        CenterSurfaceHeightMeters,
        FilteredSurfaceHeightMeters,
        FMath::Clamp(Strength, 0.0f, 1.0f));
}

bool URaftSimWaterRuntimeAdapter::SampleWaterAtWorldPosition(
    const FVector& WorldPosition,
    FRaftSimWaterSample& OutSample
) const
{
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized)
    {
        return false;
    }

    OutSample.WorldPosition = WorldPosition;
#if RAFTSIM_HAS_LIVE_SOLVER
    if (LiveWindow.IsValid())
    {
        FVector2D SolverPositionM(WorldPosition.X / 100.0, WorldPosition.Y / 100.0);
        FVector WorldTangent = FVector::ForwardVector;
        FVector WorldLeftNormal = FVector::RightVector;
        if (HasRiverCoordinateMap() &&
            !WorldToRiverCoordinates(
                WorldPosition, SolverPositionM, WorldTangent, WorldLeftNormal))
        {
            return false;
        }
        const FRaftSimLiveWaterSampleResult Live = LiveWindow->Sample(SolverPositionM);
        if (Live.bValid)
        {
            OutSample.SurfaceHeightMeters = Live.SurfaceHeightM - RiverVerticalDatumM;
            if (Live.bWet && LiveWindow->HasTravelingWavePresentation() &&
                CVarRaftSimPresentationWaveCoupling.GetValueOnAnyThread() != 0)
            {
                const UWorld* World = GetWorld();
                OutSample.SurfaceHeightMeters += PresentationTravelingWaveM(
                    SolverPositionM.X, SolverPositionM.Y,
                    World ? World->GetTimeSeconds() : 0.0f,
                    Live.VelocityMps.Size(), Live.DepthM);
            }
            OutSample.BedHeightMeters = Live.BedHeightM - RiverVerticalDatumM;
            OutSample.DepthMeters = Live.DepthM;
            OutSample.VelocityMetersPerSecond =
                WorldTangent * Live.VelocityMps.X +
                WorldLeftNormal * Live.VelocityMps.Y;
            OutSample.SurfaceNormal = (
                WorldTangent * Live.SurfaceNormal.X +
                WorldLeftNormal * Live.SurfaceNormal.Y +
                FVector::UpVector * Live.SurfaceNormal.Z).GetSafeNormal();
            OutSample.bWet = Live.bWet;
            return true;
        }
        // A live window is authoritative over its finite crop. Outside that
        // crop there is no fallback sheet of water.
        return false;
    }
#endif
    OutSample.SurfaceHeightMeters = WorldPosition.Z;
    OutSample.BedHeightMeters = WorldPosition.Z - 1.0f;
    OutSample.DepthMeters = 1.0f;
    OutSample.VelocityMetersPerSecond = FVector::ZeroVector;
    OutSample.SurfaceNormal = FVector::UpVector;
    OutSample.bWet = true;
    return true;
}
void URaftSimWaterRuntimeAdapter::ConfigureRaftSupportSurface(
    bool bEnabled,
    float SurfaceSmoothingStrength,
    float StandingWaveScale,
    float HydraulicReliefScale)
{
    bRaftSupportSurfaceEnabled = bEnabled;
    RaftSupportSurfaceSmoothingStrength =
        FMath::Clamp(SurfaceSmoothingStrength, 0.0f, 1.0f);
    RaftSupportStandingWaveScale =
        FMath::Clamp(StandingWaveScale, 0.0f, 1.0f);
    RaftSupportHydraulicReliefScale =
        FMath::Clamp(HydraulicReliefScale, 0.0f, 1.0f);

    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim raft support surface: enabled=%d smoothing=%.2f ")
        TEXT("standing=%.2f hydraulic=%.2f"),
        bRaftSupportSurfaceEnabled ? 1 : 0,
        RaftSupportSurfaceSmoothingStrength,
        RaftSupportStandingWaveScale,
        RaftSupportHydraulicReliefScale);
}

bool URaftSimWaterRuntimeAdapter::SampleRaftSupportSurfaceAtWorldPosition(
    const FVector& WorldPosition,
    FRaftSimWaterSample& OutSample) const
{
    if (!SampleWaterAtWorldPosition(WorldPosition, OutSample))
    {
        return false;
    }

#if RAFTSIM_HAS_LIVE_SOLVER
    if (!bRaftSupportSurfaceEnabled ||
        !OutSample.bWet ||
        !LiveWindow.IsValid() ||
        !LiveWindow->HasTravelingWavePresentation() ||
        CVarRaftSimPresentationWaveCoupling.GetValueOnAnyThread() == 0)
    {
        return true;
    }

    FVector2D RiverCoordinatesM(
        WorldPosition.X / 100.0f,
        WorldPosition.Y / 100.0f);
    FVector WorldTangent = FVector::ForwardVector;
    FVector WorldLeftNormal = FVector::RightVector;
    if (!WorldToRiverCoordinates(
            WorldPosition,
            RiverCoordinatesM,
            WorldTangent,
            WorldLeftNormal))
    {
        return true;
    }

    constexpr float AnalysisNearOffsetM = 3.0f;
    constexpr float AnalysisFarOffsetM = 6.0f;
    auto SamplePresentedBaseHeight = [this](
                                         const FVector2D& CoordinatesM,
                                         float& OutHeightM) -> bool
    {
        FRaftSimWaterSample Center;
        if (!SampleWaterFieldAtRiverCoordinates(CoordinatesM, Center) ||
            !Center.bWet)
        {
            return false;
        }
        OutHeightM = Center.SurfaceHeightMeters;
        if (RaftSupportSurfaceSmoothingStrength <= KINDA_SMALL_NUMBER)
        {
            return true;
        }

        FRaftSimWaterSample Upstream;
        FRaftSimWaterSample Downstream;
        FRaftSimWaterSample RiverRight;
        FRaftSimWaterSample RiverLeft;
        if (!SampleWaterFieldAtRiverCoordinates(
                CoordinatesM + FVector2D(-AnalysisNearOffsetM, 0.0f),
                Upstream) ||
            !SampleWaterFieldAtRiverCoordinates(
                CoordinatesM + FVector2D(AnalysisNearOffsetM, 0.0f),
                Downstream) ||
            !SampleWaterFieldAtRiverCoordinates(
                CoordinatesM + FVector2D(0.0f, -AnalysisNearOffsetM),
                RiverRight) ||
            !SampleWaterFieldAtRiverCoordinates(
                CoordinatesM + FVector2D(0.0f, AnalysisNearOffsetM),
                RiverLeft) ||
            !Upstream.bWet ||
            !Downstream.bWet ||
            !RiverRight.bWet ||
            !RiverLeft.bWet)
        {
            return true;
        }

        OutHeightM = ComputeCoupledSmoothedSurfaceHeightMeters(
            Center.SurfaceHeightMeters,
            Upstream.SurfaceHeightMeters,
            Downstream.SurfaceHeightMeters,
            RiverRight.SurfaceHeightMeters,
            RiverLeft.SurfaceHeightMeters,
            RaftSupportSurfaceSmoothingStrength);
        return true;
    };

    FRaftSimWaterSample RawCenter;
    float PresentedCenterHeightM = 0.0f;
    if (!SampleWaterFieldAtRiverCoordinates(RiverCoordinatesM, RawCenter) ||
        !RawCenter.bWet ||
        !SamplePresentedBaseHeight(
            RiverCoordinatesM,
            PresentedCenterHeightM))
    {
        return true;
    }

    // Replace the unsmoothed solver base with the carrier's base. Preserve the
    // already-coupled travelling swell added by SampleWaterAtWorldPosition.
    OutSample.SurfaceHeightMeters +=
        PresentedCenterHeightM - RawCenter.SurfaceHeightMeters;

    const FRaftSimWaterStandingWave StandingWave =
        ComputeCoupledStandingWave(
            RiverCoordinatesM,
            RawCenter.VelocityMetersPerSecond.Size2D(),
            RawCenter.DepthMeters);
    OutSample.SurfaceHeightMeters +=
        StandingWave.DisplacementMeters * RaftSupportStandingWaveScale;

    float UpstreamFarHeightM = 0.0f;
    float UpstreamNearHeightM = 0.0f;
    float DownstreamNearHeightM = 0.0f;
    float DownstreamFarHeightM = 0.0f;
    if (SamplePresentedBaseHeight(
            RiverCoordinatesM + FVector2D(-AnalysisFarOffsetM, 0.0f),
            UpstreamFarHeightM) &&
        SamplePresentedBaseHeight(
            RiverCoordinatesM + FVector2D(-AnalysisNearOffsetM, 0.0f),
            UpstreamNearHeightM) &&
        SamplePresentedBaseHeight(
            RiverCoordinatesM + FVector2D(AnalysisNearOffsetM, 0.0f),
            DownstreamNearHeightM) &&
        SamplePresentedBaseHeight(
            RiverCoordinatesM + FVector2D(AnalysisFarOffsetM, 0.0f),
            DownstreamFarHeightM))
    {
        OutSample.SurfaceHeightMeters +=
            ComputeCoupledHydraulicReliefMeters(
                PresentedCenterHeightM,
                UpstreamFarHeightM,
                UpstreamNearHeightM,
                DownstreamNearHeightM,
                DownstreamFarHeightM,
                RawCenter.VelocityMetersPerSecond.Size2D(),
                RawCenter.DepthMeters) *
            RaftSupportHydraulicReliefScale;
    }
#endif

    return true;
}

bool URaftSimWaterRuntimeAdapter::SampleWaterAtRiverCoordinates(
    FVector2D StationLateralM,
    FRaftSimWaterSample& OutSample
) const
{
    FRaftSimWaterSample RiverSample;
    if (!SampleWaterFieldAtRiverCoordinates(StationLateralM, RiverSample))
    {
        return false;
    }

    FVector WorldPositionCm = FVector::ZeroVector;
    FVector WorldTangent = FVector::ForwardVector;
    FVector WorldLeftNormal = FVector::RightVector;
    if (!ResolveRiverBasis(
            StationLateralM,
            RiverSample.SurfaceHeightMeters + RiverVerticalDatumM,
            WorldPositionCm, WorldTangent, WorldLeftNormal))
    {
        return false;
    }

    OutSample = RiverSample;
    OutSample.WorldPosition = WorldPositionCm;
    OutSample.VelocityMetersPerSecond =
        WorldTangent * RiverSample.VelocityMetersPerSecond.X +
        WorldLeftNormal * RiverSample.VelocityMetersPerSecond.Y;
    OutSample.SurfaceNormal = (
        WorldTangent * RiverSample.SurfaceNormal.X +
        WorldLeftNormal * RiverSample.SurfaceNormal.Y +
        FVector::UpVector * RiverSample.SurfaceNormal.Z).GetSafeNormal();
    return true;
}

bool URaftSimWaterRuntimeAdapter::SampleWaterFieldAtRiverCoordinates(
    FVector2D StationLateralM,
    FRaftSimWaterSample& OutSample
) const
{
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized)
    {
        return false;
    }

#if RAFTSIM_HAS_LIVE_SOLVER
    if (LiveWindow.IsValid())
    {
        const FRaftSimLiveWaterSampleResult Live = LiveWindow->Sample(StationLateralM);
        if (!Live.bValid)
        {
            return false;
        }
        OutSample.WorldPosition = FVector::ZeroVector;
        OutSample.SurfaceHeightMeters = Live.SurfaceHeightM - RiverVerticalDatumM;
        OutSample.BedHeightMeters = Live.BedHeightM - RiverVerticalDatumM;
        OutSample.DepthMeters = Live.DepthM;
        OutSample.VelocityMetersPerSecond = FVector(
            Live.VelocityMps.X, Live.VelocityMps.Y, 0.0);
        OutSample.SurfaceNormal = Live.SurfaceNormal;
        OutSample.bWet = Live.bWet;
        return true;
    }
#endif

    OutSample.WorldPosition = FVector(
        StationLateralM.X * 100.0f, StationLateralM.Y * 100.0f, 0.0f);
    OutSample.SurfaceHeightMeters = 0.0f;
    OutSample.BedHeightMeters = -1.0f;
    OutSample.DepthMeters = 1.0f;
    OutSample.VelocityMetersPerSecond = FVector::ZeroVector;
    OutSample.SurfaceNormal = FVector::UpVector;
    OutSample.bWet = true;
    return true;
}

FIntPoint URaftSimWaterRuntimeAdapter::RiverSpatialHashKey(
    const FVector2D& PositionM) const
{
    return FIntPoint(
        FMath::FloorToInt(PositionM.X / RiverSpatialHashCellM),
        FMath::FloorToInt(PositionM.Y / RiverSpatialHashCellM));
}

void URaftSimWaterRuntimeAdapter::RebuildRiverSpatialHash()
{
    RiverSpatialHash.Reset();
    for (int32 PointIndex = 0; PointIndex < RiverCoordinatePoints.Num(); ++PointIndex)
    {
        RiverSpatialHash.FindOrAdd(
            RiverSpatialHashKey(RiverCoordinatePoints[PointIndex].LocalPositionM)).Add(PointIndex);
    }
}

bool URaftSimWaterRuntimeAdapter::ConfigureRiverCoordinateMap(
    const FString& CoordinateMapPath)
{
    RiverCoordinatePoints.Reset();
    RiverSpatialHash.Reset();
    LastWorldToRiverSegment = INDEX_NONE;
    LastWorldToRiverPositionM = FVector2D::ZeroVector;
    bHasLastWorldToRiverQuery = false;
    RiverVerticalDatumM = 0.0f;
    RiverCoordinateMapPath.Reset();

    FString Text;
    const FString FullPath = ResolveRuntimeDataPath(CoordinateMapPath);
    if (!FFileHelper::LoadFileToString(Text, *FullPath))
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim coordinate map not found: %s"), *FullPath);
        return false;
    }
    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim coordinate map JSON is invalid: %s"), *FullPath);
        return false;
    }
    FString Schema;
    if (!Root->TryGetStringField(TEXT("schema"), Schema) ||
        Schema != TEXT("raftsim.curved_river_coordinate_map.v1"))
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim coordinate map schema is unsupported: %s"), *Schema);
        return false;
    }
    double VerticalDatum = 0.0;
    Root->TryGetNumberField(TEXT("vertical_datum_m"), VerticalDatum);
    RiverVerticalDatumM = static_cast<float>(VerticalDatum);

    const TArray<TSharedPtr<FJsonValue>>* Points = nullptr;
    if (!Root->TryGetArrayField(TEXT("points"), Points) || Points == nullptr || Points->Num() < 2)
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim coordinate map has fewer than two points"));
        return false;
    }
    RiverCoordinatePoints.Reserve(Points->Num());
    double PreviousStationM = -TNumericLimits<double>::Max();
    for (const TSharedPtr<FJsonValue>& PointValue : *Points)
    {
        const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
        if (!PointValue.IsValid() || !PointValue->TryGetArray(Values) ||
            Values == nullptr || Values->Num() != 5)
        {
            RiverCoordinatePoints.Reset();
            return false;
        }
        FRiverCoordinatePoint Point;
        Point.StationM = (*Values)[0]->AsNumber();
        Point.LocalPositionM = FVector2D((*Values)[1]->AsNumber(), (*Values)[2]->AsNumber());
        Point.LeftNormal = FVector2D((*Values)[3]->AsNumber(), (*Values)[4]->AsNumber()).GetSafeNormal();
        if (!FMath::IsFinite(Point.StationM) ||
            !FMath::IsFinite(Point.LocalPositionM.X) ||
            !FMath::IsFinite(Point.LocalPositionM.Y) ||
            Point.StationM <= PreviousStationM || Point.LeftNormal.IsNearlyZero())
        {
            RiverCoordinatePoints.Reset();
            return false;
        }
        PreviousStationM = Point.StationM;
        RiverCoordinatePoints.Add(Point);
    }
    double WorldLengthM = 0.0;
    for (int32 PointIndex = 1; PointIndex < RiverCoordinatePoints.Num(); ++PointIndex)
    {
        const FRiverCoordinatePoint& Previous = RiverCoordinatePoints[PointIndex - 1];
        const FRiverCoordinatePoint& Current = RiverCoordinatePoints[PointIndex];
        WorldLengthM += FVector2D::Distance(
            Previous.LocalPositionM, Current.LocalPositionM);
        constexpr float CorridorHalfWidthM = 256.0f;
        const double CorridorEdgeStepM = FMath::Max(
            FVector2D::Distance(
                Previous.LocalPositionM + Previous.LeftNormal * CorridorHalfWidthM,
                Current.LocalPositionM + Current.LeftNormal * CorridorHalfWidthM),
            FVector2D::Distance(
                Previous.LocalPositionM - Previous.LeftNormal * CorridorHalfWidthM,
                Current.LocalPositionM - Current.LeftNormal * CorridorHalfWidthM));
        if (CorridorEdgeStepM > 16.0)
        {
            UE_LOG(
                LogTemp, Error,
                TEXT("RaftSim coordinate map folds its terrain corridor at point %d "
                     "with a %.3f m edge step"),
                PointIndex, CorridorEdgeStepM);
            RiverCoordinatePoints.Reset();
            return false;
        }
    }
    const double StationLengthM =
        RiverCoordinatePoints.Last().StationM - RiverCoordinatePoints[0].StationM;
    if (StationLengthM <= 0.0 ||
        FMath::Abs(WorldLengthM - StationLengthM) / StationLengthM > 0.005)
    {
        UE_LOG(
            LogTemp, Error,
            TEXT("RaftSim coordinate map world length %.3f m does not match its %.3f m station domain"),
            WorldLengthM, StationLengthM);
        RiverCoordinatePoints.Reset();
        return false;
    }
    RebuildRiverSpatialHash();
    RiverCoordinateMapPath = CoordinateMapPath;
    UE_LOG(
        LogTemp, Display,
        TEXT("RaftSim bound curved river map %s (%d points, datum %.3f m)"),
        *CoordinateMapPath, RiverCoordinatePoints.Num(), RiverVerticalDatumM);
    return true;
}

bool URaftSimWaterRuntimeAdapter::WorldToRiverCoordinates(
    const FVector& WorldPositionCm, FVector2D& OutStationLateralM,
    FVector& OutWorldTangent, FVector& OutWorldLeftNormal) const
{
    TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimWater_WorldToRiverCoordinates);
    if (!HasRiverCoordinateMap())
    {
        OutStationLateralM = FVector2D(WorldPositionCm.X / 100.0, WorldPositionCm.Y / 100.0);
        OutWorldTangent = FVector::ForwardVector;
        OutWorldLeftNormal = FVector::RightVector;
        return true;
    }
    const FVector2D PositionM(WorldPositionCm.X / 100.0, WorldPositionCm.Y / 100.0);
    double BestDistanceSquared = TNumericLimits<double>::Max();
    int32 BestSegment = INDEX_NONE;
    double BestAlpha = 0.0;
    const auto EvaluateSegment =
        [this, &PositionM, &BestDistanceSquared, &BestSegment, &BestAlpha](
            int32 SegmentIndex)
    {
        if (SegmentIndex < 0 || SegmentIndex + 1 >= RiverCoordinatePoints.Num())
        {
            return;
        }
        const FRiverCoordinatePoint& PointA = RiverCoordinatePoints[SegmentIndex];
        const FRiverCoordinatePoint& PointB = RiverCoordinatePoints[SegmentIndex + 1];
        const FVector2D Segment = PointB.LocalPositionM - PointA.LocalPositionM;
        const double LengthSquared = Segment.SquaredLength();
        if (LengthSquared <= UE_DOUBLE_SMALL_NUMBER)
        {
            return;
        }

        // RiverToWorldPosition describes a ruled corridor, not a simple
        // orthogonal projection onto the centreline: its lateral axis is the
        // normalized interpolation of the two authored endpoint normals.
        // Invert that same surface here. A bounded ternary solve is stable on
        // the dense four-metre coordinate segments and makes the forward/
        // inverse pair agree to well below gameplay centimetre precision.
        auto ReconstructionDistanceSquared =
            [&PointA, &PointB, &PositionM](double Alpha)
        {
            const FVector2D Center = FMath::Lerp(
                PointA.LocalPositionM, PointB.LocalPositionM, Alpha);
            const FVector2D Left = FMath::Lerp(
                PointA.LeftNormal, PointB.LeftNormal, Alpha).GetSafeNormal();
            const double Lateral = FVector2D::DotProduct(PositionM - Center, Left);
            return (PositionM - (Center + Left * Lateral)).SquaredLength();
        };
        double LowerAlpha = 0.0;
        double UpperAlpha = 1.0;
        for (int32 Iteration = 0; Iteration < 24; ++Iteration)
        {
            const double Third = (UpperAlpha - LowerAlpha) / 3.0;
            const double LeftAlpha = LowerAlpha + Third;
            const double RightAlpha = UpperAlpha - Third;
            if (ReconstructionDistanceSquared(LeftAlpha) <=
                ReconstructionDistanceSquared(RightAlpha))
            {
                UpperAlpha = RightAlpha;
            }
            else
            {
                LowerAlpha = LeftAlpha;
            }
        }
        const double Alpha = 0.5 * (LowerAlpha + UpperAlpha);
        const double DistanceSquared = ReconstructionDistanceSquared(Alpha);
        if (DistanceSquared < BestDistanceSquared)
        {
            BestDistanceSquared = DistanceSquared;
            BestSegment = SegmentIndex;
            BestAlpha = Alpha;
        }
    };

    // The 12 D1-D4 tube samples and the center wetness probe form one
    // continuous, sub-five-metre query chain. Their correct coordinate-map
    // segments are therefore adjacent to the previous exact solution. This
    // keeps the same 24-iteration ruled-surface inverse while eliminating the
    // repeated 7x7-cell candidate-set construction that dominated raft ticks.
    constexpr double NearbyQueryDistanceM = 8.0;
    constexpr int32 NearbySegmentRadius = 4;
    const bool bCanUseNearbySeed =
        bHasLastWorldToRiverQuery &&
        LastWorldToRiverSegment != INDEX_NONE &&
        FVector2D::DistSquared(PositionM, LastWorldToRiverPositionM) <=
            FMath::Square(NearbyQueryDistanceM);
    if (bCanUseNearbySeed)
    {
        for (int32 Offset = -NearbySegmentRadius; Offset <= NearbySegmentRadius; ++Offset)
        {
            EvaluateSegment(LastWorldToRiverSegment + Offset);
        }
    }
    else
    {
        const FIntPoint CenterKey = RiverSpatialHashKey(PositionM);
        TSet<int32> CandidateSegments;
        constexpr int32 QueryRadiusCells = 3;
        for (int32 Y = -QueryRadiusCells; Y <= QueryRadiusCells; ++Y)
        {
            for (int32 X = -QueryRadiusCells; X <= QueryRadiusCells; ++X)
            {
                if (const TArray<int32>* Indices =
                        RiverSpatialHash.Find(CenterKey + FIntPoint(X, Y)))
                {
                    for (int32 PointIndex : *Indices)
                    {
                        if (PointIndex > 0)
                        {
                            CandidateSegments.Add(PointIndex - 1);
                        }
                        if (PointIndex + 1 < RiverCoordinatePoints.Num())
                        {
                            CandidateSegments.Add(PointIndex);
                        }
                    }
                }
            }
        }
        for (int32 SegmentIndex : CandidateSegments)
        {
            EvaluateSegment(SegmentIndex);
        }
    }
    if (BestSegment == INDEX_NONE)
    {
        return false;
    }
    const FRiverCoordinatePoint& A = RiverCoordinatePoints[BestSegment];
    const FRiverCoordinatePoint& B = RiverCoordinatePoints[BestSegment + 1];
    const FVector2D Center = FMath::Lerp(A.LocalPositionM, B.LocalPositionM, BestAlpha);
    const FVector2D Left2D = FMath::Lerp(
        A.LeftNormal, B.LeftNormal, BestAlpha).GetSafeNormal();
    const FVector2D Tangent2D(Left2D.Y, -Left2D.X);
    OutStationLateralM.X = FMath::Lerp(A.StationM, B.StationM, BestAlpha);
    OutStationLateralM.Y = FVector2D::DotProduct(PositionM - Center, Left2D);
    OutWorldTangent = FVector(Tangent2D.X, Tangent2D.Y, 0.0);
    OutWorldLeftNormal = FVector(Left2D.X, Left2D.Y, 0.0);
    LastWorldToRiverSegment = BestSegment;
    LastWorldToRiverPositionM = PositionM;
    bHasLastWorldToRiverQuery = true;
    return true;
}

bool URaftSimWaterRuntimeAdapter::ResolveRiverBasis(
    FVector2D StationLateralM, float ElevationM,
    FVector& OutWorldPositionCm, FVector& OutWorldTangent,
    FVector& OutWorldLeftNormal) const
{
    if (!HasRiverCoordinateMap())
    {
        OutWorldPositionCm = FVector(
            StationLateralM.X * 100.0, StationLateralM.Y * 100.0,
            (ElevationM - RiverVerticalDatumM) * 100.0);
        OutWorldTangent = FVector::ForwardVector;
        OutWorldLeftNormal = FVector::RightVector;
        return true;
    }
    if (StationLateralM.X < RiverCoordinatePoints[0].StationM ||
        StationLateralM.X > RiverCoordinatePoints.Last().StationM)
    {
        return false;
    }
    int32 Low = 0;
    int32 High = RiverCoordinatePoints.Num() - 1;
    while (Low + 1 < High)
    {
        const int32 Mid = Low + (High - Low) / 2;
        if (RiverCoordinatePoints[Mid].StationM <= StationLateralM.X)
        {
            Low = Mid;
        }
        else
        {
            High = Mid;
        }
    }
    const FRiverCoordinatePoint& A = RiverCoordinatePoints[Low];
    const FRiverCoordinatePoint& B = RiverCoordinatePoints[High];
    const double Alpha = FMath::Clamp(
        (StationLateralM.X - A.StationM) / FMath::Max(B.StationM - A.StationM, 1.0e-9),
        0.0, 1.0);
    const FVector2D Center = FMath::Lerp(A.LocalPositionM, B.LocalPositionM, Alpha);
    const FVector2D LeftNormal = FMath::Lerp(
        A.LeftNormal, B.LeftNormal, Alpha).GetSafeNormal();
    const FVector2D Tangent(LeftNormal.Y, -LeftNormal.X);
    const FVector2D WorldXYM = Center + LeftNormal * StationLateralM.Y;
    OutWorldPositionCm = FVector(
        WorldXYM.X * 100.0, WorldXYM.Y * 100.0,
        (ElevationM - RiverVerticalDatumM) * 100.0);
    OutWorldTangent = FVector(Tangent.X, Tangent.Y, 0.0);
    OutWorldLeftNormal = FVector(LeftNormal.X, LeftNormal.Y, 0.0);
    return true;
}

bool URaftSimWaterRuntimeAdapter::RiverToWorldPosition(
    FVector2D StationLateralM, float ElevationM, FVector& OutWorldPositionCm) const
{
    FVector WorldTangent;
    FVector WorldLeftNormal;
    return ResolveRiverBasis(
        StationLateralM, ElevationM, OutWorldPositionCm,
        WorldTangent, WorldLeftNormal);
}

bool URaftSimWaterRuntimeAdapter::GetRiverStationRangeM(
    float& OutMinimumStationM, float& OutMaximumStationM) const
{
    if (!HasRiverCoordinateMap())
    {
        OutMinimumStationM = 0.0f;
        OutMaximumStationM = 0.0f;
        return false;
    }
    OutMinimumStationM = static_cast<float>(RiverCoordinatePoints[0].StationM);
    OutMaximumStationM = static_cast<float>(RiverCoordinatePoints.Last().StationM);
    return true;
}

FString URaftSimWaterRuntimeAdapter::BuildDeterministicFrameHash() const
{
    const FString Payload = FString::Printf(
        TEXT("%s|%s|%s|%d|%d|%.9f|%.9f"),
        *Config.RuntimeName,
        *Config.ScenarioPackagePath,
        *ReportManifestState.LockHash,
        Config.DeterministicSeed,
        CommittedWaterFrame,
        Config.FixedStepSeconds,
        SimTimeSeconds
    );
    return FString::Printf(TEXT("%08x"), FCrc::StrCrc32(*Payload));
}

void URaftSimWaterRuntimeAdapter::AppendDeterministicCaptureFrame()
{
    if (!CaptureState.bEnabled || Config.DeterministicCapturePath.IsEmpty())
    {
        return;
    }

    CaptureState.LastFrameHash = BuildDeterministicFrameHash();
    ++CaptureState.CapturedFrameCount;

    const FString CaptureLine = FString::Printf(
        TEXT("{\"frame\":%d,\"time_seconds\":%.9f,\"runtime\":\"%s\",\"report_lock_hash\":\"%s\",\"frame_hash\":\"%s\"}\n"),
        CommittedWaterFrame,
        SimTimeSeconds,
        *Config.RuntimeName,
        *ReportManifestState.LockHash,
        *CaptureState.LastFrameHash
    );
    const FString FullPath = ResolveRuntimeDataPath(Config.DeterministicCapturePath);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(FullPath), true);
    FFileHelper::SaveStringToFile(CaptureLine, *FullPath, FFileHelper::EEncodingOptions::AutoDetect, &IFileManager::Get(), FILEWRITE_Append);
}

FString URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(const FString& Path)
{
    if (FPaths::IsRelative(Path))
    {
#if WITH_EDITOR
        // Editor automation and PIE must validate the authoritative source
        // data. A prior packaged build may leave an older RuntimeData copy in
        // Binaries/Mac; preferring it makes local tests silently exercise
        // stale hydraulics and manifests. Shipping builds take the packaged
        // branches below because the repository is not present there.
        const FString EditorRepoRelative = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(FPaths::ProjectDir(), TEXT(".."), Path));
        if (FPaths::FileExists(EditorRepoRelative) || FPaths::DirectoryExists(EditorRepoRelative)
            || Path.StartsWith(TEXT("physics/")))
        {
            return EditorRepoRelative;
        }
#endif
        // A self-contained macOS app keeps the project payload under
        // Contents/UE/<Project>/Binaries/Mac while the Mach-O executable is
        // under Contents/MacOS. Windows keeps these locations closer, but the
        // project-binaries candidate is portable across both layouts.
        const FString PackagedProjectBinaries = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(
                FPaths::ProjectDir(), TEXT("Binaries"),
                FPlatformProcess::GetBinariesSubdirectory(),
                TEXT("RaftSimRuntimeData"), Path));
        if (FPaths::FileExists(PackagedProjectBinaries) ||
            FPaths::DirectoryExists(PackagedProjectBinaries))
        {
            return PackagedProjectBinaries;
        }
        const FString PackagedRelative = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(FPlatformProcess::BaseDir(), TEXT("RaftSimRuntimeData"), Path));
        if (FPaths::FileExists(PackagedRelative) || FPaths::DirectoryExists(PackagedRelative))
        {
            return PackagedRelative;
        }
        const FString RepoRelative = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(FPaths::ProjectDir(), TEXT(".."), Path)
        );
        if (FPaths::FileExists(RepoRelative) || FPaths::DirectoryExists(RepoRelative)
            || Path.StartsWith(TEXT("physics/")))
        {
            return RepoRelative;
        }
        return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), Path));
    }
    return Path;
}

bool URaftSimWaterRuntimeAdapter::ConfigureDevTankWindow(
    FVector2D WorldOriginM, float SizeXM, float SizeYM, float CellSizeM,
    float SurfaceHeightM, float DepthM)
{
#if RAFTSIM_HAS_LIVE_SOLVER
    LiveWindow = FRaftSimLiveWaterWindow::CreateFlatTank(
        WorldOriginM, SizeXM, SizeYM, CellSizeM, SurfaceHeightM, DepthM);
    LastHandoffTransferredCellCount = 0;
    bLastHandoffPreservedState = false;
    // Recover from Uninitialized or a prior failed river attempt (Faulted).
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized
        || Status == ERaftSimWaterRuntimeStatus::Faulted)
    {
        Status = ERaftSimWaterRuntimeStatus::ScenarioBound;
    }
    return LiveWindow.IsValid();
#else
    return false;
#endif
}

bool URaftSimWaterRuntimeAdapter::ConfigureRiverWindow(
    const FString& CookedFieldsManifestDir, const FString& BandId,
    FVector2D WindowCenterM, FVector2D WindowExtentM, float RoughnessManning,
    bool bRecenterHydraulicCrux)
{
#if RAFTSIM_HAS_LIVE_SOLVER
    FString Error;
    LiveWindow = FRaftSimLiveWaterWindow::CreateFromCookedFields(
        ResolveRuntimeDataPath(CookedFieldsManifestDir), BandId,
        WindowCenterM, WindowExtentM, RoughnessManning, Error,
        bRecenterHydraulicCrux);
    LastHandoffTransferredCellCount = 0;
    bLastHandoffPreservedState = false;
    if (!LiveWindow.IsValid())
    {
        UE_LOG(
            LogTemp, Error,
            TEXT("RaftSim river window '%s' failed to load from %s: %s"),
            *BandId, *CookedFieldsManifestDir, *Error);
        Status = ERaftSimWaterRuntimeStatus::Faulted;
        return false;
    }
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized
        || Status == ERaftSimWaterRuntimeStatus::Faulted)
    {
        Status = ERaftSimWaterRuntimeStatus::ScenarioBound;
    }
    return true;
#else
    return false;
#endif
}

bool URaftSimWaterRuntimeAdapter::ConfigureMovingRiverWindow(
    const FString& CookedFieldsManifestDir, const FString& BandId,
    FVector2D WindowCenterM, FVector2D WindowExtentM, float RoughnessManning)
{
#if RAFTSIM_HAS_LIVE_SOLVER
    FString Error;
    TUniquePtr<FRaftSimLiveWaterWindow> Candidate =
        FRaftSimLiveWaterWindow::CreateFromCookedFields(
            ResolveRuntimeDataPath(CookedFieldsManifestDir), BandId,
            WindowCenterM, WindowExtentM, RoughnessManning, Error,
            /*bRecenterHydraulicCrux=*/false);
    if (!Candidate.IsValid())
    {
        UE_LOG(
            LogTemp, Error,
            TEXT("RaftSim moving river window '%s' failed to load from %s: %s"),
            *BandId, *CookedFieldsManifestDir, *Error);
        Status = ERaftSimWaterRuntimeStatus::Faulted;
        return false;
    }

    LastHandoffTransferredCellCount = 0;
    bLastHandoffPreservedState = false;
    if (LiveWindow.IsValid())
    {
        LastHandoffTransferredCellCount = Candidate->TransferOverlapStateFrom(*LiveWindow);
        if (LastHandoffTransferredCellCount <= 0)
        {
            UE_LOG(
                LogTemp, Error,
                TEXT("RaftSim rejected non-overlapping moving-window handoff for '%s'"),
                *BandId);
            return false;
        }
        ++MovingWindowHandoffCount;
        bLastHandoffPreservedState = true;
    }
    LiveWindow = MoveTemp(Candidate);
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized ||
        Status == ERaftSimWaterRuntimeStatus::Faulted)
    {
        Status = ERaftSimWaterRuntimeStatus::ScenarioBound;
    }
    return true;
#else
    return false;
#endif
}

bool URaftSimWaterRuntimeAdapter::GetLiveWindowStats(FRaftSimWaterLiveWindowStats& OutStats) const
{
    OutStats = FRaftSimWaterLiveWindowStats();
#if RAFTSIM_HAS_LIVE_SOLVER
    if (LiveWindow.IsValid())
    {
        OutStats.TotalWaterVolumeM3 = static_cast<float>(LiveWindow->TotalWaterVolumeM3());
        OutStats.WetFraction = static_cast<float>(LiveWindow->WetCellFraction());
        OutStats.SeedWetFraction = static_cast<float>(LiveWindow->SeedWetFraction());
        OutStats.bHasNonFinite = LiveWindow->HasNonFiniteState();
        OutStats.SimTimeSeconds = static_cast<float>(LiveWindow->SimTimeSeconds());
        OutStats.LastSolverStepMilliseconds =
            static_cast<float>(LastSolverStepMillisecondsValue);
        OutStats.AverageSolverStepMilliseconds = TimedSolverStepCount > 0
            ? static_cast<float>(TotalSolverStepMilliseconds / TimedSolverStepCount)
            : 0.0f;
        OutStats.MaxSolverStepMilliseconds = static_cast<float>(MaxSolverStepMilliseconds);
        OutStats.LastHandoffTransferredCellCount = LastHandoffTransferredCellCount;
        OutStats.MovingWindowHandoffCount = MovingWindowHandoffCount;
        OutStats.bLastHandoffPreservedState = bLastHandoffPreservedState;
        return true;
    }
#endif
    return false;
}

bool URaftSimWaterRuntimeAdapter::HasLiveWindow() const
{
#if RAFTSIM_HAS_LIVE_SOLVER
    return LiveWindow.IsValid();
#else
    return false;
#endif
}
