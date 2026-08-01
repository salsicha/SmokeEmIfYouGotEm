# RaftSim (SmokeEmIfYouGotEm)

An open-source, photorealistic whitewater rafting simulator built with Unreal Engine 5.8 and a first-party shallow-water physics stack. You are the river guide: read the rapid, set the angle, call the strokes, keep your crew in the boat.

**Status (July 2026): pre-release, in active development.** Six rivers are
runnable in-engine. The 1.0 production campaign remains the **South Fork
American, Chili Bar to Salmon Falls**, with all 20 named rapids at three real
flow levels. The Zambezi now adds a source-scale Boiling Pot-to-Mukuni Beach
reference run with all 25 mapped rapids; its missing bathymetry and
rapid-specific hydraulics are explicitly procedural and remain blocked from
production-fidelity claims. Its current map, regeneration path, validation, and
open gates are documented in
[docs/zambezi-reference-map-and-scenario.md](docs/zambezi-reference-map-and-scenario.md).
See [docs/game-completion-plan.md](docs/game-completion-plan.md) for the active
milestone plan and [CHANGELOG.md](CHANGELOG.md) for progress.

## What's in this repository

| Area | Contents |
|---|---|
| `physics/` | The `raftsim` Python package: deterministic simulation kernel, 2.5D scenario system, GeoClaw/PyClaw reference solvers, dual-solver validation harness, flexible-raft reference physics, and real-world river corridor pipeline. Plus the C++ finite-volume shallow-water runtime solver (`physics/cpp`). |
| `unreal/` | The UE 5.8 project: RaftSim plugin (runtime modules + a large procedural environment-authoring editor toolkit), project content, and packaging scripts. |
| `docs/` | Design docs, production plans, source/rights policies, and hash-locked review evidence. |

## Building

**Physics package** (Python ≥ 3.11, [uv](https://docs.astral.sh/uv/)):
```bash
cd physics
uv run pytest -q          # run the test suite
```

**C++ water solver** (CMake + a C++17 compiler):
```bash
cd physics/cpp && cmake -B build && cmake --build build
```

**Unreal project**: open `unreal/SmokeEmIfYouGotEm.uproject` with Unreal Engine 5.8 (the editor build compiles the RaftSim plugin). Packaging scripts live in `unreal/Scripts/`.

## Data honesty

This project keeps an explicit, hash-locked audit trail. Reference-solution playback and visual conditioning are always labeled as such and are compiled out of shipping builds; diagnostic captures are never presented as gameplay screenshots. Simulated river behavior is approximate and must never be used for real-world trip planning or safety decisions.

## Licenses

- Code: [MIT](LICENSE)
- First-party content: [CC BY 4.0](LICENSE-CONTENT.md)
- Third-party assets/data: per-item intake manifests; summarized in [CREDITS.md](CREDITS.md). See also [NOTICE.md](NOTICE.md).

Contributions are welcome as issues and pull requests. This is primarily a solo project; expect review latency.
