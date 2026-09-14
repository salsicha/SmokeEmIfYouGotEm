#pragma once
#include "RaftSimShorelineCrests.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace RaftSimCrestContextAudit
{
inline void Run(const TArray<FVector2D>& XY,const TArray<int32>& Triangles,const FRaftSimShorelineCrestInput& Input)
{
#if !UE_BUILD_SHIPPING
    static const FString Path=[]
    {FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimCrestContextAudit="),P);return P;}();
    static bool Done=false;
    if(Done || Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(Path))return;
    Done=true;
    FRaftSimSurfaceRefinement Kept,Shrinking;Kept.bMeasureStages=Shrinking.bMeasureStages=true;
    bool Passed=true;TArray<TSharedPtr<FJsonValue>> Pairs;
    for(int32 Pair=-2;Pair<8;++Pair)
    {
        double KeptMs=0,ShrinkingMs=0;
        const auto Measure=[&](FRaftSimSurfaceRefinement& Work,bool Keep,double& Milliseconds)
        {
            const double Start=FPlatformTime::Seconds();
            Passed&=Work.BuildAdaptive(XY,Triangles,Input.HeightAtWorldXYCm,3,.5f,Input.NonzeroRegionsCm,
                nullptr,true,true,Input.DetailSpanCm>0 ? &Input.DetailWindowCm : nullptr,Input.DetailSpanCm,true,true,Keep);
            Milliseconds=(FPlatformTime::Seconds()-Start)*1000.;
        };
        if(Pair%2==0){Measure(Kept,true,KeptMs);Measure(Shrinking,false,ShrinkingMs);}
        else {Measure(Shrinking,false,ShrinkingMs);Measure(Kept,true,KeptMs);}
        const bool Exact=Kept.MidpointParents==Shrinking.MidpointParents && Kept.Triangles==Shrinking.Triangles &&
            Kept.TriangleOrigins==Shrinking.TriangleOrigins;
        Passed&=Exact;
        if(Pair>=0)
        {
            auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("pair"),Pair);Row->SetBoolField(TEXT("exact"),Exact);
            Row->SetNumberField(TEXT("kept_ms"),KeptMs);Row->SetNumberField(TEXT("shrinking_ms"),ShrinkingMs);
            Row->SetNumberField(TEXT("kept_sample_ms"),Kept.SelectionSeconds*1000.);
            Row->SetNumberField(TEXT("shrinking_sample_ms"),Shrinking.SelectionSeconds*1000.);
            Row->SetNumberField(TEXT("kept_contexts_created"),double(Kept.ParallelContextsCreated));
            Row->SetNumberField(TEXT("shrinking_contexts_created"),double(Shrinking.ParallelContextsCreated));
            Row->SetNumberField(TEXT("kept_contexts_destroyed"),double(Kept.ParallelContextsDestroyed));
            Row->SetNumberField(TEXT("shrinking_contexts_destroyed"),double(Shrinking.ParallelContextsDestroyed));
            Row->SetNumberField(TEXT("kept_allocated_bytes"),double(Kept.GetRetainedMemoAllocatedBytes()));
            Row->SetNumberField(TEXT("shrinking_allocated_bytes"),double(Shrinking.GetRetainedMemoAllocatedBytes()));
            Pairs.Add(MakeShared<FJsonValueObject>(Row));
        }
    }
    auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("passed"),Passed);
    Report->SetStringField(TEXT("scope"),TEXT("Same actual playable XY, triangles and immutable profile; current height epoch on EVERY call. Two warmups then eight alternating-order pairs. Exact parents/triangles/owners. Repeated-input topology, not changing-topology, whole-frame, memory-budget or visual acceptance."));
    Report->SetNumberField(TEXT("frame"),double(GFrameCounter));Report->SetNumberField(TEXT("source_vertices"),XY.Num());
    Report->SetNumberField(TEXT("source_triangles"),Triangles.Num()/3);Report->SetNumberField(TEXT("midpoints"),Kept.MidpointParents.Num());
    Report->SetArrayField(TEXT("pairs"),Pairs);
    FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    if(Passed && Saved){UE_LOG(LogTemp,Display,TEXT("CrestContextAudit exact actual-input pairs saved: %s"),*Path);}
    else {UE_LOG(LogTemp,Error,TEXT("CrestContextAudit failed passed=%d saved=%d"),Passed,Saved);}
#endif
}
}
