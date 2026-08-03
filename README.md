# RaftSim (SmokeEmIfYouGotEm)

An open-source, photorealistic whitewater rafting simulator built with Unreal Engine 5.8 and a first-party shallow-water physics stack. You are the river guide: read the rapid, set the angle, call the strokes, keep your crew in the boat.

**Status (August 2026): pre-release, in active development.** Six rivers are
runnable in-engine. Zambezi is explicitly one of those six and is selectable
as the **Zambezi: Boiling Pot to Mukuni Beach** reference Free Run. The 1.0
production campaign remains the **South Fork
American, Chili Bar to Salmon Falls**, with all 20 named rapids at three real
flow levels. The versioned `L_Zambezi` map adds a source-scale Boiling
Pot-to-Mukuni Beach reference run with all 25 mapped rapids; its missing
bathymetry and
rapid-specific hydraulics are explicitly procedural and remain blocked from
production-fidelity claims. Its current map, regeneration path, validation, and
open gates are documented in
[docs/zambezi-reference-map-and-scenario.md](docs/zambezi-reference-map-and-scenario.md).
The August 3 post-live-water release-head revalidation confirms that the
frontend selector, source scenario, shipping cook, saved map, and live PIE
launch all resolve to `/Game/RaftSim/Maps/L_Zambezi`. Zambezi remains runnable
river 6, loads with the vertical-slice game mode and live cooked-field water,
and is not an environment-preview-only map. Its gameplay river is now a
solver-owned, wet-cell-clipped transmitting core rather than the former opaque
gray static ribbon; project-owned flow-normal and solver-masked foam textures
have no hydraulic authority. The exact contract hashes, tests, runtime counts,
and still-open production gates are recorded in the
[release-head runnable review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_runnable_release_head_v8_review.json),
with the matched visual evidence in the
[transmitting-water review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_live_transmitting_water_v1_review.json).
The versioned progression manifest also enumerates Zambezi in the six-river
Free Run contract, so catalog tests fail if its scenario or map path is removed.
The South Fork production campaign still resolves to the 49.1 km
`L_SouthForkAmerican_FullReach` gameplay map. Its August 2 organic foothill
terrain pass now shares dry-grass, oak-litter, granitic-soil, and weathered-
granite shading with the fixed Landscape review, while leaving DEM geometry,
collision, navigation, water, and raft physics unchanged. This is a retained
technical improvement, not photoreal acceptance; evidence and remaining gates
are in the [South Fork terrain review](docs/environment-captures/south_fork_full_reach/m9_south_fork_organic_foothill_terrain_v1_review.json).
The August 3 ground-cover pass retains the 220,759 project-owned grass tufts
and adds 442,938 non-colliding CC0 scanned grass forms under the source-density,
slope, bank-distance, and solver/VFX wet-mask contracts. This materially breaks
up the bare fixed-camera banks, but remains generic visual morphology rather
than species-reviewed ecology or photoreal approval. A matched local performance
A/B measures a 0.418 ms p95 candidate delta but leaves the pre-existing full-map
60 FPS, packaged-window, and VR gates open; exact visual/performance evidence and
open gates are in the [scanned ground-cover review](docs/environment-captures/south_fork_full_reach/m9_cc0_scanned_ground_cover_v216_review.json).
Pacuare's `L_UpperHuacas` is again a runnable map: a physical 600 m reach-local
Landscape, the committed Upper Huacas cooked solver field, explicit vertical
datum alignment, player raft/start, and the full vertical-slice game mode now
ship together. It is reference-runnable, not photoreal-approved; the evidence
and remaining gates are recorded in
[the Upper Huacas water/readability review](docs/environment-captures/photoreal_river_previews/landscape_candidates/pacuare_upper_huacas_solver_whitewater_v2_review.json).
Its August 3 gameplay-water pass replaces the uniform opaque live sheet with a
solver-owned, wet-cell-clipped transmitting core and a narrowly covered live
detail skin. The new project-owned flow-normal and solver-masked foam-lace
textures are visual-only and cannot alter hydraulics or raft forces. The
matched result is retained as a technical improvement, while terrain,
rainforest ecology, whitewater VFX, calibration, external review, and
photoreal promotion remain open in the
[Pacuare live-water review](docs/environment-captures/photoreal_river_previews/landscape_candidates/pacuare_live_transmitting_water_v1_review.json).
Colorado's `L_Hance` is likewise restored as a reference-runnable physical
reach: a 600×320 m Landscape preserves the complete 600×78 m interpreted Hance
solver bed, procedurally fills missing outer-canyon terrain, and launches the
live moderate-release cooked field at station 336 m with the player raft and
game mode. That retains 69 m of subcritical approach to the first accepted
interior solver transition near station 405 m; a separate solver-rapid camera
now records the downstream hydraulic view. It is not surveyed Hance geography
or photoreal-approved; its current evidence and open gates are recorded in
[the Hance nonperiodic-canyon and dryland-ecology V3 review](docs/environment-captures/photoreal_river_previews/landscape_candidates/colorado_hance_nonperiodic_canyon_dryland_ecology_v3_review.json).
Futaleufú's `L_Terminator` and Chilko's `L_LavaCanyon` now use a wet-cell-
clipped Single Layer Water core beneath their live solver detail surfaces.
The shared cold-water rollout removes the high-coverage pale overlay while
preserving raft-floor transmission, live rapid geometry, and solver authority.
Its lateral core reaches the complete sampled wet bank only through all-wet
cells, while an independent station mask clips the rectangular moving-window
ends. This is a retained technical candidate, not photoreal approval;
comparison evidence and remaining defects are recorded in
[the cold-water volume-core review](docs/environment-captures/photoreal_river_previews/landscape_candidates/cold_water_live_volume_core_v2_review.json).
See [docs/game-completion-plan.md](docs/game-completion-plan.md) for the active
milestone plan and [CHANGELOG.md](CHANGELOG.md) for progress.

| Runnable river | Player-facing run | Current tier |
|---|---|---|
| South Fork American | Chili Bar to Salmon Falls plus Troublemaker | production campaign |
| Colorado, Grand Canyon | Hance | runnable reference signature-rapid Free Run |
| Pacuare | Upper Huacas | runnable reference signature-rapid Free Run |
| Futaleufú | Terminator | signature-rapid Free Run |
| Chilko | Lava Canyon | signature-rapid Free Run |
| Zambezi, Batoka Gorge | `L_Zambezi`: Boiling Pot to Mukuni Beach, Rapids 1–25 | runnable reference Free Run |

To run Zambezi from the game, choose **Free Run**, then select **Zambezi:
Boiling Pot to Mukuni Beach**. Free Run scenarios are available without a
career-license unlock. In the Unreal Editor, the same runnable map can be
opened directly at `/Game/RaftSim/Maps/L_Zambezi`; the older
`L_ZambeziBatokaGorge_PhysicalCorridorCandidate` preview is not the gameplay
map.

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
