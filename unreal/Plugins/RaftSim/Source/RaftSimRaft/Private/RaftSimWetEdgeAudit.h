#pragma once
#include "RaftSimWaterFlowFrame.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Crc.h"

namespace RaftSimWetEdgeAudit
{
inline TArray<int32> Evaluate(int32 Nx,int32 Ny,TConstArrayView<uint8> Wet,int32 Phase)
{
    // Qualified exact and faster in BOTH actual uses and both call orders.
    // Preserve the original queue for same-binary regression comparisons.
    static const bool Sweep=!FParse::Param(FCommandLine::Get(),TEXT("RaftSimReferenceWetEdges"));
#if !UE_BUILD_SHIPPING
    static const FString Path=[]
    {FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimWetEdgeSweepAudit="),P);return P;}();
    static TArray<TSharedPtr<FJsonValue>> Rows;
    static int32 Calls=0;
    static bool Done=false;
    // Spread samples across the descent, not one brief unchanged wet mask.
    if(!Done && !Path.IsEmpty() && GFrameCounter>=120 && GFrameCounter%16==8 && !FPaths::FileExists(Path))
    {
        TArray<int32> Values[2];double Times[2]={};
        for(int32 Offset=0;Offset<2;++Offset)
        {
            // Alternate per two-call refresh, so BOTH production phases
            // are measured first and second rather than confounding phase/order.
            const int32 Kind=(Calls/2+Offset)%2;
            const double Start=FPlatformTime::Seconds();
            Values[Kind]=RaftSimWaterFlowFrame::WetEdgeSteps(Nx,Ny,Wet,Kind==1);
            Times[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
        }
        const bool Exact=Values[0]==Values[1];
        if(Calls>=4 || !Exact)
        {
            auto Row=MakeShared<FJsonObject>();
            Row->SetNumberField(TEXT("pair"),Calls-4);
            Row->SetNumberField(TEXT("frame"),double(GFrameCounter));
            Row->SetNumberField(TEXT("phase"),Phase);
            Row->SetNumberField(TEXT("nx"),Nx);Row->SetNumberField(TEXT("ny"),Ny);
            Row->SetNumberField(TEXT("vertices"),Wet.Num());
            Row->SetNumberField(TEXT("mask_crc32"),FCrc::MemCrc32(Wet.GetData(),Wet.Num()));
            Row->SetBoolField(TEXT("exact"),Exact);Row->SetBoolField(TEXT("sweep_first"),Calls/2%2==1);
            Row->SetNumberField(TEXT("queue_ms"),Times[0]);Row->SetNumberField(TEXT("sweep_ms"),Times[1]);
            Rows.Add(MakeShared<FJsonValueObject>(Row));
        }
        ++Calls;
        if(!Exact || Rows.Num()==64)
        {
            Done=true;auto Report=MakeShared<FJsonObject>();
            Report->SetBoolField(TEXT("exact"),Exact);Report->SetArrayField(TEXT("pairs"),Rows);
            Report->SetStringField(TEXT("scope"),TEXT("Actual shore damping (phase 1) and terrain-probe band (phase 2), sampled every 16 engine frames; 64 comparisons after four warm calls, both orders within each phase; every integer distance exact. No mask, damping or probing gate changed. Not frame, visual or release acceptance."));
            FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
            const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
            if(Exact && Saved){UE_LOG(LogTemp,Display,TEXT("WetEdgeSweepAudit exact pairs=%d path=%s"),Rows.Num(),*Path);}
            else {UE_LOG(LogTemp,Error,TEXT("WetEdgeSweepAudit failed exact=%d saved=%d"),Exact,Saved);}
        }
        // A failed diagnostic never publishes mismatched candidate distances.
        return MoveTemp(Values[Sweep && Exact ? 1 : 0]);
    }
#endif
    return RaftSimWaterFlowFrame::WetEdgeSteps(Nx,Ny,Wet,Sweep);
}
}
