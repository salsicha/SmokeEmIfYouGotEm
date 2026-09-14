#include "RaftSimTemporalBoundaryGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimTemporalBoundaryCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimTemporalBoundaryCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimTemporalBoundaryCS,FGlobalShader);
    class FSecondStage : SHADER_PERMUTATION_BOOL("RAFTSIM_BOUNDARY_SECOND_STAGE");
    using FPermutationDomain=TShaderPermutationDomain<FSecondStage>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Count)
        SHADER_PARAMETER(FVector2f,FirstTime)
        SHADER_PARAMETER(float,Duration)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,FirstState)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,SecondState)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,FirstBed)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,SecondBed)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,FirstVelocity)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,SecondVelocity)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Progress)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,TrialInfo)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,State)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float>,Bed)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,FaceTrace)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5);}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimTemporalBoundaryCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimTemporalBoundary.usf","MainCS",SF_Compute);

FRaftSimTemporalBoundaryResult RaftSimSampleTemporalBoundaryGPU(FRDGBuilder& Graph,
    const FRaftSimTemporalBoundaryEndpoint& A,const FRaftSimTemporalBoundaryEndpoint& B,
    FRDGBufferRef Progress,FRDGBufferRef TrialInfo,FIntPoint Size,FString& Error)
{
    Error.Reset();FRaftSimTemporalBoundaryResult R;
    if(Size.X<1 || Size.Y<1 || Size.X>512 || Size.Y>512)
    {Error=TEXT("Temporal boundary requires a valid1..512 grid");return R;}
    const int32 N=2*(Size.X+Size.Y);
    auto Record=[](FRDGBufferRef P,uint32 Stride,int32 Count)
    {return P && P->Desc.BytesPerElement==Stride && P->Desc.NumElements==Count;};
    const double Span=B.Seconds-A.Seconds;const float Duration=float(Span),Hi=float(A.Seconds),Lo=float(A.Seconds-double(Hi));
    if(!FMath::IsFinite(A.Seconds) || !FMath::IsFinite(B.Seconds) ||
        !FMath::IsFinite(Duration) || Duration<=0 || !FMath::IsFinite(Hi) || !FMath::IsFinite(Lo) ||
        !Record(Progress,16,1) || (TrialInfo && !Record(TrialInfo,16,1)))
    {Error=TEXT("Temporal boundary requires finite increasing times, valid grid and compensated stage records");return R;}
    for(const auto* E:{&A,&B})if(!Record(E->State,16,N) || !Record(E->Bed,4,N) || !Record(E->FaceNormalVelocity,4,N))
    {Error=TEXT("Temporal boundary requires complete paired state, bed and independent face observations");return R;}
    auto Buffer=[&](uint32 Stride,uint32 Count,const TCHAR* Name)
    {auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,Count);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name);};
    R.Input.ExteriorState=Buffer(16,N,TEXT("TemporalBoundary.State"));R.Input.ExteriorBed=Buffer(4,N,TEXT("TemporalBoundary.Bed"));
    R.Input.FaceVelocity=Buffer(8,N,TEXT("TemporalBoundary.FaceTrace"));R.Diagnostics=Buffer(4,4,TEXT("TemporalBoundary.Diagnostics"));
    AddClearUAVPass(Graph,Graph.CreateUAV(R.Diagnostics),0u);
    auto* P=Graph.AllocParameters<FRaftSimTemporalBoundaryCS::FParameters>();P->Count=N;P->FirstTime=FVector2f(Hi,Lo);P->Duration=Duration;
    P->FirstState=Graph.CreateSRV(A.State);P->SecondState=Graph.CreateSRV(B.State);P->FirstBed=Graph.CreateSRV(A.Bed);P->SecondBed=Graph.CreateSRV(B.Bed);
    P->FirstVelocity=Graph.CreateSRV(A.FaceNormalVelocity);P->SecondVelocity=Graph.CreateSRV(B.FaceNormalVelocity);
    P->Progress=Graph.CreateSRV(Progress);P->TrialInfo=TrialInfo?Graph.CreateSRV(TrialInfo):nullptr;
    P->State=Graph.CreateUAV(R.Input.ExteriorState);P->Bed=Graph.CreateUAV(R.Input.ExteriorBed);
    P->FaceTrace=Graph.CreateUAV(R.Input.FaceVelocity);P->Diagnostics=Graph.CreateUAV(R.Diagnostics);
    FRaftSimTemporalBoundaryCS::FPermutationDomain Perm;Perm.Set<FRaftSimTemporalBoundaryCS::FSecondStage>(TrialInfo!=nullptr);
    TShaderMapRef<FRaftSimTemporalBoundaryCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Perm);ClearUnusedGraphResources(Shader,P);
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Temporal Boundary"),Shader,P,FIntVector(FMath::DivideAndRoundUp(N,256),1,1));
    return R;
}
