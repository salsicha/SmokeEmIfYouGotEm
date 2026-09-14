#include "RaftSimNonlinearPressureGPU.h"
#include "RaftSimNonlinearAccelerationGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimNonlinearPressureCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimNonlinearPressureCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimNonlinearPressureCS,FGlobalShader);
    class FPhase : SHADER_PERMUTATION_INT("RAFTSIM_PRESSURE_PHASE",7);
    class FBoundary : SHADER_PERMUTATION_BOOL("RAFTSIM_PRESSURE_BOUNDARY");
    using FPermutationDomain=TShaderPermutationDomain<FPhase,FBoundary>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntPoint,GridSize)
        SHADER_PARAMETER(float,CellMeters)
        SHADER_PARAMETER(uint32,Periodic)
        SHADER_PARAMETER(FVector2f,Lengths)
        SHADER_PARAMETER(FVector2f,PoleWeights)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,State)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,BoundaryVelocity)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,HydroRate)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,Geometry)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Pairs)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,PhysicalBedSlope)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,NonbreakingFraction)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Correction)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,SolverDiagnostics)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,Velocity)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Terms)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,Base)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Forcing)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,BaseW)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,RightHandSide)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Pressure)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,Force)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimNonlinearPressureCS,
    "/Plugin/RaftSimWaterDetail/Private/RaftSimNonlinearPressure.usf","MainCS",SF_Compute);

FRaftSimNonlinearPressureResult RaftSimNonlinearPressureGPU(FRDGBuilder& Graph,
    FRDGBufferRef State,FRDGBufferRef HydroRate,FRDGBufferRef Geometry,FRDGBufferRef Pairs,
    FRDGBufferRef PhysicalBedSlope,FRDGBufferRef DispersionFraction,FIntPoint Size,
    float CellMeters,bool bPeriodic,FString& Error,bool bFusedReductions,FRDGBufferRef BoundaryVelocity,FRDGBufferRef IterationDispatchArgs)
{
    FRaftSimNonlinearPressureResult Result;Error.Reset();
    if(Size.X<1 || Size.Y<1 || Size.X>512 || Size.Y>512 || !FMath::IsFinite(CellMeters) || CellMeters<=0)
    { Error=TEXT("Invalid nonlinear pressure grid");return Result; }
    const uint32 Count=uint32(Size.X)*Size.Y;
    auto Matches=[Count](FRDGBufferRef B,uint32 Stride)
    { return B && B->Desc.BytesPerElement==Stride && B->Desc.NumElements==Count; };
    if(!Matches(State,16) || !Matches(HydroRate,16) || !Matches(Geometry,8) ||
        !Matches(Pairs,4) || !Matches(PhysicalBedSlope,8) || !Matches(DispersionFraction,4))
    { Error=TEXT("Pressure requires exact same-stage state/rate/geometry/graph/slope/fraction buffers");return Result; }
    if(BoundaryVelocity && (bPeriodic || BoundaryVelocity->Desc.NumElements!=uint32(2*(Size.X+Size.Y)) ||
        BoundaryVelocity->Desc.BytesPerElement!=8))
    {Error=TEXT("Prescribed pressure boundary requires exact nonperiodic face velocity/rate buffer");return Result;}
    auto Buffer=[&](uint32 Stride,uint32 N,const TCHAR* Name)
    { auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,N);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name); };
    Result.Force=Buffer(8,Count,TEXT("NonlinearPressure.Force"));
    Result.RightHandSide=Buffer(16,Count,TEXT("NonlinearPressure.RHS"));
    Result.Pressure=Buffer(16,Count,TEXT("NonlinearPressure.Pressure"));
    Result.Diagnostics=Buffer(4,4,TEXT("NonlinearPressure.Diagnostics"));
    auto Velocity=Buffer(8,Count,TEXT("NonlinearPressure.Velocity"));
    auto Terms=Buffer(16,Count,TEXT("NonlinearPressure.Terms"));
    auto Base=Buffer(8,Count,TEXT("NonlinearPressure.Base"));
    auto Forcing=Buffer(16,Count,TEXT("NonlinearPressure.Forcing"));
    auto BaseW=Buffer(8,Count,TEXT("NonlinearPressure.BaseW"));
    const FVector2f Lengths(.4052787713439809f,.03916567310046354f);
    AddClearUAVPass(Graph,Graph.CreateUAV(Result.Diagnostics),0u);
    auto Dispatch=[&](int32 Phase)
    {
        auto* P=Graph.AllocParameters<FRaftSimNonlinearPressureCS::FParameters>();
        P->GridSize=Size;P->CellMeters=CellMeters;P->Periodic=bPeriodic?1u:0u;
        P->Lengths=Lengths;P->PoleWeights=FVector2f(.8106202879112342f,.12271304542209915f);
        P->State=Graph.CreateSRV(State);P->HydroRate=Graph.CreateSRV(HydroRate);P->Geometry=Graph.CreateSRV(Geometry);
        P->BoundaryVelocity=BoundaryVelocity?Graph.CreateSRV(BoundaryVelocity):nullptr;
        P->Pairs=Graph.CreateSRV(Pairs);P->PhysicalBedSlope=Graph.CreateSRV(PhysicalBedSlope);P->NonbreakingFraction=Graph.CreateSRV(DispersionFraction);
        P->Correction=Graph.CreateSRV(Result.Correction?Result.Correction:Result.RightHandSide);
        P->SolverDiagnostics=Graph.CreateSRV(Result.SolverDiagnostics?Result.SolverDiagnostics:Result.Diagnostics);
        P->Velocity=Graph.CreateUAV(Velocity);P->Terms=Graph.CreateUAV(Terms);P->Base=Graph.CreateUAV(Base);
        P->Forcing=Graph.CreateUAV(Forcing);P->BaseW=Graph.CreateUAV(BaseW);P->RightHandSide=Graph.CreateUAV(Result.RightHandSide);
        P->Pressure=Graph.CreateUAV(Result.Pressure);P->Force=Graph.CreateUAV(Result.Force);P->Diagnostics=Graph.CreateUAV(Result.Diagnostics);
        FRaftSimNonlinearPressureCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimNonlinearPressureCS::FPhase>(Phase);
        Permutation.Set<FRaftSimNonlinearPressureCS::FBoundary>(BoundaryVelocity!=nullptr);
        TShaderMapRef<FRaftSimNonlinearPressureCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
        ClearUnusedGraphResources(Shader,P);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Nonlinear Pressure Phase%d",Phase),Shader,P,
            FIntVector(FMath::DivideAndRoundUp(Count,256u),1,1));
    };
    for(int32 Phase=0;Phase<=4;++Phase)Dispatch(Phase);
    auto Solve=RaftSimSolveNonlinearAccelerationGPU(Graph,Geometry,Pairs,Result.RightHandSide,Size,
        CellMeters,Lengths,bPeriodic,40,Error,PhysicalBedSlope,true,DispersionFraction,bFusedReductions,IterationDispatchArgs);
    if(!Solve.Solution)return {};
    Result.Correction=Solve.Solution;Result.Residual=Solve.Residual;Result.SolverDiagnostics=Solve.Diagnostics;
    Dispatch(5);Dispatch(6);
    return Result;
}
