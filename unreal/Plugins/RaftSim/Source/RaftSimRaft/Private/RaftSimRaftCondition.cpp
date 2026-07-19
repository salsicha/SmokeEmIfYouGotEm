#include "RaftSimRaftCondition.h"

namespace
{
ERaftSimRaftDamageState Classify(float Integrity, float Pressure)
{
    if (Integrity <= 0.28f || Pressure <= 0.42f)
    {
        return ERaftSimRaftDamageState::Critical;
    }
    if (Integrity <= 0.52f || Pressure <= 0.70f)
    {
        return ERaftSimRaftDamageState::Punctured;
    }
    if (Integrity <= 0.78f)
    {
        return ERaftSimRaftDamageState::Abraded;
    }
    if (Integrity < 0.97f)
    {
        return ERaftSimRaftDamageState::Creased;
    }
    return ERaftSimRaftDamageState::Intact;
}
}

FRaftSimRaftConditionState URaftSimRaftConditionLibrary::AdvanceCondition(
    const FRaftSimRaftConditionState& Current,
    const FRaftSimRaftContactExposure& Exposure)
{
    FRaftSimRaftConditionState Next = Current;
    const float Dt = FMath::Clamp(Exposure.DeltaSeconds, 0.0f, 0.25f);
    const bool bWrapping = Exposure.WrappingContactCount >= 3;
    const bool bPinned = Exposure.PinnedObstacleCount > 0;
    if (bWrapping && !Current.bWasWrapping)
    {
        ++Next.WrapEventCount;
    }
    if (bPinned && !Current.bWasPinned)
    {
        ++Next.PinEventCount;
    }
    Next.bWasWrapping = bWrapping;
    Next.bWasPinned = bPinned;

    const float SevereIndent = FMath::Max(Exposure.MaximumIndentationM - 0.075f, 0.0f);
    const float ContactDensity = FMath::Clamp(Exposure.ContactCount / 6.0f, 0.0f, 1.5f);
    const float WrapSeverity = bWrapping ? 0.55f : 0.0f;
    const float PinSeverity = bPinned ? 1.15f : 0.0f;
    const float SurfSeverity = FMath::Clamp(Exposure.RetainedWaterMassKg / 450.0f, 0.0f, 1.0f) * 0.12f;
    const float Severity = SevereIndent * 5.5f + ContactDensity * SevereIndent +
        WrapSeverity + PinSeverity + SurfSeverity;
    if (Severity > 0.0f)
    {
        Next.SevereContactExposureSeconds += Dt;
        Next.FabricIntegrity = FMath::Clamp(
            Current.FabricIntegrity - Severity * Dt * 0.028f, 0.0f, 1.0f);
        Next.PermanentCreaseAmplitudeM = FMath::Clamp(
            FMath::Max(Current.PermanentCreaseAmplitudeM, SevereIndent * 0.16f) +
                (bWrapping ? Dt * 0.0004f : 0.0f),
            0.0f,
            0.022f);
    }

    // Punctures require sustained severe deformation or a true pin; routine
    // rock rubs leave wear without magically deflating the raft.
    const bool bPunctureExposure =
        (bPinned && Exposure.MaximumIndentationM >= 0.13f) ||
        (Next.SevereContactExposureSeconds >= 8.0f && Exposure.MaximumIndentationM >= 0.10f);
    if (bPunctureExposure)
    {
        const float LeakRatePerSecond = 0.016f + 0.014f * FMath::Clamp(
            Exposure.MaximumIndentationM / 0.28f, 0.0f, 1.0f);
        Next.PressureFraction = FMath::Clamp(
            Current.PressureFraction - LeakRatePerSecond * Dt, 0.25f, 1.0f);
    }
    Next.DamageState = Classify(Next.FabricIntegrity, Next.PressureFraction);
    return Next;
}

FRaftSimRaftConditionState URaftSimRaftConditionLibrary::ApplyCheckpointRepair(
    const FRaftSimRaftConditionState& Current)
{
    FRaftSimRaftConditionState Repaired = Current;
    Repaired.FabricIntegrity = FMath::Max(Current.FabricIntegrity, 0.82f);
    Repaired.PressureFraction = 1.0f;
    Repaired.SevereContactExposureSeconds = 0.0f;
    Repaired.bWasWrapping = false;
    Repaired.bWasPinned = false;
    Repaired.DamageState = Classify(Repaired.FabricIntegrity, Repaired.PressureFraction);
    return Repaired;
}
