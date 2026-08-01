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

## Production status and gates

The full Rapid 1–25 reference route is defined. Conflicting high-water route
descriptions (Rapid 11–23 and Rapid 14–25) are preserved as disabled candidates
instead of silently choosing one. Only the full reference route is selectable.

Promotion still requires local-guide approval of stations, lines, portages,
access, and rescue routes; geospatial review of the centerline/datum; rights
review of the supplied files; seasonal-flow reconciliation; a validated C++
hydraulic window for every rapid; and desktop/VR visual and performance passes.
These gates block production hydraulic-fidelity, lifelike, and release claims;
they do not hide or disable the explicitly labeled reference Free Run.
