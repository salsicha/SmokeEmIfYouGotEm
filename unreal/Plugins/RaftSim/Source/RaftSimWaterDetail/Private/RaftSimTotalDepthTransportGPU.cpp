#include "RaftSimTotalDepthTransportGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimTotalDepthTransportCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimTotalDepthTransportCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimTotalDepthTransportCS,FGlobalShader);
    class FPhase : SHADER_PERMUTATION_INT("RAFTSIM_TRANSPORT_PHASE",6);
    class FExterior : SHADER_PERMUTATION_BOOL("RAFTSIM_TRANSPORT_EXTERIOR");
    class FContinuous : SHADER_PERMUTATION_BOOL("RAFTSIM_TRANSPORT_CONTINUOUS");
    class FUnscaled : SHADER_PERMUTATION_BOOL("RAFTSIM_TRANSPORT_UNSCALED");
    using FPermutationDomain=TShaderPermutationDomain<FPhase,FExterior,FContinuous,FUnscaled>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(FIntPoint,GridSize)
        SHADER_PARAMETER(float,CellMeters)
        SHADER_PARAMETER(uint32,Periodic)
        SHADER_PARAMETER(uint32,SecondOrder)
        SHADER_PARAMETER(uint32,PartialCount)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,State)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,Bed)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,ExteriorState)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float>,ExteriorBed)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,BoundaryFlux)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,Velocity)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,Geometry)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,PhysicalBedSlope)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,RawX)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,RawY)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,SlopeX)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,SlopeY)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,FluxX)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,FluxY)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,FoamFlux)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,CorrectionX)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,CorrectionY)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Pairs)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Flattened)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,ShorelineFactors)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,HydroRate)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float2>,Partial)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,CFL)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    {
        FPermutationDomain Permutation(P.PermutationId);
        return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5) &&
            !(Permutation.Get<FContinuous>() && Permutation.Get<FUnscaled>());
    }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimTotalDepthTransportCS,
    "/Plugin/RaftSimWaterDetail/Private/RaftSimTotalDepthTransport.usf","MainCS",SF_Compute);

FRaftSimTotalDepthTransportResult RaftSimTotalDepthTransportGPU(FRDGBuilder& Graph,
    FRDGBufferRef State,FRDGBufferRef Bed,FIntPoint Size,float CellMeters,
    bool bPeriodic,bool bSecondOrder,FString& Error,FRDGBufferRef ExteriorState,FRDGBufferRef ExteriorBed,bool bContinuousShoreline,bool bUnscaledShoreline)
{
    FRaftSimTotalDepthTransportResult R;Error.Reset();
    if(bContinuousShoreline && bUnscaledShoreline)
    { Error=TEXT("Transport shoreline models are mutually exclusive");return R; }
    if(Size.X<1 || Size.Y<1 || Size.X>512 || Size.Y>512 || !FMath::IsFinite(CellMeters) || CellMeters<=0)
    { Error=TEXT("Invalid total-depth transport grid");return R; }
    const uint32 Count=Size.X*Size.Y,Groups=FMath::DivideAndRoundUp(Count,256u);
    if(!State || !Bed || State->Desc.NumElements!=Count || State->Desc.BytesPerElement!=16 ||
        Bed->Desc.NumElements!=Count || Bed->Desc.BytesPerElement!=4)
    { Error=TEXT("Transport requires exact total-state and physical-bed buffers");return R; }
    const bool bExterior=ExteriorState!=nullptr || ExteriorBed!=nullptr;
    const uint32 BoundaryCount=2*(Size.X+Size.Y);
    if(bExterior && (bPeriodic || !ExteriorState || !ExteriorBed ||
        ExteriorState->Desc.NumElements!=BoundaryCount || ExteriorState->Desc.BytesPerElement!=16 ||
        ExteriorBed->Desc.NumElements!=BoundaryCount || ExteriorBed->Desc.BytesPerElement!=4))
    { Error=TEXT("Exterior transport requires paired exact nonperiodic ghost buffers");return R; }
    auto Buffer=[&](uint32 Stride,uint32 N,const TCHAR* Name)
    { auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,N);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name); };
    R.HydroRate=Buffer(16,Count,TEXT("TotalTransport.Rate"));R.Geometry=Buffer(8,Count,TEXT("TotalTransport.Geometry"));
    R.PhysicalBedSlope=Buffer(8,Count,TEXT("TotalTransport.BedSlope"));R.Pairs=Buffer(4,Count,TEXT("TotalTransport.Pairs"));
    R.CFL=Buffer(16,1,TEXT("TotalTransport.CFL"));R.Diagnostics=Buffer(4,4,TEXT("TotalTransport.Diagnostics"));
    if(bExterior)R.BoundaryFlux=Buffer(16,BoundaryCount,TEXT("TotalTransport.BoundaryFlux"));
    auto Velocity=Buffer(8,Count,TEXT("TotalTransport.Velocity"));
    auto RawX=Buffer(16,Count,TEXT("TotalTransport.RawX")),RawY=Buffer(16,Count,TEXT("TotalTransport.RawY"));
    auto SlopeX=Buffer(16,Count,TEXT("TotalTransport.SlopeX")),SlopeY=Buffer(16,Count,TEXT("TotalTransport.SlopeY"));
    R.RawX=RawX;R.RawY=RawY;R.SlopeX=SlopeX;R.SlopeY=SlopeY;R.Velocity=Velocity;
    auto FluxX=Buffer(16,Count,TEXT("TotalTransport.FluxX")),FluxY=Buffer(16,Count,TEXT("TotalTransport.FluxY"));
    auto FoamFlux=Buffer(8,Count,TEXT("TotalTransport.FoamFlux"));
    auto Flattened=Buffer(4,Count,TEXT("TotalTransport.Flattened"));
    auto ShorelineFactors=bContinuousShoreline?Buffer(8,Count,TEXT("TotalTransport.ShorelineFactors")):nullptr;
    auto CorrectionX=Buffer(8,Count,TEXT("TotalTransport.CorrectionX")),CorrectionY=Buffer(8,Count,TEXT("TotalTransport.CorrectionY"));
    auto Partial=Buffer(8,Groups,TEXT("TotalTransport.Partial"));
    AddClearUAVPass(Graph,Graph.CreateUAV(R.Diagnostics),0u);
    for(int32 Phase=0;Phase<6;++Phase)
    {
        auto* P=Graph.AllocParameters<FRaftSimTotalDepthTransportCS::FParameters>();
        P->GridSize=Size;P->CellMeters=CellMeters;P->Periodic=bPeriodic;P->SecondOrder=bSecondOrder;P->PartialCount=Groups;
        P->State=Graph.CreateSRV(State);P->Bed=Graph.CreateSRV(Bed);
        P->ExteriorState=bExterior?Graph.CreateSRV(ExteriorState):nullptr;
        P->ExteriorBed=bExterior?Graph.CreateSRV(ExteriorBed):nullptr;
        P->BoundaryFlux=bExterior?Graph.CreateUAV(R.BoundaryFlux):nullptr;
        P->Velocity=Graph.CreateUAV(Velocity);P->Geometry=Graph.CreateUAV(R.Geometry);P->PhysicalBedSlope=Graph.CreateUAV(R.PhysicalBedSlope);
        P->RawX=Graph.CreateUAV(RawX);P->RawY=Graph.CreateUAV(RawY);P->SlopeX=Graph.CreateUAV(SlopeX);P->SlopeY=Graph.CreateUAV(SlopeY);
        P->FluxX=Graph.CreateUAV(FluxX);P->FluxY=Graph.CreateUAV(FluxY);P->CorrectionX=Graph.CreateUAV(CorrectionX);P->CorrectionY=Graph.CreateUAV(CorrectionY);
        P->FoamFlux=Graph.CreateUAV(FoamFlux);
        P->Flattened=Graph.CreateUAV(Flattened);
        P->ShorelineFactors=bContinuousShoreline?Graph.CreateUAV(ShorelineFactors):nullptr;
        P->Pairs=Graph.CreateUAV(R.Pairs);P->HydroRate=Graph.CreateUAV(R.HydroRate);P->Partial=Graph.CreateUAV(Partial);
        P->CFL=Graph.CreateUAV(R.CFL);P->Diagnostics=Graph.CreateUAV(R.Diagnostics);
        FRaftSimTotalDepthTransportCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimTotalDepthTransportCS::FPhase>(Phase);
        Permutation.Set<FRaftSimTotalDepthTransportCS::FExterior>(bExterior);
        Permutation.Set<FRaftSimTotalDepthTransportCS::FContinuous>(bContinuousShoreline);
        Permutation.Set<FRaftSimTotalDepthTransportCS::FUnscaled>(bUnscaledShoreline);
        TShaderMapRef<FRaftSimTotalDepthTransportCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
        ClearUnusedGraphResources(Shader,P);
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Total Transport Phase%d",Phase),Shader,P,FIntVector(Phase==5?1:Groups,1,1));
    }
    return R;
}
