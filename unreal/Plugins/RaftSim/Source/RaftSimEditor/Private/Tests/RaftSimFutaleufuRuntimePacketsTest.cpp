#include "RaftSimWaterRuntimeAdapter.h"
#include "Dom/JsonObject.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/StrongObjectPtr.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFutaleufuRuntimePacketsTest,
    "RaftSim.M9.FutaleufuRuntimePackets",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFutaleufuRuntimePacketsTest::RunTest(const FString&)
{
    FString Relative;
    if (!FParse::Value(FCommandLine::Get(),TEXT("RaftSimFutaleufuRuntime="),Relative) ||
        !FPaths::IsRelative(Relative) || Relative.Contains(TEXT("..")))
    { AddError(TEXT("Supply a repo-relative -RaftSimFutaleufuRuntime=<verified export>")); return false; }
    const FString Root=URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(Relative);
    const auto Read=[](const FString& Path)
    {
        FString Text;TSharedPtr<FJsonObject> J;
        if(FFileHelper::LoadFileToString(Text,*Path)) FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),J);
        return J;
    };
    const auto Receipt=Read(Root/TEXT("export_audit.json"));
    const auto Streaming=Read(Root/TEXT("streaming_manifest.json"));
    if(!TestTrue(TEXT("Completed full-route packet export exists"),Receipt.IsValid() && Streaming.IsValid()))return false;
    if(!TestEqual(TEXT("Candidate identity"),Receipt->GetStringField(TEXT("schema")),FString(TEXT("raftsim.futaleufu_cartesian_runtime_candidate.v1"))))return false;
    const auto& Windows=Streaming->GetArrayField(TEXT("windows"));
    if(!TestEqual(TEXT("Every exported packet is tested"),Windows.Num(),int32(Receipt->GetNumberField(TEXT("source_packet_count")))))return false;
    if(!TestTrue(TEXT("Source bank/route probes are completely covered"),
        Receipt->GetNumberField(TEXT("covered_probes"))==Receipt->GetNumberField(TEXT("original_route_and_bank_probes")) && !Windows.IsEmpty()))return false;
    TStrongObjectPtr<URaftSimWaterRuntimeAdapter> Water(NewObject<URaftSimWaterRuntimeAdapter>());
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false;
    Config.bEnableDeterministicCapture=false;
    Config.FixedStepSeconds=.01f;
    int64 Sampled=0,Wet=0;
    double MaximumWorldDepthError=0.,MaximumWorldVelocityError=0.,MaximumStepMs=0.;
    for(int32 I=0;I<Windows.Num();++I)
    {
        // Independent packet loads, not a fabricated continuous descent or a
        // handoff test. Rendering/boat/rescue acceptance remains separate.
        Water->Configure(Config);
        if(!TestTrue(TEXT("Native Cartesian coordinate map loads"),Water->ConfigureRiverCoordinateMap(Relative/TEXT("coordinate_map.json"))))return false;
        const auto Row=Windows[I]->AsObject();
        const auto& B=Row->GetArrayField(TEXT("valid_live_center_bounds_m"))[0]->AsArray();
        const FVector2D Center((B[0]->AsNumber()+B[2]->AsNumber())*.5,(B[1]->AsNumber()+B[3]->AsNumber())*.5);
        const FString Fields=FPaths::GetPath(Row->GetStringField(TEXT("cooked_fields_manifest")));
        if(!TestTrue(*FString::Printf(TEXT("Actual native packet %d loads"),I),
            Water->ConfigureRiverWindow(Fields,TEXT("median_runnable"),Center,FVector2D(224.,224.),.045f,false)))return false;
        FBox2D Bounds;
        if(!TestTrue(TEXT("Full 224 m crop retained"),Water->GetLiveWaterFieldBoundsM(Bounds) && Bounds.GetSize().GetMin()>=224.))return false;
        int32 PacketWet=0;
        for(int32 Y=-96;Y<=96;Y+=8)for(int32 X=-96;X<=96;X+=8)
        {
            const FVector2D P=Center+FVector2D(X,Y);
            FRaftSimWaterSample Native,World;
            if(!TestTrue(TEXT("Native full-crop sample is available"),Water->SampleWaterFieldAtRiverCoordinates(P,Native)))return false;
            if(!TestTrue(TEXT("Native sample respects finite depth/speed bounds"),
                FMath::IsFinite(Native.DepthMeters) && Native.DepthMeters>=0. && Native.DepthMeters<=10. &&
                !Native.VelocityMetersPerSecond.ContainsNaN() && Native.VelocityMetersPerSecond.Size()<=20.001))return false;
            ++Sampled;
            // Dry terrain context can extend beyond the hydraulic atlas bounds;
            // only actual water is required to have a world-space water sample.
            if(!Native.bWet)continue;
            ++Wet;++PacketWet;
            FVector Position;
            if(!Water->RiverToWorldPosition(P,Native.SurfaceHeightMeters+Water->GetRiverVerticalDatumM(),Position) ||
                !Water->SampleWaterAtWorldPosition(Position,World))return false;
            MaximumWorldDepthError=FMath::Max(MaximumWorldDepthError,double(FMath::Abs(World.DepthMeters-Native.DepthMeters)));
            const FVector Expected(Native.VelocityMetersPerSecond.X,-Native.VelocityMetersPerSecond.Y,Native.VelocityMetersPerSecond.Z);
            MaximumWorldVelocityError=FMath::Max(MaximumWorldVelocityError,(World.VelocityMetersPerSecond-Expected).Size());
        }
        if(!TestTrue(TEXT("Every route source includes actual flowing river cells"),PacketWet>0))return false;
        if(!TestTrue(TEXT("Actual in-game solver advances"),Water->StepWater(.01f)))return false;
        FRaftSimWaterLiveWindowStats Stats;
        if(!TestTrue(TEXT("Advanced native state remains finite with a real clock"),
            Water->GetLiveWindowStats(Stats) && !Stats.bHasNonFinite && Stats.SimTimeSeconds>0.))return false;
        MaximumStepMs=FMath::Max(MaximumStepMs,double(Stats.LastSolverStepMilliseconds));
        if((I+1)%20==0)AddInfo(FString::Printf(TEXT("Loaded and advanced actual Futaleufu runtime packets %d/%d"),I+1,Windows.Num()));
    }
    Water->Configure(Config);
    TestTrue(TEXT("Hydraulic/world coordinates preserve depth"),MaximumWorldDepthError<1.e-4);
    TestTrue(TEXT("North-reflected world current agrees"),MaximumWorldVelocityError<1.e-4);
    AddInfo(FString::Printf(TEXT("Futaleufu native loader: %d packets, %lld samples, %lld wet samples, max depth error %.9g m, velocity error %.9g m/s, max isolated step %.3f ms. NOT rendered/boat/20-FPS or settled-flow acceptance."),
        Windows.Num(),Sampled,Wet,MaximumWorldDepthError,MaximumWorldVelocityError,MaximumStepMs));
    return !HasAnyErrors();
}
#endif
