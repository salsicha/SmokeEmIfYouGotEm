# RaftSim Game Completion Plan

**Status:** active · **started:** July 19, 2026 · **authority:** this plan supersedes the
phase ordering in `docs/release-1.0-plan.md` while retaining its product, licensing,
platform, solver-honesty, and scope decisions.

## Completion goal

Ship RaftSim as a complete, free, open-source whitewater guide game: one continuous,
deep South Fork American campaign from Chili Bar to Salmon Falls, all 20 named rapids
at three flow bands, first-person guiding and AI crew commands, rescue and progression,
photoreal Unreal presentation, genuine live shallow-water physics, and a visibly
flexible inflatable raft that can overturn, fold, wrap, pin, and recover around rocks.

Futaleufu, Pacuare, Chilko, Colorado, and Zambezi remain bonus rapid slices and the
post-1.0 expansion path. They do not delay a complete South Fork 1.0.

Where authoritative terrain, bathymetry, bank, or hazard geometry is unavailable, the
project will generate deterministic, physically plausible infill. Generated infill must
be labeled `procedural_infill`, store its seed and inputs, blend continuously into known
data, pass hydraulic and gameplay validation, and never be represented as surveyed fact
or used for real-world navigation.

## Operating rules

1. Working game code, cooked data, art, audio, tests, and builds are deliverables.
   Planning/review paperwork is not a substitute for them.
2. Every milestone ends with its exit tests passing, one milestone commit, and a push to
   `origin`. Do not commit or push a partially completed milestone.
3. Preserve solver honesty: reference playback and visual conditioning never become
   shipping physics authority.
4. Prefer first-party or CC0 assets with manifest-recorded provenance. Every optional
   external asset has a committed procedural fallback.
5. Human review can record a launch follow-up, but cannot cause implementation to stop.
6. Generated geography is bounded by known DEM/imagery/hydrography, reproducible, and
   visibly/source-labeled in developer evidence even when it is accepted for gameplay.

## Milestones

### M1 — Flexible-raft and rock-contact vertical slice *(complete July 19, 2026)*

- Drive the procedural raft mesh from D1 compression/freeboard and D4 indentation,
  wrap, pin, and recovery state every frame.
- Add runtime rock-obstacle actors and bind their world transforms into the authoritative
  fixed-step flexible-raft solver.
- Put a deterministic rock garden in each runnable signature-rapid map.
- Add automation proving local deformation, stable topology, wrap/pin telemetry, and
  recovery toward the rest shape.
- Rebuild Unreal, regenerate affected maps, run the focused gameplay/physics suite, and
  capture a visible contact test.

**Exit:** a live raft visibly conforms around a contacted rock, the same contact changes
forces and wrap/pin telemetry, release recovers the shape, existing float/flip/run tests
remain green, and the milestone commit is pushed.

### M2 — Procedural geography completion pipeline *(complete July 19, 2026)*

- Implement a deterministic terrain/bathymetry infill generator using DEM, centerline,
  imagery masks, known cross-sections, flow, rapid class, and guide hazard annotations.
- Generate multi-scale missing detail: conditioned valley terrain, banks, thalweg,
  shelves, boulder fields, ledges, holes, wave trains, eddies, and shoreline breakup.
- Emit source/procedural authority masks, seeds, uncertainty, hashes, and Unreal import
  products; keep collision/solver and render geometry registered.
- Complete the South Fork full-reach corridor, filling every source gap procedurally.

**Exit:** the entire 49.1 km reach has continuous terrain, channel, collision, material
masks, and source-vs-infill provenance with no voids or unbounded discontinuities.

### M3 — Full South Fork hydraulics and named rapids *(complete July 19, 2026)*

- Author and cook all 20 named rapids at 900, 1,600, and 3,000 cfs.
- Add moving live-water windows, robust inflow/outflow forcing, wet/dry boundaries, and
  reach streaming without simulation resets.
- Bind scout eddies, lines, hazards, holes, waves, strainers/rocks, checkpoints, rescue
  zones, and outcome envelopes to the catalog.
- Improve genuine canonical solver coverage and behaviorally validate exceptions.

**Exit:** 60 rapid/flow combinations run without NaNs or mass blow-up and satisfy their
feature/outcome envelopes; a complete descent crosses window boundaries seamlessly.

### M4 — Continuous photoreal South Fork environment

- Build the World Partition gameplay map with Landscape/Nanite terrain, HLOD, streaming,
  source-conditioned materials, wet banks, sediment, boulders, vegetation, roads,
  bridges, access sites, sky, weather, and seasonal flow presentation.
- Replace near-field generic assets with South-Fork-specific first-party/CC0 assets.
- Add water depth/velocity optics, foam, aeration, spray, mist, sheets, droplets,
  underwater rendering, and raft/water interaction VFX.
- Produce guide-seat and river-eye captures in representative lighting and flow bands.

**Exit:** the full reach is visually continuous, has no placeholder/blockout assets in
the gameplay corridor, and passes automated artifact plus owner art/readability review.

### M5 — Guide, crew, raft, and rescue production quality

- Replace primitive crew with licensed first-party characters, clothing/PFD/helmet
  variants, Control Rig paddling, command reactions, bracing, high-side, falls, swimming,
  rope work, re-entry, and secondary physics.
- Finish visible raft fabric response: tube volume conservation, local buckling/folding,
  floor/thwart coupling, multi-rock contacts, surf loading, taco/lateral/stern wraps,
  pin/release, damage states, and calibrated material parameters.
- Complete player swimming, throw-line aiming, reach grabs, raft approach, re-entry,
  checkpoint policy, and crew safety feedback.

**Exit:** all core guide commands and rescue paths work with final animation, and the
raft's visible/contact response passes calibrated flip/wrap/pin fixtures and playtests.

### M6 — Complete game modes and progression

- Guided Descent career with sections, license tiers, medals, unlocks, stats, and full-run
  progression; Free Run; Training Eddy drills.
- Scouting, command wheel/hotkeys, HUD, subtitles, after-action review, ghosts/assists,
  settings, rebinding, save migration, pause, photo mode, credits, and legal screens.
- Accessibility: scalable UI/text, color-safe cues, shake/vignette controls, hold/toggle,
  difficulty/assist settings, and complete keyboard/gamepad navigation.

**Exit:** a new player can learn, complete the campaign, unlock all content, recover from
failures, and retain progress without editor/debug intervention.

### M7 — Production audio, camera, and presentation polish

- Layered MetaSounds for current, rocks, holes, waves, raft fabric, paddles, impacts,
  crew, rescue, canyon/riparian ambience, UI, and music; add occlusion and reverb zones.
- Finish first-person guide camera, comfort filter, optional Free Run chase camera,
  cinematics, transitions, loading, tutorial voice/text, and coherent art direction.
- Add deterministic weather/time variants used by gameplay and captures.

**Exit:** every player action and rapid state has final audiovisual feedback, the mix is
readable over river noise, and no debug/placeholder presentation remains.

### M8 — Validation, optimization, and content lock

- Convert the rapid review-run catalog into packaged-build regression automation.
- Run determinism, solver conservation, raft contact, rescue, save, input, accessibility,
  streaming, memory, hitch, and soak suites.
- Meet 1080p60 High on RTX 3060/M2 Pro and 1440p60 Epic on RTX 4070; solver stays within
  1.6 ms/tick and full-reach streaming has no hitch above 33 ms.
- Complete source/rights/attribution, hazard-readability, guide, and geospatial review;
  label all remaining procedural inferences honestly.

**Exit:** content is locked, all automated gates are green or have explicit honest
exceptions, performance budgets pass on target hardware, and there are no release-blocking
defects.

### M9 — Release candidates and platform QA

- Cut `release/1.0`; package signed/checksummed Windows x64 and macOS Apple Silicon builds.
- Test fresh-machine first run, keyboard/gamepad matrix, save migration, complete descents
  at every flow, replay determinism, Metal rendering, and Proton compatibility.
- Build GitHub Release, itch, Steam, press kit, trailer, screenshots, changelog, support,
  crash-reporting, and patch workflow artifacts.

**Exit:** `v1.0.0-rc1` packages pass fresh-machine QA and all distribution artifacts are
ready for final acceptance.

### M10 — Final acceptance and launch

- Run the owner/guide/art/geospatial acceptance pass, fix every release rejection, rerun
  affected gates, and tag the final build.
- Publish the GitHub release and hand off or publish the itch/Steam packages as account
  authority permits.
- Open the post-1.0 expansion sequence: VR, Futaleufu, Pacuare, Chilko, Colorado, then
  other rivers and multiplayer/voice evaluation.

**Exit:** `v1.0.0` is publicly downloadable, source and credits match the build, the patch
path is verified, and the completion goal can be marked complete.

## Progress ledger

| Milestone | State | Commit | Verification |
|---|---|---|---|
| M1 Flexible raft/contact slice | Complete | `2b3be122` | UE build; M1 1/1; river maps 5/5; physics 1,017/3 |
| M2 Procedural geography | Complete | `6b44af51` | UE build; geo 19/19; physics 1,021/3; byte-stable regeneration |
| M3 South Fork hydraulics | Complete | This milestone commit | 60/60 hydraulic cooks; M3 UE 2/2; physics 1,026/3 |
| M4 Photoreal environment | Next | — | — |
| M5 Characters/raft/rescue | Pending | — | — |
| M6 Game/progression | Pending | — | — |
| M7 Audio/presentation | Pending | — | — |
| M8 Validation/performance | Pending | — | — |
| M9 Release candidates | Pending | — | — |
| M10 Launch | Pending | — | — |

## Execution notes

### July 19, 2026 — M1 complete

- Exported per-segment D1 compression/freeboard and D4 contact indentation,
  normal, wrap, pin, and recovery state from the authoritative fixed-step adapter.
- Rebuilt the procedural tube and floor sections from that state every rendered frame
  using continuous spatial blending; topology stays stable while contacted fabric moves
  and locally loses radius.
- Added `ARaftSimRockObstacleActor` as the explicit world/solver authority boundary and
  bound nearby actors into D4 in raft-local coordinates. Regenerated all five runnable
  signature-rapid maps with four deterministic contact rocks each.
- Added `RaftSim.M1.FlexibleRaftVisualTracksContact`: a multi-segment wrap produces more
  than 5 cm of visible tube displacement, preserves topology/finite vertices, and returns
  to rest after release. Added map assertions for serialized D4 rocks.
- Captured `Saved/Screenshots/M1_FlexibleRaftWrap.png`, showing the live raft conforming
  around the solver-authority boulder. This is contact evidence, not a photoreal claim.
- Verification: Unreal Editor Mac Development build succeeded; M1 test 1/1; river maps
  5/5; isolated float/flip/water/crew/audio/score regressions green; full Python physics
  suite 1,017 passed / 3 dependency-path skips. A repeated all-in-one Unreal editor run
  also exposed an engine-internal MassEntity/TedsCore `pthread_rwlock_init` assertion;
  clean-process reports are the accepted gameplay evidence until that UE harness issue
  is resolved.

### July 19, 2026 — M2 complete

- Built `south_fork_procedural_geography_v1`, a deterministic source-conditioned
  completion pipeline over the adopted 49,077.732 m NHD axis. It samples all eight
  hash-locked 3DEP/NAIP source windows, blends their seven seams, and produces a
  4 m reach-local grid across a 512 m corridor with 1,582,959 finite terrain samples.
- Preserved official DEM terrain as the valley authority while explicitly labeling
  inferred bathymetry, thalweg, banks, shelves, seam conditioning, boulder fields,
  ledges, hole controls, wave-train controls, eddy pockets, and shoreline breakup.
  Separate source, procedural-infill, uncertainty, material, and feature masks report
  11.7 percent procedural content; the manifest says it is not surveyed and must not be
  used for navigation.
- Bound all 20 stationed rapid annotations into the generator and emitted 115 stable,
  seeded boulders. Solver, render, and collision consume the same canonical elevation
  field rather than independently conditioned copies.
- Exported thirteen overlapping Unreal tiles with globally normalized 16-bit heights,
  packed authority/uncertainty/feature masks, material masks, and EPSG:3857 curvilinear
  control points. Render and collision paths/hashes are identical for every tile and
  overlap rows compare byte-for-byte.
- Verification: a second generation kept the manifest and compressed-grid SHA-256
  hashes unchanged; focused geography/source/stitching/stationing tests passed 19/19;
  Unreal Editor Mac Development built successfully; the full physics/content suite
  passed 1,021 tests with 3 expected optional-dependency path skips in 10m18s.

### July 19, 2026 — M3 complete

- Authored all 20 named South Fork rapid windows from the catalog's 105 guide-facing
  subfeatures, M2 canonical geography, and deterministic interpreted bed controls.
  Cooked every rapid through the genuine first-party order-2 HLL finite-volume solver
  at 900, 1,600, and 3,000 cfs with fixture calibrations and reference playback off.
- Rejected two intermediate full-matrix runs rather than weakening validation. The
  investigation found an over-constrained inlet and then source-DEM depressions outside
  bankfull width being flooded as false side channels. The final conditioning preserves
  M2 bathymetry in-channel, raises only out-of-channel banks, and restores authored
  stage-plus-velocity inlet behavior in the C++ solver.
- All 60/60 final combinations are finite and pass wet-area, nonnegative-depth, bounded
  velocity, bounded volume, positive inlet/outlet, bounded rapid discharge response,
  and every catalog subfeature envelope. Peak speed spans 2.29–14.28 m/s, final/initial
  volume 0.982–0.993, and solver mass drift remains below 1.85 percent.
- Added per-rapid scout eddies, three flow-specific lines, hazards, entry/exit
  checkpoints, rescue zones, and outcome envelopes. Added a deterministic 49,077.732 m
  procedural transit seed at all three flows so the gaps between named cooks still run
  through the genuine live solver; its arrays reproduced byte-for-byte across three
  generations and remain explicitly inferred/not for navigation.
- Added globally stationed Unreal moving-water crops, authored full-edge inflow/outflow
  parsing, transmissive cut edges, overlap depth/velocity transfer, solver-clock
  preservation, handoff telemetry, and rejection of non-overlapping resets. Corrected
  out-of-window sampling and last-cell bilinear interpolation while retaining legacy
  hydraulic-crux recentering for fixed rapid maps.
- Verification: standalone C++ solver build/state-replacement test passed; Unreal Editor
  Mac Development built successfully; both `RaftSim.M3` automation gates passed against
  named-rapid and full-reach transit data; focused M3/editor tests passed 8/8; repository
  guards passed; full physics/content suite passed 1,026 tests with 3 expected
  optional-dependency-path skips in 13m59s.
