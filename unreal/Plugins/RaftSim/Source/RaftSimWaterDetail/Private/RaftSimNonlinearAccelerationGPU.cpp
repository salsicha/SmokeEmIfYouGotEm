#include "RaftSimNonlinearAccelerationGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimNonlinearAccelerationCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimNonlinearAccelerationCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimNonlinearAccelerationCS,FGlobalShader);
    class FPrepare : SHADER_PERMUTATION_BOOL("RAFTSIM_ACCELERATION_PREPARE");
    class FPhase : SHADER_PERMUTATION_INT("RAFTSIM_ACCELERATION_PHASE",15);
    using FPermutationDomain=TShaderPermutationDomain<FPrepare,FPhase>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntPoint,GridSize)
        SHADER_PARAMETER(float,CellMeters)
        SHADER_PARAMETER(FVector2f,Lengths)
        SHADER_PARAMETER(uint32,Periodic)
        SHADER_PARAMETER(uint32,UsePhysicalBedSlope)
        SHADER_PARAMETER(uint32,UseDispersionFraction)
        SHADER_PARAMETER(uint32,PartialCount)
        SHADER_PARAMETER(uint32,Iteration)
        RDG_BUFFER_ACCESS(IterationDispatchArgs,ERHIAccess::IndirectArgs)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,Geometry)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,PhysicalBedSlope)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,NonbreakingFraction)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Pairs)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,RightHandSide)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Center)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Edges)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Diagonal)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,PreparedCenter)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,PreparedEdges)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,PreparedDiagonal)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Solution)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Residual)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Direction)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Scratch)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,WValue)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,TrueResidual)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Partial)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Control)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,NextPartial)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,NextControl)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,PartialExponents)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {
        const FPermutationDomain Permutation(P.PermutationId);
        return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5) &&
            (!Permutation.Get<FPrepare>() || Permutation.Get<FPhase>()==0);
    }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimNonlinearAccelerationCS,
    "/Plugin/RaftSimWaterDetail/Private/RaftSimNonlinearAcceleration.usf","MainCS",SF_Compute);

FRaftSimNonlinearAccelerationResult RaftSimSolveNonlinearAccelerationGPU(FRDGBuilder& Graph,
    FRDGBufferRef Geometry,FRDGBufferRef Pairs,FRDGBufferRef RHS,FIntPoint Size,
    float CellMeters,FVector2f Lengths,bool bPeriodic,int32 Iterations,FString& Error,FRDGBufferRef PhysicalBedSlope,bool bDistributed,FRDGBufferRef DispersionFraction,bool bFusedReductions,FRDGBufferRef IterationDispatchArgs)
{
    FRaftSimNonlinearAccelerationResult Result;Error.Reset();
    if(Size.X<1 || Size.Y<1 || Size.X>512 || Size.Y>512 || Iterations!=40 ||
        !FMath::IsFinite(CellMeters) || CellMeters<=0 || !FMath::IsFinite(Lengths.X) ||
        !FMath::IsFinite(Lengths.Y) || Lengths.X<=0 || Lengths.Y<=0)
    { Error=TEXT("Invalid nonlinear acceleration grid or unchanged 40-iteration budget");return Result; }
    const uint32 Count=uint32(Size.X)*Size.Y;
    auto Matches=[Count](FRDGBufferRef B,uint32 Stride)
    { return B && B->Desc.BytesPerElement==Stride && B->Desc.NumElements==Count; };
    if(!Matches(Geometry,8) || !Matches(Pairs,4) || !Matches(RHS,16) || (PhysicalBedSlope && !Matches(PhysicalBedSlope,8)) ||
        (DispersionFraction && !Matches(DispersionFraction,4)))
    { Error=TEXT("Nonlinear acceleration requires exact geometry, reconstructed graph and two-pole RHS buffers");return Result; }
    if(IterationDispatchArgs && (!bDistributed || IterationDispatchArgs->Desc.BytesPerElement!=4 ||
        IterationDispatchArgs->Desc.NumElements!=6 || !EnumHasAllFlags(IterationDispatchArgs->Desc.Usage,BUF_DrawIndirect | BUF_VertexBuffer)))
    {Error=TEXT("Iteration dispatch requires two exact indirect uint3 records and distributed recurrence");return Result;}
    auto Buffer=[&](uint32 Stride,uint32 N,const TCHAR* Name)
    { auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,N);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name); };
    auto Center=Buffer(16,Count,TEXT("NonlinearAcceleration.Center"));
    auto Edges=Buffer(16,Count,TEXT("NonlinearAcceleration.Edges"));
    auto Diagonal=Buffer(16,Count,TEXT("NonlinearAcceleration.Diagonal"));
    Result.Solution=Buffer(16,Count,TEXT("NonlinearAcceleration.Solution"));
    Result.Residual=Buffer(16,Count,TEXT("NonlinearAcceleration.TrueResidual"));
    Result.Diagnostics=Buffer(4,4,TEXT("NonlinearAcceleration.Diagnostics"));
    auto R=Buffer(16,Count,TEXT("NonlinearAcceleration.RecurrenceResidual"));
    auto P=Buffer(16,Count,TEXT("NonlinearAcceleration.Direction"));
    auto AP=Buffer(16,Count,TEXT("NonlinearAcceleration.Scratch"));
    auto W=Buffer(8,Count,TEXT("NonlinearAcceleration.W"));
    const uint32 Groups=FMath::DivideAndRoundUp(Count,256u);
    auto Partial=Buffer(16,Groups,TEXT("NonlinearAcceleration.Partial"));
    auto Control=Buffer(16,5,TEXT("NonlinearAcceleration.Control"));
    auto PartialExponents=Buffer(8,Groups,TEXT("NonlinearAcceleration.PartialExponents"));
    auto NextPartial=bFusedReductions?Buffer(16,Groups,TEXT("NonlinearAcceleration.NextPartial")):Partial;
    auto NextControl=bFusedReductions?Buffer(16,3,TEXT("NonlinearAcceleration.NextControl")):Control;
    AddClearUAVPass(Graph,Graph.CreateUAV(Result.Diagnostics),0u);
    auto Dispatch=[&](bool Prepare,int32 Phase,uint32 Iteration,uint32 DispatchGroups,bool Recurrence=false)
    {
        auto* Params=Graph.AllocParameters<FRaftSimNonlinearAccelerationCS::FParameters>();
        Params->GridSize=Size;Params->CellMeters=CellMeters;Params->Lengths=Lengths;Params->Periodic=bPeriodic?1u:0u;
        Params->UsePhysicalBedSlope=PhysicalBedSlope?1u:0u;
        Params->UseDispersionFraction=DispersionFraction?1u:0u;
        Params->NonbreakingFraction=Graph.CreateSRV(DispersionFraction?DispersionFraction:Pairs);
        Params->PartialCount=Groups;Params->Iteration=Iteration;
        Params->IterationDispatchArgs=Recurrence?IterationDispatchArgs:nullptr;
        Params->PhysicalBedSlope=Graph.CreateSRV(PhysicalBedSlope?PhysicalBedSlope:Geometry);
        Params->Geometry=Graph.CreateSRV(Geometry);Params->Pairs=Graph.CreateSRV(Pairs);Params->RightHandSide=Graph.CreateSRV(RHS);
        Params->Center=Graph.CreateSRV(Center);Params->Edges=Graph.CreateSRV(Edges);Params->Diagonal=Graph.CreateSRV(Diagonal);
        Params->PreparedCenter=Graph.CreateUAV(Center);Params->PreparedEdges=Graph.CreateUAV(Edges);Params->PreparedDiagonal=Graph.CreateUAV(Diagonal);
        Params->Solution=Graph.CreateUAV(Result.Solution);Params->Residual=Graph.CreateUAV(R);Params->Direction=Graph.CreateUAV(P);
        Params->Scratch=Graph.CreateUAV(AP);Params->WValue=Graph.CreateUAV(W);Params->TrueResidual=Graph.CreateUAV(Result.Residual);
        Params->Diagnostics=Graph.CreateUAV(Result.Diagnostics);
        Params->Partial=Graph.CreateUAV(Partial);Params->Control=Graph.CreateUAV(Control);
        Params->NextPartial=Graph.CreateUAV(NextPartial);Params->NextControl=Graph.CreateUAV(NextControl);
        Params->PartialExponents=Graph.CreateUAV(PartialExponents);
        FRaftSimNonlinearAccelerationCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimNonlinearAccelerationCS::FPrepare>(Prepare);
        Permutation.Set<FRaftSimNonlinearAccelerationCS::FPhase>(Phase);
        TShaderMapRef<FRaftSimNonlinearAccelerationCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
        ClearUnusedGraphResources(Shader,Params);
        if(Recurrence && IterationDispatchArgs)
            FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Nonlinear Acceleration Indirect Phase%d Iter%d",Phase,Iteration),Shader,Params,
                IterationDispatchArgs,DispatchGroups==Groups?0u:12u);
        else
            FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Nonlinear Acceleration %s Phase%d Iter%d",Prepare?TEXT("Prepare"):TEXT("PCG40"),Phase,Iteration),Shader,Params,
                FIntVector(DispatchGroups,1,1));
    };
    Dispatch(true,0,0,Groups);
    if(!bDistributed)Dispatch(false,0,0,1);
    else
    {
        Dispatch(false,1,0,Groups);Dispatch(false,2,0,1);
        Dispatch(false,3,0,Groups);Dispatch(false,4,0,1);
        for(uint32 Iteration=0;Iteration<40;++Iteration)
        {
            Dispatch(false,5,Iteration,Groups,true);Dispatch(false,6,Iteration,Groups,true);
            if(bFusedReductions)
            { Dispatch(false,13,Iteration,Groups,true);Dispatch(false,14,Iteration,Groups,true); }
            else
            {
                Dispatch(false,7,Iteration,1,true);Dispatch(false,8,Iteration,Groups,true);
                Dispatch(false,9,Iteration,1,true);Dispatch(false,10,Iteration,Groups,true);
            }
        }
        Dispatch(false,11,0,Groups);Dispatch(false,5,0,Groups);Dispatch(false,12,0,Groups);
    }
    return Result;
}
