#pragma once
#include "CoreMinimal.h"
#include "Async/ParallelFor.h"
#include "RaftSimWaterFlowFrame.h"
#include "RaftSimWaterRuntimeAdapter.h"

namespace RaftSimCartesianHydraulicRelief
{
// Same four flow-aligned samples and arithmetic as the original actor loop.
// Each worker owns one output; all inputs remain immutable until the join.
// Output must not alias Heights (the same contract as source packing).
// This schedules existing presentation relief, not a new water/terrain model.
inline bool Apply(TConstArrayView<FRaftSimWaterSample> Samples,
    TConstArrayView<float> Heights,TConstArrayView<uint8> Wet,int32 Nx,int32 Ny,
    int32 NearStride,int32 FarStride,float Scale,TArray<float>& Output,bool bParallel)
{
    if(Nx<2 || Ny<2 || int64(Nx)*Ny!=Samples.Num() || Heights.Num()!=Samples.Num() ||
        Wet.Num()!=Samples.Num() || NearStride<=0 || FarStride<NearStride || !FMath::IsFinite(Scale))return false;
    Output.Init(0.f,Samples.Num());
    const auto Vertex=[&](int32 Index)
    {
        if(!Wet[Index])return;
        const auto& Sample=Samples[Index];
        const FVector2D Direction=RaftSimWaterFlowFrame::Direction(FVector2D(
            Sample.VelocityMetersPerSecond.X,Sample.VelocityMetersPerSecond.Y));
        const FVector2D Position(Index%Nx,Index/Nx);
        float Values[4];bool Valid=true;int32 I=0;
        for(const int32 Offset:{-FarStride,-NearStride,NearStride,FarStride})
            Valid &= RaftSimWaterFlowFrame::SampleWetScalar(Heights,Wet,Nx,Ny,
                Position+Direction*Offset,Values[I++]);
        if(!Valid)return;
        Output[Index]=URaftSimWaterRuntimeAdapter::ComputeCoupledHydraulicReliefMeters(
            Heights[Index],Values[0],Values[1],Values[2],Values[3],
            Sample.VelocityMetersPerSecond.Size2D(),Sample.DepthMeters)*Scale;
    };
    if(bParallel)ParallelFor(TEXT("RaftSimHydraulicRelief"),Samples.Num(),256,Vertex,EParallelForFlags::Unbalanced);
    else for(int32 I=0;I<Samples.Num();++I)Vertex(I);
    return true;
}
}
