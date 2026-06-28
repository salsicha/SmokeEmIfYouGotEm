#include "RaftSimWaterRuntimeAdapter.h"

void URaftSimWaterRuntimeAdapter::Configure(const FRaftSimWaterRuntimeConfig& InConfig)
{
    Config = InConfig;
    SimTimeSeconds = 0.0;
    Status = Config.ScenarioPackagePath.IsEmpty()
        ? ERaftSimWaterRuntimeStatus::Uninitialized
        : ERaftSimWaterRuntimeStatus::ScenarioBound;
}

bool URaftSimWaterRuntimeAdapter::StepWater(float DeltaSeconds)
{
    if (Status == ERaftSimWaterRuntimeStatus::Uninitialized || DeltaSeconds <= 0.0f)
    {
        return false;
    }

    Status = ERaftSimWaterRuntimeStatus::Running;
    SimTimeSeconds += DeltaSeconds;
    return true;
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
    OutSample.SurfaceHeightMeters = WorldPosition.Z;
    OutSample.BedHeightMeters = WorldPosition.Z - 1.0f;
    OutSample.DepthMeters = 1.0f;
    OutSample.VelocityMetersPerSecond = FVector::ZeroVector;
    OutSample.SurfaceNormal = FVector::UpVector;
    OutSample.bWet = true;
    return true;
}
