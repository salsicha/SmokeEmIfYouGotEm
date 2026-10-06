# South Fork water feature controls and engine integration

October 1, 2026. The requested hole, eddy and froth demonstrations now use
production raft forces and shared authored current primitives in Unreal.
Those primitives are also enabled in the normal South Fork FullReach scene.
This is an incremental delivery, not geographic, hydraulic or visual acceptance
of the river, and not a newly cooked standalone game.

## Recorded controls

The recordings are actual Unreal backbuffer frames. The raft is a 605 kg
production reduced rigid body with distributed tube water forces, no paddlers
and no scripted pose, suction force or trajectory. These are authored training
controls, not surveyed rapid geometry or measured CFD.

- Hole: the surface return current and submerged downstream leg hold the raft
  within approximately 12 cm of downstream travel over 12 simulated seconds.
  Pitch varies approximately 4.6 to 6.6 degrees. The rendered breaking lip uses
  the game's lip profile. Its overturning skin is presentation geometry, not a
  resolved three dimensional fluid volume or independent collision surface.
- Eddy: actual foam tracers circulate approximately 2.25 to 2.69 times over
  30 simulated seconds. The raft turns approximately 71 degrees, then washes
  out downstream. This demonstrates turning, not indefinite retention or a
  complete eddy entry and exit acceptance test. The control obstacle is not
  registered to the raft's separate dynamic collision solver.
- Froth: additional crest-born patches accumulate and transport through the
  same hole current, fade over time and coexist with native Niagara spray.
  Surface foam does not add an independent boat force. Entrained bubble
  volume, buoyancy reduction and realistic opaque froth depth are not resolved.

Control animations and original recordings are retained at
`tmp/feature-capture-hole-v8`, `tmp/feature-capture-eddy-v8` and
`tmp/feature-capture-froth-v8`. Each `capture.json` identifies the original
recording, hashes and selected times. Every APNG frame was checked against
its decoded native source after resizing; repeating playback is not a
seamless simulation loop. The original motion receipts are
`unreal/Saved/WaterFeatureDemo/shared-{hole,eddy,froth}-v8.json`.

## Shared current in normal South Fork

`RaftSimWaterFeatureKinematics.h` supplies compact hole and eddy primitives.
Actual Cartesian boulder footprints orient the authored controls. Only the
normal `L_SouthForkAmerican_FullReach` map enables this adapter path;
other rivers and review maps do not inherit it. This fixes an earlier
source-path condition that had left the playable binding inactive.

Foam now receives a separate GPU transport input containing the shared
surface current. The liquid depth, wet mask, pressure and momentum inputs
remain unchanged. The public boat sampler consumes the retained current
paired with the displayed GPU foam frame, rather than a newer independently
sampled grid. Its submerged hole leg remains relative to that surface current.
Dry carrier support remains authoritative and expired weak owners fall back
to the ordinary current.

The flat, constant-depth hole control has zero added depth-integrated flux,
and the isolated eddy primitive uses a streamfunction. These local properties
do not establish global conservation for overlapping features, varying
depths, curved banks or the clipped real river. Source survey, riverbed,
captured evidence and cooked liquid fields were not replaced.

The normal South Fork transmission material also gained the existing game's
advected froth micro-normal treatment. Other material roots, foam coverage,
water displacement and collision were preserved. The original asset backup
and graph-change receipt are in `tmp/south-fork-playable-froth-normal-v1`.

## Native verification

The rebuilt editor passed all eight regressions, without warnings, in
`tmp/shared-feature-native-v13/index.json`. They cover the shared primitive,
current-oriented geometry and support, unavailable/dry water, weak transport
ownership, actual public boat coupling, GPU foam transport and froth normals.

In the GPU transport test, baseline foam moves approximately +1 m in one
second; reversed surface transport moves approximately -1 m while all liquid
state components remain exactly unchanged. An identical explicit transport
matches the default baseline exactly. The foam mass error is approximately
8.25e-7 in the test's units. This is a numerical control, not full-map acceptance.

Fresh normal-configuration South Fork captures both exited successfully:
`unreal/Saved/Screenshots/shared-southfork-v13-play_000.png` through `_011.png`
and the corresponding `shared-southfork-v13-breaking` series. Reviewed frame
006 from each. Gameplay animation and original recording are in
`tmp/feature-capture-southfork-v13-play`; its 25 frames contain no adjacent
duplicate captures.

The actual loaded-map public sampler audit found zero surface-current error
relative to the retained published evaluator and zero dry probes becoming wet:
394 wet gameplay probes and 395 wet close-up probes. These API checks do not
independently establish global flow accuracy, collision clearance or visual
attribution. The separate UV3 vertex audit still reports approximately
2.28 m/s maximum difference from the paired field, without opposed vertices;
mesh interpolation is not exact pointwise equality. The material's fully owned
interior and the boat sampler consume the paired field directly.

## Measured frame times

Both latest editor-hosted game profiles exited zero with no runtime errors and
no quality or solver override. Each captured 600 frames, auditing the middle
540. The normal Boot to menu to FullReach launch averaged 36.8184 ms
(approximately 27.2 FPS), with 46.0805 ms p95 and no frames over 100 ms.
It passes the user's 50 ms p95 budget in this sample.

The dense section starting at station 8310 averaged 47.2031 ms
(approximately 21.2 FPS), but its 59.4486 ms p95 misses the target. Four frames
exceeded 100 ms, with a maximum of 194.5657 ms. Average FPS alone does not
qualify this section. Receipts are
`unreal/Saved/RaftSimValidation/south-fork-shared-features-v13-{menu,8310}-frame-audit.json`.
These are not standalone packaged results and do not establish the cause of
timing differences from earlier runs. Profiling used workload guards, not
continuous monitoring of every competing process.

## Remaining acceptance work

The reviewed full-map close-up still has broad, flat, overly opaque white foam
patches. Micro-normal mathematics passing does not mean that appearance is
accepted. Refine the foam's breakup, thickness and lighting using actual engine
views, without inventing another disconnected flow field.

Calibrate placement and strength against rapid evidence; demonstrate eddy
entry, turning and escape with the real boat; qualify boulder collision,
shoreline stability and continuity over sustained motion. Improve dense-section
frame cost and hitches while preserving visual and kinematic behavior.
Rebuild and validate the standalone game before claiming
packaged delivery. South Fork remains unfinished; do not advance the queue
on the strength of these controls alone.

## Eddy return-current correction, 2026-10-01

The previous isolated block demo had two disjoint circulation ellipses. On
their shared centreline both perturbations vanished, leaving downstream
through-flow directly behind the block. This was the wrong wake topology.

`RaftSimEddyDemoBoundary.h` now differentiates one antisymmetric compact wake
streamfunction and retains the existing boundary-distance streamfunction
mask. The inner wake flows upstream, turns outward at its upstream head,
and joins the downstream outer branch. The block remains bed-connected;
water triangles and foam texture support remain excluded from its footprint.
The exact symmetry axis is a separatrix, not an invented side-selection force.
The demo starts slightly off that axis within the obstacle's downstream shadow.

The private native engine passed `RaftSim.Demo.EddySolidBoundary`: zero
current on solid faces, the return/head/outer-branch signs, 132192 tracer
steps without a solid crossing, finite-difference divergence below 1.35e-6/s,
and the existing full-hull contact impulse control. Native report:
`tmp/eddy-return-native-test-v1/index.json`.

Two actual native rendered runs used the production empty hull, the shared
authored current, 120 Hz force integration and no paddle or trajectory forcing.
Both mirrored entries travelled 8.9965 m upstream, reached their upstream
turn at 8.2083 s, entered the downstream outer branch at 9.725 s and passed
the wake's downstream end at 15.4667 s. Maximum upstream boat speed was
1.9037 m/s. The reflected motion matches to floating-point precision at
these measured events. Neither run crossed the block or required a contact
impulse. The tested motion does not prove arbitrary entry or escape behavior.

Small audit receipt: `eddy-return-native-v2-audit.json` alongside this document.
Actual video and 16-second review animation:
`tmp/eddy-return-path-v1-review/{engine-recording.mp4,animation.png}`.
Reviewed native first/turn/exit frames; packaging verified 65 selected frames
with zero adjacent duplicates and unchanged decoded pixels before resizing.
The capture is a repeating review clip, not a seamless fluid loop.

The block demo's full-hull export/review path still has substantial render
cost; the mirrored recording logged 61 source frames over 16.844 seconds.
Encoding at a nominal video rate is not proof of 20 FPS. No performance
acceptance is claimed. Loaded crew, captured hydraulics, ordinary South Fork
eddy placement/transport and packaged full-map validation remain unverified.
This patch changes the non-shipping isolated eddy demo, not the ordinary
South Fork feature primitive or the gated flip candidates. Nothing committed
or pushed as part of this correction.
