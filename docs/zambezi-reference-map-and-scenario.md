# Zambezi reference map and scenario

> Runtime status, August 2, 2026: the complete reference Free Run is one of the
> six runnable rivers, is selectable from the player-facing Free Run catalog,
> and is versioned at `/Game/RaftSim/Maps/L_Zambezi`.
> Production terrain, bathymetry, rapid hydraulics, guide, art, and performance
> acceptance remain open.

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
the retained Batoka V12 world-aligned basalt material and V15 bounded organic
morphology. Grid central differences replace triangle-averaged normals, and
the initial authored relief uses slower wavelengths under a 2.2 m cap instead
of sampling near the 12.5 m render-mesh Nyquist limit. The 72 m active-water
half-width is followed by a hard 28 m dry-bank
buffer, so terrain vertices remain untouched for the first 100 m from the full
209-point source-aligned route polyline. The widest 73.44 m water edge retains
at least 26.56 m of unchanged shoreline. Six bounded low-pass passes reconstruct
source facets by at most 3.2 m; inside the 100 m horizontal buffer this is
allowed only on rock at least 6 m above local water and reaches full strength
at 18 m. From 100-220 m the 2.8 m-capped morphology fades in smoothly. The
current deterministic build reconstructs 97,842 vertices with an observed
2.82 m maximum, then conditions 89,494 of 1,631,500 vertices; its nearest
morphology vertex is 103.73 m from the polyline. Variable-height terraces,
warped joint recesses, multi-scale erosion, and talus variation replace the
regular V14 strata. Because the 30 m DEM still produced false comb-like
self-shadows, only the four non-colliding visual tiles have shadow casting
disabled; the raft, rocks, vegetation, and gameplay geometry still cast
shadows. A movable Zambezi review sun at -48 degrees pitch and -90 degrees yaw
keeps that presentation deterministic. None of this changes the hidden
Copernicus Landscape used for collision, height queries, or physics. The actor
tags `RaftSimProceduralVisualMorphology`,
`RaftSimBatokaOrganicMorphologyV15`,
`RaftSimBatokaHeightAwareFacetReconstructionV15`,
`RaftSimCoarseSourceSelfShadowSuppressed`, `RaftSimProtectedShorelineBuffer`,
`RaftSimBatokaWorldAlignedTerrain`, and `RaftSimNonCollisionRenderSurface`
make that authority boundary inspectable in the generated map.

The runnable launch also carries two adaptive, source-conditioned bank meshes
covering stations 0-1,000 m. They bilinearly sample the four conditioned terrain
tiles onto a 5 m grid, exclude the 72 m active-water half-width plus a 3 m inner
dry-bank buffer, and extend no farther than 600 m laterally. Where the coarse
source leaves a shoreline gap, a bounded correction raises only the render
surface by at most 1.8 m; the retained map observes 0.33 m minimum dry clearance.
Sub-metre erosion, fracture, and talus detail is capped at 0.96 m and observes a
0.56 m maximum. The two actors contain 42,612 vertices and 61,748 triangles,
remain non-colliding, and never replace the Copernicus Landscape's height-query,
collision, or physics authority. Their first shadow-casting bracket was rejected
because it projected large black wedges across the river; the retained actors
are tagged `RaftSimNearFieldSelfShadowSuppressed` and do not cast shadows.

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
Editor species or their masked leaf cards. The generator creates four
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
- 1,721 of 1,800 launch-window savanna ground-cover targets in a separate
  non-shadow-casting component. A deterministic 96-candidate search spans
  approximately 151-842 m downstream, stays at least 15 m beyond the active
  half-width relative to every route segment, requires ground at least 0.8 m
  above conditioned water, and rejects slopes above 32°; and
- 44 launch-window riparian trees, 43 umbrella trees, and 87 thorn-scrub
  instances. Their deterministic 160-candidate search spans approximately
  215-864 m downstream, requires 50 m of full-route clearance beyond the active
  half-width and ground at least 3 m above conditioned water, and rejects slopes
  above 24°. Eighteen of 192 targets fail those gates, leaving 174 placed
  instances.

All four use `M_RaftSim_Zambezi_OpaqueVegetation`, contain solid branch, crown,
or blade geometry rather than alpha cards. The revised ground-cover mesh spans
several metres with 54 tapered grass blades and 11 low solid forb clusters.
All dressing actors carry the
`RaftSimZambeziOpaqueVegetation`, `RaftSimOpaqueVolumetricVegetation`,
`RaftSimSlopeScreenedPlacement`, `RaftSimNonCollisionRenderSurface`, and
`RaftSimProceduralVegetationFallback` tags. The additional component also
carries `RaftSimOrganicBankMosaic` and `RaftSimCameraVisibleBankCover`.
The woody-window components carry `RaftSimCameraVisibleWoodyEcology`,
`RaftSimOrganicWoodyBankLayer`, and `RaftSimWoodySlopeCeiling24Degrees`.
The four launch components carry `RaftSimRunnableLaunchBankEcologyV1`; the
cover component adds `RaftSimRunnableLaunchBankCover`, while the three woody
components add `RaftSimRunnableLaunchWoodyEcology`. Launch cover and woody
components do not cast shadows: this narrow presentation exception removes the
rejected near-camera crown/wall streak under the low review sun, without
changing collision, water, solver state, raft forces, downstream documentary
woody shadows, or physics authority. The full-corridor ground-cover and
camera-mosaic components are likewise shadowless so dense grass blades do not
paint synthetic black streaks across the coarse DEM; full-corridor and
documentary trees and scrub still cast shadows.
Placement selects the lowest-slope candidate on each dry bank, keeps a hard
inner exclusion outside the 72 m active river half-width, starts beyond each
camera target, and covers approximately the next 120-600 m of view. This makes
solid grass/forb cover visible in both canonical images while preserving the
navigable corridor and removing the old floating black/green card failure. It
does not establish correct species, woodland ecology, or photoreal vegetation.

The physical-corridor ribbon now uses an isolated
`M_RaftSim_Zambezi_SingleLayerWater` parent instead of changing the shared
Default Lit candidate used by the other rivers. It binds Unreal's
`SingleLayerWaterMaterialOutput` with per-centimetre scattering and absorption,
phase, behind-water colour scale, and a 0.48 surface-opacity control. Two
opposed panners animate independently tiled normal-atlas layers, while bounded
world-space optical variation keeps commandlet captures from collapsing into a
single flat colour when temporal reflections are unavailable. The ribbon stays
non-colliding and render-only; the runtime water configuration and solver remain
the gameplay authority. The generated actor exposes
`RaftSimZambeziSingleLayerWater`, `RaftSimMovingMultiScaleWaterNormals`,
`RaftSimPhysicalCorridorWater`, and `RaftSimNonCollisionRenderSurface` tags.

An August 1 second renderer bracket supersedes the first sediment-water scalar
profile. The accepted instance now uses 0.48 opacity, 0.50 roughness, 0.26
specular, 0.04 normal intensity, 0.02 reflection fill, no emissive fill, and
0.04 optical variation. The source-aligned ribbon blends its mesh normals 0.92
toward up and scales its authored calm-water displacement to 0.08; the live
solver mesh remains optically disabled and keeps its own bounded rapid relief.
In the matched 1280 x 720 launch-water band, mean luminance falls from 0.5302 to
0.3906 and mean absolute horizontal image gradient falls from 0.003204 to
0.001931, a 39.7% reduction in the long artificial streamwise-groove response.
The regenerated default capture matches the selected diagnostic bracket without
runtime overrides. It does not reproduce the foreground depth split that
rejected the earlier global Single Layer experiment. The live runtime can add
solver-triggered breaking-water, roller, aerosol, foam, and
mist components at the procedural rapid controls described below. This is an
incremental optical and runtime baseline, not final water art: realistic crest
geometry, local bathymetric transmission, seasonal calibration, and guide/art
approval remain open.

The retained frame and machine-readable comparison are
`zambezi_sediment_water_gameplay_v2.png` and
`zambezi_sediment_water_gameplay_v2_review.json` in the landscape-candidate
capture directory. They are gameplay-viewport evidence for the runnable
`reference_free_run`, not approval of real-world hydraulics or photoreal art.

An August 2 cross-current breakup pass supersedes only the parent's normal
projection and bounded calm-surface response. The primary normal uses 2.4 x
6.2 UV tiling; the secondary uses 4.1 x 10.3 and swaps its UV axes before its
opposed panner. Normal intensity and optical variation are 0.10, the mesh-normal
up blend is 0.90, and calm render displacement is 0.06. The accepted sediment
volume vectors, 0.50 roughness, 0.26 specular, 0.48 opacity, 0.02 reflection
fill, and zero emissive fill remain unchanged. Brighter reflection/emissive
brackets were rejected because the gameplay viewport became a pale sky sheet.
The retained frame shows smaller local interference across the flow, but still
has a broad smooth analytical surface, residual streamwise grooves, sparse
foam, and no credible holes, rollers, aeration, spray, mist, or rock-contact
water. The fixed offscreen guide-seat and river-eye route captures also crush
this Single Layer Water surface nearly black; they are retained as a documented
capture-path defect and are not used to claim visual acceptance. The retained
gameplay evidence and hash-locked rejection record are
`zambezi_cross_current_sediment_water_v1.png` and
`zambezi_cross_current_sediment_water_v1_review.json`.

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

The runnable classification was reverified on August 2, 2026 after a filtered
Zambezi regeneration. `RaftSim.M6.CareerCatalog` confirms that the player-facing
`zambezi_reference_run` opens `/Game/RaftSim/Maps/L_Zambezi`, and
`RaftSim.P4.RiverMapLoads.L_Zambezi` passes a live PIE launch with the cooked
water field, upright five-person raft, all rapid markers, separate live foam,
Niagara water pool, and four non-colliding visual-terrain tiles. The schema-v16
saved-map audit and all seven focused Python contracts pass. This is runnable
acceptance only; it does not close any production-hydraulic or photoreal gate
below.

This makes the complete map launchable and paddleable with the normal gameplay
stack. It does not turn the inferred bed or rapid cues into real-world
bathymetry, navigation guidance, or validated Zambezi hydraulics.

The visual fallback materially improves surface scale and canyon breakup, and
the canonical guide-seat and river-eye views now contain visible solid bank
cover plus restrained tree and thorn-scrub silhouettes instead of completely
barren slopes. The default runnable launch now also exposes a restrained
ecology layer ahead of the raft: the accepted capture contains no camera-clipped
plant and no woody silhouette visibly intersecting the waterline. The V1
placement bracket that put cover on a 54.16° face and trees at the waterline was
rejected rather than documented as progress. The 30 m DEM still yields rounded large-scale cliff silhouettes,
however, and the project-owned tree crowns and small synthetic clumps remain
repetitive and visibly procedural. The expanded launch layer makes more of the
dry bank technically occupied, but the retained gameplay frame reads that
ground cover as a thin, repeated shoreline band rather than organic vegetation.
The views prove that the broken card foliage
is absent and that multi-height bank ecology is rendered; they do not prove
that the vegetation or terrain is photoreal. The runnable reference map is
therefore not yet accepted as photoreal.

The saved-map audit is written to
`docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_reference_scenario_map_validation.json`.
Schema v16 requires all 25 rapid markers, the Rapid 9 portage, one raft, player
start, runtime water configuration, the vertical-slice game mode, four
non-colliding, non-shadow-casting V15 visual-terrain tiles, the exact -48/-90
degree presentation light, two tagged non-colliding adaptive near-field banks,
the four-actor sun/sky/fill/fog atmosphere contract, absence of rejected
high-density bank actors, the
exact four vegetation mesh families and
12 instance components with an 8,927-instance total, exactly one tagged
1,200-instance camera-visible bank mosaic, three tagged camera-visible woody
components with the 58/57/117 accepted split and 24° slope-ceiling contract,
one 1,721-instance launch-cover component, three launch woody components with
the 44/43/87 accepted split, their full-route/dry-height/slope placement tags, and
the bounded launch-window shadow exception,
six separately tagged launch-talus components with 360 total source-grounded,
shadow-casting, non-colliding rock analog instances and their explicit
no-lithology/no-hydraulic-authority contract, plus the Zambezi-specific
material instance, its project-owned parent, and material-retone tags,
one conditioned profile waterline value per talus instance, and a bounded
render-only vertex-red wet-bank mask on the two adaptive near-field meshes,
zero legacy Zambezi PVE actors, and
exactly one
non-colliding physical-corridor ribbon bound through the isolated Single Layer
Water parent with the moving-normal contract tags. The saved material asset is
also covered by `RaftSim.M9.FZambeziSingleLayerWater`; grid-normal behavior is
covered by `RaftSim.M9.FZambeziOrganicTerrainNormals`, and the talus instance
and scalar contract are covered by `RaftSim.M9.FZambeziTalusMaterial`. Schema
v16 additionally
requires global-station preservation, the global-station authority tag, all 25
procedural rapid records, the Rapid 9 visualization-only portage policy, and
the `RaftSimSafeLaunchApron` tag.
The focused runtime gate is
`RaftSim.P4.RiverMapLoads.L_Zambezi`; it
now fails unless the loaded map produces live breaking sites and production
Niagara roller and aerosol activity, stays upright before and after the first
crew command, retains five attached crew avatars, and has zero swimmers.

The live surface now exposes its advected solver foam on a separate masked
rapid-foam mesh instead of increasing opacity on the broad moving-water grid.
The underlying live carrier remains optically disabled, preserving the prior
rectangular-edge correction. The foam component copies the solver-displaced
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
