# v15r2 rapid cost: recurring refinement and rare double publications

September28 UTC. Retained packaged-game evidence, not a runtime improvement,
new visual delivery, timing pass or reconstruction acceptance. No engine was
launched alongside the running1350-to1800s hydraulic continuation.

## Evidence and timing phase

Re-read both original1200-row captures, verify their hashes against the launch
receipts, and retain exactly rows30..1169. The existing strict CSV/cadence
parsers pass27 regressions. Do not remove the expensive rows from acceptance.
Recipe: `tmp/audit-v15r2-publication-events-20260928.py`; report:
`tmp/sf-v15r2-publication-events-v1-20260928.json`, SHA256
`219395635ddeeca6c26477458f50235354786a197178819e6712c47244116a60`.
The report includes complete counted-change signatures, four time intervals,
double-update rows and neighboring elapsed-frame measurements for both runs.
Original CSV hashes remain in [the packaged review](v15r2-playable-review.md).

The profiler launcher explicitly sets `csv.UseLegacyFrameTime 0`; the8310 log
confirms `false` before capture. UE5.8 CsvProfiler.cpp records this mode's
elapsed time near the next frame start, unlike legacy EndFrame timing. These
are explicit runtime csvprofile captures, not engine boot captures. Retain the
neighboring rows rather than associating FrameTime with same-row CPU scopes.
CPU scope totals are inclusive; never add Refresh, crest and surface Tick.

| Start | Double-update CPU row | Surface Tick ms | Refresh ms | Crest ms | Following elapsed row / ms |
| --- | ---: | ---: | ---: | ---: | --- |
|8310|219|91.8027|86.2631|28.5514|220 /115.4698|
|8310|503|87.6067|81.8631|25.3495|504 /113.4651|
|8310|754|85.3010|77.0713|24.7679|755 /101.3446|
|11520|1016|77.4645|71.5776|18.7853|1017 /97.1394|

Every8310 frame above100ms follows one of its three double-update CPU rows;
there are no other double-update rows in the audited interval. The11520 run
has one such row, followed by its maximum elapsed frame, but no>100ms frame.
Each double-update row has exactly one XY/index/profile/coarse/shore change
and one dense-history update. This localizes an expensive event population;
it does not measure the saving from removing any operation.

## Two distinct costs, not a single shortcut

Regular changing geometry dominates the recurring selection work. At8310,
553 frames change XY/profile/coarse targets without index, shore or detail
window changes; mean selection is8.9887ms. At11520,561 such frames average
11.5072ms. There are only8 detail-window-change frames at8310 and3 at11520.
Thus relaxing detail-window coverage cannot address most selection work.
556/564 frames respectively contain only dense-history updates and zero
selection cost. The two rapid p95 failures are not explained by rare hitches
alone, and an unchanged-target shortcut is already functioning.

Source tracing identifies the two-publication route: Tick advances and
publishes interpolation before RefreshSurface. On a grid recentre, refresh
carries the rendered state into the shifted lattice and publishes again with
crest blend alpha0. Refresh can also publish after section loss or a hard
swap. Existing captures do not record those individual branch decisions, so
the recenter explanation is a source-supported hypothesis, not a measured
branch attribution. The source's render-event logging is default-off.

Do not simply skip the first call: it advances the fine crest history before
the second call remaps the surface. Moving refresh before interpolation also
changes which hydraulic target is integrated. Both risk visible shoreline
or crest discontinuities. Recenter also remaps coordinates, basis tangents
and multiple temporal fields; the second crest call alone does not explain
the entire77..86ms Refresh spike.

## Next bounded runtime work

Separate actual recenter mapping/history cost and the refresh publication
reason before changing scheduling. Preserve the interpolation advance and
the exact carried shoreline/crest state in any coalescing candidate. For the
recurring p95 cost, address changing-profile/root-coordinate refinement, not
detail-window enlargement, relaxed error gates or a lower refresh frequency.
Do not repeat the rejected assembly-coordinate parallelization experiment.
Use one bounded actual-game comparison after the current hydraulic owner is
terminal; do not rerun the completed v15r2 acceptance captures unchanged.

No runtime code, material, geometry, field or solver switch changed in this
analysis. Flat foam, weak breaking, recirculation, hydraulic settling, collision,
shoreline continuity and both rapid timing gates remain open. South Fork
remains first; Colorado, Pacuare and Futaleufu remain queued.
