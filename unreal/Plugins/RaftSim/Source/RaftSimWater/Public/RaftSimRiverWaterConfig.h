#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimRiverWaterConfig.generated.h"

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
    float LiveSurfaceSpecular = 0.42f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.02", ClampMax = "1.0"))
    float LiveSurfaceRoughness = 0.16f;

    /** Strength of the bounded Fresnel sky tint on the solver-owned carrier. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveSkyReflectionStrength = 0.62f;

    /** Strength of the two moving micro-normal layers. Geometry and solver
     * normals remain authoritative at zero and one alike. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LiveRippleStrength = 0.18f;

    /** Optical intensity of solver-derived entrained-air coloration. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.5"))
    float LiveFoamIntensity = 0.52f;

    /** Enables a render-only, plane-preserving five-tap filter over the
     * sampled free surface. This removes cooked-cell stair steps without
     * modifying the adapter samples, solver state, collision, buoyancy, or
     * raft forces. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    bool bEnableLivePresentationSurfaceSmoothing = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LivePresentationSurfaceSmoothingStrength = 0.0f;

    /** River-local scale for the synthetic sub-grid standing-wave term. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float LivePresentationStandingWaveScale = 1.0f;

    /** River-local scale for visual relief derived from solver curvature. */
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

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    FLinearColor LiveShallowSurfaceColor =
        FLinearColor(0.10f, 0.23f, 0.24f, 1.0f);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    FLinearColor LiveDeepSurfaceColor =
        FLinearColor(0.025f, 0.075f, 0.09f, 1.0f);

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    FLinearColor LiveReflectedSkyColor =
        FLinearColor(0.18f, 0.28f, 0.34f, 1.0f);
};
