#pragma once
#include "RaftSimShorelineCrests.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

// Explicit diagnostic: same current input and profile, independent warm state
// for each scheduling variant. Never supplies geometry to ordinary gameplay.
namespace RaftSimCrestBatchAudit
{
inline bool Enabled()
{
#if !UE_BUILD_SHIPPING
    static const bool Requested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCrestBatchAudit"));
    return Requested && GFrameCounter>=100 && GFrameCounter<=250;
#else
    return false;
#endif
}
inline void Unchanged()
{
    if(Enabled())UE_LOG(LogTemp,Display,TEXT("CrestBatchAudit unchanged frame=%llu"),GFrameCounter);
}
inline void Run(const TArray<FVector2D>& XY,const TArray<int32>& Triangles,const FRaftSimShorelineCrestInput& Input)
{
#if !UE_BUILD_SHIPPING
    if(!Enabled())return;
    static FRaftSimSurfaceRefinement Work[5];
    constexpr int32 Sizes[]={128,32,64,256,512};
    double Times[5]={};
    bool Passed=true;
    // Rotate all five call positions; no permanently first baseline/candidate.
    for(int32 Offset=0;Offset<5;++Offset)
    {
        const int32 I=int32((GFrameCounter+Offset)%5);
        auto& W=Work[I];W.ParallelBatchSize=Sizes[I];W.bMeasureStages=true;
        const double Started=FPlatformTime::Seconds();
        Passed&=W.BuildAdaptive(XY,Triangles,Input.HeightAtWorldXYCm,3,.5f,Input.NonzeroRegionsCm,
            nullptr,true,true,Input.DetailSpanCm>0 ? &Input.DetailWindowCm : nullptr,Input.DetailSpanCm,true,true,true,false);
        Times[I]=(FPlatformTime::Seconds()-Started)*1000.;
    }
    TArray<FVector2D> ReferenceXY;Work[0].Expand(XY,ReferenceXY);
    for(int32 I=1;I<5;++I)
    {
        TArray<FVector2D> ActualXY;Work[I].Expand(XY,ActualXY);
        Passed&=Work[I].MidpointParents==Work[0].MidpointParents && Work[I].Triangles==Work[0].Triangles &&
            Work[I].TriangleOrigins==Work[0].TriangleOrigins && ActualXY==ReferenceXY;
    }
    if(!Passed){UE_LOG(LogTemp,Error,TEXT("CrestBatchAudit mismatch frame=%llu"),GFrameCounter);return;}
    for(int32 I=0;I<5;++I)
    {
        UE_LOG(LogTemp,Display,TEXT("CrestBatchAudit exact frame=%llu batch=%d order=%d total_ms=%.6f selection_ms=%.6f vertices=%d triangles=%d memo_bytes=%.0f"),
            GFrameCounter,Sizes[I],(I+5-int32(GFrameCounter%5))%5,Times[I],Work[I].SelectionSeconds*1000.,
            ReferenceXY.Num(),Work[I].Triangles.Num()/3,Work[I].GetRetainedMemoAllocatedBytes());
    }
#endif
}
}
