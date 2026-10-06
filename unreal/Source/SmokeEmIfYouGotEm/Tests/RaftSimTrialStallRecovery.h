#pragma once
#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

// Opt-in observation-driver policy. Only changes ordinary command decisions;
// never changes stamina, water, pose, velocity, collision or actual progress.
struct FRaftSimTrialStallRecovery
{
    bool Enabled=false;
    double AfterStation=0,StallSeconds=15,RestSeconds=12,Lookahead=45,StartedAt=-1;
    bool Read(const FJsonObject& Trial)
    {
        *this=FRaftSimTrialStallRecovery{};
        if(!Trial.HasField(TEXT("stall_recovery")))return true;
        const TSharedPtr<FJsonObject>* Settings=nullptr;
        if(!Trial.TryGetObjectField(TEXT("stall_recovery"),Settings)||!Settings||!Settings->IsValid())return false;
        const auto& S=**Settings;
        if(!S.TryGetNumberField(TEXT("after_station_m"),AfterStation)||
           !S.TryGetNumberField(TEXT("stall_seconds"),StallSeconds)||
           !S.TryGetNumberField(TEXT("rest_seconds"),RestSeconds)||
           !S.TryGetNumberField(TEXT("lookahead_m"),Lookahead))return false;
        if(!FMath::IsFinite(AfterStation)||AfterStation<0||
           !FMath::IsFinite(StallSeconds)||StallSeconds<1||StallSeconds>60||
           !FMath::IsFinite(RestSeconds)||RestSeconds<=0||RestSeconds>30||
           !FMath::IsFinite(Lookahead)||Lookahead<12||Lookahead>100)return false;
        Enabled=true;return true;
    }
    bool TryStart(double Station,double NoProgressSeconds,double Elapsed,bool SafeToRest)
    {
        if(!Enabled||StartedAt>=0||!SafeToRest||!FMath::IsFinite(Elapsed)||Elapsed<0||
           !FMath::IsFinite(Station)||Station<AfterStation||
           !FMath::IsFinite(NoProgressSeconds)||NoProgressSeconds<StallSeconds)return false;
        StartedAt=Elapsed;return true;
    }
    bool IsResting(double Elapsed) const {return StartedAt>=0&&Elapsed<StartedAt+RestSeconds;}
    bool IsExiting(double Elapsed) const {return StartedAt>=0&&!IsResting(Elapsed);}
};
