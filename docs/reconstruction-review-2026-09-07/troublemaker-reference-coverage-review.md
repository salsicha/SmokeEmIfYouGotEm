# Troublemaker: reference sequence and liquid-test coverage

Latest retry September14,09:08UTC: both browser runtimes fail initialization with
missing kernel-assets path (os error3), including one reset/retry; direct web
opens of both supplied videos return cache misses. No new footage inspected.
See [retry details](reference-review.md). Historical observations below are not
superseded by a newly successful viewing or continuous-motion measurement.

September 9 continuation. The preceding user-facing status turn was **no
implementation progress**. This pass adds inspected reference evidence and a
reproducible geographic coverage check; it does not accept or promote a scene.

## Reference actually inspected

The user's [John Elkins Troublemaker video](https://www.youtube.com/watch?v=ZEG1kvjNI30)
loaded in the browser after the text fetch failed. The visible page identifies
Troublemaker on the South Fork American River. Paused frames were inspected at
10, 20, 30, 35, 40, 45, 50 and 55 seconds of the 1:08 video. This was a sampled
visual review, not camera tracking or a calibrated motion reconstruction.

- 10–20 s: dark approach water, intermittent broken foam, exposed rock margins.
- 30–35 s: rock-constrained approach into a much more aerated section; crests
  have dark faces and discontinuous white breaking tops.
- 40 s: pronounced piled breaking water and an irregular dark trough directly
  ahead of the raft, not an evenly white sheet.
- 45–50 s: large exposed rock masses constrain the passage; the view changes
  substantially as the raft negotiates the exit.
- 55 s: raft emerges toward a more open runout, with other rafts beside the
  rocky margin. These moving rafts are not registration landmarks.

The user's hole → sharp right → sharp left description remains an explicit
reconstruction requirement. The sampled views support a multi-obstacle rapid;
they do not independently give surveyed headings, rock coordinates, depth,
wave height, discharge or camera calibration. Do not turn screen-space motion
into measured channel curvature. No video media was downloaded or added to
shipping assets. American Whitewater's hazard page still returned HTTP 403.

## Geographic coverage result

`physics/scripts/review_troublemaker_reference_coverage.py` reads the current
registered mesh, actual grid-boundary profile, original NAIP export bounds,
crux control and reviewed rock search regions. It checks matching geometry
hashes and uses the boundary profile's physical extent (21 m), not the older
terrain manifest's nominal 20 m domain. Outputs:

- [Registered footprint on the aerial image](troublemaker-reference-coverage/coverage.png)
- [Numerical coverage and source hashes](troublemaker-reference-coverage/coverage.json)

The physical test covers 441 m². Inside it are 149 captured-ground vertices,
1,615 inferred-bed vertices, **zero authority-3 recovered-rock vertices and
zero authority-4 vertices**. This is a vertex count, not a proof that no
terrain triangle crossing its boundary includes a rock vertex.

Three of the four interpreted rock search regions have zero footprint overlap.
The north-constriction region overlaps only 0.150 m² out of 396 m² (0.038%).
Thus this local liquid test is not a test of the surrounding rock wakes and
turn sequence, even though it includes the inferred hole-control centre.
The larger collision patch's recorded rock count does not establish that those
rocks lie inside the active fluid domain.

The older `troublemaker_crux_registration.png` plot uses the **image centre**
as its origin. Geometry uses the **selected crux control**, which is
(9.775, −36.974) m relative to that image centre. The apparent ~37 m discrepancy
between old plot labels and the control was a coordinate-frame difference,
not evidence that the terrain was misplaced. The new plot consistently uses
the crux-control frame. No surveyed coordinates were moved.

## Comparison with the larger engine review

Inspected the retained `registered-traversal/crux.png` and `runout.png` engine
captures. These are older full-geometry review captures, not new renders of the
latest liquid experiment. They still show smooth white surface bands, broadly
sloping water faces and insufficient broken crest/spray structure compared to
the reference. Gray terrain is intentional diagnostic shading, not finished
scene appearance. Neither these captures nor the isolated 21 m liquid patch
passes the requested realistic-rapid comparison.

## Next implementation boundary

Return to the larger `SouthForkRegisteredRockPlayable` reconstruction and its
matched hydraulic geometry for the next source-aligned traversal/overhead
comparison. Resolve the visible fixed-rock sequence and connected flow path
there before selecting the extent/coupling of localized liquid detail. Preserve
the same terrain/collision authority and physically connected current; do not
move surveyed rocks or deepen the hole to compensate for the small fixture.
The particle-only surface fix remains the preferred local experiment baseline.

Three tests pass for metric rotation, coordinate-rebase invariance and rejection
of non-rigid/reflected frames. The plot was rendered and visually inspected.
No Unreal build or scene mutation occurred in this pass. The production route,
saved water assets and full completion queue remain unchanged and incomplete.

## September 14 access retry

Retried both exact YouTube references (`ZEG1kvjNI30` and `2XTbOCNDcZQ`).
Web retrieval returned `Cache miss`. Browser control failed before opening a
page with `failed to write kernel assets: The system cannot find the path
specified. (os error 3)`; resetting its session and retrying returned the same
error. The computer-use skill's Node/sky initialization also failed with that
error, including after one session reset. No new video frames or continuous
motion were viewed, and no remote video was downloaded. This access failure
does not invalidate or supersede the documented September 7/9 frame reviews.
It supplies no new geometry, water-motion or playable acceptance evidence.
