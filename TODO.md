# TODO

## Rough First Draft Outline

This project is starting as a photo-realistic, physically accurate 3D white water rafting simulator built in Unreal Engine with a first-person camera from the guide's position in the back of the raft, VR support, and multi-platform goals. The first playable milestone should prove that guiding a raft through current feels physically grounded, readable, immersive, and fun before the project expands into campaign, progression, or large river systems.

## Milestone 0: Project Foundation

- [ ] Choose the exact Unreal Engine 5.x version for the first project.
- [ ] Create the Unreal project with a clean multi-platform folder structure.
- [ ] Add a proper Unreal `.gitignore`.
- [ ] Decide whether the initial project uses C++, Blueprint, or a hybrid.
- [ ] Enable and validate OpenXR-based VR support.
- [ ] Set up Enhanced Input actions for VR controllers, keyboard, mouse, and gamepad.
- [ ] Add basic build targets for desktop and initial VR platforms.
- [ ] Add initial README with setup and build instructions.
- [ ] Define the first performance budgets for flat-screen, PC VR, and handheld/Steam Deck targets.
- [ ] Define the first physical accuracy targets for raft, paddle, current, and collision behavior.

## Milestone 1: First-Person And VR Guide Prototype

- [ ] Create a simple test river map.
- [ ] Add a raft pawn or actor with basic movement.
- [ ] Add a first-person guide camera anchored to the stern of the raft.
- [ ] Add VR head tracking, recentering, seated height calibration, and comfort options.
- [ ] Add mouse, keyboard, and gamepad look controls for flat-screen play.
- [ ] Keep the raft bow, tubes, guide hands, paddle, and passengers visible enough to ground the player.
- [ ] Implement forward, back, left, right, and brace commands.
- [ ] Implement VR guide paddle grip, blade angle, stroke depth, and pull path.
- [ ] Implement a flat-screen analog paddle stroke fallback.
- [ ] Make current push the raft downstream.
- [ ] Add simple raft rotation from paddle force and current.
- [ ] Add restrained camera motion for waves, drops, and collisions.
- [ ] Add restart and reset controls for rapid iteration.

## Milestone 2: Physical River And Raft Model

- [ ] Add visible current direction cues based on real water behavior.
- [ ] Add spatial current volumes or flow fields with debug visualization.
- [ ] Add rock hazards with physically grounded collision, pinning, and deflection.
- [ ] Add eddies, slower current zones, standing waves, holes, and hydraulic placeholders.
- [ ] Model raft buoyancy, drag, angular damping, contact softness, and weight distribution.
- [ ] Make paddle strokes apply force based on blade position, direction, angle, depth, and water velocity.
- [ ] Log telemetry for current velocity, raft velocity, paddle impulse, collisions, and line choice.
- [ ] Establish a visual language for safe water, risky water, and danger water without breaking realism.
- [ ] Test first-person camera height, field of view, motion, and obstruction at multiple screen sizes.
- [ ] Make foam lines, surface streaks, debris, and wave shapes communicate current direction from inside the raft.

## Milestone 3: Photoreal Visual And Audio Baseline

- [ ] Gather reference for raft materials, river canyons, wet rocks, water, foam, spray, PFDs, helmets, ropes, and paddles.
- [ ] Build a first-pass photo-real lighting and material pipeline.
- [ ] Add water, foam, mist, splash, wetness, and reflection tests.
- [ ] Add spatial audio tests for current, paddle hits, raft rubber, rocks, passengers, and rescue cues.
- [ ] Validate visual readability in VR and flat-screen modes.
- [ ] Create graphics scalability tiers for PC VR, high-end desktop, and handheld targets.

## Milestone 4: Scoring, Telemetry, And Simulation Loop

- [ ] Add start and finish gates.
- [ ] Track time through the rapid.
- [ ] Score clean lines, collisions, passenger safety, physical efficiency, and recovery.
- [ ] Add a telemetry review screen for current, raft angle, paddle force, collision impulses, and passenger events.
- [ ] Add a run summary screen.
- [ ] Add quick retry.
- [ ] Add basic audio feedback for water, collisions, and paddle calls.

## Milestone 5: Crew And Passenger Layer

- [ ] Add placeholder passenger characters.
- [ ] Place passengers in front of the guide so their paddle timing and panic states are readable from first person.
- [ ] Make passengers paddle in response to guide commands.
- [ ] Add passenger brace state.
- [ ] Add simple trust or panic meter.
- [ ] Add passenger fall-out event after major hits.
- [ ] Add rescue interaction placeholder.
- [ ] Add VR-compatible rescue and communication interactions.

## Milestone 6: VR And Multi-Platform Readiness

- [ ] Keep all gameplay actions controller-friendly.
- [ ] Test mouse and keyboard, Xbox-style controller, and Steam Deck-style controls.
- [ ] Test at least one OpenXR-compatible PC VR headset.
- [ ] Maintain VR comfort options for vignette, camera motion, horizon stabilization, snap/smooth turning, and seated recentering.
- [ ] Avoid platform-specific assumptions in UI, save data, and input.
- [ ] Add scalable graphics settings.
- [ ] Define performance budgets for desktop, VR, and handheld targets.
- [ ] Check packaging on at least one target platform before adding large systems.

## Milestone 7: Content Direction

- [ ] Design the first short rapid.
- [ ] Design three beginner hazards.
- [ ] Design one rescue scenario.
- [ ] Define river difficulty classes for the simulator.
- [ ] Sketch campaign structure or challenge progression.
- [ ] Decide whether the first vertical slice is a guided tutorial, a timed challenge, or a short river run.

## Technical Notes To Revisit

- [ ] Evaluate Unreal Water plugin, custom water simulation, third-party water systems, or a hybrid.
- [ ] Evaluate Chaos buoyancy needs versus a custom raft force model.
- [ ] Decide how river currents are authored: spline fields, volumes, flow maps, computational fluid approximations, or a hybrid.
- [ ] Define measurable physical accuracy targets for the first vertical slice.
- [ ] Decide which aspects of the simulation must be physically accurate and which can be perceptual approximations.
- [ ] Identify reference footage, river data, and expert guide feedback needed for validation.
- [ ] Evaluate VR performance impact before committing to expensive water, lighting, and particle features.
- [ ] Investigate multiplayer feasibility only after the single-player raft loop feels good.

## Immediate Next Steps

- [ ] Create the Unreal project.
- [ ] Add initial source control ignores and project README.
- [ ] Create a minimal VR-ready test map with a seated stern guide position.
- [ ] Prototype raft movement on a flat plane before adding complex water.
- [ ] Add a single downstream current field with debug vectors.
- [ ] Add simple paddle force telemetry.
- [ ] Tune the first-person and VR guide camera until the raft, line, passengers, and hazards are readable and comfortable.
