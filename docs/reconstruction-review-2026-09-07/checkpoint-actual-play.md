# Actual-game checkpoint round trip — 2026-09-17 UTC

The guarded reset implementation now passes an actual rendered South Fork
distant-reset/return experiment. This is checkpoint integration evidence, **not
scene, geographic, visual, physical-model or 30 FPS acceptance**. Installed
modules remain unchanged while the existing SM5 regression process runs.

## Experiment and retained evidence

The new non-shipping `RaftSimCheckpointPlayReport` probe requires an ephemeral
profile and the ordinary full-reach map. It observes normal gameplay for at
least ten world seconds, 100 fresh registered GPU frames and three advancing
detail seconds in each of three phases. It calls `TryRestoreCheckpoint` to
scenario chainage 25427.6352 m, then the ordinary saved-checkpoint setter and
`TryResetToCheckpoint` to return to the recorded starting pose. The outward
discontinuity exceeds 8 km in world XY. It does not use test teleports, force
solver steps, override time, reinitialize detail, or repair failed water.

Each phase requires authoritative wet water at the raft, a valid completed
detail frame covering its actual position, and nonregressing sequence/time
within that checkpoint epoch. A no-overlap checkpoint correctly starts a new
local detail clock; old-location readbacks do not count as destination frames.
Temporary streaming-provider counts must be unchanged after each reset, and
prepared Z may change but destination XY must be retained within 0.01 cm.

Final replay `south-fork-checkpoint-play-v2-20260917`, session5241, terminal0:

| Phase | World seconds | Fresh detail frames | Detail-clock advance |
| --- | ---: | ---: | ---: |
| Initial rapid | 10.003149 | 168 | 9.766667 s |
| Distant checkpoint | 10.022315 | 256 | 9.883334 s |
| Return | 10.002058 | 182 | 9.833334 s |

Native report PASS, and the runner independently retained all12 actual1280x720
PNG images with SHA256 hashes. It requires the native Boolean result, image
presence/resolution, process completion and successful background-job resume.
The prior detail-streaming120s/eight-handoff/100-frame/60-detail-second gates
are unchanged; this new shorter discontinuity experiment does not replace them.

- Native report: `unreal/Saved/RaftSimValidation/south-fork-checkpoint-play-v2-20260917-checkpoint.json`,
  SHA256 `1490dc68a38a2c59db16af790a035511494543f81006c5e1dcc769a2e2b12522`.
- Runner/image witness: `unreal/Saved/RaftSimValidation/south-fork-checkpoint-play-v2-20260917-process.json`,
  SHA256 `7895992abc249ba1b5c537c4b309ed6895093522bce38843f25e56498fc0ddf3`.
- Final isolated project module: `tmp/checkpoint-play-project-v2-20260917/UnrealEditor-SmokeEmIfYouGotEm.dll`,
  SHA256 `204f0a737ee55ba3905b57c47c29fa5aa270f82b7c0660e25de4df878fd1f7bd`.
- Matching gameplay module remains `tmp/checkpoint-reset-gameplay-v2-20260917/UnrealEditor-RaftSimRaft.dll`,
  SHA256 `5a68bcbbf6c12faba77aeafa09bb76e947c3ecb933f3ab47bbe54091d2ea799e`.

The earlier v1 round trip also passed. Its actual load log names the isolated
project/gameplay paths; these are not claimed as normally installed binaries.
Directly inspected arrival/return images show terrain and water, but distant
banks remain bare and the rapid has artificial-looking trough/crest shapes.
The same startup candidate retained all24 unskipped1280x720 images, exit0,
with terrain, water and colored crew present in image000. Images000 and023
were inspected directly. Broad froth, angular water/bank transitions and crew
presentation remain unaccepted. Startup runner witness SHA256
`595848e84c36699c3d09d71a8d974bb1b7fac315f9c35f0d669783047ca7bb29` at
`unreal/Saved/RaftSimValidation/south-fork-checkpoint-reset-startup-v1-20260917-process.json`.

Final project unity compile/link succeeded. Eight native checkpoint/compatibility
tests pass with zero warnings/failures/not-run, session11707/PID3180 terminal0;
`tmp/checkpoint-play-native-v2-20260917/index.json`, SHA256
`6903100ecb080174041f4f8c9b962e9f9aac3817fa4cb1b1c28e8cff8aa88e74`.
Focused Python suite:92 PASS. Native checks ran concurrently with the final
render replay; neither is a performance measurement. Optional installed engine
Toolset Python initializers log missing AgentSkill/PythonTestRunner attributes
in game mode; this is not a warning/error-clean whole-engine or release audit.

## Background jobs and hydraulic snapshot

All replay runners resumed precisely owned cook11316, SM5editor9976 and
workers31736/36256, each resume status0. Live CPU advancement was rechecked.
The original SM5 session9319 is still running; all63 witnessed shader inputs
retain their hashes. No restart, shader edit, installed DLL replacement, or
claim of regression success. Gameplay947f5a53... and projectf11c1bc6... remain
installed. Candidate delivery still requires safe installation and ordinary-play
revalidation after that job becomes terminal.

Same hydraulic cook40601/PID11316: completed1550s/local19000 state audit PASS
and all86,720 artificial bank-face cells exactly dry. Maximum depth4.517990m,
speed7.257709m/s, volume3,007,922.915751m3, max per-step residual1.707900e-8m3.
Outflow86.619794 versus inflow45.306955m3/s: **not settled**, no promotion.

- `tmp/control-ablation-1550s-state-v1-20260917.json`, SHA256
  `307600c198132fea8a7cadfafd51d790d196e2bda02f499e56fb5a448bc98b76`.
- `tmp/control-ablation-1550s-banks-v1-20260917.json`, SHA256
  `9c3fc2e779718f80fe82117633635ad00d7c0a49592fee20cc7dba15fb879ee4`.

Next1600s/local20000 needs both audits once its complete marker exists.
Last ordinary26.784840FPS/p9543.5724ms still FAIL30. Coupled nonlinear water,
convincing flowing/breaking/frothy water, evidence-consistent terrain/boulders/
collision, source closure, normalization/regressions/release, Colorado then
Pacuare then Futaleufu, Chilko/Zambezi/all-scene water and crew remain open.
Troublemaker remains a rapid within South Fork, never a separate menu scenario.
