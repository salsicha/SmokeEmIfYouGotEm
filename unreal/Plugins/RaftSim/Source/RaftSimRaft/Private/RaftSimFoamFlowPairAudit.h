#pragma once
#include "RaftSimDetailPresentationFrame.h"
#include "ProceduralMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace RaftSimFoamFlowPairAudit
{
inline void Run(const TArray<FProcMeshVertex>& Vertices,
    TSharedPtr<const FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe> Frame,float Sign,double WorldSeconds)
{
#if !UE_BUILD_SHIPPING
    static const FString Path=[]{FString P;FParse::Value(FCommandLine::Get(),TEXT("RaftSimFoamFlowPairAudit="),P);return P;}();
    if(Path.IsEmpty() || FPaths::FileExists(Path) || WorldSeconds<10 || !Frame || Frame->FoamFlowPixels.IsEmpty())return;
    const auto M=Frame->Pixels[Frame->Size.X*Frame->Size.Y];
    TArray<TSharedPtr<FJsonValue>> Rows;double Maximum=0,SumSquared=0;int32 Foamy=0,Opposed=0;
    for(int32 I=0;I<Vertices.Num();++I)
    {
        const auto& V=Vertices[I];
        const FVector2f P(float(V.Position.X)*.01f,float(V.Position.Y)*(.01f*Sign));
        const FVector2f Local=P-FVector2f(M.X,M.Y);
        const float Edge=FMath::Min(FMath::Min(Local.X,Local.Y),
            FMath::Min((Frame->Size.X-1)*M.Z-Local.X,(Frame->Size.Y-1)*M.Z-Local.Y));
        if(Edge<4)continue; // Fully GPU-owned interior only; no boundary mixtures.
        const auto Flow=Frame->SampleFoamFlow(P),Surface=Frame->SampleField(P);
        if(Flow.X<=.01f)continue;
        const FVector2D Mean(Flow.Y,Flow.Z),Optical=V.UV3;
        const double Delta=(Mean-Optical).Size();
        Maximum=FMath::Max(Maximum,Delta);SumSquared+=Delta*Delta;
        Foamy+=Surface.W>.1f;Opposed+=FVector2D::DotProduct(Mean,Optical)<0;
        auto R=MakeShared<FJsonObject>();R->SetNumberField(TEXT("vertex"),I);
        R->SetNumberField(TEXT("x_m"),P.X);R->SetNumberField(TEXT("y_m"),P.Y);
        R->SetNumberField(TEXT("mean_u_mps"),Mean.X);R->SetNumberField(TEXT("mean_v_mps"),Mean.Y);
        R->SetNumberField(TEXT("optical_u_mps"),Optical.X);R->SetNumberField(TEXT("optical_v_mps"),Optical.Y);
        R->SetNumberField(TEXT("depth_m"),Flow.X);R->SetNumberField(TEXT("coverage"),Surface.W);
        R->SetNumberField(TEXT("difference_mps"),Delta);Rows.Add(MakeShared<FJsonValueObject>(R));
    }
    auto Report=MakeShared<FJsonObject>();Report->SetStringField(TEXT("schema"),TEXT("raftsim.foam_flow_pair.v1"));
    Report->SetStringField(TEXT("scope"),TEXT("Actual submitted carrier UV3 versus mean-flow input retained with the displayed GPU foam frame; all wet fully-owned interior vertices, including refined nodes. Same source-coordinate convention. Not calibrated physical velocity or pixel attribution."));
    Report->SetNumberField(TEXT("game_frame"),double(GFrameCounter));Report->SetNumberField(TEXT("world_seconds"),WorldSeconds);
    Report->SetNumberField(TEXT("detail_sequence"),Frame->Sequence);Report->SetNumberField(TEXT("simulation_seconds"),Frame->SimulationSeconds);
    Report->SetNumberField(TEXT("vertices"),Rows.Num());Report->SetNumberField(TEXT("coverage_above_point_one"),Foamy);
    Report->SetNumberField(TEXT("opposed_vertices"),Opposed);Report->SetNumberField(TEXT("maximum_difference_mps"),Maximum);
    Report->SetNumberField(TEXT("rms_difference_mps"),Rows.Num()?FMath::Sqrt(SumSquared/Rows.Num()):0);
    Report->SetBoolField(TEXT("paired_frame_valid"),Frame->Validate());Report->SetArrayField(TEXT("samples"),Rows);
    FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    const bool Saved=FFileHelper::SaveStringToFile(Json,*Path);
    UE_LOG(LogTemp,Display,TEXT("Foam flow paired audit: saved=%d vertices=%d max_difference_mps=%.9g path=%s"),Saved,Rows.Num(),Maximum,*Path);
#endif
}
}
