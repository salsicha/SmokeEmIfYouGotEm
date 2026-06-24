# Physics Engine Plan

## Goal

Build a headless Python physics engine that can model a rubber white water raft moving over highly dynamic river surfaces before any 3D graphics work begins.

The engine should answer one question first: can we produce stable, inspectable, physically plausible 2D raft motion from river features such as rocks, standing waves, eddy lines, boil/upwelling proxies, local viscosity changes, and paddle forces?

## Research Summary

Useful starting points from the research pass:

- [GeoClaw](https://arxiv.org/abs/1008.0455) uses depth-averaged shallow water equations, finite-volume methods, shock capturing, dry-state handling, and adaptive mesh refinement for geophysical flows. This supports a 2.5D river-field approach instead of full 3D CFD for the first engine.
- [PyClaw](https://arxiv.org/abs/1111.6583) shows the practical pattern we want: Python orchestration with compiled numerical kernels for performance-critical wave-propagation solvers.
- [SWASHES](https://arxiv.org/abs/1110.0288) provides analytic shallow-water test cases. This is directly useful for validating any river-field solver before connecting it to raft dynamics.
- [Fossen's marine craft model](https://www.fossen.biz/html/marineCraftModel.html) gives a standard 6-DoF marine dynamics structure with inertia, added mass, hydrodynamic damping, hydrostatics, and external generalized forces.
- [MuJoCo fluid forces](https://mujoco.readthedocs.io/en/stable/computation/fluid.html) is a useful reference for stateless rigid-body fluid force approximations, including quadratic drag, viscous resistance, added mass, Kutta lift, and Magnus lift.
- [XPBD](https://matthias-research.github.io/pages/publications/XPBD.pdf) is the best first candidate for inflatable raft compliance because it provides stable compliant constraints and constraint force estimates with timestep and iteration-count independent stiffness.
- [Project Chrono](https://projectchrono.org/) is worth evaluating later as a reference or backend because it already supports multibody dynamics, flexible parts, collision, Python bindings, and fluid-solid interaction.
- [DiffTaichi](https://arxiv.org/abs/1910.00935) and [JAX MD](https://arxiv.org/abs/1912.04232) support the likely long-term direction: Python-facing simulation code with GPU acceleration and differentiability for parameter fitting.

## Core Decision

Do not start with full 3D Navier-Stokes CFD. It is too slow, too difficult to validate, and unnecessary for the first raft behavior milestone.

Use Project Chrono as the selected external physics backend for long-term boat/water simulation and for the full Unreal game runtime, but start with a 2D simulation that is easy to generate, inspect, and validate:

1. A procedurally generated 2D river field with centerline, banks, current vectors, feature tags, and collision geometry.
2. A top-down 2D raft body with position, yaw, velocity, angular velocity, and sampled hull contact points.
3. Force laws that convert local river state into current push, drag, shear, collision, wave/hole retention, grounding, and paddle impulses.
4. Telemetry and validation tests for every force contribution.
5. 2.5D surface, buoyancy, and vertical effects only after the 2D river/boat interaction is stable.
6. Optional compliant raft structure once the rigid-body force model is stable.
7. Chrono-backed multibody/contact/FSI integration once the reduced raft/water model is validated.
8. Unreal integration through a narrow C++ bridge where Chrono owns authoritative raft physics and Unreal owns rendering, VR input, audio, and platform packaging.

This gives us a controllable research platform in Python while preserving a migration path to Unreal later.

See [Backend Evaluation](../physics/docs/backend-evaluation.md) for the comparison between Project Chrono, MuJoCo, PyBullet, Bullet, Box2D, Taichi, and JAX.
See [Chrono And Unreal Integration Plan](chrono-unreal-integration.md) for the full game runtime path.
See [Procedural 2D River Generation Plan](2d-river-generation-plan.md) for the first river-generation milestone.
See [2.5D Raft Simulation Plan](2.5d-simulation-plan.md) for the next height-field, buoyancy, pitch/roll, and wave/hole simulation step.
See [Unreal Engine Full Game Plan](unreal-engine-game-plan.md) for the full game production roadmap after Python modeling, validation, and profiling.

## Current First Slice

The initial 2D raft simulator is implemented under `physics/src/raftsim`:

- `river2d.py` provides deterministic procedural river sections, bank offsets, proxy depth/gradient/current fields, river features, field sampling, JSON export, and validation summaries.
- `raft2d.py` provides a top-down rigid raft state, sampled hull/contact points, water drag, damping, shear, banks, rocks, wave/hole/lateral/boil/shallow/hypoviscous feature forces, paddle forces, simple outcome classification, and telemetry.
- `raft2d.py` can use a pure Python semi-implicit Euler planar integrator or an optional PyChrono-backed planar integrator when PyChrono is installed.
- `raftsim.examples.generate_river_2d` and `raftsim.examples.run_2d_rapid` write the first JSON, CSV, and PNG debug outputs.

This is an analytic 2D feature-field prototype, not yet a free-surface fluid solver or compliant raft model.

The next planned slice is 2.5D: a height-aware water/bed field sampled by a 6-DoF rigid raft. It should introduce bed elevation, water surface elevation, depth, surface normals, buoyancy, gravity, pitch, roll, vertical damping, wave climb, hole surf/flush behavior, grounding, and paddle blade depth while staying deterministic and testable in Python.

Unreal production should wait until the Python engine has completed the 2D/2.5D validation suite, performance profiling, coefficient tuning, telemetry schema stabilization, and native Chrono smoke testing. Until then, the Python package remains the source of truth for physics behavior.

## Simulation State

### 2D River Field

The first simulation represents the river as top-down fields over `(x, y, t)`:

- Bank membership / navigable water mask
- Centerline distance `s`
- Lateral offset `n`
- Horizontal velocity `u, v`
- Depth proxy
- Effective damping / drag coefficient
- Shear strength
- Vorticity / rotational flow proxy
- Turbulence intensity
- Collision geometry
- Feature tags such as eddy, eddy-line, standing-wave, hole, rock, pillow, shallow, strainer, and calm pool

This phase does not model vertical boat motion. Standing waves, holes, upwellings, and shallow shelves are represented as 2D force fields and outcome classifiers.

### Later 2.5D River Field

After the 2D model works, extend the river into fields over `(x, y, t)`:

- Surface height `eta`
- Bed elevation `bed`
- Water depth `h`
- Horizontal velocity `u, v`
- Vertical upwelling velocity `w`
- Effective damping / viscosity coefficient `mu_eff`
- Vorticity / rotational flow estimate
- Shear tensor or finite-difference velocity gradient
- Turbulence intensity
- Feature tags such as eddy, eddy-line, wave, hole, pour-over, rock, pillow, and calm pool

The first version can use procedural 2D fields and authored validation features. A later version can replace or augment those fields with a finite-volume shallow-water solver.

### 2D Raft Body

Start with a top-down rigid body:

- Position
- Yaw angle
- Linear velocity
- Angular velocity around vertical axis
- Mass
- Moment of inertia
- Sampled hull/contact points

The sampled hull points are more important than the initial visual shape. They are where water and rocks apply force.

The later 2.5D/3D raft will add orientation quaternion, full angular velocity, buoyancy, trim, pitch, roll, and center-of-buoyancy effects.

### Inflatable Structure

After the rigid-body engine works, add a compliant raft model:

- Longitudinal tube nodes
- Cross tube nodes
- Floor membrane nodes
- Distance, bending, area, and pressure/volume constraints
- XPBD compliance values for rubber stiffness and damping
- Coupling constraints from tube deformation back into the raft's effective rigid-body motion

The engine should support running the raft in three modes:

- Rigid raft, for fast development and debugging
- Rigid body plus compliant contact shell, for impact softness
- Full compliant raft, for deformation and tube flex

## Force Model

For the first 2D slice, forces should be computed per hull sample, then accumulated into planar net force and yaw torque on the raft.

The first 2D model includes:

- Current push
- Drag and damping
- Eddy-line shear
- Rock, bank, and shallow-shelf contact
- Standing-wave deceleration and surf/stall classification
- Hole/hydraulic retention
- Lateral wave impulse
- Boil/upwelling proxy disturbance
- Hypoviscous/aerated damping reduction
- Paddle impulses

### Later Gravity And Buoyancy

The 2D model does not simulate vertical motion, pitch, roll, submerged volume, or true buoyancy. Those arrive in the later 2.5D/3D model.

For each hull sample in the later model:

- Compare sample height against local water surface.
- Estimate submerged depth or submerged volume contribution.
- Apply hydrostatic lift along the local surface normal.
- Add restoring moments from center-of-buoyancy shifts.

This is the baseline that lets the raft float, pitch, roll, and recover.

### Wave Potential Barriers

Standing waves and wave trains should not be treated as cosmetic height bumps. They are energy barriers.

For each 2D wave feature:

- The upstream face applies deceleration.
- The crest zone can surf, stall, or destabilize the boat.
- The downstream exit can release, yaw, or flush the boat.
- Bad entry angle increases angular disturbance.
- Wave trains apply repeated speed loss and yaw disturbance.

The first implementation can model this using analytic 2D force zones and outcome classifiers. The validation target is qualitative at first: insufficient speed stalls or surfs, correct speed clears, bad angle spins or pins. Later 2.5D work can replace these proxies with actual surface height and slope forces.

### Hydrodynamic Drag, Lift, And Added Mass

For each hull sample:

- Compute relative velocity between raft material point and local water velocity.
- Apply quadratic drag in high-speed flow.
- Apply linear viscous damping where appropriate.
- Add lift terms from flow across angled hull surfaces.
- Add approximate added-mass resistance when the raft rapidly accelerates water.

The first model can use simple coefficients. The engine must log these coefficients and force components separately so they can be fitted later.

### Eddy Lines And Shearing Forces

Eddy lines are velocity discontinuities or steep velocity gradients, not just visual boundaries.

For each hull sample:

- Sample water velocity and velocity gradient.
- Apply lateral shear based on the difference between upstream and eddy-side flow.
- Apply yaw torque when one side of the raft is in fast current and the other is in slow or reverse current.
- Add turbulence noise near high-gradient boundaries.

This should produce the expected behavior: a raft crossing an eddy line at a bad angle gets grabbed and rotated.

### Boils, Upwelling Proxies, And Hypoviscous Surface Regions

In the 2D model, boils/upwellings are localized radial or rotational disturbance fields. Treat "hypoviscous" regions as authored or simulated regions where effective damping decreases and the raft loses some stabilizing resistance.

For each affected hull sample:

- Add radial, lateral, or rotational disturbance.
- Reduce local damping by `mu_eff`.
- Reduce steering authority when the raft is riding aerated or highly turbulent water.
- Increase yaw sensitivity if only part of the raft is in the region.

This is a modeling layer that needs validation. The engine should keep it explicit rather than hiding it inside generic turbulence.

### Rock Contact And Pinning

Rocks are solid collision objects with local water behavior around them.

The contact solver needs:

- Non-penetration
- Friction
- Restitution
- Contact softness for rubber tubes
- Pinning detection when current force exceeds the raft's ability to clear the obstacle
- Separate collision telemetry for tube impact, floor impact, and passenger risk

Start with simple convex rock shapes, then move to signed distance fields or triangle meshes.

### Paddle And Crew Forces

Paddle strokes are external impulses applied through blade-water interaction, not direct raft steering.

For each paddle:

- Track blade position, angle, depth, and velocity relative to local water.
- Apply drag/lift force to the blade.
- Transfer equal and opposite force to the raft/crew system.
- Model guide strokes separately from passenger strokes.

This design works for both future VR input and non-VR scripted/control tests.

## Numerical Architecture

Use deterministic fixed timesteps.

Initial loop:

1. Advance or sample the river field.
2. Predict raft state.
3. Sample all hull points against water and obstacles.
4. Accumulate water forces.
5. Accumulate paddle and crew forces.
6. Integrate linear and angular velocity.
7. Resolve rock contacts and pinning constraints.
8. Solve optional XPBD raft compliance constraints.
9. Update position and orientation.
10. Record telemetry.

Start with semi-implicit Euler because it is simple and robust for force-driven rigid bodies. Add substepping around collisions, steep waves, and high shear. Evaluate velocity Verlet or implicit methods only after the force model is instrumented.

## Python Implementation Plan

### Phase 1: Minimal Rigid Raft Sandbox

- Use Python 3, NumPy, dataclasses, and pytest.
- Implement vector/quaternion helpers.
- Implement a deterministic `Simulation.step(dt)` API.
- Implement procedural 2D river fields: centerline, banks, flat current, standing wave, eddy line, hole, rock, shallow shelf, and damping patch.
- Implement a 2D rigid raft with sampled hull points.
- Implement current push, drag, shear, wave/hole retention, grounding, paddle, and rock contact forces.
- Save telemetry as CSV or Parquet.
- Plot runs with Matplotlib.

### Phase 2: Validation Harness

- Add unit tests for conservation and stability invariants.
- Add regression tests for canonical scenarios:
  - Flat water drift
  - Calm-water drift
  - Standing wave climb/stall
  - Eddy-line yaw
  - Rock bump and deflection
  - Pinning against a rock
  - Hole surf/flush classification
  - Shallow shelf grounding
  - Low-damping hypoviscous patch
- Add parameter sweep scripts.
- Add simple objective functions for fitting coefficients to reference trajectories.

### Phase 3: River Solver Upgrade

- Implement or integrate a finite-volume shallow-water solver.
- Use SWASHES analytic cases for validation.
- Support wet/dry boundaries, hydraulic jumps, and roughness/friction terms.
- Keep authored analytic features available for controlled tests.

### Phase 4: Compliant Raft Upgrade

- Add XPBD tube and floor constraints.
- Add rubber contact shell around the rigid raft.
- Compare rigid, hybrid, and compliant raft behavior in the same test scenes.
- Fit compliance and damping to reference deformation targets.

### Phase 5: Acceleration And Differentiability

- Keep the public API Pythonic.
- Move hot loops to NumPy vectorization first.
- Evaluate Numba, JAX, and Taichi for kernel acceleration.
- Prefer JAX or Taichi if gradient-based parameter fitting becomes important.
- Keep PyChrono as a reference/backend evaluation path, not the first implementation.

## Repository Shape

Recommended first code structure:

```text
physics/
  pyproject.toml
  src/raftsim/
    __init__.py
    sim.py
    state.py
    river2d.py
    raft2d.py
    forces.py
    contacts.py
    integrators.py
    telemetry.py
  tests/
    test_river2d_generation.py
    test_raft2d_state.py
    test_flat_current_2d.py
    test_standing_wave_2d.py
    test_eddy_line_2d.py
    test_rock_contact_2d.py
  examples/
    generate_river_2d.py
    run_2d_rapid.py
```

## Validation Standards

The engine should not accept "looks right" as sufficient.

Minimum validation requirements:

- Deterministic replay with fixed seed and timestep
- Deterministic river generation for fixed seeds and parameters
- Bounded energy behavior in passive 2D current and damping fields
- Stable calm-water behavior with no uncommanded acceleration
- No unbounded spin or velocity growth without explicit energy input
- Contact solver does not tunnel through rocks under target timestep/substep settings
- Telemetry separates each force contribution
- Parameter files are versioned with run outputs
- Every new river feature gets a canonical regression scenario

## First Deliverable

The first code deliverable should be a non-graphical Python package that runs this command:

```bash
python -m raftsim.examples.generate_river_2d --seed 1
```

It should output:

- A generated 2D river plot
- A sampled flow-vector plot
- A feature list
- A validation summary

The first boat deliverable should run:

```bash
python -m raftsim.examples.run_2d_rapid --seed 1
```

It should output:

- A trajectory plot
- A telemetry file
- A pass/fail summary for whether the raft cleared, stalled, surfed, flipped, or pinned

That deliverable is enough to start evaluating whether the simulation foundation is viable before graphics, VR, or Unreal integration.
