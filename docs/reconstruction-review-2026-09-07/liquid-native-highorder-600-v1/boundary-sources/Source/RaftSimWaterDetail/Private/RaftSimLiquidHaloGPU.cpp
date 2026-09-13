#include "RaftSimLiquidHaloGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidHaloCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidHaloCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidHaloCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,ColumnCount)
        SHADER_PARAMETER(uint32,Depth)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint4>,Columns)
        SHADER_PARAMETER_RDG_TEXTURE_UAV_ARRAY(RWTexture3D<float>,Grids,[16])
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidHaloCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidHalo.usf","MainCS",SF_Compute);

class FRaftSimLiquidBoundaryHaloCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidBoundaryHaloCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidBoundaryHaloCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,ColumnCount)
        SHADER_PARAMETER(uint32,Depth)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint4>,Columns)
        SHADER_PARAMETER_RDG_TEXTURE_UAV_ARRAY(RWTexture3D<float4>,Grids,[16])
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6); }
    static void ModifyCompilationEnvironment(const FGlobalShaderPermutationParameters& P,FShaderCompilerEnvironment& Out)
    { FGlobalShader::ModifyCompilationEnvironment(P,Out);Out.SetDefine(TEXT("RAFTSIM_HALO_VECTOR"),1); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidBoundaryHaloCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidHalo.usf","MainCS",SF_Compute);

FRaftSimLiquidHaloPlan RaftSimBuildLiquidHaloPlan(FRDGBuilder& Graph,TConstArrayView<FIntVector> Sizes,
    TConstArrayView<FRaftSimLiquidHaloColumn> Columns,FString& Error)
{
    auto Fail=[&](const TCHAR* Message) { Error=Message;return FRaftSimLiquidHaloPlan{}; };
    if (Sizes.Num()<2 || Sizes.Num()>16 || Columns.IsEmpty() || Columns.Num()>200000)
        return Fail(TEXT("Bounded multi-owner halo map required"));
    for (const auto S:Sizes)
        if (S.X<6 || S.Y<6 || S.Z<4 || S.X>4096 || S.Y>4096 || S.Z>4096 ||
            int64(S.X)*S.Y*S.Z>2000000 || S.Z!=Sizes[0].Z)
            return Fail(TEXT("Compatible bounded grid sizes required"));
    auto Physical=[](FIntPoint P,FIntVector S) { return P.X>=2 && P.Y>=2 && P.X<S.X-2 && P.Y<S.Y-2; };
    TSet<uint64> Written;TArray<FUintVector4> Packed;Packed.Reserve(Columns.Num()*2);
    for (const auto& C:Columns)
    {
        if (C.SourceOwner<0 || C.SourceOwner>=Sizes.Num() || C.DestinationOwner<0 || C.DestinationOwner>=Sizes.Num() ||
            C.SourceOwner==C.DestinationOwner) return Fail(TEXT("Distinct valid physical owners required"));
        const auto SS=Sizes[C.SourceOwner],DS=Sizes[C.DestinationOwner];
        if (!Physical(C.Source,SS) || C.Destination.X<0 || C.Destination.Y<0 ||
            C.Destination.X>=DS.X || C.Destination.Y>=DS.Y || Physical(C.Destination,DS))
            return Fail(TEXT("Exchange must read physical cells and write only halo cells"));
        const uint64 Key=(uint64(C.DestinationOwner)<<32)|uint32(C.Destination.Y*DS.X+C.Destination.X);
        if (Written.Contains(Key)) return Fail(TEXT("Duplicate halo destination would race"));
        Written.Add(Key);
        Packed.Emplace(C.SourceOwner,C.Source.X,C.Source.Y,0);
        Packed.Emplace(C.DestinationOwner,C.Destination.X,C.Destination.Y,0);
    }
    FRaftSimLiquidHaloPlan Plan;Plan.Sizes.Append(Sizes.GetData(),Sizes.Num());Plan.Count=Columns.Num();
    Plan.Columns=CreateStructuredBuffer(Graph,TEXT("LiquidHalo.PhysicalOwnerColumns"),TConstArrayView<FUintVector4>(Packed));
    return Plan;
}

namespace
{
bool ValidateHaloGrids(const FRaftSimLiquidHaloPlan& Plan,TConstArrayView<FRDGTextureRef> Grids,
    EPixelFormat Format,FString& Error)
{
    if (GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6 || !Plan.Columns || !Plan.Count ||
        Grids.Num()!=Plan.Sizes.Num() || Grids.Num()<2 || Grids.Num()>16)
    { Error=TEXT("Validated same-graph multi-owner halo plan and SM6 required");return false; }
    TSet<FRDGTextureRef> Unique;
    for (int32 I=0;I<Grids.Num();++I)
    {
        const auto T=Grids[I];const auto S=Plan.Sizes[I];
        if (!T || T->Desc.Dimension!=ETextureDimension::Texture3D || T->Desc.Format!=Format ||
            !EnumHasAnyFlags(T->Desc.Flags,TexCreate_UAV) || T->Desc.Extent!=FIntPoint(S.X,S.Y) || T->Desc.Depth!=S.Z || Unique.Contains(T))
        { Error=TEXT("Distinct untiled typed UAVs must match validated owner dimensions");return false; }
        Unique.Add(T);
    }
    return true;
}
}

bool RaftSimExchangeLiquidPressureHalo(FRDGBuilder& Graph,const FRaftSimLiquidHaloPlan& Plan,
    TConstArrayView<FRDGTextureRef> Grids,FString& Error)
{
    if (!ValidateHaloGrids(Plan,Grids,PF_R32_FLOAT,Error)) return false;
    auto* P=Graph.AllocParameters<FRaftSimLiquidHaloCS::FParameters>();
    P->ColumnCount=Plan.Count;P->Depth=Plan.Sizes[0].Z;P->Columns=Graph.CreateSRV(Plan.Columns);
    // Unused slots reference a valid owner but cannot be addressed by the map.
    for (int32 I=0;I<16;++I) P->Grids[I]=Graph.CreateUAV(Grids[FMath::Min(I,Grids.Num()-1)]);
    TShaderMapRef<FRaftSimLiquidHaloCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Same-Iteration Pressure Halo"),Shader,P,
        FIntVector(FMath::DivideAndRoundUp(Plan.Count,64u),P->Depth,1));
    return true;
}

bool RaftSimExchangeLiquidBoundaryHalo(FRDGBuilder& Graph,const FRaftSimLiquidHaloPlan& Plan,
    TConstArrayView<FRDGTextureRef> Grids,FString& Error)
{
    if (!ValidateHaloGrids(Plan,Grids,PF_FloatRGBA,Error)) return false;
    auto* P=Graph.AllocParameters<FRaftSimLiquidBoundaryHaloCS::FParameters>();
    P->ColumnCount=Plan.Count;P->Depth=Plan.Sizes[0].Z;P->Columns=Graph.CreateSRV(Plan.Columns);
    for (int32 I=0;I<16;++I) P->Grids[I]=Graph.CreateUAV(Grids[FMath::Min(I,Grids.Num()-1)]);
    TShaderMapRef<FRaftSimLiquidBoundaryHaloCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Same-Step Boundary Halo"),Shader,P,
        FIntVector(FMath::DivideAndRoundUp(Plan.Count,64u),P->Depth,1));
    return true;
}

bool RaftSimExchangeLiquidVelocityHalo(FRDGBuilder& Graph,const FRaftSimLiquidHaloPlan& Plan,
    TConstArrayView<FRDGTextureRef> Grids,FString& Error)
{
    if (!ValidateHaloGrids(Plan,Grids,PF_FloatRGBA,Error)) return false;
    auto* P=Graph.AllocParameters<FRaftSimLiquidBoundaryHaloCS::FParameters>();
    P->ColumnCount=Plan.Count;P->Depth=Plan.Sizes[0].Z;P->Columns=Graph.CreateSRV(Plan.Columns);
    for (int32 I=0;I<16;++I) P->Grids[I]=Graph.CreateUAV(Grids[FMath::Min(I,Grids.Num()-1)]);
    TShaderMapRef<FRaftSimLiquidBoundaryHaloCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Same-Step Advection Velocity Halo"),Shader,P,
        FIntVector(FMath::DivideAndRoundUp(Plan.Count,64u),P->Depth,1));
    return true;
}
