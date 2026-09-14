#include "RaftSimTotalDepthIntervalGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimTotalDepthIntervalCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimTotalDepthIntervalCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimTotalDepthIntervalCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FVector2f,FirstTime)
        SHADER_PARAMETER(float,Duration)
        SHADER_PARAMETER(uint32,BoundaryMode)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,PreviousProgress)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,PreviousSummary)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,PreviousDiagnostics)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,NextProgress)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,NextSummary)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,NextDiagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5);}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimTotalDepthIntervalCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimTotalDepthInterval.usf","MainCS",SF_Compute);

FRaftSimTotalDepthAdvanceResult RaftSimBeginNextTotalDepthIntervalGPU(FRDGBuilder& Graph,
    const FRaftSimTotalDepthAdvanceResult& Previous,FIntPoint Size,double FirstSeconds,double SecondSeconds,FString& Error,bool bContinuousShoreline,bool bUnscaledShoreline)
{
    Error.Reset();
    if(bContinuousShoreline && bUnscaledShoreline)
    {Error=TEXT("Interval shoreline models are mutually exclusive");return {};}
    auto Record=[](FRDGBufferRef B,uint32 Stride,uint32 Count)
    {return B && B->Desc.BytesPerElement==Stride && B->Desc.NumElements==Count;};
    const double Span=SecondSeconds-FirstSeconds;
    const float Duration=float(Span),Hi=float(FirstSeconds),Lo=float(FirstSeconds-double(Hi));
    if(Size.X<1 || Size.Y<1 || Size.X>512 || Size.Y>512 ||
        !FMath::IsFinite(FirstSeconds) || !FMath::IsFinite(SecondSeconds) ||
        !FMath::IsFinite(Duration) || Duration<=0 || double(Duration)!=Span ||
        !FMath::IsFinite(Hi) || !FMath::IsFinite(Lo) || double(Hi)+double(Lo)!=FirstSeconds ||
        !Record(Previous.State,16,uint32(Size.X)*Size.Y) || !Record(Previous.Progress,16,1) ||
        !Record(Previous.Summary,4,4) || !Record(Previous.Diagnostics,4,4) ||
        (Previous.BoundaryVolume && !Record(Previous.BoundaryVolume,16,2*(Size.X+Size.Y))))
    {Error=TEXT("Next interval requires complete retained records and exactly representable increasing times");return {};}
    auto R=Previous;
    auto Buffer=[&](uint32 Stride,uint32 Count,const TCHAR* Name)
    {auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,Count);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name);};
    R.Progress=Buffer(16,1,TEXT("NextInterval.Progress"));R.Summary=Buffer(4,4,TEXT("NextInterval.Summary"));
    R.Diagnostics=Buffer(4,4,TEXT("NextInterval.Diagnostics"));
    auto* P=Graph.AllocParameters<FRaftSimTotalDepthIntervalCS::FParameters>();
    P->FirstTime=FVector2f(Hi,Lo);P->Duration=Duration;
    P->BoundaryMode=RaftSimTotalDepthEvolutionMode(bool(Previous.BoundaryVolume),bContinuousShoreline,bUnscaledShoreline);
    P->PreviousProgress=Graph.CreateSRV(Previous.Progress);P->PreviousSummary=Graph.CreateSRV(Previous.Summary);
    P->PreviousDiagnostics=Graph.CreateSRV(Previous.Diagnostics);P->NextProgress=Graph.CreateUAV(R.Progress);
    P->NextSummary=Graph.CreateUAV(R.Summary);P->NextDiagnostics=Graph.CreateUAV(R.Diagnostics);
    TShaderMapRef<FRaftSimTotalDepthIntervalCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Admit Consecutive Interval"),Shader,P,FIntVector(1,1,1));
    return R;
}
