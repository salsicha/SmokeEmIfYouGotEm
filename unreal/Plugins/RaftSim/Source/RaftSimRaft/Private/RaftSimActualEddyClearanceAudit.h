#pragma once

#include "RaftSimGroundSourceRegistry.h"
#include "RaftSimShorelineMeshComponent.h"
#include "RaftSimWaterShoreline.h"
#include "RaftSimWaterSurfaceActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Dom/JsonObject.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Materials/MaterialInterface.h"

// Explicit diagnostic only. Observe existing native contact and submitted
// triangles; never move a mesh, alter a mask/field, or substitute solver bed
// for missing physical ground. Excludes GPU detail, shader WPO and pixels.
namespace RaftSimActualEddyClearanceAudit
{
inline void Run(UWorld* World, URaftSimWaterRuntimeAdapter* Water,
    const URaftSimWaterRuntimeAdapter::FSupportBoulderFootprint& Owner,
    const TSharedRef<FJsonObject>& Entry)
{
    if (!FParse::Param(FCommandLine::Get(), TEXT("RaftSimEddyClearanceAudit"))) return;
    const double Started=FPlatformTime::Seconds();
    struct FCarrier
    {
        FString Name;
        FString Material;
        float LiquidExtinctionPerM=0.f;
        bool HasLiquidExtinction=false;
        bool TwoSided=false;
        FBox Bounds;
        TArray<FProcMeshVertex> Vertices;
        TArray<uint32> Indices;
    };
    TArray<FCarrier> Carriers;
    const auto AddCarrier=[&](UMeshComponent* Component,
        TConstArrayView<FProcMeshVertex> Vertices,TConstArrayView<uint32> Indices)
    {
        if (!Component->IsVisible() || Component->bHiddenInGame || Indices.IsEmpty()) return;
        FCarrier& Carrier=Carriers.AddDefaulted_GetRef();
        Carrier.Name=Component->GetPathName();
        Carrier.Bounds=Component->Bounds.GetBox();
        if (auto* Material=Component->GetMaterial(0))
        {
            Carrier.Material=Material->GetPathName();
            Carrier.TwoSided=Material->IsTwoSided();
            Carrier.HasLiquidExtinction=Material->GetScalarParameterValue(
                FHashedMaterialParameterInfo(TEXT("CapturedLiquidOpticalExtinctionPerM")),
                Carrier.LiquidExtinctionPerM);
        }
        Carrier.Vertices.Append(Vertices.GetData(),Vertices.Num());
        Carrier.Indices.Append(Indices.GetData(),Indices.Num());
        const FTransform Transform=Component->GetComponentTransform();
        for (auto& V:Carrier.Vertices) V.Position=Transform.TransformPosition(V.Position);
    };
    for (TActorIterator<ARaftSimWaterSurfaceActor> It(World);It;++It)
    {
        TInlineComponentArray<UProceduralMeshComponent*> Procedural(*It);
        for (auto* Component:Procedural)
        {
            // Foam skirts and fallback layers do not establish carrier height.
            if (Component->GetFName()!=TEXT("SurfaceMesh") &&
                Component->GetFName()!=TEXT("LiveVolumeCoreMesh")) continue;
            const FProcMeshSection* Section=Component->GetProcMeshSection(0);
            if (Section && Section->bSectionVisible)
                AddCarrier(Component,Section->ProcVertexBuffer,Section->ProcIndexBuffer);
        }
        TInlineComponentArray<URaftSimShorelineMeshComponent*> Shorelines(*It);
        for (auto* Component:Shorelines)
            AddCarrier(Component,Component->GetWaterVertices(),Component->GetWaterIndices());
    }
    FRaftSimGroundSourceRegistry Ground(World);
    const FVector2D D=Owner.FlowDirection,L(-D.Y,D.X);
    TArray<TSharedPtr<FJsonValue>> Rows,CarrierRecords;
    for (const auto& Carrier:Carriers)
    {
        auto Item=MakeShared<FJsonObject>();
        Item->SetStringField(TEXT("component"),Carrier.Name);
        Item->SetNumberField(TEXT("vertices"),Carrier.Vertices.Num());
        Item->SetNumberField(TEXT("triangles"),Carrier.Indices.Num()/3);
        CarrierRecords.Add(MakeShared<FJsonValueObject>(Item));
    }
    int32 Wet=0,GroundHits=0,WetOccluded=0,Submitted=0;
    for (int32 Along=0;Along<=20;++Along) for (int32 Across=-6;Across<=6;++Across)
    {
        const FVector2D Local(Along*.25,Across*.25);
        const FVector2D Q=Owner.RiverCoordinatesMeters+
            (D*Local.X+L*Local.Y)*Owner.RadiusMeters;
        auto Row=MakeShared<FJsonObject>();
        Row->SetNumberField(TEXT("along_radius"),Local.X);
        Row->SetNumberField(TEXT("across_radius"),Local.Y);
        Row->SetNumberField(TEXT("hydraulic_x_m"),Q.X);
        Row->SetNumberField(TEXT("hydraulic_y_m"),Q.Y);
        FRaftSimWaterSample Raw;
        const bool Available=Water->SampleWaterFieldAtRiverCoordinates(Q,Raw);
        Row->SetBoolField(TEXT("raw_available"),Available);
        Row->SetBoolField(TEXT("raw_wet"),Available && Raw.bWet);
        FVector P=FVector::ZeroVector;
        const bool WorldAvailable=Available && Water->RiverToWorldPosition(Q,
            Raw.SurfaceHeightMeters+Water->GetRiverVerticalDatumM(),P);
        Row->SetBoolField(TEXT("world_available"),WorldAvailable);
        if (WorldAvailable)
        {
            Wet+=Raw.bWet;
            Row->SetNumberField(TEXT("world_x_cm"),P.X);
            Row->SetNumberField(TEXT("world_y_cm"),P.Y);
            Row->SetNumberField(TEXT("raw_surface_world_z_cm"),P.Z);
            Row->SetNumberField(TEXT("raw_bed_world_z_cm"),Raw.BedHeightMeters*100.);
            Row->SetNumberField(TEXT("raw_depth_m"),Raw.DepthMeters);
            FVector Normal;double GroundZ=0.;FHitResult Hit;
            const bool GroundHit=Ground.SampleGround(P,GroundZ,Normal,&Hit);
            Row->SetBoolField(TEXT("physical_ground_hit"),GroundHit);
            if (GroundHit)
            {
                ++GroundHits;WetOccluded+=Raw.bWet && GroundZ>=P.Z;
                Row->SetNumberField(TEXT("physical_ground_world_z_cm"),GroundZ);
                Row->SetNumberField(TEXT("water_above_physical_ground_cm"),P.Z-GroundZ);
                Row->SetNumberField(TEXT("physical_ground_minus_raw_bed_cm"),GroundZ-Raw.BedHeightMeters*100.);
                if (Hit.GetComponent())Row->SetStringField(TEXT("physical_ground_source"),Hit.GetComponent()->GetPathName());
                else if (Hit.GetActor())Row->SetStringField(TEXT("physical_ground_source"),Hit.GetActor()->GetPathName());
            }
            const FVector Shared=Water->SampleFeatureSurfaceVelocity(Q,
                FVector2D(Raw.VelocityMetersPerSecond.X,Raw.VelocityMetersPerSecond.Y),Raw.DepthMeters);
            Row->SetNumberField(TEXT("shared_along_mps"),Shared.X*D.X+Shared.Y*D.Y);
            Row->SetNumberField(TEXT("shared_across_mps"),Shared.X*L.X+Shared.Y*L.Y);
            FRaftSimWaterSample Support;
            const bool HasSupport=Water->SampleRaftSupportSurfaceAtWorldPosition(P,Support);
            Row->SetBoolField(TEXT("support_available"),HasSupport);
            Row->SetBoolField(TEXT("support_wet"),HasSupport && Support.bWet);
            if (HasSupport)Row->SetNumberField(TEXT("support_surface_world_z_cm"),Support.SurfaceHeightMeters*100.);
            TArray<TSharedPtr<FJsonValue>> Heights;
            for (const auto& Carrier:Carriers)
            {
                FVector Surface,Weights;FIntVector Corners;
                if (!RaftSimWaterShoreline::Sample(FVector2D(P.X,P.Y),0,Carrier.Indices.Num(),
                    Carrier.Vertices,Carrier.Indices,Surface,&Corners,&Weights)) continue;
                auto Height=MakeShared<FJsonObject>();
                Height->SetStringField(TEXT("component"),Carrier.Name);
                Height->SetStringField(TEXT("material_instance"),Carrier.Material);
                Height->SetBoolField(TEXT("material_two_sided"),Carrier.TwoSided);
                Height->SetBoolField(TEXT("submitted_point_inside_component_bounds"),
                    Carrier.Bounds.IsInsideOrOn(Surface));
                const FVector FaceNormal=FVector::CrossProduct(
                    Carrier.Vertices[Corners.Y].Position-Carrier.Vertices[Corners.X].Position,
                    Carrier.Vertices[Corners.Z].Position-Carrier.Vertices[Corners.X].Position).GetSafeNormal();
                Height->SetNumberField(TEXT("world_geometric_cross_normal_z"),FaceNormal.Z);
                // Observe quantized attributes of these exact submitted
                // triangle corners, not the original solver/source colors.
                const FLinearColor Color=
                    Carrier.Vertices[Corners.X].Color.ReinterpretAsLinear()*Weights.X+
                    Carrier.Vertices[Corners.Y].Color.ReinterpretAsLinear()*Weights.Y+
                    Carrier.Vertices[Corners.Z].Color.ReinterpretAsLinear()*Weights.Z;
                Height->SetNumberField(TEXT("submitted_foam_r"),Color.R);
                Height->SetNumberField(TEXT("submitted_depth_g"),Color.G);
                Height->SetNumberField(TEXT("submitted_speed_b"),Color.B);
                Height->SetNumberField(TEXT("submitted_wet_shore_hull_alpha"),Color.A);
                Height->SetBoolField(TEXT("liquid_extinction_parameter_found"),Carrier.HasLiquidExtinction);
                if (Carrier.HasLiquidExtinction)
                {
                    Height->SetNumberField(TEXT("liquid_extinction_parameter_per_m"),Carrier.LiquidExtinctionPerM);
                    Height->SetNumberField(TEXT("no_froth_liquid_before_gpu_hull_mask"),
                        Color.A*(1.-FMath::Exp(-FMath::Max(double(Color.G),0.)*4.*
                            FMath::Max(double(Carrier.LiquidExtinctionPerM),0.))));
                }
                Height->SetNumberField(TEXT("submitted_world_z_cm"),Surface.Z);
                Height->SetNumberField(TEXT("submitted_minus_raw_surface_cm"),Surface.Z-P.Z);
                if (GroundHit)Height->SetNumberField(TEXT("submitted_above_physical_ground_cm"),Surface.Z-GroundZ);
                Heights.Add(MakeShared<FJsonValueObject>(Height));
            }
            Submitted+=!Heights.IsEmpty();
            Row->SetArrayField(TEXT("submitted_macro_surfaces"),Heights);
        }
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    auto Report=MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("schema"),TEXT("raftsim.actual_eddy_clearance.v1"));
    Report->SetStringField(TEXT("scope"),TEXT("Native registered physical-ground samples, raw hydraulic field, raft support and barycentric actual submitted macro triangles at entry time. Component transforms applied. No replacement ground, wet-mask/physics edits, GPU detail/WPO, pixel visibility or full-hull sweep/clearance acceptance."));
    Report->SetNumberField(TEXT("world_seconds"),World->GetTimeSeconds());
    Report->SetNumberField(TEXT("river_vertical_datum_m"),Water->GetRiverVerticalDatumM());
    Report->SetNumberField(TEXT("wet_points"),Wet);
    Report->SetNumberField(TEXT("physical_ground_hits"),GroundHits);
    Report->SetNumberField(TEXT("wet_points_at_or_below_ground"),WetOccluded);
    Report->SetNumberField(TEXT("points_with_submitted_macro_triangle"),Submitted);
    Report->SetArrayField(TEXT("carriers"),CarrierRecords);
    Report->SetArrayField(TEXT("profiles"),Rows);
    Report->SetNumberField(TEXT("diagnostic_elapsed_ms"),(FPlatformTime::Seconds()-Started)*1000.);
    Entry->SetObjectField(TEXT("physical_clearance_audit"),Report);
}
}
