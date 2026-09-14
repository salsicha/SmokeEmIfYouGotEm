#include "Misc/AutomationTest.h"
#include "RaftSimSurfaceRefinement.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestBatchTest,
    "RaftSim.M4.CrestBatchScheduling",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestBatchTest::RunTest(const FString&)
{
    constexpr int32 N=25;
    TArray<FVector2D> XY;TArray<int32> Triangles;
    for(int32 Y=0;Y<N;++Y)for(int32 X=0;X<N;++X)
    {
        XY.Emplace(-544000.+100.*X,-360000.+100.*Y);
        if(X<N-1 && Y<N-1){const int32 A=Y*N+X;Triangles.Append({A,A+N,A+1,A+1,A+N,A+N+1});}
    }
    FRaftSimSurfaceRefinement Serial,Work[5];
    constexpr int32 Sizes[]={32,64,128,256,512};
    int64 Compared=0;
    for(int32 Frame=0;Frame<18;++Frame)
    {
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
        if(!Serial.BuildAdaptive(XY,Triangles,Height,3,.5f,{},nullptr,false,false,Detail,25.f))return false;
        TArray<FVector2D> Expected;Serial.Expand(XY,Expected);
        for(int32 I=0;I<5;++I)
        {
            // Regroup existing tables between calls as well as comparing five
            // fixed-size alternatives; every value must belong to this epoch.
            auto& W=Work[I];W.ParallelBatchSize=Sizes[(I+Frame)%5];
            if(!W.BuildAdaptive(XY,Triangles,Height,3,.5f,{},nullptr,true,true,Detail,25.f,Frame!=14))return false;
            TArray<FVector2D> Actual;W.Expand(XY,Actual);
            TestTrue(TEXT("batch grouping preserves exact current topology and coordinates"),
                W.MidpointParents==Serial.MidpointParents && W.Triangles==Serial.Triangles &&
                W.TriangleOrigins==Serial.TriangleOrigins && Actual==Expected);
            Compared+=Actual.Num();
        }
    }
    Work[0].ParallelBatchSize=0;
    TestFalse(TEXT("invalid batch size rejected"),Work[0].Build(XY,Triangles,FBox2D(XY),1));
    AddInfo(FString::Printf(TEXT("Five regrouped batch schedules compared %lld expanded vertices across18 changing profiles/crops/detail windows against serial selection"),Compared));
    return !HasAnyErrors();
}
#endif
