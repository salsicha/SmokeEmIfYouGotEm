# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_split_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_split_balance/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `2.17635`
- Max h/u/v/hu/hv delta: `1.02867` / `2.08534` / `2.09945` / `2.17635` / `1.64691`
- Max profile mass delta: `7.64003` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `downstream_constriction` | `upper_edge` | 2 | 0.112648 / 0.147236 | 1.32521 / 1.67256 | -0.78693 / 1.00999 | 1.71242 / 2.17635 | -0.980852 / 1.2571 | 0.225297 | 0 | 8.70539 |
| `constriction_throat` | `upper_edge` | 2 | 0.755801 / 0.78062 | 0.148779 / 0.232725 | -0.382297 / 2.09945 | 2.01895 / 2.07083 | -0.861862 / 1.26651 | 1.5116 | 0 | 8.39779 |
| `recovery` | `interior` | 46 | -0.000277934 / 0.819861 | -0.0958325 / 2.08534 | -0.190259 / 0.975908 | -0.1603 / 1.85553 | -0.211689 / 1.12144 | -0.012785 | 0 | 8.34136 |
| `upstream_approach` | `interior` | 54 | -0.141482 / 0.400207 | 0.59091 / 1.20868 | -0.118415 / 0.803434 | 0.867229 / 2.08395 | -0.186248 / 1.41792 | -7.64003 | 0 | 8.33582 |
| `upstream_approach` | `upper_shelf` | 18 | -0.10751 / 0.678312 | -0.373813 / 2.08211 | 0.0291529 / 1.60557 | -0.403911 / 1.32542 | 0.063505 / 0.832526 | -1.93519 | 0.0555556 | 8.32842 |
| `constriction_throat` | `lower_shelf` | 4 | 0.28096 / 0.745319 | 0.103568 / 0.210905 | -0.371793 / 1.71899 | 0.809487 / 2.07022 | -0.103636 / 0.338007 | 1.12384 | 0 | 8.28088 |
| `downstream_constriction` | `interior` | 8 | 0.104134 / 0.227097 | -1.0559 / 1.6147 | -1.03441 / 1.29742 | -1.13482 / 2.04024 | -1.29585 / 1.64691 | 0.833071 | 0 | 8.16097 |
| `upstream_approach` | `upper_edge` | 10 | 0.487308 / 1.00025 | -0.535946 / 1.7294 | 0.868374 / 2.03342 | 0.996854 / 1.93272 | -0.265303 / 0.666289 | 4.87308 | 0 | 8.13366 |
| `upstream_approach` | `lower_shelf` | 12 | -0.174723 / 0.647319 | -0.451387 / 1.99584 | 0.224276 / 1.29018 | -0.363047 / 1.23318 | -0.0390812 / 0.732365 | -2.09668 | 0 | 7.98337 |
| `upstream_approach` | `lower_edge` | 10 | 0.124914 / 1.02867 | 0.153473 / 0.896974 | -0.182055 / 0.824985 | 0.631358 / 1.66188 | -0.266744 / 1.07484 | 1.24914 | 0 | 6.6475 |
| `constriction_throat` | `lower_edge` | 4 | -0.0899845 / 0.287294 | 0.0192002 / 0.525573 | 0.661055 / 1.13184 | -0.160282 / 0.939991 | 0.912361 / 1.63258 | -0.359938 | 0 | 6.53032 |
| `recovery` | `upper_edge` | 8 | 0.490596 / 0.842408 | 0.620033 / 1.58705 | 0.00218029 / 1.45956 | 0.606939 / 0.95816 | -0.445165 / 1.01425 | 3.92477 | 0 | 6.3482 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.185349 | 1.991 | 2.17635 | 2.17635 | 0.25 | 8.70539 |
| `v` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 1.14159 | -0.957854 | -2.09945 | 2.09945 | 0.25 | 8.39779 |
| `u` | `recovery` | `interior` | `3,17` | 17 | -2.5 | 0.179527 | 2.26487 | 2.08534 | 2.08534 | 0.25 | 8.34136 |
| `hu` | `upstream_approach` | `interior` | `5,2` | 2 | -0.5 | -0.0269994 | 2.05696 | 2.08395 | 2.08395 | 0.25 | 8.33582 |
| `u` | `upstream_approach` | `upper_shelf` | `10,1` | 1 | 4.5 | 3.39685 | 1.31474 | -2.08211 | 2.08211 | 0.25 | 8.32842 |
| `hu` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | 0.889107 | 2.95994 | 2.07083 | 2.07083 | 0.25 | 8.28334 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 2.77187 | 2.07022 | 2.07022 | 0.25 | 8.28088 |
| `hu` | `downstream_constriction` | `interior` | `5,15` | 15 | -0.5 | 4.05104 | 2.0108 | -2.04024 | 2.04024 | 0.25 | 8.16097 |
| `v` | `upstream_approach` | `upper_edge` | `9,1` | 1 | 3.5 | -3.72743 | -1.69402 | 2.03342 | 2.03342 | 0.25 | 8.13366 |
| `u` | `upstream_approach` | `lower_shelf` | `1,7` | 7 | -4.5 | -0.525053 | 1.47079 | 1.99584 | 1.99584 | 0.25 | 7.98337 |
| `hu` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 0.701957 | 2.66902 | 1.96706 | 1.96706 | 0.25 | 7.86823 |
| `u` | `upstream_approach` | `upper_shelf` | `10,2` | 2 | 4.5 | 3.28259 | 1.32831 | -1.95428 | 1.95428 | 0.25 | 7.8171 |
| `hu` | `upstream_approach` | `interior` | `5,3` | 3 | -0.5 | -0.00381284 | 1.94737 | 1.95119 | 1.95119 | 0.25 | 7.80474 |
| `hu` | `upstream_approach` | `upper_edge` | `8,9` | 9 | 2.5 | 0.304252 | 2.23698 | 1.93272 | 1.93272 | 0.25 | 7.7309 |
| `hu` | `upstream_approach` | `interior` | `4,2` | 2 | -1.5 | 0.544031 | 2.46537 | 1.92134 | 1.92134 | 0.25 | 7.68534 |
| `hu` | `upstream_approach` | `interior` | `5,1` | 1 | -0.5 | 0.0262427 | 1.93608 | 1.90983 | 1.90983 | 0.25 | 7.63933 |

## Blocked Reasons

- Final-frame `hu` field remains 8.71x over threshold at `downstream_constriction/upper_edge` cell 8,14.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `1.02867` m).
- Streamwise shear/momentum mismatch is still active in `downstream_constriction/upper_edge` (max u/hu delta `1.67256`/`2.17635`).
- Cross-stream shear/momentum mismatch is still active in `constriction_throat/upper_edge` (max v/hv delta `2.09945`/`1.26651`).

## Next Levers

- Start with `downstream_constriction/upper_edge` cell 8,14; `hu` delta is `2.17635` with reference h `1.16794` m and C++ h `1.31518` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
