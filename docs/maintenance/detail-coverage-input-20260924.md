# Full-route coverage input validation

Supporting regression work, not playable or geographic acceptance.

The native `RaftSim.M3.DetailFullRouteCoverage` gate previously iterated the
route's `points` without validating that it contained any rows. An empty route
could therefore report zero missing footprints after performing zero queries.
Malformed rows also reached unchecked array/numeric access, and the required
footprint calculation's failure result was ignored.

The gate now requires at least two rows with finite numeric station/XY/side
normal coordinates, strictly increasing stations and unit side normals
(squared-length tolerance1e-4). Invalid input produces an explicit error.
Required-footprint failure stops the test. The total query count must equal
three times the validated point count. Explicit initialization removes the
compiler's C4701 warning without changing the first-sample origin behavior.
No production sampling, source coverage limits, terrain or flow was changed.

Native malformed-route cases cover missing/empty/single-row input, short rows,
non-numeric coordinates, duplicate stations and zero normals, plus valid input.
Editor build succeeds in69.37s with no C4701 warning:
`tmp/detail-coverage-input-editor-v1-20260924.log`.

Native input/footprint/crop/full-route suites:4 passed,0 failed,0 warnings;
`tmp/detail-coverage-input-native-v1-20260924/index.json` and matching `.log`.
The actual playable coordinate map produces52,689 detail/closing footprints at
three side offsets,0 missing, against
`tmp/control-ablation-runtime-4950s-v1-20260917/streaming_manifest_coverage_checked.json`.
This tests metadata selection, not water evolution, collision, river navigation,
motion or performance. No standalone Game rebuild is claimed for this test-only
change. Non-Windows SDK availability messages in startup are not release passes.

Original hydraulic cook36692 remained live; no duplicate or replacement cook
was launched. Installed fields and nonlinear mode remain unchanged. South Fork
and the full ordered reconstruction/release scope remain open.
