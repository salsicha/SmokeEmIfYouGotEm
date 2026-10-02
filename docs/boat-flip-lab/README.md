# Native boat flip laboratory

Water-generated open-water lab validation is complete. Production promotion
remains separate. The rock-pin lab sequence is now validated as described
below; neither result is a full-map or packaged-release claim.

### Rock pinning sequence (2026-10-02)

The tall-rock native run starts broadside, upright and with zero angular
velocity. Actual full-hull contact lifts the downstream side; dipped upstream
upper-face patches admit relative current and apply pressure torque in the
direction of the ongoing roll. The first sampled downstream rise is at 0.225 s,
the first sampled reinforcing scoop at 1.283 s, and physical 100.164-degree
capsize/ejection at 1.575 s. Two upper patches are wet before vertical inversion,
with up to 62.085 N of added scoop force and an 0.0866 m sub-surface patch offset.
This pressure reinforces the composite contact/buoyancy/drag flip; it is not
proof that scoop pressure alone causes overturning. No roll target, incoming
spin, timed pose transition or proxy hull is supplied.

All three fresh 24-second native scenes complete without solver refusal:

| Scene | Outcome | Mean recorded engine FPS |
| --- | --- | ---: |
| Tall rock, 8 m/s far-field authored current | Capsize at 1.575 s; five passengers submerge and resurface | 29.884 |
| Same tall rock, calm water | Level throughout, no ejection | 39.021 |
| Previous lower sloped rock, flowing pillow | 48.542-degree tilt and recovery, no ejection | 32.647 |

The severe run records 540 real contact impulses. Minimum swimmer root offset
is -2.688 m; all five are simultaneously underwater in a native sample at
5.358 s and all return to the local datum by the end. The raft settles afloat
inverted at +0.24084 m. Initial five-passenger loading is 605 kg. The new tall
fixture's bed is -4 m and its flat rock top is +1.5 m, both shared by rendering
and collision. The original lower wedge remains unchanged as a ride-over
control. These are authored qualitative laboratory fields, not surveyed rock
geometry or measured real-raft flip thresholds.

The full 26,610-vertex / 38,344-triangle production hull and all five material
sections are retained. The earlier corner/edge refusal is addressed by
whole-arc separation certificates and feature-owned contact support updates,
not larger event/manifold budgets or dropped collision geometry. Both recorded
failure substeps now finish with passive impulse energy balance and agree with
exhaustive original-triangle replay on pose, velocities, impulses and energy.
Nine native load, cache and collision tests pass in
`tmp/rock-pin-cache-native-v1/index.json`.

Performance improvements are exact acceleration: original-face BVH pruning,
clear-only whole-curved-path flight proofs (contact/refusal uses the unchanged
bounded contact loop), and exact-input source-shape memoization. Same-count
source edits, D4/condition changes and transform changes invalidate the cache.
The cached and uncached 24-second recordings agree exactly at all 227 sampled
boat positions, orientations, angular velocities, pressures and contact counts.
Rendering independently reconstructs the committed shape and verifies every
uploaded vertex/index against collision. Recorded mean FPS passes the 20 FPS
gate; this is not a minimum instantaneous FPS or full-map performance claim.

Evidence: `tmp/flip-rock-pin-native-v4`, `tmp/flip-rock-pin-calm-native-v4`,
`tmp/flip-rock-low-wedge-native-v4`, and the strict three-scene audit in
`tmp/rock-pin-cache-native-v1/three-scene-audit-v4.json`.
The tightened final audit is `tmp/rock-pin-cache-native-v1/final-three-scene-audit-v4.json`;
a compact repository record is `captures/native-rock-pin-suite-v4-audit.json`.
Ordinary `RaftSim.P2.RaftFlipsAndRecovers` also passes without lab candidate
flags (`tmp/rock-pin-normal-recovery-v1/index.json`, zero errors and the existing
capsize warning). This regression preserves the old normal-game policy; it is
not evidence of rock-sequence rollout into normal maps.

Actual backbuffer
animations are packaged with verified pixels/frame counts in the corresponding
`-review` directories. The severe 12-second APNG has 49 verified frames and
zero adjacent duplicate selected frames; original video is retained. Earlier
10.2/17.3 FPS recordings and failed fine-interval packaging remain preserved as
rejected/intermediate evidence.

The contact, shape-cache and upper-patch experiments remain explicitly opt-in
native lab code (`-RaftSimRockPinArcCandidate` plus the existing stable-drag lab
candidate). Normal maps and shipping capsize policy have not been changed by
this rock test. Full-map placement, performance and production promotion are
separate gates, not implied by the laboratory acceptance.

### Current upright-start validation (2026-10-02)

The missing water-generated test is now exercised, not supplied rolling entry.
Fresh native severity sweeps are retained in `tmp/flip-water-generated-native-v1`
and `-v2`; both load/environment automation tests pass. Scene additions change
only the visible authored crest height (1.8, 2.0, 2.4, 2.8 and 3.2 m), keeping
the wave width/speed/jet, pressure law, loading and acceptance gates unchanged.
These are extreme lab controls, not surveyed river waves or calibrated limits.

Actual production-mesh recordings in `tmp/flip-water-generated-v2-*` start at
zero roll and zero angular velocity. The 3.2 m broadside pair both physically
cross 100.466 degrees at 5.308 s, with opposite roll directions, five crew
ejections and no timed pose transition. Peak angular rate is 2.776 rad/s and
maximum native pose step is 0.02313 rad. The raft floats inverted at +0.240 m
relative to the local surface; minimum centre offset is -0.0324 m. Mean native
render cost is 90.29 / 88.33 FPS (lab measurements, not full-map acceptance).

This pair is driven by differential buoyancy/drag against the exact displayed
moving water surface. Additional upper-face pressure impulse is zero in these
runs; it is incorrect to require overtopping pressure to call a buoyancy-driven
flip water-generated. The classifier requires upright/zero-spin initialization,
actual moving-water torque, no solid contact, integrated pose continuity and
real crew ejection. The seeded rolling entries still do not qualify.

The calm, small-crest and eddy-line controls remain upright (0, 5.604 and
0.064 degrees maximum tilt). The 2.4 m broadside and bow-on controls recover
without ejection after 87.507 / 56.853 degrees. Their mean FPS is 93.62..96.20.
The independent initial flip/control audit is
`tmp/flip-water-generated-native-v2/initial-water-flip-audit.json`.

Both fresh 24-second severe runs pass the complete seven-scene strict audit:
physical water-generated capsize, mirrored roll, submerged crew, final
resurfacing, continuous finite integration, flotation and 20 mean lab FPS.
All five crew submerge and return to the local surface with zero final vertical
velocity; the raft remains afloat inverted. Forcing still ends at 9 s, and
release momentum, PFD rules and the original 0.03 m resurfacing gate are
unchanged. The earlier 12-second v1 runs ended before every swimmer resurfaced;
those incomplete observations and their evidence are preserved, not accepted
as full crew validation.

The completed strict audit is
`tmp/flip-water-generated-native-v2/final-water-flip-suite-audit.json`.
Native APNGs and source-pixel provenance are in each scene's `*-review`
directory, including `tmp/flip-water-generated-v2-breaking_broadside_3p2m-review`
and its mirrored counterpart. First, middle and last frames were inspected for
all seven recordings. The actual recordings show upright initialization,
opposite physical flips, submerged passengers and their later flotation; the
five non-flip controls retain their crew. No poses or water frames are
synthesized or interpolated.

The normal-game `RaftSim.P2.RaftFlipsAndRecovers` regression also passes in
`tmp/flip-water-generated-recovery-v1/index.json`, without lab candidate flags:
one successful test, zero errors, one logged capsize warning. This checks the
existing gameplay recovery path, not global promotion of the lab-only policy.
Five classifier unit tests also pass; their synthetic fixtures are only parser
tests and are not used as physical evidence.

No pressure/drag, capsize or swimmer candidate has been globally promoted by
this validation, and the previously failed pinned/contact tests remain open.

These environments run the game's `URaftSimChronoRuntimeAdapter`, production
raft deformation/export, and `ARaftSimRaftActor` crew/capsize lifecycle. They
are not Python boat simulations or pre-rendered capsize animations.

## Environments

### Broadside rock-pillow mechanism (2026-10-02, validation pending)

The user's requested obstruction case is a downstream tube climbing a rock
and its pillow, with the upstream side dipping and admitting current that
loads the hull as a scoop. The accepted open-water flips do not validate this
rock-assisted sequence. The older vertical-block `pinned_breaker` remains a
rejected full-hull contact test, not evidence for this mechanism.

`rock_pillow_broadside` adds an authored bed-connected sloped rock and a
stationary upstream pillow. Rendered triangles, full-hull CCD triangles and
ground height/normal sampling use the same wedge. The production raft is not
simplified, solver limits are unchanged, and no roll or angular velocity is
seeded. `rock_pillow_calm` removes current and pillow elevation as a control.
This is qualitative authored geometry/flow, not surveyed rock hydraulics.

Only these new lab scenes use an incoming-normal upper-face scoop-pressure
candidate. The ordinary submerged drag still acts; the old lateral upper-face
pressure term is not added again on that patch. Incoming water transfers a
signed force to an overtopped, upstream-exposed upper face; dry, tangential or
outgoing flow creates no scoop load. Its application point generates torque,
not an angle target. Existing wave-scene loads and normal gameplay are unchanged.

New receipts separate contact impulses, nominal upstream/downstream tube
height and local-surface offsets, signed longitudinal scoop torque and retained
water. These tube probes are body-local nominal centres/tops transformed by
the actual integrated pose, not exact deformed mesh vertices. Acceptance must
demonstrate downstream climb, upstream overtopping, reinforcing scoop torque
and later physical inversion in that order, plus finite continuous full-hull
contact, submerged/resurfacing crew and the unchanged 20 FPS lab floor. A
passing load/field test alone does not accept the rock flip.

The first build succeeds, and all three native tests in
`tmp/rock-pillow-native-v1/index.json` pass: the new rock-pillow geometry/flow/
scoop checks, existing load/policy checks and the wave/control force sweep.
The actual full-hull broadside recording is a separate pending acceptance.

The fresh `tmp/flip-rock-pillow-broadside-v1` recording is rejected. It reaches
1.041667 simulated seconds, with 741 full-hull contact impulses, 48.54 degrees
maximum tilt and 3.24 mean rendered FPS. The solver refuses an unconsumed
substep after 512 events (0.006883891 s consumed of 0.008333334 s). No limit is
raised and no simpler hull is substituted. Native receipt/video and launch
DLL hashes are preserved, despite clean process exit being insufficient.

The downstream nominal probe rises 1.059 m relative to upstream, but the
recorded upstream top probe never goes below its local water surface (minimum
sampled clearance +0.210 m). The boat rides over this wedge rather than staying
pinned; no sampled reinforcing scoop torque or capsize follows. Thus the first
stage is observed, but neither the intended scoop sequence nor a complete
rock-assisted flip is demonstrated. Next work must address stable sustained
full-hull contact and a genuinely pinned setup, not add an imposed roll.

First/middle/last native frames were inspected. The diagnostic APNG packaging
also refuses a playback-frame-count mismatch caused by repeated frozen frames;
its partial output in `tmp/flip-rock-pillow-broadside-failed-v1-review` is not a
verified animation delivery. No packaging or physical gate is relaxed, and
this exact failing run is not to be repeated unchanged or promoted.

| Scene | Question |
| --- | --- |
| `calm` | Does a normally loaded boat remain upright without forcing? |
| `small_broadside` | Does a 0.25 m broad crest rock the boat without ejecting crew? |
| `large_broadside` | Can a steep 1.6 m crest overturn the boat through integrated forces? |
| `large_broadside_mirror` | Does reversing the forcing reverse the physical roll direction? |
| `large_bow_on` | Does the same crest produce pitch rather than a fabricated lateral roll? |
| `eddy_line` | Does ordinary 1.5 m/s shear turn the boat without a false capsize? |
| `hydraulic_broadside` | How does a broadside entry into an authored return-current/downflow field behave? |
| `rock_oblique` | Can oblique impact on a bed-connected block arrest, yaw or overturn the actual hull? |
| `breaking_broadside` / `_mirror` | Does additional crest-carried current overturn the free raft, with mirrored forcing? |
| `pinned_breaker` | Does a 0.9 m standing crest plus current overturn a broadside raft caught against the actual visible block? |
| `rolling_entry_control` | Does a 30-degree initial roll at 0.5 rad/s recover without ejection? |
| `rolling_entry_port` / `_starboard` | Does mirrored 75-degree entry at 5 rad/s continue naturally through inversion and ejection? This explicitly supplied entry is not generated by the water field. |

The moving-wave controls share one height/current definition between rendering
and force sampling. The hydraulic velocity is an explicitly authored field,
not a conservative nonlinear fluid solution. The rock's indexed faces are used
both visibly and by the game's full-hull continuous collision query; its solid
footprint has no water surface or current. No environment sets the boat's roll
after initialization; the baseline game actor's timed transition is what the
lab is intended to detect and replace.

## Run and evaluate

Run `RaftSim.Demo.FlipEnvironmentBaseline` through native Unreal automation for
the six force-only moving-wave/shear controls. This baseline uses representative
loading without a live hull, obstacle CCD or the actor capsize constraint.
Preserve its `Saved/FlipDemo/native-environments-latest.json` before rerunning.

For actual rendered production-boat runs, launch the test-tank map in game mode
and execute `RaftSim.FlipDemo <scene> <unique-label>`. Each run produces a native
screen recording, a screenshot, and fixed-step state receipts in
`Saved/FlipDemo/<unique-label>.json`. Use a fresh label for every revision.

`unreal/Scripts/evaluate_flip_demo.py` audits these actual integrated receipts.
Its strict mode rejects capsize mode entered before physical inversion, ordinary
controls that capsize, incomplete/non-finite receipts, and suites without a
demonstrated inverted boat and actual crew ejection. Inspect the native video
as well: quantitative state alone cannot establish visual plausibility.

A final change must also pass actual game recovery regression and preserve
normal playable initialization. Neither downloaded references nor passing
source-text checks constitute flip acceptance.

## Findings so far (2026-10-01)

Native force-only tests measured about 5.6 degrees maximum tilt for the small
crest, 57.7 degrees for the large crest, and 77.9 degrees with the additional
breaking jet. The mirrored force controls agreed; none physically overturned.
This is evidence about the reduced model, not proof that a real raft cannot
flip in those conditions.

The first rendered `hydraulic_broadside` candidate failed visual/physical
acceptance: its centre sank to -5.408 m while roll stalled at 91.07 degrees,
with no crew ejection. The process completed and remained finite, illustrating
why a successful command or a `failed=false` receipt is insufficient.
Original recording/receipt are preserved in `tmp/flip-native-lab-v1`; the
failed native frames are packaged in `tmp/flip-hydraulic-failure-v1`.

The lab field is being corrected to a finite-depth streamfunction with zero
bed-normal flux and current tangent to its stationary surface. Added native
surface-relative depth, quaternion, angular-rate and frame-cost receipts must
be reviewed in fresh engine runs. Normal gameplay's existing capsize behavior
has not been replaced; no candidate is accepted or pushed yet.

The isolated lab has private native binaries and Saved output, but shares the
existing Content through a junction. Do not recursively delete its linked
Content or physics directories. This avoids replacing another task's running
DLLs or copying large terrain assets.

The finite-depth hydraulic v2 completed 12 s without sinking (lowest centre
offset -0.081 m; maximum tilt 37.86 degrees; final offset +0.172 m). It did not
flip. Its 15.79 FPS measurement was made during a concurrent test that exhausted
the Windows paging budget; neither performance nor its fixed-camera end view
is accepted. Subsequent recordings use a following camera/world-anchored grid
and serial processes. No other task's engine was stopped.

`pinned_breaker` v1 failed at 0.542 s: explicit drag produced 26.79 rad/s angular
speed and the full-hull event limit was exhausted. A lab-only linearized implicit
six-point drag integration (`-RaftSimFlipStableDragCandidate`) passed native
passivity/co-moving/control tests. The recorded v2 spin stayed below 2.84 rad/s,
but still failed at 0.767 s when the full-hull manifold exceeded 128 witnesses.
Its measured 2.60 FPS also fails the 20 FPS goal. These are rejected tests, not
working flip demonstrations. Normal gameplay remains unchanged.

The next contact experiment (`-RaftSimFlipCompactContactCandidate`) removes
only witnesses whose before/after deformation coordinates are convex
combinations of retained witnesses on the same contact plane. It keeps all
source-face sweeps, capacity/event limits and failure handling. Distinct
deformation velocities/planes must not be pruned. This candidate needs fresh
native tests and actual obstruction recordings before promotion.

The pruning math tests passed, but recorded pinned v3 failed at exactly the
same manifold limit and time as v2. It is not accepted and must not be
promoted or repeatedly rerun unchanged. The actual production-mesh breaking
wave v1 tilted to 78.88 degrees, recovered, and kept the crew aboard, but
measured only 9.60 FPS. This is a non-flip control, not a successful breaker.

Controlled rolling-entry v1 physically crossed 100.64 degrees at 0.175 s,
ejected five crew, settled inverted, and floated at +0.241 m centre offset.
It retained integrated pose and angular velocity instead of the timed roll.
The milder entry recovered without ejection. Neither is performance accepted
(12.02 and 9.33 FPS). Entry momentum was specified, not produced by a rapid.
Actual backbuffer frames are in `tmp/flip-rolling-port-v1-review`.

Open-water lab revisions use the normal production deformation/render path;
they have no terrain collision query. Obstruction scenes retain per-substep
source-triangle exports and full-hull CCD, without a proxy fallback. Receipts
identify this distinction. Strict receipt acceptance now enforces the user's
20 FPS floor; it does not replace visual review or normal-game regressions.

### Underwater crew revision (native v2)

Both severe rolling-entry directions completed physical inversion at 0.175 s
and 100.64 degrees, with five real ejections, continuous integrated hull pose,
and surface flotation. Three crew roots submerged simultaneously. Minimum
root offsets were -1.756 m (port) and -1.768 m (starboard); all five returned
to the local surface by the end of the 12 s run. Measured native mean FPS was
71.62 / 71.91. The mild rolling entry, breaking crest and small crest completed
without capsize/ejection, at 73.55 / 59.66 / 73.62 FPS. These are lab costs,
not South Fork full-map performance measurements.

Native tests passed both flip/load/environment tests, including downward
release momentum and resurfacing at a 300 m local datum. Actual backbuffer
frames were inspected at rollover/submersion and after resurfacing. Original
video/receipts are preserved in `tmp/flip-native-lab-v1`, and extracted frames
in `tmp/flip-underwater-port-v2-review` and `tmp/flip-underwater-onset-v2-review`.
The compact audit is `captures/native-submersion-suite-v2-audit.json`.

The lab preserves release Z and point velocity instead of instantly snapping
to the surface/current. It retains the existing event-only XY hull-clearance
placement: continuous swimmer/hull collision during release is not established
by this test. The authored PFD candidate uses 0.8 m/s2 net lift and 2/s wet
drag; it is not calibrated to a particular life jacket or body. Render refresh
uses the normal game cadence while rigid dynamics and swimmer integration use
the native 120 Hz clock. Run severe lab recordings with
`-RaftSimFlipStableDragCandidate`; do not omit this qualification.

Production promotion was rejected by automatic safety review: successful
flips use explicitly supplied initial roll momentum, not water-generated
overturning. Global implicit drag and altered normal capsize/swimmer behavior
therefore remain unpromoted. The rejected patch made no production change.
No flip commit/push has been made. Before rollout, either demonstrate a
water-generated flip and normal-game regressions, or obtain explicit approval
for a limited physical-inversion/PFD rollout with the hydraulic/collision
limitations left open. The predictive timed capsize fallback is unchanged.

## Realism scope

Qualitative reference: the [National Park Service Big South Fork river guide](https://www.nps.gov/biso/planyourvisit/upload/riverguide.pdf)
describes obstruction/crosscurrent hazards. It concerns canoe travel on a
different river and does not calibrate this raft's threshold, inertia or timing.
No measured capsize threshold or real-raft motion trace is claimed here. These
tests assess force/pose continuity, direction, non-flip controls, collision and
crew lifecycle within the game's reduced rigid-body model. They are not a
whitewater safety predictor.
