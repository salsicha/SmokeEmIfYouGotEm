#include "RaftSimCartesianWaterRegions.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRaftMesh.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Engine/StaticMesh.h"
#include "Misc/AutomationTest.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/UnrealType.h"

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimFutaleufuHullClearanceTest,
    "RaftSim.M9.FutaleufuHullClearance",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFutaleufuHullClearanceTest::RunTest(const FString&)
{
    FString Relative,ReportPath;
    if(!FParse::Value(FCommandLine::Get(),TEXT("RaftSimFutaleufuRuntime="),Relative) ||
        !FPaths::IsRelative(Relative) || Relative.Contains(TEXT("..")) ||
        !FParse::Value(FCommandLine::Get(),TEXT("RaftSimHullClearanceReport="),ReportPath) ||
        !ReportPath.StartsWith(TEXT("tmp/")) || ReportPath.Contains(TEXT("..")))return false;
    // Runtime input resolution only prefers repo paths that already exist;
    // a fresh output must instead be rooted explicitly in this repo's tmp.
    ReportPath=FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(),TEXT(".."),ReportPath));
    if(FPaths::GetExtension(ReportPath).IsEmpty())ReportPath+=TEXT(".json");
    if(FPaths::FileExists(ReportPath)){AddError(TEXT("Fresh clearance evidence required"));return false;}
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
    const auto Progress=Read(Receipt->GetStringField(TEXT("progress_chart")));
    if(!Progress)return false;
    const auto& Points=Progress->GetArrayField(TEXT("points"));
    FRaftSimCartesianWaterRegions Regions;FString Error;
    if(!Regions.Load(Streaming,Error)){AddError(Error);return false;}
    const auto* Asset=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/RaftSim/Rafts/Production/SM_RaftSim_ProductionPaddleRaft.SM_RaftSim_ProductionPaddleRaft"));
    TArray<RaftSimRaftMesh::FMeshData> Rest,Prepared;
    const auto* RadiusProperty=FindFProperty<FFloatProperty>(ARaftSimRaftActor::StaticClass(),TEXT("TubeRadiusM"));
    if(!RadiusProperty || !RaftSimRaftMesh::ExtractProductionRaftRestMesh(Asset,Rest))return false;
    const float Radius=RadiusProperty->GetPropertyValue_InContainer(GetDefault<ARaftSimRaftActor>());
    RaftSimRaftMesh::DeformProductionRaftRestMesh(Rest,Radius,{},RaftSimRaftMesh::FRaftSimRaftVisualCondition{},Prepared);
    FRaftSimHullGeometry Hull;
    if(!RaftSimRaftMesh::ExportHullGeometry(Prepared,FTransform(FQuat::Identity,FVector(0,0,-100.*Radius)),Hull))return false;
    // Retain every production vertex and indexed face. Centroid probes extend
    // the static footprint audit; they are NOT an exact swept collision test.
    TArray<FVector> Probes=Hull.VerticesM;
    for(const auto& F:Hull.Faces)Probes.Add((Hull.VerticesM[F.X]+Hull.VerticesM[F.Y]+Hull.VerticesM[F.Z])/3.);
    TStrongObjectPtr<URaftSimWaterRuntimeAdapter> Water(NewObject<URaftSimWaterRuntimeAdapter>());
    FRaftSimWaterRuntimeConfig Config;Config.bRequireAcceptedReportManifest=false;Config.bEnableDeterministicCapture=false;
    Water->Configure(Config);
    if(!Water->ConfigureRiverCoordinateMap(Relative/TEXT("coordinate_map.json")))return false;
    TArray<TSharedPtr<FJsonValue>> Results;int32 Qualified=0,Unqualified=0,Refined=0;int64 Queries=0;
    double NextStation=0.;
    for(int32 I=0;I<Points.Num();++I)
    {
        const auto& P=Points[I]->AsArray();const double Station=P[0]->AsNumber();
        if(Station<NextStation && I!=Points.Num()-1)continue;
        NextStation=Station+20.;
        const FVector2D Axis(P[1]->AsNumber(),P[2]->AsNumber());
        const FVector2D Left=FVector2D(P[3]->AsNumber(),P[4]->AsNumber()).GetSafeNormal();
        const FVector2D Forward(Left.Y,-Left.X);
        bool Found=false;double ChosenOffset=0.,Minimum=0.;FVector2D Chosen=FVector2D::ZeroVector;
        // Find the nearest qualifying offset, never move the captured axis or
        // change the source bed/water. This does not prove linked navigability.
        for(int32 Attempt=0;Attempt<=720 && !Found;++Attempt)
        {
            const bool Fine=Attempt>80;
            const int32 Search=Fine ? Attempt-80 : Attempt;
            const double Offset=Search==0 ? 0. : ((Search+1)/2)*(Fine ? .25 : 2.)*(Search%2 ? 1. : -1.);
            // Refine failed coarse positions without widening the original
            // +/-80 m envelope, lowering the planning depth, or changing water/bed.
            if(Fine && FMath::Fmod(FMath::Abs(Offset),2.)==0.)continue;
            const FVector2D Position=Axis+Left*Offset;FVector2D Center;
            const auto* Region=Regions.Select(Position,TEXT(""),&Center);
            if(!Region)continue;
            // Each candidate reads the same immutable native time, not a
            // previously visited crop's evolved state or a fabricated velocity.
            if(!Water->ConfigureRiverWindow(Region->FieldsDirectory,TEXT("median_runnable"),Center,Regions.GetExtentM(),Regions.GetRoughnessManning(),false))return false;
            bool Good=true;Minimum=TNumericLimits<double>::Max();
            for(const auto& V:Probes)
            {
                FRaftSimWaterSample S;
                const FVector2D Q=Position+Forward*V.X-Left*V.Y;
                ++Queries;
                if(!Water->SampleWaterFieldAtRiverCoordinates(Q,S) || !FMath::IsFinite(S.DepthMeters))return false;
                Minimum=FMath::Min(Minimum,double(S.DepthMeters));
                if(!S.bWet || S.DepthMeters<.35f){Good=false;break;}
            }
            if(Good){Found=true;ChosenOffset=Offset;Chosen=Position;if(Fine)++Refined;}
        }
        auto Row=MakeShared<FJsonObject>();Row->SetNumberField(TEXT("station_m"),Station);
        Row->SetBoolField(TEXT("static_full_mesh_probes_qualified"),Found);
        if(Found)
        {
            ++Qualified;Row->SetNumberField(TEXT("lateral_offset_m"),ChosenOffset);
            Row->SetNumberField(TEXT("hydraulic_x_m"),Chosen.X);Row->SetNumberField(TEXT("hydraulic_y_m"),Chosen.Y);
            Row->SetNumberField(TEXT("minimum_probed_depth_m"),Minimum);
        }
        else ++Unqualified;
        Results.Add(MakeShared<FJsonValueObject>(Row));
    }
    Water->Configure(Config);
    auto Report=MakeShared<FJsonObject>();Report->SetStringField(TEXT("schema"),TEXT("raftsim.futaleufu_native_hull_clearance.v1"));
    Report->SetStringField(TEXT("runtime_source"),Relative);Report->SetStringField(TEXT("mesh"),Asset->GetPathName());
    Report->SetNumberField(TEXT("vertices"),Hull.VerticesM.Num());Report->SetNumberField(TEXT("faces"),Hull.Faces.Num());
    Report->SetNumberField(TEXT("sections"),Hull.Sections.Num());Report->SetNumberField(TEXT("queries"),Queries);
    Report->SetNumberField(TEXT("qualified_stations"),Qualified);Report->SetNumberField(TEXT("unqualified_stations"),Unqualified);
    Report->SetNumberField(TEXT("stations_resolved_by_submetre_search"),Refined);
    Report->SetNumberField(TEXT("coarse_lateral_spacing_m"),2.);Report->SetNumberField(TEXT("refined_lateral_spacing_m"),.25);
    Report->SetNumberField(TEXT("planning_depth_threshold_m"),.35);
    Report->SetStringField(TEXT("scope"),TEXT("Static upright production rest-hull vertex and face-centroid probes every 20 m, offset search +/-80 m. Conservative planning screen only: no swept collision, loaded draft, linked route, steering, recovery, rendering or FPS acceptance. No terrain or water was changed."));
    Report->SetArrayField(TEXT("stations"),Results);FString Json;
    if(!FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json)) || !FFileHelper::SaveStringToFile(Json,*ReportPath))return false;
    AddInfo(FString::Printf(TEXT("Native production hull clearance: %d vertices, %d faces, %d sections, %d qualified stations, %d unqualified, %lld queries. See %s; no navigation acceptance."),
        Hull.VerticesM.Num(),Hull.Faces.Num(),Hull.Sections.Num(),Qualified,Unqualified,Queries,*ReportPath));
    // A failed planning screen remains a failed screen; do not hide it behind
    // a green coverage test, broaden the search or lower the depth threshold.
    TestEqual(TEXT("Every examined station has a conservative full-mesh planning footprint"),Unqualified,0);
    return !HasAnyErrors();
}
#endif
