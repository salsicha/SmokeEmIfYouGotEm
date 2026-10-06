# Hydraulic bed versus actual terrain triangles

## Finding and correction

The render/collision export splits every source quad into triangles `(a,b,c)`
and `(b,d,c)`. The hydraulic cook instead used bilinear interpolation between
the same four heights. A shared source-raster hash therefore did **not** prove
that both consumers used the same continuous surface between its vertices.
The earlier 16 collision probes were at source vertices and could not detect
this mismatch.

`south_fork_mesh_sampling.py` now provides the exact triangle sampler and the
mesh export's shared face-index generator. Fresh survey cooks default to
`render_triangles`. A continuation/refinement without an explicit override
inherits the parent's method; old registrations without the field remain
`bilinear`. An unregistered raw resume requires an explicit method. Changed
methods are rejected by continuation/refinement and resolution-only comparisons.
Exported review packages now verify and record the method alongside source
geometry identity. No captured source vertex, rock height or mesh asset changed.

## Actual engine verification

Sixteen off-vertex points selected near the rapid were traced against the
existing, full-triangle collision mesh in `SouthForkSurveyPlayable`. Maximum
triangle-sampler error is **0.000265 cm**. Maximum bilinear error at those
same points is **104.303 cm**. These are numerical agreements/disagreements
with the game's terrain, not real-world survey accuracy.

Across cells wet in each loaded scenario's initial state, the old sampler
differs from the source triangles by over 10 cm in 138 one-metre cells and
454 half-metre cells; the respective maximum differences are 0.773 m and
1.328 m. Different initial wet masks were used for these counts, so they are
not a convergence test. The whole-grid maximum is larger than the maximum
within the engine probe selection.

The initial headless trace attempt found a missing hit before asset compilation
completed. Its failure remains in `SurveyInteriorMeshAudit.log`. The corrected
audit finishes pending asset compilation first, records every hit, and passes
all 16 probes. `SurveyInteriorMeshAuditCompiled.log` and
[engine-interior-mesh-audit.json](engine-interior-mesh-audit.json) retain the
actual result. No map was saved; its SHA-256 remains
`28a26ed62d95403d964a23dcef00382dbbb063415b3ca85f87df36362b07c6cb`.

The [probe definitions and full-grid measurements](interior-mesh-probes.json)
identify both methods and their samples. The shared topology/sampling/restart
suite passes **33 tests and 39 subtests**; another **11 export/sanity tests**
pass. No native C++ solver or engine binary was changed or rebuilt.

## Source review: do not fill the pocket blindly

The [registered source review](rock-pocket-source-review.png) shows the largest
previously localized fluctuation near a rock tip adjoining open water. Most
inferred cells around it have no returns. One nearby inferred cell has a single
accepted high return; others have water-class returns. This does not justify
lowering the acceptance threshold everywhere, treating water as rock or filling
the open pocket. The [return inventory](rock-pocket-source-review.json) keeps
the original classifications, filtered counts and source hashes. Registration
uncertainty remains approximately 3 m; no rapid identity was promoted.

This inspection led to fixing the independently provable interpolation bug,
not inventing new measured terrain to make a hydraulic test pass.

## Corrected cook: finite, conservative, not yet accepted

Separate run: `1m-mixed-inlet-mesh-triangles-20260907`. It uses 6,000 steps at
0.1 seconds / CFL 0.2, from a fresh initial state, and finishes in 421.918 wall
seconds. Source geometry, discharge (45.30695455 m³/s), inlet/outlet stages and
roughness are unchanged. The source is sampled as the actual mesh triangles.

All 13 saved frames pass the candidate sanity screen. Tail section error is
3.586% (passes 5%); interval storage rates are -0.13045, +0.02828 and -0.19865
m³/s (passes the 0.90614 limit). Crux median stage varies **10.612 mm** over
450–600 seconds, exceeding the 10 mm screen. The overall mean-flow screen
therefore remains failed; no threshold was relaxed or extra extension run to
obtain a passing tail.

The independent face-flux audit passes: inlet 45.30695455 m³/s, outlet
46.96378435 m³/s, no side leakage; net -1.65682981 m³/s matches measured
tiny-step storage derivative -1.65683014 m³/s. This is conservation, not
instantaneous steady-flow acceptance.

Evidence:

- [Mean-flow report](../reconstruction-review-2026-09-06/troublemaker_survey_flow_1m-mixed-inlet-mesh-triangles-20260907.json).
- [Actual numerical face-flux audit](../reconstruction-review-2026-09-06/troublemaker_numerical_boundary_flux-mesh-triangles-20260907.json).
- [Regional stage/storage history and hotspots](triangle-cook-regional.json).
- `tmp/south-fork-survey-hydraulics/1m-mixed-inlet-mesh-triangles-20260907/engine_review`:
  separately exported, explicitly unaccepted package, recording
  `source_bed_sampling: render_triangles`; **not loaded into the scene**.

## Handoff

The loaded review still uses the previous bilinear hydraulic package; the
source/render/collision mesh is unchanged. The new package must not be presented
as an in-game fix already seen by the user. Do not rerun the old mesh importer
or overwrite the old package. A future staged field switch must preserve its
rollback, update the candidate-specific runtime fixture/opt-in field identity,
and validate actual animation, contact, raft support, tracking and performance.

Any next resolution comparison must use triangle sampling on both grids, not
mix this result with the old bilinear fine-grid history. The broad crux
resolution discrepancy has not been shown to be resolved by this correction.
Underwater geometry remains inferred; South Fork and all later rivers remain
unfinished. No commit/push or asset/map save was made. All owned diagnostic
processes completed.
