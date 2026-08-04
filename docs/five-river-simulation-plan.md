# Runnable River Simulation & Playability Plan

Written July 18, 2026; updated August 3, 2026. Goal: **all six runnable
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

Current-release-head verification keeps Zambezi in ordinal position 6 of the
six-river Free Run registry. The rebuilt `RaftSim.M6.CareerCatalog` and
`RaftSim.P4.RiverMapLoads.L_Zambezi` gates both pass against the committed map;
the hash-locked evidence is in
`docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_runnable_release_head_v10_review.json`.

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

### 2026-08-03 — Chilko river-local transmitting gameplay water retained

- `L_LavaCanyon` now persists a Chilko-local transmitting-water V2 instance on
  the solver-owned, all-wet-cell volume core. A project-owned flow normal
  supplies sub-grid optical breakup, and a project-owned foam-lace texture is
  multiplied by solver foam and speed so it cannot invent whitewater in calm
  or dry cells. The live surface remains a `0.035-0.14` detail skin.
- The regenerated runnable map retains 1,632 core triangles, 1,098 wet
  vertices, one interior station-300 m breaking site, six visible rapid-foam
  vertices, and the existing `0.12-0.72` focus. Cooked fields, wet/dry masks,
  bathymetry, topology, collision, buoyancy, and raft forces do not change.
- Against the identical 1280x720 `breaking_water_side` camera, water-band
  coverage above 0.90 luminance falls from `0.057366` to `0.033813`, coverage
  above 0.95 falls from `0.016782` to `0.001230`, and blue-minus-red rises from
  `0.026046` to `0.033418`. The editor build, M9 water audit, P4 Lava Canyon
  map gate, P2 water-render gate, and 11 Python contracts pass. The milestone
  remains fail-closed for photoreal approval because the broad wave faces,
  shoreline/banks, repeated ecology, rapid-scale VFX, hydraulic calibration,
  and all six external reviews remain open.

### 2026-08-03 — Chilko organic shoreline presentation retained

- `L_LavaCanyon` now adds a Chilko-only non-colliding dry-bank presentation
  layer: 3,600 instances from the existing six-form rights-reviewed CC0 rock
  family and 4,200 instances from the existing two-form project-owned short
  ground-cover family. Every instance is deterministically grounded on the
  source Landscape outside the active river width and screened against the full
  centerline, conditioned water height, and hard slope ceilings.
- The first small, far-bank tuning was rejected after its same-camera frame
  failed to visibly change the smooth bank. The retained bank-face tuning places
  all 7,800 targets with zero rejects, keeps maximum placed slope below 15.952
  degrees, and increases the matched bank-band green-dominant fraction from
  `0.168841` to `0.265534` and edge fraction from `0.130677` to `0.218952`.
- Terrain geometry/collision, water geometry, cooked fields, wet/dry masks,
  bathymetry, hydraulics, buoyancy, and raft forces are unchanged. The lower
  bank remains smooth; vegetation and rock forms remain procedural and lack
  exact ecology/geology authority; water/VFX, hydraulic calibration, platform
  performance, and all six external gates remain open.

### 2026-08-03 — Chilko full-reach shoreline and non-repeating wet bank retained

- Auditing the prior “complete route” claim found that its hard-coded placement
  range stopped at station 253 m, before the station-300 hero view, while the
  runnable coordinate map spans 0-600 m. V2 now covers stations 2.5-597.5 m and
  doubles the populations to 7,200 grounded gravel plus 8,400 grounded short-
  cover instances to preserve local density. All 15,600 targets place with zero
  rejects; all components remain non-colliding and presentation-only.
- The Chilko terrain material now mixes non-harmonic 124/217-scale detail
  projections, rotates the second 37 degrees, and uses the retained seven
  world-space fields for thresholded silt, gravel, and oxide response. It is
  shade-only with no world-position offset or terrain/physics authority.
- Clean 70- and 6-action editor builds, filtered regeneration, two live
  1280x720 captures, 28 Python checks, the M9 material audit, and the P4 map
  gate pass; MapCheck reports 0 errors and 0 warnings. The same-camera bank
  edge metric does not improve, the DEM-scale profile remains smooth, and the
  vegetation, rocks, water/VFX, atmosphere, exact ecology/geology, performance,
  and all six external gates remain open. V2 is retained as a bounded runtime
  correction, not photoreal or B2 promotion.

### 2026-08-03 — Pacuare organic shoreline and rainforest-floor transition retained

- `L_UpperHuacas` now adds six rights-reviewed CC0 moss-rock morphology
  variants, short rainforest-floor cover, and a shrub transition across both
  complete 600 m banks. All 2,600 rock, 5,200 cover, and 1,200 shrub targets
  place with zero rejects; the closest new instance remains 17.775 m from the
  full route centerline and all eight dedicated HISM actors are non-colliding.
- The 1009×1009 Landscape remains sole terrain render/collision/height
  authority and live cooked water remains sole gameplay-water/raft-force
  authority. The new dressing is explicitly procedural source-gap fill with no
  exact lithology, species, ecology, survey, bathymetry, or hydraulic claim.
- In fixed side-bank regions, green-dominant coverage rises from 56.19% to
  67.38% at guide seat and 60.25% to 73.20% at river eye; measured small-scale
  edge coverage rises from 12.35% to 21.45% and 12.27% to 22.87%. Near-black
  coverage also rises, and the tree/ground-cover forms remain visibly
  procedural, so the pass is retained only as a technical visual improvement.
  The editor build, four M9 Pacuare asset audits, the live P4 map gate, and 19
  focused Python contracts pass; all six external acceptance gates remain open.

### 2026-08-03 — Pacuare compound canopy morphology V2 retained

- Upper Huacas's four project-owned opaque rainforest fallback meshes now use
  one higher-resolution core plus six smaller deterministically oriented
  crownlets wherever V1 used one large faceted ellipsoid. The two canopy assets
  contain 10,401/14,476 and 10,434/14,610 render vertices/triangles; the shrub
  and ground-cover assets also exceed 5,900 vertices. Nanite, non-collision,
  source-mask placement, and the existing 18,400 foliage transforms remain.
- A Pacuare-only shadow-fill lift from `0.145` to `0.20` reduces near-black
  canopy-bank coverage from 21.29% to 20.17% at guide seat and 19.02% to 17.68%
  at river eye. Fixed-view crown-edge coverage rises from 18.56% to 25.58% and
  18.85% to 25.54%, with higher gradient-orientation entropy in both views.
- The result has finer breakup and more readable branch structure, but remains
  an obviously procedural four-mesh fallback rather than species-authentic
  rainforest art. Terrain, collision, water, cooked fields, bathymetry,
  hydraulics, and raft forces are unchanged. The editor build, M9 Pacuare suite
  4/4, runnable P4 map gate 1/1, MapCheck 0/0, 13 focused contracts, and all 79
  Pacuare Python tests pass; photoreal promotion and all six external
  acceptance gates remain open.

### 2026-08-03 — Pacuare live transmitting gameplay water retained

- `L_UpperHuacas` now uses a solver-owned, wet-cell-clipped transmitting core
  for gameplay instead of the broad opaque Default Lit carrier. The live
  surface remains as a 3.5%-14% hydraulic-detail skin; the authored packed-
  field ribbon and foam sheet stay capture-only and hidden in play.
- Project-owned flow-normal and foam-lace textures are recorded with generation
  provenance and have no hydraulic authority. The foam lace is multiplied by
  solver foam and speed and cannot create whitewater in calm or dry cells.
- The editor build, four focused Pacuare native audits, the live Upper Huacas
  PIE map-load gate, four Python contracts, and matched over-raft capture pass
  for this bounded technical milestone. Rounded terrain, generic rainforest
  ecology, thin optics, sparse foam/spray, unconverged hydraulics, and all six
  external gates keep photoreal and production promotion closed.

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

### 2026-08-03 — Zambezi runnable release-head reaffirmed

- Revalidated the committed `L_Zambezi` package after the intervening water and
  character milestones without regenerating or changing its terrain, water, or
  gameplay data. The frontend, six-river manifest, generated selector, source
  scenario, and shipping cook list still resolve `zambezi_reference_run` to
  `/Game/RaftSim/Maps/L_Zambezi` at `reference_free_run` tier.
- Ten focused Python contracts pass. `RaftSim.M6.CareerCatalog` passes 1/1 with
  no automation warnings or errors. `RaftSim.P4.RiverMapLoads.L_Zambezi`
  passes 1/1 in PIE with the vertical-slice game mode, 5,908-point coordinate
  map, live cooked-field water, eight active breaking sites, and visible rapid
  foam.
- The V4 hash-locked review makes this exact six-river contract durable. This
  is runnable-reference acceptance only; high-resolution terrain, surveyed
  bathymetry, calibrated rapid hydraulics, guide/geospatial/rights review,
  photoreal art and water VFX, and target-hardware performance remain open.

### 2026-08-03 — Zambezi post-ground-cover runnable revalidation

- Rechecked the unchanged Zambezi runtime contract at the post-ground-cover
  release head. Free Run still exposes **Zambezi: Boiling Pot to Mukuni Beach**
  as river 6 and resolves `zambezi_reference_run` to the committed
  `/Game/RaftSim/Maps/L_Zambezi` shipping package.
- Eighteen focused Python contracts and a clean 135-action UE 5.8 editor build
  pass. `RaftSim.M6.CareerCatalog` passes 1/1 with no warnings or errors;
  `RaftSim.P4.RiverMapLoads.L_Zambezi` passes 1/1 with MapCheck 0/0, the
  vertical-slice game mode, 5,908 coordinate-map points, 2,673 wet vertices,
  eight breaking sites, and 125 visible rapid-foam vertices.
- The V6 hash-locked review supersedes V5 for release-head evidence. Runnable
  reference status is retained; terrain, bathymetry, calibrated hydraulics,
  guide/geospatial/rights review, photoreal art and water VFX, and target-
  hardware performance gates remain open.

### 2026-08-03 — Zambezi V2 bank edge and launch optics retained

- Regenerated the runnable `L_Zambezi` package with
  `MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV2`. The shared transmitting-water
  parent now consumes live-core vertex-alpha wet-cell coverage, and the river-
  local profile expands the render-only bank blend from 4.5 m to 7.5 m. Solver
  wet/dry state, bathymetry, collision, buoyancy, raft forces, rapid records,
  stationing, and scoring are unchanged.
- Matched 1280x720 gameplay captures at the identical raft transform retain
  2,673 wet vertices, eight breaking sites, 125 visible rapid-foam vertices,
  and 4,224 volume-core triangles. The measured water fraction above 0.90
  luminance falls from 7.3201 to 1.2097 percent, and the sampled right-bank p99
  vertical edge falls 14.8 percent.
- A clean 137-action editor build, saved-map schema V18, the focused V2
  material test, water-rendering guard, and runnable map test pass; MapCheck is
  0/0. The V10 runnable review and V2 matched-water review retain the bounded
  improvement without claiming photoreal shoreline, hydraulic, ecology, art,
  character, guide, rights, geospatial, seasonal-flow, or platform acceptance.

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

### 2026-08-02 — Chilko bank-clipped live water volume retained

- The live-water audit found an architectural mismatch: reach-local maps hide
  the authored capture ribbon, while `M_RaftSim_LiveRiverSurface` was designed
  as a non-transmitting detail overlay above authored Single Layer Water. Lava
  Canyon then forced that overlay to `0.88-0.98` coverage, producing a pale
  opaque sheet with no optical river body beneath it.
- Chilko now pilots a second, non-colliding solver mesh shaded by the existing
  raft-transmission Single Layer Water parent. It triangulates only cells whose
  four samples are wet and at least `0.60` inside the station/bank feather,
  sits 1 cm beneath the animated detail surface, and leaves the final soft bank
  transition to that detail layer. PIE resolves 1,352 core triangles from
  1,098 wet vertices while preserving the interior breaking site, six visible
  rapid-foam vertices, the wet/dry field, collision, buoyancy, and raft forces.
- The retained guide-side capture changes the water band from warm-gray
  (`blue-red=-0.029955`) to blue-gray (`blue-red=0.023394`) and reduces mean
  water-band luminance from `0.700035` to `0.683587`. It restores depth and
  reflections without a rectangular bank overlay. Smooth banks, stylized
  ecology, blown highlights, incomplete rapid VFX, and all six external gates
  keep photoreal and production promotion rejected. Evidence is hash-locked in
  `chilko_live_volume_core_v1_review.json`.

### 2026-08-02 — Cold-water live volume expanded and bank topology corrected

- The retained Chilko Single Layer Water architecture now also serves
  Futaleufú Terminator. Both maps use `0.035` calm and `0.14` active detail-
  surface coverage above a non-colliding optical core, while Colorado and
  Pacuare remain on their independently reviewed carrier architecture.
- The first generalized trial exposed why the pilot's combined station/bank
  alpha could not own core topology: it created an artificial one-cell dry
  strip parallel to Terminator's sampled wet bank. The retained rule now uses
  the four-corner wet mask laterally and applies the `0.60` threshold only to
  station-end coverage. That reaches the complete sampled wet bank without
  entering a cell with any dry corner or exposing the rectangular moving-
  window ends.
- Live PIE reports 2,438 core triangles from 1,575 wet Terminator vertices and
  1,632 core triangles from 1,098 wet Lava Canyon vertices. Terminator retains
  five interior breaking sites and 53 rapid-foam vertices; Chilko retains one
  site and six vertices. The full six-map native suite passes, as do the
  editor build and 15 focused source checks.
- The retained Terminator frame changes the rapid body from warm chalk-gray
  (`blue-red=-0.030928`) to blue-gray (`blue-red=0.005841`) and removes the
  rejected bank-parallel dry strip. Chilko remains blue-gray while its water-
  band highlight fraction falls from `0.066228` to `0.053854`. Smooth banks,
  tessellated ground, stylized ecology, bright rapid highlights, incomplete
  rapid VFX, and all six external gates keep photoreal and production promotion
  rejected. Current evidence is hash-locked in
  `cold_water_live_volume_core_v2_review.json`; the Chilko V1 review remains the
  historical pilot record but no longer describes the current topology.

### 2026-08-03 — Colorado Hance rapid-approach framing corrected

- Re-sampled every committed Hance release band on the live renderer's exact
  3 m grid. Low, moderate, and high bands each contain accepted interior
  supercritical-to-subcritical candidates near local station 405 m; the prior
  generic station-24 m launch kept that structure outside the useful runnable
  approach framing.
- `L_Hance` now launches at station 336 m in deep subcritical water, retaining
  69 m of approach. The live map reports seven active breaking sites, full
  strongest-interior presentation coverage, 18 m clearance, 0.2014 m maximum
  hydraulic relief, and one visible rapid-foam vertex. A separately serialized
  solver-rapid camera replaces the previously duplicated guide/rapid evidence
  view, and all three fixed cameras are byte-distinct.
- No cooked field, wet/dry mask, bathymetry, collision, buoyancy, or raft force
  changed. The corrected scenario framing remains only reference-runnable:
  flat muddy cross-river water bands, sparse foam without rapid-scale spray or
  mist, terraced/tessellated canyon surfaces, repeated sparse ecology and
  ground cover, missing surveyed geography, unconverged hydraulics, and all
  six external acceptance gates keep photoreal and production promotion open.
  Evidence is hash-locked in
  `colorado_hance_rapid_approach_launch_v1_review.json`.

### 2026-08-03 — Pacuare layered rainforest humidity retained

- `L_UpperHuacas` now serializes a four-actor Pacuare-only atmosphere contract:
  movable sun, captured sky fill, physical SkyAtmosphere aerial perspective,
  and two non-volumetric exponential humidity layers. Three volumetric
  candidates were rejected because they deepened black canopy occlusion.
- The retained views raise bank luminance and reduce near-black bank pixels by
  37.47%-44.38%. UE 5.8 PIE replays stale fog state-stream values after normal
  actor ticks, so the Pacuare runtime config alone reasserts density `0.0075`
  and volumetric-off in `TG_PostUpdateWork`; other rivers do not pay this tick.
- The editor build passes, Pacuare M9 passes 4/4, and Pacuare P4 passes 1/1 with
  the exact runtime fog values. The unchanged runnable Zambezi map also passes
  `RaftSim.P4.RiverMapLoads.L_Zambezi` 1/1 with live solver water, 2,673 wet
  vertices, eight active breaking sites, 125 visible rapid-foam vertices, and
  4,224 optical-core triangles. Terrain, water geometry, collision, cooked
  fields, hydraulics, bathymetry, and raft forces are unchanged.
- This is a bounded readability improvement, not photoreal promotion. Generic
  vegetation, coarse terrain, thin water/whitewater VFX, missing weather and
  wind, unconverged hydraulics, performance, and all six external reviews
  remain open. Evidence is hash-locked in
  `pacuare_humid_atmosphere_v1_review.json`.

### 2026-08-03 — Bounded multi-site rapid VFX coverage retained

- The shared production Niagara bridge now drives the nearest six accepted
  breaking sites instead of two, still within the existing eight-pair pool and
  120 m hard cull. Moderate-intensity aerosol and roller scale/rates increase
  inside that bound; no transient Niagara actors are spawned.
- The runnable Zambezi gate passes with eight solver-owned breaking sites, six
  active aerosol emitters, six active roller emitters, 125 rapid-foam vertices,
  2,673 wet vertices, 4,224 optical-core triangles, and MapCheck 0/0. M4 passes
  4/4 and the focused Python/source suite passes 43 tests.
- The map package and Niagara assets are byte-identical. Cooked fields, wet/dry
  state, bathymetry, water geometry, collision, buoyancy, raft forces, scoring,
  and progression do not change. Matched strongest-site and VFX-off evidence
  shows bounded local breakup but not a convincing overturning rapid volume;
  photoreal water art, validated hydraulics, target performance, and all named
  external approvals remain open in
  `zambezi_solver_driven_rapid_vfx_v1_review.json`.

### 2026-08-03 — Shared authored-river live-surface refinement retained

- All six runnable maps now use a 2x render-only subdivision of the live-water
  surface: the five curved windows resolve to 10,465 vertices and 20,480
  triangles, while South Fork's legacy straight window resolves to 17,956
  vertices and 35,378 triangles. Both use 1.5 m visual spacing. A river-water
  config is the opt-in, so the config-less test tank retains its original
  4,624-vertex, 3 m compatibility surface.
- Smoothing, hydraulic relief, normal derivatives, and jump classification
  retain a two-vertex stride on refined surfaces and therefore preserve the
  original 3 m physical analysis neighbourhood. Two short oblique wave bands
  replace part of the former broad-wave amplitude inside a reduced 0.248 m
  theoretical displacement envelope. Sampling, wet/dry authority, cooked
  fields, collision, buoyancy, D3, and D4 are unchanged.
- The UE 5.8 editor builds; `RaftSim.P2.WaterSurfaceRenders` passes 1/1;
  `RaftSim.P4.RiverMapLoads` passes all six maps; and `RaftSim.M4` passes 4/4.
  Initial refresh diagnostics range from 1.961 ms to 4.351 ms in the
  unattended null-RHI map suite. This is useful CPU evidence, not a desktop or
  VR GPU acceptance result.
- A fixed-camera Zambezi comparison increases measured high-pass surface detail
  by 7.63% and edge coverage by 12.55%. The broad diagonal analytical swell
  remains visible and the rapid still lacks a coherent overturning crest,
  aerated plunge, and recirculating body, so photoreal and production promotion
  remain failed. The evidence and all seven external gates are hash-locked in
  `zambezi_refined_live_surface_v1_review.json`.

### 2026-08-03 — Connected solver plunge membrane retained

- Production Niagara no longer suppresses every connected rapid-water surface.
  The three strongest accepted breaking sites retain one crest-to-plunge
  membrane each while the bounded particle pools provide detached aerosol and
  roller breakup.
- The former three nested translucent shells were explicitly re-tested and
  rejected because they restore dome and repeated tent artifacts. The retained
  topology removes the downstream back of that loop, uses one masked
  project-owned foam-lace sheet with raft/crew exclusion, and is bounded to
  1,512 non-colliding triangles. Sampling, cooked fields, wet/dry state,
  collision, navigation, buoyancy, D3, D4, scoring, and progression are
  unchanged.
- The editor build and P2 pass; P4 passes all six runnable rivers with exact
  connected-sheet counts from 504 to 1,512 triangles. Matched fixed-camera
  Zambezi evidence increases edge coverage 12.78% and high-pass detail 8.23%
  without the rejected shell artifacts. The solver-side change is subtle and
  the rapid still lacks a convincing aerated hole and recirculating body, so
  photoreal promotion and all named external gates remain open in
  `zambezi_connected_plunge_v1_review.json`.

### 2026-08-04 — Shared nonperiodic live-wave field retained

- The live-water renderer no longer adds its dominant continuous 11.5 cm
  diagonal sinusoid. Four hydraulically activated, station-dominant crest
  bands use smooth reach-scale energy packets and incommensurate phase warps;
  two split phase-warped ripples preserve the 1.8 cm calm-water envelope.
- Exact analytical station/lateral derivatives drive presentation normals.
  The theoretical displacement bound drops from 0.248 m to 0.168 m, while
  sampling, cooked fields, wet/dry state, collision, buoyancy, D3, and D4 stay
  unchanged.
- The editor build and `RaftSim.P2.WaterSurfaceRenders` pass; the complete P4
  suite passes all six runnable rivers. The matched Zambezi maximum drops from
  0.2343 m to 0.1046 m and the repeated center-band continuity is removed.
  The retained sampled rise and missing measured bathymetry, aerated hole,
  recirculation, spray/mist, and platform/art approvals keep photoreal and
  production promotion open in `zambezi_nonperiodic_live_wave_v1_review.json`.
