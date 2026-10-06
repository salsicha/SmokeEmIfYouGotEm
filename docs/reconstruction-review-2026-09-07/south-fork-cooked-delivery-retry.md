# South Fork cooked delivery retry — September 26

The 14:54 UTC follow-up attempted the next actual delivery step, not another
v3 source/staged-data comparison. After the shared capture process exited,
an idle-host guarded `BuildCookRun` started Development build + iterative cook
+ stage + pak + package, targeting the fresh project-local folder
`tmp/south-fork-playable-v3-20260926`. No archive copy or previous-stage deletion
was requested. The target folder was never created; no new cooked game was
published and the previous v7 playable stage remains intact.

## Exact new build failure

The standalone target failed after 228.42 seconds with C2039 in
`RaftSimCanopyGroundAudit.cpp`: `UStaticMesh::IsNaniteEnabled()` is unavailable
in the non-editor target. Local UE 5.8 `StaticMesh.h` declares that asset-build
setting query in its editor-only section. The diagnostic now instead calls
the runtime API `HasValidNaniteData()` and explicitly describes the distinction.
This inspects resident render data; it does not change mesh settings or Nanite
rendering behavior. The null-mesh guard remains.

The corrected line is intentionally left in the working tree alongside the
other session's active canopy-audit edits, not committed by wholesale staging
that file. Preserve those edits. **The correction is not yet build-verified.**
Retained failure log: `tmp/south-fork-v3-package-compile-failure-20260926.log`,
SHA-256 `d85b4db4fc2290d067c04da8c738fbdba1a1f226bb7618c81e31658626dd0389`.
The standalone executable remains the 12:07:43 UTC build, 353,318,912 bytes;
it does not include the latest far-field/backdrop-related code.

## Shared-session exclusion

After our pipeline began, the other session started a backdrop asset import.
To avoid cooking assets while they changed, only this task's verified UAT
coordinator (PID13932) was stopped. Its compiler subsequently reported the
failure above. No other session's process was stopped. A standalone-only retry
was refused before launch when another scene capture (PID6552) was found.
The active map, backdrop, installer and canopy-audit changes were preserved.
Reserve an exclusive build/cook/validation window before retrying; an idle
snapshot alone has not prevented another session from starting work mid-build.

## Ready for the next isolated run

`profile_south_fork_menu_launch_ps5.ps1` now accepts `-PackagedRoot` pointing to
the cooked Windows stage. It launches the inner game executable (no editor or
project/map override), locates that stage's CSV directory, verifies unchanged
binary hash and zero exit, and applies the existing ordered Boot → menu →
FullReach → post-travel CSV checks. Existing editor-hosted use is retained.
Both modes reject competing game/build/cook processes and record the execution
host, so editor results cannot be misreported as cooked-game measurements.

The packaged-path/syntax test and existing normal-menu ordered-launch tests
pass. This is launcher validation, not a successful cooked-game run. After a
successful fresh package, use the new option with 1,200 frames and inspect
actual raft telemetry and rendered motion separately. Keep the 20 FPS / 50 ms
p95 and >100 ms hitch gates; no physics or quality settings were relaxed.
South Fork remains unfinished; later rivers remain queued.

## 16:54 UTC follow-up — compiler repaired; v4 cook running

The next guarded retry started from `0e8448c27` (bed v2 / runtime bundle v4)
with a clean tracked tree and no competing engine/build/cook at launch.
The corrected Nanite query is now included in the shared history. The actual
standalone Development build **passed**: 2,408 actions in 89.91 seconds,
including the game link. This supersedes the unverified correction and old
executable status above; it does not yet establish a working packaged game.
The retained build log is `tmp/south-fork-v4-build-success-20260926.log`,
SHA-256 `049fd6d25e4b7411c004fb8ff24ea8e74c59f44951a2a53ef268fbd4ff463149`.

The same UAT pipeline continues through iterative cook, stage, pak and package
to the fresh destination `tmp/south-fork-playable-v4-20260926`. At 17:05 UTC,
2,265 of 2,266 packages were cooked. The remaining package is waiting on
`M_RaftSim_SouthForkRaftTransmissionWaterV4` shader jobs; six shader workers
were consuming CPU, so this is active compilation, not an established hang.
No duplicate cook was launched and no previous playable stage was removed.

Resume this existing pipeline before starting more work: UAT PID2240, parent
PID15024, cook PID30284 (identities must be rechecked, not trusted after exit).
Cook log: `C:/Program Files/Epic Games/UE_5.8/Engine/Programs/AutomationTool/Saved/Cook-2026.09.26-09.57.24.txt`.

Another session ran M9 tests and changed other-river materials during this
cook. No other session was stopped. At the follow-up check, the South Fork
map, terrain, canopy, plugin code, configuration and active v4 bundle still
matched the build-start revision. Nevertheless this is **not a clean
whole-project acceptance build**. Any completed package needs the active v4
payload verifier followed by the packaged normal-menu profiler and separate
rendered motion/collision/shoreline checks. No package completion, new FPS
result, visual acceptance or river completion is claimed here. Keep the
20 FPS / 50 ms p95 and single-frame >100 ms hitch gates unchanged.

## 17:55 UTC follow-up — package complete; runtime health fails

The existing UAT process completed successfully in 751.53 seconds (exit 0).
The v4 payload verifies and actual packaged Boot/menu travel and motion now
have receipts. The former compiler/cook blocker is resolved. However, both
normal-menu runs reject stateful detail input after about 3.25 seconds;
apparently passing CSV timings occur after that subsystem stops updating and
are not healthy-performance acceptance. See [the packaged-game report](south-fork-v4-packaged.md)
for retained evidence and the next repair. No duplicate cook was launched.
