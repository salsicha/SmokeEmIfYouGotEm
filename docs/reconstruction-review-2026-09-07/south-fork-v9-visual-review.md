# South Fork v9 actual capture: not visually accepted

Reviewed2026-09-29. This is review evidence, not a playable improvement.

Original engine video: `unreal/Saved/VideoCaptures/RaftSim_20260928-221500.mp4`.
SHA256 `6a69e308f17b66d6f4b4356184209b435302be209733225b061e44032db839a0`.
Bound replay receipt: `tmp/certified-bank-endcap-transition-live-v3-20260929-process.json`,
SHA256 `5f1e5342fd7c5de2b2db0610c05a2915665bec79ae8c924aac281c49e82f4ba3`.

Decoded2940 frames at1280x720,PTS0..97.966667s,267 exact adjacent duplicates.
Encoded cadence is not gameFPS. Inspected20/21/22/60/61/80s views:

- Boat moves relative to banks/boulders; foam outlines, spray and boat pitch vary.
- Broad opaque white foam patches dominate a comparatively low-relief surface.
  Convincing pitched breaking faces, holes and recirculating rollers remain unproven.
- Narrow diffuse vertical spray plumes recur over water and the raft interior.
  Check emitter trajectories and occlusion rather than treating these as realistic spray.
- Exposed rocks/right-bank silhouettes are conspicuously angular/block-like.
  No geographical match or surveyed underwater geometry is established by this review.
- Crew retain similar seated poses and near-horizontal paddles in these sparse frames.
  Full animation cycles, seated fit and contact need separate close-range review.

These images do not establish whole-video shoreline continuity, collision safety,
complete stroke animation or a full river traversal. Visual acceptance remains false.

## Crest dimensions: do not confuse eligibility with rendered relief

The receipt logs187 candidate rows at world10.001s.99 pass coverage/clearance;
88 do not.43 of the99 have positive raw downstream surface rise. Proposed extra
crest dimensions among eligible rows have median0.1506m,max0.4490m.
Raw/optical rise and extra dimensions are equal at the four-decimal logged precision
for all187 rows. This does not support blaming optical/raw-height mismatch at that
snapshot; it does not establish how much relief was actually selected or rendered.

`RaftSimWaterSurfaceActor.cpp` SHA256 remains the v9-qualified
`2c520382ecb5bb066a5e73149ac7378d97b80e32165a14fe58996ae8563d863b`.
Its `accepted` log field tests only coverage/clearance. Selection/deduplication,
persistent-site weights, scaling and actual mesh evaluation occur downstream.
The startup14-site/0.010m diagnostic is a DIFFERENT time; do not compare it as
though it measures final relief at10.001s. Cartesian station/lateral logs are XY,
not route chainage. No physical wave-height equivalence to real footage is claimed.

Next appearance diagnostic must pair the same time/site's hydraulic values,
selected/persisted support record, actual mesh displacement and camera view.
Do not blindly amplify waves or weaken shoreline, coverage or physics gates.

## Performance and implementation

The separate isolated v9 menu profile failed20FPS:p95102.2014ms vs50ms,
67frames>100ms. Candidate staysOFF in normal play. After a session restart,
the previously blocked source header became writable and redundant neighbor-scan
optimization was applied for fresh v10 qualification. This is not yet a validated
performance improvement. Preserve exact geometry/width/certificate checks.

Full decoded manifest, audit script/results and images remain under the task's
local visualization folder:
`C:/Users/salsi/.codex/visualizations/2026/08/20/01a01cb0-07b3-7530-a570-46d15ff22605/`.
Files: `south-fork-v9-motion-review-20260929-v2/report.json`,
`south-fork-v9-breaking-summary.json`, `review_v9_breaking.py` and
`south-fork-v9-visual-review.md`. No duplicate source video was made.
