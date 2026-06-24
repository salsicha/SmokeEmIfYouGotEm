# TODO

## Rough First Draft Outline

This project is starting as a photo-realistic, physically accurate white water rafting simulator, but the first implementation target is a headless Python physics engine. The engine must model a rubber raft moving over dynamic river surfaces before Unreal, VR, or 3D graphics work begins.

See [Physics Engine Plan](docs/physics-engine-plan.md) for the detailed research and implementation plan.

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

## Milestone 1: Minimal Rigid Raft Sandbox

- [ ] Implement 6-DoF rigid raft state: position, orientation, linear velocity, and angular velocity.
- [ ] Represent the raft using sampled hull/contact points.
- [ ] Implement still-water buoyancy and trim equilibrium.
- [ ] Implement spatially varying current fields.
- [ ] Implement quadratic drag and linear damping from relative water velocity.
- [ ] Implement paddle impulses as force applied through blade-water interaction.
- [ ] Add a flat-current drift scenario.
- [ ] Add a still-water float-equilibrium scenario.

## Milestone 2: Dynamic River Feature Forces

- [ ] Add analytic standing wave surfaces that behave as potential energy barriers.
- [ ] Add wave climb, stall, surf, and flip classification.
- [ ] Add eddy-line shear fields that apply lateral force and yaw torque.
- [ ] Add vertical upwelling fields.
- [ ] Add local effective damping / hypoviscous surface regions.
- [ ] Add turbulence noise with deterministic seeding.
- [ ] Log current velocity, raft velocity, paddle impulse, collision impulse, shear force, upwelling force, and line outcome.

## Milestone 3: Rock Contact And Pinning

- [ ] Add convex rock collision shapes.
- [ ] Implement non-penetration contact resolution.
- [ ] Add restitution, friction, and rubber contact softness.
- [ ] Detect pinning when current force keeps the raft against an obstacle.
- [ ] Add rock bump, deflection, and pinning regression scenarios.
- [ ] Add contact telemetry by hull sample.

## Milestone 4: Validation Harness

- [ ] Add pytest regression tests for every canonical scenario.
- [ ] Add bounded-energy tests for passive water.
- [ ] Add no-unbounded-spin tests for steady flow.
- [ ] Add timestep sensitivity tests.
- [ ] Add parameter sweep scripts for drag, buoyancy, wave height, eddy shear, and contact friction.
- [ ] Add pass/fail summaries for cleared, stalled, surfed, flipped, or pinned outcomes.
- [ ] Add CSV or Parquet telemetry export.

## Milestone 5: River Solver Upgrade

- [ ] Evaluate a finite-volume shallow-water solver.
- [ ] Evaluate PyClaw/GeoClaw integration versus a custom minimal solver.
- [ ] Use SWASHES analytic cases for validation.
- [ ] Add wet/dry boundary handling.
- [ ] Add hydraulic jump handling.
- [ ] Keep analytic authored features available for controlled raft tests.

## Milestone 6: Compliant Rubber Raft Upgrade

- [ ] Add XPBD-style tube and floor constraints.
- [ ] Add raft modes: rigid, rigid plus compliant shell, and full compliant raft.
- [ ] Add pressure/volume constraint for inflatable tubes.
- [ ] Add rubber stiffness and damping parameter files.
- [ ] Compare rigid and compliant behavior in identical scenarios.
- [ ] Add deformation telemetry.

## Milestone 7: Acceleration And Parameter Fitting

- [ ] Vectorize hot loops with NumPy.
- [ ] Evaluate Numba, JAX, and Taichi for acceleration.
- [ ] Keep a pure Python/NumPy reference implementation for correctness.
- [ ] Add coefficient fitting against reference trajectories.
- [x] Evaluate PyChrono as a reference/backend, not as the first implementation.
- [x] Select Project Chrono as the external backend for long-term boat/water simulation.

## Milestone 8: Unreal And VR Readiness

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
- [ ] Add a standing-wave example command.
- [ ] Implement rigid raft state and fixed-step integration.
- [ ] Implement still-water buoyancy.
- [ ] Implement one downstream current field.
- [ ] Implement one standing wave field.
- [ ] Add telemetry and Matplotlib trajectory output.
