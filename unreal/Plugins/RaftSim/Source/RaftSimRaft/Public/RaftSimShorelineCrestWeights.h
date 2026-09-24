#pragma once
#include "RaftSimWaterShoreline.h"

// Publication scratch only: every value is overwritten, including unused
// reserve nodes. Retaining allocation must never retain hydraulic history.
struct FRaftSimShorelineCrestWeights
{
    TArray<float> Coarse, Shore;
    void Update(int32 VertexCount, TConstArrayView<float> SourceCoarse,
        TConstArrayView<float> SourceShore,
        TConstArrayView<RaftSimWaterShoreline::FEdge> Edges)
    {
        const int32 Count=SourceCoarse.Num();
        check(SourceShore.Num()==Count && VertexCount>=Count);
        Coarse.SetNumUninitialized(VertexCount,EAllowShrinking::No);
        Shore.SetNumUninitialized(VertexCount,EAllowShrinking::No);
        if(Count)
        {
            FMemory::Memcpy(Coarse.GetData(),SourceCoarse.GetData(),Count*sizeof(float));
            FMemory::Memcpy(Shore.GetData(),SourceShore.GetData(),Count*sizeof(float));
        }
        if(VertexCount>Count)
        {
            FMemory::Memzero(Coarse.GetData()+Count,(VertexCount-Count)*sizeof(float));
            FMemory::Memzero(Shore.GetData()+Count,(VertexCount-Count)*sizeof(float));
        }
        for(const auto& E:Edges)
        { Coarse[E.Node]=Coarse[E.WetVertex]; Shore[E.Node]=Shore[E.WetVertex]; }
    }
};
