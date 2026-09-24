#pragma once
#include "CoreMinimal.h"
#include "RaftSimWaterRuntimeAdapter.h"

// Allocation storage only. Reset all fields, including default sample normals,
// on every refresh; no hydraulic/presentation history is cached here.
struct FRaftSimRefreshScratch
{
    TArray<uint8> Wet, LiveWet, Sampled, ProbeWanted;
    TArray<float> Feather, Heights, Relief, Froude, Foam;
    TArray<FRaftSimWaterSample> Samples;
    void Reset(int32 Count)
    {
        Wet.Init(0,Count); LiveWet.Init(0,Count); Sampled.Init(0,Count); ProbeWanted.Init(0,Count);
        Feather.Init(0.f,Count); Heights.Init(0.f,Count); Relief.Init(0.f,Count);
        Froude.Init(0.f,Count); Foam.Init(0.f,Count);
        Samples.Reset(Count);
        Samples.SetNum(Count);
    }
};
