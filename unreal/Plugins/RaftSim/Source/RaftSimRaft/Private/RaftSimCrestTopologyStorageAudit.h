#pragma once
#include "RaftSimCrestEdgeHashAudit.h"

namespace RaftSimCrestTopologyStorageAudit
{
inline void Run(const TArray<FVector2D>& XY,const TArray<int32>& Triangles,
    const FRaftSimShorelineCrestInput& Input,const FRaftSimSurfaceRefinement& Production)
{
#if !UE_BUILD_SHIPPING
    static const FString Path=[]{FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestTopologyStorageAudit="),P);return P;}();
    static FRaftSimSurfaceRefinement Work[2];
    static TArray<TSharedPtr<FJsonValue>> Rows;
    static TArray<int32> PreviousRoot;
    static int32 PreviousPoints=0,Calls=0;
    static bool Done=false;
    if(Done || Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(Path))return;
    const bool RootChanged=PreviousPoints!=XY.Num() || PreviousRoot!=Triangles;
    PreviousPoints=XY.Num();PreviousRoot=Triangles;
    double Times[2]={};bool Passed=true;
    for(int32 Offset=0;Offset<2;++Offset)
    {
        const int32 Kind=(Calls+Offset)%2;auto& W=Work[Kind];
        W.bRetainTopologyStorage=Kind==1;W.bIndexedEdges=true;W.bMeasureStages=true;
        W.HeightRangeWidthCm=Production.HeightRangeWidthCm;
        const double Start=FPlatformTime::Seconds();
        Passed&=W.BuildAdaptive(XY,Triangles,Input.HeightAtWorldXYCm,3,.5f,Input.NonzeroRegionsCm,
            nullptr,true,true,Input.DetailSpanCm>0 ? &Input.DetailWindowCm : nullptr,Input.DetailSpanCm,true);
        Times[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
        W.HeightRangeWidthCm={};
    }
    TArray<FVector2D> Points[2];
    for(int32 I=0;I<2;++I)Work[I].Expand(XY,Points[I]);
    Passed &= Work[0].MidpointParents==Work[1].MidpointParents && Work[0].Triangles==Work[1].Triangles &&
        Work[0].TriangleOrigins==Work[1].TriangleOrigins && Points[0]==Points[1] &&
        Work[0].TopologyBuildCount==Work[1].TopologyBuildCount && Work[0].TopologyReuseCount==Work[1].TopologyReuseCount &&
        Work[0].MidpointParents==Production.MidpointParents && Work[0].Triangles==Production.Triangles &&
        Work[0].TriangleOrigins==Production.TriangleOrigins;
    if(Calls>=2 || !Passed)
    {
        auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("pair"),Calls-2);
        Row->SetNumberField(TEXT("frame"),double(GFrameCounter));Row->SetBoolField(TEXT("exact"),Passed);
        Row->SetBoolField(TEXT("retained_first"),Calls%2==1);Row->SetBoolField(TEXT("root_changed"),RootChanged);
        Row->SetNumberField(TEXT("legacy_ms"),Times[0]);Row->SetNumberField(TEXT("retained_ms"),Times[1]);
        Row->SetNumberField(TEXT("legacy_assembly_ms"),Work[0].AssemblySeconds*1000.);
        Row->SetNumberField(TEXT("retained_assembly_ms"),Work[1].AssemblySeconds*1000.);
        Row->SetNumberField(TEXT("legacy_storage_bytes"),double(Work[0].GetTopologyAllocatedBytes()));
        Row->SetNumberField(TEXT("retained_storage_bytes"),double(Work[1].GetTopologyAllocatedBytes()));
        Row->SetNumberField(TEXT("vertices"),Points[0].Num());Row->SetNumberField(TEXT("triangles"),Work[0].Triangles.Num()/3);
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    ++Calls;
    if(Passed && Rows.Num()<64)return;
    Done=true;
    auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("exact"),Passed);
    Report->SetStringField(TEXT("scope"),TEXT("64 alternating-order actual changed-input whole builds after two warm builds; exact ordered parents, triangles, owners, expanded coordinates, build/reuse counters and production topology. Capacity only; every selection and profile sample remains current. Not ordinary FPS, physics or release acceptance."));
    Report->SetArrayField(TEXT("pairs"),Rows);FString Json;
    FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    UE_LOG(LogTemp,Display,TEXT("CrestTopologyStorageAudit completed exact=%d saved=%d pairs=%d path=%s"),Passed,Saved,Rows.Num(),*Path);
#endif
}
}
