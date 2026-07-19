#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RaftSimWaterAudioParameters.h"

#include "RaftSimRunAudioDirector.generated.h"

class ARaftSimPresentationDirector;
class ARaftSimRaftActor;
class ARaftSimRunManager;
class UAudioComponent;
class USceneComponent;
class USoundWaveProcedural;
class URaftSimPhysicsBridgeSubsystem;

USTRUCT(BlueprintType)
struct FRaftSimProductionAudioMixState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float RiverBed = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float RapidFeatures = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float FoamAndSpray = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float Paddle = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float FabricAndImpact = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float CrewAndRescue = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float CanyonAmbience = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float Music = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float OcclusionLowPassHz = 20000.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float ReverbStrength = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    int32 ActiveLayerCount = 0;
};

/**
 * Shipping reactive mix. Eight deterministic, project-owned procedural PCM
 * layers provide an offline-safe fallback for river, rapid, spray, paddle,
 * fabric/impact, crew/rescue, canyon ambience, and adaptive music. The same
 * live water/raft telemetry that drives gameplay drives this mix.
 */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimRunAudioDirector : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRunAudioDirector();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Audio")
    FRaftSimWaterAudioParameters GetCurrentAudioParameters() const { return CurrentParameters; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Audio")
    FRaftSimProductionAudioMixState GetProductionMixState() const { return MixState; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Audio")
    int32 GetProductionLayerCount() const { return LayerWaves.Num(); }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Audio")
    bool HasQueuedPcmForEveryLayer() const;

protected:
    UPROPERTY()
    TObjectPtr<USceneComponent> Root;

    UPROPERTY()
    TObjectPtr<UAudioComponent> RiverAudio;
    UPROPERTY()
    TObjectPtr<UAudioComponent> RapidAudio;
    UPROPERTY()
    TObjectPtr<UAudioComponent> FoamAudio;
    UPROPERTY()
    TObjectPtr<UAudioComponent> PaddleAudio;
    UPROPERTY()
    TObjectPtr<UAudioComponent> FabricAudio;
    UPROPERTY()
    TObjectPtr<UAudioComponent> CrewAudio;
    UPROPERTY()
    TObjectPtr<UAudioComponent> AmbienceAudio;
    UPROPERTY()
    TObjectPtr<UAudioComponent> MusicAudio;

    UPROPERTY()
    TArray<TObjectPtr<USoundWaveProcedural>> LayerWaves;

    UPROPERTY()
    TObjectPtr<ARaftSimRaftActor> Raft;
    UPROPERTY()
    TObjectPtr<ARaftSimRunManager> RunManager;
    UPROPERTY()
    TObjectPtr<ARaftSimPresentationDirector> PresentationDirector;
    UPROPERTY()
    TObjectPtr<URaftSimPhysicsBridgeSubsystem> Bridge;

private:
    void InitializeProductionLayers();
    void RefillProceduralLayers();
    void UpdateEventEnvelopes(float DeltaSeconds);
    void ApplyMixToComponents();

    FRaftSimWaterAudioParameters CurrentParameters;
    FRaftSimProductionAudioMixState MixState;
    TArray<TArray<uint8>> LayerPcm;
    int32 LastSwimmerCount = 0;
    int32 LastPaddleStrokeCount = 0;
    int32 LastHighSideCount = 0;
    int32 LastRescueCount = 0;
    uint8 LastCrewCommand = 0;
    float PaddleEnvelope = 0.0f;
    float FabricEnvelope = 0.0f;
    float CrewEnvelope = 0.0f;
    float LastAppliedReverb = -1.0f;
};
