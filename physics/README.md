# raftsim Physics Package

`raftsim` is the headless Python simulation foundation for the white water rafting simulator.

Milestone 0 intentionally does not implement raft hydrodynamics yet. It provides the package skeleton, deterministic fixed-step simulation loop, vector/quaternion math, telemetry recording, plotting utilities, pytest infrastructure, and modeling documentation that Milestone 1 will build on.

## Run Tests

```bash
cd physics
pytest
```

## Package Layout

```text
physics/
  pyproject.toml
  src/raftsim/
    math3d.py
    plotting.py
    sim.py
    state.py
    telemetry.py
  tests/
  docs/
```

## Current Scope

- Deterministic fixed timestep stepping
- Pluggable simulation systems
- Force and torque telemetry per frame
- CSV telemetry export
- Pure Python vector and quaternion helpers
- Matplotlib plotting helpers with lazy imports

## Next Milestone

Milestone 1 should add the minimal rigid raft sandbox: 6-DoF raft state, sampled hull points, still-water buoyancy, current fields, drag/damping, paddle impulses, and baseline scenarios.
