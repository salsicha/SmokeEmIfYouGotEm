#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimGroundContactAudit.h"
#include "RaftSimHolePourOver.h"
#include "RaftSimHoleWave.h"
#include "HAL/IConsoleManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"

#include "EngineUtils.h"
#include "LandscapeProxy.h"
#include "Components/StaticMeshComponent.h"
#include "CollisionQueryParams.h"
#include "ProfilingDebugging/CsvProfiler.h"

CSV_DEFINE_CATEGORY(RaftSimClock,true);

namespace
{
TAutoConsoleVariable<int32> CVarRaftSimHoleWaterPhysics(
    TEXT("RaftSim.HoleWaterPhysics"), 0,
    TEXT("1: the hull meets each hole's falling water and breaking wave (RaftSimHolePourOver.h, RaftSimHoleWave.h): ")
    TEXT("a drifting raft is held and pushed back into the falling water, a paddling crew punches through. ")
    TEXT("0 (default until checked on the rivers): the water adapter's own hole currents only."),
    ECVF_Default);

// Each hole's trough level, sampled once a frame: the breaking wave's pile
// stands on it.
struct FHoleToes
{
    uint64 Frame = MAX_uint64;
    TArray<TPair<FVector2D, double>> BySite;
};

// The breaking wave below a hole site's pour-over (RaftSimHoleWave.h): as
// high as the crest relief the hull already floats on, as strong as the
// shared roller.
RaftSimHoleWave::FShape WaveOf(const URaftSimWaterRuntimeAdapter::FSupportBreakingSite& Site)
{
    const double Strength = FMath::Clamp(Site.Intensity * Site.SpillingFraction, 0.0f, 1.0f);
    // A legacy lattice crest carries no physical height: a modest pile.
    const double CrestHeightM = Site.PhysicalCrestHeightMeters >= 0.0f ? Site.PhysicalCrestHeightMeters : 0.55;
    return RaftSimHoleWave::FShape::ForCrest(CrestHeightM, Site.PhysicalCrestLengthMeters, Strength);
}

// The hull's water at a point near the river's holes: the water falling over
// each pour-over (RaftSimHolePourOver.h) and the breaking wave's pile below
// it (RaftSimHoleWave.h). The holes, the surface the water falls down and
// the current over each crest all come from the same water adapter the hull
// floats on. bVelocity false skips the currents (a surface-only probe).
RaftSimHoleWave::FHullWater WithHoles(URaftSimWaterRuntimeAdapter& Water, const FVector& WorldPositionCm,
    const FRaftSimWaterSample& Here, bool bVelocity, FHoleToes& Toes)
{
    RaftSimHoleWave::FHullWater Hull;
    Hull.SurfaceM = Here.SurfaceHeightMeters;
    Hull.VelocityMps = Here.VelocityMetersPerSecond;
    if (!Here.bWet || !Water.HasFeatureKinematics() || CVarRaftSimHoleWaterPhysics.GetValueOnAnyThread() == 0)
    {
        return Hull;
    }
    const TConstArrayView<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites = Water.GetFeatureBreakingSites();
    if (Sites.IsEmpty())
    {
        return Hull;
    }
    FVector2D Coordinates;
    FVector Tangent, Left;
    if (!Water.WorldToRiverCoordinates(WorldPositionCm, Coordinates, Tangent, Left))
    {
        return Hull;
    }
    if (Toes.Frame != GFrameCounter)
    {
        Toes.Frame = GFrameCounter;
        Toes.BySite.Reset();
    }
    const float ElevationM = float(WorldPositionCm.Z * 0.01) + Water.GetRiverVerticalDatumM();
    const auto SampleAt = [&Water, ElevationM](const FVector2D& PointM, double& OutSurfaceM, FVector& OutVelocityMps)
    {
        FVector PointCm;
        FRaftSimWaterSample Sample;
        if (!Water.RiverToWorldPosition(PointM, ElevationM, PointCm) ||
            !Water.SampleRaftInteractionWaterAtWorldPosition(PointCm, Sample) || !Sample.bWet)
        {
            return false;
        }
        OutSurfaceM = Sample.SurfaceHeightMeters;
        OutVelocityMps = Sample.VelocityMetersPerSecond;
        return true;
    };
    const auto SurfaceAt = [&Water, ElevationM](const FVector2D& PointM, double& OutSurfaceM)
    {
        FVector PointCm;
        FRaftSimWaterSample Sample;
        if (!Water.RiverToWorldPosition(PointM, ElevationM, PointCm) ||
            !Water.SampleRaftSupportSurfaceAtWorldPosition(PointCm, Sample) || !Sample.bWet)
        {
            return false;
        }
        OutSurfaceM = Sample.SurfaceHeightMeters;
        return true;
    };
    for (const URaftSimWaterRuntimeAdapter::FSupportBreakingSite& Site : Sites)
    {
        const FVector2D Flow = Site.FlowDirection.GetSafeNormal();
        if (Flow.IsNearlyZero() || FVector2D::DistSquared(Coordinates, Site.RiverCoordinatesMeters) > FMath::Square(20.0))
        {
            continue;
        }
        const FVector Downstream = (Tangent * Flow.X + Left * Flow.Y).GetSafeNormal2D();
        const FVector Across = (Left * Flow.X - Tangent * Flow.Y).GetSafeNormal2D();
        const FVector2D Relative = Coordinates - Site.RiverCoordinatesMeters;
        const FVector2D Left2(-Flow.Y, Flow.X);
        if (bVelocity)
        {
            // A physical crest's relief falls to its toe; the legacy lattice
            // crest drops over about a metre.
            RaftSimHolePourOver::FSite Face = RaftSimHolePourOver::FSite::FromCrestLength(
                Site.RiverCoordinatesMeters, Flow, Site.PhysicalCrestLengthMeters);
            if (Site.PhysicalCrestHeightMeters < 0.0f)
            {
                Face.FaceLengthM = 1.0;
                Face.CrestBowPerSquareMeter = 0.0;
            }
            Hull.VelocityMps = RaftSimHolePourOver::Velocity(Face, FVector(Coordinates.X, Coordinates.Y, WorldPositionCm.Z * 0.01),
                Hull.VelocityMps, Here.SurfaceHeightMeters, Downstream, Across, SampleAt);
        }
        const RaftSimHoleWave::FShape Wave = WaveOf(Site);
        const double Along = FVector2D::DotProduct(Relative, Flow), AcrossM = FVector2D::DotProduct(Relative, Left2);
        if (Wave.TopAboveToe(Along, AcrossM) <= 0.0)
        {
            continue;
        }
        const TPair<FVector2D, double>* Cached = Toes.BySite.FindByPredicate(
            [&Site](const TPair<FVector2D, double>& Entry) { return Entry.Key == Site.RiverCoordinatesMeters; });
        double ToeM = 0.0;
        if (Cached)
        {
            ToeM = Cached->Value;
        }
        else
        {
            if (!RaftSimHoleWave::ToeM(Wave, [&](double CentreAlong, double& OutWaterM)
                    { return SurfaceAt(Site.RiverCoordinatesMeters + Flow * CentreAlong, OutWaterM); }, ToeM))
            {
                ToeM = TNumericLimits<double>::Lowest();
            }
            Toes.BySite.Emplace(Site.RiverCoordinatesMeters, ToeM);
        }
        RaftSimHoleWave::FHullWater OnPile;
        if (ToeM > TNumericLimits<double>::Lowest() &&
            RaftSimHoleWave::Apply(Wave, Along, AcrossM, WorldPositionCm.Z * 0.01, ToeM, Here.SurfaceHeightMeters,
                Hull.VelocityMps, Downstream, Across, OnPile))
        {
            Hull = OnPile;
        }
    }
    return Hull;
}
}

void URaftSimPhysicsBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    WaterRuntime = NewObject<URaftSimWaterRuntimeAdapter>(this);
    RaftRuntime = NewObject<URaftSimChronoRuntimeAdapter>(this);
}

void URaftSimPhysicsBridgeSubsystem::Deinitialize()
{
    // Release the contact registry's world delegates before subsystem teardown.
    if (RaftRuntime) { RaftRuntime->SetHullGroundArcQuery({}); RaftRuntime->SetHullGroundQuery({}); RaftRuntime->SetGroundSphereSweep({}); RaftRuntime->SetGroundContactObserver({}); RaftRuntime->SetGroundSurfaceSampler({}); }
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
    FixedClock.Reset();
    bRaftStepFailureLatched=false;
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
        // Holes' troughs, shared by the probes below.
        const TSharedRef<FHoleToes> Toes = MakeShared<FHoleToes>();
        RaftRuntime->SetWaterSurfaceSampler(
            [WeakWater, Toes](const FVector& WorldPositionCm, float& OutWaterSurfaceZCm) -> bool
            {
                if (URaftSimWaterRuntimeAdapter* Water = WeakWater.Get())
                {
                    if (Water->HasLiveWindow())
                    {
                        FRaftSimWaterSample Sample;
                        if (Water->SampleRaftSupportSurfaceAtWorldPosition(WorldPositionCm, Sample)
                            && Sample.bWet)
                        {
                            // A hole's breaking wave stands on the water.
                            OutWaterSurfaceZCm = float(WithHoles(*Water, WorldPositionCm, Sample, false, *Toes).SurfaceM * 100.0);
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
        RaftRuntime->SetGroundContactObserver({});
        RaftRuntime->SetGroundSphereSweep({});
        RaftRuntime->SetHullGroundQuery({});
        RaftRuntime->SetHullGroundArcQuery({});
        RaftRuntime->SetHullGroundQuery([GroundSources](auto A,auto B,auto Faces,double Skin,double Clearance)
            {return GroundSources->SweepCapturedSurface(A,B,Faces,Skin,Clearance);});
        RaftRuntime->SetHullGroundArcQuery([GroundSources](auto A,auto B,auto Faces,double Skin,double Clearance,const FRaftSimHullArcPath& Arc)
            {return GroundSources->SweepCapturedSurface(A,B,Faces,Skin,Clearance,true,&Arc);});
        UE_LOG(LogTemp,Display,TEXT("Production full-hull contact: original indexed raft against captured triangles and Complex landscape; physical capsize, no pose transition"));
#if !UE_BUILD_SHIPPING
        if(FParse::Param(FCommandLine::Get(),TEXT("RaftSimFullHullGroundReview")))
        {
            RaftRuntime->SetHullGroundQuery([GroundSources](TConstArrayView<FVector> A,TConstArrayView<FVector> B,
                TConstArrayView<FIntVector> Faces,double Skin,double Clearance)
            {return GroundSources->SweepCapturedSurface(A,B,Faces,Skin,Clearance);});
            UE_LOG(LogTemp,Display,TEXT("Full-hull ground review enabled: every authored face, bounded rotating/deforming sweeps; no six-sphere or height-projection fallback"));
        }
        if(FParse::Param(FCommandLine::Get(),TEXT("RaftSimContinuousGroundReview")))
        {
            RaftRuntime->SetGroundSphereSweep([GroundSources](const FVector& A,const FVector& B,double Radius,FHitResult& Hit)
            { return GroundSources->SweepCapturedSphere(A,B,Radius,Hit); });
            UE_LOG(LogTemp,Display,TEXT("Continuous ground review enabled: six swept tube supports; source mesh unchanged; rotation chord limit 0.005 rad"));
        }
        FString ContactAuditPath;
        if(FParse::Value(FCommandLine::Get(),TEXT("RaftSimGroundContactAudit="),ContactAuditPath))
        {
            if(FPaths::FileExists(ContactAuditPath))
            { UE_LOG(LogTemp,Error,TEXT("Refusing to overwrite existing ground contact evidence: %s"),*ContactAuditPath); }
            else
            {
                const auto Audit=MakeShared<FRaftSimGroundContactAudit>(GetWorld(),GroundSources,ContactAuditPath);
                RaftRuntime->SetGroundContactObserver([Audit](const FRaftSimGroundContactObservation& O){Audit->Record(O);});
            }
        }
#endif
        RaftRuntime->SetGroundSurfaceSampler(
            [WeakWater, GroundSources](
                const FVector& WorldPositionCm,
                float& OutGroundZCm,
                FVector& OutGroundNormal) -> bool
            {
                double PhysicalGroundZCm=0.;
                if (GroundSources->SampleGround(WorldPositionCm,PhysicalGroundZCm,OutGroundNormal))
                {
                    OutGroundZCm=float(PhysicalGroundZCm);
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
            [WeakWater, Toes](
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
                if (!Water->SampleRaftInteractionWaterAtWorldPosition(WorldPositionCm, Sample))
                {
                    return false;
                }
                // Over a hole's pour-over the water falls into the trough;
                // below it the breaking wave's pile rolls back upstream.
                const RaftSimHoleWave::FHullWater Hull = WithHoles(*Water, WorldPositionCm, Sample, true, *Toes);
                OutWater.SurfaceHeightM = Hull.SurfaceM;
                OutWater.VelocityMps = Hull.VelocityMps;
                OutWater.bWet = Sample.bWet;
                return true;
            });
        // Down the slope of a breaking wave's pile, back into the trough.
        RaftRuntime->SetWaterSurfaceSlopeSampler(
            [WeakWater, Toes](const FVector& WorldPositionCm, FVector2D& OutSlope) -> bool
            {
                URaftSimWaterRuntimeAdapter* Water = WeakWater.Get();
                FRaftSimWaterSample Sample;
                if (Water == nullptr || !Water->HasLiveWindow() ||
                    !Water->SampleRaftSupportSurfaceAtWorldPosition(WorldPositionCm, Sample) || !Sample.bWet)
                {
                    return false;
                }
                OutSlope = WithHoles(*Water, WorldPositionCm, Sample, false, *Toes).Slope;
                return true;
            });
    }
}

FRaftSimPhysicsTickOutput URaftSimPhysicsBridgeSubsystem::TickBridge(const FRaftSimPhysicsTickInput& Input)
{
    CSV_SCOPED_TIMING_STAT(RaftSimClock,TickBridge);
    // Bound work per rendered frame, not physical elapsed time. Every accepted
    // tick advances water AND raft; a slow frame retains its unprocessed debt.
    // Capacity/lag are measured, never hidden by dropping ticks or enlarging dt.
    int32 Completed=0;
    LastOutput.bFixedTickFailed=!FixedClock.Advance(double(Input.FrameDeltaSeconds),double(WaterStepSeconds),
        FMath::Clamp(Input.MaximumFixedTicks,1,4),
        [this]{return RunOneFixedWaterTick();},Completed);
    LastOutput.FixedTicksThisFrame=Completed;
    LastOutput.SimulationBacklogSeconds=FixedClock.BacklogSeconds;
    CSV_CUSTOM_STAT(RaftSimClock,RequestedSeconds,FixedClock.RequestedSeconds,ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimClock,CommittedSeconds,FixedClock.CommittedSeconds,ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimClock,BacklogSeconds,FixedClock.BacklogSeconds,ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimClock,FixedTicks,Completed,ECsvCustomStatOp::Set);
    CSV_CUSTOM_STAT(RaftSimClock,Failed,int32(LastOutput.bFixedTickFailed),ECsvCustomStatOp::Set);
    if(WaterRuntime)
    {
        double NativeSeconds=0;
        if(WaterRuntime->GetLiveFieldTimeSeconds(NativeSeconds))
            CSV_CUSTOM_STAT(RaftSimClock,NativeFieldSeconds,NativeSeconds,ECsvCustomStatOp::Set);
        CSV_CUSTOM_STAT(RaftSimClock,WaterCommittedSeconds,WaterRuntime->GetCommittedStepSeconds(),ECsvCustomStatOp::Set);
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

bool URaftSimPhysicsBridgeSubsystem::RunOneFixedWaterTick()
{
    CSV_SCOPED_TIMING_STAT(RaftSimClock,FixedWaterRaftTick);
    if(bRaftStepFailureLatched)return false;
    if (!WaterRuntime || !RaftRuntime)
    {
        return false;
    }

    if (!WaterRuntime->StepWater(WaterStepSeconds))
    {
        return false;
    }

    const int32 Substeps = FMath::Max(1, FMath::CeilToInt(WaterStepSeconds / ChronoSubstepSeconds));
    const float ActualSubstep = WaterStepSeconds / static_cast<float>(Substeps);
    for (int32 SubstepIndex = 0; SubstepIndex < Substeps; ++SubstepIndex)
    {
        if(!RaftRuntime->StepRaftDynamics(ActualSubstep))
        {
            bRaftStepFailureLatched=true;
            LastOutput.RaftState=RaftRuntime->GetKinematicState();
            UE_LOG(LogTemp,Error,TEXT("Raft fixed substep refused: substep=%d/%d; partial water tick latched, no clock commit or retry until reconfigure"),SubstepIndex+1,Substeps);
            return false;
        }
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
