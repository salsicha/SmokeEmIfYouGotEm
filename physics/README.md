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
    backends/
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
- Optional Project Chrono backend integration

## Physics Backend

Project Chrono is the selected external backend for long-term raft and moving-water simulation because it combines multibody dynamics, collision/contact, flexible parts, Python bindings, and fluid-solid interaction support. See [Backend Evaluation](docs/backend-evaluation.md).

The integration is optional and lazy:

```python
from raftsim.backends import select_backend

backend = select_backend()  # prefers Project Chrono, falls back to pure Python
simulation = backend.create_simulation()
```

Request Chrono explicitly when the native dependency is required:

```python
from raftsim.backends import create_backend

chrono = create_backend("chrono")
simulation = chrono.create_simulation()  # raises if PyChrono is not installed
```

Install PyChrono from the Project Chrono distribution when using the Chrono backend. The pure Python backend remains available without native dependencies.

## Next Milestone

Milestone 1 should add the minimal rigid raft sandbox: 6-DoF raft state, sampled hull points, still-water buoyancy, current fields, drag/damping, paddle impulses, and baseline scenarios.
