# Crew occupancy and normal-play load correction

Validation completed 2026-09-24 UTC. Occupancy now follows the swimmer roster
in normal play: ejected seats stop contributing mass/actions, reflip alone
does not restore swimmers' loads, and reseating/checkpoint restoration does.
Repeated ejection preserves existing swimmers and rescue clocks. This corrects
physical participation, not measured body geometry or full river acceptance.

Editor build `tmp/crew-occupancy-editor-v2-20260924.log` reports success.
The default, unflagged native selection
`RaftSim.Crew.+RaftSim.M5.CrewAvatarPoseProduction` passes **7 tests, 0 failures**
in 10.23 seconds. Authoritative report:
`tmp/crew-occupancy-default-native-v1-20260924/index.json`; matching `.log`
is retained. Process exit alone was not used as the acceptance check.

The new occupancy fixture tests actual impulse response and reports occupied
crew / integrated body mass in kg: 385/605, 235/455, 235/455, 310/530,
0/220, 0/220, 85/305, 385/605, 385/605. Hull buoyancy reference remains605kg
throughout. The stages cover partial ejection, duplicate/no-op ejection,
individual reseating, capsize, actual reflip, guide reseating and checkpoint
restoration. Unknown physical seat ids are rejected; malformed combined mass
fails closed. Existing rescue clocks and active rescue phase survive duplicate
ejection. This is a controlled native fixture, not normal-scene motion evidence.

Game build `tmp/crew-occupancy-game-v1-20260924.log` succeeds in196.77s.
The existing unrelated detail-source `Current` initialization warning remains.
Production rescue/reentry test `RaftSim.M5.RuntimeRescueLoop` succeeds with one
warning, zero errors in13.7683s; see
`tmp/crew-occupancy-rescue-native-v1-20260924/index.json`. It reaches real
ReadyForReentry and explicitly reseats the swimmer. The warning is the engine's
`r.MotionVectorSimulation` render-thread-safety warning, not suppressed.
The prior fixed-name rescue screenshot was preserved as
`tmp/M5_RescueProduction-before-occupancy-20260924.png` before this tank fixture.

## Normal South Fork motion and cost

Fresh process receipts under `unreal/Saved/RaftSimValidation/` share prefix
`south-fork-crew-occupancy-` and suffix `-v1-20260924-process.json`: `cost`,
`motion`, and `default-cost`. All confirm normal FullReach/full_descent launch,
four solver lanes, unchanged solver archive, exit0, and successful exact-process
cook suspend/resume. No contact-review flag, camera relocation, shadow override,
field promotion or nonlinear activation. These are editor-hosted normal game
runs; the Game target was rebuilt separately, not packaged-release acceptance.

Both overboard cost and motion logs contain completed physics samples at3s/9s:
one swimmer,310kg occupied crew,530kg integrated body,605kg buoyancy reference.
This verifies actual integration telemetry, not only an issued input command.
Capture guard tests pass for eight invalid mixes and unchanged default input;
the existing paddle/high-side capture guards also pass.

Independent900-frame cost runs, elapsed samples60–840 inclusive, confirmed
scope offset1, unchanged30FPS/p9533.333333ms target:

| Input | Mean ms | p95 ms | Max ms | Short first-pool gate |
| --- | ---: | ---: | ---: | --- |
| One overboard passenger |22.655119|31.0470|34.2002|PASS |
| Ordinary, no injected input |23.207030|31.3873|37.1992|PASS |

Reports: `tmp/crew-occupancy-frame-v1-20260924.json` and
`tmp/crew-occupancy-default-frame-v1-20260924.json`. CSV hashes respectively:
`8f90d473f7a9e9bdc4f0bf196e2a5d1bf1707bfb1281be704b4f57208100b2e8`,
`30a99e448a650c69e56c37e0b5eff7637ef34f736e758dce4423b8314640ada8`.
Different input workloads do not establish an isolated speedup or full-route
performance. Earlier high-side over-budget results remain valid open evidence.

Motion produces24 stills and
`unreal/Saved/VideoCaptures/RaftSim_20260923-184106.mp4`, SHA256
`f0bc6849d27cc45fde039df28834378b1997dcdcfd3d99308667465615972d45`.
Full decode succeeds:463 frames through15.4s,18 exact adjacent duplicates;
`tmp/crew-occupancy-motion-v1-20260924/report.json`. Original3s/9s frames were
inspected: changing water/boat views, river progress0.12→0.13km, one incident
and one swimmer, active rescue target at1.5m. The swimmer is outside the normal
camera view; these frames do NOT prove swimming animation, visible detachment,
continuous limb clearance, obstacle contact or shoreline stability. Encoded
video frame rate is not the performance measurement. Smooth water and coarse
canopy remain visible; this is not geographic/hydraulic acceptance.

## Remaining

The inertia remains the documented shape-based scaling,
not a newly measured articulated-body inertia or seat-COM reconstruction.
Reconcile physical/visual seat placement and whole-body high-side transitions,
then qualify swimming/reentry animation and full-route performance. Do not mark
South Fork accepted or advance the river queue on these tests.

Preflight found only the existing hydraulic cook36692, not a competing engine
or build. No cook was started, stopped or promoted; installed fields, captured
sources and nonlinear-mode choice were unchanged.
