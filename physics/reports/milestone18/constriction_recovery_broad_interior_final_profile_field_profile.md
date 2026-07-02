# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_broad_interior_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_broad_interior_final_profile/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.68509`
- Max h/u/v/hu/hv delta: `0.941313` / `1.5718` / `1.65063` / `1.68509` / `1.41792`
- Max profile mass delta: `7.12775` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `upper_edge` | 10 | 0.410861 / 0.907336 | -0.418436 / 1.27874 | 0.428 / 1.30914 | 0.832019 / 1.68509 | -0.613384 / 1.26209 | 4.10861 | 0 | 6.74036 |
| `upstream_approach` | `lower_shelf` | 12 | -0.125057 / 0.568641 | -0.312639 / 1.28747 | 0.468852 / 1.65063 | -0.182998 / 0.966763 | 0.136047 / 0.948116 | -1.50068 | 0 | 6.60252 |
| `constriction_throat` | `lower_shelf` | 4 | 0.244966 / 0.599254 | 0.0899807 / 0.210905 | 0.0339409 / 0.525518 | 0.698408 / 1.61546 | 0.237538 / 1.03662 | 0.979862 | 0 | 6.46184 |
| `upstream_approach` | `upper_shelf` | 18 | -0.100853 / 0.678313 | -0.125022 / 1.35552 | -0.0719304 / 1.60557 | -0.2962 / 1.32543 | 0.0400729 / 0.855497 | -1.81536 | 0.0555556 | 6.42229 |
| `recovery` | `upper_edge` | 8 | 0.511139 / 0.842683 | 0.247151 / 1.13175 | 0.491726 / 1.57786 | 0.40411 / 0.712751 | -0.0755357 / 0.918099 | 4.08911 | 0 | 6.31146 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 1.5718 / 1.5718 | -0.603254 / 0.603254 | 0.349893 / 0.349893 | -0.0607623 / 0.0607623 | 0.0651685 | 0 | 6.28721 |
| `constriction_throat` | `upper_edge` | 2 | 0.535663 / 0.584916 | -0.00211336 / 0.00647273 | 0.436713 / 1.33994 | 1.31986 / 1.51655 | 0.0913071 / 0.26902 | 1.07133 | 0 | 6.0662 |
| `downstream_constriction` | `interior` | 8 | 0.104187 / 0.229925 | -0.847838 / 1.30102 | -0.169254 / 0.466913 | -0.862153 / 1.45761 | -0.151981 / 0.484106 | 0.833497 | 0 | 5.83045 |
| `upstream_approach` | `interior` | 54 | -0.131995 / 0.521354 | 0.189724 / 0.596219 | -0.127456 / 0.791925 | 0.22346 / 1.03729 | -0.206642 / 1.41792 | -7.12775 | 0 | 5.6717 |
| `upstream_approach` | `lower_edge` | 10 | 0.0660342 / 0.941313 | -0.0198248 / 1.23756 | -0.149341 / 0.894022 | 0.277874 / 1.30339 | -0.196105 / 1.1417 | 0.660342 | 0 | 5.21357 |
| `constriction_throat` | `lower_edge` | 4 | -0.0510295 / 0.133423 | 0.0064755 / 0.531437 | 0.397601 / 1.0266 | -0.0803643 / 0.942203 | 0.54118 / 1.26281 | -0.204118 | 0 | 5.05122 |
| `recovery` | `lower_shelf` | 6 | -0.0741689 / 0.141071 | 1.01904 / 1.1774 | -0.0223151 / 0.292114 | 0.215595 / 0.26636 | -0.00805281 / 0.0892385 | -0.445014 | 0 | 4.70962 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `upstream_approach` | `upper_edge` | `9,3` | 3 | 3.5 | 1.30954 | 2.99463 | 1.68509 | 1.68509 | 0.25 | 6.74036 |
| `v` | `upstream_approach` | `lower_shelf` | `1,4` | 4 | -4.5 | 0.513472 | 2.1641 | 1.65063 | 1.65063 | 0.25 | 6.60252 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 2.31711 | 1.61546 | 1.61546 | 0.25 | 6.46184 |
| `v` | `upstream_approach` | `upper_shelf` | `11,0` | 0 | 5.5 | -0.228902 | -1.83447 | -1.60557 | 1.60557 | 0.25 | 6.42229 |
| `v` | `recovery` | `upper_edge` | `9,20` | 20 | 3.5 | -1.32242 | 0.255446 | 1.57786 | 1.57786 | 0.25 | 6.31146 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 1.63466 | 1.5718 | 1.5718 | 0.25 | 6.28721 |
| `hu` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 0.701957 | 2.21851 | 1.51655 | 1.51655 | 0.25 | 6.0662 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,10` | 10 | -2.5 | 1.49207 | 2.99912 | 1.50705 | 1.50705 | 0.25 | 6.02819 |
| `hu` | `downstream_constriction` | `interior` | `5,15` | 15 | -0.5 | 4.05104 | 2.59343 | -1.45761 | 1.45761 | 0.25 | 5.83045 |
| `hu` | `upstream_approach` | `upper_edge` | `9,4` | 4 | 3.5 | 1.4354 | 2.87225 | 1.43685 | 1.43685 | 0.25 | 5.74741 |
| `hv` | `upstream_approach` | `interior` | `3,5` | 5 | -2.5 | 1.06936 | -0.348561 | -1.41792 | 1.41792 | 0.25 | 5.6717 |
| `hu` | `upstream_approach` | `upper_edge` | `9,5` | 5 | 3.5 | 1.41716 | 2.80518 | 1.38802 | 1.38802 | 0.25 | 5.55207 |
| `hv` | `upstream_approach` | `interior` | `3,6` | 6 | -2.5 | 0.891438 | -0.470873 | -1.36231 | 1.36231 | 0.25 | 5.44924 |
| `u` | `upstream_approach` | `upper_shelf` | `10,1` | 1 | 4.5 | 3.39685 | 2.04133 | -1.35552 | 1.35552 | 0.25 | 5.42208 |
| `v` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | -2.58013 | -1.24019 | 1.33994 | 1.33994 | 0.25 | 5.35976 |
| `hu` | `downstream_constriction` | `interior` | `4,15` | 15 | -1.5 | 3.86465 | 2.53441 | -1.33024 | 1.33024 | 0.25 | 5.32095 |

## Blocked Reasons

- Final-frame `hu` field remains 6.74x over threshold at `upstream_approach/upper_edge` cell 9,3.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `0.941313` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/upper_edge` (max u/hu delta `1.27874`/`1.68509`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `1.65063`/`0.948116`).

## Next Levers

- Start with `upstream_approach/upper_edge` cell 9,3; `hu` delta is `1.68509` with reference h `0.383856` m and C++ h `1.25669` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
