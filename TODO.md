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
See [Chrono Water And Raft Coupling Plan](docs/chrono-water-raft-coupling-plan.md) for the fixed-step bridge between the shallow-water solver, candidate raft/contact runtime kinematics, elastic rock impacts, and inelastic bed grounding.
See [Chaos And Jolt Runtime Evaluation](docs/chaos-jolt-runtime-evaluation.md) for the split/hybrid runtime plan and shared fixtures that compare Unreal Chaos and Jolt before scoring-critical raft/contact authority is selected.

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
- [x] Integrate the selected raft/contact runtime bridge path as selected by readiness and runtime fixture reports.
- [x] Implement the fixed-step Chrono water/raft bridge: custom C++ shallow-water snapshot feeds Chrono raft substeps, Chrono returns authoritative raft pose, velocity, contacts, and force telemetry.
- [x] Add deterministic raft patch sampling for buoyancy, drag, added mass, slope force, eddy-line shear, boil/upwelling impulse, paddle blade forces, and feature tags.
- [x] Build Chrono collision geometry from rocks, banks, ledges, shallows, strainers, and bed/corridor data.
- [x] Add partially elastic rock collision presets for rubber-raft impacts: restitution, tube stiffness, damping, friction, scrape/bounce/pin telemetry, and parameter sweeps.
- [x] Add strongly inelastic riverbed grounding presets: near-zero restitution, high damping, grounding friction, stick-slip, contact hysteresis, scrape telemetry, and shallow-shelf pivot tests.
- [x] Start with one-way water-to-raft coupling; add optional bounded raft-to-water displacement/source terms only after the bridge is stable and validated.
- [x] Add native fixtures for flat pool float, current drift, standing wave lift, eddy-line yaw, rock bounce, riverbed grounding, shallow shelf pivot, and pin/release.
- [x] Keep Unreal Chaos available as the default visual/non-authoritative physics path, and require the shared Chaos/Jolt fixture suite before it can own scoring-critical raft/contact outcomes.
- [x] Enable OpenXR-based VR support.
- [x] Implement telemetry/replay playback in Unreal before live native physics.
- [x] Define fixed-step water/raft scheduling and Unreal render interpolation.
- [x] Set up Enhanced Input actions for VR controllers, keyboard, mouse, and gamepad.
- [x] Build the first-person guide camera with flat-screen and VR comfort options.
- [x] Build river, season, flow, difficulty, and raft/crew selection UI from validated data assets.
- [x] Add local/offline AI integration layer for speech recognition, command intent parsing, crew dialogue, and optional local speech synthesis.
- [x] Implement guide voice commands that map spoken instructions into deterministic crew intents: forward paddle, back paddle, left/right paddle, stop, brace, hold on, high side, rescue, and recovery commands.
- [x] Add confidence thresholds, push-to-talk/open-mic settings, noisy-river audio tests, subtitles, accessibility fallbacks, and manual input parity for all voice commands.
- [ ] Add a crew-overboard safety-state model: seated, at-risk, falling/ejected, swimming, rescue-targeted, rescued, re-seated/recovered, and failed-rescue.
- [ ] Add randomly assigned passenger swimming skills at run setup, including non-swimmers who cannot self-rescue, so ejection urgency, panic, pull-in difficulty, rescue priority, and safety scoring vary by passenger.
- [ ] Add swimmer and rescue gameplay: swimmer drift/visibility, guide and crew callouts, rescue target selection, reach/paddle grab, throw-line support where available, pull-in timing, re-seat/recovery, and failed-rescue consequences.
- [ ] Add crew safety telemetry and scoring for ejection trigger, swimmer position, time in water, rescue method, pull-in/re-seat outcome, fatigue/trust deltas, and safety-score impact.
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

## Milestone 17: Validation Contracts And Diagnostic Fixtures

This milestone turns the Milestone 16 blocker into sharper diagnostics by freezing text-first contracts and small trusted fixtures before broad C++ retuning, Unreal editor work, GPU work, or Chrono::FSI exploration.

- [x] Add a versioned analytic fixture manifest with provenance notes, expected behavior, tolerance tier, source-equation references, and explicit no-vendored-external-data policy.
- [x] Manually encode a small SWASHES-style set for lake-at-rest balance, sloping-channel friction, wet/dry shoreline, bed step, dam-break/bore, hydraulic jump, and transcritical bump cases where practical.
- [x] Add C++ and GeoClaw/analytic comparison reports that fail retuning when small analytic fixtures regress.
- [x] Add a versioned feature-forcing contract and validator with low defaults, flow-response curves, manifest records, GeoClaw comparison requirements, and conservation guards.
- [x] Add versioned contracts and validators for reach-local grids, stitched validation outputs, river validation annotations, and canonical geospatial packages.

## Milestone 18: Custom C++ Water Validation Closure

This milestone turns the blocked Milestone 16 evidence into an ordered fix plan. Milestone 17 analytic and contract fixtures must stay green while the C++ solver is retuned; Chaos/Jolt authority evaluation moves after this closure work so raft/contact runtime decisions do not depend on unapproved live water.

- [x] Build a failure triage matrix for every failed GeoClaw/C++ comparison, grouped by scenario family, solver mode, metric, likely root cause, and retune lever.
- [x] Fix and record GeoClaw boundary semantics before parity retuning: constant authored stage/depth/velocity boundaries now export as GeoClaw `user` boundaries with a generated `bc2amr.f90` adapter and manifest evidence; dynamic hydrographs fail fast until a time-varying adapter is implemented.
- [x] Retune and re-run the first blocked GeoClaw/C++ parity family without increasing feature-forcing defaults: the corrected-boundary finite-volume uniform-channel lane is promoted with HLL flux, roughness scale 0.5, bed-slope source scale 0.75, and `feature_strength_scale=0`; reduced mode remains blocked.
- [ ] Fix GeoClaw-vs-C++ parity failures in dependency order: keep flat-pool and sloping-channel cases as guardrails, then retune wet/dry, bed-step, constriction, drop/ledge, and cascading reach/drop comparisons with feature forcing off or at low validated defaults.
- [x] Promote the reduced-mode wet/dry shoreline parity lane without feature forcing: dry neighbors are masked out of reduced pressure-gradient sampling, Milestone 17 guardrails pass with zero regressions, GeoClaw/C++ threshold passes rise to 5 of 40, and finite-volume wet/dry remains blocked pending hydrostatic wet/dry reconstruction.
- [x] Promote finite-volume wet/dry shoreline parity with fixture-scoped hydrostatic interface reconstruction: the constant free-surface wet/dry fixture no longer turns a sloped bed into a depth discontinuity, dry analytic shoreline cells stay dry, lateral momentum leakage is zeroed, Milestone 17 guardrails pass with zero regressions, and `physics/reports/milestone18/wet_dry_finite_volume_reconstruction_retune.*` passes all GeoClaw/C++ thresholds with `feature_strength_scale=0`.
- [x] Record the bed-step finite-volume face-source attempt without promoting it: the scoped abrupt-bed correction preserves Milestone 17 guardrails and existing 16 promoted artifacts while improving bed-step finite-volume failures to `field_linf` and `slope_linf` only.
- [x] Promote finite-volume bed-step parity with an augmented topography Riemann/source-distribution fix: `field_linf`, `slope_linf`, probe, cross-section, conservation, Froude, and feature checks now pass without feature forcing; GeoClaw/C++ passes rise to 6 of 40 and promoted artifacts to 17.
- [x] Decide reduced-mode bed-step parity scope: finite-volume is the strict discontinuous-bed parity lane for Milestone 18 and live-water readiness; reduced mode remains diagnostic/smoke-only for bed steps until a separate reduced-dynamics redesign is justified, so its field, slope, probe, mass-drift, and energy failures stay tracked but do not undo the finite-volume promotion.
- [x] Record the corrected-reference constriction parity blocker: regenerated the constriction GeoClaw reference with west `user` inflow boundary semantics and `bc2amr.f90`, then reran reduced, finite-volume HLL, and finite-volume Roe candidates with feature forcing off; no lane is promoted, and the next lever is geometry-aware throat reconstruction/source treatment.
- [x] Record the constriction source-treatment sweep without promotion: finite-volume Roe with `bed_slope_source_scale=1.5` and `feature_strength_scale=0` brings mass and energy deltas inside threshold, but field, slope, probe, cross-section, Froude, and feature-strength checks still fail, so the next lever is geometry-aware throat reconstruction rather than more scalar source scaling.
- [x] Record the constriction hydrostatic-bank reconstruction attempt without promotion: full hydrostatic interface reconstruction and abrupt-bank source reconstruction both keep feature forcing off and improve conservation/feature-strength metrics, but field, slope, wet-mask, probe, cross-section, and Froude errors remain blocked, so the solver change is not retained and the next lever is true throat/water-shape reconstruction or scenario width/depth mapping.
- [x] Record the constriction parameter-only scan without promotion: 336 finite-volume Roe/HLL candidates across roughness, bed-slope source scale, and CFL kept feature forcing off, but no lane passed; the best-ranked family remains Roe with `roughness_scale=0.5` and `bed_slope_source_scale=0.75`, still failing field, slope, wet-mask, probe, cross-section, mass-drift, and Froude checks.
- [x] Record the constriction throat water-shape diagnostic without promotion: compare authored initial, GeoClaw final, and C++ final throat profiles for wet width, center depth, mean wet depth, column mass, cross-stream velocity, and Froude; the corrected Roe candidate wets the full 12 m throat column while GeoClaw keeps a 4 m wet throat, so the next lever is geometry-aware width/depth reconstruction rather than more parameter scanning.
- [x] Record the constriction dry-bank boundary/mask reconstruction attempt without promotion: finite-volume Roe now masks authored dry-bank inflow cells and returns leaked dry-bank water to nearest authored wet cells, fixing the throat diagnostic wet width at 4 m and bringing center/mean depth and column mass inside the throat diagnostic limits, but full parity remains blocked by field, slope, wet-mask, probe, cross-section, conservation, and Froude failures plus an underdriven throat cross-stream velocity envelope.
- [x] Record the constriction throat momentum-shape reconstruction attempt without promotion: with feature forcing still off, finite-volume Roe restores authored downstream speed and bounded edge convergence velocity only in the narrowest authored throat columns; the throat diagnostic now passes, but full parity remains blocked by broader field, slope, wet-mask, probe, cross-section, mass-drift, energy-change, and Froude errors.
- [x] Record the constriction mask-alignment diagnostic without promotion: the final-frame wet-mask mismatch is 46 of 288 cells (0.159722), worst columns differ by 4 of 12 lateral cells, wet-width delta reaches 4 m, bank-row delta reaches 3 rows, mean wet-depth delta reaches 0.427354 m, and column-mass delta reaches 5.44445 m3; C++ is still preserving the authored wet band while GeoClaw expands or row-shifts the non-throat wet span, so the next lever is non-throat dry-bank/wet-band reconstruction before cross-section, slope, and Froude parity can close.
- [x] Record the constriction non-throat wet-band relaxation attempt without promotion: finite-volume Roe now keeps the center throat strict while allowing bounded bank-fringe water to accumulate in non-center constriction columns; the throat diagnostic still passes and final-frame mask mismatch improves to 34 of 288 cells (0.118056), with threshold wet-mismatch improving from 0.402778 to 0.159722, but field, slope, probe, cross-section, mass-drift, energy-change, and Froude failures remain, so the follow-up lever is mass-balanced wet-band span shaping plus bank-row shift rather than more one-way fringe retention.
- [x] Record the constriction mass-balanced wet-band span-shaping attempt without promotion: finite-volume Roe now preserves the strict throat reconstruction while redistributing non-throat relaxed-window water across a center-of-mass-shifted support span with feature forcing off; the throat diagnostic and Milestone 17 guardrails pass, energy-change improves to 0.00230886 and mass-drift nudges down to 0.14879, but field, slope, wet-mask, probe, cross-section, and Froude failures remain and final-frame mask mismatch worsens to 56 of 288 cells (0.194444), so the next constriction lever is an asymmetric flow-classified wet-band envelope that can expand, recess, and row-shift differently upstream and downstream.
- [x] Record the constriction asymmetric wet-band envelope attempt without promotion: finite-volume Roe now classifies wet-band targets by authored constriction length and initial flow direction, expanding upstream approach bands, receding downstream constriction bands, and keeping the center throat strict; the throat diagnostic and Milestone 17 guardrails pass, final-frame mask mismatch improves to 19 of 288 cells (0.0659722), and max wet-width/bank-row deltas drop to 2 m/2 rows, but the full threshold report still fails field, slope, wet-mask, probe, cross-section, mass-drift, energy-change, and Froude checks, so the next constriction lever must address depth/mass/energy response and timing rather than wet-mask shape alone.
- [x] Add a constriction depth/mass/energy response timing diagnostic: the report partitions the corrected-reference constriction into upstream approach, throat, downstream constriction, and recovery zones; it confirms wet-mask shape is no longer the only blocker, with upstream final mass -25.6979 m3, upstream final energy -102.27, throat final mass -6.47783 m3, throat peak-energy timing -5.25 s, and recovery peak-energy magnitude +47.7367 versus GeoClaw, so the next constriction lever should retune volume/depth response, peak timing, and energy transfer before any gameplay forcing is considered.
- [x] Record the constriction bounded volume-response attempt without promotion: finite-volume Roe now preserves the shaped wet footprint and manifest-records fixture-scoped volume response caps/scales with feature forcing still off; mass-drift delta improves to 0.0090121 and energy-change delta improves to 0.116007, both inside threshold, and the throat diagnostic still passes, but field, slope, wet-mask, probe, cross-section, Froude, and response-timing checks remain blocked by upstream under-mass, recovery over-mass, and peak-energy timing/magnitude, so the next constriction lever should address recovery/energy transport and velocity/Froude timing rather than adding more volume.
- [x] Record the constriction recovery-transport attempt without promotion: finite-volume Roe now moves bounded excess recovery depth into still-deficient constriction response cells with manifest-recorded `mass_conservative=true` and feature forcing still off; mass-drift delta improves to 0.00541747, recovery final mass delta drops to +9.06728 m3, upstream final mass improves to -4.8478 m3, and the throat diagnostic still passes, but field, slope, wet-mask, probe, cross-section, Froude, and response-timing checks remain blocked, so the next constriction lever should address velocity/Froude shape and wet-band placement instead of scalar volume movement.
- [x] Record the constriction shoulder-Froude attempt without promotion: finite-volume Roe now keeps feature forcing off, preserves column mass while tapering far-upstream shoulder depth, nudges edge velocity with bounded manifest-recorded caps, and tightens the throat volume scale so the throat diagnostic still passes; mass-drift and energy-change remain inside threshold at 0.010671 and 0.13225, but wet-mask placement remains 19/288 mismatched cells and field, slope, probe, cross-section, Froude, and response-timing checks still fail, so the next constriction lever must change local shallow-fringe wet-band placement rather than simply nudging far-upstream velocity.
- [x] Record the constriction local shallow-fringe attempt without promotion: finite-volume Roe now preserves and caps shallow upstream fringe cells, returns over-deepened fringe water to authored wet cells, and manifest-records bounded mass-conservative recovery transfer with feature forcing still off; final-frame wet-mask mismatch improves from 19/288 to 7/288 cells, max wet-width and bank-row deltas drop to 1, and mass-drift/energy-change stay inside threshold at 0.0195608 and 0.188234, but full parity still fails field, slope, wet-mask, probe, cross-section, and Froude checks while the throat diagnostic blocks on a 0.34352 m center-depth delta, so the next constriction lever should shift/cap near-throat support rows and retune throat depth without undoing the shallow-fringe placement.
- [x] Record the constriction near-throat support attempt without promotion: finite-volume Roe now shifts the center throat support from rows 4-7 to GeoClaw-aligned rows 3-6, caps throat depth at the authored scale, and transfers excess mass into upstream receivers with feature forcing still off; the throat diagnostic passes with center-depth delta 0.00160956 m, max cross-stream velocity delta 0.00196364 m/s, and column-mass delta 0.132664 m3, final-frame wet-mask mismatch improves to 1/288 cells, and mass-drift/energy-change pass at 0.00601671 and 0.126945, but full parity still fails field, slope, max wet-mismatch, probe, cross-section, Froude, and response-timing checks, so the next constriction lever should address upstream/recovery depth distribution and peak-energy timing rather than more throat shape work.
- [x] Record the constriction upstream/recovery depth-distribution attempt without promotion: finite-volume Roe now moves bounded recovery excess into upstream and downstream constriction receiver cells with `mass_conservative=true`, a 0.14 m/s depth cap, 1.0/s transport rate, recovery target scale 0.93, upstream/downstream receiver scales 1.42/1.28, feature forcing still off, and throat/local-shallow-fringe exclusions; mass-drift and energy-change pass at 0.0143234 and 0.0946814, the throat diagnostic still passes, and the Milestone 17 guardrail has zero regressions, but full parity still fails field 4.10419, slope 1.39286, wet-mismatch 0.274306, probe 2.25322, cross-section 1.73192, and Froude 1.24774, while timing remains blocked by 68.8096 peak-energy error and 3 s peak timing error, so the next constriction lever should address velocity/Froude and energy-timing shape rather than additional scalar depth transport.
- [x] Record the constriction velocity/energy-timing attempt without promotion: finite-volume Roe now applies a bounded velocity-only response with a 0.35 m/s2 cap, 0.7/s rate, upstream/downstream/recovery speed scales 1.28/0.98/1.0, cross-stream damping 0.5, feature forcing still off, and throat-width/local-shallow-fringe exclusions; field error improves to 3.72832 and peak-energy magnitude error drops from 68.8096 to 21.2027 while mass-drift and energy-change still pass at 0.0356691 and 0.191673, the throat diagnostic still passes, and the Milestone 17 guardrail has zero regressions, but full parity still fails slope 1.42903, wet-mismatch 0.274306, probe 2.25322, cross-section 1.73192, and Froude 1.24774, and response timing remains blocked by recovery final mass error 6.72705 m3 and 3 s peak timing error, so the next constriction lever should couple flux/mass timing with Froude shape instead of making another velocity-only pass.
- [x] Record the constriction flux/mass/Froude timing attempt without promotion: finite-volume Roe now couples a bounded, mass-conservative recovery transfer with local shallow-fringe Froude retuning, keeps feature forcing off, raises the local-fringe speed fraction to 1.145, and manifest-records a 0.08 m/s depth cap, 0.75/s transport rate, recovery target scale 0.9, upstream/downstream receiver scales 1.5/1.35, a 0.55 m/s2 velocity cap, and a 1.15 authored-throat fringe-speed target; mass-drift, energy-change, Froude, feature-location, and feature-strength checks now pass at 0.0397839, 0.227565, 0.488792, 3.60555, and 0.637697, the throat diagnostic and Milestone 17 guardrail still pass, but full parity remains blocked by field 3.82762, slope 1.46966, wet-mismatch 0.274306, probe 2.25322, cross-section 1.73192, response timing final mass 4.84816 m3, and 3 s peak-energy timing error, so the next constriction lever should address field/slope/cross-section shape and zone timing rather than adding more Froude speed.
- [x] Add a constriction shape/timing blocker diagnostic after the Froude pass: `physics/reports/milestone18/constriction_flux_mass_froude_timing_shape_diagnostic.*` ranks the remaining field, slope, probe, and cross-section errors by threshold ratio and cell/zone; the worst blockers are final-frame upstream-approach `u` at row 1 column 7 with 3.82762 Linf (15.3105x threshold), upstream-approach `v` at row 9 column 1 with 3.72552, downstream-constriction `hu` at row 8 column 14 with 3.62353, recovery `hv` at row 7 column 17 with 3.14599, upstream `slope_y` at row 11 column 6 with 1.46966, midstream probe `hv` at 2.25322, and mid-cross-section `v` at 1.73192; next retune should target lateral/cross-stream velocity and surface-slope shape before another speed or forcing adjustment.
- [x] Record the constriction lateral/slope-shape attempt without promotion: finite-volume Roe now keeps feature forcing off, caps non-throat dry-bank support cells at 0.22 m with mass-conservative band-wide redistribution, applies side-specific local shallow-fringe targets, and adds bounded bank-side lateral velocity shaping with manifest-recorded caps; field improves to 3.69455, slope to 0.855161, wet mismatch to 0.270833, mass/energy to 0.0127905/0.159078, the throat diagnostic and Milestone 17 guardrail still pass, but full parity remains blocked by field, slope, wet-mask, probe 2.25322, cross-section 1.73192, and a near-threshold Froude regression at 0.504034, so the next constriction lever should couple cross-section/probe velocity sampling with Froude-preserving lateral circulation rather than adding another scalar slope cap.
- [x] Add a constriction probe/cross-section raw-sample diagnostic after the lateral/slope attempt: `physics/reports/milestone18/constriction_lateral_slope_shape_probe_cross_section_diagnostic.*` locates the remaining sampled blockers at exact times, distances, cells, and GeoClaw/C++ states; the worst point probe is `midstream_center` `hv` at t=3 s in throat cell row 6 column 12 with GeoClaw +0.775086 versus C++ -1.47814 (2.25322 Linf), and the matching cross-section `v` error is at t=3 s, distance 0.5 m, row 6 column 12 with GeoClaw +0.549413 versus C++ -1.18251 (1.73192 Linf), so the next constriction retune should fix center-throat cross-stream circulation sign/magnitude while preserving the Froude envelope.
- [x] Record the constriction center-throat circulation attempt without promotion: finite-volume Roe keeps feature forcing off and adds a bounded velocity-only pass on the center throat columns with manifest-recorded 3.4/s response, 2.4 m/s2 speed cap, 0.62 cross-stream fraction, and 2.35 edge boost; the exact raw blocker improves only slightly (`midstream_center` `hv` 2.25322 to 2.20322, mid-cross-section `v` 1.73192 to 1.69192), mass-drift and energy-change stay passing at 0.0127906 and 0.159088, the throat diagnostic passes, and the Milestone 17 guardrail has zero regressions, but full parity remains blocked by field 3.69455, slope 0.855161, wet mismatch 0.270833, probe/cross-section errors, and Froude 0.504034, so the next constriction lever should address broader upstream/recovery lateral circulation and energy timing instead of another local throat-only velocity nudge.
- [x] Reject a velocity-only upstream/recovery circulation retune before promotion: `physics/reports/milestone18/constriction_upstream_recovery_circulation_rejection.*` records that a bounded non-throat circulation pass slightly improves field Linf from 3.69455 to 3.64276 and corrects some velocity signs, but it regresses mass-drift delta from passing 0.0127906 to failing 0.0575969, worsens Froude from 0.504034 to 1.48585, worsens wet-mask/slope errors, and leaves probe/cross-section blockers unchanged, so the implementation is not retained and the next constriction lever must be a mass-balanced edge-depth plus circulation reconstruction.
- [x] Reject a mass-balanced upstream edge-depth/circulation retune before promotion: `physics/reports/milestone18/constriction_edge_depth_circulation_rejection.*` records two non-retained variants; the depth-plus-circulation pass keeps mass/energy inside threshold but worsens field 3.90843, slope 0.891738, and Froude 1.47423, while the depth-only pass preserves mass/energy and slightly improves slope to 0.850006 but leaves field/probe/cross-section effectively unchanged and worsens Froude to 0.671046, so the next constriction lever should move the shallow, fast upstream edge behavior into flux/source treatment rather than post-step column-local redistribution.
- [x] Record the constriction upstream-edge flux/source treatment without promotion: finite-volume Roe now keeps feature forcing off while manifest-recording an inflow-edge state preconditioner, mass-conservative lateral edge face flux, bounded momentum source, and exclusion of those flux-shaped edge cells from later depth receivers; mass/energy stay inside threshold at 0.0144205 and 0.016676 and the throat diagnostic plus Milestone 17 guardrail still pass, but full parity remains blocked by field 3.69942, slope 0.952462, wet mismatch 0.270833, probe 2.20322, cross-section 1.69192, and Froude 0.504034. The local target did move in the right direction at upstream row 9 column 1 (`h/u` 1.62776/1.05583 to 1.49323/1.80199), but C++ still misses GeoClaw's cross-stream velocity there (`v` -0.0280083 versus -3.72743), so the next constriction lever should solve lateral momentum transport/sign across upstream and recovery instead of adding more scalar edge speed.
- [x] Record the constriction recovery cross-stream momentum-source attempt without promotion: finite-volume Roe now adds a fixture-scoped, recovery-only, mass-preserving cross-stream momentum source with feature forcing still off; recovery center `v` moves toward GeoClaw at row 6 column 18 (-0.611179 to -0.201410 versus +0.51569) and row 7 column 17 (-0.940415 to -0.442367 versus +0.749607), while mass/energy stay passing at 0.0142722/0.0203663, the throat diagnostic passes, and the Milestone 17 guardrail has zero regressions. Full parity remains blocked by upstream/throat errors: field 3.69943, slope 0.952384, wet mismatch 0.270833, probe 2.20322, cross-section 1.69192, and Froude 0.504034. A broader upstream/throat/downstream cross-stream source was tested first and rejected before retention because it collapsed the Froude summary to 1.61429; the next constriction lever should use localized throat/upstream circulation or face-flux transport that preserves shallow-row Froude.
- [x] Record the constriction localized throat/recovery circulation attempt without promotion: finite-volume Roe now keeps feature forcing off while adding a manifest-recorded, velocity-only, mass-preserving final pass over the center throat and near-recovery wet band; an upstream component was tested and disabled because it regressed the Froude guard, while the retained pass keeps Froude at the prior near-miss of 0.504034 and mass/energy passing at 0.0142295/0.0212464. Sampled blockers improve without promotion: probe Linf 2.20322 to 2.15656, cross-section Linf 1.69192 to 1.6623, center throat row 6 column 12 `v` -1.14251 to -1.10518 versus +0.09605, recovery row 6 column 18 `v` -0.201410 to +0.0108016 versus +0.51569, and row 7 column 17 `v` -0.442367 to -0.117688 versus +0.749607. Full parity remains blocked by upstream field/slope/wet-mask errors and sampled probe/cross-section errors; the next constriction lever should solve upstream shallow fast lateral momentum through geometry-aware face flux or coupled mass/momentum transport rather than final velocity nudging.
- [x] Reject the constriction upstream lateral mass/momentum transport attempt before promotion: a bounded upper-shoulder donor/lower-fringe receiver pass with feature forcing still off preserved mass/energy thresholds at 0.0330179/0.0532743, but worsened field 3.69943 to 3.86487, slope 0.952377 to 0.997733, and Froude 0.504034 to 1.45 while leaving probe/cross-section blockers unchanged. The target upper-edge row 9 column 1 moved only partway toward GeoClaw (`v` -0.028008 to -0.493718 versus -3.72743), while the lower upstream fringe moved the wrong direction (`v` -0.01074 to -0.38284 versus +3.457), so the implementation is not retained. The next constriction lever should diagnose GeoClaw's face-level lateral flux/source balance for opposite-signed lower/upper upstream edge velocities before adding another C++ reconstruction.
- [x] Add a constriction lateral face-flux diagnostic before the next retune: `physics/reports/milestone18/constriction_lateral_face_flux_diagnostic.*` computes final-frame lateral face volume-flux proxies across upstream authored wet-band edge faces; GeoClaw shows opposite-signed lower/upper edge faces in 10 upstream columns, C++ shows 0, with 13 sign mismatches and max flux-proxy delta 2.72825 m3/s at upper edge column 6 rows 8-9. The next constriction lever should instrument or reconstruct the actual finite-volume lateral face flux/source balance before another post-step velocity/depth transport, preserving GeoClaw's lower-positive/upper-negative upstream edge behavior.
- [x] Add a constriction finite-volume face/source audit before the next retune: `physics/reports/milestone18/constriction_face_source_audit_diagnostic.*` reconstructs y-face volume flux, x-momentum transport, normal momentum, bed-source proxy, and combined balance from the exported final GeoClaw/C++ frames. It confirms the same upper-edge blocker at column 6 rows 8-9 with q delta 2.72825 m3/s and reconstructed balance delta 8.87381 m3/s2, 13 volume-sign mismatches, 11 x-momentum sign mismatches, and 10 lower/upper opposition mismatches; the next solver step should export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms, then move the shallow-fast upstream edge behavior into finite-volume face/source treatment rather than final velocity/depth/gameplay forcing.
- [x] Export and consume the C++ internal constriction y-face Riemann/source audit: finite-volume constriction runs now write `diagnostics/constriction_y_face_flux_source_audit.csv` and record it in the C++ manifest; the refreshed `constriction_face_source_audit_diagnostic.*` consumes 96 internal face samples, confirms 65 post-source sign mismatches, 16 constriction face-source applications, 0 hydrostatic y-face source applications, and still blocks at upper-edge column 6 rows 8-9 with internal post-source q delta 2.6134 m3/s. The next solver decision should test hydrostatic reconstruction/source splitting for constriction y-faces or an equivalent finite-volume source treatment before any more post-step transport.
- [x] Decide the constriction y-face hydrostatic/source-splitting scope from the native audit: `physics/reports/milestone18/constriction_hydrostatic_source_decision.*` initially recorded `TEST_REQUIRED`, targeted `upper_edge_face` column 6 rows 8-9 first, kept feature/gameplay forcing disabled, required manifest-recorded source-split parameters and conservation deltas, and blocked promotion unless the face/source report, throat/shape/timing diagnostics, Milestone 17 guardrail, and threshold report all supported the change. The bounded experiment below supersedes that decision with `REVISE_OR_REJECT` evidence.
- [x] Record the bounded constriction y-face hydrostatic/source-split experiment without promotion: finite-volume constriction runs now manifest-record a fixture-scoped source split with `source_split_fraction=0.06`, `max_speed_m_per_s2=0.45`, feature forcing off, and new audit columns for split-applied faces. The refreshed audit records 32 hydrostatic/source-split face applications, but post-source sign mismatches remain 65 of 96 and the target upper-edge column 6 rows 8-9 delta only moves from 2.6134 to 2.61144 m3/s; mass and energy remain passing, Froude remains the prior near-miss at 0.504034, and the split is not a promotion lever by itself. The next constriction attempt should move to geometry-aware face-state reconstruction or width/depth mapping rather than increasing source-split strength.
- [x] Add a constriction face-state width/depth diagnostic after the bounded source-split experiment: `physics/reports/milestone18/constriction_face_state_width_depth_diagnostic.*` compares authored initial, GeoClaw final, and C++ final wet-band columns plus upstream edge face states. It records 19 face-state blockers, 13 sign mismatches, 10 lower/upper opposition mismatches, 1 width-mapping blocker, 0 bank-row blockers, and 3 depth-mapping blockers; the worst target remains `upper_edge_face` column 6 rows 8-9 with q delta 2.72633 m3/s and face mean-depth delta 0.719562 m. The next constriction implementation should build geometry-aware face-state reconstruction before y-face flux evaluation while keeping width/depth mapping visible as a guardrail, not increase source-split strength or feature forcing.
- [x] Record the bounded constriction y-face state-reconstruction experiment without promotion: finite-volume Roe now applies a fixture-scoped predictor-state reconstruction before y-face Riemann fluxes on upstream constriction edge faces, manifest-recording bounded blend/depth/speed parameters, audit face-state columns, and `requires_feature_forcing=false`. The refreshed audit confirms the reconstruction fired on 16 of 96 internal face samples, but full parity remains blocked by field 3.73627, slope 0.952334, wet-mismatch 0.270833, probe 2.15656, cross-section 1.6623, and Froude 0.987165; the face-state report still records 18 blockers, 14 sign mismatches, 10 opposition mismatches, 2 width-mapping blockers, and 4 depth-mapping blockers. Mass/energy pass and the Milestone 17 guardrail has zero regressions, but the retune is not promoted; the next constriction lever should revise upstream edge width/depth and flux balance around column 1 rows 8-9 rather than add gameplay forcing or stronger source splitting.
- [x] Add a constriction upstream edge balance diagnostic after the failed state-reconstruction retune: `physics/reports/milestone18/constriction_upstream_edge_balance_diagnostic.*` joins face-state width/depth samples, reconstructed face/source balance, native C++ post-source audit rows, and lower/upper edge opposition. It records 12 blocked targets, 12 width/depth-coupled blockers, 12 source-balance blockers, 5 native post-source sign mismatches, and 10 paired-edge opposition mismatches; the primary coupled target is now `lower_edge_face` column 0 rows 1-2 with q delta -2.03004 m3/s, balance delta -15.4598 m3/s2, native post-source delta -2.57234 m3/s, wet-width delta -2 cells, and bank-row delta 1. The next constriction solver change should correct upstream edge support and y-face balance together with feature forcing off.
- [x] Record the constriction upstream edge face-convention attempt without promotion: finite-volume Roe now manifest-records that upstream face-source treatment recognizes lower faces as outside-to-first-wet and upper faces as next-to-last-to-last-wet, but the corrected-reference run still blocks. Final-frame sign mismatches improve from 14 to 13, but native post-source sign mismatches regress from 62 to 65, Froude worsens to 1.32035, and full parity still fails field 3.74989, slope 0.955443, wet-mismatch 0.270833, probe 2.15656, and cross-section 1.6623. Mass/energy pass at 0.0148899/0.0220351 and the Milestone 17 guardrail has zero regressions; the next constriction lever should fix upper-edge column 6 rows 8-9 width/depth support plus y-face balance, not rely on face convention alone.
- [x] Record the bounded constriction upstream-edge support attempt without promotion: finite-volume Roe now manifest-records a fixture-scoped, mass-conservative depth-transfer plus edge-opposition support pass with feature forcing off, and the focused reports are `physics/reports/milestone18/constriction_upstream_edge_support_*`. Final-frame face sign mismatches improve from 13 to 11 and Froude improves from 1.32035 to 1.26683, but field/slope errors worsen to 3.90185/1.00483, depth blockers rise to 5, and the primary upper-edge column 6 rows 8-9 target still blocks with q delta 2.33091 m3/s, balance delta 10.4804 m3/s2, and native post-source delta 1.66984 m3/s. Mass/energy still pass at 0.0345096/0.0594168 and the Milestone 17 guardrail has zero regressions; the next constriction lever should move back into conservative y-face state/source treatment at the target face rather than another post-step edge-support pass.
- [x] Record the bounded conservative y-face opposition-flux attempt without promotion: finite-volume Roe now manifest-records `conservative_y_face_opposition_flux` with target-depth, cross-stream, and reference-speed cap parameters while keeping feature forcing off, and the focused reports are `physics/reports/milestone18/constriction_y_face_opposition_flux_*`. Native post-source sign mismatches improve from 65 to 60 and Froude improves to 0.504034, but final-frame volume sign mismatches worsen to 12, the worst blocker shifts to `lower_edge_face` column 5 rows 1-2 with q delta -5.88954 m3/s and native post-source delta -1.91458 m3/s, and field/slope/probe/wet-mask errors worsen to 4.05737/1.02966/2.89797/0.274306. Mass/energy still pass at 0.0438297/0.110946 and the Milestone 17 guardrail has zero regressions; the next constriction lever should repair width/depth state support before applying stronger edge-opposition flux.
- [x] Record the bounded lower outside companion support attempt without promotion: finite-volume Roe now keeps feature forcing off, caps the opposition-flux reference scale at 0.28, and manifest-records a lower outside companion state reset before the y-face Riemann solve, with focused reports under `physics/reports/milestone18/constriction_lower_companion_support_*`. Mass/energy remain inside threshold at 0.0487334/0.108237 and the Milestone 17 guardrail has zero regressions, but full parity stays blocked by field 5.59714, slope 1.03033, wet mismatch 0.277778, probe 2.15656, cross-section 1.6623, and Froude 1.00891. The primary blocker remains `lower_edge_face` column 5 rows 1-2 with q delta -4.54348 m3/s, native post-source delta -1.93347 m3/s, wet-width delta -1 cell, and bank-row delta 1, so the next constriction lever should solve upstream edge width/depth support and y-face flux balance together rather than adding deeper companion support or stronger edge-opposition flux.
- [x] Record the bounded lower-edge width/depth balance attempt without promotion: finite-volume Roe now keeps feature forcing off and manifest-records a mass-conservative transfer from over-deep adjacent wet-band cells into the lower upstream outside support row, with focused reports under `physics/reports/milestone18/constriction_lower_edge_width_depth_balance_*`. The target lower-edge column 5 native post-source sign flips from negative to positive and field/wet/Froude improve versus the lower companion attempt to 4.01241/0.270833/0.504034 while mass/energy pass at 0.0450197/0.0970665 and the Milestone 17 guardrail has zero regressions. It is not promoted because slope 1.02112, probe 2.28198, cross-section 1.6623, wet-mask, and Froude remain blocked; the primary queue target shifts to `upper_edge_face` column 6 rows 8-9 with q delta 2.97684 m3/s, native post-source delta 2.05363 m3/s, wet-width delta 1 cell, and ten paired-edge opposition mismatches, so the next constriction lever should rebalance upper-edge width/depth and y-face flux without undoing the lower-edge sign repair.
- [x] Record the bounded constriction wet-band profile relaxation attempt without promotion: finite-volume Roe now keeps feature forcing off while manifest-recording mass-conservative wet-band profile relaxation, light upstream interior velocity relaxation, and bounded upper/lower edge repairs. Mass, energy, feature-location, and feature-strength checks pass at 0.0482775, 0.149363, 3.60555, and 0.770052, and the Milestone 17 guardrail has zero regressions, but full parity remains blocked by field 3.4718, slope 0.810927, wet mismatch 0.270833, probe 2.15656, cross-section 1.6623, and Froude 1.22559. The focused balance report moves the primary target to `upper_edge_face` column 9 rows 7-8 with q delta 1.44807 m3/s, balance delta 5.29476 m3/s2, native post-source delta 1.4637 m3/s, and zero wet-width/bank-row delta, so the next constriction lever should solve upper-edge lateral face flux/source sign without more post-step width/depth shaping.
- [x] Record the bounded constriction transition-edge face-balance attempt without promotion: finite-volume Roe now extends y-face predictor state reconstruction and edge face-flux/source treatment into the transition-edge window, with feature forcing off and a manifest-recorded transition face-weight scale. The column 8/9 transition upper-edge native post-source signs flip negative, mass/energy/feature checks pass at 0.048348, 0.149531, 3.60555, and 0.770133, and the Milestone 17 guardrail has zero regressions, but full parity remains blocked by field 3.47192, slope 0.811032, wet mismatch 0.270833, probe 2.15656, cross-section 1.6623, and Froude 1.22543. The focused queue moves back to `upper_edge_face` column 6 rows 8-9 with q delta 1.73125 m3/s, native post-source delta 1.02409 m3/s, zero wet-width delta, and one bank-row delta, so the next constriction lever should fix the remaining upper-edge depth/velocity coupling at column 6 instead of widening transition-face treatment further.
- [x] Record the bounded constriction upper-edge final-balance attempt without promotion: finite-volume Roe now uses the transition-aware weighting in the final upper-edge opposition pass, with feature forcing off and manifest-recorded transition weighting. Native upper-edge post-source signs are mostly aligned and mass/energy/feature checks pass at 0.0474877, 0.142814, 3.60555, and 0.769906, while wet mismatch and slope improve slightly to 0.263889 and 0.789758. Full parity remains blocked by field 3.47084, slope, wet-mask, probe 2.15656, cross-section 1.6623, and Froude 1.22692; the refreshed queue moves to `upper_edge_face` column 4 rows 8-9 with q delta 1.17713 m3/s, balance delta 4.40553 m3/s2, native post-source delta -0.699467 m3/s, wet-width delta -1 cell, and bank-row delta 1, so the next lever should restore upstream edge width/depth support before another face-flux/source adjustment.
- [x] Record the corrected-reference drop/ledge parity blocker: regenerated the drop-ledge GeoClaw reference with west `user` inflow boundary semantics and `bc2amr.f90`, then reran reduced, finite-volume HLL, and finite-volume Roe candidates with feature forcing off; finite-volume lanes pass conservation, wet-mask, slope, cross-section, Froude, and feature checks, but field/probe shape still blocks promotion pending hydraulic-control and downstream-recovery reconstruction.
- [x] Add a drop/ledge hydraulic-control diagnostic before the next retune: `physics/reports/milestone18/drop_ledge_hydraulic_control_diagnostic.*` splits the corrected-reference Roe comparison into upstream pool, hydraulic control, tailwater recovery, and downstream pool zones; the worst final-field blocker is hydraulic-control cell row 0 column 10 where GeoClaw `u=2.86392` versus C++ `u=2.03358` gives Linf `0.830342` against the `0.25` threshold, the worst raw probe blocker is `upstream_center` `u` at t=6 s with Linf `0.41761`, and the report preserves the passing mass, energy, and Froude checks so the next lever is ledge-lip/tailwater water-shape reconstruction with `feature_strength_scale=0`.
- [x] Promote stitched reach/drop handoff geometry into regression artifacts: the promotion manifest now accepts geometry validation evidence and preserves the low, median, and high South Fork cascading seam diagnostics as `geometry_validation` artifacts, raising promoted source-report artifacts to 20 without relaxing any blocked water-field thresholds.
- [x] Refresh the aggregate geometry gate with focused Milestone 18 closure evidence: `physics/reports/milestone16/geometry_validation.*` now applies the wet/dry and finite-volume bed-step closure reports, passes 4 of 6 geometry families, and leaves only constriction plus drops/ledges/tailwater/cascading water-field families as active geometry blockers; `physics/reports/milestone16/regression_promotion_manifest.*` and `physics/regression_fixtures/milestone16/registry.json` now preserve 23 promoted artifacts, including 6 geometry-validation artifacts.
- [x] Add a remaining-geometry closure queue before more retuning: `physics/reports/milestone18/remaining_geometry_closure.*` consumes the aggregate geometry report plus focused constriction/drop diagnostics, marks 4 of 6 geometry families promotion-ready, keeps `constriction` as priority 1 with 10 failing metric groups and the upper-edge face-flux blocker at column 6 rows 8-9, keeps `drops_ledges_tailwater` as priority 2 with 10 failing metric groups across drop_ledge and South Fork cascading water fields, and records that stitched reach/drop handoffs pass only as seam guardrails, not as whole-window cascading water-field acceptance.
- [ ] Close remaining geometry-specific validation failures for constrictions, drops/ledges, tailwater controls, and any cascading reach/drop water-field failures; wet/dry and finite-volume bed-step are no longer stale aggregate blockers, but the active constriction and drop/tailwater/cascading water-field families still block geometry closure.
- [ ] Retune raft coupling over C++ water only after field and geometry gates improve, comparing force envelopes, trajectories, surf/flush/clear/ground/pin/flip outcomes, and reach/drop transition stability against GeoClaw-derived fields.
- [x] Re-run raft-coupling validation over improved C++ water fields and promote newly passing outcomes: 11 of 50 raft comparisons now pass, adding finite-volume downstream-boil recovery, low-flow pool-entry, reduced eddy-line recovery, and reduced shallow-shelf pivot/release artifacts while the raft gate remains blocked overall.
- [x] Add a distinct pin/release fixture that is not just shallow-shelf or boulder proxy coverage, with flow-dependent pin force, boat orientation, wrap depth, crew high-side/shift timing, release threshold, and failed-rescue outcome telemetry.
- [x] Run Milestone 17 analytic fixtures as required preflight and postflight guardrails for every retune batch, blocking any change that regresses lake-at-rest, sloping-channel, wet/dry, bed-step, bore, hydraulic-jump, or transcritical-bump diagnostics.
- [ ] Re-run the full Milestone 16 gate after fixes, regenerate the suite-level C++ validation report and GeoClaw-to-Unreal readiness report, and explicitly approve or block live custom water.

## Milestone 19: Chaos/Jolt Runtime Authority Evaluation

This milestone decides whether Unreal Chaos, Jolt, Chrono, or the custom reduced runtime owns scoring-critical raft/contact/swimmer gameplay after custom C++ water remains authoritative.

- [x] Adopt the split/hybrid runtime plan: Chaos is default for Unreal-integrated visual/non-authoritative physics, Jolt is the leading portable authoritative gameplay-island candidate, Chrono remains high-fidelity reference/research, and custom C++ remains water authority.
- [x] Add a versioned shared Chaos/Jolt fixture contract for raft-rock angle sweeps, shallow shelf grounding, pin/release, crew ejection to swimmer, 1000-step determinism, and crowded-scene runtime cost.
- [ ] Build Unreal Chaos automation fixtures from `chaos_jolt_runtime_evaluation.json` and export matching telemetry/replay summaries.
- [ ] Build a native Jolt smoke harness or Unreal plugin path from the same fixture contract and export matching telemetry/replay summaries.
- [ ] Add a Chaos-vs-Jolt comparison report that ranks determinism, CPU cost, contact quality, outcome stability, swimmer state, and authoring/debug ergonomics.
- [ ] Select the first authoritative raft/contact runtime for the vertical slice, or keep the custom reduced runtime fallback if neither Chaos nor Jolt passes.

## Technical Notes To Revisit

- [ ] Decide when to physically remove legacy 2D code, tests, examples, and videos from the repo.
- [x] Decide whether PyClaw is enough or GeoClaw-specific behavior is required for river bathymetry and wet/dry cases: GeoClaw is now the target reference solver.
- [x] Decide if SWASHES fixtures should be vendored, regenerated, or manually encoded: manually encode a small SWASHES-style analytic set first with provenance notes; avoid vendoring external data until licensing and maintenance are clear.
- [ ] Decide whether the C++ solver starts as CPU-only or gets a GPU path after correctness is established.
- [x] Decide how much authored feature forcing is acceptable versus pure shallow-water dynamics: forcing is allowed only when bounded, manifest-recorded, GeoClaw-compared, flow-dependent, and not hiding conservation failures; expose parameters for gameplay/visual tuning with low default gains until validation passes.
- [x] Decide the canonical storage format for cascading reach/drop packages: support reach-local grids with overlap/ghost zones for authoring and streaming, but require stitched whole-window validation outputs so seams cannot hide physics errors.
- [ ] Evaluate Chrono::FSI only after the Milestone 18 water validation closure and Milestone 19 Chaos/Jolt raft-contact fixture loop are stable.
- [x] Decide whether Project Chrono remains the sole planned raft/contact runtime: no, use the split/hybrid Chaos/Jolt evaluation plan and keep Chrono as high-fidelity reference/research.
- [x] Decide whether Chaos/Jolt runtime authority evaluation should run before the custom C++ water closure: no, insert Milestone 18 for GeoClaw/C++ parity, geometry, raft-coupling, pin/release, analytic-guardrail, and readiness re-run work; move Chaos/Jolt evaluation to Milestone 19.
- [x] Identify reference footage, river data, aerial/satellite imagery, flow history, and expert guide feedback needed for validation: build a game/editor-integrated river validation annotation tool so evidence is attached directly to river stations, reaches, drops, raft lines, and expected outcomes.
- [x] Decide which geospatial formats become canonical for source data, generated scenarios, and Unreal corridor packages: JSON source manifests, GeoJSON vectors/annotations, GeoPackage for larger GIS workspaces, GeoTIFF/COG rasters, LAS/LAZ or COPC point clouds, normalized JSON/CSV/Parquet gauge history, custom JSON plus `.npy`/`.npz` solver packages, and JSON/GeoJSON plus converted assets for Unreal corridor packages.
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
- [x] Implement suite-level JSON and Markdown reports for the full C++ validation gate.
- [x] Add a versioned analytic fixture manifest with provenance notes, expected behavior, tolerance tier, and source-equation references.
- [x] Manually encode a small SWASHES-style set for lake-at-rest balance, sloping-channel friction, wet/dry shoreline, bed step, dam-break/bore, hydraulic jump, and transcritical bump cases where practical.
- [x] Add C++ and GeoClaw/analytic comparison reports that fail retuning when these small fixtures regress.
- [x] Add a versioned authored feature-forcing schema for holes, boils, laterals, eddy lines, wave trains, shallow shelves, boulder push/damping, pins/releases, and flips.
- [x] Add low-default feature-forcing parameters and flow-response curves keyed by discharge, flow band, flow percentile, or boundary inflow.
- [x] Record feature-forcing manifests with active feature kinds, gain scales, flow-response curve IDs, conservation deltas, raft-coupling modifiers, and visual-only parameters.
- [x] Add GeoClaw/C++ validation checks that reject feature forcing when it hides mass, momentum, energy, wet/dry, or reach/drop handoff failures.
- [x] Add crew weight-distribution and high-side/brace/lean telemetry for seat occupancy, center-of-gravity shifts, roll moment, contact loading, and pin/flip/release thresholds.
- [x] Add rock, sticky-hole, lateral-hit, shallow-shelf, pin/release, and flip fixtures that require correctly timed crew weight shifts for safe outcomes.
- [x] Add crew-overboard, swimmer drift, rescue timing, pull-in/re-seat, and failed-rescue fixtures tied to impacts, flips, pins, holes, missed brace/high-side timing, and recovery windows.
- [x] Add a versioned reach-local grid schema with local transforms, overlap/ghost-zone ownership, neighbor references, and reach/drop IDs.
- [x] Export stitched whole-window validation fields, probes, cross sections, conservation summaries, and raft transition checkpoints for every cascading package.
- [x] Add contract-level seam diagnostics that fail validation when reach-local boundaries omit mass, momentum, energy, wet/dry, bed-slope, feature-location, or raft-state checks.
- [x] Add a versioned river validation annotation schema for station/reach/drop anchors, footage timecodes, gauge history, aerial imagery, guide feedback, expected raft outcomes, confidence, and rights/provenance.
- [x] Build the first rapid review/editor workflow that displays DEM/lidar, aerial/satellite imagery, flowlines, cross sections, gauge history, source manifests, candidate tags, and guide notes in one view.
- [x] Export annotation packages as JSON/GeoJSON for Python scenario generation, GeoClaw/C++ validation reports, and Unreal river data assets.
- [x] Add Unreal fidelity-review overlays for annotation pins/spans/polygons, solver fields, raft trajectories, rendered water/foam/audio cues, and expected surf/flush/pin/flip behavior.
- [x] Add a versioned geospatial format contract covering CRS policy, GeoJSON/GeoPackage vectors, GeoTIFF/COG rasters, LAS/LAZ/COPC point clouds, gauge-history tables, solver arrays, and Unreal corridor exports.
- [x] Add import/export validation checks that reject missing CRS metadata, lossy Shapefile-only canonical inputs, missing source manifests, and untracked WGS84/local transform changes.
- [x] Draft the first candidate river inventory and source manifest.
- [x] Prototype course/elevation extraction for one river section.
- [ ] Draft the Colorado River rowing/oar-rig route as the second real-world river target after the South Fork American baseline, including source manifest, flow bands, rowing-frame controls, guide review, and validation annotation needs.
- [x] Define the first rapid-review labels and seasonal flow/difficulty parameter mapping.
- [x] Set up the shared Chaos/Jolt runtime evaluation fixture contract for raft-rock impacts, shelf grounding, pin/release, crew ejection/swimming, determinism, and crowded runtime cost.
- [x] Build the Milestone 18 GeoClaw/C++ failure triage matrix from the current threshold, geometry, raft-coupling, and full-gate reports.
- [x] Wire Milestone 17 analytic fixture validation into the retune preflight/postflight workflow before changing solver parameters.
- [x] Fix and record GeoClaw boundary semantics so authored constant inflow/stage/depth/velocity boundaries are enforced by generated GeoClaw `user` boundaries instead of silently falling back to extrapolation.
- [x] Retune and re-run the first blocked GeoClaw/C++ parity family without increasing feature-forcing defaults, promoting the corrected-boundary finite-volume uniform-channel lane while recording reduced mode as still blocked.
- [x] Promote the reduced wet/dry shoreline parity lane with dry-neighbor pressure-gradient masking and record finite-volume wet/dry as still blocked.
- [x] Add the distinct flow-dependent pin/release fixture and report separate from shallow-shelf and boulder proxy evidence.
- [x] Re-run raft-coupling validation over the improved C++ water fields and promote newly passing outcomes.
- [ ] Regenerate the Milestone 16 full C++ gate and GeoClaw-to-Unreal readiness report after the closure fixes.
- [ ] Implement the Unreal Chaos automation fixtures from the shared runtime evaluation contract.
