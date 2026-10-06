#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "../RaftSimRapidTitles.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRapidTitlesTest, "RaftSim.UI.RapidTitlesMatchAssessmentPlans",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimRapidTitlesTest::RunTest(const FString&)
{
    // The titles must sit where the assessed rapids are; a re-cut reach
    // that moves a rapid has to move its title too.
    FString Json;
    TArray<TSharedPtr<FJsonValue>> Plans;
    const FString Path = FPaths::ProjectDir() / TEXT("Tests/Data/rapid_assessment_reaches.json");
    if (!TestTrue(TEXT("assessment plans readable"), FFileHelper::LoadFileToString(Json, *Path) &&
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Plans))) return false;
    int32 Matched = 0;
    for (const auto& Value : Plans)
    {
        const auto River = Value->AsObject();
        const FString Map = FPackageName::GetShortName(River->GetStringField(TEXT("map")));
        const auto Titles = RaftSimRapidTitles::ForMap(Map);
        for (const auto& TrialValue : River->GetArrayField(TEXT("trials")))
        {
            const auto Trial = TrialValue->AsObject();
            const FString Id = Trial->GetStringField(TEXT("id"));
            if (Id == TEXT("stairway_approach") || Id == TEXT("reach_end_rapid")) continue;
            const FRaftSimRapidTitle* const* Title = Titles.FindByPredicate(
                [&](const FRaftSimRapidTitle* T) { return Id == T->Id; });
            if (!TestNotNull(*FString::Printf(TEXT("title for %s/%s"), *Map, *Id), Title)) continue;
            TestTrue(*FString::Printf(TEXT("%s title at its control station"), *Id),
                FMath::IsNearlyEqual((*Title)->ControlStationM, float(Trial->GetNumberField(TEXT("control_m"))), .1f));
            ++Matched;
        }
        for (int32 I = 1; I < Titles.Num(); ++I)
            TestTrue(TEXT("titles in reach order"), Titles[I]->ControlStationM >= Titles[I - 1]->ControlStationM);
    }
    TestEqual(TEXT("every titled rapid has an assessment plan"), Matched, RaftSimRapidTitles::All().Num());
    TestEqual(TEXT("PIE map names resolve"), RaftSimRapidTitles::ForMap(TEXT("UEDPIE_0_L_Hance")).Num(), 2);
    const auto Hance = RaftSimRapidTitles::ForMap(TEXT("/Game/RaftSim/Maps/L_Hance"));
    if (TestEqual(TEXT("package paths resolve"), Hance.Num(), 2))
        TestEqual(TEXT("ranges use a typographic dash"), RaftSimRapidTitles::GradeLine(*Hance[0]).ToString(),
            FString(TEXT("CLASS IV–V")));
    return true;
}
#endif
