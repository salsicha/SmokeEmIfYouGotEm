# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_upper_core_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_upper_core_final_profile/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.65066`
- Max h/u/v/hu/hv delta: `0.94132` / `1.5718` / `1.65066` / `1.61546` / `1.47364`
- Max profile mass delta: `5.37004` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `lower_shelf` | 12 | -0.125055 / 0.568614 | -0.311251 / 1.28749 | 0.465647 / 1.65066 | -0.182225 / 0.966648 | 0.13422 / 0.940383 | -1.50066 | 0 | 6.60263 |
| `constriction_throat` | `lower_shelf` | 4 | 0.244966 / 0.599254 | 0.0899807 / 0.210905 | 0.0339409 / 0.525518 | 0.698408 / 1.61546 | 0.237538 / 1.03662 | 0.979863 | 0 | 6.46184 |
| `upstream_approach` | `upper_shelf` | 18 | -0.100857 / 0.678349 | -0.118649 / 1.35035 | -0.0793728 / 1.60574 | -0.294159 / 1.32563 | 0.0380315 / 0.85528 | -1.81543 | 0.0555556 | 6.42295 |
| `recovery` | `upper_edge` | 8 | 0.511139 / 0.842683 | 0.247152 / 1.13175 | 0.491726 / 1.57786 | 0.40411 / 0.712751 | -0.0755357 / 0.918099 | 4.08911 | 0 | 6.31146 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 1.5718 / 1.5718 | -0.603254 / 0.603254 | 0.349893 / 0.349893 | -0.0607623 / 0.0607623 | 0.0651685 | 0 | 6.28721 |
| `constriction_throat` | `upper_edge` | 2 | 0.535663 / 0.584917 | -0.00211336 / 0.00647273 | 0.436713 / 1.33994 | 1.31986 / 1.51655 | 0.0913071 / 0.26902 | 1.07133 | 0 | 6.06621 |
| `upstream_approach` | `interior` | 54 | -0.0994453 / 0.521353 | 0.196695 / 0.618301 | -0.146349 / 0.822025 | 0.263815 / 1.03729 | -0.247936 / 1.47364 | -5.37004 | 0 | 5.89457 |
| `downstream_constriction` | `interior` | 8 | 0.104187 / 0.229925 | -0.847838 / 1.30102 | -0.169254 / 0.466913 | -0.862153 / 1.45761 | -0.151981 / 0.484106 | 0.833497 | 0 | 5.83045 |
| `upstream_approach` | `upper_edge` | 10 | 0.234849 / 0.789925 | -0.704392 / 1.34175 | 0.198354 / 1.27589 | 0.247433 / 1.33519 | -0.510359 / 1.32455 | 2.34849 | 0 | 5.36701 |
| `upstream_approach` | `lower_edge` | 10 | 0.066043 / 0.94132 | -0.0120406 / 1.23756 | -0.174239 / 0.894022 | 0.290629 / 1.32921 | -0.236789 / 1.1417 | 0.66043 | 0 | 5.31683 |
| `constriction_throat` | `lower_edge` | 4 | -0.0510295 / 0.133423 | 0.00647549 / 0.531437 | 0.397601 / 1.0266 | -0.0803643 / 0.942203 | 0.54118 / 1.26281 | -0.204118 | 0 | 5.05122 |
| `recovery` | `lower_shelf` | 6 | -0.0741689 / 0.141071 | 1.01904 / 1.1774 | -0.0223151 / 0.292114 | 0.215595 / 0.26636 | -0.00805281 / 0.0892385 | -0.445014 | 0 | 4.70962 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `v` | `upstream_approach` | `lower_shelf` | `1,4` | 4 | -4.5 | 0.513472 | 2.16413 | 1.65066 | 1.65066 | 0.25 | 6.60263 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 2.31711 | 1.61546 | 1.61546 | 0.25 | 6.46184 |
| `v` | `upstream_approach` | `upper_shelf` | `11,0` | 0 | 5.5 | -0.228902 | -1.83464 | -1.60574 | 1.60574 | 0.25 | 6.42295 |
| `v` | `recovery` | `upper_edge` | `9,20` | 20 | 3.5 | -1.32242 | 0.255446 | 1.57786 | 1.57786 | 0.25 | 6.31146 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 1.63466 | 1.5718 | 1.5718 | 0.25 | 6.28721 |
| `hu` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 0.701957 | 2.21851 | 1.51655 | 1.51655 | 0.25 | 6.06621 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,10` | 10 | -2.5 | 1.49207 | 2.99912 | 1.50705 | 1.50705 | 0.25 | 6.0282 |
| `hv` | `upstream_approach` | `interior` | `3,5` | 5 | -2.5 | 1.06936 | -0.404278 | -1.47364 | 1.47364 | 0.25 | 5.89457 |
| `hu` | `downstream_constriction` | `interior` | `5,15` | 15 | -0.5 | 4.05104 | 2.59343 | -1.45761 | 1.45761 | 0.25 | 5.83045 |
| `hv` | `upstream_approach` | `interior` | `3,6` | 6 | -2.5 | 0.891438 | -0.501481 | -1.39292 | 1.39292 | 0.25 | 5.57168 |
| `u` | `upstream_approach` | `upper_shelf` | `10,1` | 1 | 4.5 | 3.39685 | 2.04649 | -1.35035 | 1.35035 | 0.25 | 5.40142 |
| `u` | `upstream_approach` | `upper_edge` | `9,2` | 2 | 3.5 | 3.50488 | 2.16313 | -1.34175 | 1.34175 | 0.25 | 5.36701 |
| `v` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | -2.58013 | -1.24019 | 1.33994 | 1.33994 | 0.25 | 5.35976 |
| `hu` | `upstream_approach` | `upper_edge` | `9,6` | 6 | 3.5 | 1.30029 | 2.63548 | 1.33519 | 1.33519 | 0.25 | 5.34077 |
| `hu` | `downstream_constriction` | `interior` | `4,15` | 15 | -1.5 | 3.86465 | 2.53441 | -1.33024 | 1.33024 | 0.25 | 5.32095 |
| `hu` | `upstream_approach` | `lower_edge` | `2,6` | 6 | -3.5 | 0.921728 | 2.25093 | 1.32921 | 1.32921 | 0.25 | 5.31683 |

## Blocked Reasons

- Final-frame `v` field remains 6.60x over threshold at `upstream_approach/lower_shelf` cell 1,4.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `0.94132` m).
- Streamwise shear/momentum mismatch is still active in `constriction_throat/lower_shelf` (max u/hu delta `0.210905`/`1.61546`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `1.65066`/`0.940383`).

## Next Levers

- Start with `upstream_approach/lower_shelf` cell 1,4; `v` delta is `1.65066` with reference h `0.497546` m and C++ h `0.304195` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
