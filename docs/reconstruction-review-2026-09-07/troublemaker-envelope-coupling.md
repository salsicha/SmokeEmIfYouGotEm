# Troublemaker inferred-envelope coupling — September 27

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

Next inspect this same solve's completion and audits, regional storage/surface
coverage, then export matching runtime fields. Reuse the already verified new
ground mesh; do not repeat the unchanged ground-only import. Verify the actual
coupled native union, incrementally bind ground plus matching water in the normal
scene, rebuild, and check actual motion, shoreline/continuity/collision and the
20 FPS / p95 50 ms / no frame over 100 ms gates. Do not promote the old-roof
runtime export, claim settling from global storage alone, or advance to Colorado.
