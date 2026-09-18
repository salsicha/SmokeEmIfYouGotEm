#pragma once
#include "RaftSimWaterSourcePacking.h"

namespace RaftSimWaterInterpolationPacking
{
struct FRead
{
    TConstArrayView<FVector> Positions,Normals;
    TConstArrayView<FLinearColor> Colors;
    TConstArrayView<FVector2D> Flow,Wake;
    bool HasSize(int32 N) const
    {return Positions.Num()==N && Normals.Num()==N && Colors.Num()==N && Flow.Num()==N && Wake.Num()==N;}
};
struct FWrite
{
    TArrayView<FVector> Positions,Normals;
    TArrayView<FLinearColor> Colors;
    TArrayView<FVector2D> Flow,Wake;
    FRead Read() const{return {Positions,Normals,Colors,Flow,Wake};}
};
inline void BlendVertex(int32 I,const FRead& Target,const FWrite& Rendered,float Alpha)
{
    // Retain the original arithmetic and per-vertex attribute order exactly.
    Rendered.Positions[I]=FMath::Lerp(Rendered.Positions[I],Target.Positions[I],Alpha);
    Rendered.Normals[I]=FMath::Lerp(Rendered.Normals[I],Target.Normals[I],Alpha).GetSafeNormal();
    Rendered.Colors[I]=FMath::Lerp(Rendered.Colors[I],Target.Colors[I],Alpha);
    Rendered.Flow[I]=FMath::Lerp(Rendered.Flow[I],Target.Flow[I],Alpha);
    Rendered.Wake[I]=FMath::Lerp(Rendered.Wake[I],Target.Wake[I],Alpha);
}
inline bool Blend(const FRead& Target,const FWrite& Rendered,float Alpha)
{
    const int32 N=Target.Positions.Num();
    if(!Target.HasSize(N) || !Rendered.Read().HasSize(N))return false;
    for(int32 I=0;I<N;++I)BlendVertex(I,Target,Rendered,Alpha);
    return true;
}
inline bool BlendAndPack(const FRead& Target,const FWrite& Rendered,float Alpha,
    TConstArrayView<FVector2D> UVs,TConstArrayView<FProcMeshTangent> Tangents,
    TConstArrayView<FVector2D> Transport,TArray<FProcMeshVertex>& Output)
{
    const int32 N=Target.Positions.Num();
    if(!Target.HasSize(N) || !Rendered.Read().HasSize(N) || UVs.Num()!=N || Tangents.Num()!=N ||
       (Transport.Num()!=0 && Transport.Num()!=N))return false;
    // A single pass over the evolving fields; no cached values or changed
    // update cadence. Complete rendered state remains available to all callers.
    Output.SetNumUninitialized(N,EAllowShrinking::No);
    for(int32 I=0;I<N;++I)
    {
        BlendVertex(I,Target,Rendered,Alpha);
        auto& V=Output[I];
        V.Position=Rendered.Positions[I];V.Normal=Rendered.Normals[I];
        V.Color=Rendered.Colors[I].ToFColor(false);
        V.UV0=UVs[I];V.UV1=Rendered.Flow[I];V.UV2=Rendered.Wake[I];
        // The actor's original fallback is the current rendered bulk flow.
        V.UV3=Transport.Num() ? Transport[I] : Rendered.Flow[I];
        V.Tangent=Tangents[I];
    }
    return true;
}
}
