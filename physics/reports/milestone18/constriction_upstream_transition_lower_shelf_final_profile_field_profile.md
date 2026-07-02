# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_transition_lower_shelf_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_transition_lower_shelf_final_profile/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.97589`
- Max h/u/v/hu/hv delta: `1.01572` / `1.71529` / `1.65063` / `1.97589` / `1.62456`
- Max profile mass delta: `7.64657` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `downstream_constriction` | `upper_edge` | 2 | 0.112647 / 0.147235 | 1.14231 / 1.52014 | -0.78693 / 1.00999 | 1.47532 / 1.97589 | -0.980852 / 1.2571 | 0.225294 | 0 | 7.90356 |
| `upstream_approach` | `upper_edge` | 10 | 0.433689 / 0.907337 | -0.230264 / 1.27874 | 0.511824 / 1.30914 | 1.12633 / 1.93187 | -0.520438 / 1.26209 | 4.33689 | 0 | 7.72746 |
| `recovery` | `interior` | 46 | 0.00260669 / 0.529751 | -0.174624 / 1.71529 | -0.156797 / 0.814578 | -0.206579 / 1.7475 | -0.191412 / 1.01092 | 0.119908 | 0 | 6.99002 |
| `upstream_approach` | `lower_shelf` | 12 | -0.125056 / 0.568641 | -0.312639 / 1.28747 | 0.468852 / 1.65063 | -0.182998 / 0.966763 | 0.136047 / 0.948116 | -1.50068 | 0 | 6.60252 |
| `downstream_constriction` | `interior` | 8 | 0.104136 / 0.227099 | -0.678675 / 1.1116 | -0.657184 / 1.29742 | -0.637268 / 1.26896 | -0.798296 / 1.62456 | 0.833086 | 0 | 6.49823 |
| `constriction_throat` | `lower_shelf` | 4 | 0.243923 / 0.597171 | 0.0888893 / 0.210905 | 0.0356139 / 0.525518 | 0.694385 / 1.60981 | 0.238693 / 1.03131 | 0.975694 | 0 | 6.43926 |
| `upstream_approach` | `upper_shelf` | 18 | -0.100853 / 0.678312 | -0.130583 / 1.35552 | -0.0597176 / 1.60557 | -0.297355 / 1.32542 | 0.0426103 / 0.85547 | -1.81535 | 0.0555556 | 6.42229 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 1.57644 / 1.57644 | -0.61311 / 0.61311 | 0.350913 / 0.350913 | -0.0629307 / 0.0629307 | 0.0651685 | 0 | 6.30576 |
| `constriction_throat` | `upper_edge` | 2 | 0.533579 / 0.582834 | -0.00211336 / 0.00647273 | 0.435062 / 1.33994 | 1.31476 / 1.51115 | 0.0904897 / 0.264799 | 1.06716 | 0 | 6.04458 |
| `recovery` | `upper_edge` | 8 | 0.511122 / 0.842437 | 0.377732 / 1.50397 | 0.216507 / 1.28418 | 0.520426 / 0.958173 | -0.352358 / 0.919561 | 4.08897 | 0 | 6.01589 |
| `upstream_approach` | `interior` | 54 | -0.141603 / 0.400045 | 0.146149 / 0.651431 | -0.116106 / 0.803452 | 0.134971 / 1.27886 | -0.181912 / 1.41793 | -7.64657 | 0 | 5.6717 |
| `upstream_approach` | `lower_edge` | 10 | 0.096123 / 1.01572 | 0.081528 / 0.889785 | -0.125011 / 0.822947 | 0.473179 / 1.30339 | -0.175035 / 1.06483 | 0.96123 | 0 | 5.21356 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.185349 | 1.79054 | 1.97589 | 1.97589 | 0.25 | 7.90356 |
| `hu` | `upstream_approach` | `upper_edge` | `8,9` | 9 | 2.5 | 0.304252 | 2.23612 | 1.93187 | 1.93187 | 0.25 | 7.72746 |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 2.09654 | 1.7475 | 1.7475 | 0.25 | 6.99002 |
| `u` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.12161 | 1.40632 | -1.71529 | 1.71529 | 0.25 | 6.86117 |
| `hu` | `upstream_approach` | `upper_edge` | `9,3` | 3 | 3.5 | 1.30954 | 2.99463 | 1.68509 | 1.68509 | 0.25 | 6.74036 |
| `v` | `upstream_approach` | `lower_shelf` | `1,4` | 4 | -4.5 | 0.513472 | 2.1641 | 1.65063 | 1.65063 | 0.25 | 6.60252 |
| `hv` | `downstream_constriction` | `interior` | `7,15` | 15 | 1.5 | 0.960992 | -0.663566 | -1.62456 | 1.62456 | 0.25 | 6.49823 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 2.21755 | -1.61695 | 1.61695 | 0.25 | 6.46782 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 2.31146 | 1.60981 | 1.60981 | 0.25 | 6.43926 |
| `v` | `upstream_approach` | `upper_shelf` | `11,0` | 0 | 5.5 | -0.228902 | -1.83447 | -1.60557 | 1.60557 | 0.25 | 6.42229 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 1.6393 | 1.57644 | 1.57644 | 0.25 | 6.30576 |
| `u` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.158696 | 1.36144 | 1.52014 | 1.52014 | 0.25 | 6.08056 |
| `hu` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 3.75007 | 2.23162 | -1.51845 | 1.51845 | 0.25 | 6.0738 |
| `hu` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 0.701957 | 2.2131 | 1.51115 | 1.51115 | 0.25 | 6.04458 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 1.3886 | 1.50397 | 1.50397 | 0.25 | 6.01589 |
| `u` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.310052 | 1.81239 | 1.50234 | 1.50234 | 0.25 | 6.00934 |

## Blocked Reasons

- Final-frame `hu` field remains 7.90x over threshold at `downstream_constriction/upper_edge` cell 8,14.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `1.01572` m).
- Streamwise shear/momentum mismatch is still active in `downstream_constriction/upper_edge` (max u/hu delta `1.52014`/`1.97589`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `1.65063`/`0.948116`).

## Next Levers

- Start with `downstream_constriction/upper_edge` cell 8,14; `hu` delta is `1.97589` with reference h `1.16794` m and C++ h `1.31518` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
