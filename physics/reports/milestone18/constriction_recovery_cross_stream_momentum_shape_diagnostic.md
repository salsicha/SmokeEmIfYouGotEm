# Milestone 18 Constriction Shape/Timing Diagnostic

Schema: `raftsim.milestone18.constriction_shape_timing.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_cross_stream_momentum/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_cross_stream_momentum/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field Linf: `3.69943`
- Max slope Linf: `0.952384`
- Max probe Linf: `2.20322`
- Max cross-section Linf: `1.69192`

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
| `field` | `v` | `final` | `upstream_approach` | `9,1` | 1 | 3.5 | -3.72743 | -0.0280077 | 3.69943 | 3.69943 | 0.25 | 14.7977 |
| `field` | `hu` | `final` | `constriction_throat` | `7,10` | 10 | 1.5 | 0.889107 | 4.47565 | 3.58654 | 3.58654 | 0.25 | 14.3462 |
| `field` | `u` | `final` | `upstream_approach` | `0,1` | 1 | -5.5 | 3.63205 | 0.908513 | -2.72354 | 2.72354 | 0.25 | 10.8941 |
| `field` | `hv` | `final` | `upstream_approach` | `7,7` | 7 | 1.5 | -1.38665 | 1.07846 | 2.46512 | 2.46512 | 0.25 | 9.86047 |
| `field` | `h` | `final` | `upstream_approach` | `9,5` | 5 | 3.5 | 0.417236 | 1.87017 | 1.45293 | 1.45293 | 0.25 | 5.81172 |
| `field` | `eta` | `final` | `upstream_approach` | `9,5` | 5 | 3.5 | 0.417236 | 1.87017 | 1.45293 | 1.45293 | 0.25 | 5.81172 |
| `slope` | `slope_x` | `final` | `upstream_approach` | `9,7` | 7 | 3.5 | 1.1253 | 0.172918 | -0.952384 | 0.952384 | 0.25 | 3.80953 |
| `slope` | `slope_y` | `final` | `upstream_approach` | `10,2` | 2 | 4.5 | 1.03167 | 0.281904 | -0.749763 | 0.749763 | 0.25 | 2.99905 |
| `field` | `normal_y` | `final` | `upstream_approach` | `8,2` | 2 | 2.5 | 0.587541 | 0.00782086 | -0.57972 | 0.57972 | 0.25 | 2.31888 |
| `field` | `normal_x` | `final` | `upstream_approach` | `9,7` | 7 | 3.5 | -0.745557 | -0.170233 | 0.575324 | 0.575324 | 0.25 | 2.3013 |
| `field` | `normal_z` | `final` | `upstream_approach` | `9,7` | 7 | 3.5 | 0.66254 | 0.984472 | 0.321932 | 0.321932 | 0.25 | 1.28773 |
| `field` | `hu` | `initial` | `upstream_approach` | `3,7` | 7 | -2.5 | 2.12434 | 2.12434 | 1.02915e-07 | 1.02915e-07 | 0.25 | 4.11662e-07 |

## Worst Probe And Cross-Section Series

| Category | Sample | Field | Time s | Distance m | Abs error | Threshold | Ratio |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `probe` | `midstream_center` | `hv` | n/a | n/a | 2.20322 | 0.25 | 8.81289 |
| `probe` | `upstream_center` | `hv` | n/a | n/a | 2.02217 | 0.25 | 8.08868 |
| `probe` | `downstream_center` | `hu` | n/a | n/a | 1.9597 | 0.25 | 7.8388 |
| `probe` | `midstream_center` | `v` | n/a | n/a | 1.69192 | 0.25 | 6.76768 |
| `cross_section` | `mid_cross_section` | `v` | n/a | n/a | 1.69192 | 0.25 | 6.76768 |
| `cross_section` | `mid_cross_section` | `froude` | n/a | n/a | 1.53281 | 0.25 | 6.13123 |
| `probe` | `downstream_center` | `u` | n/a | n/a | 1.27761 | 0.25 | 5.11045 |
| `cross_section` | `mid_cross_section` | `u` | n/a | n/a | 1.09365 | 0.25 | 4.37459 |
| `probe` | `upstream_center` | `v` | n/a | n/a | 1.08839 | 0.25 | 4.35356 |
| `cross_section` | `mid_cross_section` | `h` | n/a | n/a | 1.05176 | 0.25 | 4.20705 |
| `cross_section` | `mid_cross_section` | `eta` | n/a | n/a | 1.05176 | 0.25 | 4.20705 |
| `probe` | `upstream_center` | `hu` | n/a | n/a | 0.980478 | 0.25 | 3.92191 |

## Blocked Reasons

- C++ constriction field Linf still exceeds the GeoClaw/C++ threshold.
- C++ constriction free-surface slope Linf still exceeds the GeoClaw/C++ threshold.
- C++ constriction point-probe Linf still exceeds the GeoClaw/C++ threshold.
- C++ constriction cross-section Linf still exceeds the GeoClaw/C++ threshold.

## Next Levers

- Start with `field`/`v` at `final` because it is 14.7977x the diagnostic threshold.
- Retune lateral velocity and cross-stream surface-slope shape before adding more downstream speed.
- Keep feature forcing off and rerun the Milestone 17 analytic guardrail after the next solver change.
