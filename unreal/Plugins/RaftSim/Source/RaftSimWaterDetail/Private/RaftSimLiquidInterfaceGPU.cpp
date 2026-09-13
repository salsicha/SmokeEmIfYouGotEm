#include "RaftSimLiquidInterfaceGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidInterfaceCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidInterfaceCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidInterfaceCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntVector,Size)
        SHADER_PARAMETER(FIntVector,UpdateMin)
        SHADER_PARAMETER(FIntVector,UpdateMax)
        SHADER_PARAMETER(FVector3f,CellCm)
        SHADER_PARAMETER(float,Dt)
        SHADER_PARAMETER(uint32,CompactTransport)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<float>,Source)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<float4>,Velocity)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture3D<float>,Result)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidInterfaceCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidInterface.usf","MainCS",SF_Compute);

FRaftSimLiquidInterfaceStep RaftSimAdvectLiquidInterface(FRDGBuilder& Graph,
    FRDGTextureRef Source,FRDGTextureRef Velocity,FVector3f CellCm,float Dt,
    FIntVector UpdateMin,FIntVector UpdateMax,FString& Error,bool CompactTransport)
{
    if(GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6 || !Source || !Velocity || Source==Velocity ||
        Source->Desc.Format!=PF_R32_FLOAT ||
        (Velocity->Desc.Format!=PF_FloatRGBA && Velocity->Desc.Format!=PF_A32B32G32R32F) ||
        CellCm.ContainsNaN() || CellCm.GetMin()<=0 || !FMath::IsFinite(Dt) || Dt<0)
    { Error=TEXT("Interface transport requires distinct typed scalar/velocity and finite positive metric");return {}; }
    const FIntVector Size(Source->Desc.Extent.X,Source->Desc.Extent.Y,Source->Desc.Depth);
    if(Size.GetMin()<2 || int64(Size.X)*Size.Y*Size.Z>4000000)
    { Error=TEXT("Interface grid exceeds validated allocation bounds");return {}; }
    for(const auto T:{Source,Velocity})
        if(T->Desc.Dimension!=ETextureDimension::Texture3D || T->Desc.Extent!=Source->Desc.Extent ||
            T->Desc.Depth!=Size.Z || !EnumHasAnyFlags(T->Desc.Flags,TexCreate_ShaderResource))
        { Error=TEXT("Interface transport requires matching untiled 3D source grids");return {}; }
    for(int32 A=0;A<3;++A)
        if(UpdateMin[A]<0 || UpdateMax[A]>Size[A] || UpdateMin[A]>=UpdateMax[A])
        { Error=TEXT("Invalid half-open interface update box");return {}; }
    FRaftSimLiquidInterfaceStep Out;
    Out.Scalar=Graph.CreateTexture(FRDGTextureDesc::Create3D(Size,PF_R32_FLOAT,FClearValueBinding::None,
        TexCreate_ShaderResource|TexCreate_UAV),TEXT("LiquidInterface.Advected"));
    auto DiagnosticDesc=FRDGBufferDesc::CreateStructuredDesc(sizeof(uint32),3);
    DiagnosticDesc.Usage|=BUF_SourceCopy;
    Out.Diagnostics=Graph.CreateBuffer(DiagnosticDesc,TEXT("LiquidInterface.Diagnostics"));
    AddClearUAVPass(Graph,Graph.CreateUAV(Out.Diagnostics),0u);
    auto* P=Graph.AllocParameters<FRaftSimLiquidInterfaceCS::FParameters>();
    P->Size=Size;P->UpdateMin=UpdateMin;P->UpdateMax=UpdateMax;P->CellCm=CellCm;P->Dt=Dt;
    P->CompactTransport=CompactTransport?1u:0u;
    P->Source=Graph.CreateSRV(Source);P->Velocity=Graph.CreateSRV(Velocity);
    P->Result=Graph.CreateUAV(Out.Scalar);P->Diagnostics=Graph.CreateUAV(Out.Diagnostics);
    TShaderMapRef<FRaftSimLiquidInterfaceCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Advect Explicit Liquid Interface RK2"),Shader,P,
        FComputeShaderUtils::GetGroupCount(Size,FIntVector(4,4,4)));
    Error.Reset();return Out;
}
