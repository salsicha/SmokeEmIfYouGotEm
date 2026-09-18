# Cap reference interpretation and single-cook review preflight

September 18, 2026. Supporting work only, **not a delivered scene improvement**.
No terrain, water, collision, material, menu or runtime solver was changed.

## Source interpretation narrowed without another geometry cook

Reopened [Qweniden's July 15, 2022 bank-side footage](https://www.youtube.com/watch?v=2XTbOCNDcZQ)
through ordinary browser playback using the computer-use skill's browser
workflow. The player reports 3:24. Inspected paused 0:06 and 0:55 views after
skipping an ordinary advertisement. The 0:06 upstream view includes a visibly
jagged, layered exposed rock; the 0:55 view shows a broad, fractured opposing
bank mass with surrounding vegetation and whitewater. These are qualitative
observations: the camera is uncalibrated, water/vegetation occlude the lower
rock, and no reference pixels were registered to individual source IDs.
No login, media download, permission bypass or new shipping license.

Checked a concrete alternative explanation for the downstream cap needles:
the coverage refiner selects a source point nearest an overlong triangle's XY
centroid, so it can introduce a high point after lower-bin seeding. But **13 of
the 18 actual ray-hit anchors are already the lowest eligible original return
in their 0.5 m bins**. All 18 are outside the original 549-vertex seed.
Thus changing only the coverage-refinement ordering cannot repair most of the
identified surface. This is not another candidate generation or tuning run.

For the five non-minimum anchors, the exact same-bin lower observations are:

| Cap vertex | Selected original ID | Same-bin minimum ID | Height difference (m, rounded) |
| --- | --- | --- | --- |
| 259 | 685469 | 685452 | 1.608 |
| 316 | 685817 | 689250 | 0.164 |
| 386 | 686274 | 686503 | 0.060 |
| 707 | 689127 | 689209 | 0.054 |
| 726 | 689210 | 689262 | 0.088 |

The other minimum-bin vertices are 250, 310, 321, 325, 327, 409, 427, 433,
435, 443, 447, 464 and 723. Calculation uses the existing `lower_bins` helper,
classes 1/2/10 and the original metric frame; this all-cloud diagnostic does
not apply the interpreted polygon and does not certify a replacement point.
No captured XYZ/classification was modified.

The complete archived pulse metadata also has only source 685469 at its exact
GPS timestamp/point-source ID, not a recovered second return. Source IDs 320,
321 and 322 cover the local cap rectangle. A preliminary nearby-ground
comparison found median height difference zero for pairs 320/321 and 320/322;
an empty-overlap pair stopped that exploratory calculation. It is **not** a
completed strip-adjustment audit or a reason to move captured points. No
nearest-point association is called a same-pulse return.

The coherent rock/vegetation interpretation remains unresolved. Do not flatten
all jagged features: the footage actually contains fractured rock. Next work
still needs a spatially justified rock-envelope interpretation with retained
raw data, followed by a common rendered/collision/bed union and fresh flow.

## Review launcher no longer requires a completed cook to be alive

`run_constriction_paired_review.ps1` previously required exactly two live cooks.
The candidate finished normally, so that requirement prevented the next valid
paired geometry/flow review. New `raftsim.paired_review_cooks.v2` manifests
explicitly support zero, one or two cooks; legacy v1 remains strictly two.

The launcher compares the complete observed cook PID inventory with the
explicit manifest, then retains the original PID/start-time/executable/hash/
exact-command checks and process handles. Unlisted cooks, stale IDs and
duplicates are rejected. Inventory is checked again before suspension and
before editor launch. Cleanup still resumes only successfully suspended,
retained handles; no job is restarted or silently omitted.

`-ValidateOnly` performs read-only preflight, disposes acquired process handles,
and does not suspend a cook, launch an editor, or write play/performance reports.
Actual preflight passed for the sole live PID 13584/start UTC
2026-09-18T12:17:39.4321093Z and its exact executable/command. The old manifest
containing completed PID 30276 was rejected before mutation. Verified that no
expected editor log, process receipt or play report was created. The four
PowerShell validator groups pass, including zero/one/two inventories, strict
legacy receipts, invalid/duplicate IDs, absent/extra cooks and capture controls.

This validates **preflight only**, not a new editor run, suspend/resume event,
rendered surface, collision, actual motion or measured FPS. A future qualified
candidate can use `tmp/constriction-review-cooks-v2-20260918.json` while its
recorded job identity remains live; refresh it when that job finishes.

## Continuing state

Existing baseline checkpoints 10400, 10450, 10500, 10550 and 10600 (local
28000–32000) each pass both full-state and artificial-bank audits. All 86,720
artificial-bank cells remain exactly dry. **Not settled.** No cook was paused,
stopped, duplicated or restarted. Next unaudited checkpoint is 10650/local33000.

Installed map/4950 s fields and ordinary 24.937420 FPS / p95 49.3295 ms remain
unchanged and fail 30 FPS. Nonlinear runtime remains OFF. South Fork is still
first; Colorado, Pacuare and Futaleufu remain queued and unfinished.
The [retained final checkpoint pair and explicit manifest](cap-reference-and-review-inventory/)
are supporting receipts, not normal-play acceptance.

### 20:47 UTC continuation while the source decision is unanswered

Audited all ten newly completed checkpoints 10650 through 11100, local steps
33000 through 42000, with both existing independent audit tools. Every
full-state check passes and all 86,720 artificial-bank cells remain exactly
dry. At 11100: depth 3.970706 m, speed 5.433088 m/s, volume 2,444,238.036796 m³,
maximum step residual 1.429428e-8 m³. Outflow 103.095691 m³/s still exceeds
inflow 45.306955 m³/s; this is NOT a settled field. Retained the final pair here;
the complete ten pairs remain in ignored `tmp/pending-cap-baseline-*-20260918.json`.
Next checkpoint is 11150/local43000. Same PID/start/executable/command, no
suspension, restart, duplicate cook or change to installed water.

Inspected current publication code against the retained actual timing report:
Tick includes Refresh and CartesianPublish; their nested times must not be
added. Although interpolation precedes refresh, ordinary non-recenter refresh
only changes targets and does not issue a second core publication. Skipping
interpolation whenever refresh is due would therefore remove the frame's mesh
update and change subsequent history/support. No such optimization was made,
and no new speedup, motion test or scene acceptance is claimed. The cap fidelity
question is still unanswered; no repeat question or assumed permission.
