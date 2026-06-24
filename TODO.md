# TODO

## Rough First Draft Outline

This project is starting as a photo-realistic, physically accurate white water rafting simulator, but the first implementation target is a headless 2D Python physics engine. The engine must procedurally generate rivers and model a top-down rubber raft moving through dynamic 2D current, obstacle, and hazard fields before 2.5D, 3D, Unreal, VR, or Chrono runtime work begins.

See [Physics Engine Plan](docs/physics-engine-plan.md) for the detailed research and implementation plan.
See [Procedural 2D River Generation Plan](docs/2d-river-generation-plan.md) for the first river-generation plan and boat interaction effects.

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

- [ ] Define deterministic 2D river parameter schema.
- [ ] Generate seedable river centerlines.
- [ ] Generate left and right bank boundaries from width profiles.
- [ ] Generate depth proxy, gradient proxy, and base current fields.
- [ ] Place rocks, eddies, eddy lines, standing waves, holes, laterals, shallows, and strainers.
- [ ] Compose feature effects into flow, shear, damping, turbulence, collision, and hazard fields.
- [ ] Add difficulty scoring and rejection/retuning for invalid generated rivers.
- [ ] Add generated river plots and flow-vector plots.
- [ ] Add validation checks for bank intersections, navigable line, bounded speed, and feature counts.

## Milestone 2: Minimal 2D Rigid Raft Sandbox

- [ ] Implement 2D rigid raft state: position, yaw, linear velocity, and angular velocity.
- [ ] Represent the raft using top-down sampled hull/contact points.
- [ ] Implement calm-water drift and damping.
- [ ] Sample spatially varying procedural current fields at hull points.
- [ ] Implement quadratic drag and linear damping from relative water velocity.
- [ ] Implement paddle impulses as force applied through blade-water interaction.
- [ ] Add a flat-current drift scenario.
- [ ] Add a calm-water no-force stability scenario.

## Milestone 3: 2D River Feature Forces

- [ ] Add 2D standing wave zones that behave as potential energy barriers.
- [ ] Add wave climb, stall, surf, and flip classification.
- [ ] Add eddy-line shear fields that apply lateral force and yaw torque.
- [ ] Add hole/hydraulic retention fields.
- [ ] Add lateral wave impulse fields.
- [ ] Add boil/upwelling proxy fields.
- [ ] Add shallow shelf grounding drag.
- [ ] Add local effective damping / hypoviscous surface regions.
- [ ] Add turbulence noise with deterministic seeding.
- [ ] Log current velocity, raft velocity, paddle impulse, collision impulse, shear force, retention force, grounding drag, and line outcome.

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

## Milestone 6: River Solver Upgrade

- [ ] Evaluate a finite-volume shallow-water solver.
- [ ] Evaluate PyClaw/GeoClaw integration versus a custom minimal solver.
- [ ] Use SWASHES analytic cases for validation.
- [ ] Add wet/dry boundary handling.
- [ ] Add hydraulic jump handling.
- [ ] Keep analytic authored features available for controlled raft tests.

## Milestone 7: Compliant Rubber Raft Upgrade

- [ ] Add XPBD-style tube and floor constraints.
- [ ] Add raft modes: rigid, rigid plus compliant shell, and full compliant raft.
- [ ] Add pressure/volume constraint for inflatable tubes.
- [ ] Add rubber stiffness and damping parameter files.
- [ ] Compare rigid and compliant behavior in identical scenarios.
- [ ] Add deformation telemetry.

## Milestone 8: Acceleration And Parameter Fitting

- [ ] Vectorize hot loops with NumPy.
- [ ] Evaluate Numba, JAX, and Taichi for acceleration.
- [ ] Keep a pure Python/NumPy reference implementation for correctness.
- [ ] Add coefficient fitting against reference trajectories.
- [x] Evaluate PyChrono as a reference/backend, not as the first implementation.
- [x] Select Project Chrono as the external backend for long-term boat/water simulation.

## Milestone 9: Unreal And VR Readiness

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
- [ ] Add a `generate_river_2d` example command.
- [ ] Implement deterministic 2D river centerline and bank generation.
- [ ] Implement one downstream 2D current field.
- [ ] Implement one generated rock plus eddy feature.
- [ ] Implement one 2D standing wave field.
- [ ] Implement top-down 2D raft state and fixed-step integration.
- [ ] Add telemetry and Matplotlib trajectory output.
