# Exact ground source retention and packaged qualification

2026-09-16. Progress, NOT scene completion, packaged acceptance or a 30 FPS pass.

## Saved source assets

The prior native audit proved that the actual ground meshes had CPU access
disabled. Editor collision queries still worked; that did not establish cooked
availability for the exact-source hull query. Commit `608dc6c4b` added the native
collision-provider audit, importer retention, strict migration/provenance checks,
and non-editor build fixes. Both editor and Development game targets built.
The native report records 49 successes, zero warnings/failures/not-run tests.

The first migration preflight rejected an obsolete rapid asset in the historical
assembly inventory. No packages were saved by that attempt. An independent
asset-registry dependency inventory of all 456 protected saved actor packages
confirmed exactly **443 current ground meshes**: 390 terrain tiles, 51 context
tiles, the join and the captured Troublemaker ground. The migration uses this
current set, not the obsolete registered-survey mesh. Troublemaker remains a
rapid in South Fork, not a scenario or menu entry.

The current 6,404-triangle local rock candidate was added to this set. All
**444 packages / 9,211,652 collision-source triangles** now retain CPU access.
All original packages were backed up before any save to
`tmp/ground-cpu-original-packages-v1-20260916.zip` (164,829,313 bytes).
The 443 normal-map source assets are versioned; the generated candidate and
backup remain ignored local products. No map or actor package was saved.

[The versioned receipt](ground-cpu-retention-v1.json) records each original and
retained package SHA256, native before/after identity and unchanged material
paths. Native identity includes every directed triangle's float coordinates,
cyclic corner order, material slot, collision LOD/trace setting, provider vertex
count and flip-normal setting. Renumbering does not conceal geometry changes;
reversed winding is not canonicalized away. CPU access is the intended change.
Historical import reports remain immutable: only this explicit package-hash and
native-source proof chain permits their metadata-only forward revision.

Fresh-process readback independently loaded all 444 saved packages and verified
CPU access and identical source identity. Of the earlier 464 protected files,
**462 are unchanged and two have authorized source-mesh metadata revisions**.
Those exceptions are the actual captured ground and join, not maps, actor
packages, profile state or evidence. The other 441 changed terrain assets were
not in the old 464-file comparison; they are individually covered by the receipt.

The SHA implementation uses UE's bundled OpenSSL. The first platform-hook
implementation failed with `No SHA256 Platform implementation`; that retained
failure preceded all migration saves. Independent Python serialization of the
render-buffer triangles matches the native hashes for the engine cube, all
803,842 captured-ground triangles and all 6,404 candidate triangles.

## Actual saved-package collision, not a reimported substitute

The verifier now accepts a scoped saved candidate only with BOTH its exact
package SHA256 and native collision-source SHA256. Partial identities, changed
packages, missing packages and out-of-scope paths are refused. It does not import,
change collision settings or save assets on this path. The previous transient
import path remains available for newly generated candidates.

The fresh actual FullReach-map run exits 0 and passes **all 30,403 collision
probes** at the existing 0.1 cm tolerance, with zero misses/owner mismatches.
Maximum error is 0.03176985494 cm. All **12,800 native water-field queries** pass,
with zero wet-mask mismatches. These query the existing source-matched 50-second
candidate state, NOT the later long cook or settled water. The map, 456 actor
packages and the tested saved meshes remain unchanged by validation.

Focused Python regression selection: **66 passed**, including six new saved-
package configuration checks. These pure tests do not pretend to certify native
collision; the engine report above supplies that evidence.

## Packaging is running, not accepted

UAT session **80881** is cooking the actual Boot/FullReach maps and the current
candidate directory for a Development Windows package. Cook PID **16144**, start
`2026-09-16T00:37:23.142354-07:00`. Shader workers were independently confirmed
live with increasing CPU time; an observation timeout is not a failed cook.

Archive target: `unreal/Packaged/GroundCPU-Development-20260916`.
Actual cook log: `C:/Program Files/Epic Games/UE_5.8/Engine/Programs/AutomationTool/Saved/Cook-2026.09.16-00.37.23.txt`.
The requested UAT `-log=tmp/ground-cpu-package-v1-20260916.log` did not produce
that file; do not poll the nonexistent path or infer failure from its absence.

NEXT after this SAME job completes: run the packaged non-editor executable with
`RaftSim.AuditGroundSources`, input
`tmp/ground-cpu-cooked-expected-v1-20260916.json`, and a fresh report. Require
444 matches and `editor_only_data=false`; an editor pass is not a substitute.
Do not set the receipt's `cooked_verified` flag until that proof exists. Then
qualify actual packaged play, contact, startup/memory/runtime cost and normal-
play integration. The full-hull response is still opt-in, not promoted here.

Another release gap is visible in the authoritative configuration: the current
saved streaming actor references `tmp/south-fork-runtime-atlas-600s-v1-20260912`,
whereas `RaftSimWater.Build.cs` stages older runtime roots and the old route map.
The current full-reach route and atlas require self-contained, source-verified
staging. A successful ground-only packaged audit cannot close this gap.
Earlier preview descriptors correctly become stale when their package hashes
change. Generate fresh stage/descriptor evidence from the new receipt and saved
collision report; never bypass dependency validation or rewrite old evidence.

## Hydraulic boundary failure and corrected continuation

The previous SAME cook, session 69275 / PID 27776, finished normally at 1200 s
(terminal exit 0). The 1100/1150 s snapshots pass cell/conservation and exact-dry
bank audits, but **1200 s fails the unchanged dry-bank gate**: one west-edge cell
of `core_0229` has depth 0.007962991531 m. Finite/conservation checks alone do not
make this valid. Its volume is 3,020,468.195308832 m3, maximum depth 4.5766248411 m,
maximum speed 7.0740459181 m/s, maximum step mass residual 1.35096515086e-8 m3.
Outflow 74.6290224408 versus inflow 45.3069545472 m3/s also rejects settling.

Restarted from its own last exactly dry **1150 s** state, using the later wet-edge
observation only to select context. One source-exact 80 x 80 tile at UTM
(675280,4296000) was added as `context_0837`; **zero added water**. Original 837
geometry records, terrain-union identity, bed, roughness and physical boundaries
are unchanged. Applying the current rock union to the new tile changes zero
samples. No failed 1200-second evolved state was transferred.

Native one-second pilot finished with all 5,363,200 cells valid and all 86,560
artificial-bank face cells exactly dry. Independent pilot AND actual restart
audits prove all 5,356,800 retained h/u/v cells bit-exact and the clock unchanged;
inventory error is -4.65661287308e-10 m3. This is restart correctness, NOT settling.

**LIVE continuation: session 86918 / PID 18000**, start
`2026-09-16T00:42:20.811134-07:00`, from 1150 toward 1800 s (13,000 steps at
unchanged 0.05 s, snapshots every 1,000 steps). Output:
`tmp/south-fork-landward-context1150to1800s-v1-20260916`.
Input: `tmp/south-fork-landward-dry1150-context-input-v1-20260916/manifest.json`.
NEXT completed local 1,000 / absolute 1200 s cell AND boundary audits. Revalidate
this process/handle; do not restart on observation timeout. All failed/previous
states and their reports are retained.

## Evidence SHA256

```text
retention receipt 808f23cefb33ff879884a81418669bc15890870bc443b98100dbcc2d734dbf95
saved-map inventory d9f3e76868a370ab95de16a7aa5843e490a541b9a7fff70a7d357c5abbb83cff
fresh native reload e63229686f95332892c0e305f41cba79cc51519a99a4c28ef1fcbb14c5968e1a
49 native tests 31b9d2a8b4c66646a5c9bbe03a6732aebb8f141e6e023449c575ce82600e275c
independent Python identity a1d97a71b2942612ee70ef0adb5e12de4910d2dc8520655004fea1b8943c6026
saved union/native report 4e4e2e5268ccf96711fe52debee30c4ba5966a6c0db8a85320a23fce2c7a8697
1200 s state audit 7a95da80d5a0f651511b8e658e077758421540913c461ebeb29066bb472df79e
1200 s failed bank audit 1358c6a324d7b26bb63b74f9cc3ca9c26efe27b318122a2a5f955352a5362246
corrected input 9813412e322d1ed4c121cecfb24389c36503f2128651c410353fba16697c2f64
corrected union proof 6f755bff7380f6560a2a664c17f25726102e4dec08c90288b2df1829288bcf3e
actual restart audit f16a270f052e9f51f6f7d75509e257155d67f52fd5ef504ac48115288aaf5fd3
solver executable 7d7c3be00a4eaefaba7fca67626ab4b6415f6d173ee9933459b06862734b135f
```

Visible breaking/froth, source-supported flanks, normal-play delivery and
performance remain OPEN. Last uncontended ordinary play is still 17.819710 FPS /
p95 81.6343 ms, failing 30 FPS / p95 33.333333 ms. No new visual or FPS claim.
Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi/all-scene water, crew, remaining
physical regressions, normalization and release remain required.
