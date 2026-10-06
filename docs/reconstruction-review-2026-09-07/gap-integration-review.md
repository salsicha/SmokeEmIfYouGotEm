# Matching candidate integration

The gap-repaired geometry, full-triangle collision and settled 1-m hydraulic
package now load together in **SouthForkSurveyPlayable**, not a production map.
This supersedes the earlier checkpoint saying the candidate was export-only.
No new map was created. The original review mesh remains a separate asset.

`build_south_fork_survey_review_mesh.py` accepts explicit source and output paths
and refuses to overwrite the original export with a variant. It now includes
collision probes for all geometry authority codes, including inferred gap
interpolation (4). The export has 403,200 vertices and 803,842 triangles, with
no decimation. `integrate_south_fork_gap_review.py` validates the geometry,
mesh-source, FBX and hydraulic-array hashes before applying them together. It
preserves the review's single-carrier lighting experiment and guide setup.

The imported engine collision matches all 16 source-height probes, four per
authority type, with maximum error 0.001701 cm. All measured geometry stays
unchanged; only the previously described 40 enclosed cells are interpolated.
All underwater bed estimates remain explicitly inferred, not surveyed.

Recovery is exact-file, after checking for later edits:
`tmp/project-cleanup/SouthForkSurveyPlayable-before-gap-integration.umap`.
The integration report retains both old paths and the saved map/backup hashes.
Do not restore earlier geometry alone while leaving new water fields selected.

## Actual runtime verification

The original `SouthForkRegisteredReplay` test hardcodes the older hydraulic
fixture. A new `SouthForkGapCandidateReplay` regression checks this candidate's
geographic spawn, datum, initial depth/stage, full-grid volume and two seconds
of actual native replay. It and the actual-scene captured-ground contact test
both pass. The contact test covers 20 cases / 2,400 substeps; its preexisting
`r.MotionVectorSimulation` warning remains recorded. Build succeeded (four
actions); 21 Python layout, sanity, gap and export tests pass.

Actual game log `unreal/Saved/Logs/SurveyGapIntegratedCapture.log` confirms the
new coordinate-map path, full-grid MUSCL replay and the existing surface-lit
carrier. Three 1280×720 captures at approximately 10, 30 and 50 gameplay seconds
are `unreal/Saved/Screenshots/SurveyGapIntegrated20260907_000.png` through
`_002.png`. Frames 001 and 002 were inspected: the boat advances and the view
changes; bright water patches occur near the left-side obstruction/drop, but
large areas still look smooth and the rock/bank shapes remain coarse. Do not
label bright glare as measured foam or claim photographic acceptance. The
preexisting editor-only Python startup errors remain in the game log.

This integration does not establish guided whole-rapid traversal, long-duration
runtime stability, resolution convergence, shoreline temporal stability or
photorealism. The previous failed unpowered outlet test remains historical
evidence on the older fixture; it has not been relabeled a pass. No production
route or later river has been promoted.

Clean performance (20 s after 5 s warmup, no captures/cooks in parallel): 1,052
frames, 19.024 ms mean / 25.501 ms p95 at 1280×720 and 87% internal resolution
on the RTX 3060 Laptop GPU. The frame budget still fails; this is an engineering
diagnostic, not release qualification or statistically established acceleration.
See `survey_performance_gap_integrated.json`.
