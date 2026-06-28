#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"

#include "RaftSimGuidePawn.generated.h"

class UCameraComponent;
class USceneComponent;

USTRUCT(BlueprintType)
struct FRaftSimGuideCameraSettings
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    bool bEnableVRComfortVignette = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    bool bEnableHorizonStabilization = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    bool bEnableImpactFiltering = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    float MotionIntensity = 0.65f;
};

UCLASS()
class RAFTSIMRAFT_API ARaftSimGuidePawn : public APawn
{
    GENERATED_BODY()

public:
    ARaftSimGuidePawn();

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    UCameraComponent* GetGuideCamera() const { return GuideCamera; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|GuideCamera")
    USceneComponent* GetGuideSeatAnchor() const { return GuideSeatAnchor; }

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> Root;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> GuideSeatAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<USceneComponent> PaddleAnchor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|GuideCamera")
    TObjectPtr<UCameraComponent> GuideCamera;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|GuideCamera")
    FRaftSimGuideCameraSettings CameraSettings;
};
