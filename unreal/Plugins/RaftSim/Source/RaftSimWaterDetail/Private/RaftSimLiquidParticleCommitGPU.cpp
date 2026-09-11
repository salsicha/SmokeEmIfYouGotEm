#include "RaftSimLiquidParticleRoutingGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidCommitGateCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidCommitGateCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidCommitGateCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Owners)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Capacities)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Counts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Control)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidCommitGateCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidParticleCommit.usf","GateCS",SF_Compute);

class FRaftSimLiquidCommitCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidCommitCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidCommitCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Owner)
        SHADER_PARAMETER(uint32,TotalCapacity)
        SHADER_PARAMETER(uint32,WordOffset)
        SHADER_PARAMETER(uint32,HandleTableOffset)
        SHADER_PARAMETER(uint32,HandleCapacity)
        SHADER_PARAMETER(uint32,FloatComponents)
        SHADER_PARAMETER(uint32,IntComponents)
        SHADER_PARAMETER(uint32,IndexComponent)
        SHADER_PARAMETER(uint32,TagComponent)
        SHADER_PARAMETER(uint32,FloatStride)
        SHADER_PARAMETER(uint32,IntStride)
        SHADER_PARAMETER(uint32,IDCapacity)
        SHADER_PARAMETER(uint32,CountOffset)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Words)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<int2>,Handles)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<int>,HandleTable)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Counts)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,CommitControl)
        SHADER_PARAMETER_UAV(RWBuffer<float>,NativeFloats)
        SHADER_PARAMETER_UAV(RWBuffer<int>,NativeIntegers)
        SHADER_PARAMETER_UAV(RWBuffer<int>,NativeIDTable)
        SHADER_PARAMETER_UAV(RWBuffer<uint>,NativeCounts)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidCommitCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidParticleCommit.usf","CommitCS",SF_Compute);

bool RaftSimCommitLiquidParticleAssembly(FRDGBuilder& Graph,const FRaftSimLiquidParticleAssembly& A,
    const FRaftSimLiquidParticleHandles& H,TConstArrayView<FRaftSimLiquidNativeParticleTarget> Targets,
    uint32 IndexComponent,uint32 TagComponent,FString& Error)
{
    Error=TEXT("Native commit requires complete nonaliasing sinks, valid handle ABI and bounded storage");
    const int32 Owners=Targets.Num();
    if(Owners<2 || Owners>16 || A.DestinationCapacities.Num()!=Owners || H.IDCapacities.Num()!=Owners ||
        !A.Control || !A.Words || !A.Counts || !H.Handles || !H.IDToIndex ||
        IndexComponent>=A.IntComponents || TagComponent>=A.IntComponents || IndexComponent==TagComponent) return false;
    TArray<uint32> Limits;TSet<FRHIUnorderedAccessView*> Unique;TMap<FRHIUnorderedAccessView*,TSet<uint32>> CounterSlots;
    TArray<TPair<FRHIUnorderedAccessView*,ERHIAccess>> Buffers;
    TArray<FRHIUnorderedAccessView*> Counters;
    for(int32 I=0;I<Owners;++I)
    {
        const auto& T=Targets[I];Limits.Add(T.Capacity);
        if(T.Capacity==0) continue;
        if(T.Capacity>262144 || T.FloatStride<T.Capacity || T.IntStride<T.Capacity ||
            uint64(T.FloatStride)*A.FloatComponents>MAX_uint32 || uint64(T.IntStride)*A.IntComponents>MAX_uint32 ||
            T.IDCapacity<H.IDCapacities[I] || T.IDCapacity>262144 || !T.NativeCounts || T.CountOffset==MAX_uint32) return false;
        for(auto* B:{T.Floats,T.Integers,T.IDToIndex})
        { if(!B || Unique.Contains(B)) return false;Unique.Add(B);Buffers.Emplace(B,B==T.IDToIndex?ERHIAccess::SRVCompute:ERHIAccess::SRVMask); }
        // Counter UAV can be shared, but a counter slot cannot belong to two owners.
        auto& Slots=CounterSlots.FindOrAdd(T.NativeCounts);
        if(Slots.Contains(T.CountOffset)) return false;Slots.Add(T.CountOffset);Counters.AddUnique(T.NativeCounts);
    }
    auto LimitBuffer=CreateStructuredBuffer(Graph,TEXT("LiquidCommit.NativeCapacity"),TConstArrayView<uint32>(Limits));
    auto* Gate=Graph.AllocParameters<FRaftSimLiquidCommitGateCS::FParameters>();
    Gate->Owners=Owners;Gate->Capacities=Graph.CreateSRV(LimitBuffer);Gate->Counts=Graph.CreateSRV(A.Counts);Gate->Control=Graph.CreateUAV(A.Control);
    TShaderMapRef<FRaftSimLiquidCommitGateCS> GateShader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Native Commit Capacity Gate"),GateShader,Gate,FIntVector(1,1,1));
    Graph.AddPass(RDG_EVENT_NAME("RaftSim Native Particle Commit Begin"),ERDGPassFlags::None,
        [Buffers,Counters](FRHICommandList& Cmd)
        {
            for(const auto& B:Buffers) Cmd.Transition(FRHITransitionInfo(B.Key,B.Value,ERHIAccess::UAVCompute));
            for(auto* C:Counters) Cmd.Transition(FRHITransitionInfo(C,ERHIAccess::UAVCompute,ERHIAccess::UAVCompute));
        });
    uint32 Offset=0,IDOffset=0;
    for(int32 I=0;I<Owners;++I)
    {
        const auto& T=Targets[I];
        if(T.Capacity)
        {
            auto* P=Graph.AllocParameters<FRaftSimLiquidCommitCS::FParameters>();
            P->Owner=I;P->TotalCapacity=A.TotalCapacity;P->WordOffset=Offset;P->HandleTableOffset=IDOffset;P->HandleCapacity=H.IDCapacities[I];
            P->FloatComponents=A.FloatComponents;P->IntComponents=A.IntComponents;P->IndexComponent=IndexComponent;P->TagComponent=TagComponent;
            P->FloatStride=T.FloatStride;P->IntStride=T.IntStride;P->IDCapacity=T.IDCapacity;P->CountOffset=T.CountOffset;
            P->Words=Graph.CreateSRV(A.Words);P->Handles=Graph.CreateSRV(H.Handles);P->HandleTable=Graph.CreateSRV(H.IDToIndex);
            P->Counts=Graph.CreateSRV(A.Counts);P->CommitControl=Graph.CreateSRV(A.Control);
            P->NativeFloats=T.Floats;P->NativeIntegers=T.Integers;P->NativeIDTable=T.IDToIndex;P->NativeCounts=T.NativeCounts;
            TShaderMapRef<FRaftSimLiquidCommitCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
            FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Commit Native Particle Owner %d",I),ERDGPassFlags::Compute|ERDGPassFlags::NeverCull,
                Shader,P,FIntVector(FMath::DivideAndRoundUp(FMath::Max(T.Capacity,T.IDCapacity),64u),1,1));
        }
        Offset+=A.DestinationCapacities[I];IDOffset+=H.IDCapacities[I];
    }
    Graph.AddPass(RDG_EVENT_NAME("RaftSim Native Particle Commit End"),ERDGPassFlags::None,
        [Buffers,Counters](FRHICommandList& Cmd)
        {
            for(const auto& B:Buffers) Cmd.Transition(FRHITransitionInfo(B.Key,ERHIAccess::UAVCompute,B.Value));
            for(auto* C:Counters) Cmd.Transition(FRHITransitionInfo(C,ERHIAccess::UAVCompute,ERHIAccess::UAVCompute));
        });
    Error.Reset();return true;
}
