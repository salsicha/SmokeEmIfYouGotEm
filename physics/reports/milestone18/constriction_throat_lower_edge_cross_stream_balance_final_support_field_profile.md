# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_throat_lower_edge_cross_stream_balance_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_throat_lower_edge_cross_stream_balance_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.309443`
- Max h/u/v/hu/hv delta: `0.293742` / `0.291581` / `0.300528` / `0.309443` / `0.302606`
- Max profile mass delta: `4.13691` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `interior` | 54 | -0.0472677 / 0.263487 | 0.0363676 / 0.254233 | -0.00981848 / 0.177068 | 0.0436974 / 0.309443 | -0.024336 / 0.289765 | -2.55245 | 0 | 1.23777 |
| `recovery` | `interior` | 46 | 0.0899329 / 0.277436 | -0.0748608 / 0.285781 | -0.0158393 / 0.278258 | 0.0671684 / 0.299089 | -0.0125899 / 0.302606 | 4.13691 | 0 | 1.21042 |
| `upstream_approach` | `upper_shelf` | 18 | -0.00913431 / 0.0899976 | -0.0443429 / 0.270835 | -0.0100128 / 0.300528 | -0.0272571 / 0.291333 | 0.0169122 / 0.272483 | -0.164418 | 0.0555556 | 1.20211 |
| `upstream_approach` | `lower_shelf` | 12 | -0.040179 / 0.293742 | 0.0181584 / 0.291581 | 0.0133043 / 0.221148 | -0.00321591 / 0.23179 | -0.0172536 / 0.294638 | -0.482147 | 0 | 1.17855 |
| `upstream_approach` | `lower_edge` | 10 | -0.0462097 / 0.25145 | 0.00261674 / 0.139129 | -0.00314633 / 0.173703 | -0.0530608 / 0.231657 | -0.0100558 / 0.28896 | -0.462097 | 0 | 1.15584 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.0728258 / 0.218799 | -0.0749182 / 0.285449 | 0.146906 / 0.248846 | -0.0307291 / 0.286294 | 0.809547 | 0 | 1.14518 |
| `recovery` | `upper_edge` | 8 | 0.0982205 / 0.232384 | -0.00938194 / 0.279153 | 0.0320627 / 0.239044 | 0.0445599 / 0.124942 | -0.0869955 / 0.18549 | 0.785764 | 0 | 1.11661 |
| `upstream_approach` | `upper_edge` | 10 | 0.00561358 / 0.103644 | -0.0774046 / 0.262286 | 0.0102379 / 0.105336 | 0.000946168 / 0.237098 | -0.0270507 / 0.239362 | 0.0561358 | 0 | 1.04915 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0281762 / 0.197679 | 0.0621684 / 0.189954 | 0.023389 / 0.222921 | 0.0931088 / 0.258701 | 0.208015 | 0 | 1.0348 |
| `constriction_throat` | `interior` | 8 | 0.0511096 / 0.141702 | -0.0356034 / 0.135023 | 0.0158585 / 0.0774815 | 0.112704 / 0.241919 | 0.0281307 / 0.112833 | 0.408876 | 0 | 0.967675 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.00340341 / 0.03885 | 0.0615502 / 0.233658 | 0.0205625 / 0.0417079 | 0.071492 | 0 | 0.934631 |
| `constriction_throat` | `upper_edge` | 2 | 0.0456327 / 0.0894804 | -0.00326703 / 0.00647273 | -0.051668 / 0.103293 | 0.117307 / 0.230523 | 0.030211 / 0.065044 | 0.0912653 | 0 | 0.922091 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `upstream_approach` | `interior` | `8,6` | 6 | 2.5 | 2.26775 | 2.57719 | 0.309443 | 0.309443 | 0.25 | 1.23777 |
| `hv` | `recovery` | `interior` | `5,16` | 16 | -0.5 | 0.727055 | 0.424449 | -0.302606 | 0.302606 | 0.25 | 1.21042 |
| `hu` | `upstream_approach` | `interior` | `3,4` | 4 | -2.5 | 1.23046 | 1.53202 | 0.30155 | 0.30155 | 0.25 | 1.2062 |
| `v` | `upstream_approach` | `upper_shelf` | `11,7` | 7 | 5.5 | -0.421932 | -0.722461 | -0.300528 | 0.300528 | 0.25 | 1.20211 |
| `hu` | `upstream_approach` | `interior` | `6,8` | 8 | 0.5 | 2.68314 | 2.98238 | 0.299246 | 0.299246 | 0.25 | 1.19699 |
| `hu` | `recovery` | `interior` | `5,20` | 20 | -0.5 | 3.83038 | 4.12947 | 0.299089 | 0.299089 | 0.25 | 1.19636 |
| `hv` | `upstream_approach` | `lower_shelf` | `1,2` | 2 | -4.5 | 0.738493 | 1.03313 | 0.294638 | 0.294638 | 0.25 | 1.17855 |
| `v` | `upstream_approach` | `upper_shelf` | `11,5` | 5 | 5.5 | -0.323971 | -0.618286 | -0.294316 | 0.294316 | 0.25 | 1.17726 |
| `h` | `upstream_approach` | `lower_shelf` | `1,6` | 6 | -4.5 | 0.840273 | 0.546531 | -0.293742 | 0.293742 | 0.25 | 1.17497 |
| `u` | `upstream_approach` | `lower_shelf` | `1,2` | 2 | -4.5 | 3.83283 | 3.54125 | -0.291581 | 0.291581 | 0.25 | 1.16632 |
| `hu` | `upstream_approach` | `upper_shelf` | `9,7` | 7 | 3.5 | 1.0721 | 0.780768 | -0.291333 | 0.291333 | 0.25 | 1.16533 |
| `hv` | `recovery` | `interior` | `6,21` | 21 | 0.5 | 0.142262 | -0.148682 | -0.290944 | 0.290944 | 0.25 | 1.16378 |
| `hv` | `upstream_approach` | `interior` | `4,8` | 8 | -1.5 | -0.378447 | -0.668212 | -0.289765 | 0.289765 | 0.25 | 1.15906 |
| `hv` | `upstream_approach` | `lower_edge` | `2,3` | 3 | -3.5 | 0.0141457 | 0.303106 | 0.28896 | 0.28896 | 0.25 | 1.15584 |
| `hv` | `downstream_constriction` | `interior` | `5,14` | 14 | -0.5 | 0.847429 | 0.561135 | -0.286294 | 0.286294 | 0.25 | 1.14518 |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 0.635174 | 0.28614 | 0.28614 | 0.25 | 1.14456 |

## Blocked Reasons

- Final-frame `hu` field remains 1.24x over threshold at `upstream_approach/interior` cell 8,6.
- Depth/profile mismatch is still active in `upstream_approach/lower_shelf` (max h delta `0.293742` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/interior` (max u/hu delta `0.254233`/`0.309443`).
- Cross-stream shear/momentum mismatch is still active in `recovery/interior` (max v/hv delta `0.278258`/`0.302606`).

## Next Levers

- Start with `upstream_approach/interior` cell 8,6; `hu` delta is `0.309443` with reference h `1.85496` m and C++ h `1.81252` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
