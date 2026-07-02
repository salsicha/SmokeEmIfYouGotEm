# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_transition_edge_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_transition_edge_final_profile/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.7475`
- Max h/u/v/hu/hv delta: `0.941327` / `1.71529` / `1.65063` / `1.7475` / `1.41793`
- Max profile mass delta: `7.12738` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `recovery` | `interior` | 46 | 0.00240431 / 0.529765 | -0.174838 / 1.71529 | -0.156435 / 0.806678 | -0.207331 / 1.7475 | -0.191057 / 1.00465 | 0.110598 | 0 | 6.99 |
| `upstream_approach` | `upper_edge` | 10 | 0.410863 / 0.907336 | -0.418436 / 1.27874 | 0.428 / 1.30914 | 0.832022 / 1.68509 | -0.613388 / 1.26209 | 4.10863 | 0 | 6.74036 |
| `upstream_approach` | `lower_shelf` | 12 | -0.125057 / 0.568641 | -0.312639 / 1.28747 | 0.468852 / 1.65063 | -0.182998 / 0.966763 | 0.136047 / 0.948116 | -1.50068 | 0 | 6.60252 |
| `constriction_throat` | `lower_shelf` | 4 | 0.244966 / 0.599254 | 0.0899808 / 0.210905 | 0.0339409 / 0.525518 | 0.698408 / 1.61546 | 0.237538 / 1.03662 | 0.979862 | 0 | 6.46184 |
| `upstream_approach` | `upper_shelf` | 18 | -0.100853 / 0.678312 | -0.125021 / 1.35552 | -0.0719303 / 1.60557 | -0.296199 / 1.32542 | 0.0400729 / 0.855497 | -1.81535 | 0.0555556 | 6.42229 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 1.5718 / 1.5718 | -0.603254 / 0.603254 | 0.349893 / 0.349893 | -0.0607623 / 0.0607623 | 0.0651685 | 0 | 6.28721 |
| `constriction_throat` | `upper_edge` | 2 | 0.535663 / 0.584916 | -0.00211336 / 0.00647273 | 0.436713 / 1.33994 | 1.31986 / 1.51655 | 0.091307 / 0.26902 | 1.07133 | 0 | 6.0662 |
| `recovery` | `upper_edge` | 8 | 0.510944 / 0.842436 | 0.377281 / 1.50397 | 0.216689 / 1.28418 | 0.519886 / 0.958167 | -0.352175 / 0.9181 | 4.08755 | 0 | 6.01589 |
| `downstream_constriction` | `interior` | 8 | 0.104194 / 0.229931 | -0.847837 / 1.30101 | -0.169254 / 0.466912 | -0.862137 / 1.45759 | -0.151977 / 0.484102 | 0.833555 | 0 | 5.83037 |
| `upstream_approach` | `interior` | 54 | -0.131988 / 0.521362 | 0.189724 / 0.596219 | -0.127455 / 0.791925 | 0.223467 / 1.03731 | -0.206644 / 1.41793 | -7.12738 | 0 | 5.6717 |
| `upstream_approach` | `lower_edge` | 10 | 0.0660366 / 0.941327 | -0.0198248 / 1.23756 | -0.149341 / 0.894022 | 0.277876 / 1.30339 | -0.196106 / 1.14171 | 0.660366 | 0 | 5.21358 |
| `constriction_throat` | `lower_edge` | 4 | -0.0510292 / 0.133422 | 0.00647535 / 0.531438 | 0.397601 / 1.0266 | -0.0803638 / 0.9422 | 0.54118 / 1.26281 | -0.204117 | 0 | 5.05123 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 2.09653 | 1.7475 | 1.7475 | 0.25 | 6.99 |
| `u` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.12161 | 1.40632 | -1.71529 | 1.71529 | 0.25 | 6.86117 |
| `hu` | `upstream_approach` | `upper_edge` | `9,3` | 3 | 3.5 | 1.30954 | 2.99463 | 1.68509 | 1.68509 | 0.25 | 6.74036 |
| `v` | `upstream_approach` | `lower_shelf` | `1,4` | 4 | -4.5 | 0.513472 | 2.1641 | 1.65063 | 1.65063 | 0.25 | 6.60252 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 2.21755 | -1.61696 | 1.61696 | 0.25 | 6.46783 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 2.31711 | 1.61546 | 1.61546 | 0.25 | 6.46184 |
| `v` | `upstream_approach` | `upper_shelf` | `11,0` | 0 | 5.5 | -0.228902 | -1.83447 | -1.60557 | 1.60557 | 0.25 | 6.42229 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 1.63466 | 1.5718 | 1.5718 | 0.25 | 6.28721 |
| `hu` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 3.75007 | 2.23161 | -1.51845 | 1.51845 | 0.25 | 6.07382 |
| `hu` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 0.701957 | 2.21851 | 1.51655 | 1.51655 | 0.25 | 6.0662 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,10` | 10 | -2.5 | 1.49207 | 2.99912 | 1.50705 | 1.50705 | 0.25 | 6.0282 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 1.3886 | 1.50397 | 1.50397 | 0.25 | 6.01589 |
| `u` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.310052 | 1.81239 | 1.50234 | 1.50234 | 0.25 | 6.00934 |
| `u` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 2.91578 | 1.41524 | -1.50054 | 1.50054 | 0.25 | 6.00216 |
| `u` | `recovery` | `interior` | `4,19` | 19 | -1.5 | 2.89388 | 1.41625 | -1.47763 | 1.47763 | 0.25 | 5.91051 |
| `hu` | `recovery` | `interior` | `5,20` | 20 | -0.5 | 3.83038 | 2.36209 | -1.46828 | 1.46828 | 0.25 | 5.87313 |

## Blocked Reasons

- Final-frame `hu` field remains 6.99x over threshold at `recovery/interior` cell 3,18.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `0.941327` m).
- Streamwise shear/momentum mismatch is still active in `recovery/interior` (max u/hu delta `1.71529`/`1.7475`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `1.65063`/`0.948116`).

## Next Levers

- Start with `recovery/interior` cell 3,18; `hu` delta is `1.7475` with reference h `1.12573` m and C++ h `1.15678` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
