#include "RaftSimRaftPatchSampler.h"

void URaftSimRaftPatchSampler::Configure(URaftSimRaftPatchLayout* InLayout)
{
    Layout = InLayout;
}

int32 URaftSimRaftPatchSampler::BuildPatchSamples(
    URaftSimWaterRuntimeAdapter* WaterRuntime,
    const FTransform& RaftWorldTransform,
    const FVector& RaftLinearVelocityMetersPerSecond,
    TArray<FRaftSimRaftPatchSample>& OutSamples
) const
{
    OutSamples.Reset();
    if (!Layout || !WaterRuntime)
    {
        return 0;
    }

    for (const FRaftSimRaftPatchDefinition& Patch : Layout->OrderedPatches)
    {
        FRaftSimRaftPatchSample Sample;
        Sample.PatchId = Patch.PatchId;
        Sample.WorldPosition = RaftWorldTransform.TransformPosition(Patch.LocalPositionMeters * 100.0f);
        Sample.WorldVelocityMetersPerSecond = RaftLinearVelocityMetersPerSecond;
        Sample.AreaSquareMeters = Patch.AreaSquareMeters;
        Sample.ForceChannels = Patch.ForceChannels;

        WaterRuntime->SampleWaterAtWorldPosition(Sample.WorldPosition, Sample.Water);
        OutSamples.Add(Sample);
    }

    return OutSamples.Num();
}
