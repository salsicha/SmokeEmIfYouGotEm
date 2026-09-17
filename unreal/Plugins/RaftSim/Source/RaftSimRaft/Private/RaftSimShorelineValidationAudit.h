#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

namespace RaftSimShorelineValidationAudit
{
template<typename FCheck>
inline void Run(FCheck&& Check,int32 Vertices,bool Parallel)
{
#if !UE_BUILD_SHIPPING
    static const FString Path=[]
    {FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimShorelineValidationAudit="),P);return P;}();
    static int32 Calls=0;
    static bool Done=false;
    static TArray<TSharedPtr<FJsonValue>> Rows;
    if(Done || Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(Path))return;
    double Times[2]={};bool Valid[2]={},Reuse[2]={};
    for(int32 Offset=0;Offset<2;++Offset)
    {
        const int32 Kind=(Calls+Offset)%2;
        const double Start=FPlatformTime::Seconds();
        Valid[Kind]=Check(Kind==1,Reuse[Kind]);
        Times[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
    }
    const bool Exact=Valid[0]==Valid[1] && (!Valid[0] || Reuse[0]==Reuse[1]);
    if(Calls>=2 || !Exact)
    {
        auto Row=MakeShared<FJsonObject>();
        Row->SetNumberField(TEXT("pair"),Calls-2);Row->SetNumberField(TEXT("frame"),double(GFrameCounter));
        Row->SetNumberField(TEXT("vertices"),Vertices);Row->SetBoolField(TEXT("exact"),Exact);
        Row->SetBoolField(TEXT("candidate_first"),Calls%2==1);
        Row->SetBoolField(TEXT("valid"),Valid[0]);Row->SetBoolField(TEXT("reuse"),Reuse[0]);
        Row->SetNumberField(TEXT("reference_ms"),Times[0]);Row->SetNumberField(TEXT("candidate_ms"),Times[1]);
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    ++Calls;
    if(Exact && Rows.Num()<64)return;
    Done=true;
    auto Root=MakeShared<FJsonObject>();Root->SetBoolField(TEXT("exact"),Exact);
    Root->SetStringField(TEXT("schema"),TEXT("raftsim.shoreline_validation_pair.v1"));
    Root->SetStringField(TEXT("candidate_kind"),Parallel ? TEXT("parallel-fused") : TEXT("serial-fused"));
    Root->SetStringField(TEXT("scope"),TEXT("64 alternating-order actual current shoreline inputs after two warmups. Complete validation and exact reuse predicates, no output mutation. Not whole-frame FPS or visual acceptance."));
    Root->SetArrayField(TEXT("pairs"),Rows);FString Json;
    FJsonSerializer::Serialize(Root,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    UE_LOG(LogTemp,Display,TEXT("SHORELINE_VALIDATION_AUDIT exact=%d saved=%d pairs=%d path=%s"),Exact,Saved,Rows.Num(),*Path);
#endif
}
}
