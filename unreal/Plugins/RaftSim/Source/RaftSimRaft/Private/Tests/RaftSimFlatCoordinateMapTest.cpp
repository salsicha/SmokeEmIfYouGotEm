#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFlatCoordinateMapTest,"RaftSim.M4.FlatCoordinateMemo",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimFlatCoordinateMapTest::RunTest(const FString&)
{
    TRaftSimFlatCoordinateMap<int32> Flat;
    TMap<FVector2D,int32> Original;
    for(int32 Round=0;Round<3;++Round)
    {
        for(int32 I=0;I<9000;++I)
        {
            const FVector2D P(-544000.+I*.137,360000.-I*.219);
            Flat.Add(P,I+Round);Original.Add(P,I+Round);
        }
        Flat.Add(FVector2D(-0.,0.),91);Flat.Add(FVector2D(0.,-0.),92);
        TestEqual(TEXT("signed zero keys have one numerical identity"),*Flat.Find(FVector2D(0.,0.)),92);
        for(const auto& Pair:Original)
        {
            const auto* V=Flat.Find(Pair.Key);
            if(!V || *V!=Pair.Value){AddError(TEXT("growth/collision/update lost an exact key"));return false;}
        }
        TestNull(TEXT("absent key terminates lookup"),Flat.Find(FVector2D(123.,456.)));
        Flat.Reset();Original.Reset();
        TestEqual(TEXT("reset removes all entries"),Flat.Num(),0);
        TestNull(TEXT("reset cannot expose old entries"),Flat.Find(FVector2D(0.,0.)));
    }
    for(int32 I=0;I<4096;++I)Flat.FindOrAdd(FVector2D(I,0.),4096)=I;
    TestEqual(TEXT("hit at cap keeps every entry"),Flat.FindOrAdd(FVector2D(23.,0.),4096),23);
    TestEqual(TEXT("hit does not reset"),Flat.Num(),4096);
    TestEqual(TEXT("miss at cap initializes a new epoch value"),Flat.FindOrAdd(FVector2D(4096.,0.),4096),0);
    TestEqual(TEXT("miss at cap discards bounded coordinate history"),Flat.Num(),1);
    TestNull(TEXT("reset never returns pre-cap values"),Flat.Find(FVector2D(23.,0.)));
    TArray<FVector2D> XY;TArray<int32> Triangles;
    constexpr int32 N=25;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace(-544000.+100.*X,-360000.+100.*Y);
        if(X<N-1 && Y<N-1){const int32 A=Y*N+X;Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});}
    }
    FRaftSimSurfaceRefinement Candidate,Control;
    Candidate.bFlatCoordinateMemo=true;
    for(int32 Frame=0;Frame<24;++Frame)
    {
        if(Frame>5)XY[12*N+12]+=FVector2D(.137,-.219);
        if(Frame==12)for(auto& P:XY)P+=FVector2D(900.,-300.);
        if(Frame==16)for(int32 T=0;T<Triangles.Num();T+=3)Swap(Triangles[T+1],Triangles[T+2]);
        Candidate.ParallelBatchSize=Control.ParallelBatchSize=Frame%2 ? 64 : 128;
        const auto Height=[&](const FVector2D& P)
        {const auto D=(P-XY[12*N+12])*.01;return float((Frame%3 ? 20.+Frame : 0.)*FMath::Exp(-D.SizeSquared()*.3));};
        for(auto* W:{&Candidate,&Control})if(!W->BuildAdaptive(XY,Triangles,Height,3,.5f,{},nullptr,
            true,true,nullptr,0,Frame!=18))return false;
        TestTrue(TEXT("current profile selects exact ordered topology and ownership"),
            Candidate.MidpointParents==Control.MidpointParents && Candidate.Triangles==Control.Triangles &&
            Candidate.TriangleOrigins==Control.TriangleOrigins);
        TArray<FVector2D> A,B;Candidate.Expand(XY,A);Control.Expand(XY,B);
        TestTrue(TEXT("expanded geometry is unchanged"),A==B);
    }
    return !HasAnyErrors();
}
#endif
