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
  "$PWD/unreal/SmokeEmIfYouGotEm.uproject" -unattended -nop4 -nosplash -NoSound \
  -ExecCmds="RaftSim.CreateLandscapeImportCandidateMaps zambezi_batoka_gorge,Quit"
```

This saves the locally generated, git-ignored map at
`/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_ZambeziBatokaGorge_PhysicalCorridorCandidate`.
The map contains 25 editor-only rapid marker actors, a player raft and start,
the vertical-slice game mode, and a live-water runtime configuration. Rapid 9
is tagged as a mandatory commercial portage. Gameplay hides the labels; the
World Outliner and editor viewport retain them for authoring.

The saved runnable map also contains four render-only source-terrain tiles with
the retained Batoka V12 world-aligned basalt material and V13 bounded visual
morphology. The morphology adds deterministic lava-flow terraces, joint
recesses, and talus variation only outside a 220 m protected river corridor,
fades out by 650 m, and is clamped to 4.5 m. It never changes the hidden
Copernicus Landscape used for collision, height queries, or physics. The actor
tags `RaftSimProceduralVisualMorphology`, `RaftSimBatokaWorldAlignedTerrain`,
and `RaftSimNonCollisionRenderSurface` make that authority boundary inspectable
in the generated map.

The active Zambezi dressing no longer loads the generic Procedural Vegetation
Editor species or their masked leaf cards. The generator creates four
project-owned, opaque, one-sided, vertex-colour Nanite meshes and places them as
non-colliding hierarchical instances:

- 2,100 `SM_RaftSim_Zambezi_RiparianTree_A_OpaqueV1` instances;
- 1,400 `SM_RaftSim_Zambezi_UmbrellaTree_B_OpaqueV1` instances;
- 1,400 `SM_RaftSim_Zambezi_ThornScrub_A_OpaqueV1` instances; and
- 700 `SM_RaftSim_Zambezi_SavannaGroundCover_A_OpaqueV1` instances.

All four use `M_RaftSim_Zambezi_OpaqueVegetation`, contain solid branch, crown,
or blade geometry rather than alpha cards, and carry the
`RaftSimZambeziOpaqueVegetation`, `RaftSimOpaqueVolumetricVegetation`,
`RaftSimSlopeScreenedPlacement`, `RaftSimNonCollisionRenderSurface`, and
`RaftSimProceduralVegetationFallback` tags. Placement searches a wider bank
area, rejects steep canyon-face candidates, and keeps the launch cameras and
navigable corridor clear. This removes the floating black/green triangle and
cliff-mounted-tree failures from the active Zambezi views; it does not establish
correct species, woodland ecology, or photoreal vegetation.

## Runnable reference status

The map is available from the main menu as **Zambezi: Boiling Pot to Mukuni
Beach**. It is a reference Free Run with the normal-big-water planning band.
The source-controlled runtime bundle lives under
`physics/data/real_world/zambezi_batoka_gorge/scenario_zambezi_run/runtime/`:

- `river_coordinate_map.json` maps the source-scale curved centerline into
  station/lateral coordinates used by the runtime solver.
- `cooked_flow_fields/` supplies a lightweight 30 km finite-volume seed. The
  centerline surface follows the conditioned Copernicus corridor; missing
  channel geometry and rapid cues are deterministic procedural infill.

This makes the complete map launchable and paddleable with the normal gameplay
stack. It does not turn the inferred bed or rapid cues into real-world
bathymetry, navigation guidance, or validated Zambezi hydraulics.

The visual fallback materially improves surface scale and canyon breakup, but
the 30 m DEM still yields rounded large-scale cliff silhouettes and the current
vegetation remains synthetic and is deliberately sparse outside the launch
vista. The canonical guide-seat and river-eye views prove that the broken card
foliage is absent, not that the vegetation or terrain is lifelike. The runnable
reference map is therefore not yet accepted as photoreal.

The saved-map audit is written to
`docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_reference_scenario_map_validation.json`.
Schema v4 requires all 25 rapid markers, the Rapid 9 portage, one raft, player
start, runtime water configuration, the vertical-slice game mode, four
non-colliding visual-terrain tiles, the exact four vegetation families and
5,600-instance total, and zero legacy Zambezi PVE actors. The focused runtime
gate is
`RaftSim.P4.RiverMapLoads.L_ZambeziBatokaGorge_PhysicalCorridorCandidate`.

## Production status and gates

The full Rapid 1–25 reference route is defined. Conflicting high-water route
descriptions (Rapid 11–23 and Rapid 14–25) are preserved as disabled candidates
instead of silently choosing one. Only the full reference route is selectable.

Promotion still requires local-guide approval of stations, lines, portages,
access, and rescue routes; geospatial review of the centerline/datum; rights
review of the supplied files; seasonal-flow reconciliation; a validated C++
hydraulic window for every rapid; approved southern African gorge species and
ecology; lifelike terrain, bank, vegetation, and water art; and desktop/VR
visual and performance passes. These gates block production hydraulic-fidelity
and lifelike claims; they do not hide or disable the explicitly labeled
reference Free Run.
