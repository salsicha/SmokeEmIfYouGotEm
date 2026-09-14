#pragma once
#include "RaftSimShorelineCrests.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace RaftSimCrestLookupAudit
{
inline void Run(const TArray<FVector2D>& XY,const TArray<int32>& Triangles,const FRaftSimShorelineCrestInput& Input)
{
#if !UE_BUILD_SHIPPING
    static const FString Path=[]
    {FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestLookupAudit="),P);return P;}();
    static bool Done=false;
    if(Done || Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(Path))return;
    Done=true;
    FRaftSimSurfaceRefinement Fast,Legacy;Fast.bMeasureStages=Legacy.bMeasureStages=true;
    auto Evaluate=[&](FRaftSimSurfaceRefinement& Work,bool FastHash)
    {
        return Work.BuildAdaptive(XY,Triangles,Input.HeightAtWorldXYCm,3,.5f,Input.NonzeroRegionsCm,
            nullptr,true,true,Input.DetailSpanCm>0 ? &Input.DetailWindowCm : nullptr,Input.DetailSpanCm,true,FastHash);
    };
    bool Passed=true;TArray<TSharedPtr<FJsonValue>> Pairs;
    for(int32 Pair=-2;Pair<8;++Pair)
    {
        double FastMs=0,LegacyMs=0;
        auto Measure=[&](FRaftSimSurfaceRefinement& Work,bool FastHash,double& Milliseconds)
        {const double Start=FPlatformTime::Seconds();Passed&=Evaluate(Work,FastHash);Milliseconds=(FPlatformTime::Seconds()-Start)*1000.;};
        if(Pair%2==0){Measure(Fast,true,FastMs);Measure(Legacy,false,LegacyMs);}
        else {Measure(Legacy,false,LegacyMs);Measure(Fast,true,FastMs);}
        const bool Exact=Fast.MidpointParents==Legacy.MidpointParents && Fast.Triangles==Legacy.Triangles &&
            Fast.TriangleOrigins==Legacy.TriangleOrigins;
        Passed&=Exact;
        if(Pair>=0)
        {
            auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("pair"),Pair);Row->SetBoolField(TEXT("exact"),Exact);
            Row->SetNumberField(TEXT("direct_hash_ms"),FastMs);Row->SetNumberField(TEXT("legacy_crc_ms"),LegacyMs);
            Row->SetNumberField(TEXT("direct_sample_ms"),Fast.SelectionSeconds*1000.);
            Row->SetNumberField(TEXT("legacy_sample_ms"),Legacy.SelectionSeconds*1000.);
            Row->SetNumberField(TEXT("direct_assembly_ms"),Fast.AssemblySeconds*1000.);
            Row->SetNumberField(TEXT("legacy_assembly_ms"),Legacy.AssemblySeconds*1000.);
            Pairs.Add(MakeShared<FJsonValueObject>(Row));
        }
    }
    auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("passed"),Passed);
    Report->SetStringField(TEXT("scope"),TEXT("Same actual playable XY, triangles and immutable height function; two warmup pairs then eight alternating-order pairs. Exact parent/triangle/owner arrays. Cached topology on repeated identical input; not whole-frame, changing-topology or release performance acceptance."));
    Report->SetNumberField(TEXT("frame"),double(GFrameCounter));Report->SetNumberField(TEXT("source_vertices"),XY.Num());
    Report->SetNumberField(TEXT("source_triangles"),Triangles.Num()/3);Report->SetNumberField(TEXT("midpoints"),Fast.MidpointParents.Num());
    Report->SetArrayField(TEXT("pairs"),Pairs);
    FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    if(Passed && Saved){UE_LOG(LogTemp,Display,TEXT("CrestLookupAudit exact actual-input pairs saved: %s"),*Path);}
    else {UE_LOG(LogTemp,Error,TEXT("CrestLookupAudit failed: passed=%d saved=%d"),Passed,Saved);}
#endif
}
}
