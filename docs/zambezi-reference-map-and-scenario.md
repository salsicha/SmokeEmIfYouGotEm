# Zambezi reference map and scenario

> Runtime status, August 4, 2026: the complete reference Free Run is one of the
> six runnable rivers, is selectable from the player-facing Free Run catalog,
> and is versioned at `/Game/RaftSim/Maps/L_Zambezi`.
> Production terrain, bathymetry, rapid hydraulics, guide, art, and performance
> acceptance remain open.

## Run the map

From the game frontend, choose **Free Run** and then **Zambezi: Boiling Pot to
Mukuni Beach**. Free Run bypasses career-license locks, so the reference run is
available on a new profile. Its scenario ID is `zambezi_reference_run` and it
opens `/Game/RaftSim/Maps/L_Zambezi`.

For direct editor testing, open `/Game/RaftSim/Maps/L_Zambezi` and use Play In
Editor. The stable package is also included in the shipping cook list. Do not
use `L_ZambeziBatokaGorge_PhysicalCorridorCandidate`: that superseded preview
package is not the runnable map.

### Current runnable verification

The runnable map was regenerated and rechecked after the later environment,
character, water, terrain, and rapid-presentation milestones, including the
retained V19 elevation-stratified launch ecology, later cold-water highlight
and depth passes, the V2 irregular near-field terrain pass, and the subsequent
South Fork environment and character milestones. The V22 release-head
certification supersedes V18. The versioned Zambezi map remains byte-identical
and the player path is still:

`Free Run` → `zambezi_reference_run` → `/Game/RaftSim/Maps/L_Zambezi`

The machine-readable selection and Free Run manifests count six runnable rivers,
mark `zambezi_batoka_gorge` as `runnable: true` with `availability: free_run`,
and list it at `reference_free_run` tier. Thirty-one focused Python Zambezi
source/map contracts and all five M6 frontend/progression tests pass. The native
`RaftSim.P4.RiverMapLoads.L_Zambezi`
gate loads the committed map into PIE, reports the vertical-slice game mode,
binds the 5,908-point curved coordinate map and cooked field, exposes 10,465 wet
surface vertices, ten live breaking sites, 645 visible rapid-foam vertices,
and 16,896 transmitting-water core triangles, and completes MapCheck with zero
errors and zero warnings. The sole accepted automation warning is the
external-connectivity probe timeout; it has no map-load or gameplay authority.

The exact base commit, runtime-contract hashes, test commands, measured counts,
authority boundary, and open external gates are preserved in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_runnable_release_head_v22_review.json`.

This verifies the current committed Zambezi source, runtime registry, and map
package. It does not close
the open high-resolution terrain, surveyed bathymetry, rapid-specific hydraulic,
seasonal-flow, guide, rights, photoreal-art, or target-performance gates.

The current schema-v22 saved-map audit retains the schema-v21 left/right low,
mid, and high elevation ecology strata. The retained map contains 6,512 launch ground-cover
instances with stratum counts `[978, 1200, 1200, 734, 1200, 1200]`, plus 772
woody instances with counts `[139, 122, 140, 112, 108, 151]`. All are source-
Landscape-grounded, non-colliding, waterline-safe presentation instances. The
supplemental launch-camera search retains 132 of 240 targets and records 108
rejections rather than relaxing route-clearance, dry-height, or 34-degree slope
rules. See the
`zambezi_launch_stratified_ecology_v19_review.json` matched visual record; it
does not claim production ecology or photoreal acceptance.

The Zambezi map build now combines three evidence layers without pretending they
have equal authority:

- The existing Copernicus GLO-30 corridor remains the Unreal Landscape,
  collision, height-query, and physics terrain authority.
- `zambezi_batoka_heightmap.png` is a user-supplied colour-height screenshot. Its
  20-band legend is inverted into a 16-bit visual-reference heightfield and an
  OBJ morphology mesh. OpenStreetMap labels, roads, borders, and UI pixels are
  detected by legend-fit error and locally repaired. This product is not a DEM
  and cannot drive collision or solver geometry.
- `victoria-falls-rapids-map.pdf` supplies the ordered 25-rapid sequence and
  illustrative relative spacing. Digitised pin spacing is scaled to the
  published 17-mile run, then projected onto the existing review-gated route.
  It is not surveyed stationing.

## Regeneration

```bash
PYTHONPATH=physics/src python -m raftsim.examples.generate_zambezi_reference_map --repo-root .
PYTHONPATH=physics/src python -m raftsim.examples.generate_named_rapid_review_assets --repo-root .
```

The generated bundle is under
`physics/data/real_world/zambezi_batoka_gorge/reference/user_supplied/`; the run
scenario is
`physics/data/real_world/zambezi_batoka_gorge/scenario_zambezi_run/scenario.json`.
The OBJ uses metres with local X east, Y south, and Z up; elevation 659 m is its
local zero and Unreal import scale is 100 cm per unit.

The Unreal runnable map is regenerated with:

```bash
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "$PWD/unreal/SmokeEmIfYouGotEm.uproject" \
  -unattended -nop4 -nosplash -NoSound -RenderOffscreen \
  -RaftSimCreateLandscapeImportCandidateMaps \
  -RaftSimLandscapeImportCandidateRiverId=zambezi_batoka_gorge \
  -RaftSimExitAfterEnvironmentAutomation
```

This saves the stable runtime package at `/Game/RaftSim/Maps/L_Zambezi`. The
package is versioned and listed in `DefaultGame.ini`'s shipping cook list, so a
fresh checkout contains a directly runnable Zambezi map. The Mac and Windows
packaging scripts retain a deterministic fail-closed regeneration fallback if
the package is missing before cooking.
The M6 progression migration test and the Python shipping-contract test both
require the player-facing `zambezi_reference_run` selector to resolve to this
shipping package; the former ignored
`L_ZambeziBatokaGorge_PhysicalCorridorCandidate` path is explicitly rejected.
The map contains 25 editor-only rapid marker actors, a player raft and start,
the vertical-slice game mode, and a live-water runtime configuration. Rapid 9
is tagged as a mandatory commercial portage. Gameplay hides the labels; the
World Outliner and editor viewport retain them for authoring.

The saved runnable map also contains four render-only source-terrain tiles with
the retained Batoka V12 world-aligned basalt material, V17 height-aware organic
morphology, and V18 exposure-safe shading. Grid central differences replace triangle-averaged normals,
and the initial authored relief uses slower wavelengths under a 2.2 m cap
instead of sampling near the 12.5 m render-mesh Nyquist limit. The 72 m
active-water half-width is followed by a hard 28 m dry-bank buffer. The widest
73.44 m water edge therefore retains at least 26.56 m of unchanged shoreline.
Six bounded low-pass passes reconstruct source facets by at most 3.2 m. Inside
the 100 m horizontal radius, no morphology is permitted below 6 m above local
conditioned water and it reaches full strength only at 18 m. Ordinary
morphology remains capped at 2.8 m; dry upper-scarp infill may reach 4.4 m.
From 100-220 m the original horizontal fade still applies. The deterministic
build reconstructs 97,842 vertices with an observed 2.82 m maximum, then
conditions 99,790 of 1,631,500 vertices. Of those, 7,043 lie inside the 100 m
horizontal radius; their minimum height is 6.45 m above local water, and the
nearest conditioned vertex is 53.97 m from the polyline. Variable-height
terraces, warped joint recesses, multi-scale erosion, and two broad
incommensurate buttress/gully fields fill visual detail that the 30 m source
cannot resolve. Because that DEM still produces false comb-like self-shadows,
only the four non-colliding visual tiles have shadow casting disabled; the raft,
rocks, vegetation, and gameplay geometry still cast shadows. A movable Zambezi
review sun at -48 degrees pitch and -90 degrees yaw keeps that presentation
deterministic. None of this changes the hidden Copernicus Landscape used for
collision, height queries, or physics. The actor tags
`RaftSimProceduralVisualMorphology`, `RaftSimBatokaOrganicMorphologyV17`,
`RaftSimBatokaHeightAwareFacetReconstructionV17`,
`RaftSimBatokaUpperDryScarpInfillV17`, `RaftSimBatokaExposureSafeScarpV18`,
`RaftSimCoarseSourceSelfShadowSuppressed`, `RaftSimProtectedShorelineBuffer`,
`RaftSimBatokaWorldAlignedTerrain`, and `RaftSimNonCollisionRenderSurface`
make that authority boundary inspectable in the generated map.

The runnable launch bank-cover search also no longer minimizes absolute slope,
which had collapsed most synthetic cover onto one flat contour. It gives each
of 7,200 deterministic, shadowless, non-colliding instances its own bounded
slope and dry-height target and uses a lower-energy dry-season palette. V18
reduces target height from 0.95-2.30 m to 0.55-1.55 m and narrows the footprint
range while increasing coverage. All 7,200 targets pass in the retained map;
the maximum selected source slope is 41.98 degrees. A larger, steeper talus bracket was rejected after its shadow
formed a tall black wedge on the left wall. The retained map restores the
previous 0.95-5.20 m talus size and placement bounds and has no such wedge in
the matched launch frame. The technical pass, rejected bracket, hash locks,
visual limitations, and external gates are recorded in
`zambezi_organic_upper_scarp_v17_review.json`; the later exposure, water, and
cover evidence is in `zambezi_launch_optical_naturalism_v18_review.json`.

V18 also localizes the launch-water reflection response. The calm detail skin
is disabled, active coverage is 6%, roughness is 0.66, and river-local sky
reflection strength is 0.055. A lower sun/skylight/exposure bracket and a broad
bounded erosion-stain field reduce clipped water highlights and the chalky
sun-facing scarp without moving water, terrain, collision, or solver geometry.
In the matched 1280×720 launch view, the water p95 falls from 0.8859 to 0.8478,
the fraction above 0.90 falls from 0.01685 to 0.00065, and the left-water
fraction above 0.90 falls from 0.03989 to 0.00148. These are descriptive image
metrics, not photoreal or hydraulic acceptance.

The runnable launch also carries two adaptive, source-conditioned bank meshes
covering stations 0-1,000 m. V2 bilinearly samples the four conditioned terrain
tiles onto a deterministic irregular 2.5 m grid, excludes the 72 m active-water
half-width plus a 3 m inner dry-bank buffer, and extends no farther than 600 m
laterally. Station/lateral jitter is bounded to 0.55/0.42 m and fades to zero at
the mesh boundary. Every curved-offset cell is checked before triangulation;
985 of 124,230 candidates (0.793%) are omitted for wrong winding or a triangle
below 0.25 m², while the accepted minimum is 0.263 m². This prevents the thin
inverted overlap seams visible in the prior guide-eye capture.

Where the coarse source leaves a shoreline gap, a bounded correction raises
only the render surface by at most 1.8 m; the retained map observes 0.33 m
minimum dry clearance. Domain-warped broad erosion, local basalt fracture, fine
talus, and paired joint cuts are capped at 1.35 m and observe a 0.98 m maximum.
The two actors contain 169,222 vertices and 246,490 triangles, remain
non-colliding, and never replace the Copernicus Landscape's height-query,
collision, or physics authority. They are tagged
`RaftSimIrregularPlanarTopologyV2`, `RaftSimDomainWarpedGeomorphicReliefV2`,
and `RaftSimNearFieldSelfShadowSuppressed`, and do not cast shadows. The matched
frame confirms continuous shoreline/terrain coverage but does not promote the
still-rounded source silhouette or sparse/repeated ecology to photoreal.

The runnable first kilometre now has a separate six-component talus layer. The
older physical-corridor boulder distribution begins about 5 km downstream, so
it could not break up either bank seen from the launch. A deterministic
128-candidate search now places 360 rights-reviewed CC0 Poly Haven rock analogs,
60 for each of six meshes, approximately 118-993 m downstream. Every placement
is grounded against the source Landscape, stays outside the full route by at
least 3 m beyond the 72 m active-water half-width, requires 1-160 m of dry
height above conditioned water, and rejects slopes above 48 degrees. All 360
targets pass in the retained build; the maximum accepted slope is 37.817
degrees. Heights range from 0.95-5.20 m, with small talus dominant and sparse
larger breakup rocks. The actors cast grounded presentation shadows but have no
collision, navigation, solver, water, raft-force, or Batoka-lithology authority.
Their tags include `RaftSimRunnableLaunchTalusV1`,
`RaftSimZambeziBasaltAnalogMaterialV1`,
`RaftSimProjectOwnedMineralRetone`,
`RaftSimGenericRockAnalogNoLithologyAuthority`,
`RaftSimNonCollisionRenderSurface`, and
`RaftSimPresentationOnlyNoHydraulicAuthority`.

The six components no longer bind the source moss material directly. They use
`MI_RaftSim_Zambezi_BasaltTalusV1`, a Zambezi-specific instance of the
project-owned `M_RaftSim_RiverBoulder` parent. Its reviewed-source contribution
is bounded to 0.42, mixing the already desaturated scan detail with 0.58
project-authored neutral mineral response. The instance keeps its waterline at
-10,000,000 cm as a deliberate dry-bank fail-safe: the parent has a 70 cm wet
band, but it will not be presented as real shoreline wetness until every
instance can receive a validated local water elevation.

The regenerated guide-seat and river-eye views confirm that the layer does not
enter the visible route or obstruct the raft, but the rocks remain too subtle
in those cameras to claim close material acceptance. The earlier close review
still documents the generic geometry, coarse rounded terrain, repeated bright
ground-cover forms, hard transitions, and absent credible wet bank. The
retained material decision is
`zambezi_basalt_talus_material_v1_review.json`; it supplements
`zambezi_launch_talus_v1_review.json` without promoting the layer to
photoreal, geology, wet-bank, or guide approval.

The Zambezi preview light rig now binds the directional light as atmosphere sun
zero and tags one captured skylight, one dry-season sky atmosphere, and one
volumetric gorge-haze actor. This is a deterministic presentation contract, not
evidence of measured atmospheric conditions or final lighting approval.

The active Zambezi dressing no longer loads the generic Procedural Vegetation
Editor species or their masked leaf cards. The generator creates five
project-owned, opaque, one-sided, vertex-colour Nanite meshes and places them as
non-colliding hierarchical instances:

- 2,100 `SM_RaftSim_Zambezi_RiparianTree_A_OpaqueV1` instances;
- 1,400 `SM_RaftSim_Zambezi_UmbrellaTree_B_OpaqueV1` instances;
- 1,400 `SM_RaftSim_Zambezi_ThornScrub_A_OpaqueV1` instances; and
- 700 full-corridor `SM_RaftSim_Zambezi_SavannaGroundCover_A_OpaqueV1`
  instances, plus 1,200 instances of the same mesh in a separately tagged
  organic bank-mosaic component aligned to the two canonical camera windows;
- 58 camera-window riparian trees, 57 camera-window umbrella trees, and 117
  camera-window thorn-scrub instances in three separately auditable woody
  components. Eight of 240 deterministic targets are rejected by the hard 24°
  slope ceiling, leaving 232 placed instances;
- 5,200 launch-window savanna ground-cover instances, split evenly between
  `SM_RaftSim_Zambezi_SavannaGroundCover_A_OpaqueV1` and the second morphology
  `SM_RaftSim_Zambezi_SavannaGroundCover_B_OpaqueV2`. A deterministic
  96-candidate target-offset search spans approximately 55-955 m downstream,
  distributes cover 12-180 m beyond the active half-width, requires ground at
  least 0.8 m above conditioned water, and rejects slopes above 42°; and
- 153 launch-window riparian trees, 152 umbrella trees, and 306 thorn-scrub
  instances. Their deterministic 160-candidate target-offset search spans
  approximately 155-955 m downstream, distributes forms 35-200 m beyond the
  active half-width, requires 50 m of full-route clearance and ground at least
  3 m above conditioned water, and rejects slopes above 34°. Twenty-nine of 640
  targets fail those gates, leaving 611 placed instances; the steepest retained
  placement is 24.24°.

All five use `M_RaftSim_Zambezi_OpaqueVegetation`, contain solid branch, crown,
or blade geometry rather than alpha cards. The revised ground-cover mesh spans
several metres with tapered grass blades and low solid forb clusters. The two
launch morphologies vary form, yaw, footprint, and height from 0.95-2.30 m, and
their HISM components retain a 1.2 km cull range so the first-kilometre benches
do not collapse into a single visible shoreline row.
All dressing actors carry the
`RaftSimZambeziOpaqueVegetation`, `RaftSimOpaqueVolumetricVegetation`,
`RaftSimSlopeScreenedPlacement`, `RaftSimNonCollisionRenderSurface`, and
`RaftSimProceduralVegetationFallback` tags. The additional component also
carries `RaftSimOrganicBankMosaic` and `RaftSimCameraVisibleBankCover`.
The woody-window components carry `RaftSimCameraVisibleWoodyEcology`,
`RaftSimOrganicWoodyBankLayer`, and `RaftSimWoodySlopeCeiling24Degrees`.
The five launch components carry `RaftSimRunnableLaunchBankEcologyV1`; the two
cover components add `RaftSimRunnableLaunchBankCover` and
`RaftSimOrganicGroundCoverMorphologyV2`, while the three woody
components add `RaftSimRunnableLaunchWoodyEcology`. Launch cover and woody
components do not cast shadows: this narrow presentation exception removes the
rejected near-camera crown/wall streak under the low review sun, without
changing collision, water, solver state, raft forces, downstream documentary
woody shadows, or physics authority. The full-corridor ground-cover and
camera-mosaic components are likewise shadowless so dense grass blades do not
paint synthetic black streaks across the coarse DEM; full-corridor and
documentary trees and scrub still cast shadows.
Placement balances slope against deterministic longitudinal and lateral targets
on each dry bank, keeps a hard inner exclusion outside the 72 m active river
half-width, and covers the first kilometre ahead of the launch. This breaks up
the earlier easiest-shelf rows while preserving the navigable corridor and
removing the old floating black/green card failure. It does not establish
correct species, woodland ecology, or photoreal vegetation.

The physical-corridor editor-capture ribbon uses the isolated opaque Default
Lit parent `M_RaftSim_Zambezi_DefaultLitWater`. It preserves the two opposed
panners from the earlier sediment-water experiment: the primary normal uses
2.4 x 6.2 UV tiling, while the secondary uses 4.1 x 10.3 and swaps its axes for
cross-current breakup. Bounded world-space variation and a first-party capture
fill keep the surface readable when temporal reflection history is unavailable.
The generated actor exposes `RaftSimZambeziDefaultLitWater`,
`RaftSimMovingMultiScaleWaterNormals`,
`RaftSimSingleLayerWaterCaptureRejected`, `RaftSimPhysicalCorridorWater`, and
`RaftSimNonCollisionRenderSurface` tags. During gameplay this ribbon is tagged
`RaftSimCaptureOnlyStaticWater` and hidden, so it cannot restore the former
rectangular, opaque sheet.

The retained fixed-route bracket uses 1.08 base-color scale, 0.32 emissive
fill, 0.34 roughness, 0.38 specular, 0.16 normal intensity, 0.14 optical
variation, 0.90 mesh-normal up blend, and 0.06 authored displacement. In the
canonical lower image halves, mean luminance rises from 0.060286 to 0.247354
in the guide-seat view and from 0.061027 to 0.223423 at river eye; neither
retained lower half has pixels below 0.02. The result reads as olive-green
water instead of a nearly black sheet, although broad smooth highlight bands
still reject photoreal promotion.

The former `M_RaftSim_Zambezi_SingleLayerWater` parent, its volume coefficients,
the `zambezi_sediment_water_gameplay_v2` bracket, and the
`zambezi_cross_current_sediment_water_v1` bracket remain audit evidence rather
than active map state. They established the river-local panner scales and
showed useful gameplay-viewport groove reduction, but direct fixed-route
SceneCapture2D evidence rejected that shading path. The current decision and
measurements are recorded in
`zambezi_default_lit_capture_water_v1_review.json`.

The gameplay river now comes from the live solver mesh. A non-colliding,
wet-cell-clipped volume core uses
`MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV2`, parented to the shared
raft-transmitting water material. That parent now multiplies its existing
optical-depth opacity by the smooth station/lateral wet-cell coverage stored in
vertex alpha. The Zambezi profile uses a 7.5 m bank blend—approximately three
sampled cells—so the optical body fades at both banks instead of ending as an
opaque rectangular cell edge. The live Default Lit detail layer is limited to
0.025 calm and 0.13 active optical coverage, and the river-local glare profile
uses 0.22 surface specular, 0.42 roughness, and 0.15 sky-reflection strength.
The two project-owned source textures under
`unreal/SourceArt/RaftSim/Water/ZambeziBatoka/` still supply normal and foam-
lace breakup; the latter is multiplied by solver foam and speed and cannot
create whitewater in calm or dry cells.

Matched gameplay captures retain the exact raft transform, 2,673 wet vertices,
eight active breaking sites, 125 visible rapid-foam vertices, and 4,224 volume-
core triangles. In the measured water mask, pixels above 0.90 luminance fall
from 7.3201 to 1.2097 percent, pixels above 0.95 fall to zero, and the sampled
right-bank p99 vertical edge falls 14.8 percent. This is a bounded technical
improvement, not photoreal or surveyed-shoreline acceptance. Exact hashes,
values, images, and remaining defects are recorded in
`zambezi_live_transmitting_water_v2_review.json`.

No terrain, collision, hydraulic state, bathymetry authority, wet/dry mask,
scoring, or raft-force value changes. Realistic suspended sediment, caustics,
crest geometry, local bathymetric transmission, seasonal calibration,
rapid-scale foam/spray, and guide/art approval remain open.

An August 1 organic-basalt material pass now conditions the same four
render-only V15 terrain tiles. It keeps the reviewed 50 m world-aligned macro
source, blends a second incommensurate 83 m projection through deterministic
world-space variation, doubles the Rock037 detail footprint to 4.8 m, and
reduces its color, normal, and roughness weights. A blue-gray basalt multiplier
and bounded brown weathering replace the former uniformly tan response across
both steep and rounded dry walls. The accepted gameplay comparison lowers mean
dry-canyon luminance from 0.7061 to 0.6448, lowers mean saturation from 0.3255
to 0.3003, and raises bounded adjacent luminance variation from 0.00758 to
0.01115 without introducing pixels below 0.18 luminance in the matched terrain
mask. These are descriptive renderer measurements, not an art threshold.

The graph changes color/material presentation only. The hidden Copernicus
Landscape, four render-tile meshes, V15 morphology, 100 m shoreline protection,
collision, height query, water, solver, route, hazards, raft forces, and
scenario remain unchanged. The generic CC0 Aerial Rocks 02 and Rock037 sources
are still visual analogs rather than Batoka lithology authority. The retained
frame and full rejection boundary are recorded in
`zambezi_organic_basalt_surface_v16.png` and
`zambezi_organic_basalt_surface_v16_review.json`.

## Runnable reference status

The map is available from the main menu as **Zambezi: Boiling Pot to Mukuni
Beach**. Select **Free Run** to launch it without a career-license gate. Its
frontend scenario ID is `zambezi_reference_run`, and both the player selection
catalog, its generated source model, and the source scenario now carry the
explicit portfolio role `runnable_river` and tier `reference_free_run`. The
source model resolves the same frontend scenario, saved map package, and
normal-big-water reference band, so regeneration no longer falls back to the
old South-Fork-only selection model.
The named-rapid source catalog, generated marker and simulator-run manifests,
Rapid/River Editor shell, player-facing scenario catalog, runtime map-load test,
and shipping cook list all classify it as the sixth runnable river. There are
no remaining `additional_active_environment` river entries in the current
portfolio.

The M6 progression manifest now makes that runtime promise explicit rather than
leaving it implicit in the aggregate `available_maps` count. Its six-entry
`runnable_rivers` array binds `zambezi_batoka_gorge` to
`zambezi_reference_run`, `/Game/RaftSim/Maps/L_Zambezi`, and the
`reference_free_run` tier. The focused Python contract cross-checks this row
against the versioned map, cook configuration, frontend C++ catalog, player
selection catalog, source scenario, and packaging regeneration commands.

The approximately 1.6 GB generated `.umap` is committed through Git LFS at
`/Game/RaftSim/Maps/L_Zambezi`. `package_mac.sh` and `package_win.ps1` retain a
fail-closed regeneration fallback if that versioned package is absent, and
`DefaultGame.ini` includes it in shipping cooks. The regression suite checks
that the portfolio, source scenario, player catalog, frontend launch entry,
cook list, versioned map, and packaging regeneration commands all continue to
name the same runnable map.
The source-controlled runtime bundle lives under
`physics/data/real_world/zambezi_batoka_gorge/scenario_zambezi_run/runtime/`:

- `river_coordinate_map.json` maps the source-scale curved centerline into
  station/lateral coordinates used by the runtime solver.
- `cooked_flow_fields/` supplies a lightweight 30 km finite-volume seed on a
  5 m downstream grid. The centerline surface follows the conditioned
  Copernicus corridor; missing channel geometry and rapid cues are
  deterministic procedural infill.

Every one of the 25 mapped rapid records now contributes a bounded,
feature-tagged procedural control and a renderer-detectable
supercritical-to-subcritical transition. The generator verifies those
transitions again on the runtime presentation's 3 m sample spacing, using the
same upstream Froude minimum of 1.12 and downstream maximum of 0.94 as the live
water renderer. Speeds remain below 8 m/s. Rapid 9 receives hazard
visualization only and remains a mandatory commercial portage; the generated
transition is never a runnable-line recommendation.

The full-corridor water configuration disables the legacy hydraulic-crux
recentering used by single-rapid maps and carries the
`RaftSimGlobalRiverStationAuthority` tag. This keeps the cooked 0-30 km station
axis registered to the curved Zambezi route instead of moving one rapid to the
world origin. A focused Unreal PIE gate found nine live breaking sites in the
launch window and a ready 19-component production Niagara pool; the test also
requires at least one active roller and rapid-aerosol component.

The launch itself now has an explicit fail-closed contract. The raft spawns at
station 75 m on a subcritical apron whose first rapid approach starts at 130 m
and whose first procedural hydraulic control is at 160 m. That leaves 55 m of
clearance; the generated centerline Froude number is at most 0.4041 before the
approach, below the 0.94 ceiling. The saved map carries
`RaftSimSafeLaunchApron`. Its raft transform is authored at the loaded
hydrostatic tube-center waterline, about 0.215 m below the sampled surface,
instead of falling 0.58 m from above the water. Runtime buoyancy now integrates
the 220 kg dry raft and the 385 kg guide/passenger load as one 605 kg body while
D2 retains those same occupant masses for local tube compression.

`RaftSim.P4.RiverMapLoads.L_Zambezi`
requires the raft to remain upright through the initial settle and after an
`AllForward` command, retain all five attached crew actors, and report zero
swimmers. The focused test passes, and the complete parameterized
`RaftSim.P4.RiverMapLoads` run passes all six maps with zero failures. The
renderer-backed result is `zambezi_safe_launch_crew_v1.png`; its review record
deliberately fails photoreal promotion while passing runnable launch acceptance.

The runnable classification was reverified on August 4, 2026 against the V2
near-field terrain release package. The player-facing registry confirms that the
player-facing `zambezi_reference_run` opens `/Game/RaftSim/Maps/L_Zambezi`, and
`RaftSim.P4.RiverMapLoads.L_Zambezi` passes a live PIE launch with the cooked
water field, upright five-person raft, all rapid markers, separate live foam,
Niagara water pool, four non-colliding conditioned visual-terrain tiles, and
two V2 adaptive near-field terrain actors. The schema-v22
saved-map audit also requires solver-owned rendering, the transmitting volume
core, river-local texture bindings, low detail-skin coverage, smoothing, and a
capture-only static ribbon. All focused Python contracts pass. This is runnable
acceptance only; it does not close any production-hydraulic or photoreal gate
below.

This makes the complete map launchable and paddleable with the normal gameplay
stack. It does not turn the inferred bed or rapid cues into real-world
bathymetry, navigation guidance, or validated Zambezi hydraulics.

The visual fallback materially improves surface scale and canyon breakup, and
the canonical guide-seat and river-eye views now contain visible solid bank
cover plus restrained tree and thorn-scrub silhouettes instead of completely
barren slopes. The default runnable launch now also exposes a restrained
ecology layer ahead of the raft. The V2 retained map expands that layer from
1,895 to 5,811 launch instances, uses two ground-cover morphologies, distributes
them by target offset rather than lowest slope alone, and keeps them visible
across the first kilometre. The accepted capture contains no camera-clipped
plant and no woody silhouette visibly intersecting the waterline. The V1
placement bracket that put cover on a 54.16° face and trees at the waterline was
rejected rather than documented as progress. V20 now adds three explicitly
render-only layers to the source terrain: normal-oriented relief on the four
dense visual tiles, 2.5 m adaptive upper-scarp facade refinement over the first
kilometre, and 320 source-grounded CC0 rock-analog outcrops at least 6 m above
local water. The retained outcrops are 2.2-8.5 m high, non-colliding,
non-shadow-casting, outside the active route, and carry no lithology or
hydraulic authority. The rejected 4.2-22 m shadow-casting bracket produced
floating silhouettes and black wedges and is not versioned.

The 30 m DEM still yields rounded large-scale cliff silhouettes, however, and
the project-owned tree crowns and small synthetic clumps remain repetitive and
visibly procedural. V20 adds sparse ledge and ridgeline structure, but the near
left wall remains too barren and coarse for production art acceptance.
The views prove that the broken card foliage
is absent and that multi-height bank ecology is rendered; they do not prove
that the vegetation or terrain is photoreal. The runnable reference map is
therefore not yet accepted as photoreal.

The saved-map audit is written to
`docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_reference_scenario_map_validation.json`.
Schema v23 requires all 25 rapid markers, the Rapid 9 portage, one raft, player
start, runtime water configuration, the vertical-slice game mode, four
non-colliding, non-shadow-casting V20-tagged visual-terrain tiles, the exact -48/-90
degree presentation light, two tagged non-colliding V2 adaptive near-field
banks with irregular-planar-topology, domain-warped-relief, and V20 upper-dry-
scarp contracts, six non-colliding V20 dry-scarp outcrop components with 320
instances and the 6 m dry-height/no-authority contract,
the four-actor sun/sky/fill/fog atmosphere contract, absence of rejected
high-density bank actors, the
exact five vegetation mesh families and
13 instance components with a 14,316-instance total, exactly one tagged
1,200-instance camera-visible bank mosaic, three tagged camera-visible woody
components with the 58/57/117 accepted split and 24° slope-ceiling contract,
two launch-cover components with 6,512 accepted instances, three launch woody
components with 772 accepted instances, their six custom-data strata, full-
route/dry-height/slope placement tags, the 132-of-240 launch-camera face
mosaic, and the bounded launch-window shadow exception,
six separately tagged launch-talus components with 360 total source-grounded,
shadow-casting, non-colliding rock analog instances and their explicit
no-lithology/no-hydraulic-authority contract, plus the Zambezi-specific
material instance, its project-owned parent, and material-retone tags,
one conditioned profile waterline value per talus instance, and a bounded
render-only vertex-red wet-bank mask on the two adaptive near-field meshes,
zero legacy Zambezi PVE actors, and
exactly one
non-colliding physical-corridor ribbon bound through the isolated Default Lit
Zambezi parent with moving-normal and rejected-Single-Layer evidence tags. The
saved material asset is covered by `RaftSim.M9.FZambeziDefaultLitWater`; grid-normal behavior is
covered by `RaftSim.M9.FZambeziOrganicTerrainNormals`, and the talus instance
and scalar contract are covered by `RaftSim.M9.FZambeziTalusMaterial`; the
river-local live material and first-party texture import contract are covered
by `RaftSim.M9.FZambeziLiveTransmittingWater`. Schema v18 additionally
requires the V2 live material, 0.62 presentation smoothing, a 7.5 m bank blend,
the vertex-alpha bank-edge contract, V2 water tags, global-station preservation,
the global-station authority tag, all 25 procedural rapid records, the Rapid 9
visualization-only portage policy, and the `RaftSimSafeLaunchApron` tag.
The focused runtime gate is
`RaftSim.P4.RiverMapLoads.L_Zambezi`; it
now fails unless the loaded map produces live breaking sites and production
Niagara roller and aerosol activity, stays upright before and after the first
crew command, retains five attached crew avatars, and has zero swimmers.

The live surface exposes its advected solver foam on a separate masked
rapid-foam mesh instead of increasing opacity on the broad moving-water grid.
The wet-cell volume core supplies the transmitting river body without restoring
the former rectangular static edge. The foam component copies the solver-displaced
surface at a 1.4 cm presentation offset, combines only the solver foam field
with the verified station/bank feather, and uses the existing material's
pixel-level raft/crew exclusion. It has no collision, shadow, navigation,
sampling, buoyancy, force, D3, or D4 authority. The exact-current launch test
records eight accepted breaking sites, 125 visible foam vertices, 2,673 wet
surface vertices, 0.7285 maximum foam, 0.2640 m maximum standing-wave
displacement, and 0.1262 m maximum hydraulic-relief displacement. Evidence is
in `zambezi_live_solver_rapid_foam_v1.png` and
`zambezi_live_solver_rapid_foam_v1_review.json`. This is a retained runtime
readability baseline, not photoreal or real-world hydraulic acceptance.

The shared live-water VFX bridge now presents the nearest six solver-owned
breaking sites instead of limiting long rapid approaches to two Niagara pairs.
At the runnable Zambezi launch, the native gate records six active aerosol and
six active roller emitters from eight accepted breaking sites while preserving
the eight-component pool, 120 m hard cull, deterministic missing-asset fallback,
and the unchanged `L_Zambezi` package hash. Moderate-intensity aerosol and
roller scale/rates are raised within that fixed pool so they contribute visible
local breakup without manufacturing new rapid locations. The matched review
still rejects photoreal promotion: the particles cannot supply the missing
connected crest, hole, recirculating entrained-air volume, surveyed bathymetry,
or seasonally validated hydraulics. Evidence is in
`zambezi_solver_driven_rapid_vfx_v1_review.json`.

The live presentation grid is now independently refined from the solver's
physical analysis spacing. `L_Zambezi` resolves its 240 x 96 m moving window at
1.5 m for 10,465 render vertices and 20,480 triangles, while smoothing,
hydraulic relief, derivatives, and breaking-site detection retain their 3 m
neighbourhood. Two short oblique deterministic bands redistribute part of the
broad standing-wave amplitude inside a reduced 0.248 m theoretical envelope.
The complete six-map PIE suite passes; the Zambezi launch reports 10 accepted
breaking sites, 631 visible rapid-foam vertices, 16,896 optical-core triangles,
and a 4.000 ms initial null-RHI surface refresh. The Zambezi map remains
byte-identical, and cooked hydraulics, wet/dry state, collision, buoyancy, D3,
and D4 remain authoritative and unchanged.

Matched fixed-camera evidence raises local high-pass detail by 7.63% and edge
coverage by 12.55%, but it still shows a broad analytical diagonal swell rather
than a coherent overturning rapid. The candidate therefore remains a bounded
technical improvement, not photoreal or real-world hydraulic acceptance. Its
images, hashes, cross-river runtime matrix, open defects, and seven external
gates are recorded in `zambezi_refined_live_surface_v1_review.json`.

The production water composition now retains one connected crest-to-plunge
membrane at each of the three strongest accepted interior breaking sites while
Niagara supplies detached spray and roller particles. The retained membrane
uses only the overturning half of the solver-shaped circulation profile and the
project-owned masked foam lace with the existing raft/crew exclusion. The
former three-shell translucent fallback was re-tested and rejected because it
restored broad dome and repeated tent artifacts. The new shared budget is 504
triangles per site and 1,512 triangles total, with no collision, navigation,
sampling, buoyancy, D3, or D4 authority.

The focused water-surface test passes and the complete six-river PIE matrix
passes with exact connected-sheet counts. In the matched fixed Zambezi frame,
edge coverage rises 12.78% and high-pass detail 8.23% without translucent shell
artifacts. The close side view changes only subtly, however, and the strongest
rapid still depends on a broad analytical swell rather than a convincing
aerated hole and recirculating body. This is retained technical progress, not
photoreal or real-world hydraulic acceptance. Evidence, hashes, rejected
iterations, remaining defects, and external gates are recorded in
`zambezi_connected_plunge_v1_review.json`.

The shared live-water presentation no longer uses the 11.5 cm band whose
`0.19 * station + 0.61 * lateral` phase formed one continuous diagonal ramp.
Two split calm ripples and four hydraulically activated, incommensurate
phase-warped bands now make shorter station-dominant crest packets. Their
analytical station/lateral derivatives continue to drive normals, the largest
individual active band is 6.5 cm, and the combined theoretical envelope is
16.8 cm instead of 24.8 cm. At the exact retained Zambezi camera, the logged
standing-wave maximum falls from 23.43 cm to 10.46 cm and water pixels change
while the upper-bank background remains effectively fixed. The sampled
surface and its bounded hydraulic relief are deliberately not flattened.

The editor build, focused water-surface test, and all six runnable-map PIE
gates pass. The central repeated analytical band is removed, but the broad
low-resolution sampled rise, unmeasured bathymetry, missing aerated hole and
recirculation, synthetic terrain/ecology, and final spray/occlusion still fail
photoreal and real-world hydraulic acceptance. Exact captures, telemetry,
hashes, remaining defects, and external gates are recorded in
`zambezi_nonperiodic_live_wave_v1_review.json`.

The three strongest accepted interior transitions now receive a bounded
plan-view plunge pocket beneath the connected crest membrane: a compact dark
core, irregular side shoulders, and an aerated downstream return. Site
selection still comes exclusively from the local solver-derived Froude
transition, full-coverage/15 m clearance filter, intensity sort, and 6 m
deduplication. Per-site presentation displacement is limited to -0.28/+0.16 m
and the combined surface change to -0.30/+0.18 m. The pass changes only render
vertices, their local normals, and maximum-combined foam; water samples,
wet/dry authority, collision, buoyancy, forces, D3, D4, and the saved Zambezi
map remain unchanged.

The editor build, focused P2 water test, and complete six-river P4 matrix pass.
The live Zambezi frame retains 10 accepted sites, 10,465 wet render vertices,
645 rapid-foam vertices, 16,896 optical-core triangles, and the prior 10.46 cm
standing-wave maximum. Direct side review shows a coherent shallow trough and
no dome, tent, rail, card, or new shoreline-intersection artifact. Animated
water and terrain variance prevents attributing matched pixel deltas to this
small geometry change, so no image-improvement percentage is claimed. The
candidate remains bounded technical progress, not photoreal or real-world
hydraulic acceptance; evidence and open gates are recorded in
`zambezi_plunge_pocket_v1_review.json`.

## Production status and gates

The full Rapid 1–25 reference route is defined. Conflicting high-water route
descriptions (Rapid 11–23 and Rapid 14–25) are preserved as disabled candidates
instead of silently choosing one. Only the full reference route is selectable.

Promotion still requires local-guide approval of stations, lines, portages,
access, and rescue routes; geospatial review of the centerline/datum; rights
review of the supplied files; seasonal-flow reconciliation; a validated
real-world hydraulic window for every rapid; approved southern African gorge species and
ecology; lifelike terrain, bank, vegetation, and water art; and desktop/VR
visual and performance passes. These gates block production hydraulic-fidelity
and lifelike claims; they do not hide or disable the explicitly labeled
reference Free Run.
