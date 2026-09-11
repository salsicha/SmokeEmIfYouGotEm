#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "RaftSimWaterRuntimeAdapter.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimGeographicHandednessTest,
    "RaftSim.Survey.GeographicHandedness",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FRaftSimGeographicHandednessTest::RunTest(const FString&)
{
    const FString Directory = FPaths::ProjectSavedDir()/TEXT("Automation/GeographicHandedness");
    IFileManager::Get().MakeDirectory(*Directory,true);
    auto* Adapter = NewObject<URaftSimWaterRuntimeAdapter>();
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false;
    Config.bEnableDeterministicCapture=false;
    Adapter->Configure(Config);
    FString Points;
    for (int Station=0;Station<=100;Station+=10)
        Points += FString::Printf(TEXT("%s[%d,%d,0,0,1]"),Station?TEXT(","):TEXT(""),Station,Station);
    for (const int Sign : {-1,1})
    {
        const FString File=Directory/FString::Printf(TEXT("map_%d.json"),Sign);
        // Eastward reach: true geographic left is north. In Unreal, a
        // forward +X camera sees +Y on its RIGHT, so ENU requires reflection.
        const FString Json=FString::Printf(TEXT("{\"schema\":\"raftsim.curved_river_coordinate_map.v1\",\"vertical_datum_m\":220,\"world_y_sign\":%d,\"points\":[%s]}"),Sign,*Points);
        if (!TestTrue(TEXT("write synthetic coordinate map"),FFileHelper::SaveStringToFile(Json,*File)) ||
            !TestTrue(TEXT("load explicit world orientation"),Adapter->ConfigureRiverCoordinateMap(File))) return false;
        for (const FVector2D Query : {FVector2D(25,7),FVector2D(26,8),FVector2D(75,-4)})
        {
            FVector World;
            TestTrue(TEXT("forward mapping"),Adapter->RiverToWorldPosition(Query,223,World));
            TestTrue(TEXT("only north/world Y reflected"),World.Equals(FVector(Query.X*100,Sign*Query.Y*100,300),.001));
            FVector2D Back; FVector Tangent,Left;
            TestTrue(TEXT("inverse mapping including cached query"),Adapter->WorldToRiverCoordinates(World,Back,Tangent,Left));
            TestTrue(TEXT("station/lateral preserved"),Back.Equals(Query,.0001));
            TestTrue(TEXT("downstream direction unchanged"),Tangent.Equals(FVector(1,0,0),.0001));
            TestTrue(TEXT("source river-left maps consistently"),Left.Equals(FVector(0,Sign,0),.0001));
            if (Sign<0)
                TestTrue(TEXT("geographic north is on camera left"),FVector::DotProduct(Left,FVector::RightVector)<0);
        }
    }
    const FString Legacy=Directory/TEXT("legacy.json");
    FFileHelper::SaveStringToFile(FString::Printf(TEXT("{\"schema\":\"raftsim.curved_river_coordinate_map.v1\",\"points\":[%s]}"),*Points),*Legacy);
    TestTrue(TEXT("legacy map loads"),Adapter->ConfigureRiverCoordinateMap(Legacy));
    FVector LegacyPoint;
    Adapter->RiverToWorldPosition(FVector2D(25,7),0,LegacyPoint);
    TestTrue(TEXT("omitted orientation retains legacy mapping"),LegacyPoint.Equals(FVector(2500,700,0),.001));
    const FString Invalid=Directory/TEXT("invalid.json");
    FFileHelper::SaveStringToFile(TEXT("{\"schema\":\"raftsim.curved_river_coordinate_map.v1\",\"world_y_sign\":0,\"points\":[[0,0,0,0,1],[100,100,0,0,1]]}"),*Invalid);
    AddExpectedError(TEXT("world_y_sign must be"),EAutomationExpectedErrorFlags::Contains,1);
    TestFalse(TEXT("invalid orientation rejected"),Adapter->ConfigureRiverCoordinateMap(Invalid));
    TestFalse(TEXT("invalid reconfiguration clears old map"),Adapter->HasRiverCoordinateMap());
    const FString Fields=TEXT("tmp/south-fork-survey-hydraulics/1m-mixed-inlet-registered-rock-xy-20260907/engine_review");
    const FString Source=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("..")/Fields/TEXT("coordinate_map.json"));
    FString OriginalJson; TSharedPtr<FJsonObject> OriginalMap;
    if (!TestTrue(TEXT("read registered geographic source"),FFileHelper::LoadFileToString(OriginalJson,*Source)) ||
        !TestTrue(TEXT("parse registered geographic source"),FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(OriginalJson),OriginalMap))) return false;
    OriginalMap->SetNumberField(TEXT("world_y_sign"),-1);
    FString ReflectedJson;
    FJsonSerializer::Serialize(OriginalMap.ToSharedRef(),TJsonWriterFactory<>::Create(&ReflectedJson));
    const FString Reflected=Directory/TEXT("registered_enu.json");
    if (!TestTrue(TEXT("write geographic map variant"),FFileHelper::SaveStringToFile(ReflectedJson,*Reflected))) return false;
    auto* LegacyAdapter=NewObject<URaftSimWaterRuntimeAdapter>();
    LegacyAdapter->Configure(Config);
    Adapter->Configure(Config);
    if (!TestTrue(TEXT("legacy geographic source loads"),LegacyAdapter->ConfigureRiverCoordinateMap(Source)) ||
        !TestTrue(TEXT("ENU geographic variant loads"),Adapter->ConfigureRiverCoordinateMap(Reflected))) return false;
    for (auto* Water : {LegacyAdapter,Adapter})
        if (!TestTrue(TEXT("identical captured hydraulic fields load"),Water->ConfigureRiverWindow(
            Fields,TEXT("median_runnable"),FVector2D::ZeroVector,FVector2D(273,273),.041f,false))) return false;
    for (int Step=0;Step<3;++Step)
    {
        for (const FVector2D Query : {FVector2D(-60,-9),FVector2D(0,0),FVector2D(40,0)})
        {
            FVector OldWorld,NewWorld;
            LegacyAdapter->RiverToWorldPosition(Query,228,OldWorld);
            Adapter->RiverToWorldPosition(Query,228,NewWorld);
            TestTrue(TEXT("actual registered positions reflect only world north"),
                NewWorld.Equals(FVector(OldWorld.X,-OldWorld.Y,OldWorld.Z),.001));
            FRaftSimWaterSample OldSample,NewSample;
            const bool OldValid=LegacyAdapter->SampleWaterAtWorldPosition(OldWorld,OldSample);
            const bool NewValid=Adapter->SampleWaterAtWorldPosition(NewWorld,NewSample);
            TestEqual(TEXT("world query availability preserved"),NewValid,OldValid);
            if (OldValid && NewValid)
            {
                TestEqual(TEXT("wet classification preserved"),NewSample.bWet,OldSample.bWet);
                TestTrue(TEXT("source hydraulic depth unchanged"),FMath::IsNearlyEqual(NewSample.DepthMeters,OldSample.DepthMeters,.0001f));
                TestTrue(TEXT("source elevation unchanged"),FMath::IsNearlyEqual(NewSample.SurfaceHeightMeters,OldSample.SurfaceHeightMeters,.0001f));
                const FVector V=OldSample.VelocityMetersPerSecond,N=OldSample.SurfaceNormal;
                TestTrue(TEXT("water current reflected with geometry"),NewSample.VelocityMetersPerSecond.Equals(FVector(V.X,-V.Y,V.Z),.0001));
                TestTrue(TEXT("surface normal reflected with geometry"),NewSample.SurfaceNormal.Equals(FVector(N.X,-N.Y,N.Z),.0001));
            }
        }
        for (auto* Water : {LegacyAdapter,Adapter})
            TestTrue(TEXT("source solver advances unchanged"),Water->StepWater(1.0f/60.0f));
    }
    AddInfo(TEXT("Coordinate and live-current parity only; mirrored terrain collision and full traversal require scene validation."));
    return true;
}
#endif
