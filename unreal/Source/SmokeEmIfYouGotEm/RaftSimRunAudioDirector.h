#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RaftSimWaterAudioParameters.h"

#include "RaftSimRunAudioDirector.generated.h"

class ARaftSimRaftActor;
class UAudioComponent;
class USoundWaveProcedural;
class URaftSimPhysicsBridgeSubsystem;

/**
 * P3 audio pass 1: drives a looping procedural water ambience whose loudness
 * follows the live river roar (built from the raft's flow speed and foam via
 * the RaftSimAudio cue math), with a one-shot impact layer on flips. No
 * external assets: the ambience is generated white/water noise so a run has
 * sound headlessly and in packaged builds.
 */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimRunAudioDirector : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRunAudioDirector();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** Current computed audio mix (exposed for tests/telemetry). */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Audio")
    FRaftSimWaterAudioParameters GetCurrentAudioParameters() const { return CurrentParameters; }

protected:
    UPROPERTY()
    TObjectPtr<UAudioComponent> AmbienceAudio;

    UPROPERTY()
    TObjectPtr<USoundWaveProcedural> WaterNoise;

    UPROPERTY()
    TObjectPtr<ARaftSimRaftActor> Raft;

    UPROPERTY()
    TObjectPtr<URaftSimPhysicsBridgeSubsystem> Bridge;

    FRaftSimWaterAudioParameters CurrentParameters;
    int32 LastSwimmerCount = 0;
};
