#pragma once
#include "RaftSimShorelineCrests.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace RaftSimCrestRangeAudit
{
inline void Run(const TArray<FVector2D>& XY,const TArray<int32>& Triangles,
    const FRaftSimShorelineCrestInput& Input,const FRaftSimSurfaceRefinement& Production)
{
#if !UE_BUILD_SHIPPING
    static const FString Path=[]
    {FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestRangeAudit="),P);return P;}();
    static FRaftSimSurfaceRefinement Work[2];
    static TArray<TSharedPtr<FJsonValue>> Rows;
    static int32 Calls=0;
    static bool Done=false;
    if(Done || Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(Path))return;
    double Times[2]={};bool Passed=bool(Input.HeightRangeWidthAtWorldXYCm);
    for(int32 Offset=0;Offset<2;++Offset)
    {
        const int32 Kind=(Calls+Offset)%2;auto& W=Work[Kind];
        W.HeightRangeWidthCm=Kind ? Input.HeightRangeWidthAtWorldXYCm : TFunction<float(const FBox2D&)>();
        const double Start=FPlatformTime::Seconds();
        Passed&=W.BuildAdaptive(XY,Triangles,Input.HeightAtWorldXYCm,3,.5f,Input.NonzeroRegionsCm,
            nullptr,true,true,Input.DetailSpanCm>0 ? &Input.DetailWindowCm : nullptr,Input.DetailSpanCm,true);
        Times[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
    }
    TArray<FVector2D> Points[2];
    for(int32 I=0;I<2;++I)Work[I].Expand(XY,Points[I]);
    Passed &= Work[0].MidpointParents==Work[1].MidpointParents && Work[0].Triangles==Work[1].Triangles &&
        Work[0].TriangleOrigins==Work[1].TriangleOrigins && Points[0]==Points[1] &&
        Work[0].MidpointParents==Production.MidpointParents && Work[0].Triangles==Production.Triangles &&
        Work[0].TriangleOrigins==Production.TriangleOrigins;
    if(Calls>=2 || !Passed)
    {
        auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("pair"),Calls-2);
        Row->SetNumberField(TEXT("frame"),double(GFrameCounter));Row->SetBoolField(TEXT("exact"),Passed);
        Row->SetBoolField(TEXT("bounded_first"),Calls%2==1);
        Row->SetNumberField(TEXT("reference_ms"),Times[0]);Row->SetNumberField(TEXT("bounded_ms"),Times[1]);
        Row->SetNumberField(TEXT("vertices"),Points[0].Num());Row->SetNumberField(TEXT("triangles"),Work[0].Triangles.Num()/3);
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    ++Calls;
    if(Passed && Rows.Num()<64)return;
    Done=true;
    auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("exact"),Passed);
    Report->SetStringField(TEXT("scope"),TEXT("64 alternating actual changed-input builds after two warm builds; exact parents, triangles, ownership, expanded coordinates and production topology. Original quarter-point tolerance and detail-window refinement unchanged. Diagnostic output is never published; not FPS or release acceptance."));
    Report->SetArrayField(TEXT("pairs"),Rows);FString Json;
    FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    UE_LOG(LogTemp,Display,TEXT("CrestRangeAudit completed exact=%d saved=%d pairs=%d path=%s"),Passed,Saved,Rows.Num(),*Path);
#endif
}
}
