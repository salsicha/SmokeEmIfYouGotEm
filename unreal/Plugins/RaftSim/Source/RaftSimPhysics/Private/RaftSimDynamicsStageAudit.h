#pragma once
#include "CoreMinimal.h"
#include "Engine/World.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Policies/CondensedJsonPrintPolicy.h"

// Bounded, read-only attribution for the recorded Troublemaker turn. It does
// not change forces, integration order, contact modes or the published state.
// Logging perturbs frame timing: these runs can never qualify performance.
struct FRaftSimDynamicsStageAudit
{
    FVector RetainedForce,RetainedTorque,ObstacleForce,ObstacleTorque;
    FVector LinearImpulse,AngularImpulse,PreContactVelocity,PreContactOmega;
    static bool ShouldRecord(const UWorld* World)
    {
#if !UE_BUILD_SHIPPING
        static const bool Enabled=FParse::Param(FCommandLine::Get(),TEXT("RaftSimEphemeralProfile")) &&
            FParse::Param(FCommandLine::Get(),TEXT("RaftSimDynamicsStageAudit"));
        return Enabled && World && World->GetTimeSeconds()>=26. && World->GetTimeSeconds()<34.;
#else
        return false;
#endif
    }
    void Write(double WorldSeconds,double Dt,double Mass,const FVector& Inertia,
        const FVector& BeforeVelocity,const FVector& BeforeOmega,const FVector& AfterVelocity,
        const FVector& AfterOmega,const FVector& Force,const FVector& Torque,
        double AngularDamping,int32 GroundPoints,double Penetration,bool Invalid,bool AlternateContact) const
    {
        auto Row=MakeShared<FJsonObject>();
        // Game-thread-only monotonic evidence sequence exposes dropped or
        // repeated log rows; it never feeds the integrator.
        static uint64 Sequence=0;
        Row->SetNumberField(TEXT("sequence"),double(++Sequence));
        const auto V=[&](const TCHAR* Name,const FVector& Value)
        { Row->SetArrayField(Name,{MakeShared<FJsonValueNumber>(Value.X),MakeShared<FJsonValueNumber>(Value.Y),MakeShared<FJsonValueNumber>(Value.Z)}); };
        Row->SetNumberField(TEXT("world_s"),WorldSeconds);Row->SetNumberField(TEXT("frame"),double(GFrameCounter));
        Row->SetNumberField(TEXT("dt"),Dt);Row->SetNumberField(TEXT("mass_kg"),Mass);
        Row->SetNumberField(TEXT("angular_damping"),AngularDamping);
        Row->SetNumberField(TEXT("ground_points"),GroundPoints);Row->SetNumberField(TEXT("penetration_m"),Penetration);
        Row->SetBoolField(TEXT("invalid_state"),Invalid);Row->SetBoolField(TEXT("alternate_contact"),AlternateContact);
        V(TEXT("inertia"),Inertia);V(TEXT("before_v"),BeforeVelocity);V(TEXT("before_w"),BeforeOmega);
        V(TEXT("retained_force"),RetainedForce);V(TEXT("retained_torque"),RetainedTorque);
        V(TEXT("obstacle_force_cumulative"),ObstacleForce);V(TEXT("obstacle_torque_cumulative"),ObstacleTorque);
        V(TEXT("force"),Force);V(TEXT("torque"),Torque);
        V(TEXT("linear_impulse"),LinearImpulse);V(TEXT("angular_impulse"),AngularImpulse);
        V(TEXT("pre_contact_v"),PreContactVelocity);V(TEXT("pre_contact_w"),PreContactOmega);
        V(TEXT("after_v"),AfterVelocity);V(TEXT("after_w"),AfterOmega);
        FString Json;
        auto Writer=TJsonWriterFactory<TCHAR,TCondensedJsonPrintPolicy<TCHAR>>::Create(&Json);
        FJsonSerializer::Serialize(Row,Writer);
        UE_LOG(LogTemp,Display,TEXT("DynamicsStageAudit %s"),*Json);
    }
};
