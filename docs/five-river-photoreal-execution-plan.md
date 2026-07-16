# Five-River Photoreal Production Execution Plan

Written July 15, 2026. This is a self-contained execution plan for an agent with no prior context. It consolidates the goals below into ordered, committable tasks, building on infrastructure that already exists in this repo. Read `docs/code-review-remediation-plan.md` first — its Finding 1 (water-solver validation honesty) and Finding 3 (LFS retention) are prerequisites woven into this plan.

**Execution status, July 16, 2026:** active goal started. `docs/code-review-remediation-plan.md` is complete under the owner's Option B water-solver decision and keep-versioning/no-prune retention decision. The current baseline is `504 passed, 3 skipped` for `cd physics && UV_CACHE_DIR=/private/tmp/raftsim-uv-cache uv run pytest -q`. This plan now executes from that state: live custom-water rapid approval remains blocked until genuine solver parity gates pass, while generated preview/candidate maps remain versioned in Git LFS unless the owner later reverses that decision.

## Mission

Build complete photorealistic Unreal river environments, with realistic named-rapid behavior and flexible-raft gameplay mechanics, for the five-river runnable portfolio, continuing until lifelike in-engine guide-seat and river-eye screenshots can be captured for each river:

1. **South Fork American** — Chili Bar put-in to Folsom Reservoir take-out.
2. **Colorado River, Grand Canyon** — Lees Ferry put-in to Pearce Ferry take-out.
3. **Pacuare River** — Tres Equis put-in to Siquirres take-out.
4. **Futaleufú River** — Rio Azul Swinging Bridge put-in to The Pasarela take-out.
5. **Chilko River** — Chilko River Lodge put-in to Chilko–Taseko Junction take-out.

**Zambezi (Boiling Pot to Mukuni Beach) is backlogged**: no adequate terrain/centerline source exists (see `docs/batoka-high-resolution-terrain-acquisition-request.md`). Keep its evidence and catalog entries with their existing `additional_active_environment` role; do no new Zambezi work except passively recording acquisition leads.

This matches the existing portfolio decision in `docs/chilko-futaleufu-photoreal-goal.md` and `docs/named-rapid-realism-validation-plan.md` — this plan sequences and executes that decision; it does not change it.

## What already exists (do not rebuild)

- **Corridors/source data**: production corridor packages under `physics/data/real_world/` for South Fork, Colorado, Pacuare, Futaleufú, Chilko (builders in `physics/src/raftsim/*_production_corridor.py`, `real_world.py`). Chilko has a 55.846 km official-hydrography route, MRDEM-30 terrain, gauge attachments (`08MA002`, `08MA001`).
- **Named rapids**: `physics/data/real_world/named_rapid_source_catalog.json` (85 markers, 6 rivers, link-only rights policy), generator `physics/src/raftsim/named_rapid_registry.py`, editor markers at `unreal/Content/RaftSim/River/named_rapid_editor_markers.json`, candidate geometry GeoJSON, and **453 deterministic simulator review-run definitions** at `unreal/Content/RaftSim/Automation/named_rapid_simulator_review_runs.json` — all currently *blocked* pending exact geometry, validated water windows, and guide review.
- **Editor tooling**: 40+ `RaftSim.*` commands in the RaftSimEditor module (landscape import, materials, foliage, captures) and the Rapid/River Editor (`DA_RapidRiverEditorShell`) with portfolio-role filtering.
- **Review-gate machinery**: hash-locked review JSONs, capture pipelines, map-check gates, and the photoreal completion criteria in `docs/photoreal-river-environment-production-plan.md`.
- **Raft physics baseline**: rigid 6-DoF raft coupling (`physics/src/raftsim/raft_coupling2_5d.py`), Chaos/Jolt evaluation docs, and the flexible-raft requirements already itemized in `TODO.md` (Milestone 26, "Flexible Inflatable Raft Mechanics", lines ~1361–1371).

## Ground rules (apply to every task)

1. **Commit and push after completing each task.** One task = one or more focused commits, pushed immediately to `origin` (GitHub) and `gitlab` (both remotes are configured; push to both unless the owner says one is canonical). Never batch a day of work into one commit. Before the first push, verify push access; if a push is rejected, stop and report rather than force-pushing.
2. **Tests first-class**: run `cd physics && uv run pytest -q` before and after each task; regenerate hash-locked manifests through their generators, never by hand. New data attachments and generated assets get the same manifest + regression-test treatment the repo already uses.
3. **Rights discipline** (existing policy, keep it): factual rapid names/miles/classes and source URLs are committed; third-party guide prose, maps, photos, and social posts stay **link-only** unless item-level reuse permission is recorded. Reference photos inform art review but are never committed. Exact hazard/access geometry needs publication review before public screenshots expose it.
4. **Asset licensing for an open-source repo**: Poly Haven (CC0) assets may be committed (follow the existing hash-locked intake path used for the jacaranda/fir/island-tree experiments). **Fab assets: check each item's license before intake.** Most Fab Standard License content may be *used* in the project but **not redistributed as source assets in a public repo** — such assets stay local-only under the existing `RAFTSIM_REVIEWED_*_SOURCE_ROOT` / `unreal/Scripts/*.py` import pattern with committed manifests (URL, license, hash) but uncommitted binaries, and the environment must degrade gracefully (procedural fallback) when they are absent. CC0/appropriately-licensed Fab items may be committed like Poly Haven. Record every intake decision in `docs/free-and-ai-asset-policy.md`.
5. **LFS retention**: this plan will regenerate giant corridor `.umap`s repeatedly. The owner's July 16, 2026 retention decision controls this work: keep versioning generated preview/candidate maps and do not prune Git LFS. Do not run `git lfs prune`, including dry runs; do not untrack or ignore current candidate maps; do not delete hosted LFS objects or rewrite history. Commit meaningful generated map revisions when a task intentionally changes them, but do not create meaningless LFS churn from verification-only binary resaves when the logical manifests are byte-identical.
6. **Water authority**: named-rapid behavior review is only meaningful against honestly validated water. The remediation plan's Step 1.1–1.2 (uncalibrated solver truth measurement + honest gate labeling) must land before any rapid's "validated C++ water window" is signed off in Workstream C. Fixture-playback water must never be presented as rapid-behavior evidence.
7. **Never weaken a gate to pass it.** All the existing review gates (art, guide, geospatial, rights, hazard-readability, performance) stay. "Lifelike" is decided by the human owner viewing captures, not by a metric alone.

---

## Workstream A — Source data, stationing, and seasonal flows per river

Goal: every river has an authoritative centerline with exact put-in/take-out anchors, reach-covering terrain/imagery, gauge-derived low/reference/high flow bands, and named-rapid markers stationed by GPS/aerial/guide evidence instead of order-interpolation.

### A1. South Fork American (first — smallest reach, most data, known blocker)
- Fix the recorded NHD flowline conflict: the current candidate declares 26.2 km Chili Bar→Coloma vs. ~9.0 km published miles (`physics/data/real_world/south_fork_american_chili_bar/review/named_rapid_station_alignment_review.json`). Re-select/clip the correct NHD flowline, re-anchor Chili Bar and the Folsom Reservoir take-out, rebuild stationing.
- Extend the corridor to the full Chili Bar→Folsom reach (current package covers a sub-reach; the gorge below Coloma must be included).
- Attach flow bands from the official gauge record (Chili Bar releases; use USGS/CDEC as source authority, recorded per the existing gauge-attachment pattern) — low/summer-recreational/high bands with dates and units.
- Re-station all 20 catalog markers (Meat Grinder, Troublemaker, the gorge rapids, etc.) against the corrected centerline; then remove their `provisional`/blocked flags via the catalog generator.
- Exit gate: `named_rapid_station_alignment_review.json` records the conflict as resolved; zero South Fork markers use order-interpolation; corridor regression tests pass.

### A2. Colorado Grand Canyon
- Extend the corridor from the current 4.7 km Lees Ferry pilot toward full-reach coverage (Lees Ferry→Pearce Ferry, ~450 km). This must be windowed: author per-rapid reach windows (10–20 km each) along a full-length centerline rather than one monolithic landscape. Centerline from NHD/USGS; terrain from USGS 3DEP 10 m (1 m lidar where available); imagery NAIP.
- Cross-check the 15 major-rapid miles against NPS/USGS sources and a published river guide (catalog notes this is outstanding); station Lava Falls, Crystal, Hance, Horn Creek, Granite, Hermit, Sockdolager, House Rock, Badger, Soap Creek, Upset, Deubendorff and the rest of the catalog set exactly.
- Flow bands from USGS 09380000 (Colorado River at Lees Ferry), including a note on Glen Canyon Dam release regime.
- Exit gate: every major rapid has an exact-stationed marker inside an authored terrain window; miles cross-checked with recorded sources.

### A3. Pacuare
- Replace order-interpolated stations for all 15 markers (Upper/Lower Huacas, Cimarrón, Dos Montañas, etc.) with GPS/aerial-interpreted geometry: digitize from Sentinel-2/available orthoimagery against the existing preview scaffold, then flag for guide confirmation.
- Terrain: best available public DEM for Costa Rica (record product/license; NASADEM/Copernicus GLO-30 fallback); imagery windows per rapid.
- Flows: Costa Rica has sparse public gauging — research ICE/SENARA records; if no official gauge exists, define bands from seasonal precipitation regime + operator-published runnable ranges, explicitly labeled `hypothesis_pending_guide_review`.
- Exit gate: no Pacuare marker uses `provisional_downstream_order_interpolation`; flow bands recorded with source class.

### A4. Futaleufú (continue existing work)
- Corridor and route are done (Rio Azul→Pasarela). Remaining: exact stationing for Terminator, Khyber Pass, Himalayas + the other catalog markers (currently order-interpolated), and DGA Chile gauge research for flow bands.
- Exit gate: same as A3.

### A5. Chilko
- Execute the already-scoped work: daily-window gauge routing for `08MA002` (put-in is below the lake outlet), exact stationing for Bidwell Rapids, Lava Canyon, White Mile, Green Mile, Miracle Canyon with aerial interpretation, and put-in/take-out access confirmation notes.
- Exit gate: numeric low/reference/high bands unblocked; five rapids exactly stationed.

**A-series research method** (applies to all rivers): use web research on guidebooks, outfitter descriptions, American Whitewater, NPS/USGS publications, trip reports, and rights-reviewed public/social reference photos and videos to (a) confirm rapid names/aliases/order, (b) extract feature descriptions — named holes, waves, ledges, lines ("enter left of the tongue", "lateral at the top"), (c) note flow-dependent character changes. Every source lands as a link-only catalog entry with retrieval date. Preserve source disagreement as aliases/notes per the existing catalog rules.

---

## Workstream B — Photoreal environment assets (external-first strategy)

Goal: replace proxy terrain dressing, generic PVE foliage, and fallback materials with rights-cleared, distance-stable asset sets per river biome, then enable UE5's full rendering feature set. This adopts the external-asset strategy: after 42 unpromoted in-repo procedural tree iterations, sourced assets are the default and in-repo procedural generation is for gap-filling and set dressing, not hero vegetation.

### B1. Asset source survey and intake pipeline hardening (do once)
- For each biome below, survey **Fab** (primary — Quixel Megascans are now on Fab and largely free for UE use; check per-item license for redistribution) and **Poly Haven** (CC0, committable), plus other CC0 sources. Produce a per-river shopping list with license class per item.
- Harden the existing intake path (`unreal/Scripts/*.py` importers + hash-locked manifests + isolated visual gates): one command per asset set, idempotent, with the Metal sampler/Nanite-foliage lessons already recorded in `docs/zambezi-futaleufu-photoreal-goal.md` applied automatically (alpha-as-mask classification, non-Nanite masked foliage, `PreserveArea` for woody geometry only).
- Extend `docs/free-and-ai-asset-policy.md` with the committed-vs-local-only license rules from Ground Rule 4.

### B2. Per-river biome asset sets (one task per river, in A-series order)
- **South Fork American**: Sierra foothill oak woodland + gray pine + chaparral; granite/metamorphic river rock; summer-dry grass banks. Megascans coverage for this biome is strong.
- **Colorado Grand Canyon**: layered sandstone/limestone/schist cliff materials (the signature asset — invest here), desert scrub (tamarisk, willow, barrel cactus), sand beaches, basalt at Lava Falls.
- **Pacuare**: tropical rainforest canopy (multi-strata), mossy basalt/andesite boulders, waterfall side-streams, mist/atmosphere presets.
- **Futaleufú**: continue the native-canopy program but pivot per the strategy decision: source the best available Nothofagus-analog/temperate-rainforest assets from Fab (ecology-reviewed-analog acceptability is an owner sign-off recorded in the review JSON), retain the validated project-owned sapling/fern assets for near-bank strata; granite boulders, turquoise water color grading.
- **Chilko**: interior BC lodgepole/spruce/aspen, glacial-blue water, volcanic canyon rock for Lava Canyon.
- Each set passes the existing isolated gates (turntable + 60/150 m river-distance captures, map-check zero errors, hash-locked review JSON) before corridor substitution — but with a **promotion budget**: if a set fails 3 isolated iterations, escalate to the owner with the review evidence instead of iterating further.

### B3. Water, materials, and effects
- Production water shading per river (reflection, refraction, foam, spray, mist, wet-bank transitions), driven by the accepted water fields — depends on Ground Rule 6 sequencing. Use the UE Water plugin + Niagara for spray/foam; keep the render-only/authority split the repo already enforces.
- Unique near-field material sets per river replacing the shared fallbacks (already itemized in TODO ~line 936).

### B4. Advanced UE5 feature enablement (after each river's assets are in place)
- Enable/verify per river: **Nanite** on all opaque static geometry (respecting the documented masked-foliage exceptions), **Lumen** GI + reflections, **Virtual Shadow Maps**, **TSR**, Landscape Nanite, World Partition/HLOD streaming for the long corridors, PCG for set dressing.
- Each enablement is a measured task: capture the same review views before/after with frame timings; record in a review JSON. Target hardware profiles come from Workstream E.
- Exit gate per river: guide-seat and river-eye captures at three flow bands pass automated artifact checks and the human "lifelike" review — the mission's definition of done.

---

## Workstream C — Named-rapid realism: identify, mark, simulate, review

Goal: every notable rapid — with close attention to named rapids and their notable holes and waves — is identified in each scenario, marked for the editor, and exercised by simulator boat runs so its behavior can be reviewed against the published descriptions.

### C1. Feature-level rapid research (per river, follows A-series stationing)
For each named rapid, extend its catalog entry with a **feature inventory**: each notable hole, wave, ledge, pour-over, eddy line, and lateral gets a named sub-feature record (name/alias, position within the rapid, flow-dependence notes, consequence class, source links). Examples of the level of detail required: Troublemaker's right-side hole and left sneak (South Fork); the Ledge Hole at Lava Falls and its V-wave (Colorado); Terminator's entrance seam and Himalayas' wave train (Futaleufú); the White Mile's continuous wave field (Chilko). Update `named_rapid_registry.py` schema to carry sub-features and regenerate the editor markers.

### C2. Editor marking
Extend the marker → editor pipeline so each sub-feature becomes a typed editor pin (hole/wave/ledge/eddy/line) visible in the Rapid/River Editor and placeable on the corridor landscape, with the existing confidence/blocker badges. The editor's job is to make "is the hole in the right place at this flow?" a visual question a reviewer can answer.

### C3. Water windows per rapid
For each stationed rapid, author the reach-local scenario window (bed geometry from A-series terrain + guide-informed bed interpretation) and run the C++ solver honestly (Ground Rule 6): the window's water fields must produce the cataloged features *from the dynamics* — a hole where the ledge is, a wave train where the guides say — at the three flow bands. Where the solver cannot produce a documented feature, record the gap honestly in the window's review JSON and use the bounded feature-forcing machinery only with an explicit `feature_forced: true` label per feature. Chase solver improvements only for systematic failures (that feeds the remediation plan's Option B decision).

### C4. Simulator boat runs
The 453 review-run definitions in `unreal/Content/RaftSim/Automation/named_rapid_simulator_review_runs.json` are the harness: unblock them river-by-river as C2/C3 land. Each rapid × flow band gets its defined clean reference line, bounded feature-contact line, and (where cataloged) portage control. Runs are deterministic and save trajectory, raft/crew/swimmer telemetry, conservation overlays, guide-seat video, river-eye video, and fixed frames (the TODO ~line 1355 contract). Store run outputs under the existing reports pattern with the LFS retention policy applied to video.
- **Review loop**: for each rapid, a human (ideally guide-experienced) reviews the run captures against the source descriptions and grades: feature presence/position/scale, line behavior, consequence realism. Verdicts land in per-rapid review JSONs; failures generate targeted C3 geometry/window fixes. A rapid is done when its runs at all three flows are approved.

### C5. Rapid behavior + flexible raft integration
Re-run each approved rapid's consequence lines after Workstream D lands, since flip/wrap/high-side outcomes change with the flexible raft. The named-rapid approval that counts for release is the one with flexible-raft dynamics enabled.

---

## Workstream D — Flexible inflatable raft mechanics

Goal: capture and simulate the real behavior of a flexible raft: crew sitting on the outer tube locally depresses it into the water; water flowing over a depressed/loaded tube can flood, flip, or pin the boat; a raft can wrap against a rock and be trapped. These map directly onto the existing TODO Milestone 26 items (~lines 1364–1371) — implement them in this order:

- **D1. Compliant tube model**: deterministic pressure/volume-compliant perimeter tube segments + floor/lacing/frame coupling layered on the validated rigid 6-DoF raft state. Python reference implementation in `raftsim` first (extend `raft_coupling2_5d.py`), with fixtures, before any engine port. Scoring authority stays disabled.
- **D2. Seat-load coupling**: seat occupancy, lean, brace, and high-side actions drive *local* tube deformation and freeboard — a guide sitting on the stern tube visibly sinks it — not just center-of-gravity offsets.
- **D3. Overwash and flip**: deformed upstream-tube water loading, overtopping flux, retained water mass, drainage, and the resulting roll moment, coupled to the accepted water sampler. This is the "water flowing over the outer tube flips the boat" mechanic; it must make upstream-tube exposure in a hole genuinely dangerous and a timed high-side genuinely effective.
- **D4. Rock contact, wrap, and pin**: bounded rock indentation, friction, wrap/pinch around obstacles, pressure-dependent release, damping, and stable post-contact shape recovery — without modifying accepted water fields. This is the "trapped against a rock" mechanic.
- **D5. Telemetry + replay**: per-segment state, pressure/volume, freeboard, floor load, overwash flux/side, entrained water, contact patch, release margin, and roll moments — deterministic and replayable.
- **D6. Validation fixtures**: static seat-load sag, traveling crew shift, rock pinch/wrap, upstream-tube overwash flip, timed high-side save, post-contact recovery, and pressure/flow sweeps — validated against Project Chrono (or another reviewed compliant reference) plus the Chaos rigid baseline. These fixtures are *behavioral*, not snapshot-manifest tests.
- **D7. Engine integration + budgets**: port the authoritative model into the UE runtime raft island (per `docs/unreal-physics-authority.md`), measure desktop/console/handheld/VR budgets, and require identical authoritative outcomes across platforms — only visual subdivision/wrinkles/spray scale.
- **D8. Gameplay enablement**: enable scoring-critical flexible-raft outcomes only after D6 fixtures, conservation, deterministic replay, and the C4/C5 named-rapid reviews pass.

D1–D6 are Python-side and can proceed in parallel with Workstreams A–B from day one. D7 depends on the water-authority sequencing (Ground Rule 6).

---

## Workstream E — Multi-platform

Goal: the game runs multi-platform with identical authoritative physics and scalable rendering.

- **E1. Platform matrix decision (owner input)**: propose Windows + Linux desktop, macOS (already the dev platform — keep the documented Metal caveats green), and VR via OpenXR (plan exists: `docs/unreal-vr-openxr-plan.md`) as the shipping tier; console/handheld as evaluation targets (devkit/licensing is an owner decision, tracked but not blocking).
- **E2. Scalability profiles**: define desktop-high / desktop-scalable / VR / handheld-low profiles; wire the TODO ~line 1359 contract — authoritative physics and rapid outcome envelopes identical across profiles, only rendering detail scales. Add an automated profile-parity run to the named-rapid harness (same seed, same outcomes, different profile).
- **E3. CI/packaging**: scripted package builds per platform, run per release candidate; capture performance evidence per river per profile (feeds B4's exit gate and the TODO ~line 1340 requirement).

---

## Sequencing

Parallel tracks: **A and D start immediately**; B1 starts immediately; remediation Finding 1 (solver truth) runs first in the physics track.

| Stage | Work | Depends on |
|---|---|---|
| 1 | Remediation F1 (solver truth, complete) · A1 South Fork stationing fix · D1–D2 · B1 intake hardening | — |
| 2 | A2–A5 (staggered, one river task at a time) · B2 South Fork assets · D3–D4 · C1 research (per river as A lands) | Stage 1 |
| 3 | C2–C3 South Fork (Meat Grinder + Troublemaker first — the designated first executable named-rapid runs) · B2 remaining rivers · D5–D6 | Stage 2 |
| 4 | C4 South Fork runs + review · B3 water/effects · B4 Nanite/Lumen per river · E1–E2 | Stage 3 + Ground Rule 6 |
| 5 | C2–C4 remaining rivers in order: Futaleufú, Colorado (windowed), Pacuare, Chilko · D7 | Stage 4 |
| 6 | C5 flexible-raft re-review of all rapids · D8 · E3 packaged perf evidence · final lifelike capture sets per river | Stage 5 |

Per-river completion order is deliberate: **South Fork first** (shortest, best data, cheapest iteration — it debugs the whole pipeline), then Futaleufú (corridor most mature), Colorado (largest, windowed), Pacuare, Chilko.

## Active execution queue

Started July 16, 2026 from clean commit `119239d68`.

- [x] Reconcile this execution plan with the completed code-review remediation and the owner decision to keep versioning generated maps instead of pruning/untracking them.
- [ ] A1 South Fork American stationing and full-reach corridor repair.
  - [x] Record the current A1 blocker as a reproducible status artifact: the committed published-mile scaffold covers all 20 South Fork rapids, while exact geometry, full Chili Bar-to-Folsom corridor coverage, and flow-band promotion remain blocked pending full-reach hydrography, exact anchors, and guide/geospatial review.
  - [x] Encode the full-reach acquisition and route-validation contract: `hydrography/full_reach_acquisition_plan.json` defines the over-covering Chili Bar-to-Folsom review envelope, planned USGS 3DHP/NHD, 3DEP, NAIP, flow-history, and guide/access pulls, explicit missing Folsom anchor, Coloma checkpoint tolerance, and no-promotion gates for South Fork editor geometry and Meat Grinder/Troublemaker solver windows.
  - [x] Run and record the small full-reach metadata probe: TNM NHD metadata returns 38 candidate products for the review envelope, while TNM 3DEP and NAIP product metadata return zero hits, so terrain and imagery must use bounded official 3DEP and USDA/APFO NAIP ImageServer/tile-index exports instead of pretending TNM product metadata is sufficient.
  - [x] Extract the official NHD HU8 18020129 named-flowline candidate pool for the full review envelope: `hydrography/full_reach_nhd_named_flowline_extract.geojson` preserves 198 South Fork American River source records from the verified USGS zip, totaling 65.786574 km of source linework, and keeps the result review-gated as a candidate pool rather than an ordered route.
  - [x] Diagnose the full-reach NHD route graph before promotion: `hydrography/full_reach_nhd_route_graph_diagnostic.json` records one connected 198-edge/199-node candidate pool, records that the shortest path to the current Coloma access seed lands at 5,250.419 m instead of validating the published 9,012.326 m checkpoint, records the missing Folsom anchor, and blocks editor/solver binding until anchor/source-mile review plus directed route clipping pass.
  - [x] Attach source-backed full-reach anchor review: `review/full_reach_anchor_review.json` records Chili Bar mile 0.0, Coloma Bridge mile 5.6, and the Salmon Falls/Folsom downstream-end 20.5-21.0 mile source window from link-only factual guide sources; it explicitly treats the Coloma mismatch as unresolved route/anchor/source-mile evidence, not a final coordinate rejection, and keeps exact geometry, editor binding, solver windows, and rapid restationing blocked.
  - [x] Generate directed NHD station candidates for review: `review/full_reach_directed_station_candidates.json` records a unique 184-edge downstream NHD chain from Chili Bar with no branches or merges, and `review/full_reach_directed_station_candidates.geojson` exposes the upstream/checkpoint/downstream anchors plus all 20 named rapids as review-only visual points; both block editor geometry, solver windows, and catalog restationing until exact anchors and guide/geospatial review approve them.
  - [x] Clip the directed NHD chain into downstream-end review routes: `hydrography/full_reach_directed_route_clips.geojson` contains 20.5-mile and 21.0-mile Chili Bar downstream route candidates for Salmon Falls/Folsom anchor review, with centerline promotion, rapid restationing, editor binding, and solver windows disabled until the downstream source-mile basis and exact take-out are approved.
- [ ] B1 asset source survey and intake pipeline hardening.
- [ ] D1 compliant-tube Python reference model.
- [ ] D2 seat-load coupling into local tube deformation/freeboard.

## Definition of done (per river)

1. Full-reach corridor from the named put-in to take-out with source-recorded terrain, centerline, imagery, and gauge-derived flow bands.
2. Every catalog named rapid exactly stationed, feature-inventoried, editor-marked, with approved simulator runs at three flows (clean line + consequence line), reviewed against published descriptions.
3. Photoreal asset set promoted through the isolated gates; Nanite/Lumen/VSM enabled; performance measured on the E2 profiles.
4. Flexible-raft mechanics active with the D6 fixture suite green and rapid outcomes re-approved.
5. Lifelike guide-seat and river-eye captures at low/reference/high flow pass automated artifact checks plus human art, guide, geospatial, rights, and hazard-readability review — and the owner agrees they read as lifelike.
6. All evidence hash-locked, all tests green, all work committed and pushed.

## Standing execution rules

1. One task → commit(s) → push to both remotes, every time. Task granularity is the numbered items above (A1, B2-per-river, C3-per-rapid, D3, …); split further when a task exceeds ~a day of work.
2. Run the physics suite before/after every task; regenerate locks via generators; never hand-edit hashed artifacts.
3. New heavy binaries follow the LFS retention policy; run captures/videos go to the reports pattern with retention applied.
4. Anything requiring an owner decision (Fab license edge cases, ecology-analog acceptability, platform matrix, console investment, solver Option A/B) is written up as a short decision memo and **blocks only its own branch** — keep other tracks moving.
5. Update this plan and `TODO.md` checkboxes as tasks complete; date every status change, per repo convention.
