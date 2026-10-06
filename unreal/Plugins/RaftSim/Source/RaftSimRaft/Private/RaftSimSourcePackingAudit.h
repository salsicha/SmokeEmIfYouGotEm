#pragma once
#include "RaftSimWaterSourcePacking.h"
#include "RaftSimCrestMidpointExpansion.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace RaftSimSourcePackingAudit
{
inline void Run(TConstArrayView<FVector> Positions,TConstArrayView<FVector> Normals,
    TConstArrayView<FLinearColor> Colors,TConstArrayView<FVector2D> UVs,
    TConstArrayView<FVector2D> Flow,TConstArrayView<FVector2D> Wake,
    TConstArrayView<FProcMeshTangent> Tangents,TConstArrayView<FVector2D> Transport,
    const TArray<FProcMeshVertex>& Production)
{
#if !UE_BUILD_SHIPPING
    static const bool bReuse=[]
    {FString P;return FParse::Value(FCommandLine::Get(),TEXT("RaftSimSourcePackingReuseAudit="),P);}();
    static const FString Path=[]
    {FString P;if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimSourcePackingReuseAudit="),P))
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimSourcePackingAudit="),P);return P;}();
    static TArray<TSharedPtr<FJsonValue>> Rows;
    static TArray<FProcMeshVertex> Retained;
    static int32 Calls=0;static bool Done=false;
    if(Done || Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(Path))return;
    // The reference always uses the original fresh output. Compare either
    // vector colors with fresh output or ORIGINAL colors with retained output.
    // Neither timed output is published; equality is outside timed regions.
    TArray<FProcMeshVertex> Work[2];double Times[2]={};bool Passed=true;
    auto& Candidate=bReuse ? Retained : Work[1];
    for(int32 Offset=0;Offset<2;++Offset)
    {
        const int32 Kind=(Calls+Offset)%2;
        const double Start=FPlatformTime::Seconds();
        auto& Output=Kind ? Candidate : Work[0];
        Passed &= RaftSimWaterSourcePacking::Pack(Positions,Normals,Colors,UVs,Flow,Wake,
            Tangents,Output,false,Transport,Kind==1 && !bReuse);
        Times[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
    }
    Passed &= Work[0].Num()==Candidate.Num() && Work[0].Num()==Production.Num();
    for(int32 I=0;Passed && I<Work[0].Num();++I)
        Passed=FRaftSimCrestMidpointExpansion::EqualAttributes(Work[0][I],Candidate[I]) &&
               FRaftSimCrestMidpointExpansion::EqualAttributes(Work[0][I],Production[I]);
    if(Calls>=2 || !Passed)
    {
        auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("pair"),Calls-2);
        Row->SetNumberField(TEXT("frame"),double(GFrameCounter));Row->SetBoolField(TEXT("exact"),Passed);
        Row->SetBoolField(TEXT("candidate_first"),Calls%2==1);
        Row->SetNumberField(TEXT("reference_ms"),Times[0]);Row->SetNumberField(TEXT("candidate_ms"),Times[1]);
        Row->SetNumberField(TEXT("vertices"),Work[0].Num());Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    ++Calls;
    if(Passed && Rows.Num()<64)return;
    Done=true;auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("exact"),Passed);
    Report->SetStringField(TEXT("schema"),TEXT("raftsim.source_packing_pair.v2"));
    Report->SetStringField(TEXT("candidate_kind"),bReuse ? TEXT("retained-output") : TEXT("vector-color"));
    Report->SetStringField(TEXT("scope"),TEXT("64 alternating live-input pairs after two warm calls. Reference allocates fresh; candidate_kind specifies retained output OR fresh vector-color packing. Every attribute against reference and production; no audit output published. Not FPS, shape or release acceptance."));
    Report->SetArrayField(TEXT("pairs"),Rows);FString Json;
    FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    Retained.Empty();
    UE_LOG(LogTemp,Display,TEXT("SourcePackingAudit completed exact=%d saved=%d pairs=%d path=%s"),Passed,Saved,Rows.Num(),*Path);
#endif
}
}
