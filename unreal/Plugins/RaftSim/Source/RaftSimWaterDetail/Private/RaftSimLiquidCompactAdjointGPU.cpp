#include "RaftSimLiquidCompactAdjointGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidCompactAdjointCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidCompactAdjointCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidCompactAdjointCS,FGlobalShader);
    class FStage : SHADER_PERMUTATION_INT("STAGE",2);
    using FPermutationDomain=TShaderPermutationDomain<FStage>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Capacity)
        SHADER_PARAMETER(uint32,NodeCount)
        SHADER_PARAMETER(FIntVector,Cells)
        SHADER_PARAMETER(FVector3f,Spacing)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Positions)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,ParticleGradient)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,LiveCount)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Mobility)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Heads)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Next)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Field)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidCompactAdjointCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidCompactAdjoint.usf","MainCS",SF_Compute);

FRaftSimLiquidCompactAdjoint RaftSimLiquidCompactAdjointGPU(FRDGBuilder& Graph,
    FRDGBufferRef Positions,FRDGBufferRef ParticleGradient,FRDGBufferRef LiveCount,uint32 Capacity,
    FRDGBufferRef Mobility,FIntVector Cells,FVector3f Spacing,FString& Error)
{
    Error.Reset();const int64 XY=int64(Cells.X)*Cells.Y;
    const int64 Nodes=XY>0 && XY<=MAX_int32 && Cells.Z>=4 && Cells.Z<=MAX_int32/XY?XY*Cells.Z:-1;
    if(!Positions || !ParticleGradient || !LiveCount || !Mobility || Capacity==0 || Capacity>64u*65535u ||
        Cells.X<4 || Cells.Y<4 || Cells.Z<4 || Nodes<0 || Nodes>64u*65535u ||
        !FMath::IsFinite(Spacing.X) || !FMath::IsFinite(Spacing.Y) || !FMath::IsFinite(Spacing.Z) ||
        Spacing.X<=0 || Spacing.Y<=0 || Spacing.Z<=0 ||
        Positions->Desc.BytesPerElement!=16 || Positions->Desc.NumElements<Capacity ||
        ParticleGradient->Desc.BytesPerElement!=16 || ParticleGradient->Desc.NumElements<Capacity ||
        LiveCount->Desc.BytesPerElement!=4 || LiveCount->Desc.NumElements<1 ||
        Mobility->Desc.BytesPerElement!=4 || Mobility->Desc.NumElements!=Nodes)
    { Error=TEXT("Complete finite compact-adjoint grid, typed particle buffers and mobility required");return {}; }
    FRaftSimLiquidCompactAdjoint Result;
    auto V=FRDGBufferDesc::CreateStructuredDesc(16,uint32(Nodes));V.Usage|=BUF_SourceCopy;
    Result.Field=Graph.CreateBuffer(V,TEXT("LiquidAdjoint.Field"));
    auto D=FRDGBufferDesc::CreateStructuredDesc(4,6);D.Usage|=BUF_SourceCopy;
    Result.Diagnostics=Graph.CreateBuffer(D,TEXT("LiquidAdjoint.Diagnostics"));
    auto Heads=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(4,uint32(Nodes)),TEXT("LiquidAdjoint.Heads"));
    auto Next=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(4,Capacity),TEXT("LiquidAdjoint.Next"));
    AddClearUAVPass(Graph,Graph.CreateUAV(Result.Diagnostics),0);
    AddClearUAVPass(Graph,Graph.CreateUAV(Heads),MAX_uint32);
    for(int32 Stage=0;Stage<2;++Stage)
    {
        auto* P=Graph.AllocParameters<FRaftSimLiquidCompactAdjointCS::FParameters>();
        P->Capacity=Capacity;P->NodeCount=uint32(Nodes);P->Cells=Cells;P->Spacing=Spacing;
        P->Positions=Graph.CreateSRV(Positions);P->ParticleGradient=Graph.CreateSRV(ParticleGradient);
        P->LiveCount=Graph.CreateSRV(LiveCount);P->Mobility=Graph.CreateSRV(Mobility);
        P->Heads=Graph.CreateUAV(Heads);P->Next=Graph.CreateUAV(Next);P->Field=Graph.CreateUAV(Result.Field);
        P->Diagnostics=Graph.CreateUAV(Result.Diagnostics);
        FRaftSimLiquidCompactAdjointCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimLiquidCompactAdjointCS::FStage>(Stage);
        TShaderMapRef<FRaftSimLiquidCompactAdjointCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
        ClearUnusedGraphResources(Shader,P);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Compact Adjoint %s",Stage==0?TEXT("Bins"):TEXT("Gather")),Shader,P,
            FIntVector(FMath::DivideAndRoundUp(Stage==0?Capacity:uint32(Nodes),64u),1,1));
    }
    return Result;
}
