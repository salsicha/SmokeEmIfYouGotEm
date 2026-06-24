# raftsim Physics Package

`raftsim` is the headless Python simulation foundation for the white water rafting simulator.

The current slice includes the Milestone 0 foundation plus a runnable top-down 2D river/raft simulator: deterministic river generation, rocks, eddies, standing waves, holes, laterals, boils, hypoviscous patches, shallows, strainers, bank/rock contact, paddle forces, telemetry, plots, and a pure Python or optional PyChrono planar integrator.

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
    examples/
    math2d.py
    math3d.py
    plotting.py
    raft2d.py
    river2d.py
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
- Pure Python 2D vector helpers
- Pure Python 3D vector and quaternion helpers
- Matplotlib plotting helpers with lazy imports
- Optional Project Chrono backend integration
- Procedural 2D river generation
- Top-down 2D raft simulation with pure Python and optional PyChrono planar integration
- River/rapid examples that write JSON, telemetry CSV, and plots

## Physics Backend

Project Chrono is the selected external backend for long-term raft and moving-water simulation, including the full Unreal Engine runtime, because it combines multibody dynamics, collision/contact, flexible parts, Python bindings, and fluid-solid interaction support. See [Backend Evaluation](docs/backend-evaluation.md).

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

Install PyChrono from the Project Chrono distribution when using the Python Chrono backend. The pure Python backend remains available without native dependencies. The full Unreal game should use native C++ Chrono integration rather than PyChrono.

## 2D Examples

Run from this directory after installing the package in editable mode, or with `PYTHONPATH=src` during local development:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.generate_river_2d --seed 1
PYTHONPATH=src python -m raftsim.examples.run_2d_rapid --seed 1 --backend auto
```

Outputs are written under `outputs/river2d` and `outputs/rapid2d` by default.

## Next Milestone

The next milestone should start the [2.5D Raft Simulation Plan](../docs/2.5d-simulation-plan.md): bed elevation, water surface height, depth, surface normals, 6-DoF rigid raft state, buoyancy, gravity, pitch/roll, wave climb, hole surf/flush behavior, grounding, and paddle blade depth. It should also keep strengthening scenario-level validation for the existing 2D simulator.
