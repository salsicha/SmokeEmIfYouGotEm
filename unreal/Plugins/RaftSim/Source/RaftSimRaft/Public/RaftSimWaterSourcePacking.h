#pragma once
#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"
#include "Async/ParallelFor.h"
#include "RaftSimWaterVertexCopy.h"
#include "Math/VectorRegister.h"

namespace RaftSimWaterSourcePacking
{
// Same clamp/round/byte order as FLinearColor::ToFColor(false), four channels
// at once. Explicit NaN-to-zero selection and separate multiply/add retain
// the engine's half-byte boundaries; no sRGB conversion or fused rounding.
inline FColor VectorColor(const FLinearColor& Color)
{
#if PLATFORM_CPU_X86_FAMILY && PLATFORM_LITTLE_ENDIAN
    static_assert(sizeof(FLinearColor)==4*sizeof(float));
    static_assert(STRUCT_OFFSET(FColor,B)==0 && STRUCT_OFFSET(FColor,G)==1 &&
                  STRUCT_OFFSET(FColor,R)==2 && STRUCT_OFFSET(FColor,A)==3);
    const auto Zero=VectorZeroFloat();
    const auto Input=VectorLoad(&Color.R);
    const auto Positive=VectorSelect(VectorCompareGT(Input,Zero),Input,Zero);
    const auto Clamped=VectorMin(Positive,MakeVectorRegisterFloat(1.f,1.f,1.f,1.f));
    const auto Bytes=VectorAdd(VectorMultiply(Clamped,MakeVectorRegisterFloat(255.f,255.f,255.f,255.f)),
                              MakeVectorRegisterFloat(.5f,.5f,.5f,.5f));
    FColor Result;
    VectorStoreByte4(VectorSwizzle(Bytes,2,1,0,3),&Result);
    return Result;
#else
    return Color.ToFColor(false);
#endif
}

// Output must not alias an input. Every worker writes one complete vertex;
// no UObject query, shared accumulation, color-space change or reordering.
inline bool Pack(TConstArrayView<FVector> Positions,TConstArrayView<FVector> Normals,
    TConstArrayView<FLinearColor> Colors,TConstArrayView<FVector2D> UVs,
    TConstArrayView<FVector2D> Flow,TConstArrayView<FVector2D> Wake,
    TConstArrayView<FProcMeshTangent> Tangents,TArray<FProcMeshVertex>& Output,
    bool bParallel=false,TConstArrayView<FVector2D> SurfaceTransport={},bool bVectorColors=false)
{
    const int32 N=Positions.Num();
    if (Normals.Num()!=N || Colors.Num()!=N || UVs.Num()!=N || Flow.Num()!=N ||
        Wake.Num()!=N || Tangents.Num()!=N || (SurfaceTransport.Num()!=0 && SurfaceTransport.Num()!=N)) return false;
    // Every member is assigned below. Avoid constructing a second set of
    // default positions/normals/UVs immediately before overwriting all of it.
    Output.SetNumUninitialized(N,EAllowShrinking::No);
    const auto PackVertex=[&](int32 I)
    {
        auto& V=Output[I];
        V.Position=Positions[I]; V.Normal=Normals[I];
        V.Color=bVectorColors ? VectorColor(Colors[I]) : Colors[I].ToFColor(false);
        V.UV0=UVs[I]; V.UV1=Flow[I]; V.UV2=Wake[I];
        V.UV3=SurfaceTransport.Num() ? SurfaceTransport[I] : FVector2D::ZeroVector;
        V.Tangent=Tangents[I];
    };
    if (bParallel) ParallelFor(TEXT("RaftSimWaterSourcePack"),N,512,PackVertex,EParallelForFlags::Unbalanced);
    else for (int32 I=0; I<N; ++I) PackVertex(I);
    return true;
}
}
