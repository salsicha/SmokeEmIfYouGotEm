#include "RaftSimWaterTextureHistory.h"
#include "RHICommandList.h"
#include "RenderingThread.h"
#include "Misc/CoreDelegates.h"

FRaftSimWaterTextureHistory::~FRaftSimWaterTextureHistory()
{
    check(!EndFrameHandle.IsValid());
}

bool FRaftSimWaterTextureHistory::Start(FRHICommandListImmediate& Cmd,FRHITexture* InCurrent,FRHITexture* InPrevious)
{
    check(IsInRenderingThread());
    if (EndFrameHandle.IsValid() || !InCurrent || !InPrevious || InCurrent==InPrevious ||
        InCurrent->GetDesc().Extent!=InPrevious->GetDesc().Extent ||
        InCurrent->GetDesc().Format!=InPrevious->GetDesc().Format)return false;
    Current=InCurrent;Previous=InPrevious;CapturedFrames=0;
    ResetHistory(Cmd);
    EndFrameHandle=FCoreDelegates::OnEndFrameRT.AddLambda([this]()
    { CaptureFrame(FRHICommandListExecutor::GetImmediateCommandList()); });
    return true;
}

void FRaftSimWaterTextureHistory::Copy(FRHICommandListImmediate& Cmd)
{
    check(IsInRenderingThread());
    if (!Current || !Previous)return;
    Cmd.Transition(FRHITransitionInfo(Current,ERHIAccess::Unknown,ERHIAccess::CopySrc));
    Cmd.Transition(FRHITransitionInfo(Previous,ERHIAccess::Unknown,ERHIAccess::CopyDest));
    Cmd.CopyTexture(Current,Previous,FRHICopyTextureInfo());
    Cmd.Transition(FRHITransitionInfo(Current,ERHIAccess::CopySrc,ERHIAccess::SRVMask));
    Cmd.Transition(FRHITransitionInfo(Previous,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
}

void FRaftSimWaterTextureHistory::ResetHistory(FRHICommandListImmediate& Cmd) { Copy(Cmd); }

void FRaftSimWaterTextureHistory::CaptureFrame(FRHICommandListImmediate& Cmd)
{
    if (!Current || !Previous)return;
    Copy(Cmd);++CapturedFrames;
}

void FRaftSimWaterTextureHistory::Stop()
{
    check(IsInRenderingThread());
    if (EndFrameHandle.IsValid())FCoreDelegates::OnEndFrameRT.Remove(EndFrameHandle);
    EndFrameHandle.Reset();Current.SafeRelease();Previous.SafeRelease();
}
