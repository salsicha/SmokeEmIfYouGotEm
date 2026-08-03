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

Futaleufu, Pacuare, Chilko, and Colorado remain bonus signature-rapid slices.
Zambezi is the separate, full-corridor `reference_free_run` from the Boiling Pot
to Mukuni Beach. All five remain the post-1.0 production-fidelity expansion path
and do not delay a complete South Fork 1.0.

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

### M4 — Continuous photoreal South Fork environment *(complete July 19, 2026)*

- Build the World Partition gameplay map with Landscape/Nanite terrain, HLOD, streaming,
  source-conditioned materials, wet banks, sediment, boulders, vegetation, roads,
  bridges, access sites, sky, weather, and seasonal flow presentation.
- Replace near-field generic assets with South-Fork-specific first-party/CC0 assets.
- Add water depth/velocity optics, foam, aeration, spray, mist, sheets, droplets,
  underwater rendering, and raft/water interaction VFX.
- Produce guide-seat and river-eye captures in representative lighting and flow bands.

**Exit:** the full reach is visually continuous, has no placeholder/blockout assets in
the gameplay corridor, and passes automated artifact plus owner art/readability review.

### M5 — Guide, crew, raft, and rescue production quality *(complete July 19, 2026)*

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

### M6 — Complete game modes and progression *(complete July 19, 2026)*

- Guided Descent career with sections, license tiers, medals, unlocks, stats, and full-run
  progression; Free Run; Training Eddy drills.
- Scouting, command wheel/hotkeys, HUD, subtitles, after-action review, ghosts/assists,
  settings, rebinding, save migration, pause, photo mode, credits, and legal screens.
- Accessibility: scalable UI/text, color-safe cues, shake/vignette controls, hold/toggle,
  difficulty/assist settings, and complete keyboard/gamepad navigation.

**Exit:** a new player can learn, complete the campaign, unlock all content, recover from
failures, and retain progress without editor/debug intervention.

### M7 — Production audio, camera, and presentation polish *(complete July 19, 2026)*

- Layered runtime sound synthesis/MetaSound-ready routing for current, rocks, holes,
  waves, raft fabric, paddles, impacts, crew, rescue, canyon/riparian ambience, UI, and
  music; add occlusion and reverb sends.
- Finish first-person guide camera, comfort filter, optional Free Run chase camera,
  cinematics, transitions, loading, tutorial voice/text, and coherent art direction.
- Add deterministic weather/time variants used by gameplay and captures.

**Exit:** every player action and rapid state has final audiovisual feedback, the mix is
readable over river noise, and no debug/placeholder presentation remains.

### M8 — Validation, optimization, and content lock *(complete July 19, 2026)*

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
| M3 South Fork hydraulics | Complete | `aa610a6c` | 60/60 hydraulic cooks; M3 UE 2/2; physics 1,026/3 |
| M4 Photoreal environment | Complete | `0032554d` | UE build; M4 3/3; South Fork 144/144; HLOD 20/20 |
| M5 Characters/raft/rescue | Complete | `3d08efaa` | UE build; M5 4/4; rendered rescue 1/1; P2/P3/crew safety green |
| M6 Game/progression | Complete | `77ecbf49` | UE build; M6 5/5; isolated Metal menu/HUD; score/save and rescue regressions green |
| M7 Audio/presentation | Complete | `223a111f` | UE build; M7 4/4; real CoreAudio mix; isolated Metal presentation/full-reach captures; P3 audio and M6 UI regressions green |
| M8 Validation/performance | Complete | `54cca9df` | Mac package/signature; 60/60 packaged rapid cases; 1080p High/75% p95 15.331 ms, zero hitches; M8 3/3; physics 1,040/3 |
| M9 Release candidates | In progress | — | M9B.1 architecture and M9B.2 production roster are complete. M9B.3 has accumulated technical upgrades across PPE, characters, raft deformation, contact/wrap/pin water, terrain, foliage, rocks, lighting, VFX, and presentation, but the full scene remains below the requested photoreal bar. V9 stock 3D FLIP Splash/Hose reuse was rejected and removed because neither produced a visible liquid body. V10 now supplies a project-owned six-frame closed implicit-volume mesh cache: it is visibly attached in normal and waterless-isolation captures, evolves at 0.12-second cadence, exposes 104.89 cm depth, changes no physics/gameplay authority, and passes its local technical review. It remains opt-in, default-off, photoreal-rejected, and unpromoted pending named water-VFX art and qualified South Fork guide approval. Exact-current local validation is green: M4 v431 4/4, M5 v432 5/5, M7 v433 4/4, M8 v434 4/4, reconciled fail-closed M9 v437 5/5, and v436 full matrix 1,146 passes / 3 expected skips / 1 intentional historical-V42 mismatch / 0 unexpected failures. Shipping/package evidence remains historical and non-promotable. Character fidelity/mocap, raft/water/terrain/canopy art, named owner/guide/art/geospatial/legal review, fresh-device input, external platform/hardware execution, signing/notarization, approved media, distribution accounts, clean immutable qualification, and promotion remain open. M9 stays fail-closed, uncommitted, and unpushed. |
| M10 Launch | Pending | — | — |

## Execution notes

### July 19, 2026 — M1 complete

- Exported per-segment D1 compression/freeboard and D4 contact indentation,
  normal, wrap, pin, and recovery state from the authoritative fixed-step adapter.
- Rebuilt the procedural tube and floor sections from that state every rendered frame
  using continuous spatial blending; topology stays stable while contacted fabric moves
  and locally loses radius.
- Added `ARaftSimRockObstacleActor` as the explicit world/solver authority boundary and
  bound nearby actors into D4 in raft-local coordinates. Regenerated the original five
  compact signature-rapid maps with four deterministic contact rocks each; the later
  source-scale Zambezi reference corridor uses its separate generator.
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

### July 19, 2026 — M4 complete

- Upgraded the full-reach geography to fold-safe, smoothed curvilinear frames and
  registered eight source-window far-field DEM/imagery patches by nearest global
  station ownership. Regenerated dependent South Fork geography and hydraulic products
  so render, collision, live water, and procedural provenance remain registered.
- Authored the 49.1 km World Partition gameplay map with thirteen 64,512-triangle
  Nanite terrain tiles, 39 flow-band water meshes, eight far-field patches, 20 terminal
  instanced HLOD cells, curved streaming coordinates, wet-bank response, 115 hydraulic
  boulders, 5,121 non-colliding bank rocks, and 72 bridge/access infrastructure actors.
- Added source-conditioned per-tile and far-field macro albedo, CC0 triplanar ground and
  rock detail, depth/velocity water optics, deterministic sub-grid standing waves,
  hydraulic foam/aeration, 255 spray/mist instances, and runtime pooled water-contact
  VFX without making the presentation layer authoritative over the shallow-water solver.
- Replaced near conifers with full-geometry CC0 Poly Haven pine variants and created
  project-owned Ponderosa pine/interior live-oak canopy fallbacks from first-party
  generated source art. The final map contains 18,325 detailed-corridor and 179,630
  far-field foliage instances with deterministic sparse-bank understory infill.
- Added Chili Bar, Meat Grinder, Troublemaker, Coloma bridge, and Salmon Falls
  guide/river-eye captures. Automated artifact, map, HLOD, VFX, source/procedural label,
  and readability checks pass. The build manifest deliberately leaves the subjective
  `owner_art_and_readability_review_passed` field false until the owner accepts the
  captures; under operating rule 5 this is a recorded launch follow-up, not an
  implementation stop or a claim that the captures are real-world navigation imagery.
- Corrected curved river inverse mapping to solve the same interpolated-normal ruled
  corridor used by forward mapping, restoring sub-centimetre station/lateral round trips.
  Verification: Unreal Editor Mac Development build succeeded; `RaftSim.M4` passed 3/3;
  all South Fork Python tests passed 144/144; Ruff lint/format checks passed; HLOD setup
  and build completed 20/20 with zero errors and deterministic package hashes.

### July 19, 2026 — M5 complete

- Replaced all sphere/cylinder crew assembly with `ARaftSimCrewAvatarActor`, a
  first-party MIT procedural organic mesh and deterministic joint rig. Five live
  avatars now carry splash clothing, four PFD variants, helmets, paddles, shadows, and
  final poses for idle, forward/back/turn strokes, brace, both high sides, falling,
  swimming, reach, rope throw, and re-entry. The fallback ships without a third-party
  mannequin license or raw character asset; it is not represented as a photogrammetric
  human.
- Bound the guide plus passenger masses into the authoritative D1-D4 seat solve. Crew
  commands now change the same mass distribution that their animation depicts, while
  command latency/cadence and the existing guide propulsion tests remain intact.
- Added explicit rescue targeting, camera aim validation, distinct 1.2 m reach, 2.0 m
  paddle-grab, and 8.0 m throw-line envelopes, visible sagging rope, elapsed-time throw
  flight/pull, deliberate tube-side re-entry, swimmer control, guide detach/reboard,
  stable feedback codes, and a four-second failed-rescue checkpoint reset/field repair.
  Keyboard/mouse and gamepad rescue mappings are installed in shipping runtime code and
  mirrored in the editor asset generator.
- Upgraded the raft mesh from uniform shrinkage to area-preserving reciprocal-axis tube
  buckling. Authoritative wrap/pin state now drives taco lift, thwarts and the
  self-bailing floor follow the deformation field, and persistent crease, abrasion,
  puncture, critical damage, pressure loss, and repair states feed back into effective
  contact radius and buoyancy.
- A rendered offscreen run caught a latitude-ring roundoff defect that NullRHI could not:
  fractional power of a tiny negative `sin(pi)` produced NaN vertices. The generator now
  clamps the domain, every avatar gate inspects its procedural vertex buffer and
  transforms, and both the solver adapter and actor reject non-finite transforms at the
  renderer boundary.
- Evidence is recorded in `Content/RaftSim/Crew/m5_production_quality_manifest.json` and
  `Saved/Screenshots/MacEditor/M5_RescueProduction.png`. The capture is implementation
  evidence for crew/raft/rope readability, not a claim of final photogrammetric humans.
- Verification: Unreal Editor Mac Development build succeeded; `RaftSim.M5` passed 4/4;
  the Metal offscreen `RuntimeRescueLoop` passed 1/1 with no renderer ensure; P2 passed
  3/3, P3 passed 3/3, M1 passed 1/1, Milestone11 crew safety passed 1/1, and the focused
  flexible-raft Python suite passed 89/89.

### July 19, 2026 — M6 complete

- Added a version-3 migrated save/profile schema with Guided Descent, Free Run, and
  Training Eddy modes; four continuous South Fork career sections plus the full
  descent; license tiers, medals, unlocks, aggregate stats, best times, checkpoints,
  settings, completed drills, and best-route ghosts. Free Run deliberately exposes all
  maps without weakening the career unlock rules.
- Built the complete runtime front end and in-run shell in programmatic UMG: mode and
  scenario selection, briefings and locked states, keyboard/gamepad focus, settings,
  assists, accessibility controls, credits/legal notice, status/progress/rescue HUD,
  scouting, crew command wheel/hotkeys, subtitles, pause/restart/menu flows, paused photo
  capture, and after-action route review. Saved keyboard overrides preserve gamepad
  mappings, and shared gamepad buttons are context-dispatched instead of double-bound.
- Added measured Training Eddy drills for paddle/stop calls, scouting/high-side response,
  and a real swimmer recovery. Section sessions restore exact saved transforms and
  seed a fresh live-water window before ordinary streaming resumes; career scoring now
  follows the curved river station authority rather than world +X.
- Added a non-colliding best-route ribbon and persistent route samples, and retained the
  source/procedural distinction in the scout board: inferred geography is explicitly
  an amber gameplay cue and never navigation guidance.
- Rendered QA exposed two defects that headless tests did not: constructing UMG only in
  `NativeConstruct` left empty widgets, and auto-size plus auto-wrap collapsed dynamic
  training text on portrait displays. Both widgets now build in `RebuildWidget` and use
  explicit wrapped text regions. The accepted captures are
  `Saved/Screenshots/MacEditor/M6_MainMenuWidget.png` and
  `Saved/Screenshots/MacEditor/M6_GameShellWidget.png`.
- Verification: Unreal Editor Mac Development build succeeded; the complete
  `RaftSim.M6` suite passed 5/5, including a real full-reach World Partition session;
  isolated Metal offscreen menu and runtime-shell tests passed with legible captures;
  `RaftSim.P3.RunScoresAndSaves` and `RaftSim.M5.RuntimeRescueLoop` passed. Combining
  multiple rendered PIE fixtures in one editor process still trips an engine-internal
  `SceneViewport` teardown assertion, so rendered fixtures remain isolated while the
  complete suite is accepted under NullRHI.

### July 19, 2026 — M7 complete

- Replaced the silent procedural-audio stub with eight continuously queued, project-owned
  48 kHz PCM layers for river bed, rapid hydraulics, foam/spray, paddle catches,
  raft-fabric/impact response, crew/rescue feedback, canyon ambience, and restrained
  adaptive music. Live flow, Froude/aeration, rock contact, paddle/command/high-side,
  swimmer/rescue, run progress, weather, and canyon enclosure drive the mix; voice
  activity ducks river noise, while per-layer low-pass filtering and manual reverb sends
  preserve readability. The deterministic synthesis is the cooked offline-safe shipping
  fallback and is not misrepresented as field-recorded audio or a binary MetaSound asset.
- Added a runtime presentation director with clear-morning, overcast-afternoon, and
  storm-dusk presets. It binds or creates the actual sun, skylight, exponential height
  fog, and volumetric cloud actors, blends lighting/atmosphere, and feeds wetness,
  enclosure, and reverb into the audio mix without altering physics authority.
- Finished the first-person motion/FOV comfort response, a four-second seated intro,
  and a Free Run-only chase camera. Rendered QA caught a boom-anchor test that allowed
  the active view to inherit an inverted raft transform; the final camera uses an
  explicit world-space transform, samples live surface height and downstream flow, and
  is asserted through the player camera manager above water with a level horizon.
- Added weather/camera controls, scenario and run-complete transitions, loading state,
  project-owned menu confirmation audio, tutorial/crew captions, explicit text wrapping,
  and production-language run telemetry. The accepted evidence is
  `Saved/Screenshots/MacEditor/M7_PresentationWidget.png`,
  `Saved/Screenshots/MacEditor/M7_Presentation.png`, and
  `Saved/Screenshots/MacEditor/M7_FullReachPresentation.png`.
- Verification: Unreal Editor Mac Development build succeeded; the complete headless
  `RaftSim.M7` suite passed 4/4; isolated Metal runtime-presentation and full-reach tests
  passed; `ProductionAudio` passed through the real 48 kHz CoreAudio mixer; and
  `RaftSim.P3.RunAudioReactsToFlow`, `RaftSim.M6.MainMenuRender`, and
  `RaftSim.M6.RuntimeShell` remained green. The World Partition fixture remains sorted
  last in combined automation, and rendered fixtures remain isolated to avoid the known
  engine-internal PIE/viewport teardown race documented in M6.

### July 19, 2026 — M8 complete

- Staged the complete JSON/GeoJSON/NumPy runtime-data tree into packaged builds and added
  a package-aware resolver, so the shipping C++ water solver loads the same hash-checked
  South Fork hydraulic fields as editor validation. The final app contains 611 staged
  runtime-data files, boots without repository access, and reports no missing runtime
  data, material fallback, deployment, or linker warnings during cook.
- Converted the 20-rapid catalog into an in-package 60-case regression across all three
  flow bands. The final Mac Development package passed 60/60 with the compiled live
  solver, deterministic repeat checks, accepted field hashes, and rapid feature
  envelopes; worst case-average solver cost was 0.359 ms and worst individual step was
  0.401 ms against the 1.6 ms budget.
- Removed per-tick gameplay JSON capture, added direct curvilinear field sampling, kept
  water/raft physics at 60/120 Hz, refreshed visible water at 15 Hz on a 3 m mesh, and
  instrumented solver, game, render, GPU, wall-clock, hitch, resolution, quality, and
  memory measurements. Accurate live-water swimmer drift exposed a stale capsize-point
  re-flip assumption; re-flip now occurs at the guide's current downstream position and
  the isolated flip/reseat regression passes again.
- A delayed packaged GPU profile isolated stock volumetric-cloud tracing and real-time
  skylight capture as the dominant costs. Bounded temporally reconstructed cloud samples,
  a cached skylight, and stable sun transforms retain volumetric weather while meeting
  the frame budget. The exact final package passed a 30-second 1920x1080 High/75% soak
  on Apple M5: 2,071 frames, 15.331 ms workload p95, 15.915 ms wall-clock p95, zero
  hitches above 33 ms, 0.286 ms average solver time, 0.614 ms maximum solver step, and
  6,119.6 MB peak used physical memory. A post-M8 presentation audit later proved this
  measurement was invalid for visual qualification because a missing cooked-field
  elevation datum placed the raft and camera below the terrain. M9 replaces it with a
  corrected above-water Shipping measurement; the M8 number remains here only as
  historical execution context.
- Disabled OpenXR for the flat-screen 1.0 scope, persisted production material usage
  flags, explicitly cooked all release maps, verified the final self-contained app's
  ad-hoc development signature, and locked source/procedural/rights/release-scope facts in
  `Content/RaftSim/Production/m8_content_lock_manifest.json`. Procedural geography remains
  seeded, labeled, not surveyed, and not for navigation.
- Verification: final Mac package and signature valid; final packaged rapid regression
  60/60; final `RaftSim.M8` automation 3/3; isolated live-water flip/reseat regression
  green; repository guards green; full physics/content suite 1,040 passed with 3 expected
  optional PyClaw/GeoClaw dependency-path skips. M2 Pro, RTX 3060/4070, Windows/Proton,
  and named human guide/geospatial/art/legal signoff were unavailable locally and remain
  explicit M10 acceptance exceptions rather than fabricated completions.

### July 19–20, 2026 — M9 in progress

- Cut `release/1.0`, locked the candidate version to `1.0.0-rc1`, and implemented a
  release-audit/archive/checksum tool plus macOS and Windows packaging lanes. The Mac
  lane discovers the built executable from the bundle plist, validates the complete
  staged-data tree, signs every nested binary with one identity, and distinguishes a
  locally valid development signature from a notarizable Developer ID distribution
  signature. CI requires Developer ID signing, notarization, stapling, Gatekeeper
  assessment, Authenticode, and Proton evidence rather than silently weakening them.
- Added packaged candidate QA covering the Shipping/version/live-solver contract, 14
  keyboard/gamepad actions, legacy migration and future-version save protection, all 60
  rapid/flow combinations, and deterministic complete-reach cases at 13 stations and
  three flow bands. Added stdout/base64 evidence extraction so a sandboxed Mac app can
  return machine-readable reports without relying on inaccessible container paths.
- Hardened performance validation to require the exact full-reach map and travel there
  in-game before measurement. A presentation audit exposed that cooked hydraulic crop
  elevations had lost their source datum, placing the raft and chase camera more than
  100 m below the terrain; the earlier 75% preflight was therefore discarded. Runtime
  samples now restore transit and named-rapid elevation datums, editor loads prefer
  authoritative repository data, and automated camera/water-clearance guards prevent
  recurrence. The corrected local Metal Shipping preflight passed above water on
  `L_SouthForkAmerican_FullReach` at 1920x1080 High/60%: 2,004 frames, 15.127 ms
  workload/GPU p95, 16.462 ms wall-clock p95, zero hitches above 33 ms, 0.308 ms average
  and 0.573 ms maximum solver cost, and 5,238.6 MB peak used physical memory.
- Added an isolated packaged fresh-profile harness that starts from an unused sandbox
  user directory, verifies pristine progression/default bindings/current save schema,
  persists the initial slot, starts the first Free Run, reloads from disk, and proves the
  round trip. All nine first-run gates pass in the signed Shipping app.
- Refined the reproducible environment path rather than substituting untracked media:
  the live solver patch now keeps a stable three-metre river-coordinate UV scale through
  recentering, speed-derived whitening is bounded so foam remains hydraulic, and the
  terrain blend exposes more licensed soil/rock detail beneath its source-conditioned
  aerial macro. `Saved/Screenshots/MacEditor/M7_FullReachEnvironment.png` is now captured
  directly from the PIE game viewport without HUD and its save is asserted by automation.
  The resulting image is clearer and more inspectable, but it still shows procedural
  people, raft surfaces, canopy repetition, and coarse terrain forms; it is explicitly
  not accepted as final photoreal marketing material.
- Replaced the generated pine/live-oak two-card proxies with three radial photographic
  planes, retained full 1K source/platform texture data and mip chains, reduced the
  pale emissive/card-wall response, and added seeded nonuniform crown variation. A
  renderer-enabled `RaftSim.M7.ZFullReachPresentation` run passes and shows a more
  view-stable near-bank canopy, but visual review still rejects the coarse beige terrain,
  repeated distant conifers, flat water, and procedural characters/raft as final
  photoreal marketing media.
- Corrected the full-reach terrain microdetail scale to the licensed Poly Haven sources'
  physical widths (150 cm rock ground and 200 cm forest ground), requiring their albedo,
  normal, and roughness maps together. The water material now wraps its moving UVs before
  isolating the South Fork tile in the shared normal atlas, so it no longer samples the
  neighboring river tiles. These changes affect shading only: the live solver mesh stays
  the sole water-geometry and hydraulic-feature authority.
- Corrected the Single Layer Water volume coefficients to Unreal's inverse-centimetre
  units. The previous red absorption implied an approximately four-centimetre attenuation
  length and forced an opaque cyan volume; the calibrated coefficients attenuate over
  metres, reduce green scattering and riverbed transmission, and retain a restrained
  sky reflection. Detailed-corridor terrain now blends 66 percent source imagery and the
  far field 78 percent, preserving aerial-scale geographic colour while reviewed ground
  and rock textures supply missing microdetail. The renderer-enabled gameplay capture
  now reads as darker olive/neutral water with visible hydraulic texture rather than a
  tropical pool. It remains procedural and is still rejected as final photoreal media.
- Broke up the far-field grid deterministically with DEM-gradient slope correction,
  nonuniform scale, yaw/pitch/roll, river exclusion after jitter, and six instanced mesh
  groups. The Shipping mix keeps 90 percent of conifers and 92 percent of broadleaf trees
  on three-plane photographic cards, with a bounded minority of reviewed full-geometry
  trees, after the more aggressive geometry mix exceeded the editor frame and memory
  budgets. Jitter is bounded to 0.46 DEM cells and uses stable seeded identities. The
  final M7 capture has more coherent water wrinkles and less rigid repetition, but smooth
  gold distant terrain, recurring conifer silhouettes, broadleaf alpha treatment, and
  procedural raft/crew assets still fail photoreal marketing acceptance.
- Made the World Partition generator cross-process deterministic rather than merely
  deterministic inside one editor session. Every project actor receives a stable GUID
  and a stable object name (the authority Unreal uses for external package paths), and
  the editor-created minimap is replaced with a stable project-owned identity. Two
  separate full-reach builds each validated 163 identities and produced the exact same
  347-line actor-package status: 183 superseded tracked paths, one modified tracked
  package, and 163 generated paths with no additions or removals between runs. The
  HLOD commandlet then rebuilt all 20/20 terminal cells with zero errors; repeating that
  build kept the same package set (163 superseded tracked, 21 modified tracked, and 163
  generated paths) and refreshed the checked-in package hashes. The rebuilt editor
  target and all three `RaftSim.M8` content-lock tests pass.
- Upgraded the source-authoritative procedural raft/crew path without replacing its
  physics or animation authority. The raft now has textured commercial tube/floor
  materials and an eight-sided swept safety-yellow perimeter grab line that follows the
  same D4 deformation field through contact, wrap, and pin. Ten-by-fourteen organic body
  meshes and an eight-by-twelve rounded foam recipe now give each avatar front, rear,
  side, and shoulder PFD coverage, belt, buckle, rear webbing, neck, helmet rim and
  retention straps, hands, and boots. Four deterministic body profiles break up the
  five-person silhouette, and the guide has dedicated yellow PFD/helmet treatment. The
  six coloured PFD shapes share one animated procedural component and the two helmet
  straps share another, retaining the visible layers at 25 components per avatar instead
  of paying for 31 independent draw-call-bearing parts. Spray mist was reduced and
  reshaped to remove the opaque white-disc artifact. Focused flexible-raft tests assert
  rigging topology/deformation, and the renderer-enabled M5 suite asserts the complete
  gear stack and passes 4/4. The rescue and isolated M7 full-reach captures pass. This is
  a material-readability improvement, not acceptance of the procedural people or
  environment as photoreal marketing imagery.
- Completed a second draw-call-neutral character pass by batching the base head, nose,
  ears, sclera, irises, brows, and mouth as eleven submeshes in the existing head
  component. Four deterministic skin tones use vertex colour and a project-owned
  subsurface/pore-detail face material; a three-strip open helmet rim replaces the prior
  closed visor-like form. The first Shipping cook correctly rejected an invalid face
  shader component mask; selecting the vertex-colour alpha output fixed the material,
  after which the editor build, rendered M5 suite (4/4), isolated M7 full-reach capture,
  M8 (3/3), M9 (3/3), and the corrected full Shipping cook all passed. The frontal rescue
  evidence now exposes recognizable facial features on all five avatars, but the meshes
  remain deliberately recorded as procedural and below final photoreal character-art
  acceptance.
- Completed a third draw-call-neutral character presentation pass in the current editor
  source. Project-owned synthetic 1024×1024 micro-albedo and tangent-space normal maps
  feed only vertex-alpha-marked skin through the existing subsurface face material. The
  base head is now a 20-profile-ring by 28-side anatomically conditioned mesh; eyelids
  and paired nostrils raise the batched head contract from eleven to seventeen submeshes.
  The helmet is now a 10×24 front-cut top/back shell with extended rear coverage rather
  than a closed ellipsoid. The editor target and renderer-enabled M5 suite pass 4/4, and
  the new frontal capture removes the solid visor failure. Direct image review still
  rejects the people as photoreal: skin response, facial anatomy, clothing, and helmet
  construction remain visibly procedural. A fresh v3 Shipping cook now contains these
  changes, compiles the face material for Metal SM5 and SM6, and passes local packaged
  functional and performance diagnostics. Representative-art review still rejects it.
- The correctly sandbox-signed v3 app and the previously qualified v2 app both currently
  stall inside the host macOS App Sandbox service before Unreal `main`. This proves a
  host-state launch problem rather than a v3 game-binary regression, but it also prevents
  claiming a sandboxed current-host or fresh-machine pass. A separately signed v3 clone
  with identical packaged game/content bytes and no App Sandbox entitlement passed 60/60
  rapid cases, all 14 input actions, save guards, 39/39 full-reach cases, and all nine
  unique-UserDir first-profile gates. The archive retains the valid sandbox-only Apple
  Development signature; the diagnostic clone is not the distributed artifact.
- The same current v3 Shipping bytes passed the canonical 1920×1080 High/60% Metal soak
  on the diagnostic clone: 3,748 sampled frames, 16.305 ms workload/GPU p95, 16.749 ms
  wall-clock p95, zero hitches above 33 ms, 0.339 ms average and 0.588 ms maximum solver
  cost, and 5,275.8 MB peak used physical memory. App Sandbox startup and target-hardware
  repeatability remain open rather than being inferred from this local result.
- The prior face-batched v2 Shipping rebuild containing the live-water, calibrated
  terrain/water material, optimized far-field, raft, initial batched facial/crew geometry,
  face material, and spray changes
  passed the 1920x1080 High/60% full-reach Metal soak: 3,730 sampled frames, 16.382 ms
  workload/GPU p95, 16.781 ms wall-clock p95, zero hitches above 33 ms, 0.336 ms average
  and 0.557 ms maximum solver cost, and 5,271.0 MB peak used physical memory. The isolated rendered M7 full-reach
  presentation/environment test, rendered M5 rescue loop, flexible raft/contact tests,
  and UV-scale water-surface test pass. A Development editor soak remained slightly over
  the frame target and is retained as diagnostic evidence; the packaged Shipping soak is
  the release-performance gate and passed.
- Performance validation rejected the first 31-component layered-crew variant: in a
  controlled old/new run, the accepted binary passed at 16.412 ms p95 and the new binary
  missed at 17.590 ms. Batching the six PFD shapes and bilateral helmet straps reduced
  the avatar to 25 components without changing the reviewed silhouette. The exact new
  Shipping build then passed two cooled 60-second isolated runs at 16.467 and 16.377 ms
  p95, with 3,702 and 3,727 frames and zero hitches in either run. Its immediate-post-cook
  sample missed at 17.458 ms; subsequent deliberately hot-order diagnostics also made
  both old and new binaries miss, confirming that thermal order is material on this
  passively cooled system. All failed samples remain recorded rather than discarded.
  A face-enabled replacement candidate then missed at 17.656 ms immediately after its
  cook, passed a cooled run at 16.424 ms, narrowly missed a short-order repeat at 16.705
  ms, and passed the final fully cooled run at 16.382 ms; all four reports are retained
  as superseded thermal-history evidence. The cooled passes close the earlier local
  regression concern; named target hardware and platform evidence remain open.
- The superseded local v3 Mac archive is 1,273,817,541 bytes with SHA-256
  `a8c0cc1cc7e728bac560226365e6a3feaa84a62fa1da99f75f3636774592f51b`; its 641
  package files include all 611 runtime-data files. Its Apple Development signature is
  valid but explicitly non-notarizable. Diagnostic-clone packaged rapid QA passed 60/60, packaged M9 QA
  passed all 14 input actions, save guards, and 39/39 full-reach cases, fresh-profile QA
  passed all nine gates, final M8 and manifest-sensitive M9 editor automation each passed
  3/3, and the full Python suite passes 1,054 tests with 3 expected optional-dependency
  skips. Focused release-tool
  Ruff and Black checks pass; broad project-wide formatting remains outside this
  milestone's established baseline.
- This evidence is intentionally recorded as non-promotable because the package was
  built from the M8 base commit plus the uncommitted M9 worktree; its App Sandbox startup
  is also not locally qualified because of the reproduced host service stall. M9 remains open until
  the same clean milestone commit has immutable macOS Developer ID/notarization,
  Windows x64/Authenticode/RTX, Linux Steam/Proton, and fresh-machine first-run evidence.
  Approved representative screenshots/trailer/press-kit media and authenticated
  GitHub/itch/Steam publication authority are also still missing; the current captures
  are not accepted as final photoreal marketing material.
- Audited the installed UE 5.8 MetaHuman path in an isolated temporary project. The
  factory created and saved a 739 KB `MetaHumanCharacter` asset, preview assembly built
  the base face and body, and the editor spawned its preview actor. The resulting body,
  face, and materials were transient gray editor objects. The production build gate
  correctly returned false because the character was not rigged; engine diagnostics
  also confirmed that MetaHuman Optional Content and texture-synthesis data are absent.
  Epic's production assembly path additionally requires downloaded high-resolution
  texture sources, so copying the preview geometry is explicitly rejected.
- Added a production-character adapter boundary to `ARaftSimCrewAvatarActor`. It selects
  deterministic guide/crew soft-class slots, accepts only wrappers implementing the
  `RaftSimCrewProductionVisual` appearance/pose contract, hides fallback geometry only
  after a valid child actor spawns, and restores the procedural path on any missing or
  invalid dependency. The editor target compiles with this boundary. The actual five
  optimized character wrappers remain open until MetaHuman Creator Core Data, Epic
  service rigging/textures, wardrobe/PPE art, and rendered/performance acceptance are
  available; the adapter alone is not a photoreal claim.
- Added production-raft fittings without splitting visual authority from the D4 solver:
  four D-rings, weld/protection bands, inflation valves, carry handles, steel hardware,
  and rubber detail all use the same deformation evaluator as the 18-segment outer tube,
  floor, and safety rigging. Focused M1 flexible-raft automation passes 1/1, rendered M5
  passes 4/4, and rendered M7 passes 1/1. The result reads more clearly as a commercial
  inflatable raft, but the source-authoritative mesh and material treatment remain below
  final photoreal art acceptance.
- Upgraded all eight source-backed South Fork far-field windows to V14. Geometry now uses
  513×513 samples from the registered USGS 3DEP products, macro colour is independently
  retained at 1024×1024 rather than being collapsed to the mesh grid, and the colour mix
  is 84 percent registered USDA NAIP imagery and 16 percent procedural gap/detail support.
  The generated meshes use Nanite; UV-sampled macro colour drives vertex shading and
  ecology; and a stride of two preserves the reviewed foliage population budget despite
  the denser terrain grid. Two deterministic half-probability candidates per ecology cell
  preserve expected population while allowing gaps and pairs instead of forcing a
  plantation-like one-tree-per-cell lattice.
- Regenerated the full-reach map and dependent registered assets. The build contains 13
  terrain tiles, 39 water tiles, eight far-field patches, 838,656 detailed-terrain
  triangles, 927,000 water triangles, 3,209,440 Nanite far-field triangles, 18,325
  detailed-corridor foliage instances, 176,124 clustered far-field foliage instances,
  115 hydraulic boulders, 5,121 bank rocks, 255 spray/mist instances, and 72
  infrastructure actors. Focused Python/source tests pass 13/13, the editor target and
  full source rebuild succeed, rendered M7 passes 1/1 with only Unreal's standard motion
  vector warning, M8 passes 3/3, and the latest M9 manifest/QA/save suite passes 3/3 with
  no warnings or errors.
- Made far-field foliage obey the existing High=0.75/Epic=1.0 density policy while
  retaining full density in the detailed river corridor. Generated conifer cards now
  render only from 3.6–6.0 km, generated broadleaf cards from 3.2–5.4 km, and the sparse
  reviewed full-geometry variants use bounded 2.8/3.0–4.8/5.2 km ranges. The two masked
  card systems no longer cast redundant dynamic shadows over NAIP macro colour that
  already contains canopy shade. At the production resolution these changes remove
  sub-pixel masked-card work and repeated shadow stamps without deleting geographic
  macro detail or the Epic-quality population.
- The exact current V14 Development performance gate sampled 1,906 frames at 1920×1080
  High/60%: 16.281 ms workload p95, 16.697 ms wall-clock p95, 16.276 ms render-thread p95,
  16.170 ms GPU p95, zero hitches, 0.263 ms average and 0.376 ms maximum solver cost, and
  6,958.1 MB peak used physical memory. This is a 4.48 percent workload-p95 improvement
  over the 17.045 ms clustered-V14 comparison and passes the 16.667 ms Development frame,
  1.6 ms solver, and 8,192 MB memory gates. The packaged Shipping performance gate has
  not been rerun on V14 and no historical package result is being used as a substitute.
- Corrected the gameplay-only frosted-water failure without weakening hydraulic
  authority. Static captures proved the authored Single Layer Water was neutral and
  dark, while runtime diagnostics proved the 240 m moving solver mesh was compositing a
  second transmitting water volume 2 cm above it with zero foam contribution. The live
  mesh now uses a dedicated surface-lit alpha overlay with no refraction or water-volume
  output; it retains solver-depth tint, solver-foam whitening, animated South Fork
  normal-atlas microdetail, foam-dependent roughness, and the original solver
  geometry/normals. The underlying authored surface remains the sole translucent water
  volume and pooled spray/mist remains the aeration layer. A presentation-only 36 m
  station-end smoothstep is multiplied by hydraulic coverage that rises continuously
  from 18 percent in calm water to full coverage from the real solver foam and speed
  channels. The continuous alpha lets the authored volume supply calm-water colour and
  reflection without the visible stipple produced by the rejected temporal-dither
  version; sampling, geometry, wet/dry boundaries, and hydraulic values are unchanged.
  A renderer-enabled capture caught and rejected an intermediate Metal component-mask
  compile failure rather than accepting the automation result; the corrected graph uses
  the dedicated vertex-alpha output and M8 now asserts that the actual platform shader
  resource has no compile errors. The focused source contracts pass, the native editor
  target builds, P2 live-surface and renderer-enabled M7 each pass 1/1 with only Unreal's
  standard motion-vector warning, and M8 3/3 plus M9 4/4 pass with no warnings or errors.
  The exact 1920×1080 High/60% Development soak sampled 1,873 frames at 16.607 ms workload
  p95, 16.861 ms wall-clock p95, 16.605 ms render-thread p95, 16.482 ms GPU p95, zero
  hitches, 0.267 ms average and 0.343 ms maximum solver cost, and 7,024.3 MB peak memory;
  every gate passes. Direct review confirms the hard live/static colour boundary,
  checkerboard, and stipple are gone, but still rejects the subdued water response,
  smooth banks/hills, repeated foliage, and procedural crew as final photoreal media.
- Added explicitly inferred mid-scale geomorphology where the source DEM cannot resolve
  it. A separate focused implementation applies two deterministic world-space value-noise
  bands at 180 m and 58 m wavelengths, slope-conditions their amplitude from 0.12 m to a
  hard 4.8 m cap, and displaces only the eight non-colliding far-field underlay meshes.
  Foliage samples the same function, while the detailed gameplay corridor, collision,
  water, and hydraulics remain unchanged. The build manifest records the algorithm,
  limits, visual-only authority, and not-for-navigation status. All eight 1024² NAIP
  macros now use Sharpen4 mips and remain resident (about 5.3 MiB total) so short PIE
  captures cannot substitute an average-green streaming mip. Far-field material instances
  retain 84 percent source macro colour while exposing more reviewed forest/rock detail.
  The rebuild preserves 3,209,440 Nanite far-field triangles and 176,124 far-field foliage
  instances; all 20 HLOD actors rebuilt with commandlet result 0 and no errors. Focused
  Python/source tests pass 15/15, the native editor target builds, rendered M7 passes with
  only Unreal's standard motion-vector warning, M8 passes 3/3, and M9 now passes 4/4 with
  zero warnings or errors, including deterministic phase/cap/authority coverage. The
  post-HLOD terrain-only comparison sampled 1,901 frames at 16.549 ms workload p95,
  16.852 ms wall-clock p95, 16.513 ms render-thread p95, 16.454 ms GPU p95, zero hitches,
  0.259 ms average and 0.753 ms maximum solver cost, and 6,991.7 MB peak memory; every gate
  passed. The later continuous-alpha water soak above supersedes it as the current
  Development performance evidence. Direct comparison shows more mid-scale slope breakup
  and stable macro detail, but the hills and repeated canopy still read as procedural
  rather than accepted photoreal marketing art.
- Corrected the average-green far-field failure exposed by the canonical guide-eye
  capture. The registered aerial macro is 84 percent USDA NAIP source imagery, so its
  canopy-heavy green is geographically useful from above but read as a continuous green
  carpet on oblique hills. The accepted implementation changes only the existing
  `TerrainTone` constant to `(1.04, 0.78, 0.66)` and adds the focused
  `RaftSim.CreatePhotorealTerrainMaterial` authoring command. It preserves the registered
  NAIP spatial pattern, DEM vertices, procedural-relief bounds, collision, and hydraulics
  and adds no new per-pixel shader operations. More elaborate canopy classification,
  source-macro contrast, and geologic-outcrop branches were rejected: the first complete
  graph missed at 16.794 ms workload p95, and the simplified graph had inadequate margin
  despite one 16.666 ms pass. The exact zero-extra-ALU asset subsequently sampled 16.668
  ms p95 with zero hitches, then 16.834 ms with two host hitches during repeated hot-order
  runs. A 0.70 High far-field density experiment was also rejected and reverted after a
  thermally saturated 17.355 ms result failed to establish any benefit. These reports are
  retained as diagnostic evidence. One bounded final qualification run on the restored
  High=0.75 preset sampled 1,824 frames at 17.410 ms workload p95, 17.656 ms wall-clock
  p95, 17.402 ms render-thread p95, and 17.123 ms GPU p95 with zero hitches. Solver cost
  passed at 0.272 ms average/1.042 ms maximum and memory passed at 6,970.1 MB, but the
  frame gate did not. At that point the last accepted 16.607 ms continuous-alpha soak
  therefore remained historical qualified evidence; no further unchanged same-session
  retries were used to select a favorable sample. The later far-field material
  optimization below supersedes that failed exact-asset qualification. The native editor
  target builds, the canonical renderer-enabled M7 capture passes with only Unreal's
  standard motion-vector warning, M8 passes 3/3, and M9 passes 4/4 without warnings or
  errors.
- Removed terrain shader work that was invisible at its authored viewing distance. The
  detailed gameplay corridor keeps all six reviewed 1.5–2.0 m world-aligned rock/ground
  albedo, normal, and roughness functions. The eight kilometre-scale far-field instances
  now use static material switches that compile those functions out while retaining their
  registered 1024² NAIP colour, DEM/Nanite geometry, geometric normals, a bounded 0.82
  roughness, and a constant reviewed dry-ground contribution. The first macro-only static
  branch was visually rejected because it restored saturated canopy green; the accepted
  `(0.42, 0.28, 0.14)` dry-ground average recovers the prior brown/olive balance without
  restoring distant texture samples. In the detailed path, the prior four-octave arbitrary
  per-pixel rock-mask noise is replaced by a low-cost red-minus-green signal from the
  already sampled registered macro, so exposed soil/rock follows source geography and
  canopy suppresses it. DEM vertices, inferred-relief bounds, collision, hydraulic fields,
  foliage population, and the Epic art path are unchanged. A mesh-reuse regeneration
  updated all 13 detailed and eight far-field material instances. Focused source tests
  pass 15/15, the native editor target builds, renderer-enabled M7 passes with only the
  standard motion-vector warning, M8 passes 3/3, and M9 passes 4/4 with no warnings or
  errors. The exact 1920×1080 High/60% Development soak sampled 1,932 frames at 16.322 ms
  workload p95, 16.708 ms wall-clock p95, 16.309 ms render-thread p95, and 16.215 ms GPU
  p95 with zero hitches. Solver cost passed at 0.255 ms average/1.245 ms maximum and memory
  passed at 6,964.3 MB. This is a 6.25 percent workload-p95 improvement over the failed
  17.410 ms exact-asset run and restores every Development gate, but it is not a substitute
  for the still-missing current Shipping package/soak or target-platform evidence.
- Removed the hard white mist disc exposed in the post-optimization canonical capture.
  Calm classifier residue below 0.22 no longer creates a standalone mist instance; real
  hydraulic aeration ramps to an 18-puff deterministic cluster using 4.5–11 cm
  anisotropic spheres rather than the previous 9–24 cm round puffs. Solver/contact spray,
  droplets, and impact sheets remain driven by their existing physical state. Focused M4
  classifier/runtime-pool automation passes 2/2, the native editor target builds, and the
  renderer-enabled M7 capture passes with the standard motion-vector warning and no hard
  foreground disc. The exact-current 1920×1080 High/60% Development soak sampled 1,943
  frames at 16.050 ms workload p95, 16.621 ms wall-clock p95, 16.038 ms render-thread p95,
  and 15.932 ms GPU p95 with zero hitches. Solver cost passed at 0.257 ms average/0.628 ms
  maximum and memory passed at 7,000.0 MB. Final M8 passes 3/3 and M9 passes 4/4 without
  warnings or errors.
- Removed two review-only tree families that the full-reach selector had incorrectly
  treated as production foliage. `Tree Small 02` was already explicitly rejected for a
  pale sparse canopy and regular repetition, while `Pine Tree 01` remains an isolated
  sparse-comparison asset with `production_promoted=false`; neither asset path is now
  present in the full-reach generator. The project-owned photographic Ponderosa source
  instead creates three deterministic radial-card profiles at 7.6×12.4 m, 8.2×11.8 m,
  and 9.0×11.2 m, and live-oak instances use three seeded crown aspect profiles. Generated
  canopy materials now use non-transmissive two-sided Default Lit shading, no emissive
  fill, a 0.42 alpha clip, and Sharpen4 coverage-preserving mips. The canonical M7 review
  confirms the tall white conifers are gone while preserving the established foliage
  population and source-conditioned placement. Source/release tests pass 23/23, focused
  Ruff checks pass, the native editor target builds, rendered M7 passes with only Unreal's
  standard motion-vector warning, M8 passes 3/3, and M9 passes 4/4 without warnings or
  errors. The exact-current 1920×1080 High/60% Development soak sampled 1,949 frames at
  15.977 ms workload p95, 16.630 ms wall-clock p95, 15.974 ms render-thread p95, and
  15.840 ms GPU p95 with zero hitches. Solver cost passed at 0.264 ms average/0.296 ms
  maximum and memory passed at 6,983.8 MB. This supersedes the mist-only Development soak
  above; a fresh Shipping package/soak is still required.
- Increased calm-water definition using only parameters and texture samples already in
  the static Single Layer Water and live solver-overlay graphs. Static ripple response is
  0.16, calm colour variation 0.11, water roughness 0.13, and fallback Fresnel sky response
  0.42; the live overlay uses 0.18 ripple response, 0.13 calm roughness, and 0.38 fallback
  sky response. No new sample, branch, refraction volume, geometry, depth, foam, coverage,
  or hydraulic input was added. Canonical review accepts clearer current-aligned breakup
  and reflection as an incremental improvement without the prior frosted-sheet failure,
  but still rejects the single-tile repetition and overall water response as final
  photoreal art. Source/release tests pass 23/23, Ruff checks pass, the native target
  builds, rendered M7 passes with the standard motion-vector warning, M8 passes 3/3, and
  M9 passes 4/4 without warnings or errors. The first exact soak held 15.960 ms workload
  p95 but failed honestly on one isolated 71.012 ms hitch. One bounded confirmation run
  sampled 1,939 frames at 16.095 ms workload p95, 16.674 ms wall-clock p95, 16.089 ms
  render-thread p95, and 15.978 ms GPU p95 with zero hitches. Solver cost passed at 0.266
  ms average/1.144 ms maximum and memory passed at 6,998.4 MB. This confirmation is the
  current Development evidence; it does not replace the missing Shipping package/soak.
- Replaced the first-generation far-field value-noise infill with a source-slope-
  conditioned, domain-warped, paired ridge/drainage fractal. The source USGS 3DEP DEM
  remains the geographic authority; the infill remains visual-only and non-colliding,
  never enters the detailed corridor, water geometry, or hydraulic fields, stays at
  centimetre scale on flat benches, and retains the hard ±4.8 m cap on steep canyon
  walls. The mesh-resolvable bands use 180 m broad, 58 m detail, and 96 m ridge
  wavelengths with a bounded 32 m/420 m domain warp and blend weights summing to one.
  Unreal reused all 13 detailed terrain tiles and all 39 water meshes while rebuilding
  only the eight non-colliding 513²/Nanite far-field patches and their matching foliage
  elevation. Canonical v27 review at
  `/private/tmp/raftsim_m9_v27_terrain_morphology_canonical.png` (SHA-256
  `2675bd4311bb157c1e0737121c0c57bc2093116c0bc378ea53cb3e87ffa8ce25`)
  accepts the new coherent benches, drainage folds, and broken shoulders without a
  corrugated or grid-noise silhouette. It remains an incremental geography improvement,
  not photoreal terrain acceptance: exposed slopes still need authored geologic and
  ground-cover breakup. Source/release/procedural-geography tests pass 24/24, focused
  Ruff checks pass, the native editor target builds, and the focused terrain automation
  passes 1/1. Rendered M7 passes with Unreal's standard motion-vector warning. The first
  M8 run passed 2/3 and correctly failed its stale v1 algorithm-name lock; after the lock
  was upgraded to require the v2 ridge, warp, authority, and cap fields, the clean rerun
  passed 3/3. M9 passes 4/4. The exact-current 1920×1080 High/60% Development soak sampled
  1,954 frames at 15.919 ms workload p95, 16.596 ms wall-clock p95, 15.916 ms render-thread
  p95, and 15.790 ms GPU p95 with zero hitches. Solver cost passed at 0.263 ms average and
  0.408 ms maximum; memory passed at 7,008.1 MB. This is current Development evidence
  only and does not replace a fresh Shipping package/soak.
- Corrected a stale far-field foliage selector that advertised four conifer variants but
  assigned both `FarConiferCard` and `FarConiferA` to the same Ponderosa A mesh. Combined
  with the former selector thresholds, 93.3 percent of conifers therefore repeated one
  silhouette. The duplicate HISM is removed and the three real project-owned radial-card
  profiles now form deterministic mature/intermediate/younger classes at 44/30/26
  percent. Their base height envelopes are approximately 9.7–16.6 m, 8.0–13.9 m, and
  6.5–11.6 m before the existing small nonuniform variation. All three far conifer HISMs
  disable dynamic shadows, retaining source-NAIP canopy/shadow authority and avoiding
  repeated dark stamps; the selector adds no material sample, shader branch, texture,
  instance, terrain, water, collision, or hydraulic cost and removes one HISM component.
  Canonical v28 review at
  `/private/tmp/raftsim_m9_v28_ponderosa_profiles_canonical.png` (SHA-256
  `a152db9c263582cd36d6272fc1844ac1d8f52593a5f92d98cb567b414cfe362a`)
  accepts the mixed age/crown rhythm without pale trees or a new grid artifact. It does
  not accept final vegetation art: every profile still stretches one photographic source
  and the distant crowns remain uniformly dark. Source/release/procedural-geography tests
  pass 24/24, focused Ruff checks pass, the native editor target builds, rendered M7
  passes with the standard motion-vector warning, M8 passes 3/3, and M9 passes 4/4. The
  exact-current 1920×1080 High/60% Development soak sampled 1,978 frames at 15.746 ms
  workload p95, 16.439 ms wall-clock p95, 15.744 ms render-thread p95, and 15.602 ms GPU
  p95 with zero hitches. Solver cost passed at 0.257 ms average and 0.360 ms maximum;
  memory passed at 6,994.6 MB. This supersedes v27 as current Development evidence only;
  it does not replace a fresh Shipping package/soak.
- Calibrated only the existing generated-Ponderosa albedo multiply from
  `(0.98, 1.02, 0.94)` to `(1.18, 1.20, 1.12)`, leaving the live-oak material unchanged.
  The material remains Default Lit and masked with no emissive or subsurface path; the
  pass adds no texture, sample, shader branch, geometry, instance, collision, or hydraulic
  cost. Canonical v29 review at
  `/private/tmp/raftsim_m9_v29_ponderosa_albedo_canonical.png` (SHA-256
  `a0731b67803586e43ee06b54c43cb9b4ca5b357e275d0b4a0360497a8b95830a`)
  accepts recovered green-brown branch and crown detail on near/mid Ponderosa cards
  without reintroducing pale, white, emissive, or translucent trees; distant trees remain
  intentionally darker under atmospheric lighting. This is a photometric correction,
  not final vegetation acceptance: the three profiles still derive from one photographic
  source. Source/release/procedural-geography tests pass 24/24, focused Ruff checks pass,
  the native editor target builds, rendered M7 passes with the standard motion-vector
  warning, M8 passes 3/3, and M9 passes 4/4. The exact-current 1920×1080 High/60%
  Development soak sampled 1,979 frames at 15.711 ms workload p95, 16.464 ms wall-clock
  p95, 15.710 ms render-thread p95, and 15.599 ms GPU p95 with zero hitches. Solver cost
  passed at 0.262 ms average and 0.292 ms maximum; memory passed at 7,004.9 MB. This
  supersedes v28 as current Development evidence and is itself superseded as the
  release-performance gate by the exact-current Shipping measurement below.
- Built a fresh exact-current v29 macOS arm64 Shipping package from the dirty M9 worktree.
  The full Metal SM5/SM6 cook staged 1,048/1,048 packages; the app contains 641 files,
  including all 611 runtime-data files. Its Apple Development signature verifies and its
  App Sandbox and `get-task-allow` entitlements are present, but a bounded launch attempt
  reproduced the host pre-`main` App Sandbox service stall on these current bytes. A
  `ditto`-copied diagnostic clone retained a byte-identical runtime-data payload, removed
  App Sandbox, and was re-signed with one matching local development Team ID. The clone
  runs, but strict signature verification reports `CSSMERR_TP_NOT_TRUSTED`; it is
  explicitly diagnostic and cannot be distributed or promoted.
- The exact-current diagnostic clone passes 60/60 packaged rapid cases with 0.345 ms
  maximum average and 0.377 ms maximum single solver cost. Full release-candidate QA
  passes the Shipping/version/live-solver contract, all 14 keyboard/gamepad actions,
  legacy/future save protection, and 39/39 three-flow full-reach cases. An unused
  `UserDir` passes all nine first-run gates with save schema 3 and nine default bindings.
  The canonical 10-second-warmup plus 30-second 1920×1080 High/60% Metal soak on Apple M5
  sampled 2,011 frames at 14.909 ms mean, 15.426 ms workload/GPU p95, 16.434 ms wall-clock
  p95, and zero hitches above 33 ms. Solver cost passed at 0.306 ms average and 0.505 ms
  maximum; memory passed at 5,244.2 MB. This closes the local exact-current Shipping
  functional, first-profile, and performance diagnostics, but not App Sandbox startup,
  Developer ID/notarization, clean-commit immutability, target-platform/fresh-machine
  repeatability, or representative-art and named-owner acceptance.
- Replaced the former single-source scaled Ponderosa B/C profiles with two independent,
  project-owned photographic-natural source images: an intermediate Sierra Nevada
  foothill specimen and a younger dry-bench specimen. Both final alpha cards are
  1024×1536 RGBA and have separate generated texture/material packages; A/B/C retain the
  existing 44/30/26 HISM distribution and add no HISM component or draw call. The
  source-art provenance record now stores each generation brief, resampling step, and
  SHA-256 (`46315638ec808d539c51a9ef682b25544aa195f007b80d7d0fcee9d1983971dc`
  intermediate alpha;
  `9ede99ab1403399ce9cbf6cd5d73d8bbd4c9778f6f11e2c4ea2bc61837de31e0`
  younger alpha). Canonical v31 review at
  `/private/tmp/raftsim_m9_v31_three_source_ponderosa_canonical.png` (SHA-256
  `f632381a12722705517b87bab2cead9bec4b5b337363204759cabd0e23d618f9`)
  accepts materially independent intermediate/younger silhouettes without reintroducing
  pale conifers. It does not accept final vegetation art: radial billboard planes remain
  visibly intersecting and the broadleaf treatment remains pale. M8 passes 3/3, rendered
  M7 passes with only Unreal's standard motion-vector warning, and the exact-current
  Development soak sampled 1,979 frames at 15.746 ms workload p95, 16.406 ms wall-clock
  p95, and 15.612 ms GPU p95 with zero hitches. Solver cost passed at 0.258 ms average and
  0.290 ms maximum; memory passed at 6,980.1 MB.
- Built a fresh exact-current v31 macOS arm64 Shipping package from the dirty M9
  worktree. The full Metal SM5/SM6 cook discovered 1,052 packages, cooked and staged
  1,045 runtime packages, and skipped seven editor/platform-only packages. The locally
  Apple-Development-signed app contains 641 files, including all 611 runtime-data files,
  and 1,685,943,618 bytes of payload. Its App Sandbox and `get-task-allow` entitlements
  are present, but two bounded launches of the final entitlement state reproduced the
  host pre-`main` stall for at least 30 seconds without an Unreal log. A
  `ditto`-copied diagnostic clone retained the same runtime payload, removed App
  Sandbox, and was re-signed with one matching local development Team ID. It runs, but
  strict verification reports `CSSMERR_TP_NOT_TRUSTED`; it remains diagnostic-only.
- The exact-current v31 diagnostic clone passes 60/60 packaged rapid cases with 0.347 ms
  maximum average and 0.390 ms maximum single solver cost. Release-candidate QA passes
  the Shipping/version/live-solver contract, all 14 keyboard/gamepad actions,
  legacy/future save protection, and 39/39 three-flow full-reach cases. A new unused
  `UserDir` passes all nine first-run gates with save schema 3 and nine default bindings.
  The canonical 10-second-warmup plus 30-second 1920×1080 High/60% Metal soak on Apple M5
  sampled 2,004 frames at 14.963 ms mean, 15.561 ms workload/GPU p95, 16.464 ms wall-clock
  p95, and zero hitches above 33 ms. Solver cost passed at 0.299 ms average and 0.528 ms
  maximum; memory passed at 5,240.6 MB. This supersedes the v29 package as local
  exact-current functional, first-profile, and performance evidence, but does not close
  App Sandbox startup, Developer ID/notarization, clean-commit immutability,
  target-platform/fresh-machine repeatability, or representative-art and named-owner
  acceptance.
- Added a separate project-owned photographic-natural California white-alder source and
  alpha card rather than continuing to reuse the live-oak fallback. The final 1024×1536
  RGBA alpha has SHA-256
  `863ddf0ceb758e2be2b11440c02fd732186a007c85ca712d394e56b3a4245198`; the retained
  chroma source has SHA-256
  `7a1bbbaeacb892272c56eb80c0323b7b1100a9e07b6e48e4af2d1e0004bb7ec4`. Visual
  iteration explicitly rejected a crushed-black default-lit version and a pale/emissive
  fully unlit version. Accepted v37 keeps Default Lit, normal alder shadow casting, and
  adds only a measured 0.13 photographic-color ambient-fill contribution. Canonical
  review at
  `/private/tmp/raftsim_m9_v37_white_alder_measured_ambient_fill_canonical.png`
  (SHA-256 `8b0f2cd78cec3963cc7613114c14890e39f65e7f304a980c69afe5d4448a04ff`)
  accepts readable dark-olive crowns and credible shadows without white/emissive foliage.
  It does not accept the crossed-card vegetation system as final photoreal 3D foliage.
- Regenerated and validated the entire v37 world: 13 terrain tiles, 39 water tiles,
  18,325 foliage instances, 115 boulders, 255 spray/mist actors, 72 infrastructure
  actors, eight far-field meshes, 163 deterministic World Partition identities, and
  five full-reach captures. Validation covered 157 assets plus 164 associated objects
  with no errors. Rendered M7 passes 1/1 with only Unreal's standard motion-vector
  warning; M8 passes 3/3; M9 passes 4/4. The exact-current Development soak sampled
  1,979 frames at 15.193 ms mean and 15.740 ms workload p95, 16.564 ms wall-clock p95,
  and 15.593 ms GPU p95 with zero hitches. Solver cost passed at 0.274 ms average and
  0.343 ms maximum; memory passed at 6,989.6 MB.
- Built a fresh exact-current v37 macOS arm64 Shipping package from the dirty M9
  worktree. The Metal SM5/SM6 cook discovered 1,055 packages, cooked and staged 1,048
  runtime packages, and skipped seven editor/platform-only packages. The app contains
  641 files including all 611 JSON/NumPy runtime-data files and 1,686,574,800 bytes of
  payload. Its ad-hoc signature has no Team ID and passes strict on-disk verification,
  while App Sandbox and `get-task-allow` remain present. A bounded final-entitlement
  launch again stalled before Unreal `main` for 30 seconds without a log. The copied
  diagnostic clone has identical packaged content, no App Sandbox entitlement, and one
  matching local Apple Development Team ID; it runs, but strict verification reports
  `CSSMERR_TP_NOT_TRUSTED`, so it is diagnostic-only.
- The v37 diagnostic clone passes the standalone 60/60 packaged rapid matrix with
  0.351 ms maximum average and 0.388 ms maximum single solver cost. Release-candidate
  QA passes the Shipping/version/live-solver contract, all 14 keyboard/gamepad actions,
  legacy/future save protection, and 39/39 three-flow full-reach cases. A new unused
  `UserDir` passes all nine first-run gates with save schema 3 and nine default bindings.
  The canonical 10-second-warmup plus 30-second 1920×1080 High/60% Metal soak on Apple M5
  sampled 2,011 frames at 14.910 ms mean, 15.420 ms workload/GPU p95, 16.942 ms wall-clock
  p95, and zero hitches above 33 ms. Solver cost passed at 0.413 ms average and 0.618 ms
  maximum; memory passed at 5,238.4 MB. This supersedes v31 as local exact-current
  functional, clean-profile, and performance evidence, but does not close App Sandbox
  startup, Developer ID/notarization, clean-commit immutability, target-platform and
  fresh-machine/hardware QA, or representative-art and named-owner acceptance.
- Direct review of `Saved/Screenshots/MacEditor/M7_FullReachEnvironment.png` still rejects
  the current presentation: the hills now read as dry brown/olive and have visible
  slope-conditioned benches and drainage folds, but exposed ground remains too uniform
  and under-authored; the white and flat-black near/mid conifer failures are gone, but
  distant vegetation remains visibly procedural: its three independently sourced
  Ponderosa age/profile classes break up the former single-height rhythm and now expose
  green-brown branch detail, and the independent white-alder source now reads as dark
  olive rather than crushed black or emissive; however, the three-plane radial cards
  visibly intersect. The water has clearer current-aligned surface response but remains
  synthetic, and the fallback crew remains procedural. The v31, v29, and v3 packages
  are superseded historical evidence, not promotable candidates. M9 remains
  uncommitted and
  will not be pushed until production characters, representative-art acceptance,
  sandboxed Shipping startup, distribution signing/notarization, Windows and Proton QA,
  fresh-machine/input QA, and owner/guide/art/geospatial/legal acceptance all pass.
- v44 corrected the Troublemaker far-field overlap without changing authoritative DEM,
  collision, or hydraulics. Inferred relief now fades only across the three far-field
  cells adjacent to the detailed corridor, far-field vertices remain explicitly dry,
  and the non-colliding source-window backdrop no longer casts the hidden overlap edge
  as a black diagonal shadow. The regenerated world retained 13 terrain tiles, 39 water
  tiles, 18,325 near-corridor foliage instances, 176,124 far-field foliage instances,
  115 boulders, 255 spray/mist actors, 72 infrastructure actors, eight far-field meshes,
  and 163 deterministic World Partition identities. Rendered M7 passed 1/1 with only
  Unreal's standard motion-vector warning, M8 passed 3/3, and M9 passed 4/4 before and
  after a 20/20 HLOD rebuild. The exact-current Development soak sampled 1,990 frames at
  15.689 ms workload p95 with zero hitches; solver cost passed at 0.279 ms average and
  0.573 ms maximum, and memory passed at 7,317.5 MB.
- A v47 experiment directly tested deterministic geography continuation beyond the
  finite authoritative source windows. It generated eight non-colliding 129x129 underlay
  meshes extending 1.5 km from the source boundaries and clearly labelled them as
  visual-only, non-navigation geometry. Fixed-camera review rejected the experiment:
  the underlays replaced some empty horizon with conspicuous planar shelves and
  overlapping bands at Chili Bar, Troublemaker, Coloma, and Salmon Falls. All eight
  generated assets were moved intact to
  `/private/tmp/raftsim_m9_v47_rejected_procedural_infill_assets`, the runtime behavior
  and manifest fields were removed, and v48 regenerated the accepted shadow-safe world
  with the original 163 deterministic actors. This establishes that broad clamped-edge
  underlays are not an acceptable procedural-completion strategy; future continuity work
  must solve patch ownership, blending, and valley-scale synthesis rather than stacking
  independently expanded source windows.
- The exact v48 rollback baseline rebuilt the native editor target, regenerated and
  validated the five fixed full-reach cameras, and rebuilt all 20 HLOD actors with zero
  errors. The finalized evidence hashes every HLOD actor package and records terminal
  instancing with no invalid layer assignments or merged-atlas parent. Rendered M7 passed
  1/1 with the standard motion-vector warning, M8 passed 3/3, M9 passed 4/4 both before
  and after HLOD finalization, and the full Python/data/source matrix passed 1,057 tests
  with three expected optional-path skips. The fixed 10-second-warmup plus 30-second
  1920x1080 High/60% Development soak sampled 1,987 frames at 15.128 ms mean and
  15.683 ms workload p95, 16.467 ms wall-clock p95, 15.681 ms render-thread p95, and
  15.538 ms GPU p95 with zero hitches. Solver cost passed at 0.267 ms average and
  0.322 ms maximum; memory passed at 7,010.8 MB. v48 is the accepted technical baseline,
  not a photoreal or release acceptance: the five fixed cameras still expose planar
  source-window discontinuities, under-authored beige terrain, crossed-card vegetation,
  synthetic/flat water, and procedural people. M9 therefore remains uncommitted and
  unpushed pending approved production terrain/vegetation/water/characters, named
  owner/guide/art/geospatial/legal acceptance, sandboxed startup, Developer ID and
  notarization, and target-hardware/fresh-machine QA.
- A v49 source-window seam experiment linearly blended adjacent official 3DEP heights
  and NAIP colour within the recorded 64 m handoff band. Static analysis showed much
  smaller overlap disagreement after the blend, but all five fixed Unreal cameras were
  reviewed before acceptance. Coloma and Salmon Falls still showed long diagonal terrain
  ribbons against open sky, and Troublemaker retained a planar shelf. The experiment was
  rejected because independently clipped rectangular meshes and station-derived ownership
  masks are the topology failure; changing samples inside those meshes cannot make their
  outer boundaries watertight. v50 removed every v49 code/manifest field, restored the
  exact v14 generated products, regenerated the accepted 163-actor v48 world with 176,124
  far-field foliage instances, rebuilt and hashed all 20/20 HLOD actors with zero errors,
  and passed post-HLOD M7 1/1, M8 3/3, and M9 4/4. Future terrain completion must build one
  stitched global heightfield or watertight global mesh in a shared coordinate grid, then
  derive streaming cells from that common surface; independently owned per-window cuts are
  explicitly disallowed. This restoration remains a technical rollback baseline and does
  not close the visible terrain, vegetation, water, character, acceptance, signing, or
  target-hardware gates.
- The v91 editor baseline is the first full-reach integration after the bounded
  naturalization and rigged-character pass. It retains authoritative 3DEP/NAIP and
  hydraulics where available, labels procedural completion as visual-only, noise-modulates
  and jitters deterministic vegetation placement, extends reviewed 3D pines to 650 m from
  the river, strengthens current-aligned displacement and whitewater response, and replaces
  the segmented procedural body with five poseable Manny-backed crew bodies while retaining
  rafting PFDs, helmets, paddles, hands, boots, and rescue behavior. The regenerated world
  contains 175 deterministic actors, 13 terrain tiles, 39 water tiles, eight far-field
  patches, 14,068 near-corridor and 126,901 far-field foliage instances, 115 boulders,
  12,835 visual-only bank rocks, 255 spray/mist instances, 72 infrastructure actors, and
  13 local reflection probes. All 23 terminal HLOD actors rebuilt and were package-hashed
  with zero errors. A repeat commandlet evaluated the same 23 actors, rejected every
  rebuild as already current, modified zero packages, and reproduced an identical package
  path/hash list. The native editor target builds; M5 rescue/crew validation passes;
  post-HLOD M7 passes 4/4, M8 passes 3/3, and M9 passes 4/4. The exact-current 10-second
  warmup plus 30-second 1920×1080 High/60% Development soak follows a full
  Python/data/source result of 1,058 passed with three expected optional-path skips. The
  soak sampled 2,249 frames at 13.346 ms mean, 13.609 ms workload p95, 14.826 ms
  wall-clock p95, 13.609 ms
  render-thread p95, and 13.458 ms GPU p95 with zero hitches. Solver cost passed at
  0.254 ms average and 0.343 ms maximum; memory passed at 7,003.7 MB.
- v91 is a stronger technical and visual-development baseline, not M9 acceptance. Direct
  review still rejects smooth beige landforms, visible source-window/topology transitions,
  crossed-card and conspicuously pale vegetation, broad synthetic foam, overly smooth calm
  water, the generic mannequin/facial fallback, and the procedural raft as photoreal
  release art. A production MetaHuman-equivalent crew/guide with rafting wardrobe,
  production terrain/vegetation/water/raft assets, approved representative media,
  named owner/guide/art/geospatial/legal review, Windows and Proton hardware QA,
  sandboxed fresh-machine startup, Developer ID/Authenticode signing, notarization, and
  immutable clean-commit promotion all remain open. M9 therefore remains uncommitted and
  unpushed.
- Hardened the runtime performance report after the first current Shipping preflight
  exposed an impossible stale 89,478 ms RHI GPU sample during a 14.76 ms maximum
  wall-clock frame. The v2 capture accepts finite nonnegative GPU samples inside a
  deliberately generous `max(1000 ms, 16 × wall-clock frame)` envelope, counts and
  reports rejected samples, omits only rejected GPU values from the affected workload
  sample, never filters wall-clock hitches, and fails when invalid timing recurs beyond
  `max(3, ceil(0.1% of frames))`. Dedicated automation retains normal, long, and
  wall-correlated genuine GPU stalls while rejecting negative, non-finite, and stale
  multi-second values. The native editor target builds; M8 now passes 4/4 and M9 remains
  4/4.
- Built and exercised the fresh exact-current v93 macOS arm64 Shipping candidate directly
  in its final App Sandbox entitlement state. The full Metal cook discovered 1,076
  packages, staged 1,069 runtime packages, and skipped seven editor/platform-only
  packages. The 641-file app includes all 611 runtime-data files and verifies with the
  local Apple Development identity and Team ID. It launches without the former pre-main
  sandbox stall, passes 60/60 packaged rapid/flow cases, the Shipping/version/live-solver
  release contract, all 14 keyboard/gamepad actions, save migration/forward protection,
  39/39 three-flow full-reach cases, and all nine first-run persistence gates in a unique
  sandbox-container profile.
- The v93 rendered 10-second-warmup plus 30-second 1920×1080 High/60% Metal soak sampled
  2,291 frames. All 2,291 GPU timings were plausible and zero were rejected; workload
  p95 was 13.392 ms, wall-clock p95 was 14.705 ms, maximum wall frame was 16.296 ms, and
  no hitch exceeded 33 ms. Solver cost passed at 0.289 ms average and 0.629 ms maximum;
  memory passed at 5,245.3 MB. The generated 1,231,553,753-byte archive has SHA-256
  `abe048fa099956e1bae03d157c6adaeaa13ffc2370e20d428f1fe8dff6afaeb9`, and the local
  artifact manifest passes. It remains non-promotable because the source worktree is
  intentionally dirty, the signature is not Developer ID/notarizable, and the visual,
  human-review, cross-platform, target-hardware, and external fresh-machine gates remain
  unsatisfied. App Sandbox startup is no longer a local blocker.
- v94 reduces the detailed-corridor/far-field material handoff without changing source
  geometry: over the outer 64 m of each detailed tile, source-macro influence reaches the
  far-field value and the detailed tone blends toward the far-field tone. M8 locks the
  authored `FarFieldSourceMacroTone` contract. Fixed-camera review found a bounded seam
  improvement, but smooth landforms and source-window/topology transitions remain visible.
- A v95 terrain-relief experiment was rejected and fully rolled back. Quantitative analysis
  showed the legacy valley cap suppresses much of the DEM relief away from the river, but
  restoring logarithmic residual relief exposed suspended and floating shelves at
  Troublemaker and Salmon Falls. That result confirms the primary defect is overlapping
  independently clipped source-window topology; relief cannot safely be restored until a
  single watertight shared-grid terrain surface replaces it. The restored v94 geometry
  passed all 17 focused geography/source checks.
- v96 replaces the old capsule-streak normal-atlas sample with the project-owned
  `T_RaftSim_SouthForkWater_FlowNormal` texture. Both Single Layer Water and the live-water
  overlay combine two cross-moving samples at different scales; mirror addressing makes
  the documented source edge mismatch continuous in use. The source PNG, provenance JSON,
  normal-map import settings, and material graph are content-locked. Chili Bar and Coloma
  no longer show the former full-screen capsule-scratch field, and Meat Grinder reads as a
  broken multi-scale surface. Troublemaker and Salmon Falls still show perspective-aligned
  streaking, so this is an accepted technical/art-development improvement, not photoreal
  water acceptance.
- The exact-current v96 Development soak used the required 10-second warmup and 30-second
  1920×1080 High/60% Metal measurement. It sampled 2,216 frames at 13.546 ms mean,
  14.052 ms workload p95, 15.013 ms wall-clock p95, 14.050 ms render-thread p95, and
  13.954 ms GPU p95. No frame exceeded 33 ms; all 2,216 GPU samples were plausible;
  solver cost passed at 0.254 ms average and 0.456 ms maximum; peak memory was 7,001.3 MB.
  The v96 HLOD build rebuilt all 23 actors with zero errors, and the immediate repeat
  evaluated all 23, rejected every rebuild as current, and saved zero packages. The
  finalized evidence hashes all 23 actor packages and passes 6/6 focused tests. Post-HLOD
  renderer-enabled M7, M8, and M9 each pass 4/4.
- v96 remains visually rejected overall. The main gaps are the non-watertight terrain
  source-window construction, conspicuous crossed-card/pale vegetation, residual synthetic
  water/foam response, the generic Manny/procedural face and wardrobe, and the procedural
  raft. The v93 Shipping package is now explicitly superseded diagnostic evidence because
  it predates v94/v96. An exact-current Shipping candidate will be built only after the
  next accepted source/map state is stable; M9 remains fail-closed, uncommitted, and
  unpushed until the visual, human-review, hardware, platform, signing, and promotion gates
  are all satisfied.
- A v99 detailed-corridor expansion was rejected and fully rolled back. The route-curvature
  audit found no inverted triangles through ±112 m and first found inversions at ±128 m,
  but fixed cameras showed large smooth wedges and over-steep banks at Chili Bar, Coloma,
  and Salmon Falls. The exact v96-width geometry was regenerated in v100 with 838,656
  terrain triangles and the complete 175-actor inventory restored. Wider independent
  corridor strips therefore do not solve the shared-topology terrain defect.
- v101 and v102 grazing-angle water-filter variants were rejected after shader compilation
  exposed normal dependency cycles. v104 uses a dedicated Fresnel with a constant
  horizontal `(0,0,1)` normal, exponent 1.4, and detail-normal floors of 0.45 for the
  underlying surface and 0.50 for the live overlay. It compiles cleanly, preserves broken
  multi-scale whitewater at Meat Grinder, and suppresses the harshest Salmon Falls
  streaking. Troublemaker still exposes some view-aligned foreground lines, so v104 is a
  bounded improvement rather than final water-art acceptance.
- The exact v104 world rebuilt all 23 HLOD actors with zero errors. An immediate repeat
  evaluated the same 23 actors, rebuilt and saved zero packages, and reproduced the
  finalized package-path/hash evidence; the focused evidence suite passes 6/6. Post-HLOD
  renderer-enabled M7, M8, and M9 each pass 4/4. The exact 10-second-warmup plus 30-second
  1920×1080 High/60% Development soak sampled 2,246 frames at 13.368 ms mean, 13.609 ms
  workload p95, 14.836 ms wall-clock p95, 13.608 ms render-thread p95, and 13.476 ms GPU
  p95. All GPU timings were plausible, no frame exceeded 33 ms, solver cost passed at
  0.253 ms average and 0.279 ms maximum, and peak memory was 7,015.5 MB. The environment,
  generic characters, procedural raft, representative media, named reviews, external
  hardware/platform QA, distribution signing, and immutable promotion gates remain open;
  M9 stays fail-closed, uncommitted, and unpushed.
- v109 applies one deterministic radiometric table to both the close-corridor and
  far-field orthophoto samplers. Robust source medians exposed a 151.381 Salmon Falls
  window against a 96.187 eight-window target; bounded exposure gains of 0.68–1.18 and
  contrast recovery of 1.0–1.25 reduce that pale acquisition block without changing DEM
  elevation, collision, local chroma, or source provenance. The regenerated data contract
  replaces raw RGB variance—which rewarded bad exposure seams—with chromatic and spatial
  luminance-range gates; focused environment/source tests pass 17/17. Fixed cameras accept
  the reduction in Salmon Falls washout as a bounded improvement, but still reject the
  smooth terrain forms, sparse/card foliage, generic crew, procedural raft, and remaining
  live-water artifacts as photoreal.
- The exact v109 world retains 175 deterministic actors, 838,656 terrain triangles,
  927,000 water triangles, and 2,077,407 far-field triangles. Reclassification changes the
  deterministic dressing totals to 14,179 near-corridor foliage, 127,667 far-field foliage,
  and 12,818 scenic rocks. All 23 HLOD actors rebuilt with zero errors; the repeat evaluated
  23/23 and saved zero packages, and package-hash evidence passes 6/6. Post-HLOD M7, M8,
  and M9 each pass 4/4. The exact v109 10-second-warmup plus 30-second 1920×1080 High/60%
  Development soak sampled 2,172 frames at 13.855 ms mean, 14.433 ms workload p95,
  15.473 ms wall-clock p95, 14.409 ms render-thread p95, and 14.332 ms GPU p95. All GPU
  timings were plausible, no frame exceeded 33 ms, solver cost passed at 0.255 ms average
  and 0.300 ms maximum, and peak memory was 7,324.3 MB. M9 remains fail-closed,
  uncommitted, and unpushed while the visual and external release gates remain open.
- v114 replaces eligible conifer cards within 1,100 m river distance with the three
  rights-reviewed Nanite pine analogs already used near the corridor. The deterministic
  placement and total foliage population are unchanged: the exact build contains 10,981
  detailed 3D pine instances and 96,293 remaining distant pine cards. Fixed cameras show
  a bounded improvement to mid-distance tree volume and silhouette, but the remaining
  card canopy and pale trees still fail the photoreal environment gate.
- The exact v114 world retains 175 deterministic actors, 838,656 terrain triangles,
  927,000 water triangles, 2,077,407 far-field triangles, 14,179 near-corridor foliage
  instances, 127,667 far-field foliage instances, and 12,818 scenic rocks. All 23 HLOD
  actors rebuilt with zero errors; the immediate repeat evaluated 23/23, saved zero
  packages, reproduced stable package paths and hashes, and the focused source/HLOD suite
  passes 16/16. Post-HLOD M7, M8, and M9 each pass 4/4. The exact v114 10-second-warmup
  plus 30-second 1920×1080 High/60% Development soak sampled 2,237 frames at 13.423 ms
  mean, 13.684 ms workload p95, 14.889 ms wall-clock p95, 13.680 ms render-thread p95,
  and 13.534 ms GPU p95. No frame exceeded 33 ms, all GPU timings were plausible, solver
  cost passed at 0.254 ms average and 0.319 ms maximum, and peak memory was 7,019.7 MB.
  The complete Python suite passes 1,058 tests with three expected dependency-path skips.
  Photoreal environment/character/raft/water acceptance and all named external release
  gates remain open, so M9 stays fail-closed, uncommitted, and unpushed.
- A v120 source-relief-preserving valley experiment was rejected and fully rolled back.
  Narrowing detailed-corridor registration and fading the grade safeguard sooner restored
  useful DEM-scale undulation on distant hills, but fixed cameras exposed floating
  cross-valley shelves and detached foliage at Troublemaker and Coloma while the near
  planar wedges remained. v121 regenerated and reimported the exact v114/v20 products;
  its determinism signature is `8fc68ede28d0e13a605f3e93180c95fdd64b670bf6abe4cf6334ef7478880329`,
  the focused environment suite passes 7/7, and the accepted baseline remains v114.
  Future terrain work must replace the near-bank topology with a globally watertight
  construction rather than exposing more of the ambiguous curvilinear-to-world overlap.
- v122-v126 distance/slope parameter sweeps exposed that the 1,100 m detailed-pine switch
  was not actually measuring 1,100 m: the existing query searched only three 128 m spatial
  buckets on either side and returned `BIG_NUMBER` beyond roughly 500 m. Raising the
  nominal threshold as far as 4,200 m therefore changed only zero to six trees. Those
  trials are superseded diagnostic evidence rather than accepted art changes.
- v127 emits an exact route-distance raster from the already-computed global distance
  field for every far-field patch. Each seam-identical `I;16` PNG stores decimeters,
  represents 0-6,553.5 m, is declared in the patch manifest, and participates in the
  deterministic environment signature. The importer validates the raster dimensions
  and uses its decoded distance for representation selection instead of the truncated
  bucket query. Tests lock the encoding, range, artifact contract, and horizontal and
  vertical tile seams.
- v128 restores the intended 1,100 m switch and matches the reviewed 3D conifer cull range
  to the retained cards at 300,000-520,000 cm. Placement and total far-field foliage stay
  unchanged at 127,667 instances while the exact representation split becomes 22,328
  detailed Nanite pines and 84,946 cards. The generated environment signature is
  `4364e3be19d66423c8f976ade0db80051958d95b39ee632514e6775ba0dddc97`.
  This is a bounded mid-distance fidelity improvement, not photoreal acceptance: fixed
  cameras still expose synthetic landform/topology transitions, pale/sparse vegetation,
  procedural water/raft presentation, and the Manny-backed character fallback.
- The exact v128 world retains 175 deterministic actors, 838,656 terrain triangles,
  927,000 water triangles, 2,077,407 far-field triangles, 14,179 near-corridor foliage,
  127,667 far-field foliage, 12,818 scenic rocks, 115 hydraulic boulders, 255 spray/mist
  instances, 72 infrastructure actors, and 13 local reflection probes. The 30-second
  1920x1080 High/60% Development soak after a 10-second warmup sampled 2,247 frames at
  13.356 ms mean, 13.602 ms workload p95, 14.824 ms wall-clock p95, 13.602 ms render-thread
  p95, and 13.457 ms GPU p95. No frame exceeded 33 ms, all GPU samples were plausible,
  solver cost passed at 0.254 ms average and 0.536 ms maximum, and peak memory was
  6,997.5 MB.
- The v129 HLOD build rebuilt and saved all 23 terminal actors with zero errors. The v130
  immediate repeat evaluated all 23 and rejected every rebuild, saved zero packages, and
  reproduced the complete package set; its log SHA-256 is
  `d74647e444086896756c3ab9fad3f5491a5974333bf1b12635b6150816d94698`.
  Focused HLOD/source/environment validation passes 23/23. Post-HLOD renderer-backed M7,
  headless M8, and M9 each pass 4/4 in v131/v132. The exact-current full Python suite passes
  1,058 tests with three expected optional-dependency-path skips. M9 remains fail-closed,
  uncommitted, and unpushed
  until the still-open visual, human, platform, hardware, signing, and packaging gates pass.
- v133 and v134 attempted to restore more local DEM relief by narrowing the corridor
  registration and changing its valley cap. Both were rejected because Salmon Falls and
  Coloma exposed catastrophic overhead/floating cross-valley source sheets. v135/v137
  established `south_fork_photoreal_environment_v23_bounded_valley_gully_morphology`:
  72-180 m corridor registration, a 14 percent downward-only safety envelope through
  1,800 m, and deterministic downward-only gully breakup beginning at 180 m. v136's
  deeper underlay was rejected for layered shelves and black gaps.
- Fixed-camera generation now fully flushes level streaming, completes material/shader
  compilation, streams resources, forces all generated terrain macro mips resident, and
  waits for texture streaming. The v138/v139 reuse captures first proved byte stability.
  v140 vertical cutout skirts were rejected for enormous black walls; v143's continuous
  underlay covered runnable Salmon Falls water; and v144's one-cell transition restored a
  suspended shelf. v145 removed all three rejected closures and restored strict
  per-triangle cutout safety. The v146/v147 persisted-map repeats are byte-identical across
  all five cameras. The accepted v23 environment signature is
  `681fa7769b0c25762d4f87ae926151ac5f699f40f207e2bc2e056bce2226de4e`.
- The exact v147 world contains 838,656 detailed-terrain triangles, 927,000 water
  triangles, 2,077,407 far-field triangles, 14,179 detailed-corridor foliage instances,
  127,655 far-field foliage instances, 12,769 scenic rocks, 115 hydraulic boulders, 255
  spray/mist instances, 72 infrastructure actors, and 13 local reflection probes. It is
  a safer and more deterministic technical baseline, not photoreal acceptance: the five
  cameras still expose open terrain-cutout shelves, smooth/under-authored landforms,
  sparse/card vegetation, flat/synthetic water, generic crew, and the procedural raft.
- A pre-HLOD v148 soak failed at 18.390 ms p95 with one hitch, and the post-HLOD v151
  control failed at 20.377 ms p95 with zero hitches; game thread, solver, memory, and GPU
  sample credibility all passed, isolating the regression to render/GPU cost. A bounded
  v152 diagnostic reduced only scalable non-colliding far-field foliage from High 0.75 to
  0.50 and passed at 14.329 ms p95. The accepted High preset now uses 0.50 for scalable
  far-field foliage/grass while detailed corridor vegetation stays at authored density
  and Epic remains 1.0. The exact 10-second-warmup plus 30-second v153 gate sampled 2,129
  frames at 14.137 ms mean and 14.837 ms workload p95, with 15.330 ms wall-clock p95,
  14.825 ms render p95, 14.740 ms GPU p95, zero hitches, zero invalid GPU samples, 0.261 ms
  average solver cost, 0.430 ms maximum solver cost, and 7,043.6 MB peak memory.
- v149 rebuilt and saved all 23 terminal HLOD actors with zero errors. v150 immediately
  evaluated 23/23 as `RejectRebuild`, saved zero packages, and finalized package/hash
  evidence; the repeat log SHA-256 is
  `e0b017c8c6d766c66dea039430e9f98b32fa4e04f463d3196e4f60f99e6fd6f8`.
  Post-HLOD v154 M7, v155 M8, and v156 M9 each pass 4/4. The exact-current Python/data/source
  matrix passes 1,058 tests with three expected optional-dependency-path skips in 362.69
  seconds. M9 remains fail-closed, uncommitted, and unpushed until photoreal/production-art
  acceptance, named human reviews, target-platform/fresh-machine hardware QA, exact-current
  Shipping qualification, signing/notarization, approved media, and clean promotion pass.
- The manifest-sensitive v157 M9 rerun passes 4/4 after the current evidence update. The
  canonical v158 macOS Shipping workflow then built and cooked the exact-current dirty
  worktree, packaged 641 files (611 runtime-data files), applied a valid Apple Development
  signature and App Sandbox entitlement, and passed 60/60 rapid cases, 39/39 three-flow
  full-reach cases, all 14 keyboard/gamepad action mappings, save migration/forward
  protection, and a pristine-profile disk round trip. Its 10-second-warmup plus 30-second
  1920x1080 High/60% rendered Metal soak sampled 2,363 frames at 12.692 ms mean, 12.897 ms
  workload p95, 14.302 ms wall-clock p95, 12.897 ms GPU p95, zero hitches, zero invalid GPU
  samples, 0.287 ms average/0.478 ms maximum solver cost, and 5,247.5 MB peak memory. The
  1,236,327,343-byte archive SHA-256 is
  `bdcdc2e96850b897ebc1cc3ae49362ee681f794b344b708fc76d4a6a79f7cacc`. This closes the
  exact-current local Shipping engineering preflight only. It remains a transient,
  dirty-worktree diagnostic tied to the M8 base commit, not a clean immutable candidate;
  Developer ID notarization, external machines/hardware, human acceptance, photoreal art,
  approved media, and promotion remain open, so M9 stays fail-closed and uncommitted.
- The exact-current five-camera set now has a dedicated fail-closed reviewer handoff at
  `docs/release-review/m9-south-fork-acceptance.md` and a machine-readable results form at
  `docs/release-review/m9-south-fork-acceptance.json`. Capture hashes, camera stations,
  source/procedural authority records, known visual blockers, named owner/guide/art/
  geospatial/legal review requirements, and external platform/signing gates are explicit.
  Every approval remains false and every reviewer/evidence field remains empty until a
  qualified person supplies a dated decision; the packet cannot manufacture acceptance.
- Release handoff now independently verifies the downloaded artifact manifest, release
  version/branch/commit, clean-source flag, platform, distribution-signature status,
  packaged-QA results, safe archive name, byte count, and SHA-256 before promotion or
  Proton extraction. The verifier reaccepted the v158 1.236 GB archive only when given
  explicit dirty-worktree and non-distribution diagnostic exceptions. Windows RC
  automation now includes the pristine-profile persistence lane, and Proton records a
  hash-locked input verification before unpacking the Authenticode-signed archive. The
  focused release tests pass 16/16, M9 v160 passes 4/4, Ruff and shell syntax checks pass,
  and the expanded full Python/data/source matrix passes 1,063 tests with three expected
  optional-dependency skips in 366.05 seconds.
- Geography v5 fixes a source-classification defect that had overwritten strong NAIP
  vegetation on every bank steeper than 0.42. Strong source canopy is now retained on
  plausible wooded slopes through cross-slope 1.25; 94.3443% is preserved in the visible
  34-64 m bank band. The canonical NPZ records the source vegetation score, and the
  manifest proves the rendered +/-64 m ribbon contains zero inverted/degenerate triangles
  or mixed-orientation cells. Meat Grinder, Coloma, and Troublemaker gain source-consistent
  wooded banks, but the simple tree assets and remaining cards still fail photoreal review.
- Water normal strength is now solver-conditioned rather than uniformly strong: calm
  current contributes 0.035, authored foam 0.085, normalized speed 0.045, and the combined
  response is capped at 0.14. This removes the dominant camera-radial grooves at
  Troublemaker while preserving Meat Grinder whitewater breakup. Broad foam and calm-reach
  response still require production water art. The v179/v180 capture sets are byte-identical
  across all five cameras with hashes locked in the M9 acceptance packet.
- Two additional visual experiments are explicitly rejected and absent. v168 changed
  inner-ribbon material parameters but produced five byte-identical frames because the
  visible outer-ribbon shader masked them. v176 added no more than 0.368 m of labeled,
  channel-excluded bank microrelief and retained zero detailed-ribbon folds, but a full
  rebuild exposed catastrophic far-field overhead sheets at Salmon Falls and a new Meat
  Grinder slit. The experiment was fully rolled back to geography v5 before v178-v180.
- v181 rebuilt all 23 terminal HLOD actors; v182 evaluated all 23, rejected every rebuild,
  saved zero packages, and finalized package/hash evidence. The repeat log SHA-256 is
  `bb036c1521990bdcf8614ee513c2986285c7c62100b7c4d917bbaf235c5a1de7`.
  The exact-current v183 10-second-warmup plus 30-second 1920x1080 High/60% Development
  soak sampled 2,231 frames at 13.459 ms mean, 13.719 ms workload p95, 14.906 ms wall-clock
  p95, 13.716 ms render-thread p95, and 13.590 ms GPU p95. It recorded zero hitches and
  invalid GPU samples, 0.253 ms average/0.447 ms maximum solver cost, and 7,032.8 MB peak
  memory. The v158 Shipping package is therefore historical rather than exact-current.
- The exact-current Python/data/source matrix passes 1,064 tests with the same three
  expected installed-dependency-path skips in 359.59 seconds. Post-HLOD M7, M8, and M9
  each pass 4/4 in v184-v186. These close the local source/runtime regression gates for
  the v180 candidate without changing the fail-closed human/platform/release status.
- The canonical v187 macOS arm64 Shipping workflow packages the v180 canopy/water
  gameplay and content candidate into 641 files (611 runtime-data files), applies a valid
  Apple Development signature and App Sandbox entitlement, and passes 60/60 rapid cases,
  39/39 three-flow full-reach cases, all 14 keyboard/gamepad mappings, migration/forward
  save guards, and all nine pristine-profile persistence gates. Its 10-second-warmup plus
  30-second 1920x1080 High/60% Metal soak samples 2,338 frames at 12.822 ms mean,
  13.115 ms workload/GPU p95, 14.418 ms wall-clock p95, and zero hitches. One implausible
  GPU timer is rejected within the explicit budget of three; 2,337 valid GPU samples,
  unfiltered wall-clock frames, 0.290 ms average/0.505 ms maximum solver cost, and
  5,254.9 MB peak memory all pass. The verifier reaccepts the 1,237,432,401-byte archive
  with SHA-256 `95c9e2b4e15c929c0d9e22ae95f406e5aaeed5ab55484f8afef92928b054b979`
  only under explicit dirty-worktree and non-distribution exceptions. v187 supersedes
  v158 as exact-current local engineering evidence; it does not satisfy immutable clean
  promotion, Developer ID/notarization, external platform/hardware, human acceptance,
  photoreal art, or approved-media gates, so M9 remains fail-closed and uncommitted.
- The post-evidence v188 Unreal M9 suite passes 4/4, including the release-manifest
  contract, packaged QA harness, future-save protection, and inferred far-field terrain
  relief. The acceptance JSON and release-candidate manifest both parse, and the focused
  fail-closed acceptance packet tests pass 2/2.
- v194 adds bounded calm-water definition without changing water geometry, foam, or
  shallow-water solver authority. The fallback sky-reflection alpha now reuses the
  already-evaluated surface noise with a 0.72 floor and 0.28 variation; Chili Bar,
  Coloma, Troublemaker, and Salmon Falls gain readable reflective breakup while Meat
  Grinder retains solver-driven whitewater. A separate capture-determinism defect was
  traced to reuse evidence reimporting source macro textures without persisted mips.
  Reuse now loads the saved macro textures, while authoring still performs source import.
  v193/v194 are byte-identical across all five cameras with no empty-mip warning.
- v196 rebuilt all 23 terminal HLOD actors after the water parent changed. v197 evaluated
  all 23 as `RejectRebuild`, saved zero packages, and finalized package/hash evidence; the
  repeat log SHA-256 is
  `5e05d775a7581650fd9f97edc583603b80b7385d08ce0327c38af8fd5a923efd`.
  The exact-current v195 10-second-warmup plus 30-second 1920x1080 High/60% Development
  soak sampled 2,226 frames at 13.484 ms mean, 13.755 ms workload p95, 14.917 ms
  wall-clock p95, 13.754 ms render-thread p95, and 13.625 ms GPU p95. It recorded zero
  hitches and invalid GPU samples, 0.253 ms average/0.471 ms maximum solver cost, and
  7,037.3 MB peak memory. Post-HLOD v198 M7 and v199 M8 each pass 4/4.
- The manifest-sensitive post-evidence v200 M9 suite passes 4/4, covering the release
  manifest contract, packaged QA harness, future-save protection, and inferred far-field
  terrain relief for the v194/v197 evidence state. The exact-current Python/data/source
  matrix passes 1,065 tests with three expected installed-dependency-path skips in 358.27
  seconds.
- v194 is an internal art-development improvement, not photoreal acceptance. The fixed
  views still expose smooth olive terrain sheets, sparse/repeated billboard vegetation,
  broad synthetic foam, the generic Manny-backed crew, and the procedural raft. v187 now
  remains historical same-machine Shipping evidence only; an exact-current immutable
  Shipping build is intentionally deferred until the visual, human, platform, signing,
  media, and clean-source promotion gates can all pass.
- v201/v202 tested a slope-conditioned reveal of the detailed corridor's existing
  triplanar rock/ground maps on steep outer banks at 24 and 55 percent. Both changed bank
  tint/detail but left the dominant geometric sheets and repeated vegetation intact, so
  the experiment was rejected and fully rolled back. v203-v205 then exposed sparse
  one-to-three-code-value RGB variation in otherwise identical Coloma and Troublemaker
  frames. Pixel localization proved the changes were isolated output quantization rather
  than geometry, source macro, foliage, lighting-region, or mip-state differences.
- Fixed-camera evidence now disables only `r.Tonemapper.GrainQuantization` while reading
  the final 8-bit render target and restores the caller's value afterward. Runtime
  rendering and the normal lit/postprocessed capture path are unchanged. v206/v207 are
  byte-identical across all five views and reproduce the v194 hashes exactly. The editor
  target compiles, the expanded source-layout suite passes 12/12, and the full-reach
  implementation remains at its enforced 3,000-line ceiling.
- v208 rebuilt all 23 terminal HLOD actors after the temporary material-package churn.
  v209 immediately evaluated all 23 as `RejectRebuild`, saved zero packages, and finalized
  current package/hash evidence; its repeat log SHA-256 is
  `349392dbb33dc213a981296fdaecf215125d8cbfe0aa3c75e3186d0d43a51880`.
  Final post-HLOD v210 M7, v211 M8, and manifest-sensitive v212 M9 each pass 4/4. The
  final Python/data/source matrix passes 1,066 tests with three expected
  installed-dependency-path skips in 371.26 seconds.
- Geography v6 replaces the old 14 m source-bank snap with a 14–224 m disclosed
  erosion-conditioned blend and widens the detailed curvilinear ribbon to its verified
  fold-free 112 m limit. Environment v24 derives all eight streaming cells from one
  global source/procedural surface, adds bounded nonlinear valley and drainage relief,
  and extends exact route distance beyond both endpoints. Fixed-camera review confirms
  that the dominant triangular valley walls at Chili Bar, Meat Grinder, Coloma, and
  Troublemaker are gone. A visual-only 1.8 km reservoir ribbon closes the downstream
  Salmon Falls gap without collision or hydraulic authority; the takeout acceptance
  camera now records the guide-relevant upstream context.
- v217/v218 are byte-identical across all five fixed views. The current world validates
  176 deterministic actor identities, 13 terrain tiles, 39 simulated water tiles, one
  visual-only terminal water actor, 50,227 detailed foliage instances, 125,751 far-field
  foliage instances, 11,940 scenic rocks, and 72 infrastructure actors. v219 rebuilt all
  24 HLOD actors; after one setup-settling pass, v221 evaluated 24/24 with zero modified
  packages and finalized package/hash evidence. The v222 exact-current 10-second warmup
  plus 30-second 1920×1080 High/60% Development soak sampled 2,257 frames at 13.320 ms
  mean, 13.586 ms workload p95, 14.775 ms wall-clock p95, zero hitches/invalid GPU
  samples, 0.249 ms average/0.275 ms maximum solver cost, and 7,330.3 MB peak memory.
- This is a material terrain/topology improvement, not photoreal or release acceptance.
  Smooth under-authored landforms, sparse/repeated vegetation, broad synthetic foam,
  generic Manny-backed people, and the procedural raft remain open visual blockers.
  External human, platform, signing, notarization, approved-media, and clean immutable
  promotion gates also remain open, so M9 is still deliberately uncommitted and unpushed.
- The v228 presentation pass replaces glossy cyan Manny template paint with bounded dark,
  neutral matte tints on the existing skeletal-qualified material. The fresh M7 suite
  passes 4/4 and the v229 M5 crew/raft/rescue suite passes 4/4 without skeletal-material
  usage warnings. This is a legibility improvement only: generic mannequin anatomy,
  procedural heads, slab-like PFDs, and generic wardrobe still fail photoreal character
  acceptance. The exact-current v230 10-second warmup plus 30-second 1920×1080 High/60%
  Development soak sampled 2,250 frames at 13.360 ms mean, 13.609 ms workload p95,
  14.792 ms wall-clock p95, zero hitches/invalid GPU samples, 0.249 ms average/0.280 ms
  maximum solver cost, and 7,056.6 MB peak memory.
- The manifest-sensitive exact-current v231 M8 content-lock suite and v232 M9 release
  suite each pass 4/4 after the v230 timing evidence and v228 presentation baseline were
  recorded. The expected missing Win64/Linux SDK notices on this Mac do not qualify those
  external platform lanes; they remain explicitly pending in the fail-closed matrix.
- The balanced hydraulic-water pass removes the broad pale foam carpet while preserving
  the visible Meat Grinder hydraulic core. The retained v249 fixed-camera set is the
  strongest reviewed presentation candidate, but the edge-like foam, flat reaches,
  smooth terrain, sparse/card vegetation, procedural raft, and black mannequin crew
  still fail internal photoreal acceptance.
- Capture generation and evidence capture are now separate operations. The final v269
  and v270 processes load the same settled saved World Partition map once, hard-load its
  actors, resolve camera height from the saved centerline median-water mesh, and capture
  without regenerating or resaving content. Chili Bar, Coloma, and Salmon Falls are
  byte-identical. Meat Grinder changes 3 pixels at maximum channel delta 1 and
  Troublemaker changes 7 pixels at maximum delta 4. All five pass the locked per-image
  limits of 32 changed pixels, 0.00005 changed fraction, 0.0001 mean absolute channel
  error, and maximum channel delta 8. The durable report records
  `all_byte_identical: false`; the M9 capture-repeatability engineering gate is closed
  without claiming impossible platform-level raster byte identity.
- v255 is the settled HLOD repeat: it evaluates all 24 actors, modifies zero packages,
  reports zero errors, and records hashes for every HLOD package. The exact-current v257
  10-second warmup plus 30-second 1920×1080 High/60% Development soak samples 2,226
  frames at 13.504 ms mean, 13.816 ms workload p95, 14.979 ms wall-clock p95, zero
  hitches/invalid GPU samples, 0.256 ms average/0.347 ms maximum solver cost, and
  7,059.3 MB peak memory.
- Exact-current v258 M5 and v259 M7 plus final-evidence v271 M8 and manifest-final v273
  M9 automation each pass 4/4. The exact-current full Python/data/source matrix passes
  1,068 tests with three expected optional-dependency-path skips in 358.17 seconds. M9
  remains fail-closed and
  uncommitted pending photoreal production assets, named human approvals, external
  platform/input testing, signing/notarization, approved media, and a clean immutable
  exact-current Shipping package.
- The exact-current post-textile chain is now green: v281 M5 4/4, v282 M7 4/4,
  v283 1920×1080 High/60% Development performance at 13.565 ms workload p95 with
  zero hitches and invalid GPU samples, v284 M8 4/4, and manifest-final v286 M9
  4/4. After correcting one deliberately fail-closed v257-to-v283 evidence-value
  mismatch, the complete Python/data/source matrix passes 1,070 tests with three
  expected dependency-path skips in 360.99 seconds.
- The first project-owned equipment-surface fallback now covers coated raft fabric, PFD
  ripstop, and wetsuit neoprene. Three logo-free raw studies feed deterministic
  four-way-mirrored 1024×1024 albedo, tangent-space normal, and packed
  AO/roughness/height maps; nine Unreal textures and eight dependent materials save
  cleanly, and focused Python/source checks pass 14/14. The first close-up camera attempt
  was rejected as invalid because the editor view stayed distant; the corrected v280
  guide-camera rescue render passes functionally and is retained as an explicit art
  rejection. The raft coating is a useful reusable technical fallback, while residual
  PFD grain, blank Manny anatomy, generic wardrobe, and procedural raft geometry remain
  below the photoreal bar. No named human, marketing, or release-media approval is
  implied, and the exact-current M8/M9/performance evidence must be regenerated after
  this content change.
- Added five independently morphed, game-engine-rigged CC0 MakeHuman/MPFB production
  fallback bodies for the guide and four crew seats. The GPL MPFB extension remains an
  external build tool; the project stores only generated FBXs/previews, the CC0 source
  atlases and license, and a SHA-256 provenance manifest. Blender now joins the weighted
  eye/brow surfaces into each body and bakes mesh vertices plus rest bones into declared
  centimeter units. The idempotent Unreal importer verifies every source hash, rejects
  stale meter-scale skeletons or promoted detail nodes, records the source hash on each
  asset, assigns four SkeletalMesh-enabled materials, and generates three LODs. Imported
  bodies measure 166.589–172.990 cm, with validated reference head heights of
  145.008–166.538 cm.
- Added a native poseable-mesh production adapter and made the avatar host prefer the
  packaged CC0 bodies before the Manny fallback. The adapter drives the existing rescue
  action set through 20 named bones while the host retains PFD, helmet, boot, paddle, and
  rescue authority. Source-scale, material-usage, helmet fit, and finite-pose regressions
  are now covered. The renderer-backed v287 rescue succeeds, and the exact post-character
  v288 M5 suite passes 4/4 with five CC0 bodies and zero Manny bodies.
- The v287 close-range review is deliberately recorded as
  `technical_fallback_accepted_photoreal_art_rejected`. Human anatomy, skin/eye atlases,
  individual morphology, and rigging materially improve the playable fallback, but hair,
  facial nuance, neoprene/PFD/helmet silhouettes, the procedural raft, and the test-tank
  presentation remain below final photoreal character and marketing-media quality. No
  named human approval is implied. Exact-current M7, performance, M8, M9, Python, and
  Shipping evidence must be regenerated after this content change.
- The exact-current post-character local chain is green. Renderer-backed v291 M7 and
  headless v293 M8 each pass 4/4. The v292 10-second-warmup plus 30-second 1920×1080
  High/60% Development soak samples 2,350 frames at 12.778 ms mean, 13.037 ms workload
  p95, 14.208 ms wall-clock p95, 13.037 ms render-thread p95, and 12.916 ms GPU p95 with
  zero hitches and invalid GPU samples. Solver cost passes at 0.246 ms average and 0.349
  ms maximum; peak memory is 7,335.5 MB. The complete Python/data/source matrix passes
  1,076 tests with three expected installed-dependency-path skips in 360.35 seconds, and
  Shipping-evidence-final v296 M9 passes 4/4. This closes the exact-current local editor/source
  regression gap without changing the fail-closed photoreal, human-review, external
  platform/hardware, distribution-signing/notarization, approved-media, or clean immutable
  promotion status.
- The canonical exact-current v295 macOS arm64 Shipping diagnostic completes successfully
  from the dirty character-updated worktree. It compiles and fully cooks the project,
  packages 641 files including 611 runtime-data files, verifies a valid Apple Development
  signature and App Sandbox entitlement, passes 60/60 packaged rapid cases, 39/39
  three-flow full-reach cases, save/future-version protection, and pristine-profile disk
  persistence. Its 10-second-warmup plus 30-second 1920×1080 High/60% packaged soak
  samples 1,903 frames at 15.751 ms mean and 16.375 ms workload p95 with zero hitches or
  invalid GPU samples; solver cost passes at 0.311 ms average/0.934 ms maximum and peak
  memory is 5,321.6 MB. The verified 1,269,302,214-byte archive has SHA-256
  `c42c7cb6e31e696bd008bac7d2a44886cac8f763ccf908296fdb4cc9e853d26c`.
  This closes the stale local Shipping-engineering gap but remains transient dirty-worktree
  evidence; Developer ID signing/notarization, external-machine/hardware/platform QA, human
  acceptance, approved media, clean-source immutability, and promotion remain open.
- Upgraded the project-owned rescue PPE without compromising the production-character
  adapter or D4 raft authority. The Type-V PFD now uses tapered front cells, a high back,
  fitted side wings, shoulder foam, centre closure, two adjustment/buckle rows, and a lash
  tab. Its 1K ripstop maps now repeat once per roughly 30 cm panel with 0.08 normal
  strength, replacing the rejected sub-millimetre shimmer. A checked-in Unreal Python
  utility refreshes exactly those parameters and v302 proves all four packaged PFD
  materials were found, recompiled, and saved. The helmet now has brow-length open-shell
  coverage, temple/occipital depth, aligned rim, retention, top vent inserts, and distinct
  guide/crew material selection. Runtime acceptance requires substantial vertex geometry
  in every foam, webbing, buckle, shell, rim, and retention layer rather than accepting a
  component name alone.
- The renderer-backed v306 M5 suite passes 4/4 on the exact current worktree. Its retained
  1280×1888 close-up has SHA-256
  `bbb1adffc53b6bca8a8d69b53abbf3fec199f65040b6e2eb3450aa59ac1fc790` and is deliberately
  classified `technical_upgrade_accepted_photoreal_art_rejected`: the equipment is more
  coherent and physically scaled, but the parametric PPE/body integration, limited CC0
  faces, generic wetsuits, flexible procedural raft, and test-tank presentation remain
  visibly synthetic. No named reviewer or media approval is implied.
- The affected local runtime/source/Shipping chain has been requalified after v306:
  renderer-backed v307 M7 and headless v308 M8 each pass 4/4, and the exact-current v309 10-second-warmup
  plus 30-second 1920×1080 High/60% Development soak passes on the required full-reach map
  with 2,283 frames, 13.592 ms workload p95, 14.614 ms wall-clock p95, zero >33 ms hitches,
  zero invalid GPU samples, 0.247 ms average and 0.458 ms maximum solver cost, and
  7,371.5 MB peak memory. After regenerating the source inventory, the exact-current full
  Python/data/source matrix passes 1,078 tests with three expected installed-dependency
  skips in 367.47 seconds, and post-Shipping manifest-sensitive v312 M9 passes 4/4. The
  canonical exact-current v311 dirty-worktree macOS arm64 Shipping workflow also
  passes compilation, full cook/package, Apple Development signature verification, 60/60
  packaged rapid cases, 39/39 three-flow full-reach cases, save/future-version QA,
  pristine-profile persistence, a 2,364-frame 12.915 ms workload-p95 soak with zero
  hitches, archive generation, and artifact verification. The 1,269,286,877-byte archive
  has SHA-256 `ae35e69c928e0ec290a1d3b68de9d697bb7a11f43d285084ededc25082b0c3b3`.
  M9 remains explicitly fail-closed because named-review, external-platform/hardware,
  distribution-signing, notarization, approved-media, clean-immutable-promotion, and
  production-art gates remain open.
- The v317 flexible-raft construction pass preserves D4 deformation authority while adding
  surface-projected lower chafe fabric, bonded D-ring and grab-line pads, thwart collars,
  and five-crown inflated floor relief with surface-derived normals. An initial clipping
  implementation was renderer-rejected and corrected before retention. The isolated v317
  and normal full-reach v318 frames are technically accepted but remain photoreal and
  release-media rejections: the craft is still parametric, hardware and wear are simplified,
  and the calm Chili Bar view does not prove rapid-scale wrap, spray, or wetness quality.
  Exact-current v319 M5, v320 M7, and v321 M8 each pass 4/4. The v322 Development soak
  samples 2,346 frames at 13.049 ms workload p95 and 14.222 ms wall-clock p95 with zero
  hitches/invalid GPU samples, 0.245 ms average/0.265 ms maximum solver cost, and 7,353.2 MB
  peak memory. The complete Python/data/source matrix passes 1,081 tests with three expected
  optional-path skips in 362.46 seconds. Post-Shipping manifest-sensitive v326 M9 passes
  4/4. The
  canonical v325 dirty-worktree macOS arm64 Shipping workflow passes compile, a full
  1,082-package cook/package, 60/60 rapid cases, 39/39 full-reach cases, fresh-profile
  persistence, a 2,352-frame 13.042 ms workload-p95 Metal soak with zero hitches, archive
  creation, signature inspection, and artifact verification. Its 1,269,290,377-byte archive
  has SHA-256 `80bec21059c82a23df6940ed1a2ddca17e743a551c67e2dd16079c4648710756`.
  It remains non-promotable dirty-worktree, non-notarized, same-machine evidence.
- The v418 Meat Grinder evidence capture now places a project-owned, non-colliding
  procedural D4 boulder into the cooked rapid at station 960 m. The genuine live solver
  reports four contacts, three wrapping segments, one pinned and one recovering contact,
  0.220 m indentation, 0.998 runtime wetness, 0.940 spray, 0.320 mist, and full sheet and
  droplet response; the capture path logs those values and never
  writes visual deformation segments. Water material calibration reduces the rejected
  white foreground carpet, the live mesh no longer casts a seam shadow, bounded active
  coverage preserves the authored Single Layer Water, and runtime character/raft material
  instances now receive wetness. This is accepted as source-true technical wrap/contact
  evidence but rejected as final photoreal or release-media art: procedural crew, rock,
  water, and raft construction remain visible.
- The exact-current post-v418 qualification chain passes the native water-surface,
  flexible-raft, VFX, and river-window gates (7/7), renderer-backed M5 and M7 (4/4 each),
  headless M8 (4/4), and post-evidence-refresh M9 (4/4). The final matrix passes 1,083
  Python/data/source tests with three expected optional-path skips in 362.03 seconds.
- The exact-current dirty-worktree macOS arm64 Shipping lane passes compilation, a clean
  Metal SM5/SM6 boulder-material shader cook without default-material fallback, a full
  1,082-package cook/package, 60/60 packaged rapid cases, 39/39 three-flow full-reach
  cases, save and future-version protection, pristine-profile persistence, local Apple
  Development signature verification, archive generation, and artifact verification.
  Its 60-second packaged Metal soak samples 4,612 frames at 13.213 ms workload p95 and
  14.629 ms wall-clock p95 with zero hitches or invalid GPU samples, 0.307 ms average/
  0.596 ms maximum solver cost, and 5,290.0 MB peak memory. The
  1,269,341,500-byte archive has SHA-256
  `28679ffde8415e651fc634ea20e4da65c51b9bdbb442ee39c07ed8e631603d7a`.
  It remains diagnostic same-machine evidence built from an intentionally uncommitted
  worktree and is not Developer-ID-signed, notarized, externally qualified, or promotable.
- The v426 presentation slice replaces the pale, washed-out v418 rapid frame with one
  deterministic response shared by the actual gameplay guide and chase cameras: manual
  nonphysical exposure, 1.75 EV bias, 1.03 saturation, 1.04 contrast, 0.18 sharpening,
  0.04 vignette, and zero film grain. The same source-true D4 wrap state drops mean 8-bit
  luma from 136.3 to 68.8 and near-white coverage from 0.0022 to 0.0003 while retaining
  darker reflective water plus raft and boulder surface detail. Larger procedural spray
  geometry and a CC0-skin subsurface/micro-normal experiment failed to improve the visible
  production result and were fully reverted. The retained frame remains explicitly
  rejected as photoreal because the faces and poses, parametric craft, generated boulder,
  calm-looking contact water, weak spray rendering, and gear integration are still visibly
  synthetic.
- Post-change qualification passes renderer-backed M7 v427 (4/4), headless M8 v429
  (4/4), and focused Python/source tests (26/26). The v430 dirty-worktree macOS arm64
  Shipping workflow passes compilation, a clean 1,082-package cook/package, 60/60 rapid
  cases, 39/39 full-reach cases, fresh-profile persistence, signature inspection, archive
  creation, and artifact verification. Its 60-second Metal soak samples 4,618 frames at
  13.204 ms workload p95 and 14.611 ms wall-clock p95 with zero hitches or invalid GPU
  samples, 0.313 ms average/0.604 ms maximum solver cost, and 5,277.5 MB peak memory. The
  1,269,343,403-byte archive has SHA-256
  `994fb7ce09b2222bd94345d794e7d69ccb41ffed6797cee971cf48bad5a8462c`.
  This is still non-promotable same-machine evidence from the intentionally uncommitted
  M9 worktree; named human, external platform/hardware, distribution signing/notarization,
  approved-media, and clean immutable promotion gates remain open.
- The final v430 evidence-state Python/data/source matrix passes 1,083 tests with three
  expected installed-dependency path skips in 361.10 seconds. Manifest-sensitive v432
  M9 is the final Unreal repeat for this evidence state.
- The v460 contact-water slice repairs the actual short-lived-instance render path by
  replacing per-refresh hierarchical instances with bounded immediate static-mesh
  instances. The maximum-indentation D4 segment supplies the world-space contact anchor;
  the authoritative raft solver, rock contact, collision, and water surface remain
  unchanged. A UV radial/noise soft-card material compiles cleanly for Metal SM5/SM6.
  The retained frame contains 40 fine-spray, one mist, nine contact-foam, and 68 droplet
  cards, and is technically better than v426 while still explicitly rejected for
  photoreal, marketing, store, and press use.
- Exact-current requalification passes focused water VFX 2/2, rendered water 1/1,
  renderer-backed M7 v464 4/4, headless M8 v465 4/4, and manifest-sensitive M9 v467 4/4.
  The complete Python/data/source matrix passes 1,084 tests with three expected optional
  dependency-path skips in 371.36 seconds.
- The v461 dirty-worktree macOS arm64 Shipping workflow passes a clean 1,082-package cook
  including the spray material for Metal SM5/SM6 without default fallback, 60/60 rapid
  cases, 39/39 three-flow full-reach cases, fresh-profile persistence, local Apple
  Development signature inspection, archive creation, and artifact verification. The
  60-second Metal soak samples 4,604 frames at 13.257 ms workload p95 and 14.594 ms
  wall-clock p95 with zero hitches, one rejected GPU sample within the five-sample budget,
  0.303 ms average/0.586 ms maximum solver cost, and 5,289.6 MB peak memory. The
  1,269,410,537-byte archive has SHA-256
  `a928bb877db3cf0be3bd35afe9bf4058b8082675ad6d7e70c87162debc98f3c4`.
  It remains same-machine, dirty-worktree, non-notarized, and non-promotable evidence.
- The v482 contact-water shoulder keeps D4 and the live water surface authoritative while
  making the raft/rock interaction legible as water rather than flat cards. A 9×7 bounded
  procedural mesh samples the live surface at all 63 vertices, displaces only from maximum
  D4 indentation and impact-sheet energy, produces 96 triangles, carries no collision,
  shadow, or navigation authority, and fades to the sampled surface at every edge. Matched
  renderer review accepts the blended v482 result over the separately readable green v469
  patch, but still rejects the broader water, card-like spray, boulder, people, raft, gear,
  poses, and distant terrain seam as final photoreal or release-media art.
- GPU isolation on the exact packaged candidate showed translucency—not terrain, D4, or
  live-water geometry—as the performance regression. The retained spray material replaces
  two-level procedural noise with crossed analytic triangular UV waves and uses
  non-directional volumetric translucency for the overlapping water cards. The v481 clean
  macOS arm64 Shipping cook compiles that material for Metal SM5/SM6 without fallback and
  passes 60/60 rapid cases, 39/39 full-reach cases, fresh-profile persistence, signature
  inspection, archive creation, and verification. Its 60-second soak samples 4,240 frames
  at 15.730 ms workload p95 and 16.052 ms wall-clock p95 with zero hitches or invalid GPU
  samples, 0.303 ms average/3.153 ms maximum solver cost, and 5,280.4 MB peak memory. The
  1,269,374,754-byte archive has SHA-256
  `227b9dac48bcb9d5cbd513a1a41d5fe2e1be78f4ad4addddd0c4d20be87834d1`.
  It remains same-machine, dirty-worktree, non-notarized, and non-promotable evidence.
- Exact-current requalification passes focused water VFX 2/2, rendered water 1/1,
  renderer-backed M7 v485 4/4, headless M8 v486 4/4, and manifest-sensitive M9 v488 4/4.
  The complete Python/data/source matrix passes 1,084 tests with three expected optional
  dependency-path skips in 374.64 seconds.
- The post-v510 shoreline audit replaces broad hidden water quads with a solver-bounded
  presentation completion: only alpha gaps 0.03–0.25 m above decoded terrain are filled,
  and mixed cells may emit only a five-centimetre terrain-clipped bank skirt. Deep dry
  solver gaps and tall banks remain absent. The result carries no collision, navigation,
  or hydraulic authority, reduces authored water from 1,379,312 to 988,032 triangles,
  and records 38,389 completed vertices plus 14,980 bounded transition cells. Native
  shoreline coverage and both Editor/Shipping builds pass, HLOD remains 24/24 with zero
  errors, and the regenerated source inventory contains 46 implementation files, 58,057
  lines, and 37 registered commands with no implementation above the enforced split
  threshold.
- GPU profiling moved High GI from ScreenProbeGather to Unreal's irradiance-volume final
  gather and bounded its startup update to an 8x8 radiance layout and 50 probes. A first
  scene-wide reflection optimization is deliberately rejected by the v515 fixed camera:
  it turned the boulder's upper response black. The corrected v516 review restores opaque
  Lumen reflections and retains only reflection-capture water, half-resolution water
  refraction, and removal of the redundant Single Layer Water distance-field shadow.
  D4 remains authoritative at four contacts, three wrapping segments, one pinned and one
  recovering contact, and 0.220 m maximum indentation. Both frames remain explicit
  photoreal/release-media rejections.
- The v517 macOS arm64 Shipping build linked, fully cooked all 1,082 eligible packages with
  no ignored scalability CVars, and passed its packaged functional gates. Its first cooled
  canonical minute passed at 15.649 ms workload p95 with zero hitches, but the independent
  confirmation run crashed after 55.057 seconds with `EXC_BAD_ACCESS`/`SIGSEGV` in the
  game-thread `EvaluateOverwashFlipD3` transient response-map rehash. No report was written.
  The candidate is therefore superseded rather than qualified; the passing first minute is
  retained only as performance evidence and cannot mask the stability failure.
- The v520 correction removes the per-substep `TMap<FString, response*>` allocation from D3
  and D4 response lookup, keeps SegmentId-keyed behavior when response order differs, and
  reserves the D3 output array. A native regression passes 20,000 consecutive retained-water
  evaluations with reversed response order. Editor and Shipping builds pass, all 1,082
  eligible packages cook, and the corrected locally signed app passes 60/60 rapids, 39/39
  full-reach cases, all 14 keyboard/gamepad actions, save/future-version protection, and
  pristine-profile persistence. Two independent v520 rendered minutes pass with zero
  hitches and normal exits, closing the locally reproducible v517 crash. The saturated-host
  Low control remains recorded; no quality reduction or gate weakening is accepted on that
  basis.
- Renderer-backed M4/P2 then exposed a handled Lumen ensure: the configured irradiance
  probe resolution was 8 while occlusion stayed at its default 16. v527 pairs both at 8,
  retains the 50-probe update budget, and adds fail-closed source coverage for all three
  values. Corrected P2 v524 passes 1/1, M5 v525 and M7 v526 pass 4/4, and M4 v528 passes
  2/2 with no Lumen ensure; only Unreal's existing motion-vector warning remains.
- The fresh v527 Shipping package compiles and fully cooks 1,082 of 1,089 discovered
  packages with seven platform skips. Packaged QA passes 60/60 rapid-flow cases, 39/39
  full-reach cases, all 14 keyboard/gamepad actions, save migration/future-version
  protection, and all nine pristine-profile gates. The packaged bundle contains 641 files
  and 611 runtime-data files.
- Six canonical `-RenderOffScreen` performance diagnostics are deliberately retained:
  three pass and three fail the zero-hitch gate with 85, 19, and 4 wall-clock hitches.
  Solver, memory, and GPU-timing gates pass in every run, but the aggregate v2 report cannot
  prove an OS scheduling cause, so that presentation path is not release-qualified. Two
  cooled normal-window Metal runs launched through the packaged app pass independently at
  13.278 and 13.747 ms workload p95, zero hitches, 0.511/0.634 ms average solver time,
  0.815/1.026 ms maximum solver time, and 5,281.5/5,291.1 MB peak memory. This
  player-representative protocol qualifies local macOS gameplay performance without
  weakening the hitch gate.
- The v527 finalizer consumes five passing QA reports and creates a 1,272,361,448-byte
  archive with SHA-256
  `4f92bc38bec8cac643c656fd547b9ee79b7843d732b2132fe0d6328fd0812d53`.
  Independent verification passes. Signature inspection correctly reports `adhoc` with no
  team identifier, so Developer ID signing and notarization remain open rather than being
  overstated.
- Final local qualification passes M8 v529 at 4/4, manifest-sensitive M9 v532 at 5/5,
  and the complete Python/data/source matrix at 1,086 passed with three expected skips in
  389.83 seconds. The source inventory remains 46 implementation files, 58,057 lines, and
  37 registered commands with no implementation file above 3,000 lines.
- M9 remains fail-closed and uncommitted: final photoreal people, raft, water, rocks,
  foliage, and terrain are not accepted; all five named human reviews, fresh external Mac
  input runs, Windows RTX 3060/4070, Authenticode, Proton, Developer ID/notarization,
  approved rights-cleared media, and a clean immutable rebuild/promotion are still open.
- The v552 boulder slice replaces the nearly spherical procedural fallback with a
  deterministic multiharmonic profile, shouldered crown, corrected tangent handedness,
  and a project-owned mineral material branch. The optional CC0 scan remained non-visible
  across camera, water, Nanite, culling, and fallback-mesh diagnostics, so every diagnostic
  override was removed and the scan remains disabled behind its rights/geology/guide/art/
  performance gate. The final renderer capture retains four D4 contacts, three wrapping
  nodes, one pin, one recovery, and 0.220 m indentation, proving the correction did not
  change solver, collision, hydraulic, or navigation authority. It is a bounded technical
  improvement only: the dark rock, procedural crew/gear/raft, broad water, lighting,
  shoreline, and VFX still fail photoreal review. This source/material delta also makes the
  prior v527 Shipping package, performance soak, and archive historical; they must be
  regenerated before any promotion attempt. Exact-current validation passes renderer M4
  v553 2/2, M5 v554 4/4, M7 v555 4/4, headless M8 v556 4/4, fail-closed M9 v557 5/5,
  focused source/release tests 23/23, and the complete Python/data/source matrix at 1,086
  passed with three expected optional-path skips in 369.42 seconds.
- The v559 crew-pose slice corrects the dominant torn/intersecting high-side silhouettes by
  moving shoulders, hips, knees, and progressively planted feet with the torso and head.
  It does not change crew commands, reaction timing, D4 weight action, contact, or rescue
  authority. The matched source-true frame retains four contacts, three wrapping nodes, one
  pin, one recovery, 0.220 m indentation, and 0.998 wetness. Exact-current validation passes
  renderer M4 v560 3/3, M5 v558 4/4, M7 v561 4/4, headless M8 v562 4/4,
  manifest-sensitive M9 v563 5/5, and the complete Python/data/source matrix at 1,086
  passed with three expected optional-path skips in 362.70 seconds. The figures are now
  coherent technical stand-ins, but faces, hands, helmet/PFD fit, generic clothing, raft,
  boulder, broad water, lighting, shoreline, spray, and terrain still fail photoreal and
  release-media review. M9 therefore remains fail-closed, uncommitted, and unpushed.
- The v570 character-adapter slice fixes the degenerate terminal `head → head` segment:
  when no child endpoint exists, the CC0 adapter now derives a reference direction from
  the bone's own up axis, so heads rotate with the same high-side pose as their helmets.
  A CC0-only 1.18 shell allowance reduces scalp intersection without changing the
  procedural fallback. The matched source-true frame preserves the same four contacts,
  three wrapping nodes, one pin, one recovery, 0.220 m indentation, and 0.998 wetness.
  Exact-current validation passes renderer M4 v572 3/3, M5 v571 4/4, M7 v573 4/4,
  headless M8 v574 4/4, manifest-sensitive M9 v575 5/5, and the complete matrix at
  1,086 passed with three expected skips in 364.44 seconds. Facial anatomy, hands,
  residual helmet/PFD fit, clothing, raft, rock, water, lighting, shoreline, spray, and
  terrain still fail photoreal review, so M9 remains fail-closed and uncommitted.
- The current v601 technical baseline retains the v579 rights-tracked Hair02 and
  parent-to-head shaft correction, v587 source-restored procedural boulder, and v595
  low-discrepancy spray distribution. The v594 broad-water roughness experiment and v599
  generated world-aligned granodiorite material were rejected for exposed-riverbed and
  near-black/faceted regressions; v600 removes the rejected runtime texture reference while
  retaining its generated PNG and provenance only as unpromoted source art. v601 then
  routes only the packaged CC0 body's wetsuit slot to the existing physically scaled
  generated-neoprene material with skeletal usage, reducing the chrome-gray limb response
  while retaining every licensed variant skin, eye, and hair atlas. The renderer frame
  records four contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.999
  wetness, a 63-vertex/96-triangle contact-water patch, 39 spray cards, one mist card, nine
  contact-foam cards, and 68 droplets. Focused v601 source/acceptance guards pass 31/31;
  the UE 5.8 editor target builds cleanly.
  v601 is accepted only as a narrow character-material improvement: people, gear, raft,
  rock, water, lighting, shoreline, terrain, external reviews, platform qualification,
  signing, notarization, and approved media remain open, so M9 remains uncommitted and
  unpushed.
- The v606 runtime-presentation slice retains v601 and restores the clear-weather
  captured-scene skylight toward the map-authored level: dry/wet endpoints are now 1.25
  and 0.62, applying 1.2185 at the clear-morning preset. The matched source-true frame
  preserves four contacts, three wraps, one pin, one recovery, 0.220 m indentation,
  0.999 wetness, a 63-vertex/96-triangle contact-water patch, 39 spray cards, one mist,
  nine contact-foam cards, and 68 droplets. Mean frame RGB rises from
  `[61.652, 70.477, 73.165]` in v601 to `[66.819, 77.720, 82.921]`, retaining more
  backlit crew, raft, and rock information. The v603 live-surface coverage, v605
  lifted-mineral/roughness, and v608 diffuse-only experiments were rejected and exactly
  restored. UE 5.8 builds
  cleanly, the focused source/acceptance set passes 31/31, M5 v604 passes 4/4 before the
  lighting delta, and exact-current M7 v607 passes 4/4 with a new skylight-bound assertion.
  v606 remains rejected as photoreal and M9 stays fail-closed, uncommitted, and unpushed.
- The v610 raft-material slice adds a focused `RaftSim.CreateProductionRaftMaterials`
  authoring command and explicit static-mesh shader usage for tube/floor packages. The
  v609 regeneration without that usage rendered a white/default raft and was rejected.
  Corrected v610 preserves the authored red craft while raising only saturated wet-film
  roughness scale/maximum from 0.34/0.32 to 0.46/0.40. Its source-true frame retains four
  contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.999 wetness, a
  63-vertex/96-triangle contact-water patch, 39 spray cards, one mist, nine contact-foam
  cards, and 68 droplets. Focused inventory/material/release guards pass 25/25, the UE 5.8
  editor build used for the focused authoring command succeeds, and exact-current rendered
  M7 v611 passes 4/4. This is a bounded technical improvement only: the raft's parametric
  construction and broad highlight, plus the people, PPE, rock, water, aerosol, shoreline,
  terrain, and lighting still fail the photoreal gate. M9 remains fail-closed, uncommitted,
  and unpushed.
- The v613 production-skin slice adds a focused
  `RaftSim.CreateProductionCC0SkinMaterials` authoring command for only the five CC0 skin
  packages. It retains every rights-tracked 2K MakeHuman atlas, skeletal mesh, rig, and
  material slot while adding 36× neutral microdetail, restrained 0.16 normal response,
  0.46–0.58 roughness, and near-opaque preintegrated skin. The first v612 broad-subsurface
  branch made hands orange and was rejected. Corrected v613 retains four contacts, three
  wraps, one pin, one recovery, 0.220 m indentation, 0.999 wetness, a 63-vertex/96-triangle
  contact-water patch, 40 spray cards, one mist, nine contact-foam cards, and 68 droplets.
  The focused character/material/evidence slice passes 33/33, UE 5.8 builds cleanly, and
  exact-current rendered M5 v614 and M7 v615 each pass 4/4. Character topology, facial
  expression/animation, hands, hair/PPE integration, poses, and the remaining raft, rock,
  water, aerosol, shoreline, terrain, and lighting gaps still fail photoreal review. M9
  remains fail-closed, uncommitted, and unpushed.
- The v621-v624 contact-water investigation leaves no unreviewed visual branch promoted.
  A bounded 13×9 split-flow shoulder and dedicated surface-lit material compiled, authored,
  and preserved D4 state, but matched review rejected v621's absent hero response, v622's
  contact-port glass shell, and v623's triangular foam sail. v624 removes the temporary asset
  and all repository references, restores the 9×7/63-vertex/96-triangle shared-card baseline,
  and records four contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.998
  wetness, 40 spray cards, one mist, nine contact-foam cards, and 68 droplets. The restored UE
  target builds, focused source/acceptance checks pass 25/25, restored water-VFX automation
  passes 2/2, and exact-current rendered M7 v626 passes 4/4. This is restoration evidence,
  not a visual upgrade; production water art remains open and M9 stays uncommitted/unpushed.
- The v627-v632 crew-equipment slice removes the high-side pose's explicit five-paddle
  disappearance. The retained pose keeps both hands on each shaft, carries each paddle toward
  the commanded tube, and adds a collision-free convex blade plus transverse T-grip to the
  project-owned gear host. v629's full-scale outside extension is rejected for dominating the
  close camera; v631's compact version is rejected as final evidence because most blades render
  edge-on. Retained v632 controls the feather angle and records the same source-true four
  contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.998 wetness, 40 spray
  cards, one mist, nine contact-foam cards, 68 droplets, and 96-triangle contact-water patch.
  UE 5.8 builds, exact-current M5 v634 passes 4/4, and rendered M7 v633 passes 4/4. This is a
  technical rafting-action readability upgrade, not photoreal acceptance; M9 remains
  fail-closed, uncommitted, and unpushed.
- The v635-v642 live-surface slice closes a presentation-parity defect: the moving D3
  overlay now reapplies the exact deterministic displacement and analytic slopes authored
  into the seasonal river instead of flattening covered standing-wave shoulders. It
  retains the 3 m grid, 15 Hz update, no-collision policy, deterministic phase, and all
  D3/D4/raft/rescue authority. Focused v641 automation passes 1/1 with a 1.8 cm calm-water
  maximum; the initial South Fork patch reaches 3.19 cm. A separate v638-v640 D4 contact-
  pillow bracket reached 17.38 cm on the 3 m mesh and 19.22 cm on a 1.5 m mesh, but both
  produced a tan triangular surface sail. That API, implementation, diagnostics, tests,
  and 1.5 m setting were fully removed. The retained v642 frame records four contacts,
  three wraps, one pin, one recovery, 0.220 m indentation, 0.999 final-frame wetness, 39
  spray cards, one mist, nine contact-foam cards, 68 droplets, and the 96-triangle contact
  patch. Exact-current M5 v644 and rendered M7 v643 each pass 4/4. This preserves authored
  water detail but does not create convincing large-scale hydraulics; broad water, people,
  PPE, raft, boulder, aerosol, shoreline, terrain, and lighting still fail the photoreal
  gate, so M9 remains fail-closed, uncommitted, and unpushed.
- The v647-v663 named-rapid slice closes a larger data-parity defect: seasonal authored
  water had remained on the transit seed while runtime physics selected cooked rapid D3
  windows. Environment v25 composites all 20 validated windows and three flow bands into
  the continuous water with the runtime's 64 m handoffs. At Meat Grinder station 960 m,
  the saved median surface now matches 446.568919 m instead of the 446.005981 m transit
  value, removing a 0.562938 m visual/physics mismatch without changing D3, D4, raft, or
  rescue authority. v648 exposed the newly correct field as a broad foam carpet; v650's
  all-surface breakup made the river disappear and was removed. Retained v663 applies
  finer, lower-energy breakup only to foam color/opacity while full solver coverage still
  drives roughness and ripple normals. The first exact-current M7 run then exposed and led
  to repair of a hitch-to-zero paddle audio envelope; focused audio v660 passes 1/1 and
  exact-current M7 v661 and M5 v662 pass 4/4 each; exact-current fail-closed M9 v665 passes
  5/5. v663 remains photoreal-rejected because
  large-scale crest/hole/wave-train geometry and the people, PPE, raft, boulder, aerosol,
  shoreline, terrain, and lighting remain visibly synthetic. M9 therefore stays fail-
  closed, uncommitted, and unpushed.
- The exact-current HLOD and local validation closure now follows the v663 technical
  baseline. v668 rebuilt all 24/24 HLOD actors with zero errors; an initial v669 repeat
  exposed two still-settling packages, and v670 then evaluated all 24 actors with zero
  modified packages and zero errors. Finalized evidence hashes every current HLOD package,
  and the focused evidence suite passes 6/6. M4 v666 passes 3/3, M5 v662 passes 4/4,
  M7 v661 passes 4/4, M8 v667 passes 4/4, and the post-HLOD Python/data/source matrix
  passes 1,092 tests with three expected skips in 406.19 seconds. The manifest-sensitive
  manifest-sensitive M9 v672 rerun passes 5/5 after this evidence reconciliation. These
  green technical gates
  do not change the v663 photoreal rejection or satisfy the human, rights, geospatial,
  platform, signing, approved-media, clean-build, or exact-current Shipping gates; M9
  remains fail-closed, uncommitted, and unpushed.
- The v673-v681 solver-relief slice addresses the next bounded water-geometry gap without
  inventing a new hydraulic authority. The live overlay samples each cooked vertex once,
  removes the local linear grade with a symmetric 12 m station stencil, and amplifies only
  the remaining solver-resolved crest/hole curvature under depth-, speed-, and Froude-
  bounded activation. Unit/renderer checks prove exactly zero relief for linear-grade and
  calm water; the source-true v675 Meat Grinder run records 0.2624 m maximum relief,
  0.1909 m maximum retained standing-wave displacement, a 26.02 cm increase in the live
  surface vertical range, and the unchanged final four contacts, three wraps, one pin, one
  recovery, and 0.220 m indentation. The UE 5.8 editor target builds, focused water-surface
  v673 passes 1/1, M4 v676 passes 3/3, M5 v677 passes 4/4, M7 v678 passes 4/4, M8 v679
  passes 4/4, the v680 matrix passes 1,092 tests with three expected skips in 376.73
  seconds, and fail-closed M9 v681 passes 5/5. This is retained technical art development,
  not photoreal acceptance: the surface cannot overturn or form a true breaking lip, foam
  and aerosol remain procedural, and every existing character, PPE, raft, boulder,
  shoreline, terrain, lighting, human-review, platform, signing, media, clean-build, and
  exact-current Shipping blocker remains open. M9 is still uncommitted and unpushed.
- The v682-v705 visual-water investigation leaves the reviewed v675 production material
  byte-for-byte intact at SHA-256 `dd615ad20fd70cea6f5b492ae65dbe998729107fc92d90d1be703cdedea468d1`.
  v682-v685's auxiliary folded breaking lip compiled and activated but rendered as long
  triangular white sheets, so all of its geometry, tests, diagnostics, and capture controls
  were removed; restored water-surface automation v686 passes 1/1. v687-v692's panned-noise
  and packed-mask foam branches removed the reviewed aeration field and were likewise fully
  rejected. Exact package recovery, focused source/release checks, native compilation,
  water-surface v693, and source-true v694 prove the v675 baseline was restored. The retained
  v695-v699 tooling adds an isolated `/Game/RaftSim/Experiments` material authoring command,
  a capture-only `watermaterial=` override applied before the evidence timers start, and a
  read-only canonical graph audit. With equal settling time, v698 visually matches the
  production water and v699 proves both materials contain 93 canonically identical material
  expressions and matching material properties. Finally, v700-v704's physically scaled
  river-UV noise first failed its float2-to-float3 shader contract, then produced long ruler-
  straight foam lanes and multi-second rendered-frame stalls after correction. That preview
  asset is quarantined and the recipe is restored; the retained editor target builds,
  focused source/release checks pass 19/19, water-surface v705 passes 1/1, and the production
  package hash remains unchanged. The full v707 Python/data/source matrix passes 1,093 tests
  with three expected dependency-path skips in 871.79 seconds, and the final manifest-aware
  fail-closed M9 v708 pass is 5/5. This closes an unsafe visual-iteration workflow, not the
  photoreal-water gate: the reviewed foam is still visibly cellular and production water art
  remains open, so M9 stays uncommitted and unpushed.
- The v709-v730 reviewed-rock investigation isolates the invisible CC0 scan without changing
  production selection. Submergence, reverse-culling, and Nanite-fallback hypotheses were
  rejected and reverted. A newly downloaded official Poly Haven 1K bundle matches the four
  already recorded source hashes exactly; a clean experiments-only import renders all six
  meshes with 1× LOD build scale while the capture-only actor bounds-normalizes the source-
  sized geometry into the existing contact envelope. The retained `rockmesh=` diagnostic and
  read-only audit verify rock 04's 10,588 triangles, one valid atlas UV channel, active
  base/normal/roughness textures, and 1024×1024 decoded base pixels within four code values of
  the source JPEG. v714-v727 remain art-rejected because the fixed South Fork light/exposure
  response clips the scan toward pale gray and the normal rapid view is covered by the
  intended contact-water patch. All assets remain under `/Game/RaftSim/Experiments`, the
  importer reports `production_promoted: false`, ordinary gameplay/D4/collision/raft/rescue
  behavior is unchanged, and geology, guide, art, and performance approval remain open.
  The v731 exact-current matrix passes 1,095 tests with three expected skips, and the
  manifest-sensitive fail-closed M9 v732 pass is 5/5. M9 remains fail-closed, uncommitted,
  and unpushed.
- The v733-v735 presentation slice rejects a static crew chin-tuck experiment after two
  matched renders failed to materially correct guide gaze; all five source/test hunks were
  removed before retention. v735 instead narrows the visible contact-water defect by keeping
  the existing 9x7/63-vertex/96-triangle solver-driven patch while reducing only its runtime
  opacity and crossed-wave contrast. The matched frame replaces the bright cellular quilt
  with a softer aerated fan and preserves four contacts, three wraps, one pin, one recovery,
  0.220 m indentation, full wetness, and 41/1/9/68 spray/mist/contact-foam/droplet instances.
  The UE 5.8 editor target builds, focused source checks pass 7/7, M4 v735 passes 3/3,
  M5 v736, M7 v737, and M8 v738 pass 4/4 each, the qualified v741 full Python/data/source
  matrix passes 1,095 tests with three expected skips and zero failures, and fail-closed M9
  v742 passes 5/5.
  This is a technical presentation improvement only: the water, people, PPE, raft, boulder,
  shoreline, terrain, lighting, and release-media frame remain photoreal-rejected. The local
  technical evidence chain is exact-current; M9 remains uncommitted and unpushed because
  human/external acceptance, photoreal art, package, signing, and release gates remain open.
- The v744-v753 production-character slice proves authenticated UE 5.8 auto-rig, texture
  download, and Optimized/Medium assembly in a disposable pilot, then rejects its rendered
  checkerboard face/body and absent hair/brows because MetaHuman Creator Core Data is not
  installed. The retained shipping bridge instantiates final assembled actors without losing
  face RigLogic, grooms, eyelashes, wardrobe, or baked materials, drives their bodies from the
  deterministic rafting pose solve, always cooks the production roster, and promotes only
  when all five exact Blueprint packages exist and initialize correctly. A reproducible
  editor script now performs Core Data preflight, authors five distinct identities, requests
  production rig/textures, assembles, and records token-free provenance. v750 fails closed on
  zero Optional assets and the five genuinely missing Core Data categories without creating
  partial art. A cold v751 run exposed a fixed-wall-clock rescue-test flake, and v752 isolated
  an unrelated UE 5.8 offscreen Mac IME teardown error; the retained gate now waits on the
  actual authoritative rescue phase with a bounded timeout and suppresses only that engine
  log. UE 5.8 builds cleanly and exact-current renderer-backed v753 passes all four M5 tests.
  The architecture is retained, but
  M9 remains uncommitted/unpushed until Core Data is installed, all five characters build,
  in-raft hero captures pass photoreal review, and every remaining art/human/external gate
  closes.
- The production-roster completion slice installs MetaHuman Creator Core Data and replaces
  the disposable pilot with five distinct Optimized/High builds: one guide and four crew,
  each with 84 validated local build files, exact Blueprint activation, baked face/body
  materials, brows/lashes, audited helmet-compatible hair source, and cooked-only release
  distribution. Runtime composition now requires cropped face skin, wetsuit body, visible
  PFD/helmet/retention gear, and paddle as one all-or-nothing presentation. Matched captures
  exposed three defects that turntables hid: two-sided PFD self-shadowing, a face-apron seam,
  and helmets that either culled or detached during high-side/rescue poses. The retained path
  uses stable dyed PFD materials, the V2 cropped-face hierarchy, solved-head helmet alignment,
  corrected crown fit, and atomic procedural-PPE/MetaHuman action transitions. The UE 5.8
  editor target builds; focused character/safety checks pass 11/11; renderer-backed M4, M5,
  and M7 pass 3/3, 4/4, and 4/4; M8 passes 4/4; the full matrix passes 1,095 tests with three
  expected skips in 370.70 seconds; and the post-inventory fail-closed M9 suite passes 5/5.
  The new material work was also split behind a focused 130-line texture-authoring boundary,
  restoring the 3,000-line source cap and passing all 19 layout/inventory checks. The v6
  Meat Grinder evidence accepts the High roster and runtime integration technically but
  rejects photoreal and marketing use: helmet/PFD construction, body/hand/paddle/gaze/facial
  performance, raft, boulder, water, foam/aerosol, shoreline, terrain, and lighting remain
  visibly synthetic. M9B.2 is complete; M9B.3 remains in progress, and M9 stays fail-closed,
  uncommitted, and unpushed pending photoreal replacement plus named human and external
  platform/signing/media acceptance.
- The first M9B.3 PPE follow-up audited public whitewater helmet/PFD sources and found no
  immediately usable CC0 production model: current candidates are paid, noncommercial,
  generic marine gear, attribution-licensed, or account-gated. No external model was copied
  into the project. The project-owned fallback now builds and audits five opaque two-sided
  helmet materials and maps four visible crew colors plus the guide color deterministically;
  focused source/layout checks pass 30/30, the editor target builds, the material audit
  succeeds, and renderer-backed M5 remains 4/4. The matched v7 frame improves crew/PPE
  identification but still reads as smooth procedural caps, so it is retained only as a
  readability baseline and remains photoreal-rejected pending replacement helmet geometry.
- The next M9B.3 slice replaces that cap with project-owned production source art: a
  24,508-triangle asymmetric molded shell, six physical cut-through vents, EPP liner,
  lower gasket, four-point retention, ear pads, adjusters, fasteners, and buckle. A
  deterministic Blender generator, editable `.blend`, exported FBX, source hash manifest,
  fail-closed Unreal importer, four material slots, and a 2,126-triangle Nanite fallback
  make the asset reproducible without external mesh or texture input. All five Optimized/
  High MetaHuman wrappers now select the static helmet atomically, suppress the procedural
  cap when it loads, and preserve the measured solved-head pose contract; the maximum
  five-character fit error is `1.154e-9` cm. The procedural helmet remains a load-failure
  fallback, and D3/D4, rescue, collision, and deformation authority are unchanged. v8 was
  rejected because oversized merged openings read as a broken crown. The corrected v9
  retains continuous shells and separated vents with dark liner behind them. Focused
  source/layout tests pass 22/22 and exact-current renderer-backed M5 passes 4/4 with no
  Nanite/default-material warnings. The asset is accepted as a production-geometry and
  runtime-integration upgrade, but the shell finish and the surrounding PFD/body/hand/
  paddle/pose, raft, boulder, water, aerosol, shoreline, terrain, and lighting remain below
  the photoreal bar. The v9 frame is explicitly rejected for marketing or release-media
  use; M9B.3 remains in progress and M9 remains fail-closed, uncommitted, and unpushed.
- The production-raft M9B.3 slice replaces the smooth parametric rest silhouette with an
  editable, deterministic Blender/FBX asset calibrated from current 14-foot self-bailer
  manufacturer dimensions and construction facts. No commercial mesh, texture, branding,
  or product image is copied. The 38,344-triangle, 431.8×205.8×72.5 cm rest mesh has five
  audited material sections, kicked ends, four chamber seams, two inflatable thwarts, an
  inflated self-bailing floor, perimeter line, reinforcement pads, twelve D-rings, four
  quarter handles, four tube valves, a floor relief valve, and eight drain recesses. v1 was
  corrected after direct renderer review found oversized rings/pads and crossed handles;
  v2 reduces those miniature cues and better fits the crew. At runtime the cooked asset is
  CPU-readable and copied once into the existing collisionless procedural component. The
  ordinary D4-derived field then moves the authored chamber, floor, rigging, metal, and
  bonded-detail vertices; the hidden hull, collision, buoyancy, flip, wrap, pin, damage,
  and rescue authority are unchanged. Exact-current M5 passes 4/4 and explicitly verifies
  production selection, stable five-section topology, finite D4 deformation, and more than
  30,000 authored triangles. The v12 Meat Grinder frame retains four contacts, three wraps,
  one pin, one recovery, 0.220 m indentation, 0.999 wetness, and 40/1/9/68 spray/mist/
  contact-foam/droplet instances. It is accepted as production geometry and flexible-runtime
  integration, but rejected as final photoreal art because the saturated tube highlight,
  crew seating/hands/paddle/pose, boulder, water/aerosol, shoreline, terrain, foliage, and
  lighting remain visibly synthetic. M9B.3 remains in progress; M9 remains fail-closed,
  uncommitted, and unpushed.
- The production-rescue-PFD M9B.3 slice replaces all four procedural vest layers on the
  guide and four crew with one project-owned, editable Blender/FBX asset. The retained v3
  source is 42.2×44.9×44.9 cm with 21,180 authored triangles, a 2,168-triangle Nanite
  fallback, and five audited material sections. Its separate construction includes four
  front foam panels, a thin back, side wings, continuous shoulder bands, two pockets,
  front zip, two backup buckles and webbing runs, eight adjustment points, a quick-release
  rescue belt, tether ring, reflective zones, placard, and lash tabs. Project-owned 1K
  PfdRipstop albedo, normal, and AO/roughness maps replace the flat shell colors. All five
  production MetaHuman wrappers select the asset with exactly 0.0 cm measured torso-origin
  error while body animation, seat mass, D3/D4, rescue, swimmer, and progression authority
  remain unchanged. Focused source/runtime tests pass 22/22 and exact-current renderer-
  backed M5 passes 4/4 with no Nanite/default-material warnings. The v13 Meat Grinder frame
  retains four contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.999
  wetness, 40/1/9/68 spray/mist/contact-foam/droplet instances, and a 96-triangle contact
  patch. This is accepted as a reproducible safety-gear and runtime-integration upgrade,
  but the shoulder/front surfacing and surrounding crew, raft, boulder, water/aerosol,
  shoreline, terrain, foliage, and lighting remain photoreal-rejected. M9B.3 remains in
  progress; M9 remains fail-closed, uncommitted, and unpushed.
- The production-boulder M9B.3 slice replaces the ordinary 1,632-triangle presentation
  shell with a project-owned 81,920-triangle closed Blender/FBX mesh and a 1,766-triangle
  Nanite fallback. The v2 source localizes three physical fracture bands, retains two
  water-worn facet fields, and fits the collisionless visual to 96% of the existing D4
  contact envelope. A dedicated dark wet-mineral material prevents the production asset
  from entering the quarantined reviewed-scan texture branch. The production component is
  visible while both the procedural fallback section and optional reviewed scan remain
  hidden; D4 radius, friction, contacts, wrap, pin, raft, water, and rescue authority are
  unchanged. v14-v19 were rejected while isolating imported-source selection, global
  crown-fracture petals, and uncached white shader frames. The cached v20 frame retains
  four contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.999 wetness,
  a 96-triangle contact patch, and 40/1/9/68 spray/mist/contact-foam/droplet instances.
  Focused source/release checks pass and exact-current renderer-backed M5 passes 4/4. The
  geometry and runtime boundary are accepted technically, but large-scale mineral mottling,
  broad facets, non-site-specific geology, and the surrounding water/crew/raft/environment
  remain photoreal-rejected. M9B.3 remains in progress; M9 remains fail-closed,
  uncommitted, and unpushed.
- The flow-aligned whitewater M9B.3 slice replaces the broad-water material's generic
  world-space cellular foam breakup with a deterministic project-owned 1K source mask.
  The v3 texture contains 168 bounded, curved, softened fragments with a maximum authored
  length of 108 pixels, mirrored addressing, physically scaled river-coordinate UVs, and
  slow downstream pan. It is multiplied by the existing conditioned solver foam, so no
  texture value can create whitewater outside the hydraulic mask; live sampling, surface
  geometry, D3, D4, raft, collision, and rescue authority are unchanged. Roughness now uses
  the same broken foam rather than the full broad mask. v21 was rejected for replacing the
  former cracked-cell carpet with ruler bands; v22 remained too densely parallel; v23 was
  shader warm-up only. The cached v24 frame removes the cracked-sheet artifact and dense
  speed-line field while retaining four contacts, three wraps, one pin, one recovery,
  0.220 m indentation, 0.999 wetness, the 96-triangle contact patch, and 40/1/9/68 spray/
  mist/contact-foam/droplet instances. The UE 5.8 editor target builds, all 20 layout/source
  checks pass, exact water-surface automation passes 1/1 with known warnings, and exact-
  current M5 passes 4/4. This is retained as a technical improvement, not final art:
  remaining laces are still too clean/linear, the water is a non-overturning heightfield,
  and crest/hole/pile volume plus spray/mist remain below the photoreal bar. M9B.3 remains
  in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The microdroplet-water-VFX M9B.3 slice retains the v24 solver-masked broad-water foam and
  existing solver/contact-derived VFX classifier, trajectories, bounded instance pools,
  63-vertex/96-triangle contact-water patch, contact foam, and all D3/D4/collision/raft/
  rescue authority. It lowers fine-spray/mist/rapid-aerosol/droplet opacity and emissive
  response while making the cards smaller and denser. At the matched Meat Grinder state,
  the deterministic visible populations become 91/5/9/144 fine-spray/mist/contact-foam/
  droplets; the right-side spray reads as a faint microdroplet cloud instead of a large-
  card necklace. The UE 5.8 editor target builds, focused source guards pass 32/32, and
  exact-current renderer-backed M4 and M5 pass 3/3 and 4/4. v25 is retained as a bounded
  technical presentation improvement, not final art: analytic planes remain visible at
  hero distance, production volumetric breakup/lighting/collision is absent, and no named
  guide or art reviewer has approved it. M7, M8, the full Python/data/source matrix, M9,
  packaging, and release evidence remain stale or pending. M9B.3 remains in progress; M9
  remains fail-closed, uncommitted, and unpushed.
- The bounded-local-exposure M9B.3 slice replaces the shared guide/chase/evidence camera's
  +1.75 EV response with +1.25 EV plus bilateral highlight/shadow compression. Highlight
  contrast 0.78, shadow contrast 0.72, detail strength 1.0, and a 50% blurred-luminance
  blend with a 50% screen kernel retain more wet coated-fabric detail, reduce the clipped
  raft band, and recover face/PFD/wetsuit shadows in the cached v29 matched frame. No scene
  light, material, weather, water, D3, D4, collision, raft, or rescue state changes. v26
  (+1.00 EV) was too dark, v27 isolated +1.25 EV, and v28 was shader warm-up only. The UE
  5.8 editor target builds; focused source guards pass 33/33; exact-current M4, M5, and M7
  pass 3/3, 4/4, and 4/4. The improvement is accepted technically but remains photoreal-
  rejected: manual exposure is still non-physical, raft response is synthetic, and the
  remaining character/water/rock/environment art has not passed named guide or art review.
  M8, the full Python/data/source matrix, M9, packaging, and release evidence remain stale
  or pending. M9B.3 remains in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The production-river-boot M9B.3 slice replaces both blunt rounded procedural footwear
  overlays on each of the five production characters with a project-owned, deterministic
  Blender/FBX asset. The 33.34×13.5×23.575 cm source contains a lasted shell, cuff, outsole,
  toe/heel rands, pull tab, twelve tread lugs, and three vamp bands across 9,708 authored
  triangles and three material sections; Unreal retains a 1,704-triangle Nanite fallback.
  Both collisionless static components follow the existing solved foot positions and
  roster scale, while the procedural boots remain available for missing-asset or
  procedural-body fallback. Animation, crew mass, D3, D4, collision, raft, rescue, and
  progression authority are unchanged. The UE 5.8 editor target builds, the focused source
  slice passes 34/34 before release-packet expansion, and exact-current M5 passes 4/4. Its
  first run is retained as negative test evidence because the original assertion confused
  Nanite fallback triangles with the authored FBX topology; the corrected v2 run separates
  those contracts. A dedicated material lane reuses the rights-tracked 1K WetsuitNeoprene
  maps for the upper and adds a separate bounded rubber graph for the sole and rand. A clean
  reimport temporarily disables prior Nanite state so the authored audit measures 9,708
  FBX triangles, then restores a 1,704-triangle fallback and all three material assignments.
  v31 and v33 were rejected for an over-gray plastic read; v32 was shadow-biased; the v34
  matched frame accepts the removal of the cylinder silhouette and distinct dark-neoprene
  toe/cuff/sole response as a technical upgrade, but rejects generated surface detail,
  rigid yaw-only ankle placement, surrounding body/hand/paddle contact, raft,
  rock, water, terrain, foliage, and lighting as final photoreal art. M4, M7, M8, the full
  Python/data/source matrix, M9, packaging, and release evidence are stale or pending after
  v34; water-surface and HLOD evidence remain content-current. M9B.3 remains in progress;
  M9 remains fail-closed, uncommitted, and unpushed.
- The articulated-paddle-grip M9B.3 slice closes the flat imported finger-pose gap on all
  five production MetaHuman wrappers. The adapter now caches the complete body reference
  skeleton and deterministically articulates both standard hand rigs through thumb,
  index, middle, ring, and pinky chains, including non-thumb metacarpals. Visible-paddle
  actions use a firm curl; rescue and swim states retain a light relaxed curl. Existing
  solved hand and paddle points remain authoritative, and crew mass, water, raft, D3/D4,
  collision, rescue, progression, and command selection are unchanged. The UE 5.8 editor
  target builds, focused character/raft contracts pass 21/21, and exact-current M5 passes
  4/4. Matched v35 and contact-side renderer evidence show stable attached digit chains
  and a more closed paddle-bearing hand shape, so the bounded change is retained
  technically. The generic curl, coarse hand mesh, residual hand/shaft spacing, procedural
  seated posture, and non-mocap stroke biomechanics remain photoreal-rejected. M4, M7,
  M8, the full Python/data/source matrix, fail-closed M9, packaging, and release evidence
  are stale or pending after v35; water-surface and HLOD evidence remain content-current.
  M9B.3 remains in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The palm-centred-paddle-grip v36 follow-up fixes the remaining semantic mismatch between
  solved grip points and the production skeletal wrist pivots. For visible-paddle actions,
  the adapter now derives each wrist from the reference hand-to-middle-palm offset so the
  existing `FRaftSimCrewAvatarPose` hand point remains the visible grip target. The arm and
  wrist solve move together; rescue and swim hand targets are unchanged. Matched and
  contact-side renderer evidence shows the shaft crossing the curled palm region without
  wrist, sleeve, or digit detachment. The UE 5.8 editor builds, focused character/raft
  contracts pass 21/21, and exact-current M5 passes 4/4 with every production avatar gated
  to at most 0.25 cm palm-anchor error. The correction is retained technically, but shared
  wrist orientation, generic curl, coarse hand topology, and procedural stroke biomechanics
  remain photoreal-rejected. M4, M7, M8, the full Python/data/source matrix, fail-closed M9,
  packaging, and release evidence are stale or pending after v36; water-surface and HLOD
  evidence remain content-current. M9B.3 remains in progress; M9 remains fail-closed,
  uncommitted, and unpushed.
  Follow-up v37/v38 palm-axis experiments at 65° and 28° were rejected because the first
  twisted foreground wrists and the second did not establish a clear two-view improvement;
  the branch was fully removed and the exact v36 source hashes were restored.
- The D4-aware-production-raft v42 slice makes the project-owned chamber cross-section
  consume the existing D4 compression and transforms its tangent frame with the analytic
  deformation gradient. Bounded area-preserving squash uses a 0.38 gain, a 0.90 minimum
  compressed scale, and 52% shading-gradient response. Topology, UVs, hidden collision,
  D3/D4 authority, buoyancy, flip, wrap, pin, damage, rescue, crew mass, commands, and
  progression remain unchanged. v41 was rejected as overinflated and lacquered; v43's
  wet-film bracket and v44's contact-crease bracket were also rejected and fully removed.
  The retained source/material graph remains byte-locked and passes current v48 M5 4/4.
  Broad tube highlights, weak crew contact, absent abrasion/repair/fabric-strain detail,
  and surrounding rock/water/environment art remain photoreal-rejected.
- The solver-breaking-water-lip v48 slice closes the live renderer's single-valued-
  heightfield limitation at real hydraulic jumps. A separate non-colliding procedural mesh
  consumes only existing supercritical-to-subcritical sites, with eight across segments,
  eight curl segments, 128 triangles per site, a 24-site/3,072-triangle hard cap, and a
  bounded 240° profile that rises from the free surface, noses downstream, then curls
  upstream beneath itself. The exact Meat Grinder window activates five sites and 640
  triangles. A dedicated project-owned translucent material serializes the rights-tracked
  foam-lace and flow-normal dependencies, compiles on Metal SM6, and avoids default fallback.
  Exact-current water-surface, M4, and M5 pass 1/1, 3/3, and 4/4 with zero warnings; focused
  packet/source Python checks pass 34/34. The retained raft-centred frame still records three
  wraps, one pin, 0.220 m indentation, 0.998 wetness, a 96-triangle contact patch, and
  91/5/9/144 spray/mist/contact-foam/droplet instances. This is a technical live-water
  geometry upgrade, not photoreal acceptance: coarse riverbed/terrain seams, hard water-
  patch boundaries, simplified crest form, insufficient entrained-air/collapse/pile volume,
  clean laces, and analytic aerosol remain open. M7, M8, the complete qualified Python/data/
  source matrix, fail-closed M9, Shipping/package, and release qualification remain stale or
  pending. M9B.3 remains in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The v71-v77 hydraulic-presentation follow-up adds a guide-height `river_action` evidence
  camera without changing staged D4 state, shortens the generated overturning arch to a
  3.5-4.7 m travel, bounds its full width to 8 m, and adds two-frequency lateral breakup so
  the five-site Meat Grinder sheet no longer reads as a continuous channel-spanning white
  ellipse. The retained v76 action frame still records four contacts, three wraps, one pin,
  one recovery, and approximately 0.220 m indentation. A bounded render-only raft wet-film
  multiplier exposes 58% of the physical wetness signal with a 0.65 presentation cap; the
  physical/telemetry wetness remains unchanged. Focused source checks pass, the editor
  builds, water-surface v77 passes 1/1, and renderer-backed M5 passes 4/4. The shorter broken
  pile is a technical improvement, not photoreal acceptance: its sheet topology, foam,
  collapse volume, entrained air, and aerosol remain visibly analytical.
- The v78-v83 environment follow-up replaces chalk-white repeated full-reach boulders with
  a reproducible world-aligned material using the already-vendored, rights-tracked CC0
  RockGround 4K albedo, normal, and roughness maps. The existing project-owned production
  boulder geometry and all catalogued D4/collision footprints remain unchanged. Both river-
  boot materials now persist their Nanite usage permutations, eliminating their default-
  material fallback. Three project-owned rounded cobble variants add 15,702 visual-only,
  non-colliding HISM instances to the unresolved 36-64 m bank band, while 15,136 additional
  source-conditioned deerbrush instances raise detailed-corridor foliage from 50,227 to
  65,363. v83 keeps source density authoritative but varies unresolved individuals with a
  70/30 white-alder/live-oak riparian mix and random conifer variants instead of a grid-
  modulo sequence. Map check reports zero errors and warnings; all five fixed captures save;
  focused contracts pass 35/35; the editor builds; water-surface v77 passes 1/1; M4 v83,
  M5 v82, and M7 v83 pass 3/3, 4/4, and 4/4, respectively, with only the known offscreen
  motion-vector warning. The v81 volumetric-cloud comparison was rejected for screen-space
  stippling and checker breakup, and v82 restored the clear-sky baseline before the retained
  v83 foliage mix. These are bounded environment improvements, not final art: broad water,
  shoreline/terrain resolution, radial canopy cards, far-field silhouettes, crew posture,
  raft response, and hydraulic aerosol remain below the requested photoreal bar. HLOD, M8,
  the full qualified matrix, fail-closed M9, packaging, external review, signing, and release
  evidence remain stale or pending. M9B.3 remains in progress; M9 remains uncommitted and
  unpushed.
- The v84 contact-boulder follow-up routes only the project-owned closed production mesh on
  the runtime D4 obstacle through the same two-scale world-aligned RockGround PBR family as
  scenic full-reach boulders. The new parent also accepts the solver-sampled local waterline,
  adding a noise-broken dark/wet band without changing collision, contact radius, wrapping,
  pinning, or recovery authority; the reviewed scan and procedural fallback remain isolated.
  The retained action frame records three contacts, three wraps, one pin, 0.220 m maximum
  indentation, 0.996 physical wetness, and a 96-triangle contact patch. Focused contracts pass
  36/36, the editor builds, the complete map rebuild exits successfully, and exact-current M5
  passes 4/4 with only the known motion-vector warning and no material fallback. This removes
  the previous nearly black/mottled action boulder but does not accept the frame as photoreal:
  broad water, shoreline transitions, canopy silhouettes, crew biomechanics, raft highlights,
  and hydraulic aerosol remain open. M9B.3 remains in progress; M9 remains uncommitted and
  unpushed.
- The v85-v89 review brackets close four low-value presentation avenues without changing the
  retained production baseline. v85's four-to-seven shore-cobble clusters did not materially
  improve guide-height shoreline breakup, so the map was rebuilt back to the accepted 15,702
  non-colliding instances. v86-v87 reduced registered terrain macro influence from 0.56 to
  0.40 and 0.20 only at capture time; both exposed too little useful ground detail and risked
  pale source discontinuity. v88-v89 raised authored-water normal strengths to 0.22 and the
  diagnostic 0.40 cap only at capture time; the cap exposed a repeated normal texture on an
  otherwise flat sheet. Production terrain and water material values therefore remain
  unchanged, while the bounded diagnostics remain available for later art review.
- The v90-v91 authored-water follow-up adds deterministic geometric normal variation after
  the source 4 m hydraulic field is refined to the existing 2 m visual grid. Registered river
  station/lateral coordinates set two non-repeating calm phases, vertex hydraulic energy adds
  two standing-wave phases, and the solver wet mask plus decoded shoreline depth fade the
  effect to zero at dry/shallow banks. The final retained v91 bracket is capped at 9 cm calm
  relief plus 15 cm hydraulic relief. It changes no solver height, wet mask, collision,
  navigation, flow, gameplay water query, or centerline authority; all authored water actors
  remain non-colliding. Focused source contracts pass 36/36, the editor builds, focused
  shoreline/water automation passes 1/1, the water-only full-reach rebuild exits successfully
  with 13 terrain and 39 water tiles, and exact-current M5 passes 4/4 (three clean, one with
  the known offscreen audio-device and motion-vector diagnostics). The retained action frame
  records four contacts, three wraps, one pin, one recovery, 0.220 m maximum indentation,
  0.999 physical wetness, and a 96-triangle contact patch with the production boulder material
  and no fallback. v91 provides readable broad-surface normal variation without shoreline
  tearing, but it does not make the frame photoreal: the river remains too uniform, bank and
  terrain transitions remain coarse, canopy silhouettes remain card-like, crew biomechanics
  remain stiff, raft highlights remain game-like, and hydraulic foam/aerosol remain
  analytical. M4, M7, HLOD, M8, packaging, the complete release matrix, external review, and
  signing evidence are stale or pending after the map change. M9B.3 remains in progress; M9
  remains uncommitted and unpushed.
- The v92 crew-biomechanics follow-up fixes a shared pose-output gap: `TorsoRotation` already
  rotated the production PFD, helmet, and a short neck direction, but shoulder and head
  landmarks remained at their translated positions. Seated command poses now rotate both
  shoulders and the head around the existing torso/PFD centre while hand, paddle, hip, knee,
  and foot targets stay authoritative. Falling, swimming, and re-entry keep their fully
  authored whole-body landmarks, and backstroke no longer recursively double-articulates its
  mirrored forward pose. This changes no crew command, reaction time, stroke impulse, D2/D4
  mass action, collision, rescue, progression, or solver state. The matched high-side frame
  shows a coherent waist/shoulder/head lean with planted hips and boots and no renewed
  PFD/helmet tearing. Focused source contracts pass 37/37, the editor builds, focused pose
  automation passes 1/1, and exact-current M5 passes 4/4 (three clean, one with the same two
  offscreen diagnostics). D4 evidence remains four contacts, three wraps, one pin, one
  recovery, 0.220 m indentation, 0.999 physical wetness, and a 96-triangle contact patch.
  v92 is a technical biomechanics improvement, not mocap or photoreal acceptance: cadence,
  grip orientation, facial response, secondary clothing motion, and individual reaction
  timing remain procedural. M4, M7, HLOD, M8, packaging, the complete release matrix,
  external review, and signing evidence remain stale or pending. M9B.3 remains in progress;
  M9 remains uncommitted and unpushed.
- The v93-v94 canopy bracket tested a single camera-facing plane as a replacement for each
  three-plane native-species photo card. Although the experiment reduced each mesh from 12
  vertices/6 triangles to 4 vertices/2 triangles, its camera-facing world normal overlit the
  canopy into a pale wall and erased useful depth cues. The experiment was rejected and fully
  removed. v94 rebuilt all six canopy assets at the accepted 12-vertex/6-triangle geometry,
  regenerated the full reach with the unchanged 65,363 source-conditioned foliage instances,
  and rendered a matched action frame. Focused source contracts pass 37/37, the editor builds,
  the full-reach restore exits successfully, and exact-current M5 passes 4/4 (three clean, one
  with the two known offscreen diagnostics). D4 remains four contacts, three wraps, one pin,
  one recovery, 0.220 m indentation, 0.999 physical wetness, and a 96-triangle contact patch.
  The rollback restores the v92 baseline but does not resolve the radial-card silhouette,
  pale canopy, or missing branch volume. M9B.3 remains in progress; M9 remains fail-closed,
  uncommitted, and unpushed.
- The retained v95 canopy-radiometry slice calibrates the six photo-card materials without
  changing geometry or placement. Species-separated base-color multipliers preserve more of
  the source bark/leaf range, while reduced foliage transmission keeps direct sun from
  collapsing whole stands toward beige. In the matched upper-frame region, mean RGB changes
  from 131.96/138.30/119.62 at v94 to 126.82/134.62/115.16 at v95, an approximately four-
  percent aggregate energy reduction. Focused source contracts pass 37/37, the editor builds,
  all six 12-vertex/6-triangle assets and the unchanged 65,363-instance full reach regenerate,
  and exact-current M5 passes 4/4 (three clean, one with the two known offscreen diagnostics).
  The action frame retains four contacts, three wraps, one pin, one recovery, 0.220 m
  indentation, 0.999 physical wetness, and a 96-triangle contact patch. v95 improves color
  separation but remains photoreal-rejected because radial cards, stand-scale repetition, and
  absent branch volume remain obvious. M9B.3 remains in progress; M9 remains fail-closed,
  uncommitted, and unpushed.
- The retained v96 South Fork water-optics slice changes only the unlocked river-specific
  material instance: roughness falls from 0.38 to 0.28, base/fresnel specular rise to 0.24/
  0.15, and the bounded fallback sky response rises to 0.18. The project-owned flow-normal
  texture, hydraulic vertex channels, depth/foam masks, visual mesh, collision, water query,
  and solver remain unchanged. The matched action frame gains visible short-wave structure
  and grazing reflection without mirror glare; all five settled full-reach cameras also save
  without reflection or foam-mask blowout. Focused source contracts pass 37/37, the editor
  builds, the full-reach material rebuild exits successfully, and exact-current M5 passes 4/4
  (three clean, one with the two known offscreen diagnostics). D4 remains four contacts, three
  wraps, one pin, one recovery, 0.220 m indentation, 0.999 physical wetness, and a 96-triangle
  contact patch. v96 is still photoreal-rejected: the fixed Meat Grinder view exposes broad,
  dark, low-information water, and hydraulic collapse/entrained-air/aerosol volume remains
  visibly analytical. M9B.3 remains in progress; M9 remains fail-closed, uncommitted, and
  unpushed.
- The retained v97 foam-calibration slice raises only the South Fork instance's solver-
  masked foam intensity/coverage from 0.72/0.72 to 0.88/0.82. It neither changes the
  project-owned lace texture nor introduces any presentation where the cooked foam channel
  is zero. The median source window contains positive cells through the 904-1,084 m rapid
  sequence, including a byte value of 228 at 1,024 m; the stronger but bounded material
  response makes those fragments more legible in the action frame without restoring the
  formerly rejected broad pale carpet in any of the five fixed cameras. Focused source
  contracts pass 37/37, the editor builds, the full-reach material rebuild exits successfully,
  and exact-current M5 passes 4/4 (three clean, one with the two known offscreen diagnostics).
  D4 remains four contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.999
  physical wetness, and a 96-triangle contact patch. v97 remains photoreal-rejected because
  foam is still primarily surface-color breakup rather than convincing collapse/entrained
  air, and the fixed Meat Grinder camera begins roughly 40 m upstream of the strongest cells.
  M9B.3 remains in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The retained v98 production-PFD slice replaces the project-owned asset's 31.5 x 42 cm
  rounded-box rear foam with a twelve-point extruded outline that narrows between the
  shoulder blades and at the lumbar hem. Front cells, side wings, shoulder bridges, placard,
  webbing, hardware, quick-release belt, material slots, torso attachment, and rescue/gameplay
  authority remain unchanged. Blender regeneration and the Unreal import audit pass; the
  imported asset carries 22,268 authored LOD0 triangles, five expected material slots, Nanite
  with a 2,296-triangle fallback, and a 42.2 x 44.9 x 45.8 cm envelope. Focused source/asset
  contracts pass 38/38 and exact-current M5 passes 4/4 (three clean, one with the two known
  offscreen diagnostics). The matched rear action view no longer reads each PFD as an identical
  rigid backpack. v98 remains photoreal-rejected because close-up shell/stitch response and
  secondary clothing dynamics remain synthetic. M9B.3 remains in progress; M9 remains
  fail-closed, uncommitted, and unpushed.
- The retained v99 raft-wet-film slice leaves the full physical/telemetry wetness signal,
  flexible mesh, D4 contact state, generated coated-fabric maps, and locked parent material
  unchanged. It compresses only the dynamic material-instance presentation input from 58%
  with a 0.65 cap to 42% with a 0.50 cap. In a matched bow-tube crop, 99th-percentile
  luminance falls from 165.03 to 151.04 and pixels above luminance 180 fall from 25 to 3;
  the tube remains visibly wet but the single lacquer-like highlight is less dominant.
  Focused source/asset contracts pass 38/38, the native editor target builds, and exact-
  current M5 passes 4/4 (three clean, one with the two known offscreen diagnostics). D4
  remains four contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.999
  physical wetness, and a 96-triangle contact patch. v99 remains photoreal-rejected because
  localized beads, abrasion, seams, and inflation wrinkles are under-resolved, while water,
  shoreline, terrain, canopy, crew motion, hydraulic collapse, and aerosol remain below the
  target. M9B.3 remains in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The retained v100 canopy-topology slice replaces each three-plane 60-degree radial card
  with two orthogonal full-source planes. Unlike the rejected v93 experiment, neither plane
  is camera-facing and both retain the source texture's complete trunk/crown silhouette;
  deterministic per-instance yaw still supplies unresolved stand orientation. All six
  generated assets fall from 12 vertices/6 triangles to 8 vertices/4 triangles, removing a
  third coincident source trunk and one-third of masked alpha overdraw without changing the
  65,363 source-conditioned placements. Focused contracts pass 38/38, the editor builds,
  the full reach regenerates, all five settled cameras save, and exact-current M5 passes 4/4
  (three clean, one with the two known offscreen diagnostics). D4 remains four contacts,
  three wraps, one pin, one recovery, 0.220 m indentation, 0.999 physical wetness, and a
  96-triangle contact patch. v100 remains photoreal-rejected because broadleaf/far-field
  crowns still lack true branch and leaf volume and repeated source silhouettes remain
  visible. M9B.3 remains in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The v101-v102 canopy-volume bracket tested a sparse opaque trunk and species-shaped
  primary-stem section inside every retained two-plane source silhouette. The experiment
  raised each asset to 40-48 triangles but rendered as repeated dark poles through the
  masked crowns and did not align closely enough with all six source profiles. v101 was
  rejected, its source and generated branch material were removed, and v102 regenerated
  every canopy asset at the retained v100 8-vertex/4-triangle topology with the unchanged
  65,363 source-conditioned placements. Focused contracts pass 38/38, the editor builds,
  the full-reach restore exits successfully, and exact-current M5 passes 4/4 (three clean,
  one with the two known offscreen diagnostics). The rollback capture records four
  contacts, three wraps, one pin, one recovery, 0.220 m indentation, 0.998 physical
  wetness, and a visible 512-triangle breaking lip. M9B.3 remains in progress; M9 remains
  fail-closed, uncommitted, and unpushed.
- The v103-v107 hydraulic-roller bracket isolated the solver-driven breaking lip from the
  authored broad-water surface and proved that the prior strongest-cell foreground pattern
  was primarily broad-water foam, while the live lip itself remained a low, elongated
  sheet. The retained v105 geometry compacts the moderate-jump arch from approximately
  3.5-4.7 m to 2.8-3.8 m travel and raises its unscaled profile from 0.18-0.70 m to
  0.30-1.05 m. v105's original core still rendered as a translucent white slab; v106
  squared the project-owned lace coverage, narrowed and laterally fragmented the solver
  crest core, but over-cleared the distinct roller. The retained v107 midpoint keeps that
  perforated response with 0.86 maximum foam opacity and a non-saturating 1.25 core gain.
  It remains a presentation-only, non-colliding mesh and changes no hydraulic detection,
  water query, wet mask, collision, buoyancy, D3/D4 authority, or gameplay force. Focused
  source/asset contracts pass 38/38, the editor builds, the regenerated material saves,
  and exact-current M5 passes 4/4 (three clean, one with the two known offscreen
  diagnostics). The action frame retains four contacts, three wraps, one pin, one
  recovery, 0.220 m indentation, 0.999 physical wetness, and a visible 512-triangle lip.
  v107 removes the solid slab but remains photoreal-rejected because collapse volume,
  entrained-air depth, turbulent aerosol, and the separate broad-water foam field remain
  visibly analytical. M9B.3 remains in progress; M9 remains fail-closed, uncommitted, and
  unpushed.
- The v108-v110 contact-water bracket found that the existing 9 x 7, 96-triangle
  presentation patch was centered on the contacted raft segment and therefore mostly
  hidden beneath the 1.2 m-radius production obstacle. v108 moved the patch and all card
  populations a full radius outward while retaining the shared spray material; it exposed
  a bright crossed-wave quilt and detached dotted particle arcs and was rejected. v109
  separated the continuous patch from the particle origin and reused the project-owned
  flow-lace breaking-water family, but its full-radius patch offset still read as a detached
  wedge. The retained v110 endpoint keeps spray and droplets at the physical D4 contact,
  offsets only the continuous patch by 0.55 m, supplies lower-energy intensity/core vertex
  channels, and uses a 0.02 water / 0.58 maximum foam optical response. The patch remains
  non-colliding, samples the authoritative free surface at every vertex, and changes no
  contact, obstacle, water, D3/D4, collision, buoyancy, or gameplay force. Focused contracts
  pass 38/38, the editor builds, and exact-current M5 passes 4/4 (three clean, one with the
  two known offscreen diagnostics). The action frame retains four contacts, three wraps,
  one pin, one recovery, 0.220 m indentation, 0.999 physical wetness, the visible
  96-triangle patch, and a visible 512-triangle breaking lip. v110 removes the quilt failure
  but remains photoreal-rejected because close spray/droplet populations and water-collapse
  volume are still procedural. M9B.3 remains in progress; M9 remains fail-closed,
  uncommitted, and unpushed.
- The retained v111 water-card orientation correction fixes a shared projection bug in
  spray, mist, droplet, and rapid-aerosol populations. Their helper previously discarded
  camera elevation and rotated planes only in yaw, so elevated guide/contact cameras saw
  them nearly edge-on as dotted arcs. The helper now uses the full three-dimensional view
  normal while preserving the projected vertical streak axis. Instance counts, opacity,
  trajectories, deterministic phase, source locations, VFX budgets, water sampling, D4,
  collision, and forces are unchanged. The matched contact and action frames remain
  bounded without card blowout; focused contracts pass 38/38, the editor builds, and
  exact-current M5 passes 4/4 (three clean, one with the two known offscreen diagnostics).
  v111 is geometrically correct but remains photoreal-rejected because the low-opacity
  deterministic cards are not production Niagara water volumes. M9B.3 remains in progress;
  M9 remains fail-closed, uncommitted, and unpushed.
- The retained v114 production-Niagara slice replaces those visible card populations with
  four project-owned stateless particle systems: solver/contact spray, contact droplets,
  aerated contact mist, and rapid aerosol. Every system uses a bounded looping emitter,
  the project-owned spray material with Niagara-sprite usage, and an exposed
  `User.SpawnRate` driven from the existing live-water/D4 presentation classifier. Runtime
  owns three contact components plus a fixed eight-component rapid-site pool; it never
  spawns transient Niagara actors. The deterministic card populations continue updating
  for automation and unsupported-platform fallback but are hidden when all eleven Niagara
  components are asset-bound. v112 proved the first systems and v113 reduced oversized mist
  discs; v114 emits from the exposed edge of the already solver-sampled contact shoulder and
  raises the spray/droplet launch angle so particles clear the review boulder without
  changing collision, water, D3/D4, buoyancy, scoring, or gameplay forces. All four authored
  assets contain infinite stateless emitters, the shared material reference, and the
  bindable spawn-rate parameter. Focused source/asset contracts pass 38/38, the native editor
  target builds, focused runtime-pool automation passes 1/1, and exact-current M5 covers five
  test cases with four clean and RuntimeRescueLoop carrying only the two known offscreen
  audio-device/motion-vector diagnostics. The action frame retains four contacts, three
  wraps, one pin, one recovery, 0.220 m indentation, 0.999 physical wetness, a visible
  96-triangle contact patch, and a visible 512-triangle breaking lip. v114 closes the missing
  Niagara architecture/asset/runtime gap but remains photoreal-rejected: individual spray
  sprites are still readable in the close frame, water-collapse and entrained-air volume are
  underdeveloped, and the broader water, terrain, shoreline, canopy, character motion, and
  equipment response remain below the target. M9B.3 remains in progress; M9 remains
  fail-closed, uncommitted, and unpushed.
- The retained v118 particle-art slice replaces v114's shared analytic radial stamp with a
  deterministic, project-owned 2048×2048 SubUV atlas and a Niagara-only translucent
  material. Six compact spray bursts, five droplet clusters, three aerated-mist cells, and
  two rapid-aerosol cells occupy disjoint frame ranges; each stateless emitter selects a
  random direct-set frame only from its assigned class. The material samples those cells
  through `ParticleSubUV`, multiplies live Niagara color/alpha, and applies a 14 cm depth
  fade before volumetric lighting, while the locked deterministic-card fallback and its
  material remain unchanged. v115 was discarded because the first uncached comparison did
  not render the staged boulder; v116 proved the path but was too sparse; v117's oversized
  cells were rejected as steam plumes and paint strokes. v118 retains smaller, lower-opacity
  particles at bounded full-intensity rates of 260 spray, 320 droplets, 70 mist, and 10–56
  aerosol particles/second. The native editor target builds, all four systems update/save,
  focused source/asset/provenance checks pass 39/39, offscreen-Metal M5 passes five cases
  with only the known motion-vector warning on `RuntimeRescueLoop`, and the focused runtime
  pool passes 1/1 with all eleven components asset-bound and the same warning. The matched
  frames preserve four contacts, three wraps, one pin, one recovery, 0.220 m indentation,
  and 0.999 physical wetness. v118 is retained over v114 because it removes the uniform
  circular-card silhouette without restoring v117's overdrawn stamps, but it remains
  photoreal-rejected: compact bursts are still readable close, true collapse/entrained-air
  volume remains weak, and the broader water, terrain, shoreline, canopy, character motion,
  and equipment response remain below the target. M9B.3 remains in progress; M9 remains
  fail-closed, uncommitted, and unpushed.
- The retained v121 hydraulic-volume slice adds a separate presentation-only
  `BreakingRollerVolumeMesh` at the same accepted live-water transition sites that already
  drive the breaking lip and rapid aerosol. Each site receives three continuous,
  alpha-perforated open-loop shells with an 18 x 14 grid per layer, capped at 1,512
  triangles per site and 36,288 triangles across the existing 24-site budget. The captured
  moderate site presents an approximately 0.86-1.16 m nested crown inside a maximum 4.4 m
  span; the component has no collision, shadow, navigation, water-sampling, buoyancy, D3,
  D4, flip, wrap, pin, damage, rescue, or progression authority. v119 was rejected as
  visually indistinguishable from the flat-foam baseline; v120 was rejected as a broad
  opaque dome with rectangular missing-cell holes; v122's tent-like transverse modulation
  was fully reverted. The retained v121 frame records one full-coverage 15 m-clearance
  breaking site, 512 lip triangles, 1,512 roller triangles, four contacts, three wraps, one
  pin, one recovery, 0.220 m indentation, and 0.999 physical wetness. Focused relevant
  contracts pass 39/39, the native editor target builds, WaterSurface passes 1/1, M4 passes
  3/3, and offscreen-Metal M5 passes all five cases with only the known
  `r.MotionVectorSimulation` warning. v121 closes the missing collapse-volume foundation
  but remains photoreal-rejected because the retained body and surrounding broad-water
  foam remain visibly procedural, while terrain, shoreline, canopy, distant crew, and
  lighting are also still below the release-art target. The release packet remains
  intentionally fail-closed on earlier dirty-worktree evidence. M9B.3 remains in progress;
  M9 remains uncommitted and unpushed.
- The v124-v126 near-bank broadleaf-volume experiment is rejected and reverted. v124
  split the project-owned live-oak and white-alder photographs into independently rotated
  tiles, exposing a dark scaffold and fragmented crowns. v125 reconstructed each photo
  with two contiguous, depth-warped strip directions; v126 expanded that to four shallow
  directions with wider overlap and bounded 234-triangle oak / 292-triangle alder meshes.
  Both assets retained two material sections, no collision, and no solver or gameplay
  authority. Native builds, 176/176 World Partition identity checks, zero-error/zero-warning
  map checks, and five fixed captures passed, but the exact matched comparison found no
  photoreal improvement over the cleaner two-plane card baseline. The map, source contract,
  and generated assets therefore returned to the card baseline; only the compact baseline,
  rejected capture, hashes, and review decision remain. The next canopy attempt requires a
  rights-cleared native multi-species 3D set or a connected-crown generator that materially
  beats the baseline under matched visual and performance gates. M9B.3 remains in progress;
  M9 remains uncommitted and unpushed.
- The retained v127 capsize-authority slice closes a solver/presentation state split in
  the shipping flip loop. `EnterCapsize` previously rolled only the actor after the bridge
  publish, allowing the next authoritative adapter frame to make a capsized-mode raft look
  upright. The strengthened P2 test reproduced that defect at -0.0 degrees. A first direct
  pose handoff then exposed the deeper loading error: the inverted solve kept upright deck
  water and all five occupied crew seats, sinking to the 500 m safety clamp. The retained
  implementation adds an explicit adapter capsized state with a cached allocation-free
  empty-seat view, drains self-bailing D3 deck water, preserves D4 indentation/wrap/pin
  memory, and hands a symmetric 180-degree sealed-tube pose to the authoritative fixed-step
  solver. Reflip and checkpoint reset restore normal loading. The native editor target
  builds; all three M1 flexible-raft tests, the P1 float/paddle test, and the P2 forced
  overwash -> visibly inverted raft -> five swimmers -> reflip -> reseat loop pass with zero
  warnings; 69 focused Python/source contracts pass. v127 changes no water sampler,
  buoyancy force law, rock-contact law, geography, scoring, or progression. M9B.3 remains
  in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The retained v128 capsize-transition slice replaces v127's one-frame 180-degree roll
  with a bounded 0.85-second authoritative hybrid transition. A one-shot 5.4 rad/s seed
  was explicitly rejected: live buoyancy limited it to 18.6 degrees and then righted it to
  12.0 degrees, while simply increasing the impulse risked an uncontrolled barrel roll.
  The retained path lets D3 choose the event and roll direction, then advances latch
  pitch/roll through cubic smoothstep to exact zero-pitch / signed-180-roll equilibrium,
  writing the matching pose and angular rate into the adapter each tick. Translation,
  buoyancy, drag, D4 contact/wrap/pin and downstream motion remain live. This is labeled a
  hybrid constraint because the reduced solver does not resolve the transient air/water
  volume that carries a real inflatable through the unstable side-on phase. Final P2
  evidence measures 127.6 degrees during the transition and 180.0 degrees at -13.6 cm
  settled height with five swimmers, then passes reflip, full reseat and upright recovery.
  The native editor target builds; M1 passes 3/3, P1 passes 1/1, P2 passes 1/1, and 69
  focused source contracts pass, all with zero warnings. M9B.3 remains in progress; M9
  remains fail-closed, uncommitted, and unpushed.
- The retained v129 live-segment-water slice closes a production physics disconnect:
  the shipping bridge previously supplied live river height only to rigid-body buoyancy,
  leaving D3 overwash dry unless an automation fixture forced uniform water. The same
  authoritative `URaftSimWaterRuntimeAdapter` now samples surface height, world velocity,
  and wet state at every D2-deformed tube segment and passes a SegmentId-keyed field into
  D3 on each 120 Hz raft substep. The map is pre-reserved and reused, missing samples fall
  back to dry, explicit fixture overrides retain precedence, and capsized self-bailing
  loading remains dry. A real curved South Fork transit field at station 5,000 m supplies
  12/12 wet samples at 1.101 m/s and creates 2.870 kg retained load with a 28.151 N·m roll
  moment without a synthetic descriptor. The native editor target builds; M1 passes 4/4,
  P1 passes 1/1, the v128 P2 flip/reflip loop passes 1/1, the real-river M4 coupling passes
  1/1, and 69 focused source contracts pass, all with zero warnings. v129 does not yet
  prove that an unforced shipping traversal through a named rapid crosses the sustained
  D3 flip threshold; that hazardous-line/safe-line calibration remains required. M9B.3
  remains in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The retained v130 bounded named-rapid D3 slice closes that calibration gap and a newly
  exposed coupled-physics failure. The first real 3,000 cfs Meat Grinder probe let point
  velocity, overtopping flux, retained water, and torque amplify until the hazard carried
  508 million kg and the control 50 million kg, launching both millions of metres; that
  exploratory pass is preserved as rejected evidence. Production D3 now evaluates the
  loaded tube top at its pressure-scaled 0.28 m radius, caps relative inflow at 8 m/s,
  caps flux depth at two tube radii, and limits each of the twelve self-bailing reservoirs
  to 0.05 m3. D6 reference defaults are unchanged. With only genuine cooked high-flow
  samples, an improper broadside line at the interpreted mid-river hole stays finite,
  reaches 315.059 kg retained load and a -280.787 N·m margin for 1.242 seconds, and rolls
  77.370 degrees; it therefore exceeds the actor's unchanged 0.35-second capsize latch.
  A downstream-facing river-left control using the shipping guide high-side/brace action
  stays at +1,556.578 N·m margin, zero risk time, and 2.198 degrees roll. The data remains
  labeled procedural infill interpreted from guide inventory, not surveyed or approved
  for navigation. The native editor target builds; M1 passes 4/4 including a five-second
  feedback gate, P1 and P2 pass 1/1, M4 passes 4/4, and 114 focused physics/source tests
  pass without warnings. A named professional guide review, rendered end-to-end rapid
  capture, full rapid tuning, and external D6 measurements remain open. M9B.3 remains in
  progress; M9 remains fail-closed, uncommitted, and unpushed.
- The retained v131 genuine-Chaos D6 slice closes the Unreal half of that external
  measurement gap and corrects an earlier evidence-labeling error. The old
  `RaftSim.D6.UEMeasuredExport` remains a useful C++-port diagnostic, but both of its
  passes execute the same analytical D1-D4 implementation and therefore satisfy neither
  independent D6 target. The new `RaftSimD6Chaos::RunMeasuredExport` instead creates
  transient `EWorldType::Game` physics scenes, spawns a simulated `UBoxComponent`,
  validates its `FChaosEngineInterface` rigid actor handle, advances all 18 fixed steps,
  and repeats each scenario to an identical quantized trajectory hash. All seven fixture
  records contain the contract's required metrics and top-level telemetry fields; rock
  and pressure-sweep runs use the recorded boulder geometry and measured impulse response,
  while zero sag/wrap/retained-water outputs explicitly record the rigid proxy's missing
  compliant capabilities. The sidecar merge gate accepts 7/7 Chaos records, and the D6
  execution packet now records 7/14 external jobs complete. D6 remains incomplete and
  unpromoted: all seven Project Chrono/reviewed-compliant measurements, comparison
  regeneration, and manual physics/integration/replay/guide-safety review remain open.
  M9B.3 remains in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The retained v132 South Fork canopy/daylight slice replaces the six active project-bound
  tree and shrub profiles with species-specific V2 bitmap sources generated through the
  built-in image-generation surface, then alpha-matted with the recorded border-key,
  soft-matte, threshold, and despill settings. The exact prompts, source hashes, and
  postprocess settings live in the generated-canopy provenance ledger. The bounded runtime
  topology remains two orthogonal planes (8 vertices / 4 triangles per asset) across the
  unchanged 65,363 source-conditioned placements; a lower 0.20 mask cutoff retains fine
  needles and twigs. The full-reach map was authoritatively regenerated with 176 stable
  World Partition identities, 13 terrain and 39 water tiles, 37,836 procedurally completed
  shoreline vertices, and five fixed captures. The retained clear-day bracket raises the
  sun from 6.5 to 8.2 lux, sky fill from 0.82 to 1.45, and deterministic capture exposure
  from 0.0 to +0.30 EV. It exposes more terrain, bank, bark, and crown separation without
  clipping the fixed views. The native editor target builds, editor-source contracts pass
  23/23, full-reach generation exits cleanly, and renderer-backed
  `RaftSim.M7.ZFullReachPresentation` passes with only the known UE 5.8 motion-vector
  warning. v132 is retained as a technical readability/source-art improvement, not
  photoreal acceptance: foliage remains visibly planar, broad water remains dark and flat,
  terrain/shoreline detail remains coarse, and characters, equipment, raft, rocks, and
  motion remain synthetic. Named review and all release-media gates remain open. M9B.3
  remains in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The retained v133 South Fork water-optics slice corrects the five fixed views' dark,
  nearly planar broad-water response entirely inside the river-specific material instance.
  It supplies bounded gray-green shallow/deep body colours, blue-sky reflection, volumetric
  scattering/absorption and riverbed transmission, then restores a 0.28 capture-safe sky
  reflection term with 0.24 roughness and softened 0.055/0.075/0.110 calm/flow/foam normal
  response. The first stronger bracket was rejected because it exposed camera-radial normal
  streaks at TroubleMaker and Salmon Falls; the retained midpoint preserves the useful
  colour and current modulation without that strongest artifact. The shared parent, water
  meshes, solver-authored vertex channels, live sampling, collision, D3, and D4 are
  unchanged. Hash-validated detailed meshes were reused while the map rebuilt to 176 stable
  World Partition identities with zero map-check errors/warnings and five updated fixed
  captures. The native editor target builds, editor-source contracts pass 23/23,
  renderer-backed M4 passes 4/4, and `RaftSim.M7.ZFullReachPresentation` passes; each
  renderer suite carries only the known UE 5.8 motion-vector warning. v133 is retained as a
  technical optical/readability improvement, not photoreal acceptance: the surface is still
  a non-overturning heightfield, the normal field remains analytical at hero distance, and
  foam/air volume plus the surrounding terrain, shoreline, canopy, rocks, raft, characters,
  equipment, and motion remain below the target. Named guide/art review remains open. M9B.3
  remains in progress; M9 remains fail-closed, uncommitted, and unpushed.
- The retained v134 independent-Project-Chrono D6 slice closes the remaining technical
  external-measurement gap without relabeling the Python reference, custom C++ port, or
  Unreal analytical diagnostic. An isolated official Project Chrono/PyChrono 10.0.0
  `osx-arm64` environment executes a fixture-input-only runner that creates real
  `ChSystemSMC` systems with twelve `ChLinkTSDA` pressure-compliance elements and separate
  Chrono penalty elements for rock indentation. All seven compliant fixtures run twice to
  byte-identical telemetry, preserve the ten required D5 channels, and merge with complete
  provenance and replay hashes. Combined with v131's seven genuine Chaos rigid-baseline
  records, the execution packet now records 14/14 jobs complete and the regenerated
  comparison passes 74/74 compliant numeric metrics with zero missing or failed targets;
  the largest compliant absolute delta is 0.0101 N against a 441.6 N tolerance. Focused D6
  tests pass 44/44. D6 remains deliberately unpromoted because named physics,
  Unreal-integration, deterministic-replay, and professional guide/safety reviews are
  still pending. This closes a technical validation gate, not the photoreal art, named
  review, external-platform, signing, approved-media, or release gates. M9B.3 remains in
  progress; M9 stays uncommitted and unpushed.
- The retained v135 HLOD regeneration slice closes the stale terminal-geometry gate left
  by the v132 authoritative full-reach rebuild. Unreal's World Partition HLOD builder
  rebuilt and saved all 24 terminal actors with zero errors; an immediate repeat evaluated
  all 24, rejected every rebuild as current, saved zero packages, and again exited with
  zero errors. Durable evidence hashes all 24 current actor packages and is linked from the
  regenerated world manifest. The qualified full Python matrix reports 1,112 passes and
  three expected dependency-path skips; its only failure is the intentional release-packet
  assertion comparing the current post-v317 raft source against its historical v42 hash.
  That release-candidate contract remains deliberately unreconciled until M9 has an
  accepted visual and technical candidate. This closes stale HLOD evidence, not photoreal
  art, named review, external-platform, signing, approved-media, or release gates. M9B.3
  remains in progress; M9 stays uncommitted and unpushed.
- The retained v136 far-field macro-infill slice replaces the visibly periodic procedural
  palette with deterministic world-space domain warping across dry grass, chaparral,
  woodland, and exposed rock, while widening authoritative NAIP edge feathering from
  256 m to 720 m. Two independent full generations are byte-identical. Visual inspection
  of all five fixed Unreal views accepts the removal of dominant diagonal banding and the
  reduction of hard pale source rectangles, but explicitly rejects the result as final
  photoreal art: water, sparse/card-like vegetation, abrupt shorelines, and broad terrain
  regions remain open. The resulting world rebuilt and saved 24/24 HLOD actors with zero
  errors; its immediate settled repeat evaluated 24/24 and saved zero packages. Procedural
  pixels remain game-only, non-colliding, hydraulically inert, and not suitable for
  navigation. M9B.3 remains in progress; M9 stays uncommitted and unpushed.
- The retained v137 canopy-instance-radiometry slice adds bounded per-instance energy
  (0.88-1.14) and masked-opacity (0.92-1.10) variation around the unchanged six
  project-bound sources and two-plane, 8-vertex/4-triangle topology. A small
  species-specific tint/transmission lift improves crown separation in all five fixed
  Unreal views without a pale canopy wall, clipped highlights, noisy alpha edges, ecology
  changes, placement changes, collision, or hydraulic authority. The source target builds,
  focused contracts pass, all 18 canopy assets regenerate and validate, and HLOD converges
  through 24-actor rebuild passes to a 24/24 zero-save repeat with zero errors. This remains
  a technical readability improvement, not photoreal acceptance: near foliage is still
  visibly planar, far stands remain repetitive, and water, terrain, shoreline, rocks,
  raft, crew, equipment, and motion remain below the target. Named review and release-media
  gates remain open. M9B.3 remains in progress; M9 stays uncommitted and unpushed.
- The retained v139 interior-live-oak connected-crown slice derives a project-owned 4×4
  branch atlas with twelve occupied tiles, deterministic chroma removal, cell-bounded mip
  padding, tangent normals, and packed AO/roughness/subsurface maps. Its two full-tree core
  planes retain the source-conditioned silhouette while twelve three-dimensional branch
  cards raise the mesh from 4 to 28 triangles. The denser v138 20-card/44-triangle bracket
  was rejected because Troublemaker and Coloma became darker, opaque crown masses; v139
  keeps useful branch breakup with less clumping and no visible chroma fringe or mip halo
  in five fixed 1280×720 Unreal views. The editor target builds, focused contracts pass,
  22 assets validate, the regenerated full-reach map preserves 176 stable World Partition
  identities, and a 24-actor HLOD rebuild converges immediately to a 24/24 zero-save repeat
  with zero errors. This is an active technical fallback only: other canopy species remain
  planar, and water, shoreline, terrain, rocks, raft, people, equipment, and motion still
  fail the photoreal gate. Named review and release promotion remain open. M9B.3 remains in
  progress; M9 stays uncommitted and unpushed.
- The retained v140 all-species connected-crown slice adds project-owned 4×4 branch atlases
  for Ponderosa pine, white alder, and deerbrush, then applies the same bounded twelve-spray
  topology to all six active canopy profiles. Independent 4×3 source-cell normalization,
  deterministic chroma removal, cell-bounded mip padding, tangent normals, and packed
  AO/roughness/subsurface maps preserve clean masked edges even when source aspect ratios
  differ. All six Unreal meshes validate at 56 vertices, 28 triangles, two material slots,
  and no collision; the source target builds, focused contracts pass, 34 canopy assets and
  63 full-reach assets validate, the map preserves 176 stable World Partition identities,
  and HLOD converges from 24 saved actors to a 24/24 zero-save repeat with zero errors. The
  five fixed views accept this only as restrained crown-depth progress: full-tree cores,
  dark/repeated stands, water, shoreline, terrain, rocks, raft, people, equipment, motion,
  and lighting remain below the target. Named art, guide, geospatial, legal, and owner
  review remains open. M9B.3 remains in progress; M9 stays uncommitted and unpushed.
- The retained v168 photographic-review infrastructure adds an opt-in, non-mutating
  full-reach capture mode with temporal antialiasing, ambient occlusion, Lumen GI and
  reflections, screen-space reflections, and twelve settle frames while preserving the
  byte-repeat deterministic default. All five fixed 1280×720 views render and the editor
  target plus focused contracts pass, but manual review rejects every image for photoreal
  and release-media use. The renderer-only change is small and exposes the content limit:
  water remains broad and flat, banks remain smooth and uniform, vegetation remains sparse
  and card-like, and the fixed views contain no raft or crew. This is retained review
  infrastructure, not art acceptance. M9B.3 remains in progress; M9 stays uncommitted and
  unpushed.
- The retained v169 volumetric-broadleaf slice replaces the two crossed full-tree core
  planes plus twelve sprays for interior live oak and white alder with one coherent core
  plane and thirty-six smaller sprays distributed through six crown layers. Each V2 proxy
  has 148 vertices and 74 triangles; Ponderosa and deerbrush retain their V1 topology.
  The authoritative world rebuild validates 200 stable World Partition identities, the
  photographic pass loads 201 references without mutation, and the five views change
  9.5-30.4% of pixels from v168 by only 0.93-2.23 RGB levels on average. Manual review
  accepts a modest reduction in crossed silhouettes but rejects the remaining dark,
  repetitive card crowns plus synthetic water, banks, terrain, and distant scenery. The
  UE 5.8 target builds twice, focused suites pass 45/45 before and 35/35 after HLOD,
  `RaftSim.M7.ZFullReachPresentation` passes, all 30 HLOD actors rebuild, and a final repeat
  saves zero packages. This is a bounded canopy-topology improvement, not photoreal or
  release-media acceptance. Named reviews remain open; M9 stays fail-closed, uncommitted,
  and unpushed.
- The rejected v170 detailed-terrain-relief bracket tested a two-metre visual surface over
  the authoritative four-metre DEM, with deterministic bank-only microrelief capped at
  28 cm and the original mesh retained as collision authority. All five fixed photographic
  views rendered successfully, but manual comparison found no material shoreline or terrain
  realism gain: mean RGB deltas were only 1.50-2.39 levels and the visible changes were
  dominated by foliage/settled-frame variation. The bracket multiplied detailed-terrain
  visual triangles from 1,467,648 to 5,870,592, so it failed the visual-benefit/cost gate.
  The runtime implementation and thirteen orphaned collision meshes were removed while its
  captures and review ledger were preserved as negative evidence. The accepted four-metre
  terrain was authoritatively regenerated with 200 deterministic World Partition identities;
  all 30 HLOD actors rebuilt, one settling repeat saved one package, and the final repeat
  saved zero. Renderer-backed `RaftSim.M7.ZFullReachPresentation` passes. v170 contributes
  no runtime change and closes no photoreal or named-review gate; M9 remains fail-closed,
  uncommitted, and unpushed.
- The rejected v171 shoreline-bank bracket tested a narrow median-wet-edge cutbank and
  gravel-bench mesh derived from the existing two-metre water presentation and four-metre
  DEM. Thirteen non-colliding actors added 26,208 longitudinal edge segments and 157,248
  triangles while leaving the 1,467,648-triangle terrain, hydraulics, collision, and
  navigation authority unchanged; measured height peaked at 94.50 cm under the 1.10 m
  cap. The UE 5.8 target, 23/23 focused source-layout tests, and native shoreline test pass,
  and all five fixed photographic views render. Manual comparison rejects the result:
  mean RGB deltas are only 0.73-1.15 levels, 2.73-5.25% of pixels exceed an eight-level
  delta, and the visible addition reads as a thin repeated brown shelf that worsens the
  layered-plate look at Meat Grinder and Troublemaker instead of adding believable local
  cutbank, gravel, rock, root, soil, or vegetation structure. The runtime path and thirteen
  orphaned meshes were removed while captures and a durable rejection ledger were kept.
  The accepted v169 map was restored with 200 stable identities; all 30 HLOD actors rebuilt,
  one settling repeat saved one package, and the final repeat saved zero. Renderer-backed
  M7 passes. v171 contributes no runtime change and closes no photoreal, named-review, media,
  or release gate; M9 remains fail-closed, uncommitted, and unpushed.
- The rejected v172 Forest Ground 03 bracket reused the existing hash-locked, rights-reviewed
  CC0 4K albedo, normal, and roughness on thirteen transient terrain components without map,
  collision, hydraulics, navigation, or package mutation. The candidate and rollback UE 5.8
  builds pass, focused suites pass 36/36 before and 35/35 after removal, and all five fixed
  photographic views render. Manual comparison rejects the result: only isolated bank regions
  change; Coloma and Troublemaker gain brighter tan material islands and harder discontinuities
  without believable gravel, rock, root, soil, cutbank, or vegetation-transition structure.
  The locked parent also projects at 3.2 m while the publisher documents a 2.0 m physical
  width, so direct promotion would violate the source-scale contract. Candidate runtime and
  test paths were removed; captures and a durable rejection ledger remain. The exact-current
  map and build-manifest hashes are unchanged and renderer-backed M7 passes. v172 closes no
  photoreal, named-review, media, or release gate; M9 remains fail-closed, uncommitted, and
  unpushed.
- The rejected v173 woody-debris bracket used source-conditioned shore-cobble samples to place
  three camera-forward log/root-wad clusters in each fixed view with existing rights-reviewed
  CC0 pine bark. Candidate and rollback editor builds pass, focused suites pass 36/36 before
  and 35/35 after removal, and all five photographic views render. Manual review rejects the
  straight cylinders as oversized poles, the radial root fans as synthetic prongs, and several
  placements as floating or intersecting the coarse bank, especially at Troublemaker, Coloma,
  and Salmon Falls. The transient capture path and tests were removed; no map, collision,
  hydraulics, navigation, package, or gameplay authority changed. Captures and the durable
  rejection ledger remain as negative evidence. Exact-current map and build-manifest hashes
  are unchanged and renderer-backed M7 passes. v173 closes no photoreal, named-review, media,
  or release gate; M9 remains fail-closed, uncommitted, and unpushed.
- The rejected v174 reflective-water bracket applied only transient dynamic-material values to
  fourteen median base-water components, increasing sky reflection while reducing roughness and
  keeping ripple energy below the prior radial-streak bracket. The candidate and rollback editor
  builds pass, its focused source tests pass 23/23, rollback source/rights suites pass 35/35, and
  all five fixed views render. Manual review rejects the result: Meat Grinder, Troublemaker,
  Coloma, and Salmon Falls expose dominant rectangular and polygonal light/dark patches aligned
  with the water mesh/material interpolation, making the surface read as tiled plates. Candidate
  code and tests were removed; no map, package, collision, hydraulic channel, solver mesh, or raft
  physics changed. Captures and the durable rejection ledger remain. Exact-current map and
  build-manifest hashes are unchanged and renderer-backed M7 passes. v174 proves scalar reflection
  tuning cannot close the underlying surface-fidelity gap and closes no photoreal, named-review,
  media, or release gate; M9 remains fail-closed, uncommitted, and unpushed.
- The retained v175 crew-stroke slice replaces the symmetric sine loop with a continuous
  catch/power/recovery curve, lifts each blade 26 cm through recovery, keeps both solved hands
  exactly on the visible shaft, and gives the four paddlers plus guide five deterministic timing
  offsets spanning 56.8 ms at the production cadence. The reduced-model impulse now lands at
  the 0.29 power phase after the visible catch instead of free-running on a hidden rest timer;
  per-stroke impulse, 0.8 s steady cadence, reaction latency, crew mass, D3/D4 authority, water,
  collision, rescue, terrain, maps, and packages are unchanged. The UE 5.8 target builds,
  source/rights gates pass 35/35, renderer-backed M5 passes 5/5, P3 crew propulsion passes 1/1,
  and exact-current M7 passes 1/1. The dedicated five-character frame retains the change as a
  technical animation/handling improvement but rejects photoreal acceptance: seated posture,
  arm/hand deformation, helmet fit, gaze/facial performance, and character/PPE shading remain
  synthetic, and no authored motion capture or named guide/art review exists. Evidence is in
  `docs/environment-captures/south_fork_full_reach/m9_crew_stroke_cadence_v175_review.json`.
  M9 remains fail-closed, uncommitted, and unpushed.
- The retained v176 helmet-fit correction raises the project-owned production shell 4 cm
  relative to the solved head pivot while preserving its 0.96 scale, mesh, materials, runtime
  head tracking, skeleton, hair policy, and every gameplay authority. In the matched
  front-starboard frame, all five eye lines are now visible instead of the v175 shell rims
  covering them like opaque visors. The editor target builds; source/rights gates pass 35/35;
  renderer-backed P3, M5, and exact-current M7 pass 1/1, 5/5, and 1/1. The improvement remains
  technical and photoreal-rejected: one shared fit cannot replace per-head brow/ear/occipital
  and retention landmarks, and hair edges, shell/strap detail, character anatomy, motion,
  gaze, hands, and PPE response remain synthetic. Evidence is in
  `docs/environment-captures/south_fork_full_reach/m9_helmet_fit_v176_review.json`. No named
  guide/art or release-media gate closes; M9 remains fail-closed, uncommitted, and unpushed.
- The rejected v177 arm-IK bracket replaced the production adapter's simple elbow midpoint
  with an analytic two-bone solve using each MetaHuman reference upper/lower-arm length while
  preserving the v36 palm-on-shaft targets. The source/rights gates, editor build, and P3
  propulsion test passed, but the matched renderer frame showed multiple elbows folding upward
  behind shoulders and helmets and hooked, anatomically impossible foreground arms. Candidate
  runtime and the temporary review flag were fully removed; the exact v176 adapter/test hashes
  are restored, source/rights gates pass 35/35, the editor builds, and exact-current M7 passes
  1/1. The rejected frame and rollback ledger remain in
  `docs/environment-captures/south_fork_full_reach/m9_arm_ik_v177_review.json`. Production arm
  deformation still requires authored rig/mocap work; v177 closes no gate.
- The retained v178 production-helmet-liner slice recesses the project-owned crown,
  occipital, and ear padding beneath the unchanged shell envelope. The matched five-character
  frame removes the large black shapes that protruded above and behind the v176 helmets while
  preserving all five eye lines, the v176 fit offset, six physical vents, four retention
  anchors, four material slots, and visual-only authority. The deterministic generator emits
  12,364 vertices and 12,296 polygons; the full-editor import audit measures 24,485 authored
  LOD0 triangles, enables Nanite, and records a 1,988-triangle fallback. The UE 5.8 target
  builds, focused character/source/rights gates pass 48/48, renderer-backed P3 and exact-current
  M7 pass 1/1, and M5 passes 5/5. v178 remains photoreal-rejected: small liner/webbing edges,
  shared rather than per-head fit, simplified shell/retention construction, generic materials,
  character anatomy, hands, gaze, PPE integration, and motion remain synthetic. Evidence is in
  `docs/environment-captures/south_fork_full_reach/m9_helmet_liner_v178_review.json`. No named
  guide/art, release-media, or milestone gate closes; M9 remains fail-closed, uncommitted, and
  unpushed.
- The rejected v179 continuous-surface-water diagnostic transiently replaced fourteen median
  base-water materials with the existing project-owned DefaultLit solver-surface parent. It
  preserved global station/lateral UVs and solver-foam overlays while disabling vertex tint and
  solver-field sampling, and never saved the map. The editor target and five-view photographic
  capture completed, but every view regressed: Meat Grinder and Troublemaker expose the broad
  water mesh as giant triangular and polygonal plates, and whole-frame mean RGB deltas span
  6.96-18.11 levels. The transient source path was fully removed; focused gates pass 48/48,
  the rollback editor target builds, exact-current M7 passes 1/1, and v178 is restored. Negative
  evidence is in
  `docs/environment-captures/south_fork_full_reach/m9_continuous_surface_water_v179_review.json`.
  The initial review attributed the plates to geometric normals/tessellation, but v180 later
  withdrew that inference after isolating simultaneous source/HLOD rendering. v179 still closes
  no gate and its removed material remains unaccepted because it lacked a valid exclusive review.
- The retained v180 source/HLOD-exclusive capture correction resolves the cause of v179's
  polygon mosaic without changing runtime content. `LoadAllActors` had loaded source actors and
  their instanced World Partition HLOD proxies together; the raw editor-world capture could draw
  both, while v179 changed only fourteen source materials. v180 now suppresses 185 HLOD primitive
  components whenever fully loaded source truth is captured and mirrors the configured
  `median_runnable` selector across 64 tagged flow-band components, hiding 41 inactive components
  before restoring every prior visibility state. The corrected five-view set is continuous and
  differs from accepted v169 by only 0.73-1.14 mean RGB levels, so the earlier geometric-normal
  inference is withdrawn. The editor source remains within its 3,000-line guard, the generated
  inventory is current, focused gates pass 48/48, the UE 5.8 target builds, and renderer-backed
  M7 passes 1/1. Evidence is in
  `docs/environment-captures/south_fork_full_reach/m9_source_hlod_exclusive_v180_review.json`.
  This is a retained evidence-correctness improvement, not a photoreal upgrade: the water remains
  dark, uniform, low-volume, and under-aerated; M9 stays fail-closed, uncommitted, and unpushed.
- The retained v181-v184 named-rapid water slice replaces the formerly sparse global-only
  Froude presentation with a layered, explicitly bounded authority chain. v181 preserves the
  legacy Froude base and adds solver surface-slope, acceleration, strain, and convergence only
  inside smooth named-rapid handoff envelopes. v182 adds at most 0.42 m of non-colliding
  solver-gated breaking relief. v183 supplements missing presentation geometry with flow-scaled
  ellipses derived from the guide inventory's hole, ledge, wave-train, lateral, rock, eddy-line,
  shallow, and strainer records; the manifest labels this source
  `procedural_infill_interpreted_from_guide_inventory_pending_human_review`. v184 refines only
  qualifying whitewater overlay cells from the two-metre base grid to one metre, producing 24
  overlay actors and 396,425 triangles with a 0.56 m maximum presentation displacement. All
  additions are visual-only and change no hydraulic field, collision, buoyancy, navigation,
  raft physics, rescue, or progression authority. Median-flow global aerated wet-cell coverage
  rises to 6.7546% (low 3.9886%, high 7.4469%). The UE 5.8 target and authoritative world build
  succeed; a settled source-only capture loads 201 references and selects 23 of 64 flow-band
  components; focused environment/source/HLOD/rights tests pass 65/65; renderer-backed M7 passes
  1/1; M8 passes 4/4; and the fail-closed M9 suite passes 5/5. The M8 rerun also corrects a
  stale test-only canopy topology expectation to match the retained two-plane crossed-card
  generator; no runtime canopy asset or generator changed. The M9 shoreline test now enforces
  the documented 0.42 m micro-relief source-contribution cap rather than the obsolete 0.24 m
  limit; the separate refined overlay displacement remains capped at 0.56 m. The complete
  Python/data/source matrix records 1,121 passes, three expected installed-dependency-path skips,
  and only the intentional fail-closed release-packet source-hash mismatch in 515.03 seconds.
  The final world
  rebuilds 28/28 terminal HLOD actors with zero errors and immediately
  converges to a 28/28 zero-save repeat; durable evidence hashes every current HLOD package.
  Graphify refreshes after the v185-v187 rollback and evidence update to 165,116 nodes,
  190,482 edges, and 13,656 communities. The v184 frame is
  the strongest technical water-readability baseline but remains photoreal-rejected: Meat
  Grinder is legible yet reads as bright polygonal ribbons over a dark flat sheet, Troublemaker
  remains underpowered, and coherent breaking lips, entrained-air volume, spray/mist, shoreline
  integration, production foliage/terrain, and lighting remain open. Review ledgers are
  `m9_solver_derived_aeration_v181_review.json`,
  `m9_solver_gated_breaking_relief_v182_review.json`,
  `m9_guide_feature_breaking_relief_v183_review.json`, and
  `m9_refined_guide_feature_foam_v184_review.json` in the full-reach capture directory. No named
  guide, art, geospatial, legal, owner, marketing, or release-media gate closes; M9 remains
  fail-closed, uncommitted, and unpushed.
- The rejected v185-v187 static aerated-volume experiment tested whether bounded
  multi-valued crest geometry could supply the missing pile/crest depth without altering
  solver or gameplay authority. v185 emitted 19 non-colliding actors containing 263
  solver/guide-gated sites and 42,080 triangles; its translucent carrier added depth at
  Meat Grinder but read as glass humps and made Troublemaker a broad synthetic mound. v186
  removed the water carrier and retained only translucent foam lace, but the matched frames
  barely changed and preserved the same glass silhouette. v187 reused the masked solver-field
  foam material; it removed the glass mound but reduced the new volume to disconnected bright
  shards and chevrons rather than turbulent whitewater. All three variants are visually
  rejected. Their source path, test-only contracts, material instance, and nineteen generated
  crest meshes were removed; the five-view capture sets and individual review ledgers remain
  as negative evidence. The authoritative v184 world was regenerated from source with 200
  stable actor identities, 24 foam actors, and 396,425 foam triangles. HLOD rebuilt 28/28;
  after one setup-settling resave, the final repeat rejected all 28 rebuilds and saved zero
  packages. Post-rollback source layout passes 23/23, HLOD evidence passes 6/6, M7 passes 1/1,
  M8 passes 4/4, and the exact manifest-sensitive fail-closed M9 suite passes 5/5. v184 remains
  the strongest technical baseline but is still photoreal-rejected, so M9 remains in progress,
  uncommitted, and unpushed.
- The rejected v188 raw-registered-macro diagnostic isolated the terrain material's
  source-image influence and tone chain without mutating the settled map or saving any
  package. Twenty-one detailed and far-field terrain components transiently used 100%
  registered macro colour at a neutral 1.0 tone. All five fixed photographic views
  changed materially from v184 (11.23-13.86 mean RGB levels; 58.44-63.10% of pixels
  changed by more than eight levels), proving that the registered texture path and UVs
  are active. Manual review rejects the result: banks become saturated green and smoother,
  distant slopes remain broad aerial/procedural colour regions, and no gravel, root,
  embedded-rock, cutbank, wet-edge, vegetation, or geomorphic structure appears. The
  experiment therefore identifies missing production-scale local bank morphology and
  material diversity—not suppressed NAIP colour—as the terrain blocker. Its temporary
  source path was removed; captures and
  `m9_raw_registered_macro_v188_review.json` remain as negative evidence. v184 remains
  authoritative and M9 remains fail-closed, uncommitted, and unpushed.
- The v189 riverbank-detail review converts a new project-owned, built-in-image-generation
  source into deterministic 1024-square albedo, normal, and AO/roughness/height maps without
  overwriting production v1. Exact opposite edges match on every map, Unreal validates
  1024-square running-platform data with eleven mips, and an opt-in capture path transiently
  binds the three maps to exactly thirteen detailed terrain components without saving the map
  or a production material. Five fixed views render successfully after 229 World Partition
  references load. Manual review accepts the pipeline and the more restrained brown gravel/soil
  read as useful review progress, but rejects production promotion: centimeter-scale content
  collapses at guide distance, the prompted 2.0 m patch is projected at the locked parent's
  unverified 3.2 m width, and the bank is still a smooth terrain ribbon without cutbank,
  gravel-bar, embedded-rock, root, or wet-edge morphology. The source, maps, review Texture2D
  assets, provenance, and opt-in comparison path remain isolated for future morphology work;
  v184 remains authoritative. Evidence is in
  `m9_riverbank_detail_v2_v189_review.json`. No photoreal, named-review, rights, media, or
  release gate closes; M9 remains fail-closed, uncommitted, and unpushed.
- The v190 scan-rock bank-morphology review transiently assigns six already imported,
  rights-reviewed CC0 Poly Haven rock scans across exactly 78 non-colliding scenic-rock and
  39 non-colliding shore-cobble components while retaining the v189 terrain-detail material.
  No map, mesh package, collision authority, or production asset is saved. The editor target
  builds in 84.44 seconds; all three review textures validate at 1024-square with eleven mips;
  five fixed views render after 229 World Partition references load. Manual and pixel review
  reject promotion. The scan donors improve a few large boulder silhouettes at Meat Grinder
  and Troublemaker, but existing cobble scales make the shoreline swaps nearly invisible:
  only 0.047960-0.160482% of pixels per view change above eight RGB levels from v189. Flat
  banks, absent cutbanks/bars/roots/wet edges, repeated vegetation, broad water, and synthetic
  lighting remain. Evidence is in `m9_scan_rock_bank_morphology_v190_review.json`; v184 stays
  authoritative and all photoreal, named-review, rights, media, and release gates stay open.
- The rejected v191-v194 embedded-bank sequence corrects the scan-placement hypotheses in
  controlled steps without changing collision, hydraulics, navigation, maps, or asset packages.
  v191 proves that the donors' raw bounds cannot be treated as centimetres because their LOD0
  build scale is 100x; its landscape-scale occluders are rejected. v192 removes that scale
  regression but leaves the donors buried because their bases sit 41-66 cm below their pivots.
  v193 includes effective post-build bounds and pivot compensation, but only 2,446 retained
  candidates across approximately 49 km remain visually absent. v194 increases density to 9,676
  of 15,702 candidates with patch-varying 48-96% retention and 0.25-1.90 m physical sizing.
  Four v194 views are nevertheless byte-identical to v190 and Salmon Falls changes by only
  0.000012 mean RGB; no pixel in any view exceeds an eight-level change. The existing shore
  samples are therefore rejected as a bank-morphology placement authority even after unit,
  pivot, scale, and density correction. Ledgers `m9_clustered_embedded_bank_rock_v191_review.json`
  through `m9_dense_embedded_bank_rock_fabric_v194_review.json` retain the evidence. The next
  attempt must derive longitudinal bank forms and visible gravel/rock/root/wet-edge distributions
  from river edges, terrain elevation, and water level with deterministic procedural gap filling.
  v184 stays authoritative; M9 remains fail-closed, uncommitted, and unpushed.
- The rejected v195-v197 water-edge-derived sequence replaces those shore-cobble transforms with
  a reversible source-conditioned placement seam. Fourteen median-water meshes supply encoded
  station/lateral coordinates, complex terrain traces anchor 4,521 longitudinal segments, and
  the transient layer creates 27,126 non-colliding bank triangles plus 3,828-4,971 visual-only
  scan rocks without saving maps or packages. v195 exposes a reversed-winding black face and
  broad planar wedges. v196 corrects winding, submerges and narrows the toe, and embeds smaller
  rocks, but the overlay becomes visually ineffective. v197 raises the toe in one final bounded
  bracket and densifies smaller rocks; the result is nearly absent in four guide-eye views and
  creates an angular shoreline shelf at Coloma. All three are photoreal-rejected. The review
  implementation is retained only as a non-authoritative authored-bank integration seam; the
  production correction now requires art-directed/scanned bank modules, source-conditioned
  erosion/deposition masks, multi-scale sediment and rock materials, roots/undercuts, wetness,
  and integrated vegetation/water dressing. Ledgers v195-v197 preserve hashes, measurements,
  and rejection reasons. v184 remains authoritative; M9 stays fail-closed, uncommitted, and
  unpushed.
- v198 tests a distinct bend-classified module hypothesis after correcting the review material's
  all-wet vertex-alpha defect. The transient layer derives 1,606 cutbank and 1,824 gravel-bar rows,
  connects 2,220 discontinuous segments (17,760 triangles), distributes 3,675 scan rocks across
  0.16-1.18 m, and adds 568 cylinder segments with the existing rights-reviewed CC0 fir-bark
  material. It compiles, passes its coverage guard, renders all five views, saves no map or
  derived-bank package, and changes no collision, hydraulics, navigation, buoyancy, raft, or
  gameplay authority. Visual review rejects it: corrected wetness exposes pale pyramidal berms
  and hard longitudinal seams at Chili Bar and Meat Grinder; roots do not resolve; rocks remain
  disconnected from sediment; Salmon Falls is unchanged. Procedural cross-section tuning is
  stopped. Production terrain now requires coherent scanned/authored bank modules with reviewed
  caps, material strata, embedded sediment/rock, exposed roots, wetness, and vegetation/water
  integration. Evidence is in `m9_erosion_deposition_bank_modules_v198_review.json`; v184 remains
  authoritative and M9 remains fail-closed, uncommitted, and unpushed.
- v199 tests a genuinely scanned, rights-clear bank-kit intake instead of another generated
  cross-section. Sixteen 2K payloads for Poly Haven Rock Face 01, Tree Stump 02, Roots, and
  Rocky Gravel match the publisher API MD5 values and pinned SHA-256 values; two publisher-scale
  Nanite meshes, fourteen textures, and four opaque PBR materials remain isolated under
  `ExternalReview`. A transient five-station pass places 136 rock faces, 66 stump/root scans,
  117 root patches, and 108 gravel patches using median-water station/lateral data and 427
  terrain hits without saving a map or changing collision, water, hydraulics, navigation, or
  gameplay. Visual review rejects the composition. The pale layered rock repeats as striped
  slabs, stumps resolve as dark rounded props, and opaque terrain cards expose rectangular
  orange/brown seams. These assets do not form a coherent Sierra bank, while water, terrain,
  foliage, and lighting remain synthetic. The auditable importer and isolated sources are
  retained as intake infrastructure; v199 placement and media are not promoted. Evidence is in
  `m9_scanned_bank_kit_v199_review.json`; v184 remains authoritative and M9 remains fail-closed,
  uncommitted, and unpushed.
- The v200-v202 Meat Grinder hero sequence tests a river-specific art-directed slice around the
  real guide line without changing runtime authority. v200 and v201 are rejected: the first
  produces detached orange bank arches from an averaged DEM profile, while the second replaces
  them with nearly black artificial shelves. v202 removes generated bank geometry completely and
  builds a read-only spatial index over thirteen settled DEM-derived terrain actors. All 1,760
  placement probes resolve to 14,311 indexed source vertices with zero procedural height fallback;
  ninety bank boulders, five guide-line channel hazards including a near-right-bank wrap benchmark,
  and fifty-seven detailed pines remain transient, non-colliding, non-navigable, and unsaved. The
  source-grounded review method and hash-gated CC0 `Boulder 01` intake are retained, but visual
  promotion is rejected: one pale donor repeats, banks remain smooth, vegetation remains card-like,
  water lacks convincing turbulent volume, and lighting/material integration is synthetic. v203
  then brackets six additional rights-reviewed scan-rock variants and 142 detailed small-tree
  analogs; it is also rejected and removed because the trees resolve as pale speckles, most canopy
  volume disappears into existing cards, and only 0.386719% of Meat Grinder pixels change by more
  than eight RGB levels from v202. The v203 capture remains as negative evidence. Focused
  editor-source contracts pass 26/26 and the UE 5.8 editor target builds. Evidence is in
  `m9_meat_grinder_hero_v202_review.json`; v184 remains the authoritative technical baseline and
  M9 remains fail-closed, uncommitted, and unpushed pending coherent production art and every named
  human/external gate.
- v204-v207 then tests the official Poly Haven `River Small Rocks` material and displacement as a separate
  rights-reviewed terrain input. Three 2K source payloads match official API MD5 values and pinned
  SHA-256 values; the isolated Unreal textures preserve the intended sRGB, OpenGL-normal, packed
  ARM, and 2.9 m physical-repeat contract. v204 is visually ineffective because the production
  source macro hides the replacement (0.03-0.58 mean RGB levels of fixed-view change from v202).
  v205 exposes the scan through transient dynamic-material parameters; it is rejected because the
  corridor becomes a broad beige sheet while pebble relief still does not resolve. v206-v207 add
  the official displacement field through 1,672 reconstructed shoreline rows, 21,736 detailed-DEM
  terrain traces, and 39,648 non-colliding triangles. The first bracket exposes pale contour-like
  fragments where the mesh intersects source terrain; the narrowed, lifted, darker correction
  still reads as artificial shoreline strips with seams. Geometry tuning is stopped. The importer,
  provenance, four isolated textures, review flags, coverage gates, captures, and fail-closed
  dimension/byte-layout contracts are retained, but no runtime content or media is promoted.
  Evidence is in `m9_river_small_rocks_v207_review.json`. The test closes both the texture-swap and
  unart-directed displacement-ribbon hypotheses: production now requires coherent authored/scanned
  bank modules with integrated caps and strata, multi-scale sediment/rock integration, wet-edge
  transitions, vegetation roots/understory, turbulent water volume, and art-directed lighting.
  v184 remains authoritative and M9 remains fail-closed, uncommitted, and unpushed.
- v208-v209 isolates a project-owned interior-live-oak branch-atlas hypothesis without changing
  production canopy authority. A built-in image-generation source supplies exactly twelve
  separated `Quercus wislizeni` branch studies; deterministic processing converts it to a padded
  2048-square 4x4 atlas with alpha, normal, and packed AO/roughness/subsurface maps while keeping
  the bottom four tiles transparent. v208 transiently swaps the oak HISM meshes to a retained
  billboard core plus thirty-six branch cards. It changes only 0.16-0.92% of fixed-view pixels by
  more than eight RGB levels and is rejected as visually ineffective because the planar core still
  dominates. v209 brackets a brighter isolated core and forty-eight larger, more widely distributed
  cards. It changes 1.17-2.74% of pixels above the same threshold but introduces pale leaf speckles
  and thin card silhouettes while the broad crown mass remains billboard-like. Both variants are
  rejected, canopy card-count/radius/tint tuning is stopped, and no runtime package is promoted.
  The source, deterministic derivation, isolated review seam, capture hashes, exact metrics, and
  authority boundary are retained in `m9_live_oak_branch_atlas_v2_v209_review.json`. The next
  credible canopy attempt requires species-appropriate trunk/branch topology, multiple crown-age
  variants, branch-aligned leaf clusters, controlled representation transitions, understory/root
  integration, calibrated lighting, and named art/ecology review. v184 remains authoritative and
  M9 remains fail-closed, uncommitted, and unpushed.
- v210 tests that missing topology with a two-section, true-woody interior-live-oak prototype. A
  new project-owned 2048-square bark source produces deterministic seamless albedo, normal, and
  packed PBR maps. The isolated mesh has 72 tapered trunk/branch segments, 45 terminal branches,
  90 branch-aligned leaf cards, 1,196 triangles, no billboard core, no collision, and no Nanite.
  Three Python commandlet authoring attempts correctly fail the strict running-platform texture
  gate at 0x0 / zero mips because commandlet mode cannot render; normal offscreen editor startup
  then validates all six textures at 2048-square / 12 mips and saves both materials plus the mesh.
  The transient five-view pass swaps 21 HISM components / 24,830 instances without touching the
  map or any ecology, placement, collision, hydraulic, navigation, or gameplay authority. Visual
  promotion is nevertheless rejected: sparse dark leaf-card fragments expose repetitive geometric
  limbs instead of a continuous evergreen crown, and the fixed frames still read as synthetic.
  The bark pipeline, topology, strict authoring gate, isolated integration seam, captures, hashes,
  and exact deltas are retained in `m9_live_oak_true_woody_v210_review.json`. The next input must be
  dense and leaf-dominant, support multiple crown forms and controlled representation transitions,
  and receive named art/ecology review. v184 remains authoritative; M9 stays fail-closed,
  uncommitted, and unpushed.
- v211 replaces the twig-heavy V2 leaf source with four dense, leaf-dominant terminal sprays from
  a new built-in image-generation pass. The exact prompt, untouched keyed source, soft alpha and
  despill output, largest-component quadrant cleanup, 4x4 atlas packing, tile-bounded mip padding,
  normal, and packed maps are deterministic and hash-gated. Tiles 0-3 contain 399,118 pixels above
  alpha 8; all twelve reserve tiles remain fully transparent. A separate dense-woody V2 package
  reuses the v210 bark and 72-segment scaffold, selects only those four tiles over 90 cards at
  1.12x scale, validates all six 2048-square textures at 12 mips, and passes a three-action editor
  build. Its transient five-view pass again swaps 21 HISM components / 24,830 instances without
  saving a map or changing gameplay authority. Crown continuity clearly improves over v210, with
  2.04% of pixels per view changing above eight RGB levels on average, but four silhouettes repeat
  as dark rounded clumps on one regular scaffold and the near/mid/far lighting response remains
  synthetic. Visual promotion is rejected; V3 is retained as the strongest current technical leaf
  source. Evidence is in `m9_live_oak_dense_woody_v211_review.json`. The next attempt requires
  several irregular crown-age/form variants, calibrated two-sided foliage lighting, variant
  selection, controlled transitions, and named art/ecology review. v184 remains authoritative;
  M9 stays fail-closed, uncommitted, and unpushed.
- v212 closes the next technical canopy bracket while preserving the same fail-closed authority.
  Three deterministic true-woody forms vary seed, scaffold count, crown width/height, and directional
  asymmetry; stable actor/component hashing distributes them across all 21 source oak HISMs and
  24,830 instances as 8/8,535 spreading, 5/8,421 compact, and 8/7,874 asymmetric. Six 2048-square
  textures validate at twelve mips. A calibrated masked TwoSidedFoliage material bounds baked AO,
  retains authored normal detail, uses no emissive compensation, and preserves alpha coverage.
  Every mesh has three strictly descending render LODs at explicit 1.00/0.34/0.12 screen sizes.
  The native editor target builds and the five fixed cameras render without saving the map or any
  production/gameplay-authority package. Visual review still rejects promotion: planar leaf clusters
  remain disconnected from exposed geometric limbs, fork/card patterns persist at Troublemaker and
  Coloma, and Salmon Falls silhouettes fragment. Component-level selection also cannot diversify
  individual instances inside each HISM, and fixed captures cannot validate moving-camera temporal
  transitions. The generator, distribution seam, material bracket, LOD authoring, assets, hashes,
  metrics, and negative evidence are retained in `m9_live_oak_crown_family_v212_review.json`.
  Procedural scaffold tuning is now stopped. Production needs rights-reviewed or art-authored
  botanical tree geometry with volumetric shoots, per-instance variation, roots/understory,
  temporal transition evidence, and named art/ecology approval. v184 remains authoritative; M9
  stays fail-closed, uncommitted, and unpushed.
- v213 then tests genuinely external, rights-reviewed tree geometry instead of extending the
  stopped scaffold. The existing Poly Haven Island Tree 01/02/03 intake provides a CC0 manifest,
  33 verified source files, three grounded Nanite meshes, thirty textures, and nine explicit
  trunk/leaf/branch materials. A new opt-in capture path labels them as generic morphology donors,
  not `Quercus wislizeni` or ecology authority; normalizes each to the current 12.5 m × 9.2 m oak
  proxy envelope; preserves source materials; and deterministically distributes them across the
  exact 21-component / 24,830-instance source population. Every original world transform and mesh
  is restored, and the saved map timestamp and hash do not change. The native editor target builds
  and all five cameras render, but visual promotion is rejected. Crowns become very dark narrow
  masses, branch/leaf sections create bright or sparse artifacts, and far silhouettes remain
  repeated vertical marks rather than a continuous California riparian canopy. The hash-locked
  intake and reversible integration seam are retained for a distinct masked-material/transition
  bracket; the donor content, frames, species identity, and authority are not promoted. Evidence
  is in `m9_live_oak_cc0_island_tree_morphology_v213_review.json`. M9 remains fail-closed,
  uncommitted, and unpushed pending reviewed California live-oak forms, per-instance/root/
  understory/temporal integration, named art/ecology approval, and every remaining external gate.
- v214 isolates one final leaf-material hypothesis on the same donor geometry. A review-only
  material reads the unchanged four 1K leaf textures after a ten-mip platform gate and applies lit
  masked TwoSidedFoliage, bounded opacity/normal/AO/roughness, per-instance energy, and no emissive
  shortcut to only mesh slot 1. The shared state now restores original material override arrays as
  well as every mesh and transform. All 46 native editor build actions pass, donor packages remain
  byte-identical, all five captures save, and the production map hash remains fixed. The result is
  visually ineffective: three views are byte-identical to v213 and the full set changes just
  0.021596 mean RGB / 0.089062% of pixels above eight levels. Dark narrow crowns, sparse or bright
  branch sections, repeated silhouettes, and far instability remain. This closes the leaf-only
  material hypothesis and stops Island Tree tuning. Evidence is in
  `m9_live_oak_cc0_island_tree_material_v214_review.json`; only the isolated material-authoring and
  exact override-restoration infrastructure is retained. M9 remains fail-closed, uncommitted, and
  unpushed pending new reviewed California live-oak geometry or equivalent authored art and every
  named human/external gate.
- The exact-current v214 full Python/data/source matrix reports 1,137 passes, three expected
  installed-dependency-path skips, and one intentional fail-closed release-packet failure in
  1,062.31 seconds. The sole failure preserves the documented M9 contract that refuses to treat
  the current post-v317 flexible-raft source as identical to the historical v42 review hash; it is
  not an unexpected numerical, geography, provenance, editor, or gameplay regression. The JUnit
  SHA-256 is `133861e50b3475aba344cd3b47c3c1df1dcbe445e0011324ad0e880ea5d92fbd`.
- The v220-v249 exact-current renderer/performance investigation profiles the cooked Development
  scene instead of inferring cost from asset counts. Nanite-off is catastrophically slower;
  reducing VSM rays, foliage, effects, post processing, reflections, Lumen cache settings, or
  duplicate character shadows does not recover a release-safe margin. TAA/bloom/cloud and
  shadow/GI reductions lower GPU cost, but TAA visibly regresses helmet, PFD, raft, and character
  edges and the result still fails the offscreen wall-clock gate. GI- and shadow-off controls get
  GPU p95 below 16.67 ms but still hitch, and are not acceptable production art. A cloud-only
  TSR/bloom-preserving run is statistically unchanged from baseline. Broad and close matched
  captures therefore retain TSR, bloom, clouds, Nanite, GI, shadows, and the current water. Water
  foam/specular/live-overlay/breaking-lip brackets do not isolate a safe visual improvement and
  are rejected rather than promoted. Exact metrics, capture hashes, and decisions are in
  `docs/release-review/m9-current-render-performance-diagnostics-v249.json`.
- Performance evidence is now explicitly fail-closed at the artifact boundary. Performance report
  schema v3 records whether `-RenderOffScreen` was used and distinguishes an
  `offscreen_engineering_diagnostic` from `normal_windowed_player_presentation`. Only a cooked
  Shipping, normal-window, otherwise passing run can set `release_performance_qualified: true`;
  the release-candidate finalizer treats an offscreen v3 report as failing even when its raw
  engineering `passed` field is true. The macOS RC workflow defaults to the windowed protocol and
  requires an explicit `RAFTSIM_RC_PERF_PROTOCOL=offscreen-diagnostic` opt-in for diagnostic use.
  This corrects the workflow/acceptance mismatch without weakening any budget. The current local
  offscreen runs remain negative engineering evidence, and fresh exact-current Shipping
  normal-window runs remain required before M9 can close.
- Cooked v250 verifies the schema-v3 guard in the actual packaged runtime and artifact parser. A
  Development `-RenderOffScreen` report is labeled `offscreen_engineering_diagnostic`, is ineligible
  for release qualification, remains unqualified, and is parsed as failing by finalization. Its
  deliberately short two-second sample also misses the raw engineering timing budget; it is guard
  evidence only, not performance acceptance. Report SHA-256 is
  `2f52d19421635bb15d56dbebf50e44fcc90d7ef5a212f590d2e45015c678e7e5`.
- The exact-current v252 full Python/data/source matrix reports 1,139 passes, three expected
  installed-dependency-path skips, and one intentional fail-closed release-packet failure in
  623.85 seconds. The sole failure remains the contract that rejects the current post-v317
  flexible-raft runtime-deformer hash as equivalent to the historical v42 reviewed source; there
  are zero unexpected failures. The JUnit SHA-256 is
  `a84e1411efe02cc3acf84f1ccbfaefd60c73c9464d06ba45aafbec1ae9db88f7`.
- Exact-current renderer-backed v252 native automation passes M4 4/4, M5 5/5, M7 4/4,
  M8 4/4, and fail-closed M9 5/5 with zero failures. A BeginPlay lifecycle guard eliminates the
  prior pooled Niagara `SetAutoActivate` warning burst without changing emission, assets,
  culling, simulation, or presentation authority. An intermediate cold M5 run also proves that
  texture gates must finish Unreal's asynchronous platform compilation before reading dimensions:
  v252 does so, retains the same 1K/2K thresholds, and passes cold. M4, M5, and M7 each retain one
  successful-with-warning case from UE 5.8's engine-owned TSR read of
  `r.MotionVectorSimulation`; the project never references that CVar. M8 and M9 are clean. Report
  paths and hashes are locked in `m9-current-render-performance-diagnostics-v249.json`. This
  refreshes local technical evidence but closes no Shipping/windowed performance, photoreal art,
  named human, external platform, input, signing, media, or distribution gate.
- The v269/v270 matched breaking-water review retains
  `r.Lumen.TranslucencyReflections.RadianceCache=0` for the High profile after full-resolution
  inspection finds no material loss in water reflections, breaking foam, mist, shoreline,
  foliage, or boulder presentation; breaking-water structural similarity is 0.974. The
  separate translucent-reflection cache mark disappears while opaque Lumen, Single Layer
  Water reflection captures, translucent-volume lighting, TSR, bloom, Nanite, clouds,
  authored water, and all nineteen production Niagara components remain enabled. The fresh
  exact-current game/content/renderer v273 macOS arm64 Shipping package passes build/cook/
  package, deep strict ad-hoc signature verification, 60/60 packaged rapid cases, RC QA,
  pristine-profile disk persistence, and a normal-window 1920x1080 High/60% Metal soak.
  Its 2,338 frames record 13.094 ms p95 frame/GPU, zero hitches, 0.275 ms average solver,
  and 5,560.5 MB peak memory; the runtime sets `release_performance_qualified=true`. Evidence
  is in `docs/release-review/m9-v273-translucency-cache-shipping-performance.json`. This closes
  the local exact-current technical performance gate only. The canonical workflow remains
  fail-closed on a protected sleeping Unreal commandlet, and dirty-source immutability,
  photoreal/named review, external input/hardware, Windows/Proton, distribution signing/
  notarization, approved media, accounts, and promotion remain open; M9 is still uncommitted
  and unpushed.
- Post-v273 native validation passes M4 v274 4/4, M5 v275 5/5, M7 v276 4/4, M8 v277
  4/4, and fail-closed M9 v278 5/5. The v279 exact-current Python/data/source matrix reports
  1,140 passes, three expected installed-dependency-path skips, one intentional fail-closed
  v42 visual-review hash mismatch, and zero unexpected failures in 421.41 seconds. JUnit
  SHA-256 is `be5e767599f6c0c6d671ee9e4c28ab9e684a046549399a2b9f2f3b379c79f6cb`.
  This closes the local post-change technical validation sweep without weakening the named
  photoreal approval or release-promotion gates.
- v280-v299 tests a project-owned photographic whitewater SubUV source without touching the
  selected production atlas, Niagara packages, maps, or solver/contact emission authority. The
  built-in image-generation source is deterministically reordered and conditioned into a
  2048-square 4x4 grayscale atlas with sixteen unique frames and at least 77 px / 15.039% black
  padding on every cell edge. A separate material, texture, five Niagara systems, and opt-in
  `-RaftSimPhotographicWaterAtlasV4Review` runtime seam keep the test isolated. Matched wrap and
  contact renders reject promotion: the unscaled candidate is nearly invisible at gameplay
  scale, while a review-only 2.4x spray / 2.0x droplet bracket exposes repeated soft puffs that
  read as smoke. A second BC4 grayscale-compression bracket exposes rectangular/checkerboard
  billboards when the photographic cells collapse into low gameplay mips. Both changes were
  reverted and all seven review assets were restored to the unscaled `TC_Masks` path and
  validated. Source ownership, the exact prompt, deterministic derivation, hashes, matched
  captures, both rejected brackets, and next-input requirements are retained in
  `m9_photographic_water_subuv_v4_review.json`. The next candidate must author individual,
  mip-safe ballistic particle events and pass close solver-authorized
  spray review before any promotion. M9 remains fail-closed, uncommitted, and unpushed.
- Post-restore renderer-backed validation passes M5 v300 5/5 (four clean successes and one
  successful-with-warning case from UE 5.8's engine-owned `r.MotionVectorSimulation` read) and
  fail-closed M9 v301 5/5 with zero warnings or failures. This confirms the photographic review
  seam cannot replace production defaults and does not weaken release gating.
- v305-v317 closes the particle-scale photographic V5 atlas hypothesis without changing any
  production default. Three project-owned image-generation donors are deterministically reduced
  to sixteen distinct, zero-border 512 px cells that all survive a 32 px-per-cell mip review. An
  isolated V5 material, texture, five Niagara systems, and opt-in
  `-RaftSimPhotographicWaterAtlasV5Review` seam compile and validate; simultaneous V4/V5 switches
  fail closed to production. A fixed `particle_macro` capture proves that review-only optical
  density can expose a sharp, irregular, porous water-film silhouette without V4's smoke puff,
  checkerboard, or rectangle artifacts. The established contact and wrap cameras nevertheless
  show only a small detached fuzzy mark and no material gameplay-distance improvement, including
  after a bounded mist-footprint expansion. Promotion is rejected and all production assets are
  hash-verified byte-identical. Evidence, prompts, source/asset/capture hashes, and the rejection
  rationale are locked in `m9_photographic_water_subuv_v5_review.json`. The next water-art
  architecture must use a connected solver-shaped sheet, ribbon, or mesh for temporal and
  surface continuity, with photographic masks limited to breakup detail. Final validation passes
  19/19 focused Python contracts, M5 5/5 (only the known engine motion-vector warning), and
  fail-closed M9 5/5 cleanly. M9 remains uncommitted and unpushed pending photoreal/named review,
  external platform and input, signing/notarization, approved media, account, and promotion gates.
- v318-v328 implements and closes the first connected-water V6 hypothesis while preserving the
  same fail-closed authority. An explicit `-RaftSimConnectedContactWaterV6Review` switch creates a
  noncolliding, shadowless 11 by 9 procedural sheet from the solver-sampled D4 contact shoulder and
  live-water heights; the 160-triangle component cannot change forces, collision, water samples,
  map state, scoring, or progression, and conflicts with photographic atlas switches fail closed.
  An isolated lit material uses V5 cells only as breakup detail. Native four-contact wrap/pin/
  recovery captures reject the representation: a high-density bracket proves connection but reads
  as a smooth glass wall, photographic coverage collapses to a detached tuft, and moving that
  coverage beyond the boulder makes the connected body disappear into the base surface. Production
  water assets remain selected and byte-identical. Full hashes, captures, implementation contracts,
  and the next multi-lobe/spline-layer requirement are locked in
  `m9_connected_contact_water_v6_review.json`. Final checks pass 20/20 focused Python contracts,
  renderer-backed M5 5/5 with only the known engine motion-vector warning, and fail-closed M9 5/5
  cleanly. M9 remains open, uncommitted, and unpushed pending a genuinely better water representation
  plus named art/guide review and every remaining external release gate.
- v329-v337 implements and rejects the requested multi-layer V7 contact-water architecture without
  weakening the same fail-closed authority. Three solver-sampled procedural sections independently
  supply the horizontal attachment (80 triangles), aerated crest (120), and two-lobe breakup (96),
  for 296 live noncolliding triangles during a four-contact wrap/pin/recovery state. A temporary
  vertex-color diagnostic proved that the original volume sat behind the contact boulder because
  the dominant contact vector points toward the obstacle; reversing only V7's presentation direction
  moves all three layers to the raft-rock pin. The real lit shader then exposes a smooth translucent
  sail. A final bounded lower/wider geometry and independent foam-density bracket reduces its height
  but still does not read as turbulent water. The diagnostic code path is removed, V7 remains disabled
  unless its explicit review switch is supplied, production assets remain hash-verified byte-identical,
  and promotion is rejected. Final validation passes 21/21 focused contracts, M4 4/4, M5 5/5,
  M7 4/4, M8 4/4, and fail-closed M9 5/5. M4, M5, and M7 retain only the known engine motion-vector
  warning; M8 and M9 are clean. The regenerated editor source inventory covers 62 files / 68,492
  lines, and the v343 full matrix reports 1,144 passes, three expected dependency-path skips, one
  intentional historical-v42 fail-closed mismatch, and zero unexpected failures. Exact captures,
  source/asset/log/report hashes, and the next closed/depth-layered volume requirements are recorded in
  `m9_connected_contact_water_v7_review.json`. M9 remains uncommitted and unpushed pending every
  photoreal/named-human, external platform/input, signing/notarization, media/account, and promotion
  gate.
- v344-v352 implements and rejects the closed-lobe V8 contact-water hypothesis without changing
  gameplay authority. An explicit `-RaftSimConnectedContactWaterV8Review` switch creates one sampled
  64-triangle horizontal attachment plus six independently phased, flow-aligned, sealed 112-triangle
  lobes for 736 live triangles at the D4 raft-rock pin. Collision, shadow, navigation, forces, water
  samples, map state, scoring, and progression remain unchanged, and V4-V8 conflicts fail closed.
  The first native frame proves attachment but reads as six repeated white teeth. A bounded final
  bracket widens and flattens the lobes, lowers their arch, and roughly halves foam density; it removes
  the teeth but also makes the bodies effectively disappear into the base river, so promotion remains
  rejected. Focused contracts pass 22/22; production-default M4 v348 passes 4/4, M5 v346 5/5,
  M7 v349 4/4, M8 v350 4/4, and fail-closed M9 v351 5/5. The v352 matrix reports 1,145 passes,
  three expected dependency-path skips, one intentional historical-v42 mismatch, and zero unexpected
  failures in 439.568 seconds. V6-V8 now bound the current analytic translucent-mesh family between
  walls/fins and invisibility. The next candidate must use a temporally evolving depth-bearing
  FLIP/VDB/mesh cache or bounded Niagara Fluids volume, warped and emission-gated by the existing
  solver, with advected entrained air, anisotropic spray, collision-aware breakup, and short-sequence
  review. Exact hashes and negative evidence are recorded in
  `m9_connected_contact_water_v8_review.json`. M9 remains uncommitted and unpushed pending accepted
  photoreal art, named human review, external platform/input, signing/notarization, media/account,
  clean immutable qualification, and promotion gates.
- v353-v369 closes the direct stock Niagara Fluids feasibility branch and restores the fail-closed
  production baseline. UE 5.8's Grid3D FLIP Splash and continuous Hose templates both load and
  compile warm behind an explicit command-line plugin mount; both report active, visible components
  with roughly 2.3 x 2.1 x 1.2 m world bounds anchored to the existing D4 solver contact. The two
  decisive waterless frames retain four contacts, three wrapping segments, one pin, one recovering
  segment, 0.220 m indentation, and full wetness, yet neither template renders a perceptible liquid
  body. Only the existing production spray remains visible. Direct template reuse is rejected, the
  experimental runtime and capture hooks are removed, Niagara Fluids remains absent from the project
  descriptor, and production assets/maps remain unchanged. The next implementation must be a
  project-owned Niagara Fluids system or artist-authored FLIP/VDB/mesh cache with an explicit liquid
  renderer, project-owned materials, deterministic warm-up/cache, solver-contact emission volume,
  advected air, anisotropic spray, collision-aware breakup, and a persistent three-frame review.
  Post-revert validation passes M4 v364 4/4, M5 v365 5/5, M7 v366 4/4, M8 v367 4/4, and
  reconciled fail-closed M9 v370 5/5; v369 reports 1,145 passes, three expected dependency-path skips, one
  intentional historical-v42 mismatch, and zero unexpected failures. Exact captures, telemetry,
  hashes, and next requirements are recorded in `m9_depth_bearing_contact_water_v9_review.json`.
  M9 remains uncommitted and unpushed pending accepted photoreal art, named human review, external
  platform/input, signing/notarization, media/account, clean immutable qualification, and promotion.
- v371-v437 implements the distinct project-authored V10 depth-bearing candidate and closes its local
  technical validation. Six deterministic closed implicit-volume frames are generated once at
  `BeginPlay` with marching tetrahedra, expose 104.89 cm of depth, and animate one 10,700-11,092
  triangle section at 0.12-second cadence. Existing D4 contact and live-water samples control only
  presentation transforms, material parameters, and frame visibility; collision, forces, water,
  maps, scoring, rescue, and progression authority do not change. Three forced frames plus unforced
  and waterless-isolation runs prove temporal change and attached volume where V9 rendered none.
  Renderer review still rejects the full scene as photoreal, no named water-VFX art reviewer or
  qualified South Fork guide has approved it, and the candidate remains opt-in, default-off, and
  unpromoted. Exact-current gates pass M4 v431 4/4, M5 v432 5/5, M7 v433 4/4, M8 v434 4/4,
  reconciled M9 v437 5/5, and v436's 1,150-test matrix with 1,146 passes, three expected skips, one
  intentional historical-V42 mismatch, and zero unexpected failures. Exact evidence is in
  `m9_depth_bearing_contact_water_v10_review.json`. M9 remains uncommitted and unpushed pending
  accepted photoreal art, all named reviews, external platform/input, signing/notarization,
  rights-cleared media, distribution accounts, clean immutable qualification, and promotion.
- Organic bank mosaic V2 closes the latest local low-cover pass without weakening M9. The
  deterministic ground-cover mesh now combines 52 narrow grass blades with ten low forb leaves;
  source-conditioned placement spans 22-118 m from the river with shoreline/outer-bank fades, and
  the settled map records 220,759 collisionless ground-cover instances plus 82,609 near-corridor
  foliage instances. All five canonical captures were regenerated from the saved map, and the final
  HLOD repeat evaluates 28/28 actors with zero modified packages. Validation passes the editor build,
  focused native 1/1, source-layout 35/35, M4 4/4, M5 5/5, M7 4/4, M8 4/4, the 1,148-pass Python
  matrix with three expected skips, and two 6/6 M9 runs. The scene is materially less bare but still
  photoreal-rejected for procedural tuft forms, repeated/sparse vegetation, coarse terrain materials,
  distant cards, and synthetic lighting. M9 remains in progress, uncommitted, and unpushed because
  named product-owner, guide, art, geospatial, and rights review; five-view approval; fresh-device
  input; Windows/Proton; signing/notarization; approved media; exact-current performance; clean
  immutable rebuild; and promotion gates remain open.
- Fuller seated hips V2 closes the reported production-character silhouette gap without
  changing gameplay authority. The retained 18-ring by 32-side pelvis shell broadens the
  waist-to-glute bridge, adds localized seated profile depth, and separates the thigh roots
  with a central saddle. Five production identities pass with zero hip-centre error and a
  minimum measured half-extent of 14.25×21.16×14.10 cm; the editor build, 36 focused Python
  contracts, M4 4/4, M5 5/5, M7 4/4, M8 4/4, the 1,148-pass full matrix, and two 6/6
  fail-closed M9 runs are green. The prior narrow V1 and a
  skirt-like first V2 bracket remain rejected visual evidence. Final photoreal anatomy,
  wetsuit deformation, and character-art approval remain open, so M9 is not promoted and no
  milestone commit or push is permitted yet.
- Upright fitted production river boot V1 resolves the reported inverted footwear read while
  retaining the existing project-owned mesh and support points. Runtime placement now constructs
  a toe-forward/cuff-up basis explicitly, fits the overly tall source cuff to 68% height, and
  offsets from the actual source sole bound so every tread remains at its prior planted height.
  Ten of ten boots across the five production identities pass the fitted-upright invariant;
  the editor build, 36 focused contracts, M4 4/4, M5 5/5, M7 4/4, M8 4/4, the 1,148-pass
  exact-current full matrix, and independent 6/6 M9 runs v560 and v561 are green. Rigid ankle
  deformation, photoreal wet materials, and named character-art/guide acceptance remain open,
  so this is a technical baseline rather than release promotion.
- Closed-finger paddle grip V1 closes the reported open-hand/edge-contact defect without
  moving the existing shoulder, elbow, wrist, palm, paddle, physics, collision, or gameplay
  authority. Each visible lower hand now wraps four non-thumb finger chains around the shaft;
  each upper hand wraps around the transverse T-grip. Across five production identities the
  maximum palm-anchor error is `1.880034572465661e-9` cm and the maximum eight-distal-joint
  contact error is `0.0` cm. The editor build, 38 focused acceptance/source contracts, M4 4/4,
  M5 5/5, M7 4/4, M8 4/4, the 1,148-pass full matrix, and independent 6/6 M9 runs V567 and V568
  are green. Coarse hand anatomy, thumb contact, wet skin/material response, synchronized stroke
  biomechanics, and named character-art/guide acceptance remain open, so M9 is not promoted and
  no milestone commit or push is permitted yet.
- Tapered shoulder sleeves V2 supersedes the ball-like uniform sleeve silhouette retained by
  Visible Shoulders V1 without moving solved shoulder or elbow anchors. Each project-owned
  splash-jacket sleeve is now a closed 18-ring by 28-sided surface with a broad deltoid,
  continuous upper-arm taper, and restrained cuff roll. All five production identities expose
  553 authored vertices per sleeve, retain the visible-shoulder contract, and stay within
  `1.3605050241949357e-7` cm of the authoritative shoulder anchor. The editor build, 16 focused
  Python contracts, five-identity renderer roster, and renderer-enabled M5 gate pass. Production
  cloth folds, skinning/deformation, identity-specific tailoring, cuff and torso integration,
  wet-material response, and named character-art/guide acceptance remain open; this is a
  fail-closed technical candidate, not photoreal promotion.
- Folded wet splash sleeves V3 supersedes V2's smooth, glossy tubular surface while preserving
  its solved shoulder-to-elbow placement. Each project-owned sleeve now has 28 axial rings,
  36 radial sides, two bounded diagonal fold fields, cuff gathering, underarm seam relief,
  a softly elliptical profile, and finite-difference normals. The isolated opaque Cloth parent
  uses the three project-owned ripstop texture channels and shares the PFD's bounded
  presentation-only wetness. All five identities report 1,075 vertices per sleeve, live material
  response, visible shoulder silhouettes, and at most `1.3605050241949357e-7` cm shoulder-anchor
  error. The editor build, isolated material audit, 16 focused Python contracts, five-identity
  renderer roster, and renderer-enabled M5 gate pass. Front/profile/rear evidence shows more
  cloth-like breakup and lower rigid gloss than V2, but regular procedural folds, abrupt
  torso/cuff integration, missing skinned deformation and identity tailoring, and open named
  character-art/guide acceptance keep photoreal promotion false.
- Runnable Batoka terrain integration makes the retained Zambezi V12 world-aligned basalt
  material and V13 bounded morphology part of normal map generation instead of an isolated
  comparison path. Four tagged, non-colliding render tiles receive deterministic lava-flow
  terraces, joint recesses, and talus variation outside the protected river corridor; the
  hidden Copernicus Landscape remains collision, height-query, and physics authority. Python,
  editor-map, and PIE gates now fail unless all four conditioned tiles are present and use the
  intended material. This is a reproducible visual improvement, not photoreal acceptance: the
  30 m canyon silhouette, vegetation fidelity/density, water, lighting, and named art/guide/
  geospatial review remain open under M9.
- Zambezi organic basalt surface V16 improves that runnable map's material response without
  changing its geography or gameplay authority. A second 83 m world-aligned macro projection,
  two deterministic world-space mineral fields, a 4.8 m restrained detail layer, and bounded
  blue-gray/brown grading replace the former uniform tan wall response. In the matched 1280x720
  gameplay mask, mean canyon luminance falls from 0.7061 to 0.6448, saturation falls from 0.3255
  to 0.3003, and adjacent luminance variation rises from 0.00758 to 0.01115 with no terrain pixels
  below 0.18. The source DEM, four V15 render meshes, protected shoreline, collision, water,
  solver, route, hazards, and raft forces are unchanged. The result remains photoreal-rejected
  for rounded 30 m source forms, generic rather than reach-specific lithology, sparse/repetitive
  ecology, provisional shoreline/water/lighting, and open named guide/art/geology review.
- Zambezi Single Layer Water V1 replaces only Batoka's flat opaque candidate parent with
  an isolated physical water-volume material. Active scattering, absorption, phase, and
  behind-water controls combine with two opposed panned normal layers and bounded
  world-space optical variation; the generated ribbon remains non-colliding and cannot
  affect solver, raft, or terrain authority. Both 1280x720 canonical views were regenerated.
  They materially reduce the former camera-radial grooves and do not reproduce the earlier
  global Single Layer foreground split, but remain photoreal-rejected for flat broad-water
  response, missing rapid-specific hydraulics/foam/spray, coarse Batoka terrain, synthetic
  ecology, and absent named guide/art approval. The editor build, focused saved-material
  automation 1/1, schema-v5 map audit, and focused runtime map-load gate 1/1 pass. M9 stays
  in progress; this milestone does not close the external acceptance or release gates.
- Zambezi camera-visible organic bank cover V1 adds a separately auditable
  1,200-instance ground-cover mosaic to the two canonical downstream windows.
  The underlying project-owned mesh now uses 54 solid tapered grass blades and
  11 low forb clusters over a several-metre footprint; no masked cards return.
  Placement begins beyond each camera target, searches ten DEM candidates for
  the lowest slope, and remains outside the 72 m active river half-width with
  collision disabled. The regenerated images visibly break up both formerly
  barren banks. Schema v6 passes with five components, 6,800 total instances,
  one tagged camera-visible mosaic, zero legacy PVE actors, and the existing
  runnable/water/terrain contracts intact. The result remains photoreal-rejected
  for sparse/repetitive procedural clumps, rounded 30 m terrain, missing
  authentic Batoka ecology, and absent named guide/art approval; M9 stays open.
- Zambezi camera-visible woody ecology V1 adds three separately auditable HISM
  actors to both canonical downstream windows using the existing solid opaque
  riparian-tree, umbrella-tree, and thorn-scrub meshes. The retained bracket
  places 58/57/117 instances respectively; eight of 240 deterministic targets
  are rejected by a hard 24° DEM-slope ceiling, and the maximum accepted slope
  is 15.83°. Muted olive vertex colours and a 9% low-light material floor reduce
  the oversized green/black read of the rejected first bracket. Both images now
  show restrained multi-height ecology, schema v7 passes with eight components
  and 7,032 total instances, and the runnable terrain/water/rapid contracts stay
  unchanged. Procedural repeated crowns, missing authentic species/wind/
  seasonal variation, coarse terrain/lighting, and absent named guide/art
  approval still reject photoreal promotion; M9 remains open.
- Zambezi live solver rapid foam V1 makes the already computed advected foam
  field visible without restoring the rejected rectangular moving-water
  overlay. A separate masked procedural sheet follows the displaced live
  surface, uses the existing pixel-level raft/crew exclusion material, and
  remains non-colliding, shadowless, navigation-inert, and physically
  non-authoritative. The exact-current runnable launch exposes eight accepted
  breaking sites and 125 focused foam vertices; P2 water-surface and focused
  Zambezi PIE gates pass. The retained oblique capture improves localized
  rapid readability but remains photoreal-rejected for broad flat water,
  polygonal analytical breaking forms, coarse canyon terrain, sparse synthetic
  ecology, lighting, and absent named water-VFX-art/guide approval. M9 remains
  open.
- Zambezi sediment water V2 keeps Batoka Gorge in the six-river runnable
  portfolio while correcting the calm physical ribbon's synthetic surface
  response. A matched Unreal gameplay bracket selects 0.48 opacity, 0.50
  roughness, 0.26 specular, 0.04 normal and optical-variation strength, 0.92
  mesh-normal up blend, and 0.08 authored displacement with sediment-specific
  scattering and absorption. Mean horizontal image-gradient energy in the
  audited water band falls 39.7%, removing most long streamwise grooves without
  changing the transparent live solver carrier, focused foam sheet, raft/crew
  foam exclusion, collision, navigation, forces, or hydraulics. The editor
  build, two focused Python contracts, saved-material test, water-render test,
  runnable-map load test, and schema-v12 25-marker saved-map audit pass. The
  accepted frame still exposes coarse bright terrain, sparse synthetic ecology,
  calm broad water, and simplified raft/crew art, so this is not photoreal or
  release promotion and M9 remains open.
- Torso-wrapped production PFD V2 removes the remaining backpack-like rear
  silhouette across every runnable river. The four chest cells now arc 2.0 cm
  toward the flanks; two independently rounded rear cells replace the single
  broad plate, add a narrow lumbar flex break, wrap 3.2 cm laterally, and reduce
  rear foam thickness from 4.8 to 4.0 cm. The regenerated production asset has
  26,664 authored triangles and a 2,416-triangle Nanite fallback. Five roster
  identities capture with production PFD selection and 0.0 cm maximum
  torso-origin error; five focused Python contracts and the renderer-enabled M5
  crew presentation gate pass. The runtime transform, collision, mass,
  animation, water, D3/D4, rescue, and gameplay authority are unchanged.
  Simplified fabric/hardware, identity-specific deformation, seated motion, and
  named character-art plus qualified whitewater-safety approval remain open, so
  this is a technical baseline rather than photoreal promotion.
- Integrated soft-carrier production PFD V3 supersedes that geometry baseline
  across every runnable river. A 0.9 cm fitted carrier supports four thinner
  4.2 cm chest cells and two rounded rear cells. The two rigid yellow side wings
  are removed; three flat fit connectors per side preserve all eight adjustment
  points; duplicate tubular side bands are removed; and the rescue belt becomes
  a 0.36 cm flat torso-following webbing loop. The regenerated asset has 39,448
  authored triangles, a 2,667-triangle Nanite fallback, five material slots, and
  39.025 x 34.52 x 42.8 cm bounds. Five production identities retain the asset
  with 0.0 cm maximum torso-origin error; six focused Python contracts, the
  editor build, and renderer-enabled M5 crew presentation pass. Collision, mass,
  animation, water, D3/D4, rescue, and gameplay authority are unchanged. The
  retained candidate is still photoreal-rejected for remaining foam faceting,
  simplified textile/hardware response, identity-specific deformation, seated
  presentation, and missing named character-art and whitewater-safety approval.
- Cloth and live-wet production PFD V1 replaces the same shell material on every runnable
  river with Unreal Cloth shading, project-owned PfdRipstop albedo/normal/packed maps, and
  one shared dynamic instance per avatar. Native raft surface wetness controls the seated
  baseline while swimming, re-entry, and falling impose immediate presentation-only floors;
  the 0.84 swimmer bracket is retained after reducing its wet specular endpoint to 0.42,
  saturated roughness to no less than 0.40, and wet cloth amount to 0.16. Five roster
  identities expose the live response, matched guide frames prove 0.0-to-0.84 material
  change, four focused contracts pass, the editor builds, and renderer-backed M5 reports
  five successful rows with zero failures. Physics, collision, mass, rescue, scoring, and
  progression authority are unchanged. Character/PFD art and named art/safety acceptance
  remain open, so M9 is not promoted.
- Pacuare organic rainforest terrain V1 replaces the source Landscape's flat unlit
  green response with a Pacuare-only Default Lit graph. Three incommensurate
  world-space fields vary broad humid-forest value, moss versus leaf litter, and
  fine mineral response; smoothed Landscape slope adds bounded wet-rock and rock-moss
  shading. The graph has no world-position offset and does not modify the 1009x1009
  review-gated heightfield, preview channel burn, Landscape collision, water ribbon,
  solver, route, or gameplay authority. The regenerated 256-component map passes
  MapCheck with zero errors and warnings, audits 256/256 source and 256/256 Nanite
  material slots, and retains 48 boulders plus 420 vegetation instances. The editor
  build, 37 focused Python/source-layout contracts, and the focused saved-material
  automation test pass. Both canonical 1280x720 downstream views now expose materially
  broader terrain value and soil/moss variation, but the result remains photoreal-
  rejected for compressed/coarse preview geometry, broad smooth banks, generic repeated
  PVE vegetation, sparse near-bank ground cover, flat provisional water, missing
  rainforest atmosphere/VFX, and absent named Pacuare guide, ecology, geospatial, and
  environment-art approval. This is an organic terrain foundation, not M9 promotion.
- Pacuare rainforest Single Layer Water V1 replaces the map's flat Default Lit water
  sheet with a Pacuare-only physical water-volume parent. Two opposed moving normal
  layers, two incommensurate world-space variation fields, active scattering,
  absorption, phase, behind-water color, and index-of-refraction controls now drive the
  saved material instance. Render width falls from 1.45 to 1.05, analytic displacement
  from 0.78 to 0.20, and the review cameras frame more downstream geography; the
  regenerated views retain readable gray-green surface motion instead of the rejected
  near-black first bracket and overbright cyan second bracket. The procedural ribbon
  remains non-colliding, has no world-position offset, reuses no cross-river solver
  fields, and cannot change terrain, raft forces, hydraulics, route, or gameplay
  authority. The editor build, zero-error/zero-warning MapCheck, focused native material
  test, and 44 Python/source-layout contracts pass. This remains photoreal-rejected for
  a visible near-camera transition, small river-right terrain voids, missing Pacuare-
  specific rapid hydraulics/foam/spray, coarse smooth banks, generic repeated ecology,
  and absent named guide, water-VFX, environment-art, ecology, and geospatial approval;
  M9 and the external acceptance gates remain open.
- Pacuare water depth-composition correction V1 supersedes that retained visual
  bracket without erasing its evidence. Direct isolation and a 31,409-vertex,
  48.5-267.6 cm procedural reference-infill bathymetry attempt both leave the hard
  lower-frame Single Layer depth band; a two-sided terrain-infill attempt covers the
  white gaps but creates broad tessellated bank facets. Both synthetic geometry paths
  are rejected and absent from the saved map. Pacuare now uses its own opaque Default
  Lit rainforest water parent, retaining two moving normal layers, two world-variation
  scales, and the accepted scalar palette with no world-position offset. A 1.35x
  render-only overlap removes continuous shoreline gaps and leaves one tiny distant
  river-right point for source-aligned production microgeometry; collision, solver
  width, Landscape heightfield, hydraulics, and raft forces are unchanged. The two
  canonical captures have no lower-frame band and MapCheck remains clean. This closes
  the visible composition regression only; coarse terrain, generic ecology, absent
  Pacuare solver hydraulics/foam/spray, production water and bank transitions,
  performance evidence, and named guide/art/ecology/geospatial acceptance still block
  photoreal and M9 promotion.
- Pacuare Upper Huacas reach-local runnable V1 supersedes the scale-mismatched
  broad DEM preview and the flat signature-rapid shell without claiming source
  fidelity that is not available. `L_UpperHuacas` now contains a physical
  600×78 m, 1009×1009 Landscape built from the committed C3 bed, with no
  procedural change inside the protected 17 m channel half-width or at the map
  perimeter and no more than 0.38 m of deterministic outer-bank relief. A
  301-point identity station/lateral map applies the measured 454.283 m runtime
  datum; static and live centerline surfaces agree to 0.0 m. During play the
  capture ribbon is hidden and the live finite-volume field owns rendering and
  forces. The rebuilt map passes 0/0 MapCheck, the focused runnable PIE gate
  1/1 with an upright raft and zero swimmers, both Pacuare material tests 2/2,
  and the deterministic terrain contracts. The new views remove the huge DEM
  facets and rectangular shoreline, but dark opaque water, generic sample
  foliage, absent visible rapid foam/spray at launch, missing production bank/
  riverbed optics, higher-resolution geography, and named guide/geospatial/
  hydraulic/ecology/art/performance approval keep M9 and photoreal promotion
  open.
- Colorado Hance reach-local runnable V1 replaces the flat signature-rapid
  shell and the scale-mismatched Lees Ferry preview without presenting either
  as surveyed Hance terrain. `L_Hance` now contains a 600×320 m, 1009×1009
  Landscape that preserves every sample of the complete 600×78 m interpreted
  C3 bed and adds deterministic asymmetric canyon relief only outside the
  protected 39 m solver half-width. A 301-point station/lateral map applies the
  950.713 m runtime datum with 0.0 m centerline error. The moderate-release
  cooked field, player raft/start, and vertical-slice game mode make the map
  reference-runnable; the authored field-derived ribbon and foam remain
  capture-only, non-colliding, and hidden during play. The editor builds, the
  focused runnable PIE gate passes 1/1 with an upright raft and zero swimmers,
  MapCheck reports 0 errors and 0 warnings, and the deterministic terrain,
  water, authority, and artifact-hash contracts pass. The canonical views are
  still photoreal-rejected for smooth tessellated-looking canyon walls, sparse
  generic ecology and ground cover, dark opaque stepped water, coarse foam
  mats, missing surveyed Hance geography, unconverged hydraulics, and open
  guide/geospatial/geology/ecology/water-VFX/performance acceptance gates; M9
  remains open.
- Colorado Hance organic terrain and native capture water V1 retain the same
  reference-runnable `L_Hance` geometry and live finite-volume gameplay water.
  A Colorado-only four-scale Default Lit shade graph adds bounded sandy-bench,
  weathered-rock, dark-rock, iron-cliff, talus, and fine mineral response with
  no world-position offset. The capture ribbon now uses a Colorado-only opaque
  Default Lit parent, two moving native normal layers, and the existing
  CPU-authored cooked-field vertex color; every shader-side solver-field gain is
  zero, so the shared South Fork fallback field is no longer sampled a second
  time. Fixed water-band luminance rises from 0.1922 to 0.2716 in the guide view
  and from 0.2225 to 0.3312 at river eye. The editor build, native terrain and
  water audits 2/2, and `RaftSim.P4.RiverMapLoads.L_Hance` pass. The retained
  captures remain photoreal-rejected for polygonal terraces, stepped opaque
  water, coarse foam sheets, sparse desert ecology and bank structure, missing
  surveyed Hance geography, unconverged hydraulics, and six required external
  acceptance gates; M9 remains open.
- Chilko Lava Canyon reach-local runnable V1 replaces the flat signature-rapid
  shell with a physical 600×600 m, 1009×1009 Landscape. Its broad canyon form
  follows the official BC Freshwater Atlas route through the committed NRCan
  CanElevation MRDEM-30 DTM, while the complete 600×80 m interpreted C3 bed is
  protected exactly and bounded sub-30 m procedural microrelief fills only the
  source-resolution gap outside it. The 301-point identity station/lateral map
  applies the 1101.713 m runtime datum with 0.0 m centerline error. Median-band
  cooked water, the player raft/start, vertical-slice game mode, and four
  interpreted review-gated C3 contact rocks make the saved map reference
  runnable; capture water and foam remain non-colliding and hidden in play so
  live solver water alone owns rendering and raft forces. The editor builds,
  the focused PIE gate passes 1/1 with an upright raft and zero swimmers, and
  MapCheck is clean. Dark opaque water, smooth broad banks, repeated sample
  foliage, sparse ground cover, limited rapid-specific rock detail,
  unconverged hydraulics, and open guide/geospatial/ecology/art/water-VFX/
  performance gates still reject photoreal and production promotion; M9 stays
  open.
- Chilko organic lit terrain V1 replaces the runnable map's nearly black
  generic bank response with a river-only four-scale Default Lit shade graph.
  It preserves source macro registration, material zones, close-range normals,
  wet-bank/riverbed conditioning, and the existing 1009×1009 Landscape, then
  adds non-harmonic 0.00016, 0.00059, 0.00270, and 0.00790 per-centimetre fields
  for open-bench value, dry grass and mineral soil, slope-aware wet/oxidized
  basalt, scree, and fine mineral variation. No world-position offset is
  connected, so terrain geometry, collision, the protected 600×80 m solver
  strip, route, cooked water, hydraulics, and raft forces are unchanged. In
  fixed left-bank regions, guide-seat mean luminance rises from 0.1199 to
  0.2375 and near-black coverage falls from 30.05% to 1.04%; river-eye mean
  luminance rises from 0.1397 to 0.2616 and near-black coverage falls from
  32.90% to 0.85%. The editor build succeeds; the native saved-material audit
  passes 1/1; `L_LavaCanyon` passes its runtime gate 1/1; and the focused
  terrain/water/isolation contracts pass. This is a retained technical
  foundation, not photoreal promotion: broad source-scale landform, horizontal
  material banding, repeated stylized trees, uniform opaque water, weak rapid
  foam/spray, unconverged hydraulics, and all named external gates remain open.
- Chilko native water V1 removes a cross-river presentation error from the
  retained Lava Canyon map. The physical capture ribbon now binds an isolated
  opaque Default Lit Chilko parent with the river's own first-party normal
  atlas, two moving normal layers, and non-harmonic 0.00027 and 0.00147 per-
  centimetre optical fields. The reach-local packed cooked field is interpreted
  once while the CPU builds ribbon geometry and vertex color; all shader-field
  gains are zero so the South Fork fallback can no longer double-condition this
  river. The live solver carrier retains sole gameplay rendering and force
  authority and now reads river-local reflection, ripple, foam, and water-color
  controls from the saved config. No water geometry, collision, terrain,
  hydraulic state, route, or raft-force value changed. Fixed-frame water-band
  comparisons raise mean luminance from 0.1522 to 0.2529 in the guide view and
  0.1518 to 0.2514 at river eye, with RGB standard deviation increasing from
  0.0463 to 0.0771 and 0.0473 to 0.0777. The native material audit and
  `L_LavaCanyon` runtime load gate each pass 1/1. This remains a rejected visual
  candidate: broad plate-like water, weak rapid relief, sparse foam/spray,
  smooth source-scale banks, repeated vegetation, incomplete bank structure,
  and all six named external acceptance gates remain open.
- Futaleufú Terminator reach-local runnable V1 replaces the flat signature-
  rapid shell and scale-mismatched 16 km corridor preview with a physical
  600×600 m, 1009×1009 Landscape. The review-gated OSM route scaffold and
  Copernicus GLO-30 surface define broad form; the full 600×84 m interpreted C3
  bed remains exact, while bounded terrain-edge correction and sub-30 m
  procedural microrelief fill only unresolved space outside it. A 301-point
  station/lateral map applies the 206.596 m runtime datum with 0.0 m centerline
  surface error. Median cooked water, player raft/start, vertical-slice game
  mode, and the one interpreted/review-gated entry-marker-boulder D4 contact
  make `L_Terminator` reference runnable. Capture water and foam are
  non-colliding and hidden during play so live solver water owns rendering and
  forces. The editor builds, focused PIE passes 1/1 with an upright raft and
  zero swimmers, and MapCheck is clean. Dark opaque water, understated rapid
  hydraulics, nearly black smooth banks, repeated placeholder vegetation,
  sparse ground cover, review-gated route/stationing, unconverged hydraulics,
  and open guide/geospatial/ecology/art/water-VFX/performance gates reject
  photoreal and production promotion; M9 remains open.
- Futaleufú organic lit terrain V1 fixes the runnable map's saved-material
  mismatch: its manifest promised Default Lit while the generator serialized an
  Unlit Landscape. A Futaleufú-only shade graph now preserves the registered
  source macro color, source zones, wet-bank/riverbed conditioning, and physical
  slope treatment, then layers three incommensurate world-space scales (0.00018,
  0.00071, and 0.00420 per centimetre) for humid temperate value, moss/leaf litter,
  wet granite/lichen, and fine mineral variation. It has no world-position offset
  and changes neither the 1009×1009 terrain, collision, cooked water, route,
  gameplay hydraulics, nor raft forces. The editor build succeeds; the saved
  material audit passes 1/1; `L_Terminator` loads 1/1 with zero errors and only the
  known `r.MotionVectorSimulation` engine warning; and all 32 focused Python
  contracts pass. In fixed left-bank regions, near-black coverage falls from
  13.17% to 4.77% in the guide-seat view and from 7.72% to 3.99% at river eye.
  This is a retained technical foundation, not photoreal promotion: coarse smooth
  30 m banks, repeated procedural ecology, flat dark water, weak Terminator
  hydraulics/VFX, sparse reach-specific bank structure, and all named guide,
  geospatial, hydraulic, ecology/geology/art, water-VFX, and performance gates
  remain open.
- Futaleufú native water V1 removes a cross-river presentation error from the
  retained Terminator map. The physical capture ribbon now binds an isolated
  opaque Default Lit Futaleufú parent with the river's own first-party normal
  atlas, two moving normal layers, and non-harmonic 0.00031 and 0.00163 per-
  centimetre optical fields. The reach-local packed cooked field is interpreted
  once while the CPU builds ribbon geometry and vertex color; all shader-field
  gains are zero so the South Fork fallback can no longer double-condition this
  river. The live solver carrier retains sole gameplay rendering and force
  authority and now reads river-local reflection, ripple, foam, and water-color
  controls from the saved config. No water geometry, collision, terrain,
  hydraulic state, route, or raft-force value changed. Fixed-frame water-band
  comparisons raise mean luminance from 0.1611 to 0.2063 in the guide view and
  0.1583 to 0.2028 at river eye, with RGB standard deviation increasing from
  0.0482 to 0.0722 and 0.0479 to 0.0719. The native material audit and
  `L_Terminator` runtime load gate each pass 1/1. This remains a rejected visual
  candidate: broad plate-like water, weak rapid relief, sparse foam/spray,
  smooth source-scale banks, repeated vegetation, incomplete bank structure,
  and all six named external acceptance gates remain open.
- Zambezi stable runnable delivery V1 promotes the already-validated complete
  Batoka Gorge reference run from the ignored `EnvironmentPreviews` namespace
  to the versioned `/Game/RaftSim/Maps/L_Zambezi` package. The editor generator,
  frontend scenario, generated player-selection source/model, scenario JSON,
  cook list, packaging fallback, runtime map-load gate, and docs now share that
  package. The map retains all 25 rapid markers, the Rapid 9 portage policy,
  safe five-person launch, full-corridor procedural live water, and current
  terrain/ecology/water presentation. This closes fresh-checkout delivery only;
  it does not promote inferred bathymetry, procedural rapid hydraulics, coarse
  terrain, synthetic ecology, or photoreal art, and all named external gates
  remain open.
- Zambezi runnable revalidation V2 regenerates only the filtered Batoka Gorge
  corridor and proves the complete player path again: `zambezi_reference_run`
  in the generated source model and M6 career catalog resolves to the shipping
  `/Game/RaftSim/Maps/L_Zambezi`, while the schema-v16 saved-map verifier,
  zero-error/zero-warning MapCheck, and live P4 PIE gate pass. The saved map
  contains all 25 rapid markers, Rapid 9's portage policy, the player raft/start,
  live cooked-field water, four conditioned terrain tiles, two adaptive banks,
  360 launch talus instances, and 8,927 vegetation instances. The new bank and
  talus wetness treatments are presentation-only and cannot drive terrain,
  collision, hydraulics, or raft forces. Current fixed-camera evidence remains
  visibly reference-quality, so photoreal and external acceptance gates remain
  open.
- Zambezi fixed-route capture water V3 replaces only the non-colliding
  physical-corridor presentation instance's rejected Single Layer parent with
  isolated `M_RaftSim_Zambezi_DefaultLitWater`. The retained graph preserves
  two moving cross-current normal layers, the secondary-axis swap, and bounded
  world-space variation while adding a first-party capture fill. Canonical
  lower-half mean luminance rises from 0.060286 to 0.247354 in the guide view
  and from 0.061027 to 0.223423 at river eye, with no retained lower-half pixels
  below 0.02. The schema-v16 saved-map audit, exact native material contract,
  focused runnable map load, and Python source/capture contracts pass. The old
  Single Layer asset and inactive volume settings remain rejected evidence, and
  no terrain, collision, solver, hydraulic, bathymetry, or raft-force authority
  changes. Broad smooth highlight bands, provisional geography, incomplete
  rapid-scale foam/spray, and all external acceptance gates keep the result at
  reference quality rather than photoreal promotion.
- Pacuare opaque rainforest vegetation V1 removes the bright and black PVE
  alpha-card wall from the runnable Upper Huacas map and its three canonical
  review frames. Four project-owned solid meshes—two canopy forms, riparian
  shrub, and ground cover—use a Pacuare-only opaque one-sided Default Lit
  vertex-color material, Nanite hierarchical instancing, deterministic
  source-mask placement, and slope screening. All 12,000 instances are
  non-colliding procedural infill with no species, ecology, terrain, water,
  solver, or raft-force authority. In the fixed guide and river-eye frames the
  bright-card-green artifact fraction falls from 1.6313%/1.5566% to
  0.0123%/0.0151%, while near-black frame coverage falls from 17.1912%/15.9486%
  to 7.9759%/7.1942%. The editor builds, the native Pacuare material/mesh,
  terrain, and water tests pass 3/3, and `L_UpperHuacas` passes its runnable PIE
  gate. The retained review explicitly rejects photoreal promotion: tree crowns
  and trunks remain visibly procedural, banks are still smooth and broad,
  river-edge structure and reviewed species/age/wind/wetness/season variation
  are incomplete, water lacks production rapid-scale detail, and all named
  external guide, geospatial, ecology, art, water-VFX, and performance gates
  remain open.
- South Fork organic foothill terrain V1 corrects both terrain paths instead of
  improving only the detached Landscape review. The physical-corridor Landscape
  is now Default Lit and uses a 0.58 palette correction; the actual frontend/
  campaign map, `L_SouthForkAmerican_FullReach`, consumes the same function at a
  source-preserving 0.30 strength through
  `M_RaftSim_PhotorealRiverTerrain`. Three incommensurate world-space fields
  combine summer dry grass, oak litter, granitic soil, slope-aware weathered
  granite, and fine mineral value. No world-position offset is connected and no
  DEM/static-mesh height, collision, shoreline, navigation, water, solver,
  hydraulics, or raft force changed. In the fixed Landscape right-bank region,
  pale-neutral coverage falls from 96.1066% to 0.0027%; across the five settled
  gameplay views, 7.89-17.50% of pixels change by more than eight RGB levels and
  every frame gains the intended warm dry-ground response. The editor build,
  exact two-material native audit, renderer-enabled M7 full-reach route, filtered
  Landscape capture, five settled-map captures, and nine Python contracts pass.
  The hash-locked review remains fail-closed: alpha-card foliage, repeated dark
  tree forms, sparse mid-story ecology, coarse smooth terrain, broad flat water,
  simple shoreline structure, synthetic lighting, and absent named environment-
  art, geospatial, and South Fork guide approval keep M9 and photoreal promotion
  open.
- Curved side-webbing production PFD V4 replaces the retained carrier's six
  straight rectangular flank bars with four thin open fabric arcs. Two per
  side now follow the torso and overlap both the front and rear carrier anchors,
  matching the referenced four-side-adjustment layout while retaining an
  articulated open side. The rejected solid side-gusset bracket was not
  promoted because fixed profile pixels read it as a rigid armor plate. The
  retained V4 adds no side flotation and no shoulder foam, reduces the exposed
  side sliders from six to four, preserves the flat rescue belt and five
  material slots, and leaves collision, crew mass, hydraulics, D3/D4 authority,
  rescue logic, and runtime transforms unchanged. Blender source validation,
  Unreal import, six focused Python contracts, five-identity fixed-view roster
  capture, and the renderer-enabled M5 crew presentation gate pass; all five
  identities retain production PFD selection and 0.0 cm maximum torso-origin
  error. The hash-locked review remains fail-closed for simplified fabric and
  foam response, intersections and identity deformation, and absent named
  character-art and qualified whitewater-safety approval; M9 and photoreal
  promotion remain open.
- CC0 rendered-face-fitted helmet V1 repairs the packaged fallback path that is
  used when the assembled MetaHuman roster is unavailable. The adapter caches
  64 LOD0 skin vertices nearest each authored eye line, averages their live
  post-skinning positions, publishes the rendered face forward/up frame, and
  applies bounded 10 cm guide and 6 cm Crew01 brow-seat corrections. The
  continuous production shell now contains a masked hair slot, so the five
  rights-tracked source hairstyles and attribution remain packaged without the
  detached cards that previously floated above the guide and Crew01 heads.
  All five front/profile/rear captures retain exclusive CC0 body ownership,
  production PFD/helmet/boots, 1.0 helmet forward alignment, 0.96 fit scale,
  and no more than `7.312e-10` cm solved-anchor error. The editor build and
  forced-CC0 renderer-backed M5 run pass with zero failed tests. This is a
  technical headgear-fit improvement only: simplified anatomy, skin/eye and
  clothing response, hands, helmet/webbing materials, lighting, named
  character-art approval, and qualified whitewater-safety review keep M9 and
  photoreal promotion open.
- CC0 skin reflectance calibration V1 replaces the fallback skin materials'
  broad subsurface response with Unreal's preintegrated skin shading and
  applies one linear scalar per existing, hash-locked source atlas. The gains
  preserve every atlas pixel and hue family while bringing five differently
  exposed photographic sources into the fixed roster-lighting bracket. All
  five profile comparisons reduce p95 luminance (guide 244.974→228.160,
  Crew01 173.276→170.081, Crew02 241.901→231.382, Crew03 248.127→237.186,
  Crew04 176.291→173.662). The editor target builds and the forced-CC0
  renderer-backed M5 run records five successful tests with zero failures.
  This is a reflectance-only technical improvement: the rendered review still
  fails photoreal acceptance for simplified anatomy, closed-looking eyes,
  hands, clothing/PPE intersections, hair, and absent named character-art and
  qualified whitewater-safety approval. No identity geometry, rig, animation,
  gameplay, water, raft force, collision, rescue, scoring, or progression
  authority changed.
- CC0 eye reference-pose and rendered helmet-anchor V1 removes the remaining
  detached facial-detail defect from the packaged fallback. All five checked-in
  FBXs now bake their evaluated shape and Armature deformation into raw mesh
  geometry, promote the displayed armature pose to rest, and restore exactly one
  clean Armature modifier. The schema-v2 validator passes raw reference,
  evaluated reference, paired facial Skin, and 58° synthetic-head checks for
  every identity. Fresh Unreal mesh/skeleton pairs retain three LODs, and the
  native M5 gate measures maximum eye/brow p95 reference separations of 0.368 cm
  and 1.120 cm against a 1.25 cm limit. Helmet fitting now averages the live
  rendered Eye material vertices instead of a stale nearest-Skin sample and uses
  bounded identity offsets; 20/20 fixed roster views complete with every solved
  head above the upper-body fail-closed threshold. The editor build, 12 focused
  contracts, five Blender validations, renderer capture, and all five M5 tests
  pass. The eye/helmet transform defects are technically closed; simplified
  anatomy and expression, garment/arm/hand/PPE intersections, materials, and
  missing named character-art, qualified whitewater-safety, and product-owner
  approval keep M9 and photoreal release promotion open.
- Futaleufú/Chilko temperate bank ecology V4 replaces the shared four-mesh
  fallback with eight baked deterministic morphology meshes and adds 1,800
  source-Landscape-grounded dry-bank grass/forb/shrub patches per runnable map.
  Both `L_Terminator` and `L_LavaCanyon` retain their 4,650-tree canopy, live
  solver water, terrain/collision, player raft, and game mode while total
  vegetation increases from 6,200 to 8,000. Full-centerline clearance, dry
  height, and 38-degree slope gates place 1,800/1,800 patches with zero rejects
  in each river. The editor build, two focused runtime-map gates, 14 native M9
  terrain/water audits, and 156 focused Futaleufú/Chilko/temperate Python
  contracts pass. The fixed views
  show a denser bank-to-tree transition and genuine silhouette variation, but
  the retained review remains fail-closed for procedural botanical detail,
  coarse smooth banks, dark opaque water, sparse rapid hydraulics/VFX,
  incomplete local ecology, and all six external acceptance gates. The layer is
  non-colliding presentation-only gap fill and changes no DEM, bathymetry,
  water geometry, hydraulic state, collision, or raft force.
- Zambezi runnable registry recheck V3 verifies the sixth-river contract again
  after the intervening environment milestones. The versioned Free Run
  manifest, generated player selector, source scenario, native progression
  catalog, shipping cook list, and committed map all resolve
  `zambezi_reference_run` to `/Game/RaftSim/Maps/L_Zambezi` at
  `reference_free_run` tier. `RaftSim.M6.CareerCatalog` passes 1/1 with no
  warnings or errors; `RaftSim.P4.RiverMapLoads.L_Zambezi` passes 1/1, loads
  the map into PIE with the vertical-slice game mode, curved coordinate map,
  live cooked-field water, eight active breaking sites, visible rapid foam,
  and 0 MapCheck errors/warnings. Twenty-one focused Python contracts pass.
  Runnable status is retained; high-resolution terrain, surveyed bathymetry,
  rapid-specific hydraulic, seasonal-flow, guide, rights, photoreal-art, and
  performance acceptance remain open.
- Futaleufú live rapid lace V1 retains a narrowly bounded solver-presentation
  improvement and rejects the broader material rewrite. `L_Terminator` lowers
  only its masked solver-foam focus from `0.12-0.72` to `0.08-0.58`, increasing
  visible rapid vertices from 47 to 53 while the shared calm carrier remains
  byte-identical. The equivalent Chilko bracket was reverted because the
  current cooked Lava Canyon window has zero interior breaking sites and all
  four detected candidates fail at the wet-mask edge; `L_LavaCanyon` keeps its
  conservative defaults pending better rapid data. Filtered generation now
  reuses shared solver presentation assets without resaving them. Build,
  focused source contracts, native water/material/map/render gates, and the
  protected 75-file audit pass. Photoreal water, terrain/ecology, calibrated
  hydraulics, guide/art review, and target-hardware acceptance remain open.
