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
class URaftSimSynthSoundWave;
class URaftSimPhysicsBridgeSubsystem;

USTRUCT(BlueprintType)
struct FRaftSimProductionAudioMixState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float RiverBed = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float RapidFeatures = 0.0f;
    /** The loudest whitewater ahead, heard from where it is. */
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float DistantRapid = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float DistantRapidDistanceMeters = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float FoamAndSpray = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float Paddle = 0.0f;
    /** Pre-duck stroke envelope: the water-loudness duck can push the
     * audible Paddle channel toward zero by design (rapids bury strokes),
     * so stroke observability lives here. */
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float PaddleStrokeEnvelope = 0.0f;
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
 * Shipping reactive mix. Eight project-owned procedural layers (river, rapid,
 * spray, paddle, fabric/impact, crew/rescue, canyon ambience, adaptive music)
 * are synthesized live on the audio render thread (RaftSimSynthVoice): the
 * water is built from resonating bubbles, turbulence and laps, never from a
 * looped buffer. The river and rapid layers play from both sides of the boat,
 * and the loudest whitewater ahead plays from where it is, so a rapid is
 * heard before it is seen. The same live water and raft telemetry that
 * drives gameplay drives the mix.
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

    /** Every layer has a live synth voice playing. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Audio")
    bool HasStreamingVoiceForEveryLayer() const;

    /** Where the distant-rapid emitter sits (world cm). */
    FVector GetDistantRapidLocation() const { return DistantLocation; }

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
    /** Second, decorrelated river and rapid emitters on the starboard side. */
    UPROPERTY()
    TObjectPtr<UAudioComponent> RiverAudioStarboard;
    UPROPERTY()
    TObjectPtr<UAudioComponent> RapidAudioStarboard;
    UPROPERTY()
    TObjectPtr<UAudioComponent> DistantRapidAudio;

    /** The eight mix layers' voices, in layer order. */
    UPROPERTY()
    TArray<TObjectPtr<URaftSimSynthSoundWave>> LayerWaves;
    UPROPERTY()
    TArray<TObjectPtr<URaftSimSynthSoundWave>> ExtraWaves;

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
    void UpdateEventEnvelopes(float DeltaSeconds);
    void UpdateDistantRapid(float DeltaSeconds);
    void ApplyMixToComponents();
    /** Whitewater at a point, 0..1: aerated (supercritical) flow or broken surface. */
    float SampleWhitewater(const FVector& WorldCm, float* OutSpeed = nullptr) const;

    FRaftSimWaterAudioParameters CurrentParameters;
    FRaftSimProductionAudioMixState MixState;
    int32 LastSwimmerCount = 0;
    int32 LastPaddleStrokeCount = 0;
    int32 LastCrewCatchCount = 0;
    int32 LastOarCatches[2] = {0, 0};
    int32 LastOarReleases[2] = {0, 0};
    int32 LastHighSideCount = 0;
    int32 LastRescueCount = 0;
    int32 LastRockContactCount = 0;
    uint8 LastCrewCommand = 0;
    float PaddleEnvelope = 0.0f;
    float FabricEnvelope = 0.0f;
    float CrewEnvelope = 0.0f;
    float LastAppliedReverb = -1.0f;
    float LastVerticalSpeed = 0.0f;
    float SlamCooldown = 0.0f;
    float Heave = 0.0f;
    float DistantLevel = 0.0f;
    float MixLogSeconds = 0.0f;
    float LocalTurbulence = 0.0f;
    float HullFlow = 0.0f;
    float Scrape = 0.0f;
    float DistantSearchSeconds = 0.0f;
    float DistantTargetLevel = 0.0f;
    float DistantTargetIntensity = 0.0f;
    FVector DistantTarget = FVector::ZeroVector;
    FVector DistantLocation = FVector::ZeroVector;
    bool bHasDistantLocation = false;
    // The ring survey in progress, a few samples per frame.
    int32 DistantSurveyIndex = 0;
    float SurveyBestLoudness = 0.0f;
    float SurveyBestWhitewater = 0.0f;
    FVector SurveyBest = FVector::ZeroVector;
    FVector SurveyCenter = FVector::ZeroVector;
    float LastShear = 0.0f;
    bool bSampleShearThisFrame = false;
};
