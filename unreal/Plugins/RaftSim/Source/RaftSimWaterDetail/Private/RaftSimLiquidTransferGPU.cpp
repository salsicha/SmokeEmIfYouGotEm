#include "RaftSimLiquidTransferGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidTransferCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidTransferCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidTransferCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,ColumnCount)
        SHADER_PARAMETER(uint32,Depth)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint4>,Groups)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint4>,Contributors)
        SHADER_PARAMETER_RDG_TEXTURE_SRV_ARRAY(Texture3D<float4>,Deposits,[16])
        SHADER_PARAMETER_RDG_TEXTURE_UAV_ARRAY(RWTexture3D<float4>,Totals,[16])
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidTransferCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidTransfer.usf","MainCS",SF_Compute);

class FRaftSimLiquidTransferResolveCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidTransferResolveCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidTransferResolveCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntVector,Size)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture3D<float4>,Total)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture3D<float4>,NativeVelocity)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture3D<float>,NativeSupport)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM6); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidTransferResolveCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidTransferResolve.usf","MainCS",SF_Compute);

FRaftSimLiquidTransferPlan RaftSimBuildLiquidTransferPlan(FRDGBuilder& Graph,TConstArrayView<FIntVector> Sizes,
    TConstArrayView<FRaftSimLiquidHaloColumn> Columns,FString& Error)
{
    // Reuse the pressure map's allocation/address/race validation. Its source
    // is the physical owner; its destination is a P2G contributor/subscriber.
    if (!RaftSimBuildLiquidHaloPlan(Graph,Sizes,Columns,Error).Columns) return {};
    TArray<FRaftSimLiquidHaloColumn> Sorted;Sorted.Append(Columns.GetData(),Columns.Num());
    auto Key=[](const FRaftSimLiquidHaloColumn& C)
    { return (uint64(C.SourceOwner)<<32)|(uint64(C.Source.Y)<<16)|uint32(C.Source.X); };
    Sorted.Sort([&](const auto& A,const auto& B)
    { return Key(A)!=Key(B)?Key(A)<Key(B):A.DestinationOwner<B.DestinationOwner; });
    TArray<FUintVector4> Groups,Contributors;
    for (int32 I=0;I<Sorted.Num();)
    {
        const auto& Owner=Sorted[I];const int32 First=Contributors.Num();int32 PreviousOwner=INDEX_NONE;
        do
        {
            const auto& C=Sorted[I++];
            if (C.DestinationOwner==PreviousOwner)
            { Error=TEXT("One region cannot contribute two different cells to the same global cell");return {}; }
            PreviousOwner=C.DestinationOwner;
            Contributors.Emplace(C.DestinationOwner,C.Destination.X,C.Destination.Y,0);
        } while (I<Sorted.Num() && Key(Sorted[I])==Key(Owner));
        Groups.Emplace(Owner.SourceOwner,Owner.Source.X,Owner.Source.Y,First);
        Groups.Emplace(Contributors.Num()-First,0,0,0);
    }
    FRaftSimLiquidTransferPlan Plan;Plan.Sizes.Append(Sizes.GetData(),Sizes.Num());Plan.Count=Groups.Num()/2;
    Plan.Groups=CreateStructuredBuffer(Graph,TEXT("LiquidTransfer.OwnerGroups"),TConstArrayView<FUintVector4>(Groups));
    Plan.Contributors=CreateStructuredBuffer(Graph,TEXT("LiquidTransfer.Contributors"),TConstArrayView<FUintVector4>(Contributors));
    Error.Reset();return Plan;
}

bool RaftSimReduceLiquidTransfer(FRDGBuilder& Graph,const FRaftSimLiquidTransferPlan& Plan,
    TConstArrayView<FRDGTextureRef> Deposits,TArray<FRDGTextureRef>& Totals,FString& Error)
{
    Totals.Reset();
    if (GMaxRHIFeatureLevel<ERHIFeatureLevel::SM6 || !Plan.Groups || !Plan.Contributors || !Plan.Count ||
        Deposits.Num()<2 || Deposits.Num()>16 || Deposits.Num()!=Plan.Sizes.Num())
    { Error=TEXT("Validated same-graph transfer plan and complete owner deposits required");return false; }
    TSet<FRDGTextureRef> Unique;
    for (int32 I=0;I<Deposits.Num();++I)
    {
        const auto T=Deposits[I];const auto S=Plan.Sizes[I];
        if (!T || T->Desc.Dimension!=ETextureDimension::Texture3D || T->Desc.Format!=PF_A32B32G32R32F ||
            !EnumHasAnyFlags(T->Desc.Flags,TexCreate_ShaderResource) || T->Desc.Extent!=FIntPoint(S.X,S.Y) ||
            T->Desc.Depth!=S.Z || Unique.Contains(T))
        { Error=TEXT("Independent untiled RGBA32F deposits must match every owner");return false; }
        Unique.Add(T);
    }
    // Immutable input snapshots avoid read/write races across bidirectional
    // faces and corners, and leave raw deposits available for conservation QA.
    for (const auto T:Deposits)
    {
        auto Desc=T->Desc;Desc.Flags|=TexCreate_UAV|TexCreate_ShaderResource;
        auto Out=Graph.CreateTexture(Desc,TEXT("LiquidTransfer.ReducedMomentumVolume"));
        AddCopyTexturePass(Graph,T,Out);Totals.Add(Out);
    }
    auto* P=Graph.AllocParameters<FRaftSimLiquidTransferCS::FParameters>();
    P->ColumnCount=Plan.Count;P->Depth=Plan.Sizes[0].Z;
    P->Groups=Graph.CreateSRV(Plan.Groups);P->Contributors=Graph.CreateSRV(Plan.Contributors);
    for (int32 I=0;I<16;++I)
    {
        const int32 Owner=FMath::Min(I,Deposits.Num()-1);
        P->Deposits[I]=Graph.CreateSRV(Deposits[Owner]);P->Totals[I]=Graph.CreateUAV(Totals[Owner]);
    }
    TShaderMapRef<FRaftSimLiquidTransferCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Conservative Regional P2G Reduction"),Shader,P,
        FIntVector(FMath::DivideAndRoundUp(Plan.Count,64u),P->Depth,1));
    Error.Reset();return true;
}

bool RaftSimResolveLiquidTransfer(FRDGBuilder& Graph,FRDGTextureRef Total,
    FRDGTextureRef NativeVelocity,FRDGTextureRef NativeSupport,FString& Error)
{
    if (!Total || !NativeVelocity || !NativeSupport || Total==NativeVelocity || Total==NativeSupport || NativeVelocity==NativeSupport ||
        Total->Desc.Format!=PF_A32B32G32R32F || NativeVelocity->Desc.Format!=PF_FloatRGBA ||
        (NativeSupport->Desc.Format!=PF_R16F && NativeSupport->Desc.Format!=PF_R32_FLOAT))
    { Error=TEXT("Resolve requires distinct full-precision totals and typed native velocity/support");return false; }
    for (const auto T:{Total,NativeVelocity,NativeSupport})
        if (T->Desc.Dimension!=ETextureDimension::Texture3D || T->Desc.Extent!=Total->Desc.Extent || T->Desc.Depth!=Total->Desc.Depth ||
            !EnumHasAnyFlags(T->Desc.Flags,T==Total?TexCreate_ShaderResource:TexCreate_UAV))
        { Error=TEXT("Resolve grids must have matching untiled dimensions and access");return false; }
    auto* P=Graph.AllocParameters<FRaftSimLiquidTransferResolveCS::FParameters>();
    P->Size=FIntVector(Total->Desc.Extent.X,Total->Desc.Extent.Y,Total->Desc.Depth);
    P->Total=Graph.CreateSRV(Total);P->NativeVelocity=Graph.CreateUAV(NativeVelocity);P->NativeSupport=Graph.CreateUAV(NativeSupport);
    TShaderMapRef<FRaftSimLiquidTransferResolveCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Normalize Shared P2G Before Native Boundary"),Shader,P,
        FComputeShaderUtils::GetGroupCount(P->Size,FIntVector(4,4,4)));
    Error.Reset();return true;
}
