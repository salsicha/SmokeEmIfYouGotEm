# Runnable River Simulation & Playability Plan

Written July 18, 2026; updated August 1, 2026. Goal: **all six runnable
rivers playable in-engine with live finite-volume solver water and the full
gameplay stack** (crew, flip/swim/recover, scoring, HUD, reactive audio). The
first five use a validated signature-rapid pattern. Zambezi is restored at an
explicit reference tier: the full source-scale corridor is playable, while
procedural bathymetry and rapid cues remain barred from production-fidelity
claims.

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

The runnable portfolio now contains the original five signature-rapid maps and
the full-corridor Zambezi reference run:

| River | Corridor dir | Signature rapid | Map | Status |
|---|---|---|---|---|
| South Fork American | `south_fork_american_chili_bar` | **Troublemaker** (+ Meat Grinder) | `L_Troublemaker` | **DONE, playable** |
| Colorado Grand Canyon | `colorado_river_grand_canyon_rowing` | **Hance** | `L_Hance` | to build |
| Pacuare | `pacuare_river_costa_rica` | **Upper Huacas** | `L_UpperHuacas` | to build |
| Futaleufú | `futaleufu_river_chile` | **Terminator** | `L_Terminator` | to build |
| Chilko | `chilko_river_lava_canyon` | **Lava Canyon** | `L_LavaCanyon` | to build |
| Zambezi | `zambezi_batoka_gorge` | **Rapids 1–25 reference run** | `L_ZambeziBatokaGorge_PhysicalCorridorCandidate` | **reference runnable; production hydraulics gated** |

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
The original five `L_<River>` maps load their live wet finite cooked-field
signature-rapid windows. The Zambezi corridor loads a source-aligned,
procedurally infilled full-run seed. Every map spawns a raft with crew, scoring,
HUD, and audio, is reachable from the menu, and is covered by a runtime load
test. Zambezi remains a reference Free Run until its rapid-specific hydraulic
and external acceptance gates pass.

## Execution log

### 2026-07-18 — All five rivers playable (W2 done)
- Data-driven `RaftSim.CreateRiverMaps` generates `L_Troublemaker`, `L_Hance`, `L_UpperHuacas`, `L_Terminator`, `L_LavaCanyon`; the main menu lists all five; `RaftSim.P4.RiverMapLoads` (parameterized) passes for every map. River-water config is placed only when a river's cooked fields exist, so a river cooks into real solver water automatically once its package lands (Troublemaker already on cooked water; the other four on clean dev-tank water meanwhile — both playable). Fixed the dev-tank fallback to recover from a faulted river-load. Pushed `71f51a63`.
- W1 physics agents (Colorado Hance, Pacuare Upper Huacas, Futaleufú Terminator, Chilko Lava Canyon) cooking in parallel; each river's map is regenerated onto its cooked fields as the package lands.

### 2026-07-18/19 — ALL FIVE RIVERS ON LIVE SOLVER WATER (definition of done met)
- Physics agents landed all four remaining signature-rapid windows + cooked fields, each honestly labeled (interpreted bed geometry; convergence/gaps recorded; not production-promoted): Colorado **Hance** (`2626d679`), Pacuare **Upper Huacas** (`f7faa740`/`ce4e2400`), Chilko **Lava Canyon** (`d29e4b71`), Futaleufú **Terminator** (`79d72a37`). manning_n recorded per band throughout.
- All five maps regenerated onto their cooked windows (`cooked_fields=1`); `RaftSim.P4.RiverMapLoads` passes for all five — **L_Troublemaker, L_Hance, L_UpperHuacas, L_Terminator, L_LavaCanyon all load a live wet finite cooked-field river window and the raft rests on it.** Loader falls back to the manifest's middle (reference) band so each river's band naming resolves.
- Every river is playable with the full gameplay stack (crew, flip/swim/recover, scoring, HUD, reactive audio) on genuine finite-volume solver water. Simulation-and-gameplay playability for the five-river portfolio is complete. (Photoreal environment art remains the separate owner-gated track.)

### 2026-07-31 — Zambezi restored as the sixth runnable river
- The generated Boiling Pot-to-Mukuni Beach source-scale map now carries the
  vertical-slice game mode, player raft/start, 25 mapped rapid markers, and a
  curved-coordinate live-water configuration.
- A deterministic 30 km procedural solver seed fills missing bathymetry and
  rapid cues. It is reference gameplay only: Rapid 9 remains a mandatory
  portage and guide, geospatial, rights, seasonal-flow, rapid-hydraulic,
  photoreal, desktop, and VR gates remain open.

### 2026-08-01 — Zambezi safe launch and live crew acceptance

- Rapid 1's procedural control moved to station 160 m, leaving a 55 m
  subcritical launch apron after the station-75 raft spawn. The generator
  fail-closes above Froude 0.94; the current maximum is 0.4041.
- The rigid-body support mass now includes the dry raft, guide, and four
  passengers. The generated map places that 605 kg loaded body at hydrostatic
  equilibrium instead of dropping it from above the surface.
- The saved-map audit passes schema v10 with the safe-launch tag. The focused
  PIE gate proves the raft is upright before and after `AllForward`, with five
  attached crew and zero swimmers. The full parameterized map-load regression
  passes all six rivers with zero failures.
- The close runtime capture passes runnable/crew-cohesion review but fails
  photoreal review: the water is overbright and low-detail, the terrain remains
  rounded and tessellated-looking, and biome/ground-cover fidelity is still
  provisional.
