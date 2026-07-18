#include "RaftSimPhysicsBridgeSubsystem.h"

void URaftSimPhysicsBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    WaterRuntime = NewObject<URaftSimWaterRuntimeAdapter>(this);
    RaftRuntime = NewObject<URaftSimChronoRuntimeAdapter>(this);
}

void URaftSimPhysicsBridgeSubsystem::Deinitialize()
{
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
                        if (Water->SampleWaterAtWorldPosition(WorldPositionCm, Sample)
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
    }
}

FRaftSimPhysicsTickOutput URaftSimPhysicsBridgeSubsystem::TickBridge(const FRaftSimPhysicsTickInput& Input)
{
    AccumulatedSeconds += FMath::Max(Input.FrameDeltaSeconds, 0.0f);

    while (AccumulatedSeconds + KINDA_SMALL_NUMBER >= WaterStepSeconds)
    {
        RunOneFixedWaterTick();
        AccumulatedSeconds -= WaterStepSeconds;
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

void URaftSimPhysicsBridgeSubsystem::RunOneFixedWaterTick()
{
    if (!WaterRuntime || !RaftRuntime)
    {
        return;
    }

    if (!WaterRuntime->StepWater(WaterStepSeconds))
    {
        return;
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
