# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **PASS**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_lower_edge_face_depth_balance_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_lower_edge_face_depth_balance_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.248846`
- Max h/u/v/hu/hv delta: `0.245882` / `0.245967` / `0.239044` / `0.248846` / `0.239362`
- Max profile mass delta: `2.91197` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.0728258 / 0.218799 | -0.0393133 / 0.202843 | 0.146906 / 0.248846 | 0.0169657 / 0.212547 | 0.809547 | 0 | 0.995385 |
| `recovery` | `interior` | 46 | 0.0633037 / 0.244381 | -0.0522495 / 0.245967 | -0.00698809 / 0.189581 | 0.0514495 / 0.239383 | -0.00372707 / 0.226973 | 2.91197 | 0 | 0.983867 |
| `upstream_approach` | `interior` | 54 | -0.0449697 / 0.245882 | 0.0179602 / 0.243594 | -0.000320834 / 0.121194 | 0.0141934 / 0.229556 | -0.00690035 / 0.218774 | -2.42836 | 0 | 0.983529 |
| `upstream_approach` | `upper_shelf` | 18 | -0.00913431 / 0.0899976 | -0.0137271 / 0.245143 | 0.0247169 / 0.222561 | -0.0166471 / 0.229945 | 0.0174454 / 0.201132 | -0.164418 | 0.0555556 | 0.980571 |
| `constriction_throat` | `interior` | 8 | 0.0511096 / 0.141702 | -0.0356034 / 0.135023 | 0.0158585 / 0.0774815 | 0.112704 / 0.241919 | 0.0281307 / 0.112833 | 0.408876 | 0 | 0.967675 |
| `upstream_approach` | `upper_edge` | 10 | 0.00561358 / 0.103644 | -0.0511349 / 0.23895 | 0.0102379 / 0.105336 | 0.0124392 / 0.237098 | -0.0270507 / 0.239362 | 0.0561358 | 0 | 0.957447 |
| `recovery` | `upper_edge` | 8 | 0.0982205 / 0.232384 | 0.0255628 / 0.161107 | 0.0320627 / 0.239044 | 0.0576642 / 0.124942 | -0.0869955 / 0.18549 | 0.785764 | 0 | 0.956177 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.00340341 / 0.03885 | 0.0615502 / 0.233658 | 0.0205625 / 0.0417079 | 0.071492 | 0 | 0.934631 |
| `upstream_approach` | `lower_edge` | 10 | -0.0211039 / 0.214818 | 0.00217128 / 0.139129 | -0.0196116 / 0.100765 | -0.0357549 / 0.231657 | -0.0256957 / 0.161437 | -0.211039 | 0 | 0.926627 |
| `constriction_throat` | `upper_edge` | 2 | 0.0456327 / 0.0894804 | -0.00326703 / 0.00647273 | -0.051668 / 0.103293 | 0.117307 / 0.230523 | 0.030211 / 0.065044 | 0.0912653 | 0 | 0.922091 |
| `recovery` | `lower_edge` | 6 | 0.0418054 / 0.210524 | 0.0524486 / 0.197679 | 0.0180612 / 0.151131 | 0.0607346 / 0.222097 | 0.0332325 / 0.197965 | 0.250832 | 0 | 0.888387 |
| `constriction_throat` | `lower_edge` | 4 | 0.00564182 / 0.0643546 | 0.0121396 / 0.0530374 | 0.0562206 / 0.17403 | 0.0288383 / 0.184885 | 0.0777373 / 0.212602 | 0.0225673 | 0 | 0.850409 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `downstream_constriction` | `interior` | `5,14` | 14 | -0.5 | 4.19804 | 4.44689 | 0.248846 | 0.248846 | 0.25 | 0.995385 |
| `u` | `recovery` | `interior` | `7,19` | 19 | 1.5 | 1.81784 | 1.57187 | -0.245967 | 0.245967 | 0.25 | 0.983867 |
| `h` | `upstream_approach` | `interior` | `3,5` | 5 | -2.5 | 1.86814 | 1.62226 | -0.245882 | 0.245882 | 0.25 | 0.983529 |
| `u` | `upstream_approach` | `upper_shelf` | `9,8` | 8 | 3.5 | 0.814069 | 1.05921 | 0.245143 | 0.245143 | 0.25 | 0.980571 |
| `h` | `upstream_approach` | `interior` | `4,5` | 5 | -1.5 | 1.87213 | 1.62735 | -0.244778 | 0.244778 | 0.25 | 0.979111 |
| `h` | `recovery` | `interior` | `8,20` | 20 | 2.5 | 1.40312 | 1.6475 | 0.244381 | 0.244381 | 0.25 | 0.977522 |
| `u` | `upstream_approach` | `interior` | `5,6` | 6 | -0.5 | 0.797023 | 1.04062 | 0.243594 | 0.243594 | 0.25 | 0.974375 |
| `hu` | `downstream_constriction` | `interior` | `7,14` | 14 | 1.5 | 1.22494 | 1.46813 | 0.243187 | 0.243187 | 0.25 | 0.97275 |
| `hu` | `constriction_throat` | `interior` | `5,12` | 12 | -0.5 | 4.42442 | 4.66634 | 0.241919 | 0.241919 | 0.25 | 0.967675 |
| `u` | `recovery` | `interior` | `4,16` | 16 | -1.5 | 3.09709 | 2.85533 | -0.241769 | 0.241769 | 0.25 | 0.967076 |
| `hu` | `downstream_constriction` | `interior` | `4,14` | 14 | -1.5 | 4.10354 | 4.34398 | 0.240437 | 0.240437 | 0.25 | 0.961747 |
| `h` | `recovery` | `interior` | `7,19` | 19 | 1.5 | 1.3358 | 1.57587 | 0.240077 | 0.240077 | 0.25 | 0.960308 |
| `u` | `recovery` | `interior` | `5,16` | 16 | -0.5 | 3.1046 | 2.86465 | -0.239956 | 0.239956 | 0.25 | 0.959825 |
| `hu` | `recovery` | `interior` | `4,20` | 20 | -1.5 | 3.42222 | 3.6616 | 0.239383 | 0.239383 | 0.25 | 0.957531 |
| `hv` | `upstream_approach` | `upper_edge` | `9,3` | 3 | 3.5 | -0.882652 | -1.12201 | -0.239362 | 0.239362 | 0.25 | 0.957447 |
| `hu` | `downstream_constriction` | `interior` | `6,15` | 15 | 0.5 | 3.86671 | 4.10583 | 0.23912 | 0.23912 | 0.25 | 0.956481 |

## Next Levers

- Start with `downstream_constriction/interior` cell 5,14; `hu` delta is `0.248846` with reference h `1.20314` m and C++ h `1.33955` m.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
