#pragma once
#include "CoreMinimal.h"
#include "Async/ParallelFor.h"

namespace RaftSimWaterInterpolation
{
// One writer per vertex. All five histories are advanced before publication;
// parallel scheduling changes neither arithmetic nor the exponential chase.
inline bool Advance(const TArray<FVector>& Positions,const TArray<FVector>& Normals,
    const TArray<FLinearColor>& Colors,const TArray<FVector2D>& Flow,
    const TArray<FVector2D>& Wake,float Alpha,TArray<FVector>& RenderedPositions,
    TArray<FVector>& RenderedNormals,TArray<FLinearColor>& RenderedColors,
    TArray<FVector2D>& RenderedFlow,TArray<FVector2D>& RenderedWake,bool Parallel)
{
    const int32 N=Positions.Num();
    if(Normals.Num()!=N || Colors.Num()!=N || Flow.Num()!=N || Wake.Num()!=N ||
        RenderedPositions.Num()!=N || RenderedNormals.Num()!=N || RenderedColors.Num()!=N ||
        RenderedFlow.Num()!=N || RenderedWake.Num()!=N) return false;
    const auto Vertex=[&](int32 I)
    {
        RenderedPositions[I]=FMath::Lerp(RenderedPositions[I],Positions[I],Alpha);
        RenderedNormals[I]=FMath::Lerp(RenderedNormals[I],Normals[I],Alpha).GetSafeNormal();
        RenderedColors[I]=FMath::Lerp(RenderedColors[I],Colors[I],Alpha);
        RenderedFlow[I]=FMath::Lerp(RenderedFlow[I],Flow[I],Alpha);
        RenderedWake[I]=FMath::Lerp(RenderedWake[I],Wake[I],Alpha);
    };
    if(Parallel)
    {
        constexpr int32 BatchSize=1024;
        ParallelFor(FMath::DivideAndRoundUp(N,BatchSize),[&](int32 Batch)
        {
            const int32 End=FMath::Min((Batch+1)*BatchSize,N);
            for(int32 I=Batch*BatchSize;I<End;++I) Vertex(I);
        });
    }
    else for(int32 I=0;I<N;++I) Vertex(I);
    return true;
}
}
