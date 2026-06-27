# Chrono Water And Raft Coupling Plan

## Goal

The boat should be driven by a custom shallow-water / height-field river model and by Project Chrono rigid-body/contact dynamics. The runtime must support rubber-raft buoyancy, paddle and current forces, partially elastic rock impacts, strongly inelastic riverbed grounding, deterministic replay, VR-friendly fixed steps, and telemetry that can still be validated against the Python/PyClaw harness.

## Best Integration Strategy

Use an operator-split coupling loop:

1. The custom C++ shallow-water solver owns the water state: `h`, `eta`, `u`, `v`, momentum, wet/dry state, surface normal, bed height, feature tags, and adaptive flow parameters.
2. Project Chrono owns the raft body state: pose, linear/angular velocity, inertia, collision/contact impulses, and constraints.
3. A narrow native coupling bridge samples the water field at raft patches and paddle blades, converts those samples into Chrono forces/torques, steps Chrono, and emits telemetry.
4. Unreal consumes interpolated Chrono poses for rendering, VR camera motion, passengers, audio, VFX, and debug overlays.
5. Full Chrono::FSI remains optional research/reference work. It should not replace the custom water runtime until it proves accuracy, platform availability, and VR performance.

This is the best first production path because it keeps the water solver deterministic, tunable against PyClaw, and cheap enough for large waterways, while using Chrono where it is strongest: multibody dynamics, contact, collision response, and compliant/rigid body integration.

## Fixed-Step Schedule

Run the whole physics bridge from one authoritative fixed-step scheduler.

Target starting point:

- Water solver step: `1/60 s` or scenario `fixed_dt`.
- Chrono raft/contact substeps: `1/120 s` or smaller during contact-heavy frames.
- Unreal render: variable framerate with interpolation from the latest two committed Chrono states.
- Replay/telemetry: exact fixed-step physics frames, not render frames.

Per water tick:

1. Gather deterministic input intents: guide commands, paddle strokes, controller poses, crew actions, and scripted AI actions.
2. Advance or sample the shallow-water field for the current tick.
3. Build a read-only water-query snapshot for Chrono substeps.
4. For each Chrono substep:
   - Sample raft tube/floor patches against the water snapshot.
   - Apply buoyancy, drag, added-mass approximation, current shear, slope, paddle, and feature forces.
   - Let Chrono resolve rock and bed contacts.
   - Accumulate contact and force telemetry.
5. Commit raft pose/velocity, contact state, and per-force telemetry.
6. Optionally feed low-frequency raft displacement/source terms back into the next water step after the one-way bridge is stable.

## Water-To-Chrono Force Model

The bridge should apply forces at deterministic raft sample patches, not as a single center-of-mass force.

Required water samples per patch:

- Surface height and normal.
- Bed height.
- Depth and wet/dry state.
- Horizontal water velocity and local velocity gradient.
- Roughness/friction scalar.
- Feature tags: rock, ledge, shallow, strainer, hole, lateral, eddy line, boil, wave train.

Required force channels:

- Hydrostatic buoyancy from submerged patch volume/depth, using local surface normal.
- Vertical damping against bobbing and slamming.
- Horizontal drag from patch velocity relative to local water velocity.
- Added-mass approximation scaled by local depth and patch area.
- Surface-slope force to keep the raft responding to steep standing waves and hydraulic transitions.
- Eddy-line and shear torque from cross-raft velocity gradients.
- Boil/upwelling vertical impulse where feature metadata or water gradients indicate upward flow.
- Paddle blade forces from blade pose, blade submergence, blade velocity, and local water velocity.

## Collision And Contact Model

Chrono should own collision resolution. The water solver should not directly teleport or clamp the raft. The custom bridge only supplies sampled water/bed/feature data and contact material parameters.

### Rocks: Partially Elastic Rubber-Raft Impacts

Rocks should be static or kinematic Chrono collision geometry generated from the river corridor package. The raft should collide using simplified tube and floor collision primitives that approximate the inflated hull.

Rock contacts should use:

- Nonzero restitution for partially elastic bounce.
- Contact stiffness representing rubber tube compression.
- Contact damping to prevent jitter and account for air-filled raft energy loss.
- Tangential friction for scraping and glancing blows.
- Contact telemetry that records impulse, normal, penetration, relative speed, raft patch id, rock id, and outcome tags such as bounce, scrape, pin, or launch.

Initial tuning target:

- Higher restitution than bed contacts.
- Moderate normal damping.
- Friction high enough for scrapes and pins, but not so high that every glancing blow sticks.

### Riverbed: Strongly Inelastic Grounding

The riverbed is not a bounce surface. Bed contacts should model grounding, scraping, and dragging across shallow shelves.

Bed contacts should use:

- Near-zero restitution.
- Higher damping than rock contacts.
- Grounding friction and optional stick-slip behavior.
- Soft contact/compliance to avoid numerical chatter on coarse height-field terrain.
- Contact state hysteresis so a raft that is barely touching the bed does not flicker between grounded and floating every substep.

The bed can start as a sampled height-field contact channel from `WaterFieldSample.bed_height`, then move to generated Chrono collision terrain once Unreal corridor meshes are available.

## One-Way First, Two-Way Later

The first runtime should be one-way coupled:

- Water field drives raft forces.
- Chrono raft state does not disturb the water solver.

This gets the gameplay and validation loop working quickly and deterministically. After that is stable, add a limited two-way coupling path:

- Estimate raft displaced volume and footprint from submerged patches.
- Inject a smoothed, bounded momentum/depth source into the next water step.
- Keep the source term optional and tuned against PyClaw/custom validation fixtures.
- Never let raft feedback destabilize the water solver or break replay determinism.

## Kinematics Contract

Chrono is authoritative for boat kinematics.

The bridge should expose:

- Raft transform, linear velocity, angular velocity, and accelerations.
- Per-seat attachment transforms for crew and first-person guide camera.
- Point velocities for tube, floor, and paddle samples.
- Contact impulses and contact state.
- Smoothed render/interpolation transforms for Unreal.
- Raw fixed-step transforms for replay and validation.

Unreal should not independently simulate raft kinematics. It should render interpolated Chrono state and send deterministic input intents back to the physics bridge.

## Data Contracts

Add versioned schemas for:

- `WaterQuerySnapshot`: water grid/frame id, timestep, coordinate transform, source scenario id, and solver config.
- `ChronoRaftBodyConfig`: mass, inertia, collision primitives, material presets, sample patch layout, and seat/camera anchors.
- `ContactMaterialPreset`: rock elastic, bed inelastic, shallow shelf, strainer, and bank variants.
- `PhysicsTickInput`: paddle commands, guide commands, controller poses, AI crew intents, and difficulty/assist modifiers.
- `PhysicsTickOutput`: raft state, water sample summary, force breakdown, contact events, replay keyframe, and debug vectors.

## Validation Plan

Before relying on the bridge inside Unreal:

1. Add native C++ fixtures for flat pool float, current drift, standing wave lift, eddy-line yaw, rock bounce, riverbed grounding, shallow shelf pivot, and pin/release.
2. Compare force envelopes and one-step trajectories against the Python raft coupling harness.
3. Record restitution and damping sweeps for rock and bed contacts.
4. Verify replay determinism from identical inputs and scenario packages.
5. Profile worst-case rapid scenes with many sample patches and simultaneous contacts.
6. Only then connect the bridge to Unreal telemetry playback and live rendering.

## Implementation Order

1. Expand `raftsim_water/chrono_coupling.hpp` from per-patch force sampling into a full bridge API with water snapshots, raft body config, and tick input/output structs.
2. Add contact material presets for rock, bed, shallow shelf, bank, ledge, and strainer.
3. Build a standalone native Chrono raft harness that creates the raft body, rock bodies, and sampled bed contact from scenario packages.
4. Apply water forces as external forces/torques at raft patches before each Chrono substep.
5. Configure Chrono rock contacts with partial restitution and rubber damping.
6. Configure bed contacts as inelastic grounding with high damping and friction.
7. Export telemetry matching the Python/Unreal replay schema.
8. Add regression fixtures and parameter sweeps for rock restitution, bed damping, grounding friction, raft tube stiffness, and substep count.
9. Integrate the proven bridge into the Unreal plugin after telemetry playback works.

## Acceptance Criteria

- A raft floats stably in flat water without contact jitter.
- A raft accelerates and yaws plausibly in current and eddy-line fixtures.
- Rock impacts bounce or deflect the raft with bounded, tunable restitution.
- Riverbed contacts ground and scrape the raft with near-zero bounce.
- Contact and hydrodynamic force telemetry are available per patch/contact.
- Identical fixed-step inputs reproduce the same raft trajectory within tolerance.
- The bridge fits desktop and VR runtime budgets before visual effects are layered on top.
