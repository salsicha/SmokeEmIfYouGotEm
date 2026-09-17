#pragma once
#include "RaftSimDetailPresentationFrame.h"
#include "RHICommandList.h"

// Called once on the render thread with one immutable, validated mailbox frame.
// Publish both textures before any subsequent draw; never update just one half.
inline bool RaftSimUploadDetailFrame(FRHICommandListImmediate& Cmd,
    const FRaftSimDetailPresentationFrame& Frame,FRHITexture* Surface,FRHITexture* Flow=nullptr)
{
    const FIntPoint Extent(Frame.Size.X,Frame.Size.Y+1);
    if(!Surface || Frame.Pixels.Num()!=int64(Extent.X)*Extent.Y ||
        Surface->GetDesc().Extent!=Extent || Surface->GetDesc().Format!=PF_A32B32G32R32F)return false;
    if(Flow && (Frame.FoamFlowPixels.Num()!=Frame.Pixels.Num() ||
        Flow->GetDesc().Extent!=Extent || Flow->GetDesc().Format!=PF_A32B32G32R32F))return false;
    const auto Upload=[&](FRHITexture* Texture,const TArray<FVector4f>& Pixels)
    {
        Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::Unknown,ERHIAccess::CopyDest));
        Cmd.UpdateTexture2D(Texture,0,FUpdateTextureRegion2D(0,0,0,0,Extent.X,Extent.Y),
            Extent.X*sizeof(FVector4f),reinterpret_cast<const uint8*>(Pixels.GetData()));
        Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
    };
    Upload(Surface,Frame.Pixels);
    if(Flow)Upload(Flow,Frame.FoamFlowPixels);
    return true;
}
