# Where the fine-grid flow is still adjusting

This follows the [controlled refinement](gap-resolution-review.md), which was
finite and conservative but did not pass its settling screen. No engine asset
or cooked engine field is changed by this diagnostic.

## Regional diagnosis of the 90–120 second tail

The new audit partitions the complete source domain at cell edges shared by
both resolutions. It validates saved coordinates, conserved fields and bed
identity before measuring. Stage ranges use cells wet in all four tail frames;
they do not substitute changing wet-area medians for per-cell stability.

| Downstream coordinates | Three interval storage rates (m³/s) | Per-cell stage range, 95th percentile |
| --- | --- | ---: |
| -135.5 to -80.5 m | +0.401, -0.603, +0.316 | 5.65 cm |
| -80.5 to -25.5 m | -0.793, +0.246, -0.624 | 3.15 cm |
| -25.5 to +25.5 m, crux | -0.358, +0.252, -0.528 | 3.78 cm |
| +25.5 to +80.5 m | +2.617, +1.435, +2.075 | 6.48 cm |
| +80.5 to +135.5 m | +1.017, +3.168, +0.869 | 3.80 cm |

The sustained tail accumulation is downstream of the crux. The crux regional
median's earlier sub-centimetre change did **not** mean its individual cells
were stationary; the maximum sampled per-cell stage range there is 31.96 cm.
This motivates a continuation to test decay, not a repeat from interpolation.

The first exploratory report used integer cut positions. It remains retained
as `gap-refined-regional-settling.json`; those cuts align to the fine grid but
not the parent cell edges. The authoritative aligned report is
[gap-refined-regional-aligned.json](gap-refined-regional-aligned.json).

## Controlled continuation

`--continue-from-run` inherits the saved parent's conserved state and exact
boundary objects, with unchanged source bed, grid, axes, solver SHA, timestep,
CFL, roughness and discharge. It rejects time-varying hydrographs because this
restart resets the internal clock. The output directory must be new, protecting
earlier experiments from accidental overwrite. The old raw `--resume-frame`
option is not used for this controlled continuation.

Source run: `0.5m-mixed-inlet-enclosed-rock-gaps-refined-20260907`.
Source final frame SHA-256:
`2184357cfbf0f5f737797098b53dcac384312a7fbb5826e2c25ecea1b72b8147`.
New run: `0.5m-mixed-inlet-enclosed-rock-gaps-settling-20260907`, an additional
120 seconds at 0.1-second outer steps / CFL 0.2, for 240 seconds since refinement.
This does not count the coarse parent's history as fine-grid simulation time.

Twenty-six regression tests and 32 subtests pass, including preservation of
area partitions, partial final time intervals, forcing/layout guards, and a
sampled temporal-envelope comparison that distinguishes overlapping oscillation
ranges from a persistent offset. The one existing raster-transform deprecation
warning remains unrelated. Reports retain the different tail sampling durations;
an envelope of sparse samples cannot bound unsampled extrema or establish
spatial convergence.

## Result: decaying downstream adjustment, persistent crux offset

The continuation completed in 687.08 seconds and all 13 saved frames pass the
survey sanity screen (maximum saved depth 2.4903 m, speed 15.9877 m/s; these are
not measured physical targets). The section-discharge error improves from 6.29% to 4.69%
and passes its 5% screen. Tail total storage rates improve to +1.445, +0.825 and
-0.356 m³/s, but the first interval still exceeds 0.906 m³/s. The overall
mean-flow screen therefore **still fails**; no limits were relaxed.

Downstream region +25.5 to +80.5 m now stores +1.220, +0.617 and +0.047 m³/s
over those intervals; the final downstream region records +0.212, -0.045 and
-0.610 m³/s. These sampled results support decaying downstream adjustment, not
complete stationarity. The crux's p95 per-cell temporal stage range is 2.46 cm,
but its maximum is 70.96 cm, so local extrema still need investigation.

Conservation passes independently: inlet 45.30695455 m³/s, outlet 46.88921025
m³/s, no side leakage. Numerical net -1.58225570 m³/s matches the tiny-step
storage derivative -1.58225521 m³/s. This is not steady-flow acceptance.

The crux median fine-minus-coarse stage is now **-22.98 cm**, rather than
-22.51 cm before continuation. P95 absolute stage difference is 30.01 cm and
p95 current-vector difference 0.985 m/s. Across 1,383 cells wet throughout both
sampled tails, **79.61%** have the entire sampled fine-stage range more than
1 cm below the coarse range. The median non-overlap gap is 22.93 cm.
This points to a persistent local resolution/history discrepancy rather than
only the phase of the last saved wave. It is not a formal convergence estimate:
the histories and sampled durations differ, and unsampled extrema are unknown.

Evidence: [resolution and tail comparison](gap-settled-resolution-comparison.json),
[regional history](gap-continuation-regional.json),
[mean-flow screen](../reconstruction-review-2026-09-06/troublemaker_survey_flow_0.5m-mixed-inlet-enclosed-rock-gaps-settling-20260907.json),
[face-flux audit](../reconstruction-review-2026-09-06/troublemaker_numerical_boundary_flux-0.5m-enclosed-rock-gaps-settling-20260907.json),
and [final regression tests](continuation-hotspot-tests.xml).
The output name `gap-settled-resolution-comparison.json` identifies this settling
experiment; its explicit `resolution_converged` and acceptance flags are false.

### Localized pocket, not a dry-film speed artefact

The [hotspot audit](gap-continuation-hotspots.json) locates the largest sampled
crux stage change at hydraulic row 130, column 235: downstream/left
(-17.75, -15.25) m, UTM (683827.2464, 4296681.1059) m. Its depth stays
1.51–2.22 m and speed 0.27–0.83 m/s in the four tail samples. Thus this 0.71 m
stage swing is not a nearly dry, high-speed film at the main drop. Its 3×3 bed
neighborhood ranges approximately 225.96–229.41 m NAVD88 beside steep rock.

A read-only inspection of the source raster at that point reproduces the
hydraulic bed exactly, 225.9754719984 m NAVD88. The four bilinear contributors
are source rows 264–265, columns 403–404, authority codes `[[2,2],[3,2]]`:
three inferred submerged-bed cells and one captured exposed-rock cell. The
captured-rock contributor has only 0.002066 weight; the rest is the inferred
bed. Neighboring fluctuating cells (130,236) and (130,238) use only authority-2
contributors. These are not the authority-4 gaps repaired previously.

This localizes a candidate investigation to how inferred water-filled pockets
meet captured rock. It does **not** authorize filling the pockets, altering
captured heights or claiming that a real physical pool cannot oscillate. Source
point-cloud/imagery review and numerical wet/dry flux behavior must distinguish
unsupported geometry from a legitimate pool before a repair. The mean crux
offset involves many more cells; this localized fluctuation is not established
as the cause of the full resolution difference.

## Source calibration and next work

New [USGS discharge context](naip-date-discharge-context.json) for the dated atlas
image establishes an upstream daily mean, not photo-time discharge. The cook's
1,600 cfs remains a diagnostic choice. It was not silently replaced by the
584 cfs daily mean or presented as measured photo-time flow.

Do not launch another identical extension just to seek a passing tail. Next,
localize the persistent crux stage/velocity extrema and examine how the two
grids represent the same bed control and its wet/dry interfaces. Any bed or
numerical change needs its own bounded comparison and provenance, without
altering measured rock heights to tune the answer. No fine-grid package was
exported or imported; no map/material/terrain/collision change, commit or push.
All owned solver/audit processes exited. South Fork and later rivers remain
unaccepted; no footage, rapid-identity, animation or photoreal claim is made.
