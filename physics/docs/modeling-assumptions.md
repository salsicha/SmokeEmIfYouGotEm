# Modeling Assumptions And Accuracy Targets

## Reference Threads

The first engine is based on these modeling directions:

- Project Chrono is the selected external physics backend for long-term raft/fluid-solid interaction work and full Unreal runtime physics.
- PyClaw is the offline Python reference for depth-averaged shallow-water modeling.
- A custom C++ reduced shallow-water / height-field solver is the runtime water candidate.
- 6-DoF marine craft dynamics for raft position, orientation, velocity, and angular velocity.
- Stateless fluid-force approximations for early buoyancy, drag, lift, and added-mass terms.
- XPBD-style compliant constraints for later inflatable tube and floor deformation.
- Python-first orchestration with optional acceleration after correctness and telemetry are established.

See the repository-level [Physics Engine Plan](../../docs/physics-engine-plan.md) for the full research summary.
See the repository-level [Chrono And Unreal Integration Plan](../../docs/chrono-unreal-integration.md) for the full game runtime path.
See [Backend Evaluation](backend-evaluation.md) for the external backend comparison and selection.

## Initial Validation Assumptions

- The first engine is headless and deterministic.
- Fixed timesteps are required for reproducible regression scenarios.
- Full 3D CFD is explicitly out of scope for the first implementation.
- The active first raft model is 6-DoF over 2.5D water fields.
- The legacy top-down 2D prototype is not an active validation target.
- Every force contribution must be recorded separately before tuning coefficients.
- PyClaw and the custom C++ solver must consume the same generated scenario package.
- The custom C++ solver is accepted by matching PyClaw reference outputs, not by matching the legacy 2D prototype.
- "Looks plausible" is not enough; each feature needs an explicit regression scenario.

## First Physical Accuracy Targets

### Raft

- Stable 6-DoF float behavior in flat water with bounded draft, pitch, and roll.
- No unbounded linear or angular energy growth in passive 2.5D water fields.
- Yaw and later quaternion orientation updates remain normalized/stable within `1e-9` after fixed-step integration.
- Hull-force telemetry must identify which sampled point generated each contribution.

### Paddle

- Paddle forces must be generated through blade-water interaction, not direct raft steering.
- Paddle impulse telemetry must include blade position, direction, depth, and relative water velocity once that model exists.
- Equal-and-opposite force transfer to the raft/crew system must be testable.

### Current And River Features

- Procedural 2.5D scenarios must be deterministic for a fixed seed and parameter set.
- PyClaw and C++ must load equivalent bed, water, boundary, feature, and probe definitions.
- Water fields must be deterministic functions of scenario state and simulation time.
- Eddy-line scenarios must report lateral shear and yaw torque separately.
- Standing-wave scenarios must classify cleared, stalled, surfed, flipped, or pinned outcomes.
- Boil/upwelling proxy and low-damping regions must be explicit field values, not hidden random perturbations.
- C++ field/probe errors must be compared against PyClaw reference outputs.

### Contact And Rocks

- Contact must prevent tunnel-through under the selected timestep/substep settings.
- Collision telemetry must separate normal impulse, friction impulse, and rubber softness/compliance terms.
- Pinning must be detected from sustained obstacle contact plus current force, not from position alone.

## Current Status

Milestone 0 provides reusable infrastructure. The legacy 2D prototype exists, but new validation work starts with the 2.5D PyClaw/C++ dual-solver plan.
