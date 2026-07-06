#include "RaftSimToolValidationActions.h"

void URaftSimToolValidationActionRunner::Configure(URaftSimToolValidationActionRegistry* InRegistry)
{
    Registry = InRegistry;
}

FRaftSimToolValidationActionResult URaftSimToolValidationActionRunner::RunAction(FName ActionId)
{
    FRaftSimToolValidationActionResult Result;
    Result.ActionId = ActionId;

    const FRaftSimToolValidationAction* Action = FindAction(ActionId);
    if (!Action)
    {
        Result.Message.MessageId = TEXT("unknown_validation_action");
        Result.Message.Severity = ERaftSimToolValidationSeverity::Blocking;
        Result.Message.Summary = NSLOCTEXT(
            "RaftSimToolValidationActions",
            "UnknownAction",
            "Validation action is not registered.");
        Result.Message.bBlocksExport = true;
        return Result;
    }

    if (Action->SourceManifest.IsEmpty() && Action->ReportPath.IsEmpty())
    {
        Result.Message.MessageId = TEXT("missing_action_target");
        Result.Message.Severity = ERaftSimToolValidationSeverity::Blocking;
        Result.Message.Summary = NSLOCTEXT(
            "RaftSimToolValidationActions",
            "MissingActionTarget",
            "Validation action is missing a source manifest or report target.");
        Result.Message.bBlocksExport = true;
        return Result;
    }

    Result.bAccepted = true;
    Result.Message.MessageId = Action->ActionId;
    Result.Message.Severity = Action->bBlocksPromotion ? ERaftSimToolValidationSeverity::Warning : ERaftSimToolValidationSeverity::Info;
    Result.Message.Summary = FText::Format(
        NSLOCTEXT(
            "RaftSimToolValidationActions",
            "ActionAccepted",
            "{0} is registered and ready to be wired to an editor button."),
        Action->DisplayName);
    Result.Message.SourcePath = !Action->ReportPath.IsEmpty() ? Action->ReportPath : Action->SourceManifest;
    Result.Message.bBlocksExport = false;
    return Result;
}

bool URaftSimToolValidationActionRunner::CanRunAction(FName ActionId) const
{
    const FRaftSimToolValidationAction* Action = FindAction(ActionId);
    return Action && (!Action->SourceManifest.IsEmpty() || !Action->ReportPath.IsEmpty());
}

const FRaftSimToolValidationAction* URaftSimToolValidationActionRunner::FindAction(FName ActionId) const
{
    if (!Registry)
    {
        return nullptr;
    }

    return Registry->Actions.FindByPredicate(
        [ActionId](const FRaftSimToolValidationAction& Action)
        {
            return Action.ActionId == ActionId;
        });
}
