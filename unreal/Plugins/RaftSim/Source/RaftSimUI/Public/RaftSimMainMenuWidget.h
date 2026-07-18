#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"

#include "RaftSimMainMenuWidget.generated.h"

class UButton;
class UTextBlock;
class UVerticalBox;

/**
 * Programmatic main menu (no Blueprint asset required): title plus
 * Enter Test Tank / Settings / Quit. A Blueprint skin can subclass this later;
 * all behavior stays in C++ so it is diffable and testable.
 */
UCLASS()
class RAFTSIMUI_API URaftSimMainMenuWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual void NativeConstruct() override;

protected:
    UFUNCTION()
    void HandleEnterTestTank();

    UFUNCTION()
    void HandleToggleSettings();

    UFUNCTION()
    void HandleQuit();

    UButton* MakeMenuButton(UVerticalBox* Parent, const FText& Label, FName ClickHandlerName);

    UPROPERTY()
    TObjectPtr<UTextBlock> SettingsSummaryText;

    /** Map opened by Enter Test Tank. */
    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Frontend")
    FName TestTankLevelName = TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank");
};
