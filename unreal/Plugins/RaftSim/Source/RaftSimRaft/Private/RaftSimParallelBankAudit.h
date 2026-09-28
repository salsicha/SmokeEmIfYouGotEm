#pragma once
#include "RaftSimWaterShoreline.h"
#include "RaftSimCrestMidpointExpansion.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

namespace RaftSimParallelBankAudit
{
inline bool Run(int32 Nx,int32 Ny,const TArray<FProcMeshVertex>& Source,
    TConstArrayView<uint8> Wet,TConstArrayView<uint8> Available,TConstArrayView<float> H,
    TConstArrayView<float> Bed,bool Compact,bool Opposite,bool Curved)
{
#if !UE_BUILD_SHIPPING
    static const FString Path=[]{FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimParallelBankAudit="),P);return P;}();
    static RaftSimWaterShoreline::FTopologyCache Work[2];
    static TArray<FProcMeshVertex> V[2];static TArray<uint32> T[2];static TArray<int32> O[2];
    static TArray<TSharedPtr<FJsonValue>> Rows;static int32 Calls=0;static bool Done=false;
    if(Done || Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(Path))return true;
    double Times[2]={};bool Valid[2]={},Rebuilt[2]={};
    for(int32 Offset=0;Offset<2;++Offset)
    {
        const int32 Kind=(Calls+Offset)%2;
        auto Input=Source; // Identical source copy, deliberately outside timing.
        const double Start=FPlatformTime::Seconds();
        Valid[Kind]=Work[Kind].Update(Nx,Ny,MoveTemp(Input),Wet,Available,H,Bed,
            V[Kind],T[Kind],O[Kind],Rebuilt[Kind],Compact,Opposite,Curved,Kind==1);
        Times[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
    }
    bool Exact=Valid[0] && Valid[1] && Rebuilt[0]==Rebuilt[1] && T[0]==T[1] && O[0]==O[1] && V[0].Num()==V[1].Num() &&
        Work[0].GetReuseCount()==Work[1].GetReuseCount() && Work[0].GetRebuildCount()==Work[1].GetRebuildCount();
    for(int32 I=0;Exact && I<T[0].Num();++I)
        Exact=FRaftSimCrestMidpointExpansion::EqualAttributes(V[0][T[0][I]],V[1][T[0][I]]);
    const auto& A=Work[0].GetCurvedBanks();const auto& B=Work[1].GetCurvedBanks();
    Exact&=A.Num()==B.Num();
    for(int32 I=0;Exact && I<A.Num();++I)
    {
        Exact=A[I].IntermediateCount()==B[I].IntermediateCount() && A[I].FirstNode==B[I].FirstNode && A[I].PairSide==B[I].PairSide;
        for(int32 J=0;Exact && J<A[I].IntermediateCount();++J)
            Exact=A[I].Point(J)==B[I].Point(J) && A[I].Fraction(J)==B[I].Fraction(J);
    }
    if(Calls>=2 || !Exact)
    {
        auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("pair"),Calls-2);
        Row->SetNumberField(TEXT("frame"),double(GFrameCounter));Row->SetBoolField(TEXT("exact"),Exact);
        Row->SetBoolField(TEXT("parallel_first"),Calls%2==1);Row->SetBoolField(TEXT("rebuilt"),Rebuilt[0]);
        Row->SetNumberField(TEXT("banks"),A.Num());Row->SetNumberField(TEXT("vertices"),V[0].Num());
        Row->SetNumberField(TEXT("prepared_curves_reused"),Work[1].GetPreparedCurveReuseCount());
        Row->SetNumberField(TEXT("reference_ms"),Times[0]);Row->SetNumberField(TEXT("parallel_ms"),Times[1]);
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    ++Calls;
    if(Exact && Rows.Num()<64)return true;
    Done=true;auto Report=MakeShared<FJsonObject>();Report->SetBoolField(TEXT("exact"),Exact);
    Report->SetStringField(TEXT("scope"),TEXT("64 alternating-order whole-cache updates on identical live inputs after two warmups; exact submitted attribute bits, indices, ownership, curve fractions and rebuild decisions. Source copies excluded from both timers. Not isolated game FPS or visual acceptance."));
    Report->SetArrayField(TEXT("pairs"),Rows);FString Json;
    FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    UE_LOG(LogTemp,Display,TEXT("PARALLEL_BANK_AUDIT exact=%d saved=%d pairs=%d path=%s"),Exact,Saved,Rows.Num(),*Path);
    if(!Exact || !Saved){UE_LOG(LogTemp,Error,TEXT("Parallel bank audit failed"));return false;}
#endif
    return true;
}
}
