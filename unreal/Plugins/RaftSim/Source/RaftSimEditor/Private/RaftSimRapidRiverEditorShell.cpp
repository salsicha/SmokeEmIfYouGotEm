#include "RaftSimRapidRiverEditorShell.h"

void URaftSimRapidRiverEditorShellViewModel::Configure(URaftSimRapidRiverEditorShellConfig* InConfig)
{
    Config = InConfig;
    SelectedAnnotationId = NAME_None;

    if (Config && !Config->SampleAnnotations.IsEmpty())
    {
        SelectedAnnotationId = Config->SampleAnnotations[0].AnnotationId;
    }
}

bool URaftSimRapidRiverEditorShellViewModel::SelectAnnotation(FName AnnotationId)
{
    if (FindAnnotation(AnnotationId))
    {
        SelectedAnnotationId = AnnotationId;
        return true;
    }

    return false;
}

bool URaftSimRapidRiverEditorShellViewModel::CanExport() const
{
    return GetExportBlockers().IsEmpty();
}

TArray<FRaftSimToolValidationMessage> URaftSimRapidRiverEditorShellViewModel::GetExportBlockers() const
{
    TArray<FRaftSimToolValidationMessage> Blockers;

    if (!Config)
    {
        FRaftSimToolValidationMessage MissingConfig;
        MissingConfig.MessageId = TEXT("missing_config");
        MissingConfig.Severity = ERaftSimToolValidationSeverity::Blocking;
        MissingConfig.Summary = NSLOCTEXT(
            "RaftSimRapidRiverEditorShell",
            "MissingConfig",
            "Rapid/River Editor shell is not configured.");
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

    for (const FRaftSimRiverEditorShellAnnotation& Annotation : Config->SampleAnnotations)
    {
        if (!Annotation.bRightsCleared || Annotation.ExpectedOutcomes.IsEmpty() || !Annotation.bHasValidationOverlay)
        {
            FRaftSimToolValidationMessage AnnotationBlocker;
            AnnotationBlocker.MessageId = Annotation.AnnotationId;
            AnnotationBlocker.Severity = ERaftSimToolValidationSeverity::Blocking;
            AnnotationBlocker.Summary = FText::Format(
                NSLOCTEXT(
                    "RaftSimRapidRiverEditorShell",
                    "AnnotationBlocked",
                    "{0} is missing rights clearance, expected outcomes, or validation overlay evidence."),
                Annotation.DisplayName);
            AnnotationBlocker.SourcePath = Config->SouthForkEditorPassManifest;
            AnnotationBlocker.bBlocksExport = true;
            Blockers.Add(AnnotationBlocker);
        }
    }

    return Blockers;
}

const FRaftSimRiverEditorShellAnnotation* URaftSimRapidRiverEditorShellViewModel::FindAnnotation(FName AnnotationId) const
{
    if (!Config)
    {
        return nullptr;
    }

    return Config->SampleAnnotations.FindByPredicate(
        [AnnotationId](const FRaftSimRiverEditorShellAnnotation& Annotation)
        {
            return Annotation.AnnotationId == AnnotationId;
        });
}
