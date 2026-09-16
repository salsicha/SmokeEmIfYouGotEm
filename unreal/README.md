# SmokeEmIfYouGotEm Unreal Project

UE 5.8 game project. Source, intentional binary assets, manifests and authoring
inputs are versioned; binaries use Git LFS. Build products and local captures
are not versioned. This is an unfinished simulator, not a production-fidelity
certification; older milestone manifests remain historical records.

## Open In Unreal

1. Install Unreal Engine 5.8.
2. Open `SmokeEmIfYouGotEm.uproject`.
3. Fetch the repository's Git LFS assets with `git lfs pull`.
4. Build the native physics library and editor target (below).
5. Use the startup menu in `L_RaftSimBoot` to choose a river or training.

From the repository root on Windows, with Visual Studio C++ Build Tools:

```powershell
& ./unreal/Scripts/build_solver_lib.ps1
& 'C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat' SmokeEmIfYouGotEmEditor Win64 Development "$PWD/unreal/SmokeEmIfYouGotEm.uproject" -WaitMutex -NoHotReloadFromIDE
```

On supported non-Windows hosts, the native archive builder is
`unreal/Scripts/build_solver_lib.sh`; platform packaging scripts are alongside
it. See the [root build instructions](../README.md) for the standalone solver
and Python tests.

## Scene ownership

The [scene catalog](Config/scene_catalog.json) records startup, training,
six playable rivers, development reviews and retired content. Shipping scenes
must match `Config/DefaultGame.ini` and the frontend launch catalog.

South Fork launches `L_SouthForkAmerican_FullReach`. Troublemaker is a rapid
within that scenario and must not appear as its own menu entry. The retained
`L_SouthFork_Troublemaker` cooked reconstruction component is not a selectable
scenario; the obsolete straight-channel `L_Troublemaker` prototype is retired.
The two `Maps/Review/SouthForkSurvey*` scenes are active reconstruction work,
explicitly excluded from shipping; they depend on locally generated survey
fields and are not replacement gameplay scenes.

The saved FullReach scene's exact route and hydraulic dependency closure is
versioned under `physics/data/runtime_bundles/south_fork_saved_scene_v1` and
staged beside the game executable. Fetch its LFS payloads before building.
Experimental local previews still depend on ignored local inputs and are not
release delivery. See the [remaining-work index](../docs/plans/remaining-work.md)
for current integration, visual, physical and 30 FPS acceptance status.

`bootstrap_river_maps.py` and `bootstrap_one_river_map.py` create compact
prototype maps and can overwrite their targets. Do not use them to refresh
materials or reconstruct the full South Fork/Zambezi routes. Single-map
bootstrapping requires an explicit supported river filter.

## Source Policy

- Keep generated build products out of git.
- Keep editor-created binary assets intentional and reviewed.
- Prefer JSON manifests and C++ declarations for early pipeline work until workflows are proven.
- Store large binary assets through Git LFS when they become necessary.
- Keep `Config/scene_catalog.json`, frontend launch paths and the cook list in
  agreement; `physics/tests/test_project_layout.py` checks this contract.
- Read-only asset reference audit: run `Scripts/audit_project_assets.py` with
  Unreal's `-ExecutePythonScript` option. Results go to `../tmp/project-cleanup`.
- Never remove captured source data or historical evidence merely because it
  is not in a shipping map. See [maintenance policy](../docs/maintenance/project-normalization.md).
