# Chrono And Unreal Integration Plan

## Decision

Project Chrono remains a high-fidelity physics research/reference backend for the simulator, but the shipping raft/contact authority is now selected through the Chaos/Jolt runtime evaluation.

Unreal Engine should own rendering, VR input, audio, UI, asset streaming, and platform packaging. The selected raft/contact runtime should own raft dynamics, rock/contact response, paddle-water force transfer, and scoring-critical crew/swimmer contact state. Chrono remains available for compliant raft structure and fluid-solid interaction experiments where useful.

The Python `raftsim` package remains the research harness and validation layer. GeoClaw should produce the 2.5D shallow-water/geophysical-flow reference outputs, and the custom C++ reduced shallow-water / height-field solver should be tuned against those outputs before Unreal runtime work depends on live water.

See [Real-World River Content And Seasonal Flow Plan](real-world-river-content-plan.md) for the geospatial and seasonal-flow pipeline that feeds validated river scenarios.
See [Unreal Engine Full Game Plan](unreal-engine-game-plan.md) for the production roadmap. The production Unreal project should begin only after GeoClaw reference modeling, custom C++ solver matching, real-world river scenario validation, profiling, telemetry schema stabilization, and a standalone native Chrono smoke test are complete.

The first native ownership split is frozen in [Native Runtime Boundary](chrono-runtime-boundary.md): custom C++ owns the reduced water solver and stable water query API, while raft/contact authority is selected after Chaos/Jolt fixtures pass. See [Chaos And Jolt Runtime Evaluation](chaos-jolt-runtime-evaluation.md).

[Chrono Water And Raft Coupling Plan](chrono-water-raft-coupling-plan.md) defines the detailed fixed-step bridge between the shallow-water solver, Chrono raft kinematics, elastic rock impacts, inelastic bed contacts, and Unreal render interpolation.

[Chrono::FSI Policy](chrono-fsi-policy.md) keeps full Chrono fluid-solid interaction as an optional experiment/reference path, not a baseline runtime dependency.

## Runtime Ownership

### Selected Raft/Contact Runtime Owns

- Raft body state
- Rigid raft dynamics
- Rock collision and contact response
- Pinning and obstacle force state
- Paddle blade force application
- Water/raft force exchange
- Coupling to the custom C++ water field
- Physics telemetry and force breakdowns

### Chrono Reference Path Owns

- Compliant raft experiments
- Chrono::FSI or equivalent water-coupling experiments
- High-fidelity contact comparisons when the shipping runtime needs a reference case

### Unreal Owns

- VR and flat-screen camera
- Motion-controller input
- Visual raft meshes, water rendering, spray, foam, wetness, and lighting
- Audio and spatial cues
- UI, scoring, replay presentation, menus, and save data
- Level authoring tools and cooked content
- Platform packaging

### Shared Boundary

The boundary between Unreal and the selected raft/contact runtime should be a narrow C++ integration layer:

- Unreal sends player input, paddle/controller pose, level collision geometry, selected river/season/flow/difficulty data, and authored water-field data.
- The custom C++ water solver advances or samples the runtime water field.
- Chaos, Jolt, Chrono, or the custom reduced runtime advances the candidate physics state on a fixed timestep.
- Unreal receives raft transforms, passenger attachment transforms, contact events, force telemetry, and debug vectors.

Unreal should not run an independent authoritative raft simulation outside the selected bridge. Chaos may still be used for incidental world physics, visual debris, visual ragdolls, or non-authoritative effects while Jolt is evaluated as a portable gameplay-physics island.

## Timestep Strategy

The selected raft/contact runtime should run on a fixed physics timestep independent of render framerate.

Initial target:

- Candidate raft/contact fixed step: `1/120 s` for VR-sensitive raft/contact response
- Unreal render: variable
- Unreal animation/audio: consume interpolated Chrono state
- Debug/replay output: store exact fixed-step candidate-runtime frames

If Chrono::FSI becomes too expensive at the target timestep, keep it as a reference path. Do not switch raft authority to Chaos or Jolt without passing the shared evaluation fixtures.

## Data Flow

1. Unreal gathers input and controller poses.
2. Unreal converts validated river scenario data into candidate-runtime-ready field/query data: geospatial corridor transform, river features, season/flow/difficulty preset, solver fields, rocks, banks, bed contacts, and adaptive raft/water parameters.
3. The selected runtime bridge advances zero or more fixed physics substeps.
4. The selected runtime records per-force telemetry.
5. Unreal interpolates or extrapolates the latest Chrono state for render.
6. Unreal displays debug vectors, contact events, current fields, and replay telemetry when requested.

## Build And Packaging Risks

Key risks:

- Building any external native runtime consistently for Windows, macOS, Linux, and future console targets.
- Verifying which Jolt/Chrono modules are available in each platform build.
- Keeping Chrono::FSI performant enough for reference runs when used.
- Designing a clean Unreal plugin boundary that does not leak engine types into core physics code.
- Matching Python validation behavior to Chaos/Jolt/Chrono runtime behavior.

Mitigations:

- Start with desktop-only Chaos automation and Jolt C++ smoke tests before console or standalone VR targets.
- Keep Python tests as behavior-level validation, not byte-for-byte runtime equivalence.
- Add a small Jolt smoke test and Chaos automation fixture suite before choosing raft/contact authority.
- Keep water/raft model parameters in versioned data files shared by Python and Unreal.
- Keep GeoClaw reference scenarios available for C++ water-solver regression.
- Keep river source manifests, flow presets, and difficulty-to-fluid parameter mappings versioned with the scenario packages that every candidate runtime consumes.
- Preserve a reduced force-field mode for platforms where full external runtime integration is too expensive.

## Implementation Phases

### Phase 1: Python Validation

- Keep using `raftsim` for scenario generation, GeoClaw reference runs, and comparison tests.
- Validate GeoClaw and custom C++ against the same flat current, buoyancy, standing wave, eddy-line, upwelling, and rock-contact scenarios.
- Validate one real-world river section across low, median, and high runnable season/difficulty presets before Unreal relies on those parameters.
- Export telemetry and parameter files.
- Profile the GeoClaw reference and custom C++ solver and identify the runtime budget for each force component.
- Freeze the first shared parameter and telemetry schemas before native runtime work.

### Phase 2: Chaos/Jolt Runtime Evaluation

Start after the Python modeling/profiling exit gate.

- Build the six Chaos automation fixtures from `chaos_jolt_runtime_evaluation.json`.
- Add a minimal native Jolt smoke harness or Unreal plugin path that consumes the same fixture definitions.
- Create a rigid raft body, simple rock contacts, shallow shelf contacts, pin/release pocket, and crew/swimmer transition in both targets.
- Use the shared water query API as the dependency-free bridge from custom C++ water frames to candidate-runtime buoyancy/contact force samples.
- Step both targets at fixed timestep.
- Export the same telemetry categories as Python and the custom reduced runtime.
- Compare Chaos and Jolt summaries for contact quality, determinism, replayability, runtime cost, and gameplay outcome stability.

### Phase 2B: Native Chrono Reference Prototype

Run when high-fidelity comparison is needed.

- Add a minimal standalone C++ Chrono executable outside Unreal.
- Build `physics/cpp` with the optional `raftsim_chrono_smoke` target when `find_package(Chrono)` succeeds; skip it cleanly when Chrono is unavailable.
- Use Chrono to compare selected raft/contact/compliance cases against the shipping runtime candidate.
- Keep Chrono::FSI behind explicit experiment flags.

### Phase 3: Unreal Plugin Skeleton

Start after the Chaos/Jolt fixture loop has enough evidence to choose the first raft/contact authority candidate.

- Add an Unreal plugin or module for the selected candidate if it is not pure Chaos.
- Run a headless candidate-runtime world from Unreal.
- Push one raft transform into an Unreal actor.
- Add fixed-step scheduling and render interpolation.

### Phase 4: Water And Contact Integration

- Map authored river features into the custom C++ reduced shallow-water / height-field solver.
- Couple the selected raft/contact runtime to the custom C++ water-field queries.
- Add rock collision geometry with partially elastic rubber-raft contact presets.
- Add riverbed grounding as strongly inelastic, high-damping contact.
- Add paddle/controller pose input.
- Add force/debug vector rendering in Unreal.

### Phase 5: FSI Evaluation

- Evaluate Chrono::FSI for representative wave, eddy, and rock scenes.
- Compare full FSI, reduced Chrono water forces, and Python reference outputs.
- Select per-platform runtime modes based on accuracy and performance.

## Acceptance Criteria

The selected runtime integration is viable when:

- Unreal can render a raft whose authoritative pose comes from the selected candidate runtime.
- The same scenario can be run in Python validation and the selected runtime with comparable qualitative outcomes.
- Contact, paddle, and water-force telemetry are available in both runtimes.
- Fixed-step replay can reproduce a run deterministically enough for debugging.
- VR comfort remains acceptable with candidate-runtime-driven raft motion.
