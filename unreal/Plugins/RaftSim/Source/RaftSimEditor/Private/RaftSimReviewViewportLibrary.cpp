#include "RaftSimReviewViewportLibrary.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Slate/SceneViewport.h"

bool URaftSimReviewViewportLibrary::SetOffscreenPlayViewportSize(
    UObject* WorldContext, int32 Width, int32 Height)
{
    // This is a real render-target resize, not screenshot resampling. Scope it
    // to offscreen PIE so automation cannot disturb a user's visible session.
    if (!IsInGameThread() || !GEngine || Width < 320 || Width > 3840 || Height < 180 || Height > 2160 ||
        !FParse::Param(FCommandLine::Get(), TEXT("RenderOffscreen"))) return false;
    UWorld* World = GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull);
    if (!World || World->WorldType != EWorldType::PIE || !World->GetGameInstance()) return false;
    UGameViewportClient* Client = World->GetGameInstance()->GetGameViewportClient();
    FSceneViewport* Viewport = Client ? Client->GetGameViewport() : nullptr;
    if (!Viewport) return false;
    Viewport->SetFixedViewportSize(Width, Height);
    const FIntPoint Actual = Viewport->GetSizeXY();
    UE_LOG(LogTemp, Display, TEXT("RaftSim offscreen PIE viewport: requested=%dx%d actual=%dx%d"),
        Width, Height, Actual.X, Actual.Y);
    return Actual == FIntPoint(Width, Height);
}
