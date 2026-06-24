# Unreal Engine Full Game Plan

## Goal

Build the full SmokeEmIfYouGotEm rafting simulator as a multi-platform Unreal Engine game after the Python modeling, validation, and profiling work has proven the raft/water behavior.

The Unreal game should deliver the first-person guide fantasy: seated in the stern, reading water, calling commands, steering with physically meaningful paddle strokes, managing passenger safety, and feeling the raft move through a photo-real white water environment.

## Hard Dependency Gate

Do not start the production Unreal Engine project until the Python physics program reaches an explicit exit gate.

Required before Unreal production begins:

- PyClaw 2.5D reference scenarios run deterministically.
- Custom C++ reduced shallow-water / height-field scenarios run from the same generated scenario packages.
- C++ water fields, probe traces, raft force samples, and scenario outcomes match PyClaw within accepted tolerances.
- Python profiling identifies hot loops, memory costs, timestep sensitivity, and per-scenario runtime budgets.
- Parameter files and telemetry schemas are stable enough to share with C++/Unreal tooling.
- Force model choices are documented: which effects come from PyClaw reference, which live in the C++ water solver, which move into Chrono/custom raft dynamics, and which are visual-only.
- Project Chrono runtime path is validated by a standalone C++ smoke test.
- Unreal readiness report exists with performance budgets for desktop, VR, and handheld/portable targets.

Unreal can still be used earlier for throwaway visual studies, reference capture, or material tests, but the real game project should wait until the modeling and profiling gate is passed.

## Engine Scope

Use Unreal Engine as the product runtime, presentation layer, platform layer, and content authoring environment.

Unreal owns:

- First-person and VR camera
- Input, motion controllers, haptics, and accessibility settings
- Visual raft, water, terrain, foliage, spray, foam, lighting, weather, and post-processing
- Audio, spatial cues, voice lines, UI, menus, scoring, replay presentation, and save data
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
- Realistic but teachable white water behavior.
- Training-grade feedback and replay tools.

### Initial Game Modes

- Training school: calm water, strokes, ferrying, eddy turns, wave approach, rescue basics.
- Rapid challenge: one rapid, restart quickly, score safety/line/control.
- River section: linked rapids with scouting, recovery pools, and cumulative crew state.
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

Deliverable:

- Python-to-Unreal readiness report.

### Phase 1: Unreal Preproduction

Start only after Phase 0 is accepted.

Tasks:

- Choose the exact Unreal Engine 5.x version and lock it for the first vertical slice.
- Define target platforms for the first playable build.
- Create coding standards for C++, Blueprint exposure, data assets, and content naming.
- Define plugin/module boundaries: core game, Chrono bridge, water visualization, raft, river, input, UI, debug.
- Build a small visual prototype with placeholder physics replay data, not gameplay physics.
- Establish asset scale, coordinate conventions, units, and import/export rules.
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
- Add guide voice/command inputs for passenger crew.

Deliverable:

- Playable first-person raft control in a simple test river.

### Phase 4: River Visualization And Level Pipeline

Tasks:

- Import Python-authored river sections and scenario metadata.
- Build spline/volume/data-asset representation for river centerline, banks, hazards, and current fields.
- Create photo-real canyon/forest/desert/mountain river environment pipeline.
- Add water material, foam lines, bubbles, waves, wet rocks, spray, mist, and debris cues.
- Add debug view that compares authored flow fields with visible water cues.
- Define handoff from Python/generated data to Unreal-authored content.

Deliverable:

- One believable rapid rendered with readable current, hazards, and raft motion.

### Phase 5: Core Gameplay Vertical Slice

Tasks:

- Build one training section and one technical rapid.
- Add passenger command response: forward, back, left, right, hold on, brace.
- Add safety outcomes: fall out, swim, rescue, pin, surf, flip, flush.
- Add scoring for safety, line, boat angle, paddle efficiency, passenger trust, and completion.
- Add restart, replay, ghost telemetry, and after-action feedback.
- Add basic menus and settings.

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
- Add difficulty progression.
- Add more raft types and handling profiles.
- Add passenger archetypes and crew trust progression.
- Add challenge variants and generated rapid support if validated.
- Expand weather, water levels, rescue scenarios, and training lessons.

Deliverable:

- Alpha-scale game loop with multiple playable river sections.

### Phase 8: Optimization And Platform Hardening

Tasks:

- Profile CPU physics, render thread, game thread, GPU water, particles, shadows, and asset streaming.
- Add platform-specific runtime modes for full Chrono, reduced Chrono, replay/debug, and lower-cost visual water.
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
- `RaftsimRaft`: raft actor, passenger attachment points, animation hooks, damage/safety state.
- `RaftsimInput`: flat-screen, gamepad, VR controller, paddle, command, and accessibility mappings.
- `RaftsimUI`: menus, HUD, replay, scoring, training feedback.
- `RaftsimDebug`: force vectors, current fields, contacts, profiling views, replay inspectors.

### Data Assets

Use Unreal data assets for game-facing tuning while keeping source-of-truth exports traceable to Python:

- River section definitions
- Water field / feature metadata
- Raft physical parameters
- Paddle stroke parameters
- Passenger archetypes
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
- Force contributions
- Contact points
- River sample values
- Outcome classifications

Unreal should be able to play a Python-produced run before it can run the native physics model live.

## Visual Direction

The game should be photo-real and readable:

- Water cues must reveal real gameplay information: current direction, eddy lines, holes, shallow shelves, rocks, laterals, boils, and recovery pools.
- Raft rubber should show wetness, deformation hints, contact scuffs, and tube volume.
- Rocks should look wet, slick, and dangerous without hiding collision boundaries.
- Foam, bubbles, debris, and surface streaks should support navigation rather than just decorate.
- The first-person stern view must always expose enough bow/raft context to judge angle and drift.

## Audio Direction

Audio should carry physical state:

- Water grows louder near holes, drops, and rocks.
- Paddle catch, blade slip, raft flex, tube scrape, and rock bump are distinct.
- Passengers call useful state changes, not constant noise.
- VR spatial audio should help locate hazards, swimmers, and crew problems.

## Performance Budgets

Exact budgets come after Python profiling and initial Unreal platform selection.

Initial targets to define during Phase 1:

- Physics fixed timestep budget.
- Game thread budget.
- Render thread budget.
- GPU budget for water, spray, lighting, and shadows.
- VR frametime budget by headset class.
- Memory and streaming budgets per platform.

The game should always have a reduced physics/water mode available for lower-power targets, but the authoritative behavior must remain validated against the Python reference.

## Acceptance Criteria For First Unreal Vertical Slice

The first Unreal vertical slice is successful when:

- It starts from a validated Python scenario.
- Unreal can replay the scenario with matching raft path and debug telemetry.
- Native runtime can run the same scenario with comparable qualitative outcome.
- Player can guide from stern first-person view in flat-screen and VR.
- Water visuals communicate the same hazards represented in the physics data.
- Force/contact/debug telemetry is visible in-engine.
- The section can be completed, failed, restarted, replayed, and scored.
- Performance is inside the chosen desktop and VR budgets.

## Open Decisions

- Exact Unreal Engine version for the first vertical slice.
- Whether the first live runtime uses Chrono rigid-body integration, reduced native C++ force integration, or both.
- How much Chrono::FSI is practical for real-time VR.
- Which platforms are first-class at alpha.
- Whether generated rivers become a shipping feature or remain internal content tooling.
- How much passenger animation is physical simulation versus animation-driven state.
- Whether multiplayer is in scope before the single-player guide experience is complete.
