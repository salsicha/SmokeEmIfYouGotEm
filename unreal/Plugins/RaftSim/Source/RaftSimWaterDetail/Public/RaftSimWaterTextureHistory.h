#pragma once
#include "CoreMinimal.h"
#include "RHIResources.h"

class FRHICommandListImmediate;

// Render-thread owned. Snapshot AFTER the rendered frame, not after a solver
// update: zero or several updates must still refer to the last rendered state.
// The owner must enqueue Stop before releasing this object.
class RAFTSIMWATERDETAIL_API FRaftSimWaterTextureHistory
{
public:
    ~FRaftSimWaterTextureHistory();
    bool Start(FRHICommandListImmediate& Cmd,FRHITexture* InCurrent,FRHITexture* InPrevious);
    void Stop();
    void CaptureFrame(FRHICommandListImmediate& Cmd);
    // A new lattice has no vertex correspondence. Seed current geometry rather
    // than interpreting the old lattice's same indices as water movement.
    void ResetHistory(FRHICommandListImmediate& Cmd);
    uint64 GetCapturedFrames() const { return CapturedFrames; }
private:
    void Copy(FRHICommandListImmediate& Cmd);
    FTextureRHIRef Current,Previous;
    FDelegateHandle EndFrameHandle;
    uint64 CapturedFrames=0;
};
