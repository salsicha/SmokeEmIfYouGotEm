#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UObject/Package.h"
#include "../RaftSimScenarioWorld.h"
#include "../RaftSimRunManager.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimScenarioWorldTest,
    "RaftSim.Continuous.SessionMatchesWorld",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimScenarioWorldTest::RunTest(const FString&)
{
    const FString Folder = TEXT("/Temp/RaftSimSession_") + FGuid::NewGuid().ToString();
    const FString Level = Folder + TEXT("/L_Colorado_Continuous");
    for (const FString Prefix : {FString(), FString(TEXT("UEDPIE_0_"))})
    {
        auto* Package = CreatePackage(*(Folder + TEXT("/") + Prefix + TEXT("L_Colorado_Continuous")));
        Package->SetFlags(RF_Transient);
        UWorld* World = UWorld::CreateWorld(EWorldType::Editor, false, NAME_None, Package);
        if (!TestNotNull(TEXT("session fixture world"), World)) return false;
        ON_SCOPE_EXIT { World->DestroyWorld(false); World->RemoveFromRoot(); };
        World->StreamingLevelsPrefix = Prefix;
        TestTrue(TEXT("own full package matches including PIE"), RaftSimScenarioWorld::Matches(World, FName(*Level)));
        TestFalse(TEXT("same leaf in another folder does not match"),
            RaftSimScenarioWorld::Matches(World, TEXT("/Game/Other/L_Colorado_Continuous")));
        TestFalse(TEXT("unset level is not an implicit wildcard"), RaftSimScenarioWorld::Matches(World, NAME_None));
        auto* Run = World->SpawnActor<ARaftSimRunManager>();
        if (!TestNotNull(TEXT("actual run manager"), Run)) return false;
        Run->ScenarioId = TEXT("colorado_authored");
        Run->StartStationM = 200.f;
        Run->FinishStationM = 2300.f;
        FRaftSimCareerScenarioDefinition Selected;
        Selected.ScenarioId = TEXT("unrelated_saved_selection");
        Selected.LevelName = TEXT("/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach");
        Selected.StartStationM = 12000.f;
        Selected.FinishStationM = 15000.f;
        Run->ConfigureSession(Selected, ERaftSimGameMode::TrainingEddy);
        TestEqual(TEXT("foreign save cannot replace authored identity"), Run->ScenarioId, FName(TEXT("colorado_authored")));
        TestEqual(TEXT("foreign save cannot replace start"), Run->StartStationM, 200.f);
        TestEqual(TEXT("foreign save cannot replace finish"), Run->FinishStationM, 2300.f);
        TestEqual(TEXT("foreign save cannot enable training"), Run->GetGameModeKind(), ERaftSimGameMode::FreeRun);
        Selected.LevelName = FName(*Level);
        Run->ConfigureSession(Selected, ERaftSimGameMode::TrainingEddy);
        TestEqual(TEXT("own map retains supported session selection"), Run->ScenarioId, Selected.ScenarioId);
        TestEqual(TEXT("own start applied"), Run->StartStationM, Selected.StartStationM);
        TestEqual(TEXT("own finish applied"), Run->FinishStationM, Selected.FinishStationM);
        TestEqual(TEXT("own mode applied"), Run->GetGameModeKind(), ERaftSimGameMode::TrainingEddy);
    }
    TestFalse(TEXT("no world cannot match"), RaftSimScenarioWorld::Matches(nullptr, FName(*Level)));
    return true;
}
#endif
