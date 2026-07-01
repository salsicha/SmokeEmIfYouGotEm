# Milestone 18 Constriction Shape/Timing Diagnostic

Schema: `raftsim.milestone18.constriction_shape_timing.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_flux_mass_froude_timing/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_flux_mass_froude_timing/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field Linf: `3.82762`
- Max slope Linf: `1.46966`
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
| `field` | `u` | `final` | `upstream_approach` | `1,7` | 7 | -4.5 | -0.525053 | 3.30256 | 3.82762 | 3.82762 | 0.25 | 15.3105 |
| `field` | `v` | `final` | `upstream_approach` | `9,1` | 1 | 3.5 | -3.72743 | -0.0019143 | 3.72552 | 3.72552 | 0.25 | 14.9021 |
| `field` | `hu` | `final` | `downstream_constriction` | `8,14` | 14 | 2.5 | -0.185349 | 3.43818 | 3.62353 | 3.62353 | 0.25 | 14.4941 |
| `field` | `hv` | `final` | `recovery` | `7,17` | 17 | 1.5 | 0.939262 | -2.20672 | -3.14599 | 3.14599 | 0.25 | 12.5839 |
| `slope` | `slope_y` | `final` | `upstream_approach` | `11,6` | 6 | 5.5 | 0.0439545 | -1.4257 | -1.46966 | 1.46966 | 0.25 | 5.87863 |
| `field` | `eta` | `final` | `upstream_approach` | `10,6` | 6 | 4.5 | 2.14496 | 3.6057 | 1.46074 | 1.46074 | 0.25 | 5.84298 |
| `field` | `h` | `final` | `upstream_approach` | `10,6` | 6 | 4.5 | 0.144958 | 1.6057 | 1.46074 | 1.46074 | 0.25 | 5.84298 |
| `field` | `normal_y` | `final` | `upstream_approach` | `11,1` | 1 | 5.5 | -0.147436 | 0.76694 | 0.914376 | 0.914376 | 0.25 | 3.6575 |
| `slope` | `slope_x` | `final` | `upstream_approach` | `10,6` | 6 | 4.5 | -0.0362244 | -0.802789 | -0.766565 | 0.766565 | 0.25 | 3.06626 |
| `field` | `normal_x` | `final` | `upstream_approach` | `1,3` | 3 | -4.5 | -0.0970866 | 0.516095 | 0.613181 | 0.613181 | 0.25 | 2.45272 |
| `field` | `normal_z` | `final` | `upstream_approach` | `11,5` | 5 | 5.5 | 0.999058 | 0.57427 | -0.424788 | 0.424788 | 0.25 | 1.69915 |
| `field` | `hu` | `initial` | `upstream_approach` | `3,7` | 7 | -2.5 | 2.12434 | 2.12434 | 1.02915e-07 | 1.02915e-07 | 0.25 | 4.11662e-07 |

## Worst Probe And Cross-Section Series

| Category | Sample | Field | Time s | Distance m | Abs error | Threshold | Ratio |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `probe` | `midstream_center` | `hv` | n/a | n/a | 2.25322 | 0.25 | 9.01289 |
| `probe` | `downstream_center` | `hv` | n/a | n/a | 1.9079 | 0.25 | 7.63158 |
| `probe` | `downstream_center` | `hu` | n/a | n/a | 1.82628 | 0.25 | 7.30511 |
| `probe` | `midstream_center` | `v` | n/a | n/a | 1.73192 | 0.25 | 6.92768 |
| `cross_section` | `mid_cross_section` | `v` | n/a | n/a | 1.73192 | 0.25 | 6.92768 |
| `probe` | `downstream_center` | `v` | n/a | n/a | 1.64824 | 0.25 | 6.59298 |
| `cross_section` | `mid_cross_section` | `froude` | n/a | n/a | 1.5372 | 0.25 | 6.14881 |
| `probe` | `upstream_center` | `hv` | n/a | n/a | 1.49854 | 0.25 | 5.99416 |
| `probe` | `downstream_center` | `u` | n/a | n/a | 1.27644 | 0.25 | 5.10577 |
| `cross_section` | `mid_cross_section` | `u` | n/a | n/a | 1.09365 | 0.25 | 4.37459 |
| `cross_section` | `mid_cross_section` | `h` | n/a | n/a | 1.05176 | 0.25 | 4.20705 |
| `cross_section` | `mid_cross_section` | `eta` | n/a | n/a | 1.05176 | 0.25 | 4.20705 |

## Blocked Reasons

- C++ constriction field Linf still exceeds the GeoClaw/C++ threshold.
- C++ constriction free-surface slope Linf still exceeds the GeoClaw/C++ threshold.
- C++ constriction point-probe Linf still exceeds the GeoClaw/C++ threshold.
- C++ constriction cross-section Linf still exceeds the GeoClaw/C++ threshold.

## Next Levers

- Start with `field`/`u` at `final` because it is 15.3105x the diagnostic threshold.
- Retune lateral velocity and cross-stream surface-slope shape before adding more downstream speed.
- Keep feature forcing off and rerun the Milestone 17 analytic guardrail after the next solver change.
