# Physics Backend Evaluation

## Decision

Project Chrono is the selected external backend for long-term raft/contact/compliance experiments and possible full game raft dynamics.

For moving-water modeling, the active plan now uses PyClaw as the offline Python 2.5D shallow-water reference and a custom C++ reduced shallow-water / height-field solver as the Unreal runtime water candidate. The C++ solver must be validated against PyClaw on identical solver-neutral scenario packages, starting with procedural fixtures and expanding to real-world geospatial river sections.

The Python integration is optional. `raftsim` still runs with its pure Python backend when PyChrono is not installed, but `select_backend()` now prefers Chrono and falls back to the pure Python backend. The full game should use a native C++ Chrono integration rather than relying on PyChrono at runtime.

## Why Chrono Wins

The simulator needs:

- 3D rigid-body raft dynamics
- Collision and contact with rocks
- Flexible or compliant raft structure
- Moving water, not only stateless drag
- Fluid-solid interaction between water and raft geometry
- Python access during research
- A path to higher-performance native execution later

Project Chrono is the only investigated option that directly covers the full shape of that problem. Its public documentation describes it as a multiphysics engine with rigid and compliant parts, collision/contact, Python bindings, and fluid-solid interaction. Chrono::FSI specifically provides a generic coupling interface plus SPH-based and potential-flow FSI paths.

## Candidate Notes

### Project Chrono

- Best fit.
- Supports multibody dynamics, compliant/flexible parts, collision, Python bindings, and FSI.
- Chrono::FSI supports SPH-based FSI and time-dependent potential-flow FSI.
- Heavier install path than pure Python libraries, so raftsim integrates it lazily as an optional backend.
- The first integrated adapter only creates and steps a core Chrono system. Raft geometry and Chrono::FSI mapping still need to be implemented and verified against the installed Chrono build.
- For the full Unreal game, Chrono should be linked through a native C++ plugin/module and own authoritative raft physics.

### MuJoCo

- Strong rigid-body/contact engine with useful fluid force approximations.
- Its fluid models are stateless surrounding-medium models, not dynamic moving-water or free-surface solvers.
- Good reference for drag, viscous resistance, lift, and added-mass terms, but not the main backend for white water.

### PyBullet / Bullet

- Strong general-purpose rigid-body, collision, robotics, and VR simulation stack.
- Not selected because moving water and raft/fluid interaction would still need to be custom-built around it.

### Box2D

- Explicitly 2D rigid-body simulation.
- Useful only for toy prototypes or diagrams; not suitable for 3D raft dynamics or white water.

### Taichi

- Excellent Python-facing compute system for physical simulation kernels.
- Not a boat/water physics engine by itself.
- Good future candidate for custom shallow-water, SPH, or differentiable kernels if Chrono is too heavyweight for a specific subsystem.

### JAX / JAX MD

- Excellent for differentiable, vectorized numerical kernels and parameter fitting.
- Not a complete raft/water physics engine.
- Good future candidate for coefficient fitting, optimization, and differentiable reduced-order models.

## Integration Status

Current code integration:

- `raftsim.backends.ProjectChronoBackend`
- `raftsim.backends.ChronoSimulation`
- `raftsim.backends.select_backend`
- `raftsim.backends.backend_statuses`

When PyChrono is installed, the Chrono backend can create a minimal Chrono system and advance it with raftsim's fixed timestep configuration. The next integration step is to map raft bodies, collision geometry, and water/FSI state into Chrono objects.

Full game integration target:

- Unreal owns rendering, VR input, UI, audio, asset streaming, and platform packaging.
- The custom C++ reduced shallow-water / height-field solver owns runtime water fields.
- Chrono or custom C++ owns raft dynamics, compliant structure, rock/contact response, paddle forces, and water/raft force exchange depending on the readiness report.
- PyClaw remains offline reference and validation infrastructure.
- Unreal Chaos may still be used for incidental non-authoritative effects, but not for raft authority.
- See the repository-level [Chrono And Unreal Integration Plan](../../docs/chrono-unreal-integration.md).
