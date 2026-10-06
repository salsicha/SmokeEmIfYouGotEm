#include "RaftSimLiquidParticleExitGPU.h"
#include "GlobalShader.h"
#include "RenderGraphUtils.h"
#include "ShaderParameterStruct.h"

class FRaftSimLiquidParticleExitCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FRaftSimLiquidParticleExitCS);
    SHADER_USE_PARAMETER_STRUCT(FRaftSimLiquidParticleExitCS,FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters,)
        SHADER_PARAMETER(uint32,Capacity)
        SHADER_PARAMETER(uint32,SourceOwner)
        SHADER_PARAMETER(uint32,Owners)
        SHADER_PARAMETER(uint32,PositionOffset)
        SHADER_PARAMETER(uint32,StepStartOffset)
        SHADER_PARAMETER(uint32,FloatComponents)
        SHADER_PARAMETER(uint32,IntComponents)
        SHADER_PARAMETER(uint32,TraceEnabled)
        SHADER_PARAMETER(uint32,NativeStep)
        SHADER_PARAMETER(FIntPoint,ParentCells)
        SHADER_PARAMETER(uint32,ResidualOuterBoundary)
        SHADER_PARAMETER(FVector3f,LowerWorldCm)
        SHADER_PARAMETER(FVector3f,AxisX)
        SHADER_PARAMETER(FVector3f,AxisY)
        SHADER_PARAMETER(FVector2f,SpacingCm)
        SHADER_PARAMETER(float,HeightCm)
        SHADER_PARAMETER(FIntVector4,BedOffsets)
        SHADER_PARAMETER(FIntVector4,BedCounts)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float2>,BedKnots)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<float3>,FaceRows)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,Words)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint4>,Routes)
        SHADER_PARAMETER_RDG_BUFFER_SRV(StructuredBuffer<uint>,SourceCounts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint4>,Records)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,Counts)
        SHADER_PARAMETER_RDG_BUFFER_UAV(RWStructuredBuffer<uint>,FirstRejection)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform,ERHIFeatureLevel::SM5); }
};
IMPLEMENT_GLOBAL_SHADER(FRaftSimLiquidParticleExitCS,"/Plugin/RaftSimWaterDetail/Private/RaftSimLiquidParticleExit.usf","MainCS",SF_Compute);

FRaftSimLiquidParticleExitPlan RaftSimBuildLiquidParticleExitPlan(FRDGBuilder& Graph,
    const FRaftSimLiquidParticleRoutePlan& Routing,float Height,TConstArrayView<FVector3f> Rows,FString& Error,
    const FRaftSimLiquidFaceBed* ExactBed)
{
    Error=TEXT("Exit policy requires a complete physical parent route plan and finite exterior face rows");
    if (!Routing.Bounds || Routing.Owners<2 || Routing.Owners>16 || Routing.ParentCells.X<2 || Routing.ParentCells.Y<2 ||
        !FMath::IsFinite(Height) || Height<=0 ||
        Rows.Num()!=2ll*(int64(Routing.ParentCells.X)+Routing.ParentCells.Y)) return {};
    for(const auto& R:Rows) if(R.ContainsNaN()) return {};
    FRaftSimLiquidParticleExitPlan P;P.Routing=Routing;P.HeightCm=Height;
    if(ExactBed)
    {
        Error=TEXT("Exact bed requires four finite, strictly increasing, gap-free physical face profiles");
        int32 End=0;
        if(ExactBed->Knots.Num()>16384) return {};
        for(int32 Face=0;Face<4;++Face)
        {
            const int32 N=ExactBed->Counts[Face],Begin=ExactBed->Offsets[Face];
            const int32 Tangent=Face<2?1:0;
            const float Extent=Routing.ParentCells[Tangent]*Routing.SpacingCm[Tangent];
            if(Begin!=End || N<2 || int64(Begin)+N>ExactBed->Knots.Num()) return {};
            if(ExactBed->Knots[Begin].X!=0 || ExactBed->Knots[Begin+N-1].X!=Extent) return {};
            for(int32 I=Begin;I<Begin+N;++I)
                if(ExactBed->Knots[I].ContainsNaN() || (I>Begin && ExactBed->Knots[I].X<=ExactBed->Knots[I-1].X)) return {};
            End=Begin+N;
        }
        if(End!=ExactBed->Knots.Num()) return {};
        P.BedOffsets=ExactBed->Offsets;P.BedCounts=ExactBed->Counts;
        P.BedKnots=CreateStructuredBuffer(Graph,TEXT("LiquidExit.ExactTerrainFaces"),TConstArrayView<FVector2f>(ExactBed->Knots));
    }
    else
    {
        const FVector2f Unused(0,0);
        P.BedKnots=CreateStructuredBuffer(Graph,TEXT("LiquidExit.UnusedExactTerrain"),TConstArrayView<FVector2f>(&Unused,1));
    }
    P.FaceRows=CreateStructuredBuffer(Graph,TEXT("LiquidExit.PhysicalParentFaces"),Rows);
    Error.Reset();return P;
}

FRaftSimLiquidParticleExitCandidates RaftSimClassifyLiquidParticleExits(FRDGBuilder& Graph,
    const FRaftSimLiquidParticleExitPlan& Plan,const FRaftSimLiquidParticleRoutePacket& Packet,
    uint32 Source,uint32 Position,uint32 Start,float Volume,FString& Error)
{
    Error=TEXT("Exit classifier requires full native segment words and routing counts; no native state changed");
    auto Size=[](FRDGBufferRef B,uint32 Stride,uint64 N)
    { return B && B->Desc.BytesPerElement==Stride && uint64(B->Desc.NumElements)>=FMath::Max(N,uint64(1)); };
    const auto& R=Plan.Routing;
    if(!Plan.FaceRows || !Plan.BedKnots || !R.Bounds || Source>=R.Owners || Packet.Capacity>262144 || !FMath::IsFinite(Volume) || Volume<=0 ||
        Packet.FloatComponents<6 || Packet.FloatComponents>128 || Packet.IntComponents<1 || Packet.IntComponents>128 ||
        Position>Packet.FloatComponents-3 || Start>Packet.FloatComponents-3 ||
        (Position<Start+3 && Start<Position+3) ||
        !Size(Packet.Words,4,uint64(Packet.Capacity)*(Packet.FloatComponents+Packet.IntComponents)) ||
        !Size(Packet.Routes,16,Packet.Capacity) || !Size(Packet.Counts,4,R.Owners+3)) return {};
    if(Plan.FirstRejectionTrace && (!Plan.NativeStep || !Size(Plan.FirstRejectionTrace,4,RaftSimLiquidExitTraceWords)))
    { Error=TEXT("First rejection latch requires a nonzero native step and complete fixed-size buffer");return {}; }
    auto Make=[&](const TCHAR* Name,uint32 Stride,uint32 N)
    { auto D=FRDGBufferDesc::CreateStructuredDesc(Stride,FMath::Max(N,1u));D.Usage|=BUF_SourceCopy;return Graph.CreateBuffer(D,Name); };
    FRaftSimLiquidParticleExitCandidates C;
    C.SourceWords=Packet.Words;C.SourceRoutes=Packet.Routes;C.SourceCounts=Packet.Counts;C.ParticleVolumeM3=Volume;
    C.Records=Make(TEXT("LiquidExit.SegmentCandidates"),16,Packet.Capacity);
    C.Counts=Make(TEXT("LiquidExit.Accounting"),4,8);AddClearUAVPass(Graph,Graph.CreateUAV(C.Counts),0);
    auto* P=Graph.AllocParameters<FRaftSimLiquidParticleExitCS::FParameters>();
    P->Capacity=Packet.Capacity;P->SourceOwner=Source;P->Owners=R.Owners;P->PositionOffset=Position;P->StepStartOffset=Start;
    P->FloatComponents=Packet.FloatComponents;P->IntComponents=Packet.IntComponents;
    P->TraceEnabled=Plan.FirstRejectionTrace?1:0;P->NativeStep=Plan.NativeStep;
    P->FirstRejection=Graph.CreateUAV(Plan.FirstRejectionTrace?Plan.FirstRejectionTrace:
        Make(TEXT("LiquidExit.UnusedFirstRejection"),4,RaftSimLiquidExitTraceWords));
    P->ParentCells=R.ParentCells;P->LowerWorldCm=R.LowerWorldCm;P->AxisX=R.AxisX;P->AxisY=R.AxisY;
    P->ResidualOuterBoundary=R.ResidualOuterBoundary?1u:0u;
    P->SpacingCm=R.SpacingCm;P->HeightCm=Plan.HeightCm;P->FaceRows=Graph.CreateSRV(Plan.FaceRows);
    P->BedOffsets=Plan.BedOffsets;P->BedCounts=Plan.BedCounts;P->BedKnots=Graph.CreateSRV(Plan.BedKnots);
    P->Words=Graph.CreateSRV(Packet.Words);P->Routes=Graph.CreateSRV(Packet.Routes);P->SourceCounts=Graph.CreateSRV(Packet.Counts);
    P->Records=Graph.CreateUAV(C.Records);P->Counts=Graph.CreateUAV(C.Counts);
    TShaderMapRef<FRaftSimLiquidParticleExitCS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(Graph,RDG_EVENT_NAME("RaftSim Physical Parent Exit Candidates"),Shader,P,
        FIntVector(FMath::DivideAndRoundUp(FMath::Max(Packet.Capacity,1u),64u),1,1));
    Error.Reset();return C;
}
