#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "Engine/World.h"
#include "../RaftSimRunManager.h"
#include "RaftSimVerticalSliceFrontend.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimLinkedRunBoundaryTest,
    "RaftSim.Progression.LinkedRunBoundaries",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimLinkedRunBoundaryTest::RunTest(const FString&)
{
    auto* World=UWorld::CreateWorld(EWorldType::Editor,false);
    if(!TestNotNull(TEXT("test world"),World))return false;
    ON_SCOPE_EXIT { World->DestroyWorld(false);World->RemoveFromRoot(); };
    auto* Run=World->SpawnActor<ARaftSimRunManager>();
    if(!TestNotNull(TEXT("production run manager"),Run))return false;
    struct FCase { const TCHAR* Id; const TCHAR* Map; float LastRapidEnd; };
    const FCase Cases[]={
        {TEXT("hance_challenge"),TEXT("colorado_river_grand_canyon_rowing/terrain/hance_evidence_2021/hance_evidence_runtime_coordinate_map.json"),1455.f},
        {TEXT("upper_huacas_challenge"),TEXT("pacuare_river_costa_rica/terrain/huacas_evidence_2017/huacas_evidence_runtime_coordinate_map.json"),2328.f},
        {TEXT("terminator_challenge"),TEXT("futaleufu_river_chile/terrain/terminator_evidence_2026/terminator_evidence_runtime_coordinate_map.json"),2065.f},
        {TEXT("lava_canyon_challenge"),TEXT("chilko_river_bc/terrain/lava_canyon_evidence_2023/lava_canyon_evidence_2023_runtime_coordinate_map.json"),3975.f},
        {TEXT("catalog_badger_creek"),TEXT("colorado_river_grand_canyon_rowing/catalog_runtime_2026_10_v3/badger_creek/terrain/coordinate_map.json"),1050.f}};
    for(const auto& C:Cases)
    {
        FRaftSimCareerScenarioDefinition Scenario;
        if(!TestTrue(TEXT("normal menu scenario exists"),URaftSimProgressionLibrary::FindScenario(C.Id,Scenario)))return false;
        auto* Coordinates=NewObject<URaftSimWaterRuntimeAdapter>(Run);
        if(!TestTrue(TEXT("actual source coordinates load"),Coordinates->ConfigureRiverCoordinateMap(FString(TEXT("physics/data/real_world/"))+C.Map)))return false;
        float Minimum=0,Maximum=0;
        TestTrue(TEXT("mapped station range"),Coordinates->GetRiverStationRangeM(Minimum,Maximum));
        TestTrue(TEXT("launch and finish remain in mapped data"),Scenario.StartStationM>=Minimum && Scenario.FinishStationM<=Maximum);
        TestTrue(TEXT("finish includes linked downstream rapid"),Scenario.FinishStationM>=C.LastRapidEnd);
        Run->StartStationM=Scenario.StartStationM;Run->FinishStationM=Scenario.FinishStationM;
        TestFalse(TEXT("old X and finish volume cannot end a station run early"),Run->HasCrossedFinish(true,Scenario.FinishStationM-1,1.e9f,true));
        TestFalse(TEXT("lost projection cannot end a station run"),Run->HasCrossedFinish(false,Scenario.FinishStationM,1.e9f,true));
        TestTrue(TEXT("actual station endpoint finishes"),Run->HasCrossedFinish(true,Scenario.FinishStationM,-1.e9f,false));
    }
    Run->StartStationM=Run->FinishStationM=-1.f;
    TestTrue(TEXT("training retains its legacy finish volume"),Run->HasCrossedFinish(false,0,-1.e9f,true));
    TestTrue(TEXT("training retains its legacy X finish"),Run->HasCrossedFinish(false,0,Run->FinishLineX,false));
    return !HasAnyErrors();
}
#endif
