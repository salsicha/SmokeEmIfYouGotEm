#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimHoleWave.h"

#include "RaftSimHoleChurn.generated.h"

class UAudioComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class URaftSimSynthSoundWave;

/** How a hole's breaking wave looks. Presets name the reviewed options. */
struct FRaftSimHoleChurnLook
{
    /** Height of the wave's crest above the trough's lowest water: as high
     * as the pour-over, so the hole reads as a smooth hump, a trough and a
     * white wall breaking back into it. */
    float WaveHeightCm = 75.0f;
    /** From the pour-over's foot to the boil line behind the wave. */
    float WaveLengthCm = 400.0f;
    /** Where the crest stands, from the pour-over (0) to the boil line (1):
     * behind the trough, so the lip falls into it. */
    float CrestPosition = 0.5f;
    /** How far the lip throws out over the trough before it falls. */
    float ThrowCm = 45.0f;
    /** How much the throw varies along the span and from moment to moment. */
    float ThrowVariation = 0.25f;
    /** How fast the water rolls up the back, over the lip and down. */
    float RollCmPerSecond = 170.0f;
    /** Size of the lumps rolling through the wave, as a share of its height. */
    float Turbulence = 0.12f;
    /** 1: dense white water; 0: lacy aerated veil. */
    float FoamDensity = 0.92f;

    /** "roll", "plunge" or "big"; anything else gives "roll". */
    static FRaftSimHoleChurnLook Preset(const FString& Name);
};

/** One hole, in world centimetres. The crest is the pour-over the water drops
 * off; the breaking wave stands across the trough downstream of it. */
struct FRaftSimHoleChurnSite
{
    FVector CrestCm = FVector::ZeroVector;
    FVector Downstream = FVector::ForwardVector;
    float HalfWidthCm = 330.0f;
    /** How far downstream of the pour-over the wave's front may fall. */
    float PlungeOffsetCm = 30.0f;
    /** Downstream drift of the crest's ends: the crest bows downstream by
     * this many centimetres per square metre across, as the relief does. */
    float CrestBowCmPerSquareMeter = 3.5f;
    float Intensity = 1.0f;
    int32 Seed = 0;
    FRaftSimHoleChurnLook Look;
};

/**
 * A hole's froth as the breaking wave it is, crashing back upstream without
 * moving. Across the trough below the pour-over stands a white roller: its
 * back rises from the boil line to a crest, the crest's lip curls over
 * toward the pour-over and a curtain of white water falls from it onto the
 * incoming green tongue, churning a band of white where it lands. The water
 * rolls through that shape (up the back, over the top, along the lip and
 * down the curtain), and the lip throws out and falls back in sections
 * along the span, so the wave keeps crashing in place. No spray.
 * The drawing has no collision; the hull meets the same wave (ShapeOf) through
 * RaftSimHoleWave.h.
 */
UCLASS()
class URaftSimHoleChurnComponent : public UProceduralMeshComponent
{
    GENERATED_BODY()

public:
    explicit URaftSimHoleChurnComponent(const FObjectInitializer& ObjectInitializer);

    /** Water height (cm) at a world point, so the wave sits on the water. */
    using FSurfaceHeightCm = TFunction<float(const FVector&)>;

    /** WaveMaterial is the breaking-water lip material; it gets its own instance here. */
    void Configure(const FRaftSimHoleChurnSite& InSite, FSurfaceHeightCm InSurface, UMaterialInterface* WaveMaterial);
    /** Keep the wave out of the raft's footprint (an ellipse about it). */
    void SetRaftExclusion(const FTransform& RaftTransform, float HalfLengthCm, float HalfWidthCm);
    /** Give the hole its own sound: the steady roar of the breaking wave with
     * its irregular crashing. Heard as a real source: full within 8 m,
     * fading to -40 dB by 78 m. */
    void EnableSound(uint32 Seed);
    /** Step the wave and rebuild its geometry. */
    void Advance(float DeltaSeconds, const FVector& ViewLocationCm);

    /** Set the breaking-water lip material toward dense white water (1) or a lacy veil (0). */
    static void ApplyFoamDensity(UMaterialInstanceDynamic* Material, float Density);
    /** The breaking wave a site draws, as the hull meets it. */
    static RaftSimHoleWave::FShape ShapeOf(const FRaftSimHoleChurnSite& Site);

private:
    float Outside(const FVector& PointCm) const;
    /** The wave's cross-section at one place across the span: points from
     * the boil line up the back, over the lip and down the falling curtain,
     * evenly spaced along the curve (world cm), with their outward normals
     * and the distance along the curve. */
    void Profile(float AcrossCm, float ToeLevelCm, TArray<FVector>& OutPoints, TArray<FVector>& OutNormals,
        TArray<float>& OutArc, FVector& OutPlungeCm) const;

    FRaftSimHoleChurnSite Site;
    FSurfaceHeightCm Surface;
    FVector Across = FVector::RightVector;
    FRandomStream Random;
    float TimeSeconds = 0.0f;
    float NextSoundCrashSeconds = 0.0f;
    bool bHasExclusion = false;
    FTransform Exclusion;
    float ExclusionHalfLengthCm = 0.0f, ExclusionHalfWidthCm = 0.0f;
    bool bSectionsCreated = false;
    TArray<int32> WaveTriangles, SeamTriangles;
    UPROPERTY()
    TObjectPtr<UAudioComponent> Sound;
    UPROPERTY()
    TObjectPtr<URaftSimSynthSoundWave> SoundWave;
};
