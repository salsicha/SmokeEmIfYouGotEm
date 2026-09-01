#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimRiverWaterConfig.generated.h"

class UMaterialInterface;
class UTexture2D;

/**
 * Placed in a river map to tell the water runtime to load a cooked steady-state
 * flow window (raftsim.cooked_flow_fields.v1) instead of the dev flat tank. The
 * raft resolves this at BeginPlay and calls ConfigureRiverWindow.
 */
UCLASS()
class RAFTSIMWATER_API ARaftSimRiverWaterConfig : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimRiverWaterConfig();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** Repo-relative directory of the cooked_flow_fields manifest. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    FString CookedFieldsDir =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/scenario_troublemaker/"
             "cooked_flow_fields");

    /** Flow band id to load (low_runnable / median_runnable / high_runnable). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    FName FlowBand = TEXT("median_runnable");

    /** World-space window centre in meters (XY). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    FVector2D WindowCenterM = FVector2D::ZeroVector;

    /** Window extent in meters (square). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    float WindowExtentM = 600.0f;

    /** Legacy named-rapid windows place their strongest hydraulic at local
     * origin. Full-corridor maps with a station/lateral coordinate map must
     * disable this so cooked cells retain their global river stations. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    bool bRecenterHydraulicCrux = true;

    /** Optional dense station/lateral-to-curved-world coordinate map. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming")
    FString CoordinateMapPath;

    /** M3 full-reach moving-window manifest. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming")
    FString StreamingManifestPath;

    /** Follow the raft and swap overlapping transit/named-rapid solver crops. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming")
    bool bEnableMovingWindowStreaming = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming", meta = (ClampMin = "80.0"))
    float MovingWindowStationExtentM = 320.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming", meta = (ClampMin = "40.0"))
    float MovingWindowLateralExtentM = 80.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Streaming", meta = (ClampMin = "8.0"))
    float MovingWindowAdvanceM = 80.0f;

    /** Full-reach production terrain exists in the map; suppress local bed proxy. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment")
    bool bMapProvidesTerrain = false;

    /** Reassert a generated river map's reviewed height-fog values after PIE
     * world duplication. UE 5.8 can otherwise restore stale state-stream
     * values even though the serialized component is correct. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment|Presentation")
    bool bEnforceTaggedHeightFogPresentation = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment|Presentation")
    FName RuntimeHeightFogActorTag = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "0.05"))
    float RuntimeHeightFogDensity = 0.0025f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment|Presentation")
    bool bRuntimeVolumetricFogEnabled = false;

    /** Reassert a river-local directional-light intensity in runtime worlds.
     * This prevents a capture-oriented broad sun lobe from clipping turbulent
     * water after PIE/game-world duplication. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment|Presentation")
    bool bEnforceTaggedDirectionalLightPresentation = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment|Presentation")
    FName RuntimeDirectionalLightActorTag = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "20.0"))
    float RuntimeDirectionalLightIntensity = 4.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Environment|Presentation")
    FRotator RuntimeDirectionalLightRotation = FRotator(-50.0f, 55.0f, 0.0f);

    /** The authored editor-capture ribbon is hidden during play, so the live
     * solver mesh must render the complete visible river rather than a
     * subordinate hydraulic-detail overlay. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    bool bLiveSolverOwnsRuntimeRendering = false;

    /** Render a solver-conforming Single Layer Water core beneath the live
     * detail surface. The core is triangulated only through fully sampled wet
     * cells, so it supplies optical depth without restoring the rectangular
     * moving-window or wet-bank artifacts of a broad opaque sheet. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    bool bEnableLiveSolverVolumeCore = false;

    /** Optional river-local parent/instance for the non-colliding optical
     * core. Hydraulics and topology remain owned by the sampled solver mesh;
     * this override changes only material response. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UMaterialInterface> LiveVolumeCoreMaterialOverride;

    /** River-local first-party surface detail. These textures are multiplied
     * by solver-authored activity masks and cannot create hydraulics or foam
     * outside the live wet mesh. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UTexture2D> LiveWaterFlowNormalTexture;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UTexture2D> LiveWaterFoamLaceTexture;

    /** Coverage of the non-volumetric live detail surface in ordinary current.
     * A river using the volume core keeps this low: the core supplies depth,
     * while this layer carries geometric normals and a soft shoreline feather. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveSurfaceCalmCoverage = 0.86f;

    /** Coverage of the non-volumetric detail surface in solver-active water. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveSurfaceActiveCoverage = 0.96f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveSurfaceSpecular = 0.28f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.02", ClampMax = "1.0"))
    float LiveSurfaceRoughness = 0.15f;

    /** Strength of the bounded Fresnel sky tint on the solver-owned carrier.
     * Matches MI_RaftSim_SouthForkProductionWater — at the previous 0.62 the
     * carrier wore a milky sky veil the static tiles did not. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveSkyReflectionStrength = 0.15f;

    /** Strength of the two moving micro-normal layers. Geometry and solver
     * normals remain authoritative at zero and one alike. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveRippleStrength = 0.18f;

    /** Optical intensity of solver-derived entrained-air coloration. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.5"))
    float LiveFoamIntensity = 0.52f;

    /** Enables a plane-preserving five-tap filter over the visible carrier
     * and rigid raft-support surface. This removes cooked-cell stair steps
     * without mutating solver state, collision, flexible D3 overwash, or
     * authored bathymetry. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    bool bEnableLivePresentationSurfaceSmoothing = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LivePresentationSurfaceSmoothingStrength = 0.0f;

    /** River-local scale for the solver-energy-gated sub-grid standing-wave
     * term shared by the visible carrier and rigid raft support. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LivePresentationStandingWaveScale = 1.0f;

    /** River-local scale for carrier/support relief derived from solver
     * surface curvature. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LivePresentationHydraulicReliefScale = 1.0f;

    /** Solver-foam focus remap for the separate masked lace sheet. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "0.95"))
    float LiveRapidFoamFocusStart = 0.12f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.05", ClampMax = "1.0"))
    float LiveRapidFoamFocusEnd = 0.72f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveRapidFoamCoverageGain = 1.0f;

    /** Width of the presentation-only alpha feather at the sampled wet bank.
     * Solver-owned carriers use a narrow blend so water does not appear to
     * climb several metres onto dry land. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "1.5", ClampMax = "12.0"))
    float LiveSurfaceBankBlendMeters = 4.5f;

    /** Breaks up the presentation-only bank feather in river-station space.
     * The sampled wet mask, wet-cell topology, collision, bathymetry,
     * buoyancy, raft forces, D3, and D4 remain unchanged. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    bool bEnableLivePresentationBankNaturalism = false;

    /** Maximum shift, in metres, applied inside the existing visual bank
     * feather and as an inward-only retreat of the optical core's outermost
     * wet vertex. This cannot extend visible water beyond solver-owned wet
     * topology. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.25"))
    float LivePresentationBankNaturalismAmplitudeMeters = 0.0f;

    /** Defaults are the South Fork clear-water calibration and match
     * MI_RaftSim_SouthForkProductionWater so the live carrier and the static
     * terrain-clipped tiles render one continuous body of water. Rivers with
     * different optics override these in their environment passes. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    FLinearColor LiveShallowSurfaceColor =
        FLinearColor(0.012f, 0.030f, 0.026f, 1.0f);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    FLinearColor LiveDeepSurfaceColor =
        FLinearColor(0.006f, 0.020f, 0.019f, 1.0f);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    FLinearColor LiveReflectedSkyColor =
        FLinearColor(0.075f, 0.130f, 0.150f, 1.0f);

    /** River-local optical coefficients for the non-colliding volume core.
     * These presentation values do not alter solver depth, velocity, wet/dry,
     * collision, buoyancy, raft forces, or scoring. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    FLinearColor LiveWaterScattering =
        FLinearColor(0.00010f, 0.00028f, 0.00020f, 0.0f);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    FLinearColor LiveWaterAbsorption =
        FLinearColor(0.0066f, 0.0026f, 0.0040f, 0.0f);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    FLinearColor LiveRiverbedColorScale =
        FLinearColor(0.60f, 0.64f, 0.58f, 0.0f);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveShallowWaterOpacity = 0.30f;

    /** Presentation-only power curve applied to the normalized solver depth
     * before shallow/deep colour and opacity blending. One is linear; values
     * below one concentrate optical attenuation near a clear-water bank. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.25", ClampMax = "2.0"))
    float LiveOpticalDepthResponseExponent = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveDeepWaterOpacity = 0.54f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveFoamWaterOpacity = 0.91f;

private:
    void ApplyTaggedHeightFogPresentation();
    void ApplyTaggedDirectionalLightPresentation();
};
