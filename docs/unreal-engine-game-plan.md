# Unreal Engine Full Game Plan

## Goal

Build the full SmokeEmIfYouGotEm rafting simulator as a multi-platform Unreal Engine game after the Python modeling, validation, and profiling work has proven the raft/water behavior.

The Unreal game should deliver the first-person guide fantasy: seated in the stern, reading water, calling commands, steering with physically meaningful paddle strokes, managing passenger safety, and feeling the raft move through a photo-real white water environment with fully immersive 3D audio.

See [Real-World River Content And Seasonal Flow Plan](real-world-river-content-plan.md) for the geospatial extraction, rapid identification, seasonal flow, adaptive fluid-parameter, and river-selection work that must feed Unreal content.
See [Free And AI Asset Policy](free-and-ai-asset-policy.md) for the current art and sound sourcing decision, and [Audio Asset Sourcing Plan](audio-asset-sourcing-plan.md) for audio-specific source research, library shortlist, field-recording plan, AI-audio limits, and asset manifest.
See [Python-To-Unreal Readiness Gate](python-to-unreal-readiness-gate.md) for the current readiness audit. The regenerated Milestone 16/18 gate approves live custom water, and the Milestone 20 report-set lock records the accepted source reports plus desktop, VR, and handheld target budget-profile confirmation. Production Unreal work should now move through the Milestone 20-25 full-game production sequence while physical device captures remain release/platform sign-off evidence.
See [Unreal Engine Version Lock](unreal-engine-version-lock.md) for the UE 5.8 feature review and version decision.
See [Chaos And Jolt Runtime Evaluation](chaos-jolt-runtime-evaluation.md) for the split/hybrid raft/contact runtime plan and the shared Chaos/Jolt fixture suite.

## Hard Dependency Gate

Do not treat the production Unreal Engine project as ready for live custom-water gameplay until the Python/GeoClaw/C++ physics program reaches an explicit exit gate. As of the Milestone 20 report-set lock, the custom C++ water gate passes, the accepted Milestone 16 source reports are locked by hash, and the committed runtime profile records pass desktop, VR, and handheld target budget profiles. Physical device captures still need to be appended before platform release sign-off.

Required before Unreal production begins:

- GeoClaw 2.5D reference scenarios run deterministically.
- Custom C++ reduced shallow-water / height-field scenarios run from the same solver-neutral scenario packages.
- C++ water fields, probe traces, raft force samples, and scenario outcomes match GeoClaw within accepted tolerances.
- Python profiling identifies hot loops, memory costs, timestep sensitivity, and per-scenario runtime budgets.
- Parameter files and telemetry schemas are stable enough to share with C++/Unreal tooling.
- Force model choices are documented: which effects come from GeoClaw reference, which live in the C++ water solver, which move into the selected raft/contact runtime, and which are visual-only.
- The raft/contact runtime path is validated by shared Chaos/Jolt fixtures for rock impacts, shelf grounding, pin/release, crew ejection, replay determinism, and crowded-scene runtime cost. Project Chrono remains a high-fidelity reference/research path.
- At least one real-world river section has a complete source manifest, terrain/course extraction, rapid annotations, gauge/flow research, season presets, difficulty presets, and low/median/high flow validation through GeoClaw and the custom C++ solver.
- Adaptive fluid parameters are documented for river, season, flow percentile, difficulty, channel geometry, roughness, aeration/turbulence, eddy-line shear, hole retention, wave train strength, boils, shallows, raft drag, paddle catch, and damping.
- A first real-world corridor package exists for Unreal preproduction: terrain, centerline, banks, imagery masks, rapid boundaries, hazards, flow presets, confidence metadata, and validation telemetry.
- Unreal readiness report exists with performance budgets for desktop, VR, and handheld/portable targets.
- Milestone 20 report-set lock exists at `physics/reports/milestone20/report_set_lock.json`; Unreal live-water bridge code must load or cite this manifest until a newer accepted lock supersedes it.

Unreal can still be used for throwaway visual studies, reference capture, or material tests, but the real game project should keep live-water and scoring-critical contact work gated by the accepted validation reports and runtime fixture evidence.

## Engine Scope

Use Unreal Engine as the product runtime, presentation layer, platform layer, and content authoring environment.

Unreal owns:

- First-person and VR camera
- Input, motion controllers, haptics, and accessibility settings
- Local speech recognition, command intent routing, crew conversation, passenger persona state, and optional local speech synthesis
- Visual raft, water, terrain, foliage, spray, foam, lighting, weather, and post-processing
- Audio, 3D spatial cues, ambisonic ambience, reverb/occlusion, voice lines, UI, menus, scoring, replay presentation, and save data
- Audio asset ingest, source manifests, license/attribution tracking, interactive water sound, crew barks, dialogue playback, voice-chat mix, and runtime audio budgets
- Level authoring, cooked content, build automation, and platform packaging

The selected raft/contact runtime owns:

- Authoritative raft transform and velocities
- Raft-water force integration
- Rock, bank, bed, and raft contact response
- Paddle blade force transfer
- Compliant raft experiments
- Physics telemetry, debug forces, and deterministic replay data where possible

Unreal Chaos is the default Unreal-integrated path for visual/non-authoritative physics such as loose props, splash debris, visual ropes, background objects, and visual crew ragdolls. Chaos can own scoring-critical raft/contact outcomes only if it passes the same shared fixture suite as Jolt.

Jolt is the leading specialized candidate for a portable authoritative raft/contact/swimmer gameplay island. It can own scoring-critical contacts only after a native smoke harness or plugin path runs the shared fixtures against the same water snapshots and telemetry schema.

## Target Product Shape

### Primary Experience

- First-person guide perspective from the stern.
- VR and flat-screen support from the start of Unreal production.
- Single raft, single-player guide role as the first production target.
- Scripted or AI-assisted passenger crew responding to guide commands.
- Local AI voice interaction in guided passenger paddle-raft modes so the guide can speak paddle, brace, high-side, rescue, and recovery commands; rowing/oar-rig routes use direct manual controls instead.
- Crew members can talk, acknowledge commands, react to hazards, and hold conversations shaped by passenger persona, trust, fear, fatigue, skill, weather, river history, and recent run events.
- Crew safety has explicit gameplay states: seated, at-risk, falling/ejected, swimming, rescue-targeted, rescued, re-seated/recovered, and lost/failed-rescue for scoring and training.
- Passenger swimming ability is assigned per run or roster entry, from strong swimmer through weak swimmer to completely unable to swim; this affects panic, self-rescue, drift risk, throw-line urgency, pull-in difficulty, and safety scoring after ejection.
- Fully immersive 3D audio where rapids, hydraulics, rocks, raft contacts, crew, rescue cues, voice chat, weather, and canyon reflections occupy stable world positions from the guide's stern seat.
- Realistic but teachable white water behavior.
- Data-backed river, section, season, flow level, difficulty, and raft/crew selection.
- Training-grade feedback and replay tools.

### Initial Game Modes

- Training school: calm water, strokes, ferrying, eddy turns, wave approach, rescue basics.
- Rapid challenge: one rapid, restart quickly, score safety/line/control.
- River section: linked rapids with scouting, recovery pools, and cumulative crew state.
- Real river catalog: choose river, section, season, flow level, difficulty, and raft/crew setup from validated scenario data.
- Daily/generated rapid: later, after procedural generation is stable.

### Later Modes

- Guide career.
- Custom river editor.
- Co-op crew.
- Leaderboards and challenge ghosts.
- Scenario packs based on different river types.
- Second real-world route target: rowing the Colorado River with an oar rig/rowing frame, direct manual rowing controls, and no passenger paddle voice commands after the South Fork American paddle-raft baseline is proven.
- Third runnable route target: the Pacuare River in Costa Rica, adding tropical rainforest whitewater, rain-fed flow variability, gorge pacing, and international source/provenance needs after the Colorado rowing target.

## Roadmap Milestone Mapping

The TODO roadmap now carries the full Unreal game build as explicit production milestones:

- Milestone 19: select the first raft/contact/swimmer authority path by comparing Unreal Chaos and Jolt against the same fixture contract.
- Milestone 20: create the Unreal production foundation and live custom-water bridge, including the accepted Milestone 16 report-set lock, fixed-step scheduling, report manifests, regression fixtures, in-engine debug views, and target-profile/hardware profiling evidence.
- Milestone 21: build the Unreal river editor and content pipeline for geospatial imports, reach-local authoring, stitched validation exports, flow-dependent feature tuning, guide annotations, South Fork content, and the Colorado rowing/oar-rig route.
- Milestone 22: implement authoritative raft, crew, swimmer, and rescue gameplay over the validated water and selected contact runtime.
- Milestone 23: deliver the first-person Unreal vertical slice from launch through scoring, replay, and physics/fidelity review.
- Milestone 24: expand alpha content, systems depth, South Fork coverage, Colorado rowing, Pacuare third-river planning, crew AI, generated-rapid experiments, and multiplayer feasibility only after the single-player guide loop is stable.
- Milestone 25: harden performance, platform support, QA automation, accessibility, asset/provenance workflows, release compliance, beta playtests, and patch operations.

Milestones 20-25 should not relax the water evidence rules: any new river, feature-forcing tune, raft/contact change, swimmer/rescue outcome, or content pipeline export must remain traceable to manifests, validation fixtures, telemetry, and replayable Unreal evidence.

## Production Milestones

### Phase 0: Python Exit Gate

Finish before Unreal production:

- Complete GeoClaw 2.5D reference harness.
- Complete custom C++ reduced shallow-water / height-field solver harness.
- Complete GeoClaw-vs-C++ comparison and tuning reports.
- Complete first 2.5D raft/water coupling model against both solver outputs.
- Profile Python models and decide acceleration strategy.
- Validate representative scenarios: flat pool, calm current, standing wave, hole, eddy line, lateral wave, shallow shelf, submerged rock, boil, and pinning.
- Produce shared parameter files for raft, water, paddle, rock, and scoring coefficients.
- Produce replay/telemetry examples that Unreal can visualize.
- Confirm Chrono C++ viability outside Unreal.
- Complete one real-world river scenario package with geospatial source manifest, extracted course/elevation, rapid labels, seasonal flow bands, difficulty presets, and GeoClaw/custom-C++ validation.
- Produce one Unreal-ready real-world river corridor package for preproduction review.

Deliverable:

- Python-to-Unreal readiness report, including the first real-world river content readiness appendix.

### Phase 1: Unreal Preproduction

Start only after Phase 0 is accepted.

Tasks:

- Choose the exact Unreal Engine 5.x version and lock it for the first vertical slice.
- Re-check the latest stable UE5 feature set before locking the version. The current lock is UE 5.8, with Mesh Terrain and Procedural Vegetation Editor treated as experimental evaluation features, and Nanite, Lumen/Lumen Lite, Virtual Shadow Maps, World Partition, PCG, Niagara, Substrate/material layering, and OpenXR evaluated for the first slice.
- Define target platforms for the first playable build.
- Create coding standards for C++, Blueprint exposure, data assets, and content naming.
- Define plugin/module boundaries: core game, Chrono bridge, water visualization, raft, river, input, UI, local AI/voice, crew AI, audio, and debug.
- Build a small visual prototype with placeholder physics replay data, not gameplay physics.
- Establish asset scale, coordinate conventions, units, and import/export rules.
- Define geospatial import rules: coordinate reference systems, WGS84/local transforms, JSON source manifests, GeoJSON/GeoPackage vector imports, GeoTIFF/COG terrain and mask imports, LAS/LAZ/COPC point-cloud handling where needed, terrain tile sizes, imagery masks, river corridor bounds, and confidence metadata.
- Evaluate local/offline AI runtime options for target platforms: lightweight and accurate speech-to-text, constrained command parsing, crew dialogue generation/selection, optional local speech synthesis, latency, memory, CPU/GPU cost, licensing, privacy, and console feasibility.
- Build the development asset source plan: free/open art and sound sources, AI-generation provenance, license requirements, attribution rules, AI-audio policy, asset manifest, LFS/storage policy, and Unreal import conventions; keep paid-vendor research for release-readiness only.
- Start with Unreal-native audio and MetaSounds for interactive water/raft/crew sound; evaluate Wwise/FMOD only if the native toolchain cannot meet authoring, mixing, localization, memory, or platform needs.
- Define the 3D audio stack: Sound Attenuation presets, spatialization modes, binaural/HRTF path for VR/headphones, panning/surround path for speakers, ambisonic bed format, reverb/occlusion strategy, voice-chat spatialization, and platform QA targets.
- Set up source control rules for large assets, generated files, and LFS.

Deliverable:

- Empty but buildable Unreal project with placeholder level, target platforms, and module skeleton.

### Phase 2: Runtime Physics Bridge

Tasks:

- Add Unreal plugin/module that hosts the authoritative physics runtime.
- Start with replayed Python telemetry, then move to live native Chrono/reduced runtime stepping.
- Implement fixed-step physics scheduling and render interpolation.
- Add raft actor consuming authoritative transform.
- Add debug drawing for current vectors, force vectors, contact points, paddle forces, and raft stability metrics.
- Add deterministic run capture where feasible.

Deliverable:

- Unreal level showing one raft moving from authoritative physics/replay, with debug overlays.

### Phase 3: First-Person Guide Prototype

Tasks:

- Implement stern guide camera for flat-screen and VR.
- Add comfort settings: seated recentering, motion intensity, horizon stabilization, vignette, and camera impact filtering.
- Add visible hands, paddle, guide seat position, raft bow, tubes, and passenger silhouettes.
- Implement Enhanced Input actions for keyboard/mouse, gamepad, and VR controllers.
- Add first paddle interaction model connected to physics runtime.
- Add guide voice/command inputs for passenger crew in guided paddle-raft mode using lightweight local speech recognition where available; keep rowing/oar-rig mode manual-only.
- Map recognized speech into deterministic command intents: forward paddle, back paddle, left/right paddle, stop, hold on, brace, high side, rescue, swimmer callout, and recovery commands.
- Reserve input/actions for swimmer spotting, rescue target selection, throw-line or reach/pull-in attempts, and re-seat/recovery confirmation.
- Add confidence thresholds, command repeat/confirm behavior for ambiguous recognition, subtitles, accessibility fallbacks, and manual input parity.
- Set hard budgets for command-model memory, CPU/GPU cost, latency, false positives, and noisy-river/accent accuracy before choosing the local model.
- Add noisy-water and VR microphone test scenes for false-positive and latency tuning.

Deliverable:

- Playable first-person raft control in a simple guided paddle-raft test river with manual and local voice command paths.

### Phase 4: River Visualization And Level Pipeline

Tasks:

- Import Python-authored and real-world geospatial river sections with scenario metadata, source manifests, seasonal presets, difficulty presets, and validation confidence.
- Expand the South Fork American alpha content set through `unreal/Content/RaftSim/River/south_fork_alpha_content_expansion.json`, linking reviewed rapids with scouting eddies, recovery pools, seasonal flow variants, difficulty presets, and guide-reviewed fidelity notes before new routes become authoritative.
- Build spline/volume/data-asset representation for river centerline, banks, cross sections, rapids, hazards, gauges, season/flow presets, and current fields.
- Convert GeoTIFF/COG DEMs and masks, LAS/LAZ/COPC point clouds when needed, GeoJSON/GeoPackage hydrography, and reviewed rapid annotations into Unreal terrain/corridor assets.
- Build a river validation annotation editor for viewport pins, station spans, polygons, raft lines, footage timecodes, gauge-history snippets, aerial imagery references, guide notes, confidence, and expected raft outcomes.
- Use Cesium for Unreal or equivalent geospatial tooling where it helps with real-world scale, WGS84 positioning, 3D Tiles, terrain, imagery, and georeferenced scene setup.
- Create photo-real canyon/forest/desert/mountain river environment pipeline using Nanite rocks/canyon walls/terrain details, Nanite foliage, Lumen, Virtual Shadow Maps, World Partition, PCG, Niagara, and advanced material layering where supported. Treat highly detailed, immersive landscapes and dense riverbank foliage as core content goals, pushed as close to photorealistic as target hardware, VR comfort, and gameplay readability allow.
- Add water material, foam lines, bubbles, waves, wet rocks, spray, mist, debris cues, aeration masks, turbulence masks, and seasonal water appearance.
- Build first interactive 3D water-audio prototype from free/open, first-party generated, procedural, and AI-generated development assets: river bed, nearby rapid, hydraulic hole, eddy line, spray, foam, raft scrape, paddle catch, rock impact, weather, and canyon reflections driven by solver telemetry.
- Validate large water-source behavior, ambisonic ambience rotation, binaural/HRTF localization, reverb zones, occlusion traces, and guide-seat readability for hazards and rescue cues.
- Add debug view that compares solver fields and adaptive fluid parameters with visible water cues.
- During game-engine fidelity review, overlay river annotations against GeoClaw/C++ fields, raft trajectories, rendered water features, foam/spray, audio cues, and expected surf/flush/pin/flip behavior.
- `build_unreal_cascading_corridor_metadata()` now exports a `fidelity_review_overlays` contract for annotation geometry, stitched solver fields, raft transition checkpoints/trajectories, rendered water/foam/spray, audio cues, and expected surf/flush/pin/release/flip outcomes.
- Define handoff from Python/geospatial/generated data to Unreal-authored content.

Deliverable:

- One believable real-world rapid corridor rendered with readable current, hazards, seasonal flow variation, and raft motion.

### Phase 5: Core Gameplay Vertical Slice

Tasks:

- Build one training section and one technical rapid.
- Add passenger command response: forward, back, left, right, hold on, brace.
- Add local voice-command path for the same passenger responses in guided paddle-raft mode, with deterministic command execution after intent recognition; keep rowing/oar-rig mode manual-only.
- Add crew acknowledgments, missed-command behavior, hesitation, and urgency barks based on command confidence and passenger state.
- Add safety outcomes and state transitions: fall out/ejection, swim, swimmer drift, rescue target, pull-in, re-seat/recovery, failed rescue, pin, surf, flip, flush.
- Assign passenger swimming skills at run setup, including non-swimmers who cannot self-rescue and require faster guide/crew intervention.
- Add rescue gameplay for guide and crew actions: spotting, approach line, reach/paddle grab, throw rope when available, timing window, pull-in duration, and post-rescue recovery/fatigue.
- Add scoring for safety, line, boat angle, paddle efficiency, passenger trust, and completion.
- Add restart, replay, ghost telemetry, and after-action feedback.
- Add basic menus and settings.
- Add the vertical-slice frontend shell from `unreal/Content/RaftSim/UI/vertical_slice_frontend_flow.json`: main menu, settings, save slots, scenario briefing, pause, score/after-action, replay review, and debug overlay screens.
- Add microphone, push-to-talk/open-mic, subtitles, command confirmation, voice sensitivity, privacy/offline, and fallback-control settings for guided paddle-raft voice commands.
- Add river, section, season, flow, difficulty, and raft/crew selection backed by validated data assets.
- Add manifest-approved free/open, first-party generated, procedural, and AI-generated audio for the vertical slice: water beds, rapid features, raft/paddle/rock Foley, guide commands, crew acknowledgments, UI, weather, and fail/safety states.
- Add manifest-approved 3D audio configuration for the vertical slice: attenuation/spatialization presets, ambisonic beds, reverb/occlusion zones, large rapid spread, crew/voice positions, and VR/headphone validation.
- Drive readable water visuals, foam, spray, wet rocks, raft contact cues, paddle cues, weather, 3D spatial audio, ambisonic ambience, reverb/occlusion, and rescue cues from bounded solver/runtime telemetry via `unreal/Content/RaftSim/Rendering/telemetry_presentation_cues.json` and `URaftSimTelemetryPresentationCueLibrary::BuildPresentationCues`.
- Build the vertical-slice river corridor from `unreal/Content/RaftSim/Rendering/vertical_slice_environment_corridor.json`, with photoreal landscape/bed, banks, contact rocks, dense foliage, debris/access context, lighting/weather, audio occlusion geometry, and water-readability layers tied back to source manifests and guide-seat captures.
- Gate the vertical slice with `unreal/Content/RaftSim/Automation/vertical_slice_acceptance_gate.json`, requiring build, completion, failure/rescue, restart, replay review, scoring, profiling, physics evidence, and river-fidelity review evidence.

Deliverable:

- One complete playable vertical slice from launch to scoring screen.

### Phase 6: VR Quality Pass

Tasks:

- Tune motion comfort with real headset testing.
- Add haptics for paddle catch, rock bumps, wave hits, and raft impacts.
- Validate seated play space assumptions.
- Add accessibility options for physical stroke intensity and comfort.
- Ensure UI can be used in VR and flat-screen.
- Tune binaural/HRTF localization, head-tracked ambisonic ambience, occlusion/reverb transitions, and spatial voice/crew cues for seated VR play.
- Measure VR frametime under worst-case water/physics scenes.

Deliverable:

- VR-ready vertical slice that passes comfort and performance budgets.

### Phase 7: Content Expansion

Tasks:

- Build additional river biomes.
- Build additional real-world river sections from source manifests and reviewed rapid annotations.
- Expand highly detailed, immersive landscape and foliage passes for each river biome so each corridor reads as a real place, not a thin playable channel.
- Prioritize the Colorado River rowing/oar-rig route as the second real-world river after the South Fork American baseline, with direct manual rowing-frame controls, no passenger paddle voice commands, large-volume reading, canyon pacing, and longer rescue/recovery stakes.
- Make the Pacuare River in Costa Rica the third runnable river target, with a future source manifest, flow bands, rainforest/canyon fidelity needs, rain-fed flow review, and rights-cleared guide annotations before solver or Unreal package generation.
- Add difficulty progression.
- Add more raft types and handling profiles.
- Add passenger archetypes and crew trust progression.
- Add AI-assisted crew conversations for calm water, eddies, scouting, recovery pools, run starts, run finishes, swims, rescues, and post-rapid debriefs.
- Add passenger persona data, relationship memory, river knowledge, skill/fear/fatigue state, and conversation pacing rules.
- Add conversation guardrails so active-rapid dialogue stays short, command acknowledgments take priority, and generated chatter never blocks safety-critical audio.
- Expand free/open, first-party generated, procedural, and AI-generated art/audio coverage for additional rivers, seasons, flow levels, raft types, gear, weather, and biomes.
- Revisit paid asset purchases only at the release-readiness gate if free/open and AI-generated assets are not good enough.
- Add challenge variants and generated rapid support if validated.
- Expand weather, water levels, rescue scenarios, and training lessons.

Deliverable:

- Alpha-scale game loop with multiple playable river sections.

### Phase 8: Optimization And Platform Hardening

Tasks:

- Profile CPU physics, render thread, game thread, GPU water, particles, shadows, and asset streaming.
- Profile audio voice counts, streaming, decompression, spatialization, binaural/HRTF, ambisonics, occlusion traces, convolution/reverb, MetaSounds graphs, source effects, voice chat, and memory residency.
- Profile local AI inference, speech recognition latency, audio capture cost, local speech synthesis, memory footprint, and model loading.
- Add platform-specific runtime modes for full Chrono, reduced Chrono, replay/debug, lower-cost visual water, and scalable photorealistic landscape/foliage density.
- Add platform-specific AI modes: full local conversation, command-only local voice, authored/recorded crew barks, text/manual command fallback, and disabled voice input.
- Build scalability tiers for desktop, VR, and handheld targets.
- Add automation for builds, smoke tests, content validation, and telemetry replay checks.
- Add crash reporting and performance capture tooling.

Deliverable:

- Performance-stable beta candidate.

### Phase 9: Release Readiness

Tasks:

- Polish training, onboarding, settings, accessibility, and save data.
- Add final audio mix and haptic tuning.
- Add localization-ready text and UI.
- Finalize store packaging, legal, credits, and platform compliance.
- Run QA passes on physics regressions, VR comfort, input devices, and content.
- Lock release branch and patch workflow.

Deliverable:

- Shippable multi-platform Unreal build.

## Technical Architecture

### Unreal Module Layout

Recommended modules/plugins:

- `RaftSimCore`: shared game types, units, data schemas, telemetry types.
- `RaftSimPhysics`: native raft/contact runtime bridge, replay, coupling, and selected runtime integration.
- `RaftSimWater`: authoritative custom C++ live-water bridge, accepted report manifest, fixed-step water scheduling, interpolation contracts, and solver telemetry.
- `RaftSimRiver`: river data assets, scenario loading, flow visualization, hazard volumes.
- `RaftSimGeo`: geospatial import/conversion tooling for source manifests, coordinate transforms, terrain/corridor packages, imagery masks, reach-local grids, stitched validation exports, and rapid annotations.
- `RaftSimRaft`: raft actor, passenger attachment points, animation hooks, damage/safety state.
- `RaftSimInput`: flat-screen, gamepad, VR controller, paddle, command, and accessibility mappings.
- `RaftSimAI`: guide command grammar, local AI interfaces, passenger persona/dialogue hooks, and voice-intent confidence.
- `RaftSimCrew`: passenger safety state, swimming skill assignment, ejection, swimmer drift, rescue, high-side, and weight-distribution gameplay.
- `RaftSimAudio`: asset manifest ingest, runtime audio states, 3D attenuation/spatialization presets, ambisonic beds, reverb/occlusion routing, MetaSounds/middleware events, water/raft/crew mix routing, source provenance, voice-chat spatial mix, and debug meters.
- `RaftSimUI`: menus, HUD, replay, scoring, training feedback.
- `RaftSimDebug`: force vectors, current fields, contacts, profiling views, replay inspectors.
- `RaftSimAutomation`: regression fixture import, live-water smoke suites, report-lock checks, and Unreal automation contracts.
- `RaftSimNetwork`: future multiplayer session, replication, prediction, voice, and scoring contracts.

### Data Assets

Use Unreal data assets for game-facing tuning while keeping source-of-truth exports traceable to Python:

- River section definitions
- River catalog, region, section, season, flow, difficulty, gauge, and source-manifest definitions
- Frontend flow, save-game fields, replay-review bookmarks, settings groups, and debug overlay toggles
- Vertical-slice acceptance gate manifest and report
- Water field / feature metadata
- Geospatial corridor metadata, centerlines, banks, cross sections, rapid boundaries, imagery masks, and data confidence scores
- Vertical-slice environment corridor recipe with authored landscape, bank, rock, foliage, debris, lighting/weather, audio geometry, and water-readability layers plus desktop/VR/debug quality budgets
- Raft physical parameters
- Paddle stroke parameters
- Passenger archetypes
- Voice command grammar, synonyms, confidence thresholds, locale/accent settings, and fallback command mappings
- Crew persona definitions, conversation policies, trust/fear/fatigue/skill tuning, relationship memory rules, and dialogue style profiles
- Audio source manifests, library/vendor records, license terms, attribution requirements, AI generation provenance, approval status, UCS metadata, loop points, loudness targets, and runtime mix categories
- 3D audio presets for point sources, line/area water sources, large rapids, ambisonic ambience, binaural/HRTF playback, panning/surround playback, reverb/occlusion zones, underwater/near-water states, and spatial voice chat
- Interactive audio parameter maps for flow speed, depth, turbulence, aeration, raft impact, paddle catch, rock scrape, weather, canyon geometry, camera perspective, and VR comfort mode
- Telemetry presentation cue maps for readable water visuals, foam, spray, wet rocks, raft contacts, paddle cues, weather, 3D audio, ambisonic beds, reverb/occlusion, and rescue feedback
- Scoring rules
- Camera/comfort profiles
- Platform scalability profiles

### Replay And Telemetry

Replay support is not optional. It is the main bridge between research and game feel.

Replay data should include:

- Physics timestep
- Raft pose and velocities
- Paddle inputs
- Passenger commands
- Recognized speech text or redacted transcript policy
- Voice command intent, confidence, latency, fallback path, and crew acknowledgment
- Crew conversation state, generated/selected line id, passenger speaker, and gameplay event trigger
- Crew safety state, ejection trigger, swimmer world position, rescue target, rescue method, time in water, pull-in/re-seat result, failed-rescue reason, fatigue, trust delta, and safety score impact
- Audio event id, source asset id, mix state, runtime parameters, attenuation/spatialization preset, occlusion/reverb state, ambisonic bed state, voice count, streaming/decompression/spatialization cost, and source-manifest approval state
- Presentation cue frame: water readability, foam, spray, wet rock, contact, paddle, weather, rescue, ambisonic, reverb, and occlusion outputs with any authored override manifest id
- Force contributions
- Contact points
- River sample values
- Outcome classifications

Unreal should be able to play a Python-produced run before it can run the native physics model live.

## Visual Direction

The game should be photo-real and readable:

- Water cues must reveal real gameplay information: current direction, eddy lines, holes, shallow shelves, rocks, laterals, boils, and recovery pools.
- The highest-value playable sections should be grounded in extracted real-world course/elevation data and reviewed aerial/satellite rapid annotations.
- River environments must feel highly detailed and immersive from the guide's seat: terrain, banks, rocks, shore features, canopy, understory, driftwood, camps, access points, and distant landscape should be authored toward photorealistic reference quality rather than generic backdrop dressing.
- Use the current UE5 photoreal stack where it fits the target hardware: Nanite for high-detail rocks, canyon walls, terrain details, and dense foliage; Lumen for dynamic seasonal light; Virtual Shadow Maps for high-resolution shadows; World Partition for river corridor streaming; PCG for vegetation, rocks, gravel, driftwood, debris, camps, and access points; Niagara for spray, mist, foam, rain, and paddle splashes.
- Raft rubber should show wetness, deformation hints, contact scuffs, and tube volume.
- Rocks should look wet, slick, and dangerous without hiding collision boundaries.
- Foam, bubbles, debris, and surface streaks should support navigation rather than just decorate.
- The first-person stern view must always expose enough bow/raft context to judge angle and drift.

## Audio Direction

Audio should carry physical state:

- Water grows louder near holes, drops, and rocks.
- Paddle catch, blade slip, raft flex, tube scrape, and rock bump are distinct.
- Passengers call useful state changes, not constant noise.
- Guide voice commands should receive clear local feedback through crew acknowledgments, subtitles, and command-state indicators.
- Crew conversations should feel natural in calmer moments and compress into short barks during rapids.
- Privacy-sensitive voice capture should default to local processing and clearly expose microphone settings.
- 3D spatial audio should help locate hazards, swimmers, crew problems, paddle timing, rock impacts, raft scrapes, approaching hydraulics, shore/canyon reflections, and multiplayer voice.

3D audio requirements:

- Use Sound Attenuation-style presets for point, line/area, large rapid, raft, crew, voice, UI, and ambience sources.
- Use binaural/HRTF playback for VR/headphones where supported and panning/surround playback for flat-screen speaker setups.
- Use ambisonic beds for river corridor, canyon, forest, storm, crowd, and access-area ambience where fixed directional texture matters.
- Use reverb zones, audio volumes, occlusion traces, and geometry-aware mix states so canyon walls, boulders, banks, raft tubes, and underwater/near-water perspectives change the soundfield.
- Treat large rapids, waterfalls, wave trains, and river roar as enveloping sources, not tiny point emitters.
- Validate stereo, headphones, VR binaural/HRTF, and 5.1/7.1 surround where supported before content expansion.

Source policy:

- Use free/open, first-party generated, procedural, and AI-generated art/audio assets during development.
- Defer paid art packs, paid sound libraries, marketplace packs, and subscription asset services until the release-readiness gate.
- Keep professional library, marketplace, and field-recording research notes as release-gate reference material.
- Use AI-generated audio and visuals only when prompt/model/tool metadata, license terms, source references, and approval status are tracked.
- Do not treat AI-generated or free/open assets as release-ready until legal, quality, attribution, platform, and provenance review clears them.
- Track every audio asset with source, license, attribution, commercial-use rights, platform rights, processing chain, loudness, loop points, and approval status.
- Prefer Unreal-native audio and MetaSounds for the first implementation; keep Wwise/FMOD as later evaluation options.

## Local AI Direction

The full UE5 version should support local AI integration without making cloud services mandatory for core play.

Responsibilities:

- Lightweight local speech-to-text for guided paddle-raft guide commands where the platform budget allows.
- Constrained, efficient command intent parsing that maps spoken language to explicit crew commands before gameplay state changes.
- Passenger conversation generation or selection grounded in authored persona, trust, fear, fatigue, skill, river, season, recent events, and current danger level.
- Optional local text-to-speech or hybrid recorded/generative voice playback after voice quality, licensing, latency, and platform costs are understood.

Rules:

- Gameplay-critical paddle, brace, high-side, rescue, and recovery commands must remain deterministic after recognition.
- The player must always have manual input parity for every voice command in guided paddle-raft modes.
- Rowing/oar-rig mode does not accept passenger paddle voice commands; it uses direct manual rowing controls.
- Conversation should never override urgent river audio, command acknowledgments, safety cues, or VR comfort.
- Replays should capture enough voice/intent/conversation telemetry to explain outcomes without requiring raw microphone audio.

## Performance Budgets

Exact budgets come after Python profiling and initial Unreal platform selection.

Initial targets to define during Phase 1:

- Physics fixed timestep budget.
- Game thread budget.
- Render thread budget.
- GPU budget for water, spray, lighting, and shadows.
- Audio streaming, decoding, MetaSounds/procedural graph, convolution/reverb, voice-chat, and mix budgets.
- 3D audio budgets for attenuation/spatialization, binaural/HRTF, ambisonics, occlusion traces, reverb sends, surround output, and spatial voice-chat mix.
- Local AI inference, speech recognition, audio capture, and optional speech synthesis budgets.
- VR frametime budget by headset class.
- Memory and streaming budgets per platform.

The game should always have a reduced physics/water mode available for lower-power targets, but the authoritative behavior must remain validated against the Python reference.

## Acceptance Criteria For First Unreal Vertical Slice

The first Unreal vertical slice is successful when:

- It starts from a validated Python scenario.
- It includes at least one validated real-world river/season/difficulty scenario package.
- Unreal can replay the scenario with matching raft path and debug telemetry.
- Native runtime can run the same scenario with comparable qualitative outcome.
- Player can guide from stern first-person view in flat-screen and VR.
- Player can issue at least the core crew commands through manual input and local voice input, with visible confidence/fallback behavior.
- Crew can acknowledge commands and produce state-aware barks or short conversations without disrupting gameplay-critical audio.
- The vertical slice uses free/open, first-party generated, procedural, and AI-generated development art/audio assets with complete source manifests.
- Water, raft, paddle, rock, weather, and crew audio respond to physics/solver telemetry clearly enough to improve river readability.
- 3D audio helps the player locate rapids, hazards, crew, rescue cues, raft contacts, and voice chat from the stern guide seat in stereo, headphones, and VR.
- Ambisonic ambience, reverb, occlusion, and large-source spread make the river corridor feel immersive without hiding gameplay-critical cues.
- Water visuals communicate the same hazards represented in the physics data.
- Force/contact/debug telemetry is visible in-engine.
- The section can be completed, failed, restarted, replayed, and scored.
- Performance is inside the chosen desktop and VR budgets.
- The Milestone 23 acceptance gate passes contract and editor-build checks while later human/guide playtest, VR headset validation, platform packaging, and release certification remain separate signoff gates.

## Open Decisions

- Exact Unreal Engine version for the first vertical slice.
- Exact geospatial import path: Cesium for Unreal, custom GDAL pipeline, Unreal-native landscape tiles, 3D Tiles, or a hybrid.
- First candidate river/section for the real-world vertical slice.
- Whether Chaos or Jolt becomes the first authoritative raft/contact gameplay island after the shared fixture evaluation, with custom reduced runtime as fallback and Chrono as reference.
- How much Chrono::FSI remains useful for offline/reference comparison rather than real-time VR.
- Which platforms are first-class at alpha.
- Whether generated rivers become a shipping feature or remain internal content tooling after real-world river sections are proven.
- How much passenger animation is physical simulation versus animation-driven state.
- Which lightweight local AI runtime powers accurate speech recognition, command intent parsing, crew conversation, and optional speech synthesis per platform.
- Whether crew conversation uses generated local dialogue, authored lines, recorded barks, or a hybrid.
- What voice-command latency, confidence, false-positive, noisy-river/accent accuracy, memory/CPU cost, privacy, and replay-capture requirements are acceptable.
- Whether free/open and AI-generated art/audio assets are good enough for release, or specific paid/professional libraries should be bought near release.
- Which AI-generated audio uses are allowed beyond development-only assets, if any.
- Whether Unreal-native audio/MetaSounds is enough or Wwise/FMOD should be adopted.
- Which binaural/HRTF plugin/runtime, ambisonic capture/playback format, surround target, reverb/occlusion approach, spatial voice-chat path, and spatial-audio QA process are required for the first VR build.
- Whether multiplayer is in scope before the single-player guide experience is complete.
