#include "RaftSimLiquidFoamGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"
#include "RHIStaticStates.h"

class FRaftSimLiquidFoamCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidFoamCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidFoamCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntVector,RenderSize)
        SHADER_PARAMETER(FIntVector,FlowSize)
        SHADER_PARAMETER(FVector3f,ExtentCm)
        SHADER_PARAMETER(FVector2f,PhysicalHalfExtentCm)
        SHADER_PARAMETER(float,SourceScale)
        SHADER_PARAMETER(float,DecayRate)
        SHADER_PARAMETER(uint32,HasHistory)
        SHADER_PARAMETER(uint32,ClockIndex)
        SHADER_PARAMETER_RDG_TEXTURE(Texture3D<float4>,CurrentSurface)
        SHADER_PARAMETER_RDG_TEXTURE(Texture3D<float4>,HistorySurface)
        SHADER_PARAMETER_RDG_TEXTURE(Texture3D<float4>,Velocity)
        SHADER_PARAMETER_RDG_TEXTURE(Texture3D<float4>,Boundary)
        SHADER_PARAMETER_SAMPLER(SamplerState,LinearClamp)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Clock)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture3D<float4>,OutputSurface)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Audit)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidFoamCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidFoam.usf","MainCS",SF_Compute);

FRaftSimLiquidFoamResult RaftSimLiquidFoamGPU(FRDGBuilder& Graph,FRDGTextureRef Current,
    FRDGTextureRef History,FRDGTextureRef Velocity,FRDGTextureRef Boundary,FRDGBufferRef Clock,uint32 ClockIndex,
    FVector3f ExtentCm,FVector2f PhysicalHalfExtentCm,float SourceScale,float DecayRate,FRDGBufferRef Diagnostics,FString& Error)
{
    auto Valid=[](FRDGTextureRef T){return T && T->Desc.Dimension==ETextureDimension::Texture3D && T->Desc.Format==PF_FloatRGBA;};
    if (!Valid(Current) || !Valid(Velocity) || !Valid(Boundary) || (History && !Valid(History)) ||
        !Clock || Clock->Desc.BytesPerElement!=sizeof(FVector4f) || ClockIndex>=Clock->Desc.NumElements ||
        !Diagnostics || Diagnostics->Desc.BytesPerElement!=4 || Diagnostics->Desc.NumElements!=4 ||
        ExtentCm.ContainsNaN() || ExtentCm.GetMin()<=0 || PhysicalHalfExtentCm.ContainsNaN() ||
        PhysicalHalfExtentCm.X<=0 || PhysicalHalfExtentCm.Y<=0 ||
        !FMath::IsFinite(SourceScale) || SourceScale<0 || SourceScale>8 || !FMath::IsFinite(DecayRate) || DecayRate<0 || DecayRate>8)
    { Error=TEXT("Invalid bounded live foam inputs");return {}; }
    const FIntVector R(Current->Desc.Extent.X,Current->Desc.Extent.Y,Current->Desc.Depth);
    const FIntVector V(Velocity->Desc.Extent.X,Velocity->Desc.Extent.Y,Velocity->Desc.Depth);
    if (V.GetMin()<3 || int64(R.X)*R.Y*R.Z>2000000 || R!=V*2 ||
        Boundary->Desc.Extent!=Velocity->Desc.Extent || Boundary->Desc.Depth!=Velocity->Desc.Depth ||
        (History && (History->Desc.Extent!=Current->Desc.Extent || History->Desc.Depth!=Current->Desc.Depth)))
    { Error=TEXT("Live foam requires aligned 2x render/solver domains");return {}; }
    auto Desc=Current->Desc;Desc.Flags|=TexCreate_UAV|TexCreate_ShaderResource;
    auto Output=Graph.CreateTexture(Desc,TEXT("LiquidFoam.CurrentSurface"));
    auto AuditDesc=FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f),R.X*R.Y*R.Z);AuditDesc.Usage|=BUF_SourceCopy;
    auto Audit=Graph.CreateBuffer(AuditDesc,TEXT("LiquidFoam.Audit"));
    auto* P=Graph.AllocParameters<FRaftSimLiquidFoamCS::FParameters>();
    P->RenderSize=R;P->FlowSize=V;P->ExtentCm=ExtentCm;P->PhysicalHalfExtentCm=PhysicalHalfExtentCm;
    P->SourceScale=SourceScale;P->DecayRate=DecayRate;P->HasHistory=History!=nullptr;P->ClockIndex=ClockIndex;
    P->CurrentSurface=Current;P->HistorySurface=History?History:Current;P->Velocity=Velocity;P->Boundary=Boundary;
    P->LinearClamp=TStaticSamplerState<SF_Bilinear,AM_Clamp,AM_Clamp,AM_Clamp>::GetRHI();
    P->Clock=Graph.CreateSRV(Clock);P->OutputSurface=Graph.CreateUAV(Output);
    P->Audit=Graph.CreateUAV(Audit);P->Diagnostics=Graph.CreateUAV(Diagnostics);
    TShaderMapRef<FRaftSimLiquidFoamCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Current Surface Foam"),Shader,P,
        FIntVector(FMath::DivideAndRoundUp(R.X,8),FMath::DivideAndRoundUp(R.Y,4),FMath::DivideAndRoundUp(R.Z,4)));
    return {Output,Audit};
}
