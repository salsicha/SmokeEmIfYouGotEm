#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Framework/Application/SlateApplication.h"
#include "ImageUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/AutomationTest.h"
#include "Misc/App.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "RaftSimGuidePawn.h"
#include "RaftSimRaftActor.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimVerticalSliceFrontend.h"
#include "Tests/AutomationCommon.h"
#include "UnrealClient.h"

#include "../RaftSimGuidePlayerController.h"
#include "../RaftSimPresentationDirector.h"
#include "../RaftSimRunAudioDirector.h"
#include "../RaftSimRunHudWidget.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM7ProductionAudioTest,
    "RaftSim.M7.ProductionAudio",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM7CameraWeatherTest,
    "RaftSim.M7.CameraWeather",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM7RuntimePresentationTest,
    "RaftSim.M7.RuntimePresentation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM7FullReachPresentationTest,
    // World Partition teardown must be the final fixture in a shared editor
    // process; UE can otherwise end the following PIE world before readiness.
    "RaftSim.M7.ZFullReachPresentation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{
UWorld* FindM7World()
{
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (Context.World() != nullptr &&
            (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
        {
            return Context.World();
        }
    }
    return nullptr;
}

template <typename T>
T* FindM7Actor(UWorld* World)
{
    if (World != nullptr)
    {
        if (TActorIterator<T> It(World); It)
        {
            return *It;
        }
    }
    return nullptr;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM7TriggerAudio, FAutomationTestBase*, Test);
bool FRaftSimM7TriggerAudio::Update()
{
    UWorld* World = FindM7World();
    ARaftSimRunAudioDirector* Audio = FindM7Actor<ARaftSimRunAudioDirector>(World);
    ARaftSimRaftActor* Raft = FindM7Actor<ARaftSimRaftActor>(World);
    Test->TestNotNull(TEXT("production audio director spawned"), Audio);
    Test->TestNotNull(TEXT("raft available to drive audio"), Raft);
    if (Audio != nullptr)
    {
        Test->TestEqual(TEXT("eight authored procedural mix layers"), Audio->GetProductionLayerCount(), 8);
        Test->TestTrue(TEXT("every production layer contains queued PCM"), Audio->HasQueuedPcmForEveryLayer());
    }
    if (Raft != nullptr)
    {
        Raft->ApplyPaddleStroke(ERaftSimPaddleSide::Port, 1.0f);
        Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
    }
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM7AssertAudioResponse, FAutomationTestBase*, Test);
bool FRaftSimM7AssertAudioResponse::Update()
{
    ARaftSimRunAudioDirector* Audio = FindM7Actor<ARaftSimRunAudioDirector>(FindM7World());
    if (Audio == nullptr)
    {
        Test->AddError(TEXT("audio director missing at response assertion"));
        return true;
    }
    const FRaftSimProductionAudioMixState Mix = Audio->GetProductionMixState();
    Test->TestEqual(TEXT("all production layers remain active"), Mix.ActiveLayerCount, 8);
    Test->TestTrue(TEXT("paddle stroke opens paddle envelope"), Mix.Paddle > 0.05f);
    Test->TestTrue(TEXT("crew command opens crew callout envelope"), Mix.CrewAndRescue > 0.05f);
    Test->TestTrue(TEXT("river bed is never a silent placeholder"), Mix.RiverBed > 0.05f);
    Test->TestTrue(TEXT("adaptive music bed is present"), Mix.Music >= 0.035f);
    Test->TestTrue(TEXT("occlusion filter stays audible and finite"),
        FMath::IsFinite(Mix.OcclusionLowPassHz) && Mix.OcclusionLowPassHz >= 4000.0f);
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM7AssertCameraWeather, FAutomationTestBase*, Test);
bool FRaftSimM7AssertCameraWeather::Update()
{
    UWorld* World = FindM7World();
    ARaftSimPresentationDirector* Presentation = FindM7Actor<ARaftSimPresentationDirector>(World);
    ARaftSimGuidePawn* Guide = nullptr;
    if (APlayerController* Controller = UGameplayStatics::GetPlayerController(World, 0))
    {
        Guide = Cast<ARaftSimGuidePawn>(Controller->GetPawn());
    }
    Test->TestNotNull(TEXT("weather/time director spawned"), Presentation);
    Test->TestNotNull(TEXT("guide camera pawn spawned"), Guide);
    if (Presentation != nullptr)
    {
        Test->TestTrue(TEXT("sun, skylight, fog, and cloud actors bound"),
            Presentation->HasBoundEnvironmentActors());
        Presentation->SetWeatherVariant(ERaftSimWeatherVariant::StormDusk, true);
        const FRaftSimPresentationEnvironmentState Storm = Presentation->GetEnvironmentState();
        Test->TestEqual(TEXT("storm variant selected"),
            static_cast<int32>(Storm.Weather), static_cast<int32>(ERaftSimWeatherVariant::StormDusk));
        Test->TestTrue(TEXT("storm supplies wet/reverberant dusk state"),
            Storm.WeatherWetness >= 0.85f && Storm.ReverbStrength >= 0.65f &&
            Storm.TimeOfDayHours >= 18.0f);
    }
    if (Guide != nullptr)
    {
        Test->TestNotNull(TEXT("optional chase camera is constructed"), Guide->GetChaseCamera());
        Guide->SetChaseCameraAllowed(true);
        Test->TestTrue(TEXT("Free Run chase camera toggles on"),
            Guide->ToggleChaseCamera() && Guide->IsChaseCameraActive());
        Test->TestTrue(TEXT("chase camera component becomes active"),
            Guide->GetChaseCamera() != nullptr && Guide->GetChaseCamera()->IsActive());
        Test->TestTrue(TEXT("chase camera preserves world-up above the rendered water"),
            Guide->GetChaseCamera() != nullptr &&
            FMath::Abs(Guide->GetChaseCamera()->GetComponentRotation().Roll) < 2.0f &&
            Guide->GetCameraRuntimeState().ChaseWaterClearanceCm >= 330.0f &&
            Guide->GetChaseCamera()->GetForwardVector().Z < -0.05f);
        Test->TestTrue(TEXT("chase camera toggles back to stern guide"),
            Guide->ToggleChaseCamera() && !Guide->IsChaseCameraActive());
        Guide->BeginScenarioCameraPresentation(1.0f);
        Guide->ApplyRaftImpactCue(FVector(-5.0f, 2.0f, -1.0f), FRotator(2.0f, 0.0f, 3.0f), 0.8f);
        const FRaftSimGuideCameraRuntimeState Camera = Guide->GetCameraRuntimeState();
        Test->TestTrue(TEXT("comfort camera keeps finite FOV and impact targets"),
            FMath::IsFinite(Camera.CurrentFieldOfView) && !Camera.TargetImpactOffsetCm.ContainsNaN());
        Test->TestTrue(TEXT("scenario camera transition enters cinematic settle"),
            Camera.bIntroCameraActive);
    }
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM7PrepareCapture, FAutomationTestBase*, Test);
bool FRaftSimM7PrepareCapture::Update()
{
    UWorld* World = FindM7World();
    if (ARaftSimPresentationDirector* Presentation = FindM7Actor<ARaftSimPresentationDirector>(World))
    {
        Presentation->SetWeatherVariant(ERaftSimWeatherVariant::OvercastAfternoon, true);
    }
    ARaftSimGuidePlayerController* Controller = Cast<ARaftSimGuidePlayerController>(
        UGameplayStatics::GetPlayerController(World, 0));
    if (Controller == nullptr || Controller->GetRunHud() == nullptr)
    {
        Test->AddError(TEXT("M7 runtime HUD missing before capture"));
        return true;
    }
    Controller->GetRunHud()->BeginScenarioPresentation(
        NSLOCTEXT("RaftSim", "M7CaptureTitle", "SOUTH FORK — GUIDE RUN"),
        NSLOCTEXT("RaftSim", "M7CaptureBrief", "Read the current, lead the crew, and recover every swimmer."));
    Test->TestTrue(TEXT("scenario transition is visible"),
        Controller->GetRunHud()->IsScenarioTransitionVisible());
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM7CapturePresentation, FAutomationTestBase*, Test);
bool FRaftSimM7CapturePresentation::Update()
{
    UWorld* World = FindM7World();
    ARaftSimGuidePlayerController* Controller = Cast<ARaftSimGuidePlayerController>(
        UGameplayStatics::GetPlayerController(World, 0));
    if (FApp::CanEverRender())
    {
        FScreenshotRequest::RequestScreenshot(TEXT("M7_Presentation.png"), true, false);
    }
    if (Controller == nullptr || Controller->GetRunHud() == nullptr ||
        !FSlateApplication::IsInitialized())
    {
        Test->AddError(TEXT("Cannot capture M7 presentation widget"));
        return true;
    }
    TArray<FColor> Pixels;
    FIntVector Size;
    if (!FSlateApplication::Get().TakeScreenshot(
            Controller->GetRunHud()->TakeWidget(), Pixels, Size) || Pixels.IsEmpty())
    {
        Test->AddError(TEXT("M7 presentation Slate screenshot returned no pixels"));
        return true;
    }
    TArray64<uint8> Png;
    FImageUtils::PNGCompressImageArray(Size.X, Size.Y, MakeArrayView(Pixels), Png);
    const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots/MacEditor"));
    IFileManager::Get().MakeDirectory(*Directory, true);
    Test->TestTrue(TEXT("M7 presentation capture saved"), FFileHelper::SaveArrayToFile(
        Png, *FPaths::Combine(Directory, TEXT("M7_PresentationWidget.png"))));
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM7OpenFullReach, FAutomationTestBase*, Test);
bool FRaftSimM7OpenFullReach::Update()
{
    UWorld* World = FindM7World();
    if (World == nullptr || World->GetGameInstance() == nullptr)
    {
        Test->AddError(TEXT("No game instance for M7 full-reach presentation"));
        return true;
    }
    URaftSimSaveSubsystem* Save = World->GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>();
    if (Save == nullptr || Save->GetSave() == nullptr)
    {
        Test->AddError(TEXT("No save profile for M7 full-reach presentation"));
        return true;
    }
    Save->GetSave()->ActiveGameMode = ERaftSimGameMode::FreeRun;
    Save->GetSave()->Selection.ScenarioId = TEXT("south_fork_full_descent");
    UGameplayStatics::OpenLevel(World, TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"));
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM7PrepareFullReachCapture, FAutomationTestBase*, Test);
bool FRaftSimM7PrepareFullReachCapture::Update()
{
    UWorld* World = FindM7World();
    ARaftSimPresentationDirector* Presentation = FindM7Actor<ARaftSimPresentationDirector>(World);
    ARaftSimRunAudioDirector* Audio = FindM7Actor<ARaftSimRunAudioDirector>(World);
    ARaftSimGuidePlayerController* Controller = Cast<ARaftSimGuidePlayerController>(
        UGameplayStatics::GetPlayerController(World, 0));
    Test->TestNotNull(TEXT("full reach has presentation director"), Presentation);
    Test->TestNotNull(TEXT("full reach has production audio"), Audio);
    Test->TestNotNull(TEXT("full reach has guide shell"), Controller);
    if (Presentation != nullptr)
    {
        Presentation->SetWeatherVariant(ERaftSimWeatherVariant::ClearMorning, true);
        Test->TestTrue(TEXT("full-reach authored atmosphere actors are bound"),
            Presentation->HasBoundEnvironmentActors());
    }
    if (Audio != nullptr)
    {
        Test->TestEqual(TEXT("full reach carries eight-layer mix"),
            Audio->GetProductionLayerCount(), 8);
    }
    if (Controller != nullptr && Controller->GetRunHud() != nullptr)
    {
        Controller->GetRunHud()->BeginScenarioPresentation(
            NSLOCTEXT("RaftSim", "FullReachCaptureTitle", "SOUTH FORK — CHILI BAR TO SALMON FALLS"),
            NSLOCTEXT("RaftSim", "FullReachCaptureBrief", "49.1 km continuous guide descent • clear morning"));
        if (ARaftSimGuidePawn* Guide = Cast<ARaftSimGuidePawn>(Controller->GetPawn()))
        {
            Test->TestTrue(TEXT("Free Run chase camera is enabled on the production reach"),
                Guide->ToggleChaseCamera() && Guide->IsChaseCameraActive());
        }
    }
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimM7CaptureFullReach, FAutomationTestBase*, Test);
bool FRaftSimM7CaptureFullReach::Update()
{
    UWorld* World = FindM7World();
    ARaftSimGuidePlayerController* Controller = Cast<ARaftSimGuidePlayerController>(
        UGameplayStatics::GetPlayerController(World, 0));
    if (Controller == nullptr || Controller->GetRunHud() == nullptr)
    {
        Test->AddError(TEXT("full-reach shell missing at M7 capture"));
        return true;
    }
    // A pending FScreenshotRequest has no render fence under NullRHI and can
    // race the next PIE fixture's startup. Rendered evidence is captured only
    // when a renderer exists; the same assertions remain headless-safe.
    if (FApp::CanEverRender())
    {
        FScreenshotRequest::RequestScreenshot(TEXT("M7_FullReachPresentation.png"), true, false);
    }
    Test->TestTrue(TEXT("full-reach transition remains visible for capture"),
        Controller->GetRunHud()->IsScenarioTransitionVisible());
    if (ARaftSimGuidePawn* Guide = Cast<ARaftSimGuidePawn>(Controller->GetPawn()))
    {
        const UCameraComponent* Chase = Guide->GetChaseCamera();
        const APlayerCameraManager* CameraManager = Controller->PlayerCameraManager;
        Test->TestTrue(TEXT("rendered view uses the upright chase camera"),
            Chase != nullptr && CameraManager != nullptr &&
            FVector::Distance(CameraManager->GetCameraLocation(), Chase->GetComponentLocation()) < 5.0f &&
            FMath::Abs(CameraManager->GetCameraRotation().Roll) < 2.0f &&
            CameraManager->GetCameraRotation().Vector().Z < -0.05f);
    }
    return true;
}
}

bool FRaftSimM7ProductionAudioTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.5f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM7TriggerAudio(this));
    // Crew command latency is intentionally 0.4 s; sample after it becomes
    // the active command so the voice/callout layer is measured honestly.
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(0.47f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM7AssertAudioResponse(this));
    return true;
}

bool FRaftSimM7CameraWeatherTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.5f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM7AssertCameraWeather(this));
    return true;
}

bool FRaftSimM7RuntimePresentationTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.5f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM7PrepareCapture(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(0.5f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM7CapturePresentation(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(0.5f));
    return true;
}

bool FRaftSimM7FullReachPresentationTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.5f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM7OpenFullReach(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(12.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM7PrepareFullReachCapture(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(0.75f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimM7CaptureFullReach(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(0.5f));
    return true;
}

#endif
