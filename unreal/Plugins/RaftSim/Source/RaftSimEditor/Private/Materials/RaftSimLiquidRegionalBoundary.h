#pragma once
#include "RaftSimLiquidRegionalState.h"

// Cell ownership for a coupled solve, not per-region native reservoirs. Grid
// addresses here use canonical station/lateral/up. Reflect Y at BOTH ends when
// addressing positive-scale Niagara local grids. Pressure exchange must happen
// within projection iterations; this does not implement a lagged halo copy.
namespace RaftSimLiquidRegionalBoundary
{
struct FFace
{
    int32 Axis=0,Sign=0,Neighbor=INDEX_NONE;
    TArray<FVector3f> BedStageNormalSpeed,Velocity;
    bool IsExternal() const { return Neighbor==INDEX_NONE; }
};
struct FSharedColumn
{
    FIntPoint Destination,Source;
    int32 SourceRegion=INDEX_NONE;
};
struct FExternalColumn
{
    FIntPoint Destination,Parent;
};
struct FRegion
{
    int32 Id=INDEX_NONE;
    FFace Faces[4]; // west, east, south, north in canonical coordinates
    TArray<FSharedColumn> Shared;
    TArray<FExternalColumn> External;
};
inline FIntPoint NiagaraCell(FIntPoint Canonical,int32 ComputationalY)
{
    return FIntPoint(Canonical.X,ComputationalY-1-Canonical.Y);
}

// Requires all physical owners, so missing neighbors cannot silently become
// tank walls or inlets. Bounded FState validation happens upstream; ownership
// is rechecked here. Parent exterior rows are copied exactly once, never fitted
// to new profiles at the internal cuts. No component or asset is mutated.
inline bool Build(const RaftSimLiquidRegionalState::FParent& Parent,
    const TArray<RaftSimLiquidRegionalState::FState>& States,
    const TSharedPtr<FJsonObject>& Boundary,TArray<FRegion>& Output,FString& Error)
{
    using namespace RaftSimLiquidRegionalState;
    Output.Reset();
    if (!ValidateOwnership(Parent,States,Error)) return false;
    auto Fail=[&](const TCHAR* Message) { Error=Message;return false; };
    FString Schema;
    const TArray<TSharedPtr<FJsonValue>>* Rows=nullptr;
    const int32 NX=Parent.Cells.X,NY=Parent.Cells.Y,FaceRows=2*(NX+NY),VectorOffset=8+FaceRows;
    if (!Boundary.IsValid() || !Boundary->TryGetStringField(TEXT("schema"),Schema) ||
        Schema!=TEXT("raftsim.liquid_grid_boundary.v3") ||
        !Boundary->TryGetArrayField(TEXT("packed_vectors"),Rows) || Rows->Num()!=8+2*FaceRows)
        return Fail(TEXT("Full v3 vector boundary required"));
    double DeclaredOffset=0;
    if (!Boundary->TryGetNumberField(TEXT("vector_rows_offset"),DeclaredOffset) || DeclaredOffset!=VectorOffset)
        return Fail(TEXT("Parent vector offset mismatch"));
    TArray<FVector> Values;
    for (const auto& Value:*Rows)
    {
        const TArray<TSharedPtr<FJsonValue>>* Row=nullptr;
        if (!Value.IsValid() || !Value->TryGetArray(Row) || Row->Num()!=3) return Fail(TEXT("Finite triples required"));
        FVector V;
        for (int32 A=0;A<3;++A)
            if (!(*Row)[A].IsValid() || !(*Row)[A]->TryGetNumber(V[A]) || !FMath::IsFinite(V[A]) || !FMath::IsFinite(float(V[A])))
                return Fail(TEXT("Finite float-representable triples required"));
        Values.Add(V);
    }
    if (!Values[0].Equals(Parent.Frame.AxisX,1e-9) || !Values[1].Equals(Parent.Frame.AxisY,1e-9) ||
        !Values[2].Equals(Parent.Frame.Origin,1e-7) || !Values[4].Equals(Parent.Spacing,1e-7) ||
        !Values[5].Equals(FVector(Parent.Cells),0) || !Values[6].Equals(FVector(Parent.Cells+FIntVector(4,4,0)),0) ||
        !Values[3].Equals(FVector(Parent.Cells)*Parent.Spacing,1e-7) ||
        !Values[7].Equals(FVector(Parent.Cells+FIntVector(4,4,0))*Parent.Spacing,1e-7))
        return Fail(TEXT("Parent metric/frame mismatch"));
    TArray<int32> Owners;Owners.Init(INDEX_NONE,NX*NY);
    TMap<int32,int32> StateIndex;
    for (int32 I=0;I<States.Num();++I)
    {
        const auto& S=States[I];StateIndex.Add(S.Id,I);
        for (int32 Y=0;Y<S.Cells.Y;++Y) for (int32 X=0;X<S.Cells.X;++X)
            Owners[(S.FirstCell.Y+Y)*NX+S.FirstCell.X+X]=S.Id;
    }
    const int32 Starts[4]={8,8+NY,8+2*NY,8+2*NY+NX};
    TArray<FRegion> Result;
    for (const auto& S:States)
    {
        FRegion R;R.Id=S.Id;
        for (int32 F=0;F<4;++F)
        {
            FFace& Face=R.Faces[F];Face.Axis=F/2;Face.Sign=F%2?1:-1;
            const int32 Axis=Face.Axis,Tangent=1-Axis;
            const int32 Edge=S.FirstCell[Axis]+(Face.Sign>0?S.Cells[Axis]:0);
            const bool External=Edge==(Face.Sign>0?Parent.Cells[Axis]:0);
            for (int32 T=0;T<S.Cells[Tangent];++T)
            {
                if (External)
                {
                    const int32 Row=Starts[F]+S.FirstCell[Tangent]+T;
                    const FVector V=Values[VectorOffset+Row-8];
                    if (FMath::Abs(Values[Row].Z-V[Axis]*-Face.Sign)>.001)
                        return Fail(TEXT("Exterior normal/vector rows disagree"));
                    Face.BedStageNormalSpeed.Add(FVector3f(Values[Row]));Face.Velocity.Add(FVector3f(V));
                }
                else
                {
                    FIntPoint P=S.FirstCell;P[Axis]=Edge+(Face.Sign<0?-1:0);P[Tangent]+=T;
                    const int32 Owner=Owners[P.Y*NX+P.X];
                    if (Face.Neighbor!=INDEX_NONE && Face.Neighbor!=Owner)
                        return Fail(TEXT("Segmented shared face needs explicit multiple-owner support"));
                    Face.Neighbor=Owner;
                }
            }
        }
        for (int32 Y=0;Y<S.ComputationalCells.Y;++Y) for (int32 X=0;X<S.ComputationalCells.X;++X)
        {
            if (X>=2 && X<S.Cells.X+2 && Y>=2 && Y<S.Cells.Y+2) continue;
            const FIntPoint Dest(X,Y),P=S.FirstCell+Dest-FIntPoint(2,2);
            if (P.X>=0 && P.X<NX && P.Y>=0 && P.Y<NY)
            {
                const int32 Owner=Owners[P.Y*NX+P.X];
                const auto& Source=States[StateIndex[Owner]];
                const FIntPoint SourceCell=P-Source.FirstCell+FIntPoint(2,2);
                R.Shared.Add({Dest,SourceCell,Owner});
            }
            else R.External.Add({Dest,P+FIntPoint(2,2)});
        }
        Result.Add(MoveTemp(R));
    }
    Output=MoveTemp(Result);Error.Reset();return true;
}
}
