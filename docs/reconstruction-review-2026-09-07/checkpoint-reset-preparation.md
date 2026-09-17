# Checkpoint reset destination preparation

2026-09-17 UTC. Implemented in source and verified in isolated native modules;
not installed or accepted as rendered ordinary-play behavior yet.

## Change

The prior session-start path activated destination terrain and selected wet
Cartesian water, but `ARaftSimRaftActor::ResetToCheckpoint` moved the raft without
either preparation. Both the automatic failed-rescue path and Restart Run used
that unchecked reset. A distant reset could leave contact queries at the old crop.

The scenario run manager now binds a weak UObject-owned native preparation
delegate on its raft. Before a reset commits, this callback activates destination
terrain using the existing temporary streaming-source policy, then uses the
existing transactional Cartesian packet selector and wet-destination check.
It rejects missing required water initialization and ambiguous configuration.
Legacy static ribbon/tank hydraulic behavior is unchanged; this does not claim
a new arbitrary-distance legacy ribbon reseeding implementation.

The raft makes a local copy of the requested transform, rejects reentrant resets,
and changes no saved checkpoint, crew repair state, actor pose or authoritative
body velocity until preparation succeeds. A configured provider that disappears
fails closed; a tank that never installed a provider keeps its existing reset.
The Blueprint-callable void entry points retain their signatures and route through
the same native bool-returning path. A rejected immediate checkpoint setter keeps
the prior saved checkpoint. Restart Run only clears progress/score state after
a successful reset. Session-start progress likewise requires a successful move.

The plugin has no reverse dependency on project code. Terrain-source lifetime
and player grid/range policy are unchanged. Cartesian reset launch height uses
the existing wet surface plus40cm, with unmodified XY and destination-current
velocity. No physics cutoff, teleport fallback, shoreline clamp or source-data
edit was introduced. Startup retains its explicit checks and the reset hook
revalidates that destination; its additional startup cost is not measured yet.

## Verification and limits

- Eight native tests PASS, zero warned passes/failures/not-run: new
  CheckpointResetPreparation; existing CartesianCheckpointDestination (six real
  full-river destinations and transactional dry rejection); CheckpointDestinationSources,
  StartupWaterAfterSessionRestore, ReconstructedSessionContracts,
  RunProgressDistinctFromRapidHydraulics, CoordinateFrameProgress and
  ShorelineCompactUpload. New native checks cover refused/successful preparation,
  old-pose retention, prepared height, saved-checkpoint retention, reentrancy,
  provider loss and unchanged never-configured legacy reset.
- `tmp/checkpoint-reset-native-v2-20260917/index.json`, SHA256
  `d46a57cf588c36e2c0c6cb7b2dd77e97b7a2946b2222a404236f8cbfa3f31260`.
  Session77358/PID26152 exits0. Bootstrap logs confirm both candidate module paths.
- 90 focused Python checks PASS: six checkpoint source-order/lifetime contracts
  and the existing startup/preview/retention/review-start suite. The first test
  collection hit Windows CP1252 decoding; explicit UTF-8 source reads fix it.
- All five gameplay unity units plus the project unity unit compile/link; all607
  local dependency references predate their objects. The gameplay import library
  is generated inside the candidate directory and the project links against it.
  A pre-existing C4701 warning in DetailFullRouteCoverage remains recorded in
  compile-4.log; there are no native automation warnings. It is not a clean
  whole-project warning audit.
- Initial compilation correctly rejected stale generated-header line mappings.
  Unreal's header tool regenerated one file with warnings-as-errors, terminal0.
  Its first explicit-log invocation hit a duplicate-writer collision; rerunning
  with `-NoLog` and a fresh redirected output succeeded. These failures are retained,
  not passed checks. UHT log `tmp/checkpoint-reset-uht-v3-20260917.log`, SHA256
  `f58d7c84ced10c5ca758f61a5d1856c55235f80a06c9e626c08dd5f867a4d8c4`.

Candidate modules (both required together):

- `tmp/checkpoint-reset-gameplay-v2-20260917/UnrealEditor-RaftSimRaft.dll`, SHA256
  `5a68bcbbf6c12faba77aeafa09bb76e947c3ecb933f3ab47bbe54091d2ea799e`.
- `tmp/checkpoint-reset-project-v2-20260917/UnrealEditor-SmokeEmIfYouGotEm.dll`, SHA256
  `05bb122721a9fce6ec60bc4fbc4d8cb3ae56630568af5387fcb17ab052eae73b`.

Installed gameplay947f5a53... and projectf11c1bc6... DLLs remain unchanged.
The same SM5 shader job9319/PID9976 is live, with all63 captured shader-input
hashes unchanged. Do not replace its installed modules or edit its shaders.
At01:19:44 UTC it logged900.11s without a worker state change, listing12 pending
jobs across two workers. PIDs31736 and36256 were independently verified live,
each with2098.328125 CPU seconds; that warning is not a terminal result. Keep
the original job and observation handle; do not restart it on the timeout alone.
Use the existing bootstrap with both candidate gameplay and project arguments
for isolated checks. Actual World Partition distant reset/return, post-reset
detail-domain/frame continuity, first-frame capture, safe installation and
ordinary30FPS profiling remain required. Native helper tests do not prove them.

## Hydraulic1500s checkpoint

Same cook11316 reaches1500s/local18000. State and all86,720 exact-dry artificial
bank-face checks PASS. Maximum depth4.528772m, speed7.166893m/s,
volume3,009,954.646m3, maximum per-step conservation residual1.707900e-8m3.
Outflow85.275663 versus inflow45.306955m3/s: **not settled**, not promoted.

- `tmp/control-ablation-1500s-state-v1-20260917.json`, SHA256
  `b8de505756745b552d00f89fa97d3bb4ea220bdef95a6a44050fcb9a3807dcc5`.
- `tmp/control-ablation-1500s-banks-v1-20260917.json`, SHA256
  `6c6a1245bb9d5847c0866d7876fac95d56099a838b84556fc028e913e6298e92`.

Next1550s/local19000 needs both audits. The full South Fork reconstruction,
compatible nonlinear water, convincing waves/froth,30FPS, source closure,
normalization, Colorado -> Pacuare -> Futaleufu, all-scene water including
Chilko/Zambezi, crew and release queue remain open. Troublemaker remains a
South Fork rapid, not a menu scenario.
