# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upper_edge_immediate_shelf_release/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upper_edge_immediate_shelf_release/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `2.24265`
- Max h/u/v/hu/hv delta: `1.11472` / `2.24265` / `2.09945` / `2.19148` / `1.64778`
- Max profile mass delta: `7.63998` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `recovery` | `interior` | 46 | -0.0405905 / 0.369709 | -0.186279 / 2.24265 | -0.178879 / 0.913924 | -0.39394 / 2.19148 | -0.22271 / 1.11017 | -1.86716 | 0 | 8.9706 |
| `downstream_constriction` | `upper_edge` | 2 | 0.11287 / 0.147244 | 1.32491 / 1.67253 | -0.787197 / 1.01052 | 1.71225 / 2.17632 | -0.981308 / 1.25801 | 0.22574 | 0 | 8.70529 |
| `recovery` | `upper_edge` | 8 | 0.724008 / 1.11472 | 1.24864 / 2.16729 | 0.373068 / 1.56232 | 1.50296 / 1.92139 | -0.215076 / 0.79718 | 5.79207 | 0 | 8.66916 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 2.13443 / 2.13443 | -1.26926 / 1.26926 | 0.47367 / 0.47367 | -0.207283 / 0.207283 | 0.0651685 | 0 | 8.5377 |
| `constriction_throat` | `upper_edge` | 2 | 0.755802 / 0.780621 | 0.148778 / 0.232725 | -0.382297 / 2.09945 | 2.01895 / 2.07083 | -0.861862 / 1.26651 | 1.5116 | 0 | 8.39779 |
| `upstream_approach` | `interior` | 54 | -0.141481 / 0.400208 | 0.59091 / 1.20868 | -0.118415 / 0.803433 | 0.867231 / 2.08396 | -0.186248 / 1.41792 | -7.63998 | 0 | 8.33583 |
| `upstream_approach` | `upper_shelf` | 18 | -0.10751 / 0.678312 | -0.373812 / 2.08211 | 0.0291529 / 1.60557 | -0.403911 / 1.32542 | 0.063505 / 0.832526 | -1.93519 | 0.0555556 | 8.32842 |
| `constriction_throat` | `lower_shelf` | 4 | 0.280961 / 0.74532 | 0.103568 / 0.210905 | -0.371793 / 1.719 | 0.809488 / 2.07022 | -0.103636 / 0.338007 | 1.12384 | 0 | 8.28089 |
| `downstream_constriction` | `interior` | 8 | 0.104353 / 0.227106 | -1.0562 / 1.61526 | -1.03468 / 1.29792 | -1.13488 / 2.04034 | -1.29629 / 1.64778 | 0.834824 | 0 | 8.16137 |
| `upstream_approach` | `upper_edge` | 10 | 0.487308 / 1.00025 | -0.535946 / 1.7294 | 0.868374 / 2.03342 | 0.996855 / 1.93273 | -0.265303 / 0.666288 | 4.87308 | 0 | 8.13366 |
| `upstream_approach` | `lower_shelf` | 12 | -0.174723 / 0.647319 | -0.451387 / 1.99584 | 0.224276 / 1.29018 | -0.363047 / 1.23318 | -0.0390811 / 0.732365 | -2.09668 | 0 | 7.98337 |
| `recovery` | `lower_edge` | 6 | 0.0332887 / 0.210056 | 0.501542 / 1.52858 | 0.033675 / 0.228085 | 0.612735 / 1.77352 | 0.0525281 / 0.308865 | 0.199732 | 0 | 7.09409 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `u` | `recovery` | `interior` | `3,17` | 17 | -2.5 | 0.179527 | 2.42218 | 2.24265 | 2.24265 | 0.25 | 8.9706 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 1.64303 | -2.19148 | 2.19148 | 0.25 | 8.76591 |
| `hu` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.185349 | 1.99097 | 2.17632 | 2.17632 | 0.25 | 8.70529 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 2.05192 | 2.16729 | 2.16729 | 0.25 | 8.66916 |
| `u` | `recovery` | `upper_edge` | `9,17` | 17 | 3.5 | 0.234362 | 2.4001 | 2.16574 | 2.16574 | 0.25 | 8.66295 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 2.19728 | 2.13443 | 2.13443 | 0.25 | 8.5377 |
| `v` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 1.14159 | -0.957854 | -2.09945 | 2.09945 | 0.25 | 8.39779 |
| `hu` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 3.75007 | 1.6571 | -2.09297 | 2.09297 | 0.25 | 8.37188 |
| `hu` | `upstream_approach` | `interior` | `5,2` | 2 | -0.5 | -0.0269994 | 2.05696 | 2.08396 | 2.08396 | 0.25 | 8.33583 |
| `u` | `upstream_approach` | `upper_shelf` | `10,1` | 1 | 4.5 | 3.39685 | 1.31474 | -2.08211 | 2.08211 | 0.25 | 8.32842 |
| `hu` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | 0.889107 | 2.95994 | 2.07083 | 2.07083 | 0.25 | 8.28334 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 2.77187 | 2.07022 | 2.07022 | 0.25 | 8.28089 |
| `u` | `recovery` | `interior` | `8,17` | 17 | 2.5 | 0.350557 | 2.40895 | 2.05839 | 2.05839 | 0.25 | 8.23357 |
| `hu` | `recovery` | `interior` | `5,20` | 20 | -0.5 | 3.83038 | 1.78339 | -2.04699 | 2.04699 | 0.25 | 8.18796 |
| `u` | `recovery` | `upper_edge` | `8,16` | 16 | 2.5 | 0.137262 | 2.17993 | 2.04267 | 2.04267 | 0.25 | 8.17066 |
| `hu` | `downstream_constriction` | `interior` | `5,15` | 15 | -0.5 | 4.05104 | 2.0107 | -2.04034 | 2.04034 | 0.25 | 8.16137 |

## Blocked Reasons

- Final-frame `u` field remains 8.97x over threshold at `recovery/interior` cell 3,17.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `1.11472` m).
- Streamwise shear/momentum mismatch is still active in `recovery/interior` (max u/hu delta `2.24265`/`2.19148`).
- Cross-stream shear/momentum mismatch is still active in `constriction_throat/upper_edge` (max v/hv delta `2.09945`/`1.26651`).

## Next Levers

- Start with `recovery/interior` cell 3,17; `u` delta is `2.24265` with reference h `0.578351` m and C++ h `0.86429` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
