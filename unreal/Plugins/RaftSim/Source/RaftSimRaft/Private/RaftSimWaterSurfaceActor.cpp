#include "RaftSimWaterSurfaceActor.h"
#include <tuple>
#include "RaftSimRunCoordinateProvider.h"
#include "RaftSimCartesianHydraulicRelief.h"
#include "RaftSimBreakingTileAudit.h"
#include "RaftSimWetEdgeAudit.h"
#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimTerrainProbeSources.h"
#include "RaftSimCapturedGroundRendering.h"
#include "Engine/Level.h"
#include "RaftSimShorelineMeshComponent.h"
#include "RaftSimWaterShoreline.h"
#include "RaftSimWaterSourcePacking.h"
#include "RaftSimWaterInterpolation.h"
#include "RaftSimSourcePackingAudit.h"
#include "RaftSimWaterSmoothing.h"
#include "RaftSimWaterFlowFrame.h"
#include "RaftSimIndexedBreakingProfile.h"
#include "RaftSimFineCrestIndexAudit.h"
#include "RaftSimInlineCrestAudit.h"
#include "RaftSimBreakingHeightRange.h"
#include "RaftSimPreparedBreakingHeightRange.h"
#include "RaftSimWaterFlowHistory.h"
#include "RaftSimRefreshBaselineSample.h"
#include "RaftSimWaterCarrierMeshComponent.h"
#include "RaftSimWaterTextureHistory.h"
#include "RaftSimFoamTransportFrame.h"
#include "RaftSimFoamEvolution.h"
#include "RaftSimFoamAdvection.h"
#include "RaftSimFoamFlowPairAudit.h"
#include "RaftSimPlayableCrestMesh.h"
#include "RaftSimCarrierShapeAudit.h"
#include "Async/ParallelFor.h"
#include "ProfilingDebugging/CsvProfiler.h"

#include "CollisionQueryParams.h"
#include "Engine/GameInstance.h"
#include "Engine/HitResult.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "RenderingThread.h"
#include "RHICommandList.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "RaftSimStatefulDetailComponent.h"
#include "Materials/MaterialInterface.h"
#include "Dom/JsonObject.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Misc/FileHelper.h"
#include "ProceduralMeshComponent.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/UObjectGlobals.h"

CSV_DEFINE_CATEGORY(RaftSimSurface,true);

namespace
{
// Opt-in actual-game stage timings. No solver/presentation settings change.
// Buffer timings and emit one line so individual stages exclude log I/O.
class FWaterSurfacePerf
{
public:
    explicit FWaterSurfacePerf(const TCHAR* InScope) : Scope(InScope)
    {
        static const bool Enabled = FParse::Param(FCommandLine::Get(), TEXT("RaftSimWaterStageTimings"));
        bEnabled = Enabled;
        if (bEnabled) Start = Last = FPlatformTime::Seconds();
    }
    void Mark(const TCHAR* Name)
    {
        if (!bEnabled) return;
        const double Now = FPlatformTime::Seconds();
        Stages.Emplace(Name, (Now - Last)*1000.);
        Last = Now;
    }
    ~FWaterSurfacePerf()
    {
        if (!bEnabled) return;
        const double Total = (FPlatformTime::Seconds() - Start)*1000.;
        FString Line = FString::Printf(TEXT("WaterPerf scope=%s frame=%llu total_ms=%.4f"),
            Scope, static_cast<unsigned long long>(GFrameCounter), Total);
        for (const auto& Stage : Stages) Line.Appendf(TEXT(" %s_ms=%.4f"), Stage.Key, Stage.Value);
        UE_LOG(LogTemp, Display, TEXT("%s"), *Line);
    }
private:
    const TCHAR* Scope;
    bool bEnabled = false;
    double Start = 0., Last = 0.;
    TArray<TPair<const TCHAR*, double>, TInlineAllocator<16>> Stages;
};
}

static TAutoConsoleVariable<int32> CVarRaftSimForceBoatWakeTest(
    TEXT("raftsim.ForceBoatWakeTest"), 0,
    TEXT("1 = force the geometry-only paddle wake on and use ground-relative ")
    TEXT("boat motion, for headless wake-rendering verification."));

static TAutoConsoleVariable<int32> CVarRaftSimLiveSheetDebugCoverage(
    TEXT("raftsim.LiveSheetDebugCoverage"), 0,
    TEXT("1 = force the live overlay sheet fully opaque to reveal its ")
    TEXT("actual rendered extent and vertex foam."));

static TAutoConsoleVariable<int32> CVarRaftSimHideLiveOverlay(
    TEXT("raftsim.HideLiveOverlay"), 0,
    TEXT("1 = hide the live overlay surface mesh entirely (A/B test for ")
    TEXT("near-field wash)."));

static TAutoConsoleVariable<int32> CVarRaftSimPaddleWakeRippleOverlay(
    TEXT("raftsim.PaddleWakeRippleOverlay"), 0,
    TEXT("1 = build the legacy paddle-wake ripple overlay section. Default ")
    TEXT("off: the overlay was silently dead for weeks (its in-place update ")
    TEXT("always failed a vertex-count mismatch) and rendered as unreviewed ")
    TEXT("black shapes once section handling was hardened; the visible wake ")
    TEXT("is the carrier's own vertex displacement."));

static TAutoConsoleVariable<int32> CVarRaftSimFreezeCoreTopology(
    TEXT("raftsim.FreezeCoreTopology"), 0,
    TEXT("1 = keep rendering the volume core's last-built index list instead ")
    TEXT("of recreating the section on membership changes (A/B probe for ")
    TEXT("recreation-driven temporal-history pops)."));

static TAutoConsoleVariable<float> CVarRaftSimPresentationStandingWaveScale(
    TEXT("raftsim.PresentationStandingWaveScale"), -1.0f,
    TEXT("Review override for the presentation standing-wave scale (-1 = use the river config)."));

static TAutoConsoleVariable<int32> CVarRaftSimSouthForkOpticalSmoothingPasses(
    TEXT("raftsim.SouthForkOpticalSmoothingPasses"), 16,
    TEXT("South Fork review: 1-16 optical smoothing passes. Hydraulic detection retains four passes; other rivers are unchanged."));

static TAutoConsoleVariable<int32> CVarRaftSimChilkoSharedBreakingRelief(
    TEXT("raftsim.ChilkoSharedBreakingRelief"), 1,
    TEXT("Chilko-only rollout: share persistent breaking crest geometry with raft support. 0 restores the raw-detection baseline for comparison."));

static TAutoConsoleVariable<int32> CVarRaftSimChilkoCrestFoam(
    TEXT("raftsim.ChilkoCrestFoam"), 1,
    TEXT("Chilko single-surface foam is generated at positive relief and persistent breaking crests, then transported. 0 restores raw jump/trough sources for comparison."));

static TAutoConsoleVariable<int32> CVarRaftSimChilkoHydraulicCrestScale(
    TEXT("raftsim.ChilkoHydraulicCrestScale"), 1,
    TEXT("Reconstruct unresolved Chilko crest height and face length from local depth and Froude. 0 uses the fixed 22 cm times intensity profile."));

static TAutoConsoleVariable<int32> CVarRaftSimFlatWaterNormals(
    TEXT("raftsim.FlatWaterNormals"), 0,
    TEXT("Review bisect: 1 replaces the live water vertex normals with straight up."));

static TAutoConsoleVariable<int32> CVarRaftSimLogLatticeEdgeRows(
    TEXT("raftsim.LogLatticeEdgeRows"), 0,
    TEXT("Log wet extents and coverage of the lattice rows at a corridor end (review probe)."));

static TAutoConsoleVariable<float> CVarRaftSimShorelineProbeStation(
    TEXT("raftsim.ShorelineProbeStation"), -1.0f,
    TEXT("One-shot South Fork shoreline geometry/terrain diagnostic at this station after eight seconds. -1 disables; never use during performance measurement."));

static TAutoConsoleVariable<int32> CVarRaftSimLogWaterRenderStateEvents(
    TEXT("raftsim.LogWaterRenderStateEvents"), 0,
    TEXT("1 = log every water render-state invalidation (section recreation, ")
    TEXT("section-visibility flip, grid recentre) with frame and time, for ")
    TEXT("correlating whole-surface TSR/temporal pops against a frame dump."));

namespace
{
void LogWaterRenderStateEvent(const UWorld* World, const TCHAR* Event)
{
    if (CVarRaftSimLogWaterRenderStateEvents.GetValueOnGameThread() == 0)
    {
        return;
    }
    UE_LOG(
        LogTemp, Display,
        TEXT("RaftSim water render-state event: %s frame=%llu world_s=%.3f"),
        Event,
        static_cast<unsigned long long>(GFrameCounter),
        World ? World->GetTimeSeconds() : -1.0f);
}
} // namespace

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
// Rivers that retain an authored Single Layer Water body must not show a
// second calm-water skin. Reveal the live geometry only where solver foam or
// obstruction activity drives the material, and let those breaking crests
// reach full coverage instead of reading as a translucent raised water level.
constexpr float kAuthoredCarrierCalmDetailCoverage = 0.0f;
constexpr float kAuthoredCarrierActiveDetailCoverage = 1.0f;

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

FVector2D ARaftSimWaterSurfaceActor::AdvanceFoamTextureAdvectionMeters(
    const FVector2D& CurrentDisplacementMeters,
    const FVector2D& WaterVelocityMetersPerSecond,
    float DeltaSeconds)
{
    return CurrentDisplacementMeters +
        WaterVelocityMetersPerSecond * FMath::Max(DeltaSeconds, 0.0f);
}

float ARaftSimWaterSurfaceActor::SmoothRapidFoamCoverage(
    float PreviousCoverage,
    float TargetCoverage,
    float DeltaSeconds)
{
    const float Previous = FMath::Clamp(PreviousCoverage, 0.0f, 1.0f);
    const float Target = FMath::Clamp(TargetCoverage, 0.0f, 1.0f);
    const float ResponsePerSecond = Target > Previous ? 8.0f : 0.8f;
    const float Blend = 1.0f - FMath::Exp(
        -ResponsePerSecond * FMath::Max(DeltaSeconds, 0.0f));
    return FMath::Lerp(Previous, Target, FMath::Clamp(Blend, 0.0f, 1.0f));
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

float ARaftSimWaterSurfaceActor::
    ComputePresentationShoreDisplacementWeight(
        int32 LateralIndex,
        int32 MinimumWetLateralIndex,
        int32 MaximumWetLateralIndex,
        float InVertexSpacingMeters)
{
    if (MinimumWetLateralIndex < 0 ||
        MaximumWetLateralIndex < MinimumWetLateralIndex ||
        LateralIndex < MinimumWetLateralIndex ||
        LateralIndex > MaximumWetLateralIndex ||
        InVertexSpacingMeters <= 0.0f)
    {
        return 0.0f;
    }

    const int32 EdgeSteps = FMath::Min(
        LateralIndex - MinimumWetLateralIndex,
        MaximumWetLateralIndex - LateralIndex);
    const float EdgeDistanceMeters =
        EdgeSteps * InVertexSpacingMeters;
    // Pin the actual waterline, heavily damp its first interior neighbour,
    // and recover full rapid relief by the third row. The previous direct
    // application of up-to-78 cm local-fluid crests to a shallow boundary
    // row produced isolated green wedges over the bank (Troublemaker,
    // player screenshot 2026-09-04).
    return FMath::SmoothStep(
        0.5f * InVertexSpacingMeters,
        2.5f * InVertexSpacingMeters,
        EdgeDistanceMeters);
}

bool ARaftSimWaterSurfaceActor::IsBoulderFootprintHydraulicallyExposed(
    float BoulderLateralMeters,
    float BoulderRadiusMeters,
    float MinimumWetLateralMeters,
    float MaximumWetLateralMeters,
    float InVertexSpacingMeters)
{
    if (!FMath::IsFinite(BoulderLateralMeters) ||
        !FMath::IsFinite(BoulderRadiusMeters) ||
        !FMath::IsFinite(MinimumWetLateralMeters) ||
        !FMath::IsFinite(MaximumWetLateralMeters) ||
        MinimumWetLateralMeters > MaximumWetLateralMeters ||
        BoulderRadiusMeters <= 0.0f || InVertexSpacingMeters <= 0.0f)
    {
        return false;
    }

    // A footprint on the wet/dry sample itself is commonly a scenic bank
    // stone whose fitted mesh is entirely on land. Give every hydraulic
    // obstruction at least half a render cell of water around its centre,
    // increased modestly for large rocks. Partly submerged, visible catalog
    // boulders still qualify; shoreline dressing does not synthesize a ghost
    // pillow or wake.
    const float RequiredWaterMarginMeters = FMath::Max(
        0.5f * InVertexSpacingMeters,
        0.35f * BoulderRadiusMeters);
    return BoulderLateralMeters >=
            MinimumWetLateralMeters + RequiredWaterMarginMeters &&
        BoulderLateralMeters <=
            MaximumWetLateralMeters - RequiredWaterMarginMeters;
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

    SurfaceMesh = CreateDefaultSubobject<URaftSimWaterCarrierMeshComponent>(TEXT("SurfaceMesh"));
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
    CartesianShorelineMesh = CreateDefaultSubobject<URaftSimShorelineMeshComponent>(TEXT("CartesianShorelineMesh"));
    CartesianShorelineMesh->SetupAttachment(SurfaceMesh);
    CartesianShorelineMesh->SetVisibility(false);

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

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> PaddleWakeMat(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleWakeRipple."
             "M_RaftSim_PaddleWakeRipple"));
    if (PaddleWakeMat.Succeeded())
    {
        PaddleWakeMaterial = PaddleWakeMat.Object;
    }

    // This project-owned parent is the shared photoreal Single Layer Water
    // graph with the runtime raft-floor transmission aperture already wired.
    // V4 is the parent the editor water-presentation command authors today
    // and the one MI_RaftSim_SouthForkProductionWater derives from, so the
    // live carrier renders the same current pixel graph as the authored
    // water instead of a stale sibling. All river-specific optical values
    // are supplied by the dynamic instance.
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> VolumeCoreMat(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
             "M_RaftSim_SouthForkRaftTransmissionWaterV4."
             "M_RaftSim_SouthForkRaftTransmissionWaterV4"));
    if (VolumeCoreMat.Succeeded())
    {
        LiveVolumeCoreMaterial = VolumeCoreMat.Object;
    }
    else
    {
        // A checkout that has not run the editor water rebuild holds only the
        // committed V2 parent. It exposes the same parameter contract (WPO
        // gates, turbulence, foam/ripple scalars) over an older pixel graph;
        // never leave the carrier without a Single Layer Water parent.
        static ConstructorHelpers::FObjectFinder<UMaterialInterface>
            FallbackVolumeCoreMat(
                TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/"
                     "Materials/M_RaftSim_SouthForkRaftTransmissionWaterV2."
                     "M_RaftSim_SouthForkRaftTransmissionWaterV2"));
        if (FallbackVolumeCoreMat.Succeeded())
        {
            LiveVolumeCoreMaterial = FallbackVolumeCoreMat.Object;
        }
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

float ARaftSimWaterSurfaceActor::ComputePaddleWakeDisplacementMeters(
    const FVector2D& RiverCoordinatesMeters,
    const FVector2D& BoatRiverCoordinatesMeters,
    const FVector2D& BoatTravelDirection,
    float Strength,
    float PhaseSeconds)
{
    const FVector2D TravelDirection = BoatTravelDirection.GetSafeNormal();
    const float SafeStrength = FMath::Clamp(Strength, 0.0f, 1.0f);
    if (TravelDirection.IsNearlyZero() || SafeStrength <= KINDA_SMALL_NUMBER)
    {
        return 0.0f;
    }

    const FVector2D WakeDirection = -TravelDirection;
    const FVector2D WakeAcross(-WakeDirection.Y, WakeDirection.X);
    const FVector2D RelativePosition =
        RiverCoordinatesMeters - BoatRiverCoordinatesMeters;
    const float AlongMeters =
        FVector2D::DotProduct(RelativePosition, WakeDirection);
    constexpr float WakeStartMeters = 1.0f;
    constexpr float WakeLengthMeters = 22.0f;
    if (AlongMeters <= WakeStartMeters || AlongMeters >= WakeLengthMeters)
    {
        return 0.0f;
    }

    // Kelvin-like arms open from the two tube edges. A signed sinusoid across
    // each arm creates alternating mesh crests and troughs instead of a
    // positive relief strip, foam decal, or normal-map train. The wavelength
    // remains above the 1.5 m production presentation-grid Nyquist limit.
    const float AcrossMeters =
        FVector2D::DotProduct(RelativePosition, WakeAcross);
    const float ArmCenterMeters = 1.05f + AlongMeters * 0.52f;
    const float ArmDistanceMeters =
        FMath::Abs(AcrossMeters) - ArmCenterMeters;
    constexpr float ArmEnvelopeMeters = 1.00f;
    const float ArmEnvelope = FMath::Exp(
        -0.5f * FMath::Square(ArmDistanceMeters / ArmEnvelopeMeters));
    const float StartEnvelope = FMath::SmoothStep(
        WakeStartMeters, WakeStartMeters + 2.0f, AlongMeters);
    const float EndEnvelope = 1.0f - FMath::SmoothStep(
        WakeLengthMeters - 5.0f, WakeLengthMeters, AlongMeters);
    constexpr float WakeWavelengthMeters = 5.4f;
    const float WavePhase =
        ArmDistanceMeters * (2.0f * UE_PI / WakeWavelengthMeters) +
        AlongMeters * 0.15f - PhaseSeconds * 1.35f;
    // Eleven centimetres: six read from the chase camera but disappeared
    // entirely at the first-person stern's grazing angle against bright
    // water ("there is no wake behind the boat as the crew paddles", player
    // screenshot 2026-08-31). Still a signed water ripple, not the raised
    // white ribbons this replaced; the trail also runs 22 m so the arms
    // survive into the mid-distance where the eye expects them.
    constexpr float MaximumAmplitudeMeters = 0.110f;
    return MaximumAmplitudeMeters * SafeStrength * StartEnvelope *
        EndEnvelope * ArmEnvelope * FMath::Sin(WavePhase);
}

FVector2D ARaftSimWaterSurfaceActor::ComputeBoulderWakePresentation(
    float DownstreamMeters,
    float AcrossMeters,
    float BoulderRadiusMeters,
    float WaterSpeedMetersPerSecond,
    float PhaseSeconds)
{
    return URaftSimWaterRuntimeAdapter::ComputeCoupledBoulderWakePresentation(
        DownstreamMeters,
        AcrossMeters,
        BoulderRadiusMeters,
        WaterSpeedMetersPerSecond,
        PhaseSeconds);
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

bool ARaftSimWaterSurfaceActor::TraceTerrainSurface(UWorld* World,
    const FVector& Start, const FVector& End, const FCollisionQueryParams& Params,
    int32& RemainingRayBudget, FHitResult& OutHit)
{
    OutHit = FHitResult();
    if (!World) return false;
    FCollisionQueryParams TerrainParams(Params);
    for (int32 Attempt = 0; Attempt < 4 && RemainingRayBudget > 0; ++Attempt)
    {
        --RemainingRayBudget;
        FHitResult Hit;
        if (!World->LineTraceSingleByChannel(Hit, Start, End,
                ECC_WorldStatic, TerrainParams)) return false;
        const AActor* Actor = Hit.GetActor();
        if (!Actor) return false;
        // Reconstructed physical ground replaced the legacy full-reach tiles.
        // Water probes must recognize the same captured sources as contact.
        if (RaftSimTerrainProbeSources::IsSource(Hit.GetComponent()))
        {
            OutHit = Hit;
            return true;
        }
        // Multi-by-channel also stops at the first blocker. Explicitly skip
        // unrelated proxies, dressing and boats, then repeat the same ray.
        // A non-ground sibling component must not hide a tagged source on the
        // same actor. Keep each retry inside the original four-ray/budget bound.
        if (const UPrimitiveComponent* Component=Hit.GetComponent())
            TerrainParams.AddIgnoredComponent(Component);
        else TerrainParams.AddIgnoredActor(Actor);
    }
    return false;
}

void ARaftSimWaterSurfaceActor::InvalidateMissedTerrainProbes()
{
    // Streamed-in terrain can make a previous miss resolvable. Keep successful
    // cached measurements and let the ordinary bounded refresh retry misses.
    for (uint8& State : VisualBankProbeState)
    {
        if (State == 2) State = 0;
    }
}

void ARaftSimWaterSurfaceActor::InvalidateTerrainProbes()
{
    for (uint8& State : VisualBankProbeState) State = 0;
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
    // A connected drop profile reads as one body of water: accelerating
    // drawdown, a curling lip, the impact pocket, and a broad aerated roller.
    // Every term is a displacement of the existing carrier mesh; no second
    // sheet or translucent overlay is created.
    const float DrawdownStation = (DownstreamMeters + 2.1f) / 2.7f;
    const float DrawdownAcross = AcrossMeters / 4.2f;
    const float Drawdown = FMath::Exp(
        -(DrawdownStation * DrawdownStation +
            DrawdownAcross * DrawdownAcross));

    const float LipStation = (DownstreamMeters + 0.25f) / 0.95f;
    const float LipAcross = AcrossMeters / 4.0f;
    const float CurlingLip = FMath::Exp(
        -(LipStation * LipStation + LipAcross * LipAcross));

    const float PlungeStation = (DownstreamMeters - 1.8f) / 1.7f;
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
            (-0.075f * Drawdown +
                0.15f * CurlingLip -
                0.30f * PlungeCore +
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
            (0.70f * CurlingLip +
                0.34f * PlungeCore +
                1.00f * AeratedReturn +
                0.78f * BrokenShoulder * ShoulderVariation),
        0.0f,
        1.0f);
    return FVector2D(DisplacementMeters, FoamGeneration);
}

FVector2D ARaftSimWaterSurfaceActor::
    ComputeBreakingRollerSurfaceVelocityMetersPerSecond(
        float DownstreamMeters,
        float AcrossMeters,
        float Intensity,
        float BulkWaterSpeedMetersPerSecond)
{
    const float SafeIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
    if (SafeIntensity <= KINDA_SMALL_NUMBER ||
        DownstreamMeters <= 0.2f || DownstreamMeters >= 14.5f)
    {
        return FVector2D::ZeroVector;
    }

    // At the visible surface of a hydraulic roller, aerated water returns
    // upstream toward the impact toe, then converges into its most energetic
    // core. This is deliberately an addition to foam transport only. The
    // current, raft, and authoritative free surface remain solver-driven.
    constexpr float RollerCenterMeters = 4.4f;
    constexpr float RollerStationRadiusMeters = 4.0f;
    constexpr float RollerAcrossRadiusMeters = 4.8f;
    const float Station =
        (DownstreamMeters - RollerCenterMeters) /
        RollerStationRadiusMeters;
    const float Across = AcrossMeters / RollerAcrossRadiusMeters;
    const float Envelope = FMath::Exp(
        -0.5f * (Station * Station + Across * Across));
    const float Entry = FMath::SmoothStep(0.2f, 1.4f, DownstreamMeters);
    const float Exit = 1.0f -
        FMath::SmoothStep(10.5f, 14.5f, DownstreamMeters);
    const float Strength = SafeIntensity * Envelope * Entry * Exit;
    const float SafeBulkSpeed = FMath::Max(BulkWaterSpeedMetersPerSecond, 0.0f);
    const float UpstreamReturnSpeed =
        (0.80f + 0.75f * SafeBulkSpeed) * Strength;
    const float InwardConvergenceSpeed =
        -0.24f * SafeBulkSpeed * Across * Strength;
    return FVector2D(-UpstreamReturnSpeed, InwardConvergenceSpeed);
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
    // The current live carrier also owns reconstructed-ground arrival. It must
    // not depend on a separate legacy water-streaming actor being present.
    FWorldDelegates::LevelAddedToWorld.AddWeakLambda(this, [this](ULevel* Level,UWorld* World)
    {
        if (!Level || World!=GetWorld()) return;
        bool bGroundArrived=false;
        for (AActor* Actor:Level->Actors)
        {
            RaftSimCapturedGroundRendering::ApplyToActor(Actor);
            bGroundArrived |= RaftSimTerrainProbeSources::ActorHasSource(Actor);
        }
        if (bGroundArrived) InvalidateMissedTerrainProbes();
    });
    // The carrier can arrive through World Partition after the run manager's
    // BeginPlay. Bind here, on the consumer, and let the first ordered tick
    // build the surface after any checkpoint/section-start water transaction.
    // BeginPlay itself is not tick-ordered and must not publish the old launch.
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        RaftSimCapturedGroundRendering::ApplyToActor(*It);
        if (Cast<IRaftSimRunCoordinateProvider>(*It))
        {
            AddTickPrerequisiteActor(*It);
        }
    }
}

bool ARaftSimWaterSurfaceActor::TryInitializeRuntimeSurface()
{
    if (bRuntimeSurfaceReady) return true;
    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        if (URaftSimPhysicsBridgeSubsystem* Bridge =
                GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        {
            WaterAdapter = Bridge->GetWaterRuntime();
        }
    }

    // A placed carrier may BeginPlay before the raft configures the bridge.
    // Never cache an unconfigured adapter as a flat/straight river. Retry on
    // the first ready tick; failed authored launches leave no fake surface.
    FBox2D Bounds;
    if (!WaterAdapter || !WaterAdapter->GetLiveWaterFieldBoundsM(Bounds)) return false;
    UpdateRaftFoamExclusionParameters();
    BuildGrid();
    RefreshSurface();
    return true;
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
    bRuntimeSurfaceReady = true;
    const ARaftSimRiverWaterConfig* RiverWaterConfig = nullptr;
    if (TActorIterator<ARaftSimRiverWaterConfig> ConfigIt(GetWorld()); ConfigIt)
    {
        RiverWaterConfig = *ConfigIt;
    }
    const bool bUsesAuthoredRiverPresentation = RiverWaterConfig != nullptr;
    const bool bUsesSouthForkFullReachSingleSurface =
        RiverWaterConfig && RiverWaterConfig->CookedFieldsDir.Contains(
            TEXT("south_fork_american_chili_bar/full_hydraulics"),
            ESearchCase::IgnoreCase);
    bSouthForkOpticalSmoothingReview = bUsesSouthForkFullReachSingleSurface;
    bSpatialBreakingReview = bUsesSouthForkFullReachSingleSurface &&
        GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")) &&
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimSpatialBreakingReview"));
    // The captured candidate has one surface-lit carrier, not the legacy
    // overlay plus volume core. Keep this bounded experiment opt-in until
    // actual animation, ground contact and runtime costs have been reviewed.
    const bool bOriginalSurveyReview = RiverWaterConfig &&
        GetWorld()->GetMapName().EndsWith(TEXT("SouthForkSurveyPlayable")) &&
        (RiverWaterConfig->CookedFieldsDir == TEXT("tmp/south-fork-survey-hydraulics/1m-mixed-inlet-enclosed-rock-gaps-continuation-20260907/engine_review") ||
         RiverWaterConfig->CookedFieldsDir == TEXT("tmp/south-fork-survey-hydraulics/1m-mixed-inlet-mesh-triangles-20260907/engine_review") ||
         RiverWaterConfig->CookedFieldsDir == TEXT("tmp/south-fork-survey-hydraulics/1m-mixed-inlet-depth-limited-hydrostatic-20260907/engine_review"));
    const bool bRegisteredRockSurveyReview = RiverWaterConfig &&
        GetWorld()->GetMapName().EndsWith(TEXT("SouthForkRegisteredRockPlayable")) &&
        RiverWaterConfig->CookedFieldsDir == TEXT("tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907/engine_review");
    const bool bPlayableCapturedSouthFork = RiverWaterConfig &&
        GetWorld()->GetMapName().EndsWith(TEXT("L_SouthFork_Troublemaker")) &&
        RiverWaterConfig->CookedFieldsDir == TEXT("physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/playable_flow");
    // Promote the source-matched shared carrier/support relief only. The
    // separate particle/stateful experiments still require their review map
    // and explicit flags; they are not part of ordinary reconstructed play.
    const bool bSurveyBreakingReview = bPlayableCapturedSouthFork ||
        ((bOriginalSurveyReview || bRegisteredRockSurveyReview) &&
            FParse::Param(FCommandLine::Get(), TEXT("RaftSimSurveyBreakingReview")));
    bPlayableCrestRefinement = bPlayableCapturedSouthFork;
    const bool bStatefulDetailReview = bRegisteredRockSurveyReview && bSurveyBreakingReview &&
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimStatefulDetailReview"));
    bStatefulCrestReview=bStatefulDetailReview && FParse::Param(FCommandLine::Get(),TEXT("RaftSimStatefulCrestReview"));
    const bool bStatefulFoamReview=bStatefulDetailReview && (bStatefulCrestReview || FParse::Param(FCommandLine::Get(),TEXT("RaftSimStatefulFoamReview")));
    bStatefulMotionReview=bStatefulDetailReview && (bStatefulFoamReview || FParse::Param(FCommandLine::Get(),TEXT("RaftSimStatefulMotionReview")));
    bStatefulGPUCarrierReview=bStatefulDetailReview && (bStatefulMotionReview ||
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimStatefulGPUCarrierReview")));
    bStatefulDetailGeometryReview=bStatefulDetailReview && (bStatefulGPUCarrierReview ||
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimStatefulDetailGeometryReview")));
    DetailRefinement=FRaftSimSurfaceRefinement();
    PlayableCrestCorrections.Reset();CachedPlayableCrestSites.Reset();
    CachedPlayableCoarseCrest.Reset();CachedPlayableShore.Reset();PlayableCrestCacheHits=0;
    ReleaseMacroHistory();MacroSurfaceTexture=nullptr;PreviousMacroSurfaceTexture=nullptr;
    MacroCrestSites.Reset();MacroCrestDisplacementCm.Reset();MacroCrestShoreWeights.Reset();
    if (auto* Carrier=Cast<URaftSimWaterCarrierMeshComponent>(SurfaceMesh))
        Carrier->SetHydraulicBounds(FBox(ForceInit));
    bSpatialBreakingReview |= bSurveyBreakingReview ||
        (RiverWaterConfig && RiverWaterConfig->bEnableLiveSharedBreakingRelief);
    bLiveSurfaceCarrierEnabled =
        RiverWaterConfig &&
        (RiverWaterConfig->bLiveSolverOwnsRuntimeRendering ||
            bUsesSouthForkFullReachSingleSurface);
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
    bSharedBreakingReliefEnabled = bSpatialBreakingReview ||
        (bUsesMigratedChilkoVolumeCore &&
            CVarRaftSimChilkoSharedBreakingRelief.GetValueOnGameThread() != 0);
    const bool bUsesMigratedColoradoVolumeCore =
        RiverWaterConfig &&
        RiverWaterConfig->CookedFieldsDir.Contains(
            TEXT("colorado_river_grand_canyon_rowing"),
            ESearchCase::CaseSensitive);
    const bool bUsesPacuarePresentation = RiverWaterConfig &&
        RiverWaterConfig->CookedFieldsDir.Contains(
            TEXT("pacuare_river_costa_rica"), ESearchCase::CaseSensitive);
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
    // South Fork last-resort: the config's soft texture pointers resolve
    // null on the flagship reach (every other river has a migration
    // fallback above). Without a lace texture the raised rapid-foam mesh
    // samples a dead default and its 0.18 opacity-mask clip discards every
    // pixel — boat and obstruction wake foam computed but never visible.
    if (!ResolvedLiveWaterFlowNormalTexture)
    {
        ResolvedLiveWaterFlowNormalTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/"
                 "Textures/T_RaftSim_SouthForkWater_FlowNormal."
                 "T_RaftSim_SouthForkWater_FlowNormal"));
    }
    if (!ResolvedLiveWaterFoamLaceTexture)
    {
        ResolvedLiveWaterFoamLaceTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/"
                 "Textures/T_RaftSim_SouthForkWater_FoamLace."
                 "T_RaftSim_SouthForkWater_FoamLace"));
    }
    if (ResolvedVolumeCoreMaterialOverride)
    {
        LiveVolumeCoreMaterial = ResolvedVolumeCoreMaterialOverride;
    }
    // Isolated optical review only: retain the same carrier and all runtime
    // parameters. Never replace another river's material or save scene assets.
    const bool bSmoothDisplacementNormalReview = FParse::Param(
        FCommandLine::Get(), TEXT("RaftSimSmoothDisplacementNormalReview"));
    if (bUsesSouthForkFullReachSingleSurface &&
        (bSmoothDisplacementNormalReview ||
            FParse::Param(FCommandLine::Get(), TEXT("RaftSimDisplacementNormalReview"))))
    {
        UMaterialInterface* ReviewMaterial = LoadObject<UMaterialInterface>(nullptr,
            bSmoothDisplacementNormalReview
                ? TEXT("/Game/RaftSim/Rendering/Review/M_RaftSim_SmoothDisplacementNormalReview")
                : TEXT("/Game/RaftSim/Rendering/Review/M_RaftSim_DisplacementNormalReview"));
        if (!ReviewMaterial)
        {
            UE_LOG(LogTemp, Error, TEXT("DisplacementNormalReview material missing; review invalid"));
        }
        else
        {
            LiveVolumeCoreMaterial = ReviewMaterial;
            UE_LOG(LogTemp, Display, TEXT("DisplacementNormalReview enabled: %s"),
                *ReviewMaterial->GetPathName());
        }
    }
#if !UE_BUILD_SHIPPING
    if(GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")) &&
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")) &&
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimFrothDepartureReview")))
    {
        auto* Review=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/FrothDeparture/M_SouthForkFrothDepartureV2"));
        if(Review)
        {
            LiveVolumeCoreMaterial=Review;
            UE_LOG(LogTemp,Display,TEXT("Froth departure review: frozen paired current, existing single carrier; not physical or visual acceptance"));
        }
        else UE_LOG(LogTemp,Error,TEXT("Froth departure material unavailable; no review acceptance"));
    }
    if(GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")) &&
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")) &&
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimOpticalNormalFilterReview")))
    {
        FString Variant;
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimOpticalNormalVariant="),Variant);
        FString ReviewPath=TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/OpticalNormalFilter/M_SouthForkOpticalNormalFilter");
        if(Variant==TEXT("constant"))ReviewPath+=TEXT("_constant");
        else if(Variant==TEXT("zero-flow"))ReviewPath+=TEXT("_zero_flow");
        else if(Variant==TEXT("integer-hash"))ReviewPath+=TEXT("_integer_hash");
        else if(!Variant.IsEmpty())ReviewPath.Empty();
        auto* Review=ReviewPath.IsEmpty() ? nullptr : LoadObject<UMaterialInterface>(nullptr,*ReviewPath);
        if(Review)
        {
            LiveVolumeCoreMaterial=Review;
            UE_LOG(LogTemp,Display,TEXT("Optical normal filter review: existing South Fork carrier; not appearance acceptance"));
        }
        else UE_LOG(LogTemp,Error,TEXT("Optical normal filter review unavailable; no diagnostic acceptance"));
    }
    if(GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")) &&
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimPairedFoamFlowReview")))
    {
        auto* Review=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/PairedFoamFlow/M_SouthForkPairedFoamFlow"));
        if(Review)
        {
            LiveVolumeCoreMaterial=Review;
            UE_LOG(LogTemp,Display,TEXT("Paired foam flow material review enabled on existing South Fork carrier"));
        }
        else UE_LOG(LogTemp,Error,TEXT("Paired foam flow material unavailable; no review acceptance"));
    }
    if(GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")) &&
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimCurrentFoamCoverageAudit")))
    {
        auto* Audit=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/CurrentFoamAudit/M_CurrentSouthForkFoamAudit"));
        if(Audit)
        {
            LiveVolumeCoreMaterial=Audit;
            UE_LOG(LogTemp,Display,TEXT("Current foam coverage audit enabled: same carrier; R=final coverage G=GPU ownership B=GPU coverage; diagnostic only"));
        }
        else UE_LOG(LogTemp,Error,TEXT("Current foam coverage audit unavailable; no diagnostic acceptance"));
    }
#endif
    bLiveVolumeCoreEnabled =
        bLiveSurfaceCarrierEnabled &&
        (RiverWaterConfig->bEnableLiveSolverVolumeCore ||
            bUsesMigratedLiveVolumeCore ||
            bUsesSouthForkFullReachSingleSurface) &&
        LiveVolumeCoreMaterial != nullptr;
    // Every production river with a solver-clipped optical core now renders
    // that core as its one water surface. The former low-opacity Default Lit
    // skin duplicated normals/reflections and was especially visible while a
    // moving window crossed the shoreline.
    bSingleLiveWaterSurfaceEnabled = bLiveVolumeCoreEnabled;
    bSharedBreakingReliefEnabled &= bSingleLiveWaterSurfaceEnabled || bSurveyBreakingReview;
    UE_LOG(LogTemp, Display,
        TEXT("RaftSim water surface mode: carrier=%d volumeCore=%d "
             "singleSurface=%d coreMaterial=%s"),
        bLiveSurfaceCarrierEnabled ? 1 : 0,
        bLiveVolumeCoreEnabled ? 1 : 0,
        bSingleLiveWaterSurfaceEnabled ? 1 : 0,
        LiveVolumeCoreMaterial
            ? *LiveVolumeCoreMaterial->GetPathName()
            : TEXT("none"));
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
        if (bSingleLiveWaterSurfaceEnabled)
        {
            // South Fork uses one solver-conforming Single Layer Water
            // carrier. Foam/lips may remain separate sparse features, but a
            // translucent second water sheet must never cover the hull or
            // boulders above this surface.
            ResolvedCalmLiveSurfaceCoverage = 0.0f;
            ResolvedActiveLiveSurfaceCoverage = 0.0f;
        }
    }
    const FLinearColor ResolvedLiveShallowSurfaceColor =
        bUsesMigratedColoradoVolumeCore
            ? FLinearColor(0.070f, 0.110f, 0.080f, 1.0f)
            : bUsesLegacyChilkoPresentationDefaults
            ? FLinearColor(0.012f, 0.075f, 0.105f, 1.0f)
            : bUsesMigratedFutaleufuVolumeCore
            ? FLinearColor(0.012f, 0.085f, 0.100f, 1.0f)
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveShallowSurfaceColor
                   : FLinearColor(0.025f, 0.120f, 0.150f, 1.0f));
    const FLinearColor ResolvedLiveDeepSurfaceColor =
        bUsesMigratedColoradoVolumeCore
            ? FLinearColor(0.018f, 0.038f, 0.028f, 1.0f)
            : bUsesLegacyChilkoPresentationDefaults
            ? FLinearColor(0.002f, 0.018f, 0.032f, 1.0f)
            : bUsesMigratedFutaleufuVolumeCore
            ? FLinearColor(0.003f, 0.035f, 0.046f, 1.0f)
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveDeepSurfaceColor
                   : FLinearColor(0.004f, 0.028f, 0.045f, 1.0f));
    const FLinearColor ResolvedLiveReflectedSkyColor =
        bUsesMigratedColoradoVolumeCore
            ? FLinearColor(0.12f, 0.17f, 0.18f, 1.0f)
            : bUsesLegacyChilkoPresentationDefaults
            ? FLinearColor(0.045f, 0.090f, 0.135f, 1.0f)
            : bUsesMigratedFutaleufuVolumeCore
            ? FLinearColor(0.035f, 0.100f, 0.120f, 1.0f)
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveReflectedSkyColor
                   : FLinearColor(0.11f, 0.23f, 0.31f, 1.0f));
    // River-local depth transmission must also migrate older serialized maps.
    // The cooked-field identity is stable, so runtime and newly regenerated
    // packages receive the same render-only coefficients without moving any
    // solver, geometry, collision, buoyancy, or force authority.
    const FLinearColor ResolvedLiveWaterScattering =
        bUsesMigratedFutaleufuVolumeCore
            ? FLinearColor(0.000035f, 0.000100f, 0.000110f, 0.0f)
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
    const float ConfiguredLiveFoamIntensity =
        bUsesMigratedColoradoVolumeCore
            ? 0.55f
            : bUsesLegacyChilkoPresentationDefaults
            ? 0.56f
            : bUsesMigratedFutaleufuVolumeCore
            ? 0.58f
            : (RiverWaterConfig
                   ? RiverWaterConfig->LiveFoamIntensity
                   : 0.52f);
    // The single South Fork carrier no longer has a separate whitewater sheet
    // to supply optical body. Its material now preserves current-aligned lace
    // and bubble perforations even at full aeration, so a stronger response is
    // safe here: only solver/wake foam is amplified and calm water stays clean.
    const float ResolvedLiveFoamIntensity = bSingleLiveWaterSurfaceEnabled
        ? FMath::Max(ConfiguredLiveFoamIntensity, 0.90f)
        : ConfiguredLiveFoamIntensity;
    bLivePresentationSurfaceSmoothingEnabled =
        bLiveSurfaceCarrierEnabled &&
        (bSingleLiveWaterSurfaceEnabled ||
            RiverWaterConfig->bEnableLivePresentationSurfaceSmoothing);
    ResolvedPresentationSurfaceSmoothingStrength =
        bSingleLiveWaterSurfaceEnabled
            ? 1.0f
            : bLivePresentationSurfaceSmoothingEnabled
            ? FMath::Clamp(
                  RiverWaterConfig->LivePresentationSurfaceSmoothingStrength,
                  0.0f,
                  1.0f)
            : 0.0f;
    // South Fork's one-surface presentation must not add the generic
    // station-periodic standing-wave field. At grazing angles its 2 cm sine
    // ridges become bright bars spanning the channel. The cooked solver
    // surface, hydraulic relief, boulder wakes, and breaking sites continue
    // to provide actual crest geometry and matching raft support.
    ResolvedPresentationStandingWaveScale = bLiveSurfaceCarrierEnabled
        ? FMath::Clamp(
              RiverWaterConfig->LivePresentationStandingWaveScale, 0.0f, 1.0f)
        : 1.0f;
    if (bSingleLiveWaterSurfaceEnabled)
    {
        // The full-reach carrier already renders the cooked free surface,
        // localized hydraulic relief, obstacle wakes, and raft-local GPU
        // turbulence. Adding the generic station-periodic train on top makes
        // every equal-phase row share a normal; at a chase-camera grazing
        // angle those rows become the horizontal reflection bars reported in
        // play. Keep this legacy field off for the one-surface path.
        ResolvedPresentationStandingWaveScale = 0.0f;
    }
    // Review override: raftsim.PresentationStandingWaveScale >= 0 forces the
    // presentation (and coupled support) standing-wave scale for A/B captures
    // of the channel-spanning bright bars (Pacuare 2026-09-02).
    if (CVarRaftSimPresentationStandingWaveScale.GetValueOnGameThread() >= 0.0f)
    {
        ResolvedPresentationStandingWaveScale = FMath::Clamp(
            CVarRaftSimPresentationStandingWaveScale.GetValueOnGameThread(), 0.0f, 1.0f);
    }
    ResolvedPresentationHydraulicReliefScale = bLiveSurfaceCarrierEnabled
        ? FMath::Clamp(
              RiverWaterConfig->LivePresentationHydraulicReliefScale, 0.0f, 1.0f)
        : 1.0f;
    if (bSurveyBreakingReview)
    {
        // Same bounded helper and accepted site list feed the carrier and
        // rigid support. The raw solver/captured terrain remain unchanged.
        ResolvedPresentationHydraulicReliefScale = 1.0f;
        UE_LOG(LogTemp, Display, TEXT("Captured South Fork shared relief enabled: playable=%d, local envelopes, one surface-lit carrier"), bPlayableCapturedSouthFork);
        const bool bCurrentNormalV2 = FParse::Param(FCommandLine::Get(),TEXT("RaftSimSurveyCurrentNormalV2Review"));
        if (bStatefulDetailReview || bCurrentNormalV2 || FParse::Param(FCommandLine::Get(),TEXT("RaftSimSurveyCurrentNormalReview")))
        {
            // Isolated shading A/B, selected before the usual live overrides.
            // Never save this selection into a map or change surface support.
            const bool bCoverageAudit = bStatefulCrestReview &&
                FParse::Param(FCommandLine::Get(), TEXT("RaftSimCoverageAudit"));
            const bool bUnifiedFoamOptics = bStatefulCrestReview &&
                FParse::Param(FCommandLine::Get(), TEXT("RaftSimUnifiedFoamOpticsReview"));
            const bool bFineDetail = bStatefulCrestReview &&
                FParse::Param(FCommandLine::Get(), TEXT("RaftSimFineDetailReview"));
            const FString Name = bCoverageAudit ? TEXT("M_RaftSim_LiveRiverSurface_StatefulCrestReview_CoverageAudit") :
                bFineDetail ? TEXT("M_RaftSim_LiveRiverSurface_StatefulCrestReview_FineGridReview") :
                bUnifiedFoamOptics ? TEXT("M_RaftSim_LiveRiverSurface_StatefulCrestReview_OpticsReview") :
                bStatefulCrestReview ? TEXT("M_RaftSim_LiveRiverSurface_StatefulCrestReview") :
                bStatefulFoamReview ? TEXT("M_RaftSim_LiveRiverSurface_StatefulFoamReview") :
                bStatefulMotionReview ? TEXT("M_RaftSim_LiveRiverSurface_StatefulMotionReview") :
                bStatefulGPUCarrierReview ? TEXT("M_RaftSim_LiveRiverSurface_StatefulGPUCarrierReview") :
                bStatefulDetailReview ? TEXT("M_RaftSim_LiveRiverSurface_StatefulDetailReview") : bCurrentNormalV2
                ? TEXT("M_RaftSim_LiveRiverSurface_CurrentNormalReviewV2")
                : TEXT("M_RaftSim_LiveRiverSurface_CurrentNormalReview");
            UMaterialInterface* Candidate = LoadObject<UMaterialInterface>(nullptr,
                *FString::Printf(TEXT("/Game/RaftSim/Environment/SouthForkSurveyCandidate/%s.%s"),*Name,*Name));
            if (Candidate) WaterMaterial = Candidate;
            else
            {
                UE_LOG(LogTemp,Error,TEXT("Survey current-normal review material is missing"));
                bStatefulMotionReview=false;bStatefulGPUCarrierReview=false;bStatefulDetailGeometryReview=false;
            }
        }
    }
    ResolvedRaftLocalFluidWindowMeters = RiverWaterConfig
        ? FMath::Clamp(
              RiverWaterConfig->LiveRaftLocalFluidWindowMeters, 20.0f, 200.0f)
        : 100.0f;
    ResolvedRaftLocalFluidHeightfieldStrength =
        RiverWaterConfig &&
            RiverWaterConfig->bEnableLiveRaftLocalFluidHeightfield
        ? FMath::Clamp(
              RiverWaterConfig->LiveRaftLocalFluidHeightfieldStrength,
              0.0f,
              1.0f)
        : 0.0f;
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
        WaterAdapter->ConfigureRaftSupportLocalFluid(
            bSingleLiveWaterSurfaceEnabled &&
                ResolvedRaftLocalFluidHeightfieldStrength > 0.0f,
            ResolvedRaftLocalFluidHeightfieldStrength,
            FoamTextureAdvectionMeters);
        if (bSingleLiveWaterSurfaceEnabled && WaterAdapter->HasCartesianWaterCoordinates())
        {
            const TWeakObjectPtr<ARaftSimWaterSurfaceActor> WeakSurface(this);
            WaterAdapter->SetRaftSupportCarrierSampler(this,
                [WeakSurface](const FVector& P,float& HeightM,bool& bWet)
                {
                    const auto* Surface=WeakSurface.Get();
                    return Surface && Surface->SampleCartesianCarrierSupport(P,HeightM,bWet);
                });
        }
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
        if (bSingleLiveWaterSurfaceEnabled && RiverWaterConfig && !WaterAdapter->HasCartesianWaterCoordinates())
        {
            // The named-rapid solver windows are intentionally smaller than
            // the camera's one-piece river carrier. Continue only the visible
            // surface from the full-reach terrain-clipped seed. Unlike the old
            // copied boundary row, this field owns an organic wet mask at
            // every station, so it cannot create a rectangular shoreline.
            const FString BaselineFieldPath =
                URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
                    FPaths::Combine(
                        RiverWaterConfig->CookedFieldsDir,
                        FString::Printf(
                            TEXT("support_band_field_%s.bin"),
                            *RiverWaterConfig->FlowBand.ToString())));
            WaterAdapter->LoadPresentationBaselineFieldFromFile(
                BaselineFieldPath);
        }
    }
    BoulderFootprintsSLR.Reset();
    if (RiverWaterConfig && !RiverWaterConfig->CookedFieldsDir.IsEmpty())
    {
        const FString FootprintPath = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(
                FPaths::ProjectDir(), TEXT(".."),
                RiverWaterConfig->CookedFieldsDir,
                TEXT("boulder_footprints.json")));
        FString FootprintJson;
        if (FFileHelper::LoadFileToString(FootprintJson, *FootprintPath))
        {
            TSharedPtr<FJsonObject> Root;
            const TSharedRef<TJsonReader<>> Reader =
                TJsonReaderFactory<>::Create(FootprintJson);
            const TArray<TSharedPtr<FJsonValue>>* Boulders = nullptr;
            if (FJsonSerializer::Deserialize(Reader, Root) && Root.IsValid() &&
                Root->TryGetArrayField(TEXT("boulders"), Boulders))
            {
                for (const TSharedPtr<FJsonValue>& Value : *Boulders)
                {
                    const TSharedPtr<FJsonObject>* Entry = nullptr;
                    if (Value->TryGetObject(Entry) && Entry != nullptr)
                    {
                        BoulderFootprintsSLR.Add(FVector3f(
                            (*Entry)->GetNumberField(TEXT("station_m")),
                            (*Entry)->GetNumberField(TEXT("lateral_m")),
                            (*Entry)->GetNumberField(TEXT("radius_m"))));
                    }
                }
                UE_LOG(LogTemp, Display,
                    TEXT("RaftSim live water: %d boulder footprints loaded"),
                    BoulderFootprintsSLR.Num());
            }
        }
    }

    bUsesCurvedRiverCoordinates = WaterAdapter && WaterAdapter->HasRiverCoordinateMap();
    if (bUsesSouthForkFullReachSingleSurface)
    {
        // The authored full-reach ribbons are deliberately hidden in play, so
        // this is not merely a near-raft detail patch: it is the visible river.
        // The former 240 m default ended before the first 0-400 m rapid grade
        // and exposed the riverbed exactly where the surface began descending.
        CurvedGridLengthMeters = FMath::Max(
            CurvedGridLengthMeters,
            GetSouthForkSingleSurfaceLengthMeters());
    }
    // Every shipped river map owns an explicit water configuration, including
    // the legacy straight-coordinate South Fork reach. Keep config-less test
    // tanks on the original three-metre mesh while refining production river
    // presentation independently of the adapter coordinate representation.
    // A bounded rapid window can afford the 0.5 m lattice required for a
    // crest to span several vertices. Do not multiply a many-kilometre
    // full-reach carrier: it keeps its existing far-field density and the
    // raft-local GPU layer supplies sub-grid motion around the camera.
    const bool bBoundedRapidPresentation =
        !bUsesSouthForkFullReachSingleSurface &&
        (bUsesCurvedRiverCoordinates
             ? CurvedGridLengthMeters
             : GridSizeMeters) <= 600.0f;
    const int32 ConfiguredRapidSubdivision =
        RiverWaterConfig &&
            RiverWaterConfig->bEnableLiveRapidSurfaceRefinement &&
            bBoundedRapidPresentation
        ? RiverWaterConfig->LiveRapidSurfaceSubdivision
        : RiverPresentationSubdivision;
    // South Fork is a moving 600 m full-reach carrier, not a fixed 100-240 m
    // rapid patch. Treating the inclusive 600 m boundary as "bounded" gave it
    // 0.5 m cells: 1,201 x 193 = 231,793 vertices, each sampled and passed
    // through the optical filter at 15 Hz. Three-metre vertices, however,
    // undersample the 5-6 m crest wavelengths and make genuine solver relief
    // look flat. A 1.5 m presentation lattice is 401 x 65 = 26,065 vertices:
    // enough silhouette for a rolling crest but still 8.9x smaller than the
    // old half-metre carrier. Hydraulic analysis remains on the three-metre
    // stride, so this adds render shape without multiplying solver work.
    const int32 ResolvedSubdivision = bUsesSouthForkFullReachSingleSurface
        ? 2
        // These 240 x 96 m windows at 0.5 m had 92,833 CPU-updated
        // vertices. One metre retains multiple vertices per hydraulic crest
        // while quartering the presentation work; hydraulics are unchanged.
        : (bUsesMigratedColoradoVolumeCore ||
            (bUsesPacuarePresentation && bSingleLiveWaterSurfaceEnabled) ||
            (bUsesMigratedFutaleufuVolumeCore && bSingleLiveWaterSurfaceEnabled) ||
            (bUsesMigratedChilkoVolumeCore && bSingleLiveWaterSurfaceEnabled))
        ? FMath::Clamp(ConfiguredRapidSubdivision, 1, 3)
        : bUsesAuthoredRiverPresentation
        ? FMath::Clamp(ConfiguredRapidSubdivision, 1, 6)
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
    BoatWakePresentationData.SetNumZeroed(VertCount);
    VertexColors.SetNum(VertCount);
    PaddleWakeVertexColors.SetNumZeroed(VertCount);
    LiveVolumeCoreVertices.SetNum(VertCount);
    LiveVolumeCoreTriangles.Reset((GridStationN - 1) * (GridLateralN - 1) * 6);
    // Force the immutable core topology to rebuild for this grid shape.
    LiveVolumeCoreStaticTopologyVertexCount = 0;
    RapidFoamVertices.SetNum(VertCount);
    RapidFoamVertexColors.SetNum(VertCount);
    SmoothedRapidFoamCoverage.SetNumZeroed(VertCount);
    Tangents.SetNum(VertCount);
    Triangles.Reset((GridStationN - 1) * (GridLateralN - 1) * 6);
    FoamField.SetNumZeroed(VertCount);
    FoamTransportVelocityMetersPerSecond.SetNumZeroed(VertCount);
    bFoamFieldValid = false;
    LiveVolumeCoreWetPresence.SetNumZeroed(VertCount);
    SmoothedBreakingLiftCm.SetNumZeroed(VertCount);
    ShoreSmoothedSurfaceZCm.Init(MAX_flt, VertCount);
    LastPaddleWakeRippleSourceCells.Reset();
    StationSolverCropAuthority.SetNumZeroed(GridStationN);
    BreakingSites.Reset();
    PersistentBreakingSites.Reset();
    BreakingSiteShapeSeedSerial = 0;
    LastBreakingSiteUpdateTimeSeconds = -1.0f;

    // Grid actor sits at world origin; vertices are in world cm relative to it.
    SetActorLocation(FVector::ZeroVector);

    if (bUsesCurvedRiverCoordinates)
    {
        if (bFixedCurvedGrid) CurvedGridCenterStationM=FixedCurvedGridCenterStationMeters;
        CartesianGridCenterNorthM = WaterAdapter->HasCartesianWaterCoordinates()
            ? FixedCartesianGridCenterNorthMeters : 0.0f;
        TActorIterator<ARaftSimRaftActor> RaftIt(GetWorld());
        if (RaftIt && !bFixedCurvedGrid)
        {
            FVector2D RiverPosition;
            FVector Tangent;
            FVector LeftNormal;
            if (WaterAdapter->WorldToRiverCoordinates(
                    RaftIt->GetActorLocation(), RiverPosition, Tangent, LeftNormal))
            {
                CurvedGridCenterStationM = RiverPosition.X;
                if (WaterAdapter->HasCartesianWaterCoordinates()) CartesianGridCenterNorthM = RiverPosition.Y;
            }
        }
        ClampCurvedGridCenter();
    }

    FLinearColor ExistingWaterUVOrigin;
    bRebaseWaterTextureCoordinates = bSingleLiveWaterSurfaceEnabled &&
        bUsesCurvedRiverCoordinates && LiveVolumeCoreMaterial &&
        LiveVolumeCoreMaterial->GetVectorParameterValue(
            FHashedMaterialParameterInfo(FName(TEXT("RaftSimWaterUVOrigin"))), ExistingWaterUVOrigin);
    WaterTextureOriginMeters = bRebaseWaterTextureCoordinates
        ? FVector2D(ComputeWaterTextureOriginMeters(CurvedGridCenterStationM),
            ComputeWaterTextureOriginMeters(CartesianGridCenterNorthM))
        : FVector2D::ZeroVector;

    for (int32 LateralIndex = 0; LateralIndex < GridLateralN; ++LateralIndex)
    {
        for (int32 StationIndex = 0; StationIndex < GridStationN; ++StationIndex)
        {
            const int32 Index = LateralIndex * GridStationN + StationIndex;
            if (bUsesCurvedRiverCoordinates)
            {
                const float StationM = CurvedGridCenterStationM - CurvedGridLengthMeters * 0.5f +
                    StationIndex * ResolvedVertexSpacingMeters;
                const float LateralM = CartesianGridCenterNorthM - CurvedGridWidthMeters * 0.5f +
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
            UVs[Index] = (RiverCoordinatesM[Index] - WaterTextureOriginMeters) / kWaterTextureRepeatMeters;
            FlowVelocityMetersPerSecond[Index] = FVector2D::ZeroVector;
            BoatWakePresentationData[Index] = FVector2D::ZeroVector;
            VertexColors[Index] = FLinearColor(
                0.0f,
                0.0f,
                0.0f,
                StationEdgeCoverage(StationIndex));
            PaddleWakeVertexColors[Index] = FLinearColor::Transparent;
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
    UpdateSurfaceCarrierMesh(true,VertexColors);
    // A second section uses identical displaced vertices but a localized
    // vertex-alpha mask. This keeps the authored river handoff transparent
    // while giving the real wake geometry enough optical weight to read.
    SurfaceMesh->CreateMeshSection_LinearColor(
        1,
        Vertices,
        Triangles,
        Normals,
        UVs,
        FlowVelocityMetersPerSecond,
        BoatWakePresentationData,
        EmptyUVs,
        PaddleWakeVertexColors,
        Tangents,
        /*bCreateCollision=*/false);
    SurfaceMesh->SetMeshSectionVisible(1, false);
    SurfaceMesh->SetMeshSectionVisible(0, !bSingleLiveWaterSurfaceEnabled);
    LiveVolumeCoreMesh->SetVisibility(false, true);
    CartesianShorelineMesh->SetVisibility(false);
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
                    TEXT("RaftSimWaterUVOrigin"),
                    FLinearColor(WaterTextureOriginMeters.X / kWaterTextureRepeatMeters,
                        WaterTextureOriginMeters.Y / kWaterTextureRepeatMeters, 0.0f, 0.0f));
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
#if !UE_BUILD_SHIPPING
                // Diagnostic knockout of the final optical consumer only.
                // Density/source/advection, WPO, normals and contact are not
                // edited. Zero optical density makes both GPU-authority and
                // CPU-edge coverage resolve to zero in the same material.
                if (GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")) && FParse::Param(
                    FCommandLine::Get(),TEXT("RaftSimFoamOpticsOff")))
                {
                    VolumeMaterial->SetScalarParameterValue(TEXT("SouthForkFoamOpticalDensity"),0.f);
                    UE_LOG(LogTemp,Display,TEXT("FoamOpticsOff: diagnostic optical coverage disabled; foam state and carrier unchanged"));
                }
#endif
                if (bSingleLiveWaterSurfaceEnabled)
                {
                    // South Fork presents the persistent transported foam
                    // field. Its current parent samples effective surface
                    // transport through UV3; older parents retain the shared
                    // advection collection. These legacy parameter overrides
                    // do not replace the new parent's optical coverage node.
                    // Keep a small floor for connected froth, but never force
                    // the breakup response solid again.
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("HydraulicFoamColorBreakupBias"), bRebaseWaterTextureCoordinates ? 0.0f : 0.06f);
                    // Chilko has a separately calibrated current-water parent.
                    // Replacing its 0.58 breakup gain with the old South Fork
                    // 3.0 boost clamped most lace patches solid white, hiding
                    // the wave faces even with correct linear vertex data.
                    if (!bUsesMigratedChilkoVolumeCore)
                    {
                        VolumeMaterial->SetScalarParameterValue(
                            TEXT("HydraulicFoamColorBreakupGain"), bRebaseWaterTextureCoordinates ? 3.0f : 1.08f);
                    }
                    if (bRebaseWaterTextureCoordinates)
                    {
                        // Keep open water between torn foam filaments instead
                        // of adding a uniform gray veil over every foam cell.
                        VolumeMaterial->SetScalarParameterValue(
                            // Chilko needs connected froth inside the web, not
                            // an additive bias that grays every aerated cell.
                            TEXT("WhitewaterFrothLaceModulationFloor"),
                            bUsesMigratedChilkoVolumeCore ? 0.10f : 0.02f);
                        VolumeMaterial->SetScalarParameterValue(TEXT("FoamRoughness"), 0.80f);
                    }
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("DriftFoamAerationGain"), 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("DriftFoamSpeedGain"), 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("DriftFoamOpacity"), 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("DriftFoamSurfaceGlow"), 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("DriftFoamRoughness"), 0.0f);
                    // The unified material's analytic sine-lane fallback is
                    // periodic in river station. Without the micro normal it
                    // reads as bright bars spanning the channel, so South
                    // Fork relies on solver displacement and foam instead.
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("LiveFlowStreakRoughness"), 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("LiveFlowStreakTint"), 0.0f);
                    // The saved South Fork transmission parent predates the
                    // unified LiveFlowStreak names above. Its actual analytic
                    // roughness lanes use these legacy parameters; leaving
                    // them at 0.22/5.0 is what produced the pale transverse
                    // stripes even though the newer overrides were zero.
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("FlowStreakRoughness"), 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("FlowStreakSpeedGain"), 0.0f);
                    // The guide-eye camera sees the carrier at a very grazing
                    // angle. Suppress the infinite analytic sine fallback and
                    // heavily fade micro normals there; otherwise repeated
                    // normal lobes become perspective streaks and mirrored
                    // texture boundaries become horizontal bars. Solver mesh
                    // displacement and the localized GPU crest field remain
                    // fully active, so rapid shape still has real relief.
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("AnalyticChopStrength"), 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("RippleGrazingFloor"), bRebaseWaterTextureCoordinates ? 0.50f : 0.015f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("FlowNormalSteepness"), bRebaseWaterTextureCoordinates ? 2.0f : 1.15f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("SlickNormalFloor"), bRebaseWaterTextureCoordinates ? 0.60f : 0.20f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("GrazingRoughnessBoost"), 0.12f);
                    // The capture-safe world-space brightness noise stretches
                    // into pale cross-channel bands on this long curved mesh.
                    // Keep reflection energy uniform; physical normals and
                    // solver geometry still provide all view-dependent motion.
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("CalmSurfaceColorVariation"), 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("FallbackSkyReflectionVariation"), 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("FallbackSkyReflectionFloor"), 1.0f);
                    float ExistingTravelingWaveWPOStrength = 0.0f;
                    bHasTravelingWaveWPOStrengthParameter =
                        VolumeMaterial->GetScalarParameterValue(
                            FHashedMaterialParameterInfo(FName(
                                TEXT("SouthForkTravelingWaveWPOStrength"))),
                            ExistingTravelingWaveWPOStrength);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("SouthForkTravelingWaveWPOStrength"), 0.0f);
                    // Current micro-relief is evaluated continuously in the
                    // shader. Keep it below the solver-owned obstacle/wake
                    // relief so the surface boils without lifting the raft
                    // through an unrelated render-only amplitude. Raised
                    // from the flicker-era 0.16 after the aeration/flow
                    // review: whitewater read as a smooth sheet with no
                    // visible chop. 0.30 gives ~±5 cm of foam-gated chop;
                    // the raft's render-vs-support mismatch stays inside
                    // the tube draft.
                    // Disable the retired unbounded field and enable the
                    // V2 raft-local GPU heightfield on this same carrier.
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("SouthForkTurbulenceWPOStrength"), 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("RaftSimLocalFluidWPOStrength"),
                        ResolvedRaftLocalFluidHeightfieldStrength);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("RaftSimLocalFluidWindowMeters"),
                        ResolvedRaftLocalFluidWindowMeters);
                    // Entrained-air milk must come from breaking foam, not
                    // raw speed: a fast glassy tongue stays optically green.
                    // The parent's larger default speed fraction predates the
                    // roughness-gated foam generator that now confines
                    // aeration to genuinely working water.
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("SpeedAerationFraction"), 0.0f);
                }
#if !UE_BUILD_SHIPPING
                if (GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")) && FParse::Param(
                    FCommandLine::Get(),TEXT("RaftSimDielectricWaterReview")))
                {
                    // Single Layer Water already evaluates view-dependent
                    // Fresnel reflection. Use water's dielectric F0 input,
                    // without another angle-dependent IOR or painted sky
                    // contribution in the base-color graph. No lighting,
                    // roughness, foam density, normal or geometry changes.
                    VolumeMaterial->SetScalarParameterValue(TEXT("Specular"),0.255f);
                    VolumeMaterial->SetScalarParameterValue(TEXT("FresnelSpecular"),0.f);
                    VolumeMaterial->SetScalarParameterValue(TEXT("FallbackSkyReflectionStrength"),0.f);
                    UE_LOG(LogTemp,Display,TEXT("DielectricWaterReview: specular=0.255, additional Fresnel/painted-sky=0; foam and physical carrier retained"));
                }
#endif
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("CalmRippleStrength"),
                    0.025f + ResolvedLiveRippleStrength * 0.08f);
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("FlowRippleStrength"),
                    0.035f + ResolvedLiveRippleStrength * 0.16f);
                if (bSingleLiveWaterSurfaceEnabled)
                {
                    // Small local UVs fix the half-precision row collapse that
                    // had been mistaken for a normal-map artifact. Restore
                    // bounded, aeration-weighted slopes on the migrated parent;
                    // retain the safe fallback on an unmigrated material.
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("CalmRippleStrength"), bRebaseWaterTextureCoordinates ? 0.08f : 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("FlowRippleStrength"), bRebaseWaterTextureCoordinates ? 0.14f : 0.0f);
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("FoamRippleStrength"), bRebaseWaterTextureCoordinates ? 0.25f : 0.0f);
                    // The residual "reflection flicker" was isolated
                    // (2026-08-27 static-camera bursts, all reflection
                    // subsystems disabled in turn) to the material's own
                    // sun-glint strobe: fine panning normals under a tight
                    // specular lobe decorrelate every frame. A slightly
                    // rougher lobe turns pixel-quantized blinking glints
                    // into stable soft streaks. 0.31 also blurred sky and
                    // shore into the milky sheet the clear-water pass
                    // removed (2026-08-31): 0.20 damps the glints without
                    // repainting the veil, and the static tiles' MI now
                    // matches it EXACTLY — with both sheets at the same
                    // level (WPO sink) any roughness gap reads as a
                    // reflection-sharpness seam at the carrier window edge
                    // (2026-09-02).
                    VolumeMaterial->SetScalarParameterValue(
                        TEXT("WaterRoughness"), 0.22f);
                }
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
                // The carrier's vertices FOLLOW the live level; only the
                // static cooked tiles retire their above-waterline sheet.
                VolumeMaterial->SetScalarParameterValue(
                    TEXT("ApplyLiveLevelShoreClip"), 0.0f);
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
        SurfaceMesh->SetMaterial(
            1, PaddleWakeMaterial != nullptr
                ? PaddleWakeMaterial.Get()
                : WaterMaterial.Get());
        // Most maps retain an authored Single Layer Water surface and use this
        // as a transparent hydraulic-detail overlay. Physical source-corridor
        // maps deliberately hide their capture ribbon during play; their
        // saved water config therefore promotes this same solver mesh to the
        // river-wide visible carrier with a bounded river-specific profile.
        if (bPlayableCapturedSouthFork ||
            WaterMaterial->GetPathName().Contains(TEXT("M_RaftSim_LiveRiverSurface")))
        {
            if (UMaterialInstanceDynamic* LiveWaterMaterial =
                    SurfaceMesh->CreateDynamicMaterialInstance(0, WaterMaterial))
            {
                const bool bDebugCoverage =
                    CVarRaftSimLiveSheetDebugCoverage
                        .GetValueOnGameThread() != 0;
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("CalmLiveSurfaceCoverage"),
                    bDebugCoverage ? 1.0f : ResolvedCalmLiveSurfaceCoverage);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("ActiveLiveSurfaceCoverage"),
                    bDebugCoverage ? 1.0f
                                   : ResolvedActiveLiveSurfaceCoverage);
                // On authored-band rivers the band surface owns every foam
                // presentation channel; the overlay's own foam whitening
                // only surfaces through wave troughs as flicker chasing
                // the raft. Carrier maps keep the overlay foam.
                const float OverlayFoamScale =
                    bLiveSurfaceCarrierEnabled ? 1.0f : 0.0f;
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("SolverFoamOpacityGain"),
                    (bSingleLiveWaterSurfaceEnabled ? 0.12f : 0.55f) *
                        OverlayFoamScale);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveSolverFoamGlow"), 0.55f * OverlayFoamScale);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveDriftFoamSurfaceGlow"),
                    0.40f * OverlayFoamScale);
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveDriftFoamOpacity"), 0.35f * OverlayFoamScale);
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
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LivePaddleWakeGeometryCoverage"), 0.0f);
                if (bSurveyBreakingReview && FParse::Param(
                        FCommandLine::Get(), TEXT("RaftSimSurveyLitFoamReview")))
                {
                    // The review carrier receives actual surface lighting.
                    // Overlay-era emissive foam flattens that illumination;
                    // compare lit diffuse froth without changing foam mass,
                    // UV phase, opacity, crest geometry or rigid support.
                    LiveWaterMaterial->SetScalarParameterValue(TEXT("LiveSolverFoamGlow"),0.0f);
                    LiveWaterMaterial->SetScalarParameterValue(TEXT("LiveDriftFoamSurfaceGlow"),0.0f);
                    LiveWaterMaterial->SetScalarParameterValue(TEXT("LiveFoamRoughnessOpenCell"),0.62f);
                    LiveWaterMaterial->SetScalarParameterValue(TEXT("LiveFoamRoughnessBubble"),0.80f);
                    // Restore aerated body on THIS carrier after removing
                    // the bright masked duplicate; calm vertices stay clear.
                    LiveWaterMaterial->SetScalarParameterValue(TEXT("LiveFoamIntensity"),1.50f);
                    LiveWaterMaterial->SetScalarParameterValue(TEXT("WhitewaterFrothLaceModulationFloor"),0.45f);
                    LiveWaterMaterial->SetScalarParameterValue(TEXT("WhitewaterFrothPatchOutsideFloor"),0.15f);
                    UE_LOG(LogTemp,Display,TEXT("SurveyLitFoamReview enabled: non-emissive surface-lit froth; geometry/flow/opacity unchanged"));
                }
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
                // Always fade the live sheet out over solver-dry cells.
                // With this disabled on corridor maps, the carrier drew a
                // translucent veil across everything the leveled grid spans
                // above the waterline — exposed boulder crowns read as
                // shrouded to the tip (2026-08-15 playtest report).
                LiveWaterMaterial->SetScalarParameterValue(
                    TEXT("LiveWetCoverageEnable"), 1.0f);
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
                if (bStatefulGPUCarrierReview && MacroSurfaceTexture)
                {
                    LiveWaterMaterial->SetTextureParameterValue(TEXT("MacroSurfaceAtlas"),MacroSurfaceTexture);
                    if (bStatefulMotionReview && PreviousMacroSurfaceTexture)
                        LiveWaterMaterial->SetTextureParameterValue(TEXT("PreviousMacroSurfaceAtlas"),PreviousMacroSurfaceTexture);
                    LiveWaterMaterial->SetVectorParameterValue(TEXT("MacroGridSize"),FLinearColor(GridStationN,GridLateralN,0,0));
                    LiveWaterMaterial->SetScalarParameterValue(TEXT("MacroSurfaceEnable"),1);
                }
                if (bStatefulDetailReview && (WaterMaterial->GetPathName().Contains(TEXT("StatefulDetailReview")) ||
                    WaterMaterial->GetPathName().Contains(TEXT("StatefulGPUCarrierReview")) ||
                    WaterMaterial->GetPathName().Contains(TEXT("StatefulMotionReview")) ||
                    WaterMaterial->GetPathName().Contains(TEXT("StatefulFoamReview")) ||
                    WaterMaterial->GetPathName().Contains(TEXT("StatefulCrestReview"))))
                {
                    FVector Center,Along;
                    if (WaterAdapter && WaterAdapter->RiverToWorldPosition(FVector2D(0,0),220,Center) &&
                        WaterAdapter->RiverToWorldPosition(FVector2D(1,0),220,Along))
                    {
                        auto* Detail=NewObject<URaftSimStatefulDetailComponent>(this);
                        AddInstanceComponent(Detail);Detail->RegisterComponent();
                        if (!Detail->Initialize(WaterAdapter,LiveWaterMaterial,Center,Along-Center,bStatefulMotionReview))
                            UE_LOG(LogTemp,Error,TEXT("Stateful detail review failed to initialize"));
                    }
                    else UE_LOG(LogTemp,Error,TEXT("Stateful detail review is missing its registered water basis"));
                }
            }
        }
    }
    if (PaddleWakeMaterial != nullptr)
    {
        if (UMaterialInstanceDynamic* PaddleWakeDynamic =
                SurfaceMesh->CreateDynamicMaterialInstance(
                    1, PaddleWakeMaterial))
        {
            PaddleWakeDynamic->SetVectorParameterValue(
                TEXT("PaddleWakeTroughColor"),
                FLinearColor(0.008f, 0.020f, 0.025f, 1.0f));
            PaddleWakeDynamic->SetVectorParameterValue(
                TEXT("PaddleWakeCrestColor"),
                FLinearColor(0.035f, 0.075f, 0.090f, 1.0f));
            PaddleWakeDynamic->SetVectorParameterValue(
                TEXT("PaddleWakeReflectedSkyColor"),
                FLinearColor(0.050f, 0.095f, 0.120f, 1.0f));
            PaddleWakeDynamic->SetScalarParameterValue(
                TEXT("PaddleWakeReflectionStrength"), 0.18f);
            PaddleWakeDynamic->SetScalarParameterValue(
                TEXT("PaddleWakeOpacity"), 0.58f);
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
        // Organic variation is phased by the site's lifetime seed, never by
        // its rank in the strongest-first list: intensity rank swaps between
        // refreshes used to re-roll every fold and crest offset in one frame.
        const float ShapeSeed = Site.ShapeSeed;
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
                        ShapeSeed * 1.73f + SignedAcross * 5.1f + CurlT * 8.7f) *
                    4.5f * Intensity * EdgeTaper * FMath::Sin(PI * CurlT);
                // Break both the visible boundary and dense aerated core at
                // two incommensurate lateral frequencies. This prevents a
                // moderate jump from reading as one channel-spanning white
                // oval while keeping every fragment on one connected sheet.
                const float BoundaryVariation = FMath::Clamp(
                    0.68f +
                        0.18f * FMath::Sin(
                            ShapeSeed * 1.31f + SignedAcross * 7.7f +
                            CurlT * 11.3f) +
                        0.14f * FMath::Sin(
                            ShapeSeed * 2.17f - SignedAcross * 13.1f +
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
                            ShapeSeed * 2.31f + SignedAcross * 9.7f) +
                        0.16f * FMath::Sin(
                            ShapeSeed * 0.83f - SignedAcross * 17.3f),
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
                    ShapeSeed * 1.19f + SignedAcross * 3.7f;
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

    LogWaterRenderStateEvent(GetWorld(), TEXT("breaking_lip_create"));
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
        // Lifetime seed, not list rank: rank swaps must not re-roll the
        // membrane's breakup and travel phases between refreshes.
        const float ShapeSeed = Site.ShapeSeed;
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
                                ShapeSeed * 1.67f + SignedAcross * 10.3f +
                                ProfileLoopT * 8.9f) +
                            0.18f * FMath::Sin(
                                ShapeSeed * 2.43f - SignedAcross * 16.7f +
                                ProfileLoopT * 15.1f),
                        0.16f,
                        1.0f);
                    const float OrganicTravelCm =
                        FMath::Sin(
                            ShapeSeed * 1.13f + SignedAcross * 4.7f +
                            ProfileLoopT * 6.3f) *
                        13.0f * Intensity * EdgeTaper * LoopFeather;
                    const float OrganicLiftCm =
                        FMath::Sin(
                            ShapeSeed * 2.07f + SignedAcross * 7.1f +
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

    LogWaterRenderStateEvent(GetWorld(), TEXT("breaking_roller_create"));
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
    if (!bUsesCurvedRiverCoordinates || !WaterAdapter || bFixedCurvedGrid)
    {
        return;
    }
    const float PreviousCenterStationM = CurvedGridCenterStationM;
    const float PreviousCenterNorthM = CartesianGridCenterNorthM;
    float DesiredCenterStationM = CurvedGridCenterStationM;
    float DesiredCenterNorthM = CartesianGridCenterNorthM;
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
            if (WaterAdapter->HasCartesianWaterCoordinates()) DesiredCenterNorthM = RiverPosition.Y;
        }
    }
    if (FMath::Abs(DesiredCenterStationM - CurvedGridCenterStationM) <
        CurvedGridRecenterDistanceMeters &&
        FMath::Abs(DesiredCenterNorthM - CartesianGridCenterNorthM) < CurvedGridRecenterDistanceMeters)
    {
        return;
    }
    // Preserve the global presentation lattice when the moving mesh recentres.
    // Using the raft's arbitrary fractional station as the new origin changed
    // every shoreline sample phase by up to one cell; shallow bank triangles
    // then appeared or disappeared even across the large overlapping region.
    // Integer-cell shifts keep all overlap vertices at exactly the same river
    // coordinates. Only the genuinely new leading edge is sampled anew.
    float MinimumRiverStationM = 0.0f;
    float MaximumRiverStationM = 0.0f;
    if (WaterAdapter->GetRiverStationRangeM(
            MinimumRiverStationM, MaximumRiverStationM))
    {
        const float SafeSpacingMeters = FMath::Max(
            ResolvedVertexSpacingMeters, KINDA_SMALL_NUMBER);
        DesiredCenterStationM = MinimumRiverStationM +
            FMath::RoundToFloat(
                (DesiredCenterStationM - MinimumRiverStationM) /
                SafeSpacingMeters) *
                SafeSpacingMeters;
    }
    CurvedGridCenterStationM = DesiredCenterStationM;
    CartesianGridCenterNorthM = DesiredCenterNorthM;
    ClampCurvedGridCenter();
    if (bRebaseWaterTextureCoordinates)
    {
        WaterTextureOriginMeters.X =
            ComputeWaterTextureOriginMeters(CurvedGridCenterStationM);
        WaterTextureOriginMeters.Y = ComputeWaterTextureOriginMeters(CartesianGridCenterNorthM);
        if (UMaterialInstanceDynamic* Material =
            Cast<UMaterialInstanceDynamic>(LiveVolumeCoreMesh->GetMaterial(0)))
        {
            Material->SetVectorParameterValue(TEXT("RaftSimWaterUVOrigin"),
                FLinearColor(WaterTextureOriginMeters.X / kWaterTextureRepeatMeters,
                    WaterTextureOriginMeters.Y / kWaterTextureRepeatMeters, 0, 0));
        }
    }
    for (int32 LateralIndex = 0; LateralIndex < GridLateralN; ++LateralIndex)
    {
        for (int32 StationIndex = 0; StationIndex < GridStationN; ++StationIndex)
        {
            const int32 Index = LateralIndex * GridStationN + StationIndex;
            RiverCoordinatesM[Index] = FVector2D(
                CurvedGridCenterStationM - CurvedGridLengthMeters * 0.5f +
                    StationIndex * ResolvedVertexSpacingMeters,
                CartesianGridCenterNorthM - CurvedGridWidthMeters * 0.5f +
                    LateralIndex * ResolvedVertexSpacingMeters);
            UVs[Index] = (RiverCoordinatesM[Index] - WaterTextureOriginMeters) / kWaterTextureRepeatMeters;
        }
    }
    UpdateCurvedGridPlanarGeometry();

    // Vertex-indexed temporal state must travel with its river cell, not its
    // array slot. The recentre shifts every index by a whole number of
    // station cells; leaving these fields un-shifted applied each cell's
    // smoothing history to a neighbour up to the recentre distance away,
    // which stepped shoreline presence and foam coverage on every recentre.
    const float SafeSpacingMeters = FMath::Max(
        ResolvedVertexSpacingMeters, KINDA_SMALL_NUMBER);
    const float ShiftCellsExact =
        (CurvedGridCenterStationM - PreviousCenterStationM) / SafeSpacingMeters;
    const int32 ShiftCells = FMath::RoundToInt(ShiftCellsExact);
    const float ShiftNorthExact = (CartesianGridCenterNorthM - PreviousCenterNorthM) / SafeSpacingMeters;
    const int32 ShiftNorth = FMath::RoundToInt(ShiftNorthExact);
    if ((ShiftCells != 0 || ShiftNorth != 0) &&
        FMath::Abs(ShiftCellsExact - ShiftCells) < 0.01f && FMath::Abs(ShiftNorthExact - ShiftNorth) < 0.01f)
    {
        const auto ShiftStationIndexedFloats =
            [this, ShiftCells, ShiftNorth](TArray<float>& Values, float FillValue)
        {
            if (Values.Num() != GridStationN * GridLateralN)
            {
                return;
            }
            const TArray<float> Previous = Values;
            for (int32 Y = 0; Y < GridLateralN; ++Y)
            {
                for (int32 X = 0; X < GridStationN; ++X)
                {
                    const int32 SourceX = X + ShiftCells;
                    const int32 SourceY = Y + ShiftNorth;
                    Values[Y * GridStationN + X] =
                        SourceX >= 0 && SourceX < GridStationN && SourceY >= 0 && SourceY < GridLateralN
                        ? Previous[SourceY * GridStationN + SourceX]
                        : FillValue;
                }
            }
        };
        ShiftStationIndexedFloats(LiveVolumeCoreWetPresence, 0.0f);
        ShiftStationIndexedFloats(SmoothedRapidFoamCoverage, 0.0f);
        ShiftStationIndexedFloats(SmoothedBreakingLiftCm, 0.0f);
        ShiftStationIndexedFloats(ShoreSmoothedSurfaceZCm, MAX_flt);
        ShiftStationIndexedFloats(VisualBankTerrainZCm, 0.0f);
        const auto ShiftStationIndexedBytes =
            [this, ShiftCells, ShiftNorth](TArray<uint8>& Values, uint8 FillValue)
        {
            if (Values.Num() != GridStationN * GridLateralN)
            {
                return;
            }
            const TArray<uint8> Previous = Values;
            for (int32 Y = 0; Y < GridLateralN; ++Y)
            {
                for (int32 X = 0; X < GridStationN; ++X)
                {
                    const int32 SourceX = X + ShiftCells;
                    const int32 SourceY = Y + ShiftNorth;
                    Values[Y * GridStationN + X] =
                        SourceX >= 0 && SourceX < GridStationN && SourceY >= 0 && SourceY < GridLateralN
                        ? Previous[SourceY * GridStationN + SourceX]
                        : FillValue;
                }
            }
        };
        // Incoming columns re-probe (0); a re-probe also refreshes cells whose
        // tile had not streamed in when first traced.
        ShiftStationIndexedBytes(VisualBankProbeState, 0);
        ShiftStationIndexedBytes(VisualFilmCullState, 0);
        const auto ShiftStationIndexedVectors =
            [this, ShiftCells, ShiftNorth](
                TArray<FVector2D>& Values, const FVector2D& FillValue)
        {
            if (Values.Num() != GridStationN * GridLateralN)
            {
                return;
            }
            const TArray<FVector2D> Previous = Values;
            for (int32 Y = 0; Y < GridLateralN; ++Y)
            {
                for (int32 X = 0; X < GridStationN; ++X)
                {
                    const int32 SourceX = X + ShiftCells;
                    const int32 SourceY = Y + ShiftNorth;
                    Values[Y * GridStationN + X] =
                        SourceX >= 0 && SourceX < GridStationN && SourceY >= 0 && SourceY < GridLateralN
                        ? Previous[SourceY * GridStationN + SourceX]
                        : FillValue;
                }
            }
        };
        // UV1 flow velocity is temporally smoothed in place, so its state
        // must travel with its river cell like the other smoothing fields.
        ShiftStationIndexedVectors(
            FlowVelocityMetersPerSecond, FVector2D::ZeroVector);
    }
}

void ARaftSimWaterSurfaceActor::CarryRenderedGridHistory(int32 ShiftX, int32 ShiftY)
{
    const auto Carry = [this, ShiftX, ShiftY](auto& History, const auto& Targets)
    {
        check(History.Num() == GridStationN * GridLateralN && Targets.Num() == History.Num());
        const auto Previous = History;
        for (int32 Y = 0; Y < GridLateralN; ++Y)
        {
            for (int32 X = 0; X < GridStationN; ++X)
            {
                const int32 Index = Y * GridStationN + X;
                const int32 SourceX = X + ShiftX;
                const int32 SourceY = Y + ShiftY;
                History[Index] = SourceX >= 0 && SourceX < GridStationN && SourceY >= 0 && SourceY < GridLateralN
                    ? Previous[SourceY * GridStationN + SourceX] : Targets[Index];
            }
        }
    };
    Carry(RenderedLiveVolumeCoreVertices, LiveVolumeCoreVertices);
    Carry(RenderedLiveVolumeCoreNormals, LiveVolumeCoreNormals);
    Carry(RenderedLiveVolumeCoreVertexColors, LiveVolumeCoreVertexColors);
    Carry(RenderedLiveVolumeCoreFlowVelocity, FlowVelocityMetersPerSecond);
    Carry(RenderedLiveVolumeCoreWakeData, BoatWakePresentationData);
}

int32 ARaftSimWaterSurfaceActor::CorridorEndPadState() const
{
    // Bit 1: the grid's first row sits at the corridor's first station;
    // bit 2: its last row sits at the corridor's last station. Both the
    // station edge blend and the core's immutable topology key on this.
    int32 State = 0;
    float MinimumStationM = 0.0f;
    float MaximumStationM = 0.0f;
    if (WaterAdapter && GridStationN > 1 &&
        WaterAdapter->GetRiverStationRangeM(MinimumStationM, MaximumStationM))
    {
        const float GridStartM =
            CurvedGridCenterStationM - CurvedGridLengthMeters * 0.5f;
        const float GridEndM =
            GridStartM + static_cast<float>(GridStationN - 1) *
                ResolvedVertexSpacingMeters;
        const float ToleranceM = ResolvedVertexSpacingMeters * 1.5f;
        if (GridStartM <= MinimumStationM + ToleranceM)
        {
            State |= 1;
        }
        if (GridEndM >= MaximumStationM - ToleranceM)
        {
            State |= 2;
        }
    }
    return State;
}

float ARaftSimWaterSurfaceActor::StationEdgeCoverage(int32 StationIndex) const
{
    // The station blend hides the moving window's leading and trailing rows,
    // where the next window continues the river. At the corridor's own ends
    // there is nothing to hand off to, and fading there left the first 36 m
    // of Hance solver-wet but unrendered — the raft floated above bare
    // landscape at the put-in apron (survey 2026-09-02) — and the same apron
    // gap exists at the full reach's station 0. Rows that sit at a corridor
    // end keep full coverage; the lateral bank blend is untouched.
    const int32 PadState = CorridorEndPadState();
    const int32 UpstreamPad = (PadState & 1) ? GridStationN : 0;
    const int32 DownstreamPad = (PadState & 2) ? GridStationN : 0;
    return ComputeStationEdgeCoverage(
        StationIndex + UpstreamPad,
        GridStationN + UpstreamPad + DownstreamPad,
        ResolvedVertexSpacingMeters,
        CurvedGridEdgeBlendMeters);
}

void ARaftSimWaterSurfaceActor::ClampCurvedGridCenter()
{
    FBox2D Bounds;
    if (WaterAdapter && WaterAdapter->GetCartesianWaterBoundsM(Bounds))
    {
        // Use an inward-rounded global presentation lattice on BOTH axes.
        // Bounds are hydraulic coordinates, never global gameplay chainage.
        const float Spacing = FMath::Max(ResolvedVertexSpacingMeters, KINDA_SMALL_NUMBER);
        const auto ClampAxis = [Spacing](float Desired, double Minimum, double Maximum, float Extent, int32 Samples)
        {
            const double Low = FMath::CeilToDouble((Minimum + Extent * .5) / Spacing) * Spacing;
            // BuildGrid rounds the vertex count: use its actual last vertex,
            // not the nominal extent, when the extent is not spacing-divisible.
            const double ActualSpan = FMath::Max(Samples-1, 1) * static_cast<double>(Spacing);
            const double High = FMath::FloorToDouble((Maximum + Extent * .5 - ActualSpan) / Spacing) * Spacing;
            checkf(Low <= High, TEXT("Cartesian water carrier is larger than its coordinate domain"));
            return static_cast<float>(FMath::Clamp(FMath::RoundToDouble(Desired / Spacing) * Spacing, Low, High));
        };
        CurvedGridCenterStationM = ClampAxis(CurvedGridCenterStationM, Bounds.Min.X, Bounds.Max.X, CurvedGridLengthMeters, GridStationN);
        CartesianGridCenterNorthM = ClampAxis(CartesianGridCenterNorthM, Bounds.Min.Y, Bounds.Max.Y, CurvedGridWidthMeters, GridLateralN);
        return;
    }
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
            FVector WorldPosition = FVector::ZeroVector;
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
                FProcMeshTangent(FlowTangent, WaterAdapter && WaterAdapter->GetRiverWorldYSign() < 0);
        }
    }
}

// The bounded plunge-pocket/boil budget follows this many strongest sites.
// Shared by the presentation carve and the persistent-site weight easing.
constexpr int32 kMaximumBreakingPresentationSites = 3;

void ARaftSimWaterSurfaceActor::UpdatePersistentBreakingSites(
    const TArray<FBreakingSite>& AcceptedCandidates)
{
    // Real time between hydraulic refreshes; clamped so an editor hitch or
    // breakpoint cannot teleport every eased site to its newest detection.
    const float NowSeconds = GetWorld()
        ? static_cast<float>(GetWorld()->GetTimeSeconds())
        : 0.0f;
    const float DeltaSeconds = LastBreakingSiteUpdateTimeSeconds >= 0.0f
        ? FMath::Clamp(NowSeconds - LastBreakingSiteUpdateTimeSeconds, 0.0f, 0.5f)
        : FMath::Max(RefreshIntervalSeconds, 0.0f);
    LastBreakingSiteUpdateTimeSeconds = NowSeconds;
    const auto BlendFactor = [DeltaSeconds](float ResponsePerSecond)
    {
        return 1.0f - FMath::Exp(-ResponsePerSecond * DeltaSeconds);
    };

    // The detected front wanders across presentation lattice cells and the
    // 6 m dedupe can hand one long jump line to a neighbouring survivor;
    // both remain the same physical hydraulic. Anything beyond the dedupe
    // spacing is a different feature and must spawn as its own site.
    constexpr float kSiteMatchRadiusMeters = 6.0f;
    constexpr int32 kMaxPersistentSites = 24;
    constexpr float kPositionResponsePerSecond = 7.0f;
    constexpr float kIntensityAttackPerSecond = 8.0f;
    constexpr float kIntensityReleasePerSecond = 2.5f;
    constexpr float kEnvelopeAttackPerSecond = 4.0f;
    constexpr float kEnvelopeReleasePerSecond = 1.8f;
    constexpr float kPresentationWeightAttackPerSecond = 3.0f;
    constexpr float kPresentationWeightReleasePerSecond = 2.2f;

    for (FPersistentBreakingSite& Persistent : PersistentBreakingSites)
    {
        Persistent.bMatchedThisRefresh = false;
    }

    // Candidates arrive strongest first, so the main jump claims its nearest
    // persistent identity before a weak shoulder can steal it.
    for (const FBreakingSite& Candidate : AcceptedCandidates)
    {
        FPersistentBreakingSite* Nearest = nullptr;
        float NearestDistanceSquared =
            kSiteMatchRadiusMeters * kSiteMatchRadiusMeters;
        for (FPersistentBreakingSite& Persistent : PersistentBreakingSites)
        {
            if (Persistent.bMatchedThisRefresh)
            {
                continue;
            }
            const float DistanceSquared = FVector2D::DistSquared(
                Persistent.Smoothed.RiverCoordinatesMeters,
                Candidate.RiverCoordinatesMeters);
            if (DistanceSquared < NearestDistanceSquared)
            {
                NearestDistanceSquared = DistanceSquared;
                Nearest = &Persistent;
            }
        }
        if (Nearest)
        {
            Nearest->bMatchedThisRefresh = true;
            FBreakingSite& Smoothed = Nearest->Smoothed;
            const float PositionBlend = BlendFactor(kPositionResponsePerSecond);
            Smoothed.WorldPositionCm = FMath::Lerp(
                Smoothed.WorldPositionCm,
                Candidate.WorldPositionCm,
                PositionBlend);
            Smoothed.WorldVelocityMps = FMath::Lerp(
                Smoothed.WorldVelocityMps,
                Candidate.WorldVelocityMps,
                PositionBlend);
            Smoothed.RiverCoordinatesMeters = FMath::Lerp(
                Smoothed.RiverCoordinatesMeters,
                Candidate.RiverCoordinatesMeters,
                PositionBlend);
            Smoothed.PresentationCoverage = FMath::Lerp(
                Smoothed.PresentationCoverage,
                Candidate.PresentationCoverage,
                PositionBlend);
            Smoothed.FlowDirection = RaftSimWaterFlowFrame::BlendDirections(
                Smoothed.FlowDirection,Candidate.FlowDirection,PositionBlend);
            Smoothed.HydraulicCrestDimensionsMeters = FMath::Lerp(
                Smoothed.HydraulicCrestDimensionsMeters,
                Candidate.HydraulicCrestDimensionsMeters, PositionBlend);
            Smoothed.HydraulicSpillingFraction = FMath::Lerp(
                Smoothed.HydraulicSpillingFraction, Candidate.HydraulicSpillingFraction, PositionBlend);
            Smoothed.PresentationEdgeClearanceMeters = FMath::Lerp(
                Smoothed.PresentationEdgeClearanceMeters,
                Candidate.PresentationEdgeClearanceMeters,
                PositionBlend);
            Nearest->RawIntensity = FMath::Lerp(
                Nearest->RawIntensity,
                Candidate.Intensity,
                BlendFactor(Candidate.Intensity > Nearest->RawIntensity
                    ? kIntensityAttackPerSecond
                    : kIntensityReleasePerSecond));
        }
        else if (PersistentBreakingSites.Num() < kMaxPersistentSites)
        {
            FPersistentBreakingSite& Spawned =
                PersistentBreakingSites.AddDefaulted_GetRef();
            Spawned.Smoothed = Candidate;
            // Golden-angle serial keeps every site's organic phases distinct
            // and stable for its whole life; the retired rank index reshuffled
            // them whenever two sites swapped intensity order. Reset with the
            // grid so authored captures stay deterministic.
            Spawned.Smoothed.ShapeSeed =
                (BreakingSiteShapeSeedSerial++ % 4096) * 2.399963f;
            Spawned.RawIntensity = Candidate.Intensity;
            Spawned.Envelope = 0.0f;
            Spawned.bMatchedThisRefresh = true;
        }
    }

    // Spawn/despawn hysteresis: a one-refresh detection blip barely rises out
    // of zero, and a site whose hydraulic vanishes releases over ~half a
    // second instead of deleting a rendered crest in one frame.
    for (int32 SiteIndex = PersistentBreakingSites.Num() - 1;
         SiteIndex >= 0;
         --SiteIndex)
    {
        FPersistentBreakingSite& Persistent = PersistentBreakingSites[SiteIndex];
        if (Persistent.bMatchedThisRefresh)
        {
            Persistent.Envelope = FMath::Lerp(
                Persistent.Envelope, 1.0f, BlendFactor(kEnvelopeAttackPerSecond));
        }
        else
        {
            Persistent.Envelope = FMath::Lerp(
                Persistent.Envelope, 0.0f, BlendFactor(kEnvelopeReleasePerSecond));
            Persistent.RawIntensity = FMath::Lerp(
                Persistent.RawIntensity,
                0.0f,
                BlendFactor(kIntensityReleasePerSecond));
            if (Persistent.Envelope < 0.02f)
            {
                PersistentBreakingSites.RemoveAt(SiteIndex);
                continue;
            }
        }
        Persistent.Smoothed.Intensity =
            Persistent.RawIntensity * Persistent.Envelope;
    }

    // Strongest first, with a stable sort so equal-intensity neighbours keep
    // their order instead of trading ranks on float noise.
    PersistentBreakingSites.StableSort(
        [](const FPersistentBreakingSite& A, const FPersistentBreakingSite& B)
        {
            return A.Smoothed.Intensity > B.Smoothed.Intensity;
        });

    // The pocket/boil budget follows the strongest sites, but membership
    // changes ease through the weight instead of toggling a 30 cm carve in
    // one refresh. During a handoff two sites briefly share partial weight;
    // the combined displacement clamps in the carve pass still bound it.
    BreakingSites.Reset(PersistentBreakingSites.Num());
    for (int32 SiteIndex = 0; SiteIndex < PersistentBreakingSites.Num();
         ++SiteIndex)
    {
        FPersistentBreakingSite& Persistent = PersistentBreakingSites[SiteIndex];
        const float WeightTarget =
            (bSpatialBreakingReview || SiteIndex < kMaximumBreakingPresentationSites) &&
                Persistent.Smoothed.Intensity > 0.02f
            ? 1.0f
            : 0.0f;
        Persistent.PresentationWeight = FMath::Lerp(
            Persistent.PresentationWeight,
            WeightTarget,
            BlendFactor(WeightTarget > Persistent.PresentationWeight
                ? kPresentationWeightAttackPerSecond
                : kPresentationWeightReleasePerSecond));
        FBreakingSite& Published = BreakingSites.Add_GetRef(Persistent.Smoothed);
        Published.HydraulicCrestDimensionsMeters.X *= Persistent.Envelope;
        Published.HydraulicSpillingFraction *= Persistent.Envelope;
        Published.PresentationWeight = Persistent.PresentationWeight;
        Published.PersistenceWeight = Persistent.Envelope;
    }
}

void ARaftSimWaterSurfaceActor::ReleaseMacroHistory()
{
    if (!MacroHistory)return;
    auto History=MacroHistory;
    ENQUEUE_RENDER_COMMAND(RaftSimMacroHistoryRelease)([History](FRHICommandListImmediate&)
    {
        UE_LOG(LogTemp,Display,TEXT("Macro water history: %llu rendered-frame snapshots"),History->GetCapturedFrames());
        History->Stop();
    });
    MacroHistory.Reset();
}

void ARaftSimWaterSurfaceActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    FWorldDelegates::LevelAddedToWorld.RemoveAll(this);
    if(FoamClockRefreshes){UE_LOG(LogTemp,Display,TEXT("Foam committed-water clock: origin=%.9f water=%.9f target=%.9f refreshes=%llu holds=%llu initializations=%llu; no wall-time fallback"),
        FoamWaterClock.Origin,FoamWaterClock.Last,FoamWaterClock.TargetSeconds(),FoamClockRefreshes,FoamClockHolds,FoamClockInitializations);}
    if (WaterAdapter) WaterAdapter->ClearRaftSupportCarrierSampler(this);
    CarrierGroundSources.Reset();
    ReleaseMacroHistory();
    Super::EndPlay(EndPlayReason);
}

void ARaftSimWaterSurfaceActor::UploadMacroSurface(const TArray<FLinearColor>& Colors,bool bResetHistory)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimWater_UploadMacroSurface);
    const int32 AtlasHeight=GridLateralN*4+(bStatefulCrestReview ? 2 : 0);
    if (!MacroSurfaceTexture)
    {
        MacroSurfaceTexture=NewObject<UTextureRenderTarget2D>(this);
        MacroSurfaceTexture->ClearColor=FLinearColor::Transparent;
        MacroSurfaceTexture->InitCustomFormat(GridStationN,AtlasHeight,PF_A32B32G32R32F,true);
        MacroSurfaceTexture->UpdateResourceImmediate(true);
        if (bStatefulMotionReview)
        {
            PreviousMacroSurfaceTexture=NewObject<UTextureRenderTarget2D>(this);
            PreviousMacroSurfaceTexture->ClearColor=FLinearColor::Transparent;
            PreviousMacroSurfaceTexture->InitCustomFormat(GridStationN,AtlasHeight,PF_A32B32G32R32F,true);
            PreviousMacroSurfaceTexture->UpdateResourceImmediate(true);
            MacroHistory=MakeShared<FRaftSimWaterTextureHistory,ESPMode::ThreadSafe>();
            auto History=MacroHistory;
            auto* Current=MacroSurfaceTexture->GameThread_GetRenderTargetResource();
            auto* Previous=PreviousMacroSurfaceTexture->GameThread_GetRenderTargetResource();
            ENQUEUE_RENDER_COMMAND(RaftSimMacroHistoryStart)([History,Current,Previous](FRHICommandListImmediate& Cmd)
            {
                const bool bStarted=History->Start(Cmd,Current->GetRenderTargetTexture(),Previous->GetRenderTargetTexture());
                checkf(bStarted,TEXT("Macro history requires distinct matching textures"));
            });
        }
        UE_LOG(LogTemp,Display,TEXT("GPU macro carrier: atlas=%dx%d source_vertices=%d dynamic_bounds=%d; fine mesh uploads only on lattice changes"),
            GridStationN,AtlasHeight,Vertices.Num(),SurfaceMesh->IsA<URaftSimWaterCarrierMeshComponent>() ? 1 : 0);
    }
    const int32 Count=Vertices.Num();TArray<FVector4f> Data;Data.SetNumZeroed(GridStationN*AtlasHeight);
    const bool bCrestData=bStatefulCrestReview && MacroCrestDisplacementCm.Num()==Count && MacroCrestShoreWeights.Num()==Count;
    FBox HydraulicBounds(ForceInit);
    const FTransform Transform=GetActorTransform();
    for (int32 I=0;I<Count;++I)
    {
        HydraulicBounds+=Vertices[I];
        const FVector P=Transform.TransformPosition(Vertices[I]);
        const FVector N=Transform.TransformVectorNoScale(Normals[I]).GetSafeNormal();
        Data[I]=FVector4f(P.X,P.Y,P.Z,bCrestData ? MacroCrestDisplacementCm[I] : 0);
        Data[Count+I]=FVector4f(N.X,N.Y,N.Z,bCrestData ? MacroCrestShoreWeights[I] : 0);
        Data[Count*2+I]=FVector4f(Colors[I].R,Colors[I].G,Colors[I].B,Colors[I].A);
        Data[Count*3+I]=FVector4f(FlowVelocityMetersPerSecond[I].X,FlowVelocityMetersPerSecond[I].Y,
            BoatWakePresentationData[I].X,BoatWakePresentationData[I].Y);
    }
    float CrestMarginCm=0;
    if (bCrestData)
    {
        Data[Count*4]=FVector4f(RiverCoordinatesM[0].X,RiverCoordinatesM[0].Y,ResolvedVertexSpacingMeters,MacroCrestSites.Num()/2);
        Data[Count*4+GridStationN]=FVector4f(ResolvedPresentationHydraulicReliefScale,0,0,0);
        for (int32 I=0;I<MacroCrestSites.Num()/2;++I)
        {
            Data[Count*4+I+1]=MacroCrestSites[I*2];
            Data[Count*4+GridStationN+I+1]=MacroCrestSites[I*2+1];
            CrestMarginCm=FMath::Max(CrestMarginCm,2*MacroCrestSites[I*2].Z*FMath::Abs(ResolvedPresentationHydraulicReliefScale)*100);
        }
    }
    if (auto* Carrier=Cast<URaftSimWaterCarrierMeshComponent>(SurfaceMesh))
        Carrier->SetHydraulicBounds(HydraulicBounds.ExpandBy(FVector(0,0,100+CrestMarginCm)));
    auto* Target=MacroSurfaceTexture->GameThread_GetRenderTargetResource();
    const FIntPoint Size(GridStationN,AtlasHeight);
    auto History=MacroHistory;
    ENQUEUE_RENDER_COMMAND(RaftSimMacroSurfaceUpload)([Target,Size,Data=MoveTemp(Data),History,bResetHistory](FRHICommandListImmediate& Cmd)
    {
        auto Texture=Target->GetRenderTargetTexture();
        Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::Unknown,ERHIAccess::CopyDest));
        Cmd.UpdateTexture2D(Texture,0,FUpdateTextureRegion2D(0,0,0,0,Size.X,Size.Y),Size.X*sizeof(FVector4f),reinterpret_cast<const uint8*>(Data.GetData()));
        Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
        if (History && bResetHistory)History->ResetHistory(Cmd);
    });
}

void ARaftSimWaterSurfaceActor::UpdateSurfaceCarrierMesh(bool bCreate,const TArray<FLinearColor>& Colors)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimWater_UpdateSurfaceCarrierMesh);
    const TArray<FVector2D> EmptyUVs;
    // Source topology/refinement remains in solver station/lateral space.
    // A reflected geographic world changes front-face winding only on upload.
    TArray<int32> ReflectedTriangles;
    const auto WorldWinding = [&](const TArray<int32>& Source) -> const TArray<int32>&
    {
        if (!WaterAdapter || WaterAdapter->GetRiverWorldYSign() > 0) return Source;
        ReflectedTriangles=Source;
        for (int32 I=0;I+2<ReflectedTriangles.Num();I+=3) Swap(ReflectedTriangles[I+1],ReflectedTriangles[I+2]);
        return ReflectedTriangles;
    };
    if (!bStatefulDetailGeometryReview && !bPlayableCrestRefinement)
    {
        if (bCreate)SurfaceMesh->CreateMeshSection_LinearColor(0,Vertices,WorldWinding(Triangles),Normals,UVs,
            FlowVelocityMetersPerSecond,BoatWakePresentationData,EmptyUVs,Colors,Tangents,false);
        else SurfaceMesh->UpdateMeshSection_LinearColor(0,Vertices,Normals,UVs,
            FlowVelocityMetersPerSecond,BoatWakePresentationData,EmptyUVs,Colors,Tangents,false);
        return;
    }
    const bool bRebuild=DetailRefinement.SourceVertexCount!=Vertices.Num() || DetailRefinementOrigin!=RiverCoordinatesM[0];
    if (bStatefulGPUCarrierReview)
    {
        UploadMacroSurface(Colors,bCreate || bRebuild);
        if (!bCreate && !bRebuild)return; // Fine mesh stays immutable between lattice shifts.
    }
    if (bRebuild)
    {
        const int32 Levels=bPlayableCrestRefinement ||
            (bStatefulCrestReview && FParse::Param(FCommandLine::Get(),TEXT("RaftSimFineDetailReview"))) ? 3 : 2;
        const FBox2D RefinementWindow = bPlayableCrestRefinement
            ? FBox2D(FVector2D(-18,-18),FVector2D(30,18))
            : FBox2D(FVector2D(-32,-32),FVector2D(32,32));
        // Third-level detail covers the steep settled crests, not the full
        // bounding bank rectangle. Red/green stitching remains conforming.
        const FBox2D FinestWindow(FVector2D(4,-8),FVector2D(17,12));
        if (!DetailRefinement.Build(RiverCoordinatesM,Triangles,RefinementWindow,Levels,
            bPlayableCrestRefinement ? &FinestWindow : nullptr))
        {
            UE_LOG(LogTemp,Error,TEXT("Stateful detail geometry rejected invalid source mesh"));return;
        }
        DetailRefinementOrigin=RiverCoordinatesM[0];
        PlayableCrestCorrections.Reset();
        DetailRefinement.Expand(RiverCoordinatesM,RefinedRiverCoordinates);
        if (bStatefulGPUCarrierReview)
        {
            TArray<FVector2D> GridCoordinates;GridCoordinates.SetNumUninitialized(Vertices.Num());
            for (int32 I=0;I<Vertices.Num();++I)GridCoordinates[I]=FVector2D(I%GridStationN,I/GridStationN);
            DetailRefinement.Expand(GridCoordinates,RefinedMacroCoordinates);
        }
        UE_LOG(LogTemp,Display,TEXT("Stateful detail geometry: source_vertices=%d render_vertices=%d render_triangles=%d; stitched %.4fm crux patch, one section, no added hydraulic samples"),
            Vertices.Num(),Vertices.Num()+DetailRefinement.MidpointParents.Num(),DetailRefinement.Triangles.Num()/3,
            ResolvedVertexSpacingMeters/(1<<Levels));
    }
    DetailRefinement.Expand(Vertices,RefinedVertices);DetailRefinement.Expand(Normals,RefinedNormals);
    DetailRefinement.Expand(UVs,RefinedUVs);DetailRefinement.Expand(FlowVelocityMetersPerSecond,RefinedFlow);
    DetailRefinement.Expand(BoatWakePresentationData,RefinedWake);DetailRefinement.Expand(Colors,RefinedColors);
    RefinedTangents.SetNumUninitialized(RefinedVertices.Num());
    for (int32 I=0;I<Tangents.Num();++I)RefinedTangents[I]=Tangents[I];
    for (int32 I=0;I<DetailRefinement.MidpointParents.Num();++I)
    {
        const FIntPoint P=DetailRefinement.MidpointParents[I];
        RefinedTangents[Vertices.Num()+I]=FProcMeshTangent(
            (RefinedTangents[P.X].TangentX+RefinedTangents[P.Y].TangentX).GetSafeNormal(),RefinedTangents[P.X].bFlipTangentY);
    }
    for (FVector& N:RefinedNormals)N=N.GetSafeNormal();
    if (bPlayableCrestRefinement && MacroCrestDisplacementCm.Num()==Vertices.Num())
    {
        TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites;
        for (int32 I=0; I+1<MacroCrestSites.Num(); I+=2)
        {
            const auto& G=MacroCrestSites[I]; const auto& P=MacroCrestSites[I+1];
            auto& S=Sites.AddDefaulted_GetRef();
            S.RiverCoordinatesMeters=FVector2D(G.X,G.Y);
            S.PhysicalCrestHeightMeters=G.Z; S.PhysicalCrestLengthMeters=G.W;
            S.Intensity=P.X; S.SpillingFraction=P.Y; S.bLocalEnvelopeCap=P.Z!=0;
            S.FlowDirection=RaftSimWaterFlowFrame::FromAngle(P.W);
        }
        // Exact input comparisons, not a quantized hash or a tolerance. A
        // changed physical profile/shore immediately invalidates the cache.
        const bool bRecomputeCrest=PlayableCrestCorrections.Num()!=RefinedVertices.Num() ||
            CachedPlayableCrestSites!=MacroCrestSites || CachedPlayableCoarseCrest!=MacroCrestDisplacementCm ||
            CachedPlayableShore!=MacroCrestShoreWeights;
        RaftSimPlayableCrestMesh::Reconstruct(DetailRefinement,RefinedRiverCoordinates,
            MacroCrestDisplacementCm,MacroCrestShoreWeights,Sites,BreakingCrestLiftMeters,
            ResolvedVertexSpacingMeters,ResolvedPresentationHydraulicReliefScale,
            WaterAdapter ? WaterAdapter->GetRiverWorldYSign() : 1.0f,RefinedVertices,RefinedNormals,
            &PlayableCrestCorrections,bRecomputeCrest);
        if(bRecomputeCrest)
        {
            CachedPlayableCrestSites=MacroCrestSites;CachedPlayableCoarseCrest=MacroCrestDisplacementCm;
            CachedPlayableShore=MacroCrestShoreWeights;
        }
        else if(++PlayableCrestCacheHits==60)
            UE_LOG(LogTemp,Display,TEXT("Playable crest cache: 60 exact-input reuses; no height approximation"));
        for(int32 I=0;I<RefinedTangents.Num();++I)
        {
            const FVector N=RefinedNormals[I];
            auto& T=RefinedTangents[I].TangentX;
            T=(T-N*FVector::DotProduct(T,N)).GetSafeNormal();
        }
        FString AuditPath;
        if (GetWorld()->GetTimeSeconds()>=10 &&
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestSamplingAudit="),AuditPath) &&
            !FPaths::FileExists(AuditPath+TEXT(".mesh.json")))
        {
            TArray<float> BaseZ,ExpandedBaseZ,Shore;
            for(int32 I=0;I<Vertices.Num();++I) BaseZ.Add(Vertices[I].Z-MacroCrestDisplacementCm[I]);
            DetailRefinement.Expand(BaseZ,ExpandedBaseZ);
            DetailRefinement.Expand(MacroCrestShoreWeights,Shore);
            double MaxError=0,MaxSourceChange=0;
            int32 Samples=0;
            for(int32 I=0;I<Vertices.Num();++I)
                MaxSourceChange=FMath::Max(MaxSourceChange,FVector::Distance(Vertices[I],RefinedVertices[I]));
            for(int32 T=0;T<DetailRefinement.Triangles.Num();T+=3)
            {
                const int32 A=DetailRefinement.Triangles[T],B=DetailRefinement.Triangles[T+1],C=DetailRefinement.Triangles[T+2];
                const FVector2D P=(RefinedRiverCoordinates[A]+RefinedRiverCoordinates[B]+RefinedRiverCoordinates[C])/3;
                const double Weight=(Shore[A]+Shore[B]+Shore[C])/3;
                if(Weight<=0)continue;
                const double Expected=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(
                    P,Sites,BreakingCrestLiftMeters,ResolvedVertexSpacingMeters)*ResolvedPresentationHydraulicReliefScale*Weight;
                const double Submitted=(RefinedVertices[A].Z+RefinedVertices[B].Z+RefinedVertices[C].Z-
                    ExpandedBaseZ[A]-ExpandedBaseZ[B]-ExpandedBaseZ[C])/300;
                MaxError=FMath::Max(MaxError,FMath::Abs(Expected-Submitted));++Samples;
            }
            auto Report=MakeShared<FJsonObject>();
            Report->SetStringField(TEXT("map"),GetWorld()->GetMapName());
            Report->SetStringField(TEXT("scope"),TEXT("Actual CPU carrier crest component at triangle centroids; other base relief excluded; unchanged hydraulic samples."));
            Report->SetNumberField(TEXT("source_vertices"),Vertices.Num());
            Report->SetNumberField(TEXT("submitted_vertices"),RefinedVertices.Num());
            Report->SetNumberField(TEXT("submitted_triangles"),DetailRefinement.Triangles.Num()/3);
            Report->SetNumberField(TEXT("maximum_source_vertex_change_cm"),MaxSourceChange);
            Report->SetNumberField(TEXT("maximum_centroid_crest_error_m"),MaxError);
            Report->SetNumberField(TEXT("sample_count"),Samples);
            FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
            FFileHelper::SaveStringToFile(Json,*(AuditPath+TEXT(".mesh.json")));
            UE_LOG(LogTemp,Display,TEXT("Playable crest mesh: vertices=%d triangles=%d centroid_error_m=%.7f source_change_cm=%.7f"),
                RefinedVertices.Num(),DetailRefinement.Triangles.Num()/3,MaxError,MaxSourceChange);
        }
    }
    if (bCreate || bRebuild)SurfaceMesh->CreateMeshSection_LinearColor(0,RefinedVertices,WorldWinding(DetailRefinement.Triangles),
        RefinedNormals,RefinedUVs,RefinedFlow,RefinedWake,bStatefulGPUCarrierReview ? RefinedMacroCoordinates : EmptyUVs,RefinedColors,RefinedTangents,false);
    else SurfaceMesh->UpdateMeshSection_LinearColor(0,RefinedVertices,RefinedNormals,
        RefinedUVs,RefinedFlow,RefinedWake,EmptyUVs,RefinedColors,RefinedTangents,false);
}

void ARaftSimWaterSurfaceActor::RefreshSurface()
{
    CSV_SCOPED_TIMING_STAT(RaftSimSurface,Refresh);
    FWaterSurfacePerf Perf(TEXT("refresh"));
    const bool bCartesianFlow = WaterAdapter && WaterAdapter->HasCartesianWaterCoordinates();
    FRaftSimCommittedWaterClock NextFoamClock=FoamWaterClock;
    const bool bPreviousFoamUsable=bFoamFieldValid && bCartesianFlow==bFoamUsesCommittedClock;
    double FoamCommittedDelta=0;
    float FoamDeltaSeconds=0;
    if(bCartesianFlow)
    {
        const double WaterSeconds=WaterAdapter->GetCommittedStepSeconds();
        const bool Valid=WaterAdapter->GetStatus()!=ERaftSimWaterRuntimeStatus::Faulted &&
            (bPreviousFoamUsable ? NextFoamClock.Observe(WaterSeconds,FoamCommittedDelta) : NextFoamClock.Initialize(WaterSeconds));
        FoamDeltaSeconds=float(FoamCommittedDelta);
        if(!Valid || !FMath::IsFinite(FoamDeltaSeconds) || (FoamCommittedDelta>0 && FoamDeltaSeconds==0))
        {UE_LOG(LogTemp,Error,TEXT("Foam committed-water clock invalid/regressed; refusing unpaired evolution"));return;}
        // Commit this candidate only when the new foam field is published.
        // A newly initialized field has no historical foam duration to replay.
    }
    const auto FlowDirectionFor = [bCartesianFlow](const FRaftSimWaterSample& Sample)
    {
        // Refresh samples the field API, whose velocity is already hydraulic
        // XY. Applying the world north reflection here would reverse it twice.
        return bCartesianFlow ? RaftSimWaterFlowFrame::Direction(FVector2D(
            Sample.VelocityMetersPerSecond.X,Sample.VelocityMetersPerSecond.Y))
            : FVector2D(1.,0.);
    };
    const double RefreshStartSeconds = FPlatformTime::Seconds();
    const bool bCrestLocalizedFoam = bSharedBreakingReliefEnabled &&
        CVarRaftSimChilkoCrestFoam.GetValueOnGameThread() != 0;
    bool bDirectionalFoamSource = bCartesianFlow && bSingleLiveWaterSurfaceEnabled &&
        GetWorld() && GetWorld()->GetMapName().Contains(TEXT("L_SouthForkAmerican_FullReach"));
    FString FoamSourceAuditPath;
#if !UE_BUILD_SHIPPING
    static const bool bLegacyGenericFoamSource=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLegacyGenericFoamSource"));
    bDirectionalFoamSource=bDirectionalFoamSource && !bLegacyGenericFoamSource;
    if (GetWorld() && GetWorld()->GetTimeSeconds()>=10.f)
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimFoamSourceAudit="),FoamSourceAuditPath);
    if (!FoamSourceAuditPath.IsEmpty() && FPaths::FileExists(FoamSourceAuditPath))FoamSourceAuditPath.Reset();
#endif
    TArray<FVector4f> FoamSourceAudit;
    if (!FoamSourceAuditPath.IsEmpty())FoamSourceAudit.SetNumZeroed(Vertices.Num());
    const float PreviousGridCenterStationM = CurvedGridCenterStationM;
    const float PreviousGridCenterNorthM = CartesianGridCenterNorthM;
    RecenterCurvedGrid();
    const bool bGridRecentredThisRefresh = !FMath::IsNearlyEqual(
        PreviousGridCenterStationM,
        CurvedGridCenterStationM,
        KINDA_SMALL_NUMBER) || !FMath::IsNearlyEqual(PreviousGridCenterNorthM, CartesianGridCenterNorthM, KINDA_SMALL_NUMBER);
    if (bGridRecentredThisRefresh)
    {
        LogWaterRenderStateEvent(GetWorld(), TEXT("grid_recentre"));
    }
    FBox2D LiveCropBounds(ForceInit);
    const bool bHasLiveCropBounds = bCartesianFlow && WaterAdapter->GetLiveWaterFieldBoundsM(LiveCropBounds);
    const auto CropAuthorityFor = [this, bCartesianFlow, bHasLiveCropBounds, LiveCropBounds](int32 Index)
    {
        if (bCartesianFlow)
            return bHasLiveCropBounds ? RaftSimWaterFlowFrame::CropAuthority(RiverCoordinatesM[Index], LiveCropBounds, 30.f) : 0.f;
        const int32 X = Index % GridStationN;
        return StationSolverCropAuthority.IsValidIndex(X) ? StationSolverCropAuthority[X] : 1.f;
    };
    TArray<uint8> WetVertexMask;
    WetVertexMask.Init(0, Vertices.Num());
    TArray<uint8> LiveSolverWetVertexMask;
    LiveSolverWetVertexMask.Init(0, Vertices.Num());
    // Which vertices the live solver actually answered for this refresh
    // (wet OR dry), and the feathered presence contribution of baseline-only
    // shoreline water inside the crop's authority handover band.
    TArray<uint8> SolverSampledVertexMask;
    SolverSampledVertexMask.Init(0, Vertices.Num());
    TArray<float> FeatheredBaselineWet;
    FeatheredBaselineWet.SetNumZeroed(Vertices.Num());
    TArray<FRaftSimWaterSample> WaterSamples;
    WaterSamples.SetNum(Vertices.Num());
    if (bCartesianFlow) CartesianShoreAvailable.Init(0, Vertices.Num());
    TArray<float> PresentationSurfaceHeightMeters;
    PresentationSurfaceHeightMeters.Init(0.0f, Vertices.Num());
    TArray<float> HydraulicReliefMeters;
    HydraulicReliefMeters.Init(0.0f, Vertices.Num());
    TArray<float> FroudeField;
    FroudeField.Init(0.0f, Vertices.Num());
    TArray<float> SourceFoam;
    SourceFoam.Init(0.0f, Vertices.Num());

    // Legacy non-Cartesian reviews retain their separate clock. The normal
    // Cartesian field uses only the committed-water duration prepared above.
    if(!bCartesianFlow)
    {
        const double NowRealSeconds=FPlatformTime::Seconds();
        FoamDeltaSeconds=bPreviousFoamUsable ? FMath::Clamp(float(NowRealSeconds-LastRefreshRealSeconds),0.f,.5f) : 0.f;
        LastRefreshRealSeconds=NowRealSeconds;
    }

    // Sample the live field once per vertex. A separate presentation pass can
    // then compare same-lateral station neighbours without multiplying runtime
    // adapter queries or reaching outside the active cooked window.
    // Cells where the live solver says dry but the baseline says wet — the
    // handover disagreement set — request rendered-terrain probes so the
    // visual-submersion keep below can cover whole shallow shelves, not just
    // the outer bank rings.
    TArray<uint8> BaselineKeepProbeWanted;
    BaselineKeepProbeWanted.Init(0, Vertices.Num());
    const FTransform BaselineKeepTransform =
            SurfaceMesh ? SurfaceMesh->GetComponentTransform()
                        : GetActorTransform();
    // Two independent actual-state captures preserve every field/mask and
    // improve both timing orders. Qualify other scenes separately; retain
    // same-binary original lookup for performance and regression controls.
    static const bool bReferenceAtlasStencil=FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceAtlasStencil"));
    bool bCacheAtlasStencil=!bReferenceAtlasStencil && bCartesianFlow && GetWorld() &&
        GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach"));
    const auto SampleBaseline = [&](int32 Index,FRaftSimWaterSample& Out,FRaftSimRefreshBaselineSample* Cached)
    {
        const auto Query=[&](FRaftSimWaterSample& Value)
        { return WaterAdapter->SamplePresentationBaselineFieldAtRiverCoordinates(RiverCoordinatesM[Index],Value,bCacheAtlasStencil); };
        return Cached ? Cached->Read(Query,Out) : Query(Out);
    };
    const auto SampleVertex = [&](int32 Index,FRaftSimRefreshBaselineSample* Cached=nullptr)
    {
                const FVector& V = Vertices[Index];
                FRaftSimWaterSample& Sample = WaterSamples[Index];
                const bool bSampled = bUsesCurvedRiverCoordinates
                    ? WaterAdapter->SampleWaterFieldAtRiverCoordinates(
                        RiverCoordinatesM[Index], Sample)
                    : WaterAdapter->SampleWaterAtWorldPosition(
                        FVector(V.X, V.Y, 0.0f), Sample);
                // A valid live sample, including a dry one, is authoritative.
                // Only a coordinate outside the finite hydraulic crop may use
                // the full-reach render baseline. This keeps every physics and
                // wet/dry decision inside the live window solver-owned.
                bool bBaselineSampled =
                    !bSampled && bSingleLiveWaterSurfaceEnabled &&
                    bUsesCurvedRiverCoordinates &&
                    SampleBaseline(Index,Sample,Cached);
                SolverSampledVertexMask[Index] = bSampled ? 1 : 0;
                if (bCartesianFlow) CartesianShoreAvailable[Index] = bSampled || bBaselineSampled;
                LiveSolverWetVertexMask[Index] =
                    bSampled && Sample.bWet ? 1 : 0;
                if (bBaselineSampled && Sample.bWet)
                {
                    FeatheredBaselineWet[Index] = 1.0f;
                }
                // Authority handover feather: inside the crop a dry solver
                // verdict overrides the baseline, but near the crop's
                // travelling ends that flip made shoreline water pop in and
                // out keyed to the raft's approach. Where the previous
                // refresh's authority is still fading in, a solver-dry /
                // baseline-wet cell adopts the baseline sample as ordinary
                // water and fades by presence instead.
                const float CropAuthority = CropAuthorityFor(Index);
                // Visual-submersion keep: the live solver's wetting is
                // coarser than the visible margin, so as the crop's
                // authority sweeps in with the raft its dry verdicts drained
                // baseline-wet bank bays in plain view ("the water suddenly
                // recedes from the shores for no reason", player recording
                // 2026-08-30) — an effect the old 5 mm static water used to
                // mask. Where the rendered-terrain probe proves the water
                // plane genuinely covers the visible ground (>= the film
                // cull's release depth, so the two verdicts cannot fight),
                // the baseline keeps presenting at full strength regardless
                // of crop authority. Physics stays solver-owned; unprobed
                // cells (mid-channel boulder cutouts) keep solver authority.
                bool bVisuallySubmerged = false;
                if (bSampled && !Sample.bWet &&
                    VisualBankProbeState.IsValidIndex(Index))
                {
                    if (VisualBankProbeState[Index] == 1)
                    {
                        constexpr float kBaselineKeepDepthCm = 9.0f;
                        const float WaterWorldZCm = static_cast<float>(
                            BaselineKeepTransform
                                .TransformPosition(Vertices[Index]).Z);
                        bVisuallySubmerged =
                            WaterWorldZCm - VisualBankTerrainZCm[Index] >=
                            kBaselineKeepDepthCm;
                    }
                    else if (VisualBankProbeState[Index] == 0)
                    {
                        BaselineKeepProbeWanted[Index] = 1;
                    }
                }
                if (bSampled && !Sample.bWet &&
                    (CropAuthority < 0.999f || bVisuallySubmerged) &&
                    bSingleLiveWaterSurfaceEnabled &&
                    bUsesCurvedRiverCoordinates)
                {
                    FRaftSimWaterSample BaselineSample;
                    if (SampleBaseline(Index,BaselineSample,Cached) &&
                        BaselineSample.bWet)
                    {
                        Sample = BaselineSample;
                        bBaselineSampled = true;
                        FeatheredBaselineWet[Index] = bVisuallySubmerged
                            ? 1.0f
                            : 1.0f - CropAuthority;
                    }
                }
                // The mirrored half of the handover contract: the keep above
                // stops solver-DRY verdicts from draining the stable baseline
                // shoreline, but solver-WET verdicts used to land instantly
                // at full strength with the solver's own level. The solver's
                // bank wetting is one coarse cell wider and centimetres
                // higher than the authored margin, so every pass of the crop
                // grew water visibly up flat bars and then drained it again
                // ("the shore is still changing with the water growing onto
                // the shore", player recording 2026-08-30 — ±0.5-1.5 m
                // waterline swings on a 1-4 s period tracking the raft).
                // Presentation therefore defers to the baseline in shallow
                // water: solver-wet where the baseline is dry presents dry
                // (bank bleed), and a shore level that agrees with the
                // baseline within a wave's height presents the baseline's
                // level, so the slow shore reference never sees a handover
                // step. Deep or strongly deviating water — real floods,
                // surges, rapids — keeps full solver authority, and physics
                // is untouched either way.
                if (bSampled && Sample.bWet &&
                    bSingleLiveWaterSurfaceEnabled &&
                    bUsesCurvedRiverCoordinates)
                {
                    constexpr float kShoreSolverBleedMaxDepthM = 0.35f;
                    constexpr float kShoreLevelAgreementM = 0.08f;
                    if (Sample.DepthMeters < 0.45f)
                    {
                        // A measured, bed-aligned margin must follow the live
                        // wetting front. The old baseline veto truncated even
                        // correctly aligned water at 35 cm depth, leaving an
                        // exposed sheet edge above its bank. Unknown or
                        // mismatched terrain retains the compatibility rule.
                        const bool bMeasuredBedAligned =
                            VisualBankProbeState.IsValidIndex(Index) &&
                            VisualBankProbeState[Index] == 1 &&
                            FMath::IsFinite(Sample.BedHeightMeters) &&
                            FMath::Abs(Sample.BedHeightMeters * kSurfCmPerM -
                                VisualBankTerrainZCm[Index]) <= 10.0f;
                        if (VisualBankProbeState.IsValidIndex(Index) &&
                            VisualBankProbeState[Index] == 0)
                        {
                            BaselineKeepProbeWanted[Index] = 1;
                        }
                        FRaftSimWaterSample BaselineSample;
                        const bool bBaselineWet = SampleBaseline(Index,BaselineSample,Cached) &&
                            BaselineSample.bWet;
                        if (!bMeasuredBedAligned && !bBaselineWet &&
                            Sample.DepthMeters < kShoreSolverBleedMaxDepthM)
                        {
                            Sample.bWet = false;
                            // Presence and foam/advection continuity key on
                            // the solver-wet mask; a suppressed bank-bleed
                            // cell must not present through them either.
                            LiveSolverWetVertexMask[Index] = 0;
                        }
                        else if (!bMeasuredBedAligned && bBaselineWet &&
                                 FMath::Abs(Sample.SurfaceHeightMeters -
                                     BaselineSample.SurfaceHeightMeters) <
                                     kShoreLevelAgreementM)
                        {
                            Sample.SurfaceHeightMeters =
                                BaselineSample.SurfaceHeightMeters;
                        }
                    }
                }
                WetVertexMask[Index] =
                    (bSampled || bBaselineSampled) && Sample.bWet ? 1 : 0;
                if (WetVertexMask[Index] != 0)
                {
                    PresentationSurfaceHeightMeters[Index] =
                        Sample.SurfaceHeightMeters;
                }
    };
    const auto SampleLiveVertices = [&](bool bConcurrent)
    {
        CSV_SCOPED_TIMING_STAT(RaftSimSurface,SourceSamples);
        if (!WaterAdapter) return;
        // Cartesian samplers read a stable live solver and immutable atlas.
        // Each task writes only its own element; join before any solver step,
        // probe, field resize, or following presentation pass. Legacy world /
        // route queries retain their original serial execution and ordering.
        if (bConcurrent) ParallelFor(TEXT("RaftSimCartesianSourceSamples"),Vertices.Num(),256,
            [&](int32 I) { SampleVertex(I); },EParallelForFlags::Unbalanced);
        else for (int32 I=0; I<Vertices.Num(); ++I) SampleVertex(I);
    };
    const bool bConcurrentSource=bCartesianFlow && bUsesCurvedRiverCoordinates;
    // Two independent actual-state captures: all 16 alternating-order pairs
    // preserve every field/mask and reduce this stage's cost. Whole-frame
    // timings remain mixed and still fail the 30 FPS gate. Qualify other
    // scenes separately; retain the original schedule for regression controls.
    static const bool bSeparateSource=FParse::Param(FCommandLine::Get(),TEXT("RaftSimSeparateSourceHandover"));
    const bool bFusedSource=bConcurrentSource && bSingleLiveWaterSurfaceEnabled && !bSeparateSource &&
        GetWorld() && GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach"));
    if (!bFusedSource) SampleLiveVertices(bConcurrentSource);

    // Recompute the crop's per-station wet/dry authority for the next
    // refresh: full solver ownership deep inside the covered stations,
    // feathering to baseline ownership over ~30 m at the crop's travelling
    // ends. Two sweeps give distance-to-uncovered in station steps. Cartesian
    // fields instead use exact current live bounds on all four sides above.
    if (!bCartesianFlow)
    {
        if (StationSolverCropAuthority.Num() != GridStationN)
        {
            StationSolverCropAuthority.SetNumZeroed(GridStationN);
        }
        TArray<uint8> StationCovered;
        StationCovered.Init(0, GridStationN);
        for (int32 Index = 0; Index < SolverSampledVertexMask.Num(); ++Index)
        {
            if (SolverSampledVertexMask[Index] != 0)
            {
                StationCovered[Index % GridStationN] = 1;
            }
        }
        constexpr float kAuthorityFeatherMeters = 30.0f;
        const float SafeSpacingMeters = FMath::Max(
            ResolvedVertexSpacingMeters, KINDA_SMALL_NUMBER);
        TArray<float> DistanceSteps;
        DistanceSteps.Init(static_cast<float>(GridStationN), GridStationN);
        for (int32 X = 0; X < GridStationN; ++X)
        {
            if (StationCovered[X] == 0)
            {
                DistanceSteps[X] = 0.0f;
            }
            else if (X > 0)
            {
                DistanceSteps[X] = FMath::Min(
                    DistanceSteps[X], DistanceSteps[X - 1] + 1.0f);
            }
        }
        for (int32 X = GridStationN - 2; X >= 0; --X)
        {
            DistanceSteps[X] = FMath::Min(
                DistanceSteps[X], DistanceSteps[X + 1] + 1.0f);
        }
        for (int32 X = 0; X < GridStationN; ++X)
        {
            StationSolverCropAuthority[X] = FMath::Clamp(
                DistanceSteps[X] * SafeSpacingMeters / kAuthorityFeatherMeters,
                0.0f,
                1.0f);
        }
    }

    // Blend presentation values across the SAME current-frame authority band.
    // Previously only wet presence was feathered: surface height, depth and
    // velocity jumped directly from the full-reach baseline to the live crop.
    // At a grazing camera angle that step appeared as one horizontal reflection
    // bar moving with the raft. This modifies the local render samples only;
    // the adapter's solver field, force sampling and wet/dry authority remain
    // untouched.
    const auto BlendSourceVertex = [&](int32 Index,FRaftSimRefreshBaselineSample* Cached=nullptr)
    {
            if (SolverSampledVertexMask[Index] == 0 ||
                WetVertexMask[Index] == 0)
            {
                return;
            }
            const float Authority = CropAuthorityFor(Index);
            if (Authority >= 0.999f)
            {
                return;
            }
            FRaftSimWaterSample BaselineSample;
            if (!SampleBaseline(Index,BaselineSample,Cached) ||
                !BaselineSample.bWet)
            {
                return;
            }
            const float Blend = Authority * Authority *
                (3.0f - 2.0f * Authority);
            FRaftSimWaterSample& Sample = WaterSamples[Index];
            Sample.SurfaceHeightMeters = FMath::Lerp(
                BaselineSample.SurfaceHeightMeters,
                Sample.SurfaceHeightMeters,
                Blend);
            Sample.DepthMeters = FMath::Max(
                FMath::Lerp(BaselineSample.DepthMeters, Sample.DepthMeters, Blend),
                0.0f);
            Sample.BedHeightMeters =
                Sample.SurfaceHeightMeters - Sample.DepthMeters;
            Sample.VelocityMetersPerSecond = FMath::Lerp(
                BaselineSample.VelocityMetersPerSecond,
                Sample.VelocityMetersPerSecond,
                Blend);
            PresentationSurfaceHeightMeters[Index] =
                Sample.SurfaceHeightMeters;
    };
    const auto BlendSourceVertices = [&](bool bConcurrent,bool bAlreadyBlended=false)
    {
        CSV_SCOPED_TIMING_STAT(RaftSimSurface,SourceHandover);
        if (bAlreadyBlended || !bSingleLiveWaterSurfaceEnabled || !bUsesCurvedRiverCoordinates || !WaterAdapter) return;
        if (bConcurrent) ParallelFor(TEXT("RaftSimCartesianSourceHandover"),WaterSamples.Num(),256,
            [&](int32 I) { BlendSourceVertex(I); },EParallelForFlags::Unbalanced);
        else for (int32 I=0; I<WaterSamples.Num(); ++I) BlendSourceVertex(I);
    };
    const auto SampleCombinedVertices = [&]()
    {
        // Both passes depend only on this vertex and the same immutable source;
        // Cartesian crop authority does not depend on the intervening legacy
        // station sweep. Join before any solver/probe/mesh update. This scope
        // includes sampling AND handover; the separate handover scope below
        // measures only its already-completed guard on the combined path.
        CSV_SCOPED_TIMING_STAT(RaftSimSurface,SourceSamples);
        ParallelFor(TEXT("RaftSimCartesianCombinedSource"),Vertices.Num(),256,[&](int32 I)
        {
            FRaftSimRefreshBaselineSample Cached;
            SampleVertex(I,&Cached);
            BlendSourceVertex(I,&Cached);
        },EParallelForFlags::Unbalanced);
    };
    if (bFusedSource)
    {
        SampleCombinedVertices();
        static bool bLogged=false;
        if (!bLogged)
        {
            UE_LOG(LogTemp,Display,TEXT("Within-refresh source/handover fusion active: one vertex-local baseline query; SourceSamples includes both passes, SourceHandover is the completed guard"));
            bLogged=true;
        }
    }
    BlendSourceVertices(bConcurrentSource,bFusedSource);

    // Opt-in actual-state equivalence audit, excluded from ordinary/timing runs.
    // Restore the parallel outputs after rerunning both passes from clean arrays.
    static const FString AtlasStencilAuditPath=[]()
    { FString P; FParse::Value(FCommandLine::Get(),TEXT("RaftSimAtlasStencilAudit="),P); return P; }();
    static const FString SourceAuditPath=[]()
    { FString P; FParse::Value(FCommandLine::Get(),TEXT("RaftSimWaterSourceAudit="),P); return P; }();
    const bool bAtlasStencilAudit=!AtlasStencilAuditPath.IsEmpty();
    const FString& SelectedSourceAuditPath=bAtlasStencilAudit ? AtlasStencilAuditPath : SourceAuditPath;
    static bool bSourceAuditWritten=false;
    if (!SelectedSourceAuditPath.IsEmpty() && !bSourceAuditWritten && bConcurrentSource &&
        GetWorld() && GetWorld()->GetTimeSeconds()>=10.)
    {
        bSourceAuditWritten=true;
        auto SavedSamples=WaterSamples;
        auto SavedWet=WetVertexMask, SavedLiveWet=LiveSolverWetVertexMask;
        auto SavedSampled=SolverSampledVertexMask, SavedAvailable=CartesianShoreAvailable;
        auto SavedProbeWanted=BaselineKeepProbeWanted;
        auto SavedFeather=FeatheredBaselineWet, SavedHeights=PresentationSurfaceHeightMeters;
        const bool SavedCacheAtlasStencil=bCacheAtlasStencil;
        const int32 Count=Vertices.Num();
        const auto ResetSourceOutputs=[&]()
        {
            WaterSamples.Init(FRaftSimWaterSample{},Count);
            WetVertexMask.Init(0,Count); LiveSolverWetVertexMask.Init(0,Count);
            SolverSampledVertexMask.Init(0,Count); CartesianShoreAvailable.Init(0,Count);
            BaselineKeepProbeWanted.Init(0,Count); FeatheredBaselineWet.Init(0.f,Count);
            PresentationSurfaceHeightMeters.Init(0.f,Count);
        };
        const auto MatchesSaved=[&]()
        {
            for (int32 I=0;I<Count;++I)
            {
                const auto& A=SavedSamples[I];const auto& B=WaterSamples[I];
                if (!(A.WorldPosition==B.WorldPosition && A.SurfaceHeightMeters==B.SurfaceHeightMeters &&
                    A.BedHeightMeters==B.BedHeightMeters && A.DepthMeters==B.DepthMeters &&
                    A.VelocityMetersPerSecond==B.VelocityMetersPerSecond && A.SurfaceNormal==B.SurfaceNormal && A.bWet==B.bWet)) return false;
            }
            return SavedWet==WetVertexMask && SavedLiveWet==LiveSolverWetVertexMask &&
                SavedSampled==SolverSampledVertexMask && SavedAvailable==CartesianShoreAvailable &&
                SavedProbeWanted==BaselineKeepProbeWanted && SavedFeather==FeatheredBaselineWet &&
                SavedHeights==PresentationSurfaceHeightMeters;
        };
        if(bAtlasStencilAudit)bCacheAtlasStencil=false;
        ResetSourceOutputs();
        SampleLiveVertices(false); BlendSourceVertices(false);
        int32 DifferentSamples=0;
        for (int32 I=0; I<Count; ++I)
        {
            const auto& A=SavedSamples[I]; const auto& B=WaterSamples[I];
            DifferentSamples += !(A.WorldPosition==B.WorldPosition && A.SurfaceHeightMeters==B.SurfaceHeightMeters &&
                A.BedHeightMeters==B.BedHeightMeters && A.DepthMeters==B.DepthMeters &&
                A.VelocityMetersPerSecond==B.VelocityMetersPerSecond && A.SurfaceNormal==B.SurfaceNormal && A.bWet==B.bWet);
        }
        const bool SameFields=SavedWet==WetVertexMask && SavedLiveWet==LiveSolverWetVertexMask &&
            SavedSampled==SolverSampledVertexMask && SavedAvailable==CartesianShoreAvailable &&
            SavedProbeWanted==BaselineKeepProbeWanted && SavedFeather==FeatheredBaselineWet &&
            SavedHeights==PresentationSurfaceHeightMeters;
        TArray<TSharedPtr<FJsonValue>> Pairs;
        bool AllPairsExact=true;
        if (bSingleLiveWaterSurfaceEnabled)
        {
            // Compare the TWO production parallel schedules on the same frozen
            // state, not a serial baseline against parallel work. Allocation /
            // reset and validation are outside both timed intervals. Fixed
            // alternating order; preserve every pair, including slower ones.
            for (int32 Pair=0;Pair<(bAtlasStencilAudit ? 64 : 8);++Pair)
            {
                double Ms[2]={0.,0.};bool Exact=true;
                for (int32 Order=0;Order<2;++Order)
                {
                    const int32 Kind=(Order+Pair)%2;
                    ResetSourceOutputs();
                    if(bAtlasStencilAudit)bCacheAtlasStencil=Kind==1;
                    const double Begin=FPlatformTime::Seconds();
                    if (bAtlasStencilAudit) { SampleCombinedVertices();BlendSourceVertices(true,true); }
                    else if (Kind==0) { SampleLiveVertices(true);BlendSourceVertices(true); }
                    else { SampleCombinedVertices();BlendSourceVertices(true,true); }
                    Ms[Kind]=(FPlatformTime::Seconds()-Begin)*1000.;
                    Exact &= MatchesSaved();
                }
                auto Row=MakeShared<FJsonObject>();
                Row->SetBoolField(bAtlasStencilAudit ? TEXT("candidate_first") : TEXT("fused_first"),Pair%2!=0);
                Row->SetNumberField(bAtlasStencilAudit ? TEXT("reference_ms") : TEXT("separate_ms"),Ms[0]);
                Row->SetNumberField(bAtlasStencilAudit ? TEXT("candidate_ms") : TEXT("fused_ms"),Ms[1]);
                Row->SetBoolField(TEXT("all_samples_and_masks_exact"),Exact);
                AllPairsExact &= Exact;
                Pairs.Add(MakeShared<FJsonValueObject>(Row));
            }
        }
        bCacheAtlasStencil=SavedCacheAtlasStencil;
        WaterSamples=MoveTemp(SavedSamples); WetVertexMask=MoveTemp(SavedWet);
        LiveSolverWetVertexMask=MoveTemp(SavedLiveWet); SolverSampledVertexMask=MoveTemp(SavedSampled);
        CartesianShoreAvailable=MoveTemp(SavedAvailable); BaselineKeepProbeWanted=MoveTemp(SavedProbeWanted);
        FeatheredBaselineWet=MoveTemp(SavedFeather); PresentationSurfaceHeightMeters=MoveTemp(SavedHeights);
        TSharedRef<FJsonObject> Audit=MakeShared<FJsonObject>();
        Audit->SetStringField(TEXT("schema"),bAtlasStencilAudit ? TEXT("raftsim.atlas_stencil_pair.v1") : TEXT("raftsim.source_handover_pair.v1"));
        Audit->SetStringField(TEXT("scope"),bAtlasStencilAudit
            ? TEXT("Same immutable live/atlas inputs and current render coordinates; 64 alternating parallel source+handover passes. Only atlas address lookup changes. All source fields and bank masks checked exactly; outputs restored. Not visual or whole-frame performance acceptance.")
            : TEXT("Exact serial/parallel live-source sampling, bank decisions and crop handover on the same actual runtime state; excludes later relief/foam/mesh stages and full visual acceptance."));
        Audit->SetStringField(TEXT("map"),GetWorld()->GetMapName());
        Audit->SetNumberField(TEXT("world_seconds"),GetWorld()->GetTimeSeconds());
        Audit->SetNumberField(TEXT("samples"),Count);
        Audit->SetNumberField(TEXT("different_samples"),DifferentSamples);
        Audit->SetBoolField(TEXT("identical_masks_probe_requests_feather_and_heights"),SameFields);
        Audit->SetArrayField(bAtlasStencilAudit ? TEXT("atlas_stencil_pairs") : TEXT("paired_parallel_passes"),Pairs);
        Audit->SetBoolField(TEXT("paired_parallel_passes_exact"),AllPairsExact);
        Audit->SetBoolField(TEXT("passed"),DifferentSamples==0 && SameFields && AllPairsExact);
        FString Json; auto Writer=TJsonWriterFactory<>::Create(&Json); FJsonSerializer::Serialize(Audit,Writer);
        if (!IFileManager::Get().FileExists(*SelectedSourceAuditPath)) FFileHelper::SaveStringToFile(Json,*SelectedSourceAuditPath);
    }

    Perf.Mark(TEXT("source_samples"));
    // Cooked visualization cells can otherwise read as broad transverse
    // steps. The optional cardinal filter retains the original three-metre
    // physical neighbourhood after render subdivision. It is Jacobi-style
    // (always reads the untouched sampled field), preserves a linear grade
    // exactly, and writes only this local render array.
    // WaterSamples remains the authority for gameplay.
    // Keep a lightly filtered hydraulic copy. The final multi-pass optical base
    // is deliberately glass-smooth in calm reaches, but using it for rapid
    // detection erased real ledges before relief, foam, and the local fluid
    // field could see them. Four passes suppress one-cell shocks while
    // retaining feature-scale curvature.
    TArray<float> HydraulicSourceSurfaceHeightMeters =
        PresentationSurfaceHeightMeters;
    const bool bNativeMean=bCartesianFlow && bSingleLiveWaterSurfaceEnabled;
    bool bNeedsOptical=false;
    FString SmoothingAuditPath;
    bool bAuditSmoothing=false;
#if !UE_BUILD_SHIPPING
    FString RequestedDecomposition;
    bNeedsOptical=bNativeMean && GetWorld() && GetWorld()->GetTimeSeconds()>=10.f &&
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimSurfaceDecompositionAudit="),RequestedDecomposition) &&
        !FPaths::FileExists(RequestedDecomposition);
    // Same-binary timing control; no stage/geometry settings are changed.
    bNeedsOptical |= FParse::Param(FCommandLine::Get(),TEXT("RaftSimRetainDiscardedOpticalPasses"));
    bAuditSmoothing=bNativeMean && GetWorld() && GetWorld()->GetTimeSeconds()>=10.f &&
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimSmoothingElisionAudit="),SmoothingAuditPath) &&
        !FPaths::FileExists(SmoothingAuditPath);
#endif
    if (bLivePresentationSurfaceSmoothingEnabled &&
        ResolvedPresentationSurfaceSmoothingStrength > 0.0f)
    {
        const int32 Stride = PresentationAnalysisStride;
        // Sixteen optical passes predate the UV precision repair. Keep the
        // baseline until visual review, but allow a South Fork-only ablation
        // without simultaneously changing the four-pass hydraulic sources.
        const int32 ConfiguredOpticalPassCount = bSouthForkOpticalSmoothingReview
            ? FMath::Clamp(
                  CVarRaftSimSouthForkOpticalSmoothingPasses.GetValueOnGameThread(),
                  1, 16)
            : bSingleLiveWaterSurfaceEnabled ? 16 : 1;
        const int32 HydraulicPassCount = bSingleLiveWaterSurfaceEnabled ? 4 : 1;
        const int32 OpticalPassCount=RaftSimWaterSmoothing::OpticalPassCount(
            bNativeMean,bNeedsOptical,ConfiguredOpticalPassCount);
        TArray<float> AuditSource;
        if (bAuditSmoothing) AuditSource=PresentationSurfaceHeightMeters;
        if (LastLoggedOpticalSmoothingPassCount != OpticalPassCount)
        {
            UE_LOG(LogTemp, Display,
                TEXT("Water smoothing review: optical=%d hydraulic=%d south_fork=%d"),
                OpticalPassCount, HydraulicPassCount,
                bSouthForkOpticalSmoothingReview ? 1 : 0);
            LastLoggedOpticalSmoothingPassCount = OpticalPassCount;
        }
        {
            CSV_SCOPED_TIMING_STAT(RaftSimSurface,OpticalFilter);
            RaftSimWaterSmoothing::Apply(PresentationSurfaceHeightMeters,WetVertexMask,
                GridStationN,GridLateralN,Stride,ResolvedPresentationSurfaceSmoothingStrength,
                OpticalPassCount,HydraulicPassCount,HydraulicSourceSurfaceHeightMeters);
        }
#if !UE_BUILD_SHIPPING
        if (bAuditSmoothing)
        {
            TArray<float> LegacyHydraulic;
            RaftSimWaterSmoothing::Apply(AuditSource,WetVertexMask,GridStationN,GridLateralN,
                Stride,ResolvedPresentationSurfaceSmoothingStrength,ConfiguredOpticalPassCount,
                HydraulicPassCount,LegacyHydraulic);
            int32 DifferentBase=0,DifferentHydraulic=0;
            for (int32 I=0;I<AuditSource.Num();++I)
            {
                const float Legacy=WetVertexMask[I] ? WaterSamples[I].SurfaceHeightMeters : AuditSource[I];
                const float Fast=WetVertexMask[I] ? WaterSamples[I].SurfaceHeightMeters : PresentationSurfaceHeightMeters[I];
                DifferentBase+=Legacy!=Fast;
                DifferentHydraulic+=LegacyHydraulic[I]!=HydraulicSourceSurfaceHeightMeters[I];
            }
            auto Report=MakeShared<FJsonObject>();
            Report->SetStringField(TEXT("scope"),TEXT("Same actual source state and wet mask: native base and hydraulic stage arrays with/without discarded optical passes. Excludes subsequent frame scheduling, GPU state and visual/performance acceptance."));
            Report->SetNumberField(TEXT("source_vertices"),AuditSource.Num());
            Report->SetNumberField(TEXT("executed_passes"),FMath::Max(OpticalPassCount,HydraulicPassCount));
            Report->SetNumberField(TEXT("legacy_passes"),FMath::Max(ConfiguredOpticalPassCount,HydraulicPassCount));
            Report->SetNumberField(TEXT("different_base_values"),DifferentBase);
            Report->SetNumberField(TEXT("different_hydraulic_values"),DifferentHydraulic);
            Report->SetBoolField(TEXT("passed"),DifferentBase==0 && DifferentHydraulic==0);
            FString Json; auto Writer=TJsonWriterFactory<>::Create(&Json); FJsonSerializer::Serialize(Report,Writer);
            FFileHelper::SaveStringToFile(Json,*SmoothingAuditPath);
        }
#endif
    }

    TArray<float> FilteredBaseForAudit;
    if (bNativeMean)
    {
#if !UE_BUILD_SHIPPING
        if (GetWorld() && GetWorld()->GetTimeSeconds()>=10.f &&
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimSurfaceDecompositionAudit="),RequestedDecomposition) &&
            !FPaths::FileExists(RequestedDecomposition))
            FilteredBaseForAudit=PresentationSurfaceHeightMeters;
#endif
        // Filtering is useful for feature detection, not for replacing the
        // authoritative mean stage. At the actual crux the optical filter
        // filled a solver-resolved trough by >1m. Retain HydraulicSource...
        // above for existing detection/relief, but render the native mean.
        for (int32 I=0;I<WaterSamples.Num();++I)
            if (WetVertexMask[I])PresentationSurfaceHeightMeters[I]=WaterSamples[I].SurfaceHeightMeters;
    }
    Perf.Mark(TEXT("optical_filter"));
    // Amplify only solver-resolved station curvature. The five analysis
    // samples retain their original 12 m span on the subdivided render grid,
    // large enough to describe a readable rapid crest/hole pair without
    // misclassifying the new short presentation bands as solver relief.
    const int32 AnalysisNearStride = PresentationAnalysisStride;
    const int32 AnalysisFarStride = 2 * PresentationAnalysisStride;
    if (bCartesianFlow)
    {
        CSV_SCOPED_TIMING_STAT(RaftSimSurface,HydraulicRelief);
        // Qualified on identical actual South Fork fields in both call orders.
        // Diagnostic serial switch changes scheduling only, not sample quality.
        static const bool bParallelRelief=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimSerialHydraulicRelief"));
        if(!RaftSimCartesianHydraulicRelief::Apply(WaterSamples,HydraulicSourceSurfaceHeightMeters,
            WetVertexMask,GridStationN,GridLateralN,AnalysisNearStride,AnalysisFarStride,
            ResolvedPresentationHydraulicReliefScale,HydraulicReliefMeters,bParallelRelief))
        {UE_LOG(LogTemp,Error,TEXT("Invalid Cartesian hydraulic relief input; refusing surface refresh"));return;}
#if !UE_BUILD_SHIPPING
        static const FString ReliefAuditPath=[]()
        {FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimHydraulicReliefAudit="),P);return P;}();
        static TArray<TSharedPtr<FJsonValue>> ReliefRows;
        if(!ReliefAuditPath.IsEmpty() && ReliefRows.Num()<64 && GetWorld() &&
            GetWorld()->GetTimeSeconds()>=10. && !FPaths::FileExists(ReliefAuditPath))
        {
            TArray<float> Outputs[2];double Milliseconds[2];
            const bool ParallelFirst=ReliefRows.Num()%2!=0;
            for(int32 Pass=0;Pass<2;++Pass)
            {
                const int32 Kind=ParallelFirst ? 1-Pass : Pass;
                const double Start=FPlatformTime::Seconds();
                RaftSimCartesianHydraulicRelief::Apply(WaterSamples,HydraulicSourceSurfaceHeightMeters,
                    WetVertexMask,GridStationN,GridLateralN,AnalysisNearStride,AnalysisFarStride,
                    ResolvedPresentationHydraulicReliefScale,Outputs[Kind],Kind==1);
                Milliseconds[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
            }
            int32 Different=0,Nonzero=0;
            for(int32 I=0;I<WaterSamples.Num();++I)
            {
                Different+=FMemory::Memcmp(&Outputs[0][I],&Outputs[1][I],sizeof(float))!=0 ||
                    FMemory::Memcmp(&Outputs[0][I],&HydraulicReliefMeters[I],sizeof(float))!=0;
                Nonzero+=Outputs[0][I]!=0.f;
            }
            auto Row=MakeShared<FJsonObject>();
            Row->SetNumberField(TEXT("world_seconds"),GetWorld()->GetTimeSeconds());
            Row->SetBoolField(TEXT("parallel_first"),ParallelFirst);
            Row->SetNumberField(TEXT("vertices"),WaterSamples.Num());
            Row->SetNumberField(TEXT("nonzero_relief_vertices"),Nonzero);
            Row->SetNumberField(TEXT("different_float_bits"),Different);
            Row->SetNumberField(TEXT("serial_ms"),Milliseconds[0]);
            Row->SetNumberField(TEXT("parallel_ms"),Milliseconds[1]);
            ReliefRows.Add(MakeShared<FJsonValueObject>(Row));
            if(ReliefRows.Num()==64)
            {
                auto Report=MakeShared<FJsonObject>();
                Report->SetStringField(TEXT("schema"),TEXT("raftsim.cartesian_hydraulic_relief_pair.v1"));
                Report->SetStringField(TEXT("scope"),TEXT("Same actual frozen source inputs, alternating call order, exact per-vertex relief. Not total FPS, geometry/water realism or release acceptance."));
                Report->SetArrayField(TEXT("rows"),ReliefRows);
                Report->SetBoolField(TEXT("release_accepted"),false);
                FString Json;auto Writer=TJsonWriterFactory<>::Create(&Json);FJsonSerializer::Serialize(Report,Writer);
                FFileHelper::SaveStringToFile(Json,*ReliefAuditPath);
            }
        }
#endif
    }
    else for (int32 Y = 0; Y < GridLateralN; ++Y)
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
                (URaftSimWaterRuntimeAdapter::ComputeCoupledHydraulicReliefMeters(
                     HydraulicSourceSurfaceHeightMeters[Index],
                     HydraulicSourceSurfaceHeightMeters[UpstreamFarIndex],
                     HydraulicSourceSurfaceHeightMeters[UpstreamNearIndex],
                     HydraulicSourceSurfaceHeightMeters[DownstreamNearIndex],
                     HydraulicSourceSurfaceHeightMeters[DownstreamFarIndex],
                     Sample.VelocityMetersPerSecond.Size2D(),
                     Sample.DepthMeters) +
                 URaftSimWaterRuntimeAdapter::ComputeCoupledRapidGradeWaveMeters(
                     RiverCoordinatesM[Index],
                     HydraulicSourceSurfaceHeightMeters[UpstreamFarIndex],
                     HydraulicSourceSurfaceHeightMeters[DownstreamFarIndex],
                     Sample.VelocityMetersPerSecond.Size2D())) *
                ResolvedPresentationHydraulicReliefScale;
        }
    }
    Perf.Mark(TEXT("hydraulic_relief"));
    TArray<float> StationWetSurfaceZSum;
    StationWetSurfaceZSum.Init(0.0f, GridStationN);
    TArray<int32> StationWetSurfaceCount;
    StationWetSurfaceCount.Init(0, GridStationN);
    TArray<int32> MinimumWetLateralIndex;
    MinimumWetLateralIndex.Init(GridLateralN, GridStationN);
    TArray<int32> MaximumWetLateralIndex;
    MaximumWetLateralIndex.Init(INDEX_NONE, GridStationN);
    for (int32 Y = 0; Y < GridLateralN; ++Y)
    {
        for (int32 X = 0; X < GridStationN; ++X)
        {
            const int32 Index = Y * GridStationN + X;
            if (WetVertexMask[Index] == 0)
            {
                continue;
            }
            MinimumWetLateralIndex[X] = FMath::Min(
                MinimumWetLateralIndex[X], Y);
            MaximumWetLateralIndex[X] = FMath::Max(
                MaximumWetLateralIndex[X], Y);
        }
    }
    TArray<float> ShoreDisplacementWeight;
    ShoreDisplacementWeight.SetNumZeroed(Vertices.Num());
    const TArray<int32> CartesianWetEdgeSteps = bCartesianFlow
        ? RaftSimWetEdgeAudit::EvaluateCached(WetEdgeDistanceCache,GridStationN,GridLateralN,WetVertexMask,1) : TArray<int32>();
    for (int32 Y = 0; Y < GridLateralN; ++Y)
    {
        for (int32 X = 0; X < GridStationN; ++X)
        {
            const int32 Index = Y * GridStationN + X;
            if (WetVertexMask[Index] != 0)
            {
                ShoreDisplacementWeight[Index] = bCartesianFlow
                    ? ComputePresentationShoreDisplacementWeight(CartesianWetEdgeSteps[Index],0,
                        2*CartesianWetEdgeSteps[Index],ResolvedVertexSpacingMeters)
                    :
                    ComputePresentationShoreDisplacementWeight(
                        Y,
                        MinimumWetLateralIndex[X],
                        MaximumWetLateralIndex[X],
                        ResolvedVertexSpacingMeters);
                HydraulicReliefMeters[Index] *=
                    ShoreDisplacementWeight[Index];
            }
        }
    }
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
    // Per-rebuild presentation state: prune boulder footprints to this
    // window and use the tick-sampled raft state to build the paddle wake
    // height field once for all vertex and normal passes.
    WindowBoulderFootprintsSLR.Reset();
    if (BoulderFootprintsSLR.Num() > 0 && RiverCoordinatesM.Num() > 0)
    {
        float WindowMinStationM = FLT_MAX;
        float WindowMaxStationM = -FLT_MAX;
        for (const FVector2D& Coordinate : RiverCoordinatesM)
        {
            WindowMinStationM = FMath::Min(
                WindowMinStationM, static_cast<float>(Coordinate.X));
            WindowMaxStationM = FMath::Max(
                WindowMaxStationM, static_cast<float>(Coordinate.X));
        }
        for (const FVector3f& Footprint : BoulderFootprintsSLR)
        {
            if (Footprint.X <= WindowMinStationM - 40.0f ||
                Footprint.X >= WindowMaxStationM + 40.0f)
            {
                continue;
            }

            const int32 NearestStationIndex = FMath::Clamp(
                FMath::RoundToInt(
                    (Footprint.X - RiverCoordinatesM[0].X) /
                    FMath::Max(ResolvedVertexSpacingMeters,
                        KINDA_SMALL_NUMBER)),
                0,
                GridStationN - 1);
            const int32 MinimumWetIndex =
                MinimumWetLateralIndex[NearestStationIndex];
            const int32 MaximumWetIndex =
                MaximumWetLateralIndex[NearestStationIndex];
            if (MinimumWetIndex < 0 || MaximumWetIndex < MinimumWetIndex)
            {
                continue;
            }
            const float MinimumWetLateralMeters = RiverCoordinatesM[
                MinimumWetIndex * GridStationN + NearestStationIndex].Y;
            const float MaximumWetLateralMeters = RiverCoordinatesM[
                MaximumWetIndex * GridStationN + NearestStationIndex].Y;
            if (!IsBoulderFootprintHydraulicallyExposed(
                    Footprint.Y,
                    Footprint.Z,
                    FMath::Min(MinimumWetLateralMeters,
                        MaximumWetLateralMeters),
                    FMath::Max(MinimumWetLateralMeters,
                        MaximumWetLateralMeters),
                    ResolvedVertexSpacingMeters))
            {
                continue;
            }
            WindowBoulderFootprintsSLR.Add(Footprint);
        }
    }
    // Build a signed height field on the existing live mesh. This is actual
    // vertex displacement: it does not touch foam, base color, roughness, or
    // the retired material-normal wake. The 15 Hz mesh refresh advances the
    // phase while the smoothed paddling envelope prevents command-edge pops.
    TArray<float> BoatWakeDisplacementMeters;
    BoatWakeDisplacementMeters.SetNumZeroed(WaterSamples.Num());
    float MaximumAbsoluteBoatWakeM = 0.0f;
    if (bBoatWakeValid && BoatWakePaddleEnvelope > 0.001f)
    {
        const float RelativeSpeedScale = FMath::Lerp(
            0.55f,
            1.0f,
            FMath::Clamp(BoatWakeRelativeSpeedMps / 0.9f, 0.0f, 1.0f));
        const float WakeStrength =
            BoatWakePaddleEnvelope * RelativeSpeedScale;
        for (int32 WakeIndex = 0;
             WakeIndex < BoatWakeDisplacementMeters.Num();
             ++WakeIndex)
        {
            if (WetVertexMask[WakeIndex] == 0)
            {
                continue;
            }
            const float DisplacementM =
                ComputePaddleWakeDisplacementMeters(
                    RiverCoordinatesM[WakeIndex],
                    BoatRiverPositionM,
                    BoatWakeTravelDirection,
                    WakeStrength,
                    PresentationPhaseSeconds);
            BoatWakeDisplacementMeters[WakeIndex] = DisplacementM;
            MaximumAbsoluteBoatWakeM = FMath::Max(
                MaximumAbsoluteBoatWakeM, FMath::Abs(DisplacementM));
        }
    }
    for (int32 WakeIndex = 0;
         WakeIndex < BoatWakeDisplacementMeters.Num();
         ++WakeIndex)
    {
        BoatWakeDisplacementMeters[WakeIndex] *=
            ShoreDisplacementWeight[WakeIndex];
    }
    // UV2.x reveals only the actual displaced crest and trough bands.
    // Keeping the signed zero crossings transparent separates the geometry
    // into readable ripple arcs rather than one broad wake-coloured sheet.
    BoatWakePresentationData.SetNumZeroed(
        BoatWakeDisplacementMeters.Num());
    for (int32 WakeIndex = 0;
         WakeIndex < BoatWakeDisplacementMeters.Num();
         ++WakeIndex)
    {
        if (WetVertexMask[WakeIndex] == 0)
        {
            continue;
        }
        BoatWakePresentationData[WakeIndex].X = FMath::SmoothStep(
            0.006f,
            0.025f,
            FMath::Abs(BoatWakeDisplacementMeters[WakeIndex]));
        BoatWakePresentationData[WakeIndex].Y = FMath::Clamp(
            BoatWakeDisplacementMeters[WakeIndex] / 0.110f,
            -1.0f,
            1.0f);
    }
    if (WaterAdapter)
    {
        TArray<URaftSimWaterRuntimeAdapter::FSupportBoulderFootprint>
            SupportFootprints;
        SupportFootprints.Reserve(BoulderFootprintsSLR.Num());
        for (const FVector3f& Footprint : BoulderFootprintsSLR)
        {
            URaftSimWaterRuntimeAdapter::FSupportBoulderFootprint& Support =
                SupportFootprints.AddDefaulted_GetRef();
            Support.RiverCoordinatesMeters = FVector2D(
                Footprint.X, Footprint.Y);
            Support.RadiusMeters = Footprint.Z;
        }
        WaterAdapter->ConfigureRaftSupportBoulderFootprints(
            SupportFootprints);
    }

    // Build the obstruction field before the vertex pass so its signed relief
    // participates in central-difference normals. The old boulder path found
    // the same Y arms but discarded WakeReliefM, leaving only pale foam
    // streaks. Keep the strongest overlapping footprint at each vertex to
    // avoid stacking nearby rocks into an artificial wall of water.
    TArray<float> BoulderWakeDisplacementMeters;
    BoulderWakeDisplacementMeters.SetNumZeroed(WaterSamples.Num());
    TArray<float> BoulderWakeFoam;
    BoulderWakeFoam.SetNumZeroed(WaterSamples.Num());
    float MaximumAbsoluteBoulderWakeM = 0.0f;
    float MaximumBoulderPillowM = 0.0f;
    float MaximumBoulderRingSpeedMps = 0.0f;
    int32 WetPillowRingVertexCount = 0;
    for (int32 WakeIndex = 0;
         WakeIndex < BoulderWakeDisplacementMeters.Num();
         ++WakeIndex)
    {
        if (WetVertexMask[WakeIndex] == 0)
        {
            continue;
        }
        const FVector2D& Coordinate = RiverCoordinatesM[WakeIndex];
        const float WaterSpeedMps =
            WaterSamples[WakeIndex].VelocityMetersPerSecond.Size2D();
        const FVector2D BoulderFlowDirection = FlowDirectionFor(WaterSamples[WakeIndex]);
        for (const FVector3f& Footprint : WindowBoulderFootprintsSLR)
        {
            // Match rigid support and the foam return path: geographic X
            // is east, not downstream. Keep +X for station/lateral fields.
            const FVector2D Relative = RaftSimWaterFlowFrame::ToLocal(
                Coordinate - FVector2D(Footprint.X, Footprint.Y), BoulderFlowDirection);
            const float DownstreamM = Relative.X;
            const float AcrossM = Relative.Y;
            const FVector2D Wake = ComputeBoulderWakePresentation(
                DownstreamM,
                AcrossM,
                Footprint.Z,
                WaterSpeedMps,
                PresentationPhaseSeconds);
            const float PillowM = URaftSimWaterRuntimeAdapter::
                ComputeCoupledBoulderPillowDisplacementMeters(
                    DownstreamM,
                    AcrossM,
                    Footprint.Z,
                    WaterSpeedMps);
            if (PillowM > 0.0f)
            {
                ++WetPillowRingVertexCount;
                MaximumBoulderPillowM =
                    FMath::Max(MaximumBoulderPillowM, PillowM);
                MaximumBoulderRingSpeedMps =
                    FMath::Max(MaximumBoulderRingSpeedMps, WaterSpeedMps);
                // The pillow itself is clear-water GEOMETRY — a sub-20 cm
                // smooth mound that is invisible at any distance on a calm
                // surface ("theres still no pillow on the rock", km 0.87,
                // after the ring was verified live by this probe). What a
                // player recognises as a pillow is the aerated collar where
                // the climbing water breaks white, so the ring also feeds
                // the boulder foam channel: a faint lap line at pool drift,
                // a bright cushion where fast water actually aerates.
                const float PillowRingT =
                    FMath::Clamp(PillowM / 0.24f, 0.0f, 1.0f);
                const float PillowAerationT =
                    FMath::SmoothStep(0.35f, 1.60f, WaterSpeedMps);
                BoulderWakeFoam[WakeIndex] = FMath::Max(
                    BoulderWakeFoam[WakeIndex],
                    PillowRingT * (0.12f + 0.75f * PillowAerationT));
            }
            const float CoupledDisplacementM = Wake.X + PillowM;
            if (FMath::Abs(CoupledDisplacementM) >
                FMath::Abs(BoulderWakeDisplacementMeters[WakeIndex]))
            {
                BoulderWakeDisplacementMeters[WakeIndex] =
                    CoupledDisplacementM;
            }
            BoulderWakeFoam[WakeIndex] = FMath::Max(
                BoulderWakeFoam[WakeIndex], static_cast<float>(Wake.Y));
        }
        BoulderWakeDisplacementMeters[WakeIndex] *=
            ShoreDisplacementWeight[WakeIndex];
        BoulderWakeFoam[WakeIndex] *=
            ShoreDisplacementWeight[WakeIndex];
        MaximumAbsoluteBoulderWakeM = FMath::Max(
            MaximumAbsoluteBoulderWakeM,
            FMath::Abs(BoulderWakeDisplacementMeters[WakeIndex]));
    }
    if (CVarRaftSimLogWaterRenderStateEvents.GetValueOnGameThread() != 0 &&
        WindowBoulderFootprintsSLR.Num() > 0)
    {
        // Pillow forensics ("theres no pillow on the rock", 2026-08-31):
        // how much upstream mound the wet lattice actually received this
        // refresh, and at what sampled ring speed.
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim boulder pillow probe: footprints=%d wet_ring_verts=%d "
                 "max_pillow_m=%.4f max_ring_speed_mps=%.3f coupled_max_m=%.4f "
                 "boat_wake_valid=%d paddling=%d wake_env=%.2f wake_rel_mps=%.2f "
                 "wake_max_m=%.4f level_delta_m=%.3f"),
            WindowBoulderFootprintsSLR.Num(),
            WetPillowRingVertexCount,
            MaximumBoulderPillowM,
            MaximumBoulderRingSpeedMps,
            MaximumAbsoluteBoulderWakeM,
            bBoatWakeValid ? 1 : 0,
            bBoatWakePaddling ? 1 : 0,
            BoatWakePaddleEnvelope,
            BoatWakeRelativeSpeedMps,
            MaximumAbsoluteBoatWakeM,
            LiveVsBaselineLevelDeltaM);
    }

    Perf.Mark(TEXT("shore_wake_fields"));
    // Continuous current detail belongs in the single carrier's WPO. It is
    // evaluated every rendered frame from the same integrated solver-current
    // displacement as the foam. Sampling that phase here made the whole mesh
    // jump between several-centimetre targets at the 15 Hz hydraulic refresh,
    // which was most obvious while the camera moved with the raft. CPU vertex
    // displacement remains reserved for solver relief and localized wakes.
    LastMaximumAbsoluteBoulderWakeM = MaximumAbsoluteBoulderWakeM;
    int32 WakeFoamVertexCount = 0;
    // Snapshot game-thread-only settings before joined worker execution.
    const bool bBaseFlatNormals=CVarRaftSimFlatWaterNormals.GetValueOnGameThread()!=0;
    const float BaseWorldYSign=WaterAdapter ? WaterAdapter->GetRiverWorldYSign() : 1.f;
    const float BaseRenderLiftCm=GetResolvedLiveSurfaceRenderLiftCm();
    const int32 BasePadState=CorridorEndPadState();
    const int32 BaseUpstreamPad=(BasePadState&1) ? GridStationN : 0;
    const int32 BaseDownstreamPad=(BasePadState&2) ? GridStationN : 0;
    static const bool bForceParallelBaseVertices=FParse::Param(FCommandLine::Get(),TEXT("RaftSimParallelBaseVertices"));
    static const bool bSerialBaseVertices=FParse::Param(FCommandLine::Get(),TEXT("RaftSimSerialBaseVertices"));
    // Exact paired component results do not establish a whole-game gain.
    // Both ordinary candidate runs were slower than both serial controls;
    // retain the candidate only for explicit diagnostics, not normal play.
    const bool bParallelBaseVertices=!bSerialBaseVertices && bForceParallelBaseVertices;
    static bool bLoggedBaseDispatch=false;
    if(!bLoggedBaseDispatch)
    {
        bLoggedBaseDispatch=true;
        UE_LOG(LogTemp,Display,TEXT("RaftSim base vertex dispatch: parallel=%d forced=%d serial_override=%d"),
            int32(bParallelBaseVertices),int32(bForceParallelBaseVertices),int32(bSerialBaseVertices));
    }
    static const bool bBaseVertexAudit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimBaseVertexAudit"));
    const int32 BaseVertexCount=GridStationN*GridLateralN;
    const auto RunBaseVertices=[&](bool bParallel)
    {
        struct FDeferredStats { float Speed,StandingWave; uint8 WakeFoam; };
        TArray<FDeferredStats> Deferred;
        if(bParallel)Deferred.SetNumUninitialized(BaseVertexCount);
        const auto EvaluateVertex=[&](int32 Index)
        {
            const int32 X=Index%GridStationN,Y=Index/GridStationN;
            // Wet/dry visibility is encoded in vertex alpha below. Dry and
            // out-of-crop vertices are levelled to the nearest same-station
            // wet surface in a second pass. Moving them far below the bed made
            // wet/dry boundary triangles into kilometre-tall translucent
            // curtains that occluded the raft and banks.
            float SurfaceZCm = 0.0f;
            FVector NormalOut = FVector::UpVector;
            float Foam = 0.0f;
            float WakeFoamAdd = 0.0f;
            float BoulderCoreFade = 1.0f;
            float LegacyMaterialWPOCounterM = 0.0f;
            float LegacyMaterialWPOCounterStationSlope = 0.0f;
            float LegacyMaterialWPOCounterLateralSlope = 0.0f;

            float DepthNorm = 0.0f;
            float SpeedNorm = 0.0f;
            const FVector2D PreviousFlowVelocityMps = FlowVelocityMetersPerSecond[Index];
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
                // Smoothed across refreshes: the material advects its ripple
                // normals by this vector, so raw per-refresh solver noise in
                // it stepped the ripple phase 15 times a second and read as
                // specular/reflection jitter.
                const FVector2D SampledFlowVelocityMps(
                    Sample.VelocityMetersPerSecond.X,
                    Sample.VelocityMetersPerSecond.Y);
                FlowVelocityMetersPerSecond[Index] = RaftSimWaterFlowHistory::Advance(
                    PreviousFlowVelocityMps, SampledFlowVelocityMps, RefreshIntervalSeconds);
                const float Depth = FMath::Max(Sample.DepthMeters, 0.05f);
                const FRaftSimWaterStandingWave StandingWave = bCartesianFlow ? FRaftSimWaterStandingWave{} :
                    URaftSimWaterRuntimeAdapter::ComputeCoupledStandingWave(
                        RiverCoordinatesM[Index], Speed, Depth);
                const float HydraulicRelief = HydraulicReliefMeters[Index];
                if (bSingleLiveWaterSurfaceEnabled &&
                    !bHasTravelingWaveWPOStrengthParameter)
                {
                    // Saved V1/V2 transmission parents predate the explicit
                    // amplitude gate. At a frozen zero wave clock their
                    // energetic terms cancel the static bake exactly; only
                    // the calm amplitude difference remains:
                    // (0.030 - 0.018) * sin(0.19*s + 0.61*l).
                    // Subtract that exact displacement and slope from the
                    // procedural carrier so the unchanged material adds back
                    // zero net geometry. This compatibility path disappears
                    // automatically once the gated parent is regenerated.
                    const float LegacyPhase =
                        static_cast<float>(RiverCoordinatesM[Index].X) * 0.19f +
                        static_cast<float>(RiverCoordinatesM[Index].Y) * 0.61f;
                    LegacyMaterialWPOCounterM = 0.012f * FMath::Sin(LegacyPhase);
                    const float LegacySlopeScale = 0.012f * FMath::Cos(LegacyPhase);
                    LegacyMaterialWPOCounterStationSlope =
                        LegacySlopeScale * 0.19f;
                    LegacyMaterialWPOCounterLateralSlope =
                        LegacySlopeScale * 0.61f;
                }
                // The authored seasonal surface remains beneath this live
                // solver patch. Reapply its deterministic sub-grid ripple and
                // sharpen only the large-scale relief already present in the
                // sampled cooked surface. Standing-wave and relief terms also
                // drive rigid support; the 2 cm z-fight lift is render-only,
                // and flexible D3 keeps the unamplified water field.
                SurfaceZCm =
                    (PresentationSurfaceHeightMeters[Index] +
                        StandingWave.DisplacementMeters *
                            ResolvedPresentationStandingWaveScale *
                            ShoreDisplacementWeight[Index] +
                        HydraulicRelief - LegacyMaterialWPOCounterM) *
                        kSurfCmPerM +
                    BaseRenderLiftCm;
                // The visible waterline is the surface/terrain intersection:
                // on a flat bank a few centimetres of per-refresh wave motion
                // sweep that line metres sideways, reading as patches of
                // water appearing and vanishing. Waves physically damp as
                // they shoal, so blend the shallow surface toward a slow
                // per-vertex reference; deep water stays fully dynamic and
                // the wet edge merely breathes with the reference's slow
                // drift. Render-only, like the rest of the shaping here.
                if (ShoreSmoothedSurfaceZCm.Num() == Vertices.Num())
                {
                    float& SlowZCm = ShoreSmoothedSurfaceZCm[Index];
                    if (SlowZCm == MAX_flt ||
                        FMath::Abs(SlowZCm - SurfaceZCm) > 60.0f)
                    {
                        SlowZCm = SurfaceZCm;
                    }
                    else
                    {
                        SlowZCm = FMath::Lerp(
                            SlowZCm,
                            SurfaceZCm,
                            1.0f - FMath::Exp(
                                -0.8f * FMath::Max(
                                    RefreshIntervalSeconds, 0.0f)));
                    }
                    const float ShoreDynamicDamp = FMath::SmoothStep(
                        0.05f, 0.45f, Sample.DepthMeters);
                    SurfaceZCm = FMath::Lerp(
                        SlowZCm, SurfaceZCm, ShoreDynamicDamp);
                }
                // Obstruction wakes and boulder holes on the live sheet.
                // The solver grid does not know placed boulders exist, so
                // without the sink the translucent carrier shrouds every
                // exposed rock to its tip; pillow/arm amplitudes mirror the
                // baked band-mesh terms so the two surfaces agree.
                const FVector2D BoulderFlowDirection = FlowDirectionFor(Sample);
                for (const FVector3f& Footprint : WindowBoulderFootprintsSLR)
                {
                    const float RadiusM = FMath::Max(Footprint.Z, 0.75f);
                    const FVector2D Relative = RaftSimWaterFlowFrame::ToLocal(
                        RiverCoordinatesM[Index] - FVector2D(Footprint.X, Footprint.Y),
                        BoulderFlowDirection);
                    const float DeltaStationM = Relative.X;
                    if (DeltaStationM < -RadiusM * 3.0f ||
                        DeltaStationM > RadiusM * 10.5f)
                    {
                        continue;
                    }
                    const float DeltaLateralM = Relative.Y;
                    if (FMath::Abs(DeltaLateralM) > RadiusM * 7.5f)
                    {
                        continue;
                    }
                    const float DistanceM = FMath::Sqrt(
                        DeltaStationM * DeltaStationM +
                        DeltaLateralM * DeltaLateralM);
                    if (DistanceM < RadiusM * 0.7f)
                    {
                        const float SinkT = FMath::Clamp(
                            1.0f - DistanceM / (RadiusM * 0.7f), 0.0f, 1.0f);
                        SurfaceZCm -= (Depth + 1.0f) * 100.0f * SinkT;
                        BoulderCoreFade =
                            FMath::Min(BoulderCoreFade, 1.0f - SinkT);
                        continue;
                    }
                    const float SpeedT = FMath::SmoothStep(
                        0.45f, 1.65f, Speed);
                    if (DeltaStationM < -0.35f * RadiusM &&
                        DistanceM < RadiusM * 1.9f)
                    {
                        const float Ring = FMath::Clamp(
                            1.0f -
                                FMath::Abs(DistanceM - RadiusM * 1.1f) /
                                    (RadiusM * 0.85f),
                            0.0f, 1.0f);
                        WakeFoamAdd = FMath::Max(
                            WakeFoamAdd, 0.85f * SpeedT * Ring);
                    }
                    else if (DeltaStationM > RadiusM * 0.3f)
                    {
                        if (FMath::Abs(DeltaLateralM) < RadiusM * 1.05f)
                        {
                            const float TrailT = FMath::Clamp(
                                1.0f - DeltaStationM / (RadiusM * 6.5f),
                                0.0f, 1.0f);
                            WakeFoamAdd = FMath::Max(
                                WakeFoamAdd,
                                0.55f * SpeedT * TrailT * TrailT);
                        }
                        // Eddy line: the shear seam between the sheltered
                        // pocket and the passing current collects a fine
                        // ragged foam string along each flank. The seam sits
                        // just outside the wake trail and fades with it.
                        const float SeamLateralT = FMath::Abs(DeltaLateralM) / RadiusM;
                        if (SeamLateralT > 0.95f && SeamLateralT < 1.75f &&
                            DeltaStationM < RadiusM * 6.0f)
                        {
                            const float SeamBand = 1.0f - FMath::Abs(
                                (SeamLateralT - 1.35f) / 0.4f);
                            const float SeamTrailT = FMath::Clamp(
                                1.0f - DeltaStationM / (RadiusM * 6.0f),
                                0.0f, 1.0f);
                            WakeFoamAdd = FMath::Max(
                                WakeFoamAdd,
                                0.42f * SpeedT *
                                    FMath::Max(SeamBand, 0.0f) * SeamTrailT);
                        }
                    }
                }
                WakeFoamAdd = FMath::Max(
                    WakeFoamAdd, BoulderWakeFoam[Index]);
                SurfaceZCm +=
                    (BoulderWakeDisplacementMeters[Index] +
                        BoatWakeDisplacementMeters[Index]) * kSurfCmPerM;
                if(!bParallel)
                {
                    StationWetSurfaceZSum[X] += SurfaceZCm;
                    ++StationWetSurfaceCount[X];
                }
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
                float BoatWakeStationSlope = 0.0f;
                if (X >= DerivativeStride &&
                    X < GridStationN - DerivativeStride &&
                    WetVertexMask[Index - DerivativeStride] != 0 &&
                    WetVertexMask[Index + DerivativeStride] != 0)
                {
                    BoatWakeStationSlope =
                        (BoatWakeDisplacementMeters[
                             Index + DerivativeStride] -
                            BoatWakeDisplacementMeters[
                                Index - DerivativeStride]) /
                        DerivativeSpanMeters;
                }
                float BoatWakeLateralSlope = 0.0f;
                if (Y >= DerivativeStride &&
                    Y < GridLateralN - DerivativeStride &&
                    WetVertexMask[
                        Index - DerivativeStride * GridStationN] != 0 &&
                    WetVertexMask[
                        Index + DerivativeStride * GridStationN] != 0)
                {
                    BoatWakeLateralSlope =
                        (BoatWakeDisplacementMeters[
                             Index + DerivativeStride * GridStationN] -
                            BoatWakeDisplacementMeters[
                                Index - DerivativeStride * GridStationN]) /
                        DerivativeSpanMeters;
                }
                float BoulderWakeStationSlope = 0.0f;
                if (X >= DerivativeStride &&
                    X < GridStationN - DerivativeStride &&
                    WetVertexMask[Index - DerivativeStride] != 0 &&
                    WetVertexMask[Index + DerivativeStride] != 0)
                {
                    BoulderWakeStationSlope =
                        (BoulderWakeDisplacementMeters[
                             Index + DerivativeStride] -
                            BoulderWakeDisplacementMeters[
                                Index - DerivativeStride]) /
                        DerivativeSpanMeters;
                }
                float BoulderWakeLateralSlope = 0.0f;
                if (Y >= DerivativeStride &&
                    Y < GridLateralN - DerivativeStride &&
                    WetVertexMask[
                        Index - DerivativeStride * GridStationN] != 0 &&
                    WetVertexMask[
                        Index + DerivativeStride * GridStationN] != 0)
                {
                    BoulderWakeLateralSlope =
                        (BoulderWakeDisplacementMeters[
                             Index + DerivativeStride * GridStationN] -
                            BoulderWakeDisplacementMeters[
                                Index - DerivativeStride * GridStationN]) /
                        DerivativeSpanMeters;
                }
                const FVector PresentationLocalNormal = FVector(
                    -(BaseStationSlope +
                        StandingWave.StationSlope *
                            ResolvedPresentationStandingWaveScale *
                            ShoreDisplacementWeight[Index] +
                        ReliefStationSlope +
                        BoulderWakeStationSlope +
                        BoatWakeStationSlope -
                        LegacyMaterialWPOCounterStationSlope),
                    -(BaseLateralSlope +
                        StandingWave.LateralSlope *
                            ResolvedPresentationStandingWaveScale *
                            ShoreDisplacementWeight[Index] +
                        ReliefLateralSlope +
                        BoulderWakeLateralSlope +
                        BoatWakeLateralSlope -
                        LegacyMaterialWPOCounterLateralSlope),
                    1.0f).GetSafeNormal();
                if (bUsesCurvedRiverCoordinates)
                {
                    const FVector FlowTangent = Tangents[Index].TangentX;
                    NormalOut = RaftSimFoamTransport::TransformSurfaceNormal(
                        PresentationLocalNormal, FlowTangent,
                        BaseWorldYSign);
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
                // Froude alone cannot tell a glassy accelerating tongue from
                // a broken cascade at the same number: air entrains only
                // where the surface is also locally steep and working. Gate
                // the generic generator by the combined local surface slope
                // (grade + standing waves + relief + boulder wakes) so smooth
                // chutes stay green while rough-bed riffles still break
                // white; the explicit site, tail, wake, and pocket sources
                // add their aeration regardless of this gate.
                const float LegacyWorkingSlope =
                    FMath::Abs(BaseStationSlope) +
                    FMath::Abs(StandingWave.StationSlope *
                        ResolvedPresentationStandingWaveScale) +
                    FMath::Abs(StandingWave.LateralSlope *
                        ResolvedPresentationStandingWaveScale) +
                    FMath::Abs(ReliefStationSlope) +
                    FMath::Abs(ReliefLateralSlope) +
                    FMath::Abs(BoulderWakeStationSlope) +
                    FMath::Abs(BoulderWakeLateralSlope);
                const FVector2D WorkingGradient(
                    BaseStationSlope+StandingWave.StationSlope*ResolvedPresentationStandingWaveScale+
                        ReliefStationSlope+BoulderWakeStationSlope,
                    BaseLateralSlope+StandingWave.LateralSlope*ResolvedPresentationStandingWaveScale+
                        ReliefLateralSlope+BoulderWakeLateralSlope);
                const float SurfaceWorkingSlope = bDirectionalFoamSource
                    ? RaftSimFoamTransport::RisingSurfaceSlope(WorkingGradient,
                        FVector2D(Sample.VelocityMetersPerSecond.X,Sample.VelocityMetersPerSecond.Y))
                    : LegacyWorkingSlope;
                const float RoughnessGate = FMath::SmoothStep(
                    0.015f, 0.06f, SurfaceWorkingSlope);
                Foam = RoughnessGate *
                    FMath::Clamp((Froude - 0.78f) / 1.25f, 0.0f, 1.0f);
                float LegacyFoam = FoamSourceAudit.IsEmpty() ? 0.f : FMath::SmoothStep(0.015f,0.06f,LegacyWorkingSlope)*
                    FMath::Clamp((Froude-.78f)/1.25f,0.f,1.f);
                if (!FoamSourceAudit.IsEmpty())FoamSourceAudit[Index]=FVector4f(LegacyFoam,Foam,0,0);
                // Standing-wave crests aerate at their tops: a wave train
                // below a drop reads as alternating white crest caps over
                // green troughs, not a uniform sheet. Keyed to the same
                // displacement the rigid support rides, so the caps sit on
                // the actual rendered crests.
                const float StandingCrestM =
                    StandingWave.DisplacementMeters *
                    ResolvedPresentationStandingWaveScale;
                if (StandingCrestM > 0.045f && Froude > 0.6f)
                {
                    LegacyFoam = FMath::Max(LegacyFoam,
                        0.55f*FMath::Clamp((StandingCrestM-0.045f)/0.14f,0.f,1.f));
                    Foam = FMath::Max(
                        Foam,
                        0.55f * FMath::Clamp(
                            (StandingCrestM - 0.045f) / 0.14f, 0.0f, 1.0f));
                }
                // A solver-resolved ledge remains a rapid feature even when
                // a stitched crop under-reports its local velocity. Feed its
                // bounded crest lobes into the same vertex channel that
                // drives foam and the raft-local GPU heightfield. The shared
                // helper breaks a repeated solver row laterally, avoiding a
                // smooth full-width white stripe.
                const float HydraulicFeatureEnergy =
                    URaftSimWaterRuntimeAdapter::
                        ComputeCoupledHydraulicFeatureEnergy(
                            RiverCoordinatesM[Index], bCrestLocalizedFoam
                                ? FMath::Max(HydraulicRelief, 0.0f)
                                : HydraulicRelief);
                Foam = FMath::Max(Foam, 0.72f * HydraulicFeatureEnergy);
                LegacyFoam=FMath::Max(LegacyFoam,0.72f*HydraulicFeatureEnergy);
                // Wake aeration joins solver foam; the boulder core fade
                // keeps froth off the hole opened over exposed rock.
                Foam = FMath::Max(Foam * BoulderCoreFade, WakeFoamAdd);
                if (!FoamSourceAudit.IsEmpty())
                {
                    FoamSourceAudit[Index].Z=FMath::Max(LegacyFoam*BoulderCoreFade,WakeFoamAdd);
                    FoamSourceAudit[Index].W=Foam;
                }
                if (WakeFoamAdd > 0.04f)
                {
                    if(!bParallel)++WakeFoamVertexCount;
                }
                SourceFoam[Index] = Foam;
                DepthNorm = FMath::Clamp(Sample.DepthMeters / 4.0f, 0.0f, 1.0f);
                SpeedNorm = FMath::Clamp(Speed / 8.0f, 0.0f, 1.0f);
                if(bParallel)Deferred[Index]={Speed,StandingWave.DisplacementMeters,uint8(WakeFoamAdd>0.04f)};
                else
                {
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
            }

            Vertices[Index].Z = SurfaceZCm;
            // Review bisect: raftsim.FlatWaterNormals 1 discards the solved vertex
            // normal so any remaining banding must come from the material.
            if (bBaseFlatNormals)
            {
                NormalOut = FVector::UpVector;
            }
            Normals[Index] = NormalOut;
            // R = foam, G = depth, B = flow speed (consumed by the photoreal
            // water material for whitewater, depth colour, and flow response).
            VertexColors[Index] = FLinearColor(
                Foam,
                DepthNorm,
                SpeedNorm,
                WetVertexMask[Index] != 0
                    ? (bParallel ? ComputeStationEdgeCoverage(X+BaseUpstreamPad,
                        GridStationN+BaseUpstreamPad+BaseDownstreamPad,
                        ResolvedVertexSpacingMeters,CurvedGridEdgeBlendMeters) : StationEdgeCoverage(X))
                    : 0.0f);
        };
        if(bParallel)
        {
            ParallelFor(TEXT("RaftSimBaseVertices"),BaseVertexCount,256,EvaluateVertex,EParallelForFlags::Unbalanced);
            // Original Y-major/X-minor addition order, including station sums.
            // No floating-point atomics or tree reduction changes the result.
            for(int32 Index=0;Index<BaseVertexCount;++Index)if(WetVertexMask[Index]!=0)
            {
                const int32 X=Index%GridStationN;
                StationWetSurfaceZSum[X]+=float(Vertices[Index].Z);
                ++StationWetSurfaceCount[X];
                WakeFoamVertexCount+=Deferred[Index].WakeFoam;
                ++WetVertexCount;
                DepthSum+=VertexColors[Index].G;
                SpeedSum+=VertexColors[Index].B;
                DepthMetersSum+=WaterSamples[Index].DepthMeters;
                SpeedMpsSum+=Deferred[Index].Speed;
                MaximumAbsoluteStandingWaveM=FMath::Max(MaximumAbsoluteStandingWaveM,FMath::Abs(Deferred[Index].StandingWave));
                MaximumAbsoluteHydraulicReliefM=FMath::Max(MaximumAbsoluteHydraulicReliefM,FMath::Abs(HydraulicReliefMeters[Index]));
            }
        }
        else for(int32 Index=0;Index<BaseVertexCount;++Index)EvaluateVertex(Index);
    };
    if(bBaseVertexAudit && GFrameCounter>=120 && GFrameCounter<184)
    {
        // Every mutated array and statistic, including persistent histories.
        // Copies/restores/comparison are outside measured evaluation/reduction.
        const auto Capture=[&](){return std::make_tuple(Vertices,Normals,VertexColors,
            FlowVelocityMetersPerSecond,ShoreSmoothedSurfaceZCm,FroudeField,FoamSourceAudit,SourceFoam,
            StationWetSurfaceZSum,StationWetSurfaceCount,WakeFoamVertexCount,WetVertexCount,
            DepthSum,SpeedSum,DepthMetersSum,SpeedMpsSum,MaximumAbsoluteStandingWaveM,MaximumAbsoluteHydraulicReliefM);};
        const auto Restore=[&](const auto& State){std::tie(Vertices,Normals,VertexColors,
            FlowVelocityMetersPerSecond,ShoreSmoothedSurfaceZCm,FroudeField,FoamSourceAudit,SourceFoam,
            StationWetSurfaceZSum,StationWetSurfaceCount,WakeFoamVertexCount,WetVertexCount,
            DepthSum,SpeedSum,DepthMetersSum,SpeedMpsSum,MaximumAbsoluteStandingWaveM,MaximumAbsoluteHydraulicReliefM)=State;};
        const auto Before=Capture();
        static uint64 Pair=0;const bool First=(Pair++%2)!=0;
        const double A=FPlatformTime::Seconds();RunBaseVertices(First);const double AMs=(FPlatformTime::Seconds()-A)*1000.;
        const auto FirstState=Capture();Restore(Before);
        const double B=FPlatformTime::Seconds();RunBaseVertices(!First);const double BMs=(FPlatformTime::Seconds()-B)*1000.;
        const bool Exact=FirstState==Capture();
        UE_LOG(LogTemp,Display,TEXT("BaseVertexAudit frame=%llu pair=%llu exact=%d candidate_first=%d vertices=%d wet=%d reference_ms=%.9f candidate_ms=%.9f"),
            GFrameCounter,Pair,int32(Exact),int32(First),Vertices.Num(),WetVertexCount,First ? BMs : AMs,First ? AMs : BMs);
        if(First==bParallelBaseVertices)Restore(FirstState);
        if(!Exact){UE_LOG(LogTemp,Error,TEXT("BaseVertexAudit state mismatch; candidate not qualified"));return;}
    }
    else RunBaseVertices(bParallelBaseVertices);
    LastBoulderWakeFoamVertexCount = WakeFoamVertexCount;

    Perf.Mark(TEXT("base_vertices"));
    // --- Breaking water at hydraulic jumps -------------------------------
    // A supercritical station running into a subcritical neighbour is the
    // solver's own hydraulic jump. Presentation: lift the breaking crest so it
    // leans over its downstream pile, saturate foam generation through the
    // pile, and record the site for bounded aerosol/mist. Visual only.
    BreakingSites.Reset();
    TArray<FBreakingSite> CandidateSites;
    // Raw per-refresh crest/tail lift accumulates here and is eased into the
    // carried vertices after the detection loop, so threshold flicker and
    // lattice hops of the detected front cannot step the carved geometry.
    TArray<float> BreakingLiftTargetCm;
    BreakingLiftTargetCm.SetNumZeroed(Vertices.Num());
    int32 EdgeRejectedSiteCount = 0;
    float MaximumEdgeRejectedIntensity = 0.0f;
    float StrongestEdgeRejectedCoverage = 0.0f;
    float StrongestEdgeRejectedClearanceMeters = 0.0f;
    FVector2D StrongestEdgeRejectedRiverCoordinates = FVector2D::ZeroVector;
    const bool bAuditBreakingHeight = !bLoggedBreakingHeightAudit && GetWorld() &&
        GetWorld()->GetTimeSeconds() >= 10.0f &&
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimBreakingHeightAudit"));
    for (int32 Y = 0; Y < GridLateralN; ++Y)
    {
        for (int32 X = bCartesianFlow ? 0 : PresentationAnalysisStride; X < GridStationN; ++X)
        {
            const int32 Index = Y * GridStationN + X;
            const FVector2D DownstreamDirection = FlowDirectionFor(WaterSamples[Index]);
            const int32 ImmediateUpstreamIndex = bCartesianFlow
                ? RaftSimWaterFlowFrame::OffsetIndex(Index,GridStationN,GridLateralN,
                    DownstreamDirection,-PresentationAnalysisStride) : Index-PresentationAnalysisStride;
            // The full-reach baseline is a visual continuity fallback only.
            // Hydraulic breaking sites alter rigid raft support, so both
            // sides of a detected transition must belong to the live solver.
            if (ImmediateUpstreamIndex == INDEX_NONE || LiveSolverWetVertexMask[Index] == 0 ||
                LiveSolverWetVertexMask[ImmediateUpstreamIndex] == 0)
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
                (bCartesianFlow || X >= 2 * PresentationAnalysisStride))
            {
                const int32 FarUpstreamIndex = bCartesianFlow
                    ? RaftSimWaterFlowFrame::OffsetIndex(Index,GridStationN,GridLateralN,
                        DownstreamDirection,-2*PresentationAnalysisStride) : Index-2*PresentationAnalysisStride;
                if (FarUpstreamIndex != INDEX_NONE && LiveSolverWetVertexMask[FarUpstreamIndex] != 0 &&
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

            const int32 UpstreamStationIndex = UpstreamIndex%GridStationN;
            const int32 UpstreamLateralIndex = UpstreamIndex/GridStationN;
            const float UpstreamStationCoverage = StationEdgeCoverage(UpstreamStationIndex);
            const float LocalStationCoverage = StationEdgeCoverage(X);
            const float UpstreamLateralCoverage = ComputeLateralWetCoverage(
                UpstreamLateralIndex,
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
            float PresentationCoverage = FMath::Min(
                UpstreamStationCoverage * UpstreamLateralCoverage,
                LocalStationCoverage * LocalLateralCoverage);
            float PresentationEdgeClearanceMeters = FMath::Min(
                ComputePresentationSurfaceEdgeClearanceMeters(
                    UpstreamStationIndex,
                    GridStationN,
                    UpstreamLateralIndex,
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
            if (bCartesianFlow)
            {
                PresentationEdgeClearanceMeters=FMath::Min(CartesianWetEdgeSteps[Index],
                    CartesianWetEdgeSteps[UpstreamIndex])*ResolvedVertexSpacingMeters;
                const float T=FMath::Clamp(PresentationEdgeClearanceMeters/
                    FMath::Max(CurvedGridLateralEdgeBlendMeters,KINDA_SMALL_NUMBER),0.f,1.f);
                PresentationCoverage=T*T*(3.f-2.f*T);
            }
            // Legacy overlay maps need a large fully opaque margin because a
            // separate crest/roller sheet can expose their rectangular edge.
            // South Fork has one continuous carrier: rejecting its physical
            // jumps until they were 15 m from both banks discarded the actual
            // Troublemaker hole (measured at 3 m clearance, coverage 0.741)
            // and left the named rapid visually flat. On the single surface,
            // accept the solver jump inside the organic bank feather and
            // deform only existing wet carrier vertices; no second surface or
            // rectangular patch is created.
            const float MinimumBreakingCoverage =
                (bSingleLiveWaterSurfaceEnabled || bSharedBreakingReliefEnabled) ? 0.55f : 0.999f;
            const float MinimumBreakingClearanceMeters =
                (bSingleLiveWaterSurfaceEnabled || bSharedBreakingReliefEnabled)
                ? FMath::Max(ResolvedVertexSpacingMeters, 3.0f)
                : BreakingSiteInteriorClearanceMeters;
            if (bAuditBreakingHeight)
            {
                const float RawRise = WaterSamples[Index].SurfaceHeightMeters -
                    WaterSamples[UpstreamIndex].SurfaceHeightMeters;
                const float OpticalRise = PresentationSurfaceHeightMeters[Index] -
                    PresentationSurfaceHeightMeters[UpstreamIndex];
                const auto RawDimensions = URaftSimWaterRuntimeAdapter::ComputeHydraulicCrestDimensionsMeters(
                    WaterSamples[UpstreamIndex].DepthMeters, UpstreamFroude, RawRise);
                const auto OpticalDimensions = URaftSimWaterRuntimeAdapter::ComputeHydraulicCrestDimensionsMeters(
                    WaterSamples[UpstreamIndex].DepthMeters, UpstreamFroude, OpticalRise);
                UE_LOG(LogTemp, Display,
                    TEXT("BreakingHeightAudit world_s=%.3f station_m=%.3f lateral_m=%.3f "
                         "up_depth_m=%.4f up_fr=%.4f down_fr=%.4f raw_rise_m=%.4f "
                         "optical_rise_m=%.4f raw_extra_m=%.4f optical_extra_m=%.4f "
                         "coverage=%.3f clearance_m=%.3f accepted=%d"),
                    GetWorld()->GetTimeSeconds(), RiverCoordinatesM[UpstreamIndex].X,
                    RiverCoordinatesM[UpstreamIndex].Y, WaterSamples[UpstreamIndex].DepthMeters,
                    UpstreamFroude, LocalFroude, RawRise, OpticalRise,
                    RawDimensions.X, OpticalDimensions.X, PresentationCoverage,
                    PresentationEdgeClearanceMeters,
                    PresentationCoverage >= MinimumBreakingCoverage &&
                        PresentationEdgeClearanceMeters >= MinimumBreakingClearanceMeters);
            }
            if (PresentationCoverage < MinimumBreakingCoverage ||
                PresentationEdgeClearanceMeters <
                    MinimumBreakingClearanceMeters)
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
            const float LiftCm = BreakingCrestLiftMeters * kSurfCmPerM *
                Intensity * ShoreDisplacementWeight[UpstreamIndex];
            BreakingLiftTargetCm[UpstreamIndex] += LiftCm;
            BreakingLiftTargetCm[Index] -= 0.45f * LiftCm;

            const float BreakingFrothStrength = FMath::Lerp(
                0.62f, 1.0f, FMath::Sqrt(Intensity));
            if (!bCrestLocalizedFoam)
            {
                SourceFoam[UpstreamIndex] = FMath::Max(
                    SourceFoam[UpstreamIndex], 0.75f * BreakingFrothStrength);
                SourceFoam[Index] = FMath::Max(
                    SourceFoam[Index], 0.95f * BreakingFrothStrength);
            }

            // Decaying tailwater wave train: the oscillatory surface every
            // hydraulic jump sheds downstream. Alternating, exponentially
            // decaying crests/troughs (bounded by the crest lift) give the
            // rapid readable hydraulic volume instead of a flat run-out, and
            // each surviving crest keeps generating a little foam.
            const int32 TailStepCount = FMath::Max(
                1,
                FMath::RoundToInt(18.0f / ResolvedVertexSpacingMeters));
            int32 PreviousTailIndex = Index;
            for (int32 TailStep = 1; TailStep <= TailStepCount; ++TailStep)
            {
                const int32 TailIndex = bCartesianFlow
                    ? RaftSimWaterFlowFrame::OffsetIndex(Index,GridStationN,GridLateralN,DownstreamDirection,TailStep)
                    : Index+TailStep;
                if (TailIndex == INDEX_NONE || (!bCartesianFlow && X + TailStep >= GridStationN) ||
                    WetVertexMask[TailIndex] == 0)
                {
                    break;
                }
                if (TailIndex==PreviousTailIndex) continue;
                PreviousTailIndex=TailIndex;
                const float TailDistanceMeters =
                    TailStep * ResolvedVertexSpacingMeters;
                const float Decay = FMath::Exp(-0.14f * TailDistanceMeters);
                const float Phase = FMath::Cos(
                    (2.05f / 3.0f) * TailDistanceMeters);
                BreakingLiftTargetCm[TailIndex] += 0.62f * LiftCm * Decay *
                    Phase * ShoreDisplacementWeight[TailIndex];
                if (!bCrestLocalizedFoam)
                {
                    SourceFoam[TailIndex] = FMath::Max(
                        SourceFoam[TailIndex],
                        Intensity * FMath::Max(Phase, 0.0f) * 0.65f * Decay + 0.38f * Decay);
                }
            }

            FBreakingSite Site;
            Site.WorldPositionCm = Vertices[UpstreamIndex];
            Site.WorldVelocityMps = WaterSamples[UpstreamIndex].VelocityMetersPerSecond;
            Site.FlowDirection = FlowDirectionFor(WaterSamples[UpstreamIndex]);
            if (bUsesCurvedRiverCoordinates)
            {
                // Spray/lip placement consumes world velocity. Convert only
                // at this boundary; crest/support/foam coordinates stay local.
                const FVector Tangent = Tangents[UpstreamIndex].TangentX;
                const FVector2D WorldVelocity = RaftSimFoamTransport::TransformFieldVelocity(
                    FVector2D(Site.WorldVelocityMps.X, Site.WorldVelocityMps.Y),
                    FVector2D(Tangent.X, Tangent.Y), WaterAdapter->GetRiverWorldYSign());
                Site.WorldVelocityMps = FVector(WorldVelocity.X, WorldVelocity.Y, 0.);
            }
            Site.RiverCoordinatesMeters = RiverCoordinatesM[UpstreamIndex];
            Site.Intensity = Intensity;
            Site.HydraulicCrestDimensionsMeters =
                URaftSimWaterRuntimeAdapter::ComputeHydraulicCrestDimensionsMeters(
                    WaterSamples[UpstreamIndex].DepthMeters, UpstreamFroude,
                    (WaterSamples[Index].SurfaceHeightMeters - WaterSamples[UpstreamIndex].SurfaceHeightMeters));
            Site.HydraulicSpillingFraction = FMath::SmoothStep(1.28f, 1.7f, UpstreamFroude);
            Site.PresentationCoverage = PresentationCoverage;
            Site.PresentationEdgeClearanceMeters =
                PresentationEdgeClearanceMeters;
            CandidateSites.Add(Site);
        }
    }
    if (bAuditBreakingHeight) bLoggedBreakingHeightAudit = true;
    // Ease the accumulated crest/tail lift into the carried vertices. The
    // slower release also keeps a momentary detection dropout from deleting
    // a rendered crest outright; residue decays over roughly half a second.
    if (SmoothedBreakingLiftCm.Num() != Vertices.Num())
    {
        SmoothedBreakingLiftCm.SetNumZeroed(Vertices.Num());
    }
    const float LiftAttackBlend = 1.0f - FMath::Exp(
        -8.0f * FMath::Max(RefreshIntervalSeconds, 0.0f));
    const float LiftReleaseBlend = 1.0f - FMath::Exp(
        -5.0f * FMath::Max(RefreshIntervalSeconds, 0.0f));
    for (int32 LiftIndex = 0; LiftIndex < Vertices.Num(); ++LiftIndex)
    {
        const float TargetCm = BreakingLiftTargetCm[LiftIndex];
        float SmoothedCm = FMath::Lerp(
            SmoothedBreakingLiftCm[LiftIndex],
            TargetCm,
            FMath::Abs(TargetCm) > FMath::Abs(SmoothedBreakingLiftCm[LiftIndex])
                ? LiftAttackBlend
                : LiftReleaseBlend);
        if (TargetCm == 0.0f && FMath::Abs(SmoothedCm) < 0.05f)
        {
            SmoothedCm = 0.0f;
        }
        SmoothedBreakingLiftCm[LiftIndex] = SmoothedCm;
        if (SmoothedCm != 0.0f && !bSharedBreakingReliefEnabled)
        {
            Vertices[LiftIndex].Z += SmoothedCm;
        }
    }

    // Strongest sites first, deduplicated to 6 m so one long jump line yields a
    // handful of overlapping crest lobes rather than a wall of emitters.
    CandidateSites.Sort([](const FBreakingSite& A, const FBreakingSite& B)
        { return A.Intensity > B.Intensity; });
    constexpr int32 kMaxBreakingSites = 24;
    constexpr float kMinSiteSpacingCm = 600.0f;
    TArray<FBreakingSite> AcceptedCandidates;
    for (const FBreakingSite& Candidate : CandidateSites)
    {
        if (AcceptedCandidates.Num() >= kMaxBreakingSites)
        {
            break;
        }
        bool bTooClose = false;
        for (const FBreakingSite& Accepted : AcceptedCandidates)
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
            AcceptedCandidates.Add(Candidate);
        }
    }
    // Detection has no frame-to-frame identity: candidates are re-found and
    // re-ranked from the raw Froude field every refresh, so rank swaps,
    // lattice hops of the detected front, and dedupe-survivor changes made
    // every site-keyed presentation snap at the hydraulic cadence. Fold the
    // detections into the persistent registry instead; it publishes the
    // eased, faded BreakingSites consumed by the pocket/boil carve, rigid
    // support, lips, rollers, and mist anchors below.
    UpdatePersistentBreakingSites(AcceptedCandidates);

    TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> SupportSites;
    SupportSites.Reserve(BreakingSites.Num());
    for (const FBreakingSite& Site : BreakingSites)
    {
        URaftSimWaterRuntimeAdapter::FSupportBreakingSite& SupportSite =
            SupportSites.AddDefaulted_GetRef();
        SupportSite.RiverCoordinatesMeters = Site.RiverCoordinatesMeters;
        SupportSite.FlowDirection = Site.FlowDirection;
        SupportSite.bLocalEnvelopeCap = bSpatialBreakingReview;
        SupportSite.Intensity = Site.Intensity *
            (bSharedBreakingReliefEnabled ? Site.PresentationWeight : 1.0f);
        if (bSharedBreakingReliefEnabled && CVarRaftSimChilkoHydraulicCrestScale.GetValueOnGameThread() != 0)
        {
            SupportSite.PhysicalCrestHeightMeters = Site.HydraulicCrestDimensionsMeters.X * Site.PresentationWeight;
            SupportSite.PhysicalCrestLengthMeters = Site.HydraulicCrestDimensionsMeters.Y;
            SupportSite.SpillingFraction = Site.HydraulicSpillingFraction * Site.PresentationWeight;
        }
    }
    if (bStatefulCrestReview || bPlayableCrestRefinement)
    {
        MacroCrestSites.Reset();
        bool bPhysical=SupportSites.Num()<GridStationN;
        for (const auto& Site:SupportSites) bPhysical &= Site.PhysicalCrestHeightMeters>=0;
        if (!bPhysical)
        {
            UE_LOG(LogTemp,Error,TEXT("Fine crest reconstruction rejects legacy sites or atlas overflow; retaining coarse surface"));
            MacroCrestDisplacementCm.Reset();MacroCrestShoreWeights.Reset();
        }
        else
        {
            MacroCrestDisplacementCm.Init(0.0f,Vertices.Num());
            MacroCrestShoreWeights=ShoreDisplacementWeight;
            for (const auto& Site:SupportSites)
            {
                MacroCrestSites.Add(FVector4f(Site.RiverCoordinatesMeters.X,Site.RiverCoordinatesMeters.Y,
                    Site.PhysicalCrestHeightMeters,Site.PhysicalCrestLengthMeters));
                MacroCrestSites.Add(FVector4f(Site.Intensity,Site.SpillingFraction,Site.bLocalEnvelopeCap ? 1 : 0,
                    FMath::Atan2(Site.FlowDirection.Y,Site.FlowDirection.X)));
            }
        }
    }
    static const bool bFullCrestScan=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFullCrestScan"));
    TSharedPtr<FRaftSimIndexedBreakingProfile,ESPMode::ThreadSafe> SharedCrestProfile;
    if (bCartesianFlow && bSingleLiveWaterSurfaceEnabled && bSharedBreakingReliefEnabled)
    {
        MacroCrestDisplacementCm.Init(0.f,Vertices.Num());
        MacroCrestShoreWeights=ShoreDisplacementWeight;
        const float Lift=BreakingCrestLiftMeters, Spacing=ResolvedVertexSpacingMeters;
        const float Scale=ResolvedPresentationHydraulicReliefScale;
        const float Sign=WaterAdapter->GetRiverWorldYSign();
        CartesianCrestInput.ProfileKey={Lift,Spacing,Scale,Sign};
        CartesianCrestInput.NonzeroRegionsCm.Reset();
        for (const auto& Site:SupportSites)
        {
            CartesianCrestInput.ProfileKey.Append({Site.RiverCoordinatesMeters.X,Site.RiverCoordinatesMeters.Y,
                Site.PhysicalCrestHeightMeters,Site.PhysicalCrestLengthMeters,Site.Intensity,
                Site.SpillingFraction,Site.FlowDirection.X,Site.FlowDirection.Y,Site.bLocalEnvelopeCap ? 1. : 0.});
            const bool Physical=Site.PhysicalCrestHeightMeters>=0.f;
            const float Length=FMath::Clamp(Site.PhysicalCrestLengthMeters,2.f,7.f);
            const float SafeSpacing=FMath::Max(Spacing,.05f);
            const double Low=Physical ? -3.*Length : -SafeSpacing;
            const double High=Physical ? 7.*Length : (2+FMath::Max(1,FMath::RoundToInt(18.f/SafeSpacing)))*SafeSpacing;
            const double Across=Physical ? 12. : 3.*FMath::Sqrt(-FMath::Loge(.02));
            FBox2D Bounds(ForceInit);
            for (double D:{Low,High}) for (double A:{-Across,Across})
            {
                const FVector2D P=Site.RiverCoordinatesMeters+RaftSimWaterFlowFrame::ToField(FVector2D(D,A),Site.FlowDirection);
                Bounds+=FVector2D(P.X*100.,P.Y*100.*Sign);
            }
            // Conservative roundoff padding only. The underlying profile's
            // exact compact support, not visual importance, controls culling.
            CartesianCrestInput.NonzeroRegionsCm.Add(Bounds.ExpandBy(.01));
        }
        // Capture the actual support records, not float-packed shader records
        // or reconstructed angles. The same profile survives between refreshes.
        const auto IndexedProfile=MakeShared<FRaftSimIndexedBreakingProfile,ESPMode::ThreadSafe>(SupportSites,Lift,Spacing);
        RaftSimBreakingTileAudit::Run(*IndexedProfile,RiverCoordinatesM);
        SharedCrestProfile=IndexedProfile;
        // Actual 64-pair changing-input audit: exact topology, faster in
        // every pair and both orders. Retain an independent reference switch.
        static const bool bRangeEnabled=[]
        {
            FString Path;
            return !FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceCrestRange")) ||
                FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestRangeAudit="),Path);
        }();
        if(bRangeEnabled)
        {
            static const bool bPrepareRange=[]
            {
                FString Path;
                return !FParse::Param(FCommandLine::Get(),TEXT("RaftSimUnpreparedCrestRange")) ||
                    FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestPreparedRangeAudit="),Path);
            }();
            if(bPrepareRange)
            {
                const double PrepareStart=FPlatformTime::Seconds();
                const auto Prepared=MakeShared<FRaftSimPreparedBreakingHeightRange,ESPMode::ThreadSafe>(SupportSites);
                CartesianCrestInput.PreparedHeightRangeWidthAtWorldXYCm=[Prepared,Scale,Sign](const FBox2D& Box)
                {
                    FBox2D Field(ForceInit);
                    Field+=FVector2D(Box.Min.X*.01,Box.Min.Y*.01*Sign);
                    Field+=FVector2D(Box.Max.X*.01,Box.Max.Y*.01*Sign);
                    return Prepared->WidthMeters(Field)*FMath::Abs(Scale)*100.f;
                };
                CartesianCrestInput.PreparedRangeConstructionMs=(FPlatformTime::Seconds()-PrepareStart)*1000.;
                static const bool bTightRange=[]
                {
                    FString Path;
                    return !FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceCrestInterval")) ||
                        FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestIntervalAudit="),Path);
                }();
                if(bTightRange)CartesianCrestInput.TightHeightRangeWidthAtWorldXYCm=[Prepared,Scale,Sign](const FBox2D& Box)
                {
                    FBox2D Field(ForceInit);
                    Field+=FVector2D(Box.Min.X*.01,Box.Min.Y*.01*Sign);
                    Field+=FVector2D(Box.Max.X*.01,Box.Max.Y*.01*Sign);
                    return Prepared->WidthMeters<true>(Field)*FMath::Abs(Scale)*100.f;
                };
                static bool bLoggedPreparedRange=false;
                if(!bLoggedPreparedRange)
                {
                    UE_LOG(LogTemp,Display,TEXT("Prepared crest range active: immutable spatial index with complete-scan fallback; tight_interval=%d; sampled heights and refinement tolerances unchanged"),
                        !FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceCrestInterval")));
                    bLoggedPreparedRange=true;
                }
            }
            CartesianCrestInput.HeightRangeWidthAtWorldXYCm=[Sites=SupportSites,Scale,Sign](const FBox2D& Box)
            {
                FBox2D Field(ForceInit);
                Field+=FVector2D(Box.Min.X*.01,Box.Min.Y*.01*Sign);
                Field+=FVector2D(Box.Max.X*.01,Box.Max.Y*.01*Sign);
                return RaftSimBreakingHeightRange::WidthMeters(Sites,Field)*FMath::Abs(Scale)*100.f;
            };
        }
        CartesianCrestInput.HeightAtWorldXYCm=[Sites=SupportSites,IndexedProfile,Lift,Spacing,Scale,Sign](const FVector2D& P)
        {
            static const bool bHashed=FParse::Param(FCommandLine::Get(),TEXT("RaftSimHashedBreakingTiles"));
            static const bool bSkipEmpty=FParse::Param(FCommandLine::Get(),TEXT("RaftSimSkipEmptyCrestTiles"));
            const FVector2D Field(P.X*.01,P.Y*.01*Sign);
            return (bFullCrestScan ? URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(
                Field,Sites,Lift,Spacing) : IndexedProfile->SampleWithEmptyTileSkip(Field,nullptr,!bHashed,bSkipEmpty))*Scale*100.f;
        };
#if !UE_BUILD_SHIPPING
        static const bool bFineIndex=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFineCrestIndex"));
        static const bool bFineAudit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFineCrestIndexAudit"));
        if((bFineIndex || bFineAudit) && !bFullCrestScan && GetWorld() &&
            GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")))
        {
            const auto Fine=MakeShared<FRaftSimFineIndexedBreakingProfile,ESPMode::ThreadSafe>(SupportSites,Lift,Spacing);
            const auto Audit=bFineAudit ? MakeShared<FRaftSimFineCrestIndexAudit,ESPMode::ThreadSafe>()
                : TSharedPtr<FRaftSimFineCrestIndexAudit,ESPMode::ThreadSafe>();
            CartesianCrestInput.HeightAtWorldXYCm=[Fine,IndexedProfile,Audit,Scale,Sign](const FVector2D& P)
            {
                const FVector2D Field(P.X*.01,P.Y*.01*Sign);
                const float Result=Fine->Sample(Field)*Scale*100.f;
                if(Audit)Audit->Compare(IndexedProfile->Sample(Field)*Scale*100.f,Result);
                return Result;
            };
            static bool bLoggedFine=false;
            if(!bLoggedFine)
            {
                UE_LOG(LogTemp,Display,TEXT("Fine crest index candidate active: tile_m=2 indexed=%d tiles=%d dense_tiles=%d audit=%d; unchanged physical evaluator and refinement tolerance"),
                    Fine->IsIndexed(),Fine->TileCount(),Fine->DenseTileCount(),int32(bFineAudit));
                bLoggedFine=true;
            }
        }
        // Isolated-module timings improved, but installed whole-frame A/B
        // failed repeatability. Retain as a diagnostic, never a default.
        static const bool bInlinePhysical=FParse::Param(FCommandLine::Get(),TEXT("RaftSimInlinePhysicalCrests"));
        static const bool bInlineAudit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimInlinePhysicalCrestAudit"));
        if((bInlinePhysical || bInlineAudit) && !bFullCrestScan && !bFineIndex && !bFineAudit && GetWorld() &&
            GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")))
        {
            const auto Audit=bInlineAudit ? MakeShared<FRaftSimInlineCrestAudit,ESPMode::ThreadSafe>()
                : TSharedPtr<FRaftSimInlineCrestAudit,ESPMode::ThreadSafe>();
            CartesianCrestInput.HeightAtWorldXYCm=[IndexedProfile,Audit,Scale,Sign](const FVector2D& P)
            {
                const FVector2D Field(P.X*.01,P.Y*.01*Sign);
                const float Result=IndexedProfile->SamplePhysicalInline(Field)*Scale*100.f;
                if(Audit)Audit->Compare(IndexedProfile->Sample(Field)*Scale*100.f,Result);
                return Result;
            };
            static bool bLoggedInline=false;
            if(!bLoggedInline)
            {
                UE_LOG(LogTemp,Display,TEXT("Inline physical crest candidate active: audit=%d; original 8m index, profile and tolerances unchanged"),int32(bInlineAudit));
                bLoggedInline=true;
            }
        }
#endif
        static const bool bEmptyTileAudit=[]{FString P;return FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestEmptyTileAudit="),P);}();
        if(bEmptyTileAudit)for(int32 Kind=0;Kind<2;++Kind)
            CartesianCrestInput.EmptyTileComparisonHeight[Kind]=[IndexedProfile,Scale,Sign,Kind](const FVector2D& P)
            {return IndexedProfile->SampleWithEmptyTileSkip(FVector2D(P.X*.01,P.Y*.01*Sign),nullptr,true,Kind==1)*Scale*100.f;};
    }
    if (WaterAdapter)
    {
        // Mirror the accepted sites into rigid support so the ridden surface
        // rises with the rendered crest, dip, and tailwater train. The 2 cm
        // z-fight lift and the plunge-pocket pass below stay render-only.
        WaterAdapter->ConfigureRaftSupportBreakingSites(
            SupportSites, BreakingCrestLiftMeters, ResolvedVertexSpacingMeters);
    }

    // One-shot measurement, never part of ordinary rendering or performance
    // runs. Compare the continuous support crest with the EXACT two triangles
    // used by the macro carrier. More tessellation only helps if this error is
    // material; do not increase physical wave amplitudes to hide a sampling bug.
    FString CrestAuditPath;
    if (!bLoggedCrestSamplingAudit && bSharedBreakingReliefEnabled && GetWorld() &&
        GetWorld()->GetTimeSeconds() >= 10.0f &&
        FParse::Value(FCommandLine::Get(), TEXT("RaftSimCrestSamplingAudit="), CrestAuditPath))
    {
        bLoggedCrestSamplingAudit = true;
        const auto CrestAt = [&](const FVector2D& P)
        {
            return URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(
                P, SupportSites, BreakingCrestLiftMeters, ResolvedVertexSpacingMeters) *
                ResolvedPresentationHydraulicReliefScale;
        };
        TArray<float> CoarseCrest;
        CoarseCrest.SetNumUninitialized(Vertices.Num());
        for (int32 I = 0; I < CoarseCrest.Num(); ++I)
            CoarseCrest[I] = CrestAt(RiverCoordinatesM[I]) * ShoreDisplacementWeight[I];
        double ErrorSquared = 0.0, MaxError = 0.0, MaxContinuous = 0.0, MaxInterpolated = 0.0;
        int32 SampleCount = 0, WetCellCount = 0;
        FVector2D WorstPosition = FVector2D::ZeroVector;
        for (int32 Y = 0; Y + 1 < GridLateralN; ++Y)
        for (int32 X = 0; X + 1 < GridStationN; ++X)
        {
            const int32 A = Y * GridStationN + X, B = A + 1, C = A + GridStationN, D = C + 1;
            if (!WetVertexMask[A] || !WetVertexMask[B] || !WetVertexMask[C] || !WetVertexMask[D]) continue;
            ++WetCellCount;
            // Quarter-cell interior/edge points correspond to the current
            // two-level refinement. Include source vertices as a consistency check.
            for (int32 J = 0; J <= 4; ++J)
            for (int32 I = 0; I <= 4; ++I)
            {
                const double U = I * 0.25, V = J * 0.25;
                const int32 IA = U + V <= 1.0 ? A : B;
                const int32 IB = C;
                const int32 IC = U + V <= 1.0 ? B : D;
                const double WA = U + V <= 1.0 ? 1.0 - U - V : 1.0 - V;
                const double WB = U + V <= 1.0 ? V : 1.0 - U;
                const double WC = 1.0 - WA - WB;
                const FVector2D P = RiverCoordinatesM[IA] * WA + RiverCoordinatesM[IB] * WB + RiverCoordinatesM[IC] * WC;
                const double Shore = ShoreDisplacementWeight[IA] * WA + ShoreDisplacementWeight[IB] * WB + ShoreDisplacementWeight[IC] * WC;
                const double Continuous = CrestAt(P) * Shore;
                const double Interpolated = CoarseCrest[IA] * WA + CoarseCrest[IB] * WB + CoarseCrest[IC] * WC;
                const double Error = FMath::Abs(Continuous - Interpolated);
                if (Error > MaxError) { MaxError = Error; WorstPosition = P; }
                ErrorSquared += Error * Error;
                MaxContinuous = FMath::Max(MaxContinuous, FMath::Abs(Continuous));
                MaxInterpolated = FMath::Max(MaxInterpolated, FMath::Abs(Interpolated));
                ++SampleCount;
            }
        }
        const TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
        Report->SetStringField(TEXT("map"), GetWorld()->GetMapName());
        Report->SetStringField(TEXT("scope"), TEXT("Shared analytic crest only; excludes hydraulic mean, pocket, boil and GPU perturbation. Wet cells only; repeated boundary samples retained."));
        Report->SetNumberField(TEXT("world_seconds"), GetWorld()->GetTimeSeconds());
        Report->SetNumberField(TEXT("spacing_m"), ResolvedVertexSpacingMeters);
        Report->SetNumberField(TEXT("relief_scale"), ResolvedPresentationHydraulicReliefScale);
        Report->SetNumberField(TEXT("wet_cells"), WetCellCount);
        Report->SetNumberField(TEXT("samples"), SampleCount);
        Report->SetNumberField(TEXT("maximum_error_m"), MaxError);
        Report->SetNumberField(TEXT("rms_error_m"), SampleCount ? FMath::Sqrt(ErrorSquared / SampleCount) : 0.0);
        Report->SetNumberField(TEXT("maximum_continuous_absolute_crest_m"), MaxContinuous);
        Report->SetNumberField(TEXT("maximum_interpolated_absolute_crest_m"), MaxInterpolated);
        Report->SetNumberField(TEXT("worst_station_m"), WorstPosition.X);
        Report->SetNumberField(TEXT("worst_lateral_m"), WorstPosition.Y);
        TArray<TSharedPtr<FJsonValue>> SiteRecords;
        for (const auto& Site : SupportSites)
        {
            const TSharedRef<FJsonObject> Record = MakeShared<FJsonObject>();
            Record->SetNumberField(TEXT("station_m"), Site.RiverCoordinatesMeters.X);
            Record->SetNumberField(TEXT("lateral_m"), Site.RiverCoordinatesMeters.Y);
            Record->SetNumberField(TEXT("height_m"), Site.PhysicalCrestHeightMeters);
            Record->SetNumberField(TEXT("length_m"), Site.PhysicalCrestLengthMeters);
            Record->SetNumberField(TEXT("flow_direction_x"), Site.FlowDirection.X);
            Record->SetNumberField(TEXT("flow_direction_y"), Site.FlowDirection.Y);
            Record->SetNumberField(TEXT("spilling_fraction"), Site.SpillingFraction);
            Record->SetNumberField(TEXT("intensity"), Site.Intensity);
            Record->SetBoolField(TEXT("local_envelope_cap"), Site.bLocalEnvelopeCap);
            SiteRecords.Add(MakeShared<FJsonValueObject>(Record));
        }
        Report->SetArrayField(TEXT("sites"), SiteRecords);
        FString Json;
        FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Json));
        const bool bSaved = FFileHelper::SaveStringToFile(Json, *CrestAuditPath);
        UE_LOG(LogTemp, Display, TEXT("CrestSamplingAudit samples=%d max_error_m=%.9g max_crest_m=%.9g saved=%d path=%s"),
            SampleCount, MaxError, MaxContinuous, bSaved, *CrestAuditPath);
    }

    Perf.Mark(TEXT("breaking_detection"));
    // Give the strongest accepted interior jumps a coherent plan-view
    // plunge pocket beneath the connected crest-to-plunge membrane. The
    // solver selects every site; this pass only changes presentation vertices
    // and foam. A bounded combined displacement prevents nearby accepted sites
    // from stacking into fabricated cliffs, while the pocket centre stays
    // darker than its broken shoulders and downstream aerated return.
    // Each site contributes through its eased PresentationWeight, so pocket
    // ownership changing hands cannot toggle the carve in one refresh; while
    // a handoff is in flight a retiring and an arriving site briefly overlap
    // at partial weight inside the same combined clamps.
    TArray<uint8> BreakingPresentationVertexMask;
    BreakingPresentationVertexMask.Init(0, Vertices.Num());
    const int32 BreakingPresentationSiteCount = bSpatialBreakingReview
        ? BreakingSites.Num() : FMath::Min(BreakingSites.Num(), kMaximumBreakingPresentationSites);
    TArray<FBreakingSite> WeightedPresentationSites;
    for (const FBreakingSite& Site : BreakingSites)
    {
        if (Site.PresentationWeight > 0.01f)
        {
            WeightedPresentationSites.Add(Site);
        }
    }
    // Every accepted physical jump may contribute, but only to nearby rows.
    // This spatial cache is independent of camera/raft position and excludes
    // irrelevant sites before the per-vertex exponential/trigonometric work.
    // Rigid support receives the same full site list and local-envelope cap;
    // these row subsets are a render evaluation optimization, not authority.
    struct FStationBreakingSites
    {
        TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Support;
        TArray<FBreakingSite> Presentation;
    };
    TArray<FStationBreakingSites> StationBreakingSites;
    if (bSpatialBreakingReview)
    {
        StationBreakingSites.SetNum(GridStationN);
        const float StartStation = RiverCoordinatesM[0].X;
        const float Spacing = FMath::Max(ResolvedVertexSpacingMeters, 0.05f);
        const auto RowRange = [this, StartStation, Spacing](float Low, float High)
        {
            return FIntPoint(
                FMath::Clamp(FMath::FloorToInt((Low - StartStation) / Spacing), 0, GridStationN),
                FMath::Clamp(FMath::CeilToInt((High - StartStation) / Spacing), -1, GridStationN - 1));
        };
        for (const auto& Site : SupportSites)
        {
            const float Length = FMath::Clamp(Site.PhysicalCrestLengthMeters, 2.0f, 7.0f);
            const float MinRelative = Site.PhysicalCrestHeightMeters >= 0.0f ? -3.0f * Length : -Spacing;
            const float MaxRelative = Site.PhysicalCrestHeightMeters >= 0.0f ? 7.0f * Length
                : (2 + FMath::Max(1, FMath::RoundToInt(18.0f / Spacing))) * Spacing;
            const FVector2D Bounds = RaftSimWaterFlowFrame::XBounds(Site.FlowDirection,MinRelative,MaxRelative,
                Site.PhysicalCrestHeightMeters >= 0.f ? 12. : 3.*FMath::Sqrt(-FMath::Loge(.02)));
            const FIntPoint Range = RowRange(Site.RiverCoordinatesMeters.X + Bounds.X,
                Site.RiverCoordinatesMeters.X + Bounds.Y);
            for (int32 Row = Range.X; Row <= Range.Y; ++Row)
                StationBreakingSites[Row].Support.Add(Site);
        }
        for (const FBreakingSite& Site : WeightedPresentationSites)
        {
            const FVector2D Bounds = RaftSimWaterFlowFrame::XBounds(Site.FlowDirection,-32.,23.,12.);
            const FIntPoint Range = RowRange(Site.RiverCoordinatesMeters.X + Bounds.X,
                Site.RiverCoordinatesMeters.X + Bounds.Y);
            for (int32 Row = Range.X; Row <= Range.Y; ++Row)
                StationBreakingSites[Row].Presentation.Add(Site);
        }
    }
    const auto LocalPresentationWeight = [this](const FVector2D& Relative)
    {
        if (!bSpatialBreakingReview) return 1.0f;
        const float Downstream = static_cast<float>(Relative.X);
        const float Across = static_cast<float>(FMath::Abs(Relative.Y));
        return FMath::SmoothStep(-32.0f, -30.0f, Downstream) *
            (1.0f - FMath::SmoothStep(20.5f, 23.0f, Downstream)) *
            (1.0f - FMath::SmoothStep(10.0f, 12.0f, Across));
    };
    // Entry-tongue foam suppression, filled alongside the pocket carve and
    // consumed by the foam advection pass below so the accelerating V above
    // each jump stays glassy instead of whitening with Froude-generated foam.
    TArray<float> TongueFoamSuppression;
    TongueFoamSuppression.SetNumZeroed(Vertices.Num());
    const bool bDownstreamBoilMicroreliefEnabled =
        CVarRaftSimDownstreamBoilMicrorelief.GetValueOnGameThread() != 0;
    ActiveDownstreamBoilSiteCount = bDownstreamBoilMicroreliefEnabled
        ? BreakingPresentationSiteCount
        : 0;
    const bool bUseHydraulicFoamBudget = bCartesianFlow && bCrestLocalizedFoam &&
        CVarRaftSimChilkoHydraulicCrestScale.GetValueOnGameThread()!=0;
    const bool bPhysicalCrestFoam=CVarRaftSimChilkoHydraulicCrestScale.GetValueOnGameThread()!=0;
    static const bool bSerialBreakingVertices=FParse::Param(FCommandLine::Get(),TEXT("RaftSimSerialBreakingVertices"));
    FString BreakingVertexAuditPath;
#if !UE_BUILD_SHIPPING
    if (GetWorld() && GetWorld()->GetTimeSeconds()>=10.f)
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimBreakingVertexAudit="),BreakingVertexAuditPath);
    if (!BreakingVertexAuditPath.IsEmpty() && FPaths::FileExists(BreakingVertexAuditPath))BreakingVertexAuditPath.Reset();
#endif
    // The comparison owns the SAME pre-pass input, not a different trajectory.
    TArray<FVector> SerialVertices;
    TArray<float> SerialFoam,SerialCrest,SerialTongue;
    TArray<uint8> SerialMask;
    if (!BreakingVertexAuditPath.IsEmpty())
    {
        SerialVertices=Vertices;SerialFoam=SourceFoam;SerialCrest=MacroCrestDisplacementCm;
        SerialTongue=TongueFoamSuppression;SerialMask=BreakingPresentationVertexMask;
    }
    const auto ApplyBreakingVertices=[&](TArray<FVector>& Vertices,TArray<float>& SourceFoam,
        TArray<float>& MacroCrestDisplacementCm,TArray<float>& TongueFoamSuppression,
        TArray<uint8>& BreakingPresentationVertexMask,bool bConcurrent,bool bOriginalScan)
    {
    TArray<float> AbsoluteBoil;AbsoluteBoil.Init(0.f,Vertices.Num());
    const auto ApplyVertex=[&](int32 VertexIndex)
    {
        if (WetVertexMask[VertexIndex] == 0)
        {
            return;
        }
        float CombinedPocketDisplacementMeters = 0.0f;
        float CombinedBoilDisplacementMeters = 0.0f;
        float PocketFoam = 0.0f;
        float BoilFoam = 0.0f;
        const auto& LocalPresentationSites = bSpatialBreakingReview
            ? StationBreakingSites[VertexIndex % GridStationN].Presentation : WeightedPresentationSites;
        for (const FBreakingSite& Site : LocalPresentationSites)
        {
            const FVector2D RelativeRiverPosition = RaftSimWaterFlowFrame::ToLocal(
                RiverCoordinatesM[VertexIndex] - Site.RiverCoordinatesMeters,Site.FlowDirection);
            const float LocalWeight = Site.PresentationWeight * LocalPresentationWeight(RelativeRiverPosition);
            if (LocalWeight <= 0.0f) continue;
            // The shared physical crest already budgets new foam by spilling.
            // Apply the same budget to pocket/boil generation; the legacy
            // minimum-white remap must not bypass a nonspilling wave. Do not
            // change geometry, return velocity or already-advected foam.
            const float FoamSourceWeight = RaftSimFoamTransport::BreakingSourceWeight(
                LocalWeight,Site.HydraulicSpillingFraction,
                bUseHydraulicFoamBudget);
            const FVector2D Pocket =
                ComputeBreakingPlungePocketPresentation(
                    RelativeRiverPosition.X,
                    RelativeRiverPosition.Y,
                    Site.Intensity);
            CombinedPocketDisplacementMeters +=
                Pocket.X * LocalWeight;
            PocketFoam = FMath::Max(
                PocketFoam, Pocket.Y * FoamSourceWeight);

            // Entry tongue: the smooth accelerating V upstream of the jump,
            // narrowest at the crest and widening upstream. Its centreline
            // dips slightly (the convergent draw-down into the drop) and its
            // core suppresses foam so glassy fast water frames the pile.
            const float UpstreamM = -RelativeRiverPosition.X;
            if (UpstreamM > 1.0f && UpstreamM < 30.0f)
            {
                const float AlongT = (UpstreamM - 1.0f) / 29.0f;
                const float HalfWidthM = FMath::Lerp(2.2f, 7.5f, AlongT);
                const float LateralT =
                    FMath::Abs(RelativeRiverPosition.Y) / HalfWidthM;
                if (LateralT < 1.0f)
                {
                    const float UpstreamFade =
                        1.0f - FMath::SmoothStep(0.55f, 1.0f, AlongT);
                    const float CrestRamp =
                        FMath::SmoothStep(0.0f, 0.08f, AlongT);
                    const float LateralProfile = 1.0f - LateralT * LateralT;
                    const float TongueMask =
                        UpstreamFade * CrestRamp * LateralProfile *
                        FMath::Clamp(Site.Intensity, 0.0f, 1.0f) *
                        LocalWeight;
                    if (TongueMask > 0.01f)
                    {
                        CombinedPocketDisplacementMeters -= 0.07f * TongueMask;
                        TongueFoamSuppression[VertexIndex] = FMath::Max(
                            TongueFoamSuppression[VertexIndex],
                            TongueMask * LateralProfile);
                    }
                }
            }

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
            CombinedBoilDisplacementMeters +=
                Boil.X * LocalWeight;
            BoilFoam = FMath::Max(
                BoilFoam, Boil.Y * FoamSourceWeight);
        }
        CombinedPocketDisplacementMeters = FMath::Clamp(
            CombinedPocketDisplacementMeters, -0.30f, 0.18f);
        CombinedBoilDisplacementMeters = FMath::Clamp(
            CombinedBoilDisplacementMeters, -0.045f, 0.070f);
        AbsoluteBoil[VertexIndex]=FMath::Abs(CombinedBoilDisplacementMeters);
        const float CombinedDisplacementMeters = FMath::Clamp(
            CombinedPocketDisplacementMeters + CombinedBoilDisplacementMeters,
            -0.31f,
            0.21f) * ShoreDisplacementWeight[VertexIndex];
        // The old path lifted every raw detection before deduplication, while
        // support followed only persistent accepted sites with a different
        // lateral envelope and amplitude scale. Evaluate the SAME crest/tail
        // profile and eased ownership here. Keep the dry-bank taper; this
        // aligns the interior breaking component, not all render-only WPO.
        float PhysicalCrestFoam = 0.0f;
        const auto& LocalSupportSites = bSpatialBreakingReview
            ? StationBreakingSites[VertexIndex % GridStationN].Support : SupportSites;
        const float SharedBreakingReliefMeters = bSharedBreakingReliefEnabled
            ? ((!bOriginalScan && !bFullCrestScan && !bSpatialBreakingReview && SharedCrestProfile)
                ? SharedCrestProfile->Sample(RiverCoordinatesM[VertexIndex],&PhysicalCrestFoam)
                : URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(
                  RiverCoordinatesM[VertexIndex], LocalSupportSites,
                  BreakingCrestLiftMeters, ResolvedVertexSpacingMeters, &PhysicalCrestFoam)) *
                ResolvedPresentationHydraulicReliefScale *
                ShoreDisplacementWeight[VertexIndex]
            : 0.0f;
        PocketFoam *= ShoreDisplacementWeight[VertexIndex];
        if ((bStatefulCrestReview || bPlayableCrestRefinement ||
            (bCartesianFlow && bSingleLiveWaterSurfaceEnabled && bSharedBreakingReliefEnabled)) &&
            MacroCrestDisplacementCm.IsValidIndex(VertexIndex))
            MacroCrestDisplacementCm[VertexIndex]=SharedBreakingReliefMeters*kSurfCmPerM;
        BoilFoam *= ShoreDisplacementWeight[VertexIndex];
        if (bCrestLocalizedFoam)
        {
            // Fresh crest foam follows the same accepted/eased geometry as
            // raft support. Troughs may carry old foam but do not continually
            // create it; the persistent advection below supplies the trail.
            const float CrestFoam = bPhysicalCrestFoam
                ? PhysicalCrestFoam * ShoreDisplacementWeight[VertexIndex]
                : 0.85f * FMath::SmoothStep(0.015f, 0.09f, SharedBreakingReliefMeters);
            SourceFoam[VertexIndex] = FMath::Max(SourceFoam[VertexIndex], CrestFoam);
        }
        Vertices[VertexIndex].Z +=
            (CombinedDisplacementMeters + SharedBreakingReliefMeters) * kSurfCmPerM;
        SourceFoam[VertexIndex] = FMath::Max(
            SourceFoam[VertexIndex], FMath::Max(PocketFoam, BoilFoam));
        if (FMath::Abs(CombinedDisplacementMeters) > 0.001f ||
            FMath::Abs(SharedBreakingReliefMeters) > 0.001f ||
            PocketFoam > 0.05f || BoilFoam > 0.05f)
        {
            BreakingPresentationVertexMask[VertexIndex] = 1;
        }
    };
    // Stable source/site arrays; one writer per destination. Join before foam
    // advection, source resizing, or any UObject/solver mutation. Site sum order
    // inside a vertex remains serial and identical to the reference evaluator.
    if (bConcurrent)ParallelFor(TEXT("RaftSimBreakingVertices"),Vertices.Num(),256,
        ApplyVertex,EParallelForFlags::Unbalanced);
    else for (int32 I=0;I<Vertices.Num();++I)ApplyVertex(I);
    float Maximum=0.f;
    for (float Value:AbsoluteBoil)Maximum=FMath::Max(Maximum,Value);
    return Maximum;
    };
    {
        CSV_SCOPED_TIMING_STAT(RaftSimSurface,BreakingVertices);
        MaximumAbsoluteDownstreamBoilDisplacementMeters=ApplyBreakingVertices(Vertices,SourceFoam,
            MacroCrestDisplacementCm,TongueFoamSuppression,BreakingPresentationVertexMask,
            bCartesianFlow && !bSerialBreakingVertices,bSerialBreakingVertices);
    }
#if !UE_BUILD_SHIPPING
    if (!BreakingVertexAuditPath.IsEmpty())
    {
        const float SerialMaximum=ApplyBreakingVertices(SerialVertices,SerialFoam,SerialCrest,
            SerialTongue,SerialMask,false,true);
        const auto Exact=[](const auto& A,const auto& B)
        {return A.Num()==B.Num() && (A.IsEmpty() || FMemory::Memcmp(A.GetData(),B.GetData(),A.Num()*sizeof(A[0]))==0);};
        const bool Positions=Exact(Vertices,SerialVertices),Foam=Exact(SourceFoam,SerialFoam),
            Crest=Exact(MacroCrestDisplacementCm,SerialCrest),Tongue=Exact(TongueFoamSuppression,SerialTongue),
            Mask=Exact(BreakingPresentationVertexMask,SerialMask),Maximum=MaximumAbsoluteDownstreamBoilDisplacementMeters==SerialMaximum;
        const bool Passed=Positions && Foam && Crest && Tongue && Mask && Maximum;
        const TSharedRef<FJsonObject> Report=MakeShared<FJsonObject>();
        Report->SetStringField(TEXT("scope"),TEXT("Same live pre-pass input; parallel/indexed versus serial/full scan, exact output bits; not visual or performance acceptance"));
        Report->SetBoolField(TEXT("passed"),Passed);Report->SetNumberField(TEXT("vertices"),Vertices.Num());
        Report->SetNumberField(TEXT("support_sites"),SupportSites.Num());
        Report->SetNumberField(TEXT("world_seconds"),GetWorld()->GetTimeSeconds());
        Report->SetBoolField(TEXT("parallel"),bCartesianFlow && !bSerialBreakingVertices);
        Report->SetBoolField(TEXT("indexed"),!bSerialBreakingVertices && !bFullCrestScan && !bSpatialBreakingReview && SharedCrestProfile && SharedCrestProfile->IsIndexed());
        Report->SetBoolField(TEXT("positions_exact"),Positions);Report->SetBoolField(TEXT("foam_exact"),Foam);
        Report->SetBoolField(TEXT("crest_exact"),Crest);Report->SetBoolField(TEXT("tongue_exact"),Tongue);
        Report->SetBoolField(TEXT("mask_exact"),Mask);Report->SetBoolField(TEXT("maximum_exact"),Maximum);
        FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
        const bool Saved=FFileHelper::SaveStringToFile(Json,*BreakingVertexAuditPath);
        if (Passed && Saved)
        {UE_LOG(LogTemp,Display,TEXT("BreakingVertexAudit exact vertices=%d sites=%d path=%s"),Vertices.Num(),SupportSites.Num(),*BreakingVertexAuditPath);}
        else
        {UE_LOG(LogTemp,Error,TEXT("BreakingVertexAudit failed passed=%d saved=%d path=%s"),Passed,Saved,*BreakingVertexAuditPath);}
    }
#endif

#if !UE_BUILD_SHIPPING
    FString DecompositionPath;
    if (bCartesianFlow && GetWorld() && GetWorld()->GetTimeSeconds()>=10.f &&
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimSurfaceDecompositionAudit="),DecompositionPath) &&
        !FPaths::FileExists(DecompositionPath))
    {
        // Diagnostic source targets BEFORE temporal rendering, clipping and
        // GPU perturbation. Nothing here changes the geometry or support.
        FString Csv=TEXT("field_x_m,field_y_m,raw_eta_m,raw_depth_m,filtered_eta_m,presented_base_eta_m,hydraulic_relief_m,shared_crest_m,other_relief_m,target_z_m,flow_x_mps,flow_y_mps\n");
        int32 Count=0;
        const double RenderLiftM=GetResolvedLiveSurfaceRenderLiftCm()*.01;
        for (int32 I=0;I<Vertices.Num();++I)
        {
            if (!WetVertexMask[I])continue;
            const auto& S=WaterSamples[I];
            const double Z=Vertices[I].Z*.01;
            const double Crest=MacroCrestDisplacementCm.IsValidIndex(I) ? MacroCrestDisplacementCm[I]*.01 : 0.;
            const double Other=Z-PresentationSurfaceHeightMeters[I]-HydraulicReliefMeters[I]-Crest-RenderLiftM;
            Csv+=FString::Printf(TEXT("%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g\n"),
                RiverCoordinatesM[I].X,RiverCoordinatesM[I].Y,double(S.SurfaceHeightMeters),double(S.DepthMeters),
                double(FilteredBaseForAudit.IsValidIndex(I) ? FilteredBaseForAudit[I] : PresentationSurfaceHeightMeters[I]),
                double(PresentationSurfaceHeightMeters[I]),double(HydraulicReliefMeters[I]),Crest,Other,Z,
                double(S.VelocityMetersPerSecond.X),double(S.VelocityMetersPerSecond.Y));
            ++Count;
        }
        if (FFileHelper::SaveStringToFile(Csv,*DecompositionPath))
        {
            UE_LOG(LogTemp,Display,TEXT("Surface decomposition saved: %s wet_targets=%d render_lift_m=%.9g world_s=%.9g; excludes temporal/clipping/GPU"),
                *DecompositionPath,Count,RenderLiftM,GetWorld()->GetTimeSeconds());
        }
        else { UE_LOG(LogTemp,Error,TEXT("Cannot save requested surface decomposition: %s"),*DecompositionPath); }
    }
#endif

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
            // The fine-crest shader adds the continuous crest slope to this
            // smooth base normal. Do not subtract a piecewise triangle slope
            // from an already-smoothed full normal: that leaves grid seams.
            const auto NormalPosition = [&](int32 I)
            {
                return Vertices[I] - FVector(0,0,
                    bStatefulCrestReview && MacroCrestDisplacementCm.IsValidIndex(I)
                        ? MacroCrestDisplacementCm[I] : 0.0f);
            };
            const FVector StationTangent =
                NormalPosition(DownstreamIndex) - NormalPosition(UpstreamIndex);
            const FVector LateralTangent =
                NormalPosition(RiverLeftIndex) - NormalPosition(RiverRightIndex);
            Normals[Index] = FVector::CrossProduct(
                StationTangent, LateralTangent).GetSafeNormal();
            if (WaterAdapter) Normals[Index] *= WaterAdapter->GetRiverWorldYSign();
        }
    }
    if (bSingleLiveWaterSurfaceEnabled || bSharedBreakingReliefEnabled)
    {
        // The single South Fork carrier already receives breaking relief and
        // solver foam through its displaced vertices and vertex colour. The
        // lip and roller components use separate masked foam textures and are
        // recreated as detection sites enter/leave the live window; rendering
        // them here produced the remaining full-white on/off flash.
        HideBreakingLipMesh();
        HideBreakingRollerVolumeMesh();
    }
    else
    {
        RebuildBreakingLipMesh();
        RebuildBreakingRollerVolumeMesh();
    }
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
                 "strongest_interior_crest_height_m=%.3f strongest_interior_face_length_m=%.3f "
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
            StrongestInteriorSite ? StrongestInteriorSite->HydraulicCrestDimensionsMeters.X : 0.0f,
            StrongestInteriorSite ? StrongestInteriorSite->HydraulicCrestDimensionsMeters.Y : 0.0f,
            StrongestInteriorSite
                ? StrongestInteriorSite->PresentationCoverage
                : 0.0f,
            StrongestInteriorSite
                ? StrongestInteriorSite->PresentationEdgeClearanceMeters
                : 0.0f,
            (bSingleLiveWaterSurfaceEnabled || bSharedBreakingReliefEnabled)
                ? FMath::Max(ResolvedVertexSpacingMeters, 3.0f)
                : BreakingSiteInteriorClearanceMeters);
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

    Perf.Mark(TEXT("breaking_carve"));
    // --- Persistent advected foam ----------------------------------------
    if (!FoamSourceAudit.IsEmpty())
    {
        double OldGeneric=0,NewGeneric=0,OldFinal=0,OldFinalLower=0,NewFinal=0;
        int32 Wet=0,Reduced=0,Increased=0;
        for(int32 I=0;I<Vertices.Num();++I)if(WetVertexMask[I])
        {
            const auto& A=FoamSourceAudit[I];
            // Every intervening crest/pocket/boil operation takes a maximum.
            // Recover their independent contribution where they exceed the
            // candidate background; keep equality ambiguous rather than
            // claiming an exact legacy total in that case.
            OldGeneric+=A.X;NewGeneric+=A.Y;NewFinal+=SourceFoam[I];
            OldFinal+=FMath::Max(A.Z,SourceFoam[I]);
            OldFinalLower+=SourceFoam[I]>A.W ? FMath::Max(A.Z,SourceFoam[I]) : A.Z;
            ++Wet;Reduced+=A.Y<A.X;Increased+=A.Y>A.X;
        }
        const auto Report=MakeShared<FJsonObject>();
        Report->SetStringField(TEXT("schema"),TEXT("raftsim.directional_foam_source.v1"));
        Report->SetStringField(TEXT("scope"),TEXT("Same live source input; optical source onset only, not air-entrainment measurement or visual acceptance"));
        Report->SetBoolField(TEXT("directional_source"),bDirectionalFoamSource);
        Report->SetNumberField(TEXT("wet_vertices"),Wet);
        Report->SetNumberField(TEXT("generic_reduced_vertices"),Reduced);
        Report->SetNumberField(TEXT("generic_increased_vertices"),Increased);
        Report->SetNumberField(TEXT("legacy_generic_sum"),OldGeneric);
        Report->SetNumberField(TEXT("directional_generic_sum"),NewGeneric);
        Report->SetNumberField(TEXT("legacy_final_source_sum_upper_bound"),OldFinal);
        Report->SetNumberField(TEXT("legacy_final_source_sum_lower_bound"),OldFinalLower);
        Report->SetNumberField(TEXT("current_final_source_sum"),NewFinal);
        Report->SetNumberField(TEXT("committed_water_seconds"),WaterAdapter->GetCommittedStepSeconds());
        FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
        const bool Saved=FFileHelper::SaveStringToFile(Json,*FoamSourceAuditPath);
        UE_LOG(LogTemp,Display,TEXT("DirectionalFoamSourceAudit wet=%d reduced=%d increased=%d saved=%d"),Wet,Reduced,Increased,Saved);
    }
    // Semi-Lagrangian: each wet vertex looks upstream along the sampled flow
    // into the previous foam field, decays what it finds through the half-life,
    // and takes the maximum with this refresh's generation. Foam therefore
    // streaks downstream of every hole and wave train and pools into eddy
    // lines, instead of blinking in and out on the generation cells.
    const FVector2D CurrentFieldOriginM = bUsesCurvedRiverCoordinates
        ? FVector2D(
              CurvedGridCenterStationM - CurvedGridLengthMeters * 0.5f,
              CartesianGridCenterNorthM - CurvedGridWidthMeters * 0.5f)
        : FVector2D(GridOriginCm.X / kSurfCmPerM, GridOriginCm.Y / kSurfCmPerM);
    const bool bHoldFoam=bCartesianFlow && FoamDeltaSeconds==0.f;
    const float DecayFactor = FoamDeltaSeconds > 0.0f || bCartesianFlow
        ? FMath::Pow(0.5f, FoamDeltaSeconds / FMath::Max(FoamHalfLifeSeconds, 0.5f))
        : 0.0f;
    const float FoamAttackDeltaSeconds=bCartesianFlow ? FoamDeltaSeconds :
        (FoamDeltaSeconds>0.f ? FoamDeltaSeconds : FMath::Max(RefreshIntervalSeconds,1.f/60.f));
    const float FoamAttackBlend=1.f-FMath::Exp(-FoamAttackDeltaSeconds/.22f);
    static const bool bFoamBFECCReview=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFoamBFECCReview"));
    // Same-grid reversible transport only. Recentring, initialization, clock
    // holds and incomplete history retain the unmodified first-order path.
    const bool bCorrectFoam=bFoamBFECCReview && bCartesianFlow && !bHoldFoam && bPreviousFoamUsable &&
        CurrentFieldOriginM==FoamFieldOriginM && FoamFieldWetMask.Num()==Vertices.Num();
    TArray<FVector2D> FoamBackwardNodes;
    if(bCorrectFoam)FoamBackwardNodes.Init(FVector2D(-1,-1),Vertices.Num());
    TArray<float> NewFoamField;
    NewFoamField.SetNumZeroed(Vertices.Num());
    FoamTransportVelocityMetersPerSecond.Init(FVector2D::ZeroVector,Vertices.Num());
    float FoamAdvectionSum = 0.0f;
    float FoamAdvectionMax = 0.0f;
    const auto AdvectFoam=[&](TArray<float>& OutputFoam,TArray<FVector2D>& OutputVelocity,
        TArray<FLinearColor>& OutputColors,bool Concurrent)
    {
        const auto Vertex=[&](int32 Index)
        {
            if (WetVertexMask[Index] == 0)
            {
                return;
            }
            float Advected = 0.0f;
            const FVector SampledVelocity = WaterSamples[Index].VelocityMetersPerSecond;
            OutputVelocity[Index] = FVector2D(SampledVelocity.X,SampledVelocity.Y);
            if (bPreviousFoamUsable && DecayFactor > 0.0f &&
                FoamField.Num() == OutputFoam.Num())
            {
                FVector2D FieldVelocity(SampledVelocity.X, SampledVelocity.Y);
                FVector2D FieldPosition(
                    Vertices[Index].X / kSurfCmPerM, Vertices[Index].Y / kSurfCmPerM);
                if (bUsesCurvedRiverCoordinates)
                {
                    // SampleWaterFieldAtRiverCoordinates already returns
                    // field velocity, both for station and Cartesian grids.
                    // A second world projection rotates/reflects the backtrace.
                    FieldPosition = RiverCoordinatesM[Index];
                }
                // Foam inside an accepted hydraulic jump must visibly turn
                // back toward the impact toe instead of sliding through the
                // froth patch at the bulk current speed. The return is local,
                // continuous, and presentation-only; it cannot move the raft
                // or create a second surface.
                const float BulkWaterSpeedMetersPerSecond =
                    FieldVelocity.Size();
                const FVector2D BulkFlowDirection = bCartesianFlow
                    ? RaftSimWaterFlowFrame::Direction(FieldVelocity) : FVector2D(1.,0.);
                FVector2D RollerVelocity = FVector2D::ZeroVector;
                const auto& LocalRollerSites = bSpatialBreakingReview
                    ? StationBreakingSites[Index % GridStationN].Presentation : WeightedPresentationSites;
                for (const FBreakingSite& Site : LocalRollerSites)
                {
                    const FVector2D RelativePosition = RaftSimWaterFlowFrame::ToLocal(
                        FieldPosition - Site.RiverCoordinatesMeters,Site.FlowDirection);
                    const float LocalWeight = Site.PresentationWeight * LocalPresentationWeight(RelativePosition);
                    if (LocalWeight <= 0.0f) continue;
                    RollerVelocity += RaftSimWaterFlowFrame::ToField(
                        ComputeBreakingRollerSurfaceVelocityMetersPerSecond(
                            RelativePosition.X,
                            RelativePosition.Y,
                            Site.Intensity,
                            BulkWaterSpeedMetersPerSecond),Site.FlowDirection) *
                        LocalWeight;
                }
                FieldVelocity += RollerVelocity.GetClampedToMaxSize(
                    FMath::Max(
                        1.0f,
                        BulkWaterSpeedMetersPerSecond + 1.0f));
                // Boulder eddies (presentation transport only): the sheltered
                // pocket behind an obstruction recirculates. The core returns
                // upstream toward the rock while the downstream half draws
                // surface water in toward the centreline, so foam entering
                // over the shear seam circles and collects instead of washing
                // straight through. Raft physics still rides the solver
                // field; this only steers where the foam travels.
                for (const FVector3f& Footprint : WindowBoulderFootprintsSLR)
                {
                    const float RadiusM = FMath::Max(Footprint.Z, 0.75f);
                    const FVector2D BoulderRelative = RaftSimWaterFlowFrame::ToLocal(
                        FieldPosition-FVector2D(Footprint.X,Footprint.Y),BulkFlowDirection);
                    const float DownstreamM = BoulderRelative.X;
                    if (DownstreamM < RadiusM * 0.5f ||
                        DownstreamM > RadiusM * 6.0f)
                    {
                        continue;
                    }
                    const float AcrossM = BoulderRelative.Y;
                    const float AcrossT = AcrossM / (RadiusM * 1.6f);
                    if (FMath::Abs(AcrossT) > 1.0f)
                    {
                        continue;
                    }
                    const float AlongT = FMath::Clamp(
                        (DownstreamM - RadiusM * 0.5f) / (RadiusM * 5.5f),
                        0.0f, 1.0f);
                    const float SpeedEnvelope = FMath::SmoothStep(
                        0.45f, 1.65f, BulkWaterSpeedMetersPerSecond);
                    const float PocketEnvelope =
                        (1.0f - AlongT) *
                        FMath::SmoothStep(1.0f, 0.55f, FMath::Abs(AcrossT)) *
                        SpeedEnvelope;
                    if (PocketEnvelope <= 0.01f)
                    {
                        continue;
                    }
                    const FVector2D EddyVelocity(
                        -0.55f * BulkWaterSpeedMetersPerSecond,
                        -AcrossT * 0.30f * BulkWaterSpeedMetersPerSecond *
                            AlongT);
                    FieldVelocity = FMath::Lerp(
                        FieldVelocity, RaftSimWaterFlowFrame::ToField(EddyVelocity,BulkFlowDirection), PocketEnvelope);
                }
                // Export the exact velocity that moves the foam field, after
                // every local return contribution, without changing transport.
                OutputVelocity[Index] = FieldVelocity;
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
                if(bCorrectFoam)FoamBackwardNodes[Index]=FVector2D(FractionalX,FractionalY);
                if(bHoldFoam)
                {
                    // Exact same-grid hold also preserves border-node values.
                    Advected=CurrentFieldOriginM==FoamFieldOriginM ? FoamField[Index] :
                        RaftSimFoamEvolution::RemapHeld(FoamField,GridStationN,GridLateralN,FractionalX,FractionalY);
                }
                else if (CellX >= 0 && CellX < GridStationN - 1 &&
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
            // The hydraulic field refreshes at 15 Hz. Feeding a newly
            // generated source directly to vertex colour made an entire crest
            // jump from water to white in one rendered frame even though its
            // advected release was persistent. Give generation a short
            // exponential attack while retaining the existing four-second
            // transported release. This is state smoothing only: the solver
            // still decides where foam is born and the sampled current still
            // decides where it travels.
            const float FinalFoam=RaftSimFoamEvolution::Resolve(Advected,SourceFoam[Index],FoamAttackBlend,
                TongueFoamSuppression[Index],ShoreDisplacementWeight[Index],bHoldFoam);
            OutputFoam[Index]=FinalFoam;
            OutputColors[Index].R=FinalFoam;
        };
        if(Concurrent)ParallelFor(TEXT("RaftSimFoamTransport"),Vertices.Num(),256,Vertex,EParallelForFlags::Unbalanced);
        else for(int32 I=0;I<Vertices.Num();++I)Vertex(I);
    };
    // Actual warmed captures measured dispatch overhead above this sparse
    // loop's serial cost. Keep parallel transport opt-in, not the normal path.
    static const bool bParallelFoamTransport=FParse::Param(FCommandLine::Get(),TEXT("RaftSimParallelFoamTransport")) &&
        !FParse::Param(FCommandLine::Get(),TEXT("RaftSimSerialFoamTransport"));
    FString FoamAuditPath;
#if !UE_BUILD_SHIPPING
    if(GetWorld() && GetWorld()->GetTimeSeconds()>=10.f)
    {
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimFoamEvolutionAudit="),FoamAuditPath);
        if(FPaths::FileExists(FoamAuditPath))FoamAuditPath.Reset();
    }
#endif
    TArray<float> SerialTransportFoam;TArray<FVector2D> SerialVelocity;TArray<FLinearColor> SerialColors;
    if(!FoamAuditPath.IsEmpty())
    {SerialTransportFoam.Init(0.f,Vertices.Num());SerialVelocity.Init(FVector2D::ZeroVector,Vertices.Num());SerialColors=VertexColors;}
    {
        CSV_SCOPED_TIMING_STAT(RaftSimSurface,FoamTransport);
        AdvectFoam(NewFoamField,FoamTransportVelocityMetersPerSecond,VertexColors,bCartesianFlow && bParallelFoamTransport);
        // Preserve the original Y-major reduction order; no parallel sum drift.
        for(int32 I=0;I<Vertices.Num();++I)if(WetVertexMask[I])
        {FoamAdvectionSum+=NewFoamField[I];FoamAdvectionMax=FMath::Max(FoamAdvectionMax,NewFoamField[I]);}
    }
    if(!FoamAuditPath.IsEmpty())
    {
        AdvectFoam(SerialTransportFoam,SerialVelocity,SerialColors,false);
        const auto Exact=[](const auto& A,const auto& B)
        {return A.Num()==B.Num() && (A.IsEmpty() || FMemory::Memcmp(A.GetData(),B.GetData(),A.Num()*sizeof(A[0]))==0);};
        float SerialSum=0,SerialMax=0;
        for(int32 I=0;I<Vertices.Num();++I)if(WetVertexMask[I]){SerialSum+=SerialTransportFoam[I];SerialMax=FMath::Max(SerialMax,SerialTransportFoam[I]);}
        const bool Passed=Exact(NewFoamField,SerialTransportFoam) && Exact(FoamTransportVelocityMetersPerSecond,SerialVelocity) &&
            Exact(VertexColors,SerialColors) && SerialSum==FoamAdvectionSum && SerialMax==FoamAdvectionMax;
        auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("passed"),Passed);
        Report->SetStringField(TEXT("scope"),TEXT("Same actual previous foam and current water/sites/coordinates; selected path versus serial density, effective velocity, RGBA and ordered reductions. The parallel field identifies selection; serial/default is a self-check, not parallel validation. Not visual or performance acceptance."));
        Report->SetNumberField(TEXT("vertices"),Vertices.Num());Report->SetNumberField(TEXT("committed_water_seconds"),NextFoamClock.Last);
        Report->SetNumberField(TEXT("committed_delta_seconds"),FoamCommittedDelta);Report->SetNumberField(TEXT("kernel_delta_seconds"),FoamDeltaSeconds);
        Report->SetBoolField(TEXT("held"),bHoldFoam);Report->SetBoolField(TEXT("parallel"),bCartesianFlow && bParallelFoamTransport);
        FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
        const bool Saved=FFileHelper::SaveStringToFile(Json,*FoamAuditPath);
        if(Passed && Saved){UE_LOG(LogTemp,Display,TEXT("FoamEvolutionAudit exact vertices=%d path=%s"),Vertices.Num(),*FoamAuditPath);}
        else {UE_LOG(LogTemp,Error,TEXT("FoamEvolutionAudit failed passed=%d saved=%d"),Passed,Saved);}
    }
    if(bCorrectFoam)
    {
        CSV_SCOPED_TIMING_STAT(RaftSimSurface,FoamTransport);
        const auto Correction=RaftSimFoamAdvection::Correct(GridStationN,GridLateralN,FoamField,
            FoamFieldWetMask,WetVertexMask,FoamBackwardNodes,FoamTransportVelocityMetersPerSecond,
            ResolvedVertexSpacingMeters,FoamDeltaSeconds);
        double Change=0;FoamAdvectionSum=0;FoamAdvectionMax=0;
        for(int32 I=0;I<Vertices.Num();++I)
        {
            if(Correction.Corrected.IsValidIndex(I) && Correction.Corrected[I])
            {
                const float Value=RaftSimFoamEvolution::Resolve(Correction.Values[I]*DecayFactor,SourceFoam[I],
                    FoamAttackBlend,TongueFoamSuppression[I],ShoreDisplacementWeight[I],false);
                Change+=FMath::Abs(Value-NewFoamField[I]);NewFoamField[I]=Value;VertexColors[I].R=Value;
            }
            if(WetVertexMask[I]){FoamAdvectionSum+=NewFoamField[I];FoamAdvectionMax=FMath::Max(FoamAdvectionMax,NewFoamField[I]);}
        }
        // Per-refresh evidence: the same live field, before/after correction.
        // This is not a conservation, visual-quality or performance gate.
        UE_LOG(LogTemp,Verbose,TEXT("FoamBFECC corrected=%d limited=%d absolute_change=%.9g water_seconds=%.9g"),
            Correction.CorrectedCount,Correction.LimitedCount,Change,NextFoamClock.Last);
    }
    if(bFoamBFECCReview)FoamFieldWetMask=WetVertexMask;
    FoamField = MoveTemp(NewFoamField);
    FoamFieldOriginM = CurrentFieldOriginM;
    if(bCartesianFlow)
    {
        FoamWaterClock=NextFoamClock;++FoamClockRefreshes;FoamClockHolds+=bHoldFoam;FoamClockInitializations+=!bPreviousFoamUsable;
        if(LiveVolumeCoreMesh)
            if(auto* Material=Cast<UMaterialInstanceDynamic>(LiveVolumeCoreMesh->GetMaterial(0)))
            {
                const double Seconds=FoamWaterClock.TargetSeconds();
                const float High=float(Seconds),Low=float(Seconds-double(High));
                Material->SetVectorParameterValue(TEXT("RaftSimCPUFoamClock"),FLinearColor(High,Low,0,0));
            }
        CSV_CUSTOM_STAT(RaftSimSurface,FoamWaterSeconds,FoamWaterClock.Last,ECsvCustomStatOp::Set);
        CSV_CUSTOM_STAT(RaftSimSurface,FoamDeltaSeconds,FoamCommittedDelta,ECsvCustomStatOp::Set);
    }
    bFoamFieldValid = true;
    bFoamUsesCommittedClock=bCartesianFlow;
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
    // Review probe (raftsim.LogLatticeEdgeRows 1): when the grid's first or
    // last row sits at the corridor's end, log the wet extents and coverage
    // of the twelve rows at each end so a "water missing at the put-in"
    // report can be attributed to sampling, wet extents, or coverage.
    if (CVarRaftSimLogLatticeEdgeRows.GetValueOnGameThread() != 0 && WaterAdapter)
    {
        static int32 LoggedEdgeRefreshes = 0;
        float ProbeMinimumStationM = 0.0f;
        float ProbeMaximumStationM = 0.0f;
        if (LoggedEdgeRefreshes < 3 && GridStationN > 24 && GridLateralN > 2 &&
            WaterAdapter->GetRiverStationRangeM(ProbeMinimumStationM, ProbeMaximumStationM))
        {
            const float GridStartM = CurvedGridCenterStationM - CurvedGridLengthMeters * 0.5f;
            const float GridEndM = GridStartM +
                static_cast<float>(GridStationN - 1) * ResolvedVertexSpacingMeters;
            const bool bAtStart = GridStartM <= ProbeMinimumStationM + ResolvedVertexSpacingMeters * 1.5f;
            const bool bAtEnd = GridEndM >= ProbeMaximumStationM - ResolvedVertexSpacingMeters * 1.5f;
            if (bAtStart || bAtEnd)
            {
                ++LoggedEdgeRefreshes;
                const int32 CentreY = GridLateralN / 2;
                auto LogRow = [&](int32 X)
                {
                    int32 WetCount = 0;
                    for (int32 Y = 0; Y < GridLateralN; ++Y)
                    {
                        WetCount += WetVertexMask[Y * GridStationN + X] != 0 ? 1 : 0;
                    }
                    UE_LOG(LogTemp, Display,
                        TEXT("RaftSim lattice edge row: x=%d station_m=%.1f wet_vertices=%d centre_wet=%d wet_lateral=[%d,%d] coverage=%.3f ref_z_cm=%.0f"),
                        X, RiverCoordinatesM[X].X, WetCount,
                        WetVertexMask[CentreY * GridStationN + X] != 0 ? 1 : 0,
                        MinimumWetLateralIndex[X], MaximumWetLateralIndex[X],
                        StationEdgeCoverage(X), StationReferenceSurfaceZ[X]);
                };
                UE_LOG(LogTemp, Display,
                    TEXT("RaftSim lattice edge probe: grid_start_m=%.1f grid_end_m=%.1f corridor=[%.1f,%.1f] rows=%d lateral=%d spacing=%.2f at_start=%d at_end=%d"),
                    GridStartM, GridEndM, ProbeMinimumStationM, ProbeMaximumStationM,
                    GridStationN, GridLateralN, ResolvedVertexSpacingMeters, bAtStart ? 1 : 0, bAtEnd ? 1 : 0);
                if (bAtStart)
                {
                    for (int32 X = 0; X < 12; ++X) { LogRow(X); }
                }
                if (bAtEnd)
                {
                    for (int32 X = GridStationN - 12; X < GridStationN; ++X) { LogRow(X); }
                }
            }
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
                const float StationCoverage = StationEdgeCoverage(X);
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
        TArray<uint8> VolumeCoreWetMask = WetVertexMask;
        TArray<int32> VolumeCoreMinimumWetLateralIndex =
            MinimumWetLateralIndex;
        TArray<int32> VolumeCoreMaximumWetLateralIndex =
            MaximumWetLateralIndex;
        LiveVolumeCoreNormals = Normals;
        LiveVolumeCoreVertexColors = VertexColors;
        for (int32 Index = 0; Index < Vertices.Num(); ++Index)
        {
            LiveVolumeCoreVertices[Index] = bSingleLiveWaterSurfaceEnabled
                ? Vertices[Index]
                : Vertices[Index] -
                    Normals[Index].GetSafeNormal() * kLiveVolumeCoreOffsetCm;
        }

        // Retired compatibility apron. The full-reach presentation baseline
        // now supplies a terrain-clipped wet mask outside the live crop. Never
        // copy one boundary station downriver again: doing so creates the
        // rectangular bank patch visible in close shoreline views.
        constexpr bool bUseCopiedBoundaryOpticalApron = false;
        if (bSingleLiveWaterSurfaceEnabled &&
            bUseCopiedBoundaryOpticalApron)
        {
            int32 FirstWetStation = INDEX_NONE;
            int32 LastWetStation = INDEX_NONE;
            for (int32 X = 0; X < GridStationN; ++X)
            {
                if (StationWetSurfaceCount[X] > 0)
                {
                    FirstWetStation = FirstWetStation == INDEX_NONE
                        ? X
                        : FirstWetStation;
                    LastWetStation = X;
                }
            }

            const auto LegacyWPOCounterCm =
                [this](int32 Index) -> float
                {
                    if (bHasTravelingWaveWPOStrengthParameter)
                    {
                        return 0.0f;
                    }
                    const float LegacyPhase =
                        static_cast<float>(RiverCoordinatesM[Index].X) * 0.19f +
                        static_cast<float>(RiverCoordinatesM[Index].Y) * 0.61f;
                    return 0.012f * FMath::Sin(LegacyPhase) * kSurfCmPerM;
                };
            const auto ExtendOpticalCore =
                [this,
                 &VolumeCoreWetMask,
                 &VolumeCoreMinimumWetLateralIndex,
                 &VolumeCoreMaximumWetLateralIndex,
                 &WetVertexMask,
                 &MinimumWetLateralIndex,
                 &MaximumWetLateralIndex,
                 &LegacyWPOCounterCm](int32 BoundaryX, int32 Direction)
                {
                    if (BoundaryX < 0 || BoundaryX >= GridStationN ||
                        (Direction != -1 && Direction != 1))
                    {
                        return;
                    }
                    const int32 EndX = Direction < 0 ? -1 : GridStationN;
                    for (int32 X = BoundaryX + Direction;
                         X != EndX;
                         X += Direction)
                    {
                        VolumeCoreMinimumWetLateralIndex[X] =
                            MinimumWetLateralIndex[BoundaryX];
                        VolumeCoreMaximumWetLateralIndex[X] =
                            MaximumWetLateralIndex[BoundaryX];
                        for (int32 Y = 0; Y < GridLateralN; ++Y)
                        {
                            const int32 BoundaryIndex =
                                Y * GridStationN + BoundaryX;
                            if (WetVertexMask[BoundaryIndex] == 0)
                            {
                                continue;
                            }
                            const int32 Index = Y * GridStationN + X;
                            int32 InnerX = BoundaryX - Direction;
                            while (InnerX >= 0 && InnerX < GridStationN &&
                                   WetVertexMask[Y * GridStationN + InnerX] == 0)
                            {
                                InnerX -= Direction;
                            }
                            float GradeCmPerMeter = 0.0f;
                            if (InnerX >= 0 && InnerX < GridStationN)
                            {
                                const int32 InnerIndex =
                                    Y * GridStationN + InnerX;
                                const float StationDeltaM =
                                    static_cast<float>(
                                        RiverCoordinatesM[BoundaryIndex].X -
                                        RiverCoordinatesM[InnerIndex].X);
                                if (!FMath::IsNearlyZero(StationDeltaM))
                                {
                                    const float BoundaryNeutralZCm =
                                        Vertices[BoundaryIndex].Z +
                                        LegacyWPOCounterCm(BoundaryIndex);
                                    const float InnerNeutralZCm =
                                        Vertices[InnerIndex].Z +
                                        LegacyWPOCounterCm(InnerIndex);
                                    GradeCmPerMeter = FMath::Clamp(
                                        (BoundaryNeutralZCm - InnerNeutralZCm) /
                                            StationDeltaM,
                                        -8.0f,
                                        8.0f);
                                }
                            }
                            const float TargetStationDeltaM =
                                static_cast<float>(
                                    RiverCoordinatesM[Index].X -
                                    RiverCoordinatesM[BoundaryIndex].X);
                            LiveVolumeCoreVertices[Index] = Vertices[Index];
                            LiveVolumeCoreVertices[Index].Z =
                                Vertices[BoundaryIndex].Z +
                                LegacyWPOCounterCm(BoundaryIndex) +
                                GradeCmPerMeter * TargetStationDeltaM -
                                LegacyWPOCounterCm(Index);
                            VolumeCoreWetMask[Index] = 1;
                            LiveVolumeCoreNormals[Index] = Normals[BoundaryIndex];
                            LiveVolumeCoreVertexColors[Index] =
                                VertexColors[BoundaryIndex];
                            LiveVolumeCoreVertexColors[Index].R = 0.0f;
                            const float StationCoverage =
                                StationEdgeCoverage(X);
                            const float LateralCoverage =
                                ComputePresentationBankCoverage(
                                    RiverCoordinatesM[Index].X,
                                    Y,
                                    VolumeCoreMinimumWetLateralIndex[X],
                                    VolumeCoreMaximumWetLateralIndex[X],
                                    ResolvedVertexSpacingMeters,
                                    CurvedGridLateralEdgeBlendMeters,
                                    bLivePresentationBankNaturalismEnabled,
                                    ResolvedPresentationBankNaturalismAmplitudeMeters);
                            LiveVolumeCoreVertexColors[Index].A =
                                StationCoverage * LateralCoverage;
                        }
                    }
                };
            if (FirstWetStation != INDEX_NONE)
            {
                ExtendOpticalCore(FirstWetStation, -1);
                ExtendOpticalCore(LastWetStation, 1);
            }
        }

        // Wet membership flips at cell granularity every refresh; rendering
        // the raw mask toggled whole rectangular bank quads in one frame.
        // Ease a per-vertex presence envelope toward the mask instead: a
        // cell's quads render while any presence remains, and the collapse
        // pass below the bank retreat slides partially present vertices
        // toward the channel so the shoreline expands and recedes as a
        // lapping edge. Alpha cannot express this fade — the Single Layer
        // Water body shades at near-zero surface opacity — so the envelope
        // must move geometry.
        if (LiveVolumeCoreWetPresence.Num() != Vertices.Num())
        {
            LiveVolumeCoreWetPresence.SetNumZeroed(Vertices.Num());
        }
        // Connectivity filter: the carrier must only render water that is
        // reachable from genuine solver-wet channel cells without a step in
        // surface height. The terrain-clipped baseline also marks raised
        // bank benches as wet; rendered, those benches float above the
        // adjacent channel as a second pale surface, and their wet-mask
        // noise makes whole slabs appear and vanish. Flood-fill from the
        // solver-wet channel with a per-cell height-step limit and cull the
        // disconnected islands from presentation.
        TArray<uint8> ConnectedWetMask;
        ConnectedWetMask.Init(0, Vertices.Num());
        if (bCartesianFlow) ConnectedWetMask = VolumeCoreWetMask;
        else
        {
            TArray<int32> FloodQueue;
            FloodQueue.Reserve(Vertices.Num() / 4);
            for (int32 Index = 0; Index < Vertices.Num(); ++Index)
            {
                if (LiveSolverWetVertexMask[Index] != 0 &&
                    VolumeCoreWetMask[Index] != 0)
                {
                    ConnectedWetMask[Index] = 1;
                    FloodQueue.Add(Index);
                }
            }
            // Tight step: every solver-wet cell is its own seed, so this
            // limit only gates expansion into baseline-only water. Real
            // connected shallows rise gently (~10 % bank slope = 0.15 m per
            // 1.5 m cell); a larger tolerance let baseline bank shelves
            // "connect" across the waterline and render as a second,
            // semi-transparent water sheet hovering above the channel with
            // ground visible in the gap (player screenshot, 2026-08-27).
            constexpr float kMaxNeighbourSurfaceStepM = 0.18f;
            for (int32 QueueIndex = 0; QueueIndex < FloodQueue.Num();
                 ++QueueIndex)
            {
                const int32 Index = FloodQueue[QueueIndex];
                const int32 X = Index % GridStationN;
                const int32 Y = Index / GridStationN;
                const int32 NeighbourIndices[4] = {
                    X > 0 ? Index - 1 : INDEX_NONE,
                    X < GridStationN - 1 ? Index + 1 : INDEX_NONE,
                    Y > 0 ? Index - GridStationN : INDEX_NONE,
                    Y < GridLateralN - 1 ? Index + GridStationN : INDEX_NONE};
                for (const int32 NeighbourIndex : NeighbourIndices)
                {
                    if (NeighbourIndex == INDEX_NONE ||
                        ConnectedWetMask[NeighbourIndex] != 0 ||
                        VolumeCoreWetMask[NeighbourIndex] == 0)
                    {
                        continue;
                    }
                    if (FMath::Abs(
                            PresentationSurfaceHeightMeters[NeighbourIndex] -
                            PresentationSurfaceHeightMeters[Index]) >
                        kMaxNeighbourSurfaceStepM)
                    {
                        continue;
                    }
                    ConnectedWetMask[NeighbourIndex] = 1;
                    FloodQueue.Add(NeighbourIndex);
                }
            }
        }
        // Rendered-terrain conformance: the solver's bed and the rendered
        // Nanite terrain tiles disagree by a few centimetres, and on a gentle
        // bank that vertical error stretches into metres of water column too
        // thin to show any volume colour — a tint-free specular film hovering
        // on the visible ground ("I still see the shiny texture on the
        // shore", player screenshot 2026-08-28). Solver depth cannot see this
        // because the error is between the two terrain representations, so
        // probe the rendered tiles directly: cache a line-traced terrain Z
        // under the shoreline bands and drop presentation wetness where the
        // rendered water would sit too close above the rendered ground.
        TArray<uint8> VisualFilmCullMask;
        VisualFilmCullMask.Init(0, Vertices.Num());
        {
            // Hysteresis: enter the cull below 6 cm of rendered water, leave
            // it above 9 cm. A single threshold flipped verdicts with the
            // waves' centimetre motion, churning shoreline membership (and
            // with it the boundary section) every refresh.
            constexpr float kVisualBankFilmEnterDepthCm = 6.0f;
            constexpr float kVisualBankFilmExitDepthCm = 9.0f;
            constexpr int32 kVisualBankBandRings = 3;
            constexpr int32 kVisualBankProbeBudgetPerRefresh = 192;
            if (VisualBankTerrainZCm.Num() != Vertices.Num())
            {
                VisualBankTerrainZCm.Init(0.0f, Vertices.Num());
            }
            if (VisualBankProbeState.Num() != Vertices.Num())
            {
                VisualBankProbeState.Init(0, Vertices.Num());
            }
            if (VisualFilmCullState.Num() != Vertices.Num())
            {
                VisualFilmCullState.Init(0, Vertices.Num());
            }
            int32 ProbeBudget = kVisualBankProbeBudgetPerRefresh;
            UWorld* ProbeWorld = GetWorld();
            const FTransform CarrierTransform =
                SurfaceMesh ? SurfaceMesh->GetComponentTransform()
                            : GetActorTransform();
            const auto EvaluateBandCell = [&](int32 X, int32 Y)
            {
                if (Y < 0 || Y >= GridLateralN)
                {
                    return;
                }
                const int32 Index = Y * GridStationN + X;
                if (VolumeCoreWetMask[Index] == 0)
                {
                    return;
                }
                const FVector WaterWorld =
                    CarrierTransform.TransformPosition(Vertices[Index]);
                if (VisualBankProbeState[Index] == 0 && ProbeBudget > 0 &&
                    ProbeWorld)
                {
                    FHitResult Hit;
                    FCollisionQueryParams ProbeParams(
                        TEXT("RaftSimVisualBankProbe"), true, this);
                    const FVector Start =
                        WaterWorld + FVector(0.0f, 0.0f, 300.0f);
                    const FVector End =
                        WaterWorld - FVector(0.0f, 0.0f, 600.0f);
                    if (TraceTerrainSurface(ProbeWorld, Start, End,
                            ProbeParams, ProbeBudget, Hit))
                    {
                        VisualBankTerrainZCm[Index] =
                            static_cast<float>(Hit.ImpactPoint.Z);
                        VisualBankProbeState[Index] = 1;
                    }
                    else
                    {
                        // Budget exhaustion is not a cached geometric miss.
                        // Streamed terrain invalidates genuine misses later.
                        VisualBankProbeState[Index] = ProbeBudget == 0 ? 0 : 2;
                    }
                }
                if (VisualBankProbeState[Index] == 1)
                {
                    const float RenderedDepthCm =
                        static_cast<float>(WaterWorld.Z) -
                        VisualBankTerrainZCm[Index];
                    const bool bMeasuredBedAligned =
                        LiveSolverWetVertexMask[Index] != 0 &&
                        FMath::IsFinite(WaterSamples[Index].BedHeightMeters) &&
                        FMath::Abs(WaterSamples[Index].BedHeightMeters * kSurfCmPerM -
                            VisualBankTerrainZCm[Index]) <= 10.0f;
                    if (bMeasuredBedAligned)
                    {
                        // Here the real terrain clips one bed-aligned water
                        // surface. Dropping its shallowest wet row and then
                        // shortening the shore reach leaves a 20 cm hanging
                        // edge. Keep physical shallows; film suppression is
                        // only a compatibility measure for mismatched beds.
                        VisualFilmCullState[Index] = 0;
                    }
                    else if (VisualFilmCullState[Index] == 0 &&
                        RenderedDepthCm < kVisualBankFilmEnterDepthCm)
                    {
                        VisualFilmCullState[Index] = 1;
                    }
                    else if (VisualFilmCullState[Index] != 0 &&
                             RenderedDepthCm > kVisualBankFilmExitDepthCm)
                    {
                        VisualFilmCullState[Index] = 0;
                    }
                    VisualFilmCullMask[Index] = VisualFilmCullState[Index];
                }
            };
            if (bCartesianFlow)
            {
                const auto& EdgeSteps = RaftSimWetEdgeAudit::EvaluateCached(
                    WetEdgeDistanceCache, GridStationN, GridLateralN, VolumeCoreWetMask,2);
                for (int32 I=0; I<Vertices.Num(); ++I)
                    if (VolumeCoreWetMask[I] && EdgeSteps[I]<kVisualBankBandRings)
                        EvaluateBandCell(I%GridStationN, I/GridStationN);
            }
            else for (int32 X = 0; X < GridStationN; ++X)
            {
                const int32 MinimumY = VolumeCoreMinimumWetLateralIndex[X];
                const int32 MaximumY = VolumeCoreMaximumWetLateralIndex[X];
                if (MinimumY < 0 || MaximumY < MinimumY)
                {
                    continue;
                }
                for (int32 Ring = 0; Ring < kVisualBankBandRings; ++Ring)
                {
                    EvaluateBandCell(X, MinimumY + Ring);
                    if (MaximumY - Ring > MinimumY + kVisualBankBandRings - 1)
                    {
                        EvaluateBandCell(X, MaximumY - Ring);
                    }
                }
            }
            // Solver/baseline disagreement cells (dry verdict over baseline
            // water) need probes too: the visual-submersion keep defends a
            // whole shallow shelf, and probing only the outer bank rings
            // left the shelf interior to drain as a marching straight front
            // when the crop's authority swept in ("the water suddenly
            // recedes from the shores", player recording 2026-08-30). These
            // cells are no longer wet, so they bypass the wet-mask guard.
            if (ProbeWorld)
            {
                for (int32 Index = 0;
                     Index < Vertices.Num() && ProbeBudget > 0;
                     ++Index)
                {
                    if (BaselineKeepProbeWanted[Index] == 0 ||
                        VisualBankProbeState[Index] != 0)
                    {
                        continue;
                    }
                    const FVector WaterWorld =
                        CarrierTransform.TransformPosition(Vertices[Index]);
                    FHitResult Hit;
                    FCollisionQueryParams ProbeParams(
                        TEXT("RaftSimVisualBankProbe"), true, this);
                    if (TraceTerrainSurface(ProbeWorld,
                            WaterWorld + FVector(0.0f, 0.0f, 300.0f),
                            WaterWorld - FVector(0.0f, 0.0f, 600.0f),
                            ProbeParams, ProbeBudget, Hit))
                    {
                        VisualBankTerrainZCm[Index] =
                            static_cast<float>(Hit.ImpactPoint.Z);
                        VisualBankProbeState[Index] = 1;
                    }
                    else
                    {
                        VisualBankProbeState[Index] = ProbeBudget == 0 ? 0 : 2;
                    }
                }
            }
        }
        // Slow rates: wake lapping and window handoffs churn the bank wet
        // edge at cell granularity; the envelope averages those transients
        // while genuine water-level changes still track within a couple of
        // seconds.
        const float PresenceAttackBlend = 1.0f - FMath::Exp(
            -2.2f * FMath::Max(RefreshIntervalSeconds, 0.0f));
        const float PresenceReleaseBlend = 1.0f - FMath::Exp(
            -1.4f * FMath::Max(RefreshIntervalSeconds, 0.0f));
        for (int32 Index = 0; Index < Vertices.Num(); ++Index)
        {
            // Solver-wet cells present fully; baseline shoreline water
            // presents through the crop-authority feather so ownership
            // handovers are spatial gradients, never flips. A rendered-
            // terrain film cull overrides both: the release rate fades the
            // sliver out instead of popping it.
            const float PresenceTarget =
                ConnectedWetMask[Index] == 0 || VisualFilmCullMask[Index] != 0
                ? 0.0f
                : FMath::Max(
                      LiveSolverWetVertexMask[Index] != 0 ? 1.0f : 0.0f,
                      FeatheredBaselineWet[Index]);
            float Presence = FMath::Lerp(
                LiveVolumeCoreWetPresence[Index],
                PresenceTarget,
                PresenceTarget > LiveVolumeCoreWetPresence[Index]
                    ? PresenceAttackBlend
                    : PresenceReleaseBlend);
            // Snap the settled tails so long-stable cells compare exactly
            // and topology only changes once a fade has fully finished.
            if (Presence > 0.995f)
            {
                Presence = 1.0f;
            }
            else if (Presence < 0.005f)
            {
                Presence = 0.0f;
            }
            LiveVolumeCoreWetPresence[Index] = Presence;
        }

        if (bCartesianFlow)
        {
            CartesianShoreWet.SetNumUninitialized(Vertices.Num());
            CartesianShoreDepthM.SetNumUninitialized(Vertices.Num());
            CartesianShoreBedM.SetNumUninitialized(Vertices.Num());
            for (int32 I=0; I<Vertices.Num(); ++I)
            {
                CartesianShoreDepthM[I] = WaterSamples[I].DepthMeters;
                CartesianShoreBedM[I] = WaterSamples[I].BedHeightMeters;
                CartesianShoreWet[I] = CartesianShoreAvailable[I] && ConnectedWetMask[I] &&
                    !VisualFilmCullMask[I] && VolumeCoreWetMask[I] && WaterSamples[I].DepthMeters>1.e-4f &&
                    StationEdgeCoverage(I%GridStationN)>=kLiveVolumeCoreMinimumStationCoverage;
            }
        }

        // One immutable index list, the terminal form of a long render
        // lesson: a recreated mesh section is a new render proxy, and its
        // first frame renders with no temporal history and cold shading
        // caches — TSR pops at high framerate, and at PIE-hitch framerates
        // the Single Layer Water shore strip loses its reflection for a
        // whole visible frame and shows the bed through clear water ("the
        // shore appears and disappears", player recording 2026-08-30; the
        // drift benchmark logged ~2 section recreations per second from
        // wet-membership churn despite the earlier interior/boundary split
        // and frozen band). The split, the depth latch, and the band-escape
        // rebuilds are therefore all retired: the core's topology now covers
        // EVERY lattice cell that passes the static station-coverage feather
        // and is built exactly once per grid shape. Wet/dry churn,
        // recentres, band motion, the film cull, and the crop feather all
        // move VERTICES (dry columns collapse to zero-area piles on the
        // waterline), so after the first build the render proxy is never
        // recreated and no frame ever renders without history.
        // Per-station presence bounds of the rendered band, needed by the
        // waterline band below and the sub-cell extension later.
        TArray<int32> MinPresentY;
        TArray<int32> MaxPresentY;
        MinPresentY.Init(INDEX_NONE, GridStationN);
        MaxPresentY.Init(INDEX_NONE, GridStationN);
        for (int32 Y = 0; Y < GridLateralN; ++Y)
        {
            for (int32 X = 0; X < GridStationN; ++X)
            {
                if (LiveVolumeCoreWetPresence[Y * GridStationN + X] > 0.0f)
                {
                    if (MinPresentY[X] == INDEX_NONE)
                    {
                        MinPresentY[X] = Y;
                    }
                    MaxPresentY[X] = Y;
                }
            }
        }
        // Immutable full-lattice topology. Only the station-edge coverage
        // feather trims cells, and that is a pure function of X and the grid
        // constants, so the list is identical for every refresh of a given
        // grid shape. Cells the water never reaches render as zero-area
        // piles through the vertex collapse below.
        // The topology is immutable per grid shape, but which edge rows carry
        // triangles depends on whether the grid sits at a corridor end (the
        // 36 m blend excludes them elsewhere). Built once at the launch, the
        // core then had no triangles for the first 18 m of Hance when the raft
        // reached the put-in, whatever the vertex coverage said.
        const int32 TopologyEdgeState = CorridorEndPadState();
        if (LiveVolumeCoreStaticTopologyVertexCount != Vertices.Num() ||
            LiveVolumeCoreStaticTopologyEdgeState != TopologyEdgeState)
        {
            LiveVolumeCoreStaticTopologyVertexCount = Vertices.Num();
            LiveVolumeCoreStaticTopologyEdgeState = TopologyEdgeState;
            LiveVolumeCoreTriangles.Reset(
                (GridStationN - 1) * (GridLateralN - 1) * 6);
            for (int32 Y = 0; Y < GridLateralN - 1; ++Y)
            {
                for (int32 X = 0; X < GridStationN - 1; ++X)
                {
                    const int32 I0 = Y * GridStationN + X;
                    const int32 I1 = I0 + 1;
                    const int32 I2 = I0 + GridStationN;
                    const int32 I3 = I2 + 1;
                    const float MinimumCellStationCoverage = FMath::Min(
                        StationEdgeCoverage(X),
                        StationEdgeCoverage(X + 1));
                    if (MinimumCellStationCoverage <
                        kLiveVolumeCoreMinimumStationCoverage)
                    {
                        continue;
                    }
                    LiveVolumeCoreTriangles.Add(I0);
                    LiveVolumeCoreTriangles.Add(I2);
                    LiveVolumeCoreTriangles.Add(I1);
                    LiveVolumeCoreTriangles.Add(I1);
                    LiveVolumeCoreTriangles.Add(I2);
                    LiveVolumeCoreTriangles.Add(I3);
                }
            }
        }
        // (The diagonal stitch triangles the one-row bank steps used to need
        // are gone: every dry cell is emitted and collapses onto the
        // waterline, so the edge fill is real geometry.)
        if (!bCartesianFlow && bLivePresentationBankNaturalismEnabled)
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
                const int32 MinimumY =
                    VolumeCoreMinimumWetLateralIndex[X];
                const int32 MaximumY =
                    VolumeCoreMaximumWetLateralIndex[X];
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
        // Sub-cell waterline: the mesh otherwise ends exactly on the
        // outermost wet lattice vertex, so the shoreline renders as
        // cell-sized rectangular steps and every wet/dry change slides the
        // edge a whole 1.5 m cell (player screenshot, 2026-08-27). The
        // depth gradient toward the bank locates where depth actually
        // reaches zero, and the boundary vertex extrapolates outward to
        // that point: the edge becomes continuous along the bank, slides
        // smoothly as the water level moves, and hands over seamlessly
        // when a new cell turns wet (its extrapolation starts near zero).
        // Reach is computed per station for both banks, then smoothed along
        // the station axis so neighbouring boundary vertices agree; without
        // the smoothing, shallow-depth noise gave adjacent stations very
        // different reaches and the waterline zig-zagged.
        const auto ComputeBankReach =
            [&](const TArray<int32>& BoundRows, int32 InteriorStep,
                TArray<float>& OutReach)
        {
            OutReach.Init(-1.0f, GridStationN);
            for (int32 X = 0; X < GridStationN; ++X)
            {
                const int32 BoundaryY = BoundRows[X];
                const int32 InteriorY = BoundaryY + InteriorStep;
                if (BoundaryY == INDEX_NONE || InteriorY < 0 ||
                    InteriorY >= GridLateralN)
                {
                    continue;
                }
                const int32 BoundaryIndex = BoundaryY * GridStationN + X;
                const int32 InteriorIndex = InteriorY * GridStationN + X;
                if (WetVertexMask[BoundaryIndex] == 0 ||
                    WetVertexMask[InteriorIndex] == 0)
                {
                    continue;
                }
                const float BoundaryDepthM =
                    WaterSamples[BoundaryIndex].DepthMeters;
                const float InteriorDepthM =
                    WaterSamples[InteriorIndex].DepthMeters;
                // Reach to the ~3 cm depth line, not the exact zero line:
                // Single Layer Water renders a near-zero-depth strip as pure
                // specular coat with no volume tint, so extending to zero
                // depth painted a broad glossy film past the visible blue
                // edge ("the shiny layer rides up onto the shore while the
                // blue doesn't", player screenshot 2026-08-28). Stopping
                // where a little depth remains keeps mesh edge and visible
                // water edge together. Presence scales the reach so the
                // extension ramps in with a fading-in cell instead of
                // snapping on the frame its envelope completes.
                constexpr float kShoreFilmDepthMarginM = 0.03f;
                OutReach[X] = FMath::Clamp(
                    (BoundaryDepthM - kShoreFilmDepthMarginM) /
                        FMath::Max(InteriorDepthM - BoundaryDepthM, 0.05f),
                    0.0f,
                    0.85f) *
                    FMath::SmoothStep(
                        0.55f, 1.0f,
                        LiveVolumeCoreWetPresence[BoundaryIndex]);
                // Do not re-bridge ground the rendered-terrain film cull just
                // uncovered: extending toward a culled neighbour would lay the
                // specular film right back over the visible bank.
                const int32 OutwardY = BoundaryY - InteriorStep;
                if (OutwardY >= 0 && OutwardY < GridLateralN &&
                    VisualFilmCullMask[OutwardY * GridStationN + X] != 0)
                {
                    OutReach[X] *= 0.25f;
                }
            }
            // Two conservative box passes; only neighbours whose bound rows
            // differ by at most one cell participate, so reach never
            // smears across a genuine break in the bank.
            for (int32 Pass = 0; Pass < 2; ++Pass)
            {
                TArray<float> Smoothed = OutReach;
                for (int32 X = 0; X < GridStationN; ++X)
                {
                    if (OutReach[X] < 0.0f)
                    {
                        continue;
                    }
                    float Sum = OutReach[X] * 2.0f;
                    float Weight = 2.0f;
                    for (const int32 NeighbourX : {X - 1, X + 1})
                    {
                        if (NeighbourX < 0 || NeighbourX >= GridStationN ||
                            OutReach[NeighbourX] < 0.0f ||
                            BoundRows[NeighbourX] == INDEX_NONE ||
                            FMath::Abs(BoundRows[NeighbourX] - BoundRows[X]) > 1)
                        {
                            continue;
                        }
                        Sum += OutReach[NeighbourX];
                        Weight += 1.0f;
                    }
                    Smoothed[X] = Sum / Weight;
                }
                OutReach = MoveTemp(Smoothed);
            }
            // Apply: HORIZONTAL reach only. Extending along the boundary/
            // interior slope rode the water sheet up the bank like a carpet
            // with a visible gap under the raised lip (player screenshots,
            // 2026-08-27); a flat reach lets rising terrain clip the water
            // plane at the true waterline instead.
            for (int32 X = 0; X < GridStationN; ++X)
            {
                if (OutReach[X] <= 0.0f || BoundRows[X] == INDEX_NONE)
                {
                    continue;
                }
                const int32 BoundaryIndex = BoundRows[X] * GridStationN + X;
                const int32 InteriorIndex =
                    (BoundRows[X] + InteriorStep) * GridStationN + X;
                FVector OutwardCm =
                    Vertices[BoundaryIndex] - Vertices[InteriorIndex];
                OutwardCm.Z = 0.0;
                LiveVolumeCoreVertices[BoundaryIndex] +=
                    OutwardCm * OutReach[X];
            }
        };
        if (!bCartesianFlow)
        {
        TArray<float> BankReachScratch;
        ComputeBankReach(MinPresentY, +1, BankReachScratch);
        ComputeBankReach(MaxPresentY, -1, BankReachScratch);

        // Presence-driven shoreline collapse. A partially present vertex
        // slides onto its most-present lateral neighbour (after the bank
        // retreat, so the water's edge stays inside the retreated contour);
        // at zero presence its quads have collapsed to zero area. Fading
        // strips chain toward the channel because earlier rows collapse
        // first.
        for (int32 Y = 0; Y < GridLateralN; ++Y)
        {
            for (int32 X = 0; X < GridStationN; ++X)
            {
                const int32 Index = Y * GridStationN + X;
                const float Presence = LiveVolumeCoreWetPresence[Index];
                if (Presence <= 0.0f || Presence >= 1.0f)
                {
                    continue;
                }
                const int32 TowardRightIndex =
                    Y > 0 ? Index - GridStationN : Index;
                const int32 TowardLeftIndex =
                    Y < GridLateralN - 1 ? Index + GridStationN : Index;
                const int32 AnchorIndex =
                    LiveVolumeCoreWetPresence[TowardRightIndex] >=
                        LiveVolumeCoreWetPresence[TowardLeftIndex]
                    ? TowardRightIndex
                    : TowardLeftIndex;
                const float Expansion =
                    Presence * Presence * (3.0f - 2.0f * Presence);
                LiveVolumeCoreVertices[Index] = FMath::Lerp(
                    LiveVolumeCoreVertices[AnchorIndex],
                    LiveVolumeCoreVertices[Index],
                    Expansion);
                LiveVolumeCoreVertexColors[Index].A *= Expansion;
            }
        }
        // One collapse target per boulder footprint: the grid vertex nearest
        // the footprint centre, where the cutout gap's whole funnel gathers
        // and dives beneath the rock mesh.
        TArray<int32> BoulderFootprintNearestVertex;
        BoulderFootprintNearestVertex.Init(
            INDEX_NONE, WindowBoulderFootprintsSLR.Num());
        for (int32 FootprintIndex = 0;
             FootprintIndex < WindowBoulderFootprintsSLR.Num();
             ++FootprintIndex)
        {
            const FVector3f& Footprint =
                WindowBoulderFootprintsSLR[FootprintIndex];
            float BestDistanceSq = MAX_flt;
            for (int32 Index = 0; Index < Vertices.Num(); ++Index)
            {
                const float DistanceSq = FVector2D(
                    static_cast<float>(RiverCoordinatesM[Index].X) -
                        Footprint.X,
                    static_cast<float>(RiverCoordinatesM[Index].Y) -
                        Footprint.Y).SizeSquared();
                if (DistanceSq < BestDistanceSq)
                {
                    BestDistanceSq = DistanceSq;
                    BoulderFootprintNearestVertex[FootprintIndex] = Index;
                }
            }
        }
        // Directed dry pile: every fully dry vertex in a column with any
        // presence sits EXACTLY on the finished (retreated + extended)
        // waterline vertex of its column, so every dry quad in the immutable
        // full-lattice topology is genuinely zero-area — the geometry that
        // keeps wet/dry churn off the index list entirely. The copy chains
        // outward from the waterline across the WHOLE column on each bank.
        for (int32 X = 0; X < GridStationN; ++X)
        {
            if (MinPresentY[X] == INDEX_NONE)
            {
                continue;
            }
            for (int32 Y = MinPresentY[X] - 1; Y >= 0; --Y)
            {
                const int32 Index = Y * GridStationN + X;
                const int32 AnchorIndex = (Y + 1) * GridStationN + X;
                LiveVolumeCoreVertices[Index] =
                    LiveVolumeCoreVertices[AnchorIndex];
                LiveVolumeCoreNormals[Index] =
                    LiveVolumeCoreNormals[AnchorIndex];
                LiveVolumeCoreVertexColors[Index] =
                    LiveVolumeCoreVertexColors[AnchorIndex];
                LiveVolumeCoreVertexColors[Index].A = 0.0f;
            }
            for (int32 Y = MaxPresentY[X] + 1; Y < GridLateralN; ++Y)
            {
                const int32 Index = Y * GridStationN + X;
                const int32 AnchorIndex = (Y - 1) * GridStationN + X;
                LiveVolumeCoreVertices[Index] =
                    LiveVolumeCoreVertices[AnchorIndex];
                LiveVolumeCoreNormals[Index] =
                    LiveVolumeCoreNormals[AnchorIndex];
                LiveVolumeCoreVertexColors[Index] =
                    LiveVolumeCoreVertexColors[AnchorIndex];
                LiveVolumeCoreVertexColors[Index].A = 0.0f;
            }
            // Interior presence gaps. Two kinds, two treatments — both
            // learned the hard way on 2026-08-30:
            //
            // A boulder-cutout gap collapses onto ONE sunken point at its
            // footprint's centre, well below the rock's base. Every mutual
            // quad inside the hole is then exactly degenerate, and the rim
            // cone from the waterline dives underneath the rock mesh that
            // owns the cutout, which occludes it. (A per-column 1.5 m sink
            // rendered the funnel itself: a crater of exposed bed around
            // every exposed rock, with steep faceted water walls and a
            // stray deep-blue skirt triangle — "no pillow and hole in
            // water" / "disappearing water", player screenshots at km
            // 0.98/1.02.)
            //
            // A footprint-less gap (a shallow gravel bar) keeps the
            // original same-column nearest-wet-row copy: adjacent columns
            // can still disagree across the middle of the bar and leave
            // thin slivers, but those read as wet sheen on a bar, not as
            // a crater.
            int32 LastWetY = MinPresentY[X];
            for (int32 Y = MinPresentY[X] + 1; Y < MaxPresentY[X]; ++Y)
            {
                const int32 Index = Y * GridStationN + X;
                if (LiveVolumeCoreWetPresence[Index] > 0.0f)
                {
                    LastWetY = Y;
                    continue;
                }
                int32 NextWetY = Y + 1;
                while (NextWetY < MaxPresentY[X] &&
                       LiveVolumeCoreWetPresence[
                           NextWetY * GridStationN + X] <= 0.0f)
                {
                    ++NextWetY;
                }
                const int32 AnchorY =
                    (Y - LastWetY <= NextWetY - Y) ? LastWetY : NextWetY;
                const int32 AnchorIndex = AnchorY * GridStationN + X;
                int32 FootprintSinkIndex = INDEX_NONE;
                float FootprintSinkDropCm = 0.0f;
                const FVector2D& GapRiverM = RiverCoordinatesM[Index];
                for (int32 FootprintIndex = 0;
                     FootprintIndex < WindowBoulderFootprintsSLR.Num();
                     ++FootprintIndex)
                {
                    const FVector3f& Footprint =
                        WindowBoulderFootprintsSLR[FootprintIndex];
                    const float RadiusM = FMath::Max(Footprint.Z, 0.75f);
                    const float DeltaStationM =
                        static_cast<float>(GapRiverM.X) - Footprint.X;
                    const float DeltaLateralM =
                        static_cast<float>(GapRiverM.Y) - Footprint.Y;
                    if (FMath::Abs(DeltaStationM) > RadiusM * 1.45f ||
                        FMath::Abs(DeltaLateralM) > RadiusM * 1.45f)
                    {
                        continue;
                    }
                    if (FVector2D(DeltaStationM, DeltaLateralM).SizeSquared() >
                        FMath::Square(RadiusM * 1.45f))
                    {
                        continue;
                    }
                    if (BoulderFootprintNearestVertex.IsValidIndex(
                            FootprintIndex) &&
                        BoulderFootprintNearestVertex[FootprintIndex] !=
                            INDEX_NONE)
                    {
                        FootprintSinkIndex =
                            BoulderFootprintNearestVertex[FootprintIndex];
                        FootprintSinkDropCm = RadiusM * 80.0f;
                    }
                    break;
                }
                if (FootprintSinkIndex != INDEX_NONE)
                {
                    // Footprint centre in the horizontal plane; the column's
                    // own wet rim supplies the height reference so the sink
                    // depth follows the local water level, not a stale dry
                    // sample at the gap centre.
                    LiveVolumeCoreVertices[Index].X =
                        LiveVolumeCoreVertices[FootprintSinkIndex].X;
                    LiveVolumeCoreVertices[Index].Y =
                        LiveVolumeCoreVertices[FootprintSinkIndex].Y;
                    LiveVolumeCoreVertices[Index].Z =
                        LiveVolumeCoreVertices[AnchorIndex].Z -
                        FootprintSinkDropCm;
                    LiveVolumeCoreNormals[Index] = FVector::UpVector;
                }
                else
                {
                    LiveVolumeCoreVertices[Index] =
                        LiveVolumeCoreVertices[AnchorIndex];
                    LiveVolumeCoreNormals[Index] =
                        LiveVolumeCoreNormals[AnchorIndex];
                }
                LiveVolumeCoreVertexColors[Index] =
                    LiveVolumeCoreVertexColors[AnchorIndex];
                LiveVolumeCoreVertexColors[Index].A = 0.0f;
            }
        }
        // Columns with no presence at all (the lattice corners past a bend,
        // or the whole grid when the raft is beached): collapse every vertex
        // onto the nearest present column's already-piled edge vertex so the
        // quads bridging into them are zero-area too. Two sweeps give each
        // dry column its nearest present column without a search per column.
        {
            TArray<int32> NearestPresentX;
            NearestPresentX.Init(INDEX_NONE, GridStationN);
            int32 Carry = INDEX_NONE;
            for (int32 X = 0; X < GridStationN; ++X)
            {
                if (MinPresentY[X] != INDEX_NONE)
                {
                    Carry = X;
                }
                NearestPresentX[X] = Carry;
            }
            Carry = INDEX_NONE;
            for (int32 X = GridStationN - 1; X >= 0; --X)
            {
                if (MinPresentY[X] != INDEX_NONE)
                {
                    Carry = X;
                }
                else if (Carry != INDEX_NONE &&
                         (NearestPresentX[X] == INDEX_NONE ||
                          Carry - X < X - NearestPresentX[X]))
                {
                    NearestPresentX[X] = Carry;
                }
            }
            for (int32 X = 0; X < GridStationN; ++X)
            {
                if (MinPresentY[X] != INDEX_NONE)
                {
                    continue;
                }
                const int32 AnchorX = NearestPresentX[X];
                for (int32 Y = 0; Y < GridLateralN; ++Y)
                {
                    const int32 Index = Y * GridStationN + X;
                    if (AnchorX != INDEX_NONE)
                    {
                        const int32 AnchorIndex =
                            Y * GridStationN + AnchorX;
                        LiveVolumeCoreVertices[Index] =
                            LiveVolumeCoreVertices[AnchorIndex];
                        LiveVolumeCoreNormals[Index] =
                            LiveVolumeCoreNormals[AnchorIndex];
                        LiveVolumeCoreVertexColors[Index] =
                            LiveVolumeCoreVertexColors[AnchorIndex];
                    }
                    else
                    {
                        // No water anywhere in the window: sink the whole
                        // degenerate lattice out of sight instead of
                        // clearing the section (a clear is a render-state
                        // invalidation; this is just vertex motion).
                        LiveVolumeCoreVertices[Index] =
                            FVector(0.0f, 0.0f, -100000.0f);
                    }
                    LiveVolumeCoreVertexColors[Index].A = 0.0f;
                }
            }
        }
        } // Legacy column reach/collapse. Cartesian dry regions are clipped in 2D.
#if !UE_BUILD_SHIPPING
        const float ShoreProbeStation = CVarRaftSimShorelineProbeStation.GetValueOnGameThread();
        if (ShoreProbeStation >= 0.0f && GetWorld() && GetWorld()->GetTimeSeconds() >= 8.0f &&
            GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")))
        {
            int32 ProbeX = INDEX_NONE;
            float ClosestStation = ResolvedVertexSpacingMeters;
            for (int32 X = 0; X < GridStationN; ++X)
            {
                const float Delta = FMath::Abs(float(RiverCoordinatesM[X].X) - ShoreProbeStation);
                if (Delta < ClosestStation) { ClosestStation = Delta; ProbeX = X; }
            }
            if (ProbeX != INDEX_NONE)
            {
                CVarRaftSimShorelineProbeStation->Set(-1.0f, ECVF_SetByConsole);
                const FTransform Transform = LiveVolumeCoreMesh->GetComponentTransform();
                for (int32 Y = 0; Y < GridLateralN; ++Y)
                {
                    const int32 Index = Y * GridStationN + ProbeX;
                    const FVector Before = Transform.TransformPosition(Vertices[Index]);
                    const FVector After = Transform.TransformPosition(LiveVolumeCoreVertices[Index]);
                    FHitResult Hit;
                    int32 Budget = 4;
                    FCollisionQueryParams Params(TEXT("RaftSimShorelineDiagnostic"), true, this);
                    const bool bHit = TraceTerrainSurface(GetWorld(), After + FVector(0, 0, 1000),
                        After - FVector(0, 0, 2000), Params, Budget, Hit);
                    UE_LOG(LogTemp, Display,
                        TEXT("ShoreProbe s=%.2f l=%.2f wet=%d live=%d connected=%d presence=%.3f alpha=%.3f depth=%.3f source_z=%.2f render_z=%.2f shift_xy=%.3f film=%d cached=%d terrain_hit=%d clearance=%.3f"),
                        RiverCoordinatesM[Index].X, RiverCoordinatesM[Index].Y,
                        WetVertexMask[Index], LiveSolverWetVertexMask[Index], ConnectedWetMask[Index],
                        LiveVolumeCoreWetPresence[Index], LiveVolumeCoreVertexColors[Index].A,
                        WaterSamples[Index].DepthMeters, Before.Z / 100.0, After.Z / 100.0,
                        FVector::Dist2D(Before, After) / 100.0, VisualFilmCullMask[Index],
                        VisualBankProbeState[Index], bHit ? 1 : 0,
                        bHit ? (After.Z - Hit.ImpactPoint.Z) / 100.0 : -999.0);
                }
            }
        }
#endif
        LiveVolumeCoreTriangleCount = LiveVolumeCoreTriangles.Num() / 3;
        if (LiveVolumeCoreTriangleCount > 0)
        {
            const TArray<FVector2D> VolumeCoreEmptyUVs;
            // "Missing" includes a cleared or mis-sized section: the entry
            // survives ClearMeshSection with zero vertices, and an in-place
            // update against it raises a per-call engine error.
            const FProcMeshSection* CoreSectionState =
                LiveVolumeCoreMesh->GetProcMeshSection(0);
            // A rebuilt topology (corridor-end rows gained or lost) must also
            // recreate the section: an in-place update keeps the old index
            // buffer.
            const bool bSectionMissing = bCartesianFlow
                ? CartesianShoreSourceVertexCount != LiveVolumeCoreVertices.Num()
                : CoreSectionState == nullptr ||
                CoreSectionState->ProcVertexBuffer.Num() !=
                    LiveVolumeCoreVertices.Num() ||
                CoreSectionState->ProcIndexBuffer.Num() !=
                    LiveVolumeCoreTriangles.Num();
            const bool bRenderedStateShapeMatches =
                RenderedLiveVolumeCoreVertices.Num() ==
                    LiveVolumeCoreVertices.Num() &&
                RenderedLiveVolumeCoreNormals.Num() ==
                    LiveVolumeCoreNormals.Num() &&
                RenderedLiveVolumeCoreVertexColors.Num() ==
                    LiveVolumeCoreVertexColors.Num() &&
                RenderedLiveVolumeCoreFlowVelocity.Num() ==
                    FlowVelocityMetersPerSecond.Num() &&
                RenderedLiveVolumeCoreWakeData.Num() ==
                    BoatWakePresentationData.Num();
            // A recentre shifts the lattice by whole station cells, so the
            // previously rendered overlap can be carried into the new index
            // space instead of discarding the in-flight interpolation.
            // Hard-swapping the mid-blend surface for the fresh solve was the
            // one remaining whole-carrier snap, repeating every
            // CurvedGridRecenterDistanceMeters of travel. Vertices entering
            // at the leading edge have no history and seed at their targets,
            // inside the station-edge alpha feather.
            bool bRecentreCarryApplied = false;
            if (bSingleLiveWaterSurfaceEnabled && bGridRecentredThisRefresh &&
                !bSectionMissing && bRenderedStateShapeMatches)
            {
                const float SafeSpacingMeters = FMath::Max(
                    ResolvedVertexSpacingMeters, KINDA_SMALL_NUMBER);
                const float ShiftCellsExact =
                    (CurvedGridCenterStationM - PreviousGridCenterStationM) /
                    SafeSpacingMeters;
                const int32 ShiftCells = FMath::RoundToInt(ShiftCellsExact);
                const float ShiftNorthExact = (CartesianGridCenterNorthM - PreviousGridCenterNorthM) / SafeSpacingMeters;
                const int32 ShiftNorth = FMath::RoundToInt(ShiftNorthExact);
                // The river-end clamp can land the centre off the shared
                // lattice. Only an exact integer shift keeps every overlap
                // vertex at its previous river coordinates; otherwise fall
                // through to the hard swap below.
                if (FMath::Abs(ShiftCellsExact - ShiftCells) < 0.01f && FMath::Abs(ShiftNorthExact - ShiftNorth) < 0.01f)
                {
                    if (ShiftCells != 0 || ShiftNorth != 0)
                    {
                        CarryRenderedGridHistory(ShiftCells, ShiftNorth);
                    }
                    bRecentreCarryApplied = true;
                }
            }
            const bool bCanInterpolate =
                bSingleLiveWaterSurfaceEnabled &&
                (!bGridRecentredThisRefresh || bRecentreCarryApplied) &&
                !bSectionMissing &&
                bRenderedStateShapeMatches;
            if (bCanInterpolate)
            {
                // Preserve the exact currently rendered state as the start of
                // the next interval. Vertex positions, vertex normals, and
                // optical/foam channels then advance every rendered frame;
                // replacing these targets outright at 15 Hz made specular
                // reflections appear to jump even with one visible surface.
                LiveVolumeCoreInterpolationStartVertices =
                    RenderedLiveVolumeCoreVertices;
                LiveVolumeCoreInterpolationStartNormals =
                    RenderedLiveVolumeCoreNormals;
                LiveVolumeCoreInterpolationStartVertexColors =
                    RenderedLiveVolumeCoreVertexColors;
                LiveVolumeCoreInterpolationStartFlowVelocity =
                    RenderedLiveVolumeCoreFlowVelocity;
                LiveVolumeCoreInterpolationStartWakeData =
                    RenderedLiveVolumeCoreWakeData;
                LiveVolumeCoreInterpolationElapsedSeconds = 0.0f;
                bLiveVolumeCoreInterpolationActive = true;
                if (bRecentreCarryApplied)
                {
                    // Same world-space geometry the previous frame drew, but
                    // every index now maps to a shifted station. Push the
                    // carried state together with the recentred UVs so the
                    // river-anchored WPO and texture fields stay glued to
                    // their coordinates for the frame this refresh renders.
                    // With the immutable topology this is a plain in-place
                    // update — a recentre no longer touches the index list.
                    PublishLiveVolumeCore(RenderedLiveVolumeCoreVertices, RenderedLiveVolumeCoreNormals,
                        RenderedLiveVolumeCoreVertexColors, RenderedLiveVolumeCoreFlowVelocity,
                        RenderedLiveVolumeCoreWakeData, false,0.f);
                }
            }
            else if (bSectionMissing)
            {
                // The only remaining render-state invalidation: first build
                // of a grid shape (or an engine-side loss of the section).
                // Everything else — recentres, wet/dry churn, dry-out,
                // re-wet — is vertex motion on this one immortal section.
                LogWaterRenderStateEvent(
                    GetWorld(), TEXT("core_create_hard_section_missing"));
                PublishLiveVolumeCore(LiveVolumeCoreVertices, LiveVolumeCoreNormals,
                    LiveVolumeCoreVertexColors, FlowVelocityMetersPerSecond, BoatWakePresentationData, true);
                RenderedLiveVolumeCoreVertices = LiveVolumeCoreVertices;
                RenderedLiveVolumeCoreNormals = LiveVolumeCoreNormals;
                RenderedLiveVolumeCoreVertexColors =
                    LiveVolumeCoreVertexColors;
                RenderedLiveVolumeCoreFlowVelocity =
                    FlowVelocityMetersPerSecond;
                RenderedLiveVolumeCoreWakeData = BoatWakePresentationData;
                bLiveVolumeCoreInterpolationActive = false;
            }
            else
            {
                PublishLiveVolumeCore(LiveVolumeCoreVertices, LiveVolumeCoreNormals,
                    LiveVolumeCoreVertexColors, FlowVelocityMetersPerSecond, BoatWakePresentationData, false);
                RenderedLiveVolumeCoreVertices = LiveVolumeCoreVertices;
                RenderedLiveVolumeCoreNormals = LiveVolumeCoreNormals;
                RenderedLiveVolumeCoreVertexColors =
                    LiveVolumeCoreVertexColors;
                RenderedLiveVolumeCoreFlowVelocity =
                    FlowVelocityMetersPerSecond;
                RenderedLiveVolumeCoreWakeData = BoatWakePresentationData;
                bLiveVolumeCoreInterpolationActive = false;
            }
            // The mesh stays visible for the section's whole life: an
            // all-dry window is already invisible geometrically (every
            // vertex collapsed or sunk), and a visibility flip is itself a
            // render-state invalidation.
            if (bCartesianFlow)
            {
                if (LiveVolumeCoreMesh->IsVisible()) LiveVolumeCoreMesh->SetVisibility(false);
                if (!CartesianShorelineMesh->IsVisible()) CartesianShorelineMesh->SetVisibility(true);
                LiveVolumeCoreTriangleCount = CartesianShorelineMesh->GetWaterIndices().Num()/3;
            }
            else if (!LiveVolumeCoreMesh->IsVisible())
            {
                LiveVolumeCoreMesh->SetVisibility(true, true);
            }
        }
    }
    else
    {
        LiveVolumeCoreTriangleCount = 0;
        LiveVolumeCoreTriangles.Reset();
        LiveVolumeCoreStaticTopologyVertexCount = 0;
        bLiveVolumeCoreInterpolationActive = false;
        LiveVolumeCoreMesh->SetVisibility(false, true);
        CartesianShorelineMesh->SetVisibility(false);
    }

    Perf.Mark(TEXT("foam_core_publish"));
    // Present solver-owned foam on a separate masked lace sheet. Vertex alpha
    // combines advected foam with the verified station/bank feather; the
    // material's runtime raft ellipse removes foam over the boat and crew at
    // pixel resolution. This mesh is presentation-only.
    VisibleRapidFoamVertexCount = 0;
    const bool bSharedSurfaceLitCarrierOwnsFoam =
        bSharedBreakingReliefEnabled && !bLiveVolumeCoreEnabled;
    const bool bCartesianSingleCarrier = bCartesianFlow && bSingleLiveWaterSurfaceEnabled;
    if (bSharedSurfaceLitCarrierOwnsFoam || bCartesianSingleCarrier)
    {
        // The visible carrier already shades its advected foam. The Cartesian
        // single-surface path also kept calculating/uploading this entire
        // raised sheet even though it was unconditionally hidden below.
        // Keep foam transport and core channels above; omit only dead uploads.
        RapidFoamMesh->SetVisibility(false, true);
    }
    else if (RapidFoamVertices.Num() == Vertices.Num() &&
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
            // Authored-water rivers already own their broad foam/current
            // presentation. On those maps this raised masked sheet is only
            // the opaque lace on the animated boulder wake; using the whole
            // persistent foam field would recreate a second river texture.
            const float FoamSignal = bLiveSurfaceCarrierEnabled
                ? VertexColors[Index].R
                : BoulderWakeFoam[Index];
            const float FocusedFoam = FMath::SmoothStep(
                ResolvedRapidFoamFocusStart,
                ResolvedRapidFoamFocusEnd,
                FoamSignal) * ResolvedRapidFoamCoverageGain;
            const float TargetFoamCoverage = FMath::Clamp(
                FocusedFoam * VertexColors[Index].A,
                0.0f,
                1.0f);
            const float FoamCoverage = SmoothRapidFoamCoverage(
                SmoothedRapidFoamCoverage[Index],
                TargetFoamCoverage,
                FoamDeltaSeconds);
            SmoothedRapidFoamCoverage[Index] = FoamCoverage;
            RapidFoamVertexColors[Index] = FLinearColor(
                0.96f, 0.98f, 1.0f, FoamCoverage);
            if (FoamCoverage >= 0.01f)
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
            Tangents,
            /*bSRGBConversion=*/false);
        // Carrier maps use this for the full solver foam field. Authored-band
        // maps use it only for boulder-wake lace, which is masked (opaque foam
        // with real holes) rather than another translucent water surface.
        // South Fork's unified Single Layer Water already consumes the same
        // solver foam through VertexColor.R. Never place this second raised
        // texture above that surface: it was the layer that visibly outran the
        // drifting raft and blinked as marginal masked islands refreshed.
        // Keep the component stable while the material's per-pixel mask and
        // smoothed vertex coverage decide what is visible. Switching the
        // entire component at a single threshold made marginal foam fields
        // flash on and off from one 15 Hz refresh to the next.
        const bool bRapidFoamVisible =
            !bSingleLiveWaterSurfaceEnabled &&
            (bLiveSurfaceCarrierEnabled ||
                WindowBoulderFootprintsSLR.Num() > 0);
        if (RapidFoamMesh->IsVisible() != bRapidFoamVisible)
        {
            LogWaterRenderStateEvent(
                GetWorld(), TEXT("rapidfoam_visibility_flip"));
        }
        RapidFoamMesh->SetVisibility(bRapidFoamVisible, true);
    }

    const bool bBuildPaddleRipple = MaximumAbsoluteBoatWakeM > 0.001f &&
        CVarRaftSimPaddleWakeRippleOverlay.GetValueOnGameThread() != 0 &&
        CVarRaftSimFreezeCoreTopology.GetValueOnGameThread() < 2;
    TArray<FLinearColor> SurfacePresentationColors;
    if (!bCartesianSingleCarrier || bBuildPaddleRipple)
        SurfacePresentationColors = VertexColors;
    bSubmittedHullMask=IsValid(FoamOcclusionRaft);
    if (IsValid(FoamOcclusionRaft))
    {
        const FVector RaftCenterCm = FoamOcclusionRaft->GetActorLocation();
        const FVector RaftForward = FoamOcclusionRaft->GetActorForwardVector();
        SubmittedHullMaskCenter=RaftCenterCm;
        SubmittedHullMaskForward=RaftForward;
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

    int32 VisiblePaddleWakeVertexCount = 0;
    if (!bCartesianSingleCarrier || bBuildPaddleRipple)
        PaddleWakeVertexColors = VertexColors;
    for (int32 Index = 0; Index < SurfacePresentationColors.Num(); ++Index)
    {
        PaddleWakeVertexColors[Index].R = 0.0f;
        PaddleWakeVertexColors[Index].A =
            SurfacePresentationColors[Index].A *
            BoatWakePresentationData[Index].X;
        if (PaddleWakeVertexColors[Index].A > 0.05f)
        {
            ++VisiblePaddleWakeVertexCount;
        }
    }

    const TArray<FVector2D> EmptyUVs;
    // Section zero is hidden for the lifetime of the Cartesian single core.
    // Its source arrays still drive crests, foam, wakes and support; copying
    // them to a second unused procedural render buffer serves no consumer.
    if (!bCartesianSingleCarrier)
        UpdateSurfaceCarrierMesh(false,SurfacePresentationColors);

    // Rebuild section 1 from only the triangles touched by the wake. Its
    // topology is the bilateral ripple, while vertex alpha softly feathers
    // the signed displaced crest/trough bands without sampling a texture.
    int32 PaddleWakeRenderTriangleCount = 0;
    if (bBuildPaddleRipple)
    {
        TArray<FVector> RippleVertices;
        TArray<int32> RippleTriangles;
        TArray<FVector> RippleNormals;
        TArray<FVector2D> RippleUVs;
        TArray<FVector2D> RippleFlowVelocity;
        TArray<FVector2D> RipplePresentationData;
        TArray<FLinearColor> RippleColors;
        TArray<FProcMeshTangent> RippleTangents;
        const int32 ReserveVertexCount =
            FMath::Max(VisiblePaddleWakeVertexCount * 12, 96);
        RippleVertices.Reserve(ReserveVertexCount);
        RippleTriangles.Reserve(ReserveVertexCount);
        RippleNormals.Reserve(ReserveVertexCount);
        RippleUVs.Reserve(ReserveVertexCount);
        RippleFlowVelocity.Reserve(ReserveVertexCount);
        RipplePresentationData.Reserve(ReserveVertexCount);
        RippleColors.Reserve(ReserveVertexCount);
        RippleTangents.Reserve(ReserveVertexCount);
        TMap<int32, FVector> RippleVertexCache;
        RippleVertexCache.Reserve(VisiblePaddleWakeVertexCount * 2);

        TArray<int32> RippleSourceCells;
        RippleSourceCells.Reserve(ReserveVertexCount);
        auto AppendRippleVertex = [&](int32 SourceIndex)
        {
            RippleTriangles.Add(RippleVertices.Num());
            RippleSourceCells.Add(SourceIndex);
            FVector RippleVertex = Vertices[SourceIndex];
            if (const FVector* CachedVertex =
                    RippleVertexCache.Find(SourceIndex))
            {
                RippleVertex = *CachedVertex;
            }
            else
            {
                FRaftSimWaterSample SupportSample;
                if (WaterAdapter &&
                    WaterAdapter->SampleRaftSupportSurfaceAtWorldPosition(
                        RippleVertex, SupportSample) &&
                    SupportSample.bWet)
                {
                    const float SupportBaseZCm =
                        SupportSample.SurfaceHeightMeters * kSurfCmPerM +
                        GetLiveSurfaceRenderLiftCm();
                    RippleVertex.Z =
                        SupportBaseZCm +
                        BoatWakeDisplacementMeters[SourceIndex] * kSurfCmPerM;
                }
                RippleVertexCache.Add(SourceIndex, RippleVertex);
            }
            RippleVertices.Add(RippleVertex);
            RippleNormals.Add(Normals[SourceIndex]);
            RippleUVs.Add(UVs[SourceIndex]);
            RippleFlowVelocity.Add(
                FlowVelocityMetersPerSecond[SourceIndex]);
            RipplePresentationData.Add(
                BoatWakePresentationData[SourceIndex]);
            RippleColors.Add(PaddleWakeVertexColors[SourceIndex]);
            RippleTangents.Add(Tangents[SourceIndex]);
        };
        auto AppendRippleTriangle = [&](int32 A, int32 B, int32 C)
        {
            const float Coverage = FMath::Max3(
                PaddleWakeVertexColors[A].A,
                PaddleWakeVertexColors[B].A,
                PaddleWakeVertexColors[C].A);
            if (Coverage <= 0.02f)
            {
                return;
            }
            AppendRippleVertex(A);
            AppendRippleVertex(B);
            AppendRippleVertex(C);
        };
        for (int32 WakeY = 0; WakeY < GridLateralN - 1; ++WakeY)
        {
            for (int32 WakeX = 0; WakeX < GridStationN - 1; ++WakeX)
            {
                const int32 I0 = WakeY * GridStationN + WakeX;
                const int32 I1 = I0 + 1;
                const int32 I2 = I0 + GridStationN;
                const int32 I3 = I2 + 1;
                AppendRippleTriangle(I0, I2, I1);
                AppendRippleTriangle(I1, I2, I3);
            }
        }
        PaddleWakeRenderTriangleCount = RippleTriangles.Num() / 3;
        // Same membership as the previous refresh -> update the section in
        // place. Recreating it 15 times a second replaced the near-raft
        // overlay's render state every refresh, a visible hitch exactly
        // where the guide looks.
        const FProcMeshSection* RippleSectionState =
            SurfaceMesh->GetProcMeshSection(1);
        if (RippleSourceCells == LastPaddleWakeRippleSourceCells &&
            RippleSectionState != nullptr &&
            RippleSectionState->ProcVertexBuffer.Num() == RippleVertices.Num())
        {
            SurfaceMesh->UpdateMeshSection_LinearColor(
                1,
                RippleVertices,
                RippleNormals,
                RippleUVs,
                RippleFlowVelocity,
                RipplePresentationData,
                EmptyUVs,
                RippleColors,
                RippleTangents,
                /*bSRGBConversion=*/false);
        }
        else
        {
            LogWaterRenderStateEvent(GetWorld(), TEXT("ripple_create"));
            SurfaceMesh->CreateMeshSection_LinearColor(
                1,
                RippleVertices,
                RippleTriangles,
                RippleNormals,
                RippleUVs,
                RippleFlowVelocity,
                RipplePresentationData,
                EmptyUVs,
                RippleColors,
                RippleTangents,
                /*bCreateCollision=*/false);
        }
        LastPaddleWakeRippleSourceCells = MoveTemp(RippleSourceCells);
    }
    if (SurfaceMesh->IsMeshSectionVisible(1) !=
        (PaddleWakeRenderTriangleCount > 0))
    {
        LogWaterRenderStateEvent(GetWorld(), TEXT("ripple_visibility_flip"));
    }
    SurfaceMesh->SetMeshSectionVisible(
        1, PaddleWakeRenderTriangleCount > 0);


    // Retain only a byte per vertex for presentation source eligibility;
    // don't retain/copy the large transient solver sample array for VFX.
    SprayWetCarrierMask.SetNumUninitialized(Vertices.Num());
    for (int32 Index = 0; Index < Vertices.Num(); ++Index)
    {
        SprayWetCarrierMask[Index] = LiveSolverWetVertexMask[Index] != 0 &&
            WetVertexMask[Index] != 0 &&
            FMath::IsFinite(WaterSamples[Index].DepthMeters) &&
            WaterSamples[Index].DepthMeters >= 0.10f ? 1 : 0;
    }
    Perf.Mark(TEXT("foam_overlay_finish"));
    // Current immutable profile, next interpolation's known sample positions.
    // The component's experimental opt-in owns copies and never waits here.
    if(bCartesianFlow && CartesianShorelineMesh)
        CartesianShorelineMesh->PrefetchCrestProfile(CartesianCrestInput);
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
                 "boulder_wake_abs_max_m=%.4f wake_foam_vertices=%d "
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
            MaximumAbsoluteBoulderWakeM,
            WakeFoamVertexCount,
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
    if (!bLoggedBoulderWakeDiagnostics &&
        MaximumAbsoluteBoulderWakeM > 0.01f)
    {
        bLoggedBoulderWakeDiagnostics = true;
        UE_LOG(
            LogTemp,
            Display,
            TEXT("RaftSim live boulder wakes activated: footprints_in_window=%d "
                 "abs_max_m=%.4f wake_foam_vertices=%d masked_foam_visible=%d"),
            WindowBoulderFootprintsSLR.Num(),
            MaximumAbsoluteBoulderWakeM,
            WakeFoamVertexCount,
            IsRapidFoamMeshVisible() ? 1 : 0);
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
    if (WaterAdapter && WaterAdapter->HasCartesianWaterCoordinates())
        return CartesianShorelineMesh && CartesianShorelineMesh->IsVisible() &&
            !CartesianShorelineMesh->GetWaterIndices().IsEmpty();
    return LiveVolumeCoreMesh &&
        LiveVolumeCoreMesh->IsVisible() &&
        LiveVolumeCoreTriangleCount > 0;
}

void ARaftSimWaterSurfaceActor::GetBreakingSites(TArray<FBreakingSite>& OutSites) const
{
    OutSites = BreakingSites;
}

bool ARaftSimWaterSurfaceActor::SampleCartesianCarrierSupport(
    const FVector& WorldPositionCm,float& OutHeightM,bool& OutWet) const
{
    FVector Position;
    const bool Available=SampleCartesianCarrierPosition(WorldPositionCm,Position,OutWet);
    OutHeightM=OutWet ? float(Position.Z*.01) : 0.f;
    return Available;
}

bool ARaftSimWaterSurfaceActor::SampleCartesianCarrierPosition(
    const FVector& WorldPositionCm,FVector& OutPositionCm,bool& OutWet) const
{
    OutPositionCm=FVector::ZeroVector; OutWet=false;
    if (!WaterAdapter || !WaterAdapter->HasCartesianWaterCoordinates() ||
        !bSingleLiveWaterSurfaceEnabled || !IsLiveVolumeCoreVisible() ||
        GridStationN<2 || GridLateralN<2 || RiverCoordinatesM.IsEmpty() ||
        ResolvedVertexSpacingMeters<=0.f || WorldPositionCm.ContainsNaN()) return false;
    FVector2D Coordinates; FVector Tangent,Left;
    if (!WaterAdapter->WorldToRiverCoordinates(WorldPositionCm,Coordinates,Tangent,Left)) return false;
    const FVector2D Grid=(Coordinates-RiverCoordinatesM[0])/ResolvedVertexSpacingMeters;
    if (Grid.X<0. || Grid.Y<0. || Grid.X>GridStationN-1 || Grid.Y>GridLateralN-1) return false;
    if (MovingDetail) MovingDetail->CommitCompletedFrame();
    const int32 X=FMath::Min(FMath::FloorToInt(Grid.X),GridStationN-2);
    const int32 Y=FMath::Min(FMath::FloorToInt(Grid.Y),GridLateralN-2);
    const int32 Cell=Y*(GridStationN-1)+X;
    const auto& Offsets=CartesianShorelineMesh->GetCellOffsets();
    if (!Offsets.IsValidIndex(Cell+1)) return false;
    FVector Position,Weights;FIntVector Corners;
    const auto& Drawn=CartesianShorelineMesh->GetWaterVertices();
    OutWet=RaftSimWaterShoreline::Sample(FVector2D(WorldPositionCm.X,WorldPositionCm.Y),
        Offsets[Cell],Offsets[Cell+1],Drawn,CartesianShorelineMesh->GetWaterIndices(),Position,&Corners,&Weights);
    const auto Detail=MovingDetail ? MovingDetail->GetPresentedFrame() : nullptr;
    if (OutWet && Detail)
    {
        // WPO is applied at rendered vertices, then rasterized linearly. A
        // bilinear detail query at the hull point is NOT that same triangle.
        const float Sign=WaterAdapter->GetRiverWorldYSign();
        Position.Z+=Weights.X*Detail->DisplacementCm(Drawn[Corners.X].Position,Sign)+
            Weights.Y*Detail->DisplacementCm(Drawn[Corners.Y].Position,Sign)+
            Weights.Z*Detail->DisplacementCm(Drawn[Corners.Z].Position,Sign);
    }
    if (OutWet)
    {
        const double PhysicalWaterZCm=Position.Z-GetResolvedLiveSurfaceRenderLiftCm();
        if (!CarrierGroundSources) CarrierGroundSources=MakeShared<FRaftSimGroundSourceRegistry>(GetWorld());
        double GroundZCm=0.; FVector GroundNormal;
        // A submitted water triangle can be hidden by finer captured rock.
        // Match solid contact geometry, including WPO above, without lifting
        // the water, changing conserved state, or suppressing positive films.
        if (CarrierGroundSources->SampleGround(WorldPositionCm,GroundZCm,GroundNormal) &&
            PhysicalWaterZCm<=GroundZCm) OutWet=false;
        else { OutPositionCm=Position; OutPositionCm.Z=PhysicalWaterZCm; }
    }
    return true;
}

bool ARaftSimWaterSurfaceActor::SampleVisibleCarrierAtRiverCoordinates(
    const FVector2D& CoordinatesM, FVector& OutPositionCm) const
{
    OutPositionCm = FVector::ZeroVector;
    const bool bGpuCarrier = bStatefulGPUCarrierReview && MacroSurfaceTexture &&
        SurfaceMesh && SurfaceMesh->IsVisible() && SurfaceMesh->IsMeshSectionVisible(0) &&
        !Triangles.IsEmpty();
    if ((!bGpuCarrier && (!bSingleLiveWaterSurfaceEnabled || !IsLiveVolumeCoreVisible())) ||
        GridStationN < 2 || GridLateralN < 2 || RiverCoordinatesM.IsEmpty() ||
        ResolvedVertexSpacingMeters <= 0.0f ||
        !FMath::IsFinite(CoordinatesM.X) || !FMath::IsFinite(CoordinatesM.Y))
    {
        return false;
    }
    const FVector2D Grid = (CoordinatesM - RiverCoordinatesM[0]) /
        ResolvedVertexSpacingMeters;
    if (Grid.X < 0.0 || Grid.Y < 0.0 ||
        Grid.X > GridStationN - 1 || Grid.Y > GridLateralN - 1)
    {
        return false;
    }
    const int32 X = FMath::Min(FMath::FloorToInt(Grid.X), GridStationN - 2);
    const int32 Y = FMath::Min(FMath::FloorToInt(Grid.Y), GridLateralN - 2);
    const float U = Grid.X - X;
    const float V = Grid.Y - Y;
    const int32 I0 = Y * GridStationN + X;
    if (!bGpuCarrier && WaterAdapter && WaterAdapter->HasCartesianWaterCoordinates())
    {
        const int32 Cell=Y*(GridStationN-1)+X;
        const auto& CartesianShoreCellOffsets=CartesianShorelineMesh->GetCellOffsets();
        if (!CartesianShoreCellOffsets.IsValidIndex(Cell+1)) return false;
        FVector QueryWorld;
        if (!WaterAdapter->RiverToWorldPosition(CoordinatesM,0.f,QueryWorld)) return false;
        bool bWet=false;
        if (!SampleCartesianCarrierPosition(QueryWorld,OutPositionCm,bWet) || !bWet) return false;
        OutPositionCm.Z+=GetResolvedLiveSurfaceRenderLiftCm();
        return true;
    }
    // Match the actual I0/I2/I1, I1/I2/I3 carrier diagonal, not a bilinear
    // height patch that can float above or under a non-planar triangle.
    const bool bFirstTriangle = U + V <= 1.0f;
    const int32 Indices[3] = { bFirstTriangle ? I0 : I0 + 1,
        I0 + GridStationN, bFirstTriangle ? I0 + 1 : I0 + GridStationN + 1 };
    const float Weights[3] = { bFirstTriangle ? 1.0f - U - V : 1.0f - V,
        bFirstTriangle ? V : 1.0f - U, bFirstTriangle ? U : U + V - 1.0f };
    const TArray<FVector>& SourceVertices = bGpuCarrier ? Vertices : RenderedLiveVolumeCoreVertices;
    if (SourceVertices.Num() != GridStationN * GridLateralN)
    {
        return false;
    }
    FVector Position = FVector::ZeroVector;
    float CoarseCrestCm = 0.0f, ShoreWeight = 0.0f;
    const bool bFineCrest = bGpuCarrier && bStatefulCrestReview &&
        MacroCrestDisplacementCm.Num() == SourceVertices.Num() &&
        MacroCrestShoreWeights.Num() == SourceVertices.Num();
    for (int32 Corner = 0; Corner < 3; ++Corner)
    {
        if (Weights[Corner] <= KINDA_SMALL_NUMBER) continue;
        const int32 Index = Indices[Corner];
        if (!SprayWetCarrierMask.IsValidIndex(Index) || SprayWetCarrierMask[Index] == 0)
        {
            return false;
        }
        const FVector Vertex = bGpuCarrier
            ? GetActorTransform().TransformPosition(SourceVertices[Index]) : SourceVertices[Index];
        if (Vertex.ContainsNaN() ||
            (VisualBankProbeState.IsValidIndex(Index) && VisualBankProbeState[Index] == 1 &&
                VisualBankTerrainZCm.IsValidIndex(Index) &&
                Vertex.Z <= VisualBankTerrainZCm[Index] + 2.0f))
        {
            return false;
        }
        Position += Vertex * Weights[Corner];
        if (bFineCrest)
        {
            CoarseCrestCm += MacroCrestDisplacementCm[Index] * Weights[Corner];
            ShoreWeight += MacroCrestShoreWeights[Index] * Weights[Corner];
        }
    }
    if (bFineCrest)
    {
        // Reconstruct the SAME immutable physical sites uploaded to the atlas.
        // This is a presentation anchor: GPU perturbation height is deliberately
        // not read back, so it is not a particle collision/support authority.
        TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite, TInlineAllocator<8>> Sites;
        for (int32 I = 0; I + 1 < MacroCrestSites.Num(); I += 2)
        {
            const FVector4f& Geometry = MacroCrestSites[I];
            const FVector4f& Properties = MacroCrestSites[I + 1];
            auto& Site = Sites.AddDefaulted_GetRef();
            Site.RiverCoordinatesMeters = FVector2D(Geometry.X, Geometry.Y);
            Site.PhysicalCrestHeightMeters = Geometry.Z;
            Site.PhysicalCrestLengthMeters = Geometry.W;
            Site.Intensity = Properties.X;
            Site.SpillingFraction = Properties.Y;
            Site.bLocalEnvelopeCap = Properties.Z != 0;
            Site.FlowDirection = RaftSimWaterFlowFrame::FromAngle(Properties.W);
        }
        Position.Z += 100.0f * ResolvedPresentationHydraulicReliefScale * ShoreWeight *
            URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(
                CoordinatesM, Sites, BreakingCrestLiftMeters, ResolvedVertexSpacingMeters) - CoarseCrestCm;
    }
    OutPositionCm = Position;
    return true;
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

void ARaftSimWaterSurfaceActor::SampleBoatWakeState()
{
    bBoatWakeValid = false;
    bBoatWakePaddling = false;
    BoatWakeRelativeSpeedMps = 0.0f;
    if (!WaterAdapter || !WaterAdapter->HasRiverCoordinateMap())
    {
        return;
    }
    TActorIterator<ARaftSimRaftActor> RaftIt(GetWorld());
    if (!RaftIt)
    {
        return;
    }
    ARaftSimRaftActor* Raft = *RaftIt;
    const ERaftSimCrewCommand CrewCommand = Raft->GetActiveCrewCommand();
    const bool bForceWake =
        CVarRaftSimForceBoatWakeTest.GetValueOnGameThread() != 0;
    bBoatWakePaddling = bForceWake ||
        CrewCommand == ERaftSimCrewCommand::AllForward ||
        CrewCommand == ERaftSimCrewCommand::AllBackward ||
        CrewCommand == ERaftSimCrewCommand::TurnLeft ||
        CrewCommand == ERaftSimCrewCommand::TurnRight ||
        CrewCommand == ERaftSimCrewCommand::Stop;

    const FVector RaftLocationCm = Raft->GetActorLocation();
    // The solver drives the raft kinematically, so GetVelocity() is zero;
    // difference positions instead, then low-pass the result.
    const double NowSeconds = GetWorld()->GetTimeSeconds();
    FVector RaftVelocityCmS = FVector::ZeroVector;
    double DeltaSampleSeconds = 0.0;
    if (LastBoatSampleTimeSeconds > 0.0)
    {
        DeltaSampleSeconds = NowSeconds - LastBoatSampleTimeSeconds;
        if (DeltaSampleSeconds > 0.001 && DeltaSampleSeconds < 1.0)
        {
            RaftVelocityCmS =
                (RaftLocationCm - LastBoatWorldPositionCm) /
                DeltaSampleSeconds;
        }
    }
    LastBoatWorldPositionCm = RaftLocationCm;
    LastBoatSampleTimeSeconds = NowSeconds;
    FVector2D RaftSL;
    FVector Tangent;
    FVector LeftNormal;
    if (!WaterAdapter->WorldToRiverCoordinates(
            RaftLocationCm, RaftSL, Tangent, LeftNormal))
    {
        return;
    }
    const FVector VelocityMps = RaftVelocityCmS * 0.01f;
    const FVector2D InstantVelocityMps(
        static_cast<float>(FVector::DotProduct(VelocityMps, Tangent)),
        static_cast<float>(FVector::DotProduct(VelocityMps, LeftNormal)));
    const float SmoothingAlpha = FMath::Clamp(
        static_cast<float>(DeltaSampleSeconds) * 3.0f, 0.0f, 1.0f);
    BoatRiverPositionM = RaftSL;
    BoatRiverVelocityMps +=
        (InstantVelocityMps - BoatRiverVelocityMps) * SmoothingAlpha;

    FVector2D FallbackTravelDirection(
        FVector::DotProduct(Raft->GetActorForwardVector(), Tangent),
        FVector::DotProduct(Raft->GetActorForwardVector(), LeftNormal));
    if (CrewCommand == ERaftSimCrewCommand::AllBackward ||
        CrewCommand == ERaftSimCrewCommand::Stop)
    {
        FallbackTravelDirection *= -1.0f;
    }
    FallbackTravelDirection = FallbackTravelDirection.GetSafeNormal();
    if (FallbackTravelDirection.IsNearlyZero())
    {
        FallbackTravelDirection = FVector2D(1.0, 0.0);
    }

    FVector2D RelativeVelocityMps = BoatRiverVelocityMps;
    if (!bForceWake)
    {
        FRaftSimWaterSample BoatWaterSample;
        if (WaterAdapter->SampleWaterAtWorldPosition(
                RaftLocationCm, BoatWaterSample) &&
            BoatWaterSample.bWet)
        {
            // The boat velocity above lives in river coordinates
            // (tangent/left-normal components); the world sampler returns a
            // WORLD-frame vector. Subtracting them raw skewed the relative
            // velocity by the river's world heading, bending the wake off
            // the true travel line everywhere the channel is not aligned
            // with world +X.
            RelativeVelocityMps -= FVector2D(
                static_cast<float>(FVector::DotProduct(
                    BoatWaterSample.VelocityMetersPerSecond, Tangent)),
                static_cast<float>(FVector::DotProduct(
                    BoatWaterSample.VelocityMetersPerSecond, LeftNormal)));
        }
    }
    BoatWakeRelativeSpeedMps = RelativeVelocityMps.Size();
    BoatWakeTravelDirection = BoatWakeRelativeSpeedMps > 0.08f
        ? RelativeVelocityMps / BoatWakeRelativeSpeedMps
        : FallbackTravelDirection;
    bBoatWakeValid = true;
}

bool ARaftSimWaterSurfaceActor::SavePresentedCarrierShapeAudit(const FString& Path) const
{
#if !UE_BUILD_SHIPPING
    if (!GetWorld() || !WaterAdapter || !WaterAdapter->HasCartesianWaterCoordinates() ||
        !CartesianShorelineMesh) return false;
    const auto Detail=MovingDetail ? MovingDetail->GetPresentedFrame() : nullptr;
    const float Sign=WaterAdapter->GetRiverWorldYSign();
    const FVector Focus=FoamOcclusionRaft ? FoamOcclusionRaft->GetActorLocation() : GetActorLocation();
    return RaftSimCarrierShapeAudit::Save(Path,
        CartesianShorelineMesh->GetWaterVertices(),CartesianShorelineMesh->GetWaterIndices(),
        CartesianShorelineMesh->GetActiveVertexCount(),CartesianShorelineMesh->GetCrestRefinement(),
        [&](const FVector& P)->double { return Detail ? Detail->DisplacementCm(P,Sign) : 0.; },
        GetWorld()->GetTimeSeconds(),Detail ? Detail->Sequence : 0,GetResolvedLiveSurfaceRenderLiftCm(),
        Focus,GridStationN,GridLateralN,RiverCoordinatesM,CartesianShoreWet,
        CartesianShoreDepthM,CartesianShoreBedM,Sign,LiveVolumeCoreVertices,MacroCrestDisplacementCm);
#else
    return false;
#endif
}

void ARaftSimWaterSurfaceActor::PublishLiveVolumeCore(const TArray<FVector>& Positions,
    const TArray<FVector>& VertexNormals, const TArray<FLinearColor>& Colors,
    const TArray<FVector2D>& Flow, const TArray<FVector2D>& Wake, bool bCreate,float CrestBlendAlpha)
{
    if (WaterAdapter && WaterAdapter->HasCartesianWaterCoordinates())
    {
        FWaterSurfacePerf Perf(TEXT("cartesian_publish"));
        CSV_SCOPED_TIMING_STAT(RaftSimSurface,CartesianPublish);
        const int32 N=Positions.Num();
        if (N!=GridStationN*GridLateralN || VertexNormals.Num()!=N || Colors.Num()!=N ||
            Flow.Num()!=N || Wake.Num()!=N || UVs.Num()!=N || Tangents.Num()!=N) return;
        TArray<FProcMeshVertex> FreshSource;
        // Same-input live pairs preserve every attribute and improve both
        // orders. Retain capacity only; Pack still writes every current field.
        static const bool bReuseSource=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimFreshSourcePacking"));
        auto& Source=bReuseSource ? CartesianSourcePackingScratch : FreshSource;
        {
            CSV_SCOPED_TIMING_STAT(RaftSimSurface,PackSource);
            // Exact packing is not necessarily faster in parallel. Keep it
            // opt-in for same-binary timing comparisons until measured better.
            static const bool bParallelSourcePacking = FParse::Param(
                FCommandLine::Get(), TEXT("RaftSimParallelSourcePacking"));
            static const bool bVectorColors=FParse::Param(FCommandLine::Get(),TEXT("RaftSimVectorSourceColors"));
            if (!RaftSimWaterSourcePacking::Pack(Positions,VertexNormals,Colors,UVs,
                Flow,Wake,Tangents,Source,bParallelSourcePacking,
                FoamTransportVelocityMetersPerSecond.Num()==N
                    ? TConstArrayView<FVector2D>(FoamTransportVelocityMetersPerSecond) : TConstArrayView<FVector2D>(Flow),bVectorColors)) return;
        }
        RaftSimSourcePackingAudit::Run(Positions,VertexNormals,Colors,UVs,Flow,Wake,Tangents,
            FoamTransportVelocityMetersPerSecond.Num()==N ? TConstArrayView<FVector2D>(FoamTransportVelocityMetersPerSecond) : TConstArrayView<FVector2D>(Flow),Source);
        Perf.Mark(TEXT("pack_source"));
        if (CartesianShorelineMesh->GetMaterial(0)!=LiveVolumeCoreMesh->GetMaterial(0))
            CartesianShorelineMesh->SetMaterial(0, LiveVolumeCoreMesh->GetMaterial(0));
        const bool bFineCrests=bSharedBreakingReliefEnabled && bSingleLiveWaterSurfaceEnabled &&
            MacroCrestDisplacementCm.Num()==N && MacroCrestShoreWeights.Num()==N && CartesianCrestInput.HeightAtWorldXYCm;
        CartesianCrestInput.SourceCrestCm=MacroCrestDisplacementCm;
        CartesianCrestInput.SourceShoreWeight=MacroCrestShoreWeights;
        CartesianCrestInput.BlendAlpha=bCreate ? 1.f : CrestBlendAlpha;
        CartesianCrestInput.DetailSpanCm=0;
        if (MovingDetail && MovingDetail->IsReady() && FoamOcclusionRaft)
        {
            // Quantized 16m coverage with 16m padding encloses every possible
            // 8m-hysteresis detail window until the next geometry submission.
            const FVector P=FoamOcclusionRaft->GetActorLocation();
            const FVector2D C(FMath::RoundToDouble(P.X/1600.)*1600.,FMath::RoundToDouble(P.Y/1600.)*1600.);
            CartesianCrestInput.DetailWindowCm=FBox2D(C-FVector2D(4800,4800),C+FVector2D(4800,4800));
            CartesianCrestInput.DetailSpanCm=50.f;
        }
        if (CartesianShorelineMesh->SetClippedWaterMesh(GridStationN,GridLateralN,MoveTemp(Source),
            CartesianShoreWet,CartesianShoreAvailable,CartesianShoreDepthM,CartesianShoreBedM,
            bFineCrests ? &CartesianCrestInput : nullptr))
        {
            CartesianShoreSourceVertexCount=N;
            LiveVolumeCoreTriangleCount=CartesianShorelineMesh->GetWaterIndices().Num()/3;
        }
        Perf.Mark(TEXT("clip_bounds_enqueue"));
        if(MovingDetail && GetWorld())RaftSimFoamFlowPairAudit::Run(CartesianShorelineMesh->GetWaterVertices(),
            MovingDetail->GetPresentedFrame(),WaterAdapter->GetRiverWorldYSign(),GetWorld()->GetTimeSeconds());
#if !UE_BUILD_SHIPPING
        FString ShapeAuditPath;
        if (bFineCrests && GetWorld() && GetWorld()->GetTimeSeconds()>=13.f &&
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimCarrierShapeAudit="),ShapeAuditPath) &&
            !FPaths::FileExists(ShapeAuditPath))
        {
            // Inspect the already presented payload; do not force a new commit.
            const bool Saved=SavePresentedCarrierShapeAudit(ShapeAuditPath);
            if (Saved) { UE_LOG(LogTemp,Display,TEXT("Submitted carrier shape saved: %s"),*ShapeAuditPath); }
            else { UE_LOG(LogTemp,Error,TEXT("Submitted carrier shape capture refused: %s"),*ShapeAuditPath); }
        }
        FString ContactAuditPath;
        if (GetWorld() && GetWorld()->GetTimeSeconds()>=10.f &&
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimCarrierContactAudit="),ContactAuditPath) &&
            !FPaths::FileExists(ContactAuditPath))
        {
            // Independent barycentric points on ACTUAL submitted triangles,
            // including shore clipping and temporal/fine-crest corrections.
            // Includes the paired detail payload; GPU upload/sampler parity is
            // audited separately. This does not measure render latency.
            const auto& Drawn=CartesianShorelineMesh->GetWaterVertices();
            const auto& Indices=CartesianShorelineMesh->GetWaterIndices();
            if (MovingDetail) MovingDetail->CommitCompletedFrame();
            const auto Detail=MovingDetail ? MovingDetail->GetPresentedFrame() : nullptr;
            double MaxError=0.,SumSquared=0.; int32 Count=0,Dry=0,Unavailable=0;
            int32 DetailAffectedPoints=0; double MaxContactDetailCm=0.;
            FRaftSimGroundSourceRegistry AuditGround(GetWorld());
            TArray<TSharedPtr<FJsonValue>> GroundProbes;
            int32 GroundOccluded=0,GroundOccludedWet=0;
            const int32 TriangleStride=FMath::Max(1,Indices.Num()/3/2000);
            for (int32 T=0;T<Indices.Num()/3;T+=TriangleStride)
            {
                const FVector P=Drawn[Indices[3*T]].Position*.2+
                    Drawn[Indices[3*T+1]].Position*.3+Drawn[Indices[3*T+2]].Position*.5;
                double DetailCm=0.;
                if (Detail)
                {
                    const float Sign=WaterAdapter->GetRiverWorldYSign();
                    DetailCm=.2*Detail->DisplacementCm(Drawn[Indices[3*T]].Position,Sign)+
                        .3*Detail->DisplacementCm(Drawn[Indices[3*T+1]].Position,Sign)+
                        .5*Detail->DisplacementCm(Drawn[Indices[3*T+2]].Position,Sign);
                }
                const double WaterZCm=P.Z+DetailCm-GetResolvedLiveSurfaceRenderLiftCm();
                double GroundZCm=0.; FVector GroundNormal;
                const bool GroundHit=AuditGround.SampleGround(P,GroundZCm,GroundNormal);
                FRaftSimWaterSample Support,Raw;
                const bool Available=WaterAdapter->SampleRaftSupportSurfaceAtWorldPosition(P,Support);
                const bool RawAvailable=WaterAdapter->SampleWaterAtWorldPosition(P,Raw);
                auto Probe=MakeShared<FJsonObject>();
                Probe->SetNumberField(TEXT("x_cm"),P.X); Probe->SetNumberField(TEXT("y_cm"),P.Y);
                Probe->SetNumberField(TEXT("water_z_cm"),WaterZCm);
                Probe->SetBoolField(TEXT("ground_hit"),GroundHit);
                if (GroundHit) Probe->SetNumberField(TEXT("ground_z_cm"),GroundZCm);
                Probe->SetBoolField(TEXT("support_available"),Available);
                Probe->SetBoolField(TEXT("support_wet"),Available && Support.bWet);
                Probe->SetBoolField(TEXT("raw_available"),RawAvailable);
                Probe->SetBoolField(TEXT("raw_wet"),RawAvailable && Raw.bWet);
                GroundProbes.Add(MakeShared<FJsonValueObject>(Probe));
                if (GroundHit && WaterZCm<=GroundZCm)
                {
                    ++GroundOccluded;
                    if (Available && Support.bWet) ++GroundOccludedWet;
                }
                if (!Available) { ++Unavailable; continue; }
                if (!Support.bWet) { ++Dry; continue; }
                if (FMath::Abs(DetailCm)>1.e-6) ++DetailAffectedPoints;
                MaxContactDetailCm=FMath::Max(MaxContactDetailCm,FMath::Abs(DetailCm));
                const double Error=Support.SurfaceHeightMeters*100.-
                    (P.Z+DetailCm-GetResolvedLiveSurfaceRenderLiftCm());
                MaxError=FMath::Max(MaxError,FMath::Abs(Error)); SumSquared+=Error*Error; ++Count;
            }
            auto Report=MakeShared<FJsonObject>();
            Report->SetStringField(TEXT("scope"),TEXT("Actual world-space raft support versus independent barycentric submitted wet triangles, including the paired resolved-detail payload when present. GPU payload/upload parity is audited separately. Excludes render latency, full traversal and visual acceptance."));
            Report->SetBoolField(TEXT("includes_paired_detail"),Detail.IsValid());
            Report->SetNumberField(TEXT("detail_affected_contact_points"),DetailAffectedPoints);
            Report->SetNumberField(TEXT("maximum_contact_detail_height_cm"),MaxContactDetailCm);
            Report->SetNumberField(TEXT("detail_frame_sequence"),Detail ? Detail->Sequence : 0);
            Report->SetBoolField(TEXT("detail_gpu_audit_requested"),MovingDetail && MovingDetail->AuditPresentedFrame());
            Report->SetNumberField(TEXT("world_seconds"),GetWorld()->GetTimeSeconds());
            Report->SetNumberField(TEXT("tested_wet_points"),Count);
            Report->SetNumberField(TEXT("ground_occluded_points"),GroundOccluded);
            Report->SetNumberField(TEXT("ground_occluded_wet_points"),GroundOccludedWet);
            Report->SetArrayField(TEXT("ground_contact_probes"),GroundProbes);
            Report->SetStringField(TEXT("dry_point_scope"),TEXT("raw_dry_points includes ground-occluded support; inspect per-probe raw_wet separately. Independent registered-source triangle verification is required for ground classification."));
            Report->SetNumberField(TEXT("raw_dry_points"),Dry);
            Report->SetNumberField(TEXT("unavailable_points"),Unavailable);
            Report->SetNumberField(TEXT("maximum_support_carrier_error_cm"),MaxError);
            Report->SetNumberField(TEXT("rms_support_carrier_error_cm"),Count ? FMath::Sqrt(SumSquared/Count) : 0.);
            Report->SetNumberField(TEXT("render_lift_cm"),GetResolvedLiveSurfaceRenderLiftCm());
            FString Json; auto Writer=TJsonWriterFactory<>::Create(&Json); FJsonSerializer::Serialize(Report,Writer);
            FFileHelper::SaveStringToFile(Json,*ContactAuditPath);
        }
#endif
        FString TransportAuditPath;
        if (GetWorld() && GetWorld()->GetTimeSeconds()>=10.f && FoamTransportVelocityMetersPerSecond.Num()==N &&
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimFoamTransportAudit="),TransportAuditPath) &&
            !FPaths::FileExists(TransportAuditPath))
        {
            const auto& Drawn=CartesianShorelineMesh->GetWaterVertices();
            double MaxTransportError=0.,MaxBulkError=0.,MaxReturn=0.;
            int32 WetCount=0,ReturnCount=0;
            if (Drawn.Num()>=N) for (int32 I=0;I<N;++I)
            {
                MaxTransportError=FMath::Max(MaxTransportError,(Drawn[I].UV3-FoamTransportVelocityMetersPerSecond[I]).Size());
                MaxBulkError=FMath::Max(MaxBulkError,(Drawn[I].UV1-Flow[I]).Size());
                if (CartesianShoreWet[I])
                {
                    ++WetCount;
                    // Compare against the published (smoothed) bulk channel.
                    // This difference includes smoothing as well as return
                    // flow; it is not a measurement of roller velocity alone.
                    const double Return=(FoamTransportVelocityMetersPerSecond[I]-Flow[I]).Size();
                    ReturnCount+=Return>1.e-6; MaxReturn=FMath::Max(MaxReturn,Return);
                }
            }
            auto Report=MakeShared<FJsonObject>();
            Report->SetStringField(TEXT("scope"),TEXT("Actual submitted Cartesian source UV3 versus exact CPU foam backtrace velocity; UV1 bulk flow unchanged. Roller/eddy contributions are presentation-only, not measured fluid momentum or visual acceptance."));
            Report->SetNumberField(TEXT("source_vertices"),N);
            Report->SetBoolField(TEXT("complete_source_prefix"),Drawn.Num()>=N);
            Report->SetNumberField(TEXT("wet_vertices"),WetCount);
            Report->SetNumberField(TEXT("transport_differs_from_published_bulk_vertices"),ReturnCount);
            Report->SetNumberField(TEXT("maximum_difference_from_published_bulk_mps"),MaxReturn);
            Report->SetNumberField(TEXT("maximum_source_transport_error_mps"),MaxTransportError);
            Report->SetNumberField(TEXT("maximum_bulk_channel_error_mps"),MaxBulkError);
            FString Json; FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
            FFileHelper::SaveStringToFile(Json,*TransportAuditPath);
        }
        FString CrestAuditPath;
        if (bFineCrests && GetWorld() && GetWorld()->GetTimeSeconds()>=10.f &&
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestSamplingAudit="),CrestAuditPath) &&
            !FPaths::FileExists(CrestAuditPath+TEXT(".cartesian-mesh.json")))
        {
            const auto& MeshVertices=CartesianShorelineMesh->GetWaterVertices();
            const auto& MeshIndices=CartesianShorelineMesh->GetWaterIndices();
            const auto& Offsets=CartesianShorelineMesh->GetCellOffsets();
            const auto& Fine=CartesianShorelineMesh->GetCrestRefinement();
            const auto& Coarse=Fine.GetExpandedCoarseCrestCm();
            const auto& Shore=Fine.GetExpandedShore();
            const auto& Target=Fine.GetTargetCorrectionsCm();
            const auto& Rendered=Fine.GetRenderedCorrectionsCm();
            double MaxTargetErrorCm=0.,MaxCorrectionTrackingCm=0.,MaxSourceChangeCm=0.;
            int32 SampleCount=0;
            for (int32 I=0; I<N; ++I)
                MaxSourceChangeCm=FMath::Max(MaxSourceChangeCm,FVector::Distance(Positions[I],MeshVertices[I].Position));
            for (int32 Y=0; Y<GridLateralN-1; ++Y) for (int32 X=0; X<GridStationN-1; ++X)
            {
                const int32 A=Y*GridStationN+X,Cell=Y*(GridStationN-1)+X;
                if (!CartesianShoreWet[A] || !CartesianShoreWet[A+1] ||
                    !CartesianShoreWet[A+GridStationN] || !CartesianShoreWet[A+GridStationN+1]) continue;
                for (int32 T=Offsets[Cell]; T<Offsets[Cell+1]; T+=3)
                {
                    const int32 IA=MeshIndices[T],IB=MeshIndices[T+1],IC=MeshIndices[T+2];
                    for (int32 U=0; U<=7; ++U) for (int32 V=0; V<=7-U; ++V)
                    {
                        const double WB=U/7.,WC=V/7.,WA=1.-WB-WC;
                        const FVector P=MeshVertices[IA].Position*WA+MeshVertices[IB].Position*WB+MeshVertices[IC].Position*WC;
                        const double Weight=Shore[IA]*WA+Shore[IB]*WB+Shore[IC]*WC;
                        const double Expected=CartesianCrestInput.HeightAtWorldXYCm(FVector2D(P.X,P.Y))*Weight;
                        const double Actual=(Coarse[IA]+Target[IA])*WA+(Coarse[IB]+Target[IB])*WB+(Coarse[IC]+Target[IC])*WC;
                        const double Tracking=(Rendered[IA]-Target[IA])*WA+(Rendered[IB]-Target[IB])*WB+(Rendered[IC]-Target[IC])*WC;
                        MaxTargetErrorCm=FMath::Max(MaxTargetErrorCm,FMath::Abs(Expected-Actual));
                        MaxCorrectionTrackingCm=FMath::Max(MaxCorrectionTrackingCm,FMath::Abs(Tracking));
                        ++SampleCount;
                    }
                }
            }
            auto Report=MakeShared<FJsonObject>();
            Report->SetStringField(TEXT("map"),GetWorld()->GetMapName());
            Report->SetStringField(TEXT("scope"),TEXT("Current shared crest target on actual submitted Cartesian topology; sevenths sampled in fully wet source cells. Excludes macro temporal lag, other base relief and GPU perturbations. Fine correction temporal tracking reported separately; not full shaded motion acceptance."));
            Report->SetNumberField(TEXT("world_seconds"),GetWorld()->GetTimeSeconds());
            Report->SetNumberField(TEXT("source_vertices"),N);
            Report->SetNumberField(TEXT("active_vertices_including_shore_reserve"),CartesianShorelineMesh->GetActiveVertexCount());
            Report->SetNumberField(TEXT("render_buffer_vertices"),MeshVertices.Num());
            Report->SetNumberField(TEXT("submitted_triangles"),MeshIndices.Num()/3);
            Report->SetNumberField(TEXT("samples"),SampleCount);
            Report->SetNumberField(TEXT("maximum_target_crest_error_cm"),MaxTargetErrorCm);
            Report->SetNumberField(TEXT("maximum_fine_correction_tracking_cm"),MaxCorrectionTrackingCm);
            Report->SetNumberField(TEXT("maximum_source_vertex_change_cm"),MaxSourceChangeCm);
            Report->SetNumberField(TEXT("refinement_build_count"),Fine.GetBuildCount());
            FString Json; FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
            const bool Saved=FFileHelper::SaveStringToFile(Json,*(CrestAuditPath+TEXT(".cartesian-mesh.json")));
            UE_LOG(LogTemp,Display,TEXT("Cartesian fine crest audit: samples=%d target_error_cm=%.9g tracking_cm=%.9g source_change_cm=%.9g saved=%d"),
                SampleCount,MaxTargetErrorCm,MaxCorrectionTrackingCm,MaxSourceChangeCm,Saved);
        }
        return;
    }
    const TArray<FVector2D> Empty;
    if (bCreate) LiveVolumeCoreMesh->CreateMeshSection_LinearColor(0, Positions,
        LiveVolumeCoreTriangles, VertexNormals, UVs, Flow, Wake, Empty, Colors, Tangents, false, false);
    else LiveVolumeCoreMesh->UpdateMeshSection_LinearColor(0, Positions, VertexNormals,
        UVs, Flow, Wake, Empty, Colors, Tangents, false);
}

void ARaftSimWaterSurfaceActor::UpdateLiveVolumeCoreInterpolation(
    float DeltaSeconds)
{
    // The section pointer stays valid after ClearMeshSection (the entry is
    // merely emptied), so an in-place update must also match the section's
    // CURRENT vertex count or the engine rejects it with a per-frame error.
    const FProcMeshSection* CoreSection = LiveVolumeCoreMesh
        ? LiveVolumeCoreMesh->GetProcMeshSection(0)
        : nullptr;
    const bool bCartesianFlow = WaterAdapter && WaterAdapter->HasCartesianWaterCoordinates();
    const bool bMeshShapeValid = bCartesianFlow ? CartesianShoreSourceVertexCount == LiveVolumeCoreVertices.Num()
        : CoreSection && CoreSection->ProcVertexBuffer.Num() == LiveVolumeCoreVertices.Num();
    if (!bLiveVolumeCoreInterpolationActive ||
        !LiveVolumeCoreMesh ||
        !bMeshShapeValid ||
        LiveVolumeCoreVertices.Num() == 0 ||
        LiveVolumeCoreInterpolationStartVertices.Num() !=
            LiveVolumeCoreVertices.Num() ||
        LiveVolumeCoreInterpolationStartNormals.Num() !=
            LiveVolumeCoreNormals.Num() ||
        LiveVolumeCoreInterpolationStartVertexColors.Num() !=
            LiveVolumeCoreVertexColors.Num() ||
        LiveVolumeCoreInterpolationStartFlowVelocity.Num() !=
            FlowVelocityMetersPerSecond.Num() ||
        LiveVolumeCoreInterpolationStartWakeData.Num() !=
            BoatWakePresentationData.Num())
    {
        return;
    }

    // Continuous exponential chase, not a restarted linear blend. The
    // restart-lerp reversed every vertex's velocity at each 15 Hz retarget;
    // from a world-static camera that zigzag is sub-millimetre, but the
    // guide camera rides the TRUE surface via rigid support, so the
    // rendered surface oscillated relative to the view and its grazing
    // reflections snapped in rhythmic bursts (measured 2026-08-27:
    // 3-4 % of water pixels popping in intermittent frame pairs from the
    // guide seat, zero from a static camera). Exponential approach is
    // monotonic toward each target, so velocity only turns when the water
    // actually does.
    LiveVolumeCoreInterpolationElapsedSeconds +=
        FMath::Max(DeltaSeconds, 0.0f);
    const float Alpha = 1.0f - FMath::Exp(
        -16.0f * FMath::Max(DeltaSeconds, 0.0f));

    RenderedLiveVolumeCoreVertices.SetNumUninitialized(
        LiveVolumeCoreVertices.Num());
    RenderedLiveVolumeCoreNormals.SetNumUninitialized(
        LiveVolumeCoreNormals.Num());
    RenderedLiveVolumeCoreVertexColors.SetNumUninitialized(
        LiveVolumeCoreVertexColors.Num());
    RenderedLiveVolumeCoreFlowVelocity.SetNumUninitialized(
        FlowVelocityMetersPerSecond.Num());
    RenderedLiveVolumeCoreWakeData.SetNumUninitialized(
        BoatWakePresentationData.Num());
    // Two actual-game captures preserve every field bit and reduce this pass
    // in both call orders. Keep an exact serial control; legacy surfaces retain
    // their original scheduling until separately reviewed.
    static const bool AllowParallelInterpolation=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimSerialWaterInterpolation"));
    const bool ParallelInterpolation=bCartesianFlow && AllowParallelInterpolation;
    static const bool InterpolationAudit=FParse::Param(FCommandLine::Get(),TEXT("RaftSimWaterInterpolationAudit"));
    if(InterpolationAudit && GFrameCounter>=120 && GFrameCounter<184)
    {
        auto P=RenderedLiveVolumeCoreVertices;auto N=RenderedLiveVolumeCoreNormals;
        auto C=RenderedLiveVolumeCoreVertexColors;auto F=RenderedLiveVolumeCoreFlowVelocity;
        auto W=RenderedLiveVolumeCoreWakeData;
        double SerialMs=0.,ParallelMs=0.;bool Valid=true;
        const auto Serial=[&]() {const double Start=FPlatformTime::Seconds();
            Valid &= RaftSimWaterInterpolation::Advance(LiveVolumeCoreVertices,LiveVolumeCoreNormals,
                LiveVolumeCoreVertexColors,FlowVelocityMetersPerSecond,BoatWakePresentationData,Alpha,
                RenderedLiveVolumeCoreVertices,RenderedLiveVolumeCoreNormals,RenderedLiveVolumeCoreVertexColors,
                RenderedLiveVolumeCoreFlowVelocity,RenderedLiveVolumeCoreWakeData,false);
            SerialMs=(FPlatformTime::Seconds()-Start)*1000.;};
        const auto Parallel=[&]() {const double Start=FPlatformTime::Seconds();
            Valid &= RaftSimWaterInterpolation::Advance(LiveVolumeCoreVertices,LiveVolumeCoreNormals,
                LiveVolumeCoreVertexColors,FlowVelocityMetersPerSecond,BoatWakePresentationData,Alpha,P,N,C,F,W,true);
            ParallelMs=(FPlatformTime::Seconds()-Start)*1000.;};
        if(GFrameCounter%2){Parallel();Serial();}else{Serial();Parallel();}
        const auto Exact=[](const auto& A,const auto& B)
        {return A.Num()==B.Num() && (!A.Num() || !FMemory::Memcmp(A.GetData(),B.GetData(),A.Num()*sizeof(A[0])));};
        Valid &= Exact(P,RenderedLiveVolumeCoreVertices) && Exact(N,RenderedLiveVolumeCoreNormals) &&
            Exact(C,RenderedLiveVolumeCoreVertexColors) && Exact(F,RenderedLiveVolumeCoreFlowVelocity) && Exact(W,RenderedLiveVolumeCoreWakeData);
        UE_LOG(LogTemp,Display,TEXT("WaterInterpolationPair frame=%llu exact=%d parallel_first=%d vertices=%d serial_ms=%.9f parallel_ms=%.9f"),
            GFrameCounter,int32(Valid),int32(GFrameCounter%2),P.Num(),SerialMs,ParallelMs);
        if(!Valid){UE_LOG(LogTemp,Error,TEXT("Water interpolation comparison failed"));return;}
        if(ParallelInterpolation)
        {
            RenderedLiveVolumeCoreVertices=MoveTemp(P);RenderedLiveVolumeCoreNormals=MoveTemp(N);
            RenderedLiveVolumeCoreVertexColors=MoveTemp(C);RenderedLiveVolumeCoreFlowVelocity=MoveTemp(F);
            RenderedLiveVolumeCoreWakeData=MoveTemp(W);
        }
    }
    else if(!RaftSimWaterInterpolation::Advance(LiveVolumeCoreVertices,LiveVolumeCoreNormals,
        LiveVolumeCoreVertexColors,FlowVelocityMetersPerSecond,BoatWakePresentationData,Alpha,
        RenderedLiveVolumeCoreVertices,RenderedLiveVolumeCoreNormals,RenderedLiveVolumeCoreVertexColors,
        RenderedLiveVolumeCoreFlowVelocity,RenderedLiveVolumeCoreWakeData,ParallelInterpolation)) return;

    const TArray<FVector2D> EmptyUVs;
    // R/G/B store foam/depth/speed, not display colour. Creation defaults to
    // linear quantization, but UpdateMeshSection defaults to sRGB conversion!
    // Preserve the numeric channels on every refresh/recentre/interpolation:
    // otherwise e.g. 0.05 foam becomes ~0.25 after the first update, driving
    // both exaggerated whitening and different local-fluid displacement.
    PublishLiveVolumeCore(RenderedLiveVolumeCoreVertices, RenderedLiveVolumeCoreNormals,
        RenderedLiveVolumeCoreVertexColors, RenderedLiveVolumeCoreFlowVelocity,
        RenderedLiveVolumeCoreWakeData, false,Alpha);
    // The chase never "completes": it keeps easing toward the latest
    // refresh targets every frame until a hard swap or grid teardown
    // deactivates it.
}

void ARaftSimWaterSurfaceActor::Tick(float DeltaSeconds)
{
    CSV_SCOPED_TIMING_STAT(RaftSimSurface,Tick);
    Super::Tick(DeltaSeconds);
    if (!TryInitializeRuntimeSurface()) return;
    if (MovingDetail) MovingDetail->CommitCompletedFrame();
    FWaterSurfacePerf Perf(TEXT("tick"));
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
    FVector2D TargetFoamTextureVelocityMps = FVector2D::ZeroVector;
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
        if (bSingleLiveWaterSurfaceEnabled &&
            WaterAdapter->HasCartesianWaterCoordinates())
        {
            auto* Material=Cast<UMaterialInstanceDynamic>(LiveVolumeCoreMesh->GetMaterial(0));
            if (MovingDetailMaterial && MovingDetailMaterial!=Material)
            {
                if (MovingDetail)MovingDetail->DestroyComponent();
                MovingDetail=nullptr;MovingDetailMaterial=nullptr;bMovingDetailAttempted=false;
            }
            float IntegratedMarker=0;
            if (!bMovingDetailAttempted && Material && Material->GetScalarParameterValue(
                FHashedMaterialParameterInfo(TEXT("StatefulDetailWorldYSign")),IntegratedMarker))
            {
                bMovingDetailAttempted=true;MovingDetailMaterial=Material;
                MovingDetail=NewObject<URaftSimStatefulDetailComponent>(this);
                MovingDetail->RegisterComponent();
                if (MovingDetail->Initialize(WaterAdapter,Material,FoamOcclusionRaft->GetActorLocation(),
                    FVector::ForwardVector,true,true))
                {
                    // Retire both sides of the old procedural local-fluid
                    // coupling. Macro height/shared crest support remains.
                    // GPU perturbation support/contact still needs validation.
                    ResolvedRaftLocalFluidHeightfieldStrength=0;
                    Material->SetScalarParameterValue(TEXT("RaftSimLocalFluidWPOStrength"),0);
                }
                else UE_LOG(LogTemp,Error,TEXT("Playable South Fork moving detail initialization failed; not accepted as integrated water"));
            }
            if (MovingDetail)MovingDetail->SetFocusActor(FoamOcclusionRaft);
        }
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
            FVector2D RiverPositionMeters;
            FVector RiverTangent;
            FVector RiverLeft;
            if (WaterAdapter->WorldToRiverCoordinates(
                    FoamOcclusionRaft->GetActorLocation(),
                    RiverPositionMeters,
                    RiverTangent,
                    RiverLeft))
            {
                const FVector2D WorldVelocityMps(
                    ClockSample.VelocityMetersPerSecond.X,
                    ClockSample.VelocityMetersPerSecond.Y);
                TargetFoamTextureVelocityMps = FVector2D(
                    FVector2D::DotProduct(
                        WorldVelocityMps,
                        FVector2D(RiverTangent.X, RiverTangent.Y)),
                    FVector2D::DotProduct(
                        WorldVelocityMps,
                        FVector2D(RiverLeft.X, RiverLeft.Y)));
            }
            else
            {
                TargetFoamTextureVelocityMps = FVector2D(
                    ClockSample.VelocityMetersPerSecond.X,
                    ClockSample.VelocityMetersPerSecond.Y);
            }
        }
    }
    SmoothedFlowClockScale += (TargetFlowClockScale - SmoothedFlowClockScale) *
        FMath::Clamp(2.0f * DeltaSeconds, 0.0f, 1.0f);
    if (bSingleLiveWaterSurfaceEnabled &&
        !bHasTravelingWaveWPOStrengthParameter)
    {
        // Keep the legacy parent at the analytically cancelled phase. Solver
        // foam advection and CPU hydraulic/wake motion continue independently.
        PresentationWaveClockSeconds = 0.0f;
    }
    else
    {
        PresentationWaveClockSeconds +=
            SmoothedFlowClockScale * FMath::Max(DeltaSeconds, 0.0f);
    }
    const float FoamVelocityBlend = 1.0f - FMath::Exp(
        -3.0f * FMath::Max(DeltaSeconds, 0.0f));
    SmoothedFoamTextureVelocityMps = FMath::Lerp(
        SmoothedFoamTextureVelocityMps,
        TargetFoamTextureVelocityMps,
        FMath::Clamp(FoamVelocityBlend, 0.0f, 1.0f));
    FoamTextureAdvectionMeters = AdvanceFoamTextureAdvectionMeters(
        FoamTextureAdvectionMeters,
        SmoothedFoamTextureVelocityMps,
        DeltaSeconds);
    if (WaterAdapter)
    {
        WaterAdapter->SetPresentationWaveClockSeconds(
            PresentationWaveClockSeconds);
        WaterAdapter->ConfigureRaftSupportLocalFluid(
            bSingleLiveWaterSurfaceEnabled &&
                ResolvedRaftLocalFluidHeightfieldStrength > 0.0f,
            ResolvedRaftLocalFluidHeightfieldStrength,
            FoamTextureAdvectionMeters);
    }
    SampleBoatWakeState();
    const float WakeEnvelopeTarget =
        bBoatWakeValid && bBoatWakePaddling ? 1.0f : 0.0f;
    // Catch quickly with the planted blades, then let the displaced water
    // settle over roughly a stroke interval after paddling stops.
    BoatWakePaddleEnvelope = FMath::FInterpTo(
        BoatWakePaddleEnvelope,
        WakeEnvelopeTarget,
        FMath::Max(DeltaSeconds, 0.0f),
        WakeEnvelopeTarget > BoatWakePaddleEnvelope ? 5.0f : 1.1f);
    if (SurfaceMesh)
    {
        const bool bHideOverlay =
            CVarRaftSimHideLiveOverlay.GetValueOnGameThread() != 0;
        if (bHideOverlay == SurfaceMesh->IsVisible())
        {
            SurfaceMesh->SetVisibility(!bHideOverlay, false);
        }
    }
    if (WaterAdapter)
    {
        // Live-minus-cooked level near the raft: the static flow-band tiles
        // are cooked at one discharge, and on a low-release morning their
        // glossy sheet kept rendering metres up the bank past the solver's
        // waterline. Sample both fields along the channel at the boat and
        // publish the smoothed delta for the tile material's shore clip.
        float LevelDeltaSumM = 0.0f;
        int32 LevelDeltaCount = 0;
        for (const float StationOffsetM : {-20.0f, 0.0f, 20.0f})
        {
            const FVector2D ProbeM(
                BoatRiverPositionM.X + StationOffsetM, BoatRiverPositionM.Y);
            FRaftSimWaterSample LiveSample;
            FRaftSimWaterSample BaselineSample;
            if (WaterAdapter->SampleWaterAtRiverCoordinates(
                    ProbeM, LiveSample) &&
                LiveSample.bWet &&
                WaterAdapter->SamplePresentationBaselineFieldAtRiverCoordinates(
                    ProbeM, BaselineSample) &&
                BaselineSample.bWet)
            {
                LevelDeltaSumM += LiveSample.SurfaceHeightMeters -
                    BaselineSample.SurfaceHeightMeters;
                ++LevelDeltaCount;
            }
        }
        if (LevelDeltaCount > 0)
        {
            LiveVsBaselineLevelDeltaM = FMath::FInterpTo(
                LiveVsBaselineLevelDeltaM,
                LevelDeltaSumM / LevelDeltaCount,
                FMath::Max(DeltaSeconds, 0.0f),
                0.8f);
        }
    }
    if (RaftFoamOcclusionCollection && GetWorld())
    {
        if (UMaterialParameterCollectionInstance* ClockParameters =
                GetWorld()->GetParameterCollectionInstance(
                    RaftFoamOcclusionCollection))
        {
            ClockParameters->SetScalarParameterValue(
                TEXT("RaftSimWaveClockSeconds"), PresentationWaveClockSeconds);
            ClockParameters->SetScalarParameterValue(
                TEXT("RaftSimLiveWaterLevelDeltaM"), LiveVsBaselineLevelDeltaM);
            ClockParameters->SetVectorParameterValue(
                TEXT("RaftSimFoamAdvectionMeters"),
                FLinearColor(
                    FoamTextureAdvectionMeters.X,
                    FoamTextureAdvectionMeters.Y,
                    0.0f,
                    0.0f));
            // Keep the legacy gate hard-disabled even when a saved material
            // package still contains the retired wake expressions. Rebuilding
            // the C++ material authoring graph does not rewrite an existing
            // derived South Fork parent, so forwarding bBoatWakeValid here
            // could reactivate the old white V-shaped trail until that asset
            // happened to be regenerated. Position/velocity continue to be
            // published only for compatibility; the new wake uses CPU mesh
            // displacement and never enables this material path.
            ClockParameters->SetScalarParameterValue(
                TEXT("RaftSimWakeBoatEnable"),
                0.0f);
            ClockParameters->SetScalarParameterValue(
                TEXT("RaftSimWakeBoatStationM"),
                static_cast<float>(BoatRiverPositionM.X));
            ClockParameters->SetScalarParameterValue(
                TEXT("RaftSimWakeBoatLateralM"),
                static_cast<float>(BoatRiverPositionM.Y));
            ClockParameters->SetScalarParameterValue(
                TEXT("RaftSimWakeBoatVelStationMps"),
                static_cast<float>(BoatRiverVelocityMps.X));
            ClockParameters->SetScalarParameterValue(
                TEXT("RaftSimWakeBoatVelLateralMps"),
                static_cast<float>(BoatRiverVelocityMps.Y));
        }
    }

    // The raft-aligned foam/interior masks are material parameters, so they
    // must follow the boat every rendered frame rather than hopping at the
    // lower-frequency hydraulic mesh refresh cadence.
    UpdateRaftFoamExclusionParameters();

    // Solver sampling and topology stay at the bounded hydraulic cadence, but
    // the one visible carrier must not expose that cadence through its normal
    // field. Reflections are especially sensitive to even small normal steps.
    Perf.Mark(TEXT("clock_masks"));
    UpdateLiveVolumeCoreInterpolation(DeltaSeconds);
    Perf.Mark(TEXT("interpolation"));

    TimeSinceRefresh += DeltaSeconds;
    if (TimeSinceRefresh >= RefreshIntervalSeconds)
    {
        TimeSinceRefresh = 0.0f;
        RefreshSurface();
    }
    Perf.Mark(TEXT("refresh"));
}
