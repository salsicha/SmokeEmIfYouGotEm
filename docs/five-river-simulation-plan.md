# Five-River Simulation & Playability Plan

Written July 18, 2026. Goal: **all five runnable rivers playable in-engine with live finite-volume solver water and the full gameplay stack** (crew, flip/swim/recover, scoring, HUD, reactive audio). This plan replicates the proven Troublemaker pattern across the portfolio. It is decision-complete for autonomous execution; where the source data is thin, the executing agent authors honestly-labeled `interpreted_bed_geometry` and records gaps, per `docs/release-1.0-plan.md` §11.

## The proven pattern (Troublemaker, shipped July 18)

One signature rapid per river, taken end-to-end:

1. **Stationing** — confirm the signature rapid's station on the adopted centerline (South Fork A1 already adopted; other rivers use their committed corridor centerline; adopt anchors autonomously per §11 if unset).
2. **C3 window** — author a ~600 m reach-local scenario package (2 m cells): bed from the committed DEM window covering the station, hydrologically conditioned (slope-bounded to the rapid's class where the raw DEM runs supercritical/drains, as Meat Grinder required), with interpreted in-channel features (holes/waves/rocks) honestly labeled.
3. **Behavioral validation** — run the genuine solver (order 2, HLL, calibrations off) at the flow bands; assert the headline features form; record honest gaps.
4. **Cooked fields** — cook steady-state h/u/v/bed/wet grids into a `raftsim.cooked_flow_fields.v1` package that records `manning_n`, for the UE loader `FRaftSimLiveWaterWindow::CreateFromCookedFields`.
5. **Map** — generate `L_<River>` with `ARaftSimRiverWaterConfig` → the cooked window, a raft at the scout eddy, a player start, the vertical-slice game mode.
6. **Menu + test** — a main-menu entry, and an automation test that the map loads a live wet finite river window and the raft rests on it.
7. **Polish** — flow-band tuning, encounter volumes at the signature features, and an interactive playable check.

The gameplay stack (crew, flip/swim/recover, scoring, HUD, audio) is river-agnostic and already shipped, so once a river has a live-water map it is immediately playable with all systems.

## Portfolio (decisions final)

Zambezi remains backlogged (no adequate terrain/centerline). The five runnable rivers and their **signature rapids** (chosen for iconicity + data availability):

| River | Corridor dir | Signature rapid | Map | Status |
|---|---|---|---|---|
| South Fork American | `south_fork_american_chili_bar` | **Troublemaker** (+ Meat Grinder) | `L_Troublemaker` | **DONE, playable** |
| Colorado Grand Canyon | `colorado_river_grand_canyon_rowing` | **Hance** | `L_Hance` | to build |
| Pacuare | `pacuare_river_costa_rica` | **Upper Huacas** | `L_UpperHuacas` | to build |
| Futaleufú | `futaleufu_river_chile` | **Terminator** | `L_Terminator` | to build |
| Chilko | `chilko_river_lava_canyon` | **Lava Canyon** | `L_LavaCanyon` | to build |

Reference flow band for the initial cook: **each river's median/reference band** (all three bands cooked when the solver converges in bounded time; low/high are polish).

## Workstreams

### W1 — Physics per river (parallel; cmake solver only, disjoint data dirs)
For Colorado/Pacuare/Futaleufú/Chilko, one agent each authors the signature-rapid C3 window + behavioral validation + cooked fields, mirroring `physics/src/raftsim/troublemaker_c3_window.py` and `meat_grinder_c3_window.py` exactly (module + example driver + tests + `scenario_<rapid>/` packages + `cooked_flow_fields/`). South Fork also cooks Meat Grinder fields (its window is done). No `unreal/` edits; no review-form artifacts.

### W2 — Engine generalization (main session; owns UE builds)
- Generalize the map generator: a data-driven `RaftSim.CreateRiverMaps` command reads a table of `{river, rapid, cookedFieldsDir, mapName, spawn}` and generates each `L_<River>` with its river-water config, raft, player start, and game mode — replacing the hardcoded Troublemaker command.
- Main menu: a "Rivers" list with all five entries (Troublemaker relabeled under South Fork), each opening its map; keep Training Eddy.
- Per-river automation test (`RaftSim.P4.<River>RiverLoads`): live wet finite window + raft rests on it. One parameterized test iterating the five maps.
- A river registry data asset (`DA_RaftSimRiverCatalog`) so the menu and tests share one source of truth.

### W3 — Polish per river
- Flow-band selection in the map/config (median default; low/high via the config actor).
- Encounter volumes at each signature rapid's cataloged features (scout eddy start, hazard at the crux hole, finish), so each river scores a real line.
- Per-river raft-feel and water-shading tuning; an interactive playable pass driving each map to confirm the raft runs the rapid, can flip, and scores.

## Execution order

1. Commit + push this plan.
2. Launch W1 agents (4 rivers + South Fork Meat Grinder cook) in parallel.
3. Build W2 engine generalization while W1 cooks; land the parameterized map generator + menu + test against Troublemaker first (regression-safe).
4. As each river's cooked fields land: generate its map, add its menu entry, run its load test, commit + push per river.
5. W3 polish pass across all five; final verification that each river is playable end-to-end.
6. Stop when all five maps load live solver water and pass their playable checks.

## Standing rules (unchanged)
Commit + push per river as it lands. Physics suite green before every push. Honest evidence: interpreted geometry labeled, convergence gaps recorded, no playback presented as solver parity. No review-form/readiness paperwork — code, data, maps, tests. Photoreal environment art (terrain meshes, foliage, rock/water materials) is **out of scope for this plan** — this plan delivers *simulation and gameplay* playability on blockout visuals; photoreal is the separate owner-gated P4 art track.

## Definition of done
All five `L_<River>` maps: load a live wet finite cooked-field river window; spawn the raft on it with crew, scoring, HUD, and audio; are reachable from the main menu; pass their automation load test; and drive end-to-end in an interactive playable check (raft runs the rapid, can flip and be recovered, scores, saves). Physics suite green.
