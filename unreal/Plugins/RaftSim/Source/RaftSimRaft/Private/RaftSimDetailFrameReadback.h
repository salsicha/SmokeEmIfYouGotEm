#pragma once
#include "RaftSimDetailPresentationFrame.h"
#include "RHIGPUReadback.h"
#include "RHICommandList.h"

// Render-thread owned ring slot. Poll never waits, and an in-flight copy is
// never reused. No file IO or solver state mutation.
struct FRaftSimDetailFrameReadback
{
    FRHIGPUTextureReadback Readback{TEXT("RaftSimPresentedDetailFrame")};
    FIntPoint Size=FIntPoint::ZeroValue;
    uint64 Sequence=0;
    double Elapsed=0,Simulation=0;
    bool bGPUClockMetadata=false;
    TArray<FVector4f> FoamFlow;
    bool Poll(FRaftSimDetailFrameMailbox& Mailbox)
    {
        if (!Sequence || !Readback.IsReady()) return true;
        int32 Pitch=0;
        const auto* Source=static_cast<const FVector4f*>(Readback.Lock(Pitch));
        if (!Source || Pitch<Size.X) { if (Source) Readback.Unlock(); return false; }
        auto Frame=MakeShared<FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe>();
        Frame->Size=Size;Frame->Sequence=Sequence;Frame->ElapsedSeconds=Elapsed;Frame->SimulationSeconds=Simulation;
        Frame->Pixels.SetNumUninitialized(Size.X*(Size.Y+1));
        for (int32 Y=0;Y<=Size.Y;++Y)
            FMemory::Memcpy(Frame->Pixels.GetData()+Y*Size.X,Source+Y*Pitch,Size.X*sizeof(FVector4f));
        Readback.Unlock();Sequence=0;
        if(bGPUClockMetadata && !Frame->AdoptGPUClock())return false;
        if (!Frame->Validate()) return false;
        if (!bGPUClockMetadata && !Frame->WriteHostClockMetadata()) return false;
        if(!FoamFlow.IsEmpty() && !Frame->AttachFoamFlow(FoamFlow))return false;
        FoamFlow.Reset();
        Mailbox.Publish(Frame); // A newer completed slot may already supersede it.
        return true;
    }
    void Enqueue(FRHICommandListImmediate& Cmd,FRHITexture* Texture,FIntPoint InSize,
        uint64 InSequence,double InElapsed,double InSimulation,bool bInGPUClockMetadata=false,
        const TArray<FVector4f>* InFoamFlow=nullptr)
    {
        check(!Sequence); Size=InSize;Sequence=InSequence;Elapsed=InElapsed;Simulation=InSimulation;bGPUClockMetadata=bInGPUClockMetadata;
        if(InFoamFlow)FoamFlow=*InFoamFlow;else FoamFlow.Reset();
        Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::SRVMask,ERHIAccess::CopySrc));
        Readback.EnqueueCopy(Cmd,Texture);
        Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopySrc,ERHIAccess::SRVMask));
    }
};
