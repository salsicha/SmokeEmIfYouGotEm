#include "RaftSimGuideCommands.h"

namespace
{
struct FGuideCommandPhrase
{
    const TCHAR* Phrase;
    ERaftSimGuideCommandIntent Intent;
    const TCHAR* CrewIntent;
};

FString NormalizeForCommandMatch(const FString& InText)
{
    FString Normalized = InText.ToLower();
    for (TCHAR& Character : Normalized)
    {
        if (!FChar::IsAlnum(Character))
        {
            Character = TEXT(' ');
        }
    }
    while (Normalized.Contains(TEXT("  ")))
    {
        Normalized.ReplaceInline(TEXT("  "), TEXT(" "));
    }
    Normalized.TrimStartAndEndInline();
    return FString::Printf(TEXT(" %s "), *Normalized);
}

bool ContainsPhrase(const FString& NormalizedTranscript, const TCHAR* Phrase)
{
    const FString NormalizedPhrase = NormalizeForCommandMatch(Phrase);
    return NormalizedTranscript.Contains(NormalizedPhrase);
}

const FGuideCommandPhrase* FindBestPhraseMatch(const FString& Transcript)
{
    static const FGuideCommandPhrase PhraseTable[] = {
        {TEXT("forward paddle"), ERaftSimGuideCommandIntent::ForwardPaddle, TEXT("crew_forward_paddle")},
        {TEXT("paddle forward"), ERaftSimGuideCommandIntent::ForwardPaddle, TEXT("crew_forward_paddle")},
        {TEXT("all forward"), ERaftSimGuideCommandIntent::ForwardPaddle, TEXT("crew_forward_paddle")},
        {TEXT("forward"), ERaftSimGuideCommandIntent::ForwardPaddle, TEXT("crew_forward_paddle")},
        {TEXT("back paddle"), ERaftSimGuideCommandIntent::BackPaddle, TEXT("crew_back_paddle")},
        {TEXT("back stroke"), ERaftSimGuideCommandIntent::BackPaddle, TEXT("crew_back_paddle")},
        {TEXT("back"), ERaftSimGuideCommandIntent::BackPaddle, TEXT("crew_back_paddle")},
        {TEXT("left side"), ERaftSimGuideCommandIntent::LeftPaddle, TEXT("crew_left_paddle")},
        {TEXT("left forward"), ERaftSimGuideCommandIntent::LeftPaddle, TEXT("crew_left_paddle")},
        {TEXT("left"), ERaftSimGuideCommandIntent::LeftPaddle, TEXT("crew_left_paddle")},
        {TEXT("right side"), ERaftSimGuideCommandIntent::RightPaddle, TEXT("crew_right_paddle")},
        {TEXT("right forward"), ERaftSimGuideCommandIntent::RightPaddle, TEXT("crew_right_paddle")},
        {TEXT("right"), ERaftSimGuideCommandIntent::RightPaddle, TEXT("crew_right_paddle")},
        {TEXT("stop"), ERaftSimGuideCommandIntent::Stop, TEXT("crew_stop")},
        {TEXT("rest"), ERaftSimGuideCommandIntent::Stop, TEXT("crew_stop")},
        {TEXT("easy"), ERaftSimGuideCommandIntent::Stop, TEXT("crew_stop")},
        {TEXT("brace"), ERaftSimGuideCommandIntent::Brace, TEXT("crew_brace")},
        {TEXT("hold on"), ERaftSimGuideCommandIntent::HoldOn, TEXT("crew_hold_on")},
        {TEXT("get down"), ERaftSimGuideCommandIntent::HoldOn, TEXT("crew_hold_on")},
        {TEXT("high side"), ERaftSimGuideCommandIntent::HighSide, TEXT("crew_high_side")},
        {TEXT("highside"), ERaftSimGuideCommandIntent::HighSide, TEXT("crew_high_side")},
        {TEXT("lean left"), ERaftSimGuideCommandIntent::LeanLeft, TEXT("crew_lean_left")},
        {TEXT("left lean"), ERaftSimGuideCommandIntent::LeanLeft, TEXT("crew_lean_left")},
        {TEXT("lean right"), ERaftSimGuideCommandIntent::LeanRight, TEXT("crew_lean_right")},
        {TEXT("right lean"), ERaftSimGuideCommandIntent::LeanRight, TEXT("crew_lean_right")},
        {TEXT("rescue"), ERaftSimGuideCommandIntent::Rescue, TEXT("crew_rescue")},
        {TEXT("swimmer"), ERaftSimGuideCommandIntent::Rescue, TEXT("crew_rescue")},
        {TEXT("rope"), ERaftSimGuideCommandIntent::Rescue, TEXT("crew_rescue")},
        {TEXT("recover"), ERaftSimGuideCommandIntent::Recovery, TEXT("crew_recovery")},
        {TEXT("reset"), ERaftSimGuideCommandIntent::Recovery, TEXT("crew_recovery")},
        {TEXT("back in"), ERaftSimGuideCommandIntent::Recovery, TEXT("crew_recovery")}
    };

    const FString NormalizedTranscript = NormalizeForCommandMatch(Transcript);
    const FGuideCommandPhrase* BestMatch = nullptr;
    int32 BestPhraseLength = INDEX_NONE;
    for (const FGuideCommandPhrase& Candidate : PhraseTable)
    {
        if (ContainsPhrase(NormalizedTranscript, Candidate.Phrase))
        {
            const int32 PhraseLength = FCString::Strlen(Candidate.Phrase);
            if (PhraseLength > BestPhraseLength)
            {
                BestMatch = &Candidate;
                BestPhraseLength = PhraseLength;
            }
        }
    }
    return BestMatch;
}
}

FRaftSimGuideCommand URaftSimGuideCommandParser::ParseTranscript(
    const FString& Transcript,
    float RecognitionConfidence
) const
{
    FRaftSimGuideCommand Command;
    Command.SourcePhrase = Transcript;
    Command.Confidence = RecognitionConfidence;

    if (const FGuideCommandPhrase* Match = FindBestPhraseMatch(Transcript))
    {
        Command.Intent = Match->Intent;
        Command.DeterministicCrewIntent = FName(Match->CrewIntent);
        Command.bMatchedGrammar = true;
    }

    return Command;
}
