#include "RaftSimLiquidInterfaceHighOrderGPU.h"
#include "RaftSimLiquidHaloGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidInterfaceHighOrderCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidInterfaceHighOrderCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidInterfaceHighOrderCS,FGlobalShader);
    class FNativeBoundary : SHADER_PERMUTATION_BOOL("RAFTSIM_HIGHORDER_NATIVE_BOUNDARY");
    using FPermutationDomain=TShaderPermutationDomain<FNativeBoundary>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntVector,Size)
        SHADER_PARAMETER(FIntVector,UpdateMin)
        SHADER_PARAMETER(FIntVector,UpdateMax)
        SHADER_PARAMETER(FVector3f,CellCm)
        SHADER_PARAMETER(float,Dt)
        SHADER_PARAMETER(uint32,CompactTransport)
        SHADER_PARAMETER(uint32,Stage)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<float>,Source)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<float4>,Velocity)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<float>,Auxiliary)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<float>,Forward)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<float>,InputValid)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<float>,AuxiliaryValid)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<uint>,Solid)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<float4>,NativeBoundary)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture3D<float>,Result)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture3D<float>,ResultValid)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidInterfaceHighOrderCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidInterfaceHighOrder.usf","HighOrderCS",SF_Compute);

namespace
{
bool Validate(FRDGTextureRef Source,FRDGTextureRef Velocity,FRDGTextureRef Solid,FVector3f CellCm,float Dt,
    FIntVector UpdateMin,FIntVector UpdateMax,FString& Error)
{
    Error.Reset();
    if(GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6 || !Source || !Velocity || !Solid ||
        Source==Velocity || Source==Solid || Velocity==Solid || Source->Desc.Format!=PF_R32_FLOAT ||
        (Velocity->Desc.Format!=PF_FloatRGBA && Velocity->Desc.Format!=PF_A32B32G32R32F) ||
        (Solid->Desc.Format!=PF_R32_UINT && Solid->Desc.Format!=PF_FloatRGBA) || !FMath::IsFinite(CellCm.X) || !FMath::IsFinite(CellCm.Y) ||
        !FMath::IsFinite(CellCm.Z) || CellCm.GetMin()<=0 || !FMath::IsFinite(Dt) || Dt<0)
    { Error=TEXT("High-order interface requires distinct typed grids, finite metric and nonnegative timestep");return false; }
    const FIntVector Size(Source->Desc.Extent.X,Source->Desc.Extent.Y,Source->Desc.Depth);
    if(Size.GetMin()<2 || Size.GetMax()>4000000 || int64(Size.X)*Size.Y>4000000 ||
        int64(Size.X)*Size.Y*Size.Z>4000000)
    { Error=TEXT("High-order interface exceeds validated grid bounds");return false; }
    for(auto T:{Source,Velocity,Solid})
        if(T->Desc.Dimension!=ETextureDimension::Texture3D || T->Desc.Extent!=Source->Desc.Extent || T->Desc.Depth!=Size.Z ||
            !EnumHasAnyFlags(T->Desc.Flags,TexCreate_ShaderResource))
        { Error=TEXT("Matching untiled 3D high-order source grids required");return false; }
    for(int A=0;A<3;++A) if(UpdateMin[A]<0 || UpdateMax[A]>Size[A] || UpdateMin[A]>=UpdateMax[A])
    { Error=TEXT("Invalid high-order owned update box");return false; }
    return true;
}
struct FWork
{
    FRaftSimLiquidInterfaceHighOrderStep Out;
    FRDGTextureRef Fields[5]{},Valid[5]{};
};
void Initialize(FRDGBuilder& Graph,FWork& Work)
{
    auto Desc=FRDGBufferDesc::CreateStructuredDesc(4,8);Desc.Usage|=BUF_SourceCopy;
    Work.Out.Diagnostics=Graph.CreateBuffer(Desc,TEXT("LiquidHighOrder.Diagnostics"));
    AddClearUAVPass(Graph,Graph.CreateUAV(Work.Out.Diagnostics),0u);
}
void Dispatch(FRDGBuilder& Graph,const FRaftSimLiquidInterfaceHighOrderRegion& Region,FWork& Work,
    FVector3f CellCm,float Dt,FIntVector UpdateMin,FIntVector UpdateMax,int Stage,bool CompactTransport)
{
    const auto Source=Region.Source,Velocity=Region.Velocity,Solid=Region.Solid;
    const FIntVector Size(Source->Desc.Extent.X,Source->Desc.Extent.Y,Source->Desc.Depth);
    auto& Fields=Work.Fields;auto& Valid=Work.Valid;
        Fields[Stage]=Graph.CreateTexture(FRDGTextureDesc::Create3D(Size,PF_R32_FLOAT,FClearValueBinding::None,
            TexCreate_ShaderResource|TexCreate_UAV),TEXT("LiquidHighOrder.Scalar"));
        Valid[Stage]=Graph.CreateTexture(FRDGTextureDesc::Create3D(Size,PF_R32_FLOAT,FClearValueBinding::None,
            TexCreate_ShaderResource|TexCreate_UAV),TEXT("LiquidHighOrder.Valid"));
        auto* P=Graph.AllocParameters<FRaftSimLiquidInterfaceHighOrderCS::FParameters>();
        P->Size=Size;P->UpdateMin=UpdateMin;P->UpdateMax=UpdateMax;P->CellCm=CellCm;P->Dt=Dt;P->Stage=Stage;
        P->CompactTransport=CompactTransport?1u:0u;
        P->Source=Graph.CreateSRV(Stage==1?Fields[0]:Stage==3?Fields[2]:Source);
        const bool Native=Solid->Desc.Format==PF_FloatRGBA;
        P->Velocity=Graph.CreateSRV(Velocity);
        P->Solid=Native?nullptr:Graph.CreateSRV(Solid);
        P->NativeBoundary=Native?Graph.CreateSRV(Solid):nullptr;
        P->Auxiliary=Graph.CreateSRV(Stage==2?Fields[1]:Stage==4?Fields[3]:Source);
        P->Forward=Graph.CreateSRV(Stage>0?Fields[0]:Source);
        P->InputValid=Graph.CreateSRV(Stage>0?Valid[0]:Source);
        P->AuxiliaryValid=Graph.CreateSRV(Stage==2?Valid[1]:Stage==4?Valid[2]:Source);
        P->Result=Graph.CreateUAV(Fields[Stage]);P->ResultValid=Graph.CreateUAV(Valid[Stage]);
        P->Diagnostics=Graph.CreateUAV(Work.Out.Diagnostics);
        FRaftSimLiquidInterfaceHighOrderCS::FPermutationDomain Permutation;
        Permutation.Set<FRaftSimLiquidInterfaceHighOrderCS::FNativeBoundary>(Native);
        TShaderMapRef<FRaftSimLiquidInterfaceHighOrderCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Limited BFECC Stage %d",Stage),Shader,P,
            FComputeShaderUtils::GetGroupCount(Size,FIntVector(4,4,4)));
}
}

FRaftSimLiquidInterfaceHighOrderStep RaftSimAdvectLiquidInterfaceHighOrder(FRDGBuilder& Graph,
    FRDGTextureRef Source,FRDGTextureRef Velocity,FRDGTextureRef Solid,FVector3f CellCm,float Dt,
    FIntVector UpdateMin,FIntVector UpdateMax,FString& Error,bool CompactTransport)
{
    if(!Validate(Source,Velocity,Solid,CellCm,Dt,UpdateMin,UpdateMax,Error)) return {};
    FWork Work;Initialize(Graph,Work);
    for(int Stage=0;Stage<5;++Stage)
        Dispatch(Graph,{Source,Velocity,Solid},Work,CellCm,Dt,UpdateMin,UpdateMax,Stage,CompactTransport);
    Work.Out.Scalar=Work.Fields[4];return Work.Out;
}

TArray<FRaftSimLiquidInterfaceHighOrderStep> RaftSimAdvectLiquidInterfaceHighOrderRegions(
    FRDGBuilder& Graph,const FRaftSimLiquidHaloPlan& Halo,
    TConstArrayView<FRaftSimLiquidInterfaceHighOrderRegion> Regions,
    FVector3f CellCm,float Dt,FString& Error,bool CompactTransport)
{
    Error.Reset();
    if(!Halo.Columns || !Halo.Count || Regions.Num()<2 || Regions.Num()>16 || Regions.Num()!=Halo.Sizes.Num())
    { Error=TEXT("High-order regions require a same-graph bounded owner halo plan");return {}; }
    TSet<FRDGTextureRef> Unique;
    for(int I=0;I<Regions.Num();++I)
    {
        const auto& R=Regions[I];const auto Size=Halo.Sizes[I];
        if(!Validate(R.Source,R.Velocity,R.Solid,CellCm,Dt,FIntVector(2),Size-FIntVector(2),Error)) return {};
        if(R.Source->Desc.Extent!=FIntPoint(Size.X,Size.Y) || R.Source->Desc.Depth!=Size.Z)
        { Error=TEXT("High-order owner dimensions do not match halo plan");return {}; }
        for(auto T:{R.Source,R.Velocity,R.Solid})
        {
            if(Unique.Contains(T)) { Error=TEXT("High-order owner inputs must not alias");return {}; }
            Unique.Add(T);
        }
    }
    TArray<FWork> Work;Work.SetNum(Regions.Num());
    for(auto& W:Work) Initialize(Graph,W);
    for(int Stage=0;Stage<5;++Stage)
    {
        for(int I=0;I<Regions.Num();++I)
            Dispatch(Graph,Regions[I],Work[I],CellCm,Dt,FIntVector(2),Halo.Sizes[I]-FIntVector(2),Stage,CompactTransport);
        // Stage 3 is only read at the same cell by the limiter. Other scalar
        // stages feed neighbor stencils; their validity must travel with them.
        if(Stage!=3)
        {
            TArray<FRDGTextureRef> Fields,Valid;
            for(auto& W:Work) { Fields.Add(W.Fields[Stage]);Valid.Add(W.Valid[Stage]); }
            if(!RaftSimExchangeLiquidPressureHalo(Graph,Halo,Fields,Error)) return {};
            if(Stage<3 && !RaftSimExchangeLiquidPressureHalo(Graph,Halo,Valid,Error)) return {};
        }
    }
    TArray<FRaftSimLiquidInterfaceHighOrderStep> Result;
    for(auto& W:Work) { W.Out.Scalar=W.Fields[4];Result.Add(W.Out); }
    return Result;
}
