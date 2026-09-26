#include "Misc/AutomationTest.h"
#include "RaftSimDetailEntrainment.h"
#include "RaftSimDetailWaterGPU.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimEntrainmentRoundoffTest,
    "RaftSim.WaterDetail.EntrainmentRoundoffRange",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimEntrainmentRoundoffTest::RunTest(const FString&)
{
    int32 OldOvershoots=0;double MaxError=0;
    for(const FVector2f Bounds:{FVector2f(.65f,1.1f),FVector2f(.05f,.65f)})
    {
        float Previous=-1;
        for(int32 I=0;I<=1000000;++I)
        {
            const float X=Bounds.X+(Bounds.Y-Bounds.X)*(float(I)/1000000.f);
            const float Value=FRaftSimDetailEntrainment::BoundedSmoothStep(Bounds.X,Bounds.Y,X);
            const double T=FMath::Clamp((double(X)-Bounds.X)/(double(Bounds.Y)-Bounds.X),0.,1.);
            MaxError=FMath::Max(MaxError,FMath::Abs(double(Value)-T*T*(3.-2.*T)));
            OldOvershoots+=FMath::SmoothStep(Bounds.X,Bounds.Y,X)>1.f;
            if(!FMath::IsFinite(Value) || Value<0.f || Value>1.f || Value<Previous)
            {AddError(FString::Printf(TEXT("Unbounded/nonmonotone ramp at %.9g: %.9g"),X,Value));return false;}
            Previous=Value;
        }
        TestEqual(TEXT("below lower endpoint"),FRaftSimDetailEntrainment::BoundedSmoothStep(Bounds.X,Bounds.Y,Bounds.X-1),0.f);
        TestEqual(TEXT("upper endpoint"),FRaftSimDetailEntrainment::BoundedSmoothStep(Bounds.X,Bounds.Y,Bounds.Y),1.f);
    }
    TestTrue(TEXT("same cubic within float arithmetic tolerance"),MaxError<2e-7);
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(16,16);
    TArray<FVector4f> Flow;Flow.Init(FVector4f(.184797242f,-.781726241f,-.880908549f,1.00000012f),256);
    FString Error;
    TestFalse(TEXT("observed one-ULP invalid source remains rejected"),Grid.Validate(Flow,Error));
    FRaftSimDetailEntrainment::Build(Grid.Size,.5f,Flow);
    TestTrue(TEXT("producer supplies valid flow without weakening guard"),Grid.Validate(Flow,Error));
    AddInfo(FString::Printf(TEXT("2000002 ramp samples; legacy overshoots=%d max cubic error=%.9g"),OldOvershoots,MaxError));
    return !HasAnyErrors();
}
#endif
