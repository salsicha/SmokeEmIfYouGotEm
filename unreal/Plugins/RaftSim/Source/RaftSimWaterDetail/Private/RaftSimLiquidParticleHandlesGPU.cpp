#include "RaftSimLiquidParticleRoutingGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidHandlesCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidHandlesCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidHandlesCS,FGlobalShader);
    class FMode : SHADER_PERMUTATION_INT("HANDLE_MODE",4);
    using FPermutationDomain=TShaderPermutationDomain<FMode>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Owner)
        SHADER_PARAMETER(uint32,TotalCapacity)
        SHADER_PARAMETER(uint32,IndexPlane)
        SHADER_PARAMETER(uint32,TagPlane)
        SHADER_PARAMETER(uint32,NewAcquireTag)
        SHADER_PARAMETER(FUintVector2,ParticleRange)
        SHADER_PARAMETER(FUintVector2,IDRange)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Words)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,References)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Counts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<int2>,Handles)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<int>,IDToIndex)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,FreeIDs)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,FreeCounts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,IncomingCounts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Control)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidHandlesCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidParticleHandles.usf","MainCS",SF_Compute);

FRaftSimLiquidParticleHandles RaftSimPrepareLiquidParticleHandles(FRDGBuilder& Graph,
    const FRaftSimLiquidParticleAssembly& A,TConstArrayView<uint32> IDCapacities,
    uint32 IndexComponent,uint32 TagComponent,uint32 Epoch,uint32 NativeTag,FString& Error)
{
    Error=TEXT("Local handle preparation requires bounded receiving ranges, exact ID planes and nonwrapped acquire-tag namespaces");
    const auto& Capacities=A.DestinationCapacities;const int32 Owners=Capacities.Num();
    if(Owners<2 || Owners>16 || IDCapacities.Num()!=Owners || !A.Words || !A.References || !A.Counts || !A.Control ||
        IndexComponent>=A.IntComponents || TagComponent>=A.IntComponents || IndexComponent==TagComponent ||
        Epoch==0 || Epoch>=0x7fffffffu || NativeTag>=0x80000000u) return {};
    TArray<FUintVector2> ParticleRanges,IDRanges;uint32 Slots=0,IDs=0;
    for(int32 I=0;I<Owners;++I)
    {
        if(Capacities[I]==0 || Capacities[I]>262144 || IDCapacities[I]<Capacities[I] || IDCapacities[I]>262144) return {};
        ParticleRanges.Emplace(Slots,Capacities[I]);IDRanges.Emplace(IDs,IDCapacities[I]);
        Slots+=Capacities[I];IDs+=IDCapacities[I];
    }
    if(Slots!=A.TotalCapacity) return {};
    auto Make=[&](const TCHAR* Name,uint32 Stride,uint32 N)
    { auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,N);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name); };
    FRaftSimLiquidParticleHandles H;H.TotalIDs=IDs;
    H.IDCapacities.Append(IDCapacities.GetData(),IDCapacities.Num());
    H.Handles=Make(TEXT("LiquidHandles.ReceivingHandles"),8,Slots);
    H.IDToIndex=Make(TEXT("LiquidHandles.ReceivingLookup"),4,IDs);
    H.FreeIDs=Make(TEXT("LiquidHandles.FreeIDs"),4,IDs);
    H.FreeCounts=Make(TEXT("LiquidHandles.FreeCounts"),4,Owners);
    H.TableRanges=CreateStructuredBuffer(Graph,TEXT("LiquidHandles.TableRanges"),TConstArrayView<FUintVector2>(IDRanges));
    auto Incoming=Make(TEXT("LiquidHandles.IncomingCounts"),4,Owners);
    AddClearUAVPass(Graph,Graph.CreateUAV(H.Handles),MAX_uint32);
    AddClearUAVPass(Graph,Graph.CreateUAV(H.IDToIndex),MAX_uint32);
    AddClearUAVPass(Graph,Graph.CreateUAV(H.FreeIDs),MAX_uint32);
    AddClearUAVPass(Graph,Graph.CreateUAV(H.FreeCounts),0);
    AddClearUAVPass(Graph,Graph.CreateUAV(Incoming),0);
    for(int32 Mode=0;Mode<4;++Mode) for(int32 I=0;I<Owners;++I)
    {
        auto* P=Graph.AllocParameters<FRaftSimLiquidHandlesCS::FParameters>();
        P->Owner=I;P->TotalCapacity=A.TotalCapacity;P->IndexPlane=A.FloatComponents+IndexComponent;
        P->TagPlane=A.FloatComponents+TagComponent;P->NewAcquireTag=0x80000000u|Epoch;
        P->ParticleRange=ParticleRanges[I];P->IDRange=IDRanges[I];
        P->Words=Graph.CreateSRV(A.Words);P->References=Graph.CreateSRV(A.References);P->Counts=Graph.CreateSRV(A.Counts);
        P->Handles=Graph.CreateUAV(H.Handles);P->IDToIndex=Graph.CreateUAV(H.IDToIndex);
        P->FreeIDs=Graph.CreateUAV(H.FreeIDs);P->FreeCounts=Graph.CreateUAV(H.FreeCounts);
        P->IncomingCounts=Graph.CreateUAV(Incoming);P->Control=Graph.CreateUAV(A.Control);
        FRaftSimLiquidHandlesCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimLiquidHandlesCS::FMode>(Mode);
        TShaderMapRef<FRaftSimLiquidHandlesCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Receiving Handles Phase %d Owner %d",Mode,I),Shader,P,
            FIntVector(Mode==3?1:FMath::DivideAndRoundUp(Mode==1?IDCapacities[I]:Capacities[I],64u),1,1));
    }
    Error.Reset();return H;
}
