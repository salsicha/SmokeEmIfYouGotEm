#pragma once

#include "CoreMinimal.h"
#include "RenderGraphResources.h"

class FRHICommandListImmediate;
class FRHIGPUBufferReadback;
class FRHITexture;

// Test the exact material sampling function on GPU; no runtime readback path.
RAFTSIMWATERDETAIL_API bool RaftSimValidateMacroSamplingGPU(FRHICommandListImmediate& Cmd,
    FRHITexture* Atlas,FIntPoint GridSize,const TArray<FVector4f>& Queries,
    FRHIGPUBufferReadback* Readback,FString& Error,bool bReconstructCrest=false);

// Detail perturbations over the authoritative FV mean flow, not a second
// water level or a replacement for bathymetry / raft-support physics.
struct RAFTSIMWATERDETAIL_API FRaftSimDetailWaterGrid
{
    FIntPoint Size = FIntPoint(128,128);
    float CellMeters = 0.5f;
    float StepSeconds = 1.0f/120.0f;
    float MomentumDampingPerSecond = 0.6f;
    float FoamDecayPerSecond = 0.15f;
    float FoamSourcePerSecond = 0.7f;
    bool bPeriodic = false; // Regression fixtures only; runtime uses walls.
    bool bSecondOrder = false; // MC wave reconstruction + SSP-RK2; foam spatial flux stays upwind.
    bool bActivityMemory = false; // Authored entrainment persistence, not measured turbulent kinetic energy.
    float ActivitySourcePerSecond = 1.0f;
    float ActivityDecayPerSecond = 0.5f;
    FVector2f OriginMeters = FVector2f::ZeroVector;
    float TurbulentHeadMeters = 0; // Explicit, source-driven detail excitation.

    // Flow cells contain depth (m), mean u/v (m/s), aeration source [0,1].
    bool Validate(TConstArrayView<FVector4f> Flow, FString& Error) const;
};

// Render-thread owned. Persist extracted state between graphs; no game-thread
// readback or per-frame reconstruction. Resize/reset must be explicit.
class RAFTSIMWATERDETAIL_API FRaftSimDetailWaterGPU
{
public:
    bool Advance(FRHICommandListImmediate& RHICmdList,
        const FRaftSimDetailWaterGrid& Grid, const TArray<FVector4f>& Flow,
        int32 Steps, const TArray<FVector4f>* InitialState,
        FRHIGPUBufferReadback* Readback, FString& Error,
        const TArray<float>* InitialActivity=nullptr, FRHIGPUBufferReadback* ActivityReadback=nullptr);
    void Reset();
    bool Resolve(FRHICommandListImmediate& RHICmdList,FRHITexture* Target,FString& Error);
    uint64 GetStepCount() const { return StepCount; }
    double GetSimulationSeconds() const { return SimulationSeconds; }
private:
    // State: height perturbation (m), x/y depth-integrated perturbation
    // momentum (m²/s), nonnegative transported foam density. Convert density
    // to bounded coverage in shading; compression must not discard foam mass.
    TRefCountPtr<FRDGPooledBuffer> State;
    TRefCountPtr<FRDGPooledBuffer> MeanFlowState;
    TRefCountPtr<FRDGPooledBuffer> ActivityState;
    FIntPoint StateSize = FIntPoint::ZeroValue;
    float StateCellMeters = 0;
    bool bStatePeriodic = false;
    bool bStateSecondOrder = false;
    bool bStateActivityMemory = false;
    FVector2f StateOriginMeters = FVector2f::ZeroVector;
    double SimulationSeconds = 0;
    uint64 StepCount = 0;
};
