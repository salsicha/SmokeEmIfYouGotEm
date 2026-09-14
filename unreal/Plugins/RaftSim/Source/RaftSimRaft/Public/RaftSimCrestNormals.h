#pragma once
#include "CoreMinimal.h"
#include "Async/ParallelFor.h"
#include "ProceduralMeshComponent.h"

// Exact face normals and original-order per-vertex sums. The cached CSR stores
// incidence only, never evolving positions, normals, tangents or wave values.
class FRaftSimCrestNormals
{
    TArray<uint32> CachedIndices;
    TArray<int32> Offsets,Faces;
    TArray<uint8> Touched;
    TArray<FVector> FaceNormals;
    int32 CachedSourceCount=INDEX_NONE,CachedVertexCount=INDEX_NONE;
public:
    uint64 Builds=0,Reuses=0;
    void Reset()
    {
        CachedIndices.Reset();Offsets.Reset();Faces.Reset();Touched.Reset();FaceNormals.Reset();
        CachedSourceCount=CachedVertexCount=INDEX_NONE;
    }
    static void Reference(TArray<FProcMeshVertex>& Vertices,const TArray<uint32>& Indices,int32 SourceCount)
    {
        TArray<FVector> Sums;Sums.Init(FVector::ZeroVector,Vertices.Num());
        TArray<uint8> Used;Used.Init(0,Vertices.Num());
        for(int32 T=0;T<Indices.Num();T+=3)
        {
            const int32 A=Indices[T],B=Indices[T+1],C=Indices[T+2];
            const FVector N=FVector::CrossProduct(Vertices[C].Position-Vertices[A].Position,
                Vertices[B].Position-Vertices[A].Position);
            Sums[A]+=N;Sums[B]+=N;Sums[C]+=N;
            if(A>=SourceCount || B>=SourceCount || C>=SourceCount)Used[A]=Used[B]=Used[C]=1;
        }
        for(int32 I=0;I<Vertices.Num();++I)if(Used[I] && !Sums[I].IsNearlyZero())
        {
            auto& V=Vertices[I];V.Normal=Sums[I].GetSafeNormal();auto& T=V.Tangent.TangentX;
            T=(T-V.Normal*FVector::DotProduct(T,V.Normal)).GetSafeNormal();
        }
    }
    bool Apply(TArray<FProcMeshVertex>& Vertices,const TArray<uint32>& Indices,int32 SourceCount)
    {
        if(Indices.Num()%3 || SourceCount<0 || SourceCount>Vertices.Num())return false;
        const bool Same=CachedVertexCount==Vertices.Num() && CachedSourceCount==SourceCount && CachedIndices==Indices;
        if(!Same)
        {
            for(uint32 I:Indices)if(I>=uint32(Vertices.Num()))return false;
            Offsets.Init(0,Vertices.Num()+1);Touched.Init(0,Vertices.Num());
            for(uint32 I:Indices)++Offsets[I+1];
            for(int32 I=1;I<Offsets.Num();++I)Offsets[I]+=Offsets[I-1];
            Faces.SetNumUninitialized(Indices.Num(),EAllowShrinking::No);
            TArray<int32> Next=Offsets;
            for(int32 T=0;T<Indices.Num();T+=3)
            {
                const bool Fine=Indices[T]>=uint32(SourceCount) || Indices[T+1]>=uint32(SourceCount) || Indices[T+2]>=uint32(SourceCount);
                for(int32 C=0;C<3;++C)
                {
                    const uint32 I=Indices[T+C];Faces[Next[I]++]=T/3;
                    if(Fine)Touched[I]=1;
                }
            }
            CachedIndices=Indices;CachedSourceCount=SourceCount;CachedVertexCount=Vertices.Num();++Builds;
        }
        else ++Reuses;
        FaceNormals.SetNumUninitialized(Indices.Num()/3,EAllowShrinking::No);
        ParallelFor(FaceNormals.Num(),[&](int32 T)
        {
            const int32 A=Indices[3*T],B=Indices[3*T+1],C=Indices[3*T+2];
            FaceNormals[T]=FVector::CrossProduct(Vertices[C].Position-Vertices[A].Position,
                Vertices[B].Position-Vertices[A].Position);
        });
        ParallelFor(Vertices.Num(),[&](int32 I)
        {
            if(!Touched[I])return;
            FVector Sum=FVector::ZeroVector;
            for(int32 J=Offsets[I];J<Offsets[I+1];++J)Sum+=FaceNormals[Faces[J]];
            if(Sum.IsNearlyZero())return;
            auto& V=Vertices[I];V.Normal=Sum.GetSafeNormal();auto& T=V.Tangent.TangentX;
            T=(T-V.Normal*FVector::DotProduct(T,V.Normal)).GetSafeNormal();
        });
        return true;
    }
};
