# Runnable River Simulation & Playability Plan

Written July 18, 2026; updated August 2, 2026. Goal: **all six runnable
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
| Colorado Grand Canyon | `colorado_river_grand_canyon_rowing` | **Hance** | `L_Hance` | **reference runnable on physical reach-local Landscape; photoreal gates open** |
| Pacuare | `pacuare_river_costa_rica` | **Upper Huacas** | `L_UpperHuacas` | **reference runnable on physical reach-local Landscape; photoreal gates open** |
| Futaleufú | `futaleufu_river_chile` | **Terminator** | `L_Terminator` | **reference runnable on physical reach-local Landscape; photoreal gates open** |
| Chilko | `chilko_river_lava_canyon` | **Lava Canyon** | `L_LavaCanyon` | **reference runnable on physical reach-local Landscape; photoreal gates open** |
| Zambezi | `zambezi_batoka_gorge` | **Rapids 1–25 reference run** | `L_Zambezi` | **versioned reference runnable; production hydraulics gated** |

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

### 2026-08-01 — Pacuare Upper Huacas physical runnable map restored

- `L_UpperHuacas` now delegates to the source-Landscape builder instead of the
  old flat signature-rapid shell. The saved map contains a 1009×1009,
  8×8-component Landscape over the physical 600×78 m C3 window, with bounded
  deterministic bank relief outside a protected 17 m channel half-width.
- An identity station/lateral coordinate map applies the recorded 454.283 m
  vertical datum, aligning absolute cooked elevations with the local Unreal
  reach. Static capture water matches the live centerline surface exactly; it
  is hidden in play so solver water alone renders and drives the raft.
- `RaftSim.P4.RiverMapLoads.L_UpperHuacas` passes with a wet finite live window,
  an upright raft, and zero swimmers. Both Pacuare material tests pass and
  MapCheck reports 0 errors/0 warnings. The new captures remove the gross DEM
  facets and rectangular shoreline, but opaque water, generic foliage,
  incomplete whitewater VFX, source fidelity, and external guide/geospatial/
  ecology/art/performance approvals still reject photoreal promotion.

### 2026-08-01 — Colorado Hance organic terrain and native capture water retained

- `L_Hance` remains reference-runnable on its unchanged 600×320 m reach-local
  Landscape and unchanged moderate-release finite-volume gameplay water. Its
  source-conditioned Landscape material now adds four non-harmonic world-space
  color fields for sandy benches, weathered and iron-stained canyon rock, dark
  basement-like rock, talus, and fine mineral breakup without world-position
  offset, collision, bathymetry, solver, or raft-force changes.
- The non-colliding capture ribbon now binds a Colorado-only opaque Default Lit
  parent with two moving native normal layers. The Hance cooked field remains
  sampled once into CPU-authored vertex color; shader-side reuse of the shared
  South Fork field is disabled. Fixed water-band luminance rises from 0.1922 to
  0.2716 in the guide view and from 0.2225 to 0.3312 at river eye.
- The editor build, `RaftSim.M9.FColoradoHanceWater`,
  `RaftSim.M9.FColoradoOrganicHanceTerrain`, and
  `RaftSim.P4.RiverMapLoads.L_Hance` pass. Captures still fail photoreal review
  because polygonal terrain, stepped opaque water, coarse foam, sparse ecology,
  missing surveyed geography, and unconverged hydraulics remain. The guide,
  geospatial, hydraulic, geology/ecology/art, water-VFX, and target-hardware
  acceptance gates remain open.

### 2026-08-01 — Colorado Hance physical runnable map restored

- `L_Hance` now delegates to the source-Landscape builder instead of the old
  flat signature-rapid shell or the unrelated broad Lees Ferry preview. Its
  1009×1009, 8×8-component Landscape covers 600×320 m, preserves the complete
  600×78 m interpreted C3 solver bed exactly, and adds as much as 74.977 m of
  deterministic asymmetric canyon relief only outside that protected strip.
- A 301-point identity station/lateral coordinate map applies the recorded
  950.713 m runtime datum. The saved map launches the moderate-release cooked
  field, player raft/start, and vertical-slice game mode; the non-colliding
  field-derived capture ribbon and foam are serialized hidden in play so live
  finite-volume water remains the gameplay renderer and force authority.
- `RaftSim.P4.RiverMapLoads.L_Hance` passes 1/1 with a wet finite window, an
  upright raft, and zero swimmers; MapCheck reports 0 errors and 0 warnings.
  The lit canyon and hydraulic review view are a useful technical baseline,
  but smooth tessellated-looking walls, sparse generic ecology and ground
  cover, dark opaque water, coarse foam mats, missing Hance survey geography,
  unconverged hydraulics, and external guide/geospatial/ecology/art/performance
  gates keep photoreal and production promotion rejected.

### 2026-08-01 — Chilko Lava Canyon physical runnable map restored

- `L_LavaCanyon` now uses a 1009×1009, 8×8-component Landscape covering a
  reach-local 600×600 m window. Broad terrain is sampled in a Frenet frame from
  the official BC Freshwater Atlas route and NRCan CanElevation MRDEM-30 DTM;
  the complete 600×80 m interpreted C3 solver bed is preserved without change.
  Where the 30 m source cannot resolve local ground form, deterministic
  sub-30 m microrelief is bounded to 1.030 m and explicitly remains visual and
  Landscape-collision infill rather than surveyed geography.
- A 301-point station/lateral coordinate map applies the recorded 1101.713 m
  vertical datum with 0.0 m centerline surface error. The median runnable
  cooked field, player raft/start, and vertical-slice game mode are live in the
  saved map; the authored hydraulic ribbon and foam remain non-colliding,
  capture-only, and hidden during play. Four interpreted C3 contact rocks make
  the existing broach controls and first seeded boulder physically present, but
  remain review-gated rather than surveyed hazard claims.
- `RaftSim.P4.RiverMapLoads.L_LavaCanyon` passes 1/1 with a wet finite live
  window, upright raft, and zero swimmers; MapCheck reports 0 errors and 0
  warnings. The technical runnable baseline is accepted, but dark opaque water,
  broad/smooth banks, visibly repeated sample foliage, sparse ground cover,
  limited rapid-specific rock detail, unconverged hydraulics, and open guide,
  geospatial, ecology, environment-art, water-VFX, and performance gates keep
  photoreal and production promotion rejected.

### 2026-08-01 — Futaleufú Terminator physical runnable map restored

- `L_Terminator` now uses a 1009×1009, 8×8-component Landscape covering a
  reach-local 600×600 m window. Broad terrain is sampled in a Frenet frame from
  the review-gated OpenStreetMap route scaffold and Copernicus DEM GLO-30;
  the complete 600×84 m interpreted C3 bed remains unchanged. Where the 30 m
  source cannot resolve local form, deterministic correction and microrelief
  are bounded to 4.882 m and 1.160 m respectively outside the protected strip,
  explicitly as visual/collision infill rather than surveyed geography.
- A 301-point station/lateral coordinate map applies the recorded 206.596 m
  runtime datum with 0.0 m centerline surface error. Median cooked water, the
  player raft/start, and vertical-slice game mode are live in the saved map;
  field-derived capture water and foam are non-colliding and hidden during play.
  The one discrete C3 rock—the interpreted 3.2 m entry marker boulder—is present
  as review-gated D4 contact geometry rather than a surveyed hazard claim.
- `RaftSim.P4.RiverMapLoads.L_Terminator` passes 1/1 with a wet finite live
  window, upright raft, and zero swimmers; MapCheck reports 0 errors and 0
  warnings. The physical/runnable baseline is accepted, but dark opaque water,
  weak rapid structure, smooth banks, repeated placeholder vegetation, sparse
  ground cover, non-authoritative route stationing, unconverged hydraulics, and
  open guide/geospatial/ecology/art/water-VFX/performance gates keep photoreal
  and production promotion rejected.

### 2026-08-01 — Zambezi stable runnable package promoted

- The complete source-scale Boiling Pot-to-Mukuni Beach reference run now
  resolves through `/Game/RaftSim/Maps/L_Zambezi` in the generator, frontend,
  generated player model, scenario, shipping cook, packaging fallback, and
  runtime acceptance suite. The 1,722,040,058-byte Git LFS package is versioned,
  so a fresh checkout can launch every advertised runnable river without first
  generating an ignored preview map.
- Unreal regeneration and saved-map audit pass with 0 MapCheck errors/warnings,
  all 25 rapid markers, one runtime water config, four conditioned terrain
  tiles, and 7,679 vegetation instances. Focused PIE passes 1/1 with a wet
  finite solver window, eight breaking sites, visible masked rapid foam, an
  upright five-person raft, and zero swimmers. This is runtime delivery
  acceptance only; bathymetry, rapid-specific hydraulics, terrain/ecology art,
  guide/geospatial review, and performance promotion remain open.
- The player-facing catalog, M6 progression regression test, Python shipping
  contract, and cook list now all require `/Game/RaftSim/Maps/L_Zambezi`; the
  old ignored Landscape-candidate preview path is no longer accepted as a
  runnable destination.

### 2026-08-02 — Zambezi current-head runnable registry recheck

- Rechecked the six-river Free Run manifest, generated player selector, source
  scenario, runtime catalog, cook list, and committed `L_Zambezi` package after
  the intervening environment milestones. Every layer still resolves
  `zambezi_reference_run` to `/Game/RaftSim/Maps/L_Zambezi` at
  `reference_free_run` tier.
- `RaftSim.M6.CareerCatalog` passes 1/1 with no warnings or errors.
  `RaftSim.P4.RiverMapLoads.L_Zambezi` passes 1/1, loads PIE with the
  vertical-slice game mode and live cooked-field water, and completes MapCheck
  with 0 errors and 0 warnings. Twenty-one focused Python contracts pass.
- This reaffirms runnable status only. Production terrain, bathymetry,
  rapid-specific hydraulics, guide/rights review, photoreal art, and
  target-hardware performance remain open.

### 2026-08-02 — Futaleufú and Chilko organic waterline structure retained

- `L_Terminator` and `L_LavaCanyon` each add 1,440 source-Landscape-grounded
  instances from the rights-reviewed six-form CC0 rock set across both banks
  and the complete route. A deterministic 72-choice search keeps every
  instance outside the complete visible-water width and enforces full-route
  centerline clearance, dry-height, and 55-degree slope gates.
- All six per-river HISM components remain non-colliding and explicitly carry
  procedural-gap-fill, generic-rock/no-lithology, no-hydraulic-authority, and
  river-run tags. Source terrain, collision, water geometry, bathymetry,
  hydraulics, route stationing, hazard contacts, and raft forces are unchanged.
- Both maps place 1,440/1,440 targets with zero rejects. Fixed comparisons
  change 14.35-14.43% of the Futaleufú bank review band and 18.11-20.87% of
  the Chilko band beyond a two-percent pixel threshold. The result is retained
  as useful bank breakup, but photoreal promotion remains rejected because the
  coarse terrain, procedural ecology, opaque water, incomplete gravel/deadwood,
  sparse rapid VFX, unconverged hydraulics, and all six external acceptance
  gates remain open.

### 2026-08-02 — Futaleufú and Chilko temperate bank ecology V4 retained

- `L_Terminator` and `L_LavaCanyon` now alternate two deterministic baked
  morphologies for each broadleaf, conifer, riparian-shrub, and grass/forb
  ground-cover form. The shared family therefore has eight actual meshes rather
  than four forms varied only by instance scale and rotation.
- Each runnable map adds 1,800 dry near-bank grass, forb, and shrub patches. A
  64-choice source-Landscape search enforces full-route centerline clearance,
  the complete visible-water width, a 15 cm dry-height floor, and a 38-degree
  slope ceiling. Both rivers place 1,800/1,800 with zero rejects; total foliage
  rises to 8,000 while the existing 4,650-tree canopy count is unchanged.
- The new layer is non-colliding procedural presentation gap fill with explicit
  no-species/ecology/survey/hydraulic/raft-force authority. The editor builds,
  both focused runtime map tests pass 1/1 with zero warnings/errors, and the M9
  terrain/water audit passes 14/14. Fixed views retain the denser dry-bank
  transition, but photoreal promotion remains rejected for stylized botanical
  geometry, smooth coarse banks, dark opaque water, weak rapid VFX, incomplete
  reach-specific ecology, unconverged hydraulics, and open external gates.

### 2026-08-02 — Futaleufú live rapid lace retained; Chilko bracket rejected

- The Terminator runtime map keeps the accepted calm-water carrier byte-for-
  byte and lowers only its solver-foam presentation focus from `0.12-0.72` to
  `0.08-0.58`. Five interior breaking sites remain solver-owned, and visible
  rapid-lace vertices rise from 47 to 53 without changing terrain, collision,
  cooked fields, wet/dry ownership, bathymetry, hydraulics, or raft forces.
- Chilko's attempted `0.06-0.55` bracket was not retained. The current cooked
  Lava Canyon window has zero interior breaking sites and zero visible rapid-
  foam vertices; all four detected transitions fail at the wet-mask edge. The
  shipping map therefore keeps the conservative `0.12-0.72` defaults until a
  reviewed interior rapid field exists.
- Filtered map generation now reuses shared solver textures and foam material
  without resaving them. The editor build, 42 focused Python checks, six native
  water/map/render tests, and the 75-file protected-work audit pass. This is a
  technical readability improvement only; the retained Futaleufú rapid frame
  still fails photoreal water/VFX review and every external acceptance gate
  remains open.

### 2026-08-02 — Chilko rapid-approach launch framing corrected

- Re-evaluated the committed Lava Canyon cooked fields on the live surface's
  exact 3 m sampling grid. Low, median, and high bands all contain an interior
  supercritical-to-subcritical transition near local station 300 m with the
  required 15 m clearance. The earlier zero-site result came from the generic
  station-24 m launch clamping the moving carrier to stations 0-240, not from
  missing solver structure.
- `L_LavaCanyon` now launches at station 228 m in deep subcritical water,
  retaining 72 m of approach. The PIE map exposes one interior site at station
  300 m, full presentation coverage, 15 m clearance, six visible rapid-foam
  vertices, and a visible foam mesh. Boundary candidates remain rejected and
  no threshold is relaxed.
- Cooked fields, wet/dry masks, bathymetry, collision, buoyancy, and raft forces
  are unchanged. The live evidence remains too pale and sheet-like for
  photoreal promotion; coarse banks, procedural ecology, missing calibrated
  rapid morphology/VFX, and all six external reviews remain open.
