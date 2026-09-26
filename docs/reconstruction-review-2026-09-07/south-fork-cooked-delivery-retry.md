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
