#pragma once
#include "RaftSimIndexedBreakingProfile.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace RaftSimBreakingTileAudit
{
inline void Run(const FRaftSimIndexedBreakingProfile& Profile,TConstArrayView<FVector2D> Points)
{
#if !UE_BUILD_SHIPPING
    static const FString Path=[]
    {FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimBreakingTileAudit="),P);return P;}();
    static TArray<TSharedPtr<FJsonValue>> Rows;
    static int32 Calls=0;static bool Done=false;
    if(Done || Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(Path))return;
    TArray<float> Heights[2],Foams[2];double Times[2]={};
    for(int32 I=0;I<2;++I){Heights[I].SetNumUninitialized(Points.Num());Foams[I].SetNumUninitialized(Points.Num());}
    for(int32 Offset=0;Offset<2;++Offset)
    {
        const int32 Kind=(Calls+Offset)%2;const double Start=FPlatformTime::Seconds();
        for(int32 I=0;I<Points.Num();++I)Heights[Kind][I]=Profile.Sample(Points[I],&Foams[Kind][I],Kind==1);
        Times[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
    }
    const bool Exact=Heights[0]==Heights[1] && Foams[0]==Foams[1];
    int32 Nonzero=0;for(float V:Heights[0])Nonzero+=V!=0.f;
    if(Calls>=2 || !Exact)
    {
        auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("pair"),Calls-2);
        Row->SetNumberField(TEXT("frame"),double(GFrameCounter));Row->SetBoolField(TEXT("exact"),Exact);
        Row->SetBoolField(TEXT("dense_first"),Calls%2==1);
        Row->SetNumberField(TEXT("hash_ms"),Times[0]);Row->SetNumberField(TEXT("dense_ms"),Times[1]);
        Row->SetNumberField(TEXT("points"),Points.Num());Row->SetNumberField(TEXT("nonzero_heights"),Nonzero);
        Row->SetNumberField(TEXT("dense_tiles"),Profile.DenseTileCount());Row->SetNumberField(TEXT("hash_tiles"),Profile.TileCount());
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    ++Calls;if(Exact && Rows.Num()<64)return;Done=true;
    auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("exact"),Exact);
    Report->SetStringField(TEXT("scope"),TEXT("64 alternating-order full actual source-grid crest-height/foam evaluations after two warm calls, each with current immutable sites. Construction/copy cost excluded from paired sample times; inspect ordinary whole-frame timing too. No diagnostic arrays are published. Not motion or release acceptance."));
    Report->SetArrayField(TEXT("pairs"),Rows);FString Json;
    FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    UE_LOG(LogTemp,Display,TEXT("BreakingTileAudit completed exact=%d saved=%d pairs=%d path=%s"),Exact,Saved,Rows.Num(),*Path);
#endif
}
}
