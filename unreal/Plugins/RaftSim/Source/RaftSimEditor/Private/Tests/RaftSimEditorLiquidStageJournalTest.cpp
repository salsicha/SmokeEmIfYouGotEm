#include "Misc/AutomationTest.h"
#include "../Materials/RaftSimLiquidStageJournal.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLiquidStageJournalTest,"RaftSim.Editor.LiquidStageJournal",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FLiquidStageJournalTest::RunTest(const FString&)
{
    FRaftSimLiquidStageJournal Journal;
    auto A=MakeShared<FJsonObject>();A->SetStringField(TEXT("simulation_generation"),TEXT("actual-generation"));
    A->SetNumberField(TEXT("native_rate_spawns"),17);
    auto B=MakeShared<FJsonObject>();B->SetStringField(TEXT("simulation_generation"),TEXT("actual-generation"));
    B->SetNumberField(TEXT("native_rate_spawns"),18);
    for(uint32 I=0;I<20000;++I)
        if(!Journal.Add(I/54,I%54,(I==100)?B:A)) { AddError(TEXT("Long journal dropped a group"));return false; }
    TestEqual(TEXT("Every observed group retained"),Journal.Records.Num(),20000);
    TestEqual(TEXT("Only exact repeats share a template"),Journal.Templates.Num(),2);
    TestEqual(TEXT("Changed native births have their own template"),Journal.Records[100].Template,1u);
    const auto J=Journal.Json();
    TestEqual(TEXT("Every serialized group retained"),J->GetArrayField(TEXT("records")).Num(),20000);
    TestEqual(TEXT("Actual ordinal retained"),Journal.Records[19999].Group,19999u%54);
    Journal.Records.SetNum(FRaftSimLiquidStageJournal::MaxRecords);
    TestFalse(TEXT("Record budget cannot truncate silently"),Journal.Add(400,1,A));
    TestTrue(TEXT("Overflow is sticky"),Journal.Failed);
    Journal.Records.Empty();TestFalse(TEXT("Failed journal cannot resume"),Journal.Add(401,1,A));
    FRaftSimLiquidStageJournal TextLimit;TextLimit.TemplateChars=FRaftSimLiquidStageJournal::MaxTemplateChars;
    TestFalse(TEXT("Template storage bound enforced"),TextLimit.Add(1,1,A));
    return !HasAnyErrors();
}
