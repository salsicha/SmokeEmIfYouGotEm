#include "Misc/AutomationTest.h"
#include "Environment/RaftSimContinuousCollisionProbes.h"
#include "Serialization/MemoryReader.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimContinuousCollisionProbesTest,
    "RaftSim.Continuous.CollisionProbeStream",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimContinuousCollisionProbesTest::RunTest(const FString&)
{
    TArray<uint8> Bytes;
    auto Append=[&](double Value)
    {
        uint64 Bits;FMemory::Memcpy(&Bits,&Value,8);
        for(int32 I=0;I<8;++I)Bytes.Add(uint8(Bits>>(I*8)));
    };
    for(double Value:{-25200.,25200.,123.125,25200.,-25200.,-7.5})Append(Value);
    FString Error;int32 Seen=0;
    FMemoryReader Good(Bytes);
    TestTrue(TEXT("exact binary triples"),RaftSimContinuousCollisionProbes::Visit(Good,2,[&](const FVector& P)
    {TestTrue(TEXT("lossless position"),P.Equals(Seen==0?FVector(-25200,25200,123.125):FVector(25200,-25200,-7.5),0.));++Seen;return true;},Error));
    TestEqual(TEXT("every probe visited"),Seen,2);
    FMemoryReader WrongCount(Bytes);
    TestFalse(TEXT("reject count mismatch"),RaftSimContinuousCollisionProbes::Visit(WrongCount,1,[](const FVector&){return true;},Error));
    FMemoryReader CallbackFailure(Bytes);
    TestFalse(TEXT("propagate collision failure"),RaftSimContinuousCollisionProbes::Visit(CallbackFailure,2,[](const FVector&){return false;},Error));
    Bytes.Pop();FMemoryReader Truncated(Bytes);
    TestFalse(TEXT("reject truncated triple"),RaftSimContinuousCollisionProbes::Visit(Truncated,2,[](const FVector&){return true;},Error));
    Bytes.Reset();Append(0.);Append(0.);Append(std::numeric_limits<double>::quiet_NaN());FMemoryReader Nonfinite(Bytes);
    TestFalse(TEXT("reject nonfinite height"),RaftSimContinuousCollisionProbes::Visit(Nonfinite,1,[](const FVector&){return true;},Error));
    return true;
}
#endif
