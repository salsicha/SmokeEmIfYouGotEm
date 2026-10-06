#pragma once
#include "RaftSimShorelineCrests.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace RaftSimFlatMemoAudit
{
inline bool Enabled()
{
#if !UE_BUILD_SHIPPING
    static const bool Requested=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFlatMemoAudit"));
    return Requested && GFrameCounter>=100 && GFrameCounter<=250;
#else
    return false;
#endif
}
inline void Unchanged()
{if(Enabled())UE_LOG(LogTemp,Display,TEXT("FlatMemoAudit unchanged frame=%llu"),GFrameCounter);}
inline void Run(const TArray<FVector2D>& XY,const TArray<int32>& Triangles,const FRaftSimShorelineCrestInput& Input)
{
#if !UE_BUILD_SHIPPING
    if(!Enabled())return;
    static FRaftSimSurfaceRefinement Work[2];double Times[2]={};bool Passed=true;
    for(int32 Offset=0;Offset<2;++Offset)
    {
        const int32 I=int32((GFrameCounter+Offset)%2);auto& W=Work[I];W.bFlatCoordinateMemo=I==1;
        const double Started=FPlatformTime::Seconds();
        Passed&=W.BuildAdaptive(XY,Triangles,Input.HeightAtWorldXYCm,3,.5f,Input.NonzeroRegionsCm,
            nullptr,true,true,Input.DetailSpanCm>0 ? &Input.DetailWindowCm : nullptr,Input.DetailSpanCm,true,true,true,false);
        Times[I]=(FPlatformTime::Seconds()-Started)*1000.;
    }
    TArray<FVector2D> A,B;Work[0].Expand(XY,A);Work[1].Expand(XY,B);
    Passed&=Work[0].MidpointParents==Work[1].MidpointParents && Work[0].Triangles==Work[1].Triangles &&
        Work[0].TriangleOrigins==Work[1].TriangleOrigins && A==B;
    if(!Passed){UE_LOG(LogTemp,Error,TEXT("FlatMemoAudit mismatch frame=%llu"),GFrameCounter);return;}
    UE_LOG(LogTemp,Display,TEXT("FlatMemoAudit exact frame=%llu vertices=%d triangles=%d map_ms=%.6f flat_ms=%.6f flat_first=%d map_bytes=%.0f flat_bytes=%.0f"),
        GFrameCounter,A.Num(),Work[0].Triangles.Num()/3,Times[0],Times[1],int32(GFrameCounter%2),
        Work[0].GetRetainedMemoAllocatedBytes(),Work[1].GetRetainedMemoAllocatedBytes());
#endif
}
}
