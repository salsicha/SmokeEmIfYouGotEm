#pragma once
#include "RaftSimCrestBoundaries.h"
#include "RaftSimCrestEdgeHashAudit.h"

namespace RaftSimCrestBoundaryAudit
{
inline void Run(const TArray<int32>& Triangles,const TArray<FIntPoint>& Parents,
    int32 SourceCount,const TArray<uint8>& Production)
{
#if !UE_BUILD_SHIPPING
    static const FString Path=[](){FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestBoundaryAudit="),P);return P;}();
    static TArray<TSharedPtr<FJsonValue>> Rows;
    static int32 Calls=0;static bool Done=false;
    if(Done || Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(Path))return;
    TArray<uint8> Results[2];double Times[2]={};
    for(int32 Offset=0;Offset<2;++Offset)
    {
        const int32 Kind=(Calls+Offset)%2;const double Start=FPlatformTime::Seconds();
        if(Kind)RaftSimCrestBoundaries::Indexed(Triangles,Parents,SourceCount,Results[Kind]);
        else RaftSimCrestBoundaries::Reference(Triangles,Parents,SourceCount,Results[Kind]);
        Times[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
    }
    const bool Exact=Results[0]==Results[1] && Results[0]==Production;
    if(Calls>=2 || !Exact)
    {
        auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("pair"),Calls-2);
        Row->SetNumberField(TEXT("frame"),double(GFrameCounter));Row->SetBoolField(TEXT("exact"),Exact);
        Row->SetBoolField(TEXT("indexed_first"),Calls%2==1);
        Row->SetNumberField(TEXT("reference_ms"),Times[0]);Row->SetNumberField(TEXT("indexed_ms"),Times[1]);
        Row->SetNumberField(TEXT("source_vertices"),SourceCount);Row->SetNumberField(TEXT("midpoints"),Parents.Num());
        Row->SetNumberField(TEXT("triangles"),Triangles.Num()/3);
        int32 Boundaries=0;for(uint8 Value:Production)Boundaries+=Value;
        Row->SetNumberField(TEXT("boundary_midpoints"),Boundaries);Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    ++Calls;if(Exact && Rows.Num()<64)return;
    Done=true;auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("exact"),Exact);
    Report->SetStringField(TEXT("scope"),TEXT("64 alternating-order actual topology boundary classifications after two warm calls; complete allocation/counting/propagation, exact reference and production flags. Not whole-frame FPS, physical or visual acceptance."));
    Report->SetArrayField(TEXT("pairs"),Rows);FString Json;
    FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    UE_LOG(LogTemp,Display,TEXT("CrestBoundaryAudit completed exact=%d saved=%d pairs=%d path=%s"),Exact,Saved,Rows.Num(),*Path);
#endif
}
}
