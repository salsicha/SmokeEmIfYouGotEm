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
    LastOutput.ContactEvents = 0;
}
