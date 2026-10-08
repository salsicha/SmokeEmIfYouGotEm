#include "Environment/RaftSimContinuousRiverSpec.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimContinuousRiverSpecTest,
    "RaftSim.M9.ContinuousRiverIdentityAndFrame",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimContinuousRiverSpecTest::RunTest(const FString& Parameters)
{
    using namespace RaftSimContinuousRiver;
    FString Error;FSpec Spec;
    auto J=MakeShared<FJsonObject>();
    J->SetStringField(TEXT("schema"),TEXT("raftsim.colorado_continuous_map_import.v1"));
    J->SetStringField(TEXT("rig"),TEXT("ColoradoOarRig"));
    TestTrue(TEXT("Existing Colorado contract remains supported"),Resolve(J,Spec,Error));
    TestTrue(TEXT("Colorado keeps its oar rig"),Spec.Rig==ERaftSimRaftRig::ColoradoOarRig);
    auto F=MakeShared<FJsonObject>();
    const TArray<TSharedPtr<FJsonValue>> Origin={MakeShared<FJsonValueNumber>(442909.),MakeShared<FJsonValueNumber>(5752141.5)};
    F->SetArrayField(TEXT("horizontal_origin_epsg6404_m"),Origin);
    F->SetNumberField(TEXT("vertical_datum_m"),310.);
    FVector2D XY;double Datum=0;
    TestTrue(TEXT("Legacy Colorado frame remains readable"),Frame(F,Spec,XY,Datum,Error));
    J->SetStringField(TEXT("river_id"),TEXT("chilko_river_bc"));
    TestFalse(TEXT("Legacy schema cannot disguise another river"),Resolve(J,Spec,Error));
    J->SetStringField(TEXT("schema"),TEXT("raftsim.continuous_map_import.v1"));
    TestFalse(TEXT("Chilko rejects the Colorado oar rig"),Resolve(J,Spec,Error));
    J->SetStringField(TEXT("rig"),TEXT("PaddleCrew"));
    TestTrue(TEXT("Explicit Chilko identity is supported"),Resolve(J,Spec,Error));
    TestTrue(TEXT("Chilko uses the production paddle crew"),Spec.Rig==ERaftSimRaftRig::PaddleCrew);
    TestEqual(TEXT("Chilko water asset family"),Spec.WaterStem,FString(TEXT("ChilkoLavaCanyon")));
    TestFalse(TEXT("Chilko rejects an EPSG6404 origin alias"),Frame(F,Spec,XY,Datum,Error));
    F->RemoveField(TEXT("horizontal_origin_epsg6404_m"));
    F->SetArrayField(TEXT("horizontal_origin_m"),Origin);
    F->SetStringField(TEXT("horizontal_crs"),TEXT("EPSG:3157"));
    F->SetStringField(TEXT("vertical_reference"),TEXT("CGVD2013 (EPSG:6647)"));
    F->SetNumberField(TEXT("vertical_datum_m"),900.);
    TestTrue(TEXT("Explicit native Chilko frame is accepted"),Frame(F,Spec,XY,Datum,Error));
    TestEqual(TEXT("Chilko origin is not recentered"),XY,FVector2D(442909.,5752141.5));
    TestEqual(TEXT("Chilko local Z offset is preserved"),Datum,900.);
    F->SetStringField(TEXT("horizontal_crs"),TEXT("EPSG:32610"));
    TestFalse(TEXT("WGS84 UTM is not substituted for NAD83 CSRS"),Frame(F,Spec,XY,Datum,Error));
    F->SetStringField(TEXT("horizontal_crs"),TEXT("EPSG:3157"));
    F->SetStringField(TEXT("vertical_reference"),TEXT("NAD83(2011) ellipsoid"));
    TestFalse(TEXT("Ellipsoid heights are not accepted as CGVD2013"),Frame(F,Spec,XY,Datum,Error));
    J->RemoveField(TEXT("river_id"));
    TestFalse(TEXT("New contracts require explicit river identity"),Resolve(J,Spec,Error));
    J->SetStringField(TEXT("river_id"),TEXT("unreviewed"));
    TestFalse(TEXT("Unknown rivers do not fall back to Colorado"),Resolve(J,Spec,Error));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFutaleufuContinuousTerrainFrameTest,
    "RaftSim.M9.FutaleufuContinuousTerrainFrame",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFutaleufuContinuousTerrainFrameTest::RunTest(const FString& Parameters)
{
    using namespace RaftSimContinuousRiver;
    FString Error; FSpec Spec;
    auto J=MakeShared<FJsonObject>();
    J->SetStringField(TEXT("schema"),TEXT("raftsim.continuous_landscape.v1"));
    J->SetStringField(TEXT("river_id"),TEXT("futaleufu_river_chile"));
    J->SetStringField(TEXT("rig"),TEXT("PaddleCrew"));
    TestTrue(TEXT("Full Futaleufu terrain has an explicit identity"),Resolve(J,Spec,Error));
    TestEqual(TEXT("Futaleufu keeps its own detail assets"),Spec.DetailStem,FString(TEXT("Futaleufu")));
    TestEqual(TEXT("Encoding includes the lower river below 200 m"),TerrainHeightBase(Spec),0.);
    J->SetArrayField(TEXT("horizontal_origin_m"),
        {MakeShared<FJsonValueNumber>(739986.),MakeShared<FJsonValueNumber>(5195961.5)});
    J->SetStringField(TEXT("horizontal_crs"),TEXT("EPSG:32718"));
    J->SetStringField(TEXT("vertical_reference"),TEXT("EGM2008"));
    J->SetNumberField(TEXT("vertical_datum_m"),150.);
    FVector2D XY;double Datum=0;
    TestTrue(TEXT("Southern UTM18 and source geoid frame accepted"),Frame(J,Spec,XY,Datum,Error));
    TestEqual(TEXT("Continuous river origin is not recentered"),XY,FVector2D(739986.,5195961.5));
    TestEqual(TEXT("Local vertical offset retained"),Datum,150.);
    J->SetArrayField(TEXT("horizontal_origin_m"),
        {MakeShared<FJsonValueNumber>(739987.),MakeShared<FJsonValueNumber>(5195961.5)});
    TestFalse(TEXT("Changed origin cannot silently misregister captured colour"),Frame(J,Spec,XY,Datum,Error));
    J->SetArrayField(TEXT("horizontal_origin_m"),
        {MakeShared<FJsonValueNumber>(739986.),MakeShared<FJsonValueNumber>(5195961.5)});
    J->SetStringField(TEXT("horizontal_crs"),TEXT("EPSG:32618"));
    TestFalse(TEXT("Northern hemisphere cannot substitute"),Frame(J,Spec,XY,Datum,Error));
    J->SetStringField(TEXT("horizontal_crs"),TEXT("EPSG:32718"));
    J->SetStringField(TEXT("vertical_reference"),TEXT("NAD83(2011) ellipsoid"));
    TestFalse(TEXT("Ellipsoid elevation cannot substitute for EGM2008"),Frame(J,Spec,XY,Datum,Error));
    TestFalse(TEXT("Foreign vegetation cannot silently populate Futaleufu"),Dressing(J,Spec,Error));
    J->SetStringField(TEXT("schema"),TEXT("raftsim.continuous_map_import.v1"));
    TestFalse(TEXT("Terrain registration alone cannot authorize a single-inlet runtime"),Resolve(J,Spec,Error));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimContinuousRiverDressingTest,
    "RaftSim.M9.ContinuousRiverDressingIdentity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimContinuousRiverDressingTest::RunTest(const FString& Parameters)
{
    using namespace RaftSimContinuousRiver;
    FString Error; FSpec Spec;
    auto Contract=MakeShared<FJsonObject>();
    Contract->SetStringField(TEXT("schema"),TEXT("raftsim.continuous_map_import.v1"));
    Contract->SetStringField(TEXT("river_id"),TEXT("chilko_river_bc"));
    TestTrue(TEXT("Resolve Chilko profile"),Resolve(Contract,Spec,Error));
    auto J=MakeShared<FJsonObject>();
    J->SetStringField(TEXT("schema"),TEXT("raftsim.chilko_continuous_dressing.v1"));
    J->SetStringField(TEXT("river_id"),TEXT("chilko_river_bc"));
    J->SetNumberField(TEXT("minimum_water_clearance_m"),12.);
    J->SetNumberField(TEXT("maximum_slope_degrees"),30.);
    J->SetNumberField(TEXT("cull_start_cm"),45000.);
    J->SetNumberField(TEXT("cull_end_cm"),65000.);
    const TCHAR* Names[]={TEXT("ConiferTree_A"),TEXT("ConiferTree_B"),TEXT("RiparianShrub_A"),TEXT("RiparianShrub_B")};
    TArray<TSharedPtr<FJsonValue>> Meshes;
    for(const TCHAR* Name:Names)
    {
        const FString Asset=FString(TEXT("SM_RaftSim_Temperate_"))+Name+TEXT("_OpaqueV1");
        Meshes.Add(MakeShared<FJsonValueString>(TEXT("/Game/RaftSim/Environment/TemperateRivers/Vegetation/Meshes/")+Asset+TEXT(".")+Asset));
    }
    J->SetArrayField(TEXT("meshes"),Meshes);
    TestTrue(TEXT("Reviewed Chilko vegetation contract accepted"),Dressing(J,Spec,Error));
    J->SetStringField(TEXT("schema"),TEXT("raftsim.colorado_continuous_dressing.v1"));
    TestFalse(TEXT("Colorado vegetation cannot substitute for Chilko"),Dressing(J,Spec,Error));
    J->SetStringField(TEXT("schema"),TEXT("raftsim.chilko_continuous_dressing.v1"));
    J->SetStringField(TEXT("river_id"),TEXT("other"));
    TestFalse(TEXT("Dressing must identify the same river"),Dressing(J,Spec,Error));
    J->SetStringField(TEXT("river_id"),TEXT("chilko_river_bc"));
    J->SetNumberField(TEXT("minimum_water_clearance_m"),11.99);
    TestFalse(TEXT("Water clearance cannot be weakened"),Dressing(J,Spec,Error));
    J->SetNumberField(TEXT("minimum_water_clearance_m"),12.);
    J->SetNumberField(TEXT("maximum_slope_degrees"),31.);
    TestFalse(TEXT("Steep ground cannot be accepted"),Dressing(J,Spec,Error));
    J->SetNumberField(TEXT("maximum_slope_degrees"),30.);
    J->SetNumberField(TEXT("cull_end_cm"),100000.);
    TestFalse(TEXT("Unreviewed render distance is refused"),Dressing(J,Spec,Error));
    J->SetNumberField(TEXT("cull_end_cm"),65000.);
    Meshes[0]=MakeShared<FJsonValueString>(TEXT("/Game/Unreviewed.Tree"));
    J->SetArrayField(TEXT("meshes"),Meshes);
    TestFalse(TEXT("Unreviewed asset is refused"),Dressing(J,Spec,Error));
    return true;
}
#endif
