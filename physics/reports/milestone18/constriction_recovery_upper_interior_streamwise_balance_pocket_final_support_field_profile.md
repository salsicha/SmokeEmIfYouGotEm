# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_upper_interior_streamwise_balance_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_upper_interior_streamwise_balance_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.33579`
- Max h/u/v/hu/hv delta: `0.309993` / `0.329199` / `0.33579` / `0.332812` / `0.322086`
- Max profile mass delta: `4.38441` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |
| `constriction_throat` | `interior` | 8 | 0.0511096 / 0.141702 | -0.0168364 / 0.150006 | 0.0158585 / 0.0774815 | 0.143981 / 0.332812 | 0.0281307 / 0.112833 | 0.408876 | 0 | 1.33125 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.104128 / 0.329199 | -0.107961 / 0.285449 | 0.103474 / 0.248846 | -0.0765761 / 0.286294 | 0.809547 | 0 | 1.3168 |
| `upstream_approach` | `lower_shelf` | 12 | -0.0345226 / 0.293742 | -0.00878871 / 0.324043 | 0.0133891 / 0.221148 | 0.0108789 / 0.323404 | -0.0136829 / 0.294638 | -0.414271 | 0 | 1.29617 |
| `constriction_throat` | `upper_edge` | 2 | 0.105621 / 0.121761 | -0.00211336 / 0.00647273 | -0.0594552 / 0.103293 | 0.256167 / 0.28181 | -0.128521 / 0.322086 | 0.211242 | 0 | 1.28834 |
| `upstream_approach` | `interior` | 54 | -0.0472677 / 0.263487 | 0.0400205 / 0.254233 | -0.0116253 / 0.177068 | 0.0499342 / 0.314239 | -0.0274209 / 0.289765 | -2.55245 | 0 | 1.25696 |
| `recovery` | `interior` | 46 | 0.0953134 / 0.277436 | -0.081601 / 0.309551 | -0.0158518 / 0.278258 | 0.0740249 / 0.313287 | -0.0115655 / 0.302606 | 4.38441 | 0 | 1.25315 |
| `constriction_throat` | `lower_edge` | 4 | 0.00564182 / 0.0643546 | 0.0121396 / 0.0530374 | 0.107042 / 0.196049 | 0.0288383 / 0.184885 | 0.155837 / 0.312878 | 0.0225673 | 0 | 1.25151 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0192081 / 0.181599 | -0.0107517 / 0.173703 | -0.0380703 / 0.231657 | -0.0321846 / 0.28896 | -0.709597 | 0 | 1.23997 |
| `upstream_approach` | `upper_shelf` | 18 | -0.00913431 / 0.0899976 | -0.0443429 / 0.270835 | -0.0100128 / 0.300528 | -0.0272571 / 0.291333 | 0.0169122 / 0.272483 | -0.164418 | 0.0555556 | 1.20211 |
| `recovery` | `upper_edge` | 8 | 0.0982205 / 0.232384 | -0.00938194 / 0.279153 | 0.0320627 / 0.239044 | 0.0445599 / 0.124942 | -0.0869955 / 0.18549 | 0.785764 | 0 | 1.11661 |
| `upstream_approach` | `upper_edge` | 10 | 0.00561358 / 0.103644 | -0.0774046 / 0.262286 | 0.0102379 / 0.105336 | 0.000946168 / 0.237098 | -0.0270507 / 0.239362 | 0.0561358 | 0 | 1.04915 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `v` | `constriction_throat` | `lower_shelf` | `3,11` | 11 | -2.5 | 0.693877 | 1.02967 | 0.33579 | 0.33579 | 0.25 | 1.34316 |
| `hu` | `constriction_throat` | `interior` | `5,10` | 10 | -0.5 | 3.88779 | 4.2206 | 0.332812 | 0.332812 | 0.25 | 1.33125 |
| `u` | `downstream_constriction` | `interior` | `6,15` | 15 | 0.5 | 3.03794 | 2.70874 | -0.329199 | 0.329199 | 0.25 | 1.3168 |
| `u` | `upstream_approach` | `lower_shelf` | `0,2` | 2 | -5.5 | 3.28259 | 2.95854 | -0.324043 | 0.324043 | 0.25 | 1.29617 |
| `hu` | `upstream_approach` | `lower_shelf` | `0,2` | 2 | -5.5 | 0.56416 | 0.887563 | 0.323404 | 0.323404 | 0.25 | 1.29361 |
| `hv` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | -0.995196 | -1.31728 | -0.322086 | 0.322086 | 0.25 | 1.28834 |
| `hu` | `upstream_approach` | `interior` | `4,2` | 2 | -1.5 | 0.544031 | 0.85827 | 0.314239 | 0.314239 | 0.25 | 1.25696 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 4.14779 | 0.313287 | 0.313287 | 0.25 | 1.25315 |
| `hv` | `constriction_throat` | `lower_edge` | `4,12` | 12 | -1.5 | 0.265452 | 0.578331 | 0.312878 | 0.312878 | 0.25 | 1.25151 |
| `h` | `upstream_approach` | `lower_edge` | `2,6` | 6 | -3.5 | 1.94414 | 1.63415 | -0.309993 | 0.309993 | 0.25 | 1.23997 |
| `u` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.12161 | 2.81206 | -0.309551 | 0.309551 | 0.25 | 1.2382 |
| `hu` | `upstream_approach` | `interior` | `8,6` | 6 | 2.5 | 2.26775 | 2.57719 | 0.309443 | 0.309443 | 0.25 | 1.23777 |
| `hv` | `recovery` | `interior` | `5,16` | 16 | -0.5 | 0.727055 | 0.424449 | -0.302606 | 0.302606 | 0.25 | 1.21042 |
| `hu` | `upstream_approach` | `interior` | `3,4` | 4 | -2.5 | 1.23046 | 1.53202 | 0.30155 | 0.30155 | 0.25 | 1.2062 |
| `v` | `upstream_approach` | `upper_shelf` | `11,7` | 7 | 5.5 | -0.421932 | -0.722461 | -0.300528 | 0.300528 | 0.25 | 1.20211 |
| `hu` | `upstream_approach` | `interior` | `6,8` | 8 | 0.5 | 2.68314 | 2.98238 | 0.299246 | 0.299246 | 0.25 | 1.19699 |

## Blocked Reasons

- Final-frame `v` field remains 1.34x over threshold at `constriction_throat/lower_shelf` cell 3,11.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `0.309993` m).
- Streamwise shear/momentum mismatch is still active in `constriction_throat/interior` (max u/hu delta `0.150006`/`0.332812`).
- Cross-stream shear/momentum mismatch is still active in `constriction_throat/lower_shelf` (max v/hv delta `0.33579`/`0.241447`).

## Next Levers

- Start with `constriction_throat/lower_shelf` cell 3,11; `v` delta is `0.33579` with reference h `0.534869` m and C++ h `0.594932` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
