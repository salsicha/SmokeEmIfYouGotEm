#include "RaftSimLiquidParticleIdentityGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidIntegerSnapshotCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidIntegerSnapshotCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidIntegerSnapshotCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Elements)
        SHADER_PARAMETER_RDG_BUFFER_SRV(Buffer<int>,SourceIntegers)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<int>,SnapshotIntegers)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidIntegerSnapshotCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidIntegerSnapshot.usf","MainCS",SF_Compute);

FRDGBufferRef RaftSimSnapshotLiquidIntegersGPU(FRDGBuilder& Graph,FRDGBufferSRVRef Source,uint32 Elements)
{
    if (!Source || Source->Desc.Format!=PF_R32_SINT || !Elements || Elements>4194304 ||
        uint64(Elements)*4>Source->Desc.Buffer->Desc.GetSize()) return nullptr;
    auto Desc=FRDGBufferDesc::CreateStructuredDesc(4,Elements);Desc.Usage|=BUF_SourceCopy;
    auto* Output=Graph.CreateBuffer(Desc,TEXT("LiquidParticle.IntegerSnapshot"));
    auto* P=Graph.AllocParameters<FRaftSimLiquidIntegerSnapshotCS::FParameters>();
    P->Elements=Elements;P->SourceIntegers=Source;P->SnapshotIntegers=Graph.CreateUAV(Output);
    TShaderMapRef<FRaftSimLiquidIntegerSnapshotCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Native Integer Snapshot"),Shader,P,
        FIntVector(FMath::DivideAndRoundUp(Elements,64u),1,1));
    return Output;
}

class FRaftSimLiquidIdentityCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidIdentityCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidIdentityCS,FGlobalShader);
    class FCountUav : SHADER_PERMUTATION_BOOL("RAFTSIM_ID_COUNT_UAV");
    using FPermutationDomain=TShaderPermutationDomain<FCountUav>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Capacity)
        SHADER_PARAMETER(uint32,IntStride)
        SHADER_PARAMETER(uint32,CountOffset)
        SHADER_PARAMETER(FIntVector4,Offsets)
        SHADER_PARAMETER_SRV(Buffer<int>,Integers)
        SHADER_PARAMETER_SRV(Buffer<uint>,Counts)
        SHADER_PARAMETER_UAV(RWBuffer<uint>,CountsUav)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<int4>,Identities)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,PackedCount)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidIdentityCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidParticleIdentity.usf","MainCS",SF_Compute);

FRDGBufferRef RaftSimPackLiquidIdentityGPU(FRDGBuilder& Graph,FRHIShaderResourceView* Integers,
    FRHIShaderResourceView* Counts,FRHIUnorderedAccessView* CountsInUavState,uint32 IntStride,
    uint32 Components,FIntVector4 Offsets,uint32 CountOffset,uint32 Capacity,FRDGBufferRef& PackedCount)
{
    PackedCount=nullptr;
    if (!Integers || (!Counts && !CountsInUavState) || !Capacity || Capacity>262144 ||
        IntStride<Capacity || !Components || Components>1024 || uint64(IntStride)*Components>MAX_uint32 || CountOffset==INDEX_NONE) return nullptr;
    for (int32 I=0;I<4;++I) if (Offsets[I]<0 || uint32(Offsets[I])>=Components) return nullptr;
    auto IdDesc=FRDGBufferDesc::CreateStructuredDesc(16,Capacity);IdDesc.Usage|=BUF_SourceCopy;
    auto CountDesc=FRDGBufferDesc::CreateStructuredDesc(4,1);CountDesc.Usage|=BUF_SourceCopy;
    auto Output=Graph.CreateBuffer(IdDesc,TEXT("LiquidParticle.BirthIdentity"));
    PackedCount=Graph.CreateBuffer(CountDesc,TEXT("LiquidParticle.IdentityLiveCount"));
    auto* P=Graph.AllocParameters<FRaftSimLiquidIdentityCS::FParameters>();
    P->Capacity=Capacity;P->IntStride=IntStride;P->CountOffset=CountOffset;P->Offsets=Offsets;
    P->Integers=Integers;P->Counts=Counts;P->CountsUav=CountsInUavState;
    P->Identities=Graph.CreateUAV(Output);P->PackedCount=Graph.CreateUAV(PackedCount);
    FRaftSimLiquidIdentityCS::FPermutationDomain Permutation;
    Permutation.Set<FRaftSimLiquidIdentityCS::FCountUav>(CountsInUavState!=nullptr);
    TShaderMapRef<FRaftSimLiquidIdentityCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
    ClearUnusedGraphResources(Shader,P);
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Exact Native Particle Identity"),Shader,P,
        FIntVector(FMath::DivideAndRoundUp(Capacity,64u),1,1));
    return Output;
}
