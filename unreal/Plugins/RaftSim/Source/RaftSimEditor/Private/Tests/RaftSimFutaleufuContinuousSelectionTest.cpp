#include "RaftSimCartesianWaterRegions.h"
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
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFutaleufuContinuousSelectionTest,
    "RaftSim.M9.FutaleufuContinuousSelection",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFutaleufuContinuousSelectionTest::RunTest(const FString&)
{
    FString Relative;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimFutaleufuRuntime="),Relative) ||
        !FPaths::IsRelative(Relative) || Relative.Contains(TEXT("..")))
    {AddError(TEXT("Supply a verified repo-relative Futaleufu runtime export"));return false;}
    const auto Read=[](const FString& Path)
    {
        FString Text;TSharedPtr<FJsonObject> J;
        if(FFileHelper::LoadFileToString(Text,*URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(Path)))
            FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),J);
        return J;
    };
    const auto Receipt=Read(Relative/TEXT("export_audit.json"));
    const auto Streaming=Read(Relative/TEXT("streaming_manifest.json"));
    if(!Receipt || !Streaming)return false;
    const FString ProgressPath=Receipt->GetStringField(TEXT("progress_chart"));
    const auto Progress=Read(ProgressPath);
    if(!Progress)return false;
    const auto& Points=Progress->GetArrayField(TEXT("points"));
    if(!TestTrue(TEXT("Full original captured route, not a short fixture"),Points.Num()>8000 &&
        Points.Last()->AsArray()[0]->AsNumber()>15960.))return false;
    FRaftSimCartesianWaterRegions Regions;FString Error;
    if(!Regions.Load(Streaming,Error)){AddError(Error);return false;}
    TStrongObjectPtr<URaftSimWaterRuntimeAdapter> Water(NewObject<URaftSimWaterRuntimeAdapter>());
    TStrongObjectPtr<URaftSimWaterRuntimeAdapter> Route(NewObject<URaftSimWaterRuntimeAdapter>());
    FRaftSimWaterRuntimeConfig Config;
    Config.bRequireAcceptedReportManifest=false;Config.bEnableDeterministicCapture=false;Config.FixedStepSeconds=.01f;
    Water->Configure(Config);Route->Configure(Config);
    if(!Water->ConfigureRiverCoordinateMap(Relative/TEXT("coordinate_map.json")) || !Route->ConfigureRiverCoordinateMap(ProgressPath))return false;
    FString Active;FVector2D PreviousCenter=FVector2D::ZeroVector;
    int32 Changes=0,DryCenters=0;int64 Samples=0;double MaxCoordinateError=0.;
    // Follow every real source vertex and interpolated route point through
    // the same selector/recentering rules used by the production actor.
    // Advancing a probe is NOT a boat descent or navigation proof.
    for(int32 I=0;I<Points.Num();++I)
    {
        const auto& Row=Points[I]->AsArray();
        const double Station=Row[0]->AsNumber();
        FVector World,Tangent,Normal;FVector2D P,Center;
        if(!Route->RiverToWorldPosition(FVector2D(Station,0),150.,World) ||
            !Water->WorldToRiverCoordinates(World,P,Tangent,Normal))return false;
        MaxCoordinateError=FMath::Max(MaxCoordinateError,(P-FVector2D(Row[1]->AsNumber(),Row[2]->AsNumber())).Size());
        const auto* Region=Regions.Select(P,Active,&Center);
        if(!Region){AddError(FString::Printf(TEXT("No complete source at captured station %.3f"),Station));return false;}
        const bool Change=Active.IsEmpty() || Region->FieldsDirectory!=Active ||
            !Regions.CoversRaft(P,PreviousCenter) || Regions.NeedsRecentering(Center,PreviousCenter);
        if(Change)
        {
            FRaftSimWaterLiveWindowStats Before,After;
            const bool Existing=Water->GetLiveWindowStats(Before);
            if(!Water->ConfigureMovingRiverWindow(Region->FieldsDirectory,TEXT("median_runnable"),Center,Regions.GetExtentM(),Regions.GetRoughnessManning()) ||
                !Water->GetLiveWindowStats(After))return false;
            if(Existing && !TestTrue(TEXT("Continuous route cannot cold-restart water"),After.bLastHandoffPreservedState &&
                After.LastHandoffTransferredCellCount>0 && After.SimTimeSeconds==Before.SimTimeSeconds))return false;
            Active=Region->FieldsDirectory;PreviousCenter=Center;++Changes;
            for(int32 Step=0;Step<5;++Step)if(!Water->StepWater(.01f))return false;
        }
        if(!TestTrue(TEXT("Production selection retains full raft margin"),Regions.CoversRaft(P,PreviousCenter)))return false;
        FBox2D Bounds;if(!Water->GetLiveWaterFieldBoundsM(Bounds))return false;
        for(int32 Y=-4;Y<=4;Y+=4)for(int32 X=-4;X<=4;X+=4)
        {
            FRaftSimWaterSample S;const FVector2D Probe=P+FVector2D(X,Y);
            if(!Bounds.IsInside(Probe) || !Water->SampleWaterFieldAtRiverCoordinates(Probe,S) ||
                !FMath::IsFinite(S.DepthMeters) || S.DepthMeters<0. || S.DepthMeters>10. ||
                S.VelocityMetersPerSecond.ContainsNaN() || S.VelocityMetersPerSecond.Size()>20.001)
            {AddError(FString::Printf(TEXT("Unavailable/unbounded route field at station %.3f offset %d,%d"),Station,X,Y));return false;}
            if(X==0 && Y==0 && !S.bWet)++DryCenters;
            ++Samples;
        }
    }
    Water->Configure(Config);Route->Configure(Config);
    TestTrue(TEXT("Cartesian hydraulic and curved progress coordinates agree"),MaxCoordinateError<1.e-5);
    TestTrue(TEXT("Full-route source changes exercised"),Changes>100);
    AddInfo(FString::Printf(TEXT("Futaleufu full captured-route selection: %d points, %d source/recenter loads, %lld field samples, %d dry centerline points, maximum coordinate error %.9g m. No cold restarts. Probe walk only; dry centers are reported, not treated as navigation or boat/visual/FPS acceptance."),
        Points.Num(),Changes,Samples,DryCenters,MaxCoordinateError));
    return !HasAnyErrors();
}
#endif
