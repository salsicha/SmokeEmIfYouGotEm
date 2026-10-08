#include "Environment/RaftSimContinuousRuntimeWindow.h"
#include "Misc/AutomationTest.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimContinuousRuntimeWindowTest,
    "RaftSim.M9.ContinuousRuntimeWindowCoordinates",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimContinuousRuntimeWindowTest::RunTest(const FString&)
{
    using namespace RaftSimContinuousRuntimeWindow;
    TSharedPtr<FJsonObject> Streaming;
    const FString Text=TEXT(R"({"schema":"raftsim.cartesian_water_streaming.v1","grid_spacing_m":1,"advance_m":80,"roughness_manning":0.045,"source_context_cells":3,"minimum_raft_interior_margin_m":8,"live_window_extent_m":[224,224],"windows":[{"window_id":"launch","cooked_fields_manifest":"fixture/launch/manifest.json","hydraulic_bounds_m":[1040,140,1360,460],"valid_live_center_bounds_m":[[1155,255,1245,345]]}]})");
    if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Streaming))return false;
    FBinding Out;FString Error;
    TestTrue(TEXT("Native geographic source selects launch crop"),
        Resolve(true,Streaming,FVector2D(1250,300),5000,224,TEXT("fixture/launch"),Out,Error));
    TestEqual(TEXT("Water center is clamped geographic XY, never 5000m chainage"),Out.CenterM,FVector2D(1245,300));
    TestEqual(TEXT("Native crop extent retained, not legacy 480m"),Out.ExtentM,FVector2D(224,224));
    TestEqual(TEXT("Native advance retained"),Out.AdvanceM,80.);
    TestFalse(TEXT("Unrelated initial source refused"),
        Resolve(true,Streaming,FVector2D(1250,300),5000,224,TEXT("fixture/other"),Out,Error));
    TestFalse(TEXT("Distant launch cannot borrow nearest packet"),
        Resolve(true,Streaming,FVector2D(5000,0),5000,224,TEXT("fixture/launch"),Out,Error));
    TestFalse(TEXT("Declared extent cannot shrink the reviewed crop"),
        Resolve(true,Streaming,FVector2D(1250,300),5000,80,TEXT("fixture/launch"),Out,Error));
    TestFalse(TEXT("Cartesian streaming cannot configure a curved chart"),
        Resolve(false,Streaming,FVector2D(1250,300),5000,224,TEXT("fixture/launch"),Out,Error));
    Streaming->SetStringField(TEXT("schema"),TEXT("raftsim.south_fork.moving_water_streaming.v1"));
    TestFalse(TEXT("Curved streaming cannot configure Cartesian hydraulics"),
        Resolve(true,Streaming,FVector2D(1250,300),5000,224,TEXT("fixture/launch"),Out,Error));
    TestTrue(TEXT("Existing curved station/lateral initialization unchanged"),
        Resolve(false,Streaming,FVector2D(5000,3),5000,80,TEXT("fixture/launch"),Out,Error));
    TestEqual(TEXT("Curved progress station stays the crop center"),Out.CenterM,FVector2D(5000,0));
    TestEqual(TEXT("Curved extent unchanged"),Out.ExtentM,FVector2D(480,80));
    return !HasAnyErrors();
}
#endif
