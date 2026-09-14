#include "RaftSimTotalDepthAdvanceGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimTotalDepthAdvanceCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimTotalDepthAdvanceCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimTotalDepthAdvanceCS,FGlobalShader);
    class FPhase : SHADER_PERMUTATION_INT("RAFTSIM_ADVANCE_PHASE",4);
    class FBoundary : SHADER_PERMUTATION_BOOL("RAFTSIM_ADVANCE_BOUNDARY");
    using FPermutationDomain=TShaderPermutationDomain<FPhase,FBoundary>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,TotalTrialLimit)
        SHADER_PARAMETER(uint32,BoundaryMode)
        SHADER_PARAMETER(uint32,Count)
        SHADER_PARAMETER(uint32,BoundaryCount)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWBuffer<uint>,IterationDispatchArgs)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,PreviousState)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,TrialState)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,PreviousBoundaryVolume)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,TrialBoundaryVolume)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,CandidateBoundaryRead)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,CandidateBoundaryWrite)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,NextState)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,NextBoundaryVolume)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,LedgerErrors)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,LedgerErrorsRead)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,CommitWrite)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,CommitRead)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,PreviousProgress)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,PreviousSummary)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,PreviousDiagnostics)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,TrialProgress)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,TrialDiagnostics)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,NextProgress)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,NextSummary)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,NextDiagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5);}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimTotalDepthAdvanceCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimTotalDepthAdvance.usf","MainCS",SF_Compute);

FRaftSimTotalDepthAdvanceResult RaftSimAdvanceTotalDepthGPU(FRDGBuilder& Graph,
    FRDGBufferRef InputState,FRDGBufferRef Bed,FRDGBufferRef InputProgress,
    FRDGBufferRef PreviousSummary,FRDGBufferRef PreviousDiagnostics,FIntPoint Size,
    float CellMeters,bool bPeriodic,bool bSecondOrder,int32 TrialsThisGraph,int32 TotalTrialLimit,
    TFunctionRef<FRDGBufferRef(FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&)> FractionForStage,FString& Error,
    FRaftSimTotalDepthBoundaryProvider BoundaryForStage,FRDGBufferRef PreviousBoundaryVolume,bool bCullInactiveIterations,TOptional<double> IntervalEndSeconds,
    bool bContinuousShoreline,bool bUnscaledShoreline)
{
    Error.Reset();FRaftSimTotalDepthAdvanceResult R;
    if(bContinuousShoreline && bUnscaledShoreline)
    {Error=TEXT("Advance shoreline models are mutually exclusive");return R;}
    auto IsRecord=[](FRDGBufferRef B,uint32 Stride,uint32 Count)
    {return B && B->Desc.BytesPerElement==Stride && B->Desc.NumElements==Count;};
    if(Size.X<1 || Size.Y<1 || Size.X>512 || Size.Y>512 || !FMath::IsFinite(CellMeters) || CellMeters<=0 ||
        !IsRecord(InputState,16,uint32(Size.X)*Size.Y) || !IsRecord(Bed,4,uint32(Size.X)*Size.Y) ||
        TrialsThisGraph<1 || TrialsThisGraph>RaftSimMaxTotalDepthTrialsPerGraph || TotalTrialLimit<1 || TotalTrialLimit>4096 ||
        !IsRecord(InputProgress,16,1) || (bool(PreviousSummary)!=bool(PreviousDiagnostics)) ||
        (PreviousSummary && (!IsRecord(PreviousSummary,4,4) || !IsRecord(PreviousDiagnostics,4,4))))
    {Error=TEXT("Invalid bounded total-depth grid, state/bed, interval budget or progress records");return R;}
    const bool HasBoundary=bool(BoundaryForStage);
    if((!HasBoundary && PreviousBoundaryVolume) || (HasBoundary &&
        (bPeriodic || Size.X<1 || Size.Y<1 || Size.X>512 || Size.Y>512 ||
        (bool(PreviousSummary)!=bool(PreviousBoundaryVolume)) ||
        (PreviousBoundaryVolume && !IsRecord(PreviousBoundaryVolume,16,2*(Size.X+Size.Y))))))
    {Error=TEXT("Boundary continuation requires the same explicit provider and complete per-face inventory");return R;}
    const uint32 N=uint32(Size.X)*Size.Y,NB=HasBoundary?2*(Size.X+Size.Y):0;
    auto Buffer=[&](uint32 Stride,uint32 Count,const TCHAR* Name)
    {auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,Count);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name);};
    if(!PreviousSummary)
    {
        TArray<uint32> InitialSummary={0,0,0,RaftSimTotalDepthEvolutionMode(HasBoundary,bContinuousShoreline,bUnscaledShoreline)};
        PreviousSummary=CreateStructuredBuffer(Graph,TEXT("Advance.InitialSummary"),InitialSummary);
        PreviousDiagnostics=Buffer(4,4,TEXT("Advance.InitialDiagnostics"));
        AddClearUAVPass(Graph,Graph.CreateUAV(PreviousDiagnostics),0u);
        if(HasBoundary)
        {
            PreviousBoundaryVolume=Buffer(16,NB,TEXT("Advance.InitialBoundaryVolume"));
            AddClearUAVPass(Graph,Graph.CreateUAV(PreviousBoundaryVolume),0u);
        }
    }
    R.State=InputState;R.Progress=InputProgress;R.Summary=PreviousSummary;R.Diagnostics=PreviousDiagnostics;
    R.BoundaryVolume=PreviousBoundaryVolume;
    for(int32 Slot=0;Slot<TrialsThisGraph;++Slot)
    {
        auto Old=R;auto Scratch=Buffer(16,1,TEXT("Advance.TrialInputProgress"));
        // Always initialize both uint3 records in phase0. The comparison path
        // simply does not consume them. No CPU completion readback or guessing.
        auto IterationArgs=Graph.CreateBuffer(FRDGBufferDesc::CreateIndirectDesc(4u,6u),TEXT("Advance.IterationDispatchArgs"));
        R.Progress=Buffer(16,1,TEXT("Advance.Progress"));R.Summary=Buffer(4,4,TEXT("Advance.Summary"));
        R.Diagnostics=Buffer(4,4,TEXT("Advance.Diagnostics"));
        FRDGBufferRef CandidateBoundary=nullptr,LedgerErrors=nullptr,Commit=nullptr;
        if(HasBoundary)
        {
            CandidateBoundary=Buffer(16,NB,TEXT("Advance.CandidateBoundaryVolume"));
            Commit=Buffer(4,1,TEXT("Advance.Commit"));
            LedgerErrors=Buffer(4,1,TEXT("Advance.LedgerErrors"));AddClearUAVPass(Graph,Graph.CreateUAV(LedgerErrors),0u);
            R.BoundaryVolume=Buffer(16,NB,TEXT("Advance.BoundaryVolume"));R.State=Buffer(16,N,TEXT("Advance.State"));
        }
        auto Dispatch=[&](int32 Phase,FRDGBufferRef TrialProgress,FRDGBufferRef TrialDiagnostics,
            FRDGBufferRef TrialState,FRDGBufferRef TrialVolume)
        {
            auto* P=Graph.AllocParameters<FRaftSimTotalDepthAdvanceCS::FParameters>();P->TotalTrialLimit=TotalTrialLimit;
            P->BoundaryMode=RaftSimTotalDepthEvolutionMode(HasBoundary,bContinuousShoreline,bUnscaledShoreline);P->Count=N;P->BoundaryCount=NB;
            P->IterationDispatchArgs=Phase==0?Graph.CreateUAV(IterationArgs,PF_R32_UINT):nullptr;
            P->PreviousState=Graph.CreateSRV(Old.State);P->TrialState=Graph.CreateSRV(TrialState);
            P->PreviousBoundaryVolume=Graph.CreateSRV(Old.BoundaryVolume?Old.BoundaryVolume:Old.State);
            P->TrialBoundaryVolume=Graph.CreateSRV(TrialVolume?TrialVolume:Old.State);
            P->CandidateBoundaryRead=Graph.CreateSRV(CandidateBoundary?CandidateBoundary:Old.State);
            P->CandidateBoundaryWrite=Phase==2?Graph.CreateUAV(CandidateBoundary):nullptr;
            P->NextState=Phase==3?Graph.CreateUAV(R.State):nullptr;
            P->NextBoundaryVolume=Phase==3?Graph.CreateUAV(R.BoundaryVolume):nullptr;
            P->LedgerErrors=Phase==2?Graph.CreateUAV(LedgerErrors):nullptr;
            P->LedgerErrorsRead=LedgerErrors?Graph.CreateSRV(LedgerErrors):nullptr;
            P->CommitWrite=HasBoundary && Phase==1?Graph.CreateUAV(Commit):nullptr;
            P->CommitRead=Commit?Graph.CreateSRV(Commit):nullptr;
            P->PreviousProgress=Graph.CreateSRV(Old.Progress);P->PreviousSummary=Graph.CreateSRV(Old.Summary);
            P->PreviousDiagnostics=Graph.CreateSRV(Old.Diagnostics);P->TrialProgress=Graph.CreateSRV(TrialProgress);
            P->TrialDiagnostics=Graph.CreateSRV(TrialDiagnostics);P->NextProgress=Graph.CreateUAV(Phase==0?Scratch:R.Progress);
            P->NextSummary=Graph.CreateUAV(R.Summary);P->NextDiagnostics=Graph.CreateUAV(R.Diagnostics);
            FRaftSimTotalDepthAdvanceCS::FPermutationDomain Perm;Perm.Set<FRaftSimTotalDepthAdvanceCS::FPhase>(Phase);
            Perm.Set<FRaftSimTotalDepthAdvanceCS::FBoundary>(HasBoundary);
            TShaderMapRef<FRaftSimTotalDepthAdvanceCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Perm);ClearUnusedGraphResources(Shader,P);
            const uint32 Threads=Phase==2?NB:Phase==3?FMath::Max(N,NB):1;
            FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Bounded Advance Phase%d",Phase),Shader,P,
                FIntVector(FMath::DivideAndRoundUp(Threads,256u),1,1));
        };
        Dispatch(0,Old.Progress,Old.Diagnostics,Old.State,Old.BoundaryVolume);
        auto Trial=RaftSimTryTotalDepthStepGPU(Graph,Old.State,Bed,Scratch,Size,CellMeters,bPeriodic,bSecondOrder,FractionForStage,Error,BoundaryForStage,
            bCullInactiveIterations?IterationArgs:nullptr,IntervalEndSeconds,bContinuousShoreline,bUnscaledShoreline);
        if(!Trial.State)return {};
        if(HasBoundary)
        {
            if(!Trial.BoundaryVolume){Error=TEXT("Boundary trial omitted its inventory");return {};}
            Dispatch(2,Trial.Progress,Trial.Diagnostics,Trial.State,Trial.BoundaryVolume);
        }
        else R.State=Trial.State;
        Dispatch(1,Trial.Progress,Trial.Diagnostics,Trial.State,Trial.BoundaryVolume);
        if(HasBoundary)Dispatch(3,Trial.Progress,Trial.Diagnostics,Trial.State,Trial.BoundaryVolume);
    }
    return R;
}
