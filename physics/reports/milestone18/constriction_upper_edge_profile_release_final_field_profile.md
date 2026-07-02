# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upper_edge_profile_release_final/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upper_edge_profile_release_final/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `2.5603`
- Max h/u/v/hu/hv delta: `1.13532` / `2.43911` / `2.47477` / `2.5603` / `1.73888`
- Max profile mass delta: `7.00442` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `constriction_throat` | `upper_edge` | 2 | 0.921375 / 0.939113 | 0.214589 / 0.298576 | -0.37471 / 2.26205 | 2.53251 / 2.5603 | -1.02087 / 1.62268 | 1.84275 | 0 | 10.2412 |
| `downstream_constriction` | `upper_edge` | 2 | 0.130179 / 0.163937 | 1.64057 / 1.93427 | -0.78832 / 1.01179 | 2.14771 / 2.5502 | -0.990018 / 1.26892 | 0.260358 | 0 | 10.2008 |
| `constriction_throat` | `lower_shelf` | 4 | 0.363976 / 0.917975 | 0.094359 / 0.210905 | -0.372092 / 1.71999 | 1.0204 / 2.50502 | -0.0955262 / 0.315762 | 1.4559 | 0 | 10.0201 |
| `upstream_approach` | `upper_edge` | 10 | 0.663268 / 1.06533 | -0.710007 / 1.73357 | 1.00537 / 2.47477 | 1.1792 / 1.94862 | -0.366087 / 0.74074 | 6.63268 | 0 | 9.89907 |
| `upstream_approach` | `lower_shelf` | 12 | -0.233019 / 0.647161 | -0.717375 / 2.43911 | -0.16729 / 2.10088 | -0.525293 / 1.23331 | -0.279536 / 1.17672 | -2.79622 | 0 | 9.75644 |
| `recovery` | `interior` | 46 | -0.0205006 / 0.334135 | -0.187923 / 2.2316 | -0.179781 / 0.915519 | -0.356224 / 2.15913 | -0.223266 / 1.11438 | -0.943029 | 0 | 8.9264 |
| `recovery` | `upper_edge` | 8 | 0.755565 / 1.13532 | 1.24604 / 2.15576 | 0.371307 / 1.5623 | 1.5613 / 2.14025 | -0.220808 / 0.802891 | 6.04452 | 0 | 8.62302 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 2.12425 / 2.12425 | -1.27063 / 1.27063 | 0.471432 / 0.471432 | -0.207585 / 0.207585 | 0.0651685 | 0 | 8.49701 |
| `upstream_approach` | `interior` | 54 | -0.129712 / 0.410248 | 0.553461 / 1.21435 | -0.120087 / 0.802149 | 0.823319 / 2.11416 | -0.19372 / 1.40328 | -7.00442 | 0 | 8.45663 |
| `downstream_constriction` | `interior` | 8 | 0.121687 / 0.243299 | -1.06069 / 1.61933 | -1.03582 / 1.29872 | -1.11193 / 2.01873 | -1.304 / 1.6578 | 0.973497 | 0 | 8.07493 |
| `upstream_approach` | `upper_shelf` | 18 | -0.157248 / 0.671231 | -0.418791 / 1.70248 | 0.227186 / 1.83086 | -0.473521 / 1.4494 | 0.184732 / 0.831398 | -2.83047 | 0.0555556 | 7.32346 |
| `recovery` | `lower_edge` | 6 | 0.0505663 / 0.229417 | 0.501058 / 1.51034 | 0.0324381 / 0.227828 | 0.625205 / 1.79672 | 0.0520897 / 0.30875 | 0.303398 | 0 | 7.18689 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | 0.889107 | 3.44941 | 2.5603 | 2.5603 | 0.25 | 10.2412 |
| `hu` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.185349 | 2.36485 | 2.5502 | 2.5502 | 0.25 | 10.2008 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 3.20667 | 2.50502 | 2.50502 | 0.25 | 10.0201 |
| `hu` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 0.701957 | 3.20667 | 2.50471 | 2.50471 | 0.25 | 10.0189 |
| `v` | `upstream_approach` | `upper_edge` | `9,1` | 1 | 3.5 | -3.72743 | -1.25267 | 2.47477 | 2.47477 | 0.25 | 9.89907 |
| `u` | `upstream_approach` | `lower_shelf` | `1,7` | 7 | -4.5 | -0.525053 | 1.91406 | 2.43911 | 2.43911 | 0.25 | 9.75644 |
| `u` | `upstream_approach` | `lower_shelf` | `0,1` | 1 | -5.5 | 3.63205 | 1.27269 | -2.35936 | 2.35936 | 0.25 | 9.43742 |
| `v` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 1.14159 | -1.12046 | -2.26205 | 2.26205 | 0.25 | 9.04821 |
| `u` | `recovery` | `interior` | `3,17` | 17 | -2.5 | 0.179527 | 2.41113 | 2.2316 | 2.2316 | 0.25 | 8.9264 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 1.67538 | -2.15913 | 2.15913 | 0.25 | 8.63651 |
| `u` | `recovery` | `upper_edge` | `9,17` | 17 | 3.5 | 0.234362 | 2.39012 | 2.15576 | 2.15576 | 0.25 | 8.62302 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 2.033 | 2.14837 | 2.14837 | 0.25 | 8.59349 |
| `hu` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.0251073 | 2.11514 | 2.14025 | 2.14025 | 0.25 | 8.56098 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 2.18711 | 2.12425 | 2.12425 | 0.25 | 8.49701 |
| `hu` | `upstream_approach` | `interior` | `5,2` | 2 | -0.5 | -0.0269994 | 2.08716 | 2.11416 | 2.11416 | 0.25 | 8.45663 |
| `v` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.45712 | 1.35624 | -2.10088 | 2.10088 | 0.25 | 8.40353 |

## Blocked Reasons

- Final-frame `hu` field remains 10.24x over threshold at `constriction_throat/upper_edge` cell 7,10.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `1.13532` m).
- Streamwise shear/momentum mismatch is still active in `constriction_throat/upper_edge` (max u/hu delta `0.298576`/`2.5603`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/upper_edge` (max v/hv delta `2.47477`/`0.74074`).

## Next Levers

- Start with `constriction_throat/upper_edge` cell 7,10; `hu` delta is `2.5603` with reference h `0.385715` m and C++ h `1.32483` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
