#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

class UNiagaraSystem;

// Canonical parent ENU centimetres are independent of the old rebased fixture's
// mutable translation. Niagara receives a positive-scale, proper actor frame.
namespace RaftSimLiquidRegionalState
{
struct FCanonicalFrame
{
    FVector Origin=FVector::ZeroVector;
    FVector AxisX=FVector::ForwardVector;
    FVector AxisY=FVector::RightVector;
    static FVector WorldVector(FVector V) { return FVector(V.X,-V.Y,V.Z); }
    static FVector WorldPosition(FVector P) { return WorldVector(P); }
    FVector WorldSourceOffset(FVector P) const { return WorldVector(P-Origin); }
    FVector WorldAxisX() const { return WorldVector(AxisX); }
    FVector WorldAxisY() const { return -WorldVector(AxisY); }
    FVector LocalPosition(FVector P) const
    {
        const FVector D=P-Origin;
        return FVector(FVector::DotProduct(D,AxisX),-FVector::DotProduct(D,AxisY),D.Z);
    }
};
struct FParent
{
    FCanonicalFrame Frame;
    FIntVector Cells=FIntVector::ZeroValue;
    FVector Spacing=FVector::ZeroVector; // centimetres
    FVector2D Lower=FVector2D::ZeroVector; // canonical station/lateral metres
    int32 Seeds=0,Sources=0;
    double ParticleVolume=0,Inflow=0;
};
struct FState
{
    int32 Id=INDEX_NONE;
    FCanonicalFrame Frame;
    FIntPoint FirstCell=FIntPoint::ZeroValue;
    FIntVector Cells=FIntVector::ZeroValue,ComputationalCells=FIntVector::ZeroValue;
    FVector Extent=FVector::ZeroVector;
    double ParticleVolume=0,Inflow=0,SpawnRate=0;
    TArray<int32> SeedIds,SourceIds;
    TArray<FVector> Positions,Velocities,SourcePositions,SourceVelocities;
    TArray<double> SourceWeights;
};

// Parent headers describe the whole domain; only region allocations use the
// bounded GPU capacity test. Decode clears output on failure, never truncates.
bool DecodeParent(const TSharedPtr<FJsonObject>& Manifest,const TSharedPtr<FJsonObject>& Boundary,FParent& Out,FString& Error);
bool Decode(const TSharedPtr<FJsonObject>& Json,const FParent& Parent,FState& Out,FString& Error);
bool ValidateOwnership(const FParent& Parent,const TArray<FState>& Regions,FString& Error);

// Installs arrays/nominal metrics on an UNUSED transient clone only. Deliberately
// does not activate it or enable per-region physics: shared
// contact/boundary/projection/particle handoff must be installed first. Empty
// external source arrays remain empty and their spawn rate is exactly zero.
// Wires the existing initial-burst branch to these arrays and sets its count
// to exactly the seed count (within the unchanged 163840 seed limit). Preserves
// its native time gate and subsequent external-source branch.
bool InstallArrays(UNiagaraSystem* System,const FState& State,FString& Error);
}
