#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "RaftSimInputContracts.generated.h"

UENUM(BlueprintType)
enum class ERaftSimInputValueType : uint8
{
    Boolean,
    Axis1D,
    Axis2D,
    Axis3D
};

UENUM(BlueprintType)
enum class ERaftSimInputGameplayMode : uint8
{
    GuidedPaddleRaft,
    RowingOarRig,
    SharedSafety
};

USTRUCT(BlueprintType)
struct FRaftSimManualInputActionContract
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Input")
    FName ActionId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Input")
    FName DeterministicIntent;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Input")
    ERaftSimInputValueType ValueType = ERaftSimInputValueType::Boolean;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Input")
    ERaftSimInputGameplayMode GameplayMode = ERaftSimInputGameplayMode::SharedSafety;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Input")
    bool bKeyboardMouse = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Input")
    bool bGamepad = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Input")
    bool bVRMotionControllers = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Input")
    bool bGuidedPaddleVoiceEligible = false;
};

UCLASS()
class RAFTSIMINPUT_API URaftSimInputContractLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category = "RaftSim|Input")
    static TArray<FRaftSimManualInputActionContract> GetMilestone23ManualInputContracts();

    UFUNCTION(BlueprintPure, Category = "RaftSim|Input")
    static bool HasManualParity(const FRaftSimManualInputActionContract& Contract);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Input")
    static bool IsEnabledForGameplayMode(
        const FRaftSimManualInputActionContract& Contract,
        ERaftSimInputGameplayMode GameplayMode
    );

    UFUNCTION(BlueprintPure, Category = "RaftSim|Input")
    static bool CanRouteFromVoiceInGuidedPaddleRaft(const FRaftSimManualInputActionContract& Contract);
};
