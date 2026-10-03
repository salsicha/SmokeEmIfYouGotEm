#include "RaftSimWaterRuntimeAdapter.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include <cmath>
#include <limits>

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimExactRiverEndpointsTest,
    "RaftSim.Water.ExactAuthoredRiverEndpoints",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimExactRiverEndpointsTest::RunTest(const FString&)
{
    auto* Water=NewObject<URaftSimWaterRuntimeAdapter>();
    double Minimum=123.,Maximum=456.;
    TestFalse(TEXT("unbound domain refuses"),Water->GetExactRiverStationRangeM(Minimum,Maximum));
    TestTrue(TEXT("unbound outputs are cleared"),Minimum==0. && Maximum==0.);
    for(const FString Path:{
        FString(TEXT("physics/data/real_world/zambezi_batoka_gorge/scenario_zambezi_run/runtime/river_coordinate_map.json")),
        FString(TEXT("physics/data/real_world/zambezi_batoka_gorge/scenario_upper_gorge_evidence_2025/cartesian_runtime/progress_coordinate_map.json"))})
    {
        FString Json;TSharedPtr<FJsonObject> Source;
        if(!FFileHelper::LoadFileToString(Json,*URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(Path)) ||
            !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Source) || !Source.IsValid())
        {AddError(TEXT("actual authored coordinate source unavailable"));return false;}
        const auto& Points=Source->GetArrayField(TEXT("points"));
        if(Points.Num()<2 || !Water->ConfigureRiverCoordinateMap(Path))return false;
        const double SourceStart=Points[0]->AsArray()[0]->AsNumber();
        const double SourceEnd=Points.Last()->AsArray()[0]->AsNumber();
        if(!TestTrue(TEXT("native range available"),Water->GetExactRiverStationRangeM(Minimum,Maximum)))return false;
        TestTrue(TEXT("both endpoints preserve exact authored doubles"),Minimum==SourceStart && Maximum==SourceEnd);
        FVector Position;
        TestTrue(TEXT("entire original first endpoint resolves"),Water->RiverToWorldPosition({Minimum,0.},Water->GetRiverVerticalDatumM(),Position) && !Position.ContainsNaN());
        TestTrue(TEXT("entire original last endpoint resolves"),Water->RiverToWorldPosition({Maximum,0.},Water->GetRiverVerticalDatumM(),Position) && !Position.ContainsNaN());
        TestFalse(TEXT("one representable step before domain still refuses"),Water->RiverToWorldPosition(
            {std::nextafter(Minimum,-std::numeric_limits<double>::infinity()),0.},Water->GetRiverVerticalDatumM(),Position));
        TestFalse(TEXT("one representable step after domain still refuses"),Water->RiverToWorldPosition(
            {std::nextafter(Maximum,std::numeric_limits<double>::infinity()),0.},Water->GetRiverVerticalDatumM(),Position));
        float LegacyMinimum=0.f,LegacyMaximum=0.f;
        TestTrue(TEXT("legacy Blueprint range stays available"),Water->GetRiverStationRangeM(LegacyMinimum,LegacyMaximum));
        TestTrue(TEXT("legacy API remains unchanged"),LegacyMinimum==float(SourceStart) && LegacyMaximum==float(SourceEnd));
        TestTrue(TEXT("fixture reproduces outward rounding from failed native routes"),double(LegacyMaximum)>Maximum);
    }
    return !HasAnyErrors();
}
#endif
