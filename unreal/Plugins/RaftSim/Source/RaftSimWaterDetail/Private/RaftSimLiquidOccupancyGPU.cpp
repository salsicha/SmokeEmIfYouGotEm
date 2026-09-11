#include "RaftSimLiquidDensityGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidOccupancyCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidOccupancyCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidOccupancyCS,FGlobalShader);
    class FStage : SHADER_PERMUTATION_INT("RAFTSIM_OCCUPANCY_STAGE",2);
    using FPermutationDomain=TShaderPermutationDomain<FStage>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntVector,SolverSize)
        SHADER_PARAMETER(FIntVector,RenderSize)
        SHADER_PARAMETER_RDG_TEXTURE(Texture3D<float4>,Boundary)
        SHADER_PARAMETER_RDG_TEXTURE(Texture3D<float>,SourceScalar)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture3D<float>,Core)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture3D<float>,OutputScalar)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,Audit)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidOccupancyCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidOccupancy.usf","MainCS",SF_Compute);

FRaftSimLiquidOccupancyResult RaftSimLiquidOccupancyGPU(FRDGBuilder& Graph,
    FRDGTextureRef Scalar,FRDGTextureRef Boundary,FRDGBufferRef Diagnostics,FString& Error)
{
    if (!Scalar || !Boundary || !Diagnostics || Scalar==Boundary ||
        Scalar->Desc.Dimension!=ETextureDimension::Texture3D || Boundary->Desc.Dimension!=ETextureDimension::Texture3D ||
        Scalar->Desc.Format!=PF_R32_FLOAT || Boundary->Desc.Format!=PF_FloatRGBA ||
        Diagnostics->Desc.BytesPerElement!=sizeof(uint32) || Diagnostics->Desc.NumElements!=4)
    { Error=TEXT("Invalid occupancy textures or diagnostic buffer");return {}; }
    const FIntVector Solver(Boundary->Desc.Extent.X,Boundary->Desc.Extent.Y,Boundary->Desc.Depth);
    const FIntVector Render(Scalar->Desc.Extent.X,Scalar->Desc.Extent.Y,Scalar->Desc.Depth);
    if (Solver.GetMin()<3 || int64(Render.X)*Render.Y*Render.Z>2000000 ||
        !((Render==Solver) || (Render==Solver*2) || (Render==Solver*4)))
    { Error=TEXT("Occupancy requires uniform 1x/2x/4x registered refinement");return {}; }
    auto Core=Graph.CreateTexture(FRDGTextureDesc::Create3D(Solver,PF_R32_FLOAT,FClearValueBinding::None,TexCreate_ShaderResource|TexCreate_UAV),TEXT("LiquidOccupancy.Core"));
    auto OutputDesc=Scalar->Desc;OutputDesc.Flags|=TexCreate_ShaderResource|TexCreate_UAV;
    auto Output=Graph.CreateTexture(OutputDesc,TEXT("LiquidOccupancy.Scalar"));
    auto AuditDesc=FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector2f),Render.X*Render.Y*Render.Z);AuditDesc.Usage|=BUF_SourceCopy;
    auto Audit=Graph.CreateBuffer(AuditDesc,TEXT("LiquidOccupancy.Audit"));
    for (int32 Stage=0;Stage<2;++Stage)
    {
        auto* P=Graph.AllocParameters<FRaftSimLiquidOccupancyCS::FParameters>();
        P->SolverSize=Solver;P->RenderSize=Render;P->Boundary=Boundary;P->SourceScalar=Scalar;
        P->Core=Graph.CreateUAV(Core);P->OutputScalar=Graph.CreateUAV(Output);
        P->Audit=Graph.CreateUAV(Audit);P->Diagnostics=Graph.CreateUAV(Diagnostics);
        FRaftSimLiquidOccupancyCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimLiquidOccupancyCS::FStage>(Stage);
        TShaderMapRef<FRaftSimLiquidOccupancyCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
        ClearUnusedGraphResources(Shader,P);
        const FIntVector Size=Stage==0?Solver:Render;
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Liquid Occupancy Stage%d",Stage),Shader,P,
            FIntVector(FMath::DivideAndRoundUp(uint32(Size.X*Size.Y*Size.Z),64u),1,1));
    }
    return {Output,Audit};
}
