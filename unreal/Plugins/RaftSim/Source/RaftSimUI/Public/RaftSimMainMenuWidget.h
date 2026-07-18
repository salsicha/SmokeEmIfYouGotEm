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
    void HandleRunSouthFork();
    UFUNCTION()
    void HandleRunColorado();
    UFUNCTION()
    void HandleRunPacuare();
    UFUNCTION()
    void HandleRunFutaleufu();
    UFUNCTION()
    void HandleRunChilko();

    UFUNCTION()
    void HandleToggleSettings();

    UFUNCTION()
    void HandleQuit();

    void OpenRiverLevel(FName LevelName);
    UButton* MakeMenuButton(UVerticalBox* Parent, const FText& Label, FName ClickHandlerName);

    UPROPERTY()
    TObjectPtr<UTextBlock> SettingsSummaryText;

    /** Map opened by Training Eddy. */
    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Frontend")
    FName TestTankLevelName = TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank");

    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Frontend")
    FName SouthForkLevelName = TEXT("/Game/RaftSim/Maps/L_Troublemaker");
    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Frontend")
    FName ColoradoLevelName = TEXT("/Game/RaftSim/Maps/L_Hance");
    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Frontend")
    FName PacuareLevelName = TEXT("/Game/RaftSim/Maps/L_UpperHuacas");
    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Frontend")
    FName FutaleufuLevelName = TEXT("/Game/RaftSim/Maps/L_Terminator");
    UPROPERTY(EditDefaultsOnly, Category = "RaftSim|Frontend")
    FName ChilkoLevelName = TEXT("/Game/RaftSim/Maps/L_LavaCanyon");
};
