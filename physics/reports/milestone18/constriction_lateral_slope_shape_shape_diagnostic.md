# Milestone 18 Constriction Shape/Timing Diagnostic

Schema: `raftsim.milestone18.constriction_shape_timing.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_lateral_slope_shape/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_lateral_slope_shape/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field Linf: `3.69455`
- Max slope Linf: `0.855161`
- Max probe Linf: `2.25322`
- Max cross-section Linf: `1.73192`

## Zones

| Zone | Columns |
| --- | --- |
| `upstream_approach` | `0-9` |
| `constriction_throat` | `10-13` |
| `downstream_constriction` | `14-15` |
| `recovery` | `16-23` |

## Worst Field And Slope Cells

| Category | Field | Frame | Zone | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `field` | `v` | `final` | `upstream_approach` | `9,1` | 1 | 3.5 | -3.72743 | -0.0328864 | 3.69455 | 3.69455 | 0.25 | 14.7782 |
| `field` | `hu` | `final` | `downstream_constriction` | `8,14` | 14 | 2.5 | -0.185349 | 3.10395 | 3.2893 | 3.2893 | 0.25 | 13.1572 |
| `field` | `u` | `final` | `upstream_approach` | `1,1` | 1 | -4.5 | 3.85418 | 1.03846 | -2.81572 | 2.81572 | 0.25 | 11.2629 |
| `field` | `hv` | `final` | `upstream_approach` | `7,7` | 7 | 1.5 | -1.38665 | 1.04193 | 2.42859 | 2.42859 | 0.25 | 9.71434 |
| `field` | `h` | `final` | `upstream_approach` | `9,2` | 2 | 3.5 | 0.327768 | 1.65971 | 1.33195 | 1.33195 | 0.25 | 5.32779 |
| `field` | `eta` | `final` | `upstream_approach` | `9,2` | 2 | 3.5 | 0.327768 | 1.65971 | 1.33195 | 1.33195 | 0.25 | 5.32779 |
| `slope` | `slope_x` | `final` | `upstream_approach` | `9,7` | 7 | 3.5 | 1.1253 | 0.27014 | -0.855161 | 0.855161 | 0.25 | 3.42065 |
| `slope` | `slope_y` | `final` | `upstream_approach` | `10,1` | 1 | 4.5 | 1.07162 | 0.260042 | -0.811575 | 0.811575 | 0.25 | 3.2463 |
| `field` | `normal_y` | `final` | `upstream_approach` | `8,2` | 2 | 2.5 | 0.587541 | 0.0030951 | -0.584446 | 0.584446 | 0.25 | 2.33778 |
| `field` | `normal_x` | `final` | `upstream_approach` | `3,7` | 7 | -2.5 | 0.470216 | -0.0427865 | -0.513002 | 0.513002 | 0.25 | 2.05201 |
| `field` | `normal_z` | `final` | `upstream_approach` | `9,7` | 7 | 3.5 | 0.66254 | 0.96344 | 0.300901 | 0.300901 | 0.25 | 1.2036 |
| `field` | `hu` | `initial` | `upstream_approach` | `3,7` | 7 | -2.5 | 2.12434 | 2.12434 | 1.02915e-07 | 1.02915e-07 | 0.25 | 4.11662e-07 |

## Worst Probe And Cross-Section Series

| Category | Sample | Field | Time s | Distance m | Abs error | Threshold | Ratio |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `probe` | `midstream_center` | `hv` | n/a | n/a | 2.25322 | 0.25 | 9.01289 |
| `probe` | `upstream_center` | `hv` | n/a | n/a | 2.01084 | 0.25 | 8.04336 |
| `probe` | `downstream_center` | `hu` | n/a | n/a | 1.96382 | 0.25 | 7.85526 |
| `probe` | `midstream_center` | `v` | n/a | n/a | 1.73192 | 0.25 | 6.92768 |
| `cross_section` | `mid_cross_section` | `v` | n/a | n/a | 1.73192 | 0.25 | 6.92768 |
| `cross_section` | `mid_cross_section` | `froude` | n/a | n/a | 1.5372 | 0.25 | 6.14881 |
| `probe` | `downstream_center` | `u` | n/a | n/a | 1.28182 | 0.25 | 5.12729 |
| `probe` | `downstream_center` | `hv` | n/a | n/a | 1.27932 | 0.25 | 5.11726 |
| `probe` | `upstream_center` | `v` | n/a | n/a | 1.14841 | 0.25 | 4.59365 |
| `probe` | `downstream_center` | `v` | n/a | n/a | 1.12709 | 0.25 | 4.50836 |
| `cross_section` | `mid_cross_section` | `u` | n/a | n/a | 1.09365 | 0.25 | 4.37459 |
| `cross_section` | `mid_cross_section` | `h` | n/a | n/a | 1.05176 | 0.25 | 4.20705 |

## Blocked Reasons

- C++ constriction field Linf still exceeds the GeoClaw/C++ threshold.
- C++ constriction free-surface slope Linf still exceeds the GeoClaw/C++ threshold.
- C++ constriction point-probe Linf still exceeds the GeoClaw/C++ threshold.
- C++ constriction cross-section Linf still exceeds the GeoClaw/C++ threshold.

## Next Levers

- Start with `field`/`v` at `final` because it is 14.7782x the diagnostic threshold.
- Retune lateral velocity and cross-stream surface-slope shape before adding more downstream speed.
- Keep feature forcing off and rerun the Milestone 17 analytic guardrail after the next solver change.
