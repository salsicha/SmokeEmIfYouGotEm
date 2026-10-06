#pragma once
#include "RaftSimGroundContactObservation.h"
#include "RaftSimGroundSourceRegistry.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Engine/StaticMesh.h"

// Opt-in evidence only. Uses the same immutable collision geometry for an
// independent source identity query; never modifies the observed dynamics.
class FRaftSimGroundContactAudit
{
    TWeakObjectPtr<UWorld> World;
    TSharedPtr<FRaftSimGroundSourceRegistry> Sources;
    FString Path;
    TArray<TSharedPtr<FJsonValue>> Rows;
public:
    FRaftSimGroundContactAudit(UWorld* W,TSharedPtr<FRaftSimGroundSourceRegistry> S,FString P)
        : World(W),Sources(MoveTemp(S)),Path(MoveTemp(P)) {}
    void Record(const FRaftSimGroundContactObservation& O)
    {
        if(Rows.Num()>=64 || O.VerticalCorrectionMeters<.005)return;
        auto Row=MakeShared<FJsonObject>();
        const auto Vector=[&](const TCHAR* Key,const FVector& V)
        { Row->SetArrayField(Key,{MakeShared<FJsonValueNumber>(V.X),MakeShared<FJsonValueNumber>(V.Y),MakeShared<FJsonValueNumber>(V.Z)}); };
        const FVector Point=O.PredictedPoseCm.TransformPosition(O.LocalSupportMeters*100.);
        Vector(TEXT("previous_position_cm"),O.PreviousPoseCm.GetLocation());
        Vector(TEXT("predicted_position_cm"),O.PredictedPoseCm.GetLocation());
        Vector(TEXT("previous_support_cm"),O.PreviousPoseCm.TransformPosition(O.LocalSupportMeters*100.));
        Vector(TEXT("predicted_support_cm"),Point);
        Vector(TEXT("local_support_m"),O.LocalSupportMeters);
        Vector(TEXT("velocity_before_projection_mps"),O.VelocityBeforeProjectionMps);
        Vector(TEXT("applied_contact_normal"),O.ContactNormal);
        Row->SetNumberField(TEXT("frame"),double(GFrameCounter));
        Row->SetNumberField(TEXT("world_seconds"),World.IsValid()?World->GetTimeSeconds():-1.);
        Row->SetNumberField(TEXT("substep_seconds"),O.SubstepSeconds);
        Row->SetNumberField(TEXT("radius_m"),O.RadiusMeters);
        Row->SetNumberField(TEXT("ground_z_cm"),O.GroundZCm);
        Row->SetNumberField(TEXT("vertical_correction_m"),O.VerticalCorrectionMeters);
        Row->SetNumberField(TEXT("mass_kg"),O.MassKg);
        Row->SetNumberField(TEXT("projection_gravitational_energy_j"),O.MassKg*9.80665*O.VerticalCorrectionMeters);
        double Ground=0;FVector Normal;FHitResult Hit;
        const bool Found=Sources->SampleGround(Point,Ground,Normal,&Hit);
        Row->SetBoolField(TEXT("physical_ground_resampled"),Found);
        Row->SetBoolField(TEXT("resampled_height_matches_solver_float"),Found && double(float(Ground))==O.GroundZCm);
        Row->SetNumberField(TEXT("resampled_ground_z_cm"),Ground);
        Row->SetNumberField(TEXT("face_index"),Hit.FaceIndex);
        Vector(TEXT("geometric_hit_normal"),Hit.ImpactNormal);
        Row->SetStringField(TEXT("component"),GetPathNameSafe(Hit.GetComponent()));
        const auto* Mesh=Cast<UStaticMeshComponent>(Hit.GetComponent());
        Row->SetStringField(TEXT("mesh"),Mesh?GetPathNameSafe(Mesh->GetStaticMesh()):TEXT("unavailable"));
        Rows.Add(MakeShared<FJsonValueObject>(Row));
        auto Report=MakeShared<FJsonObject>();
        Report->SetStringField(TEXT("schema"),TEXT("raftsim.ground_projection_observation.v1"));
        Report->SetStringField(TEXT("scope"),TEXT("First 64 projections >=5 mm. Exact pre-projection state and resampled original collision identity. Not a complete contact ledger, performance run or traversal acceptance."));
        Report->SetBoolField(TEXT("traversal_accepted"),false);
        Report->SetArrayField(TEXT("observations"),Rows);
        FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));
        if(!FFileHelper::SaveStringToFile(Json,*Path))UE_LOG(LogTemp,Error,TEXT("Ground contact observation save failed: %s"),*Path);
    }
};
