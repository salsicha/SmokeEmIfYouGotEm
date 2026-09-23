# Rigid crew paddles in normal play

Delivered 2026-09-23 UTC. Scoped crew-equipment correction, not river or full
character acceptance. The previous turn closed the unproven water-filtering
trial. Further scalar foam tuning is not a substitute for coupled breaking
physics; this increment addresses a separate concrete normal-play defect.

## Correction

The project-owned paddle previously used independently authored endpoints as
a stretchable limb: its shaft was about83 cm at rest, about108 cm in the base
stroke, and about121 cm during high-side. Recovery also changed shaft length.
The normal shared pose evaluator now constrains it to120 cm from T-grip centre
to blade root in every visible-paddle action. The existing blade extends39 cm
beyond the root: total159 cm, approximately63 inches. This is an authored
equipment choice, not an exact replica or measured river geometry. Commercial
63-inch sizes exist ([manufacturer specifications](https://www.nrs.com/nrs-pt-guide-paddle/pgan));
no third-party artwork or mesh was copied.

The solve retains the authored top position, blade-root height, horizontal
direction, and each hand's distance along the shaft. It solves horizontal reach
on the constant-length sphere, then supplies the same new grip points to the
body and equipment. Recovery clearance and planted-stroke timing are retained.
No extra mesh layer, draw call, source geometry, physical impulse, water field
or solver mode is introduced. The authored idle hands still rest on the shaft;
their appearance in a rear screenshot was not proof of broken grip anchoring.

The first candidate simply normalized the endpoint vector. Native verification
correctly rejected it because that reduced recovery lift: two of three suites
failed. That report remains retained. The final solve preserves blade height
instead; the existing recovery threshold was NOT relaxed.

## Verification

- Editor and standalone Game rebuilds pass (final18.27/37.32 s). No packaged
  traversal or clean all-platform SDK claim; existing absent platform SDK
  warnings remain in the native logs.
- Three native suites pass, no warnings/failures/not-run: RigidPaddleAcrossActions,
  VestFollowsTorsoNotHead, and existing M5.CrewAvatarPoseProduction. The new test
  checks1616 visible poses: eight actions, two seat sides,101 cycle samples,
  plus phase periodicity, finite-segment hand attachment, outboard blades,
  rest grip distances and unchanged catch/recovery requirements.
- Actual production-raft component checks cover five crew × eight actions.
  All40 shaft measurements are120 cm within3e-14 cm; maximum rig grip-anchor
  error4.12e-14 cm. These are anchor/component measurements, not skin contact,
  cloth or finger-surface collision certification.
- Eight renderer-produced views retained. Idle-side, forward-rear and high-side
  side originals inspected. Equipment remains attached; high-side/body/foot
  fit and garment quality remain unfinished. The posed views do not prove
  continuous reentry or capsize animation.
- New capture-only `StartupPaddle` invokes the existing normal AllForward
  crew command. It is rejected for ordinary FPS captures and defaults OFF;
  four new/existing PowerShell guard suites pass.13 frame-parser tests pass.

## Normal launch, motion and measured cost

The rebuilt editor-hosted D3D12 game ran FullReach/full_descent from its ordinary
start, with NO review-station override or candidate rendering/physics flag.
Four solver lanes,1280×720. Explicit crew input was used only for motion review.
The24 stills and movie show rest-to-stroke transition, crew pose changes, moving
water and downstream HUD progress from roughly0.12 to0.15 km. Original movie
frames3/6/9/13 s were inspected; this is not calibrated stroke/water-force
synchronization or full character-motion acceptance. The recording fully
decodes467 frames over15.533333 s,23 exact adjacent duplicates. Encoder cadence
is NOT engine FPS.

Movie: `unreal/Saved/VideoCaptures/RaftSim_20260923-135944.mp4`.
Decode: `tmp/rigid-paddle-motion-v2-20260923/report.json`.
Posed review: `tmp/rigid-paddle-views-v1-20260923/report.json` and eight PNGs.

Separate ordinary900-frame run has no capture, paddle injection or diagnostic
override. Rows60–840 inclusive give mean23.904421 ms and p9532.8541 ms:
**this short first-pool window passes33.333333 ms**. Frame-time mode is confirmed
from its engine log, scope offset1. There is no matched baseline or causal
speedup claim; it does not supersede rapid/full-route failures or establish
sustained30 FPS. Report: `tmp/rigid-paddle-cost-v2-20260923.json`.

All build/native/posed-view/game/decode jobs are terminal. Both ordinary-game
receipts confirm exit0/no timeout and successful guarded suspension/resumption
of sole cook36692, retaining archive63e9e592…f1d0365f. The original cook remains
live, not restarted. Captured data, terrain, collision, installed4950 fields
and nonlinear OFF are unchanged. South Fork remains unfinished; Colorado,
Pacuare and Futaleufu stay queued. Full crew fit/reentry and release work remain.

The [receipt](rigid-crew-paddle.json) binds implementation, both native results,
builds/binaries, component audit, motion, cost and parser evidence. The component
audit's finite values were additionally checked after adding explicit NaN
rejection to the script; the numerical run was not represented as a rerun.
