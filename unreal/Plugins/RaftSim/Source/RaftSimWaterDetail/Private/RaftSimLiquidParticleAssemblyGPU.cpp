#include "RaftSimLiquidParticleRoutingGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidAssemblyCheckCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidAssemblyCheckCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidAssemblyCheckCS,FGlobalShader);
    class FFinalize : SHADER_PERMUTATION_BOOL("FINALIZE");
    using FPermutationDomain=TShaderPermutationDomain<FFinalize>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Owners)
        SHADER_PARAMETER(uint32,ExitsEnabled)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,SourceCounts)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,OwnerRanges)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,SourceCapacities)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,SourceExitCounts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,ExitCounts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Counts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Control)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidAssemblyCheckCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidParticleAssembly.usf","CheckCS",SF_Compute);

class FRaftSimLiquidAssemblyAppendCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidAssemblyAppendCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidAssemblyAppendCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Owners)
        SHADER_PARAMETER(uint32,SourceOwner)
        SHADER_PARAMETER(uint32,SourceCapacity)
        SHADER_PARAMETER(uint32,TotalCapacity)
        SHADER_PARAMETER(uint32,Components)
        SHADER_PARAMETER(uint32,ExitsEnabled)
        SHADER_PARAMETER(uint32,TotalExitCapacity)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,SourceCounts)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,OwnerRanges)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,SourceWords)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint4>,SourceRoutes)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint4>,SourceExitRecords)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint2>,ExitOwnerRanges)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,ExitWords)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint2>,ExitReferences)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint4>,ExitRecords)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,ExitCounts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Words)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint2>,References)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Counts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Control)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidAssemblyAppendCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidParticleAssembly.usf","AppendCS",SF_Compute);

FRaftSimLiquidParticleAssembly RaftSimAssembleLiquidParticleDestinations(FRDGBuilder& Graph,
    TConstArrayView<FRaftSimLiquidParticleRoutePacket> Sources,TConstArrayView<uint32> Capacities,FString& Error,
    TConstArrayView<FRaftSimLiquidParticleExitCandidates> Exits)
{
    Error=TEXT("Destination assembly requires complete bounded source packets with one native ABI");
    const int32 Owners=Sources.Num();
    const bool WithExits=!Exits.IsEmpty();
    if (Owners<2 || Owners>16 || Capacities.Num()!=Owners || (WithExits && Exits.Num()!=Owners)) return {};
    const uint32 NF=Sources[0].FloatComponents,NI=Sources[0].IntComponents;
    if (NF<3 || NF>128 || NI<1 || NI>128) return {};
    TArray<FUintVector2> Ranges,ExitRanges;TArray<uint32> SourceCapacities;uint32 TotalCapacity=0,TotalExitCapacity=0;
    for (int32 I=0;I<Owners;++I)
    {
        const auto& S=Sources[I];
        auto Size=[](FRDGBufferRef B,uint32 Stride,uint64 Num)
        { return B && B->Desc.BytesPerElement==Stride && uint64(B->Desc.NumElements)>=FMath::Max(Num,uint64(1)); };
        if (Capacities[I]==0 || Capacities[I]>262144 || S.Capacity>262144 || S.FloatComponents!=NF || S.IntComponents!=NI ||
            !Size(S.Words,4,uint64(S.Capacity)*(NF+NI)) || !Size(S.Routes,16,S.Capacity) || !Size(S.Counts,4,Owners+3)) return {};
        if(WithExits)
        {
            const auto& E=Exits[I];
            if(!Size(E.Records,16,S.Capacity) || !Size(E.Counts,4,8) || E.SourceWords!=S.Words || E.SourceRoutes!=S.Routes ||
                E.SourceCounts!=S.Counts || !FMath::IsFinite(E.ParticleVolumeM3) || E.ParticleVolumeM3<=0) return {};
        }
        Ranges.Emplace(TotalCapacity,Capacities[I]);TotalCapacity+=Capacities[I];SourceCapacities.Add(S.Capacity);
        ExitRanges.Emplace(TotalExitCapacity,WithExits?S.Capacity:0);if(WithExits) TotalExitCapacity+=S.Capacity;
    }
    // Explicit staging allocation ceiling, not a silent particle-count clamp.
    if ((uint64(TotalCapacity)+TotalExitCapacity)*(NF+NI)*4>512ull*1024*1024) return {};
    auto Make=[&](const TCHAR* Name,uint32 Stride,uint32 N)
    { auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,FMath::Max(N,1u));D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name); };
    FRaftSimLiquidParticleAssembly R;R.TotalCapacity=TotalCapacity;R.FloatComponents=NF;R.IntComponents=NI;
    R.DestinationCapacities.Append(Capacities.GetData(),Capacities.Num());
    R.Words=Make(TEXT("LiquidAssembly.FullWords"),4,TotalCapacity*(NF+NI));
    R.References=Make(TEXT("LiquidAssembly.SourceReferences"),8,TotalCapacity);
    R.Counts=Make(TEXT("LiquidAssembly.DestinationLiveCounts"),4,Owners);
    R.Control=Make(TEXT("LiquidAssembly.TransactionControl"),4,4);
    R.TotalExitCapacity=TotalExitCapacity;
    R.ExitWords=Make(TEXT("LiquidAssembly.ExitFullWords"),4,TotalExitCapacity*(NF+NI));
    R.ExitReferences=Make(TEXT("LiquidAssembly.ExitSourceReferences"),8,TotalExitCapacity);
    R.ExitRecords=Make(TEXT("LiquidAssembly.ExitCrossings"),16,TotalExitCapacity);
    R.ExitCounts=Make(TEXT("LiquidAssembly.ExitFaceCounts"),4,Owners*5);
    R.ExitOwnerRanges=CreateStructuredBuffer(Graph,TEXT("LiquidAssembly.ExitOwnerRanges"),TConstArrayView<FUintVector2>(ExitRanges));
    for(const auto& E:Exits) R.ExitParticleVolumesM3.Add(E.ParticleVolumeM3);
    if(WithExits) R.ExitSourceCapacities=SourceCapacities;
    R.OwnerRanges=CreateStructuredBuffer(Graph,TEXT("LiquidAssembly.OwnerRanges"),TConstArrayView<FUintVector2>(Ranges));
    auto SourceLimits=CreateStructuredBuffer(Graph,TEXT("LiquidAssembly.SourceCapacities"),TConstArrayView<uint32>(SourceCapacities));
    auto AllCounts=Make(TEXT("LiquidAssembly.SourceAccounting"),4,Owners*(Owners+3));
    auto AllExitCounts=Make(TEXT("LiquidAssembly.SourceExitAccounting"),4,Owners*8);
    AddClearUAVPass(Graph,Graph.CreateUAV(AllExitCounts),0);
    auto EmptyExitRecords=Make(TEXT("LiquidAssembly.NoExitRecords"),16,1);
    AddClearUAVPass(Graph,Graph.CreateUAV(EmptyExitRecords),0);
    for (int32 I=0;I<Owners;++I) AddCopyBufferPass(Graph,AllCounts,I*(Owners+3)*4,Sources[I].Counts,0,(Owners+3)*4);
    if(WithExits) for(int32 I=0;I<Owners;++I) AddCopyBufferPass(Graph,AllExitCounts,I*8*4,Exits[I].Counts,0,8*4);
    AddClearUAVPass(Graph,Graph.CreateUAV(R.Words),0);
    AddClearUAVPass(Graph,Graph.CreateUAV(R.References),MAX_uint32);
    AddClearUAVPass(Graph,Graph.CreateUAV(R.ExitWords),0);
    AddClearUAVPass(Graph,Graph.CreateUAV(R.ExitReferences),MAX_uint32);
    AddClearUAVPass(Graph,Graph.CreateUAV(R.ExitRecords),0);
    AddClearUAVPass(Graph,Graph.CreateUAV(R.ExitCounts),0);
    auto Check=[&](bool Finalize)
    {
        auto* P=Graph.AllocParameters<FRaftSimLiquidAssemblyCheckCS::FParameters>();
        P->Owners=Owners;P->SourceCounts=Graph.CreateSRV(AllCounts);P->OwnerRanges=Graph.CreateSRV(R.OwnerRanges);
        P->ExitsEnabled=WithExits?1:0;P->SourceExitCounts=Graph.CreateSRV(AllExitCounts);P->ExitCounts=Graph.CreateUAV(R.ExitCounts);
        P->SourceCapacities=Graph.CreateSRV(SourceLimits);P->Counts=Graph.CreateUAV(R.Counts);P->Control=Graph.CreateUAV(R.Control);
        FRaftSimLiquidAssemblyCheckCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimLiquidAssemblyCheckCS::FFinalize>(Finalize);
        TShaderMapRef<FRaftSimLiquidAssemblyCheckCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Particle Assembly %s",Finalize?TEXT("Finalize"):TEXT("Preflight")),Shader,P,FIntVector(1,1,1));
    };
    Check(false);
    for (int32 I=0;I<Owners;++I)
    {
        const auto& S=Sources[I];if (!S.Capacity) continue;
        auto* P=Graph.AllocParameters<FRaftSimLiquidAssemblyAppendCS::FParameters>();
        P->Owners=Owners;P->SourceOwner=I;P->SourceCapacity=S.Capacity;P->TotalCapacity=TotalCapacity;P->Components=NF+NI;
        P->ExitsEnabled=WithExits?1:0;P->TotalExitCapacity=TotalExitCapacity;
        P->SourceExitRecords=Graph.CreateSRV(WithExits?Exits[I].Records:EmptyExitRecords);
        P->ExitOwnerRanges=Graph.CreateSRV(R.ExitOwnerRanges);
        P->ExitWords=Graph.CreateUAV(R.ExitWords);P->ExitReferences=Graph.CreateUAV(R.ExitReferences);
        P->ExitRecords=Graph.CreateUAV(R.ExitRecords);P->ExitCounts=Graph.CreateUAV(R.ExitCounts);
        P->SourceCounts=Graph.CreateSRV(AllCounts);P->OwnerRanges=Graph.CreateSRV(R.OwnerRanges);
        P->SourceWords=Graph.CreateSRV(S.Words);P->SourceRoutes=Graph.CreateSRV(S.Routes);
        P->Words=Graph.CreateUAV(R.Words);P->References=Graph.CreateUAV(R.References);P->Counts=Graph.CreateUAV(R.Counts);P->Control=Graph.CreateUAV(R.Control);
        TShaderMapRef<FRaftSimLiquidAssemblyAppendCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Assemble Particle Owner %d",I),Shader,P,
            FIntVector(FMath::DivideAndRoundUp(S.Capacity,64u),1,1));
    }
    Check(true);Error.Reset();return R;
}
