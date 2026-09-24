#include "RaftSimWaterSourceBounds.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterSourceBoundsTest,
    "RaftSim.M4.WaterSourceBounds", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimWaterSourceBoundsTest::RunTest(const FString&)
{
    for (int32 Count : {0, 1, 1023, 1024, 1025, 50625, 65537})
    {
        TArray<FProcMeshVertex> Source;
        Source.SetNum(Count);
        for (int32 Epoch = 0; Epoch < 4; ++Epoch)
        {
            for (int32 I = 0; I < Count; ++I)
                Source[I].Position = FVector((I % 211 - 105) * .03125 + Epoch * 1600.,
                    (I % 317 - 158) * -.125, ((I * 17) % 701 - 350) * .0625 - Epoch * .125);
            if (Count > 1024)
            {
                Source[1023].Position = FVector(-1.e6, 2.e6, -3.e6);
                Source[1024].Position = FVector(1.e6, -2.e6, 3.e6);
            }
            const FBox A = RaftSimWaterSourceBounds::Reference(Source);
            const FBox B = RaftSimWaterSourceBounds::Parallel(Source);
            TestEqual(TEXT("validity matches including empty input"), B.IsValid, A.IsValid);
            if (A.IsValid)
            {
                TestTrue(TEXT("all min/max coordinates match exactly"), A.Min == B.Min && A.Max == B.Max);
                for (const auto& V : Source)
                    if (!B.IsInsideOrOn(V.Position)) { AddError(TEXT("source position excluded")); break; }
            }
        }
    }
    return !HasAnyErrors();
}
#endif
