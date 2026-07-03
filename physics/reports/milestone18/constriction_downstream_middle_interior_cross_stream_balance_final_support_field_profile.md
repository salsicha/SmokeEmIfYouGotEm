# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_downstream_middle_interior_cross_stream_balance_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_downstream_middle_interior_cross_stream_balance_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.28614`
- Max h/u/v/hu/hv delta: `0.277436` / `0.285781` / `0.263705` / `0.28614` / `0.284311`
- Max profile mass delta: `3.93832` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `recovery` | `interior` | 46 | 0.0856157 / 0.277436 | -0.0706354 / 0.285781 | -0.00539434 / 0.191931 | 0.0607041 / 0.28614 | 0.00219097 / 0.280291 | 3.93832 | 0 | 1.14456 |
| `upstream_approach` | `interior` | 54 | -0.0472677 / 0.263487 | 0.0258046 / 0.254233 | -0.00767891 / 0.177068 | 0.0253467 / 0.278403 | -0.0206342 / 0.284311 | -2.55245 | 0 | 1.13724 |
| `recovery` | `upper_edge` | 8 | 0.0982205 / 0.232384 | -0.00938194 / 0.279153 | 0.0320627 / 0.239044 | 0.0445599 / 0.124942 | -0.0869955 / 0.18549 | 0.785764 | 0 | 1.11661 |
| `upstream_approach` | `lower_shelf` | 12 | -0.0236296 / 0.0895693 | 0.0250608 / 0.276679 | -0.0204984 / 0.153865 | -0.0255879 / 0.138735 | -0.0357168 / 0.223915 | -0.283556 | 0 | 1.10672 |
| `upstream_approach` | `upper_shelf` | 18 | -0.00913431 / 0.0899976 | -0.0284828 / 0.251359 | 0.00921659 / 0.263705 | -0.0192516 / 0.229945 | 0.0147086 / 0.20115 | -0.164418 | 0.0555556 | 1.05482 |
| `upstream_approach` | `upper_edge` | 10 | 0.00561358 / 0.103644 | -0.0774046 / 0.262286 | 0.0102379 / 0.105336 | 0.000946168 / 0.237098 | -0.0270507 / 0.239362 | 0.0561358 | 0 | 1.04915 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0281762 / 0.197679 | 0.0621684 / 0.189954 | 0.023389 / 0.222921 | 0.0931088 / 0.258701 | 0.208015 | 0 | 1.0348 |
| `upstream_approach` | `lower_edge` | 10 | -0.0462097 / 0.25145 | 0.00261674 / 0.139129 | -0.0205066 / 0.100765 | -0.0530608 / 0.231657 | -0.039019 / 0.243958 | -0.462097 | 0 | 1.0058 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.0728258 / 0.218799 | -0.0393133 / 0.202843 | 0.146906 / 0.248846 | 0.0169657 / 0.212547 | 0.809547 | 0 | 0.995385 |
| `constriction_throat` | `interior` | 8 | 0.0511096 / 0.141702 | -0.0356034 / 0.135023 | 0.0158585 / 0.0774815 | 0.112704 / 0.241919 | 0.0281307 / 0.112833 | 0.408876 | 0 | 0.967675 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.00340341 / 0.03885 | 0.0615502 / 0.233658 | 0.0205625 / 0.0417079 | 0.071492 | 0 | 0.934631 |
| `constriction_throat` | `upper_edge` | 2 | 0.0456327 / 0.0894804 | -0.00326703 / 0.00647273 | -0.051668 / 0.103293 | 0.117307 / 0.230523 | 0.030211 / 0.065044 | 0.0912653 | 0 | 0.922091 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 0.635174 | 0.28614 | 0.28614 | 0.25 | 1.14456 |
| `u` | `recovery` | `interior` | `8,23` | 23 | 2.5 | 1.21176 | 0.925983 | -0.285781 | 0.285781 | 0.25 | 1.14312 |
| `hv` | `upstream_approach` | `interior` | `6,4` | 4 | 0.5 | -0.271389 | -0.555699 | -0.284311 | 0.284311 | 0.25 | 1.13724 |
| `hv` | `recovery` | `interior` | `7,22` | 22 | 1.5 | 0.0803816 | -0.199909 | -0.280291 | 0.280291 | 0.25 | 1.12116 |
| `u` | `recovery` | `upper_edge` | `9,21` | 21 | 3.5 | 0.510092 | 0.23094 | -0.279153 | 0.279153 | 0.25 | 1.11661 |
| `hu` | `upstream_approach` | `interior` | `5,8` | 8 | -0.5 | 2.85796 | 3.13637 | 0.278403 | 0.278403 | 0.25 | 1.11361 |
| `h` | `recovery` | `interior` | `8,23` | 23 | 2.5 | 1.45123 | 1.72867 | 0.277436 | 0.277436 | 0.25 | 1.10974 |
| `u` | `upstream_approach` | `lower_shelf` | `1,3` | 3 | -4.5 | 3.49092 | 3.7676 | 0.276679 | 0.276679 | 0.25 | 1.10672 |
| `hu` | `recovery` | `interior` | `6,16` | 16 | 0.5 | 3.78421 | 4.05832 | 0.274105 | 0.274105 | 0.25 | 1.09642 |
| `h` | `recovery` | `interior` | `3,19` | 19 | -2.5 | 1.16739 | 1.43831 | 0.270925 | 0.270925 | 0.25 | 1.0837 |
| `hu` | `recovery` | `interior` | `5,18` | 18 | -0.5 | 3.81809 | 4.08499 | 0.266907 | 0.266907 | 0.25 | 1.06763 |
| `u` | `recovery` | `interior` | `5,21` | 21 | -0.5 | 2.74567 | 2.48038 | -0.265283 | 0.265283 | 0.25 | 1.06113 |
| `v` | `upstream_approach` | `upper_shelf` | `11,6` | 6 | 5.5 | -0.354582 | -0.618286 | -0.263705 | 0.263705 | 0.25 | 1.05482 |
| `h` | `upstream_approach` | `interior` | `4,6` | 6 | -1.5 | 1.86864 | 1.60515 | -0.263487 | 0.263487 | 0.25 | 1.05395 |
| `u` | `upstream_approach` | `upper_edge` | `9,6` | 6 | 3.5 | 2.86357 | 2.60128 | -0.262286 | 0.262286 | 0.25 | 1.04915 |
| `h` | `recovery` | `interior` | `8,21` | 21 | 2.5 | 1.42473 | 1.68667 | 0.261945 | 0.261945 | 0.25 | 1.04778 |

## Blocked Reasons

- Final-frame `hu` field remains 1.14x over threshold at `recovery/interior` cell 3,18.
- Depth/profile mismatch is still active in `recovery/interior` (max h delta `0.277436` m).
- Streamwise shear/momentum mismatch is still active in `recovery/interior` (max u/hu delta `0.285781`/`0.28614`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/interior` (max v/hv delta `0.177068`/`0.284311`).

## Next Levers

- Start with `recovery/interior` cell 3,18; `hu` delta is `0.28614` with reference h `1.12573` m and C++ h `1.15969` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
