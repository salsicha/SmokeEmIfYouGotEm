# South Fork v3: standalone build and staging repaired

September 26, 2026. This closes the missing standalone payloads identified in
[the staging-gap audit](south-fork-v3-staging-gap.md). The subsequent native
staged-path check below also passes. Cooked-package, geographic, hydraulic and
performance acceptance remain open.

## Delivered build

On an idle host, ran the normal Unreal build target:

```powershell
& 'C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat' SmokeEmIfYouGotEm Win64 Development '-Project=C:/Users/salsi/repos/SmokeEmIfYouGotEm/unreal/SmokeEmIfYouGotEm.uproject' -WaitMutex -NoHotReloadFromIDE
```

Build succeeded: 2,416 actions, 699.86 seconds, process exit zero. This includes
the 2,405 v3 runtime-file copies, game compilation, executable link and target
metadata. The executable is `unreal/Binaries/Win64/SmokeEmIfYouGotEm.exe`,
353,318,912 bytes, written at 2026-09-26 12:07:43 UTC; SHA-256:
`20f9cdf2fbd22b2e317878fec3baad4200e42e0ee128aabcbec90ebd02791073`.

This builds the shared working tree, including pre-existing source edits; it
is not a clean release qualification. Those edits and the other session's
Zambezi map were neither changed nor committed by this task. No solver switch,
geometry change, cook, history rewrite or push was performed.

## Actual staged-tree result

The repaired verifier follows the active build-rule selection, v3. Against
`unreal/Binaries/Win64/RaftSimRuntimeData`, it now **passes** all 2,405 files,
917,958,619 logical bytes and the complete dependency closure. No source-tree
fallback is used. The [after receipt](south-fork-v3-stage-after.json) and
[before failure](south-fork-v3-stage-before.json) retain the distinction.
The three active-bundle selection tests also pass.

Successful build log preserved locally:
`tmp/discharge-bed-independent-audit-20260926/standalone-v3-build.log`, SHA-256
`d483e0976ea364b688443dd52ef9483a4d0707c8ed50ef4ccc4ad5621882a502`.
The global Unreal build log was overwritten by the other session before the
initial copy. That copy was renamed `editor-build-overlap-observation.log`;
the correct archived log was recovered only after matching the standalone
target, success marker and exact 699.86-second duration. Do not attribute the
editor build log to this standalone result.

## Native staged-data validation passed on the idle-host retry

The read-only native staged-path comparison was started after the build.
Another session had just started an editor rebuild, exposed as `dotnet.exe`
rather than `UnrealBuildTool.exe`. To avoid holding editor DLLs open, this
task stopped only its own verifier (PID24344) and its own SDK-check child;
no user or other-session process was stopped and no assets were saved.
The verifier produced **no success receipt**. A later retry used a guard that
also recognizes UnrealBuildTool under dotnet and Build.bat under cmd; it found
the host occupied and stopped before launching an engine.

After the other session's P4 suite exited at 13:01 UTC, the guarded retry ran
`verify_south_fork_runtime_bundle.py` against the actual staged root. It exited
zero at 13:08 UTC and produced the [native receipt](south-fork-v3-native-stage.json):
2,405 files verified, 2,001 native route queries and 2,601 native initial-water
queries (691 wet), with maximum staged/source errors exactly zero. Absolute
staged paths were used with no external source fallback. This was an editor
process, with zero solver steps and no saved assets, not standalone gameplay.
The local log is `tmp/discharge-bed-independent-audit-20260926/native-v3-idle.log`,
SHA-256 `a559cbb80be68e5802deea1ed37b169975869b538973e0a7c78998d75a3502db`.

Next: rebuild and validate the cooked game. The standalone executable has not been run or
accepted in this pass, and older cooked content is not updated by this build.
Normal-menu motion/20 FPS results from the preceding editor-hosted delivery
are historical evidence, not new standalone measurements.

Do not rerun the old missing-file diagnostic: the build/staging repair is now
verified. South Fork still needs the open rapid, geometry and hydraulic gates
before the queue advances to Colorado.
