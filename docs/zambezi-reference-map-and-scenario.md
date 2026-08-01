# Zambezi reference map and scenario

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

The Unreal candidate is generated with:

```bash
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "$PWD/unreal/SmokeEmIfYouGotEm.uproject" \
  -unattended -nop4 -nosplash -NoSound -RenderOffscreen \
  -RaftSimCreateLandscapeImportCandidateMaps \
  -RaftSimLandscapeImportCandidateRiverId=zambezi_batoka_gorge \
  -RaftSimExitAfterEnvironmentAutomation
```

This saves the locally generated, git-ignored map at
`/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_ZambeziBatokaGorge_PhysicalCorridorCandidate`.
The logical package is in `DefaultGame.ini`'s shipping cook list. Because the
1.6 GB candidate remains reproducible and intentionally excluded from Git LFS,
the Mac and Windows packaging scripts build the editor and regenerate this one
river automatically when the map is absent, then fail closed if the package was
not created before cooking.
The map contains 25 editor-only rapid marker actors, a player raft and start,
the vertical-slice game mode, and a live-water runtime configuration. Rapid 9
is tagged as a mandatory commercial portage. Gameplay hides the labels; the
World Outliner and editor viewport retain them for authoring.

The saved runnable map also contains four render-only source-terrain tiles with
the retained Batoka V12 world-aligned basalt material and V14 bounded visual
morphology. The 72 m active-water half-width is followed by a hard 28 m dry-bank
buffer, so terrain vertices remain untouched for the first 100 m from the full
209-point source-aligned route polyline. The widest 73.44 m water edge retains
at least 26.56 m of unchanged shoreline. From 100-220 m the morphology fades in
smoothly; the current deterministic build's nearest conditioned vertex is
102.63 m from the polyline. The treatment reaches full strength on the lower
canyon wall by 220 m, and adds deterministic
lava-flow terraces, joint recesses, and talus variation under a 4.5 m vertical
cap. A broader rounded-slope mask within the near-bank envelope breaks up the
30 m DEM silhouette without manufacturing a hard water/land boundary. It never
changes the hidden Copernicus Landscape used for collision, height queries, or
physics. The actor tags `RaftSimProceduralVisualMorphology`,
`RaftSimBatokaNearBankMorphologyV14`, `RaftSimProtectedShorelineBuffer`,
`RaftSimBatokaWorldAlignedTerrain`, and `RaftSimNonCollisionRenderSurface` make
that authority boundary inspectable in the generated map.

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
  slope ceiling, leaving 232 placed instances.

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
phase, behind-water colour scale, and a 0.64 surface-opacity control. Two
opposed panners animate independently tiled normal-atlas layers, while bounded
world-space optical variation keeps commandlet captures from collapsing into a
single flat colour when temporal reflections are unavailable. The ribbon stays
non-colliding and render-only; the runtime water configuration and solver remain
the gameplay authority. The generated actor exposes
`RaftSimZambeziSingleLayerWater`, `RaftSimMovingMultiScaleWaterNormals`,
`RaftSimPhysicalCorridorWater`, and `RaftSimNonCollisionRenderSurface` tags.

The regenerated views remove most of the former camera-radial dark grooves and
show a lighter gray-green surface without reproducing the foreground depth
split that rejected the earlier global Single Layer experiment. The live
runtime can now add solver-triggered breaking-water, roller, aerosol, foam, and
mist components at the procedural rapid controls described below. This is an
incremental optical and runtime baseline, not final water art: realistic crest
geometry, local bathymetric transmission, seasonal calibration, and guide/art
approval remain open.

## Runnable reference status

The map is available from the main menu as **Zambezi: Boiling Pot to Mukuni
Beach**. It is a reference Free Run with the normal-big-water planning band.
The named-rapid source catalog, generated marker and simulator-run manifests,
Rapid/River Editor shell, player-facing scenario catalog, runtime map-load test,
and shipping cook list all classify it as the sixth runnable river. There are
no remaining `additional_active_environment` river entries in the current
portfolio.
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

`RaftSim.P4.RiverMapLoads.L_ZambeziBatokaGorge_PhysicalCorridorCandidate`
requires the raft to remain upright through the initial settle and after an
`AllForward` command, retain all five attached crew actors, and report zero
swimmers. The focused test passes, and the complete parameterized
`RaftSim.P4.RiverMapLoads` run passes all six maps with zero failures. The
renderer-backed result is `zambezi_safe_launch_crew_v1.png`; its review record
deliberately fails photoreal promotion while passing runnable launch acceptance.

This makes the complete map launchable and paddleable with the normal gameplay
stack. It does not turn the inferred bed or rapid cues into real-world
bathymetry, navigation guidance, or validated Zambezi hydraulics.

The visual fallback materially improves surface scale and canyon breakup, and
the canonical guide-seat and river-eye views now contain visible solid bank
cover plus restrained tree and thorn-scrub silhouettes instead of completely
barren slopes. The 30 m DEM still yields rounded large-scale cliff silhouettes,
however, and the project-owned tree crowns and small synthetic clumps remain
repetitive and visibly procedural. The views prove that the broken card foliage
is absent and that multi-height bank ecology is rendered; they do not prove
that the vegetation or terrain is photoreal. The runnable reference map is
therefore not yet accepted as photoreal.

The saved-map audit is written to
`docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_reference_scenario_map_validation.json`.
Schema v10 requires all 25 rapid markers, the Rapid 9 portage, one raft, player
start, runtime water configuration, the vertical-slice game mode, four
non-colliding visual-terrain tiles, the exact four vegetation mesh families and
eight instance components with a 7,032-instance total, exactly one tagged
1,200-instance camera-visible bank mosaic, three tagged camera-visible woody
components with the 58/57/117 accepted split and 24° slope-ceiling contract,
zero legacy Zambezi PVE actors, and
exactly one
non-colliding physical-corridor ribbon bound through the isolated Single Layer
Water parent with the moving-normal contract tags. The saved material asset is
also covered by `RaftSim.M9.FZambeziSingleLayerWater`. Schema v10 additionally
requires global-station preservation, the global-station authority tag, all 25
procedural rapid records, the Rapid 9 visualization-only portage policy, and
the `RaftSimSafeLaunchApron` tag.
The focused runtime gate is
`RaftSim.P4.RiverMapLoads.L_ZambeziBatokaGorge_PhysicalCorridorCandidate`; it
now fails unless the loaded map produces live breaking sites and production
Niagara roller and aerosol activity, stays upright before and after the first
crew command, retains five attached crew avatars, and has zero swimmers.

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
