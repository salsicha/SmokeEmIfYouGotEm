#include "RaftSimShorelineCrestWeights.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimShorelineCrestWeightsTest,
    "RaftSim.M4.ShorelineCrestWeights",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimShorelineCrestWeightsTest::RunTest(const FString&)
{
    FRaftSimShorelineCrestWeights Scratch;
    for(int32 Frame=0;Frame<32;++Frame)
    {
        // Growing, shrinking and empty edge lists must erase old shore weights.
        const int32 Count=Frame%4 ? 221 : 4, Total=Count+Frame%7;
        TArray<float> A,B,ExpectedA,ExpectedB;
        A.SetNum(Count);B.SetNum(Count);
        for(int32 I=0;I<Count;++I)
        {A[I]=(I%2 ? -1.f : 1.f)*(Frame+I)*.03125f;B[I]=(I%5)*.125f;}
        A[0]=-0.f;
        TArray<RaftSimWaterShoreline::FEdge> Edges;
        for(int32 I=Count;I<Total;++I) if((I+Frame)%2)
            Edges.Add({(I+Frame)%Count,0,I,.5});
        // Independent original scalar publication contract, including reserves.
        ExpectedA.Init(0,Total);ExpectedB.Init(0,Total);
        for(int32 I=0;I<Count;++I){ExpectedA[I]=A[I];ExpectedB[I]=B[I];}
        for(const auto& E:Edges)
        {ExpectedA[E.Node]=ExpectedA[E.WetVertex];ExpectedB[E.Node]=ExpectedB[E.WetVertex];}
        Scratch.Update(Total,A,B,Edges);
        TestTrue(TEXT("Every coarse float is bit-exact"),
            FMemory::Memcmp(ExpectedA.GetData(),Scratch.Coarse.GetData(),Total*sizeof(float))==0);
        TestTrue(TEXT("Every shore float is bit-exact"),
            FMemory::Memcmp(ExpectedB.GetData(),Scratch.Shore.GetData(),Total*sizeof(float))==0);
    }
    return true;
}
#endif
