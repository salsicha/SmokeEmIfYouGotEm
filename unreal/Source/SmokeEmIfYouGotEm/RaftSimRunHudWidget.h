#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"

#include "RaftSimRunHudWidget.generated.h"

class UTextBlock;
class ARaftSimRunManager;

/**
 * In-run HUD (P3 HUD v1): run state + timer, speed, crew/swimmer status, score,
 * and a subtitle line. Programmatic UMG so it stays C++-diffable.
 */
UCLASS()
class SMOKEEMIFYOUGOTEM_API URaftSimRunHudWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;

    /** Show a transient subtitle (command callouts, crew barks). */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|HUD")
    void ShowSubtitle(const FText& Line, float DurationSeconds = 3.0f);

protected:
    UPROPERTY()
    TObjectPtr<UTextBlock> StatusText;

    UPROPERTY()
    TObjectPtr<UTextBlock> ScoreText;

    UPROPERTY()
    TObjectPtr<UTextBlock> SubtitleText;

    UPROPERTY()
    TObjectPtr<ARaftSimRunManager> RunManager;

    float SubtitleRemaining = 0.0f;
};
