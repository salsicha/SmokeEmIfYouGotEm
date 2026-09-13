// Normal-map, real-tick segment diagnostic. Only normal crew/guide inputs;
// no teleports, injected motion, manual stepping, water overrides or save writes.
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/DateTime.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformTime.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/UnrealType.h"
#include "UnrealClient.h"
#include "RaftSimRaftActor.h"
#include "RaftSimWaterSurfaceActor.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "../RaftSimRunManager.h"

#if WITH_AUTOMATION_TESTS
namespace
{
class FNormalRiverGuidedSegment final : public IAutomationLatentCommand
{
public:
    explicit FNormalRiverGuidedSegment(FAutomationTestBase* InTest) : Test(InTest) {}
    bool Update() override;
private:
    FAutomationTestBase* Test;
    double WallStart=FPlatformTime::Seconds(), Start=-1., LastSample=-1., LastStroke=-1.;
    double StartStation=0., EndStation=0., MaximumRouteError=0., MinimumClearance=DBL_MAX;
    double MaximumPenetration=0.;
    int32 MissingGround=0, GroundedSamples=0, SamplesWithWetCenter=0, Strokes=0, Shot=0;
    bool bFinite=true, bSingleCarrier=true, bProgressMatches=true;
    ERaftSimCrewCommand CrewCommand=ERaftSimCrewCommand::AllForward;
    FString Label;
    FString PlannedLinePath;
    TArray<FVector2D> PlannedLine;
    double MaximumPlannedLineError=0., PlannedEndStation=0.;
    double DesiredYaw=0., HeadingError=0., LastGuideStroke=0.;
    bool bTurnBrake=false;
    TArray<TSharedPtr<FJsonValue>> Samples;
};

bool FNormalRiverGuidedSegment::Update()
{
    UWorld* World=nullptr;
    for (const auto& Context:GEngine->GetWorldContexts())
        if (Context.WorldType==EWorldType::PIE || Context.WorldType==EWorldType::Game)
        { World=Context.World(); break; }
    if (!World || !World->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach")))
    { Test->AddError(TEXT("Guided segment requires the normal full South Fork map")); return true; }
    auto* Bridge=World->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    auto* Water=Bridge ? Bridge->GetWaterRuntime() : nullptr;
    auto* Physics=Bridge ? Bridge->GetRaftRuntime() : nullptr;
    ARaftSimRaftActor* Raft=nullptr;
    ARaftSimRunManager* Run=nullptr;
    for (TActorIterator<ARaftSimRaftActor> It(World); It; ++It) { Raft=*It; break; }
    for (TActorIterator<ARaftSimRunManager> It(World); It; ++It) { Run=*It; break; }
    if (!Water || !Physics || !Raft || !Run || !Water->HasCartesianWaterCoordinates())
    { Test->AddError(TEXT("Missing normal river gameplay/Cartesian water runtime")); return true; }
    const auto* Progress=Run->GetProgressCoordinates(Water);
    if (!Progress || Progress==Water || Run->ScenarioId!=TEXT("south_fork_full_descent"))
    { Test->AddError(TEXT("Requires full descent and separate route/hydraulic coordinates")); return true; }
    const double Now=World->GetTimeSeconds();
    const auto& State=Physics->GetKinematicState();
    const FVector Position=State.WorldTransform.GetLocation();
    FVector2D Route;
    FVector Tangent, Left;
    if (!Run->WorldToRunCoordinates(Position,Water,Route,Tangent,Left))
    { Test->AddError(TEXT("Cannot locate raft on full-river progress axis")); return true; }
    if (Start<0.)
    {
        bTurnBrake=FParse::Param(FCommandLine::Get(),TEXT("RaftSimGuidedTurnBrake"));
        if (FParse::Value(FCommandLine::Get(),TEXT("RaftSimGuidedLine="),PlannedLinePath))
        {
            FString Json;
            TSharedPtr<FJsonObject> Line;
            if (!FFileHelper::LoadFileToString(Json,*PlannedLinePath) ||
                !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Line) || !Line.IsValid() ||
                Line->GetStringField(TEXT("schema"))!=TEXT("raftsim.normal_river_planned_line.v1") ||
                Line->GetStringField(TEXT("scenario_id"))!=Run->ScenarioId.ToString() ||
                !Line->GetBoolField(TEXT("planned")) || !Line->GetBoolField(TEXT("flow_heading_screen_passed")) ||
                Line->GetNumberField(TEXT("endpoint_maximum_offset_m"))>5.)
            { Test->AddError(TEXT("Explicit guided line must pass geometry/flow screening and rejoin the river")); return true; }
            for (const auto& Value:Line->GetArrayField(TEXT("world_east_north_m")))
            {
                const auto& XY=Value->AsArray();
                if (XY.Num()!=2 || !FMath::IsFinite(XY[0]->AsNumber()) || !FMath::IsFinite(XY[1]->AsNumber()))
                { Test->AddError(TEXT("Invalid guided line point")); return true; }
                PlannedLine.Emplace(XY[0]->AsNumber()*100.,-XY[1]->AsNumber()*100.);
            }
            PlannedEndStation=Line->GetNumberField(TEXT("target_chainage_m"));
            if (PlannedLine.Num()<2 || !FMath::IsFinite(PlannedEndStation))
            { Test->AddError(TEXT("Guided line has no finite endpoint")); return true; }
        }
        Start=Now; StartStation=Route.X;
        Label=TEXT("SouthForkNormalGuidedSegment_")+FDateTime::UtcNow().ToString(TEXT("%Y%m%d_%H%M%S"));
        Raft->IssueCrewCommand(CrewCommand);
    }
    if (Now-LastSample<.1 && FPlatformTime::Seconds()-WallStart<600.) return false;
    LastSample=Now;
    const double Elapsed=Now-Start;
    EndStation=Route.X;
    bFinite &= State.WorldTransform.IsValid() && !State.LinearVelocityMetersPerSecond.ContainsNaN() &&
        !State.AngularVelocityRadiansPerSecond.ContainsNaN() && !Route.ContainsNaN();
    MaximumRouteError=FMath::Max(MaximumRouteError,FMath::Abs(Route.Y));
    // Actor and physics ticks can expose different poses to latent commands.
    // Test the scoring projection at its recorded input, retaining the old
    // latest-physics comparison as a separate, explicitly asynchronous measure.
    const auto& ProgressSample=Run->GetLastProgressSample();
    FVector2D SampledRoute=FVector2D::ZeroVector;
    FVector SampledTangent, SampledLeft;
    const bool bSampleProjected=ProgressSample.bValid && Run->WorldToRunCoordinates(
        ProgressSample.WorldPositionCm,Water,SampledRoute,SampledTangent,SampledLeft);
    const double SampleAge=Now-ProgressSample.WorldTimeSeconds;
    const double AlignedError=bSampleProjected ? FMath::Abs(ProgressSample.StationM-SampledRoute.X) : -1.;
    bProgressMatches &= bSampleProjected && SampleAge>=0. && SampleAge<=1. && AlignedError<1. &&
        Run->GetCurrentStationM()==ProgressSample.StationM;
    FRaftSimWaterSample Sample;
    const bool bWet=Water->SampleWaterAtWorldPosition(Position,Sample) && Sample.bWet;
    SamplesWithWetCenter+=bWet ? 1 : 0;
    const int32 Grounded=Physics->GetLastGroundedSupportPointCount();
    GroundedSamples+=Grounded>0 ? 1 : 0;
    MaximumPenetration=FMath::Max(MaximumPenetration,double(Physics->GetLastMaximumGroundPenetrationMeters()));
    int32 Carriers=0;
    for (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It; ++It)
    {
        ++Carriers;
        bSingleCarrier &= It->IsLiveVolumeCoreVisible() && !It->IsTranslucentBaseSheetVisible() &&
            !It->IsRapidFoamMeshVisible() && !It->IsBreakingLipVisible();
    }
    bSingleCarrier &= Carriers==1;
    FVector PlannedAim=FVector::ZeroVector;
    double PlannedDistance=0.;
    if (!PlannedLine.IsEmpty())
    {
        const FVector2D XY(Position.X,Position.Y);
        double Best=DBL_MAX;
        int32 Nearest=0;
        FVector2D OnLine=PlannedLine[0];
        for (int32 I=0; I+1<PlannedLine.Num(); ++I)
        {
            const FVector2D D=PlannedLine[I+1]-PlannedLine[I];
            const double T=D.SizeSquared()>0. ? FMath::Clamp(FVector2D::DotProduct(XY-PlannedLine[I],D)/D.SizeSquared(),0.,1.) : 0.;
            const FVector2D P=PlannedLine[I]+T*D;
            const double Distance=(XY-P).SizeSquared();
            if (Distance<Best) { Best=Distance; Nearest=I; OnLine=P; }
        }
        PlannedDistance=FMath::Sqrt(Best)/100.;
        MaximumPlannedLineError=FMath::Max(MaximumPlannedLineError,PlannedDistance);
        double Ahead=1200.;
        for (int32 I=Nearest+1; I<PlannedLine.Num(); ++I)
        {
            const FVector2D D=PlannedLine[I]-OnLine;
            const double Length=D.Size();
            if (Length>=Ahead && Length>0.) { OnLine+=D*(Ahead/Length); break; }
            Ahead-=Length; OnLine=PlannedLine[I];
        }
        PlannedAim=FVector(OnLine.X,OnLine.Y,Position.Z);
    }
    // A provisional centerline-following baseline, NOT a surveyed safe line.
    // Bound the current-relative effort to the existing 2.2 m/s driver model.
    if (bFinite && Now-LastStroke>=.85)
    {
        FVector Aim;
        if (!PlannedLine.IsEmpty()) Aim=PlannedAim;
        else if (!Progress->RiverToWorldPosition(FVector2D(Route.X+12.,0.),Progress->GetRiverVerticalDatumM(),Aim))
        { Test->AddError(TEXT("Missing lookahead on full-river route")); return true; }
        const FVector2D Track=FVector2D(Aim.X-Position.X,Aim.Y-Position.Y).GetSafeNormal();
        const FVector2D Flow=bWet ? FVector2D(Sample.VelocityMetersPerSecond.X,Sample.VelocityMetersPerSecond.Y) : FVector2D::ZeroVector;
        const FVector2D Across=Flow-Track*FVector2D::DotProduct(Flow,Track);
        const double Remaining=2.2*2.2-Across.SizeSquared();
        const FVector2D Effort=Remaining>0. ? Track*FMath::Sqrt(Remaining)-Across : -Across.GetSafeNormal()*2.2;
        const double Yaw=FMath::RadiansToDegrees(FMath::Atan2(Effort.Y,Effort.X));
        const double Error=FMath::FindDeltaAngleDegrees(State.WorldTransform.Rotator().Yaw,Yaw);
        DesiredYaw=Yaw; HeadingError=Error;
        const double Rate=FMath::RadiansToDegrees(State.AngularVelocityRadiansPerSecond.Z);
        auto Desired=FMath::Abs(Error)>25. ? (Error>0. ? ERaftSimCrewCommand::TurnRight : ERaftSimCrewCommand::TurnLeft)
            : FMath::Abs(Error)<12. ? ERaftSimCrewCommand::AllForward : CrewCommand;
        // Existing player brake/brace command only; never alter raft forces or
        // paddle capability. Leave the original pivot-only driver selectable.
        // Slow ground motion while the stern guide aligns for a large turn,
        // then let the crew pivot once speed has fallen. Hysteresis prevents
        // cancelling every catch with a new reaction-delayed crew order.
        if (bTurnBrake && !PlannedLine.IsEmpty() && FMath::Abs(Error)>25.)
        {
            const double Speed=State.LinearVelocityMetersPerSecond.Size2D();
            if ((FMath::Abs(Error)>35. && Speed>1.5) ||
                (CrewCommand==ERaftSimCrewCommand::Stop && Speed>.6))
                Desired=ERaftSimCrewCommand::Stop;
        }
        if (Desired!=CrewCommand) { CrewCommand=Desired; Raft->IssueCrewCommand(CrewCommand); }
        const float Stroke=FMath::Clamp(float(Error/45.-Rate*.025),-1.f,1.f);
        LastGuideStroke=Stroke;
        if (FMath::Abs(Stroke)>.08f) { Raft->ApplyGuideSteerStroke(Stroke); ++Strokes; }
        LastStroke=Now;
    }
    // Trace all loaded captured ground, not one old isolated candidate mesh.
    const auto* Length=FindFProperty<FFloatProperty>(Raft->GetClass(),TEXT("FootprintLengthM"));
    const auto* Width=FindFProperty<FFloatProperty>(Raft->GetClass(),TEXT("FootprintWidthM"));
    const auto* Radius=FindFProperty<FFloatProperty>(Raft->GetClass(),TEXT("TubeRadiusM"));
    if (!Length || !Width || !Radius) { Test->AddError(TEXT("Missing actual raft footprint")); return true; }
    const double HalfLength=Length->GetPropertyValue_InContainer(Raft)*.5;
    const double HalfWidth=Width->GetPropertyValue_InContainer(Raft)*.5;
    const double TubeRadius=Radius->GetPropertyValue_InContainer(Raft);
    double Clearance=DBL_MAX;
    int32 GroundQueries=0;
    for (double X:{-FMath::Max(HalfLength-.3,.1),0.,FMath::Max(HalfLength-.3,.1)})
        for (double Side:{-1.,1.})
        {
            const double Y=Side*(X==0. ? HalfWidth : FMath::Max(HalfWidth-.15,.1));
            const FVector P=State.WorldTransform.TransformPosition(FVector(X,Y,0.)*100.);
            FCollisionQueryParams Query(SCENE_QUERY_STAT(NormalSouthForkSegment),true);
            Query.AddIgnoredActor(Raft);
            FHitResult Hit;
            if (!World->LineTraceSingleByChannel(Hit,P+FVector(0,0,10000),P-FVector(0,0,10000),ECC_WorldStatic,Query) ||
                !Hit.GetActor() || !Hit.GetActor()->ActorHasTag(TEXT("RaftSimPhysicalGround")))
            { ++MissingGround; continue; }
            ++GroundQueries;
            Clearance=FMath::Min(Clearance,P.Z-TubeRadius*100.-Hit.ImpactPoint.Z);
        }
    if (GroundQueries) MinimumClearance=FMath::Min(MinimumClearance,Clearance);
    auto Row=MakeShared<FJsonObject>();
    Row->SetNumberField(TEXT("elapsed_s"),Elapsed);
    Row->SetNumberField(TEXT("route_station_m"),Route.X);
    Row->SetNumberField(TEXT("route_lateral_m"),Route.Y);
    if (!PlannedLine.IsEmpty()) Row->SetNumberField(TEXT("planned_line_distance_m"),PlannedDistance);
    Row->SetBoolField(TEXT("progress_sample_valid"),bSampleProjected);
    Row->SetNumberField(TEXT("progress_station_m"),Run->GetCurrentStationM());
    Row->SetNumberField(TEXT("progress_latest_physics_difference_m"),Run->GetCurrentStationM()-Route.X);
    if (bSampleProjected)
    {
        Row->SetNumberField(TEXT("progress_sample_world_time_s"),ProgressSample.WorldTimeSeconds);
        Row->SetNumberField(TEXT("progress_sample_age_s"),SampleAge);
        Row->SetNumberField(TEXT("progress_sample_world_x_cm"),ProgressSample.WorldPositionCm.X);
        Row->SetNumberField(TEXT("progress_sample_world_y_cm"),ProgressSample.WorldPositionCm.Y);
        Row->SetNumberField(TEXT("progress_sample_world_z_cm"),ProgressSample.WorldPositionCm.Z);
        Row->SetNumberField(TEXT("progress_sample_expected_station_m"),SampledRoute.X);
        Row->SetNumberField(TEXT("progress_aligned_error_m"),AlignedError);
    }
    Row->SetNumberField(TEXT("world_x_cm"),Position.X); Row->SetNumberField(TEXT("world_y_cm"),Position.Y);
    Row->SetNumberField(TEXT("world_z_cm"),Position.Z);
    Row->SetNumberField(TEXT("speed_mps"),State.LinearVelocityMetersPerSecond.Size());
    Row->SetNumberField(TEXT("yaw_deg"),State.WorldTransform.Rotator().Yaw);
    Row->SetNumberField(TEXT("yaw_rate_deg_per_s"),FMath::RadiansToDegrees(State.AngularVelocityRadiansPerSecond.Z));
    Row->SetNumberField(TEXT("velocity_x_mps"),State.LinearVelocityMetersPerSecond.X);
    Row->SetNumberField(TEXT("velocity_y_mps"),State.LinearVelocityMetersPerSecond.Y);
    if (bWet)
    {
        Row->SetNumberField(TEXT("water_velocity_x_mps"),Sample.VelocityMetersPerSecond.X);
        Row->SetNumberField(TEXT("water_velocity_y_mps"),Sample.VelocityMetersPerSecond.Y);
    }
    Row->SetNumberField(TEXT("commanded_yaw_deg"),DesiredYaw);
    Row->SetNumberField(TEXT("commanded_heading_error_deg"),HeadingError);
    Row->SetNumberField(TEXT("commanded_guide_stroke"),LastGuideStroke);
    Row->SetNumberField(TEXT("commanded_crew"),int32(CrewCommand));
    Row->SetNumberField(TEXT("last_stroke_world_time_s"),LastStroke);
    Row->SetNumberField(TEXT("roll_deg"),State.WorldTransform.Rotator().Roll);
    Row->SetNumberField(TEXT("grounded_supports"),Grounded);
    Row->SetNumberField(TEXT("dry_supports"),Physics->GetLastDrySupportPointCount());
    Row->SetNumberField(TEXT("ground_queries"),GroundQueries);
    if (GroundQueries) Row->SetNumberField(TEXT("minimum_tube_clearance_cm"),Clearance);
    Row->SetBoolField(TEXT("wet_center"),bWet);
    Samples.Add(MakeShared<FJsonValueObject>(Row));
    const bool bReached=EndStation-StartStation>=120. && (PlannedLine.IsEmpty() ||
        (EndStation>=PlannedEndStation-5. && (FVector2D(Position.X,Position.Y)-PlannedLine.Last()).Size()<=500.));
    const bool bDone=bReached || Elapsed>=120. || !bFinite || FPlatformTime::Seconds()-WallStart>=600.;
    if (Elapsed>=Shot*30. || bDone)
    {
        FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir()/TEXT("Screenshots")/
            FString::Printf(TEXT("%s_%03d.png"),*Label,Shot++),false,false);
    }
    if (!bDone) return false;
    Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
    auto Report=MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("schema"),TEXT("raftsim.normal_river_guided_segment.v2"));
    Report->SetStringField(TEXT("progress_comparison"),TEXT("Same recorded actor pose; <1 m station error, <=1 s sample age. Latest physics difference retained separately."));
    Report->SetStringField(TEXT("map"),World->GetMapName());
    Report->SetStringField(TEXT("scenario_id"),Run->ScenarioId.ToString());
    Report->SetStringField(TEXT("route_source"),Run->ProgressCoordinateMapPath);
    Report->SetStringField(TEXT("scope"),TEXT("120 m/120 s centerline-guidance diagnostic in the normal map. Normal inputs only. Not a surveyed safe route, complete river traversal, motion or release acceptance."));
    if (!PlannedLine.IsEmpty())
    {
        Report->SetStringField(TEXT("scope"),TEXT("Explicit geometry/flow-screened guidance line in the normal map; no pose changes after normal checkpoint initialization. At least 120 m and endpoint rejoin within 120 s. Original scoring-axis 5 m gate retained separately from planned-line tracking. Not full-river or release acceptance."));
        Report->SetStringField(TEXT("planned_line_path"),PlannedLinePath);
        Report->SetNumberField(TEXT("maximum_planned_line_error_m"),MaximumPlannedLineError);
        Report->SetNumberField(TEXT("planned_endpoint_station_m"),PlannedEndStation);
    }
    Report->SetBoolField(TEXT("production_accepted"),false);
    Report->SetBoolField(TEXT("normal_turn_brake_inputs"),bTurnBrake);
    Report->SetBoolField(TEXT("reached_segment_end"),bReached);
    Report->SetBoolField(TEXT("finite"),bFinite);
    Report->SetBoolField(TEXT("one_cartesian_carrier_throughout"),bSingleCarrier);
    Report->SetBoolField(TEXT("progress_axis_matches"),bProgressMatches);
    Report->SetNumberField(TEXT("start_station_m"),StartStation);
    Report->SetNumberField(TEXT("end_station_m"),EndStation);
    Report->SetNumberField(TEXT("elapsed_s"),Elapsed);
    Report->SetNumberField(TEXT("maximum_route_error_m"),MaximumRouteError);
    Report->SetNumberField(TEXT("maximum_support_penetration_m"),MaximumPenetration);
    if (MinimumClearance!=DBL_MAX) Report->SetNumberField(TEXT("minimum_tube_clearance_cm"),MinimumClearance);
    Report->SetNumberField(TEXT("missing_ground_queries"),MissingGround);
    Report->SetNumberField(TEXT("grounded_samples"),GroundedSamples);
    Report->SetNumberField(TEXT("wet_center_samples"),SamplesWithWetCenter);
    Report->SetNumberField(TEXT("guide_strokes"),Strokes);
    Report->SetArrayField(TEXT("samples"),Samples);
    FString Json;
    FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const FString Directory=FPaths::ProjectSavedDir()/TEXT("Automation");
    IFileManager::Get().MakeDirectory(*Directory,true);
    const FString ReportPath=Directory/(Label+TEXT(".json"));
    Test->TestTrue(TEXT("actual full-map segment report saved"),FFileHelper::SaveStringToFile(Json,*ReportPath));
    Test->AddInfo(TEXT("Normal river segment report: ")+ReportPath);
    Test->TestTrue(TEXT("normal crew inputs reach 120 m in 120 seconds"),bReached);
    Test->TestTrue(TEXT("state remains finite"),bFinite);
    Test->TestTrue(TEXT("one normal Cartesian surface remains visible"),bSingleCarrier);
    Test->TestTrue(TEXT("scoring follows full-river chainage, not hydraulic east/north"),bProgressMatches);
    Test->TestTrue(TEXT("guide stays within existing 5 m route tolerance"),MaximumRouteError<=5.);
    if (!PlannedLine.IsEmpty()) Test->TestTrue(TEXT("guide follows explicit line within 5 m"),MaximumPlannedLineError<=5.);
    Test->TestEqual(TEXT("all tube queries find captured ground"),MissingGround,0);
    Test->TestTrue(TEXT("sampled tubes do not penetrate captured ground beyond 1 mm"),MinimumClearance!=DBL_MAX && MinimumClearance>=-.1);
    return true;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimNormalSouthForkGuidedSegmentTest,
    "RaftSim.Survey.NormalSouthForkGuidedSegment",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimNormalSouthForkGuidedSegmentTest::RunTest(const FString&)
{
    if (!FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")) ||
        !FParse::Param(FCommandLine::Get(),TEXT("RaftSimNormalRiverTraversal")))
    { AddError(TEXT("Normal segment traversal requires explicit opt-in and an ephemeral profile")); return false; }
    if (!AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"),true)) return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.f));
    FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FNormalRiverGuidedSegment>(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.f));
    return true;
}
#endif
