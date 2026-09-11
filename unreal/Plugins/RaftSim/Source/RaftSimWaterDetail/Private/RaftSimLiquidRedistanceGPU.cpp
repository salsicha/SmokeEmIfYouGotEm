#include "RaftSimLiquidRedistanceGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidRedistanceCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidRedistanceCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidRedistanceCS,FGlobalShader);
    class FStage : SHADER_PERMUTATION_INT("RAFTSIM_REDISTANCE_STAGE",3);
    using FPermutationDomain=TShaderPermutationDomain<FStage>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntVector,GridSize)
        SHADER_PARAMETER(FVector3f,CellCm)
        SHADER_PARAMETER(float,BandwidthCm)
        SHADER_PARAMETER_RDG_TEXTURE(Texture3D<float4>,SourceScalar)
        SHADER_PARAMETER_RDG_TEXTURE(Texture3D<float4>,CoverageSource)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,SeedDistance)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,PreviousDistance)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float>,NextDistance)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture3D<float4>,SurfaceOutput)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidRedistanceCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidRedistance.usf","MainCS",SF_Compute);

bool RaftSimLiquidRedistanceRDG(FRDGBuilder& Graph,FRDGTextureRef Source,FRDGTextureRef Target,
    FIntVector Size,FVector3f CellCm,float BandwidthCm,int32 Iterations,FString& Error,FRDGTextureRef CoverageSource)
{
    check(IsInRenderingThread());
    if (!Source || !Target || Source==Target || CoverageSource==Target || Size.GetMin()<2 || int64(Size.X)*Size.Y*Size.Z>2000000 ||
        !FMath::IsFinite(CellCm.X) || !FMath::IsFinite(CellCm.Y) || !FMath::IsFinite(CellCm.Z) || CellCm.GetMin()<=0 ||
        !FMath::IsFinite(BandwidthCm) || BandwidthCm<=CellCm.GetMax() || BandwidthCm>8*CellCm.GetMin() ||
        Iterations<1 || Iterations>32)
    { Error=TEXT("Invalid bounded metric redistance configuration");return false; }
    const auto& A=Source->Desc;const auto& B=Target->Desc;
    if (A.Extent!=FIntPoint(Size.X,Size.Y) || B.Extent!=A.Extent || A.Depth!=Size.Z || B.Depth!=Size.Z ||
        (A.Format!=PF_R32_FLOAT && A.Format!=PF_R16F && A.Format!=PF_FloatRGBA && A.Format!=PF_A32B32G32R32F) ||
        B.Format!=PF_FloatRGBA || !EnumHasAnyFlags(B.Flags,TexCreate_UAV))
    { Error=TEXT("Redistance requires matching floating-point 3D source and RGBA16f UAV target");return false; }
    if (CoverageSource && (CoverageSource->Desc.Extent!=A.Extent || CoverageSource->Desc.Depth!=A.Depth))
    { Error=TEXT("Coverage must share the same registered reconstruction domain");return false; }
    auto Input=Source;auto Output=Target;
    const int32 Count=Size.X*Size.Y*Size.Z;
    auto Seed=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(sizeof(float),Count),TEXT("RaftSim.Liquid.DistanceSeeds"));
    auto Ping=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(sizeof(float),Count),TEXT("RaftSim.Liquid.DistancePing"));
    auto Pong=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(sizeof(float),Count),TEXT("RaftSim.Liquid.DistancePong"));
    const FIntVector Groups(FMath::DivideAndRoundUp(Size.X,8),FMath::DivideAndRoundUp(Size.Y,4),FMath::DivideAndRoundUp(Size.Z,4));
    auto Dispatch=[&](int32 Stage,FRDGBufferRef Previous,FRDGBufferRef Next,int32 Iteration)
    {
        auto* P=Graph.AllocParameters<FRaftSimLiquidRedistanceCS::FParameters>();
        P->GridSize=Size;P->CellCm=CellCm;P->BandwidthCm=BandwidthCm;P->SourceScalar=Input;
        P->CoverageSource=CoverageSource?CoverageSource:Input;
        P->SeedDistance=Graph.CreateSRV(Seed);P->PreviousDistance=Graph.CreateSRV(Previous);
        P->NextDistance=Graph.CreateUAV(Next);P->SurfaceOutput=Graph.CreateUAV(Output);
        FRaftSimLiquidRedistanceCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimLiquidRedistanceCS::FStage>(Stage);
        TShaderMapRef<FRaftSimLiquidRedistanceCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
        ClearUnusedGraphResources(Shader,P);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Liquid Redistance Stage%d Iteration%d",Stage,Iteration),Shader,P,Groups);
    };
    Dispatch(0,Seed,Seed,0);
    FRDGBufferRef Previous=Seed;
    for (int32 I=0;I<Iterations;++I)
    {
        FRDGBufferRef Next=(I%2)==0?Ping:Pong;
        Dispatch(1,Previous,Next,I);Previous=Next;
    }
    Dispatch(2,Previous,Ping,0);
    return true;
}

bool RaftSimLiquidRedistanceGPU(FRHICommandListImmediate& Cmd,FRHITexture* Source,FRHITexture* Target,
    FIntVector Size,FVector3f CellCm,float BandwidthCm,int32 Iterations,FString& Error)
{
    if (!Source || !Target || Source==Target) { Error=TEXT("Distinct valid distance textures required");return false; }
    FRDGBuilder Graph(Cmd);
    auto Input=Graph.RegisterExternalTexture(CreateRenderTarget(Source,TEXT("RaftSim.Liquid.ScalarSource")));
    auto Output=Graph.RegisterExternalTexture(CreateRenderTarget(Target,TEXT("RaftSim.Liquid.DistanceTarget")));
    if (!RaftSimLiquidRedistanceRDG(Graph,Input,Output,Size,CellCm,BandwidthCm,Iterations,Error)) return false;
    Graph.Execute();return true;
}
