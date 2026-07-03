# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_inner_upper_shelf_streamwise_balance_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_inner_upper_shelf_streamwise_balance_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.250292`
- Max h/u/v/hu/hv delta: `0.248559` / `0.245967` / `0.239044` / `0.250292` / `0.250269`
- Max profile mass delta: `3.3627` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `recovery` | `interior` | 46 | 0.0731021 / 0.248273 | -0.0541368 / 0.245967 | -0.00960214 / 0.189581 | 0.0635366 / 0.250292 | -0.0066713 / 0.226973 | 3.3627 | 0 | 1.00117 |
| `upstream_approach` | `interior` | 54 | -0.0472677 / 0.248559 | 0.0179621 / 0.243594 | -0.00277454 / 0.133059 | 0.0121401 / 0.229556 | -0.0118918 / 0.250269 | -2.55245 | 0 | 1.00108 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.0728258 / 0.218799 | -0.0393133 / 0.202843 | 0.146906 / 0.248846 | 0.0169657 / 0.212547 | 0.809547 | 0 | 0.995385 |
| `upstream_approach` | `upper_shelf` | 18 | -0.00913431 / 0.0899976 | -0.0137235 / 0.245204 | 0.0247186 / 0.222589 | -0.0166449 / 0.229945 | 0.0174464 / 0.20115 | -0.164418 | 0.0555556 | 0.980816 |
| `constriction_throat` | `interior` | 8 | 0.0511096 / 0.141702 | -0.0356034 / 0.135023 | 0.0158585 / 0.0774815 | 0.112704 / 0.241919 | 0.0281307 / 0.112833 | 0.408876 | 0 | 0.967675 |
| `upstream_approach` | `upper_edge` | 10 | 0.00561358 / 0.103644 | -0.0511349 / 0.23895 | 0.0102379 / 0.105336 | 0.0124392 / 0.237098 | -0.0270507 / 0.239362 | 0.0561358 | 0 | 0.957447 |
| `recovery` | `upper_edge` | 8 | 0.0982205 / 0.232384 | 0.0255628 / 0.161107 | 0.0320627 / 0.239044 | 0.0576642 / 0.124942 | -0.0869955 / 0.18549 | 0.785764 | 0 | 0.956177 |
| `upstream_approach` | `lower_edge` | 10 | -0.0448425 / 0.237778 | 0.00258903 / 0.139129 | -0.020451 / 0.100765 | -0.0521183 / 0.231657 | -0.0382934 / 0.236702 | -0.448425 | 0 | 0.951111 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.00340341 / 0.03885 | 0.0615502 / 0.233658 | 0.0205625 / 0.0417079 | 0.071492 | 0 | 0.934631 |
| `constriction_throat` | `upper_edge` | 2 | 0.0456327 / 0.0894804 | -0.00326703 / 0.00647273 | -0.051668 / 0.103293 | 0.117307 / 0.230523 | 0.030211 / 0.065044 | 0.0912653 | 0 | 0.922091 |
| `upstream_approach` | `lower_shelf` | 12 | -0.0236296 / 0.0895693 | 0.00201027 / 0.0605504 | -0.0204984 / 0.153865 | -0.0327912 / 0.138735 | -0.0357168 / 0.223915 | -0.283556 | 0 | 0.895661 |
| `recovery` | `lower_edge` | 6 | 0.0418054 / 0.210524 | 0.0524486 / 0.197679 | 0.0180612 / 0.151131 | 0.0607346 / 0.222097 | 0.0332325 / 0.197965 | 0.250832 | 0 | 0.888387 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `recovery` | `interior` | `6,18` | 18 | 0.5 | 3.72586 | 3.97615 | 0.250292 | 0.250292 | 0.25 | 1.00117 |
| `hv` | `upstream_approach` | `interior` | `8,5` | 5 | 2.5 | -0.607975 | -0.858244 | -0.250269 | 0.250269 | 0.25 | 1.00108 |
| `hu` | `downstream_constriction` | `interior` | `5,14` | 14 | -0.5 | 4.19804 | 4.44689 | 0.248846 | 0.248846 | 0.25 | 0.995385 |
| `h` | `upstream_approach` | `interior` | `4,6` | 6 | -1.5 | 1.86864 | 1.62008 | -0.248559 | 0.248559 | 0.25 | 0.994238 |
| `h` | `recovery` | `interior` | `8,21` | 21 | 2.5 | 1.42473 | 1.673 | 0.248273 | 0.248273 | 0.25 | 0.99309 |
| `u` | `recovery` | `interior` | `7,19` | 19 | 1.5 | 1.81784 | 1.57187 | -0.245967 | 0.245967 | 0.25 | 0.983867 |
| `h` | `upstream_approach` | `interior` | `3,5` | 5 | -2.5 | 1.86814 | 1.62226 | -0.245882 | 0.245882 | 0.25 | 0.983529 |
| `u` | `upstream_approach` | `upper_shelf` | `9,8` | 8 | 3.5 | 0.814069 | 1.05927 | 0.245204 | 0.245204 | 0.25 | 0.980816 |
| `h` | `recovery` | `interior` | `8,22` | 22 | 2.5 | 1.44468 | 1.68962 | 0.244941 | 0.244941 | 0.25 | 0.979762 |
| `h` | `upstream_approach` | `interior` | `4,5` | 5 | -1.5 | 1.87213 | 1.62735 | -0.244778 | 0.244778 | 0.25 | 0.979111 |
| `h` | `recovery` | `interior` | `8,20` | 20 | 2.5 | 1.40312 | 1.6475 | 0.244381 | 0.244381 | 0.25 | 0.977522 |
| `u` | `upstream_approach` | `interior` | `5,6` | 6 | -0.5 | 0.797023 | 1.04062 | 0.243594 | 0.243594 | 0.25 | 0.974375 |
| `hu` | `downstream_constriction` | `interior` | `7,14` | 14 | 1.5 | 1.22494 | 1.46813 | 0.243187 | 0.243187 | 0.25 | 0.97275 |
| `hu` | `constriction_throat` | `interior` | `5,12` | 12 | -0.5 | 4.42442 | 4.66634 | 0.241919 | 0.241919 | 0.25 | 0.967675 |
| `u` | `recovery` | `interior` | `4,16` | 16 | -1.5 | 3.09709 | 2.85533 | -0.241769 | 0.241769 | 0.25 | 0.967076 |
| `hu` | `downstream_constriction` | `interior` | `4,14` | 14 | -1.5 | 4.10354 | 4.34398 | 0.240437 | 0.240437 | 0.25 | 0.961747 |

## Blocked Reasons

- Final-frame `hu` field remains 1.00x over threshold at `recovery/interior` cell 6,18.
- Streamwise shear/momentum mismatch is still active in `recovery/interior` (max u/hu delta `0.245967`/`0.250292`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/interior` (max v/hv delta `0.133059`/`0.250269`).

## Next Levers

- Start with `recovery/interior` cell 6,18; `hu` delta is `0.250292` with reference h `1.2504` m and C++ h `1.37449` m.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
