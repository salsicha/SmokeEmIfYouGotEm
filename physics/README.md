# raftsim Physics Package

`raftsim` is the headless Python simulation foundation for the white water rafting simulator.

The repository currently includes a legacy top-down 2D prototype, but the active plan has moved to a 2.5D dual-solver program: PyClaw as the Python shallow-water reference model and a custom C++ reduced shallow-water / height-field solver as the runtime candidate. The same generated or real-world geospatial scenario will be applied to both, and the C++ model will be tuned to match PyClaw.

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
- Pure Python 3D vector and quaternion helpers
- Matplotlib plotting helpers with lazy imports
- Optional Project Chrono backend integration
- Legacy procedural 2D prototype code
- Planned PyClaw 2.5D reference model
- Planned custom C++ reduced shallow-water / height-field runtime solver
- Planned dual-solver comparison and tuning harness
- Planned real-world river scenario packages with source manifests, course/elevation extraction, rapid annotations, seasonal flow presets, and difficulty-adaptive parameters

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

## Legacy 2D Examples

The existing 2D examples are legacy scratch artifacts. They are useful only as historical smoke tests until the 2.5D scenario/solver harness replaces them.

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.generate_river_2d --seed 1
PYTHONPATH=src python -m raftsim.examples.run_2d_rapid --seed 1 --backend auto
```

Outputs are written under `outputs/river2d` and `outputs/rapid2d` by default.

## Next Milestone

The next milestone should start the [2.5D Dual-Solver Simulation Plan](../docs/2.5d-simulation-plan.md): define the shared scenario schema, add a PyClaw reference runner, add the custom C++ solver skeleton, and build the first PyClaw-vs-C++ comparison report. After the procedural fixtures are stable, the plan extends into the [Real-World River Content And Seasonal Flow Plan](../docs/real-world-river-content-plan.md) for geospatial river sections, seasonal flows, and Unreal-ready corridor packages.
