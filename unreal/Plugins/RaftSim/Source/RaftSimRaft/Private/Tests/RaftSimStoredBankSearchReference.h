#pragma once
#include "RaftSimStoredBankContour.h"

namespace RaftSimStoredBankSearchReference
{
using namespace RaftSimThreeWetBankContour;
struct FStorage : RaftSimStoredBankContour::FStorage
{
    explicit FStorage(const RaftSimStoredBankContour::FStorage& Source)
        : RaftSimStoredBankContour::FStorage(Source) {SignedNeighborFallbacks=0;}
    FPoint operator()(const FPoint& P,double T)const {return Store<false>(P,T);}
};
inline bool ExactPoints(const TArray<FPoint>& A,const TArray<FPoint>& B)
{
    if(A.Num()!=B.Num())return false;
    for(int32 I=0;I<A.Num();++I)
        if(A[I].XY!=B[I].XY || !SamePoint(A[I],B[I]))return false;
    return true;
}
inline bool ExactResult(const FResult& A,const FResult& B)
{
    return ExactPoints(A.Boundary,B.Boundary) && ExactPoints(A.InnerBoundary,B.InnerBoundary) &&
        ExactPoints(A.Polygon,B.Polygon) && A.Triangles==B.Triangles &&
        A.Stats.CoefficientTests==B.Stats.CoefficientTests && A.Stats.InitialSegments==B.Stats.InitialSegments &&
        A.Stats.RootSolves==B.Stats.RootSolves && A.Stats.RootEvaluations==B.Stats.RootEvaluations &&
        A.Stats.FailedStage==B.Stats.FailedStage && A.Stats.ReorderedProposalSpans==B.Stats.ReorderedProposalSpans &&
        A.Stats.FailedA==B.Stats.FailedA && A.Stats.FailedB==B.Stats.FailedB;
}
inline bool Equivalent(const FCurve& C,const RaftSimStoredBankContour::FStorage& Source,
    const FResult& Bounded,const FResult& Full)
{
    FStorage Original(Source);FResult OriginalBounded,OriginalFull;
    const bool BoundedGood=BuildStored(C,Original.Width,OriginalBounded,Original,Original.RootWidth);
    const bool FullGood=BuildStored(C,Original.Width,OriginalFull,Original,Original.RootWidth,true,false);
    return BoundedGood && FullGood && ExactResult(Bounded,OriginalBounded) && ExactResult(Full,OriginalFull) &&
        Source.SignedNeighborFallbacks==Original.SignedNeighborFallbacks;
}
}
