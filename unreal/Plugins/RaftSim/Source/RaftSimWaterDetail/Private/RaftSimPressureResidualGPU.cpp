#include "RaftSimPressureResidualGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimPressureResidualCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimPressureResidualCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimPressureResidualCS,FGlobalShader);
    class FPhase : SHADER_PERMUTATION_INT("RAFTSIM_RESIDUAL_PHASE",4);
    class FPhysical : SHADER_PERMUTATION_BOOL("RAFTSIM_RESIDUAL_PHYSICAL");
    using FPermutationDomain=TShaderPermutationDomain<FPhase,FPhysical>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Count)
        SHADER_PARAMETER(uint32,PartialCount)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,RHS)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Residual)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,Geometry)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Partial)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,Scale)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Norms)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5);}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimPressureResidualCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimPressureResidual.usf","MainCS",SF_Compute);

FRaftSimPressureResidualCheck RaftSimCheckPressureResidualGPU(FRDGBuilder& Graph,
    FRDGBufferRef RHS,FRDGBufferRef Residual,FIntPoint Size,FString& Error,FRDGBufferRef Geometry)
{
    FRaftSimPressureResidualCheck R;Error.Reset();
    if(Size.X<1 || Size.Y<1 || Size.X>512 || Size.Y>512)
    {Error=TEXT("Invalid pressure residual grid");return R;}
    const uint32 N=Size.X*Size.Y,Groups=FMath::DivideAndRoundUp(N,256u);
    if(!RHS || !Residual || RHS->Desc.NumElements!=N || Residual->Desc.NumElements!=N ||
        RHS->Desc.BytesPerElement!=16 || Residual->Desc.BytesPerElement!=16)
    {Error=TEXT("Residual check needs matching two-pole RHS and true residual");return R;}
    if(Geometry && (Geometry->Desc.NumElements!=N || Geometry->Desc.BytesPerElement!=8))
    {Error=TEXT("Physical residual check requires same-stage float2 geometry");return R;}
    auto Buffer=[&](uint32 Stride,uint32 Count,const TCHAR* Name)
    {auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,Count);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name);};
    auto Partial=Buffer(16,Groups,TEXT("PressureCheck.Partial"));auto Scale=Buffer(8,1,TEXT("PressureCheck.Scale"));
    R.Norms=Buffer(16,Geometry?2:1,TEXT("PressureCheck.Norms"));R.Diagnostics=Buffer(4,4,TEXT("PressureCheck.Diagnostics"));
    AddClearUAVPass(Graph,Graph.CreateUAV(R.Diagnostics),0u);
    for(int32 Physical=0;Physical<(Geometry?2:1);++Physical)
    for(int32 Phase=0;Phase<4;++Phase)
    {
        auto* P=Graph.AllocParameters<FRaftSimPressureResidualCS::FParameters>();P->Count=N;P->PartialCount=Groups;
        P->RHS=Graph.CreateSRV(RHS);P->Residual=Graph.CreateSRV(Residual);P->Partial=Graph.CreateUAV(Partial);
        P->Geometry=Geometry?Graph.CreateSRV(Geometry):nullptr;
        P->Scale=Graph.CreateUAV(Scale);P->Norms=Graph.CreateUAV(R.Norms);P->Diagnostics=Graph.CreateUAV(R.Diagnostics);
        FRaftSimPressureResidualCS::FPermutationDomain Perm;Perm.Set<FRaftSimPressureResidualCS::FPhase>(Phase);
        Perm.Set<FRaftSimPressureResidualCS::FPhysical>(Physical!=0);
        TShaderMapRef<FRaftSimPressureResidualCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Perm);ClearUnusedGraphResources(Shader,P);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Pressure Qualification Physical%d Phase%d",Physical,Phase),Shader,P,FIntVector(Phase%2==0?Groups:1,1,1));
    }
    return R;
}
