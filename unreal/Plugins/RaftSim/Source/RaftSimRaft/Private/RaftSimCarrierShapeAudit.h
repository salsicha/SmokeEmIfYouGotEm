#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonSerializer.h"
#include "RaftSimShorelineCrests.h"

// Opt-in observation of the submitted carrier. No solver advance, GPU wait,
// geometry rewrite, temporal reset or extra detail commit is permitted here.
namespace RaftSimCarrierShapeAudit
{
inline bool Save(const FString& Path,const TArray<FProcMeshVertex>& Vertices,
    const TArray<uint32>& Indices,int32 ActiveCount,
    const FRaftSimShorelineCrests& Crests,
    TFunctionRef<double(const FVector&)> DetailCm,double WorldSeconds,
    uint64 DetailSequence,double RenderLiftCm,const FVector& FocusCm,
    int32 Nx,int32 Ny,TConstArrayView<FVector2D> FieldCoordinates,
    TConstArrayView<uint8> SourceWet,TConstArrayView<float> DepthM,
    TConstArrayView<float> BedM,float WorldYSign,
    TConstArrayView<FVector> TargetPositions,TConstArrayView<float> TargetCrestCm)
{
    const auto& Coarse=Crests.GetExpandedCoarseCrestCm();
    const auto& Correction=Crests.GetRenderedCorrectionsCm();
    if (ActiveCount<=0 || ActiveCount>Vertices.Num() || Coarse.Num()!=ActiveCount ||
        Correction.Num()!=ActiveCount || Indices.Num()%3 ||
        FieldCoordinates.Num()!=Nx*Ny || SourceWet.Num()!=Nx*Ny ||
        DepthM.Num()!=Nx*Ny || BedM.Num()!=Nx*Ny ||
        TargetPositions.Num()!=Nx*Ny || TargetCrestCm.Num()!=Nx*Ny) return false;
    for (int32 I=0;I<Nx*Ny;++I)
    {
        const auto& P=TargetPositions[I];
        if (P.ContainsNaN() || !FMath::IsFinite(TargetCrestCm[I]) ||
            FMath::Abs(P.X*.01-FieldCoordinates[I].X)>1.e-6 ||
            FMath::Abs(P.Y*.01*WorldYSign-FieldCoordinates[I].Y)>1.e-6) return false;
    }
    for (uint32 I:Indices) if (I>=uint32(ActiveCount)) return false;
    const FString VertexPath=Path+TEXT(".vertices.csv");
    const FString TrianglePath=Path+TEXT(".triangles.csv");
    const FString SourcePath=Path+TEXT(".source.csv");
    if (FPaths::FileExists(Path) || FPaths::FileExists(VertexPath) ||
        FPaths::FileExists(TrianglePath) || FPaths::FileExists(SourcePath)) return false;
    FString Rows=TEXT("id,x_cm,y_cm,carrier_z_cm,coarse_crest_cm,fine_correction_cm,detail_cm\n");
    for (int32 I=0;I<ActiveCount;++I)
    {
        const FVector& P=Vertices[I].Position;
        const double Detail=DetailCm(P);
        if (P.ContainsNaN() || !FMath::IsFinite(Coarse[I]) ||
            !FMath::IsFinite(Correction[I]) || !FMath::IsFinite(Detail)) return false;
        Rows.Appendf(TEXT("%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n"),
            I,P.X,P.Y,P.Z,double(Coarse[I]),double(Correction[I]),Detail);
    }
    if (!FFileHelper::SaveStringToFile(Rows,*VertexPath)) return false;
    Rows=TEXT("a,b,c\n");
    for (int32 I=0;I<Indices.Num();I+=3)
        Rows.Appendf(TEXT("%u,%u,%u\n"),Indices[I],Indices[I+1],Indices[I+2]);
    if (!FFileHelper::SaveStringToFile(Rows,*TrianglePath)) return false;
    Rows=TEXT("id,field_x_m,field_y_m,clipping_wet,source_bed_plus_depth_m,source_depth_m,target_base_m,target_full_m\n");
    for (int32 I=0;I<DepthM.Num();++I)
    {
        const auto& P=FieldCoordinates[I];
        const double Target=TargetPositions[I].Z*.01;
        Rows.Appendf(TEXT("%d,%.17g,%.17g,%d,%.17g,%.17g,%.17g,%.17g\n"),I,P.X,P.Y,
            int32(SourceWet[I]),double(BedM[I])+double(DepthM[I]),double(DepthM[I]),
            Target-(double(TargetCrestCm[I])+RenderLiftCm)*.01,Target);
    }
    if (!FFileHelper::SaveStringToFile(Rows,*SourcePath)) return false;
    auto Report=MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("schema"),TEXT("raftsim.submitted_carrier_shape.v2"));
    Report->SetStringField(TEXT("target_scope"),TEXT("Current pre-temporal carrier targets on the exact source lattice at this publication. Target base subtracts the current coarse crest and render lift; it retains hydraulic and other shaping. Submitted base minus interpolated target base includes temporal and refinement/interpolation differences, not a pure measured temporal error. No targets are updated by this audit."));
    Report->SetStringField(TEXT("scope"),TEXT("Actual submitted CPU triangles and the already presented detail payload, sampled at their vertices. Base is a residual containing current temporal/clipped source and other relief, NOT raw solver stage. Source comparison is the double sum of currently cached bed and depth used by clipping, with its connected/available wet mask, not a new source sample or necessarily the temporally displayed state. No GPU readback, additional commit, optical normal measurement, occlusion, render latency, or visual/physical acceptance."));
    Report->SetNumberField(TEXT("world_seconds"),WorldSeconds);
    Report->SetNumberField(TEXT("detail_sequence"),DetailSequence);
    Report->SetNumberField(TEXT("render_lift_cm"),RenderLiftCm);
    Report->SetNumberField(TEXT("active_vertices"),ActiveCount);
    Report->SetNumberField(TEXT("buffer_vertices"),Vertices.Num());
    Report->SetNumberField(TEXT("triangles"),Indices.Num()/3);
    Report->SetNumberField(TEXT("source_nx"),Nx);Report->SetNumberField(TEXT("source_ny"),Ny);
    Report->SetNumberField(TEXT("world_y_sign"),WorldYSign);
    Report->SetNumberField(TEXT("focus_x_cm"),FocusCm.X);Report->SetNumberField(TEXT("focus_y_cm"),FocusCm.Y);
    FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
    // Metadata last is the completion marker; partial files remain evidence.
    return FFileHelper::SaveStringToFile(Json,*Path);
}
}
