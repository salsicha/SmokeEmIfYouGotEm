# Repaired-bed resolution check

This is a new hydraulic diagnostic on the integrated **gap-repaired geometry**,
not a repeat of the old half-metre runs. It does not change the playable review
or production scene. Colorado, Pacuare and Futaleufu remain queued behind South
Fork acceptance.

## Experiment identity

- Parent: `1m-mixed-inlet-enclosed-rock-gaps-continuation-20260907`, the
  600-second, 1-metre lineage that passed its mean-flow screen.
- Fine run: `0.5m-mixed-inlet-enclosed-rock-gaps-refined-20260907`, 1,200 steps
  at 0.1 seconds, CFL 0.2 (120 simulated seconds after interpolation).
- Geometry SHA-256:
  `af6ea6676d8cea99d82fef9044fcc139952c6c1855868a7d136fa8afcfe3241a`.
- Solver SHA-256:
  `1bbf29bda937e7e9cd19b8baf41113529df36d5ce7dcf0ef50e9606f2621ae4c`.
- Both grids cover exactly 271 by 161 metres with the same cell-edge bounds,
  rigid axes and source terrain. The fine grid is 542 by 322 cells.
- Boundary stages remain 229.83945561893123 / 226.47797828534254 m NAVD88;
  target discharge remains 45.3069545472 m³/s, Manning roughness 0.035.

The refinement cook previously recomputed median boundary stages at the new
cell centres, changing imposed head as well as resolution. It now inherits the
parent boundary objects and rejects changed discharge, boundary mode, solver,
CFL, fixed timestep or roughness. This corrects future comparisons; it does not
retroactively make the older runs a controlled experiment.

The warm start interpolates wet-weighted stage and velocity onto the unchanged
finer bed. It is **not a conservative solver step**. Initial storage increases
from 16,833.5990 to 16,838.7729 m³ (+5.1739 m³, about 0.031%). The finer grid must
settle independently; its clock is not a continuation on the same discretization.

## Verification method

`compare_south_fork_resolution.py` checks every saved frame against the existing
finite/depth/speed sanity bounds, then verifies identical forcing and nested
physical bounds. It area-averages fine depth and momentum onto the parent cells.
Stage/current differences exclude cells with any dry fine child; wet-area and
storage changes are recorded separately. This avoids interpolating dry-bank
elevations into water or comparing misaligned cell centres.

The regression run passes **19 tests and 22 subtests**. It covers geographic
identity, inherited forcing, cell-edge bounds, area-preserving restriction,
dry-edge exclusion and rejection of invalid/nonfinite comparisons. The one
existing raster-transform deprecation warning is unrelated.

## Result: finite and conservative, not settled

The native run completed in 714.19 seconds. All **13 saved fine frames** and
14 parent frames pass the generous sanity screen. Fine maximum saved depth is
2.6993 m and maximum speed 11.9751 m/s; neither is a measured river value.

The independent numerical-face audit passes: inlet 45.30695455 m³/s, outlet
46.31873627 m³/s, zero side leakage. Net face flux is -1.01178172 m³/s versus
-1.01178375 m³/s measured storage derivative in a tiny conservative step.
The final instantaneous outflow still differs from the target by 2.23%.
The native summary's 1.94% storage change over the whole run is **not** itself
a conservation error in an open-boundary river.

The mean-flow screen **fails**. Last-four-frame section error reaches 6.29%
(limit 5%); the three tail storage rates are +2.883, +4.499 and +2.108 m³/s
(limit 0.906 m³/s). Regional median stage varies by 8.14 mm and passes its 1 cm
screen, but that alone cannot establish settling. Instantaneous final flux and
10-second interval storage rates measure different time windows, so their
different signs do not invalidate the conservation audit.

The final snapshots show substantial resolution/history sensitivity:

| Common-wet area | Median fine-minus-coarse stage | 95th-percentile absolute stage difference | 95th-percentile current-vector difference |
| --- | ---: | ---: | ---: |
| Whole domain, 10,304 m² | +0.9 mm | 23.1 cm | 0.547 m/s |
| Crux, 1,387 m² | -22.5 cm | 29.3 cm | 0.986 m/s |

Fine final storage is 320.99 m³ below the parent final state and wet area above
0.1 m depth is 39 m² smaller. Because the fine run is still adjusting, these are
**not** spatial truncation-error estimates or proof of grid convergence.

Evidence:

- [Every-frame sanity and nested-grid comparison](gap-resolution-comparison.json).
- [Mean-flow screen](../reconstruction-review-2026-09-06/troublemaker_survey_flow_0.5m-mixed-inlet-enclosed-rock-gaps-refined-20260907.json).
- [Numerical-face conservation audit](../reconstruction-review-2026-09-06/troublemaker_numerical_boundary_flux-0.5m-enclosed-rock-gaps-refined-20260907.json).
- [Flow-field diagnostic](../reconstruction-review-2026-09-06/troublemaker_survey_flow_0.5m-mixed-inlet-enclosed-rock-gaps-refined-20260907.png), inspected after generation. This is a numerical plot, not a game screenshot.
- [Regression test results](refinement-comparison-tests.xml).

## Handoff

No fine-grid engine package was exported/imported. The review map, material,
terrain, collision and 1-metre engine fields remain unchanged. All owned cook
and audit processes have exited; no commit or push was made.

Next hydraulic work should distinguish a persistent resolution-dependent crux
state from residual boundary/storage oscillation. Use region-specific temporal
stage/flux evidence and, if warranted, a uniquely labeled continuation from
this exact final frame; do not restart the warm start or rerun an unchanged
comparison as progress. An unsettled finer grid must not be promoted or used
to tune foam/wave amplitudes. Crest realism, runtime budget, robust guided
tracking, rapid identities and full-route migration remain open separately.
