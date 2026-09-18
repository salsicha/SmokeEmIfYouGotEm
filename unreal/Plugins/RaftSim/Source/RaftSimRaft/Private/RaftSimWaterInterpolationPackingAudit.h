#pragma once
#include "RaftSimWaterInterpolationPacking.h"
#include "RaftSimCrestMidpointExpansion.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace RaftSimWaterInterpolationPackingAudit
{
using namespace RaftSimWaterInterpolationPacking;
#if !UE_BUILD_SHIPPING
struct FOwned
{
    TArray<FVector> Positions,Normals;
    TArray<FLinearColor> Colors;
    TArray<FVector2D> Flow,Wake;
    explicit FOwned(const FRead& R)
    {
        Positions.Append(R.Positions.GetData(),R.Positions.Num());Normals.Append(R.Normals.GetData(),R.Normals.Num());
        Colors.Append(R.Colors.GetData(),R.Colors.Num());Flow.Append(R.Flow.GetData(),R.Flow.Num());Wake.Append(R.Wake.GetData(),R.Wake.Num());
    }
    FRead Read() const{return {Positions,Normals,Colors,Flow,Wake};}
    FWrite Write(){return {Positions,Normals,Colors,Flow,Wake};}
    bool Exact(const FOwned& Other) const
    {
        const auto Same=[](const auto& A,const auto& B)
        {return A.Num()==B.Num() && (!A.Num() || FMemory::Memcmp(A.GetData(),B.GetData(),SIZE_T(A.Num())*sizeof(A[0]))==0);};
        return Same(Positions,Other.Positions)&&Same(Normals,Other.Normals)&&Same(Colors,Other.Colors)&&Same(Flow,Other.Flow)&&Same(Wake,Other.Wake);
    }
};
struct FState
{
    FString Path;
    TArray<TSharedPtr<FJsonValue>> Rows;
    TArray<FProcMeshVertex> Packed[2];
    TSharedPtr<FJsonObject> Pending;
    int32 Calls=0;
    bool Done=false;
    FState(){FParse::Value(FCommandLine::Get(),TEXT("RaftSimWaterInterpolationAudit="),Path);}
};
inline FState& State(){static FState Value;return Value;}
#endif
inline void Run(const FRead& Target,const FRead& Initial,float Alpha,TConstArrayView<FVector2D> UVs,
    TConstArrayView<FProcMeshTangent> Tangents,TConstArrayView<FVector2D> Transport)
{
#if !UE_BUILD_SHIPPING
    auto& S=State();
    if(S.Done || S.Path.IsEmpty() || GFrameCounter<120 || FPaths::FileExists(S.Path))return;
    if(S.Pending){UE_LOG(LogTemp,Error,TEXT("WaterInterpolationAudit previous publication missing"));S.Done=true;return;}
    // Input copies and ALL comparisons are outside both timed regions.
    // Both paths retain equally sized packed-output storage after warmup.
    FOwned A(Initial),B(Initial);double Times[2]={};bool Passed=true;
    for(int32 Order=0;Order<2;++Order)
    {
        const int32 Kind=(S.Calls+Order)%2;const double Start=FPlatformTime::Seconds();
        if(Kind)Passed&=BlendAndPack(Target,B.Write(),Alpha,UVs,Tangents,Transport,S.Packed[1]);
        else
        {
            Passed&=Blend(Target,A.Write(),Alpha);
            Passed&=RaftSimWaterSourcePacking::Pack(A.Positions,A.Normals,A.Colors,UVs,A.Flow,A.Wake,Tangents,
                S.Packed[0],false,Transport.Num() ? Transport : TConstArrayView<FVector2D>(A.Flow));
        }
        Times[Kind]=(FPlatformTime::Seconds()-Start)*1000.;
    }
    Passed&=A.Exact(B) && S.Packed[0].Num()==S.Packed[1].Num();
    for(int32 I=0;Passed && I<S.Packed[0].Num();++I)
        Passed=FRaftSimCrestMidpointExpansion::EqualAttributes(S.Packed[0][I],S.Packed[1][I]);
    S.Pending=MakeShared<FJsonObject>();
    S.Pending->SetNumberField(TEXT("pair"),S.Calls-2);S.Pending->SetNumberField(TEXT("frame"),double(GFrameCounter));
    S.Pending->SetNumberField(TEXT("vertices"),Initial.Positions.Num());S.Pending->SetNumberField(TEXT("alpha"),Alpha);
    S.Pending->SetBoolField(TEXT("candidate_first"),S.Calls%2==1);S.Pending->SetBoolField(TEXT("fields_and_packing_exact"),Passed);
    S.Pending->SetNumberField(TEXT("reference_ms"),Times[0]);S.Pending->SetNumberField(TEXT("candidate_ms"),Times[1]);
#endif
}
inline void Production(const TArray<FProcMeshVertex>& Output)
{
#if !UE_BUILD_SHIPPING
    auto& S=State();if(!S.Pending || S.Done)return;
    bool Passed=S.Pending->GetBoolField(TEXT("fields_and_packing_exact")) && Output.Num()==S.Packed[0].Num();
    for(int32 I=0;Passed && I<Output.Num();++I)
        Passed=FRaftSimCrestMidpointExpansion::EqualAttributes(Output[I],S.Packed[0][I]);
    S.Pending->SetBoolField(TEXT("production_exact"),Passed);
    if(S.Calls>=2 || !Passed)S.Rows.Add(MakeShared<FJsonValueObject>(S.Pending));
    S.Pending.Reset();++S.Calls;
    if(Passed && S.Rows.Num()<64)return;
    S.Done=true;auto Report=MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("schema"),TEXT("raftsim.water_interpolation_packing_pair.v1"));
    Report->SetBoolField(TEXT("exact"),Passed);Report->SetArrayField(TEXT("pairs"),S.Rows);
    Report->SetStringField(TEXT("scope"),TEXT("64 alternating same-input pairs after two warmups, including both complete rendered field histories and all packed attributes against actual production. Copies/checks excluded, both output buffers retained. No diagnostic output published. Not FPS or visual acceptance."));
    FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*S.Path);
    for(auto& Packed:S.Packed)Packed.Empty();
    UE_LOG(LogTemp,Display,TEXT("WaterInterpolationAudit complete exact=%d saved=%d pairs=%d"),Passed,Saved,S.Rows.Num());
#endif
}
}
