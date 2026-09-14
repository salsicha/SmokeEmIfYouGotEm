#include "RaftSimTotalDepthFrameGPU.h"
#include "RaftSimTotalDepthStateGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimTotalDepthFrameCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimTotalDepthFrameCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimTotalDepthFrameCS,FGlobalShader);
    class FPhase : SHADER_PERMUTATION_INT("RAFTSIM_FRAME_PHASE",3);
    class FBoundary : SHADER_PERMUTATION_BOOL("RAFTSIM_FRAME_BOUNDARY");
    using FPermutationDomain=TShaderPermutationDomain<FPhase,FBoundary>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntPoint,GridSize)
        SHADER_PARAMETER(FVector2f,OriginMeters)
        SHADER_PARAMETER(float,CellMeters)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,State)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Surface)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Progress)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,BoundaryVolume)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Summary)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,TrialDiagnostics)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,ProjectionDiagnostics)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>,Output)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5);}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimTotalDepthFrameCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimTotalDepthFrame.usf","MainCS",SF_Compute);

FRaftSimTotalDepthFrameResult RaftSimResolveTotalDepthFrameGPU(FRDGBuilder& Graph,
    const FRaftSimTotalDepthAdvanceResult& C,FRDGBufferRef Reference,FIntPoint Size,
    FVector2f OriginMeters,float CellMeters,FString& Error)
{
    FRaftSimTotalDepthFrameResult R;Error.Reset();
    auto Record=[](FRDGBufferRef B,uint32 Stride,uint32 N){return B && B->Desc.BytesPerElement==Stride && B->Desc.NumElements==N;};
    if(OriginMeters.ContainsNaN() || !Record(C.Progress,16,1) || !Record(C.Summary,4,4) || !Record(C.Diagnostics,4,4))
    {Error=TEXT("Completed total-depth frame requires finite registration and paired progress/summary/diagnostics");return R;}
    auto Projection=RaftSimTransferTotalDepthStateGPU(Graph,C.State,C.State,Reference,Size,FIntPoint::ZeroValue,CellMeters,Error);
    if(!Projection.Surface)return R;
    if(C.BoundaryVolume && !Record(C.BoundaryVolume,16,2*(Size.X+Size.Y)))
    {Error=TEXT("Completed boundary frame requires its exact per-face inventory");return R;}
    auto D=FRDGBufferDesc::CreateStructuredDesc(4,4);D.Usage|=BUF_SourceCopy;
    R.Diagnostics=Graph.CreateBuffer(D,TEXT("TotalFrame.Diagnostics"));AddClearUAVPass(Graph,Graph.CreateUAV(R.Diagnostics),0u);
    R.Texture=Graph.CreateTexture(FRDGTextureDesc::Create2D(FIntPoint(Size.X,Size.Y+1),PF_A32B32G32R32F,
        FClearValueBinding::None,TexCreate_ShaderResource|TexCreate_UAV),TEXT("TotalFrame.PairedSurface"));
    for(int32 Phase=0;Phase<3;++Phase)
    {
        auto* P=Graph.AllocParameters<FRaftSimTotalDepthFrameCS::FParameters>();
        P->GridSize=Size;P->OriginMeters=OriginMeters;P->CellMeters=CellMeters;
        P->State=Graph.CreateSRV(C.State);P->Surface=Graph.CreateSRV(Projection.Surface);P->Progress=Graph.CreateSRV(C.Progress);
        P->BoundaryVolume=C.BoundaryVolume?Graph.CreateSRV(C.BoundaryVolume):nullptr;
        P->Summary=Graph.CreateSRV(C.Summary);P->TrialDiagnostics=Graph.CreateSRV(C.Diagnostics);
        P->ProjectionDiagnostics=Graph.CreateSRV(Projection.Diagnostics);P->Diagnostics=Graph.CreateUAV(R.Diagnostics);P->Output=Graph.CreateUAV(R.Texture);
        FRaftSimTotalDepthFrameCS::FPermutationDomain Perm;Perm.Set<FRaftSimTotalDepthFrameCS::FPhase>(Phase);
        Perm.Set<FRaftSimTotalDepthFrameCS::FBoundary>(C.BoundaryVolume!=nullptr);
        TShaderMapRef<FRaftSimTotalDepthFrameCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Perm);ClearUnusedGraphResources(Shader,P);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Total Frame Phase%d",Phase),Shader,P,
            Phase==1?FIntVector(1,1,1):FComputeShaderUtils::GetGroupCount(FIntPoint(Size.X,Size.Y+(Phase==2?1:0)),FIntPoint(8,8)));
    }
    // This graph-local texture may still be consumed by later passes. Its
    // owner sets final access when extracting it, not before ownership exists.
    return R;
}
