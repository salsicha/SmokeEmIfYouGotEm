#include "RaftSimLiquidParticleRoutingGPU.h"
#include "GlobalShader.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidParticleRouteCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidParticleRouteCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidParticleRouteCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Capacity)
        SHADER_PARAMETER(uint32,SourceOwner)
        SHADER_PARAMETER(uint32,Owners)
        SHADER_PARAMETER(uint32,FloatStride)
        SHADER_PARAMETER(uint32,IntStride)
        SHADER_PARAMETER(uint32,FloatComponents)
        SHADER_PARAMETER(uint32,IntComponents)
        SHADER_PARAMETER(uint32,PositionOffset)
        SHADER_PARAMETER(uint32,CountOffset)
        SHADER_PARAMETER(FIntPoint,ParentCells)
        SHADER_PARAMETER(FVector3f,LowerWorldCm)
        SHADER_PARAMETER(FVector3f,AxisX)
        SHADER_PARAMETER(FVector3f,AxisY)
        SHADER_PARAMETER(FVector2f,SpacingCm)
        SHADER_PARAMETER_SRV(Buffer<float>,Floats)
        SHADER_PARAMETER_SRV(Buffer<int>,Integers)
        SHADER_PARAMETER_UAV(RWBuffer<uint>,NativeCounts)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<int4>,Bounds)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Words)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint4>,Routes)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Counts)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidParticleRouteCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidParticleRouting.usf","MainCS",SF_Compute);

FRaftSimLiquidParticleRoutePlan RaftSimBuildLiquidParticleRoutePlan(FRDGBuilder& Graph,
    FIntPoint Parent,TConstArrayView<FIntRect> Regions,FVector Lower,FVector X,FVector Y,FVector2D Spacing,FString& Error)
{
    Error=TEXT("Particle routing requires complete nonoverlapping physical owners in one orthonormal frame");
    if (Parent.X<2 || Parent.Y<2 || int64(Parent.X)*Parent.Y>2000000 || Regions.Num()<2 || Regions.Num()>16 ||
        Lower.ContainsNaN() || X.ContainsNaN() || Y.ContainsNaN() || !FMath::IsFinite(Spacing.X) || !FMath::IsFinite(Spacing.Y) ||
        Spacing.X<=0 || Spacing.Y<=0 || !FMath::IsNearlyEqual(X.SizeSquared(),1.,1e-9) ||
        !FMath::IsNearlyEqual(Y.SizeSquared(),1.,1e-9) || FMath::Abs(FVector::DotProduct(X,Y))>1e-9 || X.Z!=0 || Y.Z!=0) return {};
    TBitArray<> Covered(false,Parent.X*Parent.Y);TArray<FIntVector4> Bounds;
    for (const auto& R:Regions)
    {
        if (R.Min.X<0 || R.Min.Y<0 || R.Max.X>Parent.X || R.Max.Y>Parent.Y || R.Width()<1 || R.Height()<1) return {};
        for (int32 J=R.Min.Y;J<R.Max.Y;++J) for (int32 I=R.Min.X;I<R.Max.X;++I)
        { const int32 K=J*Parent.X+I;if(Covered[K]) return {};Covered[K]=true; }
        Bounds.Emplace(R.Min.X,R.Min.Y,R.Max.X,R.Max.Y);
    }
    if (Covered.CountSetBits()!=Covered.Num()) return {};
    FRaftSimLiquidParticleRoutePlan P;
    P.Bounds=CreateStructuredBuffer(Graph,TEXT("LiquidRoute.PhysicalOwners"),TConstArrayView<FIntVector4>(Bounds));
    P.Owners=Regions.Num();P.ParentCells=Parent;P.LowerWorldCm=FVector3f(Lower);
    P.AxisX=FVector3f(X);P.AxisY=FVector3f(Y);P.SpacingCm=FVector2f(Spacing);
    Error.Reset();return P;
}

FRaftSimLiquidParticleRoutePacket RaftSimStageLiquidParticleRoutes(FRDGBuilder& Graph,
    const FRaftSimLiquidParticleRoutePlan& Plan,uint32 SourceOwner,
    FRHIShaderResourceView* Floats,FRHIShaderResourceView* Integers,FRHIUnorderedAccessView* NativeCounts,
    uint32 CountOffset,uint32 FloatStride,uint32 IntStride,uint32 FloatComponents,uint32 IntComponents,
    uint32 HalfComponents,uint32 PositionOffset,uint32 Capacity,FString& Error)
{
    Error=TEXT("Invalid bounded native particle routing ABI; no native state changed");
    if (!Plan.Bounds || SourceOwner>=Plan.Owners || !Floats || !Integers || !NativeCounts || CountOffset==INDEX_NONE ||
        Capacity==0 || Capacity>262144 || FloatComponents<3 || FloatComponents>128 || IntComponents<1 || IntComponents>128 ||
        HalfComponents || PositionOffset>FloatComponents-3 || FloatStride<Capacity || IntStride<Capacity ||
        uint64(FloatStride)*FloatComponents>MAX_uint32 || uint64(IntStride)*IntComponents>MAX_uint32) return {};
    auto Make=[&](const TCHAR* Name,uint32 Stride,uint32 N)
    { auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,N);D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name); };
    FRaftSimLiquidParticleRoutePacket R;
    R.Capacity=Capacity;R.FloatComponents=FloatComponents;R.IntComponents=IntComponents;
    R.Words=Make(TEXT("LiquidRoute.FullNativeWords"),4,Capacity*(FloatComponents+IntComponents));
    R.Routes=Make(TEXT("LiquidRoute.Candidates"),16,Capacity);
    // owner counts, exterior count, invalid count, source live count.
    R.Counts=Make(TEXT("LiquidRoute.Accounting"),4,Plan.Owners+3);
    AddClearUAVPass(Graph,Graph.CreateUAV(R.Counts),0);
    auto* P=Graph.AllocParameters<FRaftSimLiquidParticleRouteCS::FParameters>();
    P->Capacity=Capacity;P->SourceOwner=SourceOwner;P->Owners=Plan.Owners;
    P->FloatStride=FloatStride;P->IntStride=IntStride;P->FloatComponents=FloatComponents;P->IntComponents=IntComponents;
    P->PositionOffset=PositionOffset;P->CountOffset=CountOffset;P->ParentCells=Plan.ParentCells;
    P->LowerWorldCm=Plan.LowerWorldCm;P->AxisX=Plan.AxisX;P->AxisY=Plan.AxisY;P->SpacingCm=Plan.SpacingCm;
    P->Floats=Floats;P->Integers=Integers;P->NativeCounts=NativeCounts;P->Bounds=Graph.CreateSRV(Plan.Bounds);
    P->Words=Graph.CreateUAV(R.Words);P->Routes=Graph.CreateUAV(R.Routes);P->Counts=Graph.CreateUAV(R.Counts);
    TShaderMapRef<FRaftSimLiquidParticleRouteCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Full Native Particle Routing Candidates"),Shader,P,
        FIntVector(FMath::DivideAndRoundUp(Capacity,64u),1,1));
    Error.Reset();return R;
}
