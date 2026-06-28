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
    float InWaterStepSeconds,
    float InChronoSubstepSeconds
)
{
    WaterStepSeconds = FMath::Max(InWaterStepSeconds, KINDA_SMALL_NUMBER);
    ChronoSubstepSeconds = FMath::Clamp(InChronoSubstepSeconds, KINDA_SMALL_NUMBER, WaterStepSeconds);
    AccumulatedSeconds = 0.0f;
    PhysicsFrame = 0;
    LastOutput = FRaftSimPhysicsTickOutput();

    if (WaterRuntime)
    {
        WaterRuntime->Configure(WaterConfig);
    }

    if (RaftRuntime)
    {
        RaftRuntime->ConfigureRaftBody(RaftConfig);
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

    WaterRuntime->StepWater(WaterStepSeconds);

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
