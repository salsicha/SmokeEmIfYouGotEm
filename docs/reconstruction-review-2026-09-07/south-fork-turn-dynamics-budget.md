# Troublemaker turn: bounded dynamics attribution

September27,2026. The bounded live velocity budget now closes. **Supporting
attribution only: no new playable improvement, physical acceptance or FPS claim.**

The [healthy v4 motion capture](south-fork-v4-troublemaker-motion.md) shows a
brief turn/reversal near8364m at world28..32s, after the last recorded >=5mm
ground projection. That observer cannot exclude smaller ground responses or
attribute rotation to water, paddles or other forces. Repeating it unchanged
would not answer the remaining question.

## Read-only observer

`RaftSimDynamicsStageAudit.h`, called from the existing flexible-raft adapter,
records every fixed step during world26<=t<34 seconds **only** when both
`-RaftSimEphemeralProfile` and `-RaftSimDynamicsStageAudit` are supplied. It is
disabled in Shipping builds. Existing force accumulation, queued impulses,
damping, contact modes, integration order and publication assignments are
unchanged. The observation does not feed back into simulation.

Recorded categories are retained-water load; D4 obstacle normal/friction load;
the remaining support stage (gravity, buoyancy, water drag and heave damping);
queued external linear/angular impulses; angular damping; and measured
post-integration ground-response velocity changes. External impulses must not
be labelled exclusively paddle impulses without checking their callers.
Sub-5mm ground responses remain observable. A monotonic sequence detects lost,
duplicate or reordered log rows. Logging changes timing and may change the
actual trajectory, so it cannot provide a paired FPS result or be assumed to
reproduce the packaged capture's exact path.

`physics/scripts/audit_dynamics_stages.py` independently reconstructs each
pre-contact linear/angular velocity update, checks closure within1e-9,
requires consecutive observations with continuous state, rejects invalid or
alternate-contact runs, and requires coverage of the bounded eight-second
interval. It reports signed stage contributions and absolute yaw contributions
without interpreting cancellation as absence of forces. This is a bookkeeping
check, not validation of the physical model or a diagnosis by itself.

## Preparation and verification

- Eight Python regressions pass: analytic force/damping budget, missing/duplicate/
  reordered observations, incomplete interval, incorrect integration, external
  state discontinuity, invalid parameters/contact modes, a small ground response,
  and separate force/queued-impulse contributions.
- Initial editor build succeeds42.60s; final sequence-enabled build succeeds
  **12.28s**, no compiler failures. Logs:
  `tmp/dynamics-stage-editor-build-20260927.log` and
  `tmp/dynamics-stage-editor-build-final-20260927.log`.
- The first guarded live launch **did not start**: another session's engine job
  occupied the machine; by the final check another build (`dotnet24300`,
  `cl34452`) was active. None was stopped or modified. Earlier Hance test logs
  identify the separate work; they are not South Fork acceptance evidence.
- After that work exited, the guarded live capture completed successfully.
  The packaged v4 executable was not replaced, and no map, captured geometry
  or cooked field was edited.
- A separate observer-disabled native run passes all four tests with zero
  warnings/errors: `GroundContactObservationIsReadOnly`,
  `LoadedRaftBuoyancyUsesTubeBottomDatum`,
  `PaddleCoastDownUsesLowSpeedHullResistance`, and `PassiveRaftCapturesCurrent`.
  Process exit0; report `tmp/dynamics-stage-native-20260927/index.json`.
  These are regressions, not acceptance of real river physics.

## Completed live observation

`tmp/run-dynamics-stage-live-20260927.ps1` ran once after its idle check. It
launched rebuilt editor-hosted normal FullReach at8330m, D3D12,1280x720, with
the AllForward capture schedule and observer opt-in. Experimental contact and
solver modes remained off. This is not a packaged normal-menu traversal.

The process exited0 after38.047s of healthy detail:1015 paired commits,3 holds,
246 flow preparations,zero backlog and no runtime Error lines. Twelve actual
engine screenshots were captured; inspected images007 and011 show the seated
raft/paddles/water changing with the turn. Broad foam and coarse rock flanks
remain unaccepted; two images do not establish shoreline or collision continuity.

The ledger contains964 consecutive fixed steps, world26.001021..33.987163s,
integrated8.033334s. State is continuous between every row. Maximum reconstructed
pre-contact velocity error is2.22e-16. No invalid state, alternate contact,
ground-contact substep or penetration occurs in this interval; every measured
ground-response velocity delta is zero, including responses below5mm.

| Stage | Sum of yaw-velocity changes (rad/s) |
| --- | ---: |
| Retained-water load | 0 |
| Obstacle load | 0 |
| Support | -1.287643970 |
| Queued external impulses | 0 |
| Angular damping | +1.368644803 |
| Ground response | 0 |

These sums are velocity increments, **not angles, displacement or energy**.
Initial/final yaw rates are-0.142574932/-0.061574099rad/s. Source inspection
attributes this run's support yaw to spatial tube-point water drag: gravity,
buoyancy and heave damping are vertical, while drag contributes the point-force
cross-product torque. Damping opposes the rotation. This explains the observed
budget, not whether the local water velocities or hull drag model are accurate.

Crucially, the trajectory differs from the old packaged reversal. Samples at
world26.040/28.028/30.044/32.039/34.015s advance through
stations8365.790/8368.063/8370.335/8373.159/8376.553m, while yaw changes from
32.863 to-21.880degrees. It turns but does not reproduce that earlier backwards
station segment. Do not claim the packaged reversal's cause is resolved or
change rocks, collision, drag coefficients or water fields from this alone.

## Reproduction and evidence

Existing capture parser command (no need to repeat the live run unchanged):

```text
python -B physics/scripts/audit_dynamics_stages.py tmp/dynamics-stage-live-20260927.log --report tmp/dynamics-stage-live-20260927.json
```

Raw log: `tmp/dynamics-stage-live-20260927.log`, SHA256
`4a6b5932812b8bf54fdf1620d0f3bd9f3462f835b7a1841c6968df75632605e7`.
Budget report: `tmp/dynamics-stage-live-20260927.json`, SHA256
`f7e81b6b8e1d08b85f1539de9e11ff1f082923497eda8194b739960bd7093e6d`.
Native report SHA256:
`5a034ff822a1bfb9cc1de362a403430f508728e193eddb3badfebeafd2220e32`.
Screenshots: `unreal/Saved/Screenshots/dynamics-stage-live-20260927_007.png`
and `_011.png`. Large raw logs/images remain in existing local output locations;
no duplicate media or new cooked data was created for evidence retention.

Next distinguish local sampled-flow/hull-drag accuracy from the already-closed
velocity bookkeeping, or advance the independent busy-rapid CPU bottleneck.
Do not repeat this unchanged eight-second attribution or infer source accuracy
from numerical closure. Instrumentation timing is not a20FPS qualification.
South Fork is still first unfinished; busy-rapid performance, visual fidelity,
geometry/shoreline/contact and hydraulic settling remain unresolved.
