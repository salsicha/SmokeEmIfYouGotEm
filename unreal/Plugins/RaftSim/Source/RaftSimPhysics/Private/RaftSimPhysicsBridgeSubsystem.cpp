#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimGroundSourceRegistry.h"

#include "EngineUtils.h"
#include "LandscapeProxy.h"
#include "Components/StaticMeshComponent.h"
#include "CollisionQueryParams.h"

void URaftSimPhysicsBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    WaterRuntime = NewObject<URaftSimWaterRuntimeAdapter>(this);
    RaftRuntime = NewObject<URaftSimChronoRuntimeAdapter>(this);
}

void URaftSimPhysicsBridgeSubsystem::Deinitialize()
{
    // Release the contact registry's world delegates before subsystem teardown.
    if (RaftRuntime) RaftRuntime->SetGroundSurfaceSampler({});
    WaterRuntime = nullptr;
    RaftRuntime = nullptr;
    Super::Deinitialize();
}

void URaftSimPhysicsBridgeSubsystem::ConfigureBridge(
    const FRaftSimWaterRuntimeConfig& WaterConfig,
    const FRaftSimRaftBodyConfig& RaftConfig,
    const FRaftSimWaterRaftCouplingPolicy& InCouplingPolicy,
    float InWaterStepSeconds,
    float InChronoSubstepSeconds
)
{
    WaterStepSeconds = FMath::Max(InWaterStepSeconds, KINDA_SMALL_NUMBER);
    ChronoSubstepSeconds = FMath::Clamp(InChronoSubstepSeconds, KINDA_SMALL_NUMBER, WaterStepSeconds);
    CouplingPolicy = InCouplingPolicy;
    AuthorityIntegrationPolicy.SelectedRuntime = RaftConfig.Runtime;
    AuthorityIntegrationPolicy.WaterAuthority = TEXT("custom_cxx_shallow_water_solver");
    AuthorityIntegrationPolicy.bChaosMayDriveScoringCriticalPhysics = false;
    AuthorityIntegrationPolicy.bRenderTickMayAdvanceAuthority = false;
    AccumulatedSeconds = 0.0f;
    PhysicsFrame = 0;
    LastOutput = FRaftSimPhysicsTickOutput();

    if (WaterRuntime)
    {
        FRaftSimWaterRuntimeConfig RuntimeWaterConfig = WaterConfig;
        RuntimeWaterConfig.FixedStepSeconds = WaterStepSeconds;
        WaterRuntime->Configure(RuntimeWaterConfig);
    }

    if (RaftRuntime)
    {
        RaftRuntime->ConfigureRaftBody(RaftConfig);
        RaftRuntime->ConfigureAuthorityIntegrationPolicy(AuthorityIntegrationPolicy);

        // Bind the raft adapter's buoyancy probe to the live water runtime.
        // Without a live solver window the probe reports a flat surface at
        // world Z=0, matching the P1 dev-tank waterline.
        TWeakObjectPtr<URaftSimWaterRuntimeAdapter> WeakWater = WaterRuntime;
        RaftRuntime->SetWaterSurfaceSampler(
            [WeakWater](const FVector& WorldPositionCm, float& OutWaterSurfaceZCm) -> bool
            {
                if (URaftSimWaterRuntimeAdapter* Water = WeakWater.Get())
                {
                    if (Water->HasLiveWindow())
                    {
                        FRaftSimWaterSample Sample;
                        if (Water->SampleRaftSupportSurfaceAtWorldPosition(WorldPositionCm, Sample)
                            && Sample.bWet)
                        {
                            OutWaterSurfaceZCm = Sample.SurfaceHeightMeters * 100.0f;
                            return true;
                        }
                        return false;
                    }
                }
                OutWaterSurfaceZCm = 0.0f;
                return true;
            });

        // The custom raft state is kinematic to Unreal, so QueryOnly hull
        // collision cannot resolve Landscape contact. Supply authoritative
        // height-field data to the selected reduced runtime instead. Physical
        // source Landscapes take precedence; maps without one use solver bed.
        const auto GroundSources=MakeShared<FRaftSimGroundSourceRegistry>(GetWorld());
        RaftRuntime->SetGroundSurfaceSampler(
            [WeakWater, GroundSources](
                const FVector& WorldPositionCm,
                float& OutGroundZCm,
                FVector& OutGroundNormal) -> bool
            {
                GroundSources->RefreshIfDirty();
                // The survey mesh and hydraulic bed share a source, but a
                // coarser hydraulic raster cannot resolve every exposed rock.
                // Query the full collision triangles at the requested XY;
                // use component bounds, not raft height, even after a fall.
                TOptional<float> CapturedGroundZCm;
                FVector CapturedNormal = FVector::UpVector;
                FCollisionQueryParams Params(SCENE_QUERY_STAT(RaftSimCapturedGround), true);
                for (const TWeakObjectPtr<UStaticMeshComponent>& WeakMesh : GroundSources->Meshes)
                {
                    UStaticMeshComponent* Mesh = WeakMesh.Get();
                    if (!Mesh || !Mesh->IsQueryCollisionEnabled()) continue;
                    const FBox Bounds = Mesh->Bounds.GetBox();
                    if (WorldPositionCm.X < Bounds.Min.X || WorldPositionCm.X > Bounds.Max.X ||
                        WorldPositionCm.Y < Bounds.Min.Y || WorldPositionCm.Y > Bounds.Max.Y) continue;
                    FHitResult Hit;
                    if (Mesh->LineTraceComponent(Hit,
                            FVector(WorldPositionCm.X, WorldPositionCm.Y, Bounds.Max.Z + 100.0),
                            FVector(WorldPositionCm.X, WorldPositionCm.Y, Bounds.Min.Z - 100.0), Params) &&
                        (!CapturedGroundZCm.IsSet() || Hit.ImpactPoint.Z > CapturedGroundZCm.GetValue()))
                    {
                        // Component traces report geometric intersections;
                        // Chaos uses an overlap-all filter and need not set
                        // bBlockingHit as a world-channel trace would.
                        CapturedGroundZCm = Hit.ImpactPoint.Z;
                        CapturedNormal = Hit.ImpactNormal.GetSafeNormal();
                    }
                }
                if (CapturedGroundZCm.IsSet())
                {
                    OutGroundZCm = CapturedGroundZCm.GetValue();
                    OutGroundNormal = CapturedNormal.Z > 0.05 ? CapturedNormal : FVector::UpVector;
                    return true;
                }
                const ALandscapeProxy* HighestLandscape = nullptr;
                TOptional<float> HighestLandscapeZCm;
                for (const TWeakObjectPtr<ALandscapeProxy>& WeakLandscape :
                     GroundSources->Landscapes)
                {
                    const ALandscapeProxy* Landscape = WeakLandscape.Get();
                    if (Landscape == nullptr)
                    {
                        continue;
                    }
                    const TOptional<float> Height =
                        Landscape->GetHeightAtLocation(
                            WorldPositionCm, EHeightfieldSource::Complex);
                    if (Height.IsSet() &&
                        (!HighestLandscapeZCm.IsSet() ||
                         Height.GetValue() > HighestLandscapeZCm.GetValue()))
                    {
                        HighestLandscape = Landscape;
                        HighestLandscapeZCm = Height;
                    }
                }

                if (HighestLandscape != nullptr && HighestLandscapeZCm.IsSet())
                {
                    OutGroundZCm = HighestLandscapeZCm.GetValue();
                    constexpr float NormalProbeOffsetCm = 50.0f;
                    const TOptional<float> HeightX =
                        HighestLandscape->GetHeightAtLocation(
                            WorldPositionCm +
                                FVector(NormalProbeOffsetCm, 0.0f, 0.0f),
                            EHeightfieldSource::Complex);
                    const TOptional<float> HeightY =
                        HighestLandscape->GetHeightAtLocation(
                            WorldPositionCm +
                                FVector(0.0f, NormalProbeOffsetCm, 0.0f),
                            EHeightfieldSource::Complex);
                    OutGroundNormal = FVector::UpVector;
                    if (HeightX.IsSet() && HeightY.IsSet())
                    {
                        OutGroundNormal = FVector(
                            -(HeightX.GetValue() - OutGroundZCm) /
                                NormalProbeOffsetCm,
                            -(HeightY.GetValue() - OutGroundZCm) /
                                NormalProbeOffsetCm,
                            1.0f).GetSafeNormal();
                    }
                    return true;
                }

                if (URaftSimWaterRuntimeAdapter* Water = WeakWater.Get();
                    Water != nullptr && Water->HasLiveWindow())
                {
                    FRaftSimWaterSample Sample;
                    if (Water->SampleWaterAtWorldPosition(
                            WorldPositionCm, Sample))
                    {
                        OutGroundZCm = Sample.BedHeightMeters * 100.0f;
                        OutGroundNormal = FVector::UpVector;
                        return true;
                    }
                }
                return false;
            });

        // D3 needs velocity as well as surface elevation, and a single raft-
        // center sample cannot represent a lateral, crest, or seam crossing.
        // Bind the same authoritative water adapter as a per-segment field;
        // the raft adapter chooses the deformed tube sample positions.
        RaftRuntime->SetFlexibleWaterFieldSampler(
            [WeakWater](
                const FVector& WorldPositionCm,
                FRaftSimFlexUniformWater& OutWater) -> bool
            {
                OutWater = FRaftSimFlexUniformWater{};
                OutWater.bWet = false;
                URaftSimWaterRuntimeAdapter* Water = WeakWater.Get();
                if (Water == nullptr || !Water->HasLiveWindow())
                {
                    return false;
                }
                FRaftSimWaterSample Sample;
                if (!Water->SampleWaterAtWorldPosition(WorldPositionCm, Sample))
                {
                    return false;
                }
                OutWater.SurfaceHeightM = Sample.SurfaceHeightMeters;
                OutWater.VelocityMps = Sample.VelocityMetersPerSecond;
                OutWater.bWet = Sample.bWet;
                return true;
            });
    }
}

FRaftSimPhysicsTickOutput URaftSimPhysicsBridgeSubsystem::TickBridge(const FRaftSimPhysicsTickInput& Input)
{
    AccumulatedSeconds += FMath::Max(Input.FrameDeltaSeconds, 0.0f);

    // A 0.5 m rapid window is intentionally much more expensive than the
    // earlier 2 m field. Never solve it repeatedly inside one rendered frame:
    // a single hitch otherwise requested as many as 15 second-order solves,
    // each made the next frame later, and the game locked into a ~1 FPS
    // catch-up spiral. Raft/Chrono ticks may catch up against the latest
    // authoritative water state; the live fluid itself advances at most once
    // per render frame. Four raft ticks cover a stable 15 FPS floor, and any
    // still-older wall-clock debt is discarded so recovery is immediate.
    constexpr int32 kMaximumRaftCatchUpTicksPerFrame = 4;
    int32 CatchUpTickCount = 0;
    while (AccumulatedSeconds + KINDA_SMALL_NUMBER >= WaterStepSeconds &&
           CatchUpTickCount < kMaximumRaftCatchUpTicksPerFrame)
    {
        if (!RunOneFixedWaterTick(/*bAdvanceWaterSolver=*/CatchUpTickCount == 0))
        {
            break;
        }
        AccumulatedSeconds -= WaterStepSeconds;
        ++CatchUpTickCount;
    }
    if (AccumulatedSeconds >= WaterStepSeconds)
    {
        AccumulatedSeconds = FMath::Fmod(AccumulatedSeconds, WaterStepSeconds);
    }

    return LastOutput;
}

void URaftSimPhysicsBridgeSubsystem::RecordContactTelemetryEvent(
    const FRaftSimRaftContactTelemetryEvent& Event
)
{
    LastOutput.ContactTelemetryEvents.Add(Event);
    RefreshContactRuntimeSummary();
}

bool URaftSimPhysicsBridgeSubsystem::RunOneFixedWaterTick(bool bAdvanceWaterSolver)
{
    if (!WaterRuntime || !RaftRuntime)
    {
        return false;
    }

    if (bAdvanceWaterSolver && !WaterRuntime->StepWater(WaterStepSeconds))
    {
        return false;
    }

    const int32 Substeps = FMath::Max(1, FMath::CeilToInt(WaterStepSeconds / ChronoSubstepSeconds));
    const float ActualSubstep = WaterStepSeconds / static_cast<float>(Substeps);
    for (int32 SubstepIndex = 0; SubstepIndex < Substeps; ++SubstepIndex)
    {
        RaftRuntime->StepRaftDynamics(ActualSubstep);
    }

    ++PhysicsFrame;
    LastOutput.CommittedPhysicsFrame = PhysicsFrame;
    LastOutput.SimTimeSeconds = PhysicsFrame * WaterStepSeconds;
    LastOutput.RaftState = RaftRuntime->GetKinematicState();
    LastOutput.WaterSamplesApplied = 0;
    RefreshContactRuntimeSummary();
    return true;
}

void URaftSimPhysicsBridgeSubsystem::RefreshContactRuntimeSummary()
{
    FRaftSimRaftContactRuntimeSummary Summary;
    Summary.EventCount = LastOutput.ContactTelemetryEvents.Num();

    for (const FRaftSimRaftContactTelemetryEvent& Event : LastOutput.ContactTelemetryEvents)
    {
        Summary.MaxContactLoadingNewtons = FMath::Max(
            Summary.MaxContactLoadingNewtons,
            Event.ContactLoadingNewtons
        );

        if (Event.Outcome == ERaftSimContactOutcome::Pin || Event.Outcome == ERaftSimContactOutcome::Release)
        {
            ++Summary.PinOrReleaseEventCount;
        }

        if (
            Event.Outcome == ERaftSimContactOutcome::Surf
            || Event.Outcome == ERaftSimContactOutcome::Flush
            || Event.Outcome == ERaftSimContactOutcome::Flip
            || Event.Outcome == ERaftSimContactOutcome::FlipRisk
        )
        {
            ++Summary.SurfFlushOrFlipEventCount;
        }
    }

    LastOutput.ContactRuntimeSummary = Summary;
    LastOutput.ContactEvents = Summary.EventCount;
}
