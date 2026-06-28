# TODO

## Rough First Draft Outline

This project is a photo-realistic, physically accurate white water rafting simulator, but the active implementation target is now a headless 2.5D dual-solver modeling system that can later ingest real river data.

The old 2D river/raft path is retired. Future physics work starts with:

- PyClaw as the Python 2.5D shallow-water reference model.
- A custom C++ reduced shallow-water / height-field solver as the runtime candidate.
- Identical procedurally generated and real-world geospatial scenarios applied to both solvers.
- A comparison and tuning harness that makes the C++ model match PyClaw before Unreal production begins.
- Real river course, elevation, imagery, gauge, season, and difficulty presets that become validated scenario packages.

See [Physics Engine Plan](docs/physics-engine-plan.md) for the overall physics architecture.
See [2.5D Dual-Solver Simulation Plan](docs/2.5d-simulation-plan.md) for the PyClaw/C++ validation workflow.
See [Real-World River Content And Seasonal Flow Plan](docs/real-world-river-content-plan.md) for geospatial extraction, rapid identification, seasonal flow research, adaptive parameters, and the future river/season/difficulty picker.
See [Audio Asset Sourcing Plan](docs/audio-asset-sourcing-plan.md) for the recorded/downloaded-vs-AI audio policy, source shortlist, 3D spatial audio plan, asset manifest, and production sound pipeline.
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
- [x] Create low, median, and high runnable flow validation matrix, including PyClaw availability/run status and C++ smoke results; full PyClaw/C++ match tuning remains the Milestone 10 readiness gate.
- [x] Export an Unreal-ready real-world corridor package for later visualization: terrain, imagery masks, centerline, banks, rapids, hazards, flow presets, and confidence metadata.

## Milestone 10: Python-To-Unreal Readiness Gate

- [x] Complete PyClaw reference scenarios.
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
- [ ] Add native fixtures for flat pool float, current drift, standing wave lift, eddy-line yaw, rock bounce, riverbed grounding, shallow shelf pivot, and pin/release.
- [ ] Keep Unreal Chaos available only for incidental non-authoritative effects.
- [ ] Enable OpenXR-based VR support.
- [ ] Implement telemetry/replay playback in Unreal before live native physics.
- [ ] Define fixed-step water/raft scheduling and Unreal render interpolation.
- [ ] Set up Enhanced Input actions for VR controllers, keyboard, mouse, and gamepad.
- [ ] Build the first-person guide camera with flat-screen and VR comfort options.
- [ ] Build river, season, flow, difficulty, and raft/crew selection UI from validated data assets.
- [ ] Add local/offline AI integration layer for speech recognition, command intent parsing, crew dialogue, and optional local speech synthesis.
- [ ] Implement guide voice commands that map spoken instructions into deterministic crew intents: forward paddle, back paddle, left/right paddle, stop, brace, hold on, high side, rescue, and recovery commands.
- [ ] Add confidence thresholds, push-to-talk/open-mic settings, noisy-river audio tests, subtitles, accessibility fallbacks, and manual input parity for all voice commands.
- [ ] Add AI-assisted crew conversation with passenger personas, trust, fear, fatigue, skill, river knowledge, and scenario state, while keeping gameplay-critical paddling under explicit command-state control.
- [ ] Add telemetry for recognized phrase, intent, confidence, command latency, crew response, conversation state, and command outcome.
- [ ] Build the first production audio source manifest and choose initial downloaded/professional library purchases for water, raft, paddle, rocks, weather, Foley, UI, and ambience.
- [ ] Prototype interactive water audio with recorded/downloaded assets first, using solver telemetry for flow speed, aeration, turbulence, raft impacts, paddle catches, rock scrapes, weather, and camera perspective.
- [ ] Add 3D spatial audio as a core roadmap feature for VR/headphones, stereo speakers, and surround: attenuation, spatialization, binaural/HRTF, ambisonic beds, reverb, occlusion, and large-water-source behavior.
- [ ] Validate 3D audio from the stern guide seat for nearby hazards, rapids, hydraulics, crew positions, voice commands, multiplayer voice, shore/canyon reflections, raft contacts, underwater/near-water states, and rescue cues.
- [ ] Build the first rapid vertical slice with training, scoring, restart, replay, and debug force visualization.

## Milestone 12: Networked Human Crew Multiplayer

- [ ] Plan network play after the single-player guide experience, physics runtime, local voice commands, and AI crew systems are stable.
- [ ] Support a full human raft crew where every boat seat can be occupied by a human player.
- [ ] Define player roles: stern guide, left/right paddlers, bow paddlers, safety/rescue responsibilities, and optional spectator/scout roles.
- [ ] Add integrated voice communication for everyone on the boat, with push-to-talk/open-mic, mute, volume, subtitles/transcription options, moderation hooks, and privacy settings.
- [ ] Decide networking architecture: listen server, dedicated server, relay/session service, LAN/offline co-op experiments, authoritative host, or hybrid rollback/prediction.
- [ ] Replicate guide commands, human paddle strokes, brace/hold-on actions, rescue actions, crew animation state, passenger/seat state, raft contacts, and outcome telemetry.
- [ ] Keep authoritative raft/water physics deterministic enough for multiplayer replay, debugging, and desync detection.
- [ ] Add latency compensation and prediction for paddle strokes, raft impacts, rescue grabs, swimmer state, and VR/controller poses.
- [ ] Add seat assignment, lobby/invite flow, ready checks, reconnect, host migration or session recovery, and AI takeover for dropped players.
- [ ] Add multiplayer-specific scoring for crew coordination, command clarity, safety, line execution, rescue timing, and communication.
- [ ] Add network voice and gameplay telemetry for debugging: packet loss, ping, jitter, command latency, voice activity, paddle timing, and raft-state divergence.
- [ ] Validate desktop/VR mixed crews, accessibility fallbacks, and comfort settings for each connected player.

## Milestone 13: Production Audio Asset Sourcing And Sound Design

- [ ] Treat professionally recorded/downloaded libraries and custom field recordings as the production backbone for shipping audio.
- [ ] Use AI-generated audio only for prototypes, ideation, non-critical variations, abstract UI/debug sounds, or temp dialogue unless legal/audio review explicitly approves shipping use.
- [ ] Research and compare BOOM Library, Pro Sound Effects, A Sound Effect, Soundly, Fab audio packs, Sound Ideas/Sounddogs-style catalogs, Freesound CC0/CC-BY assets, and BBC Sound Effects licensing.
- [ ] Purchase or trial the first high-value water, weather, impact, Foley, ambience, UI, and gear libraries.
- [ ] Build a custom field-recording plan for real rivers, rapids, flow levels, guide-seat perspective, shore perspective, eddies, raft contacts, paddle strokes, hydrophone captures, ambisonic/spatial beds, surround ambience, and crew reactions.
- [ ] Define audio asset manifest schema: source, license, attribution, platform rights, sample rate, bit depth, channels, mic setup, location/date, processing chain, loop points, UCS metadata, attenuation preset, spatialization mode, ambisonic format/order, reverb/occlusion behavior, intended playback context, and approval status.
- [ ] Define AI audio manifest fields: tool, model, version, prompt, seed, date, account/license tier, output terms, review status, similarity check, and prototype/shipping flag.
- [ ] Add LFS/storage rules for raw recordings, purchased libraries, edited masters, generated prototypes, and Unreal-ready compressed exports.
- [ ] Build an interactive MetaSounds or middleware prototype for river roar, nearby rapids, spray, foam, paddle catch, raft scrape, rock impact, weather, canyon reflections, and crew voice layering.
- [ ] Build 3D audio presets for point sources, line/area water sources, large rapids, ambisonic ambience, occluded rock/bank sounds, raft contact, underwater/near-water perspective, crew voice, guide commands, and multiplayer voice chat.
- [ ] Validate spatial audio on stereo speakers, headphones, VR binaural/HRTF, and 5.1/7.1 surround where supported.
- [ ] Add spatial-audio debug tools for emitter position, attenuation radius, spread, occlusion traces, reverb sends, ambisonic rotation, voice count, mix priority, and runtime cost.
- [ ] Evaluate Wwise and FMOD only if Unreal-native audio/MetaSounds are insufficient for authoring, mixing, localization, memory, or platform workflow.
- [ ] Define AI audio prohibited use cases: unclear commercial rights, unlicensed voice cloning, recognizably similar music, celebrity/style imitation, and any core gameplay cue that cannot be reviewed/reproduced.
- [ ] Validate audio in stereo, headphones, VR spatial audio, noisy voice-command conditions, and multiplayer voice-chat scenarios.

## Technical Notes To Revisit

- [ ] Decide when to physically remove legacy 2D code, tests, examples, and videos from the repo.
- [ ] Decide whether PyClaw is enough or GeoClaw-specific behavior is required for river bathymetry and wet/dry cases.
- [ ] Decide if SWASHES fixtures should be vendored, regenerated, or manually encoded.
- [ ] Decide whether the C++ solver starts as CPU-only or gets a GPU path after correctness is established.
- [ ] Decide how much authored feature forcing is acceptable versus pure shallow-water dynamics.
- [ ] Evaluate Chrono::FSI only after the PyClaw/custom-C++ solver comparison path is stable.
- [ ] Identify reference footage, river data, aerial/satellite imagery, flow history, and expert guide feedback needed for validation.
- [ ] Decide which geospatial formats become canonical for source data, generated scenarios, and Unreal corridor packages.
- [ ] Re-check latest UE5 rendering/geospatial plugin capabilities at the Python-to-Unreal readiness gate.
- [ ] Decide local AI model/runtime strategy for desktop, VR, handheld, and future console targets.
- [ ] Decide how much crew dialogue is generated locally versus authored as recorded barks, constrained templates, or designer-approved lines.
- [ ] Decide latency, privacy, profanity/safety, save-data, and deterministic replay requirements for voice and conversation systems.
- [ ] Decide final audio source policy, approved vendors, AI audio policy, attribution requirements, and asset-manifest format before buying libraries at scale.
- [ ] Decide whether Unreal-native audio/MetaSounds is enough or whether Wwise/FMOD should be adopted for the full UE5 version.
- [ ] Decide the binaural/HRTF plugin/runtime path, ambisonic capture/playback format, surround targets, reverb/occlusion strategy, and spatial-audio certification requirements for the first VR build.
- [ ] Decide multiplayer network architecture, voice communication stack, session backend, crossplay scope, moderation requirements, and host/dropout recovery.
- [ ] Investigate multiplayer feasibility only after the single-player guide experience feels good enough to preserve under network latency.

## Immediate Next Steps

- [x] Remove 2D-first assumptions from active docs.
- [x] Define the shared 2.5D scenario schema.
- [x] Add fixture scenario generation for flat pool, channel flow, dam-break/bore, bed step, constriction, and wet/dry shoreline.
- [x] Add deterministic procedural 2.5D rafting scenario generation from seed.
- [x] Add a PyClaw availability check and first reference runner.
- [x] Add a C++ solver directory and build skeleton.
- [ ] Add the first PyClaw-vs-C++ comparison report format.
- [ ] Draft the first candidate river inventory and source manifest.
- [ ] Prototype course/elevation extraction for one river section.
- [ ] Define the first rapid-review labels and seasonal flow/difficulty parameter mapping.
