#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestLevelMemoTest,
    "RaftSim.M4.CrestLevelMemoSelection",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestLevelMemoTest::RunTest(const FString&)
{
    constexpr int32 N=23;
    TArray<FVector2D> XY;TArray<int32> Triangles;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace(-544000.+100.*X,-360000.+100.*Y);
        if(X<N-1 && Y<N-1){const int32 A=Y*N+X;Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});}
    }
    FRaftSimSurfaceRefinement Original,Candidate,Serial;
    Candidate.bLevelLocalMemos=true;
    int64 Compared=0;
    for(int32 Frame=0;Frame<24;++Frame)
    {
        Candidate.bLevelLocalMemos=Frame%7!=6; // Switching storage never revives an old profile epoch.
        if(Frame>=4)XY[N*N/2]+=FVector2D(.173,-.241);
        if(Frame==9)for(auto& P:XY)P+=FVector2D(1900,-2300);
        if(Frame==12)for(int32 T=0;T<Triangles.Num();T+=3)Swap(Triangles[T+1],Triangles[T+2]);
        const auto Height=[&](const FVector2D& P)
        {
            const auto D=(P-XY[N*N/2])*.01;
            return float((Frame%3 ? 15.+Frame*3. : 0.)*FMath::Exp(-.3*D.X*D.X-.6*D.Y*D.Y));
        };
        const FBox2D Window(XY[N*N/2]-FVector2D(220),XY[N*N/2]+FVector2D(220));
        const FBox2D* Detail=Frame%4 ? nullptr : &Window;
        TArray<FBox2D> Regions;
        if(Frame%5==0)Regions.Add(FBox2D(XY[N*N/2]-FVector2D(1100),XY[N*N/2]+FVector2D(1100)));
        for(auto* W:{&Original,&Candidate})
            if(!W->BuildAdaptive(XY,Triangles,Height,3,.5f,Regions,nullptr,true,true,Detail,25.f,Frame!=14))return false;
        if(!Serial.BuildAdaptive(XY,Triangles,Height,3,.5f,Regions,nullptr,false,false,Detail,25.f))return false;
        TArray<FVector2D> A,B,C;Original.Expand(XY,A);Candidate.Expand(XY,B);Serial.Expand(XY,C);
        TestTrue(TEXT("level-local memo preserves original and serial ordered topology, ownership and coordinates"),
            Original.MidpointParents==Candidate.MidpointParents && Original.Triangles==Candidate.Triangles &&
            Original.TriangleOrigins==Candidate.TriangleOrigins && A==B && B==C &&
            Original.MidpointParents==Serial.MidpointParents && Original.Triangles==Serial.Triangles &&
            Original.TriangleOrigins==Serial.TriangleOrigins);
        Compared+=A.Num();
    }
    AddInfo(FString::Printf(TEXT("Level-local/shared/serial exact over %lld vertices and 24 moving profiles, crops, winding, regions, detail windows and cache epochs"),Compared));
    return !HasAnyErrors();
}
#endif
