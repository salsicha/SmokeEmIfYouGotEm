#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

// GPU-only ABI: negative columns mark quad-relative XY vertices. Negative rows
// additionally mark v3's third header (global nominal-quad offset). The original
// query anchor stays unchanged across pages, including float32 floor decisions.
// Disk profiles always retain positive counts and an explicit schema/encoding.
// This keeps the encoding with each DI (not a mutable process-global flag), so
// legacy and new bounded liquid regions can coexist in the same scene.
namespace RaftSimLiquidContactProfile
{
inline bool Decode(const TSharedPtr<FJsonObject>& Profile,TArray<FVector3f>& Output)
{
    Output.Reset();
    if (!Profile.IsValid()) return false;
    FString Schema,Encoding;
    if (!Profile->TryGetStringField(TEXT("schema"),Schema)) return false;
    const bool Anchored=Schema==TEXT("raftsim.registered_liquid_contact.v3");
    const bool Relative=Anchored || Schema==TEXT("raftsim.registered_liquid_contact.v2");
    const int32 Header=Anchored?3:2;
    if (!Relative && Schema!=TEXT("raftsim.registered_liquid_contact.v1")) return false;
    if (Relative && (!Profile->TryGetStringField(TEXT("vertex_encoding"),Encoding) ||
        Encoding!=TEXT("nominal-quad-local-xy-and-world-z-centimetres"))) return false;
    const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
    if (!Profile->TryGetArrayField(TEXT("packed_vectors"),Values) || Values->Num()<Header+6 || Values->Num()>Header+6*256*256) return false;
    TArray<FVector3f> Candidate;
    Candidate.Reserve(Values->Num());
    for (const auto& Value:*Values)
    {
        const TArray<TSharedPtr<FJsonValue>>* Row=nullptr;
        if (!Value.IsValid() || !Value->TryGetArray(Row) || Row->Num()!=3) return false;
        FVector3f V;
        for (int32 Axis=0;Axis<3;++Axis)
        {
            double Number;
            if (!(*Row)[Axis].IsValid() || !(*Row)[Axis]->TryGetNumber(Number) || !FMath::IsFinite(Number)) return false;
            V[Axis]=float(Number);
            if (!FMath::IsFinite(V[Axis])) return false;
        }
        Candidate.Add(V);
    }
    const auto& Meta=Candidate[0];auto& Dims=Candidate[1];
    if (Meta.Z<=0 || Dims.X<=0 || Dims.Y<1 || Dims.Z<1 || Dims.Y>256 || Dims.Z>256 ||
        Dims.Y!=FMath::FloorToFloat(Dims.Y) || Dims.Z!=FMath::FloorToFloat(Dims.Z) ||
        Candidate.Num()!=Header+6*int32(Dims.Y)*int32(Dims.Z)) return false;
    if (Anchored)
    {
        const auto& Offset=Candidate[2];
        if (Offset.Z!=0 || FMath::Abs(Offset.X)>4096 || FMath::Abs(Offset.Y)>4096 ||
            Offset.X!=FMath::FloorToFloat(Offset.X) || Offset.Y!=FMath::FloorToFloat(Offset.Y)) return false;
        Dims.Z=-Dims.Z;
    }
    if (Relative) Dims.Y=-Dims.Y;
    Output=MoveTemp(Candidate);
    return true;
}
}
