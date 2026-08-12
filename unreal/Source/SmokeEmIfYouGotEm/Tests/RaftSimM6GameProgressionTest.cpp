#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "ProceduralMeshComponent.h"
#include "ImageUtils.h"
#include "Framework/Application/SlateApplication.h"
#include "InputKeyEventArgs.h"
#include "Input/Events.h"
#include "RaftSimGuidePawn.h"
#include "RaftSimRaftActor.h"
#include "../RaftSimGuidePlayerController.h"
#include "../RaftSimRouteGhostActor.h"
#include "../RaftSimRunHudWidget.h"
#include "../RaftSimRunManager.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimVerticalSliceFrontend.h"
#include "RaftSimMainMenuWidget.h"
#include "Tests/AutomationCommon.h"
#include "UnrealClient.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM6ProgressionMigrationTest,
    "RaftSim.M6.ProgressionMigration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM6CareerCatalogTest,
    "RaftSim.M6.CareerCatalog",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM6RuntimeShellTest,
    "RaftSim.M6.RuntimeShell",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM6FullReachSessionTest,
    "RaftSim.M6.FullReachSession",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM6MainMenuRenderTest,
    "RaftSim.M6.MainMenuRender",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

bool FRaftSimM6ProgressionMigrationTest::RunTest(const FString&)
{
    URaftSimVerticalSliceSaveGame* Save = NewObject<URaftSimVerticalSliceSaveGame>();
    Save->CompletedScenarioIds.Add(TEXT("legacy_rapid"));
    Save->BestSafetyScore = 0.82f;
    Save->BestOverallScore = 0.78f;
    Save->Settings.UiScale = 9.0f;
    Save->Settings.MotionIntensity = -4.0f;
    URaftSimSaveSubsystem::NormalizeSave(Save);

    TestEqual(TEXT("legacy save upgraded to current additive schema"),
        Save->SaveVersion, URaftSimSaveSubsystem::CurrentSaveVersion);
    TestEqual(TEXT("UI scale clamped"), Save->Settings.UiScale, 1.5f);
    TestEqual(TEXT("motion intensity clamped"), Save->Settings.MotionIntensity, 0.0f);
    TestTrue(TEXT("legacy completion retained"), Save->CompletedScenarioIds.Contains(TEXT("legacy_rapid")));
    TestTrue(TEXT("runtime bindings seeded"),
        Save->InputBindings.Contains(TEXT("Pause")) &&
        Save->InputBindings.Contains(TEXT("PaddleStroke")) &&
        Save->InputBindings.Contains(TEXT("RescueThrowLine")));

    FRaftSimRunResult Result;
    Result.GameMode = ERaftSimGameMode::GuidedDescent;
    Result.SafetyScore = 0.96f;
    Result.OverallScore = 0.96f;
    Result.RunTimeSeconds = 120.0f;
    Result.FurthestStationM = 5200.0f;
    Result.GhostRoute = {FVector::ZeroVector, FVector(1000.0f, 0.0f, 20.0f)};
    Result.ScenarioId = TEXT("south_fork_upper");
    const ERaftSimMedal UpperMedal = URaftSimSaveSubsystem::ApplyRunResult(Save, Result);
    TestEqual(TEXT("clean authentic result earns gold"),
        static_cast<int32>(UpperMedal), static_cast<int32>(ERaftSimMedal::Gold));
    TestTrue(TEXT("first gold unlocks Trip Leader section"),
        Save->UnlockedScenarioIds.Contains(TEXT("south_fork_coloma")));

    Result.ScenarioId = TEXT("south_fork_coloma");
    Result.FurthestStationM = 18500.0f;
    URaftSimSaveSubsystem::ApplyRunResult(Save, Result);
    TestEqual(TEXT("two gold runs promote Senior Guide"),
        static_cast<int32>(Save->LicenseTier), static_cast<int32>(ERaftSimLicenseTier::SeniorGuide));
    TestTrue(TEXT("gorge and lower sections unlock together"),
        Save->UnlockedScenarioIds.Contains(TEXT("south_fork_gorge")) &&
        Save->UnlockedScenarioIds.Contains(TEXT("south_fork_lower")));

    Result.ScenarioId = TEXT("south_fork_gorge");
    Result.FurthestStationM = 33000.0f;
    URaftSimSaveSubsystem::ApplyRunResult(Save, Result);
    Result.ScenarioId = TEXT("south_fork_lower");
    Result.FurthestStationM = 48900.0f;
    URaftSimSaveSubsystem::ApplyRunResult(Save, Result);
    TestEqual(TEXT("four gold sections promote Expedition Guide"),
        static_cast<int32>(Save->LicenseTier), static_cast<int32>(ERaftSimLicenseTier::ExpeditionGuide));
    TestTrue(TEXT("full descent and bonus runs unlock"),
        Save->UnlockedScenarioIds.Contains(TEXT("south_fork_full_descent")) &&
        Save->UnlockedScenarioIds.Contains(TEXT("terminator_challenge")));

    Result.ScenarioId = TEXT("assisted_result"), Result.bAssistUsed = true;
    TestEqual(TEXT("assist prevents gold but preserves completion medal"),
        static_cast<int32>(URaftSimSaveSubsystem::ApplyRunResult(Save, Result)),
        static_cast<int32>(ERaftSimMedal::Silver));
    FRaftSimScenarioProgress* UpperProgress = Save->ScenarioProgress.FindByPredicate(
        [](const FRaftSimScenarioProgress& Progress)
        { return Progress.ScenarioId == TEXT("south_fork_upper"); });
    TestTrue(TEXT("best route persisted with result"),
        UpperProgress != nullptr && UpperProgress->BestGhostRoute.Num() == 2);
    TestTrue(TEXT("career statistics aggregate completed play"),
        Save->CareerStats.CompletedRuns >= 5 && Save->CareerStats.TotalGuideTimeSeconds > 0.0f);
    return true;
}

bool FRaftSimM6CareerCatalogTest::RunTest(const FString&)
{
    const TArray<FRaftSimCareerScenarioDefinition> Catalog =
        URaftSimProgressionLibrary::GetScenarioCatalog();
    TestTrue(
        TEXT("training, South Fork campaign, five signature challenges, and Zambezi reference run are catalogued"),
        Catalog.Num() >= 12);
    TArray<FRaftSimCareerScenarioDefinition> Sections;
    FRaftSimCareerScenarioDefinition FullDescent;
    int32 TrainingCount = 0;
    for (const FRaftSimCareerScenarioDefinition& Scenario : Catalog)
    {
        if (Scenario.bTraining) ++TrainingCount;
        if (Scenario.SectionIndex >= 1 && Scenario.SectionIndex <= 4) Sections.Add(Scenario);
        if (Scenario.bFullDescent) FullDescent = Scenario;
    }
    Sections.Sort([](const auto& A, const auto& B) { return A.SectionIndex < B.SectionIndex; });
    TestEqual(TEXT("one measured training course"), TrainingCount, 1);
    TestEqual(TEXT("four career sections"), Sections.Num(), 4);
    for (int32 Index = 1; Index < Sections.Num(); ++Index)
    {
        TestTrue(FString::Printf(TEXT("section %d begins where prior section ends"), Index + 1),
            FMath::IsNearlyEqual(Sections[Index - 1].FinishStationM, Sections[Index].StartStationM));
        TestEqual(FString::Printf(TEXT("section %d uses continuous full-reach map"), Index + 1),
            Sections[Index].LevelName, FName(TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach")));
    }
    TestTrue(TEXT("full descent spans authored playable reach"),
        FullDescent.bFullDescent && FullDescent.StartStationM <= 120.0f &&
        FullDescent.FinishStationM >= 48900.0f);
    FRaftSimCareerScenarioDefinition Zambezi;
    TestTrue(
        TEXT("Zambezi reference run is catalogued"),
        URaftSimProgressionLibrary::FindScenario(TEXT("zambezi_reference_run"), Zambezi));
    TestEqual(
        TEXT("Zambezi reference run opens the source-scale Batoka Gorge map"),
        Zambezi.LevelName,
        FName(TEXT("/Game/RaftSim/Maps/L_Zambezi")));
    TestTrue(
        TEXT("Zambezi reference run spans the mapped Rapids 1-25 station range"),
        Zambezi.StartStationM == 0.0f && Zambezi.FinishStationM >= 27358.0f);
    TestEqual(TEXT("assist gold cap deterministic"),
        static_cast<int32>(URaftSimProgressionLibrary::CalculateMedal(0.98f, 0.98f, true)),
        static_cast<int32>(ERaftSimMedal::Silver));
    return true;
}

namespace
{
UWorld* FindM6GameWorld()
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

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertM6RuntimeShell, FAutomationTestBase*, Test);
bool FRaftSimAssertM6RuntimeShell::Update()
{
    UWorld* World = FindM6GameWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("M6 test world did not open"));
        return true;
    }
    ARaftSimGuidePlayerController* Controller = nullptr;
    if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
    {
        Controller = Cast<ARaftSimGuidePlayerController>(PC);
    }
    Test->TestNotNull(TEXT("guide controller owns runtime shell"), Controller);
    if (Controller == nullptr || Controller->GetRunHud() == nullptr)
    {
        return true;
    }
    URaftSimRunHudWidget* Hud = Controller->GetRunHud();
    Test->TestTrue(TEXT("runtime HUD is attached to viewport"), Hud->IsInViewport());
    Hud->ShowOverlay(ERaftSimHudOverlay::CommandWheel);
    Test->TestEqual(TEXT("command wheel visible"),
        static_cast<int32>(Hud->GetVisibleOverlay()),
        static_cast<int32>(ERaftSimHudOverlay::CommandWheel));
    Controller->ToggleScoutBoard();
    Test->TestTrue(TEXT("scout board pauses live water"), Controller->IsScoutBoardVisible() && UGameplayStatics::IsGamePaused(World));
    Controller->ToggleScoutBoard();
    Test->TestFalse(TEXT("closing scout resumes"), UGameplayStatics::IsGamePaused(World));
    Controller->TogglePhotoMode();
    Test->TestTrue(TEXT("photo mode pauses simulation"), Controller->IsPhotoModeActive() && UGameplayStatics::IsGamePaused(World));
    Controller->TogglePhotoMode();
    Test->TestFalse(TEXT("leaving photo mode resumes"), UGameplayStatics::IsGamePaused(World));

    ARaftSimGuidePawn* Guide = Cast<ARaftSimGuidePawn>(Controller->GetPawn());
    Test->TestTrue(TEXT("rescue actions retain keyboard/gamepad parity"),
        Guide != nullptr && Guide->HasCompleteRescueInputBindings());
    Test->TestTrue(TEXT("saved forward binding preserves S back paddle"),
        Guide != nullptr && Guide->HasPaddleStrokeKeyBinding(EKeys::S, true));
    Test->TestTrue(TEXT("mouse look is independent of held paddle actions"),
        Guide != nullptr && Guide->UsesIndependentMouseLook());

    ARaftSimRouteGhostActor* Ghost = World->SpawnActor<ARaftSimRouteGhostActor>(
        ARaftSimRouteGhostActor::StaticClass(), FTransform::Identity);
    Test->TestNotNull(TEXT("route ghost actor spawns"), Ghost);
    if (Ghost != nullptr)
    {
        Ghost->SetRoute({FVector(0.0f, 0.0f, 40.0f), FVector(1000.0f, 150.0f, 45.0f),
            FVector(2000.0f, 0.0f, 50.0f)});
        Test->TestEqual(TEXT("ghost retains sampled route"), Ghost->GetRoutePointCount(), 3);
    }
    Hud->ShowOverlay(ERaftSimHudOverlay::ScoutBoard);
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimCaptureM6Shell, FAutomationTestBase*, Test);
bool FRaftSimCaptureM6Shell::Update()
{
    FScreenshotRequest::RequestScreenshot(TEXT("M6_GameShell.png"), true, false);
    ARaftSimGuidePlayerController* Controller = Cast<ARaftSimGuidePlayerController>(
        UGameplayStatics::GetPlayerController(FindM6GameWorld(), 0));
    if (Controller == nullptr || Controller->GetRunHud() == nullptr ||
        !FSlateApplication::IsInitialized())
    {
        Test->AddError(TEXT("Cannot capture the M6 Slate game shell"));
        return true;
    }
    TArray<FColor> Pixels;
    FIntVector Size;
    if (!FSlateApplication::Get().TakeScreenshot(
            Controller->GetRunHud()->TakeWidget(), Pixels, Size) ||
        Pixels.IsEmpty() || Size.X <= 0 || Size.Y <= 0)
    {
        Test->AddError(TEXT("M6 Slate game-shell screenshot returned no pixels"));
        return true;
    }
    TArray64<uint8> Png;
    FImageUtils::PNGCompressImageArray(Size.X, Size.Y, MakeArrayView(Pixels), Png);
    const FString Directory = FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("Screenshots/MacEditor"));
    IFileManager::Get().MakeDirectory(*Directory, true);
    const FString Path = FPaths::Combine(Directory, TEXT("M6_GameShellWidget.png"));
    Test->TestTrue(TEXT("M6 Slate game-shell screenshot saved"),
        FFileHelper::SaveArrayToFile(Png, *Path));
    return true;
}

class FRaftSimVerifyM6HeldPaddleMouseLook final : public IAutomationLatentCommand
{
public:
    explicit FRaftSimVerifyM6HeldPaddleMouseLook(FAutomationTestBase* InTest)
        : Test(InTest)
    {
    }

    virtual bool Update() override
    {
        ARaftSimGuidePlayerController* Controller = Cast<ARaftSimGuidePlayerController>(
            UGameplayStatics::GetPlayerController(FindM6GameWorld(), 0));
        if (Controller == nullptr)
        {
            Test->AddError(TEXT("Cannot verify held-paddle mouse look without controller"));
            return true;
        }

        if (!bInjected)
        {
            if (!FSlateApplication::IsInitialized())
            {
                Test->AddError(TEXT("Cannot verify PIE mouse look without Slate"));
                return true;
            }
            InitialYaw = Controller->GetControlRotation().Yaw;
            FVector InitialViewLocation;
            FRotator InitialViewRotation;
            Controller->GetPlayerViewPoint(InitialViewLocation, InitialViewRotation);
            InitialViewYaw = InitialViewRotation.Yaw;
            StartSeconds = FPlatformTime::Seconds();
            Controller->InputKey(FInputKeyEventArgs::CreateSimulated(
                EKeys::W, IE_Pressed, 1.0f));
            InjectSlateMouseMove();
            bInjected = true;
            return false;
        }

        const float YawDelta = FMath::Abs(FMath::FindDeltaAngleDegrees(
            InitialYaw, Controller->GetControlRotation().Yaw));
        FVector ViewLocation;
        FRotator ViewRotation;
        Controller->GetPlayerViewPoint(ViewLocation, ViewRotation);
        const float ViewYawDelta = FMath::Abs(FMath::FindDeltaAngleDegrees(
            InitialViewYaw, ViewRotation.Yaw));
        if (YawDelta > 0.1f && ViewYawDelta > 0.1f)
        {
            Test->TestTrue(TEXT("PIE mouse pans rendered camera while W is held"), true);
            Controller->InputKey(FInputKeyEventArgs::CreateSimulated(
                EKeys::W, IE_Released, 0.0f));
            return true;
        }
        if (FPlatformTime::Seconds() - StartSeconds > 1.0)
        {
            Test->AddError(FString::Printf(
                TEXT("mouse did not pan rendered camera while W was held "
                     "(control yaw delta %.2f, view yaw delta %.2f)"),
                YawDelta, ViewYawDelta));
            Controller->InputKey(FInputKeyEventArgs::CreateSimulated(
                EKeys::W, IE_Released, 0.0f));
            return true;
        }

        // Keep supplying the same pre-widget-routing mouse event generated by
        // a real embedded PIE session while W remains pressed.
        InjectSlateMouseMove();
        return false;
    }

private:
    static void InjectSlateMouseMove()
    {
        const FVector2D PreviousPosition(
            FSlateApplication::Get().GetCursorPos());
        const FVector2D Delta(12.0f, 0.0f);
        const FPointerEvent MouseMove(
            0, PreviousPosition + Delta, PreviousPosition, Delta,
            TSet<FKey>(), FModifierKeysState());
        FSlateApplication::Get().ProcessMouseMoveEvent(MouseMove);
    }

    FAutomationTestBase* Test = nullptr;
    bool bInjected = false;
    float InitialYaw = 0.0f;
    float InitialViewYaw = 0.0f;
    double StartSeconds = 0.0;
};

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimOpenM6FullReach, FAutomationTestBase*, Test);
bool FRaftSimOpenM6FullReach::Update()
{
    UWorld* World = FindM6GameWorld();
    if (World == nullptr || World->GetGameInstance() == nullptr)
    {
        Test->AddError(TEXT("No game instance for full-reach session setup"));
        return true;
    }
    URaftSimSaveSubsystem* Save = World->GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>();
    if (Save == nullptr || Save->GetSave() == nullptr)
    {
        Test->AddError(TEXT("No M6 save profile for full-reach session setup"));
        return true;
    }
    // Memory-only selection avoids mutating a developer's persistent profile.
    Save->GetSave()->ActiveGameMode = ERaftSimGameMode::FreeRun;
    Save->GetSave()->Selection.ScenarioId = TEXT("south_fork_full_descent");
    UGameplayStatics::OpenLevel(World, TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach"));
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertM6MainMenu, FAutomationTestBase*, Test);
bool FRaftSimAssertM6MainMenu::Update()
{
    UWorld* World = FindM6GameWorld();
    TArray<UUserWidget*> Widgets;
    UWidgetBlueprintLibrary::GetAllWidgetsOfClass(
        World, Widgets, URaftSimMainMenuWidget::StaticClass(), false);
    URaftSimMainMenuWidget* Menu = Widgets.IsEmpty()
        ? nullptr : Cast<URaftSimMainMenuWidget>(Widgets[0]);
    Test->TestNotNull(TEXT("boot level creates complete main menu"), Menu);
    if (Menu == nullptr)
    {
        return true;
    }
    Test->TestTrue(TEXT("main menu is in viewport"), Menu->IsInViewport());
    Test->TestFalse(TEXT("main menu resolves a persisted/default scenario"),
        Menu->GetSelectedScenarioId().IsNone());
    TArray<FColor> Pixels;
    FIntVector Size;
    if (!FSlateApplication::Get().TakeScreenshot(Menu->TakeWidget(), Pixels, Size) ||
        Pixels.IsEmpty() || Size.X <= 0 || Size.Y <= 0)
    {
        Test->AddError(TEXT("M6 main-menu Slate capture returned no pixels"));
        return true;
    }
    TArray64<uint8> Png;
    FImageUtils::PNGCompressImageArray(Size.X, Size.Y, MakeArrayView(Pixels), Png);
    const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots/MacEditor"));
    IFileManager::Get().MakeDirectory(*Directory, true);
    Test->TestTrue(TEXT("M6 main-menu screenshot saved"), FFileHelper::SaveArrayToFile(
        Png, *FPaths::Combine(Directory, TEXT("M6_MainMenuWidget.png"))));
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertM6FullReach, FAutomationTestBase*, Test);
bool FRaftSimAssertM6FullReach::Update()
{
    UWorld* World = FindM6GameWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("Full-reach world did not open"));
        return true;
    }
    ARaftSimRunManager* Run = nullptr;
    ARaftSimGuidePlayerController* Controller = nullptr;
    ARaftSimRaftActor* Raft = nullptr;
    if (TActorIterator<ARaftSimRunManager> It(World); It) Run = *It;
    if (TActorIterator<ARaftSimRaftActor> It(World); It) Raft = *It;
    Controller = Cast<ARaftSimGuidePlayerController>(UGameplayStatics::GetPlayerController(World, 0));
    Test->TestNotNull(TEXT("full-reach raft is present"), Raft);
    Test->TestNotNull(TEXT("full-reach run manager is present"), Run);
    Test->TestNotNull(TEXT("full-reach game shell controller is present"), Controller);
    if (Run != nullptr)
    {
        Test->TestEqual(TEXT("selected full-descent scenario reached runtime"),
            Run->ScenarioId, FName(TEXT("south_fork_full_descent")));
        Test->TestEqual(TEXT("Free Run mode bypassed career locks"),
            static_cast<int32>(Run->GetGameModeKind()), static_cast<int32>(ERaftSimGameMode::FreeRun));
        Test->TestTrue(TEXT("curved river station authority is finite and near the put-in"),
            FMath::IsFinite(Run->GetCurrentStationM()) && Run->GetCurrentStationM() >= 0.0f &&
            Run->GetCurrentStationM() < 1000.0f);
        Test->TestTrue(TEXT("full-descent progress is finite"),
            FMath::IsFinite(Run->GetProgressFraction()) && Run->GetProgressFraction() >= 0.0f);
    }
    Test->TestTrue(TEXT("full-reach HUD is created without editor intervention"),
        Controller != nullptr && Controller->GetRunHud() != nullptr);
    return true;
}
}

bool FRaftSimM6RuntimeShellTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.5f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertM6RuntimeShell(this));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimVerifyM6HeldPaddleMouseLook(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(0.75f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimCaptureM6Shell(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.0f));
    return true;
}

bool FRaftSimM6FullReachSessionTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimOpenM6FullReach(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(12.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertM6FullReach(this));
    return true;
}

bool FRaftSimM6MainMenuRenderTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimBoot"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.5f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertM6MainMenu(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(0.5f));
    return true;
}

#endif
