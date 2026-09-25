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
