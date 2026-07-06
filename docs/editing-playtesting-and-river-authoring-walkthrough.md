# Editing, Playtesting, And River Authoring Walkthrough

This walkthrough is for opening the current RaftSim Unreal tools, editing reviewed river data, playtesting the vertical slice, and drafting additional rivers without bypassing the validation gates. The current production baseline is South Fork American. Colorado and Pacuare are selectable planning targets, but both remain review-gated until their source, hydrology, media-rights, guide-review, and validation blockers are closed.

## Before You Start

Use Unreal Editor 5.8 with `unreal/SmokeEmIfYouGotEm.uproject`. The expected local editor command on this machine is:

```bash
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor" "/Users/alexmoran/repos/SmokeEmIfYouGotEm/unreal/SmokeEmIfYouGotEm.uproject"
```

If the editor has stale binaries, build the editor target first:

```bash
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh" SmokeEmIfYouGotEmEditor Mac Development -Project="/Users/alexmoran/repos/SmokeEmIfYouGotEm/unreal/SmokeEmIfYouGotEm.uproject" -NoHotReload
```

Open tools from the Unreal main menu: `RaftSim Tools`. The registry for that menu is `unreal/Content/RaftSim/Tools/polished_tool_registry.json`.

## Core Editing Loop

1. Open `Replay + Debug Viewer`.
   Load the existing replay package and verify depth, velocity, Froude, wet/dry, feature tags, conservation deltas, raft trajectory, contact probes, and runtime-budget overlays before touching live river data.

2. Open `Rapid/River Editor`.
   Use it to review or edit station pins, reach and drop spans, polygons, raft lines, evidence references, guide notes, expected surf/flush/pin/release/flip outcomes, and export blockers.

3. Open `Feature Tuning Editor`.
   Keep physics-facing forcing conservative. Solver-state and raft-coupling edits must stay bounded, manifest-recorded, GeoClaw-compared, conservation-guarded, flow-dependent, and unable to hide physics failures. Visual-only and audio-only sliders can polish readability, but they must not change scoring-critical solver or raft state.

4. Open `Geospatial Import/Export Validator`.
   Check source manifests, CRS, local-to-WGS84 transforms, reach-local grids, stitched whole-window outputs, and round-trip metadata before exporting.

5. Use the validation buttons in this order:
   `Validate Source`, `Export Deterministically`, `Regenerate Solver Package`, `Validate Stitched Window`, `Run Round Trip`, `Run Live-Water Smoke`, then `Open Latest Report`.

6. Capture review evidence.
   Use the console command `RaftSim.CaptureToolEvidence` to open tool tabs and write screenshots plus a manifest under `docs/tool-captures/milestone25a/`.

7. Create reviewed tool DataAssets when needed.
   Use `RaftSim.CreateReviewedDataAssets` to generate reviewed assets under `/Game/RaftSim/Tools/Reviewed`.

Do not promote an edit if any blocking validation message remains. Reach-local authoring is allowed, but stitched whole-window validation outputs are required for acceptance.

## Playtesting Loop

1. Open `Vertical Slice Playtest Launcher`.
   It is wired through `unreal/Content/RaftSim/VerticalSlice/first_rapid_vertical_slice.json` and `unreal/Content/RaftSim/Automation/vertical_slice_acceptance_gate.json`.

2. Select from the catalog.
   The menu flow is recorded in `unreal/Content/RaftSim/UI/river_selection_catalog.json`: river, section, season, flow band, difficulty, raft setup, crew setup.

3. Prefer the South Fork baseline for real playtesting.
   South Fork has the strongest validated path. Colorado is a rowing/oar-rig planning prototype. Pacuare is a guided paddle-raft planning target with relative rain-fed flow bands only.

4. Match input mode to route style.
   Guided paddle-raft runs can use voice or manual crew commands. Rowing/oar-rig routes use manual oar controls only, with passenger paddle voice commands disabled.

5. Play both success and failure paths.
   A useful playtest covers training completion, technical clean-line completion, technical failure or rescue, restart, replay review, and after-action scoring.

6. Review telemetry after the run.
   Check safety incidents, swimmer/rescue state, line choice, boat angle, paddle efficiency, command timing, high-side timing, replay bookmarks, and debug overlays.

7. Keep evidence attached.
   Save reports, screenshots, replay manifests, and guide notes next to the relevant gate or river manifest. Loose notes are useful during exploration, but promotion evidence must be manifest-linked.

Run the Milestone 25A tooling gate when validating tool polish:

```bash
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" "/Users/alexmoran/repos/SmokeEmIfYouGotEm/unreal/SmokeEmIfYouGotEm.uproject" -unattended -nop4 -nosplash -NullRHI -NoSound -ExecCmds="Automation RunTests RaftSim.Milestone25A.PolishedToolingSliceGateManifest" -TestExit="Automation Test Queue Empty"
```

Run the release-readiness manifest gate when checking the broader release contract:

```bash
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" "/Users/alexmoran/repos/SmokeEmIfYouGotEm/unreal/SmokeEmIfYouGotEm.uproject" -unattended -nop4 -nosplash -NullRHI -NoSound -ExecCmds="Automation RunTests RaftSim.Milestone25.ReleaseReadinessGate" -TestExit="Automation Test Queue Empty"
```

## Adding More Rivers

Treat a new river as a source-controlled content package first, not as an Unreal-only level. Add it as review-gated until the validation evidence is strong enough to promote.

1. Choose the route style.
   Use `guided_paddle_raft` for passenger paddle-raft sections with optional voice commands. Use `rowing_oar_rig` for rowing routes with direct manual oar controls and no passenger paddle voice commands.

2. Create the source folder.
   Add `physics/data/real_world/<river_id>/source_manifest.json` using `physics/schemas/source_manifest.schema.json`. Add `flow_presets.json` only when the flow bands have clear provenance. If numeric discharge is not reviewed, use relative or planning bands and mark them blocked.

3. Register the river in the inventory.
   Update `physics/data/real_world/candidate_rivers.json`, `physics/data/real_world/candidate_river_inventory.json`, and `physics/data/real_world/player_selection_model.json` when the river should appear in planning and selection models.

4. Add or extend source catalog entries.
   Update `physics/data/real_world/source_catalog.json` for new DEM, lidar, hydrography, imagery, gauge, guide-feedback, protected-area, or field-media sources. Do not vendor heavy media or guidebook text unless rights are explicit.

5. Draft the Unreal river manifest.
   Add a file under `unreal/Content/RaftSim/River/`, following the pattern of `south_fork_alpha_content_expansion.json`, `colorado_rowing_route_editor_pass.json`, or `pacuare_river_third_target_editor_pass.json`. Include `river_id`, `section_id`, route style, flow bands, route segments or content nodes, guide-review requirements, annotation needs, input contract, and status.

6. Add it to the selection catalog.
   Update `unreal/Content/RaftSim/UI/river_selection_catalog.json` with river, section, seasons, flow bands, difficulty presets, raft setups, crew setups, route style, and validation status. New rivers should default to `requires_validation_before_playable` until the gates pass.

7. Add content coverage.
   Update `unreal/Content/RaftSim/Production/alpha_content_coverage_manifest.json` with biome, environment, art, audio, VFX, haptics, UI/accessibility, and platform-scalability targets. Highly detailed, immersive, photoreal landscape and foliage remain core goals, but readability and performance still gate promotion.

8. Add round-trip validation coverage.
   Update `unreal/Content/RaftSim/River/round_trip_validation.json` with a case for the new river. At first, it can be metadata-only like the Colorado planning case, but production promotion requires solver packages, GeoClaw/C++ comparison inputs, and fidelity-review overlays.

9. Build geospatial and annotation layers.
   Use JSON source manifests, GeoJSON vectors and annotations, GeoPackage for larger GIS workspaces, GeoTIFF or COG rasters, LAS/LAZ or COPC point clouds when needed, normalized JSON/CSV/Parquet gauge history, and versioned solver JSON plus `.npy` or `.npz` arrays.

10. Attach river-validation evidence.
    Every playable feature should be tied to station spans or geometry with footage timecodes, gauge history, aerial imagery dates, guide feedback, expected raft outcomes, confidence, rights/provenance, and flow context.
    Use `physics/data/real_world/reference_media_review_queue.json` to turn link-only media leads into station-aware review targets before changing art, water, or gameplay tuning. Keep third-party media link-only until creator, URL, date, station or reach, observed flow/weather, license or written permission, attribution, and allowed-use notes are recorded.

11. Generate or update solver packages.
    Existing South Fork seed packages can be regenerated with:

    ```bash
    python -m raftsim.examples.generate_real_world_scenario --write-full-package --output-dir outputs/real_world
    ```

    A new river needs matching generator support in `physics/src/raftsim/real_world.py` before it can produce solver-neutral packages, GeoClaw/C++ comparison inputs, stitched validation outputs, and Unreal corridor metadata.

12. Validate before promotion.
    Run source checks, deterministic export, round-trip validation, stitched-window validation, live-water smoke, physics regression replay, raft/contact fixtures, rescue outcome checks, and replay determinism checks. The river is not production-playable until those pass and the relevant reports are linked.

## Promotion Checklist For A New River

- Source manifest has CRS, sources, license/terms, rights, confidence, retrieval date, and processing version.
- Flow presets are backed by gauge, hydrology, rainfall, release, or guide-reviewed flow evidence.
- Media and guide feedback have rights/provenance status and timecodes where applicable.
- Rapid/reach annotations include expected surf, flush, pin, release, flip, swim, and rescue outcomes.
- Feature forcing is bounded, manifest-recorded, GeoClaw-compared, flow-dependent, and not hiding conservation failures.
- Reach-local grids export stitched whole-window validation outputs.
- GeoClaw and custom C++ inputs are generated from the same solver-neutral source package.
- Raft/contact, swimmer, rescue, scoring, replay, and input behavior are covered by fixtures.
- Unreal selection catalog marks unvalidated routes as blocked.
- Photoreal environment and foliage review passes without hiding hazards or rescue targets.

## Current River Status

| River | File | Status |
| --- | --- | --- |
| South Fork American | `unreal/Content/RaftSim/River/south_fork_alpha_content_expansion.json` | Baseline alpha authoring and validation planning target. Use first for playtests. |
| Colorado River | `unreal/Content/RaftSim/River/colorado_rowing_route_editor_pass.json` | Rowing/oar-rig planning route. Voice passenger paddle commands disabled. Needs gauge, guide, media, and geospatial review before playable promotion. |
| Pacuare River | `unreal/Content/RaftSim/River/pacuare_river_third_target_editor_pass.json` | Rain-fed guided paddle-raft planning route with a review-gated preview centerline/stationing scaffold for annotations only. Needs official hydrography, hydrology, protected-area/source-rights, field-media, and rainforest/gorge fidelity review before solver generation. |
