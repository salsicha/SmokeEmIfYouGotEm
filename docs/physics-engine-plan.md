# Physics Engine Plan

## Goal

Build a headless 2.5D physics and modeling system for a photo-realistic white water rafting simulator before full Unreal production begins.

The active plan is no longer 2D-first. The 2D prototype path is retired. The project now starts from a 2.5D shallow-water / height-field modeling program with two solvers:

- GeoClaw reference model offline through the Python/Clawpack research harness.
- Custom C++ reduced shallow-water / height-field solver for runtime use.

Both solvers must run the same solver-neutral scenario packages, starting with procedural fixtures and expanding into real-world geospatial river sections. The next scenario-package revision should model pool-and-drop rivers as variable cascading reach sequences: pools, tongues, drops, boulder gardens, wave trains, eddies, and recovery zones with different slopes and hydraulic controls. The C++ solver is tuned and accepted by matching GeoClaw reference outputs.

## Core Decision

Do not start with full 3D Navier-Stokes CFD, and do not build the game around the old 2D prototype.

Use a staged 2.5D approach:

1. Generate deterministic 2.5D river scenarios with bed elevation, water depth, surface elevation, velocity, boundaries, features, rocks, and raft parameters.
2. Run those scenarios through GeoClaw as the physically credible geophysical-flow reference.
3. Run the exact same scenarios through a custom C++ reduced shallow-water / height-field solver.
4. Compare water fields, probe traces, feature metrics, raft force samples, and eventual raft outcomes.
5. Tune the C++ model until it matches GeoClaw within accepted tolerances.
6. Extend scenario generation from procedural fixtures into variable cascading river packages built from geospatial course/elevation data, rapid annotations, seasonal flow research, and difficulty presets.
7. Validate reach-to-reach handoffs, sudden drops, pools, and hydraulic transitions against GeoClaw before treating them as runtime-ready.
8. Use the custom C++ solver as the Unreal runtime candidate.
9. Keep GeoClaw offline for validation, regression fixtures, parameter fitting, and reference telemetry.
10. Use Project Chrono for raft rigid/compliant dynamics, contact, and possible FSI experiments once the water-field reference/runtime split is validated.

See [2.5D Dual-Solver Simulation Plan](2.5d-simulation-plan.md) for the detailed dual-solver workflow.
See [GeoClaw Reference Solver Transition Plan](geoclaw-transition-plan.md) for the PyClaw-to-GeoClaw replacement plan.
See [Custom C++ Engine Full Validation Plan](custom-cpp-engine-validation-plan.md) for the complete acceptance gate before live Unreal water depends on the custom engine.
See [Real-World River Content And Seasonal Flow Plan](real-world-river-content-plan.md) for the geospatial, imagery, gauge, seasonal flow, adaptive parameter, and river-selection pipeline.
See [Chrono And Unreal Integration Plan](chrono-unreal-integration.md) for the full game runtime path.
See [Unreal Engine Full Game Plan](unreal-engine-game-plan.md) for the full game production roadmap after Python modeling, validation, and profiling.

## Retired 2D Path

The repository contains legacy 2D prototype code and artifacts, but they are no longer the architecture target.

Rules going forward:

- Do not extend the 2D river/raft prototype.
- Do not use 2D validation as the gate for Unreal production.
- Do not make the custom C++ solver match the 2D prototype.
- Delete or replace 2D artifacts after the 2.5D scenario schema and solver harness are in place.

The source of truth is now 2.5D GeoClaw reference output plus the custom C++ solver comparison harness. Existing PyClaw outputs remain historical regression artifacts only.

## Research Direction

Useful foundations:

- GeoClaw/Clawpack for depth-averaged geophysical-flow reference modeling, topography/bathymetry source terms, wet/dry handling, Manning friction, and adaptive mesh refinement.
- PyClaw artifacts only as legacy comparison/regression data from earlier milestones.
- Manually encoded SWASHES-style analytic cases for validating shallow-water solvers, with provenance notes and no vendored external data until licensing and maintenance are clear.
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

This state is generated and sampled in the same way for GeoClaw and the custom C++ solver.

## Shared Scenario Package

Every scenario must be solver-neutral:

- Seed and generator version
- Source manifest, scenario type, river id, section id, coordinate reference system, and processing version when generated from real-world data
- Grid bounds and resolution
- Duration and timestep policy
- Bed elevation
- Initial water depth/surface
- Initial momentum/velocity
- Boundary conditions and inflow/outflow definitions
- Rocks, shelves, ledges, constrictions, and hazards
- Authored feature metadata
- Rapid annotations, gauge metadata, season preset, flow percentile/band, difficulty preset, and confidence scores when available
- Raft physical parameters
- Probe points and cross sections
- Expected telemetry channels

For California-style pool-and-drop rivers, the package should also carry a variable cascading river model:

- Ordered reaches with station ranges, local slope profiles, widths, banks, roughness, boulder density, and confidence metadata.
- Explicit drop/rapid transitions with bed-elevation fall, crest, ramp/ledge length, tailwater depth, hydraulic-control type, recirculation risk, aeration/damping proxy, and hazard tags.
- Active pool definitions for storage, depth, eddies, recirculation, and recovery windows.
- Reach IDs and drop IDs on grids, probes, raft checkpoints, audio/VFX hooks, and Unreal corridor metadata.
- Handoff diagnostics for mass flux, momentum flux, energy loss, wet/dry fronts, and raft state continuity.

The same files feed:

- GeoClaw reference run
- Custom C++ solver run
- Solver comparison harness
- Unreal replay/debug tools later

## GeoClaw Reference Model

GeoClaw is the reference solver for 2.5D river-water modeling.

Responsibilities:

- Run canonical shallow-water fixtures.
- Run procedurally generated rafting scenarios.
- Run real-world topography/bathymetry-driven rapid scenarios.
- Produce reference fields and telemetry.
- Validate mass conservation, wave propagation, wet/dry behavior, topographic source terms, hydraulic transitions, and feature behavior.
- Export outputs for comparison and tuning.

GeoClaw is not expected to ship inside Unreal. It is the offline truth model.

## Custom C++ Solver

The custom C++ solver is the runtime candidate.

Responsibilities:

- Load the same scenario package as GeoClaw.
- Step a reduced shallow-water / height-field model deterministically.
- Provide water fields to raft, debug, and eventually Unreal visualization.
- Export the same telemetry as GeoClaw.
- Run inside target performance budgets.

The C++ solver may use a simpler numerical model than GeoClaw, but the outputs must match GeoClaw well enough for raft-relevant behavior.

Authored feature forcing is allowed in the C++ runtime only as a bounded, manifest-recorded, GeoClaw-compared tuning layer. It may expose holes, boils, laterals, eddy lines, wave trains, shallow shelves, boulder push/damping, pins/releases, and flips for gameplay and visualization, but the default gains remain low until the full GeoClaw/C++ geometry and raft-coupling gates pass. Forced features must be flow-dependent, with sticky/washout/low-water behavior tied to discharge or flow band rather than a single static strength.

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
- Apply crew weight distribution from seat occupancy, lean, high-side, brace, paddle timing, and recovery actions.

The same raft-force sampler should run against GeoClaw output and C++ runtime fields whenever possible.

## Comparison And Tuning

Compare GeoClaw and C++ on:

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
- Crew counterplay telemetry for high-side/brace/lean timing, weight distribution, and pin/flip/release outcomes

Acceptance metrics should include L1/L2/Linf field errors, probe errors, feature-location error, mass drift, runtime cost, and scenario outcome agreement.

## Chrono And Unreal Path

Project Chrono remains the planned raft/contact/compliance runtime, but the water solver plan is now:

- GeoClaw is offline reference.
- Custom C++ reduced shallow-water / height-field solver is the runtime water candidate.
- Chrono integrates raft/contact/paddle dynamics against that custom water field.
- Chrono::FSI remains an optional experiment/reference path, not the baseline runtime dependency.

Unreal production begins only after:

- GeoClaw reference scenarios run.
- Custom C++ scenarios run.
- Solver comparison and tuning reports pass.
- Raft-force coupling matches on representative scenarios.
- At least one real-world river scenario package runs through both solvers with low, median, and high runnable seasonal flow presets.
- Adaptive fluid parameters for season/flow/difficulty are documented and validated against GeoClaw reference output.
- Profiling proves the C++ path can meet target budgets.

## Implementation Phases

### Phase 1: Scenario Schema

- Define the solver-neutral 2.5D scenario package.
- Generate fixture scenarios and procedural rafting scenarios.
- Add probe/cross-section definitions.
- Add schema validation tests.

### Phase 2: GeoClaw Reference

- Add optional GeoClaw integration.
- Run canonical shallow-water fixtures.
- Export fields, probes, and telemetry.
- Add manually encoded analytic/SWASHES-style validation where practical.

### Phase 3: Custom C++ Solver

- Add standalone C++ water solver library/executable.
- Load shared scenarios.
- Implement reduced shallow-water / height-field stepping.
- Export matching telemetry.
- Add C++ tests.

### Phase 4: Solver Comparison

- Run both solvers on identical scenarios.
- Compare field and probe metrics.
- Tune C++ coefficients against GeoClaw.
- Promote passing cases to regression fixtures.

### Phase 5: Raft Coupling

- Add 6-DoF raft state and sample patches.
- Couple raft forces to GeoClaw outputs and C++ fields.
- Compare force envelopes, trajectories, and outcome classifications.

### Phase 6: Profiling And Runtime Readiness

- Profile GeoClaw reference costs for research workflows.
- Profile C++ runtime costs for Unreal budgets.
- Produce readiness report before Unreal production starts.

### Phase 7: Real-World Scenario Readiness

- Convert one selected river section into a solver-neutral scenario package from geospatial terrain/course data, reviewed rapid annotations, and flow research.
- Run low, median, and high runnable season/difficulty presets in GeoClaw and the custom C++ solver.
- Tune adaptive fluid parameters and raft coupling against GeoClaw outputs.
- Export source manifests, validation telemetry, and an Unreal-ready corridor package before full Unreal production starts.

### Phase 8: Variable Cascading River Readiness

- Replace the current monolithic real-world package with ordered reach/drop sequences for pool-and-drop rivers.
- Generate South Fork American baseline packages with variable slopes, pools, ledges, boulder gardens, eddies, and recovery zones.
- Use reach-local grids with overlap/ghost zones for authoring and streaming, and require stitched whole-window validation outputs with reach/drop IDs.
- Run GeoClaw and C++ on the same cascading package at low, median, and high runnable flows.
- Validate per-reach behavior and stitched whole-section behavior before exposing live custom water to Unreal gameplay.
