# Troublemaker inferred-envelope coupling — September 27

Latest: normal-scene candidate SAVED and fresh reload verified. V6 game build
session5004 is LIVE. No visual/settling/performance acceptance. Earlier live-cook
and unchanged-scene notes below are historical; see the completion section.

Supporting implementation and fresh solve in progress; no visible delivery or
river acceptance. Normal playable v5, its ground and rock actors are unchanged.

The previous candidate used the captured-return roof while the installed mesh
uses a lower interpreted envelope. The new explicit envelope contract validates
the original cap against captured returns first, then substitutes only the
active hydraulic roof. It never takes a second maximum with the old roof.
Original returns, roof XY, topology, floor, and provenance remain protected.
The lowered envelope is inference, not measured rock or validated bathymetry.
Historical vertex constraints do not prove whole-surface hydraulic equivalence.

## Completed this increment

- 65 focused geometry, terrain-revision, envelope rejection and runtime packet
  identity tests pass. Existing captured-cap validation is not relaxed.
- All 841 cores / 5,382,400 original cells pass preparation checks. The same
  candidate registered ground is retained. Captured masks/stages and physical
  settings/endpoints are unchanged.
- Independent comparison with the previous candidate changes only 296 bed
  samples in cores 0629 and 0631, all lower-only. All 319 hydraulic sample
  locations under the roof now exactly match candidate ground plus the actual
  inferred envelope (maximum error 0 m). This is lattice parity, not native
  whole-triangle collision, motion, or shoreline acceptance.
- All 799 matching source packets are prepared and independently reconstructed;
  15 differ from the original source packets. The runtime export identity guard
  accepts their exact match to the new full-river geometry.

Source descriptor: `tmp/troublemaker-envelope-union-source-v1-20260927.json`.
Envelope archive SHA-256:
`36811cf7adf7710fefaaba3ffbb6dfc11d4dc113a44b7daf322a4090c0a4c1a3`.
Candidate ground SHA-256:
`3fd9eef54ff243c09fe7c33aa69129a3496387d7d603012a543457fb1cf14542`.
Union geometry: `tmp/troublemaker-envelope-conveyance-union-v1-20260927/manifest.json`,
SHA-256 `f90a070c5bc01869f554e1b150790d2607a4d31d53b9b8d354547a967d0447a3`.
Source packets: `tmp/troublemaker-envelope-source-packets-v1-20260927/manifest.json`,
SHA-256 `3ff33318461254d951257bad839c09e17c2fa17149e4bf1a610e4b26d28f8f0e`.
Independent audit: `tmp/troublemaker-envelope-input-audit-v1-20260927.json`;
recipe `tmp/audit-envelope-input-v1-20260927.py`.

## One live fresh solve — do not duplicate

Cook PID **31092**, shell session **3804**, launched after checking that no engine,
build, Blender or solver was active. Process receipt:
`tmp/troublemaker-envelope-process-v1-20260927.json`.
Wrapper `tmp/cook-envelope-conveyance-v1-20260927.py` owns the subprocess handle
and records its native return code, avoiding the previous PowerShell null-exit
observation failure. Do not infer completion from this launch note.

Input: `tmp/troublemaker-envelope-full-input-v1-20260927/full/manifest.json`,
SHA-256 `58cbc5b1d570a7976f85b3d4a21b089073e020a0751cf87ecabc60bf67a67716`.
All package file hashes were checked immediately before launch. Qualified solver
SHA-256 `458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.
Output: `tmp/troublemaker-envelope-full150-v1-20260927`.
3,000 steps at 0.05 s, eight lanes, snapshots at 0/75/150 s. Fresh initialization;
no old-bed evolved state transferred. Wrapper runs final finite-state and dry-bank
audits only after successful native completion; storage and station analysis
remain separate checks. Solver gates are unchanged.

## Combined native check prepared during the same solve

The coupling implementation is committed locally as `6d4d3206e`; no push.
New `prepare_envelope_union_native.py` builds 132,763 physical-union probes:
129,242 changed ground-triangle centroids, 2,954 inferred roof-triangle centroids,
319 hydraulic-envelope cells, 246 exposed inferred flanks and two covered
boundary points. Source-space roof/ground ownership and reflected flank normals
have unit coverage; the combined focused suite has 70 passing tests. Engine
scripts parse, but this is not evidence that engine traces or installation pass.

Probe file `tmp/envelope-ground-union-probes-v1-20260927.json` has SHA-256
`a295d6b2d5c7967ad6009b5ca1d0268f93a1433b30375bd7c681ce5acd0cdb97`.
Preparation initially stopped before output on a mistyped geometry path; the
correct `geometry_manifest.json` path comes from the input manifest, and the
subsequent preparation succeeded. No data or validation gate was weakened.

Deferred shell session **25615** waits on the existing Python wrapper PID38948
(identified by its actual command line), then checks native exit0 and final
banks before launching ONE no-save Unreal check. Helper:
`tmp/after-envelope-cook-native-v1-20260927.ps1`; native launch recipe:
`tmp/run-envelope-union-native-v1-20260927.py`. Do not duplicate this stage.
Future engine report/process receipt use prefix
`tmp/envelope-ground-union-native-v1-20260927`. The check reuses the saved candidate
ground mesh, validates all directed mesh identities, traces each probe in simple
and complex modes against all physical ground, restores the original ground and
checks protected scene/source hashes. No saved scene mutation or FPS claim.

`install_envelope_conveyance_runtime.py` is prepared but NOT EXECUTED. It requires
successful native proof with unchanged protected files, exact source-packet /
geometry identity and full runtime dependency closure. It backs up only the two
actors to be changed, duplicates the native-verified ground to a fresh production
asset, and saves only the existing ground and water-config packages. The current
rock actor, materials, coordinate maps and runtime solver settings remain intact.
Native execution, fresh reload and rebuilt normal play are still required.

The native preparation/checker and guarded installer are committed locally as
`dfe96dd21`. The same live solve's completed 75s checkpoint passes independent
state and bank audits: all 5,382,400 cells finite/nonnegative, maximum depth
2.913112 m, maximum speed 8.208481 m/s, and all 86,720 artificial-bank cells
exactly dry. Maximum step conservation residual is 8.99e-9 m3. Receipts:
`tmp/troublemaker-envelope75-state-v1-20260927.json` and
`tmp/troublemaker-envelope75-banks-v1-20260927.json`. These are intermediate
safety checks, not settling or playable acceptance; retain PID31092/session3804
and deferred native session25615 until their actual terminal results.

The75s regional audit closes343.111421m3 of storage change to exterior flux
within1.49e-10m3; this is not equilibrium. Surface analysis still has local
8380..8465m bins roughly0.5m below the captured surface and reduced wet coverage.
Receipts: `tmp/troublemaker-envelope75-storage-v1-20260927.json` and
`tmp/troublemaker-envelope75-analysis-v1-20260927/report.json`.

Paired snapshot check `tmp/envelope-fresh75-comparison-20260927.json` finds exact
initial h/u/v and exact75s h/u/v versus the previous fresh conveyance candidate.
All296 changed bed cells are still dry at75s in both runs; the old candidate has
11 of those cells wet at150s. The loader reads each package's actual `bed.npy`.
Thus unchanged75s state is explained by dry changed terrain, not evidence of an
improved hole or grounds to substitute an old final snapshot for the new solve.

The same deferred native helper now runs final0/75/150s regional storage and
station analysis, then exports `tmp/troublemaker-envelope-runtime150-v1-20260927`
only after native collision passes. No scene installation is automatic. Inspect
session25615 and its receipts before running any of these stages again.

The installer identity guard was separated into a standard-library-only module:
`south_fork_packet_geometry_identity.py`. Unreal's embedded Python no longer
imports the NumPy-based exporter merely to validate identity. Nine identity
tests pass, including isolated `-I -S` import with no NumPy or site packages.
The full-array exporter and native checks remain mandatory; no gate relaxed.

Next inspect this same solve's completion and audits, regional storage/surface
coverage, then export matching runtime fields. Reuse the already verified new
ground mesh; do not repeat the unchanged ground-only import. Verify the actual
coupled native union, incrementally bind ground plus matching water in the normal
scene, rebuild, and check actual motion, shoreline/continuity/collision and the
20 FPS / p95 50 ms / no frame over 100 ms gates. Do not promote the old-roof
runtime export, claim settling from global storage alone, or advance to Colorado.

## Completed solve, native union, export and normal-scene installation

Same cook PID31092/session3804 completed150s with native exit0 and wrapper exit0.
Final state and86,720 dry-bank checks pass. Maximum depth2.904861m and
speed8.208481m/s; no settling claim. Final receipts:
`tmp/troublemaker-envelope150-state-v1-20260927.json`,
`tmp/troublemaker-envelope150-banks-v1-20260927.json`,
`tmp/troublemaker-envelope150-storage-v1-20260927.json`, and
`tmp/troublemaker-envelope150-analysis-v1-20260927/report.json`.
Final75s net filling remains11.220582m3/s and8-9km drains about14.20m3/s.
Local surface deviations near8430..8465m remain about-0.59m; not calibration.

The queued native check PID4800 exits0. All132,763 points pass both simple and
complex traces (265,526 total), preserving1,356 protected source/scene files.
Largest positional error is0.00634514cm on roof centroids; hydraulic-envelope
cell maximum0.00016557cm. Full native directed-triangle hashes match both meshes.
Report: `tmp/envelope-ground-union-native-v1-20260927.json`, SHA-256
`0cc0a68ddfaa895df9fe0aa20eb5104cae0f5ab4f811d24088569f97dc883c6f`.
This is enumerated collision verification, not continuous surface or motion proof.

Same deferred session25615 exits0 after final analysis and runtime export.
`tmp/troublemaker-envelope-runtime150-v1-20260927/export_audit.json` verifies
all799 packets /841 atlas tiles and42,185,039 exact bed-intersection samples.
Atlas SHA-256 `17ceb1e86301b8715ff110d978f1d0d19d036f92fb58a3a1e8a327fd16dc6bc7`;
streaming SHA-256 `9379b7a803bd2022f70aa64c297b82fc7777664c54e8451e22f1abb4d93812a4`.
No old-roof fields are substituted. Final h/u/v hashes:
`070421c254126316526f7a5f1c7bc0340995543ef9d0cc7325bcc8e561eb8f2b`,
`6ab5a5a988bbd36a49fdcde22fb4e9b6b3edd345292ae86c654f779505dac411`,
`c2b6b39d7deeeca2e686c653bc4b6049c80d1b552d90123b0864c8964780265e`.

Normal installer PID31316 saved the new production mesh and only the existing
ground/water-config actors. It then exited with3221225477 (0xC0000005) during
shutdown, after the install receipt and final log close; no Python exception
is in the log. This is an abnormal exit, not a clean successful process.
The writes were NOT repeated. Session98485 stopped on that return code.
Exact two-actor backup:
`tmp/envelope-conveyance-install-v1-20260927.before.zip`, SHA-256
`0a6dc2874c5c97924d8e5ff33dcd59bf73ae4d974617a8a3252324b693ad1a00`.
Installation receipt/log/process record share that prefix. Preserve them.

Independent inventory PID35040 exits0; recovery session33436 exits0 after bundle
creation. Fresh reload verifies ground/envelope native geometry, transforms,
ground fallback policy and matching normal water bindings. No scene writes.
Inventory: `tmp/envelope-conveyance-inventory-v1-20260927.json`.
Production ground:
`/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/ConveyanceEnvelope20260927/SM_ConveyanceGround`,
package SHA-256 `056d670dd2bb25fece3f67d9268d5083b8ee46dc5936451b6a83092c2e359489`.
Its native triangle hash stays`d6a5f18ffe07c881b6dcbe40201cafa863b93d78b6f086e86c78effabdae743a`.
Ground actor package`3/LY/MFF59H58N6AWIGUAUQOON1.uasset` now has hash
`8695405868c2c071f32620e4dce13643088b20b21533106d38733f5efee1d979`.
Water-config package`0/P0/A1GOUPANCXW4AY40QJTLTK.uasset` now has hash
`6f1262d278e0ceb230990f256397c8f98d252b4218e4c7eb595844c9dc529bb3`.
Rock actor, map, manager, materials and coordinate maps remain unchanged.

Frozen bundle`physics/data/runtime_bundles/south_fork_discharge_bed_v6` verifies
2,405 logical files /917,995,570 bytes. Manifest SHA-256
`243ec143409f1c698e3fe567c1b3436fd8fd3a9451d0bd22503390d81c5dd25b`.
Its saved-scene hashes include the ground and rock actors as well as water
configuration and run manager. Build.cs stages v6;38 bundle regressions pass.
V5 package and bundle are preserved. BuildCookRun session**5004** is LIVE,
recipe`tmp/package-south-fork-v6-20260927.ps1`, log
`tmp/south-fork-v6-package-20260927.log`, fresh stage
`tmp/south-fork-playable-v6-20260927`. Do not duplicate it.
Next actual staged hash closure, normal Boot/menu launch, motion/contact capture,
shoreline/surface/crest review and20FPS performance. Saved integration is not
yet a visually inspected rebuilt-game delivery. Retain the abnormal installer
shutdown as a release issue until assessed; do not erase or silently waive it.
