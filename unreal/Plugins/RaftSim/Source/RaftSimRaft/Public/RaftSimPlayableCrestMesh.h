#pragma once
#include "CoreMinimal.h"
#include "RaftSimSurfaceRefinement.h"
#include "RaftSimWaterRuntimeAdapter.h"

// Replace only the linearly interpolated crest with the SAME continuous
// profile used by rigid support. Keep every source vertex and all other
// displacement/coverage fields. The conforming topology has no T-junctions.
namespace RaftSimPlayableCrestMesh
{
inline void Reconstruct(const FRaftSimSurfaceRefinement& Refinement,
    const TArray<FVector2D>& Coordinates, const TArray<float>& CoarseCrestCm,
    const TArray<float>& Shore, TConstArrayView<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Sites,
    float Lift, float Spacing, float ReliefScale, float WorldYSign,
    TArray<FVector>& Positions, TArray<FVector>& Normals,
    TArray<float>* CorrectionCache=nullptr, bool bRefreshCache=true)
{
    const bool bReuse=CorrectionCache && !bRefreshCache && CorrectionCache->Num()==Positions.Num();
    if(bReuse)
    {
        for(int32 I=Refinement.SourceVertexCount;I<Positions.Num();++I) Positions[I].Z+=(*CorrectionCache)[I];
    }
    else
    {
    if(CorrectionCache) CorrectionCache->Init(0.0f,Positions.Num());
    TArray<float> InterpolatedCrest, InterpolatedShore;
    Refinement.Expand(CoarseCrestCm, InterpolatedCrest);
    Refinement.Expand(Shore, InterpolatedShore);
    check(Coordinates.Num() == Positions.Num());
    for (int32 I = Refinement.SourceVertexCount; I < Positions.Num(); ++I)
    {
        if (InterpolatedShore[I] <= 0.0f) continue;
        const float Crest = URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(
            Coordinates[I], Sites, Lift, Spacing) * ReliefScale * InterpolatedShore[I] * 100.0f;
        const float Correction=Crest-InterpolatedCrest[I];
        Positions[I].Z += Correction;
        if(CorrectionCache) (*CorrectionCache)[I]=Correction;
    }
    }
    // Area-weighted normals of the actual new geometry. Only the refined
    // neighbourhood changes; distant original normals retain their values.
    TArray<FVector> Sums;
    Sums.Init(FVector::ZeroVector, Positions.Num());
    TArray<uint8> Touched;
    Touched.Init(0, Positions.Num());
    for (int32 T = 0; T < Refinement.Triangles.Num(); T += 3)
    {
        const int32 A=Refinement.Triangles[T], B=Refinement.Triangles[T+1], C=Refinement.Triangles[T+2];
        // Source topology uses Unreal's clockwise front face.
        const FVector N=FVector::CrossProduct(Positions[C]-Positions[A], Positions[B]-Positions[A]) * WorldYSign;
        Sums[A]+=N; Sums[B]+=N; Sums[C]+=N;
        if (A>=Refinement.SourceVertexCount || B>=Refinement.SourceVertexCount || C>=Refinement.SourceVertexCount)
            Touched[A]=Touched[B]=Touched[C]=1;
    }
    for (int32 I=0; I<Normals.Num(); ++I)
        if (Touched[I] && !Sums[I].IsNearlyZero()) Normals[I]=Sums[I].GetSafeNormal();
}
}
