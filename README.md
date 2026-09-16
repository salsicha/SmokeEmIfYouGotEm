# RaftSim — SmokeEmIfYouGotEm

Whitewater rafting simulator built with Unreal Engine 5.8 and a C++/Python shallow-water physics stack.

## Current state

In development. Six rivers are selectable; photorealism and geographic accuracy are not yet accepted. The saved South Fork full-reach scene now uses the survey-water-constrained route, reconstructed terrain and versioned hydraulic data. The newer landward rock/water candidate and full-hull contact remain under review rather than normal-menu defaults. Convincing breaking/froth and the 30 FPS target are still unfinished. See the [current remaining-work index](docs/plans/remaining-work.md) and [South Fork work plan](docs/plans/south-fork-evidence-reconstruction.md).

## Project layout

| Directory | Purpose |
| --- | --- |
| `unreal/Source`, `unreal/Plugins/RaftSim/Source` | Game and plugin C++ |
| `unreal/Content` | Intentional game assets and source manifests |
| `unreal/SourceArt`, `unreal/Scripts` | Asset sources, authoring, capture and packaging tools |
| `physics/src`, `physics/cpp`, `physics/tests` | Simulation, native solver and tests |
| `physics/data` | Source data, provenance and hydraulic inputs |
| `Scripts` | Repository maintenance and release tooling |
| `docs` | Plans, rights records and historical evidence |
| `tmp`, `unreal/Saved`, build directories | Local generated work; not source-controlled |

The [scene inventory](unreal/Config/scene_catalog.json) is checked against the frontend and packaging configuration. It distinguishes startup, training, six playable rivers, a retained cooked rapid-component map, development review maps, and retired content. Troublemaker is a rapid within South Fork, not a separate scenario or menu entry. A cooked rapid-component map is not an independently selectable river or proof that every reconstruction candidate is integrated.

Selectable rivers: South Fork American, Colorado, Pacuare, Futaleufú, Chilko, and Zambezi (Batoka Gorge).

## Build and test

Python 3.11+ and [uv](https://docs.astral.sh/uv/):

```sh
cd physics
uv run pytest -q
```

C++17, CMake 3.22+, and zlib:

```sh
cmake -S physics/cpp -B physics/cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build physics/cpp/build --config Release
ctest --test-dir physics/cpp/build -C Release --output-on-failure --no-tests=error
```

For Unreal, install UE 5.8, fetch Git LFS assets, build the native solver library, then build/open [SmokeEmIfYouGotEm.uproject](unreal/SmokeEmIfYouGotEm.uproject). See [Unreal setup](unreal/README.md) for commands.

## Maintenance and evidence

- Keep runtime content, development reviews and generated scratch separate.
- Do not delete assets based solely on zero Asset Registry references: scene launches and procedural builders also use text paths.
- Preserve captured sources, licenses and historical review evidence. Historical hashes and screenshots are records of earlier revisions, not current acceptance.
- Do not regenerate maps as part of a material-only refresh.
- See the [cleanup and recovery record](docs/maintenance/project-normalization.md) and [archived development narrative](docs/history/README-before-normalization.md).

## Licenses and limitations

Code: [MIT](LICENSE). First-party content: [CC BY 4.0](LICENSE-CONTENT.md). Third-party data/assets retain their individual terms: [credits](CREDITS.md), [notices](NOTICE.md).

River geometry and behavior include approximations and inferred underwater terrain. This is a game, not a source of navigation or river-safety advice.
