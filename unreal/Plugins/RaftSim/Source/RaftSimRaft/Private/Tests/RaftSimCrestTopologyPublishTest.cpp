#include "Misc/AutomationTest.h"
#include "RaftSimCrestTopologyPublish.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrestTopologyPublishTest,
    "RaftSim.M4.CrestTopologyPublish",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimCrestTopologyPublishTest::RunTest(const FString&)
{
    TArray<uint32> A,B; TArray<int32> AO,BO;
    for (int32 Count : {0,1,2,1023,1024,1025,2048,2049,51001})
    {
        TArray<int32> Triangles,Origins,Offsets;
        for (int32 I=0; I<Count; ++I)
        {
            Offsets.Add(I*6);
            // Gaps represent dry source triangles; repeated owners are refined children.
            if (I%7==0) continue;
            for (int32 Child=0; Child<(I%11)+1; ++Child)
            { Triangles.Append({I*3,I*3+2,I*3+1}); Origins.Add(I*2); }
        }
        Offsets.Add(Count*6);
        const auto Check=[&]()
        {
            RaftSimCrestTopologyPublish::Reference(Triangles,Origins,Offsets,A,AO);
            RaftSimCrestTopologyPublish::Partitioned(Triangles,Origins,Offsets,B,BO);
            TestTrue(TEXT("all index bits and cell/sentinel offsets exactly match reference"),A==B && AO==BO);
        };
        Check();
        for (int32& Offset : Offsets) Offset+=1; // Same original integer-division semantics.
        Check();
        if (Offsets.Num()>2) { Swap(Offsets[0],Offsets.Last()); Check(); }
        if (Origins.Num()>2) { Swap(Origins[0],Origins.Last()); Check(); }
    }
    const TArray<int32> Bits={MIN_int32,-1,0,1,MAX_int32};
    RaftSimCrestTopologyPublish::Reference(Bits,{}, {},A,AO);
    RaftSimCrestTopologyPublish::Partitioned(Bits,{}, {},B,BO);
    TestTrue(TEXT("empty ownership and signed-to-unsigned conversion preserved"),A==B && AO==BO);
    return !HasAnyErrors();
}
#endif
