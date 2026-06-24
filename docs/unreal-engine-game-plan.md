# Unreal Engine Full Game Plan

## Goal

Build the full SmokeEmIfYouGotEm rafting simulator as a multi-platform Unreal Engine game after the Python modeling, validation, and profiling work has proven the raft/water behavior.

The Unreal game should deliver the first-person guide fantasy: seated in the stern, reading water, calling commands, steering with physically meaningful paddle strokes, managing passenger safety, and feeling the raft move through a photo-real white water environment.

See [Real-World River Content And Seasonal Flow Plan](real-world-river-content-plan.md) for the geospatial extraction, rapid identification, seasonal flow, adaptive fluid-parameter, and river-selection work that must feed Unreal content.
See [Audio Asset Sourcing Plan](audio-asset-sourcing-plan.md) for the production audio source policy, library shortlist, field-recording plan, AI-audio limits, and asset manifest.

## Hard Dependency Gate

Do not start the production Unreal Engine project until the Python physics program reaches an explicit exit gate.

Required before Unreal production begins:

- PyClaw 2.5D reference scenarios run deterministically.
- Custom C++ reduced shallow-water / height-field scenarios run from the same solver-neutral scenario packages.
- C++ water fields, probe traces, raft force samples, and scenario outcomes match PyClaw within accepted tolerances.
- Python profiling identifies hot loops, memory costs, timestep sensitivity, and per-scenario runtime budgets.
- Parameter files and telemetry schemas are stable enough to share with C++/Unreal tooling.
- Force model choices are documented: which effects come from PyClaw reference, which live in the C++ water solver, which move into Chrono/custom raft dynamics, and which are visual-only.
- Project Chrono runtime path is validated by a standalone C++ smoke test.
- At least one real-world river section has a complete source manifest, terrain/course extraction, rapid annotations, gauge/flow research, season presets, difficulty presets, and low/median/high flow validation through PyClaw and the custom C++ solver.
- Adaptive fluid parameters are documented for river, season, flow percentile, difficulty, channel geometry, roughness, aeration/turbulence, eddy-line shear, hole retention, wave train strength, boils, shallows, raft drag, paddle catch, and damping.
- A first real-world corridor package exists for Unreal preproduction: terrain, centerline, banks, imagery masks, rapid boundaries, hazards, flow presets, confidence metadata, and validation telemetry.
- Unreal readiness report exists with performance budgets for desktop, VR, and handheld/portable targets.

Unreal can still be used earlier for throwaway visual studies, reference capture, or material tests, but the real game project should wait until the modeling and profiling gate is passed.

## Engine Scope

Use Unreal Engine as the product runtime, presentation layer, platform layer, and content authoring environment.

Unreal owns:

- First-person and VR camera
- Input, motion controllers, haptics, and accessibility settings
- Local speech recognition, command intent routing, crew conversation, passenger persona state, and optional local speech synthesis
- Visual raft, water, terrain, foliage, spray, foam, lighting, weather, and post-processing
- Audio, spatial cues, voice lines, UI, menus, scoring, replay presentation, and save data
- Audio asset ingest, source manifests, license/attribution tracking, interactive water sound, crew barks, dialogue playback, voice-chat mix, and runtime audio budgets
- Level authoring, cooked content, build automation, and platform packaging

Chrono or the validated reduced runtime owns:

- Authoritative raft transform and velocities
- Raft-water force integration
- Rock, bank, bed, and raft contact response
- Paddle blade force transfer
- Compliant raft experiments
- Physics telemetry, debug forces, and deterministic replay data where possible

Unreal Chaos may be used for incidental non-authoritative physics such as loose props, splash debris, visual ropes, or background objects. It should not own the raft.

## Target Product Shape

### Primary Experience

- First-person guide perspective from the stern.
- VR and flat-screen support from the start of Unreal production.
- Single raft, single-player guide role as the first production target.
- Scripted or AI-assisted passenger crew responding to guide commands.
- Local AI voice interaction so the guide can speak paddle, brace, high-side, rescue, and recovery commands.
- Crew members can talk, acknowledge commands, react to hazards, and hold conversations shaped by passenger persona, trust, fear, fatigue, skill, weather, river history, and recent run events.
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

## Production Milestones

### Phase 0: Python Exit Gate

Finish before Unreal production:

- Complete PyClaw 2.5D reference harness.
- Complete custom C++ reduced shallow-water / height-field solver harness.
- Complete PyClaw-vs-C++ comparison and tuning reports.
- Complete first 2.5D raft/water coupling model against both solver outputs.
- Profile Python models and decide acceleration strategy.
- Validate representative scenarios: flat pool, calm current, standing wave, hole, eddy line, lateral wave, shallow shelf, submerged rock, boil, and pinning.
- Produce shared parameter files for raft, water, paddle, rock, and scoring coefficients.
- Produce replay/telemetry examples that Unreal can visualize.
- Confirm Chrono C++ viability outside Unreal.
- Complete one real-world river scenario package with geospatial source manifest, extracted course/elevation, rapid labels, seasonal flow bands, difficulty presets, and PyClaw/custom-C++ validation.
- Produce one Unreal-ready real-world river corridor package for preproduction review.

Deliverable:

- Python-to-Unreal readiness report, including the first real-world river content readiness appendix.

### Phase 1: Unreal Preproduction

Start only after Phase 0 is accepted.

Tasks:

- Choose the exact Unreal Engine 5.x version and lock it for the first vertical slice.
- Re-check the latest stable UE5 feature set before locking the version. As of this planning pass, Epic's public docs are on UE 5.8, so expect Nanite foliage, Nanite landscape/spline/tessellation workflows, Lumen, Virtual Shadow Maps, World Partition, PCG, Niagara, Substrate/material layering, and OpenXR to be evaluated for the first slice.
- Define target platforms for the first playable build.
- Create coding standards for C++, Blueprint exposure, data assets, and content naming.
- Define plugin/module boundaries: core game, Chrono bridge, water visualization, raft, river, input, UI, local AI/voice, crew AI, audio, and debug.
- Build a small visual prototype with placeholder physics replay data, not gameplay physics.
- Establish asset scale, coordinate conventions, units, and import/export rules.
- Define geospatial import rules: coordinate reference systems, WGS84/local transforms, source manifests, terrain tile sizes, imagery masks, river corridor bounds, and confidence metadata.
- Evaluate local/offline AI runtime options for target platforms: speech-to-text, constrained command parsing, crew dialogue generation/selection, optional local speech synthesis, latency, memory, CPU/GPU cost, licensing, privacy, and console feasibility.
- Build the production audio source plan: approved vendors, field-recording needs, license requirements, attribution rules, AI-audio policy, asset manifest, LFS/storage policy, and Unreal import conventions.
- Start with Unreal-native audio and MetaSounds for interactive water/raft/crew sound; evaluate Wwise/FMOD only if the native toolchain cannot meet authoring, mixing, localization, memory, or platform needs.
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
- Add guide voice/command inputs for passenger crew using local speech recognition where available.
- Map recognized speech into deterministic command intents: forward paddle, back paddle, left/right paddle, stop, hold on, brace, high side, rescue, swimmer callout, and recovery commands.
- Add confidence thresholds, command repeat/confirm behavior for ambiguous recognition, subtitles, accessibility fallbacks, and manual input parity.
- Add noisy-water and VR microphone test scenes for false-positive and latency tuning.

Deliverable:

- Playable first-person raft control in a simple test river with manual and local voice command paths.

### Phase 4: River Visualization And Level Pipeline

Tasks:

- Import Python-authored and real-world geospatial river sections with scenario metadata, source manifests, seasonal presets, difficulty presets, and validation confidence.
- Build spline/volume/data-asset representation for river centerline, banks, cross sections, rapids, hazards, gauges, season/flow presets, and current fields.
- Convert DEM/lidar, aerial/satellite masks, hydrography, and reviewed rapid annotations into Unreal terrain/corridor assets.
- Use Cesium for Unreal or equivalent geospatial tooling where it helps with real-world scale, WGS84 positioning, 3D Tiles, terrain, imagery, and georeferenced scene setup.
- Create photo-real canyon/forest/desert/mountain river environment pipeline using Nanite rocks/canyon walls/terrain details, Nanite foliage, Lumen, Virtual Shadow Maps, World Partition, PCG, Niagara, and advanced material layering where supported.
- Add water material, foam lines, bubbles, waves, wet rocks, spray, mist, debris cues, aeration masks, turbulence masks, and seasonal water appearance.
- Build first interactive water-audio prototype from recorded/downloaded assets: river bed, nearby rapid, hydraulic hole, eddy line, spray, foam, raft scrape, paddle catch, rock impact, weather, and canyon reflections driven by solver telemetry.
- Add debug view that compares solver fields and adaptive fluid parameters with visible water cues.
- Define handoff from Python/geospatial/generated data to Unreal-authored content.

Deliverable:

- One believable real-world rapid corridor rendered with readable current, hazards, seasonal flow variation, and raft motion.

### Phase 5: Core Gameplay Vertical Slice

Tasks:

- Build one training section and one technical rapid.
- Add passenger command response: forward, back, left, right, hold on, brace.
- Add local voice-command path for the same passenger responses, with deterministic command execution after intent recognition.
- Add crew acknowledgments, missed-command behavior, hesitation, and urgency barks based on command confidence and passenger state.
- Add safety outcomes: fall out, swim, rescue, pin, surf, flip, flush.
- Add scoring for safety, line, boat angle, paddle efficiency, passenger trust, and completion.
- Add restart, replay, ghost telemetry, and after-action feedback.
- Add basic menus and settings.
- Add microphone, push-to-talk/open-mic, subtitles, command confirmation, voice sensitivity, privacy/offline, and fallback-control settings.
- Add river, section, season, flow, difficulty, and raft/crew selection backed by validated data assets.
- Add source-approved audio for the vertical slice: water beds, rapid features, raft/paddle/rock Foley, guide commands, crew acknowledgments, UI, weather, and fail/safety states.

Deliverable:

- One complete playable vertical slice from launch to scoring screen.

### Phase 6: VR Quality Pass

Tasks:

- Tune motion comfort with real headset testing.
- Add haptics for paddle catch, rock bumps, wave hits, and raft impacts.
- Validate seated play space assumptions.
- Add accessibility options for physical stroke intensity and comfort.
- Ensure UI can be used in VR and flat-screen.
- Measure VR frametime under worst-case water/physics scenes.

Deliverable:

- VR-ready vertical slice that passes comfort and performance budgets.

### Phase 7: Content Expansion

Tasks:

- Build additional river biomes.
- Build additional real-world river sections from source manifests and reviewed rapid annotations.
- Add difficulty progression.
- Add more raft types and handling profiles.
- Add passenger archetypes and crew trust progression.
- Add AI-assisted crew conversations for calm water, eddies, scouting, recovery pools, run starts, run finishes, swims, rescues, and post-rapid debriefs.
- Add passenger persona data, relationship memory, river knowledge, skill/fear/fatigue state, and conversation pacing rules.
- Add conversation guardrails so active-rapid dialogue stays short, command acknowledgments take priority, and generated chatter never blocks safety-critical audio.
- Expand purchased/downloaded and field-recorded audio libraries for additional rivers, seasons, flow levels, raft types, gear, weather, and biomes.
- Use AI-generated audio only for approved supplemental variants, temporary dialogue, non-critical UI/debug cues, or ideation after provenance and license review.
- Add challenge variants and generated rapid support if validated.
- Expand weather, water levels, rescue scenarios, and training lessons.

Deliverable:

- Alpha-scale game loop with multiple playable river sections.

### Phase 8: Optimization And Platform Hardening

Tasks:

- Profile CPU physics, render thread, game thread, GPU water, particles, shadows, and asset streaming.
- Profile audio voice counts, streaming, decompression, convolution/reverb, MetaSounds graphs, source effects, voice chat, and memory residency.
- Profile local AI inference, speech recognition latency, audio capture cost, local speech synthesis, memory footprint, and model loading.
- Add platform-specific runtime modes for full Chrono, reduced Chrono, replay/debug, and lower-cost visual water.
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

- `RaftsimCore`: shared game types, units, data schemas, telemetry types.
- `RaftsimPhysics`: native physics runtime bridge, Chrono/reduced model integration.
- `RaftsimRiver`: river data assets, scenario loading, flow visualization, hazard volumes.
- `RaftsimGeo`: optional geospatial import/conversion tooling for source manifests, coordinate transforms, terrain/corridor packages, imagery masks, and rapid annotations.
- `RaftsimRaft`: raft actor, passenger attachment points, animation hooks, damage/safety state.
- `RaftsimInput`: flat-screen, gamepad, VR controller, paddle, command, and accessibility mappings.
- `RaftsimAudio`: asset manifest ingest, runtime audio states, MetaSounds/middleware events, water/raft/crew mix routing, source provenance, and debug meters.
- `RaftsimVoice`: microphone capture, local speech recognition integration, command grammar, intent confidence, push-to-talk/open-mic modes, subtitles, and fallback routing.
- `RaftsimCrewAI`: passenger persona state, command interpretation, conversation state, crew memory, local dialogue generation/selection, and safety-critical dialogue priority.
- `RaftsimUI`: menus, HUD, replay, scoring, training feedback.
- `RaftsimDebug`: force vectors, current fields, contacts, profiling views, replay inspectors.

### Data Assets

Use Unreal data assets for game-facing tuning while keeping source-of-truth exports traceable to Python:

- River section definitions
- River catalog, region, section, season, flow, difficulty, gauge, and source-manifest definitions
- Water field / feature metadata
- Geospatial corridor metadata, centerlines, banks, cross sections, rapid boundaries, imagery masks, and data confidence scores
- Raft physical parameters
- Paddle stroke parameters
- Passenger archetypes
- Voice command grammar, synonyms, confidence thresholds, locale/accent settings, and fallback command mappings
- Crew persona definitions, conversation policies, trust/fear/fatigue/skill tuning, relationship memory rules, and dialogue style profiles
- Audio source manifests, library/vendor records, license terms, attribution requirements, AI generation provenance, approval status, UCS metadata, loop points, loudness targets, and runtime mix categories
- Interactive audio parameter maps for flow speed, depth, turbulence, aeration, raft impact, paddle catch, rock scrape, weather, canyon geometry, camera perspective, and VR comfort mode
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
- Audio event id, source asset id, mix state, runtime parameters, voice count, streaming/decompression cost, and source-manifest approval state
- Force contributions
- Contact points
- River sample values
- Outcome classifications

Unreal should be able to play a Python-produced run before it can run the native physics model live.

## Visual Direction

The game should be photo-real and readable:

- Water cues must reveal real gameplay information: current direction, eddy lines, holes, shallow shelves, rocks, laterals, boils, and recovery pools.
- The highest-value playable sections should be grounded in extracted real-world course/elevation data and reviewed aerial/satellite rapid annotations.
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
- VR spatial audio should help locate hazards, swimmers, and crew problems.

Source policy:

- Use professional downloaded libraries and custom field recordings as the shipping backbone.
- Use custom field recordings for signature real-river identity: guide seat, shore, eddy, rapid, hydrophone, raft contact, paddle, gear, and crew perspectives.
- Use AI-generated audio only for prototyping, ideation, non-critical variations, abstract UI/debug sounds, or temp dialogue unless legal/audio review approves a shipping use.
- Avoid AI-generated white water, raft contact, paddle, rock, crew voice performance, and music as primary shipping assets.
- Track every audio asset with source, license, attribution, commercial-use rights, platform rights, processing chain, loudness, loop points, and approval status.
- Prefer Unreal-native audio and MetaSounds for the first implementation; keep Wwise/FMOD as later evaluation options.

## Local AI Direction

The full UE5 version should support local AI integration without making cloud services mandatory for core play.

Responsibilities:

- Local speech-to-text for guide commands where the platform budget allows.
- Constrained command intent parsing that maps spoken language to explicit crew commands before gameplay state changes.
- Passenger conversation generation or selection grounded in authored persona, trust, fear, fatigue, skill, river, season, recent events, and current danger level.
- Optional local text-to-speech or hybrid recorded/generative voice playback after voice quality, licensing, latency, and platform costs are understood.

Rules:

- Gameplay-critical paddle, brace, high-side, rescue, and recovery commands must remain deterministic after recognition.
- The player must always have manual input parity for every voice command.
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
- The vertical slice uses licensed/downloaded or field-recorded audio assets with complete source manifests.
- Water, raft, paddle, rock, weather, and crew audio respond to physics/solver telemetry clearly enough to improve river readability.
- Water visuals communicate the same hazards represented in the physics data.
- Force/contact/debug telemetry is visible in-engine.
- The section can be completed, failed, restarted, replayed, and scored.
- Performance is inside the chosen desktop and VR budgets.

## Open Decisions

- Exact Unreal Engine version for the first vertical slice.
- Exact geospatial import path: Cesium for Unreal, custom GDAL pipeline, Unreal-native landscape tiles, 3D Tiles, or a hybrid.
- First candidate river/section for the real-world vertical slice.
- Whether the first live runtime uses Chrono rigid-body integration, reduced native C++ force integration, or both.
- How much Chrono::FSI is practical for real-time VR.
- Which platforms are first-class at alpha.
- Whether generated rivers become a shipping feature or remain internal content tooling after real-world river sections are proven.
- How much passenger animation is physical simulation versus animation-driven state.
- Which local AI runtime powers speech recognition, command intent parsing, crew conversation, and optional speech synthesis per platform.
- Whether crew conversation uses generated local dialogue, authored lines, recorded barks, or a hybrid.
- What voice-command latency, confidence, false-positive, privacy, and replay-capture requirements are acceptable.
- Which professional libraries and field-recording sessions become the first approved production audio sources.
- Which AI-generated audio uses are allowed in shipping builds, if any.
- Whether Unreal-native audio/MetaSounds is enough or Wwise/FMOD should be adopted.
- Whether multiplayer is in scope before the single-player guide experience is complete.
