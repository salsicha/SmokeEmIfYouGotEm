#include "RaftSimTotalDepthStepGPU.h"
#include "RaftSimNonlinearPressureGPU.h"
#include "RaftSimPressureResidualGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimTotalDepthStepCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimTotalDepthStepCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimTotalDepthStepCS,FGlobalShader);
    class FPhase : SHADER_PERMUTATION_INT("RAFTSIM_STEP_PHASE",7);
    using FPermutationDomain=TShaderPermutationDomain<FPhase>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Count)
        SHADER_PARAMETER(uint32,BoundaryCount)
        SHADER_PARAMETER(uint32,UseIntervalEnd)
        SHADER_PARAMETER(FVector2f,IntervalEnd)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,InputState)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,StageState)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,InputProgress)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,HydroRate)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,PressureForce)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,StageCFL)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,TransportErrors)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,PressureErrors)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,SolverErrors)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,ResidualErrors)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,FirstBoundaryFlux)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,SecondBoundaryFlux)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,BoundaryVolume)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,OutputState)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,OutputProgress)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Info)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5);}
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimTotalDepthStepCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimTotalDepthStep.usf","MainCS",SF_Compute);

FRaftSimTotalDepthStepResult RaftSimTryTotalDepthStepGPU(FRDGBuilder& Graph,
    FRDGBufferRef InputState,FRDGBufferRef Bed,FRDGBufferRef InputProgress,FIntPoint Size,
    float CellMeters,bool bPeriodic,bool bSecondOrder,
    TFunctionRef<FRDGBufferRef(FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&)> FractionForStage,FString& Error,
    FRaftSimTotalDepthBoundaryProvider BoundaryForStage,FRDGBufferRef IterationDispatchArgs,TOptional<double> IntervalEndSeconds,bool bContinuousShoreline,bool bUnscaledShoreline)
{
    FRaftSimTotalDepthStepResult R;Error.Reset();
    if(bContinuousShoreline && bUnscaledShoreline)
    {Error=TEXT("Trial shoreline models are mutually exclusive");return R;}
    FVector2f End=FVector2f::ZeroVector;
    if(IntervalEndSeconds.IsSet())
    {
        const double T=IntervalEndSeconds.GetValue();End.X=float(T);End.Y=float(T-double(End.X));
        if(!FMath::IsFinite(T) || End.ContainsNaN() || double(End.X)+End.Y!=T)
        {Error=TEXT("Interval endpoint must be exactly representable by the compensated GPU clock");return R;}
    }
    if(!InputProgress || InputProgress->Desc.NumElements!=1 || InputProgress->Desc.BytesPerElement!=16)
    {Error=TEXT("Total-depth trial requires one compensated progress record");return R;}
    if(BoundaryForStage && (bPeriodic || Size.X<1 || Size.Y<1 || Size.X>512 || Size.Y>512 ||
        !FMath::IsFinite(CellMeters) || CellMeters<=0))
    {Error=TEXT("Explicit stage boundary requires a valid nonperiodic grid");return R;}
    FRaftSimTotalDepthBoundaryInput Boundary;
    auto SelectBoundary=[&](FRDGBufferRef State,FRDGBufferRef Info)
    {
        if(!BoundaryForStage)return true;
        Boundary=BoundaryForStage(Graph,State,InputProgress,Info);
        if(!Boundary.ExteriorState || !Boundary.ExteriorBed || !Boundary.FaceVelocity)
        {Error=TEXT("Stage boundary requires exterior state, bed and explicit face velocity/rate");return false;}
        return true;
    };
    if(!SelectBoundary(InputState,nullptr))return {};
    auto F=RaftSimTotalDepthTransportGPU(Graph,InputState,Bed,Size,CellMeters,bPeriodic,bSecondOrder,Error,
        Boundary.ExteriorState,Boundary.ExteriorBed,bContinuousShoreline,bUnscaledShoreline);
    if(!F.HydroRate)return R;
    const uint32 N=Size.X*Size.Y;
    auto Buffer=[&](uint32 Stride,uint32 Count,const TCHAR* Name)
    {auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,Count);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name);};
    R.State=Buffer(16,N,TEXT("TotalStep.AcceptedState"));R.Progress=Buffer(16,1,TEXT("TotalStep.Progress"));
    R.Info=Buffer(16,1,TEXT("TotalStep.Info"));R.Diagnostics=Buffer(4,4,TEXT("TotalStep.Diagnostics"));
    const uint32 NB=BoundaryForStage?2*(Size.X+Size.Y):0;
    if(NB)R.BoundaryVolume=Buffer(16,NB,TEXT("TotalStep.BoundaryVolume"));
    const auto FirstBoundaryFlux=F.BoundaryFlux;
    auto Stage=Buffer(16,N,TEXT("TotalStep.EulerState")),Candidate=Buffer(16,N,TEXT("TotalStep.Candidate"));
    R.EulerState=Stage;R.CandidateState=Candidate;
    AddClearUAVPass(Graph,Graph.CreateUAV(R.Diagnostics),0u);
    auto Pressure=[&](FRDGBufferRef State,const FRaftSimTotalDepthTransportResult& FV)
    {return RaftSimNonlinearPressureGPU(Graph,State,FV.HydroRate,FV.Geometry,FV.Pairs,FV.PhysicalBedSlope,
        FractionForStage(Graph,State,FV),Size,CellMeters,bPeriodic,Error,true,Boundary.FaceVelocity,IterationDispatchArgs);};
    auto P=Pressure(InputState,F);if(!P.Force)return {};
    R.FirstPressureForce=P.Force;
    R.PressureStages[0]=P;
    auto Check=RaftSimCheckPressureResidualGPU(Graph,P.RightHandSide,P.Residual,Size,Error,F.Geometry);if(!Check.Diagnostics)return {};
    auto Dispatch=[&](int32 Phase,FRDGBufferRef ReadStage,FRDGBufferRef WriteState)
    {
        auto* Params=Graph.AllocParameters<FRaftSimTotalDepthStepCS::FParameters>();Params->Count=N;
        Params->BoundaryCount=NB;
        Params->UseIntervalEnd=IntervalEndSeconds.IsSet()?1u:0u;Params->IntervalEnd=End;
        Params->InputState=Graph.CreateSRV(InputState);Params->StageState=Graph.CreateSRV(ReadStage);Params->InputProgress=Graph.CreateSRV(InputProgress);
        Params->HydroRate=Graph.CreateSRV(F.HydroRate);Params->PressureForce=Graph.CreateSRV(P.Force);Params->StageCFL=Graph.CreateSRV(F.CFL);
        Params->TransportErrors=Graph.CreateSRV(F.Diagnostics);Params->PressureErrors=Graph.CreateSRV(P.Diagnostics);
        Params->SolverErrors=Graph.CreateSRV(P.SolverDiagnostics);Params->ResidualErrors=Graph.CreateSRV(Check.Diagnostics);
        Params->FirstBoundaryFlux=Graph.CreateSRV(FirstBoundaryFlux?FirstBoundaryFlux:F.HydroRate);
        Params->SecondBoundaryFlux=Graph.CreateSRV(F.BoundaryFlux?F.BoundaryFlux:F.HydroRate);
        Params->BoundaryVolume=Graph.CreateUAV(R.BoundaryVolume?R.BoundaryVolume:WriteState);
        Params->OutputState=Graph.CreateUAV(WriteState);Params->OutputProgress=Graph.CreateUAV(R.Progress);
        Params->Info=Graph.CreateUAV(R.Info);Params->Diagnostics=Graph.CreateUAV(R.Diagnostics);
        FRaftSimTotalDepthStepCS::FPermutationDomain Perm;Perm.Set<FRaftSimTotalDepthStepCS::FPhase>(Phase);
        TShaderMapRef<FRaftSimTotalDepthStepCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Perm);ClearUnusedGraphResources(Shader,Params);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Total Step Phase%d",Phase),Shader,Params,
            FIntVector(Phase==0 || Phase==2 || Phase==4?1:FMath::DivideAndRoundUp(Phase==6?NB:N,256u),1,1));
    };
    Dispatch(0,InputState,Stage);Dispatch(1,InputState,Stage);
    if(!SelectBoundary(Stage,R.Info))return {};
    F=RaftSimTotalDepthTransportGPU(Graph,Stage,Bed,Size,CellMeters,bPeriodic,bSecondOrder,Error,
        Boundary.ExteriorState,Boundary.ExteriorBed,bContinuousShoreline,bUnscaledShoreline);if(!F.HydroRate)return {};
    P=Pressure(Stage,F);if(!P.Force)return {};
    R.SecondPressureForce=P.Force;
    R.PressureStages[1]=P;
    Check=RaftSimCheckPressureResidualGPU(Graph,P.RightHandSide,P.Residual,Size,Error,F.Geometry);if(!Check.Diagnostics)return {};
    Dispatch(2,Stage,Candidate);Dispatch(3,Stage,Candidate);Dispatch(4,Candidate,R.State);Dispatch(5,Candidate,R.State);
    if(NB)Dispatch(6,Candidate,R.State);
    return R;
}
