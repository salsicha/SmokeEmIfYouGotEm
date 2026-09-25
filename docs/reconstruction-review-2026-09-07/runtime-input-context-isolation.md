# Runtime input context ownership repair

## Runtime rebind ordering follow-through — September 25

The runtime key-rebind path still called UE's swap-removing `UnmapKey` directly.
It now uses the same order-preserving removal helper as startup cleanup. Native
coverage rebinds PaddleStroke K -> L -> J and checks every surviving full mapping
record and position, negative S binding, other pawn context and source asset.
This checks mapping presence/order, not physical hardware dispatch (despite the
fixture's overly broad "dispatched by mapping" assertion label).

Editor build succeeded (82.04s); Game build succeeded (52.76s). Native
`RaftSim.Input.PawnContextIsolation`: 1 success, 0 warnings, 0 failures.
Report `tmp/runtime-rebind-order-native-20260925/index.json`, SHA256
`779b3b6a55855c238a6bd4611e05c8fb3166604d9d7358c931d0f91958625def`.

Normal v7 staged executable now has SHA256
`5246445253bdca36b1076643235ab21639d5b6ba719cfb585d51e4d4e3d1ad85`.
Previous executable was preserved and verified as
`SmokeEmIfYouGotEm-pre-runtime-rebind-order-20260925.exe`, SHA256
`f83b3dfb780191526a4c92d615fe9b44471c423635291e60bfe542ba0d60905d`.
No cooked content, geometry or hydraulic field changed.

Normal Boot/menu StartScenario -> FullReach, without direct-map/scenario override,
completed 300 post-travel CSV frames. World-10s telemetry reports wet raft drift
at 1.368m/s and zero ground points/penetration. Full log has no `Error:`, fatal,
blank-action or null-action matches; shutdown closes the engine and object
subsystem. The process is absent. Engine requested status 0, but the OS process
exit code was not captured; shell return from launching the GUI is not that code.
Log `tmp/runtime-rebind-order-normal-stage-20260925.log`, SHA256
`8984b82dac67f06d295d5b1e2d300b2c2f1fe2cdd700aee133b1c12db0213b72`.

This delivers a normal-play code repair, not a visible river reconstruction or
performance improvement. Physical input dispatch, repeated real respawn/travel,
visual water/geometry and the 30FPS acceptance gate remain open. No duplicate
cook or engine validation process remains running.

2026-09-24. Fix implemented and packaged GC stress checked; full input/travel
regression and release installation remain open.

The previous longer menu-launch run failed GC verification because the cooked
IMC_RaftSimDefault asset had been modified by each pawn constructor to hold
pawn-owned runtime steering/recording actions and negate modifiers. Root-set
cooked assets cannot safely reference these ordinary runtime objects.

ARaftSimGuidePawn now leaves the loaded asset untouched in its constructor.
Runtime action default subobjects still originate there. PostInitializeComponents
duplicates the complete configured mapping context under the gameplay pawn,
marks it transient, then applies the existing mouse-look removal and rescue,
steering and recording fallback mappings to that private copy. DuplicateObject
preserves profile overrides/context settings and duplicates instanced children;
the copy is held by the existing UPROPERTY. No GC checks are disabled and no
input action is intentionally removed beyond the pre-existing raw-mouse rule.
Construction of the other guide components was moved intact into a helper.

Game build passed73.04s. The separately named
`SmokeEmIfYouGotEm-InputIsolationReview.exe` sits beside the original v7 and
previous review executable, both preserved. Uses unchanged v7 cooked content.
Binary SHA256: `b5ef92e5a3f2bfca7973835cf49ddcdee0793b28f67b2dbfab187720445a71bb`.

## Packaged forced-GC result

Default boot, existing menu StartScenario handler, no direct map/scenario
override; ephemeral profile,1280x720D3D12offscreen. Requested
`gc.CollectGarbageEveryFrame 1` and verbose GC logging;180CSVframes bound the
run, not a frame-performance assessment. Exit0. Log confirms boot->FullReach,
the GC setting,181actual `Verify GC Assumptions` checks, raft drift while wet,
and clean shutdown. No previous Disregard-for-GC fatal recurred.

Log: `tmp/input-isolation-forced-gc-20260924.log`, SHA256
`56bc26017f3e383a0369704d317921be2d3192d45997470ba7a8bd2c45ca100a`.
Build log: `tmp/input-context-isolation-game-build-20260924.log`.

Next: native assertions for asset immutability and independent pawn contexts,
mapping/control coverage, proper removal of the private context on EndPlay,
respawn/travel and sustained ordinary-GC play. Existing rescue checks are in
M6GameProgression and M5ProductionQuality. Do not equate this stress pass with
input dispatch, visual motion, 30FPS, full river acceptance or finished release.
The normal staged executable still predates this fix until final integration.

## Isolation regression and teardown implementation

EndPlay now removes the private context from the weakly remembered subsystem
that actually registered it. This does not depend on GetController still being
available after unpossession, and does not remove another pawn's context.
Editor build passed68.72s. Native `RaftSim.Input.PawnContextIsolation` passes,
1success/0warnings/0failures, report
`tmp/input-context-isolation-native-20260924/index.json` and adjacent log.

The test loads the source asset, spawns2actual game-world pawns and initializes
their components, then asserts distinct pawn-owned transient contexts, source
mapping immutability, retained rescue and independent mouse-look bindings,
runtime steering/recording action ownership, successful positive paddle rebind,
retained negative paddle key, and unchanged second-pawn mappings. This proves
binding configuration/isolation, not physical input dispatch or EndPlay removal
from an actual local-player subsystem. Teardown implementation still needs that
integration check, followed by rebuild/integration of the normal game binary.
The earlier packaged181GC-check executable predates EndPlay cleanup; do not
attribute that test to the newer binary. No processes from this test remain live.

## Subsystem teardown and normal-stage integration

Extended native fixture registers both contexts with a real
UEnhancedInputLocalPlayerSubsystem/UEnhancedPlayerInput pair. With no pawn
possession, Destroyed EndPlay removes only the first context and clears its
remembered owner; LevelTransition EndPlay removes the second. Source mappings
remain unchanged. Report `tmp/input-context-teardown-native-v2-20260924/index.json`:
1success,0warnings,0failures. Earlier fixture runs exposed an incorrect API
name and invalid LocalPlayer outer; corrected to the controller property and
engine-owned LocalPlayer, without weakening assertions. Editor rebuild13.18s.

Game build passed49.56s including lifecycle cleanup. Installed at the existing
stage's normal `Binaries/Win64/SmokeEmIfYouGotEm.exe`; original first copied to
`SmokeEmIfYouGotEm-pre-input-lifecycle.exe` and hash-verified before replacement.
Installed SHA256 `47216065481e65b35ca19ef67118e2dc0c0523219bde5f00d093ef066946b6a7`;
backup SHA256 `f54541b0e5d429e8a9dec598a6f6f2ea788d7ac45b3cbabd8edd1310780d0f30`.
No cooked content was replaced; this is incremental code integration, not a
fresh release package. The final test-fixture-only outer correction is in the
editor test binary, not this Game binary; production lifecycle code is identical.

Normal installed executable, no map/scenario override, default boot->menu
StartScenario->FullReach, ordinary GC settings,1800frames: exit0. Log confirms
in-play GC assumptions verification at13:35:57, about60s after map travel,
subsequent wet raft drift and clean shutdown. This crosses the prior natural
GC crash point. Log `tmp/input-lifecycle-normal-stage-soak-20260924.log`, SHA256
`1b200cbfd9b74cbde5c41269815eba8b556bc53998e36dee59bdb28ed1219a00`.
No rendering/cook/build ran concurrently. This is a scoped crash/lifecycle pass,
not full traversal, physical input dispatch, visual-water or30FPS acceptance.
Repeated real respawn/travel and final release staging remain to be checked.

## Legacy null mappings and stable input priority — September 24

The previous normal-stage log contains four Enhanced Input warnings for blank
actions on RightMouseButton, LeftMouseButton, Gamepad_LeftTrigger and F9.
These are stale entries alongside the runtime replacements, not evidence that
the replacements themselves are null. The private-context initializer now
removes null entries only for a key with an available replacement action. Valid
same-key bindings, source assets and unrelated unresolved mappings are retained.

UE 5.8 `UnmapKey` uses `RemoveAtSwap`. A stronger native fixture exposed that
the pre-existing removal of Mouse2D/MouseX/MouseY look mappings could reorder
surviving bindings too. Both startup removal paths now restore the exact
surviving mapping order and full mapping records, including modifiers. No
runtime priority, source asset or profile override is deliberately rewritten.

The fixture supplies duplicate null entries on all four keys, an unrelated
null F8 entry, and ordered valid F9/F10/F11 marker bindings. It checks repaired
keys have actions, every repaired null duplicate is gone, unrelated missing
actions remain visible, valid same-key entries/order survive, and the original
template remains unchanged, alongside the existing ownership/rebind/teardown
checks. The initial ordering regression failed in
`tmp/input-stale-order-native-20260924/index.json`; this failure is retained.
The assertion was not relaxed: the raw-look removal path was corrected.

The first cleanup-only Game build (105.49s) ran through the normal staged
boot/menu-handler/FullReach path for 900 post-travel frames, exit 0, no blank
action warnings, with wet raft drift. This version predates the full ordering
correction and is not its validation. Log:
`tmp/input-stale-mappings-normal-stage-20260924.log`. No physical input delivery
or scene/water/performance acceptance is inferred from this result.

The corrected native test passes: 1 success, 0 warnings, 0 failures,
`tmp/input-stale-order-v2-native-20260924/index.json`, SHA256
`36ce03844019f7452570e9a1041e98ed1cba147da57fb6ef3aaff1b6297f5072`.
Editor build 12.49s; Game build 27.76s. The final normal-stage executable is
SHA256 `394d06c94b22918ba83afac9a3831991d76229dac5ba955acdfcfea7b486726e`.
The prior cleanup-only version is preserved as
`SmokeEmIfYouGotEm-pre-stale-order-repair.exe` (SHA256
`074dbf34edce28474a2b3a7a72aabcb0f748696ea94aa4f9269e2359432819a8`);
the earlier lifecycle version remains `SmokeEmIfYouGotEm-pre-stale-input-repair.exe`
(SHA256 `47216065481e65b35ca19ef67118e2dc0c0523219bde5f00d093ef066946b6a7`).
Both backups were verified before their successors replaced the normal binary.

Final installed normal executable: default Boot -> normal menu StartScenario
handler -> FullReach, 900 post-travel frames, clean exit 0. No blank-action
warnings or fatal errors. Logged wet raft positions change at world 10/20/30s
with speeds 1.368/1.186/1.124m/s. This is engine motion telemetry, not visual
animation inspection or physical mouse/gamepad dispatch. Log
`tmp/input-stale-order-v2-normal-stage-20260924.log`, SHA256
`4d4deaa1788c35a24df990dee504bd2463a621aceacb712a7ecda3ebbd1db979`.
No concurrent engine/build/cook/test was live during this capture.

Strict unchanged CSV audit of rows 60..840 (781 samples), confirmed nonlegacy
timing offset 1: mean 34.352297ms, p95 41.6848ms, FAIL 33.333333ms. Report
`tmp/input-stale-order-v2-frame-audit-20260924.json`; CSV SHA256
`8a52656aaf19413e2769a2480930fafa33e0ec6bc7dc2867f33de6415d1d2266`.
This is not a controlled performance comparison or optimization claim. No
terrain, boulders, collision, cooked fields or water presentation changed.
Physical input dispatch, repeated real respawn/travel, source-asset regeneration
and final release packaging remain unverified; river acceptance stays open.
