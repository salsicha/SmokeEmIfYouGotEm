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
- Solver-neutral 2.5D scenario package schema
- Deterministic 2.5D fixture generator for flat pool, uniform channel, dam-break, bed step, constriction, and wet/dry shoreline cases
- Deterministic 2.5D procedural rapid generator with bends, width/depth variation, dry banks, flow vectors, and whitewater feature metadata
- PyClaw 2.5D reference model
- Standalone custom C++ reduced shallow-water / height-field runtime solver
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

## 2.5D Scenario Packages

The first 2.5D milestone is a solver-neutral scenario package, not a live water solver yet. Generate a deterministic fixture package with:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.generate_scenario2_5d --mode fixture --fixture uniform_channel --seed 1
```

Available fixtures:

- `flat_pool`
- `uniform_channel`
- `dam_break`
- `bed_step`
- `constriction`
- `wet_dry_shoreline`

Generate a deterministic procedural rafting rapid with:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.generate_scenario2_5d --mode procedural --seed 1 --difficulty 0.6
```

Procedural scenarios include a seeded bending channel, variable width/depth, dry banks, initial flow vectors, and metadata for rocks, ledges, constrictions, holes, laterals, boils, shallows, strainers, and wave trains.

The generator writes one package under `outputs/scenarios2_5d/<scenario_id>/`:

```text
scenario.json
bed.npy
initial_state.npz
features.json
probes.json
validation.txt
bed.png
depth.png
speed.png
```

`scenario.json` is the shared manifest. PyClaw and the custom C++ solver both load this same package.

## PyClaw Reference Harness

PyClaw is an optional research dependency. Install it with:

```bash
cd physics
python -m pip install -e ".[research,plot]"
```

Check whether the local environment can import PyClaw:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.run_pyclaw_reference --check
```

Run one canonical fixture:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.run_pyclaw_reference --fixture flat_pool
```

Run all canonical fixtures plus one procedural rapid:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.run_pyclaw_reference --all-fixtures
```

Run a procedural rapid:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.run_pyclaw_reference --procedural --seed 1 --difficulty 0.6
```

PyClaw outputs are written under `outputs/pyclaw_reference/<scenario_id>/`:

```text
manifest.json
validation.json
frames/frame_0000.npz
probes/*.csv
cross_sections/*.npz
```

Each frame exports `h`, `eta`, `u`, `v`, `hu`, `hv`, `wet`, `normal_x`, `normal_y`, `normal_z`, and `froude`. The first harness uses PyClaw's shallow-water equations with the bed retained for exported `eta` and diagnostics; richer bathymetry source-term handling remains a follow-up once the PyClaw/C++ comparison path is active.

## C++ Reduced Water Solver

Milestone 3 adds a standalone C++17 solver outside Unreal under `physics/cpp/`. It is intentionally small and dependency-light: CMake builds a reusable `raftsim_water` library, a `raftsim_water_solver` command, and a native smoke-test executable. The solver loads the same shared 2.5D scenario package as PyClaw, advances deterministic fixed steps, tracks `h`, `eta`, `u`, `v`, `hu`, `hv`, wet/dry masks, and exports comparison-ready fields, probes, cross sections, and validation telemetry.

Build it with:

```bash
cd physics
cmake -S cpp -B /tmp/raftsim-water-build
cmake --build /tmp/raftsim-water-build
```

Generate a shared scenario package:

```bash
cd physics
PYTHONPATH=src python -m raftsim.examples.generate_scenario2_5d --mode procedural --seed 1 --difficulty 0.6
```

Run the C++ solver on that package:

```bash
cd physics
/tmp/raftsim-water-build/raftsim_water_solver \
  --scenario outputs/scenarios2_5d/procedural_rapid_seed_1 \
  --output outputs/cpp_solver \
  --steps 120 \
  --frame-interval 30
```

C++ outputs are written under `outputs/cpp_solver/<scenario_id>/`:

```text
manifest.json
validation.json
frames/frame_0000.csv
probes/*.csv
cross_sections/*.csv
```

Run the native smoke test directly with:

```bash
/tmp/raftsim-water-build/raftsim_water_tests outputs/scenarios2_5d/procedural_rapid_seed_1
```

The pytest suite also builds the C++ solver against a tiny generated procedural package when CMake and a compiler are available.

## Dual-Solver Runs

Milestone 4 starts with a shared runner that applies one scenario package to both solvers and records the linked outputs:

```bash
cd physics
cmake -S cpp -B /tmp/raftsim-water-build
cmake --build /tmp/raftsim-water-build
PYTHONPATH=src python -m raftsim.examples.run_dual_solver \
  --fixture flat_pool \
  --cpp-solver /tmp/raftsim-water-build/raftsim_water_solver \
  --output-dir outputs/dual_solver/flat_pool
```

The runner writes:

```text
dual_solver_manifest.json
scenario/<scenario_id>/
pyclaw_reference/<scenario_id>/
cpp_solver/<scenario_id>/
```

The manifest records the exact shared `scenario.json`, PyClaw output manifest, C++ output manifest, C++ command, and validation paths. Later Milestone 4 tasks add field, probe, feature, runtime, threshold, tuning, and regression promotion reports on top of this shared run directory.

## Next Milestone

The next milestone should continue the [2.5D Dual-Solver Simulation Plan](../docs/2.5d-simulation-plan.md): build the first PyClaw-vs-C++ comparison report and decide whether the PyClaw path needs GeoClaw-style bathymetry/wet-dry source terms before real-world river packages. After procedural scenario packages are stable under both solvers, the plan extends into the [Real-World River Content And Seasonal Flow Plan](../docs/real-world-river-content-plan.md) for geospatial river sections, seasonal flows, and Unreal-ready corridor packages.
