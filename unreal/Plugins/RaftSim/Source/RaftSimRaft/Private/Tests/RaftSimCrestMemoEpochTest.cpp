#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestMemoEpochTest,
    "RaftSim.M4.CrestMemoEpoch", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestMemoEpochTest::RunTest(const FString&)
{
    constexpr int32 N=33;
    TArray<FVector2D> XY; TArray<int32> Triangles;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace(-544000.+100.*X,-360000.+100.*Y);
        if(X<N-1 && Y<N-1)
        { const int32 A=Y*N+X; Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1}); }
    }
    FRaftSimSurfaceRefinement Retained,Fresh,LegacyParallel,Shrinking,Unshared;
    int64 Compared=0,KeptCreated=0,ShrinkCreated=0,KeptDestroyed=0,ShrinkDestroyed=0;
    for(int32 Frame=0;Frame<28;++Frame)
    {
        // Identical coordinates but a different function EVERY call. Then
        // drifting shore points, a translated crop, changed winding and a
        // disabled/re-enabled memo path: no old value may survive any of them.
        if(Frame>=8 && Frame<16) XY[16*N+16]+=FVector2D(.137,-.219);
        if(Frame==16) for(auto& P:XY) P+=FVector2D(3700,-1100);
        if(Frame==20) for(int32 T=0;T<Triangles.Num();T+=3) Swap(Triangles[T+1],Triangles[T+2]);
        const float Amplitude=Frame%3==0 ? 0.f : 9.f+Frame*2.7f;
        TAtomic<int32> Queries{0};
        const auto Height=[&](const FVector2D& P)
        {
            ++Queries;
            const double X=(P.X-XY[16*N+16].X)*.01,Y=(P.Y-XY[16*N+16].Y)*.01;
            return float(Amplitude*FMath::Exp(-.7*X*X-.3*Y*Y));
        };
        const bool Retain=Frame!=23;
        if(!Retained.BuildAdaptive(XY,Triangles,Height,3,.5f,{},nullptr,true,true,nullptr,0,Retain,true,true,true))return false;
        TestTrue(TEXT("current function is evaluated even for retained coordinates"),Queries.Load()>0);
        TestTrue(TEXT("one current corner sample serves repeated triangle reads"),
            Retained.SharedCornerSamples>0 && Retained.SharedCornerSamples<Retained.SharedCornerReads);
        if(!Unshared.BuildAdaptive(XY,Triangles,Height,3,.5f,{},nullptr,true,true,nullptr,0,Retain,true,true,false))return false;
        TestTrue(TEXT("shared corners preserve the original batch-local selection exactly"),
            Retained.MidpointParents==Unshared.MidpointParents && Retained.Triangles==Unshared.Triangles &&
            Retained.TriangleOrigins==Unshared.TriangleOrigins);
        if(Retain){KeptCreated+=Retained.ParallelContextsCreated;KeptDestroyed+=Retained.ParallelContextsDestroyed;}
        // Fresh serial memoization is independent of retained epoch machinery.
        if(!Fresh.BuildAdaptive(XY,Triangles,Height,3,.5f))return false;
        if(!LegacyParallel.BuildAdaptive(XY,Triangles,Height,3,.5f,{},nullptr,true,true,nullptr,0,Retain,false))return false;
        if(!Shrinking.BuildAdaptive(XY,Triangles,Height,3,.5f,{},nullptr,true,true,nullptr,0,Retain,true,false))return false;
        if(Retain){ShrinkCreated+=Shrinking.ParallelContextsCreated;ShrinkDestroyed+=Shrinking.ParallelContextsDestroyed;}
        TestTrue(TEXT("inactive worker storage cannot change current topology or ownership"),
            Retained.MidpointParents==Shrinking.MidpointParents && Retained.Triangles==Shrinking.Triangles &&
            Retained.TriangleOrigins==Shrinking.TriangleOrigins);
        TestTrue(TEXT("current selection retains exact parents, winding and cell ownership"),
            Retained.MidpointParents==Fresh.MidpointParents && Retained.Triangles==Fresh.Triangles &&
            Retained.TriangleOrigins==Fresh.TriangleOrigins);
        TestTrue(TEXT("direct coordinate hash retains exact legacy-parallel topology and owners"),
            Retained.MidpointParents==LegacyParallel.MidpointParents && Retained.Triangles==LegacyParallel.Triangles &&
            Retained.TriangleOrigins==LegacyParallel.TriangleOrigins);
        TArray<FVector2D> A,B;Retained.Expand(XY,A);Fresh.Expand(XY,B);
        TestTrue(TEXT("every expanded coordinate is exact"),A==B);
        Compared+=A.Num();
    }
    TestEqual(TEXT("retained mode never destroys inactive contexts between levels"),KeptDestroyed,int64(0));
    TestTrue(TEXT("fixture exercises original context churn"),ShrinkDestroyed>0 && KeptCreated<ShrinkCreated);
    AddInfo(FString::Printf(TEXT("Retained coordinate-table epochs compared %lld vertices over28 changing profiles/crops against fresh serial, legacy-CRC and shrinking-context selection; created %lld vs %lld, destroyed %lld vs %lld, retained bytes %.0f vs %.0f"),
        Compared,KeptCreated,ShrinkCreated,KeptDestroyed,ShrinkDestroyed,Retained.GetRetainedMemoAllocatedBytes(),Shrinking.GetRetainedMemoAllocatedBytes()));
    return !HasAnyErrors();
}
#endif
