#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimGroundContactAudit.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"

#include "EngineUtils.h"
#include "LandscapeProxy.h"
#include "Components/StaticMeshComponent.h"
#include "CollisionQueryParams.h"
#include "ProfilingDebugging/CsvProfiler.h"

CSV_DEFINE_CATEGORY(RaftSimClock,true);

void URaftSimPhysicsBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    WaterRuntime = NewObject<URaftSimWaterRuntimeAdapter>(this);
    RaftRuntime = NewObject<URaftSimChronoRuntimeAdapter>(this);
}

void URaftSimPhysicsBridgeSubsystem::Deinitialize()
{
    // Release the contact registry's world delegates before subsystem teardown.
    if (RaftRuntime) { RaftRuntime->SetGroundContactObserver({}); RaftRuntime->SetGroundSurfaceSampler({}); }
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
        RaftRuntime->SetGroundContactObserver({});
#if !UE_BUILD_SHIPPING
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
    // Bound work per rendered frame, not physical elapsed time. Every accepted
    // tick advances water AND raft; a slow frame retains its unprocessed debt.
    // Capacity/lag are measured, never hidden by dropping ticks or enlarging dt.
    int32 Completed=0;
    LastOutput.bFixedTickFailed=!FixedClock.Advance(double(Input.FrameDeltaSeconds),double(WaterStepSeconds),4,
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
