#include "RaftSimLiquidDensityGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidDensityCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidDensityCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidDensityCS,FGlobalShader);
    class FStage : SHADER_PERMUTATION_INT("RAFTSIM_DENSITY_STAGE",6);
    class FCountUav : SHADER_PERMUTATION_BOOL("RAFTSIM_COUNT_UAV");
    using FPermutationDomain=TShaderPermutationDomain<FStage,FCountUav>;
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,ClockIndex)
        SHADER_PARAMETER(uint32,ClockHasTick)
        SHADER_PARAMETER_RDG_TEXTURE(Texture3D<float4>,ClockSurface)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,ClockTimeline)
        SHADER_PARAMETER(FIntVector,GridSize)
        SHADER_PARAMETER(FIntVector,BinSize)
        SHADER_PARAMETER(FVector3f,MinimumMeters)
        SHADER_PARAMETER(FVector3f,BinMinimumMeters)
        SHADER_PARAMETER(FVector3f,ExtentMeters)
        SHADER_PARAMETER(float,RadiusMeters)
        SHADER_PARAMETER(float,FootprintMeters)
        SHADER_PARAMETER(uint32,SmoothSparse)
        SHADER_PARAMETER(uint32,Capacity)
        SHADER_PARAMETER(uint32,UseCountBuffer)
        SHADER_PARAMETER(uint32,CountOffset)
        SHADER_PARAMETER(uint32,FloatStride)
        SHADER_PARAMETER(uint32,PositionOffset)
        SHADER_PARAMETER(uint32,SourceCountOffset)
        SHADER_PARAMETER(FMatrix44f,SimulationToLocalCm)
        SHADER_PARAMETER(float,PackedUnitsScale)
        SHADER_PARAMETER_SRV(Buffer<float>,NiagaraFloats)
        SHADER_PARAMETER_SRV(Buffer<uint>,NiagaraCounts)
        SHADER_PARAMETER_UAV(RWBuffer<uint>,NiagaraCountsUav)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,PackedPositions)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,PackedCount)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float4>,Positions)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,CountBuffer)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Heads)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Next)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,KernelRows)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<float4>,Bounds)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,DensityFixed)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Diagnostics)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture3D<float>,Scalar)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidDensityCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidDensity.usf","MainCS",SF_Compute);

void RaftSimRecordLiquidClockGPU(FRDGBuilder& Graph,FRDGTextureRef Surface,
    FRDGBufferRef Timeline,uint32 Index,bool HasTick)
{
    check(Surface && Timeline && Index<Timeline->Desc.NumElements);
    auto* P=Graph.AllocParameters<FRaftSimLiquidDensityCS::FParameters>();
    P->ClockSurface=Surface;P->ClockTimeline=Graph.CreateUAV(Timeline);P->ClockIndex=Index;P->ClockHasTick=HasTick;
    FRaftSimLiquidDensityCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimLiquidDensityCS::FStage>(5);
    TShaderMapRef<FRaftSimLiquidDensityCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
    ClearUnusedGraphResources(Shader,P);
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Actual Liquid Clock"),Shader,P,FIntVector(1,1,1));
}

FRDGBufferRef RaftSimPackLiquidParticlesGPU(FRDGBuilder& Graph,FRHIShaderResourceView* Floats,
    FRHIShaderResourceView* Counts,uint32 FloatStride,uint32 PositionOffset,uint32 SourceCountOffset,
    uint32 Capacity,FMatrix44f SimulationToLocalCm,FRDGBufferRef& PackedCount,FRHIUnorderedAccessView* CountsInUavState,float PackedUnitsScale)
{
    if (!Floats || !Counts || !Capacity || Capacity>262144 || FloatStride<Capacity || !FMath::IsFinite(PackedUnitsScale) || PackedUnitsScale<=0) return nullptr;
    auto PositionDesc=FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f),Capacity);PositionDesc.Usage|=BUF_SourceCopy;
    auto CountDesc=FRDGBufferDesc::CreateStructuredDesc(sizeof(uint32),1);CountDesc.Usage|=BUF_SourceCopy;
    auto Output=Graph.CreateBuffer(PositionDesc,TEXT("LiquidDensity.LivePositions"));
    PackedCount=Graph.CreateBuffer(CountDesc,TEXT("LiquidDensity.LiveCount"));
    auto* P=Graph.AllocParameters<FRaftSimLiquidDensityCS::FParameters>();
    P->Capacity=Capacity;P->NiagaraFloats=Floats;P->NiagaraCounts=Counts;P->FloatStride=FloatStride;
    P->NiagaraCountsUav=CountsInUavState;
    P->PositionOffset=PositionOffset;P->SourceCountOffset=SourceCountOffset;P->SimulationToLocalCm=SimulationToLocalCm;
    P->PackedUnitsScale=PackedUnitsScale;
    P->PackedPositions=Graph.CreateUAV(Output);P->PackedCount=Graph.CreateUAV(PackedCount);
    FRaftSimLiquidDensityCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimLiquidDensityCS::FStage>(4);
    Permutation.Set<FRaftSimLiquidDensityCS::FCountUav>(CountsInUavState!=nullptr);
    TShaderMapRef<FRaftSimLiquidDensityCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
    ClearUnusedGraphResources(Shader,P);
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Pack Current Niagara Particles"),Shader,P,FIntVector(FMath::DivideAndRoundUp(Capacity,64u),1,1));
    return Output;
}

FRaftSimLiquidDensityResult RaftSimLiquidDensityGPU(FRDGBuilder& Graph,FRDGBufferRef Positions,
    uint32 Capacity,FRDGBufferRef CountBuffer,uint32 CountOffset,FVector3f MinimumMeters,
    FVector3f ExtentMeters,FIntVector Cells,float RadiusMeters,float FootprintMeters,FString& Error,bool SmoothSparse)
{
    if (!Positions || Capacity==0 || Capacity>262144 || Positions->Desc.BytesPerElement!=sizeof(FVector4f) ||
        Positions->Desc.NumElements<Capacity || Cells.GetMin()<2 || int64(Cells.X)*Cells.Y*Cells.Z>2000000 ||
        !FMath::IsFinite(RadiusMeters) || RadiusMeters<=0 || !FMath::IsFinite(FootprintMeters) || FootprintMeters<=0 ||
        ExtentMeters.ContainsNaN() || MinimumMeters.ContainsNaN() || ExtentMeters.GetMin()<=0 ||
        (CountBuffer && (CountBuffer->Desc.BytesPerElement!=sizeof(uint32) || CountOffset>=CountBuffer->Desc.NumElements)))
    { Error=TEXT("Invalid bounded GPU liquid density domain or particle buffer");return {}; }
    const float Support=2*RadiusMeters;
    // A kernel's largest possible covariance eigenvalue is <= support^2.
    // Include every center that could affect the render box, plus its fitting
    // neighborhood; do not cut kernels at the numeric window boundary.
    const float Halo=Support+FMath::Sqrt(FMath::Square(RadiusMeters/.15)+FootprintMeters*FootprintMeters/.9f);
    const FVector3f BinMinimum=MinimumMeters-FVector3f(Halo),BinExtent=ExtentMeters+FVector3f(2*Halo);
    const FIntVector Bins(FMath::CeilToInt(BinExtent.X/Support),FMath::CeilToInt(BinExtent.Y/Support),FMath::CeilToInt(BinExtent.Z/Support));
    if (int64(Bins.X)*Bins.Y*Bins.Z>2000000)
    { Error=TEXT("GPU particle bin count exceeds supported budget");return {}; }
    const bool HasCount=CountBuffer!=nullptr;
    if (!CountBuffer) CountBuffer=CreateStructuredBuffer(Graph,TEXT("LiquidDensity.ConstantCount"),TConstArrayView<uint32>(&Capacity,1));
    auto MakeUint=[&](const TCHAR* Name,uint32 Count,bool Readback=false)
    { auto Desc=FRDGBufferDesc::CreateStructuredDesc(sizeof(uint32),Count);if (Readback) Desc.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(Desc,Name); };
    auto Heads=MakeUint(TEXT("LiquidDensity.Heads"),Bins.X*Bins.Y*Bins.Z);
    auto Next=MakeUint(TEXT("LiquidDensity.Next"),Capacity);
    auto Fixed=MakeUint(TEXT("LiquidDensity.FixedPoint"),Cells.X*Cells.Y*Cells.Z,true);
    auto Diagnostics=MakeUint(TEXT("LiquidDensity.Diagnostics"),4,true);
    auto RowDesc=FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f),Capacity*3);RowDesc.Usage|=BUF_SourceCopy;
    auto Rows=Graph.CreateBuffer(RowDesc,TEXT("LiquidDensity.Kernels"));
    auto Bounds=Graph.CreateBuffer(FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f),Capacity),TEXT("LiquidDensity.Bounds"));
    auto Scalar=Graph.CreateTexture(FRDGTextureDesc::Create3D(Cells,PF_R32_FLOAT,FClearValueBinding::None,TexCreate_ShaderResource|TexCreate_UAV),TEXT("LiquidDensity.Scalar"));
    AddClearUAVPass(Graph,Graph.CreateUAV(Heads),0xffffffff);
    AddClearUAVPass(Graph,Graph.CreateUAV(Next),0xffffffff);
    AddClearUAVPass(Graph,Graph.CreateUAV(Fixed),0);
    AddClearUAVPass(Graph,Graph.CreateUAV(Diagnostics),0);
    for (int32 Stage=0;Stage<4;++Stage)
    {
        auto* P=Graph.AllocParameters<FRaftSimLiquidDensityCS::FParameters>();
        P->GridSize=Cells;P->BinSize=Bins;P->MinimumMeters=MinimumMeters;P->ExtentMeters=ExtentMeters;
        P->BinMinimumMeters=BinMinimum;
        P->RadiusMeters=RadiusMeters;P->FootprintMeters=FootprintMeters;P->Capacity=Capacity;
        P->SmoothSparse=SmoothSparse;
        P->UseCountBuffer=HasCount;P->CountOffset=CountOffset;
        P->Positions=Graph.CreateSRV(Positions);P->CountBuffer=Graph.CreateSRV(CountBuffer);
        P->Heads=Graph.CreateUAV(Heads);P->Next=Graph.CreateUAV(Next);P->KernelRows=Graph.CreateUAV(Rows);
        P->Bounds=Graph.CreateUAV(Bounds);P->DensityFixed=Graph.CreateUAV(Fixed);P->Diagnostics=Graph.CreateUAV(Diagnostics);
        P->Scalar=Graph.CreateUAV(Scalar);
        FRaftSimLiquidDensityCS::FPermutationDomain Permutation;Permutation.Set<FRaftSimLiquidDensityCS::FStage>(Stage);
        TShaderMapRef<FRaftSimLiquidDensityCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel),Permutation);
        ClearUnusedGraphResources(Shader,P);
        const uint32 Count=Stage==3?Cells.X*Cells.Y*Cells.Z:Capacity;
        FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Liquid Density Stage%d",Stage),Shader,P,FIntVector(FMath::DivideAndRoundUp(Count,64u),1,1));
    }
    return {Scalar,Rows,Diagnostics,Fixed};
}
