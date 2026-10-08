#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimHoleWaterActor.generated.h"

class ARaftSimRaftActor;
class UMaterialInterface;
class URaftSimHoleChurnComponent;
class URaftSimRaftSplashComponent;

/**
 * The river's holes as the raft meets them, while RaftSim.HoleWater is on.
 * - At each hole near the view, the breaking wave crashing back upstream in
 *   place (URaftSimHoleChurnComponent), with its roar from the nearest two.
 * - Water thrown over the crew when the raft hits a hole or a wave hard
 *   (URaftSimRaftSplashComponent).
 *
 * The holes are the water adapter's own breaking sites, the ones whose
 * falling water and breaking wave the hull meets (RaftSimHolePourOver.h,
 * RaftSimHoleWave.h), drawn at the same size: the raft hits what is drawn.
 * While it draws them it hides the rapid roller and crest-spray particles,
 * whose puffs read as random spray shooting off a hole.
 */
UCLASS()
class ARaftSimHoleWaterActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimHoleWaterActor();
    virtual void Tick(float DeltaSeconds) override;

    /** RaftSim.HoleWater is on. */
    static bool IsEnabled();
    /** The raft whose crew are splashed and whose hull the waves keep out of. */
    void SetRaft(ARaftSimRaftActor* InRaft) { Raft = InRaft; }
    /** Holes drawn now, for review and tests. */
    int32 GetDrawnHoleCount() const;

private:
    URaftSimHoleChurnComponent* NewWave();
    void HideWaves();
    void SetHoleParticlesHidden(bool bHide);

    UPROPERTY()
    TArray<TObjectPtr<URaftSimHoleChurnComponent>> Waves;
    UPROPERTY()
    TObjectPtr<URaftSimRaftSplashComponent> Splash;
    UPROPERTY()
    TObjectPtr<UMaterialInterface> WaveMaterial;

    TWeakObjectPtr<ARaftSimRaftActor> Raft;
    TArray<bool> WaveInUse;
    bool bHoleParticlesHidden = false;
    int32 NextSeed = 1;
};
