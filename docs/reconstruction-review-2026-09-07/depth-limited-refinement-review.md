# Corrected-core half-metre hydraulic check

The app completion goal is active for the entire queue. This is a completed
numerical milestone, not completed South Fork reconstruction or water realism.

## Controlled experiment

Run: `tmp/south-fork-survey-hydraulics/0.5m-mixed-inlet-depth-limited-refined-20260907`.
Warm-started from the completed 600-second one-metre depth-limited candidate,
using the same solver SHA `1f010cbe7edce8eb579c2d9a040820a24d6ee6ac1615073e3afbf899cac9ba50`,
triangle-sampled geometry SHA `af6ea6676d8cea99d82fef9044fcc139952c6c1855868a7d136fa8afcfe3241a`,
boundary conditions, 45.3069545472 m3/s inflow, 0.035 roughness, CFL 0.2 and
0.1-second outer steps. Physical domain remains 271 x 161 m; the finer grid
is 542 x 322 cells. Initial interpolation changes storage by +1.602 m3 and
must re-equilibrate; it is not a conservative simulation step.

240 simulated seconds complete in 697.415 wall seconds. All 13 saved frames
(20-second cadence) pass the unchanged candidate sanity bounds. Maximum saved
depth is 2.501368 m and maximum speed 6.051162 m/s. The old 23.7504 m/s failure
belongs to the previous solver; do not import its fields or claim unsampled
transients are ruled out by this new cadence.

## Independent numerical results

- All three mean-flow checks pass: maximum tail section-discharge error 3.351%,
  tail storage rates 0.1831, 0.7065 and 0.1897 m3/s (under 2% of discharge),
  and regional median-stage range below 1 cm.
- Exact boundary audit passes: west +45.3069545472, east -45.3913399654,
  north/south zero, net -0.0843854182 m3/s. Independent tiny-step storage
  derivative is -0.0843865564 m3/s. Conservation is not visual acceptance.
- Crux per-cell tail stage range is 0.00450 m median, 0.03405 m p95 and
  0.16179 m maximum. Some localized movement persists even though the
  regional median is settled.

Matched coarse/fine results, using area-restricted fine conserved fields:

| Crux common wet area, 1,391 m2 | Median | p95 absolute | Maximum absolute |
| --- | --- | --- | --- |
| Fine minus coarse stage | -0.01541 m | 0.08735 m | 0.25344 m |
| Fine minus coarse depth | -0.01609 m | 0.09869 m | 0.65555 m |
| Velocity-vector difference magnitude | 0.12346 m/s | 0.49303 m/s | 2.48458 m/s |

These are two-grid differences, not proven convergence. About 59.8% of common
crux cells have fine tail stages entirely more than 1 cm below coarse sampled
tail stages. Median sampled-envelope separation is 1.53 cm, p95 8.22 cm.
Different tail durations and sampling cannot bound unsampled extrema. Local
rock-edge/channel sensitivity still requires interpretation before promotion.

Reports: `depth-limited-resolution-comparison.json`,
`depth-limited-refined-regional.json`, and the corresponding
`troublemaker_survey_flow_0.5m-mixed-inlet-depth-limited-refined-20260907.json`
and `troublemaker_numerical_boundary_flux-0.5m-depth-limited-refined-20260907.json`
under the September 6 report directory.

## Export and safeguards

A separate `engine_review` package is exported, not staged in any map. Manifest
SHA `50fe1c91f8982a6a8b20cf2efbfa912c0afc60668a647aeab094a35dca62fdca`;
depth SHA `0d3ee838bd67996ab03c4e5a3b6978a75ec51b1e135e891ecbdeaa0ee3618217`.
Start station/lateral [-60.25, -9.75], world cm
[5961.619945985687, -1307.798768781198, 859.3053445731347], yaw 158.43478935409635.
Minimum depth in the 4 m-radius square is 1.003302 m. Export retains all false
production/whole-reconstruction acceptance flags and the exact solver identity.

The conservation tool now verifies the executable against the completed cook's
recorded SHA, rejects an invalid endpoint and refuses to overwrite previous
audit/report evidence. New tests cover relative/absolute binary paths, changed
and missing executables. Eight identity/resolution tests plus 18 subtests pass.
Actual fine-grid conservation above also passes through the strengthened path.

Playable map SHA remains `2c53df655cd7fa83a232f40f951c4babcdc34adbd3fb7aafda8db270b64969bd`;
engine archive remains `83f35ddf4e6ab28fc07999804e63d3ccfcd5d0d78d8f0775c96e909913910f03`.
No engine assets, source terrain, gameplay or rendering were changed here.
All owned cooks/audits/export processes exited. Do not repeat this completed
cook unchanged. Next: interpret remaining local resolution differences and
test efficient presentation of the validated flow with visible crest/foam
motion. The existing every-frame full-window solver is still over budget;
simply replacing it with four times as many live cells is not a performance fix.
Full route/source registration, crew, normalization, later rivers and final
commit remain in the active goal.
