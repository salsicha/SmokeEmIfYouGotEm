# Physics Engine Plan

## Goal

Build a headless Python physics engine that can model a rubber white water raft moving over highly dynamic river surfaces before any 3D graphics work begins.

The engine should answer one question first: can we produce stable, inspectable, physically plausible raft motion from river features such as rocks, standing waves, eddy lines, vertical upwellings, local viscosity changes, and paddle forces?

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

Use Project Chrono as the selected external physics backend for long-term boat/water simulation, but keep the first implementation layered and inspectable:

1. A dynamic river field over a 2D domain.
2. A 6-DoF raft body sampled at many hull contact points.
3. Force laws that convert local water state into buoyancy, drag, lift, shear, collision, and paddle impulses.
4. Telemetry and validation tests for every force contribution.
5. Optional compliant raft structure once the rigid-body force model is stable.
6. Chrono-backed multibody/contact/FSI integration once the reduced raft/water model is validated.

This gives us a controllable research platform in Python while preserving a migration path to Unreal later.

See [Backend Evaluation](../physics/docs/backend-evaluation.md) for the comparison between Project Chrono, MuJoCo, PyBullet, Bullet, Box2D, Taichi, and JAX.

## Simulation State

### River Field

Represent the river as fields over `(x, y, t)`:

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

The first version can use analytic fields and authored features. A later version can replace or augment those fields with a finite-volume shallow-water solver.

### Raft Body

Start with a single 6-DoF rigid body:

- Position
- Orientation quaternion
- Linear velocity
- Angular velocity
- Mass
- Inertia tensor
- Center of gravity
- Sampled hull/contact points

The sampled hull points are more important than the initial visual shape. They are where water and rocks apply force.

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

All forces should be computed per hull sample, then accumulated into net force and torque on the raft.

### Gravity And Buoyancy

For each hull sample:

- Compare sample height against local water surface.
- Estimate submerged depth or submerged volume contribution.
- Apply hydrostatic lift along the local surface normal.
- Add restoring moments from center-of-buoyancy shifts.

This is the baseline that lets the raft float, pitch, roll, and recover.

### Wave Potential Barriers

Standing waves and wave trains should not be treated as cosmetic height bumps. They are energy barriers.

For each wave feature:

- Surface slope changes the local normal force.
- Upstream face applies deceleration and upward force.
- Crest crossing requires sufficient kinetic energy.
- Downstream face can accelerate, drop, or destabilize the raft.
- Breaking-wave features can add stochastic impact impulses.

The first implementation can model this using analytic heightfields and velocity fields. The validation target is qualitative at first: insufficient speed stalls or surfs, correct speed climbs over, bad angle spins or flips.

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

### Upwellings And Hypoviscous Surface Regions

Treat updrafts/upwellings as localized vertical water velocity and pressure fields. Treat "hypoviscous" regions as authored or simulated regions where effective damping decreases and the raft loses some stabilizing resistance.

For each affected hull sample:

- Add vertical impulse or sustained vertical lift from `w`.
- Reduce local damping by `mu_eff`.
- Reduce contact stability when the raft is riding aerated or highly turbulent water.
- Increase roll/pitch sensitivity if only part of the raft is in the region.

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
- Implement analytic river fields: flat current, standing wave, eddy line, vertical upwelling, viscosity patch.
- Implement a rigid raft with sampled hull points.
- Implement buoyancy, drag, shear, upwelling, and rock contact forces.
- Save telemetry as CSV or Parquet.
- Plot runs with Matplotlib.

### Phase 2: Validation Harness

- Add unit tests for conservation and stability invariants.
- Add regression tests for canonical scenarios:
  - Flat water drift
  - Still-water float equilibrium
  - Standing wave climb/stall
  - Eddy-line yaw
  - Rock bump and deflection
  - Pinning against a rock
  - Upwelling roll/pitch disturbance
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
    river.py
    raft.py
    forces.py
    contacts.py
    integrators.py
    telemetry.py
  tests/
    test_float_equilibrium.py
    test_flat_current.py
    test_standing_wave.py
    test_eddy_line.py
    test_rock_contact.py
  examples/
    run_flat_current.py
    run_standing_wave.py
    run_eddy_line.py
```

## Validation Standards

The engine should not accept "looks right" as sufficient.

Minimum validation requirements:

- Deterministic replay with fixed seed and timestep
- Bounded energy behavior in passive water
- Stable float equilibrium in still water
- No unbounded spin or velocity growth without explicit energy input
- Contact solver does not tunnel through rocks under target timestep/substep settings
- Telemetry separates each force contribution
- Parameter files are versioned with run outputs
- Every new river feature gets a canonical regression scenario

## First Deliverable

The first code deliverable should be a non-graphical Python package that runs this command:

```bash
python -m raftsim.examples.run_standing_wave
```

It should output:

- A trajectory plot
- A telemetry file
- A pass/fail summary for whether the raft cleared, stalled, surfed, flipped, or pinned

That deliverable is enough to start evaluating whether the simulation foundation is viable before graphics, VR, or Unreal integration.
