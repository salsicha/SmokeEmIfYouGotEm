#include "Misc/AutomationTest.h"
#include "RaftSimHolePourOver.h"
#include "RaftSimHoleWave.h"
#include "RaftSimHoleChurn.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimHoleWaterTest, "RaftSim.Physics.HoleWater",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimHoleWaterTest::RunTest(const FString&)
{
    // A 0.8 m pour-over 2 m long on a 2 m/s current: its face drops 1.05 m
    // to the trough over 1.9 m, as the hull's crest relief draws it.
    const auto Water = [](double Along) { return Along <= 0.0 ? 0.8 : FMath::Lerp(0.8, -0.25, FMath::Min(Along / 1.9, 1.0)); };
    const FVector Base(2.0, 0.0, 0.0);
    const auto SampleAt = [&](const FVector2D& P, double& S, FVector& V) { S = Water(P.X); V = Base; return true; };
    const auto Face = RaftSimHolePourOver::FSite::FromCrestLength(FVector2D::ZeroVector, FVector2D(1.0, 0.0), 2.0);
    const auto Falling = [&](double Along, double Z)
    { return RaftSimHolePourOver::Velocity(Face, FVector(Along, 0.0, Z), Base, Water(Along), FVector::ForwardVector, FVector::RightVector, SampleAt); };

    // Down the face the water falls: faster than it came and downward, as
    // fast as the drop gives it.
    const FVector OnFace = Falling(1.2, Water(1.2));
    TestTrue(TEXT("water on the face outruns the approach"), OnFace.Size() > 3.5);
    TestTrue(TEXT("and falls"), OnFace.Z < -1.0);
    TestTrue(TEXT("at the speed the drop gives it"),
        FMath::IsNearlyEqual(OnFace.Size(), FMath::Sqrt(4.0 + 2.0 * 9.81 * (0.8 - Water(1.2))), 0.2));
    // Anything just above the sheet (a tube top, a paddler) meets it too;
    // well under the sheet, and upstream of the crest, the water is its own.
    TestTrue(TEXT("a tube top over the face is hit by it"), Falling(1.2, Water(1.2) + 0.3).Z < -1.0);
    TestTrue(TEXT("deep water under the sheet keeps its flow"), Falling(1.2, Water(1.2) - 1.5).Equals(Base));
    TestTrue(TEXT("nothing falls upstream of the crest"), Falling(-0.5, 0.8).Equals(Base));
    TestTrue(TEXT("the falling sheet ends at the face's foot"), Falling(2.5, -0.25).Equals(Base));
    // A flat river has no pour-over.
    const auto Flat = [&](const FVector2D&, double& S, FVector& V) { S = 0.0; V = Base; return true; };
    TestTrue(TEXT("no drop, no falling water"), RaftSimHolePourOver::Velocity(Face, FVector(1.0, 0.0, 0.0), Base, 0.0,
        FVector::ForwardVector, FVector::RightVector, Flat).Equals(Base));

    // The breaking wave below it is the one the churn draws.
    FRaftSimHoleChurnSite Drawn;
    Drawn.Look = FRaftSimHoleChurnLook::Preset(TEXT("roll"));
    const RaftSimHoleWave::FShape Pile = URaftSimHoleChurnComponent::ShapeOf(Drawn);
    const RaftSimHoleWave::FShape FromCrest = RaftSimHoleWave::FShape::ForCrest(0.8, 2.0, 1.0);
    TestTrue(TEXT("a site's own pile matches the drawn roll"),
        FMath::IsNearlyEqual(FromCrest.HeightM, Pile.HeightM, 0.01) && FMath::IsNearlyEqual(FromCrest.LengthM, Pile.LengthM, 0.01) &&
        FMath::IsNearlyEqual(FromCrest.PlungeOffsetM, Pile.PlungeOffsetM, 0.01) && FMath::IsNearlyEqual(FromCrest.ThrowM, Pile.ThrowM, 0.01) &&
        FMath::IsNearlyEqual(FromCrest.HalfWidthM, Pile.HalfWidthM, 0.01));
    TestTrue(TEXT("its crest stands its full height over the trough"), FMath::IsNearlyEqual(Pile.TopAboveToe(Pile.CrestAlong(), 0.0), Pile.HeightM, 0.01));
    TestEqual(TEXT("no pile upstream of where its front lands"), Pile.TopAboveToe(Pile.PlungeAlong() - 0.05, 0.0), 0.0);
    TestEqual(TEXT("none past its boil line"), Pile.TopAboveToe(Pile.BoilAlong() + 0.05, 0.0), 0.0);
    TestTrue(TEXT("it dies away at the hole's ends"), Pile.TopAboveToe(Pile.CrestAlong(), Pile.HalfWidthM) < 0.25 * Pile.HeightM);

    // On its front the hull floats higher, is pushed back upstream down its
    // slope and meets its water rolling upstream; on its back the slope runs
    // the other way. Off it, nothing changes.
    const double Toe = -0.25;
    const double FrontAlong = 0.5 * (Pile.PlungeAlong() + Pile.CrestAlong());
    RaftSimHoleWave::FHullWater Front, Back, Off;
    TestTrue(TEXT("the front of the pile stands above the trough"), RaftSimHoleWave::Apply(Pile, FrontAlong, 0.0, Toe, Toe, Toe,
        Base, FVector::ForwardVector, FVector::RightVector, Front));
    TestTrue(TEXT("the hull floats higher on it"), Front.SurfaceM > Toe + 0.1);
    TestTrue(TEXT("its slope pushes a hull back upstream"), Front.Slope.X > 0.3);
    TestTrue(TEXT("its water falls back upstream down its curling front"), Front.VelocityMps.X < 0.0 && Front.VelocityMps.Z < -0.5);
    TestTrue(TEXT("its back"), RaftSimHoleWave::Apply(Pile, 0.5 * (Pile.CrestAlong() + Pile.BoilAlong()), 0.0, Toe, Toe, Toe,
        Base, FVector::ForwardVector, FVector::RightVector, Back));
    TestTrue(TEXT("slopes a hull on over it"), Back.Slope.X < 0.0);
    TestTrue(TEXT("while its water still rolls upstream"), Back.VelocityMps.X < -1.0);
    TestFalse(TEXT("off the pile"), RaftSimHoleWave::Apply(Pile, Pile.BoilAlong() + 1.0, 0.0, 0.0, Toe, 0.0,
        Base, FVector::ForwardVector, FVector::RightVector, Off));
    TestTrue(TEXT("the water is unchanged"), Off.SurfaceM == 0.0 && Off.VelocityMps.Equals(Base) && Off.Slope.IsZero());
    return true;
}
#endif
