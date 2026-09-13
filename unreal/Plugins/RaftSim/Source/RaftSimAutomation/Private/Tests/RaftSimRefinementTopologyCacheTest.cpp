#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRefinementTopologyCacheTest,
    "RaftSim.WaterDetail.RefinementTopologyCache",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimRefinementTopologyCacheTest::RunTest(const FString&)
{
    constexpr int32 N=25;
    TArray<FVector2D> XY;TArray<int32> Triangles;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace(-544000+100*X,-360000+100*Y);
        if(X<N-1 && Y<N-1)
        {
            const int32 A=Y*N+X;
            Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});
        }
    }
    FRaftSimSurfaceRefinement Cached,Fresh,Serial;
    int64 Compared=0;
    for(int32 Frame=0;Frame<20;++Frame)
    {
        // Changing XY and heights must never reuse stale geometric values.
        XY[12*N+12].X+=.03125;
        const float Amplitude=Frame<5 ? 0.f : (Frame<10 ? 30.f+Frame*.125f : 100.f-Frame);
        const auto Height=[&](const FVector2D& P)
        {
            const double X=(P.X+544000)*.01-12,Y=(P.Y+360000)*.01-12;
            return float(Amplitude*FMath::Exp(-X*X*.7-Y*Y*.3));
        };
        const double Shift=Frame<12 ? 0. : 350.;
        const FBox2D Window(FVector2D(-543800+Shift,-359800),FVector2D(-542200+Shift,-358200));
        // Exercise root invalidation and a changed number of refinement levels.
        if(Frame==15) Swap(Triangles[0],Triangles[1]);
        const int32 Levels=Frame==17 ? 1 : 3;
        Fresh.InvalidateTopologyCache();
        TestTrue(TEXT("cached build"),Cached.BuildAdaptive(XY,Triangles,Height,Levels,.5f,{},nullptr,true,true,&Window,50));
        TestTrue(TEXT("fresh build"),Fresh.BuildAdaptive(XY,Triangles,Height,Levels,.5f,{},nullptr,true,true,&Window,50));
        TestTrue(TEXT("serial build"),Serial.BuildAdaptive(XY,Triangles,Height,Levels,.5f,{},nullptr,false,false,&Window,50));
        TestTrue(TEXT("exact topology, parents and original triangle owners"),
            Cached.Triangles==Fresh.Triangles && Cached.MidpointParents==Fresh.MidpointParents &&
            Cached.TriangleOrigins==Fresh.TriangleOrigins && Cached.Triangles==Serial.Triangles &&
            Cached.MidpointParents==Serial.MidpointParents && Cached.TriangleOrigins==Serial.TriangleOrigins);
        TArray<FVector2D> A,B;Cached.Expand(XY,A);Fresh.Expand(XY,B);
        TestTrue(TEXT("all expanded current coordinates exact"),A==B);
        TArray<float> SourceValues,AV,BV;
        for(const auto P:XY)SourceValues.Add(Height(P));
        Cached.Expand(SourceValues,AV);Fresh.Expand(SourceValues,BV);
        TestTrue(TEXT("all current interpolated values exact"),AV==BV);
        Compared+=A.Num();
    }
    TestTrue(TEXT("unchanged masks actually reuse assembly"),Cached.TopologyReuseCount>0);
    TestTrue(TEXT("changed masks actually rebuild assembly"),Cached.TopologyBuildCount>0);
    TestTrue(TEXT("less assembly than a forced rebuild"),Cached.TopologyBuildCount<Fresh.TopologyBuildCount);
    AddInfo(FString::Printf(TEXT("Compared %lld current vertices; cached builds=%llu reuses=%llu fresh builds=%llu"),
        Compared,Cached.TopologyBuildCount,Cached.TopologyReuseCount,Fresh.TopologyBuildCount));
    return !HasAnyErrors();
}
#endif
