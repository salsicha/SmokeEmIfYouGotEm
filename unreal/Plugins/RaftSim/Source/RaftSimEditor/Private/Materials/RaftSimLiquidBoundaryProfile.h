#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

namespace RaftSimLiquidBoundaryProfile
{
struct FDecoded
{
    TArray<FVector3f> Packed;
    FVector3f CellSize=FVector3f::ZeroVector;
    FVector3f ComputationalExtent=FVector3f::ZeroVector;
    FIntVector PhysicalCells=FIntVector::ZeroValue;
    FIntVector ComputationalCells=FIntVector::ZeroValue;
    bool Rectangular=false;
};

inline bool Decode(const TSharedPtr<FJsonObject>& Json,bool Vectors,FDecoded& Output)
{
    Output=FDecoded();
    FString Schema;
    if (!Json.IsValid() || !Json->TryGetStringField(TEXT("schema"),Schema)) return false;
    const bool Rect=Schema==TEXT("raftsim.liquid_grid_boundary.v3");
    if (!Rect && Schema!=(Vectors?TEXT("raftsim.liquid_grid_boundary.v2"):TEXT("raftsim.liquid_grid_boundary.v1"))) return false;
    const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
    if (!Json->TryGetArrayField(TEXT("packed_vectors"),Values) || Values->Num()<8 || Values->Num()>65544) return false;
    FDecoded Candidate;Candidate.Rectangular=Rect;
    for (const auto& Value:*Values)
    {
        const TArray<TSharedPtr<FJsonValue>>* Row=nullptr;
        if (!Value.IsValid() || !Value->TryGetArray(Row) || Row->Num()!=3) return false;
        FVector3f V;
        for (int32 Axis=0;Axis<3;++Axis)
        {
            double Number;
            if (!(*Row)[Axis].IsValid() || !(*Row)[Axis]->TryGetNumber(Number) || !FMath::IsFinite(Number)) return false;
            V[Axis]=float(Number);if (!FMath::IsFinite(V[Axis])) return false;
        }
        Candidate.Packed.Add(V);
    }
    auto& P=Candidate.Packed;
    if (!FMath::IsNearlyEqual(P[0].SizeSquared(),1.f,.0001f) || !FMath::IsNearlyEqual(P[1].SizeSquared(),1.f,.0001f) ||
        !FMath::IsNearlyZero(FVector3f::DotProduct(P[0],P[1]),.0001f) || P[0].Z!=0 || P[1].Z!=0) return false;
    if (Rect)
    {
        Candidate.CellSize=P[4];Candidate.ComputationalExtent=P[7];
        for (int32 Axis=0;Axis<3;++Axis)
        {
            if (P[5][Axis]<2 || P[5][Axis]>4096 || P[5][Axis]!=FMath::FloorToFloat(P[5][Axis]) || P[4][Axis]<=0) return false;
            Candidate.PhysicalCells[Axis]=int32(P[5][Axis]);
            Candidate.ComputationalCells[Axis]=Candidate.PhysicalCells[Axis]+(Axis<2?4:0);
            if (P[6][Axis]!=float(Candidate.ComputationalCells[Axis]) ||
                !FMath::IsNearlyEqual(P[3][Axis],P[4][Axis]*P[5][Axis],.01f) ||
                !FMath::IsNearlyEqual(P[7][Axis],P[4][Axis]*P[6][Axis],.01f)) return false;
        }
        // Existing reconstruction cap and native half-X dispatch requirements.
        // Full-rapid data must be paged/coupled, not accepted by raising these.
        const auto N=Candidate.ComputationalCells;
        if (int64(N.X)*N.Y*N.Z*8>2000000 || N.X%2!=0) return false;
    }
    else
    {
        if (!P[2].Equals(FVector3f(32.8125f,1050.f,350.f),.001f) || !P[3].Equals(FVector3f(800.f/24.f,64.f,24.f),.001f)) return false;
        Candidate.CellSize=FVector3f(P[2].X,P[2].X,P[3].X);
        Candidate.PhysicalCells=FIntVector(64,64,24);Candidate.ComputationalCells=FIntVector(68,68,24);
        Candidate.ComputationalExtent=FVector3f(2231.25f,2231.25f,800.f);
    }
    const int32 NX=Candidate.PhysicalCells.X,NY=Candidate.PhysicalCells.Y;
    const int32 Header=Rect?8:4,Total=2*(NX+NY),VectorOffset=Header+Total;
    if (P.Num()!=Header+Total*(Vectors?2:1)) return false;
    if (Rect)
    {
        const TArray<TSharedPtr<FJsonValue>> *Offsets=nullptr,*Counts=nullptr;
        if (!Json->TryGetArrayField(TEXT("face_rows_offsets"),Offsets) || Offsets->Num()!=4 ||
            !Json->TryGetArrayField(TEXT("face_row_counts"),Counts) || Counts->Num()!=4) return false;
        int32 Cursor=Header;
        for (int32 Face=0;Face<4;++Face)
        {
            double Offset,Count;
            if (!(*Offsets)[Face]->TryGetNumber(Offset) || !(*Counts)[Face]->TryGetNumber(Count) ||
                Offset!=Cursor || Count!=(Face<2?NY:NX)) return false;
            Cursor+=int32(Count);
        }
    }
    if (Vectors)
    {
        double Offset;
        if (!Json->TryGetNumberField(TEXT("vector_rows_offset"),Offset) || Offset!=VectorOffset) return false;
        int32 Cursor=0;
        for (int32 Face=0;Face<4;++Face)
            for (int32 Column=0;Column<(Face<2?NY:NX);++Column,++Cursor)
                if (!FMath::IsNearlyEqual(P[VectorOffset+Cursor][Face<2?0:1]*(Face%2?-1.f:1.f),P[Header+Cursor].Z,.001f) ||
                    !FMath::IsNearlyZero(P[VectorOffset+Cursor].Z,.001f)) return false;
    }
    if (Rect) P[3].Z=-P[3].Z; // self-describing runtime ABI, disk JSON unchanged
    Output=MoveTemp(Candidate);
    return true;
}
}
