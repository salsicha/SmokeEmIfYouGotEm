#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"

#include "RaftSimRaftSplash.generated.h"

class UMaterialInterface;

/**
 * Water thrown over the crew when the raft hits a wave or a hole: when the
 * bow digs into water rising against it, or water rushes at it, or a hole's
 * pile crashes onto a tube, a burst of spray sheets and droplets is thrown up
 * from the hit and back over the boat, falling through the crew. Reference:
 * rafting photographs of a raft punching a hole, white water breaking over
 * the bow and drenching the crew. Presentation only: no force on the raft.
 */
UCLASS()
class URaftSimRaftSplashComponent : public UProceduralMeshComponent
{
    GENERATED_BODY()

public:
    explicit URaftSimRaftSplashComponent(const FObjectInitializer& ObjectInitializer);

    /** Water height (cm) and velocity (cm/s) at a world point; false where dry. */
    using FWaterSampler = TFunction<bool(const FVector&, float&, FVector&)>;

    void Configure(FWaterSampler InSampler, UMaterialInterface* DropletMaterial);
    /** Watch this raft (its transform, velocity in cm/s and size) for hits. */
    void TrackRaft(const FTransform& RaftTransform, const FVector& RaftVelocityCmPerSecond,
        float HalfLengthCm, float HalfWidthCm);
    /** Throw water from a world point on the raft's edge over the boat. */
    void Splash(const FVector& AtCm, float Strength);
    /** Step the droplets and rebuild them facing the view. */
    void Advance(float DeltaSeconds, const FVector& ViewLocationCm);

    int32 GetSplashCount() const { return SplashCount; }

private:
    struct FDrop { FVector PositionCm, VelocityCmPerSecond; float Age, Life, SizeCm, Spin; int32 Tile; bool bSheet; };

    void DetectHits(float DeltaSeconds);

    FWaterSampler Sampler;
    TArray<FDrop> Drops;
    FRandomStream Random;
    FTransform Raft;
    FVector RaftVelocity = FVector::ZeroVector;
    float HalfLengthCm = 250.0f, HalfWidthCm = 95.0f;
    bool bTracking = false;
    /** The bow's last freeboard (cm above the water) at each of three points across it. */
    float LastFreeboardCm[3] = {0.0f, 0.0f, 0.0f};
    bool bHaveFreeboard = false;
    float Cooldown = 0.0f;
    int32 SplashCount = 0;
    bool bSectionCreated = false;
    TArray<int32> Triangles;
};
