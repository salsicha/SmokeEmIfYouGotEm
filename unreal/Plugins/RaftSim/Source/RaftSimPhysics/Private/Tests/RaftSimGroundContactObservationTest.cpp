#include "Misc/AutomationTest.h"
#include "RaftSimChronoRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimGroundContactObservationTest,
    "RaftSim.Physics.GroundContactObservationIsReadOnly",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimGroundContactObservationTest::RunTest(const FString&)
{
    auto* Control=NewObject<URaftSimChronoRuntimeAdapter>();
    auto* Observed=NewObject<URaftSimChronoRuntimeAdapter>();
    FRaftSimRaftBodyConfig Body;Body.Runtime=ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg=220;Body.LengthMeters=4.3f;Body.WidthMeters=2.f;Body.TubeRadiusMeters=.28f;
    Body.InertiaTensorKgM2=FVector(180,180,400);
    FRaftSimFlexParameters Flex;Flex.MassKg=Body.MassKg;Flex.LengthM=Body.LengthMeters;
    Flex.WidthM=Body.WidthMeters;Flex.TubeRadiusM=Body.TubeRadiusMeters;
    Flex.GuideMassKg=0;Flex.PassengerMassKg=0;Flex.PassengerCount=0;
    FRaftSimRaftKinematicState Initial;
    Initial.WorldTransform.SetTranslation(FVector(0,0,-50));
    Initial.LinearVelocityMetersPerSecond=FVector(3,0,-4);
    for(auto* Adapter:{Control,Observed})
    {
        Adapter->ConfigureRaftBody(Body);Adapter->ConfigureFlexibleRaftModel(Flex,{});
        Adapter->SetWaterSurfaceSampler([](const FVector&,float&){return false;});
        Adapter->SetGroundSurfaceSampler([](const FVector&,float& Z,FVector& N){Z=0;N=FVector::UpVector;return true;});
        Adapter->SetKinematicState(Initial);
    }
    int32 Count=0;FRaftSimGroundContactObservation Last;
    Observed->SetGroundContactObserver([&](const FRaftSimGroundContactObservation& O){++Count;Last=O;});
    for(int32 Step=0;Step<24;++Step)
    {
        TestTrue(TEXT("control advances"),Control->StepRaftDynamics(1.f/120.f));
        TestTrue(TEXT("observed advances"),Observed->StepRaftDynamics(1.f/120.f));
        const auto& A=Control->GetKinematicState();const auto& B=Observed->GetKinematicState();
        TestTrue(TEXT("observer does not change pose or either velocity"),
            A.WorldTransform.Equals(B.WorldTransform,0.) && A.LinearVelocityMetersPerSecond==B.LinearVelocityMetersPerSecond &&
            A.AngularVelocityRadiansPerSecond==B.AngularVelocityRadiansPerSecond);
        if(Step<12)
        {
            TestEqual(TEXT("one observation for each actual projection"),Count,Step+1);
            const FVector Point=Last.PredictedPoseCm.TransformPosition(Last.LocalSupportMeters*100.);
            TestTrue(TEXT("reported support and radius reconstruct actual correction"),
                FMath::Abs(Last.VerticalCorrectionMeters-(Last.GroundZCm*.01+Last.RadiusMeters-Point.Z*.01))<1.e-12);
            TestTrue(TEXT("observation is before the applied projection"),
                FMath::Abs(B.WorldTransform.GetLocation().Z-Last.PredictedPoseCm.GetLocation().Z-100.*Last.VerticalCorrectionMeters)<1.e-10);
        }
        if(Step==11)Observed->SetGroundContactObserver({});
    }
    TestEqual(TEXT("cleared observer never receives later contact"),Count,12);
    return !HasAnyErrors();
}
#endif
