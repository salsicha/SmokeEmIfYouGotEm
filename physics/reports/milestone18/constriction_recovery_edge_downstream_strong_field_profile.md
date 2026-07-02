# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_edge_downstream_strong/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_edge_downstream_strong/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `2.94`
- Max h/u/v/hu/hv delta: `1.13605` / `2.70432` / `2.48597` / `2.94` / `1.73855`
- Max profile mass delta: `7.05494` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `downstream_constriction` | `upper_edge` | 2 | 0.107042 / 0.12243 | 2.08392 / 2.29347 | -0.778935 / 0.998302 | 2.68153 / 2.94 | -0.970126 / 1.24896 | 0.214084 | 0 | 11.76 |
| `recovery` | `lower_edge` | 6 | 0.0510755 / 0.230106 | 1.24461 / 2.33388 | 0.0323354 / 0.227821 | 1.61787 / 2.78469 | 0.0520396 / 0.308733 | 0.306453 | 0 | 11.1387 |
| `upstream_approach` | `lower_shelf` | 12 | -0.23302 / 0.647165 | -0.914282 / 2.70432 | -0.378191 / 2.48597 | -0.577203 / 1.29439 | -0.336035 / 1.29205 | -2.79624 | 0 | 10.8173 |
| `constriction_throat` | `upper_edge` | 2 | 0.906359 / 0.938821 | 0.249598 / 0.298576 | -0.389064 / 2.29076 | 2.53153 / 2.55954 | -1.02047 / 1.62219 | 1.81272 | 0 | 10.2382 |
| `constriction_throat` | `lower_shelf` | 4 | 0.35635 / 0.888235 | 0.11186 / 0.210905 | -0.371538 / 1.71778 | 1.01959 / 2.50383 | -0.0960421 / 0.31724 | 1.4254 | 0 | 10.0153 |
| `upstream_approach` | `upper_edge` | 10 | 0.671606 / 1.09391 | -0.746237 / 1.73262 | 0.989772 / 2.47141 | 1.14458 / 1.94807 | -0.397811 / 0.779051 | 6.71606 | 0 | 9.88563 |
| `recovery` | `interior` | 46 | -0.0154998 / 0.336461 | -0.188198 / 2.2376 | -0.181373 / 0.939903 | -0.344753 / 2.15699 | -0.224679 / 1.14715 | -0.712991 | 0 | 8.95039 |
| `recovery` | `upper_edge` | 8 | 0.779843 / 1.13605 | 1.24602 / 2.16217 | 0.367818 / 1.56229 | 1.61402 / 2.16498 | -0.226944 / 0.849248 | 6.23875 | 0 | 8.65993 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 2.11364 / 2.11364 | -1.2974 / 1.2974 | 0.469096 / 0.469096 | -0.213474 / 0.213474 | 0.0651685 | 0 | 8.45454 |
| `upstream_approach` | `interior` | 54 | -0.130647 / 0.409876 | 0.541174 / 1.20876 | -0.158467 / 0.802136 | 0.801882 / 2.10311 | -0.256603 / 1.42337 | -7.05494 | 0 | 8.41244 |
| `upstream_approach` | `upper_shelf` | 18 | -0.160996 / 0.6878 | -0.515072 / 1.89201 | 0.223697 / 2.04411 | -0.50236 / 1.562 | 0.187983 / 0.831411 | -2.89794 | 0.0555556 | 8.17645 |
| `constriction_throat` | `lower_edge` | 4 | -0.118924 / 0.330964 | 0.149416 / 0.475843 | 0.565399 / 1.24095 | -0.0490743 / 0.99075 | 0.744323 / 1.73855 | -0.475698 | 0 | 6.95418 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.185349 | 2.75466 | 2.94 | 2.94 | 0.25 | 11.76 |
| `hu` | `recovery` | `lower_edge` | `2,18` | 18 | -3.5 | -0.362344 | 2.42234 | 2.78469 | 2.78469 | 0.25 | 11.1387 |
| `u` | `upstream_approach` | `lower_shelf` | `0,1` | 1 | -5.5 | 3.63205 | 0.927726 | -2.70432 | 2.70432 | 0.25 | 10.8173 |
| `hu` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | 0.889107 | 3.44865 | 2.55954 | 2.55954 | 0.25 | 10.2382 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 3.20547 | 2.50383 | 2.50383 | 0.25 | 10.0153 |
| `hu` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 0.701957 | 3.20547 | 2.50352 | 2.50352 | 0.25 | 10.0141 |
| `v` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.45712 | 0.971151 | -2.48597 | 2.48597 | 0.25 | 9.94389 |
| `v` | `upstream_approach` | `upper_edge` | `9,1` | 1 | 3.5 | -3.72743 | -1.25603 | 2.47141 | 2.47141 | 0.25 | 9.88563 |
| `u` | `upstream_approach` | `lower_shelf` | `1,7` | 7 | -4.5 | -0.525053 | 1.91388 | 2.43893 | 2.43893 | 0.25 | 9.75574 |
| `hu` | `downstream_constriction` | `upper_edge` | `8,15` | 15 | 2.5 | -0.0924264 | 2.33062 | 2.42305 | 2.42305 | 0.25 | 9.6922 |
| `u` | `upstream_approach` | `lower_shelf` | `0,2` | 2 | -5.5 | 3.28259 | 0.929665 | -2.35292 | 2.35292 | 0.25 | 9.41169 |
| `u` | `recovery` | `lower_edge` | `2,18` | 18 | -3.5 | -0.306137 | 2.02775 | 2.33388 | 2.33388 | 0.25 | 9.33553 |
| `u` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.158696 | 2.13477 | 2.29347 | 2.29347 | 0.25 | 9.17388 |
| `v` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 1.14159 | -1.14917 | -2.29076 | 2.29076 | 0.25 | 9.16304 |
| `u` | `recovery` | `interior` | `3,17` | 17 | -2.5 | 0.179527 | 2.41712 | 2.2376 | 2.2376 | 0.25 | 8.95039 |
| `u` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.85418 | 1.65117 | -2.20301 | 2.20301 | 0.25 | 8.81204 |

## Blocked Reasons

- Final-frame `hu` field remains 11.76x over threshold at `downstream_constriction/upper_edge` cell 8,14.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `1.13605` m).
- Streamwise shear/momentum mismatch is still active in `downstream_constriction/upper_edge` (max u/hu delta `2.29347`/`2.94`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `2.48597`/`1.29205`).

## Next Levers

- Start with `downstream_constriction/upper_edge` cell 8,14; `hu` delta is `2.94` with reference h `1.16794` m and C++ h `1.29037` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
