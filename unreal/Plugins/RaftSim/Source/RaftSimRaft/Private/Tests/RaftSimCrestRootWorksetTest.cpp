#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestRootWorksetTest,
    "RaftSim.M4.CrestRootWorkset",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestRootWorksetTest::RunTest(const FString&)
{
    constexpr int32 N=25;
    FRaftSimSurfaceRefinement Reference,Candidate;
    Reference.bIndexedEdges=Candidate.bIndexedEdges=true;
    Candidate.bSparseRoots=true;
    int64 Compared=0;int32 Reduced=0;
    for(int32 Frame=0;Frame<18;++Frame)
    {
        TArray<FVector2D> XY;TArray<int32> Roots;
        for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
        {
            const double Sign=Frame<9 ? 1. : -1.;
            XY.Emplace(-544000.+X*100.,Sign*(-360000.+Y*100.));
            if(X<N-1 && Y<N-1 && !(X==12 && Y>=10 && Y<=13 && Frame%3==0))
            {
                const int32 A=Y*N+X;
                if(Frame%4==0)Roots.Append({A+N,A+1,A,A+N+1,A+N,A+1});
                else Roots.Append({A,A+N,A+1,A+1,A+N,A+N+1});
            }
        }
        if(Frame%3==1)XY[12*N+12].X+=.137;
        const FVector2D Center=XY[10*N+7+Frame%7];
        const FBox2D Support(Center-FVector2D(251,319),Center+FVector2D(251,319));
        TArray<FBox2D> Regions={Support};
        if(Frame==7)Regions={FBox2D(FVector2D(1.e7,1.e7),FVector2D(1.e7+1,1.e7+1))};
        if(Frame==8)Regions.Reset(); // Unrestricted callback must never be pruned.
        const auto Height=[&](const FVector2D& P)
        {
            if(Frame!=8 && !Regions[0].IsInsideOrOn(P))return 0.f;
            const auto D=(P-Center)*.01;
            return float((21.+Frame)*FMath::Exp(-D.SizeSquared()*.25)*FMath::Cos(D.X*1.3));
        };
        const FBox2D Detail(XY[5*N+18]-FVector2D(175),XY[5*N+18]+FVector2D(175));
        const FBox2D* Window=Frame%2 ? &Detail : nullptr;
        TestTrue(TEXT("full refinement succeeds"),Reference.BuildAdaptive(XY,Roots,Height,3,.5f,Regions,
            nullptr,true,true,Window,50,true));
        TestTrue(TEXT("sparse refinement succeeds"),Candidate.BuildAdaptive(XY,Roots,Height,3,.5f,Regions,
            nullptr,true,true,Window,50,true));
        TestTrue(TEXT("ordered midpoint parents are exact, including conforming neighbours"),Reference.MidpointParents==Candidate.MidpointParents);
        TestTrue(TEXT("all output triangles and their original owners are exact"),Reference.Triangles==Candidate.Triangles && Reference.TriangleOrigins==Candidate.TriangleOrigins);
        TArray<FVector2D> A,B;Reference.Expand(XY,A);Candidate.Expand(XY,B);
        TestTrue(TEXT("expanded coordinates are exact"),A==B);Compared+=A.Num();
        Reduced+=Candidate.RootTrianglesRetained<Candidate.RootTrianglesConsidered;
        if(Frame==8)TestEqual(TEXT("missing support metadata keeps full workset"),Candidate.RootTrianglesRetained,Roots.Num()/3);
    }
    TestTrue(TEXT("fixture actually exercises reduced worksets"),Reduced>12);
    FRaftSimCrestRootWorkset Invalid;
    TestFalse(TEXT("invalid root index rejects"),Invalid.Prepare({FVector2D(0)}, {0,1,0}, {},nullptr,0));
    AddInfo(FString::Printf(TEXT("Compared %lld expanded vertices across18 changing support/topology frames"),Compared));
    return !HasAnyErrors();
}
#endif
