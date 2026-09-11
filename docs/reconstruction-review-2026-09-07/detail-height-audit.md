# Live detail height, slope and foam audit

September 7, 2026 local time. South Fork registered candidate only. This is new
measurement of the running simulation, not visual acceptance or a physics fix.
The previous spray integration pass was progress; the white face remained smooth.

## Reproducible diagnostic

Added non-Shipping opt-in `-RaftSimDetailSnapshot=ABSOLUTE_PREFIX` to the existing
detail component. It requests three paired GPU state-buffer and resolved texture
copies at component elapsed10/15/20s, retaining the exact mean-flow input and
simulation clock. Polls readiness without waiting, restores texture SRV access
after copy, refuses to overwrite pending evidence and logs incomplete teardown.
Normal play allocates no snapshot/readback and receives no state feedback.
This path writes files on the render thread once a snapshot is ready: its runs
are explicitly excluded from performance qualification.

Each snapshot has a JSON manifest plus three row-major128x128x4 float32 arrays:
`flow` = depth,u,v,entrainment potential;
`state` = perturbation height,qx,qy,transported foam density;
`surface` = weighted height,slopeX,slopeY,coverage actually resolved for material.
Frame alignment and dimensions are explicit. It does not read macro geometry,
particle state or a final shaded image.

Initial build64271 failed because unbraced logging macros broke two if/else
pairs. Braces corrected; next build exited0,5actions8.65s. Diagnostic engine
process75363 exited0, all three snapshots finalized in `DetailHeightAudit.log`.
Outputs: `detail-snapshot/live_00..02.json` and accompanying `.f32` arrays.
Same registered/crest/second-order/ballistic options as the prior current review;
no recorder, no changes to forcing0.06m, source, damping, grid or geometry.

`unreal/Scripts/analyze_detail_snapshot.py` validates array sizes/finiteness,
nonnegative density, bounded coverage and all four actual texture channels
against an independent NumPy implementation of the resolve. Analysis exited0;
`detail-snapshot/analysis.json`. Largest height/slope discrepancy is below4e-9
and coverage discrepancy below1e-7 for the first sample; all three pass1e-5.
Thus the texture resolve is not discarding the observed small perturbations.

## Measurements

Interior means full edge/depth weight >0.99. Foam group is resolved coverage
>0.65, not an image-space classification of the broad white region.

| Elapsed s | Foam cells | Median absolute height mm | p95 absolute height mm | RMS height mm |
| --- | --- | --- | --- | --- |
| 10.001 | 108 | 2.276 | 17.406 | 8.169 |
| 15.015 | 125 | 2.211 | 17.560 | 7.210 |
| 20.010 | 126 | 2.614 | 16.383 | 8.856 |

In each foam group the median instantaneous entrainment potential is zero:
transported foam persists beyond its production cells. At10s,195interior cells
have source>0.3; their height RMS is20.676mm, while all6600wet interior cells
have4.108mm RMS. Maximum interior excursion at that sample is80.640mm; it is
not representative of most foam cells. Dense coverage>0.9 occupies only6/9/10
cells respectively. Pairwise five-second differences in common foam-covered
cells have RMS9.664mm and14.227mm. These sparse differences are NOT a temporal
frequency spectrum, flow velocity, wave energy budget or photographic score.

The fixed detail-window centre is river(0,0), world(0,0,0)cm, with the registered
downstream basis(-0.929999836,0.367559935). Do not call the analysis's relative
crux rectangle a measured pixel region. Shared macro crests can be much larger
(previous0.545m audit); this pass measures only the added GPU perturbation.

## Base-color view and regression scope

Separate engine process41712 exited0, log `DetailBaseColorAudit.log` confirms
`r.BufferVisualizationTarget BaseColor` and `viewmode VisualizeBuffer`.
`unreal/Saved/Screenshots/DetailBaseColorAudit_000.png` inspected: broad smooth
gray variation, not a direct foam-coverage mask. This does NOT establish that
every bright pixel in the lit view is foam rather than reflection/scattering.
No claim that the base-color view isolates the final foam authority.

Final process87316 exited0; `engine-detail-snapshot/index.json`: **15 clean
successes,0failures**. Thirteen actual-GPU detail/history/crest/resolve tests and
the two map/visible-carrier regressions. The diagnostic's own data is separately
checked by the paired-texture analysis above. No release or performance run was
substituted with this result, and no improved appearance is claimed.

## Consequence for the next implementation

The current added wave motion is genuinely small where persistent foam remains;
it is not sufficient evidence of piled, churning whitewater. Pressure excitation
is driven by instantaneous entrainment, while density persists downstream and
momentum is independently damped. Do not increase foam whiteness, arbitrarily
raise the0.1m forcing bound, or redo unchanged transport tuning to hide this.
First distinguish final material coverage from reflections at the broad face,
then address persistent, surface-coupled churning and spray landing using the
actual liquid surface/velocity, with bounded budgets and raft consistency.

An external method reference inspected this pass is the official
[SideFX whitewater solver documentation](https://www.sidefx.com/docs/houdini/nodes/dop/whitewatersolver.html).
It treats foam/spray/bubbles as particles coupled to liquid velocity and surface
distance, with separate advection, gravity, surface attachment and density
behavior. This supports separating those mechanisms; it is not validation of
our heightfield, proof that stateless puffs implement them, or a decision to
import Houdini. Two research-PDF search hits (ETH2007 shallow-water bubble
coupling and RWTH2018 micropolar foam) were not opened/read and are not an
implemented method or calibration source.

Full goal active. No production/material/survey/particle-asset changes, later
river start, commit or push. All owned processes in this pass are terminal.
