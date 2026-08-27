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
