# Unused contact-shape elision — September 25 UTC

Rejected; not delivered to normal gameplay. The experiment skipped accumulated
contact normal/center/weight/compression for sections1–4, whose deformation uses
offsets/gradients but not chamber squash. All vertices, faces, offsets, gradients,
pressure and crease calculations were retained. No captured geometry changed.

Candidate Editor build succeeded166.71s; review-switch build succeeded10.69s.
Three native tests passed with engine exit0: authored hull identity, fixed-step
snapshot transaction and the new elision comparison. The latter compared128
exact pairs across32changing contact states, shading on/off and both orders.
Geometry, normals, tangents, UVs and topology matched. Mean deformation ms:
positions-only3.716137→3.127175 and3.712125→3.147634;
shaded6.133403→5.544550 and6.054460→5.608160. These are fixture timings.
Report: `tmp/unused-contact-shape-native-20260925/index.json`.

Normal Boot/menu-handler to South Fork FullReach, same Editor-game binary,
D3D12 adapter0,1280x720, ephemeral profile,900post-travel frames per run.
No full-hull solver flag. Candidate-only `RaftSimUnusedContactShapeReview`.
All four processes exited0 and produced one CSV each; strict audit rows60–840,
scope offset1, unchanged30FPS target. Mean/p95 frame ms:

| Run | Mean | p95 |
| --- | ---: | ---: |
| control-a |37.384118|44.882000|
| candidate-a |34.756625|44.558800|
| candidate-b |32.283836|41.392900|
| control-b |31.866603|41.032000|

Both candidate metrics improve in the first pair but regress in the reversed
pair. All p95 values FAIL33.333333ms. No repeatable whole-frame benefit proven.
Receipt: `tmp/unused-contact-shape-abba-20260925.json`; logs/audits use the
same prefix and run names. Audit reports retain CSV paths and SHA256 hashes.

Candidate implementation, API option, review switch and experimental test were
removed after this result. Do not repeat this unchanged experiment. No staged
executable, hydraulic field or source geometry was altered. Baseline Editor
restoration rebuild completed23actions, exit0, `Result: Succeeded`,167.78s;
log `tmp/unused-contact-shape-restore-build-20260925.log`.
No visual or reconstruction acceptance claimed.
