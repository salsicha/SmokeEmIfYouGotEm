#include "RaftSimGuideCommands.h"

namespace
{
bool ContainsAny(const FString& LowerTranscript, std::initializer_list<const TCHAR*> Phrases)
{
    for (const TCHAR* Phrase : Phrases)
    {
        if (LowerTranscript.Contains(Phrase))
        {
            return true;
        }
    }
    return false;
}
}

FRaftSimGuideCommand URaftSimGuideCommandParser::ParseTranscript(
    const FString& Transcript,
    float RecognitionConfidence
) const
{
    const FString Lower = Transcript.ToLower();
    FRaftSimGuideCommand Command;
    Command.SourcePhrase = Transcript;
    Command.Confidence = RecognitionConfidence;

    if (ContainsAny(Lower, {TEXT("forward"), TEXT("forward paddle"), TEXT("all forward"), TEXT("paddle forward")}))
    {
        Command.Intent = ERaftSimGuideCommandIntent::ForwardPaddle;
    }
    else if (ContainsAny(Lower, {TEXT("back"), TEXT("back paddle"), TEXT("back stroke")}))
    {
        Command.Intent = ERaftSimGuideCommandIntent::BackPaddle;
    }
    else if (ContainsAny(Lower, {TEXT("left"), TEXT("left side")}))
    {
        Command.Intent = ERaftSimGuideCommandIntent::LeftPaddle;
    }
    else if (ContainsAny(Lower, {TEXT("right"), TEXT("right side")}))
    {
        Command.Intent = ERaftSimGuideCommandIntent::RightPaddle;
    }
    else if (ContainsAny(Lower, {TEXT("stop"), TEXT("rest"), TEXT("easy")}))
    {
        Command.Intent = ERaftSimGuideCommandIntent::Stop;
    }
    else if (ContainsAny(Lower, {TEXT("brace")}))
    {
        Command.Intent = ERaftSimGuideCommandIntent::Brace;
    }
    else if (ContainsAny(Lower, {TEXT("hold on"), TEXT("get down")}))
    {
        Command.Intent = ERaftSimGuideCommandIntent::HoldOn;
    }
    else if (ContainsAny(Lower, {TEXT("high side"), TEXT("highside")}))
    {
        Command.Intent = ERaftSimGuideCommandIntent::HighSide;
    }
    else if (ContainsAny(Lower, {TEXT("rescue"), TEXT("swimmer"), TEXT("rope")}))
    {
        Command.Intent = ERaftSimGuideCommandIntent::Rescue;
    }
    else if (ContainsAny(Lower, {TEXT("recover"), TEXT("reset"), TEXT("back in")}))
    {
        Command.Intent = ERaftSimGuideCommandIntent::Recovery;
    }

    return Command;
}
