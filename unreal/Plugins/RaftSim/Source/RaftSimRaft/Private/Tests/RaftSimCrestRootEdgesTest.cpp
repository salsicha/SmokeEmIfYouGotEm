#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestRootEdgesTest,"RaftSim.M4.CrestRootEdges",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestRootEdgesTest::RunTest(const FString&)
{
    FRaftSimCrestRootEdges Edges;
    TArray<int32> Fan;
    for(int32 I=1;I<40;++I)Fan.Append({0,I,I+1});
    Fan.Append({0,0,1,1,0,0}); // Degenerate and reversed shared edges.
    for(int32 Pass=0;Pass<3;++Pass)
    {
        Edges.Prepare(Fan,41);
        TestTrue(TEXT("no selected edges survive a preparation"),Edges.IsEmpty());
        FRaftSimIndexedEdgeMap Reference(41);
        for(int32 I=0;I<Fan.Num();I+=3)for(int32 E=0;E<3;++E)
        {
            const int32 A=Fan[I+E],B=Fan[I+(E+1)%3];
            const uint64 Key=(uint64(FMath::Min(A,B))<<32)|uint32(FMath::Max(A,B));
            const int32* Ref=Reference.Find(Key);const int32* Got=Edges.Find(I+E);
            if(!TestTrue(TEXT("bounded and spill adjacency matches current map"),bool(Ref)==bool(Got) && (!Ref || *Ref==*Got)))return false;
            Reference.Add(Key,I+E+Pass);Edges.Add(I+E,I+E+Pass);
        }
    }
    TestEqual(TEXT("one incidence build"),Edges.Builds,uint64(1));
    TestEqual(TEXT("two incidence reuses"),Edges.Reuses,uint64(2));
    FRaftSimSurfaceRefinement Reference,Candidate;
    Reference.bIndexedEdges=Candidate.bIndexedEdges=true;Candidate.bCachedRootEdges=true;
    int64 Compared=0;
    for(int32 Frame=0;Frame<32;++Frame)
    {
        const int32 N=Frame<18 ? 19 : 21;
        TArray<FVector2D> XY;TArray<int32> Triangles;
        for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
        {
            XY.Emplace(-546000.+X*100.+Frame*.17*(X%3),359000.+Y*100.-Frame*.13*(Y%2));
            if(X<N-1 && Y<N-1){const int32 A=Y*N+X;Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});}
        }
        if(Frame>=10)for(int32 I=0;I<Triangles.Num();I+=3)Swap(Triangles[I+1],Triangles[I+2]);
        if(Frame==23){Reference.InvalidateTopologyCache();Candidate.InvalidateTopologyCache();}
        const FVector2D Center=XY[N*N/2];
        const auto Height=[&](const FVector2D& P){const FVector2D D=(P-Center)*.01;
            return float((Frame%5 ? 20.+Frame : 0.)*FMath::Exp(-D.X*D.X*.2-D.Y*D.Y*.4));};
        const FBox2D Window(Center-FVector2D(170),Center+FVector2D(170));
        const int32 Levels=Frame%7 ? 3 : Frame%3;
        for(auto* W:{&Reference,&Candidate})
            if(!W->BuildAdaptive(XY,Triangles,Height,Levels,.5f,{},nullptr,true,true,
                Frame%4 ? nullptr : &Window,25.f,true))return false;
        TArray<FVector2D> A,B;Reference.Expand(XY,A);Candidate.Expand(XY,B);
        if(!TestTrue(TEXT("exact ordered parents, triangles, owners, current coordinates and cache decisions"),
            Reference.MidpointParents==Candidate.MidpointParents && Reference.Triangles==Candidate.Triangles &&
            Reference.TriangleOrigins==Candidate.TriangleOrigins && A==B &&
            Reference.TopologyBuildCount==Candidate.TopologyBuildCount && Reference.TopologyReuseCount==Candidate.TopologyReuseCount))return false;
        Compared+=A.Num();
    }
    AddInfo(FString::Printf(TEXT("Root incidence: 32 changing position/profile/topology/winding/detail/level states, %lld exact expanded vertices"),Compared));
    return !HasAnyErrors();
}
#endif
