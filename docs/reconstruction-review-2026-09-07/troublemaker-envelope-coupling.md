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

## Completed v6 packaged validation — not accepted

BuildCookRun session5004 exited0 after276.73s. Validation session92941 also
exited0 after normal Boot/menu, busy11520m and actual8330m paddling capture.
The motion process was PID21480. A subsequent process inventory found no live
Unreal/game/Python/AutomationTool processes. Do not duplicate these runs.
Recipe: `tmp/validate-south-fork-v6-20260927.ps1`.

Actual staged closure `tmp/south-fork-v6-staged-payload-20260927.json` passes
2,405 files /917,995,570 bytes without external source fallback. The packaged
executable SHA-256 remains
`8ffc14bef18cf155290b62bf60686346e1a639d3cbb50188371abf7bd1f2fff8`,
identical to v5. This was a ground/water data change, not a C++ optimization.

Both1200-frame runs have clean game exits and zero logged runtime errors.
Audited rows30..1169 (1,140 frames) fail the unchanged20FPS acceptance gates:

| Normal packaged run | Mean ms | p95 ms | Maximum ms | Frames over100ms |
| --- | ---: | ---: | ---: | ---: |
| Boot/menu FullReach |47.6834|85.4841|165.9686|22|
| Busy11520m |55.9701|81.5321|110.0699|2|

Receipts in `unreal/Saved/RaftSimValidation/`:
`sf-v6-normal-menu-20260927-frame-audit.json` and
`sf-v6-rapid11520-20260927-frame-audit.json`. The profiling wrapper returning0
does NOT mean the timing gate passed. V5's earlier corresponding p95 values
were44.4436ms and71.8342ms; these are sequential, not controlled interleaved
measurements, so the difference does not isolate a causal data regression.

Existing CSV scope inspection (same audited rows; overlapping scopes must not
be summed) points primarily to game-thread cost. Busy11520m mean game thread
54.274ms versus GPU17.457ms; water-surface Tick32.290ms, SetMesh15.296ms,
crest Update12.919ms, solver StepWater12.466ms, ground Sample0.641ms.
Normal-menu means are46.196ms game thread,15.699ms GPU,26.297ms surface Tick,
10.690ms SetMesh and10.797ms StepWater. These identify investigation targets,
not a proven optimization or grounds to reduce simulation/quality settings.

Original engine movie:
`tmp/south-fork-playable-v6-20260927/Windows/SmokeEmIfYouGotEm/Saved/VideoCaptures/RaftSim_20260927-121302.mp4`,
SHA-256 `ea117ef5f489e36303c7bdb7fa34a7aff3753832f518c7527a342f10f0aa0098`.
Decode receipt `tmp/sf-v6-troublemaker-decoded-20260927/report.json` verifies
770 frames,25.6333s,1280x720 and2 exact adjacent duplicates. Recording frame
rate is not game FPS. Reviewed original decoded1s,9s and20s views: boat and
paddles change pose and advance from displayed8.37km to8.40km; the raft reaches
large rocks and slows. Broad smooth reflective water/flat white foam and coarse
bank/rock shape remain visible. This is not convincing breaking-water realism,
proof of stable shoreline over time, or successful collision traversal.

Motion log `tmp/sf-v6-troublemaker-motion-20260927.log` confirms AllForward.
Logged raft speeds progress4.745,1.480,0.275m/s; the final sample has2 dry
support points and1 ground point. These observations do not alone diagnose
whether current direction, steering, inferred geometry or contact response is
responsible. Contact receipt with the same prefix and `-contact.json` contains
64 capped observations over15.4564..36.2351 world seconds. All resample the
NEW `ConveyanceEnvelope20260927/SM_ConveyanceGround` and match the solver's
float ground height; maximum vertical projection is0.01574287m. This is bounded
identity evidence, not a complete collision ledger or traversal acceptance.

The normal scene and rebuilt package now contain the coupled geometry/fields;
their visible delivery is verified, but an improvement in realism is not.
Keep South Fork first. Next investigate measured CPU surface/mesh-update work
and the rock-contact route, without repeating the completed cook/build or
turning on a broken solver. The unsettled150s hydraulic state and abnormal
installer shutdown remain open; later rivers and release acceptance stay gated.

## V6 crest diagnosis and exact150→300s continuation

The prior goal turn completed validation and changed the next action: v6 was
not accepted. This follow-through uses the current coupled fields, not a repeat
of the older v5 diagnostic. Packaged process4116/session44439 exits0; recipe
`tmp/profile-sf-v6-crest-shape-20260927.ps1`. Same executable and normal FullReach
at8330m, ephemeral profile, AllForward, no solver/material/quality overrides.
Stage instrumentation makes this diagnostic unsuitable as a new FPS baseline.

At10.17255s the persistent shared-crest report contains7 sites, heights
0.109499..0.211680m. Only1 has positive spilling fraction,0.0519040; all others
are zero. The raw detection audit has68 candidates,20 accepted before site
consolidation, and equal raw/optical rises at the logged precision. Neither the
candidate count nor the spilling fraction proves physical realism.

Actual-submitted topology at10.01377s:42,343 triangles,1,303,200 sampled points,
maximum target crest error0.905407cm, fine-correction tracking1.295259cm and
zero source-anchor displacement (8,183 audited anchors). The coarse regular-grid
error6.82313cm is NOT the actual submitted-mesh error. More tessellation and
lowering the breaking onset have no support from these results.

Receipts: `tmp/sf-v6-crest-shape-20260927.log`, `.json`, and
`.json.cartesian-mesh.json`. The existing SetMesh CSV scope includes crest
refinement; it must not be added to the refinement scope or called upload cost.
In this instrumented8330m run, logged frames120..399 contain142 rebuilt calls
and139 cached calls (calls, not unique frames). Rebuilt crest mean11.6530ms,
selection7.3315ms (sampling3.6326ms, assembly2.8913ms), targets1.5650ms,
vertex work1.3824ms, topology publication0.2703ms and normals1.1037ms.
Cached calls average1.6875ms. This narrows the CPU investigation, not a speedup.

Because the new150s fields still have substantial regional storage drift,
continue that exact state before another geometry refit or presentation change.
Preparation session98932 completed; input:
`tmp/troublemaker-envelope-restart150-input-v1-20260927/manifest.json`, SHA-256
`c7fb7d8719184c013d226bc914a9555a225c173c9e5ebd384229e5cd6d29d9ea`.
No bank context or water was added. Geometry manifest remains
`0007939ed34e8cfcc033623f7bbeb5c20e5f4982e7553928a69bac7f15789738`.
Native restart audit verifies all5,382,400 h/u/v cells bit-exact, zero volume
error, identical clock and all retained grid/bed/roughness/boundaries/settings.
Report: `tmp/troublemaker-envelope150to300-restart-v1-20260927.json`.

ONE continuation is LIVE as solver PID35776, wrapper30456, shell session42718;
recipe `tmp/continue-envelope150to300-v1-20260927.py`. Qualified solver SHA-256
`458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`,
3,000 additional0.05s steps, snapshots every1,500 steps,8 workers. Output:
`tmp/troublemaker-envelope150to300-v1-20260927`; process receipt:
`tmp/troublemaker-envelope150to300-process-v1-20260927.json`.
Native local frame003000 will correspond to absolute300s; do not request6000.

The owned wrapper independently checks the actual native restart, waits for
the same child process, records its real exit, and runs final state, dry-bank,
regional-storage and station analysis. Final report prefixes:
`tmp/troublemaker-envelope300-{state,banks,storage,analysis}-v1-20260927`.
Observation timeouts are not terminal and must not trigger a second cook.
Inspect those results before deciding on a further continuation or runtime
export. No automatic scene install or acceptance follows from completion.
Normal v6 remains unchanged; this is supporting hydraulic work, not a new
visible improvement. Preserve the full reconstruction and release queue.

## Restart station-analysis repair during the same live continuation

Inspection found a concrete upcoming failure in the owned final-analysis
command: `prepare_cartesian_snapshot_restart.py` does not duplicate
`station_map.npz`, while the analyzer required it in the restart directory.
The solver does not use that diagnostic file and is unaffected. No solver
restart, captured-source edit, state transfer or new engine run was needed.

`analyze_south_fork_discharge_bed_cook.py` now resolves the map through the
restart's hash-verified source-manifest ancestry. Every hop requires identical
geometry identity and ordered packages, unchanged retained physical settings,
actual scenario/grid/bed/features/probes checks and zero added context/water.
Missing maps without valid ancestry fail closed; an expanded domain requires
its own map. The report records the exact map path/hash and inherited status.
Only analysis reads the ancestor; native h/u/v still come from the requested
new cook snapshot. No old flow arrays are substituted.

The first stricter map-validation trial rejected3,750,110 intentionally
unassigned dry-cell stations. Preparation uses NaN there, and those cells never
enter the captured-water station bins. The corrected contract requires matching
array shapes and a boolean mask, with finite station/surface for every captured
water cell. A regression retains these dry NaNs without admitting nonfinite
water samples.39 tests pass in2.48s, including exact full-analysis comparison,
multi-hop ancestry and14 changed-input rejection cases. Test output:
`tmp/restart-station-analysis-tests2-20260927`.

Actual end-to-end proof (exit0):
`tmp/troublemaker-envelope-restart150-analysis-proof-20260927/report.json`.
It analyzes native frame000000 of the running continuation at absolute150s.
All summary fields, all station bins and the mass-balance block are exactly
equal to the original150s analysis. Inherited station-map SHA-256:
`207694af0285b46ed8524b54240587e98c1c38bbb381ed0fd0d1d8eb6d2d6097`.
The queued final subprocess loads this repaired analyzer after the cook ends.

The same native process/session remains live beyond200s. An observed209.5s
checkpoint has maximum step conservation residual8.47e-9m3; this is intermediate
progress, not a final safety, settling or visual pass. Continue session42718 and
its recorded outputs. Do not duplicate preparation or replace this work with
another unchanged initial-state analysis. Next inspect final300s safety and
regional/rapid behavior before selecting the next playable field candidate.

## Scoped save protection for the next data-only field trial

The existing `bind_south_fork_discharge_bed_runtime.py` promised to save only
the config actor, but its failed actor-save fallback called `save_dirty_packages`,
which could persist unrelated editor work. It now calls `save_packages` with
only the config actor's external package. A failed save raises without a bulk
fallback or success receipt. Invalid modes and existing/outside-tmp report
paths are rejected before loading the scene; paths are resolved before checking
containment, so `tmp/../outside.json` is not accepted.

Seven mocked regressions pass in0.51s:
`physics/tests/test_south_fork_runtime_binding.py`, temporary fixtures in
`tmp/runtime-binding-scope-tests-20260927`. These exercise save scope, failure,
read-only inventory, invalid mode and report confinement. They are not native
Unreal save/reload validation or a runtime payload closure check. Existing
`load`, `entries` and `package_file` helper contracts are unchanged.

No binding command, asset save, export, rebuild or engine timing was run in
this follow-up. Normal v6 remains unchanged and unaccepted. The SAME native
solver35776/wrapper30456 is still progressing: observed local step2160,
absolute258s, maximum step conservation residual9.1124e-9m3. Final300s audits
remain owned by that wrapper; do not duplicate it. Review the final physical
state before deciding whether new fields warrant a normal playable trial.
