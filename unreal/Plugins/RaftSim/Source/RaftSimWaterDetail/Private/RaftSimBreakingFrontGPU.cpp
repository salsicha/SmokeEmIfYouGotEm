#include "RaftSimBreakingFrontGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimBreakingFrontCS:public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimBreakingFrontCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimBreakingFrontCS,FGlobalShader);
    class FPhase:SHADER_PERMUTATION_INT("RAFTSIM_BREAKING_PHASE",3);
    using FPermutationDomain=TShaderPermutationDomain<FPhase>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntPoint,GridSize)
        SHADER_PARAMETER(float,CellMeters)
        SHADER_PARAMETER(uint32,Periodic)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,Geometry)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,HydroRate)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Pairs)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Coverage)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float>,Fraction)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,SurfaceJumps)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5);}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimBreakingFrontCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimBreakingFront.usf","MainCS",SF_Compute);

FRaftSimBreakingFrontResult RaftSimClassifyBreakingFrontGPU(FRDGBuilder& Graph,
    FRDGBufferRef Geometry,FRDGBufferRef HydroRate,FRDGBufferRef Pairs,FIntPoint Size,
    float CellMeters,bool bPeriodic,FString& Error)
{
    FRaftSimBreakingFrontResult R;Error.Reset();
    if(Size.X<1 || Size.Y<1 || Size.X>512 || Size.Y>512 || !FMath::IsFinite(CellMeters) || CellMeters<=0)
    {Error=TEXT("Invalid breaking-front grid");return R;}
    const uint32 N=Size.X*Size.Y;
    const auto Matches=[N](FRDGBufferRef B,uint32 Stride){return B && B->Desc.NumElements==N && B->Desc.BytesPerElement==Stride;};
    if(!Matches(Geometry,8) || !Matches(HydroRate,16) || !Matches(Pairs,4))
    {Error=TEXT("Breaking fronts require same-stage depth/bed, hydro rate and wet graph");return R;}
    auto Buffer=[&](uint32 Count,const TCHAR* Name)
    {auto D=FRDGBufferDesc::CreateStructuredDesc(4,Count);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name);};
    auto Coverage=Buffer(N,TEXT("BreakingFront.Coverage"));
    R.Fraction=Buffer(N,TEXT("BreakingFront.Fraction"));R.Diagnostics=Buffer(4,TEXT("BreakingFront.Diagnostics"));
    auto JumpDesc=FRDGBufferDesc::CreateStructuredDesc(8,N);JumpDesc.Usage|=BUF_SourceCopy;
    R.SurfaceJumps=Graph.CreateBuffer(JumpDesc,TEXT("BreakingFront.SurfaceJumps"));
    AddClearUAVPass(Graph,Graph.CreateUAV(R.Diagnostics),0u);
    for(int32 Phase=0;Phase<3;++Phase)
    {
        auto* P=Graph.AllocParameters<FRaftSimBreakingFrontCS::FParameters>();
        P->GridSize=Size;P->CellMeters=CellMeters;P->Periodic=bPeriodic?1u:0u;
        P->Geometry=Graph.CreateSRV(Geometry);P->HydroRate=Graph.CreateSRV(HydroRate);P->Pairs=Graph.CreateSRV(Pairs);
        P->Coverage=Graph.CreateUAV(Coverage);P->Diagnostics=Graph.CreateUAV(R.Diagnostics);P->Fraction=Graph.CreateUAV(R.Fraction);
        P->SurfaceJumps=Graph.CreateUAV(R.SurfaceJumps);
        FRaftSimBreakingFrontCS::FPermutationDomain Perm;Perm.Set<FRaftSimBreakingFrontCS::FPhase>(Phase);
        TShaderMapRef<FRaftSimBreakingFrontCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Perm);ClearUnusedGraphResources(Shader,P);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Breaking Front Phase%d",Phase),Shader,P,
            FIntVector(FMath::DivideAndRoundUp(N,64u),1,1));
    }
    return R;
}

FRaftSimTotalDepthStepResult RaftSimTryHybridBreakingStepGPU(FRDGBuilder& Graph,
    FRDGBufferRef State,FRDGBufferRef Bed,FRDGBufferRef Progress,FIntPoint Size,
    float CellMeters,bool bPeriodic,bool bSecondOrder,FString& Error,
    FRaftSimTotalDepthBoundaryProvider BoundaryForStage,FRDGBufferRef IterationDispatchArgs)
{
    auto Select=[&](FRDGBuilder& G,FRDGBufferRef,const FRaftSimTotalDepthTransportResult& Stage)
    {return RaftSimClassifyBreakingFrontGPU(G,Stage.Geometry,Stage.HydroRate,Stage.Pairs,Size,CellMeters,bPeriodic,Error).Fraction;};
    return RaftSimTryTotalDepthStepGPU(Graph,State,Bed,Progress,Size,CellMeters,bPeriodic,
        bSecondOrder,Select,Error,BoundaryForStage,IterationDispatchArgs);
}
