# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_downstream_upper_edge_final_return_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_downstream_upper_edge_final_return_profile/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.93187`
- Max h/u/v/hu/hv delta: `1.01572` / `1.71529` / `1.65063` / `1.93187` / `1.41793`
- Max profile mass delta: `7.64657` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `upper_edge` | 10 | 0.433689 / 0.907337 | -0.230264 / 1.27874 | 0.511825 / 1.30914 | 1.12633 / 1.93187 | -0.520438 / 1.26209 | 4.33689 | 0 | 7.72746 |
| `recovery` | `interior` | 46 | 0.00240669 / 0.529765 | -0.174837 / 1.71529 | -0.156435 / 0.806681 | -0.207326 / 1.7475 | -0.191057 / 1.00466 | 0.110708 | 0 | 6.99002 |
| `upstream_approach` | `lower_shelf` | 12 | -0.125056 / 0.568641 | -0.312639 / 1.28747 | 0.468852 / 1.65063 | -0.182998 / 0.966763 | 0.136047 / 0.948116 | -1.50068 | 0 | 6.60252 |
| `constriction_throat` | `lower_shelf` | 4 | 0.244444 / 0.599254 | 0.0888893 / 0.210905 | 0.0360912 / 0.525518 | 0.695797 / 1.61546 | 0.24002 / 1.03662 | 0.977777 | 0 | 6.46184 |
| `upstream_approach` | `upper_shelf` | 18 | -0.100853 / 0.678312 | -0.130583 / 1.35552 | -0.0597176 / 1.60557 | -0.297355 / 1.32542 | 0.0426103 / 0.85547 | -1.81535 | 0.0555556 | 6.42229 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 1.5718 / 1.5718 | -0.603254 / 0.603254 | 0.349893 / 0.349893 | -0.0607623 / 0.0607623 | 0.0651685 | 0 | 6.28721 |
| `constriction_throat` | `upper_edge` | 2 | 0.53462 / 0.584917 | -0.00211336 / 0.00647273 | 0.436713 / 1.33994 | 1.31746 / 1.51655 | 0.0926002 / 0.26902 | 1.06924 | 0 | 6.06621 |
| `recovery` | `upper_edge` | 8 | 0.510945 / 0.842437 | 0.377281 / 1.50397 | 0.216689 / 1.28418 | 0.519888 / 0.958173 | -0.352175 / 0.918101 | 4.08756 | 0 | 6.01589 |
| `downstream_constriction` | `interior` | 8 | 0.104196 / 0.229933 | -0.847836 / 1.30101 | -0.169253 / 0.466912 | -0.862133 / 1.45759 | -0.151975 / 0.4841 | 0.83357 | 0 | 5.83035 |
| `upstream_approach` | `interior` | 54 | -0.141603 / 0.400045 | 0.146149 / 0.651431 | -0.116106 / 0.803452 | 0.134971 / 1.27886 | -0.181911 / 1.41793 | -7.64657 | 0 | 5.6717 |
| `upstream_approach` | `lower_edge` | 10 | 0.096123 / 1.01572 | 0.081528 / 0.889785 | -0.125011 / 0.822947 | 0.473179 / 1.30339 | -0.175035 / 1.06483 | 0.96123 | 0 | 5.21356 |
| `constriction_throat` | `lower_edge` | 4 | -0.0516008 / 0.135712 | 0.00648115 / 0.531439 | 0.397627 / 1.0266 | -0.0817843 / 0.942194 | 0.541276 / 1.26281 | -0.206403 | 0 | 5.05124 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `upstream_approach` | `upper_edge` | `8,9` | 9 | 2.5 | 0.304252 | 2.23612 | 1.93187 | 1.93187 | 0.25 | 7.72746 |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 2.09654 | 1.7475 | 1.7475 | 0.25 | 6.99002 |
| `u` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.12161 | 1.40632 | -1.71529 | 1.71529 | 0.25 | 6.86117 |
| `hu` | `upstream_approach` | `upper_edge` | `9,3` | 3 | 3.5 | 1.30954 | 2.99463 | 1.68509 | 1.68509 | 0.25 | 6.74036 |
| `v` | `upstream_approach` | `lower_shelf` | `1,4` | 4 | -4.5 | 0.513472 | 2.1641 | 1.65063 | 1.65063 | 0.25 | 6.60252 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 2.21755 | -1.61695 | 1.61695 | 0.25 | 6.46782 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 2.31711 | 1.61546 | 1.61546 | 0.25 | 6.46184 |
| `v` | `upstream_approach` | `upper_shelf` | `11,0` | 0 | 5.5 | -0.228902 | -1.83447 | -1.60557 | 1.60557 | 0.25 | 6.42229 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 1.63466 | 1.5718 | 1.5718 | 0.25 | 6.28721 |
| `hu` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 3.75007 | 2.23162 | -1.51845 | 1.51845 | 0.25 | 6.0738 |
| `hu` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 0.701957 | 2.21851 | 1.51655 | 1.51655 | 0.25 | 6.06621 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 1.3886 | 1.50397 | 1.50397 | 0.25 | 6.01589 |
| `u` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.310052 | 1.81239 | 1.50234 | 1.50234 | 0.25 | 6.00934 |
| `u` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 2.91578 | 1.41524 | -1.50054 | 1.50054 | 0.25 | 6.00216 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,10` | 10 | -2.5 | 1.49207 | 2.98867 | 1.4966 | 1.4966 | 0.25 | 5.98642 |
| `u` | `recovery` | `interior` | `4,19` | 19 | -1.5 | 2.89388 | 1.41625 | -1.47763 | 1.47763 | 0.25 | 5.91051 |

## Blocked Reasons

- Final-frame `hu` field remains 7.73x over threshold at `upstream_approach/upper_edge` cell 8,9.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `1.01572` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/upper_edge` (max u/hu delta `1.27874`/`1.93187`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `1.65063`/`0.948116`).

## Next Levers

- Start with `upstream_approach/upper_edge` cell 8,9; `hu` delta is `1.93187` with reference h `0.799984` m and C++ h `1.46126` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
