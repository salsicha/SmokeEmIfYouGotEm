# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_throat_shelf_edge_final_relief/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_throat_shelf_edge_final_relief/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.60574`
- Max h/u/v/hu/hv delta: `0.941308` / `1.37024` / `1.60574` / `1.50705` / `1.47378`
- Max profile mass delta: `5.36976` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `upper_shelf` | 18 | -0.100858 / 0.67835 | -0.118507 / 1.35013 | -0.0794026 / 1.60574 | -0.294094 / 1.32564 | 0.0380252 / 0.85528 | -1.81545 | 0.0555556 | 6.42297 |
| `recovery` | `upper_edge` | 8 | 0.580465 / 0.842682 | 0.208113 / 1.02502 | 0.511006 / 1.57786 | 0.443278 / 1.02597 | -0.0732269 / 0.899622 | 4.64372 | 0 | 6.31146 |
| `constriction_throat` | `lower_shelf` | 4 | 0.146001 / 0.541208 | 0.0899807 / 0.210905 | 0.0464172 / 0.525518 | 0.430102 / 1.50705 | 0.0683936 / 0.36015 | 0.584003 | 0 | 6.02819 |
| `upstream_approach` | `interior` | 54 | -0.09944 / 0.521335 | 0.197176 / 0.61834 | -0.146884 / 0.822103 | 0.264652 / 1.03726 | -0.248857 / 1.47378 | -5.36976 | 0 | 5.89513 |
| `downstream_constriction` | `interior` | 8 | 0.100537 / 0.220558 | -0.859833 / 1.32818 | -0.16834 / 0.46445 | -0.885455 / 1.45937 | -0.152481 / 0.483391 | 0.804299 | 0 | 5.83749 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 1.37024 / 1.37024 | -0.544841 / 0.544841 | 0.30555 / 0.30555 | -0.0479116 / 0.0479116 | 0.0651685 | 0 | 5.48097 |
| `upstream_approach` | `upper_edge` | 10 | 0.234876 / 0.789933 | -0.704392 / 1.34175 | 0.198378 / 1.27589 | 0.247497 / 1.33521 | -0.510391 / 1.3246 | 2.34876 | 0 | 5.36701 |
| `constriction_throat` | `upper_edge` | 2 | 0.337779 / 0.486409 | -0.00211336 / 0.00647273 | 0.43356 / 1.33994 | 0.806207 / 1.12317 | -0.0437259 / 0.0864049 | 0.675559 | 0 | 5.35976 |
| `upstream_approach` | `lower_edge` | 10 | 0.0659091 / 0.941308 | -0.00973007 / 1.23756 | -0.179614 / 0.894022 | 0.294243 / 1.33016 | -0.245804 / 1.14169 | 0.659091 | 0 | 5.32063 |
| `constriction_throat` | `lower_edge` | 4 | -0.0870769 / 0.230044 | 0.00946999 / 0.519459 | 0.402274 / 1.04529 | -0.172427 / 1.30935 | 0.497764 / 1.08928 | -0.348307 | 0 | 5.23741 |
| `upstream_approach` | `lower_shelf` | 12 | -0.125053 / 0.56859 | -0.0314778 / 1.29645 | 0.194985 / 0.769665 | -0.0878731 / 0.966648 | 0.04263 / 0.746941 | -1.50064 | 0 | 5.18581 |
| `recovery` | `lower_shelf` | 6 | -0.0741688 / 0.141071 | 1.01905 / 1.1774 | -0.0223146 / 0.292114 | 0.215599 / 0.266383 | -0.0080527 / 0.0892385 | -0.445013 | 0 | 4.70961 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `v` | `upstream_approach` | `upper_shelf` | `11,0` | 0 | 5.5 | -0.228902 | -1.83464 | -1.60574 | 1.60574 | 0.25 | 6.42297 |
| `v` | `recovery` | `upper_edge` | `9,20` | 20 | 3.5 | -1.32242 | 0.255446 | 1.57786 | 1.57786 | 0.25 | 6.31146 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,10` | 10 | -2.5 | 1.49207 | 2.99911 | 1.50705 | 1.50705 | 0.25 | 6.02819 |
| `hv` | `upstream_approach` | `interior` | `3,5` | 5 | -2.5 | 1.06936 | -0.404419 | -1.47378 | 1.47378 | 0.25 | 5.89513 |
| `hu` | `downstream_constriction` | `interior` | `5,15` | 15 | -0.5 | 4.05104 | 2.59167 | -1.45937 | 1.45937 | 0.25 | 5.83749 |
| `hv` | `upstream_approach` | `interior` | `3,6` | 6 | -2.5 | 0.891438 | -0.501477 | -1.39292 | 1.39292 | 0.25 | 5.57166 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 1.4331 | 1.37024 | 1.37024 | 0.25 | 5.48097 |
| `u` | `upstream_approach` | `upper_shelf` | `10,1` | 1 | 4.5 | 3.39685 | 2.04672 | -1.35013 | 1.35013 | 0.25 | 5.4005 |
| `u` | `upstream_approach` | `upper_edge` | `9,2` | 2 | 3.5 | 3.50488 | 2.16313 | -1.34175 | 1.34175 | 0.25 | 5.36701 |
| `v` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | -2.58013 | -1.24019 | 1.33994 | 1.33994 | 0.25 | 5.35976 |
| `hu` | `upstream_approach` | `upper_edge` | `9,6` | 6 | 3.5 | 1.30029 | 2.6355 | 1.33521 | 1.33521 | 0.25 | 5.34085 |
| `hu` | `downstream_constriction` | `interior` | `4,15` | 15 | -1.5 | 3.86465 | 2.53292 | -1.33172 | 1.33172 | 0.25 | 5.32689 |
| `hu` | `upstream_approach` | `lower_edge` | `2,6` | 6 | -3.5 | 0.921728 | 2.25189 | 1.33016 | 1.33016 | 0.25 | 5.32063 |
| `u` | `downstream_constriction` | `interior` | `5,14` | 14 | -0.5 | 3.48923 | 2.16105 | -1.32818 | 1.32818 | 0.25 | 5.31271 |
| `hu` | `upstream_approach` | `upper_shelf` | `11,0` | 0 | 5.5 | 2.00238 | 0.676742 | -1.32564 | 1.32564 | 0.25 | 5.30255 |
| `hv` | `upstream_approach` | `upper_edge` | `9,5` | 5 | 3.5 | -0.823694 | -2.1483 | -1.3246 | 1.3246 | 0.25 | 5.29841 |

## Blocked Reasons

- Final-frame `v` field remains 6.42x over threshold at `upstream_approach/upper_shelf` cell 11,0.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `0.941308` m).
- Streamwise shear/momentum mismatch is still active in `constriction_throat/lower_shelf` (max u/hu delta `0.210905`/`1.50705`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/upper_shelf` (max v/hv delta `1.60574`/`0.85528`).

## Next Levers

- Start with `upstream_approach/upper_shelf` cell 11,0; `v` delta is `-1.60574` with reference h `0.864998` m and C++ h `0.186647` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
