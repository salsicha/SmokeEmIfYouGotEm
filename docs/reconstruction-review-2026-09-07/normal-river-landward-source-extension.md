# Landward source extension and physical-union checks

September 15, 2026. Reconstruction candidate, not visual/playable acceptance.
The preceding goal turn made progress by committing the source-connected cap
builder and tests (`e94405eb7`). This turn reviewed the actual result before
using it in a physical union.

## Why the unrestricted extension was not promoted

The unrestricted v3 candidate retained all 1,021 prior roof triangles exactly,
but grew from 115.922 to 441.649 m², acquired five holes and reached apparent
whitewater in the original registered aerial image. Its perimeter grew from
47.322 to 221.821 m. An endpoint-based positive boundary-gap area estimate grew
from 66.157 to 212.840 m². That estimate is NOT an exact parent intersection
or measured wall area, but it contradicts treating automatic expansion as a
resolved rock-foot reconstruction. There were 360 missing-neighbor edges.

Original class 1 remains unclassified. Continuity and height above a flattened
surface cannot distinguish exposed rock from all river or vegetation returns.
The 2019 lidar and 2022 aerial image are not contemporaneous; the aerial pixel
spacing is about 0.425 m and registration uncertainty remains 3 m.

The audit verifies the original sources, class labels, roof triangles and
closed solid, then plots the original aerial image without smoothing next to
both boundaries. Unrestricted evidence:
`tmp/troublemaker-source-connected-audit-v1-20260915/`.
The earlier v2 unrestricted triangulation also remains rejected: it changed
prior roof heights by roughly -0.986 to +0.382 m. No rejected artifact was
overwritten or promoted.

## Explicitly interpreted landward selection

[Selection record](troublemaker-landward-selection-20260915.json) binds the
reviewed landward search polygon to the original source/imagery hashes and
coordinate frame. It excludes the unrestricted south/east branch into apparent
whitewater; it is NOT a measured shoreline, rock outline, or surveyed flank.
The older roof is retained verbatim. Additional triangles cannot bridge the
review exclusions. Missing/excluded support is never treated as ground.
The selection hash is part of the physical-union identity, runtime packet
identity, and future ephemeral-preview dependency list.

Candidate: `tmp/troublemaker-source-connected-landward-v1-20260915/manifest.json`.
Manifest SHA256:
`606e5bab4bd269690c22327d4ccd27c59bd670d39f09d8585ff6a09629ca5bce`.
Cap SHA256:
`78f77b67c64dc98094522ad2a8362edd0bfeab422816c90dc668e2cc5dd2baeb`.

There are 1,601 exact original-return roof vertices (1,534 class 1 / 67 class 2), 2,954 roof triangles,
321.545 m² projected area, one connected component and one retained hole.
All prior roof triangles are bit-exact; centroid differences are arithmetic
noise below 9e-15 m. The entire closed solid has 6,404 triangles; none were
decimated. About 62.921 m of boundary has both endpoints within 0.3 m of the
retained parent. Steep gaps remain (maximum 3.689 m), along with 155 missing or
selection-excluded neighbor edges. The endpoint wall-area estimate is still
121.187 m². This is NOT a claim that the flanks are finished or correct.

Landward registered-image audit:
`tmp/troublemaker-source-connected-landward-audit-v1-20260915/`.
Both original and annotated aerial plots were inspected at actual source
registration; no game image was edited or substituted for an engine capture.

## Native collision: preserve failures and test the actual union

First isolated native run: 6,652 requested probes, 6,650 hits, 11 failures.
Nine long angled vertex rays encountered another source roof face before their
intended vertex. Independent double-precision segment/triangle intersections
reproduced their 5.32–99.48 cm early-hit distances. One vertical ray and one
old angled ray missed. These results remain in the v1 report.

Additional vertex directions now account for ALL incident source roof planes
(including coincident separated fans), with source visibility certified before
engine use. ALL 1,601 actual candidate rays retained the original 100 cm half
length; none needed shortening. Every one of the 6,652 legacy probes is also
retained unchanged in v2. Native additional-vertex result: 1,601/1,601 PASS,
maximum error 0.031770 cm at the unchanged 0.1 cm gate. All 2,954 roof-centroid
and 496 inferred-wall probes pass. The same 11 legacy failures remain;
`collision_verified` stays false, and no legacy failure is waived.

Reports:
`unreal/Saved/RaftSimValidation/source-connected-landward-collision-v{1,2}-20260915.json`.

Actual saved South Fork map plus transient candidate: **30,403/30,403 PASS**.
Both full 12,800-cell baseline/union grids, every roof vertex, every roof
centroid and every boundary midpoint are tested. The 37 vertices, five roof
centroids and one boundary midpoint covered by the retained parent are NOT
discarded: their original source targets remain in probe metadata, and the
physical union surface is tested at those XYs. Exactly 319 grid queries hit
the candidate; all other grid queries retain original ground. Maximum source
vertex error is 0.031770 cm; the unchanged gate is 0.1 cm. This sampled union
pass does not close the separately retained tangent/legacy gate or prove raft
contact/traversal.

Report:
`unreal/Saved/RaftSimValidation/south-fork-landward-full-map-v1-20260915.json`.
No asset or level was saved. Native verifier configuration is now explicit,
bounded to generated local-review inputs/assets and fresh validation reports;
existing callers retain their defaults.

## Fresh hydraulics and next playable review

All 836 original cores / 5,350,400 cells were checked before deriving new bed
geometry. Only 319 samples change (195 in core_0629 and 124 in core_0631).
Captured masks, stages, physical endpoints, roughness and imposed discharge
45.3069545472 m³/s remain unchanged. No evolved old water was transferred.

Geometry: `tmp/south-fork-landward-union-geometry-v1-20260915/manifest.json`, SHA256
`5270d8c4bc41ba87132c4589792f4dacd2b23ab1f83ab90d8d45b5b70efefbd4`.
Cold input: `tmp/south-fork-landward-cold-input-v1-20260915/manifest.json`, SHA256
`801a56422fbb56bb3827adaf9f4355c668c04e86189d818be3d83ddcdaecd389`.
The first audit invocation incorrectly supplied the directory rather than the
manifest; it failed without a report. Correct-manifest audit passed without
rebuilding or restarting preparation.

One-second native pilot: snapshot/conservation and all 86,720 artificial bank
cells PASS (exactly dry); maximum step residual 5.220e-9 m³. This is NOT settled
flow. Reports: `tmp/south-fork-landward-pilot-{snapshot,banks}-v1-20260915.json`.

799 runtime source packets are prepared: eight changed, 791 verified reused,
2,552 overlapping changed samples (=319 × 8); all altered fields recomputed
against the shared source union. Manifest:
`tmp/south-fork-landward-source-packets-v1-20260915/manifest.json`, SHA256
`8dcc26975c48a0aa56600bc3ecb0890f322b527e7f3eec840f72e80f72e9e21a`.

Fresh 50-second review cook started with the SAME verified solver executable:
`tmp/south-fork-landward-cook50s-v1-20260915`, session59493 / PID24324,
1,000 steps × 0.05 s, final snapshot interval 1,000. Confirmed live by process
identity and progress. The separate previous-geometry 600-second cook remains
live, session45187 / PID32276; its 250/300/350-second snapshots and banks passed
independent audits, but discharge is still not settled. Never mix their states
or restart either run because an observation times out.

NEXT: finish and audit the landward 50-second snapshot; export source-matched
runtime atlas, prove original-water coverage and native field agreement;
stage its exact mesh/retained material and joint ephemeral descriptor; compare
actual playable motion/captures with references. The staging script still
contains old-candidate report paths/triangle counts and must be parameterized
without weakening its native-runtime/material gates. Do not install a
visual-only prop or use the old v4 water state on the landward bed.

## Remaining acceptance

All 105 focused source/union/ray/configuration/preview tests pass (report
`tmp/source-connected-landward-final-tests-v2-20260915.xml`); all 464 protected
source and actor hashes match. No default scenario, shader, material, physics
threshold, collision tolerance or source asset was changed. This turn does NOT
prove convincing terrain/froth, breaking waves, raft contact or 30 FPS. Last
ordinary performance remains 24.225877 FPS / p95 47.78 ms (FAIL). Colorado →
Pacuare → Futaleufu, Chilko/Zambezi/all-scene water, crew, normalization, 13
physical and four presentation regressions and release remain open.
Troublemaker is still a rapid within South Fork, never a menu scenario.
