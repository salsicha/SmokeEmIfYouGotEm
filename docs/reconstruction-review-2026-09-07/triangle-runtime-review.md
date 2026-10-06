# Triangle-sampled South Fork candidate: actual runtime review

The corrected hydraulic package is now staged in the existing isolated
`SouthForkSurveyPlayable` review. This supersedes the earlier export-only
status; production scenes remain unchanged and unaccepted.

## Guarded integration

`stage_south_fork_triangle_review.py` verifies the previous map SHA, geometry
bytes, exported array hashes, both sampling declarations and mesh-source
hashes before changing anything. It traces the 16 off-vertex collision probes
again and preserves an exclusive rollback copy. It changes only the water
package/coordinate-map references and matching upstream raft/player start.
It refuses a later map revision, an existing backup/report, unsafe saved
history or a mismatched package. Nine new safety tests pass; the combined
staging, route and sampling suite passes 26 tests plus 21 subtests. The final
expanded suite, including export identity and saved-field sanity, passes
**37 tests plus 21 subtests** (`triangle-runtime-regressions-final.xml`).

- Package: `tmp/south-fork-survey-hydraulics/1m-mixed-inlet-mesh-triangles-20260907/engine_review`.
- Method: `render_triangles` at hydraulic cell centres. The coarser hydraulic
  interpolation between its cells is still an approximation, not the exact
  full-resolution collision surface everywhere.
- Source SHA: `af6ea6676d8cea99d82fef9044fcc139952c6c1855868a7d136fa8afcfe3241a`.
- Rollback: `tmp/project-cleanup/SouthForkSurveyPlayable-before-triangle-fields.umap`,
  SHA `28a26ed62d95403d964a23dcef00382dbbb063415b3ca85f87df36362b07c6cb`.
- Saved review SHA: `a54447bbc029acfe40dfed0cd3379e8119dab1cc49d304ead558d37b558ae7cb`.

Mesh and surface-lit material hashes are unchanged. No captured rock height,
inferred submerged geometry, native solver, physical force or acceptance
threshold was changed for this integration. The cook's 10.612 mm stage range
still fails its 10 mm settling screen. [Staging evidence](triangle-engine-integration.json).

## Candidate-specific engine checks

The new `SouthForkTriangleCandidateReplay` checks this package's initial depth,
stage, volume and registration, then advances it for two seconds. The old gap
test deliberately retains its old bilinear fixture and is not counted here.
The opt-in shared-breaking identity gate accepts either exact review package,
never arbitrary fields or production maps.

The route planner now accepts separate input/output paths and refuses to
overwrite prior routes. The new route has 174 points and 0.741 m minimum
downstream-aligned planning-envelope depth. It remains a synthetic game-test
route over inferred bathymetry, not a measured real-river navigation line.
`-RaftSimSurveyGuidedRoute=docs/reconstruction-review-2026-09-07/guided-route-mesh-triangles.json`
selects it; the test rejects mismatched field path, depth hash, source identity
or sampling metadata. Traversal report schema v3 records its actual package.

Build succeeds. The actual-engine suite is **2/3**, not all green:

- Captured-ground contact passes.
- Triangle-candidate replay passes.
- Guided traversal reaches the outlet in **81.682 s**, but **5.145 m** maximum
  tracking error fails the unchanged 5 m criterion. Minimum sampled tube/ground
  clearance is 80.294 cm; no missing ground queries or grounded samples, 740
  wet samples. The single water/foam carrier and material checks pass, with
  up to nine breaking sites. Normal paddle commands only; no force override.

Raw report: `unreal/Saved/Automation/SouthForkGuidedTraversal_20260907_121859.json`.
[Engine suite](engine-triangle-fields/index.json), [retained run ledger](guided-review.json).
These are bounded diagnostics, not full-route or repeated robust acceptance.

## Appearance and clean performance

The actual fixed-camera captures at 6/9/12 seconds show changing foam and spray
on one surface. The main crest is still too faceted, froth too marbled/smooth,
and the diagnostic banks too plain. Visual acceptance remains **failed**.
Three snapshots cannot rule out intermittent animation artifacts.

![Corrected fields at six seconds](C:/Users/salsi/repos/SmokeEmIfYouGotEm/unreal/Saved/Screenshots/SurveyTriangleFields20260907_000.png)

![Corrected fields at twelve seconds](C:/Users/salsi/repos/SmokeEmIfYouGotEm/unreal/Saved/Screenshots/SurveyTriangleFields20260907_002.png)

Clean performance, separately from captures/tests/cooks: **18.990 ms mean /
24.632 ms p95**, 1,054 frames at 1280×720 / 87% internal resolution on the RTX
3060 Laptop GPU. Solver mean is 11.274 ms. Both frame and solver budgets fail.
The previous single-carrier run was 20.933 / 26.991 ms; these individual runs
do not prove a statistically reliable speedup. [Performance report](survey_performance_triangle_fields.json).

The performance/capture logs confirm the triangle package's coordinate map,
10,465 presentation vertices, 1.5 m spacing, analysis stride 2, hidden rapid
foam sheet and disabled separate volume core. The engine-linked solver archive
has not changed during this comparison.

## Remaining work

A separate native CPU experiment moved repeated grid bounds checks to one
shape validation per immutable spatial stage. Three alternating 100-step
pairs on this triangle scenario produced byte-identical saved frames, but
median native wall time including export changed only from 12.676 to 12.539 s
(1.09%). That is not a compelling gain, so the raw-pointer optimization was
**rejected and reverted**, not linked into the engine or used for any cook.
The pre-experiment solver code is restored; the no-index diff is empty apart
from line-ending normalization. Restored file SHA is
`e478b4f96d66566cd6eb1135bb31cb5a225088040b3e411f9f7455280ac5b4d2`;
the retained before-file SHA is
`4ed34c2abcb78b20414839da8eeca7917c89f51c4beb7ab727f33c002a113b73`.
Candidate source/binary and the A/B commands, timings and frame evidence are
retained in `tmp/south-fork-stage-access-20260907` and
`tmp/south-fork-stage-access-build-20260907`. The comparison's `passed` means
equivalence, not a performance-budget or physical-acceptance pass. Do not
mistake that unused candidate binary for the engine-linked solver.

Resolve CPU cost and crest detail, robust traversal and same-method hydraulic
resolution sensitivity. Keep the failed settling result visible. Production
route/terrain/fields/start migration and geographic rapid identity checks are
still outstanding. Colorado, Pacuare and Futaleufu remain queued behind South
Fork. All owned build/cook/editor processes have exited. No commit or push has
been made in this pass. Existing unrelated changes remain preserved.
