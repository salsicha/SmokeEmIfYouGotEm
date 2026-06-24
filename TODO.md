# TODO

## Rough First Draft Outline

This project is starting as a photo-realistic, physically accurate white water rafting simulator, but the first implementation target is a headless 2D Python physics engine. The engine must procedurally generate rivers and model a top-down rubber raft moving through dynamic 2D current, obstacle, and hazard fields before 2.5D, 3D, Unreal, VR, or Chrono runtime work begins.

See [Physics Engine Plan](docs/physics-engine-plan.md) for the detailed research and implementation plan.
See [Procedural 2D River Generation Plan](docs/2d-river-generation-plan.md) for the first river-generation plan and boat interaction effects.
See [2.5D Raft Simulation Plan](docs/2.5d-simulation-plan.md) for the height-field, buoyancy, pitch/roll, and wave/hole transition plan.

## Milestone 0: Python Physics Research Foundation

- [x] Create a Python package for the physics engine.
- [x] Add pytest-based test infrastructure.
- [x] Add deterministic fixed-timestep simulation loop.
- [x] Add vector and quaternion math helpers.
- [x] Add telemetry output for every force contribution.
- [x] Add simple plotting for trajectories, force vectors, and raft orientation.
- [x] Document reference papers, validation assumptions, and model limitations.
- [x] Define the first physical accuracy targets for raft, paddle, current, and collision behavior.
- [x] Evaluate candidate physics backends and integrate Project Chrono as the optional selected backend.

## Milestone 1: Procedural 2D River Generator

- [x] Define deterministic 2D river parameter schema.
- [x] Generate seedable river centerlines.
- [x] Generate left and right bank boundaries from width profiles.
- [x] Generate depth proxy, gradient proxy, and base current fields.
- [x] Place rocks, eddies, standing waves, holes, laterals, boils, hypoviscous patches, shallows, and strainers.
- [x] Compose feature effects into flow, shear, damping, turbulence, collision, and hazard fields.
- [ ] Add difficulty scoring and rejection/retuning for invalid generated rivers.
- [x] Add generated river plots and flow-vector plots.
- [x] Add first validation checks for positive width, monotonic sections, centerline rock clearance, bounded speed, and feature counts.

## Milestone 2: Minimal 2D Rigid Raft Sandbox

- [x] Implement 2D rigid raft state: position, yaw, linear velocity, and angular velocity.
- [x] Represent the raft using top-down sampled hull/contact points.
- [x] Implement calm-water drift and damping.
- [x] Sample spatially varying procedural current fields at hull points.
- [x] Implement relative-velocity water drag and linear damping.
- [x] Implement paddle impulses as force applied at guide/passenger sample points.
- [x] Add a generated-current drift scenario.
- [ ] Add a calm-water no-force stability scenario.
- [x] Add optional PyChrono-backed planar integration for the 2D raft body.

## Milestone 3: 2D River Feature Forces

- [x] Add 2D standing wave zones that behave as potential energy barriers.
- [ ] Add wave climb, stall, surf, and flip classification.
- [x] Add eddy/shear fields that apply lateral force and yaw torque.
- [x] Add hole/hydraulic retention fields.
- [x] Add lateral wave impulse fields.
- [x] Add boil/upwelling proxy fields.
- [x] Add shallow shelf grounding drag.
- [x] Add local effective damping / hypoviscous surface regions.
- [ ] Add turbulence noise with deterministic seeding.
- [x] Log current velocity, paddle impulse, collision force, shear force, retention force, grounding drag, and line outcome.

## Milestone 4: 2D Rock Contact And Pinning

- [ ] Add convex rock collision shapes.
- [ ] Implement non-penetration contact resolution.
- [ ] Add restitution, friction, and rubber contact softness.
- [ ] Detect pinning when current force keeps the raft against an obstacle.
- [ ] Add rock bump, deflection, and pinning regression scenarios.
- [ ] Add contact telemetry by hull sample.

## Milestone 5: 2D Validation Harness

- [ ] Add pytest regression tests for every canonical scenario.
- [ ] Add deterministic generation tests for fixed seeds.
- [ ] Add bounded-energy tests for passive current and damping.
- [ ] Add no-unbounded-spin tests for steady flow.
- [ ] Add timestep sensitivity tests.
- [ ] Add parameter sweep scripts for drag, wave retention, eddy shear, grounding drag, and contact friction.
- [ ] Add pass/fail summaries for cleared, stalled, surfed, flipped, or pinned outcomes.
- [ ] Add CSV or Parquet telemetry export.

## Milestone 6: 2.5D River Field Layer

- [ ] Add a `River25D` query API layered on top of generated 2D rivers.
- [ ] Generate bed elevation from gradient, constrictions, rocks, ledges, and shallow shelves.
- [ ] Generate water surface elevation from mean depth plus analytic waves, holes, laterals, and boils.
- [ ] Compute depth, surface normals, slope, vertical/upwelling proxy, damping, and turbulence fields.
- [ ] Add surface and bed diagnostic plots.
- [ ] Add cross-section plots for bed, surface, velocity, and feature tags.
- [ ] Add validation checks for bounded depth, bounded slope, surface continuity, and dry/wet consistency.
- [ ] Add deterministic fixture rivers for flat pool, single standing wave, hole, lateral wave, shallow shelf, and submerged rock.

## Milestone 7: 2.5D Rigid Raft Dynamics

- [ ] Add 6-DoF raft state with position, orientation quaternion, linear velocity, and angular velocity.
- [ ] Add mass, inertia tensor, gravity, and crew/guide mass offsets.
- [ ] Add sampled tube and floor buoyancy/contact patches.
- [ ] Apply buoyancy from submerged sample depth and local surface normal.
- [ ] Apply vertical damping, horizontal water drag, surface-slope forces, and added-mass approximation.
- [ ] Add bed, rock, ledge, and shallow grounding contact against height-aware geometry.
- [ ] Add pitch, roll, surf, flush, grounding, pinning, and flip outcome classification.
- [ ] Add flat-pool draft/trim stability and calm-current pitch/roll regression tests.

## Milestone 8: 2.5D River Feature Dynamics

- [ ] Convert standing waves from planar barriers to surface-height barriers with crest/trough sampling.
- [ ] Add wave clear, stall, surf, and flush regression scenarios.
- [ ] Convert holes to depression, upstream retention, aerated damping, and downstream boil/upwelling systems.
- [ ] Convert lateral waves to height plus sideways impulse and roll torque fields.
- [ ] Add eddy-line roll coupling when only one tube crosses high shear.
- [ ] Add shallow shelf grounding and pivot tests.
- [ ] Add submerged rock launch/scrape tests.
- [ ] Add deterministic boil/upwelling vertical impulse tests.

## Milestone 9: 2.5D Paddle And VR-Ready Input Model

- [ ] Add paddle blade pose, depth, and blade-water relative velocity.
- [ ] Apply paddle forces only while the blade is submerged.
- [ ] Add guide strokes: forward, back, draw, pry, sweep, rudder, and brace.
- [ ] Record blade depth, missed/air strokes, force, torque, and local water velocity.
- [ ] Define the future VR controller-to-paddle mapping.
- [ ] Export paddle/raft telemetry suitable for Unreal replay.

## Milestone 10: 2.5D Validation Harness

- [ ] Add pytest scenarios for flat pool, calm current, standing wave, wave train, hole, eddy line, lateral wave, shallow shelf, submerged rock, and boil.
- [ ] Add bounded-energy tests for passive floating and passive current.
- [ ] Add no-unbounded-spin/no-unbounded-launch tests.
- [ ] Add timestep sensitivity tests for buoyancy, contact, and waves.
- [ ] Add force-sign and torque-sign checks for each feature.
- [ ] Add CSV summaries for clear, stalled, surfed, flushed, grounded, pinned, or flipped outcomes.

## Milestone 11: River Solver Upgrade

- [ ] Evaluate a finite-volume shallow-water solver.
- [ ] Evaluate PyClaw/GeoClaw integration versus a custom minimal solver.
- [ ] Use SWASHES analytic cases for validation.
- [ ] Add wet/dry boundary handling.
- [ ] Add hydraulic jump handling.
- [ ] Keep analytic authored features available for controlled raft tests.

## Milestone 12: Compliant Rubber Raft Upgrade

- [ ] Add XPBD-style tube and floor constraints.
- [ ] Add raft modes: rigid, rigid plus compliant shell, and full compliant raft.
- [ ] Add pressure/volume constraint for inflatable tubes.
- [ ] Add rubber stiffness and damping parameter files.
- [ ] Compare rigid and compliant behavior in identical scenarios.
- [ ] Add deformation telemetry.

## Milestone 13: Acceleration And Parameter Fitting

- [ ] Vectorize hot loops with NumPy.
- [ ] Evaluate Numba, JAX, and Taichi for acceleration.
- [ ] Keep a pure Python/NumPy reference implementation for correctness.
- [ ] Add coefficient fitting against reference trajectories.
- [x] Evaluate PyChrono as a reference/backend, not as the first implementation.
- [x] Select Project Chrono as the external backend for long-term boat/water simulation.

## Milestone 14: Unreal And VR Readiness

- [ ] Choose the exact Unreal Engine 5.x version for visualization and VR.
- [ ] Create the Unreal project only after the Python physics sandbox has validated core raft behavior.
- [ ] Create a standalone native C++ Chrono smoke test before Unreal plugin work.
- [ ] Design the Unreal plugin/module boundary for Chrono.
- [ ] Link Chrono into Unreal as the authoritative raft/water physics runtime.
- [ ] Keep Unreal Chaos available only for incidental non-authoritative effects.
- [ ] Enable OpenXR-based VR support.
- [ ] Define the data bridge from Python validation output to Chrono/Unreal playback and debug visualization.
- [ ] Define fixed-step Chrono scheduling and Unreal render interpolation.
- [ ] Set up Enhanced Input actions for VR controllers, keyboard, mouse, and gamepad.
- [ ] Define performance budgets for desktop, VR, and handheld targets.
- [ ] Verify Chrono module availability and build process for each target platform.
- [ ] Gather reference for raft materials, river canyons, wet rocks, water, foam, spray, PFDs, helmets, ropes, and paddles.

## Technical Notes To Revisit

- [ ] Evaluate Unreal Water plugin, custom water simulation, third-party water systems, or a hybrid.
- [ ] Evaluate Unreal Chaos only for incidental non-authoritative effects after the Chrono raft model exists.
- [ ] Decide how river currents are authored: spline fields, volumes, flow maps, computational fluid approximations, or a hybrid.
- [ ] Define measurable physical accuracy targets for the first vertical slice.
- [ ] Decide which aspects of the simulation must be physically accurate and which can be perceptual approximations.
- [ ] Identify reference footage, river data, and expert guide feedback needed for validation.
- [ ] Evaluate VR performance impact before committing to expensive water, lighting, and particle features.
- [x] Decide that Project Chrono is the planned full game physics runtime.
- [ ] Decide which Python validation models migrate into native Chrono C++ code.
- [ ] Investigate multiplayer feasibility only after the single-player raft loop feels good.

## Immediate Next Steps

- [x] Create the Python package skeleton.
- [x] Add a `generate_river_2d` example command.
- [x] Implement deterministic 2D river centerline and bank generation.
- [x] Implement one downstream 2D current field.
- [x] Implement one generated rock plus eddy feature.
- [x] Implement one 2D standing wave field.
- [x] Implement top-down 2D raft state and fixed-step integration.
- [x] Add telemetry and Matplotlib trajectory output.
- [ ] Start the 2.5D field layer with bed/surface/depth queries and diagnostic plots.
- [ ] Add a flat-pool 6-DoF raft draft stability test.
