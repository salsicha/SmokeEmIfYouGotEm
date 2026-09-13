#include "RaftSimLiquidDensityGradientGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidDensityGradientCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidDensityGradientCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidDensityGradientCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Capacity)
        SHADER_PARAMETER(FIntVector,Cells)
        SHADER_PARAMETER(FVector3f,Spacing)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Positions)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,LiveCount)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,DensitySolid)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Gradient)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Diagonal)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidDensityGradientCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidDensityGradient.usf","MainCS",SF_Compute);

FRaftSimLiquidDensityGradient RaftSimLiquidDensityGradientGPU(FRDGBuilder& Graph,
    FRDGBufferRef Positions,FRDGBufferRef LiveCount,uint32 Capacity,FRDGBufferRef Field,
    FIntVector Cells,FVector3f Spacing,FString& Error)
{
    Error.Reset();const int64 XY=int64(Cells.X)*Cells.Y;
    const int64 Count=XY>0 && XY<=MAX_int32 && Cells.Z>=2 && Cells.Z<=MAX_int32/XY ? XY*Cells.Z:-1;
    if(!Positions || !LiveCount || !Field || Capacity==0 || Capacity>64u*65535u ||
        Cells.X<2 || Cells.Y<2 || Cells.Z<2 || Count<0 ||
        !FMath::IsFinite(Spacing.X) || !FMath::IsFinite(Spacing.Y) || !FMath::IsFinite(Spacing.Z) ||
        Spacing.X<=0 || Spacing.Y<=0 || Spacing.Z<=0 ||
        Positions->Desc.BytesPerElement!=16 || Positions->Desc.NumElements<Capacity ||
        LiveCount->Desc.BytesPerElement!=4 || LiveCount->Desc.NumElements<1 ||
        Field->Desc.BytesPerElement!=8 || Field->Desc.NumElements!=Count)
    { Error=TEXT("Complete finite density-gradient grid and native particle buffers required");return {}; }
    FRaftSimLiquidDensityGradient Result;
    auto VectorDesc=FRDGBufferDesc::CreateStructuredDesc(16,Capacity);VectorDesc.Usage|=BUF_SourceCopy;
    Result.Gradient=Graph.CreateBuffer(VectorDesc,TEXT("LiquidDensity.Gradient"));
    Result.Diagonal=Graph.CreateBuffer(VectorDesc,TEXT("LiquidDensity.Diagonal"));
    auto CountDesc=FRDGBufferDesc::CreateStructuredDesc(4,4);CountDesc.Usage|=BUF_SourceCopy;
    Result.Diagnostics=Graph.CreateBuffer(CountDesc,TEXT("LiquidDensity.Diagnostics"));
    AddClearUAVPass(Graph,Graph.CreateUAV(Result.Diagnostics),0);
    auto* P=Graph.AllocParameters<FRaftSimLiquidDensityGradientCS::FParameters>();
    P->Capacity=Capacity;P->Cells=Cells;P->Spacing=Spacing;
    P->Positions=Graph.CreateSRV(Positions);P->LiveCount=Graph.CreateSRV(LiveCount);P->DensitySolid=Graph.CreateSRV(Field);
    P->Gradient=Graph.CreateUAV(Result.Gradient);P->Diagonal=Graph.CreateUAV(Result.Diagonal);P->Diagnostics=Graph.CreateUAV(Result.Diagnostics);
    TShaderMapRef<FRaftSimLiquidDensityGradientCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Whole-Support Density Gradient"),Shader,P,
        FIntVector(FMath::DivideAndRoundUp(Capacity,64u),1,1));
    return Result;
}
