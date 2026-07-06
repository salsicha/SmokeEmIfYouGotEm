#include "RaftSimFeatureTuningEditorShell.h"

#include "Math/UnrealMathUtility.h"

void URaftSimFeatureTuningEditorShellViewModel::Configure(URaftSimFeatureTuningEditorShellConfig* InConfig)
{
    Config = InConfig;
    CurrentValues.Reset();
    SelectedControlId = NAME_None;

    if (!Config)
    {
        return;
    }

    for (const FRaftSimFeatureTuningShellControl& Control : Config->Controls)
    {
        CurrentValues.Add(Control.ControlId, Control.DefaultValue);
    }

    if (!Config->Controls.IsEmpty())
    {
        SelectedControlId = Config->Controls[0].ControlId;
    }
}

bool URaftSimFeatureTuningEditorShellViewModel::SelectControl(FName ControlId)
{
    if (FindControl(ControlId))
    {
        SelectedControlId = ControlId;
        return true;
    }

    return false;
}

bool URaftSimFeatureTuningEditorShellViewModel::SetControlValue(FName ControlId, float NewValue)
{
    if (const FRaftSimFeatureTuningShellControl* Control = FindControl(ControlId))
    {
        CurrentValues.Add(ControlId, FMath::Clamp(NewValue, Control->MinValue, Control->MaxValue));
        SelectedControlId = ControlId;
        return true;
    }

    return false;
}

float URaftSimFeatureTuningEditorShellViewModel::GetControlValue(FName ControlId) const
{
    if (const float* CurrentValue = CurrentValues.Find(ControlId))
    {
        return *CurrentValue;
    }

    if (const FRaftSimFeatureTuningShellControl* Control = FindControl(ControlId))
    {
        return Control->DefaultValue;
    }

    return 0.0f;
}

bool URaftSimFeatureTuningEditorShellViewModel::HasControlChanged(FName ControlId) const
{
    if (const FRaftSimFeatureTuningShellControl* Control = FindControl(ControlId))
    {
        return !FMath::IsNearlyEqual(GetControlValue(ControlId), Control->DefaultValue);
    }

    return false;
}

bool URaftSimFeatureTuningEditorShellViewModel::CanExport() const
{
    return GetExportBlockers().IsEmpty();
}

TArray<FRaftSimToolValidationMessage> URaftSimFeatureTuningEditorShellViewModel::GetExportBlockers() const
{
    TArray<FRaftSimToolValidationMessage> Blockers;

    if (!Config)
    {
        FRaftSimToolValidationMessage MissingConfig;
        MissingConfig.MessageId = TEXT("missing_config");
        MissingConfig.Severity = ERaftSimToolValidationSeverity::Blocking;
        MissingConfig.Summary = NSLOCTEXT(
            "RaftSimFeatureTuningEditorShell",
            "MissingConfig",
            "Feature Tuning Editor shell is not configured.");
        MissingConfig.bBlocksExport = true;
        Blockers.Add(MissingConfig);
        return Blockers;
    }

    for (const FRaftSimToolValidationMessage& Message : Config->ValidationMessages)
    {
        if (Message.bBlocksExport || Message.Severity == ERaftSimToolValidationSeverity::Blocking)
        {
            Blockers.Add(Message);
        }
    }

    for (const FRaftSimFeatureTuningShellControl& Control : Config->Controls)
    {
        const bool bChanged = HasControlChanged(Control.ControlId);
        const bool bPresentationOnly =
            Control.Domain == ERaftSimRiverFeatureTuningDomain::VisualOnly ||
            Control.Domain == ERaftSimRiverFeatureTuningDomain::AudioOnly;

        if (Control.MinValue > Control.MaxValue || GetControlValue(Control.ControlId) < Control.MinValue ||
            GetControlValue(Control.ControlId) > Control.MaxValue)
        {
            FRaftSimToolValidationMessage RangeBlocker;
            RangeBlocker.MessageId = Control.ControlId;
            RangeBlocker.Severity = ERaftSimToolValidationSeverity::Blocking;
            RangeBlocker.Summary = FText::Format(
                NSLOCTEXT(
                    "RaftSimFeatureTuningEditorShell",
                    "ControlOutOfRange",
                    "{0} has an invalid or out-of-range tuning value."),
                Control.DisplayName);
            RangeBlocker.SourcePath = Config->FeatureTuningManifest;
            RangeBlocker.bBlocksExport = true;
            Blockers.Add(RangeBlocker);
        }

        if (bPresentationOnly && (Control.bAffectsSolverState || Control.bAffectsRaftCoupling))
        {
            FRaftSimToolValidationMessage PresentationBlocker;
            PresentationBlocker.MessageId = Control.ControlId;
            PresentationBlocker.Severity = ERaftSimToolValidationSeverity::Blocking;
            PresentationBlocker.Summary = FText::Format(
                NSLOCTEXT(
                    "RaftSimFeatureTuningEditorShell",
                    "PresentationAffectsPhysics",
                    "{0} is marked visual/audio-only but can affect solver or raft state."),
                Control.DisplayName);
            PresentationBlocker.SourcePath = Config->FeatureTuningManifest;
            PresentationBlocker.bBlocksExport = true;
            Blockers.Add(PresentationBlocker);
        }

        if (bChanged && Control.bManifestRecordingRequired && !Control.bHasManifestRecord)
        {
            FRaftSimToolValidationMessage ManifestBlocker;
            ManifestBlocker.MessageId = Control.ControlId;
            ManifestBlocker.Severity = ERaftSimToolValidationSeverity::Blocking;
            ManifestBlocker.Summary = FText::Format(
                NSLOCTEXT(
                    "RaftSimFeatureTuningEditorShell",
                    "MissingManifestRecord",
                    "{0} was changed without a manifest record."),
                Control.DisplayName);
            ManifestBlocker.SourcePath = Config->FeatureTuningManifest;
            ManifestBlocker.bBlocksExport = true;
            Blockers.Add(ManifestBlocker);
        }

        if (bChanged && (Control.bAffectsSolverState || Control.bAffectsRaftCoupling) &&
            (Control.bGeoClawComparisonRequired || Control.bConservationGuardRequired ||
             Control.bCanHideConservationFailures))
        {
            FRaftSimToolValidationMessage PhysicsBlocker;
            PhysicsBlocker.MessageId = Control.ControlId;
            PhysicsBlocker.Severity = ERaftSimToolValidationSeverity::Blocking;
            PhysicsBlocker.Summary = FText::Format(
                NSLOCTEXT(
                    "RaftSimFeatureTuningEditorShell",
                    "PhysicsRetuneBlocked",
                    "{0} changes physics-facing behavior and must pass GeoClaw comparison and conservation guards before export."),
                Control.DisplayName);
            PhysicsBlocker.SourcePath = Config->FeatureTuningManifest;
            PhysicsBlocker.bBlocksExport = true;
            Blockers.Add(PhysicsBlocker);
        }
    }

    return Blockers;
}

const FRaftSimFeatureTuningShellControl* URaftSimFeatureTuningEditorShellViewModel::FindControl(FName ControlId) const
{
    if (!Config)
    {
        return nullptr;
    }

    return Config->Controls.FindByPredicate(
        [ControlId](const FRaftSimFeatureTuningShellControl& Control)
        {
            return Control.ControlId == ControlId;
        });
}
