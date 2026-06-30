# TODO

## Rough First Draft Outline

This project is a photo-realistic, physically accurate white water rafting simulator, but the active implementation target is now a headless 2.5D dual-solver modeling system that can later ingest real river data.

The old 2D river/raft path is retired. Future physics work starts with:

- GeoClaw as the offline 2.5D shallow-water/geophysical-flow reference model.
- A custom C++ reduced shallow-water / height-field solver as the runtime candidate.
- Identical procedurally generated and real-world geospatial scenarios applied to both solvers.
- A variable cascading 2.5D scenario package that models California-style pool-and-drop rivers as connected reaches with different slopes, roughness, hydraulic controls, and rapid/drop transitions.
- A comparison and tuning harness that makes the C++ model match GeoClaw before Unreal production depends on live water.
- Real river course, elevation, imagery, gauge, season, and difficulty presets that become validated scenario packages.

See [Physics Engine Plan](docs/physics-engine-plan.md) for the overall physics architecture.
See [2.5D Dual-Solver Simulation Plan](docs/2.5d-simulation-plan.md), [GeoClaw Reference Solver Transition Plan](docs/geoclaw-transition-plan.md), and [Custom C++ Engine Full Validation Plan](docs/custom-cpp-engine-validation-plan.md) for the GeoClaw/C++ validation workflow and live-water acceptance gate.
See [Real-World River Content And Seasonal Flow Plan](docs/real-world-river-content-plan.md) for geospatial extraction, rapid identification, seasonal flow research, adaptive parameters, and the future river/season/difficulty picker.
See [Free And AI Asset Policy](docs/free-and-ai-asset-policy.md) for the current art/sound sourcing decision, [Art Asset Source Research](docs/art-asset-source-research.md) for visual asset source notes, and [Audio Asset Sourcing Plan](docs/audio-asset-sourcing-plan.md) for audio source research, 3D spatial audio, manifests, and release-gate vendor notes.
See [Unreal Engine Full Game Plan](docs/unreal-engine-game-plan.md) for the full game roadmap after Python modeling and profiling are complete, including local AI voice commands, crew conversation systems, networked crews, and fully immersive 3D audio.
See [Chrono Water And Raft Coupling Plan](docs/chrono-water-raft-coupling-plan.md) for the fixed-step bridge between the shallow-water solver, Chrono raft kinematics, elastic rock impacts, and inelastic bed grounding.

## Milestone 0: Python Physics Research Foundation

- [x] Create a Python package for the physics engine.
- [x] Add pytest-based test infrastructure.
- [x] Add deterministic fixed-timestep simulation loop.
- [x] Add vector and quaternion math helpers.
- [x] Add telemetry output for every force contribution.
- [x] Add simple plotting for trajectories, force vectors, and raft orientation.
- [x] Document reference papers, validation assumptions, and model limitations.
- [x] Define the first physical accuracy targets for raft, paddle, current, and collision behavior.
- [x] Evaluate candidate physics backends and integrate Project Chrono as an optional backend.
- [x] Build a legacy 2D prototype.
- [ ] Delete or replace legacy 2D code and examples after the 2.5D scenario/solver harness exists.

## Milestone 1: Shared 2.5D Scenario Schema

- [x] Define solver-neutral scenario metadata.
- [x] Define grid bounds, resolution, timestep policy, and duration.
- [x] Define bed elevation, initial depth/surface, initial velocity/momentum, and wet/dry masks.
- [x] Define boundary conditions: inflow, outflow, wall/bank, and optional time-varying hydrographs.
- [x] Define feature encoding for rocks, ledges, constrictions, holes, laterals, boils, shallows, strainers, and wave trains.
- [x] Define optional real-world provenance fields: river id, section id, source manifest, coordinate reference system, gauge source, season preset, flow percentile, difficulty preset, and confidence scores.
- [x] Define raft physical parameters and probe/sample sets.
- [x] Export `scenario.json`, bed grid, initial state, feature metadata, probes, and diagnostic plots.
- [x] Add schema validation tests.
- [x] Generate deterministic fixture scenarios.
- [x] Generate deterministic procedural rafting scenarios from seed.

## Milestone 2: PyClaw 2.5D Reference Solver

Superseded as the active acceptance reference by Milestone 14 GeoClaw transition. Keep PyClaw artifacts as legacy regression data.

- [x] Add PyClaw as an optional research dependency.
- [x] Add an environment/setup check for PyClaw availability.
- [x] Implement a PyClaw scenario loader for the shared 2.5D scenario package.
- [x] Run canonical shallow-water fixtures: flat pool, uniform channel, dam-break/bore, bed step, constriction, and wet/dry shoreline.
- [x] Export PyClaw frames for `h`, `eta`, `u`, `v`, `hu`, `hv`, wet/dry masks, surface normals, and Froude number.
- [x] Export probe time series and cross sections.
- [x] Validate mass conservation and bounded velocities.
- [x] Add SWASHES-style analytic validation cases where practical.
- [x] Run the first procedurally generated rafting scenario in PyClaw.

## Milestone 3: Custom C++ Reduced Shallow-Water / Height-Field Solver

- [x] Create a standalone C++ solver library/executable outside Unreal.
- [x] Load the same shared 2.5D scenario package used by PyClaw.
- [x] Implement deterministic fixed-step stepping.
- [x] Implement reduced shallow-water / height-field state for `h`, `eta`, `u`, `v`, `hu`, `hv`, and wet/dry masks.
- [x] Implement bed slope, roughness/friction, and boundary source terms.
- [x] Implement stable wet/dry handling.
- [x] Implement authored feature forcing for holes, laterals, boils, wave trains, ledges, and shallows.
- [x] Export the same field, probe, cross-section, and telemetry channels as PyClaw.
- [x] Add C++ unit tests and fixture regression tests.
- [x] Add a command that runs one shared scenario and writes comparison-ready output.

## Milestone 4: Dual-Solver Comparison And Tuning Harness

Legacy PyClaw/C++ comparison milestone. Milestone 14 replaces the active acceptance reference with GeoClaw.

- [x] Run PyClaw and C++ on identical scenario packages.
- [x] Compare `h`, `eta`, `u`, `v`, `hu`, `hv`, wet/dry masks, surface normals, and slopes.
- [x] Compare probe time series and cross sections.
- [x] Compare mass conservation, energy trends, Froude number, hydraulic jump location, wave crest/trough location, and hole retention geometry.
- [x] Add L1/L2/Linf field-error summaries.
- [x] Add feature-location and feature-strength error summaries.
- [x] Add runtime cost per simulated second for both solvers.
- [x] Add scenario pass/fail thresholds.
- [x] Tune C++ numerical coefficients, friction, roughness, and authored feature forcing against PyClaw.
- [x] Promote passing scenarios to regression fixtures.

## Milestone 5: 2.5D Raft Coupling Against Both Solvers

- [x] Add 6-DoF raft state with position, orientation quaternion, linear velocity, and angular velocity.
- [x] Add raft mass, inertia tensor, gravity, guide/passenger mass offsets, and sampled tube/floor patches.
- [x] Define a solver-neutral water query API for surface height, normal, depth, velocity, wet/dry state, bed height, roughness, and feature tags.
- [x] Apply buoyancy from submerged sample depth and local surface normal.
- [x] Apply vertical damping, horizontal water drag, surface-slope forces, and added-mass approximation.
- [x] Add bed, rock, ledge, and shallow grounding contact.
- [x] Add paddle blade pose, depth, and blade-water relative velocity.
- [x] Run raft-force sampling against PyClaw output fields.
- [x] Run raft-force sampling against custom C++ runtime fields.
- [x] Compare raft force envelopes, trajectories, and outcomes between the two solvers.

## Milestone 6: 2.5D White Water Feature Validation

- [x] Validate standing wave clear, stall, surf, and flush cases.
- [x] Validate hole depression, upstream retention, aerated damping, and downstream boil/upwelling behavior.
- [x] Validate lateral wave side impulse and roll torque.
- [x] Validate eddy-line yaw/roll coupling.
- [x] Validate shallow shelf grounding and pivot behavior.
- [x] Validate submerged rock scrape/launch behavior.
- [x] Validate deterministic boil/upwelling vertical impulses.
- [x] Add outcome summaries for clear, stalled, surfed, flushed, grounded, pinned, or flipped runs.

## Milestone 7: Profiling, Parameter Fitting, And Runtime Budgets

- [x] Profile PyClaw reference runs for research-loop cost.
- [x] Profile the custom C++ solver for target runtime cost.
- [x] Profile raft coupling and probe/export cost.
- [x] Add parameter sweep scripts for roughness, feature forcing, raft drag, buoyancy, grounding, and contact coefficients.
- [x] Fit C++ solver and raft-force parameters to PyClaw reference outputs.
- [x] Produce baseline performance reports for canonical and generated scenarios.
- [x] Define desktop, VR, and handheld physics budgets before Unreal production begins.
- [x] Freeze the first shared scenario, telemetry, replay, and parameter schemas.

## Milestone 8: Chrono And Native Runtime Integration

- [x] Decide which raft dynamics run in custom C++ versus Project Chrono.
- [x] Create a standalone native C++ Chrono smoke test outside Unreal.
- [x] Couple Chrono raft/contact dynamics to the custom C++ water field.
- [x] Compare native Chrono/custom-water telemetry against Python/PyClaw reference scenarios.
- [x] Keep Chrono::FSI as an optional experiment/reference path, not the baseline runtime dependency.
- [x] Preserve the custom C++ reduced water solver as the primary Unreal runtime candidate.

## Milestone 9: Real-World River Data And Seasonal Flow Pipeline

- [x] Create a candidate river/region inventory for the first playable sections.
- [x] Record source availability and licensing/attribution notes for elevation, hydrography, imagery, gauges, guide references, and field media.
- [x] Pull 3DEP/state lidar terrain and 3DHP/NHD/OSM hydrography for one representative river section.
- [x] Extract centerline, downstream stationing, banks, cross sections, channel width, gradient, constrictions, and roughness indicators.
- [x] Build a `source_manifest.json` format for geospatial, hydrology, imagery, and review provenance.
- [x] Identify candidate rapids from DEM slope, constrictions, boulder density, foam/whitewater imagery texture, bends, eddies, ledges, guide notes, and access points.
- [x] Define manual rapid-review labels for pools, riffles, wave trains, holes, ledges, laterals, strainers, portages, and access points.
- [x] Pull USGS/NWIS gauge history, NOAA/NWPS/National Water Model context, StreamStats estimates, and local seasonal references where available.
- [x] Derive runnable season windows, flow percentile bands, gauge-to-section transfer functions, stage/depth/width estimates, and data confidence scores.
- [x] Map river + season + flow level + difficulty into solver parameters: boundary inflow/outflow, depth, momentum, roughness, aeration/turbulence, hole retention, wave trains, eddy-line shear, boil strength, shallows, hazards, raft drag, paddle catch, and damping.
- [x] Build the player-facing data model for region, river, section, season, flow level, difficulty, and raft/crew setup.
- [x] Convert at least one real-world river/season/difficulty selection into a shared scenario package that both PyClaw and the custom C++ solver can load.
- [x] Create low, median, and high runnable flow validation matrix, including PyClaw availability/run status and C++ smoke results; this is now a legacy baseline and GeoClaw/C++ revalidation moves to Milestone 14.
- [x] Export an Unreal-ready real-world corridor package for later visualization: terrain, imagery masks, centerline, banks, rapids, hazards, flow presets, and confidence metadata.

## Milestone 10: Python-To-Unreal Readiness Gate

Conditionally superseded for live water by Milestone 14. Telemetry/replay playback can still use these artifacts; live custom water needs GeoClaw revalidation.

- [x] Complete legacy PyClaw reference scenarios.
- [x] Complete custom C++ solver scenarios.
- [x] Complete dual-solver comparison and tuning reports; current gate decision is approved after shallow-cell-aware velocity/Froude comparison.
- [x] Complete 2.5D raft coupling validation against both solvers.
- [x] Complete the first real-world river section scenario with season, flow, difficulty, gauge, imagery, terrain, and source-manifest data.
- [x] Validate adaptive fluid parameters across low, medium, and high runnable flows for at least one real-world section.
- [x] Complete profiling and runtime budget reports.
- [x] Export representative telemetry/replay files for Unreal visualization.
- [x] Export at least one real-world corridor package for Unreal preproduction.
- [x] Write a Python-to-Unreal readiness report with risks, budgets, runtime choices, and accepted model limitations.
- [x] Explicitly record the gate decision: production Unreal project start is approved, with telemetry/replay playback as the first Unreal integration target.

## Milestone 11: Unreal Engine Full Game Production

- [x] Re-check the latest stable Unreal Engine 5.x feature set, then choose the exact version for visualization and VR.
- [x] Create the Unreal project only after the readiness gate is complete.
- [x] Enable the current UE5 photoreal open-world stack where supported: Nanite, Nanite foliage, Nanite landscapes/splines/tessellation, Lumen, Virtual Shadow Maps, World Partition, PCG, Niagara, Substrate/material layering, and OpenXR.
- [x] Create the Unreal module/plugin skeleton: core, physics bridge, river, raft, input, UI, and debug modules.
- [x] Integrate the custom C++ water solver as the runtime water field candidate.
- [x] Integrate Chrono/custom raft dynamics as selected by the readiness report.
- [x] Implement the fixed-step Chrono water/raft bridge: custom C++ shallow-water snapshot feeds Chrono raft substeps, Chrono returns authoritative raft pose, velocity, contacts, and force telemetry.
- [x] Add deterministic raft patch sampling for buoyancy, drag, added mass, slope force, eddy-line shear, boil/upwelling impulse, paddle blade forces, and feature tags.
- [x] Build Chrono collision geometry from rocks, banks, ledges, shallows, strainers, and bed/corridor data.
- [x] Add partially elastic rock collision presets for rubber-raft impacts: restitution, tube stiffness, damping, friction, scrape/bounce/pin telemetry, and parameter sweeps.
- [x] Add strongly inelastic riverbed grounding presets: near-zero restitution, high damping, grounding friction, stick-slip, contact hysteresis, scrape telemetry, and shallow-shelf pivot tests.
- [x] Start with one-way water-to-raft coupling; add optional bounded raft-to-water displacement/source terms only after the bridge is stable and validated.
- [x] Add native fixtures for flat pool float, current drift, standing wave lift, eddy-line yaw, rock bounce, riverbed grounding, shallow shelf pivot, and pin/release.
- [x] Keep Unreal Chaos available only for incidental non-authoritative effects.
- [x] Enable OpenXR-based VR support.
- [x] Implement telemetry/replay playback in Unreal before live native physics.
- [x] Define fixed-step water/raft scheduling and Unreal render interpolation.
- [x] Set up Enhanced Input actions for VR controllers, keyboard, mouse, and gamepad.
- [x] Build the first-person guide camera with flat-screen and VR comfort options.
- [x] Build river, season, flow, difficulty, and raft/crew selection UI from validated data assets.
- [x] Add local/offline AI integration layer for speech recognition, command intent parsing, crew dialogue, and optional local speech synthesis.
- [x] Implement guide voice commands that map spoken instructions into deterministic crew intents: forward paddle, back paddle, left/right paddle, stop, brace, hold on, high side, rescue, and recovery commands.
- [x] Add confidence thresholds, push-to-talk/open-mic settings, noisy-river audio tests, subtitles, accessibility fallbacks, and manual input parity for all voice commands.
- [x] Add AI-assisted crew conversation with passenger personas, trust, fear, fatigue, skill, river knowledge, and scenario state, while keeping gameplay-critical paddling under explicit command-state control.
- [x] Add telemetry for recognized phrase, intent, confidence, command latency, crew response, conversation state, and command outcome.
- [x] Build the first development art/audio source policy and defer downloaded/professional library purchases for water, raft, paddle, rocks, weather, Foley, UI, ambience, and visual assets until release-readiness.
- [x] Prototype interactive water audio with free/open, first-party generated, procedural, and AI-generated development assets first, using solver telemetry for flow speed, aeration, turbulence, raft impacts, paddle catches, rock scrapes, weather, and camera perspective.
- [x] Add 3D spatial audio as a core roadmap feature for VR/headphones, stereo speakers, and surround: attenuation, spatialization, binaural/HRTF, ambisonic beds, reverb, occlusion, and large-water-source behavior.
- [x] Validate 3D audio from the stern guide seat for nearby hazards, rapids, hydraulics, crew positions, voice commands, multiplayer voice, shore/canyon reflections, raft contacts, underwater/near-water states, and rescue cues.
- [x] Build the first rapid vertical slice with training, scoring, restart, replay, and debug force visualization.

## Milestone 12: Networked Human Crew Multiplayer

- [x] Plan network play after the single-player guide experience, physics runtime, local voice commands, and AI crew systems are stable.
- [x] Support a full human raft crew where every boat seat can be occupied by a human player.
- [x] Define player roles: stern guide, left/right paddlers, bow paddlers, safety/rescue responsibilities, and optional spectator/scout roles.
- [x] Add integrated voice communication for everyone on the boat, with push-to-talk/open-mic, mute, volume, subtitles/transcription options, moderation hooks, and privacy settings.
- [x] Decide networking architecture: listen server, dedicated server, relay/session service, LAN/offline co-op experiments, authoritative host, or hybrid rollback/prediction.
- [x] Replicate guide commands, human paddle strokes, brace/hold-on actions, rescue actions, crew animation state, passenger/seat state, raft contacts, and outcome telemetry.
- [x] Keep authoritative raft/water physics deterministic enough for multiplayer replay, debugging, and desync detection.
- [x] Add latency compensation and prediction for paddle strokes, raft impacts, rescue grabs, swimmer state, and VR/controller poses.
- [x] Add seat assignment, lobby/invite flow, ready checks, reconnect, host migration or session recovery, and AI takeover for dropped players.
- [x] Add multiplayer-specific scoring for crew coordination, command clarity, safety, line execution, rescue timing, and communication.
- [x] Add network voice and gameplay telemetry for debugging: packet loss, ping, jitter, command latency, voice activity, paddle timing, and raft-state divergence.
- [x] Validate desktop/VR mixed crews, accessibility fallbacks, and comfort settings for each connected player.

## Milestone 13: Production Audio Asset Sourcing And Sound Design

- [x] Treat free/open, first-party generated, procedural, and AI-generated art/audio assets as the active development backbone.
- [x] Defer paid/professional art and sound asset purchases until release-readiness proves free/open and AI-generated assets are not good enough.
- [x] Research and compare BOOM Library, Pro Sound Effects, A Sound Effect, Soundly, Fab audio packs, Sound Ideas/Sounddogs-style catalogs, Freesound CC0/CC-BY assets, and BBC Sound Effects licensing.
- [x] Preserve high-value water, weather, impact, Foley, ambience, UI, gear, and visual-asset vendor research without purchasing or trialing paid libraries yet.
- [x] Keep a custom field-recording plan as future/reference material for real rivers, rapids, flow levels, guide-seat perspective, shore perspective, eddies, raft contacts, paddle strokes, hydrophone captures, ambisonic/spatial beds, surround ambience, and crew reactions; use only first-party/free captures during development.
- [x] Define audio asset manifest schema: source, license, attribution, platform rights, sample rate, bit depth, channels, mic setup, location/date, processing chain, loop points, UCS metadata, attenuation preset, spatialization mode, ambisonic format/order, reverb/occlusion behavior, intended playback context, and approval status.
- [x] Define AI audio manifest fields: tool, model, version, prompt, seed, date, account/license tier, output terms, review status, similarity check, and development/shipping flag.
- [x] Add LFS/storage rules for raw recordings, future purchased libraries, edited masters, generated prototypes, and Unreal-ready compressed exports.
- [x] Build an interactive MetaSounds or middleware prototype for river roar, nearby rapids, spray, foam, paddle catch, raft scrape, rock impact, weather, canyon reflections, and crew voice layering.
- [x] Build 3D audio presets for point sources, line/area water sources, large rapids, ambisonic ambience, occluded rock/bank sounds, raft contact, underwater/near-water perspective, crew voice, guide commands, and multiplayer voice chat.
- [x] Validate spatial audio on stereo speakers, headphones, VR binaural/HRTF, and 5.1/7.1 surround where supported.
- [x] Add spatial-audio debug tools for emitter position, attenuation radius, spread, occlusion traces, reverb sends, ambisonic rotation, voice count, mix priority, and runtime cost.
- [x] Evaluate Wwise and FMOD only if Unreal-native audio/MetaSounds are insufficient for authoring, mixing, localization, memory, or platform workflow.
- [x] Define AI audio prohibited use cases: unclear commercial rights, unlicensed voice cloning, recognizably similar music, celebrity/style imitation, and any core gameplay cue that cannot be reviewed/reproduced.
- [x] Validate audio in stereo, headphones, VR spatial audio, noisy voice-command conditions, and multiplayer voice-chat scenarios.

## Milestone 14: GeoClaw Reference Solver Transition

- [x] Freeze existing PyClaw outputs as legacy regression artifacts, not acceptance targets.
- [x] Add GeoClaw availability/setup checks and document system dependencies.
- [x] Build a shared-scenario-to-GeoClaw exporter for `setrun.py`, topography files, initial water state, roughness, boundaries, hydrographs, AMR regions, and fixed-grid output.
- [x] Convert canonical fixtures to GeoClaw: flat pool, uniform channel, dam-break/bore, bed step, constriction, wet/dry shoreline, sloping channel with Manning friction, and drop/ledge over variable topography.
- [x] Convert rafting fixtures to GeoClaw: boulder garden, cascading wave train, hydraulic hole/downstream boil, lateral wave, eddy-line shear, shallow shelf, and real-world low/median/high flows.
- [x] Normalize GeoClaw fixed-grid outputs into the frozen field/probe/cross-section telemetry schema.
- [x] Update the comparison harness from PyClaw-vs-C++ to GeoClaw-vs-C++.
- [x] Retune C++ wet/dry handling, roughness, damping, feature forcing, velocity/Froude masks, and raft-force parameters against GeoClaw.
- [x] Re-run raft coupling against GeoClaw outputs and C++ fields and compare force envelopes, trajectories, and outcomes.
- [x] Regenerate the Python-to-Unreal readiness report with GeoClaw as the approved reference solver before live Unreal water depends on the custom C++ solver.

## Milestone 15: Variable Cascading 2.5D Scenario Package

This milestone replaces the current monolithic/mostly uniform 2.5D scenario package with a river-reach sequence model suitable for California pool-and-drop rivers. Each playable section should become an ordered chain of locally parameterized 2.5D reaches connected by explicit hydraulic transition zones.

- [x] Define `reach` metadata: station range, local grid transform, slope profile, width profile, bank shape, bed roughness, boulder density, vegetation/debris flags, and confidence score.
- [x] Define `drop_transition` metadata between reaches: crest station, bed-elevation fall, ramp/ledge length, tailwater depth, expected hydraulic control, recirculation risk, aeration/turbulence proxy, and hazard tags.
- [x] Encode pools separately from rapids: low-gradient recovery pools should have their own depth, eddy, recirculation, and tailwater controls rather than being treated as inactive gaps.
- [x] Support a sequence of reach-local grids with overlap/ghost zones or an equivalent stitched global grid so GeoClaw and C++ consume identical bathymetry, boundaries, and initial state.
- [x] Add conservation handoff checks across reach boundaries: mass flux, momentum flux, surface-elevation continuity where appropriate, energy loss across drops, and bounded wet/dry fronts.
- [x] Add procedural generators for California-style pool-and-drop patterns: pool, constricted tongue, ledge/drop, wave train, recovery eddy, boulder garden, and next pool.
- [x] Add South Fork American seed scenarios with variable slopes and rapid/drop transitions before generalizing to other rivers.
- [x] Run GeoClaw reference cases over the same cascading package and normalize fixed-grid output per reach and for the stitched river window.
- [x] Extend the custom C++ solver loader to consume the cascading package without changing scenario semantics.
- [x] Tune C++ section-handoff, roughness, dissipation, wet/dry, and feature-forcing coefficients against GeoClaw cascading outputs.
- [x] Add raft validation cases for pool entry, drop entry, hydraulic-hole surf/flush, eddy recovery, boulder-garden impacts, and transition-boundary crossings.
- [x] Export Unreal corridor metadata that preserves reach/drop IDs for streaming, debug overlays, audio, VFX, and designer review.

## Milestone 16: Full Custom C++ Engine Validation Gate

This milestone turns the custom C++ shallow-water / height-field solver from a runtime candidate into an accepted Unreal live-water candidate by comparing full GeoClaw reference runs, C++ outputs, raft outcomes, and runtime budgets on the same solver-neutral packages.

- [x] Freeze the scenario matrix and threshold tiers for smoke, research-accepted, Unreal-prototype, and production-candidate validation.
- [x] Run full GeoClaw fixed-grid reference simulations for canonical, rafting, real-world low/median/high, and South Fork cascading suites; do not count initial-state-only fallback normalization as full validation.
- [x] Run C++ reduced and finite-volume solver modes on the same packages with versioned manifests for CFL, dry tolerance, roughness, feature forcing, bed-slope source scale, and cascading metadata.
- [x] Compare GeoClaw and C++ fields, probes, cross sections, mass/energy/Froude diagnostics, wet/dry masks, feature localization, and reach/drop window outputs against frozen thresholds.
- [x] Validate geometry-specific cases: hydrostatic/sloping-channel balance, wet/dry shorelines, bed steps, constrictions, drops/ledges, tailwater controls, and stitched reach/drop boundary handoffs.
- [x] Re-run raft coupling validation for pool entry, drop entry, hydraulic-hole surf/flush, eddy recovery, boulder impacts, shallow shelves, pins/releases, and transition-boundary crossings against GeoClaw-derived and C++ water fields.
- [x] Promote passing GeoClaw/C++/raft comparison runs into regression fixtures or artifact manifests with JSON and Markdown reports.
- [x] Profile validated C++ configurations against desktop, VR, and handheld runtime budgets and record deterministic replay results.
- [x] Regenerate the GeoClaw-to-Unreal readiness report and explicitly approve or block live custom water based on the full validation gate.

## Technical Notes To Revisit

- [ ] Decide when to physically remove legacy 2D code, tests, examples, and videos from the repo.
- [x] Decide whether PyClaw is enough or GeoClaw-specific behavior is required for river bathymetry and wet/dry cases: GeoClaw is now the target reference solver.
- [ ] Decide if SWASHES fixtures should be vendored, regenerated, or manually encoded.
- [ ] Decide whether the C++ solver starts as CPU-only or gets a GPU path after correctness is established.
- [ ] Decide how much authored feature forcing is acceptable versus pure shallow-water dynamics.
- [ ] Decide the canonical storage format for cascading reach/drop packages: one stitched grid with reach annotations, multiple reach-local grids with ghost zones, or both.
- [ ] Evaluate Chrono::FSI only after the GeoClaw/custom-C++ solver comparison path is stable.
- [ ] Identify reference footage, river data, aerial/satellite imagery, flow history, and expert guide feedback needed for validation.
- [ ] Decide which geospatial formats become canonical for source data, generated scenarios, and Unreal corridor packages.
- [ ] Re-check latest UE5 rendering/geospatial plugin capabilities at the Python-to-Unreal readiness gate.
- [ ] Decide local AI model/runtime strategy for desktop, VR, handheld, and future console targets.
- [ ] Decide how much crew dialogue is generated locally versus authored as recorded barks, constrained templates, or designer-approved lines.
- [ ] Decide latency, privacy, profanity/safety, save-data, and deterministic replay requirements for voice and conversation systems.
- [ ] Decide whether free/open and AI-generated art/audio assets are good enough for release, and buy paid libraries only for proven gaps.
- [ ] Decide whether Unreal-native audio/MetaSounds is enough or whether Wwise/FMOD should be adopted for the full UE5 version.
- [ ] Decide the binaural/HRTF plugin/runtime path, ambisonic capture/playback format, surround targets, reverb/occlusion strategy, and spatial-audio certification requirements for the first VR build.
- [ ] Decide multiplayer network architecture, voice communication stack, session backend, crossplay scope, moderation requirements, and host/dropout recovery.
- [ ] Investigate multiplayer feasibility only after the single-player guide experience feels good enough to preserve under network latency.

## Immediate Next Steps

- [x] Remove 2D-first assumptions from active docs.
- [x] Define the shared 2.5D scenario schema.
- [x] Add fixture scenario generation for flat pool, channel flow, dam-break/bore, bed step, constriction, and wet/dry shoreline.
- [x] Add deterministic procedural 2.5D rafting scenario generation from seed.
- [x] Add a PyClaw availability check and first reference runner as a legacy baseline; GeoClaw availability/checks are now Milestone 14.
- [x] Add a C++ solver directory and build skeleton.
- [ ] Implement suite-level JSON and Markdown reports for the full C++ validation gate.
- [ ] Draft the first candidate river inventory and source manifest.
- [ ] Prototype course/elevation extraction for one river section.
- [ ] Define the first rapid-review labels and seasonal flow/difficulty parameter mapping.
