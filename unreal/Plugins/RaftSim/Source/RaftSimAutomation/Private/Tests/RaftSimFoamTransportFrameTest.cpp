#include "Misc/AutomationTest.h"
#include "RaftSimFoamTransportFrame.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSpillingFoamBudgetTest,
    "RaftSim.Water.SpillingFoamBudget",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSpillingFoamBudgetTest::RunTest(const FString&)
{
    for (float Weight : {0.f,.1f,.3f,.75f,1.f})
    {
        TestEqual(TEXT("nonspilling accepted wave does not continually generate pocket foam"),
            RaftSimFoamTransport::BreakingSourceWeight(Weight,0.f,true),0.f);
        TestEqual(TEXT("fully spilling site preserves its source envelope"),
            RaftSimFoamTransport::BreakingSourceWeight(Weight,1.f,true),Weight);
        TestEqual(TEXT("unmigrated legacy scenes retain their source calibration"),
            RaftSimFoamTransport::BreakingSourceWeight(Weight,0.f,false),Weight);
        float Previous=0.f;
        for (int32 I=0;I<=100;++I)
        {
            const float Fraction=I/100.f;
            const float Source=RaftSimFoamTransport::BreakingSourceWeight(Weight,Fraction,true);
            TestEqual(TEXT("pocket and boil share the same eased spilling budget as crest foam"),Source,Weight*Fraction);
            TestTrue(TEXT("source has no positive minimum or nonmonotonic whitening"),Source>=Previous && Source<=Weight);
            Previous=Source;
        }
    }
    TestEqual(TEXT("negative fraction cannot create foam"),RaftSimFoamTransport::BreakingSourceWeight(1,-1,true),0.f);
    TestEqual(TEXT("fraction remains bounded"),RaftSimFoamTransport::BreakingSourceWeight(1,2,true),1.f);
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFoamTransportFrameTest,
    "RaftSim.Water.FoamTransportGeographicReflection",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFoamTransportFrameTest::RunTest(const FString& Parameters)
{
    // Includes the actual captured Troublemaker downstream direction and
    // rotated flows: pure station, pure lateral, mixed and reverse current.
    for (const FVector2D SourceTangent : {FVector2D(1,0), FVector2D(0,1),
             FVector2D(-.93,.36756).GetSafeNormal(), FVector2D(.6,.8)})
    {
        const FVector2D SourceLeft(-SourceTangent.Y, SourceTangent.X);
        for (const float Sign : {1.0f,-1.0f})
        {
            const FVector Tangent(SourceTangent.X,SourceTangent.Y*Sign,0);
            const FVector Left(SourceLeft.X,SourceLeft.Y*Sign,0);
            const FVector LocalNormal = FVector(-.12,.31,1).GetSafeNormal();
            const FVector Actual = RaftSimFoamTransport::TransformSurfaceNormal(LocalNormal,Tangent,Sign);
            const FVector StationEdge = Tangent+FVector(0,0,.12);
            const FVector LateralEdge = Left+FVector(0,0,-.31);
            const FVector Geometric = (FVector::CrossProduct(StationEdge,LateralEdge)*Sign).GetSafeNormal();
            TestTrue(TEXT("Shading normal matches the reflected source surface derivatives"),Actual.Equals(Geometric,1e-6));
            TestTrue(TEXT("Tangent-space bitangent follows source-left UV axis"),
                (FVector::CrossProduct(FVector::UpVector,Tangent)*Sign).Equals(Left,1e-6));
        }
        for (const FVector2D FieldVelocity : {FVector2D(3,0), FVector2D(0,2),
                 FVector2D(2.2,-.85), FVector2D(-1.4,.5), FVector2D::ZeroVector})
        {
            const FVector2D SourceVelocity = SourceTangent*FieldVelocity.X+SourceLeft*FieldVelocity.Y;
            for (const float Sign : {1.0f,-1.0f})
            {
                const FVector2D Tangent(SourceTangent.X,SourceTangent.Y*Sign);
                const FVector2D Velocity(SourceVelocity.X,SourceVelocity.Y*Sign);
                const FVector2D Projected = RaftSimFoamTransport::ProjectWorldVelocity(Velocity,Tangent,Sign);
                TestTrue(TEXT("spray receives reflected world velocity exactly once"),
                    RaftSimFoamTransport::TransformFieldVelocity(FieldVelocity,Tangent,Sign).Equals(Velocity,1e-6));
                TestTrue(TEXT("Station and source-left velocity preserved under world reflection"),
                    Projected.Equals(FieldVelocity,1e-6));
                const FVector2D Position(12.0,-4.0);
                TestTrue(TEXT("Semi-Lagrangian upstream lookup stays in the same source cell"),
                    (Position-Projected*.125).Equals(Position-FieldVelocity*.125,1e-6));
            }
        }
    }
    return true;
}
#endif
