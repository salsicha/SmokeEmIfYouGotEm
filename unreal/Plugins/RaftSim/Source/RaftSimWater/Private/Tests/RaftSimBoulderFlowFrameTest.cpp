#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimBoulderFlowFrameTest,
    "RaftSim.P2.CurrentOrientedBoulderRelief",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimBoulderFlowFrameTest::RunTest(const FString&)
{
    using namespace RaftSimWaterFlowFrame;
    using FFootprint = URaftSimWaterRuntimeAdapter::FSupportBoulderFootprint;
    auto* Water = NewObject<URaftSimWaterRuntimeAdapter>();
    const TArray<FFootprint> Original = {
        {FVector2D(0., 0.), 1.5f}, {FVector2D(3., 2.), .9f}};
    double MaxError = 0.;
    int32 Samples = 0, NonzeroSamples = 0;
    for (const float Angle : {0.f, float(PI), float(PI/2), float(-PI/2), .713f, -2.31f})
    {
        const FVector2D D = FromAngle(Angle), Translation(-5432., 3600.);
        auto Rotated = Original;
        for (auto& Rock : Rotated) Rock.RiverCoordinatesMeters =
            Translation + ToField(Rock.RiverCoordinatesMeters, D);
        Water->ConfigureRaftSupportBoulderFootprints(Rotated);
        for (const float Speed : {0.f, .3f, .8f, 1.8f})
        for (int32 Y = -24; Y <= 24; ++Y) for (int32 X = -12; X <= 80; ++X)
        {
            const FVector2D P(X*.25+.123, Y*.25+.234);
            // Independent expected profile in the original +X frame, including
            // overlapping rocks: do not use the new configured rotation path.
            float Expected = 0.f;
            for (const auto& Rock : Original)
            {
                const FVector2D R = P - Rock.RiverCoordinatesMeters;
                const float H = URaftSimWaterRuntimeAdapter::ComputeCoupledBoulderPillowDisplacementMeters(
                    R.X, R.Y, Rock.RadiusMeters, Speed) +
                    URaftSimWaterRuntimeAdapter::ComputeCoupledBoulderWakePresentation(
                        R.X, R.Y, Rock.RadiusMeters, Speed, 2.4f).X;
                if (FMath::Abs(H) > FMath::Abs(Expected)) Expected = H;
            }
            const float Actual = Water->ComputeConfiguredBoulderSupportDisplacementMeters(
                Translation + ToField(P, D), Speed, 2.4f, D);
            MaxError = FMath::Max(MaxError, double(FMath::Abs(Actual - Expected)));
            ++Samples;
            NonzeroSamples += FMath::Abs(Expected) > .01f;
        }
    }
    Water->ConfigureRaftSupportBoulderFootprints(Original);
    TestEqual(TEXT("legacy three-argument call retains +X flow"),
        Water->ComputeConfiguredBoulderSupportDisplacementMeters(FVector2D(-1.65, 0.), 1.8f, 0.f),
        Water->ComputeConfiguredBoulderSupportDisplacementMeters(FVector2D(-1.65, 0.), 1.8f, 0.f, FVector2D(1., 0.)));
    TestTrue(TEXT("rotation test exercises actual pillows and signed wakes"), NonzeroSamples > 10000);
    TestTrue(TEXT("west/north/south/oblique support preserves original signed rock profile"), MaxError < 1.e-6);
    AddInfo(FString::Printf(TEXT("%d rotated boulder samples (%d above 1 cm), max error %.12g m"), Samples, NonzeroSamples, MaxError));
    return !HasAnyErrors();
}
#endif
