#include "RaftSimTotalDepthStateGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimTotalDepthStateCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimTotalDepthStateCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimTotalDepthStateCS,FGlobalShader);
    class FExchange : SHADER_PERMUTATION_BOOL("RAFTSIM_WINDOW_EXCHANGE");
    using FPermutationDomain=TShaderPermutationDomain<FExchange>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntPoint,GridSize)
        SHADER_PARAMETER(FIntPoint,SourceOffset)
        SHADER_PARAMETER(float,CellMeters)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,PreviousState)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,NewDomainState)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,Reference)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,PreviousWindowExchange)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,NextState)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Surface)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,WindowExchange)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimTotalDepthStateCS,
    "/Plugin/RaftSimWaterDetail/Private/RaftSimTotalDepthState.usf","MainCS",SF_Compute);

FRaftSimTotalDepthStateResult RaftSimTransferTotalDepthStateGPU(FRDGBuilder& Graph,
    FRDGBufferRef Previous,FRDGBufferRef Entering,FRDGBufferRef Reference,FIntPoint Size,
    FIntPoint Offset,float CellMeters,FString& Error,FRDGBufferRef PreviousWindowExchange)
{
    FRaftSimTotalDepthStateResult Result;
    Error.Reset();
    if(Size.X<2 || Size.Y<2 || Size.X>512 || Size.Y>512 || !FMath::IsFinite(CellMeters) || CellMeters<=0 ||
        int64(Offset.X)<=-int64(Size.X) || int64(Offset.X)>=Size.X ||
        int64(Offset.Y)<=-int64(Size.Y) || int64(Offset.Y)>=Size.Y)
    { Error=TEXT("Total-depth transfer requires a valid grid and retained integer-cell overlap");return Result; }
    const uint32 Count=uint32(Size.X)*uint32(Size.Y);
    auto Matches=[Count](FRDGBufferRef Buffer,uint32 Stride)
    { return Buffer && Buffer->Desc.BytesPerElement==Stride && Buffer->Desc.NumElements==Count; };
    if(!Matches(Previous,16) || !Matches(Entering,16) || !Matches(Reference,8) ||
        (PreviousWindowExchange && !Matches(PreviousWindowExchange,16)))
    { Error=TEXT("Total-depth transfer needs exact total-state and paired bed/surface buffers");return Result; }
    auto StateDesc=FRDGBufferDesc::CreateStructuredDesc(16,Count);StateDesc.Usage|=BUF_SourceCopy;
    auto DiagnosticDesc=FRDGBufferDesc::CreateStructuredDesc(4,4);DiagnosticDesc.Usage|=BUF_SourceCopy;
    Result.State=Graph.CreateBuffer(StateDesc,TEXT("TotalDepth.ConservedState"));
    Result.Surface=Graph.CreateBuffer(StateDesc,TEXT("TotalDepth.DerivedSurface"));
    Result.Diagnostics=Graph.CreateBuffer(DiagnosticDesc,TEXT("TotalDepth.TransferDiagnostics"));
    const bool TrackExchange=Offset!=FIntPoint::ZeroValue || PreviousWindowExchange!=nullptr;
    if(TrackExchange)Result.WindowExchange=Graph.CreateBuffer(StateDesc,TEXT("TotalDepth.WindowExchange"));
    if(TrackExchange && !PreviousWindowExchange)
    {
        PreviousWindowExchange=Graph.CreateBuffer(StateDesc,TEXT("TotalDepth.InitialWindowExchange"));
        AddClearUAVPass(Graph,Graph.CreateUAV(PreviousWindowExchange),0u);
    }
    AddClearUAVPass(Graph,Graph.CreateUAV(Result.Diagnostics),0u);
    auto* P=Graph.AllocParameters<FRaftSimTotalDepthStateCS::FParameters>();
    P->GridSize=Size;P->SourceOffset=Offset;P->CellMeters=CellMeters;
    P->PreviousState=Graph.CreateSRV(Previous);P->NewDomainState=Graph.CreateSRV(Entering);
    P->Reference=Graph.CreateSRV(Reference);P->NextState=Graph.CreateUAV(Result.State);
    P->PreviousWindowExchange=TrackExchange?Graph.CreateSRV(PreviousWindowExchange):nullptr;
    P->WindowExchange=TrackExchange?Graph.CreateUAV(Result.WindowExchange):nullptr;
    P->Surface=Graph.CreateUAV(Result.Surface);P->Diagnostics=Graph.CreateUAV(Result.Diagnostics);
    FRaftSimTotalDepthStateCS::FPermutationDomain Perm;Perm.Set<FRaftSimTotalDepthStateCS::FExchange>(TrackExchange);
    TShaderMapRef<FRaftSimTotalDepthStateCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Perm);ClearUnusedGraphResources(Shader,P);
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Conserved Total-State Transfer"),Shader,P,
        FComputeShaderUtils::GetGroupCount(Size,FIntPoint(8,8)));
    return Result;
}
