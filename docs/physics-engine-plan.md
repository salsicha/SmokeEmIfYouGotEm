# Physics Engine Plan

## Goal

Build a headless 2.5D physics and modeling system for a photo-realistic white water rafting simulator before full Unreal production begins.

The active plan is no longer 2D-first. The 2D prototype path is retired. The project now starts from a 2.5D shallow-water / height-field modeling program with two solvers:

- PyClaw reference model in Python.
- Custom C++ reduced shallow-water / height-field solver for runtime use.

Both solvers must run the same procedurally generated scenarios. The C++ solver is tuned and accepted by matching PyClaw reference outputs.

## Core Decision

Do not start with full 3D Navier-Stokes CFD, and do not build the game around the old 2D prototype.

Use a staged 2.5D approach:

1. Generate deterministic 2.5D river scenarios with bed elevation, water depth, surface elevation, velocity, boundaries, features, rocks, and raft parameters.
2. Run those scenarios through PyClaw as the physically credible Python reference.
3. Run the exact same scenarios through a custom C++ reduced shallow-water / height-field solver.
4. Compare water fields, probe traces, feature metrics, raft force samples, and eventual raft outcomes.
5. Tune the C++ model until it matches PyClaw within accepted tolerances.
6. Use the custom C++ solver as the Unreal runtime candidate.
7. Keep PyClaw offline for validation, regression fixtures, parameter fitting, and reference telemetry.
8. Use Project Chrono for raft rigid/compliant dynamics, contact, and possible FSI experiments once the water-field reference/runtime split is validated.

See [2.5D Dual-Solver Simulation Plan](2.5d-simulation-plan.md) for the detailed PyClaw/C++ solver workflow.
See [Chrono And Unreal Integration Plan](chrono-unreal-integration.md) for the full game runtime path.
See [Unreal Engine Full Game Plan](unreal-engine-game-plan.md) for the full game production roadmap after Python modeling, validation, and profiling.

## Retired 2D Path

The repository contains legacy 2D prototype code and artifacts, but they are no longer the architecture target.

Rules going forward:

- Do not extend the 2D river/raft prototype.
- Do not use 2D validation as the gate for Unreal production.
- Do not make the custom C++ solver match the 2D prototype.
- Delete or replace 2D artifacts after the 2.5D scenario schema and solver harness are in place.

The source of truth is now 2.5D PyClaw reference output plus the custom C++ solver comparison harness.

## Research Direction

Useful foundations:

- PyClaw/Clawpack for Python-facing finite-volume shallow-water reference modeling.
- GeoClaw concepts for depth-averaged geophysical flows, wet/dry handling, bathymetry, and hydraulic behavior.
- SWASHES-style analytic cases for validating shallow-water solvers.
- Fossen-style marine craft dynamics for raft rigid-body state, hydrodynamic forces, and added-mass approximations.
- Project Chrono for C++ raft dynamics, contact, compliant raft experiments, and potential FSI evaluation.
- JAX/Taichi/Numba only as later acceleration or fitting tools if they help the Python research loop.

## 2.5D Water State

The shared water model should expose:

- `bed(x, y)`: riverbed elevation
- `eta(x, y, t)`: water surface elevation
- `h(x, y, t)`: water depth
- `u, v`: depth-averaged horizontal velocity
- `hu, hv`: momentum
- `wet`: wet/dry state
- `normal`: surface normal derived from `eta`
- `slope`: surface gradient
- `roughness`: friction/roughness parameters
- `feature_tags`: rocks, ledges, holes, laterals, boils, wave trains, shallows, strainers

This state is generated and sampled in the same way for PyClaw and the custom C++ solver.

## Shared Scenario Package

Every scenario must be solver-neutral:

- Seed and generator version
- Grid bounds and resolution
- Duration and timestep policy
- Bed elevation
- Initial water depth/surface
- Initial momentum/velocity
- Boundary conditions and inflow/outflow definitions
- Rocks, shelves, ledges, constrictions, and hazards
- Authored feature metadata
- Raft physical parameters
- Probe points and cross sections
- Expected telemetry channels

The same files feed:

- PyClaw reference run
- Custom C++ solver run
- Solver comparison harness
- Unreal replay/debug tools later

## PyClaw Reference Model

PyClaw is the reference solver for 2.5D modeling.

Responsibilities:

- Run canonical shallow-water fixtures.
- Run procedurally generated rafting scenarios.
- Produce reference fields and telemetry.
- Validate mass conservation, wave propagation, wet/dry behavior, hydraulic transitions, and feature behavior.
- Export outputs for comparison and tuning.

PyClaw is not expected to ship inside Unreal. It is the offline truth model.

## Custom C++ Solver

The custom C++ solver is the runtime candidate.

Responsibilities:

- Load the same scenario package as PyClaw.
- Step a reduced shallow-water / height-field model deterministically.
- Provide water fields to raft, debug, and eventually Unreal visualization.
- Export the same telemetry as PyClaw.
- Run inside target performance budgets.

The C++ solver may use a simpler numerical model than PyClaw, but the outputs must match PyClaw well enough for raft-relevant behavior.

## Raft Coupling

The raft samples either solver through one interface:

- Surface height and normal
- Depth and wet/dry state
- Velocity and momentum
- Bed height
- Feature tags
- Roughness/damping

For each raft sample point:

- Compute submerged depth.
- Apply buoyancy along the surface normal.
- Apply vertical damping.
- Apply horizontal drag from depth-averaged velocity.
- Apply added-mass approximation where useful.
- Resolve bed, rock, ledge, and shallow grounding contact.
- Apply paddle blade forces based on depth and relative water velocity.

The same raft-force sampler should run against PyClaw output and C++ runtime fields whenever possible.

## Comparison And Tuning

Compare PyClaw and C++ on:

- `h`, `eta`, `u`, `v`, `hu`, `hv`
- Wet/dry masks
- Surface normals and slopes
- Probe time series
- Cross sections
- Mass conservation
- Hydraulic jump location
- Wave crest/trough location
- Hole retention geometry
- Lateral/boil feature metrics
- Raft force envelopes
- Raft trajectory and outcome classification

Acceptance metrics should include L1/L2/Linf field errors, probe errors, feature-location error, mass drift, runtime cost, and scenario outcome agreement.

## Chrono And Unreal Path

Project Chrono remains the planned raft/contact/compliance runtime, but the water solver plan is now:

- PyClaw is offline reference.
- Custom C++ reduced shallow-water / height-field solver is the runtime water candidate.
- Chrono integrates raft/contact/paddle dynamics against that custom water field.
- Chrono::FSI remains an optional experiment/reference path, not the baseline runtime dependency.

Unreal production begins only after:

- PyClaw reference scenarios run.
- Custom C++ scenarios run.
- Solver comparison and tuning reports pass.
- Raft-force coupling matches on representative scenarios.
- Profiling proves the C++ path can meet target budgets.

## Implementation Phases

### Phase 1: Scenario Schema

- Define the solver-neutral 2.5D scenario package.
- Generate fixture scenarios and procedural rafting scenarios.
- Add probe/cross-section definitions.
- Add schema validation tests.

### Phase 2: PyClaw Reference

- Add optional PyClaw integration.
- Run canonical shallow-water fixtures.
- Export fields, probes, and telemetry.
- Add analytic/SWASHES-style validation where practical.

### Phase 3: Custom C++ Solver

- Add standalone C++ water solver library/executable.
- Load shared scenarios.
- Implement reduced shallow-water / height-field stepping.
- Export matching telemetry.
- Add C++ tests.

### Phase 4: Solver Comparison

- Run both solvers on identical scenarios.
- Compare field and probe metrics.
- Tune C++ coefficients against PyClaw.
- Promote passing cases to regression fixtures.

### Phase 5: Raft Coupling

- Add 6-DoF raft state and sample patches.
- Couple raft forces to PyClaw outputs and C++ fields.
- Compare force envelopes, trajectories, and outcome classifications.

### Phase 6: Profiling And Runtime Readiness

- Profile PyClaw reference costs for research workflows.
- Profile C++ runtime costs for Unreal budgets.
- Produce readiness report before Unreal production starts.
