# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_approach_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_approach_final_profile/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `2.07083`
- Max h/u/v/hu/hv delta: `1.02867` / `2.02572` / `1.65063` / `2.07083` / `1.64691`
- Max profile mass delta: `7.64003` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `constriction_throat` | `upper_edge` | 2 | 0.681727 / 0.78062 | 0.113126 / 0.232725 | 0.432518 / 1.33485 | 1.79099 / 2.07083 | -0.0962095 / 0.457218 | 1.36345 | 0 | 8.28334 |
| `downstream_constriction` | `interior` | 8 | 0.104134 / 0.227097 | -1.0559 / 1.6147 | -1.03441 / 1.29742 | -1.13482 / 2.04024 | -1.29585 / 1.64691 | 0.833071 | 0 | 8.16097 |
| `upstream_approach` | `lower_shelf` | 12 | -0.150534 / 0.645357 | -0.0677167 / 2.02572 | 0.550282 / 1.65063 | -0.140437 / 0.966763 | 0.147483 / 0.948117 | -1.8064 | 0 | 8.10287 |
| `downstream_constriction` | `upper_edge` | 2 | 0.112648 / 0.147236 | 1.14231 / 1.52014 | -0.78693 / 1.00999 | 1.47532 / 1.97589 | -0.980852 / 1.2571 | 0.225297 | 0 | 7.90357 |
| `upstream_approach` | `upper_edge` | 10 | 0.434829 / 0.907319 | -0.135915 / 1.2787 | 0.468344 / 1.30914 | 1.28731 / 1.93272 | -0.595438 / 1.26209 | 4.34829 | 0 | 7.7309 |
| `recovery` | `interior` | 46 | 0.00259463 / 0.529751 | -0.174623 / 1.71528 | -0.156796 / 0.814571 | -0.206596 / 1.74749 | -0.191411 / 1.01091 | 0.119353 | 0 | 6.98997 |
| `upstream_approach` | `lower_edge` | 10 | 0.124914 / 1.02867 | 0.153473 / 0.896974 | -0.182055 / 0.824985 | 0.631358 / 1.66188 | -0.266744 / 1.07484 | 1.24914 | 0 | 6.6475 |
| `constriction_throat` | `lower_edge` | 4 | -0.0899845 / 0.287294 | 0.0192002 / 0.525573 | 0.661055 / 1.13184 | -0.160282 / 0.939991 | 0.912361 / 1.63258 | -0.359938 | 0 | 6.53032 |
| `constriction_throat` | `lower_shelf` | 4 | 0.243923 / 0.597171 | 0.0888894 / 0.210905 | 0.035614 / 0.525518 | 0.694385 / 1.60981 | 0.238693 / 1.03131 | 0.975694 | 0 | 6.43926 |
| `upstream_approach` | `upper_shelf` | 18 | -0.100857 / 0.678312 | -0.102442 / 1.35552 | -0.0686085 / 1.60557 | -0.291342 / 1.32542 | 0.0407426 / 0.822331 | -1.81543 | 0.0555556 | 6.42228 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 1.57644 / 1.57644 | -0.61311 / 0.61311 | 0.350913 / 0.350913 | -0.0629306 / 0.0629306 | 0.0651685 | 0 | 6.30576 |
| `recovery` | `upper_edge` | 8 | 0.511116 / 0.842408 | 0.377732 / 1.50397 | 0.216507 / 1.28418 | 0.520422 / 0.95816 | -0.352354 / 0.919559 | 4.08893 | 0 | 6.01589 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | 0.889107 | 2.95994 | 2.07083 | 2.07083 | 0.25 | 8.28334 |
| `hu` | `downstream_constriction` | `interior` | `5,15` | 15 | -0.5 | 4.05104 | 2.0108 | -2.04024 | 2.04024 | 0.25 | 8.16097 |
| `u` | `upstream_approach` | `lower_shelf` | `1,7` | 7 | -4.5 | -0.525053 | 1.50066 | 2.02572 | 2.02572 | 0.25 | 8.10287 |
| `hu` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.185349 | 1.79054 | 1.97589 | 1.97589 | 0.25 | 7.90357 |
| `hu` | `upstream_approach` | `upper_edge` | `8,9` | 9 | 2.5 | 0.304252 | 2.23698 | 1.93272 | 1.93272 | 0.25 | 7.7309 |
| `hu` | `downstream_constriction` | `interior` | `4,15` | 15 | -1.5 | 3.86465 | 1.96887 | -1.89578 | 1.89578 | 0.25 | 7.58312 |
| `hu` | `downstream_constriction` | `interior` | `6,15` | 15 | 0.5 | 3.86671 | 1.98561 | -1.8811 | 1.8811 | 0.25 | 7.52439 |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 2.09653 | 1.74749 | 1.74749 | 0.25 | 6.98997 |
| `u` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.12161 | 1.40633 | -1.71528 | 1.71528 | 0.25 | 6.86113 |
| `hu` | `upstream_approach` | `upper_edge` | `9,3` | 3 | 3.5 | 1.30954 | 2.99463 | 1.68509 | 1.68509 | 0.25 | 6.74037 |
| `hu` | `upstream_approach` | `lower_edge` | `3,7` | 7 | -2.5 | 1.40305 | 3.06493 | 1.66188 | 1.66188 | 0.25 | 6.6475 |
| `v` | `upstream_approach` | `lower_shelf` | `1,4` | 4 | -4.5 | 0.513472 | 2.1641 | 1.65063 | 1.65063 | 0.25 | 6.60252 |
| `hv` | `downstream_constriction` | `interior` | `6,15` | 15 | 0.5 | 1.04389 | -0.603018 | -1.64691 | 1.64691 | 0.25 | 6.58762 |
| `hv` | `constriction_throat` | `lower_edge` | `4,10` | 10 | -1.5 | -0.292386 | 1.34019 | 1.63258 | 1.63258 | 0.25 | 6.53032 |
| `hv` | `downstream_constriction` | `interior` | `7,15` | 15 | 1.5 | 0.960992 | -0.663561 | -1.62455 | 1.62455 | 0.25 | 6.49821 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 2.21748 | -1.61702 | 1.61702 | 0.25 | 6.4681 |

## Blocked Reasons

- Final-frame `hu` field remains 8.28x over threshold at `constriction_throat/upper_edge` cell 7,10.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `1.02867` m).
- Streamwise shear/momentum mismatch is still active in `constriction_throat/upper_edge` (max u/hu delta `0.232725`/`2.07083`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `1.65063`/`0.948117`).

## Next Levers

- Start with `constriction_throat/upper_edge` cell 7,10; `hu` delta is `2.07083` with reference h `0.385715` m and C++ h `1.16634` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
