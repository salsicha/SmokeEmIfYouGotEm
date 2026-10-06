#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterFlowFrame.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimWaterFlowFrameTest,
    "RaftSim.P2.CurrentOrientedBreakingRelief",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimWaterFlowFrameTest::RunTest(const FString&)
{
    using namespace RaftSimWaterFlowFrame;
    double MaxHeightError=0.,MaxFoamError=0.,MaxRoundTrip=0.;
    int32 Samples=0;
    const FVector2D OpposedBlend=BlendDirections(FVector2D(1.,0.),FVector2D(-1.,0.),.5);
    TestTrue(TEXT("persistent direction reversal stays unit length"),FMath::Abs(OpposedBlend.Size()-1.)<1.e-12 && FMath::Abs(OpposedBlend.Y)>.99);
    const FVector2D SeamBlend=BlendDirections(FromAngle(3.1f),FromAngle(-3.1f),.5);
    TestTrue(TEXT("persistent heading crosses pi by the short arc"),SeamBlend.X<-.999 && FMath::Abs(SeamBlend.Y)<1.e-6);
    for (bool Physical : {false,true}) for (bool LocalCap : {false,true})
    {
        TArray<URaftSimWaterRuntimeAdapter::FSupportBreakingSite> Original;
        auto& A=Original.AddDefaulted_GetRef(); A.RiverCoordinatesMeters=FVector2D(.25,-.75);
        A.Intensity=.7f; A.PhysicalCrestHeightMeters=Physical?.8f:-1.f;
        A.PhysicalCrestLengthMeters=3.7f; A.SpillingFraction=.65f; A.bLocalEnvelopeCap=LocalCap;
        auto& B=Original.AddDefaulted_GetRef(); B=Original[0]; B.RiverCoordinatesMeters+=FVector2D(2.,3.);
        B.PhysicalCrestHeightMeters=Physical?.43f:-1.f; B.Intensity=.35f;
        for (const float Angle : {0.f,float(PI),float(PI/2),float(-PI/2),.713f,-2.31f})
        {
            const FVector2D D=FromAngle(Angle), Translation(-5432.,3600.);
            auto Rotated=Original;
            for (auto& Site : Rotated)
            {
                Site.RiverCoordinatesMeters=Translation+ToField(Site.RiverCoordinatesMeters,D);
                Site.FlowDirection=D;
            }
            const FVector2D Bounds=XBounds(D,-32.,23.,12.);
            for (const double Along : {-32.,23.}) for (const double Across : {-12.,12.})
            {
                const double X=ToField(FVector2D(Along,Across),D).X;
                TestTrue(TEXT("oriented site bucket retains every envelope corner"),X>=Bounds.X-1.e-12&&X<=Bounds.Y+1.e-12);
            }
            for (int32 Y=-13;Y<=13;++Y) for (int32 X=-24;X<=54;++X)
            {
                const FVector2D P(X*.5+.123,Y*.7+.234), Q=Translation+ToField(P,D);
                MaxRoundTrip=FMath::Max(MaxRoundTrip,FVector2D::Distance(ToLocal(Q-Translation,D),P));
                float Foam=0,RotatedFoam=0;
                const float H=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(P,Original,.22f,1.f,&Foam);
                const float RH=URaftSimWaterRuntimeAdapter::ComputeCoupledBreakingReliefMeters(Q,Rotated,.22f,1.f,&RotatedFoam);
                MaxHeightError=FMath::Max(MaxHeightError,double(FMath::Abs(H-RH)));
                MaxFoamError=FMath::Max(MaxFoamError,double(FMath::Abs(Foam-RotatedFoam)));
                ++Samples;
            }
            // The same transform applied to a returning roller velocity must
            // move upstream in field coordinates, including west/north flow.
            const FVector2D Roller=ToField(FVector2D(-1.3,.2),D);
            TestTrue(TEXT("roller returns against signed bulk flow"),FVector2D::DotProduct(Roller,D)<0.);
            const FVector2D FieldStart=Translation+ToField(FVector2D(4.,2.),D);
            TestTrue(TEXT("foam backtrace commutes with rotation"),
                FVector2D::Distance(ToLocal(FieldStart-Roller*.05-Translation,D),FVector2D(4.,2.)-FVector2D(-1.3,.2)*.05)<1.e-11);
        }
    }
    TestTrue(TEXT("rotated physical/legacy heights retain the same profile"),MaxHeightError<1.e-6);
    TestTrue(TEXT("rotated spilling remains localized to the same crest"),MaxFoamError<1.e-6);
    TestTrue(TEXT("large geographic translation and rotation round trip"),MaxRoundTrip<1.e-11);
    TArray<uint8> Wet; Wet.Init(1,13*13);
    auto Clearance=WetEdgeSteps(13,13,Wet);
    TestEqual(TEXT("all-wet domain still reserves all four grid edges"),Clearance[6*13+6],6);
    Wet[6*13+6]=0;
    Clearance=WetEdgeSteps(13,13,Wet);
    TestEqual(TEXT("internal dry island has a pinned wet rim"),Clearance[5*13+5],0);
    TestEqual(TEXT("diagonal clearance is conservative"),Clearance[3*13+3],2);
    TestEqual(TEXT("east-facing upstream stencil looks west"),OffsetIndex(6*13+6,13,13,FVector2D(1,0),-3.),6*13+3);
    TestEqual(TEXT("west-facing upstream stencil looks east"),OffsetIndex(6*13+6,13,13,FVector2D(-1,0),-3.),6*13+9);
    TestEqual(TEXT("north-facing upstream stencil looks south"),OffsetIndex(6*13+6,13,13,FVector2D(0,1),-3.),3*13+6);
    TestEqual(TEXT("south-facing upstream stencil looks north"),OffsetIndex(6*13+6,13,13,FVector2D(0,-1),-3.),9*13+6);
    TestEqual(TEXT("stencil never wraps between rows"),OffsetIndex(6*13,13,13,FVector2D(-1,0),1.),INDEX_NONE);
    TArray<float> Values; Values.SetNumUninitialized(Wet.Num());
    for (int32 Y=0;Y<13;++Y) for (int32 X=0;X<13;++X) Values[Y*13+X]=2.f*X+3.f*Y;
    float Interpolated=0.;
    TestTrue(TEXT("directional relief interpolates the same wet plane"),
        SampleWetScalar(Values,Wet,13,13,FVector2D(3.25,4.75),Interpolated)&&Interpolated==20.75f);
    TestFalse(TEXT("fractional relief sample cannot bridge a dry island"),
        SampleWetScalar(Values,Wet,13,13,FVector2D(5.5,5.5),Interpolated));
    TestFalse(TEXT("relief sample never clamps outside source"),
        SampleWetScalar(Values,Wet,13,13,FVector2D(-.1,4.),Interpolated));
    AddInfo(FString::Printf(TEXT("%d signed/rotated crest samples; height error %.12g m, foam error %.12g, XY error %.12g m"),Samples,MaxHeightError,MaxFoamError,MaxRoundTrip));
    return !HasAnyErrors();
}
#endif
