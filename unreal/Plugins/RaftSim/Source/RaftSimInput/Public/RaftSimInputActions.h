#pragma once

#include "CoreMinimal.h"

namespace RaftSimInputActions
{
static const FName PaddleStroke(TEXT("PaddleStroke"));
static const FName PaddleBrace(TEXT("PaddleBrace"));
static const FName PaddleDraw(TEXT("PaddleDraw"));
static const FName OarLeftStroke(TEXT("OarLeftStroke"));
static const FName OarRightStroke(TEXT("OarRightStroke"));
static const FName OarFeather(TEXT("OarFeather"));
static const FName GuideCommandForwardPaddle(TEXT("GuideCommandForwardPaddle"));
static const FName GuideCommandBackPaddle(TEXT("GuideCommandBackPaddle"));
static const FName GuideCommandLeftPaddle(TEXT("GuideCommandLeftPaddle"));
static const FName GuideCommandRightPaddle(TEXT("GuideCommandRightPaddle"));
static const FName GuideCommandStop(TEXT("GuideCommandStop"));
static const FName HighSide(TEXT("HighSide"));
static const FName CrewLean(TEXT("CrewLean"));
static const FName HoldOn(TEXT("HoldOn"));
static const FName RescueTargetSelect(TEXT("RescueTargetSelect"));
static const FName RescueReachGrab(TEXT("RescueReachGrab"));
static const FName RescueThrowLine(TEXT("RescueThrowLine"));
static const FName ReseatCrew(TEXT("ReseatCrew"));
static const FName GuideCommandPushToTalk(TEXT("GuideCommandPushToTalk"));
static const FName RecenterVR(TEXT("RecenterVR"));
static const FName Pause(TEXT("Pause"));
static const FName CommandWheel(TEXT("CommandWheel"));
static const FName Scout(TEXT("Scout"));
static const FName PhotoMode(TEXT("PhotoMode"));
static const FName AfterActionReview(TEXT("AfterActionReview"));
static const FName ReplayScrub(TEXT("ReplayScrub"));
static const FName DebugOverlayToggle(TEXT("DebugOverlayToggle"));
}
