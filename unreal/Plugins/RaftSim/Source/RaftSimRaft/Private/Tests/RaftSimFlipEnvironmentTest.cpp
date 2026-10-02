#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "RaftSimFlipTestEnvironment.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewSeatLayout.h"
#include "RaftSimFlipCandidateLoads.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "RaftSimCapsizePolicy.h"
#include "RaftSimImplicitDrag.h"
#include "RaftSimContactWitnessPrune.h"
#include "RaftSimSwimmerSubmersion.h"
#include "RaftSimFlipObstacle.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRockPillowLoads,
    "RaftSim.Demo.RockPillowLoads",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::ProductFilter)
bool FRaftSimRockPillowLoads::RunTest(const FString&)
{
    const auto Scenes=RaftSimFlipTestEnvironment::Scenes();
    const auto& Pillow=*Scenes.FindByPredicate([](const auto& S){return S.Name==TEXT("rock_pillow_broadside");});
    TestTrue(TEXT("rock control starts without imposed roll or spin"),Pillow.InitialRollDegrees==0. && Pillow.InitialRollRateRadS==0.);
    TArray<FVector> V;TArray<FIntVector> Faces;RaftSimFlipObstacle::Geometry(V,Faces,false,true);
    TestTrue(TEXT("bed-connected wedge has the same twelve rendered/contact triangles"),V.Num()==8 && Faces.Num()==12);
    const FVector Normal=RaftSimFlipObstacle::TopNormal(true);
    for(int32 I=4;I<8;++I)TestEqual(TEXT("top mesh vertices match ground height sampler"),V[I].Z,RaftSimFlipObstacle::TopCm(V[I].X,false,true));
    TestTrue(TEXT("sloped rock supports upstream and upward, not a vertical wall"),Normal.X<0. && Normal.Z>0.);
    TestTrue(TEXT("top collision/render plane has the sampled normal"),FMath::Abs(FVector::DotProduct(V[5]-V[4],Normal))<1.e-9);
    for(double X=-3.;X<-.6;X+=.2)
    {
        FVector P(X*100.,0,0);P.Z=Pillow.Surface(P,0.)*100.;
        const FVector Flow=Pillow.Velocity(P,0.);
        const double Hx=(Pillow.Surface(P+FVector(.1,0,0),0.)-Pillow.Surface(P-FVector(.1,0,0),0.))/.002;
        TestTrue(TEXT("pillow flow is finite and tangent to visible stationary surface"),!Flow.ContainsNaN() && FMath::Abs(Flow.Z-Flow.X*Hx)<1.e-7);
        TestTrue(TEXT("pillow bed has no vertical flux"),FMath::Abs(Pillow.Velocity(FVector(X*100.,0,-200.),0.).Z)<1.e-9);
    }
    TestTrue(TEXT("no water velocity inside solid footprint"),Pillow.Velocity(FVector::ZeroVector,0.).IsZero());
    FRaftSimFlexSegmentOverwash Wet;Wet.bWet=true;Wet.bUpstreamExposed=true;
    Wet.OvertoppingDepthM=.35;Wet.LocalPosition=FVector(0,1.,0);
    FRaftSimFlexTubeSegment Tube;Tube.TributaryLengthM=1.;
    // Local +Y is upstream after yaw 90. Negative local X roll lifts the
    // downstream side and dips upstream. No integrator pose is set here.
    const FQuat Q=FQuat(FVector::UpVector,PI*.5)*FQuat(FVector::ForwardVector,-PI/6.);
    const FVector Current(4.,0,0);
    const auto Scoop=RaftSimOverwashLoads::ScoopingFace(Wet,Tube,Q,.32,Current);
    TestTrue(TEXT("dipped upstream face receives downward and downstream pressure"),Scoop.ForceN.Z<0. && Scoop.ForceN.X>0.);
    TestTrue(TEXT("scoop torque reinforces upstream dip about raft longitudinal axis"),FVector::DotProduct(Scoop.TorqueNm,Q.GetForwardVector())<0.);
    TestTrue(TEXT("scoop transfers momentum from relative water, not a roll target"),FVector::DotProduct(Scoop.ForceN,Current)>0.);
    TestTrue(TEXT("outgoing relative flow creates no suction load"),RaftSimOverwashLoads::ScoopingFace(Wet,Tube,Q,.32,-Current).ForceN.IsZero());
    TestTrue(TEXT("tangential water creates no scoop pressure"),RaftSimOverwashLoads::ScoopingFace(Wet,Tube,Q,.32,Q.GetForwardVector()*4.).ForceN.IsNearlyZero(1.e-9));
    Wet.OvertoppingDepthM=0.;
    TestTrue(TEXT("non-overtopped tube cannot scoop"),RaftSimOverwashLoads::ScoopingFace(Wet,Tube,Q,.32,Current).ForceN.IsZero());
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFlipLoadsAndPolicy,
    "RaftSim.Demo.FlipLoadsAndPolicy",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::ProductFilter)
bool FRaftSimFlipLoadsAndPolicy::RunTest(const FString&)
{
    FRaftSimFlexSegmentOverwash Wet;Wet.bWet=true;Wet.bUpstreamExposed=true;
    Wet.OvertoppingDepthM=.5;Wet.IncomingSpeedMps=4.;Wet.LocalPosition=FVector(0,-1,0);
    FRaftSimFlexTubeSegment Tube;Tube.OutwardNormal=FVector(0,-1,0);Tube.TributaryLengthM=1.;
    const auto Port=RaftSimOverwashLoads::UpperFace(Wet,Tube,FQuat::Identity,.32);
    TestTrue(TEXT("port load follows the incoming current"),Port.ForceN.Y>0.);
    TestTrue(TEXT("upper-face force has signed overturning roll"),Port.TorqueNm.X<0.);
    Wet.LocalPosition.Y=1.;Tube.OutwardNormal.Y=1.;
    const auto Starboard=RaftSimOverwashLoads::UpperFace(Wet,Tube,FQuat::Identity,.32);
    TestTrue(TEXT("mirrored pressure force and torque reverse"),
        (Port.ForceN+Starboard.ForceN).IsNearlyZero() && (Port.TorqueNm+Starboard.TorqueNm).IsNearlyZero());
    Wet.LocalPosition=FVector(2,0,0);Tube.OutwardNormal=FVector(1,0,0);
    const auto Bow=RaftSimOverwashLoads::UpperFace(Wet,Tube,FQuat::Identity,.32);
    TestTrue(TEXT("bow pressure creates pitch, not invented roll"),FMath::Abs(Bow.TorqueNm.X)<1.e-9 && Bow.TorqueNm.Y<0.);
    const FQuat Rotation=FRotator(15,47,23).Quaternion();
    const auto Rotated=RaftSimOverwashLoads::UpperFace(Wet,Tube,Rotation,.32);
    TestTrue(TEXT("pressure load is rotation-covariant"),
        Rotated.ForceN.Equals(Rotation.RotateVector(Bow.ForceN),1.e-8) &&
        Rotated.TorqueNm.Equals(Rotation.RotateVector(Bow.TorqueNm),1.e-8));
    Wet.bWet=false;
    TestTrue(TEXT("dry faces contribute no pressure"),RaftSimOverwashLoads::UpperFace(Wet,Tube,FQuat::Identity,.32).ForceN.IsZero());
    Wet.bWet=true;Wet.IncomingSpeedMps=0.;
    TestTrue(TEXT("co-moving water contributes no pressure"),RaftSimOverwashLoads::UpperFace(Wet,Tube,FQuat::Identity,.32).ForceN.IsZero());
    TestFalse(TEXT("upright boat is not capsized"),RaftSimCapsizePolicy::PhysicallyInverted(FQuat::Identity,100.));
    TestFalse(TEXT("Euler roll 180 at physical tilt 95 is below the 100 degree gate"),
        RaftSimCapsizePolicy::PhysicallyInverted(FRotator(85,30,180).Quaternion(),100.));
    TestTrue(TEXT("physically inverted roll enters the gate"),
        RaftSimCapsizePolicy::PhysicallyInverted(FRotator(0,0,110).Quaternion(),100.));
    TestTrue(TEXT("physical pitch-over also enters the gate"),
        RaftSimCapsizePolicy::PhysicallyInverted(FRotator(110,30,0).Quaternion(),100.));
    FRaftSimSwimmerRescueFrame Released;
    Released.SwimmerWorldPositionMeters=FVector(2,3,299.3);
    Released.SwimmerDriftVelocityMetersPerSecond=FVector(1,0,-1.5);
    const auto Early=RaftSimAdvanceSubmergedSwimmer(Released,FVector::ZeroVector,300.,.1);
    TestTrue(TEXT("submerged release retains downward momentum, not surface snap"),
        Early.SwimmerWorldPositionMeters.Z<Released.SwimmerWorldPositionMeters.Z &&
        Early.SwimmerDriftVelocityMetersPerSecond.Z<0.);
    auto Swimming=Released;
    for(int32 I=0;I<1440;++I)Swimming=RaftSimAdvanceSubmergedSwimmer(Swimming,FVector::ZeroVector,300.,1./120.);
    TestTrue(TEXT("PFD candidate rises to the local surface without sinking"),
        FMath::Abs(Swimming.SwimmerWorldPositionMeters.Z-300.)<.002 &&
        FMath::Abs(Swimming.SwimmerDriftVelocityMetersPerSecond.Z)<1.e-9);
    TestTrue(TEXT("release horizontal momentum is relaxed, not erased"),Early.SwimmerWorldPositionMeters.X>2.);
    const auto Environments=RaftSimFlipTestEnvironment::Scenes();
    using namespace RaftSimContactWitnessPrune;
    TArray<FWitness> Witnesses={
        {FVector(0,0,0),FVector(0,0,0),FVector(-1,0,0),FVector::ZeroVector,3},
        {FVector(0,1,0),FVector(0,1,.2),FVector(-1,0,0),FVector::ZeroVector,3},
        {FVector(0,0,1),FVector(0,0,1.2),FVector(-1,0,0),FVector::ZeroVector,3}};
    FWitness Interior{FVector(0,.25,.25),FVector(0,.25,.35),FVector(-1,0,0),FVector::ZeroVector,3};
    TestTrue(TEXT("convex witness endpoint representation is redundant"),Redundant(Interior,Witnesses,INDEX_NONE,1.e-13));
    Interior.After.Z+=.001;
    TestFalse(TEXT("distinct deformation velocity must not be discarded"),Redundant(Interior,Witnesses,INDEX_NONE,1.e-13));
    Interior.After.Z-=.001;Interior.Ground.X=.001;
    TestFalse(TEXT("a different contact plane must not be discarded"),Redundant(Interior,Witnesses,INDEX_NONE,1.e-13));
    RaftSimImplicitDrag::FSystem Drag;
    Drag.AddPoint(FVector(1,.8,.2),FVector::ZeroVector,9000.,-6000.,FVector::ForwardVector);
    Drag.AddPoint(FVector(-1,-.8,.2),FVector::ZeroVector,9000.,0.,FVector::ForwardVector);
    FRaftSimFlexRigidState Moving;Moving.LinearVelocity=FVector(3,-2,1);Moving.AngularVelocity=FVector(4,-3,2);
    const FVector I(59,59,132);constexpr double Mass=70.;
    const auto Energy=[&](const auto& S){return .5*(Mass*S.LinearVelocity.SizeSquared()+I.X*FMath::Square(S.AngularVelocity.X)+I.Y*FMath::Square(S.AngularVelocity.Y)+I.Z*FMath::Square(S.AngularVelocity.Z));};
    const double Before=Energy(Moving);FVector Force,Torque;
    TestTrue(TEXT("empty-hull strong drag solve remains finite"),Drag.Advance(Moving,Mass,I,FVector::ZeroVector,FVector::ZeroVector,1./120.,Force,Torque));
    TestTrue(TEXT("still-water coupled drag cannot add kinetic energy"),Energy(Moving)<Before);
    RaftSimImplicitDrag::FSystem Uniform;
    Uniform.AddPoint(FVector(1,0,0),FVector(3,0,0),9000.,0.,FVector::ForwardVector);
    FRaftSimFlexRigidState Carried;Carried.LinearVelocity=FVector(3,0,0);
    TestTrue(TEXT("uniform co-moving integration succeeds"),Uniform.Advance(Carried,Mass,I,FVector::ZeroVector,FVector::ZeroVector,1./120.,Force,Torque));
    TestTrue(TEXT("co-moving current creates neither force nor rotation"),Carried.LinearVelocity.Equals(FVector(3,0,0),1.e-9) && Carried.AngularVelocity.IsNearlyZero(1.e-9));
    const auto& Hydraulic=*Environments.FindByPredicate([](const auto& S){return S.bHydraulic;});
    for(double Y=-3.;Y<=3.;Y+=.25)
    {
        const FVector SurfacePoint(0,Y*100.,Hydraulic.Surface(FVector(0,Y*100.,0),0.)*100.);
        const FVector V=Hydraulic.Velocity(SurfacePoint,0.);
        const double Hy=(Hydraulic.Surface(SurfacePoint+FVector(0,.1,0),0.)-Hydraulic.Surface(SurfacePoint-FVector(0,.1,0),0.))/.002;
        TestTrue(TEXT("hydraulic current is tangent to its stationary free surface"),FMath::Abs(V.Z-V.Y*Hy)<1.e-7);
        TestTrue(TEXT("hydraulic bed has no vertical flux"),FMath::Abs(Hydraulic.Velocity(FVector(0,Y*100.,-200),0.).Z)<1.e-9);
    }
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFlipEnvironmentBaseline,
    "RaftSim.Demo.FlipEnvironmentBaseline",
    EAutomationTestFlags::EditorContext|EAutomationTestFlags::ClientContext|EAutomationTestFlags::ProductFilter)
bool FRaftSimFlipEnvironmentBaseline::RunTest(const FString&)
{
    TArray<TSharedPtr<FJsonValue>> Reports;
    const bool Candidate=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFlipCandidateLoads"));
    for(const auto& Scene:RaftSimFlipTestEnvironment::Scenes())
    {
        // These moving-wave force controls intentionally exclude obstacle CCD
        // and stationary hydraulic entries, which require the live actor lab.
        if(Scene.bObstacle || Scene.bHydraulic)continue;
        auto* Runtime=NewObject<URaftSimChronoRuntimeAdapter>();
        FRaftSimRaftBodyConfig Body;Body.MassKg=605.;Body.BuoyancyWeightMultiple=5.2;
        Body.InertiaTensorKgM2=FVector(514.,514.,1142.);Body.LinearDragCoefficient=9000.;
        FRaftSimFlexParameters Flex;Flex.MassKg=70.;Flex.GuideMassKg=85.;Flex.PassengerMassKg=75.;Flex.PassengerCount=6;
        Flex.LengthM=Body.LengthMeters;Flex.WidthM=Body.WidthMeters;Flex.TubeRadiusM=Body.TubeRadiusMeters;
        Runtime->ConfigureRaftBody(Body);
        Runtime->ConfigureFlexibleRaftModel(Flex,RaftSimCrewSeatLayout::BuildNormalSeats(Flex,false),18000.,true);
        double Seconds=0.;
        Runtime->SetWaterSurfaceSampler([&](const FVector& P,float& H){H=Scene.Surface(P,Seconds)*100.;return true;});
        Runtime->SetFlexibleWaterFieldSampler([&](const FVector& P,FRaftSimFlexUniformWater& W)
            {W.bWet=true;W.SurfaceHeightM=Scene.Surface(P,Seconds);W.VelocityMps=Scene.Velocity(P,Seconds);return true;});
        FRaftSimRaftKinematicState Initial;Initial.WorldTransform.SetLocation(FVector(0,0,20));
        Initial.WorldTransform.SetRotation(FQuat(FVector::ForwardVector,FMath::DegreesToRadians(Scene.InitialRollDegrees)));
        Initial.AngularVelocityRadiansPerSecond=FVector(Scene.InitialRollRateRadS,0,0);
        Runtime->SetKinematicState(Initial);
        double MinimumUp=1.,MaximumOmega=0.,RiskSeconds=0.;TArray<TSharedPtr<FJsonValue>> Motion;
        for(int32 Step=0;Step<1440;++Step)
        {
            Seconds=Step/120.;
            if(Candidate)
            {
                const auto Load=RaftSimFlipCandidateLoads::Evaluate(*Runtime,Scene,Seconds,1./120.);
                Runtime->AddExternalImpulse(Load.ForceN/120.,Load.TorqueNm/120.);
            }
            if(!TestTrue(TEXT("production integration remains valid"),Runtime->StepRaftDynamics(1.f/120.f)))break;
            const auto& State=Runtime->GetKinematicState();const auto& Telemetry=Runtime->GetLastFlexibleStepTelemetry();
            const double Up=State.WorldTransform.GetRotation().GetUpVector().Z;
            MinimumUp=FMath::Min(MinimumUp,Up);MaximumOmega=FMath::Max(MaximumOmega,State.AngularVelocityRadiansPerSecond.Size());
            if(Telemetry.bReferenceFlipRisk)RiskSeconds+=1./120.;
            if(Step%12==0)
            {
                auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("seconds"),Seconds);
                Row->SetNumberField(TEXT("up_z"),Up);Row->SetNumberField(TEXT("roll_deg"),State.WorldTransform.Rotator().Roll);
                Row->SetNumberField(TEXT("pitch_deg"),State.WorldTransform.Rotator().Pitch);
                Row->SetNumberField(TEXT("omega_rad_s"),State.AngularVelocityRadiansPerSecond.Size());
                Row->SetNumberField(TEXT("flip_margin_nm"),Telemetry.ReferenceFlipMarginNm);
                Row->SetNumberField(TEXT("dynamic_roll_nm"),Telemetry.OvertoppingDynamicRollMomentNm);
                Row->SetNumberField(TEXT("torque_x_nm"),Telemetry.AppliedTorqueNm.X);
                Motion.Add(MakeShared<FJsonValueObject>(Row));
            }
        }
        auto Report=MakeShared<FJsonObject>();Report->SetStringField(TEXT("scene"),Scene.Name);
        Report->SetStringField(TEXT("scope"),TEXT("Native production adapter forces without actor timed capsize constraint. Authored wave; representative loading; not live production mesh or calibrated hydraulic threshold."));
        Report->SetBoolField(TEXT("lab_only_candidate_pressure"),Candidate);
        Report->SetNumberField(TEXT("minimum_up_z"),MinimumUp);Report->SetNumberField(TEXT("maximum_omega_rad_s"),MaximumOmega);
        Report->SetNumberField(TEXT("risk_seconds"),RiskSeconds);Report->SetArrayField(TEXT("motion"),Motion);
        Reports.Add(MakeShared<FJsonValueObject>(Report));
        AddInfo(FString::Printf(TEXT("FLIP_BASELINE %s up_min=%.6f omega_max=%.6f risk_s=%.3f"),*Scene.Name,MinimumUp,MaximumOmega,RiskSeconds));
        if(Scene.Name==TEXT("calm"))TestTrue(TEXT("still water does not capsize"),MinimumUp>.99);
    }
    auto Root=MakeShared<FJsonObject>();Root->SetArrayField(TEXT("scenes"),Reports);
    FString Json;FJsonSerializer::Serialize(Root,TJsonWriterFactory<>::Create(&Json));
    const FString Dir=FPaths::ProjectSavedDir()/TEXT("FlipDemo");IFileManager::Get().MakeDirectory(*Dir,true);
    FString Label=TEXT("native-environments-latest");
    const bool Named=FParse::Value(FCommandLine::Get(),TEXT("RaftSimFlipEnvironmentLabel="),Label);
    if(Label.IsEmpty() || Label!=FPaths::MakeValidFileName(Label))
    {AddError(TEXT("Flip environment receipt requires a plain filename label"));return false;}
    const FString Receipt=Dir/(Label+TEXT(".json"));
    if(Named && IFileManager::Get().FileExists(*Receipt))
    {AddError(TEXT("Preserve prior flip receipt; use a fresh label"));return false;}
    TestTrue(TEXT("native flip receipt saved"),FFileHelper::SaveStringToFile(Json,*Receipt));
    return !HasAnyErrors();
}
#endif
