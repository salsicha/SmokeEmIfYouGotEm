# Shifted spray-emitter height repair: SOURCE ONLY, validation pending

September28 UTC owner update: original session71849/wrapper15924 exited1
BEFORE building because publication owner4504's post-capture parser used a
stale duplicate-column exception. The saved1200-frame normal-config capture
was healthy; its same-CSV analysis now passes without that exception. Neither
game capture nor cook was repeated, and both failed receipts are preserved.
Recovery session9712/wrapper24660 is LIVE in `editor_build`, start
05:30:50.8818041UTC. Recipe/receipt use `v2-20260928` instead of `v1-20260928`.
It verifies original six source hashes plus recovered capture/report identity
and performs the same build/six native tests. Motion/cost/package remain pending.
This supersedes the live-owner descriptions below; do not duplicate this build.

September28 UTC. Prepared in the working tree, NOT built, packaged, committed
or visually accepted. Do not mistake the37 passing source-wiring guards for
the new C++ fixture or an actual game result.

## Concrete mismatch

The normal Cartesian South Fork VFX path checks the wet source footprint and
gets the visible carrier height at the crest site's centre. It then shifts
the aerosol35cm downstream, the roller12cm upstream and crest spray12cm
upstream plus its existing lateral bias, but retains the centre's Z. Hence
the configured6/3/3cm clearances are centre-relative, not clearances above the
water at each emitter's own XY. Earlier attachment audits explicitly recorded
this limitation. On a sloped crest this can place a source above or below its
intended clearance. This source mismatch is demonstrated by inspection; it
has NOT been established as the cause of all detached-looking spray puffs.

## Prepared change

- `RaftSimWaterVfxActor.cpp` samples each shifted origin's own visible wet
  carrier before the common emission gate. A failed query disables all three
  populations at that site. Existing source footprint, site selection, six-site
  budget, density, scales, horizontal planes, assets, directions and clearances
  are retained. No increased emission is used to hide weak breaking.
- The change is restricted to crest-owned Cartesian South Fork. Its affine
  world-to-river mapping avoids nearest-bend ambiguity; legacy curved scenes,
  Chilko and the legacy South Fork comparison mode retain their placement.
- `RaftSimSprayEmitterAnchor.h` preserves emitter XY and sets only Z from the
  sampled visible carrier plus clearance. Invalid origins/clearance/samples
  fail without modifying that origin. Caller gating is mandatory on failure.
- Default-off review logging retains honest centre-relative gaps and adds
  `SprayEmitterAnchorAudit` per emitter with sampled/enabled flags, world XYZ,
  independently queried carrier Z and actual clearance. Unavailable/disabled
  records are not clearance evidence.
- `RaftSim.M4.SprayEmitterAnchor` is a NEW, UNRUN native fixture covering the
  three offsets on curved-height fixtures under four flow headings, exact XY
  preservation, old centre-height mismatch and invalid/failed queries.

This anchors source centres only. It does not conform entire spawn planes,
provide particle collision/landing, repair atlas clumps, or prove realistic
breaking, foam or returning rollers. It does not change conserved water state.

## Verified preflight and exact next sequence

FullReach and Chilko presentation source guards pass37/37 after the final
Cartesian restriction,2.24s. Report:
`tmp/spray-emitter-anchor-source-v2-tests-20260928.xml`, SHA256
`efbb96cb152bfa0a0150a2f464bb53a304a8c725cbc17a0eadcd1b64c950d450`.
`git diff --check` passed for the changed VFX source. These are preflight only.

Existing hydraulic owner33552/39708 is still running to1800s and queued
publication capture4504/session60320 waits for its terminal state AND audits.
The five frozen capture inputs, including actor source and built Raft DLL,
are unchanged. The queued run uses the OLD COMPILED VFX, not this pending source.
Do not rebuild the DLL or start another game while these owners are active.

One follow-through now OWNS the next build/native phase: session71849,
PowerShell wrapper15924, receipt start05:10:09.2480274UTC (process start
05:10:08.3369808UTC). Recipe `tmp/follow-spray-emitter-anchor-v1-20260928.ps1`;
receipt `tmp/spray-emitter-anchor-follow-through-v1-20260928.json`. Live process
was verified after launch; phase is `waiting_for_publication_capture`.

It waits on exact capture4504 (verified process start04:12:35.1824058UTC),
requires its successful terminal receipt and original input hashes, checks
engine/build/cook isolation and8GiB disk reserve, then performs ONE single-worker
Editor Development build. It runs precisely SprayEmitterAnchor, RapidSourcePlane,
SouthForkSprayReviewMap, SpraySourceFootprint, VisibleSprayCarrier and
WaterVfxClassifierUsesHydraulicsAndContacts. All six must report clean Success,
not merely process exit0. It stops there: no automatic motion, package or commit.
The pending VFX/header/fixture/source guard, existing water actor and preserved
user test have frozen hashes. Do not edit/rebuild these until that owner is
terminal. No current cook/capture is stopped or restarted on a wait bound.

1. Finish existing cook/audits and capture; inspect their actual results.
2. Inspect the queued owner's build and six native results; do not duplicate
   them. Repair
   compile or native failures before claiming a working runtime change.
3. Run one normal-scene actual-motion review with the explicit anchor audit;
   require sampled/enabled emitter clearances6/3/3cm at THEIR positions.
   Inspect spray/crest/shoreline motion and measure cost without diagnostic
   logging; do not assume appearance is fixed from numerical anchor equality.
4. Integrate into the normal rebuilt game and validate delivery. Commit the
   scoped runtime change only after verification. Preserve the user's separate
   WaterSurfaceTest line-ending edit. No push is authorized by this work.

## Prepared capture-log check (not engine evidence)

`physics/scripts/audit_spray_emitter_anchors.py` now checks the actual
`SprayEmitterAnchorAudit` records intended for step3. Run it on that future
engine log with `--report` pointing to a new JSON report. It requires complete,
ordered aerosol/roller/crest triplets with one slot and common emission flag;
rejects missing/duplicate/invalid fields and nonfinite values; verifies the
independently logged Z-minus-carrier arithmetic; and requires sampled, enabled
6/3/3cm source-centre evidence for each population. The0.000002cm tolerance is
only for six-decimal log rounding, not a visual-error allowance. Disabled or
unavailable samples cannot establish clearance. Source path/hash and counts
are retained. A mismatch exits1 and writes a failed report.

Twenty synthetic parser tests pass in0.55s, including truncated records,
wrong clearances, missing samples, flag disagreement and disabled-only logs.
Report `tmp/spray-emitter-anchor-audit-tests-v1-20260928.xml`, SHA256
`5ae49e084a783c788f5ef770a8099567e6d03df55f5416660e3a245f5f823a36`.
This is supporting validation ONLY: no actual new engine log has passed,
and duration/motion, normal launch configuration, spawn-plane or particle
clearance, appearance and performance are explicitly not proven by this check.
All six queued build inputs remain unchanged; cook33552/39708 and queued
capture4504/build15924 were reverified live at simulated1761.5s. No extra
engine/cook/build was launched, and no pending runtime change was committed.

## Disk headroom restored without deleting captured evidence

Free space had fallen to4.58GB before cleanup, insufficient for the prior
14GiB packaging preflight. Under the user's obsolete-file cleanup request,
removed ONLY five generated Paks/container files from each obsolete stagev5
throughv13 (`south-fork-playable-vN-20260927`): global.ucas/global.utoc and
SmokeEmIfYouGotEm-Windows.pak/.ucas/.utoc. All45 targets were regular files
inside verified, non-reparse stage paths, untracked; no running process named
an old stage. No recursive directory deletion was used.

Deleted29,118,858,726 logical bytes (~27.1GiB). Free space afterwards:
33,702,551,552 bytes (~31.4GiB). Retained both v14 and v15r2 five-file container
sets, all source/captured data, videos, logs and reports, and active cook data.
Old executable stubs remain but those obsolete stages need rebuilding to run.
Files were deleted, not recycled; no recovery promise for identical old binaries.

Receipt: `tmp/obsolete-v5-v13-containers-cleanup-20260928.json`.
Recipe: `tmp/remove-obsolete-v5-v13-containers-20260928.ps1`.
Initial preflight failed on PowerShell5 Split-Path parameter compatibility before
any deletion. After correction all45 deletions succeeded; final byte summation
then failed on hashtable property access. The separate finalizer rechecked all
45 absences, retained packages and five frozen capture hashes, and completed
the receipt without additional deletions. Do NOT rerun the cleanup.
