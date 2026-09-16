#include "Misc/AutomationTest.h"
#include "RaftSimBoundCoordinateMemo.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimBoundMemoTest,"RaftSim.M4.BoundCoordinateMemo",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimBoundMemoTest::RunTest(const FString&)
{
    FRaftSimBoundCoordinateMemo Memo; Memo.Prepare(15);
    int32 Calls=0;float Offset=0;
    const auto Height=[&](const FVector2D& P){++Calls;return float(P.X*.17-P.Y*.31)+Offset;};
    const FVector2D P(-544000.137,360000.219);
    const float First=Memo.Value(P,0,1,Height);
    TestEqual(TEXT("repeat binding reuses this epoch only"),Memo.Value(P,0,1,Height),First);
    TestEqual(TEXT("another binding shares the exact coordinate"),Memo.Value(P,1,1,Height),First);
    TestEqual(TEXT("same-epoch coordinate evaluated once"),Calls,1);
    Offset=27;
    TestEqual(TEXT("new epoch evaluates the current profile"),Memo.Value(P,0,2,Height),First+27);
    TestEqual(TEXT("profile epoch advanced evaluation"),Calls,2);
    const FVector2D Moved=P+FVector2D(.000001,-.000001);
    Memo.Value(Moved,0,2,Height);
    TestEqual(TEXT("moving coordinates invalidate a binding even below float precision"),Calls,3);
    Memo.Value(FVector2D(0.,-0.),3,2,Height);
    const int32 ZeroCalls=Calls;
    Memo.Value(FVector2D(-0.,0.),3,2,Height);
    TestEqual(TEXT("signed zeros retain numerical identity"),Calls,ZeroCalls);
    Memo.Reset();Memo.Prepare(15);Offset=0;
    Memo.Value(FVector2D(0,0),1,3,Height);
    for(int32 I=1;I<4096;++I)Memo.Value(FVector2D(I,0),0,3,Height);
    TestEqual(TEXT("existing bounded history capacity"),Memo.Num(),4096);
    const int32 BeforeGrowthRead=Calls;
    TestEqual(TEXT("original binding survives all intermediate growth and rehashes"),Memo.Value(FVector2D(0,0),1,3,Height),0.f);
    TestEqual(TEXT("growth retains the already evaluated sample"),Calls,BeforeGrowthRead);
    Memo.Value(FVector2D(4096,0),0,3,Height);
    TestEqual(TEXT("new coordinate at capacity clears old history"),Memo.Num(),1);
    TestEqual(TEXT("old handle cannot alias a new point after reset"),Memo.Value(FVector2D(0,0),1,3,Height),0.f);
    Memo.Prepare(30);
    Offset=5;
    TestEqual(TEXT("batch resize keeps coordinates but reevaluates current epoch"),
        Memo.Value(FVector2D(0,0),29,4,Height),5.f);
    Memo.Reset();Memo.Prepare(45);Calls=0;
    for(int32 Level=0;Level<3;++Level)Memo.Value(P,Level*15,5,Height);
    TestEqual(TEXT("different level bindings share one current coordinate sample"),Calls,1);
    for(int32 Level=0;Level<3;++Level)Memo.Value(P,Level*15,6,Height);
    TestEqual(TEXT("shared levels never reuse a previous profile epoch"),Calls,2);
    for(int32 I=0;I<4096;++I)Memo.Value(FVector2D(I,0),44,6,Height);
    const int32 BeforeOldBindings=Calls;
    for(int32 Level=0;Level<3;++Level)Memo.Value(P,Level*15,6,Height);
    TestEqual(TEXT("capacity reset invalidates every level but still deduplicates"),Calls,BeforeOldBindings+1);
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimBoundMemoRefinementTest,"RaftSim.M4.BoundMemoRefinement",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimBoundMemoRefinementTest::RunTest(const FString&)
{
    TArray<FVector2D> XY;TArray<int32> Triangles;
    constexpr int32 N=25;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace(-544000.+100.*X,-360000.+100.*Y);
        if(X<N-1 && Y<N-1){const int32 A=Y*N+X;Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});}
    }
    FRaftSimSurfaceRefinement Candidate,Control;
    Candidate.bBoundCoordinateMemo=true;
    for(int32 Frame=0;Frame<32;++Frame)
    {
        if(Frame>5)XY[12*N+12]+=FVector2D(.137,-.219);
        if(Frame==12)for(auto& P:XY)P+=FVector2D(900.,-300.);
        if(Frame==16)for(int32 T=0;T<Triangles.Num();T+=3)Swap(Triangles[T+1],Triangles[T+2]);
        if(Frame==22)Triangles.RemoveAt(0,6);
        Candidate.ParallelBatchSize=Control.ParallelBatchSize=Frame%2 ? 64 : 128;
        const auto Height=[&](const FVector2D& P)
        {const auto D=(P-XY[12*N+12])*.01;return float((Frame%3 ? 20.+Frame : 0.)*FMath::Exp(-D.SizeSquared()*.3));};
        const FBox2D Detail(XY[10*N+10],XY[14*N+14]);
        const int32 Levels=Frame<24 ? 1+Frame%3 : 3;
        for(auto* W:{&Candidate,&Control})if(!W->BuildAdaptive(XY,Triangles,Height,Levels,.5f,{},nullptr,
            true,true,Frame>=24 ? &Detail : nullptr,Frame>=24 ? 25.f : 0.f,Frame!=18))return false;
        TestTrue(TEXT("moving/profile/reordered/hole/detail/batch changes preserve all ordered topology"),
            Candidate.MidpointParents==Control.MidpointParents && Candidate.Triangles==Control.Triangles &&
            Candidate.TriangleOrigins==Control.TriangleOrigins);
        TArray<FVector2D> A,B;Candidate.Expand(XY,A);Control.Expand(XY,B);
        TestTrue(TEXT("expanded positions are exact, not merely within a tolerance"),A==B);
    }
    return !HasAnyErrors();
}
#endif
