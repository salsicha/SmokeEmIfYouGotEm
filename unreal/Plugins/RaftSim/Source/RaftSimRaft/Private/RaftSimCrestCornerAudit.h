#pragma once
#include "RaftSimShorelineCrests.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace RaftSimCrestCornerAudit
{
inline void Run(const TArray<FVector2D>& XY,const TArray<int32>& Triangles,const FRaftSimShorelineCrestInput& Input)
{
#if !UE_BUILD_SHIPPING
    static const FString Path=[]
    {FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestCornerAudit="),P);return P;}();
    static bool Done=false;
    if(Done || Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(Path))return;
    Done=true;
    FRaftSimSurfaceRefinement Shared,Original;Shared.bMeasureStages=Original.bMeasureStages=true;
    bool Passed=true;TArray<TSharedPtr<FJsonValue>> Pairs;
    for(int32 Pair=-2;Pair<8;++Pair)
    {
        double SharedMs=0,OriginalMs=0;
        const auto Measure=[&](FRaftSimSurfaceRefinement& Work,bool Share,double& Milliseconds)
        {
            const double Start=FPlatformTime::Seconds();
            Passed&=Work.BuildAdaptive(XY,Triangles,Input.HeightAtWorldXYCm,3,.5f,Input.NonzeroRegionsCm,
                nullptr,true,true,Input.DetailSpanCm>0 ? &Input.DetailWindowCm : nullptr,Input.DetailSpanCm,true,true,true,Share);
            Milliseconds=(FPlatformTime::Seconds()-Start)*1000.;
        };
        if(Pair%2==0){Measure(Shared,true,SharedMs);Measure(Original,false,OriginalMs);}
        else {Measure(Original,false,OriginalMs);Measure(Shared,true,SharedMs);}
        const bool Exact=Shared.MidpointParents==Original.MidpointParents && Shared.Triangles==Original.Triangles &&
            Shared.TriangleOrigins==Original.TriangleOrigins;
        Passed&=Exact;
        if(Pair>=0)
        {
            auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("pair"),Pair);Row->SetBoolField(TEXT("exact"),Exact);
            Row->SetNumberField(TEXT("shared_ms"),SharedMs);Row->SetNumberField(TEXT("original_ms"),OriginalMs);
            Row->SetNumberField(TEXT("shared_selection_ms"),Shared.SelectionSeconds*1000.);
            Row->SetNumberField(TEXT("original_selection_ms"),Original.SelectionSeconds*1000.);
            Row->SetNumberField(TEXT("corner_samples"),double(Shared.SharedCornerSamples));
            Row->SetNumberField(TEXT("corner_reads"),double(Shared.SharedCornerReads));
            Pairs.Add(MakeShared<FJsonValueObject>(Row));
        }
    }
    TArray<FVector2D> A,B;Shared.Expand(XY,A);Original.Expand(XY,B);Passed&=A==B;
    auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("passed"),Passed);
    Report->SetStringField(TEXT("scope"),TEXT("Identical actual playable input. Per-build shared corner values versus original batch-local values; all intermediate samples and decisions retained. Two warmups/eight alternating pairs, exact topology/owners/coordinates. Not whole-frame or visual acceptance."));
    Report->SetNumberField(TEXT("frame"),double(GFrameCounter));Report->SetNumberField(TEXT("source_vertices"),XY.Num());
    Report->SetNumberField(TEXT("source_triangles"),Triangles.Num()/3);Report->SetNumberField(TEXT("midpoints"),Shared.MidpointParents.Num());
    Report->SetArrayField(TEXT("pairs"),Pairs);
    FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    if(Passed && Saved){UE_LOG(LogTemp,Display,TEXT("CrestCornerAudit exact actual-input pairs saved: %s"),*Path);}
    else {UE_LOG(LogTemp,Error,TEXT("CrestCornerAudit failed passed=%d saved=%d"),Passed,Saved);}
#endif
}
}
