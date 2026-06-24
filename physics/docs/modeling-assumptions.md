# Modeling Assumptions And Accuracy Targets

## Reference Threads

The first engine is based on these modeling directions:

- Project Chrono is the selected external physics backend for long-term raft/fluid-solid interaction work.
- Depth-averaged shallow water methods for river-surface dynamics.
- 6-DoF marine craft dynamics for raft position, orientation, velocity, and angular velocity.
- Stateless fluid-force approximations for early buoyancy, drag, lift, and added-mass terms.
- XPBD-style compliant constraints for later inflatable tube and floor deformation.
- Python-first orchestration with optional acceleration after correctness and telemetry are established.

See the repository-level [Physics Engine Plan](../../docs/physics-engine-plan.md) for the full research summary.
See [Backend Evaluation](backend-evaluation.md) for the external backend comparison and selection.

## Initial Validation Assumptions

- The first engine is headless and deterministic.
- Fixed timesteps are required for reproducible regression scenarios.
- Full 3D CFD is explicitly out of scope for the first implementation.
- The first raft model may be rigid, but the API must not block later compliant raft modes.
- Every force contribution must be recorded separately before tuning coefficients.
- Analytic river features are acceptable before a finite-volume river solver exists.
- "Looks plausible" is not enough; each feature needs an explicit regression scenario.

## First Physical Accuracy Targets

### Raft

- Stable float equilibrium in still water with bounded oscillation once buoyancy is implemented.
- No unbounded linear or angular energy growth in passive water.
- Orientation updates remain normalized within `1e-9` after fixed-step integration.
- Hull-force telemetry must identify which sampled point generated each contribution.

### Paddle

- Paddle forces must be generated through blade-water interaction, not direct raft steering.
- Paddle impulse telemetry must include blade position, direction, depth, and relative water velocity once that model exists.
- Equal-and-opposite force transfer to the raft/crew system must be testable.

### Current And River Features

- Current fields must be deterministic functions of position and simulation time.
- Eddy-line scenarios must report lateral shear and yaw torque separately.
- Standing-wave scenarios must classify cleared, stalled, surfed, flipped, or pinned outcomes.
- Upwelling and low-damping regions must be explicit field values, not hidden random perturbations.

### Contact And Rocks

- Contact must prevent tunnel-through under the selected timestep/substep settings.
- Collision telemetry must separate normal impulse, friction impulse, and rubber softness/compliance terms.
- Pinning must be detected from sustained obstacle contact plus current force, not from position alone.

## Current Milestone 0 Status

Milestone 0 provides the infrastructure required to start validating those targets. It does not yet implement raft buoyancy, river fields, paddle physics, or rock contact.
