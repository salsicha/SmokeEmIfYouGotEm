#include "RaftSimRaftActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimCrewRoster.h"

// Paddler fatigue. Sustained hard strokes spend a paddler; the force each one
// puts into the water falls toward a floor (an exhausted guest still pulls,
// weakly), and sitting easy brings it back on a slow exponential: most of it
// within a minute or two, the last of it longer. Strokes, high-side holds and
// rescues all cost effort; bracing low recovers at half the resting rate.

namespace
{
float WorkFor(ERaftSimCrewAvatarAction Action)
{
    switch (Action)
    {
    case ERaftSimCrewAvatarAction::ForwardStroke:
    case ERaftSimCrewAvatarAction::TurnLeft:
    case ERaftSimCrewAvatarAction::TurnRight:
        return 1.f;
    case ERaftSimCrewAvatarAction::BackStroke:
        // Back-paddling and braking strokes are the heavier pull.
        return 1.15f;
    case ERaftSimCrewAvatarAction::HighSidePort:
    case ERaftSimCrewAvatarAction::HighSideStarboard:
        return .5f;
    case ERaftSimCrewAvatarAction::ThrowLine:
    case ERaftSimCrewAvatarAction::HaulLine:
    case ERaftSimCrewAvatarAction::ReachRescue:
        return .7f;
    default:
        return 0.f;
    }
}

// A working guide outlasts the guests; stronger swimmers are the fitter ones.
float FitnessFor(FName PassengerId)
{
    if (PassengerId == TEXT("guide")) return 1.4f;
    switch (URaftSimCrewRoster::GetIdentity(PassengerId).SwimAbility)
    {
    case ERaftSimCrewSwimAbility::Strong: return 1.2f;
    case ERaftSimCrewSwimAbility::Weak: return .85f;
    default: return 1.f;
    }
}

FName IdForIndex(int32 Index, int32 Count)
{
    return Index == Count - 1 ? FName(TEXT("guide")) : FName(*FString::Printf(TEXT("paddler_%d"), Index + 1));
}
}

int32 ARaftSimRaftActor::CrewIndexFor(FName PassengerId) const
{
    const ARaftSimCrewAvatarActor* Avatar = FindAvatar(PassengerId);
    return Avatar ? CrewAvatars.IndexOfByKey(Avatar) : INDEX_NONE;
}

float ARaftSimRaftActor::GetCrewStamina(FName PassengerId) const
{
    const int32 Index = CrewIndexFor(PassengerId);
    return CrewStamina.IsValidIndex(Index) ? CrewStamina[Index] : 1.f;
}

void ARaftSimRaftActor::SetCrewStaminaForTesting(FName PassengerId, float Stamina)
{
    const int32 Index = CrewIndexFor(PassengerId);
    if (Index == INDEX_NONE) return;
    while (CrewStamina.Num() < CrewAvatars.Num()) CrewStamina.Add(1.f);
    CrewStamina[Index] = FMath::Clamp(Stamina, 0.f, 1.f);
}

void ARaftSimRaftActor::UpdateCrewStamina(int32 Index, ERaftSimCrewAvatarAction Action, float DeltaSeconds)
{
    if (!CrewAvatars.IsValidIndex(Index) || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    while (CrewStamina.Num() < CrewAvatars.Num()) CrewStamina.Add(1.f);
    float& Stamina = CrewStamina[Index];
    const float Work = WorkFor(Action);
    if (Work > 0.f)
    {
        const float Fitness = FitnessFor(IdForIndex(Index, CrewAvatars.Num()));
        Stamina -= Work * DeltaSeconds / (FMath::Max(CrewEnduranceSeconds, 10.f) * Fitness);
    }
    else
    {
        const float Rate = Action == ERaftSimCrewAvatarAction::Brace ? .5f : 1.f;
        Stamina += (1.f - Stamina) * (1.f - FMath::Exp(-Rate * DeltaSeconds / FMath::Max(CrewRecoverySeconds, 1.f)));
    }
    Stamina = FMath::Clamp(Stamina, 0.f, 1.f);
}

float ARaftSimRaftActor::GetCrewStrokeStrength() const
{
    // Fixtures that never spawned a crew keep their configured paddlers.
    if (CrewAvatars.Num() <= 1) return float(FMath::Max(1, PaddlerCount));
    float Strength = 0.f;
    for (int32 Index = 0; Index + 1 < CrewAvatars.Num(); ++Index)
    {
        const ARaftSimCrewAvatarActor* Avatar = CrewAvatars[Index];
        // Only paddlers in their seats pull; swimmers and anyone still being
        // hauled over the tube add nothing to the stroke.
        if (!Avatar || Avatar->GetAttachParentActor() != this || Avatar == AssistedBoardingAvatar.Get()) continue;
        Strength += StrokeStrengthForStamina(CrewStamina.IsValidIndex(Index) ? CrewStamina[Index] : 1.f);
    }
    return Strength;
}

float ARaftSimRaftActor::GetGuideStrokeStrength() const
{
    // The guide's steering blade loses less than a guest's: technique, not
    // muscle, carries most of a stern draw.
    const float Stamina = GetCrewStamina(TEXT("guide"));
    return .6f + .4f * FMath::Clamp(Stamina, 0.f, 1.f);
}

float ARaftSimRaftActor::GetCrewEnergy() const
{
    float Sum = 0.f;
    int32 Count = 0;
    for (int32 Index = 0; Index + 1 < CrewAvatars.Num(); ++Index)
    {
        const ARaftSimCrewAvatarActor* Avatar = CrewAvatars[Index];
        if (!Avatar || Avatar->GetAttachParentActor() != this) continue;
        Sum += CrewStamina.IsValidIndex(Index) ? CrewStamina[Index] : 1.f;
        ++Count;
    }
    if (Count == 0 && IsSoloOarRig()) return GetCrewStamina(TEXT("guide"));
    return Count > 0 ? Sum / Count : 1.f;
}

FName ARaftSimRaftActor::GetMostTiredPaddler(float& OutStamina) const
{
    FName Tired = NAME_None;
    OutStamina = 1.f;
    for (int32 Index = 0; Index + 1 < CrewAvatars.Num(); ++Index)
    {
        const ARaftSimCrewAvatarActor* Avatar = CrewAvatars[Index];
        if (!Avatar || Avatar->GetAttachParentActor() != this) continue;
        const float Stamina = CrewStamina.IsValidIndex(Index) ? CrewStamina[Index] : 1.f;
        if (Stamina < OutStamina)
        {
            OutStamina = Stamina;
            Tired = IdForIndex(Index, CrewAvatars.Num());
        }
    }
    return Tired;
}
