// Opt-in real-world-tick traversal of the isolated captured survey candidate.
// No teleport, injected velocity, manual physics stepping or production writes.
#include "Misc/AutomationTest.h"
#include "Tests/AutomationCommon.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/Texture2D.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "CollisionQueryParams.h"
#include "UObject/UnrealType.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterSurfaceActor.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"
#include "UnrealClient.h"
#include "ProceduralMeshComponent.h"

#if WITH_AUTOMATION_TESTS
namespace
{
struct FSurveyGuidanceMode
{
    bool bCoordinated;
    bool bAttainable;
};
FSurveyGuidanceMode SurveyGuidanceMode(const TCHAR* CommandLine)
{
    // The driver uses available catch-timed crew/guide inputs together and a
    // feasible current-relative effort by default. Retain the old driver only
    // as an explicit diagnostic, not as the ordinary traversal's steering.
    const bool bLegacy=FParse::Param(CommandLine,TEXT("RaftSimSurveyLegacyGuidanceReview"));
    return {!bLegacy || FParse::Param(CommandLine,TEXT("RaftSimSurveyCoordinatedSteeringReview")),
        !bLegacy || FParse::Param(CommandLine,TEXT("RaftSimSurveyAttainableTrackReview"))};
}
FVector2D SurveyAttainablePaddleVelocity(const FVector2D& ToAim,
    const FVector2D& Flow, double PaddleSpeed, bool& bTrackAttainable)
{
    bTrackAttainable = false;
    const FVector2D Track = ToAim.GetSafeNormal();
    if (Track.IsNearlyZero() || PaddleSpeed <= 0.0) return FVector2D::ZeroVector;
    const double Along = FVector2D::DotProduct(Flow, Track);
    const FVector2D Across = Flow - Track * Along;
    const double RemainingSquared = PaddleSpeed * PaddleSpeed - Across.SizeSquared();
    if (RemainingSquared <= 0.0)
    {
        // The requested ground track cannot cancel this cross-current.
        // Return bounded cross-current effort, never imaginary speed or thrust.
        return -Across.GetSafeNormal() * PaddleSpeed;
    }
    const double ForwardEffort = FMath::Sqrt(RemainingSquared);
    bTrackAttainable = Along + ForwardEffort > 0.1;
    return Track * ForwardEffort - Across;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSurveyAttainableGuidanceTest,
    "RaftSim.Survey.AttainableGuidance",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
bool FRaftSimSurveyAttainableGuidanceTest::RunTest(const FString&)
{
    const auto DefaultMode=SurveyGuidanceMode(TEXT(""));
    TestTrue(TEXT("default driver coordinates guide and attainable crew effort"),
        DefaultMode.bCoordinated && DefaultMode.bAttainable);
    const auto LegacyMode=SurveyGuidanceMode(TEXT("-RaftSimSurveyLegacyGuidanceReview"));
    TestTrue(TEXT("explicit legacy driver remains reproducible"),!LegacyMode.bCoordinated && !LegacyMode.bAttainable);
    const auto CoordinatedOnly=SurveyGuidanceMode(TEXT("-RaftSimSurveyLegacyGuidanceReview -RaftSimSurveyCoordinatedSteeringReview"));
    TestTrue(TEXT("legacy comparison can isolate coordination"),CoordinatedOnly.bCoordinated && !CoordinatedOnly.bAttainable);
    const auto AttainableOnly=SurveyGuidanceMode(TEXT("-RaftSimSurveyLegacyGuidanceReview -RaftSimSurveyAttainableTrackReview"));
    TestTrue(TEXT("legacy comparison can isolate current compensation"),!AttainableOnly.bCoordinated && AttainableOnly.bAttainable);
    bool bAttainable = false;
    const FVector2D Aim(12.0, 0.0);
    const FVector2D Flow(3.0, 1.0);
    const FVector2D Effort = SurveyAttainablePaddleVelocity(Aim, Flow, 2.2, bAttainable);
    TestTrue(TEXT("bounded effort cancels cross-current"), bAttainable &&
        FMath::IsNearlyEqual(Effort.Size(), 2.2, 1.e-6) &&
        FMath::IsNearlyZero((Effort + Flow).Y, 1.e-6));
    const FVector2D Rotated = SurveyAttainablePaddleVelocity(
        FVector2D(0.0, 12.0), FVector2D(-1.0, 3.0), 2.2, bAttainable);
    TestTrue(TEXT("guidance is independent of world-axis orientation"), bAttainable &&
        Rotated.Equals(FVector2D(-Effort.Y, Effort.X), 1.e-6));
    const FVector2D StrongCross = SurveyAttainablePaddleVelocity(Aim, FVector2D(0, 3), 2.2, bAttainable);
    TestTrue(TEXT("unattainable cross-current is flagged without exceeding paddle limit"),
        !bAttainable && StrongCross.Equals(FVector2D(0, -2.2), 1.e-6));
    const FVector2D Upstream = SurveyAttainablePaddleVelocity(Aim, FVector2D(-3, 0), 2.2, bAttainable);
    TestTrue(TEXT("unattainable upstream progress is not reported feasible"),
        !bAttainable && Upstream.Equals(FVector2D(2.2, 0), 1.e-6));
    TestTrue(TEXT("zero-length target produces no heading effort"),
        SurveyAttainablePaddleVelocity(FVector2D::ZeroVector, Flow, 2.2, bAttainable).IsNearlyZero() && !bAttainable);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkNaturalDriftTest,
    "RaftSim.Survey.SouthForkNaturalDrift",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkGuidedTraversalTest,
    "RaftSim.Survey.SouthForkGuidedTraversal",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkRegisteredRockGuidedTraversalTest,
    "RaftSim.Survey.SouthForkRegisteredRockGuidedTraversal",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkGeographicGuidedTraversalTest,
    "RaftSim.Survey.SouthForkGeographicGuidedTraversal",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSouthForkPlayableGuidedTraversalTest,
    "RaftSim.Survey.SouthForkPlayableGuidedTraversal",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

class FRaftSimObserveNaturalDrift : public IAutomationLatentCommand
{
public:
    explicit FRaftSimObserveNaturalDrift(FAutomationTestBase* InTest, bool InGuided=false, bool InRegisteredRock=false, bool InGeographic=false)
        : Test(InTest), bGuided(InGuided), bRegisteredRock(InRegisteredRock), bGeographic(InGeographic) {}
    virtual bool Update() override;
private:
    FAutomationTestBase* Test;
    double Start = -1.0, LastSample = -1.0;
    FString Label;
    // Match SouthForkSurveyPlayable's current depth-limited field. Explicit
    // overrides still undergo the same geometry, field and depth-hash checks.
    FString RouteSource = TEXT("docs/reconstruction-review-2026-09-07/guided-route-depth-limited.json");
    FString FieldsDirectory, BedSampling;
    TArray<TSharedPtr<FJsonValue>> Samples;
    TArray<TSharedPtr<FJsonValue>> ScreenshotRequests;
    TArray<TSharedPtr<FJsonValue>> SurfaceMaterials;
    bool bStationCaptures = false;
    double NextCaptureStationM = -45.0;
    bool bNormalIsolationReview = false, bNormalIsolationVerified = false;
    double StartStation = 0.0, LastStation = 0.0;
    double MinimumClearanceCm = TNumericLimits<double>::Max();
    int32 MissingGround = 0, GroundedSamples = 0, WetSamples = 0, Shot = 0;
    bool bFinite = true;
    bool bGuided = false;
    bool bRegisteredRock = false;
    bool bGeographic = false;
    TArray<FVector2D> Route;
    int32 RouteIndex = 0, GuideStrokes = 0;
    double LastGuideStroke = -10.0, MaximumRouteErrorM = 0.0;
    bool bSurveyBreakingReview = false, bOneCarrierThroughout = true;
    bool bFullSurfaceReview = false, bFixedBoundsThroughout = true;
    bool bCarrierOpticsConfigured = true;
    bool bPlayableProgressCorrect = true;
    int32 FullSurfaceProbeCount = 0, MissingSurfaceProbes = 0;
    double MinimumSurfaceAlpha = 1.0;
    double MinimumPreHullAlpha = 1.0, MaximumSubmittedAlphaError = 0.0;
    int32 HullMaskedProbeCount = 0;
    TArray<TSharedPtr<FJsonValue>> SurfaceProbeFailures;
    bool bLitFoamReview = false, bLitFoamParameters = true;
    bool bCoordinatedSteeringReview = false;
    bool bAttainableTrackReview = false;
    int32 UnattainableTrackSamples = 0;
    int32 MaximumBreakingSiteCount = 0;
    ERaftSimCrewCommand LastGuidedCrewCommand = ERaftSimCrewCommand::AllForward;
};

bool FRaftSimObserveNaturalDrift::Update()
{
    UWorld* World = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
        if (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game)
        { World = Context.World(); break; }
    URaftSimPhysicsBridgeSubsystem* Bridge = World && World->GetGameInstance()
        ? World->GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>() : nullptr;
    URaftSimChronoRuntimeAdapter* Adapter = Bridge ? Bridge->GetRaftRuntime() : nullptr;
    URaftSimWaterRuntimeAdapter* Water = Bridge ? Bridge->GetWaterRuntime() : nullptr;
    ARaftSimRaftActor* Raft = nullptr;
    UStaticMeshComponent* Ground = nullptr;
    if (World)
    {
        for (TActorIterator<ARaftSimRaftActor> It(World); It; ++It) { Raft = *It; break; }
        for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
            if (It->ActorHasTag(TEXT("RaftSimPhysicalGround"))) { Ground = It->GetStaticMeshComponent(); break; }
    }
    if (!World || !Adapter || !Water || !Raft || !Ground || !Ground->GetStaticMesh())
    { Test->AddError(TEXT("Natural drift requires the live captured survey map")); return true; }
    const double Now = World->GetTimeSeconds();
    if (Start < 0)
    {
        Start = Now;
        const bool bPlayable = World->GetMapName().EndsWith(TEXT("L_SouthFork_Troublemaker"));
        bSurveyBreakingReview = bPlayable || FParse::Param(FCommandLine::Get(),TEXT("RaftSimSurveyBreakingReview"));
        bFullSurfaceReview = bPlayable || FParse::Param(FCommandLine::Get(),TEXT("RaftSimSurveyFullSurfaceReview"));
        if (bFullSurfaceReview && (!bGeographic || !bSurveyBreakingReview))
        { Test->AddError(TEXT("Full surface audit requires geographic breaking review")); return true; }
        bLitFoamReview = bSurveyBreakingReview && FParse::Param(FCommandLine::Get(),TEXT("RaftSimSurveyLitFoamReview"));
        bStationCaptures = FParse::Param(FCommandLine::Get(),TEXT("RaftSimSurveyStationCaptures"));
        bNormalIsolationReview = bSurveyBreakingReview && FParse::Param(
            FCommandLine::Get(),TEXT("RaftSimSurveyNormalIsolationReview"));
        const auto GuidanceMode=SurveyGuidanceMode(FCommandLine::Get());
        bCoordinatedSteeringReview = bGuided && GuidanceMode.bCoordinated;
        bAttainableTrackReview = bGuided && GuidanceMode.bAttainable;
        Label = FString(bGuided ? TEXT("SouthForkGuidedTraversal_") : TEXT("SouthForkNaturalDrift_")) + FDateTime::UtcNow().ToString(TEXT("%Y%m%d_%H%M%S"));
        ARaftSimRiverWaterConfig* Config=nullptr;
        for (TActorIterator<ARaftSimRiverWaterConfig> It(World);It;++It) { Config=*It;break; }
        if (!Config) { Test->AddError(TEXT("Missing survey water configuration"));return true; }
        if (bGeographic && (Water->GetRiverWorldYSign()!=-1.0 ||
            !Ground->GetComponentScale().Equals(FVector(1,-1,1),.0001)))
        { Test->AddError(TEXT("Geographic traversal requires matched reflected terrain and flow"));return true; }
        FieldsDirectory=Config->CookedFieldsDir;
        if (bGuided)
        {
            if (bRegisteredRock)
                RouteSource=TEXT("docs/reconstruction-review-2026-09-07/guided-route-registered-rock.json");
            FString RouteJson;
            TSharedPtr<FJsonObject> RouteData;
            FParse::Value(FCommandLine::Get(),TEXT("RaftSimSurveyGuidedRoute="),RouteSource);
            if (bPlayable) RouteSource=TEXT("docs/reconstruction-review-2026-09-07/guided-route-playable.json");
            const FString RouteFile=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("..")/RouteSource);
            if (!FFileHelper::LoadFileToString(RouteJson,*RouteFile) ||
                !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(RouteJson),RouteData) || !RouteData.IsValid())
            { Test->AddError(TEXT("Missing candidate guided route"));return true; }
            const FString GroundPath=Ground->GetStaticMesh()->GetPathName();
            const bool bExpectedGround=bPlayable
                ? GroundPath==TEXT("/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.SM_TroublemakerCapturedGround")
                : (bRegisteredRock
                    ? GroundPath==TEXT("/Game/RaftSim/Environment/SouthForkRockRegisteredCandidate20260907/SM_TroublemakerSurveyCandidate.SM_TroublemakerSurveyCandidate")
                    : GroundPath.Contains(TEXT("SouthForkSurveyGapCandidate20260907")));
            if (!Config || Config->CookedFieldsDir!=RouteData->GetStringField(TEXT("cooked_fields_dir")) || !bExpectedGround)
            { Test->AddError(TEXT("Guided route does not match the scene's candidate geometry/fields"));return true; }
            BedSampling=TEXT("bilinear");
            RouteData->TryGetStringField(TEXT("source_bed_sampling"),BedSampling);
            FString ManifestJson;
            TSharedPtr<FJsonObject> Manifest;
            const FString ManifestFile=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("..")/FieldsDirectory/TEXT("manifest.json"));
            if (!FFileHelper::LoadFileToString(ManifestJson,*ManifestFile) ||
                !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(ManifestJson),Manifest) || !Manifest.IsValid())
            { Test->AddError(TEXT("Missing candidate field provenance"));return true; }
            const auto& Review=Manifest->GetObjectField(TEXT("review"));
            FString ManifestSampling=TEXT("bilinear");
            Review->TryGetStringField(TEXT("source_bed_sampling"),ManifestSampling);
            const auto& Bands=Manifest->GetArrayField(TEXT("bands"));
            if (Bands.Num()!=1 || ManifestSampling!=BedSampling ||
                Review->GetStringField(TEXT("source_geometry_sha256"))!=RouteData->GetStringField(TEXT("source_geometry_sha256")) ||
                Bands[0]->AsObject()->GetObjectField(TEXT("arrays"))->GetObjectField(TEXT("h"))->GetStringField(TEXT("sha256"))!=RouteData->GetStringField(TEXT("depth_sha256")))
            { Test->AddError(TEXT("Route provenance does not match hydraulic package"));return true; }
            for (const auto& Value:RouteData->GetArrayField(TEXT("station_lateral_m")))
            {
                const auto& Pair=Value->AsArray();
                if (Pair.Num()!=2) { Test->AddError(TEXT("Malformed route point"));return true; }
                Route.Add(FVector2D(Pair[0]->AsNumber(),Pair[1]->AsNumber()));
            }
            if (Route.Num()<2) { Test->AddError(TEXT("Empty guided route"));return true; }
        }
        Raft->IssueCrewCommand(bGuided ? ERaftSimCrewCommand::AllForward : ERaftSimCrewCommand::Rest);
    }
    if (Now - LastSample < 0.1) return false;
    LastSample = Now;
    const double Elapsed = Now - Start;
    const auto& State = Adapter->GetKinematicState();
    const FVector Position = State.WorldTransform.GetLocation();
    FVector2D River;
    FVector Tangent, Left;
    const bool bMapped = Water->WorldToRiverCoordinates(Position, River, Tangent, Left);
    FRaftSimWaterSample WaterSample;
    const bool bWater = Water->SampleWaterAtWorldPosition(Position, WaterSample);
    bFinite &= State.WorldTransform.IsValid() && !State.LinearVelocityMetersPerSecond.ContainsNaN() && bMapped;
    if (bSurveyBreakingReview)
    {
        int32 CarrierCount = 0;
        for (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It; ++It)
        {
            ++CarrierCount;
            if (bFullSurfaceReview)
            {
                FVector2D Minimum, Maximum;
                const bool bBounds = It->GetSurfaceRiverBounds(Minimum, Maximum) &&
                    Minimum.Equals(FVector2D(-135,-81),.001) &&
                    Maximum.Equals(FVector2D(135,81),.001) &&
                    FMath::IsNearlyEqual(It->GetPresentationVertexSpacingMeters(),1.5f,.001f);
                bFixedBoundsThroughout &= bBounds;
                const auto* Property=FindFProperty<FObjectProperty>(It->GetClass(),TEXT("SurfaceMesh"));
                auto* Mesh=Property ? Cast<UProceduralMeshComponent>(Property->GetObjectPropertyValue_InContainer(*It)) : nullptr;
                const auto* Section=Mesh ? Mesh->GetProcMeshSection(0) : nullptr;
                // Submitted alpha alone cannot prove visible water. A renamed
                // gameplay parent once skipped the runtime optical overrides.
                UMaterialInterface* Material = Mesh ? Mesh->GetMaterial(0) : nullptr;
                float CalmCoverage = 0, ActiveCoverage = 0;
                bCarrierOpticsConfigured &= Material &&
                    Material->GetScalarParameterValue(FHashedMaterialParameterInfo(TEXT("CalmLiveSurfaceCoverage")), CalmCoverage) &&
                    Material->GetScalarParameterValue(FHashedMaterialParameterInfo(TEXT("ActiveLiveSurfaceCoverage")), ActiveCoverage) &&
                    FMath::IsNearlyEqual(CalmCoverage, 1.0f) && FMath::IsNearlyEqual(ActiveCoverage, 1.0f);
                // Check actual submitted carrier data, not the volume-only sampling helper.
                // Four stationary route locations must remain covered as the raft moves.
                for (const FVector2D Point : {FVector2D(-60,-9),FVector2D(0,3),FVector2D(60,2),FVector2D(100,20)})
                {
                    ++FullSurfaceProbeCount;
                    const auto& PreHull=It->GetPreHullSurfaceColors();
                    // Conforming refinement retains every macro vertex at its
                    // original index, then adds crest-only render vertices.
                    // Require the normal playable refinement, not just a
                    // relaxed lower bound that could accept a legacy mesh.
                    if (!bBounds || !Section || !Section->bSectionVisible ||
                        Section->ProcVertexBuffer.Num()<=181*109 ||
                        Section->ProcIndexBuffer.Num()<=180*108*6 || PreHull.Num()!=181*109)
                    { ++MissingSurfaceProbes; continue; }
                    const FVector2D Cell=(Point-Minimum)/1.5;
                    const int32 X=FMath::FloorToInt(Cell.X), Y=FMath::FloorToInt(Cell.Y);
                    const double U=Cell.X-X, V=Cell.Y-Y;
                    const int32 I0=Y*181+X, I1=I0+1, I2=I0+181, I3=I2+1;
                    auto Alpha=[&](int32 I) { return Section->ProcVertexBuffer[I].Color.A/255.0; };
                    const double A=U+V<=1 ? Alpha(I0)*(1-U-V)+Alpha(I1)*U+Alpha(I2)*V
                        : Alpha(I1)*(1-V)+Alpha(I2)*(1-U)+Alpha(I3)*(U+V-1);
                    auto Interpolate=[&](auto Value) { return U+V<=1
                        ? Value(I0)*(1-U-V)+Value(I1)*U+Value(I2)*V
                        : Value(I1)*(1-V)+Value(I2)*(1-U)+Value(I3)*(U+V-1); };
                    const double BeforeHull=Interpolate([&](int32 I) { return double(PreHull[I].A); });
                    FVector HullCenter,HullForward;
                    const bool bHull=It->GetSubmittedHullMaskPose(HullCenter,HullForward);
                    const double Expected=Interpolate([&](int32 I) {
                        const FVector P=It->GetActorTransform().TransformPosition(FVector(Section->ProcVertexBuffer[I].Position));
                        return double(PreHull[I].A)*(bHull ?
                            ARaftSimWaterSurfaceActor::ComputeRaftHullSurfaceExclusion(P,HullCenter,HullForward) : 1.0);
                    });
                    if (Expected<BeforeHull-.01) ++HullMaskedProbeCount;
                    MinimumPreHullAlpha=FMath::Min(MinimumPreHullAlpha,BeforeHull);
                    MaximumSubmittedAlphaError=FMath::Max(MaximumSubmittedAlphaError,FMath::Abs(A-Expected));
                    MinimumSurfaceAlpha=FMath::Min(MinimumSurfaceAlpha,A);
                    // A raft interior must be dry. Require continuous pre-hull water AND
                    // actual submitted alpha to match that exact last-submitted hull pose.
                    if (!FMath::IsFinite(A) || BeforeHull<.1 || FMath::Abs(A-Expected)>1.0/255.0+.0001)
                    {
                        ++MissingSurfaceProbes;
                        FRaftSimWaterSample ProbeSample;
                        const bool bSampled=Water->SampleWaterAtRiverCoordinates(Point,ProbeSample);
                        auto Failure=MakeShared<FJsonObject>();
                        Failure->SetNumberField(TEXT("elapsed_s"),Elapsed);
                        Failure->SetNumberField(TEXT("station_m"),Point.X);
                        Failure->SetNumberField(TEXT("lateral_m"),Point.Y);
                        Failure->SetNumberField(TEXT("alpha"),A);
                        Failure->SetNumberField(TEXT("pre_hull_alpha"),BeforeHull);
                        Failure->SetNumberField(TEXT("expected_submitted_alpha"),Expected);
                        Failure->SetBoolField(TEXT("source_sampled"),bSampled);
                        Failure->SetNumberField(TEXT("source_depth_m"),ProbeSample.DepthMeters);
                        SurfaceProbeFailures.Add(MakeShared<FJsonValueObject>(Failure));
                    }
                }
            }
            if (Samples.IsEmpty())
            {
                const auto* Property = FindFProperty<FObjectProperty>(It->GetClass(),TEXT("SurfaceMesh"));
                auto* Mesh = Property ? Cast<UProceduralMeshComponent>(Property->GetObjectPropertyValue_InContainer(*It)) : nullptr;
                auto* Material = Mesh ? Mesh->GetMaterial(0) : nullptr;
                auto Audit = MakeShared<FJsonObject>();
                Audit->SetStringField(TEXT("material"),Material ? Material->GetPathName() : TEXT("missing"));
                const bool bCurrentNormalV2 = FParse::Param(FCommandLine::Get(),TEXT("RaftSimSurveyCurrentNormalV2Review"));
                if (bCurrentNormalV2 || FParse::Param(FCommandLine::Get(),TEXT("RaftSimSurveyCurrentNormalReview")))
                    Test->TestTrue(TEXT("aperiodic normal review uses the requested runtime material"),
                        Material && Material->GetPathName().Contains(bCurrentNormalV2
                            ? TEXT("M_RaftSim_LiveRiverSurface_CurrentNormalReviewV2")
                            : TEXT("M_RaftSim_LiveRiverSurface_CurrentNormalReview")));
                Audit->SetNumberField(TEXT("vertex_spacing_m"),It->GetPresentationVertexSpacingMeters());
                TArray<TSharedPtr<FJsonValue>> Textures;
                if (Material)
                {
                    TArray<FMaterialParameterInfo> Parameters;
                    TArray<FGuid> Ids;
                    Material->GetAllTextureParameterInfo(Parameters,Ids);
                    for (const FMaterialParameterInfo& Parameter : Parameters)
                    {
                        UTexture* Texture = nullptr;
                        if (!Material->GetTextureParameterValue(FHashedMaterialParameterInfo(Parameter),Texture)) continue;
                        auto Entry = MakeShared<FJsonObject>();
                        Entry->SetStringField(TEXT("parameter"),Parameter.Name.ToString());
                        Entry->SetStringField(TEXT("texture"),Texture ? Texture->GetPathName() : TEXT("missing"));
                        if (const auto* Texture2D = Cast<UTexture2D>(Texture))
                        {
                            Entry->SetNumberField(TEXT("width"),Texture2D->GetSizeX());
                            Entry->SetNumberField(TEXT("height"),Texture2D->GetSizeY());
                            Entry->SetNumberField(TEXT("platform_mips"),Texture2D->GetNumMips());
                            Entry->SetNumberField(TEXT("address_x"),static_cast<int32>(Texture2D->AddressX.GetValue()));
                            Entry->SetNumberField(TEXT("address_y"),static_cast<int32>(Texture2D->AddressY.GetValue()));
                        }
                        Textures.Add(MakeShared<FJsonValueObject>(Entry));
                    }
                }
                Audit->SetArrayField(TEXT("textures"),Textures);
                SurfaceMaterials.Add(MakeShared<FJsonValueObject>(Audit));
            }
            TArray<ARaftSimWaterSurfaceActor::FBreakingSite> Sites;
            It->GetBreakingSites(Sites);
            MaximumBreakingSiteCount = FMath::Max(MaximumBreakingSiteCount,Sites.Num());
            bOneCarrierThroughout &= It->IsLiveSurfaceCarrierEnabled() &&
                It->IsTranslucentBaseSheetVisible() && !It->IsLiveVolumeCoreVisible() &&
                !It->IsBreakingLipVisible() && !It->IsBreakingRollerVolumeVisible() &&
                !It->IsRapidFoamMeshVisible() &&
                FMath::IsNearlyEqual(It->GetLivePresentationHydraulicReliefScale(),1.0f);
            if (bNormalIsolationReview && Samples.IsEmpty())
            {
                // Runtime-only A/B: remove just the sampled micro-normal.
                // Mesh normals, live solver, foam mass and optics stay intact.
                const auto* Property = FindFProperty<FObjectProperty>(It->GetClass(),TEXT("SurfaceMesh"));
                auto* Mesh = Property ? Cast<UProceduralMeshComponent>(Property->GetObjectPropertyValue_InContainer(*It)) : nullptr;
                auto* Material = Mesh ? Cast<UMaterialInstanceDynamic>(Mesh->GetMaterial(0)) : nullptr;
                float Previous = 0.0f;
                if (Material && Material->GetScalarParameterValue(
                        FHashedMaterialParameterInfo(TEXT("LiveRippleStrength")),Previous))
                {
                    Material->SetScalarParameterValue(TEXT("LiveRippleStrength"),0.0f);
                    float Actual = -1.0f;
                    bNormalIsolationVerified = Material->GetScalarParameterValue(
                        FHashedMaterialParameterInfo(TEXT("LiveRippleStrength")),Actual) && Actual == 0.0f;
                    UE_LOG(LogTemp,Display,TEXT("SurveyNormalIsolationReview LiveRippleStrength %.4f -> %.4f; mesh/flow unchanged"),Previous,Actual);
                }
            }
            if (bLitFoamReview && Samples.IsEmpty())
            {
                const auto* Property = FindFProperty<FObjectProperty>(It->GetClass(),TEXT("SurfaceMesh"));
                auto* Mesh = Property ? Cast<UProceduralMeshComponent>(Property->GetObjectPropertyValue_InContainer(*It)) : nullptr;
                auto* Material = Mesh ? Mesh->GetMaterial(0) : nullptr;
                const TPair<const TCHAR*,float> Expected[] = {
                    {TEXT("LiveSolverFoamGlow"),0.f}, {TEXT("LiveDriftFoamSurfaceGlow"),0.f},
                    {TEXT("LiveFoamRoughnessOpenCell"),.62f}, {TEXT("LiveFoamRoughnessBubble"),.80f},
                    {TEXT("LiveFoamIntensity"),1.5f}, {TEXT("WhitewaterFrothLaceModulationFloor"),.45f},
                    {TEXT("WhitewaterFrothPatchOutsideFloor"),.15f}};
                for (const auto& Parameter : Expected)
                {
                    float Value=0.f;
                    bLitFoamParameters &= Material && Material->GetScalarParameterValue(
                        FHashedMaterialParameterInfo(FName(Parameter.Key)),Value) && FMath::IsNearlyEqual(Value,Parameter.Value);
                }
            }
        }
        bOneCarrierThroughout &= CarrierCount == 1;
    }
    if (Samples.IsEmpty()) StartStation = River.X;
    LastStation = River.X;
    double RouteErrorM=0.0;
    if (bGuided && bFinite)
    {
        double Closest=TNumericLimits<double>::Max();
        for (int32 Index=FMath::Max(0,RouteIndex-3);Index<Route.Num();++Index)
        {
            const double Distance=FVector2D::DistSquared(Route[Index],River);
            if (Distance<Closest) { Closest=Distance;RouteIndex=Index; }
        }
        RouteErrorM=FMath::Sqrt(Closest);MaximumRouteErrorM=FMath::Max(MaximumRouteErrorM,RouteErrorM);
        const FVector2D Aim=Route[FMath::Min(RouteIndex+12,Route.Num()-1)];
        FVector WorldAim;
        if (Water->RiverToWorldPosition(Aim,220.0f,WorldAim) && Now-LastGuideStroke>=0.85)
        {
            // Paddle for a desired ground track, not merely a heading toward
            // the point: cross-current otherwise carries the raft outside a
            // safe corridor while its bow still appears correctly aimed.
            const FVector Flow=bWater ? WaterSample.VelocityMetersPerSecond : FVector::ZeroVector;
            const double FlowAlong=FVector::DotProduct(Flow,Tangent);
            const double Along=FMath::Max(2.2,FlowAlong+0.8);
            // A two-second pursuit horizon anticipates the slow paddle/yaw
            // response without the excessive lateral feed-forward of 0.6/s.
            const double Across=FMath::Clamp((Aim.Y-River.Y)*0.50,-2.0,2.0);
            FVector Delta=Tangent*Along+Left*Across-Flow;
            if (bAttainableTrackReview)
            {
                // Solve the same current/2.2 m/s effort triangle as the route
                // planner. The old fixed 0.8 m/s along-water demand combined
                // with up to 2 m/s lateral feedback produced abrupt ferry-angle
                // reversals. This aims along a feasible ground track instead.
                bool bAttainable = false;
                const FVector2D Effort = SurveyAttainablePaddleVelocity(
                    FVector2D(WorldAim.X-Position.X, WorldAim.Y-Position.Y),
                    FVector2D(Flow.X, Flow.Y), 2.2, bAttainable);
                Delta = FVector(Effort.X, Effort.Y, 0.0);
                UnattainableTrackSamples += bAttainable ? 0 : 1;
            }
            const double DesiredYaw=FMath::RadiansToDegrees(FMath::Atan2(Delta.Y,Delta.X));
            const double Error=FMath::FindDeltaAngleDegrees(State.WorldTransform.Rotator().Yaw,DesiredYaw);
            const double YawRate=FMath::RadiansToDegrees(State.AngularVelocityRadiansPerSecond.Z);
            const ERaftSimCrewCommand DesiredCrew=FMath::Abs(Error)>25.0
                ? (Error>0 ? ERaftSimCrewCommand::TurnRight : ERaftSimCrewCommand::TurnLeft) : FMath::Abs(Error)<12.0
                ? ERaftSimCrewCommand::AllForward : LastGuidedCrewCommand;
            if (DesiredCrew!=LastGuidedCrewCommand)
            {
                Raft->IssueCrewCommand(DesiredCrew);LastGuidedCrewCommand=DesiredCrew;
            }
            const float Stroke=FMath::Clamp(static_cast<float>(Error/45.0-YawRate*0.025),-1.0f,1.0f);
            UE_LOG(LogTemp,Display,TEXT("SurveyGuideControl t=%.2f station=%.2f lateral=%.2f aim=%.2f,%.2f yaw=%.2f desired=%.2f error=%.2f yawRate=%.2f stroke=%.2f flow=%.2f,%.2f tangent=%.2f,%.2f left=%.2f,%.2f"),
                Elapsed,River.X,River.Y,Aim.X,Aim.Y,State.WorldTransform.Rotator().Yaw,DesiredYaw,Error,YawRate,Stroke,
                Flow.X,Flow.Y,Tangent.X,Tangent.Y,Left.X,Left.Y);
            // A guide can sweep while the crew pivots. The baseline withheld
            // the stern blade precisely during large heading errors, leaving
            // the current to carry the boat sideways through slow crew turns.
            // Keep the experiment explicit and use the normal catch-timed API;
            // do not change paddle strength, impose yaw or widen route limits.
            if (FMath::Abs(Stroke)>0.08f && (bCoordinatedSteeringReview ||
                LastGuidedCrewCommand==ERaftSimCrewCommand::AllForward))
            {
                Raft->ApplyGuideSteerStroke(Stroke);
                LastGuideStroke=Now;++GuideStrokes;
            }
            else if (LastGuidedCrewCommand!=ERaftSimCrewCommand::AllForward)
            {
                LastGuideStroke=Now;
            }
        }
    }
    WetSamples += bWater && WaterSample.bWet ? 1 : 0;
    GroundedSamples += Adapter->GetLastGroundedSupportPointCount() > 0 ? 1 : 0;
    const FFloatProperty* Length = FindFProperty<FFloatProperty>(Raft->GetClass(), TEXT("FootprintLengthM"));
    const FFloatProperty* Width = FindFProperty<FFloatProperty>(Raft->GetClass(), TEXT("FootprintWidthM"));
    const FFloatProperty* Radius = FindFProperty<FFloatProperty>(Raft->GetClass(), TEXT("TubeRadiusM"));
    if (!Length || !Width || !Radius) { Test->AddError(TEXT("Missing actual raft footprint")); return true; }
    const double HalfLength = Length->GetPropertyValue_InContainer(Raft) * 0.5;
    const double HalfWidth = Width->GetPropertyValue_InContainer(Raft) * 0.5;
    const double TubeRadius = Radius->GetPropertyValue_InContainer(Raft);
    double Clearance = TNumericLimits<double>::Max();
    const FBox Bounds = Ground->Bounds.GetBox();
    for (const double X : {-FMath::Max(HalfLength - 0.3, 0.1), 0.0, FMath::Max(HalfLength - 0.3, 0.1)})
        for (const double Side : {-1.0, 1.0})
        {
            const double Y = Side * (X == 0 ? HalfWidth : FMath::Max(HalfWidth - 0.15, 0.1));
            const FVector Point = State.WorldTransform.TransformPosition(FVector(X,Y,0) * 100.0);
            FHitResult Hit;
            FCollisionQueryParams Query(SCENE_QUERY_STAT(SouthForkNaturalDrift), true);
            Query.AddIgnoredActor(Raft);
            if (!World->LineTraceSingleByChannel(Hit, FVector(Point.X,Point.Y,Bounds.Max.Z+100),
                FVector(Point.X,Point.Y,Bounds.Min.Z-100),ECC_WorldStatic,Query) || Hit.GetComponent() != Ground)
            { ++MissingGround; continue; }
            Clearance = FMath::Min(Clearance, Point.Z - TubeRadius*100.0 - Hit.ImpactPoint.Z);
        }
    MinimumClearanceCm = FMath::Min(MinimumClearanceCm, Clearance);
    auto Sample = MakeShared<FJsonObject>();
    Sample->SetNumberField(TEXT("time_s"), Elapsed);
    Sample->SetNumberField(TEXT("station_m"), River.X);
    Sample->SetNumberField(TEXT("lateral_m"), River.Y);
    Sample->SetNumberField(TEXT("z_cm"), Position.Z);
    Sample->SetNumberField(TEXT("speed_mps"), State.LinearVelocityMetersPerSecond.Size());
    Sample->SetNumberField(TEXT("water_speed_mps"), bWater ? WaterSample.VelocityMetersPerSecond.Size() : 0.0);
    Sample->SetNumberField(TEXT("horizontal_speed_mps"),State.LinearVelocityMetersPerSecond.Size2D());
    Sample->SetNumberField(TEXT("vertical_speed_mps"),State.LinearVelocityMetersPerSecond.Z);
    Sample->SetNumberField(TEXT("yaw_degrees"),State.WorldTransform.Rotator().Yaw);
    Sample->SetNumberField(TEXT("route_error_m"),RouteErrorM);
    Sample->SetNumberField(TEXT("minimum_tube_clearance_cm"), Clearance);
    Sample->SetNumberField(TEXT("grounded_supports"), Adapter->GetLastGroundedSupportPointCount());
    Sample->SetNumberField(TEXT("dry_supports"), Adapter->GetLastDrySupportPointCount());
    Sample->SetBoolField(TEXT("wet"), bWater && WaterSample.bWet);
    Samples.Add(MakeShared<FJsonValueObject>(Sample));
    const bool bReachedOutlet = bMapped && River.X >= 110.0;
    if (World->GetMapName().EndsWith(TEXT("L_SouthFork_Troublemaker")))
    {
        bool bFoundProgress = false;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (It->GetClass()->GetName() != TEXT("RaftSimRunManager")) continue;
            UFunction* Progress = It->FindFunction(TEXT("GetProgressFraction"));
            struct { float ReturnValue = -1.0f; } Result;
            if (Progress) It->ProcessEvent(Progress, &Result);
            const float Expected = FMath::Clamp(static_cast<float>((River.X + 60.0) / 170.0), 0.0f, 1.0f);
            bFoundProgress = Progress && FMath::IsNearlyEqual(Result.ReturnValue, Expected, 0.02f);
        }
        bPlayableProgressCorrect &= bFoundProgress;
    }
    const bool bDone = Elapsed >= 120.0 || bReachedOutlet || !bFinite;
    const bool bStationShot = bStationCaptures && bMapped && River.X >= NextCaptureStationM;
    if ((bStationCaptures ? (Shot == 0 || bStationShot) : Elapsed >= Shot * 30.0) || bDone)
    {
        const FString Filename = FString::Printf(TEXT("%s_%03d.png"), *Label, Shot);
        FScreenshotRequest::RequestScreenshot(FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), Filename), false, false);
        auto Capture = MakeShared<FJsonObject>();
        Capture->SetStringField(TEXT("filename"),Filename);
        Capture->SetNumberField(TEXT("request_time_s"),Elapsed);
        Capture->SetNumberField(TEXT("request_station_m"),River.X);
        Capture->SetNumberField(TEXT("request_lateral_m"),River.Y);
        // Request metadata is not proof the render-thread image was written.
        // External review must verify the file and inspect the actual frame.
        ScreenshotRequests.Add(MakeShared<FJsonValueObject>(Capture));
        if (bStationShot)
            do { NextCaptureStationM += 15.0; } while (NextCaptureStationM <= River.X);
        ++Shot;
    }
    if (!bDone) return false;
    auto Report = MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("map_name"),World->GetMapName());
    Report->SetStringField(TEXT("world_package"),World->GetOutermost()->GetName());
    Report->SetBoolField(TEXT("geographic_orientation_review"),bGeographic);
    Report->SetNumberField(TEXT("world_y_sign"),Water->GetRiverWorldYSign());
    Report->SetBoolField(TEXT("full_surface_review"),bFullSurfaceReview);
    if (bFullSurfaceReview)
    {
        Report->SetBoolField(TEXT("fixed_surface_bounds_throughout"),bFixedBoundsThroughout);
        Report->SetBoolField(TEXT("carrier_optics_configured_throughout"), bCarrierOpticsConfigured);
        Report->SetBoolField(TEXT("playable_progress_correct_throughout"), bPlayableProgressCorrect);
        Report->SetNumberField(TEXT("full_surface_probe_count"),FullSurfaceProbeCount);
        Report->SetNumberField(TEXT("missing_surface_probes"),MissingSurfaceProbes);
        Report->SetNumberField(TEXT("minimum_submitted_surface_alpha"),MinimumSurfaceAlpha);
        Report->SetNumberField(TEXT("minimum_pre_hull_surface_alpha"),MinimumPreHullAlpha);
        Report->SetNumberField(TEXT("maximum_submitted_alpha_error"),MaximumSubmittedAlphaError);
        Report->SetNumberField(TEXT("hull_masked_probe_count"),HullMaskedProbeCount);
        Report->SetArrayField(TEXT("surface_probe_failures"),SurfaceProbeFailures);
        Test->TestTrue(TEXT("whole reconstructed domain remains fixed throughout traversal"),bFixedBoundsThroughout);
        Test->TestTrue(TEXT("carrier material retains full calm and active coverage"), bCarrierOpticsConfigured);
        Test->TestTrue(TEXT("playable progress uses the negative-to-positive survey station range"), bPlayableProgressCorrect);
        Test->TestTrue(TEXT("stationary route locations have visible submitted carrier throughout"),
            FullSurfaceProbeCount>0 && MissingSurfaceProbes==0);
    }
    Report->SetStringField(TEXT("ground_mesh"),Ground->GetStaticMesh()->GetPathName());
    Report->SetBoolField(TEXT("registered_rock_map_review"),bRegisteredRock);
    Report->SetStringField(TEXT("schema"),bGuided ? TEXT("raftsim.survey.guided_traversal.v3") : TEXT("raftsim.survey.natural_drift.v1"));
    Report->SetStringField(TEXT("cooked_fields_dir"),FieldsDirectory);
    Report->SetBoolField(TEXT("guided_with_normal_paddle_commands"),bGuided);
    Report->SetBoolField(TEXT("coordinated_guide_and_crew_steering"),bCoordinatedSteeringReview);
    Report->SetBoolField(TEXT("attainable_ground_track_guidance"),bAttainableTrackReview);
    Report->SetNumberField(TEXT("unattainable_track_control_samples"),UnattainableTrackSamples);
    Report->SetBoolField(TEXT("survey_shared_breaking_experiment"),bSurveyBreakingReview);
    Report->SetBoolField(TEXT("survey_lit_foam_experiment"),bLitFoamReview);
    Report->SetBoolField(TEXT("station_based_screenshot_requests"),bStationCaptures);
    Report->SetArrayField(TEXT("screenshot_requests"),ScreenshotRequests);
    Report->SetArrayField(TEXT("runtime_surface_materials"),SurfaceMaterials);
    Report->SetBoolField(TEXT("survey_normal_isolation_experiment"),bNormalIsolationReview);
    if (bNormalIsolationReview)
    {
        Report->SetBoolField(TEXT("normal_isolation_verified"),bNormalIsolationVerified);
        Test->TestTrue(TEXT("normal isolation sets the existing micro-normal parameter to zero"),bNormalIsolationVerified);
    }
    if (bLitFoamReview) Report->SetBoolField(TEXT("lit_foam_parameters_verified"),bLitFoamParameters);
    if (bSurveyBreakingReview)
    {
        Report->SetBoolField(TEXT("one_carrier_and_shared_scale_throughout"),bOneCarrierThroughout);
        Report->SetNumberField(TEXT("maximum_breaking_site_count"),MaximumBreakingSiteCount);
    }
    Report->SetNumberField(TEXT("guide_stroke_count"),GuideStrokes);
    Report->SetNumberField(TEXT("maximum_route_error_m"),MaximumRouteErrorM);
    if (bGuided)
    {
        Report->SetStringField(TEXT("route_source"),RouteSource);
        Report->SetStringField(TEXT("route_source_bed_sampling"),BedSampling);
    }
    Report->SetNumberField(TEXT("duration_s"), Elapsed);
    Report->SetNumberField(TEXT("start_station_m"), StartStation);
    Report->SetNumberField(TEXT("end_station_m"), LastStation);
    Report->SetNumberField(TEXT("minimum_tube_clearance_cm"), MinimumClearanceCm);
    Report->SetNumberField(TEXT("missing_ground_queries"), MissingGround);
    Report->SetNumberField(TEXT("grounded_samples"), GroundedSamples);
    Report->SetNumberField(TEXT("wet_samples"), WetSamples);
    Report->SetBoolField(TEXT("finite"), bFinite);
    Report->SetBoolField(TEXT("reached_outlet"), bReachedOutlet);
    Report->SetBoolField(TEXT("production_accepted"), false);
    Report->SetArrayField(TEXT("samples"), Samples);
    FString Json;
    FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Json));
    const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Automation"));
    IFileManager::Get().MakeDirectory(*Directory, true);
    const FString Path = Directory / (Label + TEXT(".json"));
    Test->TestTrue(TEXT("natural drift report saved"), FFileHelper::SaveStringToFile(Json, *Path));
    Test->AddInfo(TEXT("Natural drift report: ") + Path);
    Test->TestTrue(TEXT("natural traversal stays finite and on registered domain"), bFinite);
    Test->TestEqual(TEXT("all tube queries remain on captured terrain"), MissingGround, 0);
    Test->TestTrue(TEXT("no sampled tube penetrates captured ground by more than 1 mm"), MinimumClearanceCm >= -0.1);
    Test->TestTrue(bGuided ? TEXT("normally paddled raft reaches survey outlet within 120 seconds") : TEXT("unpowered raft reaches survey outlet within 120 seconds"), bReachedOutlet);
    if (bGuided) Test->TestTrue(TEXT("guide remains within 5 m of diagnostic route"),MaximumRouteErrorM<=5.0);
    if (bSurveyBreakingReview)
    {
        Test->TestTrue(TEXT("survey breaking uses one visible carrier and the coupled relief scale"),bOneCarrierThroughout);
        Test->TestTrue(TEXT("survey breaking resolves actual hydraulic sites"),MaximumBreakingSiteCount>0);
    }
    if (bLitFoamReview) Test->TestTrue(TEXT("actual carrier has the reviewed lit-foam parameters"),bLitFoamParameters);
    return true;
}

bool FRaftSimSouthForkNaturalDriftTest::RunTest(const FString&)
{
    if (!AutomationOpenMap(TEXT("/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable"),true)) return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FRaftSimObserveNaturalDrift>(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.0f));
    return true;
}

bool FRaftSimSouthForkGuidedTraversalTest::RunTest(const FString&)
{
    // Reload even after another survey test: otherwise the same PIE world
    // keeps drifting during preceding tests and changes this test's start.
    if (!AutomationOpenMap(TEXT("/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable"),true)) return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FRaftSimObserveNaturalDrift>(this,true));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.0f));
    return true;
}
bool FRaftSimSouthForkRegisteredRockGuidedTraversalTest::RunTest(const FString&)
{
    if (!AutomationOpenMap(TEXT("/Game/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable"),true)) return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FRaftSimObserveNaturalDrift>(this,true,true));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.0f));
    return true;
}
bool FRaftSimSouthForkGeographicGuidedTraversalTest::RunTest(const FString&)
{
    if (!AutomationOpenMap(TEXT("/Game/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable"),true)) return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FRaftSimObserveNaturalDrift>(this,true,true,true));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.0f));
    return true;
}
bool FRaftSimSouthForkPlayableGuidedTraversalTest::RunTest(const FString&)
{
    if (!FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")))
    { AddError(TEXT("Playable traversal requires an ephemeral profile to protect user saves")); return false; }
    if (!AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_SouthFork_Troublemaker"),true)) return false;
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    FAutomationTestFramework::Get().EnqueueLatentCommand(MakeShared<FRaftSimObserveNaturalDrift>(this,true,true,true));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.0f));
    return true;
}
#endif
