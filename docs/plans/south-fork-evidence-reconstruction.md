# South Fork evidence-based reconstruction objective

Requested 2026-09-06. Work in progress; no geographic or hydraulic acceptance yet.

Performance target revised by the user on2026-09-12: desktop30FPS,33.333ms
p95 frame budget. Earlier60FPS assessments below are historical. See the
current target and unchanged quality/physics requirements in[remaining work](remaining-work.md).

Reconstruct Chili Bar to Salmon Falls as accurately as available captured data
permits, then make the rendered terrain, boulders, collisions, bathymetry, water
geometry and hydraulics mutually consistent. Keep source evidence, inferred
underwater shape and artistic detail explicitly separate.

The initial September 6 app goal creation call was rejected because an older
all-rivers goal was unfinished. On September 7, after the app reported no active
goal, the user's explicit completion request successfully created a new goal
covering this reconstruction and the full queue in `remaining-work.md`. Keep
that goal active until its complete scope is genuinely handled.

## Sequence and acceptance

1. Audit the current route origin, length, projection, named-rapid bindings and
   terrain provenance against independent maps/imagery. Preserve old artifacts.
2. Acquire actual LiDAR coverage/tile indexes, point clouds or native-resolution
   DEMs and dated orthophotos for the correct reach. Verify coverage polygons,
   horizontal/vertical units, datum, acquisition date and licensing.
3. Reconstruct in a metric geographic frame: channel boundaries, rock islands,
   exposed boulder outlines/heights, banks and persistent bedrock controls.
   Do not place rocks randomly in the main rapids. Undocumented features stay
   provisional; videos alone do not establish surveyed underwater coordinates.
4. Start at Troublemaker, then Meat Grinder and the other upper-run rapids,
   then the Gorge including Satan's Cesspool and Hospital Bar. Register photos
   and footage to visible fixed landmarks; document flow and unknown camera
   calibration. Compare overhead planform and boat-height views.
5. Derive render geometry and collision from the same reconstruction; derive
   hydraulic bed and bank masks from it with resolution/uncertainty recorded.
   Re-cook flow windows, verify discharge/storage balance, dry-bank exclusion,
   expected hole/wave positions, raft collision and surface/boat consistency.
6. Validate real engine captures and motion, not merely generator flags.
   Measure frame times on the same test route. Do not accept missing drops,
   made-up channels, smooth placeholder water or unstable shoreline patches.

Online imagery/footage is reference-only unless its license permits shipping.
This reconstruction is a game environment, not a river-navigation product.

## User-requested next river

On 2026-09-06 the user queued the Colorado Grand Canyon run after South Fork
is completed and validated. See `colorado-evidence-reconstruction.md`.
Source acquisition alone does not satisfy the South Fork prerequisite: the
playable scene and consistent geometry/physics must also be validated.

## Current launch hierarchy — September 13 (unfinished)

South Fork is the scenario. Troublemaker is a rapid inside it and is NOT a
separate menu entry; the five South Fork launch contracts retain the full river
map. The bounded captured-rapid assets remain available for reconstruction,
but do not replace the river. Native career/catalog and migration regressions
cover this correction. The rapid-challenge launch note below is superseded.

The normal FullReach water material has received current-carried ripple and
transported-foam updates. It is not yet accepted for convincing breaking waves,
froth, reconstructed terrain/river alignment or performance. Latest measured
ordinary play is23.365478FPS/p9547.2488ms with live unmasked source uploads,
still below30FPS/33.333ms; prior21.571211FPS/p9552.6052ms is retained. Current supporting
GPU trial work and remaining integration are recorded in
[remaining work](remaining-work.md); passing solver fixtures is not scene delivery.

## Historical implementation checkpoint — 2026-09-06 (unfinished)

Superseded playable integration, September12UTC: the normal Troublemaker Rapid
Challenge now uses L_SouthFork_Troublemaker with the corrected captured terrain,
shared collision and byte-identical source-matched flow in a packageable data
location. This is the bounded270m section, NOT the corrected full river. The
other five South Fork entries retain the old route. Guided traversal/material
coverage/native progress pass; source geometry and user save are preserved.
Visible rock/shoreline coarseness, breaking-water realism and performance gates
remain unresolved. See
[actual integration and limits](../reconstruction-review-2026-09-07/playable-captured-rapid-integration.md).
The following September6 checkpoints are historical, not current launch wiring.

The old route starts 15.4 km upstream of the actual Chili Bar bridge. Its old
Troublemaker marker is about 9.7 km from the published real-rapid hazard location.
The captured-water-constrained route candidate is 33.334 km; production still
uses the old approximately 49 km route. This requires a coordinated migration,
not a cosmetic water-material substitution.

Acquired all 82 native DEM tiles for the candidate corridor, four original
classified LiDAR tiles around Troublemaker, and dated NAIP search references
and half-metre source windows for 20 rapid names. All source windows have full
coverage. Search locations are not verified rapid identities. Hydroflattened
elevation is not submerged bathymetry.

Troublemaker's candidate uses captured banks and photo-reviewed original
returns for exposed rock; underwater depth and the hole control remain explicit
hypotheses. Rendering, terrain collision and hydraulic resampling share one
hashed half-metre geometry. Twelve Unreal terrain collision-height probes pass.
One-metre MUSCL diagnostics pass the mean-flow screen and numerical face-flux
conservation audit. A half-metre refinement is a separate resolution test, not
automatic acceptance. Native regressions cover mixed-regime prescribed inflow
and retaining positive sub-dry films rather than deleting their water mass.

Separate review maps are `/Game/RaftSim/Maps/Review/SouthForkSurveyCandidate`
and `/Game/RaftSim/Maps/Review/SouthForkSurveyPlayable`. The playable candidate
opts into the offline MUSCL boundary/roughness and disables the unrelated legacy
support wave. It has not passed final animation, full raft collision or
performance acceptance. Its raw solver state is intentionally not hidden by
additional standing-wave geometry during this diagnostic.

An unchecked `new_level` failure in the review scripts added test actors to the
startup map. Those specific additions were removed, original actors retained,
and the boot game mode restored. Recovery evidence is in
`docs/reconstruction-review-2026-09-06/engine/boot_spill_repair.json`.
Both import scripts now fail closed on the wrong world or a failed save.

Run `physics/scripts/update_south_fork_reconstruction_progress.py` to aggregate
the current evidence. Its report does not promote any production geometry or
claim that South Fork, its 20 rapid layouts, or photorealism is finished.

## Hydraulic stability and runtime checkpoint — 2026-09-06 evening

The half-metre refinement at CFL 0.38, with 0.1-second outer steps, is rejected.
The bounded rerun remained around 2.46 m maximum depth at 90 seconds, then
reached 3,593.28 m depth and safety-clamped velocities by 100 seconds. The
original uninstrumented process was stopped after more than 78 CPU minutes;
its termination is not a successful cook. The old generic native validator
incorrectly accepted the bounded failed result because its limits allowed
50% storage drift and 100 m/s speed without checking safety-clamp saturation.

Native validation now rejects non-finite conserved/primitive fields and
velocity-limit saturation. Excessive CFL workloads fail before overflowing
the integer substep count. The runtime adapter catches native step failures,
latches its fault, and does not commit a successful water frame or silently
retry on the next tick. Engine export additionally screens every saved survey
frame against generous candidate-specific 10 m depth / 20 m/s failure bounds;
these are numerical rejection limits, not surveyed physical targets.

Two continuations from the last saved stable fine-grid frame pass the bounded
sanity check: CFL 0.2 / outer dt 0.025 for 10 seconds, and CFL 0.2 / outer dt 0.1
for 20 seconds. This implicates insufficient temporal stability margin, but
does not establish long-duration stability or spatial convergence. Keep the
half-metre result out of the engine until longer tests and flux/storage audits
pass. Full details: `docs/reconstruction-review-2026-09-06/half_metre_stability.json`.

Verification completed after these changes:

- Four native fixtures pass, including lake-at-rest, wet/dry shoreline,
  transcritical flow and the one-metre survey case; new regression assertions
  cover CFL fail-fast, non-finite states and velocity saturation.
- Thirteen captured-source/coordinate tests and five survey-sanity tests pass.
- The updated Unreal editor builds and `RaftSim.Survey.SouthForkRegisteredReplay`
  passes (including rejecting non-finite dt and preserving fault state).
- The final 100-step native optimization comparison is bitwise identical to
  the baseline in every exported field: 7.98 s versus 5.12 s, about 36% less
  wall time. This is not a production FPS measurement.
- Earlier offscreen stripped-review performance was 23.73 ms mean / 30.71 ms
  p95 at 1280x720 with 87% screen percentage. It fails the 60 FPS target;
  production scenery was not included and is not performance-qualified.

The captured banks, rigid coordinates, terrain collision heights and short
unpowered raft drift are validated only within the neutral review section.
Full raft/boulder collision traversal, long-run water animation, verified
identities for all rapid windows, the 33.334 km production route migration,
scenery replacement and photorealistic/performance acceptance remain open.
No production reconstruction has been promoted. No later river was started.

## Queue resumed — 2026-09-06 late evening (September 7 UTC)

The user requested completion of all queued work. The existing hourly follow-up
now actively advances South Fork instead of waiting for it to finish elsewhere.
The order remains South Fork, Colorado, Pacuare, Futaleufu; no later river has
been started or marked complete.

A 120-second continuation of the half-metre solve at CFL 0.2 / outer dt 0.1
completed in 846 wall seconds. All 13 saved frames are finite, maximum saved
depth is 2.468 m, maximum speed is 12.463 m/s, and velocity clamps were not
reached. The numerical face-flux/storage derivative audit passes. The mean-flow
settling screen still fails because tail storage rates exceed 2% of discharge.
This result has not replaced engine fields or established spatial convergence.
See `docs/reconstruction-review-2026-09-07/extended_stability.json`.

The custom raft bridge previously ignored the captured static-mesh terrain,
using Landscapes or the coarser hydraulic bed for ground contact. Explicitly
tagged `RaftSimPhysicalGround` mesh components now supply full-triangle contact
heights and normals; untagged scenery is excluded. Only the isolated playable
review map is tagged. Its constructor/import scripts retain the registration.
The new engine test checks four captured rock sites and one bank at four
headings, across 2,400 substeps, against independent world collision queries.
The contact-only corrected test passed all 20 cases without sampled penetration;
this does not certify a natural downstream traversal or D4 wrap behavior.

Live captures exposed a second setup bug: the review game mode's pawn class was
null because the script looked in `/Script/SmokeEmIfYouGotEm` instead of
`/Script/RaftSimRaft`. The isolated game mode now selects the real guide pawn,
and the engine regression also requires that it is possessed and attached to
the raft. Earlier underground camera captures and their mixed screenshot/
performance run are rejected as boat-height visual acceptance.

The final two engine tests pass, including possession and contact checks. Three
corrected boat-height captures show unpowered drift, but their plain terrain,
sharp channel cuts and smooth water do not pass visual acceptance. A clean
1280x720 run measures 21.752 ms mean / 28.336 ms p95 over 920 frames, with a
12.905 ms mean solver step: still above the 60 FPS and solver-time budgets.
The report now identifies the actual NVIDIA RTX 3060 Laptop rendering adapter
instead of the OS primary-device string (AMD integrated graphics).

Remaining immediate work: natural whole-rapid collision/animation traversal,
fine-grid storage oscillation and runtime performance, then rapid identity/
landmark registration and coordinated full-route migration. Preserve raw failed
diagnostics. Never convert these bounded checks into full-scene or photoreal
acceptance. Detailed current handoff:
`docs/reconstruction-review-2026-09-07/checkpoint.md`.

### Hourly continuation: runtime optimization and build identity

Interior MUSCL flux pairs are now reused within each integration stage, retaining
both bed-correction sides and invalidating cache entries for skipped dry cells.
Three alternating 100-step survey comparisons retain bitwise-identical saved
fields and show a modest 5.2% lower median native wall time. Three native fixtures,
the native survey fixture and 12 Python survey/layout checks pass.

The engine had not relinked a newer external solver archive despite a successful
build. Its archive SHA-256 now enters the module compile environment, forcing
actual rebuild/relink of consumers when the binary changes. The full editor
rebuild succeeds. A clean review benchmark is 19.783 ms mean / 27.209 ms p95,
11.057 ms mean solver step, versus the earlier 21.752 / 28.336 / 12.905 ms.
This still fails acceptance. No geometry, cooked field, resolution, stability
setting or visual-quality setting was changed; no later river was started.
Reports and remaining work remain in the September 7 checkpoint.

### Completion request: traversal and repaired-bed experiment

The normal-clock, unpowered engine traversal advances 145.7 m without sampled
ground penetration, then grounds at a downstream rock and fails to reach its
outlet criterion. The diagnostic remains failed; guided traversal is pending.
Twenty-two captured-rock repair, geographic and export-identity regressions pass.
A conservative enclosed-gap candidate preserves measured values and marks its
40 interpolated cells explicitly inferred. Its 600-second 1-m hydraulic lineage
now passes mean-flow and conservation screens, with all 14 continuation frames
finite and within sanity bounds. This is not spatial convergence or photographic
acceptance. A separately exported package is not yet engine-integrated; mesh,
collision and fields must move together. The production reconstruction and
Colorado/Pacuare/Futaleufu queue remain incomplete. See the September 7 checkpoint.

### Hourly continuation: coordinated candidate engine integration

The repaired mesh, full-triangle collision and matching hydraulic package now
load together in the isolated playable review, preserving the old assets and
exact previous map. Sixteen collision-height probes and two candidate/contact
engine regressions pass, plus 21 Python layout/sanity/export tests. Actual
gameplay captures still fail visual acceptance; clean mean frame time is 19.024
ms (p95 25.501 ms), above budget. The old natural-drift outlet failure remains
historical evidence, not a candidate pass. Follow the latest checkpoint and
`gap-integration-review.md`; do not regenerate the old review over the new
candidate or repeat the completed cook/import instead of advancing breaking
water, guided traversal and grid convergence.

### Completion request: guided candidate and single-carrier breaking

Normal-paddle guided traversal is now implemented with a current-aware
diagnostic route, footprint checks and independent sampled ground clearance.
The baseline has one bounded pass. A fresh-map opt-in shared-breaking run also
passes: 80.11 s to the outlet, 4.62 m maximum route error and no sampled ground
contact. The combined engine suite passes 3/3; ten Python route/ledger tests
and nine subtests pass. Earlier failures remain in the ledger, including a
misleading early outlet-only success rejected by the stronger tracking check.

The surface-lit survey carrier had inherited a 15 m legacy-overlay exclusion.
An exact-map/package-gated experiment uses existing shared crest/support relief
and single-carrier ownership, with no separate lip/roller sheets. Actual fixed
camera comparisons still fail visual acceptance, and clean mean/p95 frame time
is 21.423/28.024 ms, over budget. The experiment stays opt-in, production remains
unchanged and all later rivers remain queued. Continue from
`docs/reconstruction-review-2026-09-07/guided-traversal-review.md`; do not claim
full-route, spatial-convergence or photorealism acceptance from these passes.

### Hourly continuation: duplicate rapid-foam sheet

Live probes found an extra `RapidFoamMesh` still rendering above the review
carrier, missed by the previous assertion. The scoped shared surface-lit path
now hides it and avoids its redundant uploads. Fixed-camera comparisons confirm
the hard bright overlay disappears; opt-in lit foam parameters retain aeration
on the main surface. No asset, geometry or hydraulic field was changed.

The strengthened carrier/material checks pass, as do collision and replay.
Guided traversal still fails its tracking limit (5.846 m), despite reaching the
outlet without sampled ground contact. Final suite is 2/3, not all green. Clean
mean/p95 frame time is 20.933/26.991 ms and still fails budget. Follow
`docs/reconstruction-review-2026-09-07/single-foam-carrier-review.md` for evidence
and next work. All production/rapid-identity/photorealism acceptance remains false.

### Controlled refinement of the integrated repaired geometry

The finer cook now preserves exact parent boundary forcing rather than changing
median stage when resampling. Nineteen tests and 22 subtests pass. A new bounded
120-second, 0.5-metre run of the current repaired geometry passes every-frame
sanity and numerical conservation, but fails mean-flow settling. Crux stage
differs materially from the coarse result (median -22.5 cm), so grid convergence
remains unresolved. No fine fields were promoted, and the engine scene is
unchanged. Continue from `docs/reconstruction-review-2026-09-07/gap-resolution-review.md`;
do not substitute old-geometry tests or an unchanged repeat for progress.

### Regional settling versus persistent resolution differences

A controlled same-grid continuation now reaches 240 fine-grid seconds. It
preserves source bed and forcing, passes conservation and section discharge,
but still fails the storage screen. Downstream adjustment decreases while a
roughly 23 cm crux stage offset persists across sampled temporal envelopes.
A deep slow pocket beside captured rock is localized for source/interface
investigation; no measured rock was changed. Twenty-six tests and 32 subtests
pass. New dated USGS daily flow context is explicitly not photo-time calibration.
Follow `docs/reconstruction-review-2026-09-07/gap-settling-continuation-review.md`.
No engine or production promotion, and no later river started.

### Matching the hydraulic bed to actual collision triangles

The source mesh uses triangles but the cook used bilinear heights. New
off-vertex engine probes confirm differences up to 1.043 m at tested points;
the triangle sampler matches collision to sub-millimetre precision. Fresh
cooks now use the shared mesh topology, old histories retain their method,
and exports/resolution comparisons verify interpolation provenance.
Thirty-three tests plus 39 subtests and 11 export/sanity tests pass.

A new 600-second triangle-matched cook passes finite/conservation/discharge/
storage checks but still misses the 1 cm regional-stage screen (10.612 mm).
Its separate review package is exported, not loaded. No captured rock or
engine asset changed. See `docs/reconstruction-review-2026-09-07/triangle-sampling-review.md`
before staging it or performing a same-method refinement. No later river starts
and no overall reconstruction/photorealism acceptance follow from this fix.

### Actual-engine check of the triangle-sampled package

The previously export-only package is now reversibly staged in the same
isolated review, preserving the mesh/material and exact previous map. Sixteen
interior collision probes and the new candidate-specific water replay pass.
The final engine suite is 2/3: contact and replay pass; guided traversal reaches
the outlet but misses the unchanged tracking limit (5.145 m versus 5 m).
Twenty-six Python tests plus 21 subtests pass; build succeeds. Actual captures
still fail photorealism, and clean performance (18.990 ms mean / 24.632 ms p95)
still misses budget. A tiny-gain native optimization was tested and discarded;
the engine-linked solver is unchanged. Follow
`docs/reconstruction-review-2026-09-07/triangle-runtime-review.md` and the latest
checkpoint. The queue remains incomplete; no production or later-river rollout.

### Same-triangle half-metre refinement: rejected intermediate frame

A matched 240-second half-metre warm start now isolates resolution from the
previous interpolation mismatch. Independent history checks reject a 23.7504 m/s
shallow-bank momentum spike at 100 seconds; a finite/sane final frame is not
acceptance. The offending cell and adjacent saved samples are localized in
`docs/reconstruction-review-2026-09-07/triangle-refinement-review.md`. No fine
engine package is exported. Investigate this specific excursion before another
full cook; do not relax the safety bound or repeat unchanged runs.

A static subgrid audit separately exposes narrow rock/channel sampling loss.
New primary CDFW photos/maps cover upstream rapids at a different release target,
not measured Troublemaker bathymetry. Both findings retain explicit provenance
and limitations. The playable review and later-river queue are unchanged.

### Reproduced bank spike and consistent depth-limited reconstruction

The current uncalibrated numerical core now uses consistent hydrostatic
interfaces, cell-constant face beds and depth-limited stage slopes. Earlier
guard-only and adaptive-timestep candidates were tested and rejected; evidence
is retained. Passing bounded fine-grid intervals and a fresh 600-second 1 m
cook now meet all saved-history, mean-flow and conservation checks. This is
not spatial convergence or measured underwater geometry.

The editor is rebuilt and the matching fields/start reversibly staged in the
isolated review. Candidate replay and captured-ground contact pass. Correctly
quoted guided traversal reaches the outlet but fails 5 m tracking at 12.329 m;
the earlier malformed-argument launch is retained separately. Clean mean/p95
frame time is 14.669/19.437 ms, still over p95 and solver budgets. Actual captures
still fail photographic acceptance. Follow the latest checkpoint and
`docs/reconstruction-review-2026-09-07/bank-spike-fix-review.md`.

Three cross-platform packaging-fixture failures are also resolved without
weakening package checks. The comprehensive unfinished-work index is
`docs/plans/remaining-work.md`. South Fork and the later-river queue are not done.

### Attainable-track guided traversal

The current package's 12.329 m tracking failure is localized to abrupt heading
demands and withholding the guide's stern stroke during crew pivots. An opt-in
controller now solves for feasible ground-track heading with the same 2.2 m/s
paddle-speed limit and permits normal guide sweeps during crew turns. Neither
physics, assets, route points nor acceptance limits change. The coordinated-only
experiment still fails at 10.216 m and is retained. The complete controller has
two bounded passes at 3.869 and 4.712 m. The final combined engine suite passes
all four guidance, captured-ground, candidate replay and traversal tests; twelve
Python tests plus nine subtests also pass. These are not photographic, continuous
swept-collision or full-rapid robustness acceptance. Follow
`docs/reconstruction-review-2026-09-07/attainable-guidance-review.md` and the latest
checkpoint. Fine-grid convergence and water appearance/performance remain next.

### Corrected-core half-metre check

The full-queue app goal is now active by explicit user request. A same-core,
same-forcing 240-second half-metre refinement completes, passes every saved
frame, all three mean-flow screens and exact conservation. Crux median stage
difference from the coarse result is -1.54 cm, p95 absolute 8.74 cm, but local
differences reach 25.34 cm and two grids do not establish convergence. A separate
review package is exported, not engine-staged. The actual map remains unchanged.
The conservation tool now guards solver identity and prior evidence; eight tests
plus 18 subtests pass. See `depth-limited-refinement-review.md` in the September 7
review directory. Continue efficient crest/foam presentation and remaining
grid-sensitivity work, not an unchanged rerun or a premature later-river rollout.
