# Water Visual Feature Plan — South Fork Full Reach

Goal: every named whitewater feature reads correctly in game, verified one at
a time with in-game screenshots reviewed before moving to the next item.

## Status (2026-08-26 session)

1. Shoreline rectangles — TWO mechanisms fixed. (a) Wet-presence envelope:
   cells collapse/expand geometrically instead of toggling topology. (b) The
   deeper one, found after (a) alone proved insufficient: the visible
   waterline is the surface/terrain INTERSECTION, and per-refresh wave Z was
   sweeping it metres across flat banks. Shallow water (<0.45 m) now blends
   toward a slow per-vertex height reference (waves shoal out physically),
   so the wet edge holds while deep water stays dynamic.
2. Jitter — sources removed in two passes. Pass 1: eased crest/tail lift,
   persistent sites, recentre carry, per-vertex state remap. Pass 2 (after
   reflections still jittered): UV1 per-vertex flow velocity and UV2 wake
   data now interpolate per frame alongside positions/normals/colors —
   they previously stepped at 15 Hz, and UV1 drives the ripple-normal
   advection phase that specular reflections ride — plus the flow field is
   temporally smoothed across refreshes (4/s, teleport guard, remapped on
   recentre). If any residual shimmer remains it is likely TAA/TSR ghosting
   on CPU-updated ProcMesh vertices (no motion vectors) interacting with
   SSR — an engine-level limitation to investigate separately.
3. Tongues — V1 IN (foam suppression + centreline draw-down in an upstream
   cone of each weighted site). Glassy read still limited by noon sky wash.
4. Standing waves — verified present; crest caps now aerate above 4.5 cm of
   coupled displacement so trains read white-over-green.
5. Holes — crest lift, pocket, recirculation all active; visual read pending
   the aeration-contrast pass at a strong site.
6. Pillows — system verified (0.22 m at ≥1.65 m/s with foam collar + sink);
   formula is unit-tested, left untouched. Big Meat Grinder boulder sits in
   slow water, hence no mound there.
7. Eddies — V1 IN (recirculating foam transport behind boulder footprints +
   eddy-line seam foam). Presentation-only; raft physics unchanged.
8. Boils — present (pocket/boil microrelief + WPO pulse); the foam push-out
   ring refinement deferred (formula is unit-tested).
9. Aerated water — volume-scattering aeration already existed in the parent;
   the everywhere-milk came from speed-keyed generation. Foam generation is
   now gated by local surface slope (glassy chutes stay green), and the
   carrier overrides SpeedAerationFraction 0.22 -> 0.05. Verified: green
   water restored between distinct clusters at Meat Grinder.

New tooling: `RaftSim.CaptureSeries <start> <count> <interval> [label]
[pose|shore_left|shore_right|breaking_water*|breaking_water_high] [paddle]
[station=<m>] [lateral=<m>]` — walks the raft to any river station in
handoff-sized hops, then takes a numbered screenshot burst.

## 2026-08-27 follow-up (player-reported)

- "Two water surfaces" + shoreline patches, root-caused via the in-game
  water inventory: the terrain-clipped baseline marks raised bank benches
  wet, and the carrier rendered those slabs floating above the channel
  surface; their wet-mask noise toggled whole slabs. Fixed with a
  connectivity flood-fill from solver-wet channel cells (0.55 m max
  neighbour surface step) culling disconnected islands from presentation.
  Verified before/after: plan_banklslab_before / plan_bankslab_after.
- "Paddling doesn't make it go faster", root-caused with the new throttled
  `RaftSim crew propulsion` log: hull drag returned the raft to water speed
  between strokes, so the +2.2 m/s governor never engaged (260 Ns strokes
  sustained ~+0.15 m/s). Drag belongs to the measured physics contract, so
  feel is tuned via `PaddleStrokeImpulseNs` 260 -> 1150 (sustained ~+0.8,
  peaks +1.2 with natural surge-and-glide) and the governor is now the
  EditAnywhere `MaxPaddleSpeedOverWaterMps` (2.2). P3 crew test green.
- Reflection jitter: UV1 flow velocity + UV2 wake data now interpolate per
  frame and the flow field is smoothed across refreshes (this was the
  ripple-phase stepping); the co-located bank slabs (a shimmer source) are
  gone. If shimmer persists in gameplay, the remaining suspect is temporal
  AA on CPU-updated ProcMesh vertices (no motion vectors) interacting with
  SSR — engine-level, not data-level.
- Turning regression + guide-stroke steering: the paddle-power raise had
  scaled every yaw impulse 4.4x because turns shared PaddleStrokeImpulseNs.
  Yaw now has its own knobs at the pre-regression feel:
  `CrewTurnStrokeImpulseNs` 260 (A/D + HUD pivot commands) and
  `GuideSteerYawImpulseNms` 300 (mouse-button stern sweep). The guide's
  steer is also a real sweep now: `GuideSteerForwardImpulseNs` 170 pulls
  the hull forward with each steering stroke — or backward while the crew
  back-paddles (back-ferry) — through the same speed governor. P3 + P4
  green.

## 2026-08-27 flicker root cause (measured)

Fixed-camera frame bursts with a numeric per-pixel diff finally isolated the
"texture/reflections suddenly changing" flicker. It survived disabling Lumen
reflections and TAA, did not shrink at 0.05 s frame spacing (so not motion),
and the SKY flickered nearly as much as the water — a global post-process
oscillation. Auto eye adaptation was chasing the water's glint churn and
pumping the whole frame (capture cameras), and the gameplay cameras' LOCAL
exposure (bilateral, detail 1.0, tight blur) was doing the same regionally.
Fixes: review capture cameras now use the same fixed photographic exposure
as gameplay (RaftSimCameraPresentation::Configure); local exposure tempered
(detail 0.75, blur blend 0.70, kernel 65 %, highlight 0.86); fine ripple
normal layers toned (FlowRipple 0.13, FoamRipple 0.24). Pool-burst metric:
sky 16.9 -> 2.5, water 22.1 -> 10.6 (remainder is genuine ripple motion).

## 2026-08-27 second flicker pass (elimination complete)

Player still saw reflection flicker after the exposure fix. Systematic
static-camera elimination on the calm pool: Lumen reflections off, SSR off,
volumetric clouds off (sky diff 2.5 -> 0.7, water unchanged), volumetric
fog off, TAA off, real-time sky capture off, ripple/roughness energy cuts —
water metric unchanged by all of them. An amplified per-pixel difference
image then exposed a metric artifact: the "water region" numbers were
dominated by wind-swaying trees, the bobbing raft, and the bank edge inside
the sampled band — open-water pixels are temporally STABLE from a fixed
camera. Conclusion: remaining perceived flicker occurs under CAMERA MOTION
(TAA re-resolving high-frequency water specular each frame). Project AA
switched TAA -> TSR (markedly stabler moving-image history; revert note in
DefaultEngine.ini). WaterRoughness 0.31 + reduced ripple strengths kept —
they soften glint streaks in motion. If flicker persists under TSR, next
lever is the directional light's SourceAngle (softer sun disc = softer
glints), an artistic call.

## 2026-08-27 third pass (near-boat flicker, shore proximity, editor parity)

- Near-boat residual flicker: the paddle-wake ripple overlay (SurfaceMesh
  section 1) was RECREATED via CreateMeshSection every 15 Hz refresh right
  where the guide looks; it now updates in place whenever its cell
  membership is unchanged (LastPaddleWakeRippleSourceCells).
- Shore water keyed to raft proximity: inside the moving solver crop a DRY
  solver verdict overrides the baseline (by design), so shoreline ownership
  flipped as the crop travelled with the raft. Added a per-station crop
  authority feather (~30 m at the crop's ends, one-refresh lag): where the
  solver says dry but the baseline says wet inside the feather, the cell
  adopts the baseline sample and presents at 1-authority, so handover is a
  spatial gradient. Presence envelope slowed (attack 2.2/s, release 1.4/s)
  to average wake-lapping and window-handoff churn at the bank.
- Editor flicker: PIE viewports default to resolution-scaled screen
  percentage (upscaler noise -game never has). DefaultEditor.ini now pins
  realtime editor viewports to Manual 100 %. Remaining editor-side causes
  are per-user settings: disable Editor Preferences -> Performance ->
  "Monitor Editor Performance" (it silently degrades scalability), keep
  Engine Scalability pinned to High/Epic, and wait for the "Compiling
  Shaders (N)" toast to finish before judging water after material changes.

## 2026-08-27 hull glide (direction-split drag)

"Boat speed fixed to water speed; stroke gains vanish instantly." Root
cause: hull drag opposes relative-to-water velocity with a blunt
coefficient floored at 9000 (deliberate — at 1800 an overtaking current
took >10 s to capture the raft and advected froth visibly passed the
boat), which also killed bow-first momentum in ~0.15 s. Drag is now
direction-split in the runtime adapter: the bow-first slicing component of
relative flow drags at ForwardSlicingDragCoefficient (1400, EditAnywhere,
no floor) so a stroke coasts down over a couple of seconds, while reverse/
lateral relative flow keeps the blunt 9000 response — and slicing fades out
entirely above ~2 m/s relative speed, so window-handoff current jumps stay
bluntly captured regardless of hull heading (a spun raft cannot out-glide
the froth). Measured while paddling: sustained 1.9-2.5 m/s in a 1.05 m/s
pool (previously dipping to water speed between every stroke). P1 tank,
P2, P3, P4 all green.

## 2026-08-27 shoreline sub-cell waterline + chop

- Rectangles root cause: all prior smoothing changed WHEN the wet edge
  moved, but the edge itself sat on lattice vertices, so every change moved
  it a whole 1.5 m cell. Boundary vertices now extrapolate to the actual
  depth-zero waterline from the shoreward depth gradient — continuous along
  the bank and through cell turnover (a newly wet cell starts near zero
  reach), ramped by the presence envelope.
- Two same-day corrections from player screenshots: the extension is
  HORIZONTAL only (extending along the bank slope rode the water up the
  shore as a carpet with a visible gap under the lip), and it ramps with
  presence rather than gating on completion.
- Whitewater chop: turbulence WPO raised 0.16 -> 0.30 (flicker-era caution
  no longer needed; foam-gated ±5 cm chop). Real discrete splashing at
  rocks remains a follow-up feature: splash/droplet emitters keyed to
  boulder footprints and flow speed in the water VFX actor.

## 2026-08-28 shoreline corners (topological)

Remaining right-angle notches were topological, not positional: where the
wet band's edge steps one lateral row between adjacent stations, the
corner quad cannot exist (its dry corner fails the presence test), so the
edge rendered an L no matter where the boundary vertices sat. Each
one-row step is now closed with a diagonal stitch triangle between the
two boundary vertices, and the sub-cell reach is computed per station and
box-smoothed along the bank (neighbours within one row of each other)
so depth noise cannot zig-zag the waterline. Multi-row steps (very steep
bank narrowing) remain unstitched — revisit if one shows up in review.

## 2026-08-28 cloud and distant-tree jitter

- Clouds: the volumetric cloud budget was starved (ViewRaySampleMaxCount 8
  vs engine default 768, min 1, component scales 0.5), so per-frame
  jittered sampling made the reconstruction boil. Raised to 64/2 in
  DefaultEngine.ini — sky-band frame diff 2.42 -> 1.10; still a firm perf
  budget with a revert note.
- Sparse distant trees: sub-pixel geometry shimmer under TSR. The
  dedicated anti-flicker period knob measured as a no-op here;
  r.TSR.History.ScreenPercentage=200 cut the treeline band 4.62 -> 3.20.
  Combined config verified: sky 1.03 / trees 3.24 / water unchanged.
  Residual tree motion is genuine wind sway plus remaining sub-pixel
  scatter; if still objectionable, the next lever is authoring-side
  (earlier billboard LODs or no wind on far scatter LODs).

## 2026-08-28 shore sheen ("shiny texture on the shore")

Player report: a broad glossy band riding the bank above the waterline from
the seated guide view. Isolated by elimination with a new low grazing-height
shore camera preset (shore_left_low / shore_right_low, station=/lateral=
walker): hiding the live overlay left it, retracting the carrier's shore
extension left it, hiding static meshes removed it — the band is the
terrain-clipped static water: its build clips at 5 mm depth
(SouthForkMinimumVisibleWaterDepthM), and Single Layer Water renders a
sub-decimetre column with no volume tint at all, so on a gentle bank the
0-10 cm margin is a metres-wide pure mirror over the visible ground,
strongest at grazing incidence (Fresnel -> 1). Fixes, both sides:

- Material (root fix): BuildPhotorealRiverWaterMaterial now lerps roughness
  and specular toward a matte wet-sediment response below ~7 cm of
  solver-authored depth (VC.G; ShoreMarginDepthFloor 0.028, gain 18,
  ShoreMarginRoughness 0.58, ShoreMarginSpecular 0.07), restoring authored
  gloss by ~20 cm. The shallow margin now reads as damp ground / clear
  shallow water with visible bed texture, not chrome. Applies to the static
  water, the V4 transmission parent (regenerated from the fresh source via
  unreal/Scripts/regenerate_water_froth_materials.py after moving the saved
  V4 duplicate aside), and the carrier core (whose G channel is depth/4.0 vs
  the cook's depth/2.5, so its matte onset is ~11 cm — acceptable; tune if
  shallow chutes dull).
- Carrier (conformance guard): the solver bed and rendered Nanite tiles
  disagree by a few cm, which on a gentle bank becomes metres of core film
  hovering above the visible ground. RefreshSurface now line-traces the
  rendered terrain (actors tagged RaftSimFullReachTerrain) under the
  shoreline bands (3 rings, 96 probes/refresh budget, cached per cell and
  carried across recentres), and zeroes presentation wet-presence where the
  rendered column is under 6 cm (kVisualBankFilmMinDepthCm); the bank-reach
  extension also refuses to re-bridge culled ground (reach x0.25). Fail-open
  when no terrain tile is under a cell (boulders, unstreamed tiles).

Verified: grazing before/after crops at station 130 lateral 16 (mirror film
gone, sediment texture continuous into the tint), elevated shore and open
pool unchanged. RaftSim.P2.WaterSurfaceRenders, P2.RiverWindowLoads,
P4.SouthForkFullReachSupportParity green. Pre-existing failures (verified
failing at pushed HEAD a61d758f too, likely from the hull-drag overhaul):
P2.RaftFlipsAndRecovers (raft no longer capsizes under the test's sustained
overwash), P4.SouthForkApproachDraftTelemetry,
P4.TroublemakerApproachDraftTelemetry — flagged as a separate task.

## 2026-08-29 reflective-surface pops (proxy recreation)

Player recording (2.9 s guide-view crop): the whole water surface's fine
reflective detail toggled on for a single game frame and back, twice —
each event a one-frame state B differing ~10 mean-RGB from both
neighbours while A and C differed only ~3 (normal evolution). Signature
of a temporal-history reset, not exposure or geometry.

Cause (proven by A/B): the Single Layer Water core rebuilt its ONE
26k-vertex mesh section with CreateMeshSection whenever shoreline
membership changed. A recreated section is a new render proxy whose
first frame carries no motion history, so TSR renders one raw sharp
frame across the section's entire screen area. Membership churn (bank
lapping, crop-feather sweep, film-cull flicker) recreated it up to 6
times a second. A benchmark frame-dump A/B (raftsim.FreezeCoreTopology,
kept as a probe cvar) zeroed both the one-frame-anomaly count (24 -> 0
in 14 s) and the water band's diff tail (p90 5.7 -> 2.4).

Fix, in layers (RaftSimWaterSurfaceActor):
- Split the core into two sections sharing vertices and material:
  a stable INTERIOR (section 0) and a thin bank BOUNDARY strip
  (section 1). Only the boundary is allowed to churn.
- Interior membership keys on hydraulic depth (VC.G), not presence —
  every presence threshold sweeps with the raft's crop feather — with
  double hysteresis: enter >= ~0.5 m held for ~2 s, exit < ~0.3 m held
  for ~2 s, so rapid waves can neither admit nor evict. The partition
  itself only moves when the grid recentres (per-vertex dwell completions
  otherwise re-partition every refresh while a streamed edge settles),
  and a recentre already recreates everything, so membership updates add
  no extra invalidations.
- Boundary adoption throttled to ~1 Hz (15-refresh hold, forced on
  recentre/boot): the strip's recreation batches instead of firing per
  refresh; the lapping edge still tracks inside the presence envelope's
  attack time.
- Film cull got enter/exit hysteresis (6 cm / 9 cm) — the single
  threshold flickered with wave motion and was itself a churn source.
- Diagnostics kept behind raftsim.LogWaterRenderStateEvents: every
  section recreation / visibility flip / recentre logs frame + time for
  correlating against -benchmark -dumpmovie frame diffs.

Validated on the same benchmark profile (30 fps dump, paddling from
launch): interior recreations 0 (was 87), boundary batches 13/15 s,
one-frame anomalies 0 at the strictest threshold, water-band p90 2.58
(baseline 5.72) — matching the freeze-everything probe while shoreline
behaviour stays live. Shoreline stills unchanged (no seam between
sections); RaftSim.P2 suite + P4.SouthForkFullReachSupportParity green.

Follow-up (same day, player screenshots + 7.2 s recording): the 1 Hz
boundary throttle traded per-refresh strip flashes for once-per-second
BATCHED shoreline jumps — the recording's diff spikes sat at 1.0 s
intervals exactly — and batched admissions landed as rectangular blocks.
Superseded by a frozen waterline band: the boundary section now emits
every cell within 4 rings of the waterline captured at band-rebuild time
(recentres, band-edge escapes), and DRY cells render collapsed onto the
finished waterline vertex of their column (directed pile pass; interior
presence gaps collapse onto their nearest wet row so islands are not
skinned). Wet/dry churn therefore moves vertices — per-frame smooth
through the interpolation — and never touches an index list; the
adoption throttle is gone; the diagonal stitch triangles are gone too
(the collapsed dry quads ARE the corner fill, which also kills the
remaining right-angle notches). Benchmark: ZERO core section events of
any kind in 15 s (no creates, no band rebuilds), water-band median 1.95
/ p90 2.44 / max 3.14 — byte-identical to the freeze-probe ideal.

Static/live shoreline unification: the terrain-clipped static water kept
water to 5 mm depth, so its (de-glossed but still distinct) margin ran
metres past the carrier's ~6 cm rendered-depth cull line and the two
waterline contours read as different edges ("where the blue surface and
where the shiny surface intersect the shore are different").
SouthForkMinimumVisibleWaterDepthM raised 0.005 -> 0.06 and the static
water meshes regenerated in place via the new water-only rebuild flag
(-RaftSimRebuildSouthForkWaterMeshes overrides every reuse umbrella;
terrain, far field, and materials untouched). All 39 band meshes
regenerated; shoreline stills show one edge.

Hardening from the post-rebuild suite run: every in-place mesh-section
update in the water actor now verifies the section's CURRENT vertex
count and recreates on mismatch (a cleared section keeps its entry with
zero vertices) — this also fixed a latent ripple-section bug that
updated a full-grid section with empty arrays whenever a wake had no
visible triangles. And the SupportParity test learned the second half of
the suite-order leak: AutomationOpenMap is a no-op when the map is
already loaded, so a preceding approach ride hands this test the SAME
world with its raft still mid-river; the test now settles the raft onto
the nearest wet centreline station before its readiness gate. Full
RaftSim.P2+P3+P4: 15/15, zero procedural-mesh error lines.

## 2026-08-28 pre-existing test failures fixed (flip + approach telemetry)

Root causes were three unrelated bugs, none of them the hull drag:

- Capsize infeasibility: the self-bailer retention retune (6a0463f8; per-
  segment cap 0.05 -> 0.035 m^3) capped the whole-side flood moment at
  ~1370 Nm against the unchanged 1800 Nm righting threshold, so the D3
  flip-risk latch could never fire at any flow — in the test or in gameplay.
  The missing physics is the overwashing current itself: EvaluateOverwashFlipD3
  now adds an overtopped-face dynamic-pressure side load
  (q = rho v^2/2 over the overtopped strip, one pressure-scaled tube-radius
  lever), accumulated only while a face is genuinely overtopped, as the
  production coupling term DynamicPressureRollLeverM (default 0 keeps every
  D6 fixture and the Python reference identical). Drifting with the current
  contributes nothing (near-zero relative speed); a buried tube in fast
  relative flow levers over. Flip-test capsize log now reads: retained
  1373 Nm + dynamic 9615 Nm vs threshold 1800 -> flips, 5 swimmers, re-flip
  recovers.
- ProcMesh error spam ("different number of vertices [Previous: 0, New:
  26065]", every frame in map-load/telemetry runs): ClearMeshSection keeps
  the section entry alive with zero vertices, and the volume-core dry-clear
  branch left the per-frame interpolation armed, whose guard only
  null-checked the section. The clear now deactivates interpolation and the
  guard also requires the section's current vertex count to match.
- Moving-window wedge: a zero-overlap handoff (raft teleported/checkpointed
  far away) was rejected with an Error and kept the stale window, wedging it
  permanently since every retry was equally non-overlapping. The adapter now
  reboots the window cold at the new station with a Warning; continuous
  descents always overlap, so gameplay still never resets silently.
- Approach-telemetry transit hardening (test-side): wet probes scan a small
  lateral fan (the wet channel leaves the centreline by station ~60 on
  Troublemaker's approach), and after 20 consecutive dry holds the seek
  phase blind-creeps 8 m via the coordinate map — safe now that the window
  reboots instead of wedging (previously it deadlocked at the ~6.9 km
  source-grid boundary seeking Troublemaker at 8050 m).

Two more latent issues surfaced by full-suite runs, both fixed:

- SupportParity order-dependence: the water adapter is a game-instance
  subsystem, so it outlives AutomationOpenMap; running after a far-river
  ride left the moving window kilometres away and the parity asserts
  sampled dry before the fresh map's streaming actor reconfigured. The
  assert command now holds (bounded 12 s) until the raft's support sample
  answers wet.
- Flip-test timing: the mid-flip assert at 0.50 s after forced overwash
  landed exactly on its 20 deg bound (latch 0.35 s + 0.85 s smoothstep
  transition; measured 18.0-21.1 deg across runs). Wait extended to
  0.65 s (~55 deg at assert); three consecutive green runs.

All three tests green; full RaftSim.P2+P3+P4 15/15 with zero
procedural-mesh or window-handoff error lines; SouthFork telemetry rides
Troublemaker proper (drop 1.13 m at station 8170, draft spread ~16-24 cm
over 121 samples). The physics/ Python reference suite could not run
locally (no python/uv on this machine) but is unchanged by construction:
the D3 reference path is bit-identical with the new parameter defaulted
off, and the Python model itself was not touched.

## Repo audit (2026-08-27)

- .git 9.8 GB, of which .git/lfs cache 8.0 GB; pack only 1.79 GiB.
  `git lfs prune` would reclaim ~811 MB (1543 stale objects) — left for the
  user to run (destructive-class command).
- Working tree: Content 5.1 GB (uassets/umaps in LFS), physics 1.5 GB,
  docs/environment-captures 1.4 GB (review evidence — keep).
- Disk-only regenerables (gitignored, deletable anytime): Intermediate
  2.7 GB, Saved 460 MB, DerivedDataCache.
- Cleaned this session: orphan M_RaftSim_SouthForkRaftTransmissionWaterV3
  (unreferenced), tracked tmp/ scratch (4 files), 130+ session screenshots
  (483 -> 96 MB in Saved/Screenshots).

New issues found (not yet addressed):
- Troublemaker (station 8369) and presumably everything downstream sits in
  dense height fog — the fog falloff swallows the river as it loses
  elevation. Blocks captures/review of the lower reach.
- Hard tan polygon edges around boulder sink cutouts read as cardboard.
- Small floating shard artifacts (bank-clip triangles?) near shorelines in
  the elevated Meat Grinder views.
- Noon sky reflection washes the whole surface pale versus the darker
  gallery-reference lighting; consider capture-time sun presets (CaptureRaft
  already accepts sunpitch=/sunyaw= diagnostics).

## Verification loop (applies to every item)

1. Build `SmokeEmIfYouGotEmEditor Win64 Development`.
2. Launch `-game` on `/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach`
   (real RHI, windowed 1920x1080) and run
   `RaftSim.CaptureAfter <seconds> <label> [x y z pitch yaw |
   breaking_water | breaking_water_side | breaking_water_opposite]`,
   or `RaftSim.CaptureRaft` for the over-the-shoulder paddle-in framing.
3. Save shots as
   `docs/environment-captures/south_fork_full_reach/photographic/<feature>_<yyyymmdd>.png`
   and post them in the session for review. Before/after pairs at the same
   camera pose whenever a feature changes existing presentation.
4. A feature is done only when the reviewed screenshot reads correctly, the
   focused water automation stays green
   (`RaftSim.P2.WaterSurfaceRenders`, `RaftSim.P4.SouthForkFullReachSupportParity`,
   `RaftSim.M8.BRuntimeDataAndMaterials`), and raft rigid support stays
   paired with whatever geometry changed (adapter mirrors).

Named verification sites: Troublemaker (hole + entry tongue), Meat Grinder
(boulder garden: pillows, wakes), Satan's Cesspool (wave train), Chili Bar
hole (first drop), plus any calm pool for shoreline/eddy work.

## Execution order

Bugs first — they contaminate every screenshot taken after them — then
geometry from the largest shapes down, then the aerated-water look that sits
on top of all of it.

### 1. BUG — shoreline water appears/disappears in rectangular chunks

Symptom: along the banks, water pops in and out in cell-shaped rectangles.
Suspects, most likely first:
- Wet/dry cell membership (`LiveSolverWetVertexMask`, 1.5 m cells) flapping
  at the 15 Hz refresh where bank depth hovers at the wet threshold — the
  admitted/removed triangles are exactly rectangular. The interpolated
  topology path fades admitted triangles in, but any refresh that falls into
  the hard-swap branch (recentre fallback, size change) installs them at
  full alpha in one frame.
- Station/lateral edge feather (`ComputeStationEdgeCoverage` /
  `ComputeLateralWetCoverage`) recomputed against a moved window while the
  vertex colors it feeds are mid-interpolation.
- World Partition streaming of authored shoreline cells: the streaming actor
  hides band-presentation actors on level-add, but its safety sweep only
  re-runs every 2 s (`ApplyStaticFlowBandVisibility`), so a straggler actor
  can render for up to 2 s before being hidden.
Fix approach: reproduce near a bank, identify which of the three it is
(toggle candidates via cvars/logging), then either add hysteresis to wet
membership (a cell must be wet/dry N refreshes before switching), always
route admitted bank triangles through the faded path, or hide streamed
actors synchronously at spawn. Verify: 60 s shoreline soak, screenshots plus
absence of pops.

### 2. BUG — occasional surface jitter

What remains after the persistent-site and recentre-carry fixes:
- Per-cell breaking crest lift / tail train (`Vertices[...] += LiftCm`) is
  driven by raw per-refresh Froude detection with no temporal smoothing —
  cells at the Fr ≈ 0.94/1.12 thresholds toggle their lift with only the
  67 ms carrier blend to soften them, and the detected front hops whole
  1.5 m cells.
- Per-vertex temporal state (`SmoothedRapidFoamCoverage`, boulder-wake
  smoothing if any) is indexed by vertex and NOT remapped when the grid
  recentres — after a recentre the smoothing history applies to the wrong
  river cells.
- UV1/UV2 (`FlowVelocityMetersPerSecond`, `BoatWakePresentationData`) and
  `Tangents` step to fresh values at 15 Hz instead of interpolating —
  visible through the flow-normal response.
Fix approach: smooth the crest-lift field per river station (same style as
the persistent sites), remap or reset per-vertex temporal state on
recentre, interpolate UV1/UV2 alongside positions. Verify: frame-series
captures (CaptureAfter at 0.1 s spacing) show no frame-to-frame pops; PIE
soak at a rapid.

### 3. Tongues (rapid-entry V)

Smooth, glassy, dark convergent V where the pool accelerates into a rapid.
Today: nothing explicit — only whatever the solver surface produces.
To build: detect convergent accelerating flow upstream of breaking sites
(Froude rising toward ~1, lateral velocity convergence); inside the tongue,
lower the center line slightly with converging lateral slopes, suppress the
turbulence WPO, ripple normals, and foam (aeration ≈ 0 — tongues are the
least aerated water on the river), and let the existing specular/reflection
carry the glassy read. Anchor it upstream of the persistent breaking sites
so it inherits their eased identity. Verify: Troublemaker entry from the
guide-eye pose — dark smooth V framed by white shoulders.

### 4. Standing waves

Today: `ComputeCoupledStandingWave` plus the decaying tail train behind each
accepted jump; render and rigid support share the field.
To do: verify wavelength/steepness/count read correctly at speed, crests
carry extra aeration at their tops (feed wave crest phase into the foam
source), and the wave train amplitude decays believably. Verify: Satan's
Cesspool wave train, side and guide-eye captures.

### 5. Hydraulic holes

Today: breaking-site detection → crest lift, plunge pocket, downstream boil,
recirculating foam velocity, persistent-site easing (this session).
To do: confirm the pocket still reads as a real depression after the
presentation-weight easing (deepen/steepen if the eased handoff softened
it), keep the backpile crest leaning upstream over the pocket, and make the
pile the most aerated water on the river (ties into item 9). Verify:
`breaking_water` camera presets at Troublemaker and Chili Bar hole.

### 6. Pillows

Today: `ComputeCoupledBoulderPillowDisplacementMeters` + boulder wake
displacement/foam, coupled into rigid support.
To do: verify the upstream mound hugs exposed boulders at the right
amplitude for boulder size and current speed, add the thin foam collar at
the pillow's upstream seam, and keep the downstream face slick (aeration
low) before the wake foam begins. Verify: Meat Grinder boulder garden
close-ups.

### 7. Eddies

Today: effectively nothing (name appears only in a dev-tank label).
Largest new feature. Three parts:
- Flow: recirculation zones behind obstructions and bank points. First check
  whether the cooked shallow-water fields already contain reverse flow in
  those pockets; if not, author bounded analytic eddy velocity patches
  (behind boulders and bank projections, scaled by current) and blend them
  into the sampled field so foam advection, raft drift, and presentation all
  see the same recirculation.
- Presentation: eddy line as a visible shear seam (ragged foam string plus a
  small surface height step), flatter and slightly raised pool inside the
  eddy, foam naturally collecting and slowly circling (falls out of the
  foam advection once the velocity field recirculates).
- Verify: eddy behind a named boulder/point — foam ring circulating in the
  screenshot pair a few seconds apart, raft catchable in the eddy.

### 8. Boils

Today: downstream boil microrelief at the top-3 sites plus the turbulence
WPO boil term and its slow pulse.
To do: verify the mushrooming dome read (rising center, radial spread),
push foam outward from boil centers so the upwelling core reads as clean
water ringed by aeration (currently foam sits uniformly), and scale boil
population/amplitude with site intensity. Verify: below Troublemaker's
pile, top-down and grazing captures.

### 9. Aerated water rendering (the "foam" that is not foam)

The current-advected ragged clusters move correctly but read as a white
surface decal. They should read as aerated water — air entrained in the
water column:
- Drive shading from an aeration quantity (vertex foam channel + crest/boil
  injection): raise scattering and desaturate toward white with aeration,
  fade translucency/depth color (aerated water hides the bottom), lift
  roughness, soften the specular — instead of compositing a white texture.
- Keep the torn V4 web/lace masks as the aeration's spatial structure, but
  let them modulate aeration density, not albedo directly, so cluster edges
  are milky gradients rather than texture cuts.
- Depth cue: aeration whitens most at the surface and fades over the first
  ~0.5 m of optical depth.
- This is a V4 parent / photoreal-builder change; the same aeration value
  should feed the audio/VFX layers that already key off foam.
Verify: close-up of a pile and of drift clusters on green water — no crisp
decal edges, milky volume, correct read at both grazing and top-down angles.

## Standing constraints

- One visible carrier: every feature is carved into the single Single Layer
  Water surface + its material; no second sheets (the retired lace/overlay
  meshes stay retired on South Fork).
- Rigid support parity: any geometric feature the raft can touch must be
  mirrored into the adapter (as standing waves, jumps, pillows already are).
- All motion ties to the shared current integral / wave clock — nothing may
  pan independently of the drifting raft.
- 15 Hz refresh + per-frame interpolation architecture stays; features must
  be continuous across refreshes, recentres, and window handoffs.
