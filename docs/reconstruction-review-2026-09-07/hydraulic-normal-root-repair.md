# Restore the displaced water's hydraulic normal connection

September 28 UTC. Concrete normal-material authoring regression repaired;
not acceptance of breaking/roller realism or the South Fork reconstruction.
The preceding foam-edge experiment was rejected and restored, not shipped.

## Evidence and cause

Fresh saved-material inspection found the Normal root was
`SouthForkCurrentGradientNormalV1` (`MaterialExpressionCustom_7`): optical
current-carried ripple only. The existing `SouthForkMovingDetailNormalV1`
(`MaterialExpressionCustom_19`) remained in the asset with its correct Base
and Detail inputs, but was unreachable from Normal. Its Detail input is the
same `SouthForkRegisteredDetailV1` sampled by the active displacement branch.
Thus displacement still used live detail while lighting omitted its slopes.

`LoadOrCreateCurrentGradientWaterParent` unconditionally connected the ripple
node to Normal during `RaftSim.RefreshSouthForkCurrentNormals`. This bypassed
the composition installed and checked in September 12-15. The inspection
establishes the current defect, not the exact historical refresh that caused it.
It does not establish that all flat foam or weak breaking came from this defect.

The author now detects the existing South Fork composition, verifies its Base
is the refreshed optical normal and its Detail input exists, and selects that
composition as Normal. Duplicate or unrecognized compositions fail rather than
silently dropping hydraulic slopes. Other rivers and unregistered legacy
parents retain the direct optical root. No shader formula, expression, height,
foam coverage, source geometry, collision, solver, field or clock was changed.

## Saved asset and checks

Editor build passed in 32.77 seconds; one author regression plus four existing
local-current-normal tests pass. The author regression is a source guard,
not an engine material test. Actual engine checks are below.

`unreal/Scripts/repair_south_fork_hydraulic_normal.py` requires the exact original
asset and preserves a hash-verified backup. It invokes the rebuilt author twice
and checks **every existing node**, seven protected non-normal output graphs,
and the root's link to the same detail sample as WPO. No new nodes are allowed.
The independent fresh-process audit confirms the same saved graphs. Both engine
processes exited zero, with zero errors and four existing commandlet warnings.

- Before SHA256: `6f235b61577289f195cbbb801ce8a83e40b961827ba4be637806178ea1dcedf9`.
- Repaired SHA256: `6e7884ed44c1f3a372cda6dd1aae675409031fd1c1fbdd3a73bcb5a2effbc96a`.
- Inspection: `tmp/hydraulic-normal-before-v1.json`, SHA256
  `5a08dedd445ca4b8557123bbf77c16d64e117940d2cf145a4b2864051ece413f`.
- Two-refresh receipt: `tmp/south-fork-hydraulic-normal-installed-v1.json`, SHA256
  `f575693803537ed3cd8953095470c0c09022bee7266c25c486e6b71ffdef97a2`.
- Fresh audit: `tmp/south-fork-hydraulic-normal-fresh-v1.json`.
- Logs: `tmp/hydraulic-normal-{repair-build,install,fresh}-v1.log`.

## Actual playable capture

Normal FullReach scene, ordinary boat camera, station8310, 1280x720 D3D12,
ephemeral profile, no quality/solver override. Twelve requested one-second
samples completed and the process exited zero without logged runtime errors.
Observed raft station8312.359 to8330.859m, world time2.485 to13.123s. Inspected
frames004 and010 show the river/raft continuing alongside exposed right-bank
rocks. Flat white patches and weak breaking remain. Differences from previous
captures are not pixel-matched or same-clock evidence; no visual gain magnitude,
continuous shoreline/contact pass, or performance claim is inferred from them.

Evidence: `tmp/sf-hydraulic-normal-repaired-v1.log` (SHA256
`08a3f38d034e08468c3e721156113a367056b917919c553a36a7ed712550b3e9`),
and `unreal/Saved/Screenshots/sf-hydraulic-normal-repaired-v1_000..011.png`.
The verified improvement is restored consistency of the material's live-wave
lighting input with its displacement input, not a new fluid or breaking model.

## Packaged delivery status

### Current: storage failure diagnosed; one larger-headroom retry

Initial package98074/wrapper39604 is TERMINAL failure (UAT25, cook4 errors).
Follow-through28345/wrapper26912 also terminated; no validation or motion ran.
Zen rejected the material/oplog with HTTP507. Its own `Data/logs/zenserver.log`
records free space falling from about10.7GiB to1.86GiB at20:25:59 local, below
the2GiB write floor. It returned to11.6GiB after the cook exited. The precise
temporary file type was not established; post-exit free space alone concealed
the peak. Do not lower the storage safety floor or retry unchanged headroom.

Under the user's previous obsolete-file cleanup authorization, removed only
the five generated cooked containers in
`tmp/south-fork-playable-v4-20260926/Windows/SmokeEmIfYouGotEm/Content/Paks`.
Reclaimed2,898,684,760bytes; v4 Saved recordings/screenshots/logs/profiling,
all captured source and the current v14 stage remain. v4 is no longer runnable
without rebuilding its containers; no byte-identical recovery promise is made.
Exact paths, sizes and pre-removal hashes are retained in
`tmp/retired-v4-cooked-containers-20260928.json`. Engine/cook process inventory
was empty before removal; no recursive directory deletion or Git rewrite.

One retry is LIVE: package session5066/wrapper35132, recipe
`tmp/package-south-fork-v15r2-20260928.ps1`; log/receipt
`tmp/south-fork-v15r2-package-20260928.{json,log}`. Same three frozen input hashes,
same450s fields, fresh stage, raised minimum free space14GiB; observed15.32GB
free after cleanup. One attached follow-through session57198/wrapper39640 waits
on that exact package handle, then runs the corresponding v15r2 closure/menu/
two-rapid timing/motion recipes. Receipt
`tmp/south-fork-v15r2-follow-through-20260928.json`. Do not duplicate these owners.
The earlier live-state paragraphs below are historical and superseded here.

Epic documents that Zen holds cooked output and DDC in its managed data store,
while staged containers are separate outputs:
[Zen cooked output storage](https://dev.epicgames.com/documentation/unreal-engine/using-zen-storage-server-as-cooked-output-store-for-unreal-engine).
The specific disk-floor diagnosis above comes from this machine's service log,
not an assumption based on that documentation. No new physics or acceptance pass.

A single fresh v15 package owner is running: session98074, wrapper39604;
recipe `tmp/package-south-fork-v15-20260928.ps1`, receipt/log
`tmp/south-fork-v15-package-20260928.{json,log}`. Frozen material, author and v8
manifest hashes are in the receipt. Existing v14 is preserved; v15 uses the same
450s v8 fields, not the still-draining1350s candidate. Do not duplicate the build.
One follow-through owner is LIVE: session28345/wrapper26912, recipe
`tmp/follow-through-sf-v15-20260928.ps1`, receipt
`tmp/south-fork-v15-follow-through-20260928.json`. It holds the existing package
process handle39604 and will not restart it. After terminal success and frozen
input checks, it runs `tmp/validate-sf-v15-20260928.ps1` (closure, normal Boot/menu,
8310 and11520;1200 frames each; unchanged20FPS/50ms p95/no>100ms-frame gate), then
`tmp/capture-sf-v15-spatial-approach-v1-20260928.ps1` (80-second passive packaged
approach plus existing surface/contact observers). No timing/capture has begun
while the cook is active. Do not start duplicate validation or capture owners.
Read actual terminal receipts and decode/inspect motion before acceptance.

Cook has reported missing MetaHuman texture dependencies also present in the
v14 cook log; these remain unresolved release warnings, not new water failures
or proof of a clean release. The preceding goal turn made progress by repairing
the saved normal graph; this continuation verifies the same live build and
attaches its sequential validation/motion follow-through.
