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

## 2026-09-02 round 6: the forearm shape, and the end of visibility races

"A strange black shape pops up out of the fore arm when the crew is
paddling" (player F9 recording): the shoulder-sleeve capsule anchors
to the PROCEDURAL elbow, but the 9 cm elbow-drop clamp existed only
in the CC0 adapter — at power phases the two solutions diverged ~7 cm
and the sleeve burst out of the rendered forearm. The clamp now
applies identically in ApplyPose, so gear and body solve one elbow.

Root of the whole bug family: SetProceduralVisualVisible ran once at
spawn with CC0 readiness evaluated at that moment; parts in the
gap-fill list stayed visible (or hidden) on load-order luck — the
empty helmets and the stroke-time sleeve burst were both instances.
Tick now re-applies the pass whenever readiness flips.

M5 fallout fixed: the exclusive-ownership checker listed Neck as
redundant anatomy, but the CC0 body renders NO visible skin between
collar and chin — the neck band is production dressing (2026-08-30
design) and is no longer counted against ownership.

## 2026-09-02 round 5: blade winding truth, heads in helmets

"The paddles are still black" (fourth report) — final root cause, and
it was the MESH all along: BuildCommercialPaddleBladeMesh's outline
traverses counter-clockwise, so both cap faces wound {centre,
current, next} DISAGREE with their stored +/-Y normals. From the
guide's high-behind seat every render combination (single-sided cull,
two-sided, TwoSidedSign flip) resolves the face-up resting blade to a
down-facing normal: black slab from above, bright yellow from the
side — which is why side captures kept "disproving" the report. Caps
now wind {centre, next, current}; verified yellow from the guide
angle. Material stays two-sided for robustness.

"The crew don't have heads — there should be a skin tone head in the
helmet": two stacked causes. The round-4 vest lift closed the last
visible neck sliver (softened to +0.5 cm / +2% Z), and the skin neck
band lived in the CC0-not-ready gap-fill list, so its visibility
depended on load timing. The neck is now in the always-visible
production overlay list and extends higher into the helmet shell.
Verified: skin necks under all four helmets from the guide seat.

## 2026-09-02 round 4: tonal boots, vest layering, scheduled drag floor

Third repeats of three reports forced different tools:
- "Boots are still cylinders": the mesh was never the remaining
  problem — boot rubber (0.005) and upper tint (0.018) rendered the
  same value as the wetsuit shin, so leg and boot fused into one
  column. The production boot materials brightened to charcoal
  (rubber 0.034, upper tint 0.048; python regen) and the procedural
  fallback boot to match. Footwear finally separates.
- "Shoulders still covered with black material": shoulders 73 -> 71,
  elbow clamp 12 -> 9, and the PFD shell lifts 1.2 cm with +5% Z so
  the vest wins the layering. RESIDUAL: the wetsuit's authored
  scalloped neckline still shows at the vest top; the real fix is a
  Blender trim of the CC0 wetsuit source. Bone-scaling neck_01 or
  spine_03 to shrink it is OFF THE TABLE - component-space scales
  there crush every vertex weighted downstream (tried, catastrophic,
  reverted same day).
- "The boat still drifts sideways" vs the earlier "should be pushed
  to the outside of the turn": resolved with a water-speed-scheduled
  viscous floor - SlowWaterDragReferenceMps (1.2) in still water
  blending to LowSpeedDragReferenceMps (0.35) by ~2 m/s of current.
  Pools track the channel hands-off; fast bends keep the outside
  carry. Fixtures pinning the legacy 1.5 get a constant floor via the
  max-of-both-ends rule. Verified: 160 s hands-off from the put-in
  with zero ground contacts. RESIDUAL FINDING: the tail-end lag
  toward the left grows near the bend approach IDENTICALLY across
  floor values 0.25/0.55/scheduled - it is not drag slip but the
  buoyant hull sliding down the water surface's lateral slope (the
  same gravity term that makes the raft outrun slow water
  downstream). If the slow left set still reads wrong in play, the
  next investigation is lateral surface-gradient telemetry, not more
  drag tuning.

Also: the V4 regen validator broke silently after EffectiveDepthMask
rewired the depth blends - "exposed only 0 of the two required depth
colour/opacity blends" meant NO V4 was created, the carrier fell back
to V2, the MI ran orphaned, and missing-parent churn under VRAM
exhaustion cascaded into black shader-fallback materials (the black
paddle saga's true root). The validator now traces the shared depth
alpha through the effective-mask chain. ALWAYS Test-Path V4 after a
delete+regen.

## 2026-09-02 D-rings bonded to the tube

"The D rings aren't attached to the boat" (run-complete close-up).
The rings were bare metal ovals standing VERTICALLY, tangent-kissing
the curving tube flank at one point — centres 2-3 cm off the surface,
no mounting hardware, so up close they floated. Each ring is now
built in the tube's tangent frame at the upper-outer shoulder (lying
flat against the fabric) over a bonded rubber mounting patch, both
riding the same hull deformation field as the tube. M5+P2 8/8 (ring
topology, four-ring count, and fold-coupling asserts unchanged).

## 2026-09-02 round 3: black blades, seated contact, splayed boots, drift trim

"The paddles are black now": the two-sided blade material was the
bug, not the fix — the blade mesh's top shell winds with downward
normals, so single-sided culling had always shown the upward-lit
underside faces; TwoSided painted the unlit black backs over them.
Reverted to single-sided; the near-saturated yellow stays.

"The crew butts aren't sitting on the boat": the seat-height formula
assumes the procedural pelvis ellipsoid's depth below the hip centre,
but the rendered CC0 glute — pulled forward-up by the knees-up seated
fold — does not reach that low. SeatContactSinkCm 1.5 -> 4.0 presses
every paddler onto the tube.

"The shoes are still cylinders": the boot mesh (Blender-built) is
boot-shaped, but dead-ahead toes hid its whole length behind the round
cuff from the guide seat. Seated feet now splay outward 16 degrees per
side, showing heel and toe.

"While drifting the boat moves sideways into the left shore": drift
telemetry showed the 0.25 blunt floor overshooting — the raft lagged
the turning water by up to 4.7 degrees on a gentle pool reach (the
"outside carry" running away) and beached itself in minutes.
LowSpeedDragReferenceMps 0.25 -> 0.55: bends keep a visible outside
set, hands-off pool drift stays in the channel.

## 2026-09-02 positive-delta water, one-stroke stops, crew polish round 2

First F9 recordings from the player immediately paid off. At km 0.92
the probe read live +0.51 m OVER the cooked band (the release wave) —
the level sink was designed for negative mornings and RAISED the whole
sheet uniformly: its shoreline rim hung in mid-air over the beach
(white polygon shards), rock cutout rims floated as gap rings, and
the raised sheet shaded itself with COOKED depth (VC.G says ankle
deep) so it rendered as a pale membrane over the flooded bar ("water
texture is missing"). Two-part fix, both gated by
ApplyLiveLevelShoreClip so the carrier is untouched: (1) raising now
tapers to zero at the cooked shoreline (scaled by cooked depth), so
the sheet tilts from its pinned bank edge up to the live level —
sinking stays full-strength since buried edges are invisible; (2) an
EffectiveDepthMask (cooked + delta) now drives body colour, opacity,
and the shore de-gloss, so raised water shades as the depth it really
is. Station 920 verification: spray collar on the rock, foamy rapid
water, the flooded bar reads as shallows. V4 regen for this REQUIRES
the delete-and-recreate route — the patcher's Desc probe will not
upgrade an existing sink node.

"A single back paddle stroke suddenly stopped the boat": the stroke
impulse (1150 Ns/paddler) is sized for the governor-faded FORWARD
feel; backward it met no brake until sternway built, and on the 220 kg
chrono body one crew stroke is a ~10 m/s delta. The old weld-stiff
drag floor masked it; the bend-carry fix exposed it. Back strokes now
cap at 0.85 m/s of speed change per full stroke, and the Stop brake
additionally never exceeds the momentum that remains (an uncapped
brake now visibly REVERSED a slow raft).

Crew round 2 (from the same recordings): shoulders 76 -> 73 so the
wetsuit's scalloped neckline tucks to the vest top (elbow-drop clamp
tightened 14 -> 12); boots widened 0.88/0.92 -> 0.98/1.04 so heel and
toe break the shin's tube silhouette (sole-down caps track); blade
colour raised to near-saturated Carlisle yellow and made two-sided
(0.68/0.44 rendered amber-olive, and back faces went black).

## 2026-09-02 shoulder yoke, sunlit blades, debug screen recorder

"What is the black material sticking out the top of the life jacket?
It seems much to high to be shoulders." A show-SkeletalMeshes A/B
proved it was the CC0 body's own deltoid/trapezius skin: swinging the
upper-arm bones steeply down to the new lap-resting hands rolls the
shoulder skin up beside the neck into a black yoke reaching the chin.
The CC0 adapter now caps the elbow's drop below the shoulder at 14 cm
— the forearm still reaches the true wrist, so hands stay on the
shaft and the arm simply bends more. All four crew read as rounded
wetsuit shoulders at the vest line.

"Their paddles look like they are in shade" — at rest the blade face
derived from ForwardVector, which stands the lap-rest blade
edge-up like a knife: a 2 cm sliver catching no skylight. The face
axis is now action-aware (up at SeatedIdle, forward for strokes);
resting blades lie flat and read bright Carlisle yellow.

Debug screen recorder (new): F9 (or RaftSim.ToggleRecording
[delaySeconds]) toggles an H.264 MP4 capture of the game viewport,
UI included — FFrameGrabber into a Windows Media Foundation sink
writer at 30 fps / 12 Mbps, clips in Saved/VideoCaptures (override
with raftsim.RecordingDir). Verified headless: 17.4 s / 521-frame
clip, clean finalize on game exit. PIE is not supported (standalone
game viewport only).

Also: the boots sole-down checker's Z-scale bound tracks the taller
0.85 cuff (was pinned to the 0.68 era, failing M5.RuntimeRescueLoop).

## 2026-09-02 sink the cooked sheet, bend carry, ankle taper

"The glossy surface and the water surface are still separate ... the
glossy surface still runs over the shore." The pixel-side shore clip
only retired the tile margin below the live waterline; the REST of the
cooked sheet still rendered at its cooked height — a full glossy
surface floating 0.36-0.66 m (measured) above the live carrier,
meeting the bank higher up. Terminal fix: a live-level WPO sink
appended to the V4 parent (Desc-probed like the turbulence blocks) —
the whole cooked sheet moves down by the published
RaftSimLiveWaterLevelDeltaM (clamped +/-1.5 m) wherever
ApplyLiveLevelShoreClip=1 (tiles only). The sheet then LIVES at the
live level: its cooked shoreline edge sinks under the bank and the
terrain depth-test draws today's waterline. Verified at station 280
(delta -0.66): one surface, one waterline. No V4 delete needed — the
patcher appends to the existing asset.

"The boat should be pushed to the outside of the turn by the water but
isn't." Drift telemetry through a 4-degree reach: raft_dir tracked
water_dir to within 0.1 DEGREE at every sample — the hull was
velocity-welded to the streamline. Cause: LowSpeedDragReferenceMps 1.5
under the blunt 9000 coefficient gives a ~0.1 s lateral decay; outward
slip in a bend computes to centimetres. The blunt floor now matches
the slicing term's 0.25 (the >=1.5 m/s capture regime that keeps
froth behind the boat is numerically unchanged): rerun shows the raft
lagging the turning water by 0.2-0.3 degrees on the same gentle reach
— real momentum carry that compounds into an outside set through the
sharp arcs. Test fixtures that pin 1.5 keep their own value.

"Their ankles look like cylindars": zero-scaled foot bones collapsed
every ankle-blend vertex onto one point (calf chopped into a
featureless tube) and the 0.68-height boot cuff from the
short-shin era read as a squat ring. Foot bones now keep a third of
their scale (a tapering ankle cone that hides inside the cuff) and the
cuff rises to 0.85 so the shin enters from clearly above.

## 2026-09-01 live-level shore clip, palm sense, hard beach gate

"The shiny water texture runs over the left bank ... the shiny surface
and the water coloured surface meet the bank at different places." The
static terrain-clipped tiles are cooked at ONE flow band
(median_runnable) while the release schedule moves the live level
through the day — measured live-minus-cooked at the report site
(station 380, morning): -0.36 m. The cooked sheet therefore kept
rendering metres up the bank past the solver waterline as a glossy
apron (the "shiny" surface), while the carrier's colored water ended
at the true line. Fix: the runtime samples live vs baseline level at
the boat each frame and publishes the smoothed delta through the
foam-occlusion MPC (RaftSimLiveWaterLevelDeltaM, also in the pillow
probe log as level_delta_m); the tile material recomputes each pixel's
cooked depth (VC.G x 2.5) against today's level and retires everything
above it — opacity, specular, body colour, drift emissive to zero,
roughness to matte — over a 6 cm feather. Tiles enable it via the MI
(ApplyLiveLevelShoreClip=1); the carrier follows the solver by
construction and keeps it off. Verified capture at station 380: one
waterline, no apron. V4 regenerated (graph change: delete + recreate).

"The hands look twisted" (round 2): the first mirror fix chose the
back-of-hand sense for BOTH hands — every resting hand lay palm-up
under the shaft. Cross orders swapped to the empirically verified palm
sense; close-up confirms knuckles-up palm-down grips both sides.

"Paddling on dry ground still moves the boat": the first gate only
CAPPED thrust when grounded (0.35), so a beached raft whose blade tips
reached nearby water still crawled. A grounded hull (3+ support
points) whose CENTRE sample is dry now gets zero purchase; the reduced
bite survives only when the hull itself still stands in water, which
keeps working off a mid-river gravel touch possible.

## 2026-09-01 pillow round 3: the aerated collar (why "no pillow" persisted)

"Theres still no pillow on the rock" (km 0.87, glassy pool). The probe
proved the field was working — 11 footprints in the window, ring speed
~3 m/s upstream, 19 cm max pillow — and the catalog covers the site
(radius-1.65 footprint at station 882). The real gap: the pillow was
CLEAR-WATER GEOMETRY ONLY. A sub-20 cm smooth transparent mound is
invisible at distance on a calm surface, and with the clear-water
optics it got even harder to see. What a player recognises as a pillow
is the aerated collar where climbing water breaks white — and the
pillow fed the boulder foam channel nothing (only the downstream wake
term wrote foam, which is why rocks had white tails but never a white
bow cushion). The pillow ring now also writes boulder wake foam,
speed-gated: PillowRingT * (0.12 + 0.75 * SmoothStep(0.35, 1.60,
speed)) — a faint lap line on pool rocks, a bright cushion where fast
water actually aerates.

## 2026-09-01 crew polish: rest grips untwisted, seated fold fixed

"The hands on the t-grip look twisted" — the resting hands anchored
exactly on the T-grip point, which selects the crossbar-axis precision
grip solve; with the shaft laid across the lap the crossbar points
fore-aft and the relaxed wrist wrenched 90 degrees around it. Resting
hands now drape over the SHAFT (off the 2 cm T-grip window), knuckles
along it, palms on top.

"The feet seem to be coming out of the shins" — measurement first: the
CC0 source rig's thigh/calf are 41/46 cm (new one-shot log), but leg
skin SQUASHES between explicitly placed bone heads (the foot bone is
pinned at the pose target and scaled to zero), so rig lengths are not
the constraint. The real cause: a 10 cm knee-to-foot drop inside a
~12 cm production boot cuff — the boot swallowed the whole shin and
read as a foot sprouting mid-shin. The seated fold is now anatomical
for a low tube: knees drawn up (Z 34), heels pulled back under them,
soles planted on the interior floor (Z 6) — a ~28 cm shin drop that
enters the cuff from clearly above. M5+P2+P3 green.

## 2026-08-31 resting paddles + mirrored paddle grips

"When they aren't paddling the paddles should be out of the water in a
neutral position with the shaft resting on the thigh." SeatedIdle had
no pose case of its own, so idle crew held the STROKE-READY base
paddle: T-grip high at the chest, blade planted in the water. A
dedicated SeatedIdle case now lays the shaft across the tops of the
thighs just behind the knees (forward of the PFD belly so it cannot
thread the torso), T-grip inboard, blade hanging outboard just above
the tube, hands loosely on the shaft in the lap. The stroke/turn/brace
cases still articulate from the untouched catch-ready base. Verified
from a side capture: all blades level at lap height, out of the water.

"The hand gripping the paddle shaft seems to be bending the wrong way
like it is upside down or backwards" (player recording). The CC0 grip
solver built its reference hand basis with one cross-product order for
BOTH hands: index-to-pinky x hand-to-middle is the PALM normal on the
right hand but the BACK of the hand on the mirrored left, so the left
grip solved 180 degrees flipped about the shaft — palm away, wrist
bent backwards. Its knuckle axis was also unmirrored, which put the
left grip thumb-down on a shared shaft axis. Both are now
side-mirrored (palm-normal basis per hand, knuckle line negated for
the left), and the T-grip hand caps the grip from above instead of
approaching underhand (the palm-approach ternary aimed the top-hand
palm at the shoulder — an upside-down underhand hold).

## 2026-08-31 seated legs inboard (feet on the raft floor)

"The crew's legs should be in the boat with their feet on the floor of
the boat" (guide-POV screenshot: every paddler's lower legs folded
along the TOP of their tube). Root cause: the pose library's leg
targets were side-blind — feet 34 cm straight ahead of the seat at
lateral +/-15 — and the seat origin rides the tube crest at raft
|Y| 62, so the feet landed at raft |Y| 47-77: on the tube, never over
the interior. The 2026-08-30 "tucked brace" only moved them along the
tube. The base pose now aims the legs INBOARD using the seat side the
library already receives: knees at |Y|~35-57 crossing the tube's
inner shoulder, feet at |Y|~22-40 planted at the measured interior
surface height. Measured, not guessed: AttachAvatarToSeat now probes
the raft visual mesh at the foot window with the same scanner the
seat height uses and logs floor_top/foot_local_z (interior
cushion/floor tops ~raft 21 vs tube top ~27 at the stern pair).
High-side lateral shifts and the M5 relative-pose assertions are
unaffected (they compare against the same base). Verified over-stern
capture: knees drape inboard, lower legs inside the hull, no
tube-folded legs, glutes clean. M5 5/5 + P2 + P3 green.

## 2026-08-31 beached paddling gate + clear-water optics

"Paddling on dry land should be impossible, the boat should simply be
too heavy to move" (recording of a beached raft crawling under
AllForward). Every stroke impulse — crew commands and the guide's
direct stroke path — is now scaled by GetPaddleWaterPurchase(): the
two blade stations (+/-165 cm on the right vector) each contribute 0.5
when the water sample there is wet and >10 cm deep, and a raft
grounded on 3+ support points caps purchase at 0.35 even if a blade
finds a puddle. Fully dry = zero impulse; the sim never fakes it with
extra mass. Afloat, both blades reach water and purchase is exactly
1.0, so on-water behaviour (and every propulsion test fixture) is
numerically unchanged.

"River water should be clear and transparent, the aerated foamy parts
should contrast with the clear pools where the colour of the rocks
beneath comes through" (player reference photo of the real South
Fork). The calibration was doing the opposite: RiverbedColorScale
crushed the behind-water bed to ~20% of its light, opacity 0.76-0.82
occluded the rest, and the carrier painted a bright teal body colour
(LiveShallowSurfaceColor 0.10/0.23/0.24) on top — the milk in the
recording. New optics on BOTH layers (MI for the static tiles,
RiverWaterConfig defaults for the live carrier, now matched so the
two meshes read as one body of water):
- RiverbedColorScale 0.60/0.64/0.58 — submerged granite keeps its
  light wherever water is not aerated.
- Shallow/Deep opacity 0.30/0.54 — see through the margins, keep an
  emerald body in the deep channel; FoamWaterOpacity stays 0.91 so
  whitewater is still an opaque white pile (the contrast the player
  asked for).
- Absorption 0.0066/0.0026/0.0040 per cm — red dies ~2.5x faster than
  green, so depth tints emerald instead of gray-teal; scattering
  green-forward at 0.00010/0.00028/0.00020 (still ~200x below the
  aerated coefficient) so the body glows green instead of milky gray.
- Body colours dropped to near-black green (0.012/0.030/0.026 shallow,
  0.006/0.020/0.019 deep) — clear water has almost no diffuse albedo;
  its colour now comes from the volume and the bed, as in the photo.
- The milky veil itself was mostly SURFACE terms, and the carrier wore
  more of it than the tiles: the additive fallback sky tint ran at
  0.62 strength on the carrier (LiveSkyReflectionStrength default) vs
  0.28 on the MI, over a brighter sky colour, with specular 0.42 vs
  0.28 — the guide's near-field water was the milkiest on the river.
  Both layers now run fallback 0.15 over a darker green-gray sky
  colour (0.075/0.130/0.150) and specular 0.28. Roughness drops
  0.24 -> 0.15 on the tiles so reflections resolve as a mirror
  instead of a diffuse sheet; the carrier keeps a 0.20 anti-glint
  margin (its panning micro-normals strobed under a tight lobe,
  measured 2026-08-27 — the tiles run zero micro-normals so they can
  go tighter).
Captured verification (shore + steep + rapid series): bed visible
through the margins and shallow bars, green volume in the channel,
white wake/foam contrast intact, no carrier/tile seam. MI re-authored
via RaftSim.CreateSouthForkTransmissionWater (no V4 graph change
needed — all edits are instance/config values). P2+P3+P4 15/15.

## 2026-08-31 bend-following hull + visible boat wake

Player experiment: raft released at the top of the first rapid ran a
straight line through the left-arc instead of being carried with the
water. Heading telemetry (new water_dir/raft_dir fields in the drift
log) split the diagnosis: in a FREE drift the raft heading locks to the
turning water within a degree — translation drag was never the defect —
but under paddle thrust the boat runs 2-3x water speed and NOTHING ever
yawed the hull, because drag was a single centre force with zero
torque. Fix: per-point hull drag — each tube sample point drags against
the water sampled AT that point with its own rotational velocity, so
differential current along the hull becomes the bend-following yaw
torque and rotation against uniform water becomes yaw damping. Weighted
by per-point immersion over the point count, the uniform-water total is
exactly the former centre force with zero net torque, so every tank and
parity fixture is unchanged by construction; P2+P3+P4 15/15 including
the flip and both approach-draft telemetry parities. Paddled repro now
turns with the bend (raft +2.7 deg while water turns +7.3 deg over the
same reach; free drift still heading-locked).

"There is no wake behind the boat as the crew paddles" — three stacked
causes: (1) 6 cm Kelvin-arm amplitude vanished at the first-person
grazing angle (now 11 cm, 22 m trail, foam gate 0.6-2.5 cm; contract
bound updated); (2) the wake state subtracted WORLD-frame water
velocity from RIVER-frame boat velocity, skewing direction/magnitude
everywhere the channel is not world-X-aligned (now projected through
the local tangent basis); (3) the carrier's V4 transmission material —
a frozen duplicate — had NO wake surface response at all (that lived
only in the live-overlay material). First material pass (0.30 roughness
+ a foam-colour tint) read as WHITE AERATED bands under a bright sky —
"it should just be a ripple like a lateral wave" — so the colour term
was removed entirely and roughness cut to a 0.06 whisper: the ripple
reads through the wake slopes already folded into the vertex normals
(moving specular), which is the honest look for a displacement wake.
V4 regenerated via RaftSim.CreateSouthForkTransmissionWater.
Regen note: the first pythonscript attempt hung and its zombie held
MPC_RaftSim_RaftFoamOcclusion.uasset locked, which fails the
transmission creator's collection precondition (now logged with
per-condition detail) — kill stale UnrealEditor-Cmd processes before
regenerating.

## 2026-08-31 handed guide seat

"The guide should be right handed or left handed... if right handed they
sit on the right side of the boat." The guide's visual seat was a
centred coxswain perch (-175, 0) no paddle guide uses. The guide now
perches on a stern-quarter tube at the paddler lateral (+/-62 cm),
side chosen by raftsim.GuideLeftHanded (default 0 = right-handed,
right tube), and ConfigureAppearance's seat side follows so the stroke,
T-grip hand, and blade land on the dominant side. Physics seat mass
stays at the Python reference's centre-stern (D6 parity untouched).
Verified over-stern capture: centre empty, guide on the right tube;
M5 5/5 + P2 3/3 green.

## 2026-08-31 pillow round 2: waterline rocks + readability floor

Repeat "no pillow" reports (km 0.86/0.88/0.91/0.98/1.02) forced three
deeper moves:

- Runtime probe added (behind raftsim.LogWaterRenderStateEvents):
  "RaftSim boulder pillow probe: footprints=N wet_ring_verts=N
  max_pillow_m=... max_ring_speed_mps=..." per refresh — proved the
  field computes and applies (19 cm at 2.96 m/s in-window) in scripted
  runs, so remaining player-visible gaps are location/flow-specific.

- Waterline scenic rocks promoted to footprints: the rocks players
  photograph are bank scatter standing at wide pools' waterlines, which
  the footprint pipeline (rapid catalog only) never covered. The
  environment pass now records scenic rocks >= 0.7 m radius whose base
  sits within 25 cm of the local water surface and writes them beside
  the catalog: boulder_footprints.json grew 113 -> 209. Cutout, pillow,
  and wake attach to them automatically.

- Readability floor: rocks at pool edges stand in slow bank water where
  the physical stagnation rise is a few invisible centimetres. Any
  current >= 0.12 m/s now guarantees at least a 33 % envelope
  (~4-7 cm mound); dead-still water still mounds nothing. Contract test
  extended (slow-drift floor + still-water zero).

Note: the player's specific km 0.86-0.88 rock still is not positively
identified among the placement systems (not catalog by position, not
promoted-scenic there, cobble too small) and exposure differs between
sessions at equal stations for unestablished reasons — if it stays
flat, the in-game probe line pins which link fails.

## 2026-08-30 headless guide shadow + cutout membrane (+ pillow triage)

Three-part player report:

- "The guide doesn't cast a full shadow, head is missing" — the
  first-person head hide zero-scales the CC0 head bone and hid the
  production helmet outright, which removed both from the shadow pass.
  While the hide is active, the always-posed procedural head/helmet
  shells and the production helmet now cast hidden-primitive shadows
  (SetCastHiddenShadow, toggled symmetrically so third-person never
  double-shadows).

- "There seems to be a hole in the water texture" — the immutable-
  topology island collapse anchored each column to its own nearest wet
  row, and adjacent columns choosing OPPOSITE sides of a presence gap
  stretched visible membranes across it (pale faceted sheet beside the
  rock). First fix (per-column 1.5 m sink) was WORSE at real boulder
  cutouts: the funnel from the water rim to the sunk sheet rendered as
  a crater of exposed bed with faceted water walls around every exposed
  rock ("no pillow and hole in water" / "disappearing water", player
  screenshots km 0.98/1.02). Final treatment: a cutout gap collapses
  onto ONE sunken point at its boulder footprint's centre (nearest grid
  vertex, rim-referenced Z minus 0.8 R) so every interior quad is
  degenerate and the rim cone dives beneath the rock mesh that owns the
  cutout; footprint-less bar gaps revert to the original same-column
  collapse, whose occasional slivers read as wet sheen, not craters.
  Note for anyone reproducing: the release schedule moves the water
  level over run time, so rocks exposed in a player session can be
  submerged (or beached) in a fresh scripted capture — the geometry
  logic is level-independent.

- "The water flowing downhill should form a pillow as it slams into the
  rock" — the player's follow-up HUD shot pinned it: river km 0.86 =
  the Meat Grinder cluster (footprints 874/883/905, the big r=2.54 rock
  downstream of the readout). Current there measures 1.26 m/s, but the
  pillow's speed envelope SmoothStep(0.45, 1.65) muted moderate drift
  current (~11 % amplitude at the 0.7-0.9 m/s that carries the raft
  past exposed rocks — a dead-flat nose on a metre-wide boulder in
  visibly moving water). Envelope lowered to SmoothStep(0.25, 1.20):
  full amplitude from ~1.2 m/s, a readable ~7 cm mound at 0.8, still
  nothing in slack water. Contract test extended with a moderate-drift
  assertion (>4 cm at 0.8 m/s at the nose probe); the 1.8 m/s bound
  assertions are unchanged. Note: water level differs between sessions
  (release schedule), so the same rock can be exposed for the player
  and submerged in a fresh capture — footprint attachment and pillow
  amplitude are level-independent. Six rapids (incl. Chili Bar Hole)
  still have no catalog boulders at all — flagged as a future content
  pass, not part of this fix.

## 2026-08-30 water growing onto the shore (solver bank-bleed suppression)

Player recording (PIE, scout view of the km 0.15-0.19 point bar while
the raft drifted past): "the shore is still changing with the water
growing onto the shore". Waterline tracking on the clip measured
±0.5-1.5 m advance/retreat swings on 1-4 s periods, tracking the raft.
A fixed-camera hold test in -game showed a frozen waterline (±2 px over
20 s), so the motion is coupled to the raft's approach: the crop
authority handover. The recede half of that handover was already fixed
(feather + visual-submersion keep), but the ADVANCE half never was — a
solver-WET verdict landed instantly at full presence with the solver's
own level, and the solver's bank wetting is one coarse cell wider and
centimetres higher than the authored margin. Every pass of the crop
painted that extra water up the flat bar and then drained it again; on
a near-flat shelf a few centimetres of level step sweep the visible
waterline metres sideways (the slow shore reference faithfully follows
a sustained step within ~1.25 s).

Fix — presentation defers to the baseline in shallow water: a
solver-wet cell where the baseline is dry presents dry below 0.35 m
(bank bleed, also cleared from the solver-wet presence/foam mask), and
a shore cell whose solver level agrees with the baseline within 8 cm
presents the baseline's level, so the handover never steps the slow
reference. Deep or strongly deviating water — floods, surges, rapids —
keeps full solver authority; physics is untouched. Verified: fixed-
camera hold, drift-past, 9 fps drift-past, and authority-arrival
captures all show the waterline steady within a few pixels (the
arrival's feather front settles ~8 px once, smoothly); zero render-
state events; RaftSim.P2+P3+P4 15/15.

## 2026-08-30 shore flicker in PIE (immutable core topology)

Player recording from a live editor (PIE) session at ~9 fps: "the shore
appears and disappears" — the near-shore water flashed to a transparent
window over the bed roughly once a second while drifting, reading as the
beach appearing for a frame. Pixel forensics on the recording proved the
surface never left (the "bed" pixels carried the water's transmission
tint, nothing like the dry bank sand in the same frame): each flash is
ONE FRAME of the carrier rendering with cold shading caches right after
a mesh-section recreation. At 30 fps TSR blends that frame into a
barely-visible pop (the long-running "reflective surface pops" saga —
same event class); at PIE-hitch framerates each one is a full 110 ms
shore flash.

The drift benchmark with raftsim.LogWaterRenderStateEvents=1 showed the
real recreation rate: ~2/s interior ("core_create_interp_topology") plus
~2/s boundary ("core_boundary_create") — the interior/boundary split and
frozen band had NOT made the lists stable, because interior emission
still keyed on live wet presence (bFullyWetCell), which churns with
wakes and lapping even mid-channel.

Fix — immutable full-lattice topology: the core's index list now covers
EVERY cell passing the static station-coverage feather and is built
exactly once per grid shape. Wet/dry churn, recentres (pure vertex
remap + in-place update), band motion, dry-out, and re-wet are all
vertex motion: the directed dry pile extends across whole columns, and
fully-dry columns duplicate their nearest present column's piled profile
(all-dry windows sink the degenerate lattice out of sight instead of
clearing the section). The interior/boundary section split, the
deep-water dwell latch, the partition snapshot, the frozen band's
escape rebuilds, and the boundary section itself are all retired — the
one remaining CreateMeshSection is the first build of a grid shape.
Verified: the same 90 s drift benchmark now logs 6 grid_recentre events
and ZERO section events across five streaming handoffs; frame scan of
2824 dumped frames shows no step anomalies after the walk-in teleports;
shoreline reads clean in spot frames.

## 2026-08-30 crew presentation: "butt gash", buried necks, guide rear glance

Player report, four items (one screenshot pair + recording). The shore
item was the already-fixed recession bug on a pre-fix recording; the
other three were crew-visual defects:

- "A gash in the right butt cheek of each crew member" — root cause was
  NOT anatomy. The procedural paddle blade material was solid dark
  blood-red (0.30, 0.05, 0.002); on the forward-stroke exit the blade
  sweeps past the paddler's hip, and against the black wetsuit glutes
  the maroon shape (plus TSR silhouette noise on the fast-moving edge)
  read as an open wound. Proven by capture bracketing: blob absent in
  plant/recovery frames, present at stroke exit, and it survives `show
  StaticMeshes` (so not boots; the blade is procedural). Fix: commercial
  polyethylene blade yellow (0.68, 0.44, 0.02, roughness 0.48) via
  RaftSim.CreateRaftCrewMaterials; the guide's first-person paddle
  shares the asset. Verified in captures: blade reads as equipment,
  glutes clean in every stroke phase. (The seated-pelvis fallback mesh
  also gained numeric central-difference normals replacing analytic
  ellipse normals — correct shading if the procedural body is ever
  presented, invisible while the CC0 body owns anatomy.)

- Helmet/PFD/wetsuit interpenetration with no visible neck — geometry
  made a neck impossible: solved head centre Z 91 put the head underside
  (~78) below the PFD shoulder foam top (~81). EvaluatePose head raised
  to Z 96 (CC0 bone chain follows the pose contract, so the rendered
  neck stretches with it), procedural fallback neck lengthened
  (offset -13, Z extent 9) and it keeps its skin material in the
  production path (the old wetsuit-material override made any exposed
  band read as more neoprene). Verified: helmet rides clear of the
  collar with an articulated neck column between. Note: the visible
  column renders as the CC0 suit's own black neoprene collar (the CC0
  skin atlases are hash-locked photographs; the suit coverage is
  authored mesh geometry) — flagged to the player that true skin tone
  there would need per-variant work if the collar look isn't enough.

- Guide's own body blocking the rear view — first-person rear glance now
  hides the guide avatar (actor-level, restores per-component state on
  return) with 100 degrees enter / 85 degrees exit hysteresis on the
  control-vs-raft yaw offset.

- "The crew legs clip into the boat texture" (follow-up report) — the
  seated base pose was a bench-sit with knees at 21 cm and feet planted
  45 cm forward at 8 cm, which drove the shins through the raised
  self-bailing floor cushions and the inboard knees into the thwart
  base. The legs now hold a tucked paddler's brace: knees (19, ±13, 27),
  feet (34, ±15, 17) resting on the cushion tops. Verified from the
  guide seat and a top-down interior view (clean silhouettes, boots
  with floor contact shadows); M5 crew pose + rescue loop stay green
  (the high-side leg asserts are relative shifts, unaffected by base
  constants).

Validation surfaced two RaftSim.M5 failures that PREDATE this session
(the M5 test file last changed 2026-08-07): the forward-stroke landmark
assert still encoded the reversed blade motion fixed on 2026-08-10
(expectation updated to the validated catch-forward/sweep-rearward
stroke), and RuntimeRescueLoop's exclusive-ownership assert has failed
since the guide-eye camera landed on 2026-08-08 — the first-person
guide hides its own helmet by design, so HasExclusiveCC0BodyOwnership
now accepts a helmet hidden specifically by the first-person head hide
(and logs which clause failed whenever ownership is refused). M5 also
proved NullRHI-hostile (texture sizes read 0, Niagara never readies):
run it with a real RHI.

## 2026-08-30 black shapes in the wake (resurrected ripple overlay)

Player recording: paddling forward produced large faceted black shapes
in the water instead of a wake. The paddle-wake ripple overlay
(SurfaceMesh section 1) had been silently dead since authoring — its
in-place update always failed the engine's vertex-count check against
the full-grid section BuildGrid created — so its material was never
reviewed on real geometry. The section-count hardening (recreate on
mismatch) resurrected it, and it renders black. Per the standing
one-visible-carrier constraint the overlay is a second sheet anyway;
the wake belongs to the carrier's own signed vertex displacement
(Kelvin-arm field, ~6 cm, 16 m), which the black mass was occluding.
Retired behind raftsim.PaddleWakeRippleOverlay (default 0). Wake area
renders clean; if the geometric wake reads too subtle in review, tune
its amplitude/foam rather than reviving the overlay.

## 2026-08-30 shore recession (authority-handover dry front)

Player recording: "the water seems to suddenly recede from the shores
for no reason" — bank bays and, in reproduction, whole shallow shelves
draining behind a hard straight line that marches with the raft. Cause:
the live solver's wetting is coarser than the visible margin, so as the
crop's authority feather sweeps in, its dry verdicts drain baseline-wet
shallow cells in plain view. The old 5 mm static water used to mask this
(it skinned the same shelves regardless), so retracting it to the 6 cm
line unmasked the sweep; the frozen band's dry pile then rendered the
draining front as a razor edge.

Fix — visual-submersion keep: where the rendered-terrain probe proves
the water plane genuinely covers the visible ground by >= the film
cull's release depth (9 cm), a solver-dry / baseline-wet cell keeps
presenting the baseline at full strength regardless of crop authority.
Physics stays solver-owned. Probes now also cover the whole
solver/baseline disagreement set (not just the outer bank rings; budget
raised to 192/refresh) so shelf interiors are defended too; boulder
cutouts stay solver-owned because their traces hit the untagged boulder
and fail open without granting the keep. Verified: the drift burst that
previously emptied the entire view (recede_007) now holds a full river
with one clean waterline; RaftSim.P2+P3+P4 15/15 with zero
procedural-mesh or handoff error lines.

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
