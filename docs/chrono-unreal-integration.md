# Chrono And Unreal Integration Plan

## Decision

Project Chrono should be the authoritative physics runtime for the full simulator, not only a Python research backend.

Unreal Engine should own rendering, VR input, audio, UI, asset streaming, and platform packaging. Chrono should own raft dynamics, rock/contact response, compliant raft structure, paddle-water force transfer, and fluid-solid interaction where available.

The Python `raftsim` package remains the research harness and validation layer. It should prototype reduced models, generate regression scenarios, tune coefficients, and prove behavior before that behavior is moved into the Chrono-backed game runtime.

See [Unreal Engine Full Game Plan](unreal-engine-game-plan.md) for the production roadmap. The production Unreal project should begin only after Python modeling, validation, profiling, telemetry schema stabilization, and a standalone native Chrono smoke test are complete.

## Runtime Ownership

### Chrono Owns

- Raft body state
- Rigid and compliant raft dynamics
- Rock collision and contact response
- Pinning and obstacle force state
- Paddle blade force application
- Water/raft force exchange
- Chrono::FSI or equivalent water-coupling experiments
- Physics telemetry and force breakdowns

### Unreal Owns

- VR and flat-screen camera
- Motion-controller input
- Visual raft meshes, water rendering, spray, foam, wetness, and lighting
- Audio and spatial cues
- UI, scoring, replay presentation, menus, and save data
- Level authoring tools and cooked content
- Platform packaging

### Shared Boundary

The boundary between Unreal and Chrono should be a narrow C++ integration layer:

- Unreal sends player input, paddle/controller pose, level collision geometry, and authored water-field data.
- Chrono advances the authoritative physics state on a fixed timestep.
- Unreal receives raft transforms, passenger attachment transforms, contact events, force telemetry, and debug vectors.

Unreal should not run an independent authoritative raft simulation. Chaos may still be used for incidental world physics, visual debris, or non-authoritative effects.

## Timestep Strategy

Chrono should run on a fixed physics timestep independent of render framerate.

Initial target:

- Chrono fixed step: `1/120 s` for VR-sensitive raft/contact response
- Unreal render: variable
- Unreal animation/audio: consume interpolated Chrono state
- Debug/replay output: store exact fixed-step Chrono frames

If Chrono::FSI becomes too expensive at the target timestep, the first fallback should be a reduced water-force model in Chrono, not a switch back to Unreal Chaos for raft authority.

## Data Flow

1. Unreal gathers input and controller poses.
2. Unreal converts level-authored river features into Chrono-ready field/query data.
3. The Chrono bridge advances zero or more fixed physics substeps.
4. Chrono records per-force telemetry.
5. Unreal interpolates or extrapolates the latest Chrono state for render.
6. Unreal displays debug vectors, contact events, current fields, and replay telemetry when requested.

## Build And Packaging Risks

Key risks:

- Building Chrono consistently for Windows, macOS, Linux, and future console targets.
- Verifying which Chrono modules are available in each platform build.
- Keeping Chrono::FSI performant enough for VR.
- Designing a clean Unreal plugin boundary that does not leak engine types into core physics code.
- Matching Python validation behavior to C++ Chrono runtime behavior.

Mitigations:

- Start with desktop-only Chrono C++ integration before console or standalone VR targets.
- Keep Python tests as behavior-level validation, not byte-for-byte runtime equivalence.
- Add a small C++ Chrono smoke test before any Unreal plugin work.
- Keep water/raft model parameters in versioned data files shared by Python and Unreal.
- Preserve a reduced force-field mode for platforms where full FSI is too expensive.

## Implementation Phases

### Phase 1: Python Validation

- Keep using `raftsim` for reduced models and scenario tests.
- Validate flat current, buoyancy, standing waves, eddy-line yaw, upwellings, and rock contact.
- Export telemetry and parameter files.
- Profile the 2D/2.5D models and identify the runtime budget for each force component.
- Freeze the first shared parameter and telemetry schemas before native runtime work.

### Phase 2: Native Chrono Prototype

Start after the Python modeling/profiling exit gate.

- Add a minimal standalone C++ Chrono executable outside Unreal.
- Create a rigid raft body and simple rock contact.
- Step Chrono at fixed timestep.
- Export the same telemetry categories as Python.

### Phase 3: Unreal Plugin Skeleton

Start after the native Chrono smoke test succeeds.

- Add an Unreal plugin or module that links Chrono.
- Run a headless Chrono world from Unreal.
- Push one raft transform into an Unreal actor.
- Add fixed-step scheduling and render interpolation.

### Phase 4: Water And Contact Integration

- Map authored river features into Chrono/reduced water-force queries.
- Add rock collision geometry.
- Add paddle/controller pose input.
- Add force/debug vector rendering in Unreal.

### Phase 5: FSI Evaluation

- Evaluate Chrono::FSI for representative wave, eddy, and rock scenes.
- Compare full FSI, reduced Chrono water forces, and Python reference outputs.
- Select per-platform runtime modes based on accuracy and performance.

## Acceptance Criteria

The Chrono/Unreal integration is viable when:

- Unreal can render a raft whose authoritative pose comes from Chrono.
- The same scenario can be run in Python validation and Chrono runtime with comparable qualitative outcomes.
- Contact, paddle, and water-force telemetry are available in both runtimes.
- Fixed-step replay can reproduce a run deterministically enough for debugging.
- VR comfort remains acceptable with Chrono-driven raft motion.
