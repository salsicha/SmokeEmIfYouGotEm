#include "RaftSimRapidFeatureFrame.h"
#include "Misc/AutomationTest.h"
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRapidFeatureFrameTest,
    "RaftSim.Continuous.RapidFeatureFrame",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FRaftSimRapidFeatureFrameTest::RunTest(const FString&)
{
    using namespace RaftSimRapidFeatureFrame;
    auto Heading=[](double Degrees,const FVector& T,const FVector& L)
    {
        const double A=FMath::DegreesToRadians(Degrees);
        return T*FMath::Cos(A)+L*FMath::Sin(A);
    };
    for(double Sign:{-1.,1.})
    for(double Bearing:{0.,37.,90.,180.,270.})
    for(double Normal:{-35.,0.,35.})
    {
        const double A=FMath::DegreesToRadians(Bearing);
        const FVector ST(FMath::Cos(A),Sign*FMath::Sin(A),0.);
        const FVector SL(-FMath::Sin(A),Sign*FMath::Cos(A),0.);
        const FVector TT(1.,0.,0.),TL(0.,Sign,0.);
        double MovedNormal=0.,MovedFlow=0.;
        TestTrue(TEXT("normal transfers through either world-Y convention"),
            ReexpressAngle(Normal,ST,SL,TT,TL,MovedNormal));
        TestTrue(TEXT("downstream activation axis transfers independently"),
            ReexpressAngle(0.,ST,SL,TT,TL,MovedFlow));
        TestTrue(TEXT("world-space crest normal is unchanged"),
            Heading(Normal,ST,SL).Equals(Heading(MovedNormal,TT,TL),1.e-10));
        TestTrue(TEXT("world-space downstream is unchanged"),
            ST.Equals(Heading(MovedFlow,TT,TL),1.e-10));
        // Preserve the old signed downstream test, not total speed and not
        // projection along the diagonal crest normal. Crossflow cannot turn
        // an upstream or stagnant site into an active rapid.
        for(double Along:{-3.,0.,.749,.751,3.})
        for(double Across:{-7.,0.,7.})
        {
            const FVector WorldVelocity=ST*Along+SL*Across;
            const FVector FieldVelocity(FVector::DotProduct(WorldVelocity,TT),
                FVector::DotProduct(WorldVelocity,TL),0.);
            const double Actual=DownstreamSpeed(FieldVelocity,MovedFlow);
            TestTrue(TEXT("signed speed invariant under chart rotation"),FMath::Abs(Actual-Along)<1.e-10);
            TestEqual(TEXT("unchanged activation threshold"),Actual>=.75,Along>=.75);
        }
        double Roundtrip=0.;
        TestTrue(TEXT("reverse registration succeeds"),ReexpressAngle(MovedNormal,TT,TL,ST,SL,Roundtrip));
        TestTrue(TEXT("normal survives roundtrip"),Heading(Roundtrip,ST,SL).Equals(Heading(Normal,ST,SL),1.e-10));
    }
    const FVector X(1.,0.,0.),Y(0.,1.,0.);
    double Out=123.;
    TestFalse(TEXT("nonfinite angle refused"),ReexpressAngle(std::numeric_limits<double>::quiet_NaN(),X,Y,X,Y,Out));
    TestEqual(TEXT("failure clears previous output"),Out,0.);
    TestFalse(TEXT("scaled basis refused"),ReexpressAngle(0.,X*2.,Y,X,Y,Out));
    TestFalse(TEXT("nonorthogonal basis refused"),ReexpressAngle(0.,X,X,X,Y,Out));
    TestFalse(TEXT("vertical basis refused"),ReexpressAngle(0.,X,FVector(0.,0.,1.),X,Y,Out));
    TestFalse(TEXT("nonfinite target refused"),ReexpressAngle(0.,X,Y,X,FVector(0.,std::numeric_limits<double>::infinity(),0.),Out));
    TestEqual(TEXT("legacy zero-angle speed unchanged"),DownstreamSpeed(FVector(3.,7.,0.),0.),3.);
    return !HasAnyErrors();
}
#endif
