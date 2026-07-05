#include "RaftSimVoiceCommandRouter.h"

FRaftSimVoiceCommandRoute URaftSimVoiceCommandRouter::RouteRecognizedSpeech(
    const FRaftSimRecognizedSpeech& RecognizedSpeech,
    ERaftSimVoiceGameplayMode GameplayMode,
    const FRaftSimVoiceCommandSafetySettings& Settings,
    int32 PhysicsFrame,
    FName ConversationStateId
) const
{
    if (!Parser)
    {
        URaftSimVoiceCommandRouter* MutableThis = const_cast<URaftSimVoiceCommandRouter*>(this);
        MutableThis->Parser = NewObject<URaftSimGuideCommandParser>(MutableThis);
    }

    FRaftSimVoiceCommandRoute Route;
    Route.Command = Parser->ParseTranscript(RecognizedSpeech.Transcript, RecognizedSpeech.Confidence);
    Route.DeterministicCrewIntent = Route.Command.DeterministicCrewIntent;

    Route.Telemetry.PhysicsFrame = PhysicsFrame;
    Route.Telemetry.RecognizedPhrase = RecognizedSpeech.Transcript;
    Route.Telemetry.Intent = Route.Command.Intent;
    Route.Telemetry.DeterministicCrewIntent = Route.DeterministicCrewIntent;
    Route.Telemetry.Confidence = RecognizedSpeech.Confidence;
    Route.Telemetry.CommandLatencyMs = RecognizedSpeech.LatencyMs;
    Route.Telemetry.CrewResponseId = Route.DeterministicCrewIntent;
    Route.Telemetry.ConversationStateId = ConversationStateId;

    if (GameplayMode == ERaftSimVoiceGameplayMode::RowingOarRig)
    {
        Route.Outcome = ERaftSimCommandOutcome::RejectedUnsafe;
    }
    else if (Settings.ActivationMode == ERaftSimVoiceActivationMode::DisabledManualOnly)
    {
        Route.Outcome = ERaftSimCommandOutcome::RejectedUnsafe;
    }
    else if (RecognizedSpeech.LatencyMs > Settings.MaxCommandLatencyMs)
    {
        Route.Outcome = ERaftSimCommandOutcome::TimedOut;
    }
    else if (!Route.Command.bMatchedGrammar || Route.Command.Intent == ERaftSimGuideCommandIntent::None)
    {
        Route.Outcome = ERaftSimCommandOutcome::IgnoredLowConfidence;
    }
    else if (RecognizedSpeech.Confidence < Settings.ConfirmConfidenceThreshold)
    {
        Route.Outcome = ERaftSimCommandOutcome::IgnoredLowConfidence;
    }
    else if (RecognizedSpeech.Confidence < Settings.ExecuteConfidenceThreshold)
    {
        Route.Outcome = ERaftSimCommandOutcome::ConfirmationRequested;
        Route.bRequiresConfirmation = true;
    }
    else
    {
        Route.Outcome = ERaftSimCommandOutcome::Executed;
        Route.bShouldExecute = true;
    }

    Route.Telemetry.Outcome = Route.Outcome;
    return Route;
}
