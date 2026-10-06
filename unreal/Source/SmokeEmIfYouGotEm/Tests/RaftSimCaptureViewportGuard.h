#pragma once

#include "CoreMinimal.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Misc/AutomationTest.h"
#include "UnrealClient.h"
#include "Widgets/SWindow.h"

#if WITH_AUTOMATION_TESTS
// PIE inherits a per-user window size that UE writes back after each session,
// and it can collapse to a 0-px viewport that renders and captures nothing.
// Give the PIE window a real size before any rendered capture.
class FRaftSimEnsureCaptureViewport final : public IAutomationLatentCommand
{
public:
    explicit FRaftSimEnsureCaptureViewport(FAutomationTestBase* InTest) : Test(InTest) {}

    virtual bool Update() override
    {
        UGameViewportClient* Client = nullptr;
        for (const FWorldContext& Context : GEngine->GetWorldContexts())
        {
            if (Context.World() && Context.GameViewport &&
                (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
            {
                Client = Context.GameViewport;
                break;
            }
        }
        const FIntPoint Size = Client && Client->Viewport ? Client->Viewport->GetSizeXY() : FIntPoint::ZeroValue;
        if (Size.X >= 640 && Size.Y >= 360) return true;
        const double Now = FPlatformTime::Seconds();
        if (StartSeconds <= 0.0)
        {
            StartSeconds = Now;
            if (Client)
            {
                if (const TSharedPtr<SWindow> Window = Client->GetWindow())
                {
                    Window->Resize(FVector2D(1280.0, 720.0));
                }
            }
            return false;
        }
        if (Now - StartSeconds > 5.0)
        {
            Test->AddError(FString::Printf(TEXT("PIE game viewport is %dx%d (need >= 640x360); reset "
                "LevelEditorPlaySettings NewWindowWidth/NewWindowHeight"), Size.X, Size.Y));
            return true;
        }
        return false;
    }

private:
    FAutomationTestBase* Test = nullptr;
    double StartSeconds = 0.0;
};
#endif
