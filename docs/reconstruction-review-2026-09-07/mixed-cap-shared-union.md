# Mixed-cap shared union validation — September 25 UTC

Supporting work only: no playable geometry, collision, cooked flow or staged
executable changed. South Fork remains unfinished; later rivers remain queued.

The shared SourceRockUnion now accepts an explicit mixed-survey schema. It checks
2019 vertices against the retained source array and the 2021 vertex against its
original LAZ point record, source hash, compound CRS and classification. It rejects
withheld points, unknown datasets, invalid indices, moved vertices, relabelling,
legacy index ambiguity and nonzero vertical adjustments. This verifies captured
positions, not rock identity or underwater flanks.

The first candidate manifest accidentally inherited the parent's closure counts
and volume. It is preserved but now rejected. Preparation writes a separate v2
manifest using the candidate construction receipt, and the shared loader checks
those statistics against the reconstructed solid.

- Corrected manifest: `tmp/troublemaker-mixed-support-candidate-20260925/rock_cap_manifest-v2.json`
- Manifest SHA256: `1d37ed2dd4e9b53b55da3a76c8dc81ef9d811d389086b15a808b523492ec7558`
- Cap SHA256: `2ce993c54e489cf42a9773f5b8f34def310586f9b785c03325af0477033ae4b6`
- Volume: 2086.5066174418944 m3; manifold edges: 9642.
- 41 focused provenance, shared-union and metadata tests passed.
- Actual corrected candidate loaded successfully; actual superseded manifest
  failed specifically on stale closure statistics. `git diff --check` passed.

Follow-through: explicit `--replace-union` now reconstructs the previous union
using its own cap and terrain-revision descriptors and checks its exact identity.
Replacement preserves that bed revision and reconstructs the new geometry from
original source fields. Cells outside a smaller replacement revert to source,
not the previous cap. Two additional regressions cover dependency identity and
full preparation with tampered-core rejection before output: 43 tests pass.

Actual preparation completed at
`tmp/troublemaker-mixed-union-geometry-20260925/manifest.json`, SHA256
`6876cc58378b51627f1516153303614c027e38139b935185c2f0f70386960b6a`.
It checks all 841 cores / 5,382,400 cells against source provenance. Compared
with the previous constriction-source union (not merely the original terrain),
exactly one bed cell changes, by -1.1749487100640579 m. The registered terrain
revision identity and captured surfaces/masks remain exact. The generated
manifest predates the subsequent wording-only clarification of its notes.

Next: fresh source-stage flow initialization, matching runtime packets and
collision/render geometry, then engine validation before playable promotion.
No cook was started and no evolved water state was transferred. Normal-launch
motion, appearance and performance acceptance remain open, including the existing
p95 frame-budget failure. The constriction base is a verified prior candidate;
this report does not establish that it is the installed normal-scene bed.

## Normal-baseline follow-through

The saved runtime bundle `south_fork_source_matched_v2` points to the
control-ablation 4950s runtime, whose cook input identifies
`tmp/south-fork-control-ablation-union-geometry-v1-20260916/manifest.json`.
Its bed revision is the control-ablation revision, not the later constriction
candidate. Preserve this baseline for the bounded cap update. The earlier
constriction-based fresh inputs were generated but were not cooked or installed.

Normal-baseline replacement geometry:
`tmp/troublemaker-mixed-normal-baseline-geometry-20260925/manifest.json`, SHA256
`7805eff51f8be11b6878a194c50920ce99870bd1507e016e0ba3050b89d3021b`.
All 841 original cores passed provenance checks. Matching runtime packets at
`tmp/troublemaker-mixed-normal-packets-20260925/manifest.json`, SHA256
`b3f403d95defad4d1c1e82b38f6b04be77df74897e909e7968be5ee5cb0ed54d`, pass
independent reconstruction of all 799 regions (eight derived packets).

Fresh inputs are at `tmp/troublemaker-mixed-normal-fresh-input-20260925`.
The first audit found that the retained cook's copied input manifest has no
adjacent scenario packages. The audit now accepts an explicitly supplied original
manifest only if byte-identical, then still hashes every package dependency.
The original is `tmp/control-ablation-4900to5400s-input-v1-20260917/manifest.json`.
The rejection regression and existing shared-union tests pass (31 tests).

Collision targets at `tmp/troublemaker-mixed-normal-collision-probes-20260925.json`
were reconstructed from the same geometry: 30,066 baseline and 34,887 combined
targets. These are targets, not native collision passes. No solver, engine import,
normal-scene mutation or new acceptance occurred in this step.

## Export and fresh pilot follow-through

The full fresh-input audit passed all 841 cores / 5,382,400 cells; receipt:
`tmp/troublemaker-mixed-normal-fresh-input-audit-20260925.json`. Initial volume
is 3022042.2917456147 m3, inflow 45.30695454719999 m3/s, no evolved-state transfer.

Mixed-source Blender export now requires a hash-matching completed shared-union
geometry and audit rather than the legacy manifest's closed-solid boolean. A
changed-provenance rejection regression passes. Actual Blender 5.2 export:
`tmp/troublemaker-mixed-normal-rock-export-20260925/manifest.json`, 3214 vertices,
6428 triangles, no decimation. FBX SHA256:
`f9ddf163fb5b91f4350f42f309be360da8ef6106e846cdbe6727cf387739304a`.
No native import/collision or visual acceptance yet.

One bounded native fresh pilot was started for 1000 steps / 50 simulated seconds,
four workers, snapshots every 1000 steps, output:
`tmp/troublemaker-mixed-normal-fresh-50s-20260925`.
At this entry it is LIVE, exec session 92780, PID 33552, started September25
00:56:10 local. Last sampled progress: step90 / 4.5s, conservation residual
2.5170265871565789e-10 m3. Do not restart based on this note: poll the session
or inspect the process/output for current authoritative status first. No settling,
normal-scene installation or performance acceptance is implied.

## Native import follow-through

48 combined provenance, union, export-authority and directed-hash tests pass.
Transient Unreal import was attempted with no saves. Commandlet mode cannot
provide StaticMeshEditorSubsystem; the preserved failure receipt is
`tmp/troublemaker-mixed-native-import-20260925.failure.json`. Use full editor
`-ExecutePythonScript`, not `-run=pythonscript`, for this importer.

Full-editor process exited0, but the actual report explicitly FAILED:
`tmp/troublemaker-mixed-native-import-20260925.json`. Exit code is not acceptance.
It contains all6428triangles, CPU-accessible collision LOD0, and flip_normals=true.
The directed provider hash is
`3745f79c8609822b440fd085b0f718f051b1cf63d798e5156df64ba355ba6e69`;
the initial source-order expectation was
`2e0d15fd67af14df240476824917a89a5371aa254a358ba9e91d78d3d3008839`.
Independent recomputation exactly matches the actual provider when every source
triangle reverses winding; unreflected and Y-reflected alternatives do not match.
Thus this is an exact winding convention difference, not lost triangles or moved
float32 positions. The native hash implementation deliberately does not apply
bFlipNormals. Do not merely replace the expected hash to claim full acceptance:
verify effective collision orientation and actual full-map traces first.
No saved scene or asset changed. Full-editor log:
`tmp/troublemaker-mixed-native-editor-20260925.log`.

The same pilot remains live (session92780/PID33552); latest inspected on this pass
was step350/17.5s. No second cook was started. Native import sessions70778 and
68291 failed in commandlet mode; full-editor session43035 is terminal.

## Effective collision orientation verified

Full-editor session60267 completed exit0 with a passing report at
`tmp/troublemaker-mixed-orientation-20260925.json`, copied to
`independent-lidar-followup/mixed-cap-native-orientation.json`.
All6428source-face centroids were traced from their independently computed
outward side in the actual actor frame (scale1,-1,1), checking position, impact
normal and actor ownership. No face was omitted:2966roof,2966internal-bottom,
496inferred-wall queries. Maximum position errors were0.000283,0.000169 and
0.000246cm respectively; minimum normal dot was0.9999999993. No failures.

Local UE5.8 StaticMesh.cpp explicitly sets collision-provider bFlipNormals=true.
Together with exact reversed directed-triangle identity and the actual traces,
this resolves the isolated orientation discrepancy without moving vertices or
loosening tolerances. Preserve the earlier failed source-order assumption report.
This is NOT full-map collision, raft traversal, rendered appearance or hydraulic
acceptance. No asset or level was saved. Next use the installed normal-scene
ground and replace its cap transiently for full-map union checks, then paired
runtime validation once the fresh pilot finishes.

The pilot remains the original session92780/PID33552; latest inspected step520,
26simulated seconds. Poll it rather than starting another cook.

## Installed-scene collision union verified

The no-save check loads the normal South Fork map, verifies installed ground and
cap package/native hashes, preserves the ground, swaps only the existing cap
actor's mesh, then restores that mesh. Its first invocation had a verifier-only
map-extension typo, corrected from uasset to umap before the actual trace run.

Legacy rays produced nine failures; preserve
`tmp/troublemaker-mixed-installed-union-20260925.json`. Eight hit another part of
the exact nonconvex source solid first; independent segment intersections match
their native hit distances. The ninth legacy ray remains unexplained by isolated
source-solid intersection alone and is not waived as a passing legacy query.

The existing source-visible construction supplies ALL1607original vertices,
without moving targets or changing tolerance. Every ray is certified against
the closed source solid; all remain100cm half-length, max source first-hit error
5.51e-11cm. Legacy6676probes remain preserved alongside the added vertex probes in
`tmp/troublemaker-mixed-visible-probes-20260925.json`.

Full-map source-visible run session71515 is terminal, exit0, with actual report
passed=true: `tmp/troublemaker-mixed-installed-visible-union-20260925.json`, copied
to `independent-lidar-followup/mixed-cap-installed-union.json`. All34887queries
pass, including25600hydraulic cells,4466registered-ground centroids, all1607roof
vertices,2966roof centroids and248boundary midpoints. Largest error0.031770cm;
the physical0.1cm gate is unchanged. Actual cap/ground ownership also matches.
Original cap restored;472protected saved files unchanged. No scene/asset save,
water update, raft traversal, visual or performance acceptance.

Cook remains original session92780/PID33552; latest inspected step800/40s.
Next audit its terminal1000step snapshot, then export matching runtime fields
and proceed to native water/mesh consistency and normal-play validation.

## Fresh50s pilot terminal and runtime export

Original cook session92780 finished exit0 at step1000/50s, wall1428.60s.
Do not poll or restart it as if still live. Snapshot audit passes5382400cells:
maximum depth4.277084m, speed12.166877m/s, maximum step conservation residual
1.18348e-8m3. Artificial-bank audit finds all86720bank cells exactly dry.
Reports are retained in `independent-lidar-followup/mixed-cap-50s-snapshot.json`
and `mixed-cap-50s-banks.json`. This is NOT settled flow: final inlet45.306955m3/s
versus outlet27.973981m3/s leaves substantial positive storage change. No normal
scene promotion is justified by numerical sanity alone.

Runtime export `tmp/troublemaker-mixed-normal-runtime-50s-20260925` completed
exit0 (session59299),841atlas tiles and799packets, verifying42185039overlap bed
cells.791unchanged packets reuse733751375bytes; eight union packets are new.
Atlas SHA256 `3b6bdc88650c46a21f30bb17ccf0b58810cd265a3ee02ccb0c01996b2a95b8af`.
Exact25600native query expectations are prepared at
`tmp/troublemaker-mixed-normal-runtime-expectations-20260925.json`; not yet run
in Unreal. They cover the same hydraulic-cell queries as the collision proof.

Continuous coverage audit (session35609) finished exit0. The initial declaration
had two unavailable cells in region0002. Existing constrained-center repair
produced `streaming_manifest_coverage_checked.json`, SHA256
`619f31d25c81b53fc47ab01fe865b1480c92f7f4430723ee14a5a1c3dab5867f`.
It verifies all406823original water probes with10mminimum interior margin,
797continuous center rectangles;3822centers move, maximum102m. No terrain or
water sample is fabricated. Preserve both the original failure and corrected
coverage evidence (`independent-lidar-followup/mixed-cap-runtime-coverage.json`).
This center change still needs actual engine window/motion review. All processes
started in this step are terminal; no active cook remains. Next run the native
water-query expectations and actual moving/visual checks with matching cap.

## Native field comparison completed; preview source retention hardened

The native Unreal adapter completed all25600 matching hydraulic-cell queries
with zero wet mismatches and no failures. Maximum bed/surface error is
7.62939453125e-6m; depth error1.1918204823e-7m, velocity component error at most
2.3817516670e-7m/s. Receipt:
`independent-lidar-followup/mixed-cap-native-runtime.json`. The engine ran no
solver steps and saved no assets or levels. This proves loading/sampling of the
50s candidate, not hydraulic settling, moving-window behavior or visual motion.

Preview dependency binding now also requires and hashes the independent LAZ,
parent manifest and construction receipt for mixed-survey caps. Missing or
changed records are rejected; all six dependencies of the actual candidate
verify. Preview and mesh-staging regression suites pass80tests. This closes a
provenance-retention gap before ephemeral play, not a playable delivery.

No cook or editor remains live. Normal scene and staged game are unchanged.
Next work remains matching-cap rendered/moving review, followed by a justified
playable increment; do not install the unsettled50s pilot merely because these
sampler checks pass. South Fork remains first and unfinished.

## Matching-cap actual PIE review completed

The unsaved normal-map preview now runs fresh full-map collision and native
field checks before play, swaps only the existing cap actor, preserves its
material, and verifies exact candidate/ground presence plus water configuration
inside PIE before requesting captures. No map or asset package is saved.

Initial upstream launch failed candidate-presence verification before capture;
retain `independent-lidar-followup/mixed-cap-pie-upstream-failure.json`.
The retry used the existing `-RaftSimWaterReviewStation=8330` override; engine
log confirms requested/applied8330m and region0190, then moving region0193.
Actual PIE verified one candidate, one retained ground and zero old caps.
All three screenshots completed and the session ended, exit0,50.36s wall time;
protected files unchanged. Receipt: `independent-lidar-followup/mixed-cap-pie-crux.json`.
Screenshots remain at `unreal/Saved/Screenshots/mixed-cap-pie-crux-20260925_00[0-2].png`.
First capture records raft station8353.026m, not a stationary fixture.

The inspected final engine frame shows frothy water and strongly faceted rock;
this is not photographic acceptance. No timing acceptance is inferred from
capture wall time. This PIE session is not normal packaged startup or settled
hydraulics, and does not prove full-reach shoreline stability or contact safety.
Normal staged game remains unchanged; no cook/editor process remains live.

## Existing crease shading carried into mixed-source candidate

The new mixed-source FBX had used the flat exporter default, unlike the installed
cap's previously reviewed45degree crease shading (see landward-rock-shading).
Fresh export `tmp/troublemaker-mixed-crease45-export-20260925` carries that same
authored choice without moving any source vertices or triangles. Export FBX SHA
`e41c65571d84c5bd0216ac17b93ca607f54b83916f74d1c98a63ba90c712deee`.
All6428native directed collision triangles retain the exact previously verified
hash; native shading vertex splits increase the provider count to4749.
Actual normal-map union collision passes34887queries and paired native water
passes25600queries again, before play. No solver/bed/flow change or recook.

Crux PIE session19653 is terminal exit0,51.78s wall, threecaptures complete,
472protected packages unchanged. Reports/export retained under
`independent-lidar-followup/mixed-cap-{pie-crease45,crease45-collision,crease45-export}.json`.
Actual images: `unreal/Saved/Screenshots/mixed-cap-pie-crease45-20260925_00[0-2].png`.
Compared final frame at the same camera with the flat candidate: triangle-level
lighting is reduced, while jagged silhouette and inferred flanks remain plainly
visible. Separately evolved water states preclude pixelwise water comparison.
This prevents a candidate shading regression; it is NOT a new normal-game
delivery, measured normals, photographic acceptance, settled flow or FPS proof.
91shading/preview/staging regression tests pass. Further smoothing alone is not
the next geometry solution; retain the source-supported cap and address the
remaining shape evidence, hydraulic settling and measured whole-frame cost.

## Recorded candidate motion inspected

Decoded the already-completed crease45 PIE recording, without another scene
launch: `unreal/Saved/VideoCaptures/RaftSim_20260925-013802.mp4`, SHA256
`0de97403339fb5f8cf2202c839e422685841888237575972f819a5067925e05b`.
Existing decoder `tmp/decode-constriction-motion-20260918.py` completed exit0:
627frames, strictly increasing timestamps0..20.866667s,2742x1222,4exact adjacent
duplicates. Receipt: `independent-lidar-followup/mixed-cap-crease45-motion.json`.
Engine log reports292source frames over20.915s; codec repetition/compression
means neither decoded count nor exact-duplicate count establishes game FPS or
the number of independently rendered frames.

Inspected decoded3s/11s/20s frames together. Raft moves downstream out of view;
foam patterns evolve with no whole-water disappearance in these samples.
Broad bright foam patches and jagged rock silhouette remain. These sampled
frames do not prove every-frame shoreline continuity, sustained wetting,
collision robustness, photographic fidelity or crew animation acceptance.
Engine capture metadata advances station8358.575→8385.765→8413.941m at world
12.823→22.427→32.437s. Logged wet support persists with zero reported ground
penetration at the sampled telemetry times; no continuous collision claim.

This closes the uninspected-recording gap for the candidate, not the visual or
performance gate. No normal launch changes, new cook or source edits. Next
visible work must address source-supported shape and local froth structure,
not another identical playback or another smoothing-only trial.
