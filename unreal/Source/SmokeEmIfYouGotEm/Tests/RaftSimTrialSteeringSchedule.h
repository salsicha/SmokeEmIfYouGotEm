#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

// Observation-driver input timing only. Never a water, boat or gate force.
struct FRaftSimTrialSteeringSchedule
{
    bool Disabled=false;
    double Start=-DBL_MAX,End=DBL_MAX;
    TOptional<double> MistakeTrigger;
    TArray<FVector2D> Blackouts;

    bool Read(const FJsonObject& Trial)
    {
        Disabled=false;Start=-DBL_MAX;End=DBL_MAX;Blackouts.Reset();MistakeTrigger.Reset();
        Trial.TryGetBoolField(TEXT("disable_steering"),Disabled);
        Trial.TryGetNumberField(TEXT("steering_start_m"),Start);
        Trial.TryGetNumberField(TEXT("steering_end_m"),End);
        if(!FMath::IsFinite(Start)||!FMath::IsFinite(End)||Start>End)return false;
        if(Trial.HasField(TEXT("mistake_trigger_m")))
        {
            double Trigger=0.;
            if(!Trial.TryGetNumberField(TEXT("mistake_trigger_m"),Trigger)||!FMath::IsFinite(Trigger))return false;
            MistakeTrigger=Trigger;
        }
        if(!Trial.HasField(TEXT("steering_blackouts")))return true;
        const TArray<TSharedPtr<FJsonValue>>* Values=nullptr;
        if(!Trial.TryGetArrayField(TEXT("steering_blackouts"),Values))return false;
        for(const auto& Value:*Values)
        {
            const TArray<TSharedPtr<FJsonValue>>* Pair=nullptr;
            if(!Value.IsValid()||!Value->TryGetArray(Pair)||Pair->Num()!=2)return false;
            double A=0,B=0;
            if(!(*Pair)[0]->TryGetNumber(A)||!(*Pair)[1]->TryGetNumber(B)||
                !FMath::IsFinite(A)||!FMath::IsFinite(B)||A>=B)return false;
            Blackouts.Emplace(A,B);
        }
        return true;
    }

    bool Suppressed(double Station) const
    {
        if(Disabled||Station<Start||Station>=End)return true;
        for(const auto& Range:Blackouts)if(Station>=Range.X&&Station<Range.Y)return true;
        return false;
    }
};
