# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_pre_throat_shelf_release/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_pre_throat_shelf_release/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `2.38356`
- Max h/u/v/hu/hv delta: `1.13532` / `2.35936` / `2.10088` / `2.38356` / `1.6578`
- Max profile mass delta: `7.00442` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `constriction_throat` | `lower_shelf` | 4 | 0.341753 / 0.87353 | 0.094359 / 0.210905 | -0.372092 / 1.71999 | 0.961563 / 2.38356 | -0.0976747 / 0.321744 | 1.36701 | 0 | 9.53426 |
| `constriction_throat` | `upper_edge` | 2 | 0.876931 / 0.894669 | 0.134387 / 0.232725 | -0.37471 / 2.08427 | 2.31839 / 2.36027 | -0.985712 / 1.37218 | 1.75386 | 0 | 9.44107 |
| `upstream_approach` | `lower_shelf` | 12 | -0.233019 / 0.647161 | -0.796584 / 2.35936 | -0.21254 / 2.10088 | -0.542588 / 1.23331 | -0.287412 / 1.17672 | -2.79622 | 0 | 9.43742 |
| `upstream_approach` | `upper_edge` | 10 | 0.663268 / 1.06533 | -0.541118 / 1.73357 | 0.836485 / 1.9118 | 1.40732 / 2.31723 | -0.594213 / 1.525 | 6.63268 | 0 | 9.26891 |
| `recovery` | `interior` | 46 | -0.0205006 / 0.334135 | -0.187923 / 2.2316 | -0.179781 / 0.915519 | -0.356224 / 2.15913 | -0.223266 / 1.11438 | -0.943029 | 0 | 8.9264 |
| `downstream_constriction` | `upper_edge` | 2 | 0.130179 / 0.163937 | 1.3205 / 1.66754 | -0.78832 / 1.01179 | 1.72713 / 2.19495 | -0.990018 / 1.26892 | 0.260358 | 0 | 8.77981 |
| `recovery` | `upper_edge` | 8 | 0.755565 / 1.13532 | 1.24604 / 2.15576 | 0.371307 / 1.5623 | 1.5613 / 2.14025 | -0.220808 / 0.802891 | 6.04452 | 0 | 8.62302 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 2.12425 / 2.12425 | -1.27063 / 1.27063 | 0.471432 / 0.471432 | -0.207585 / 0.207585 | 0.0651685 | 0 | 8.49701 |
| `upstream_approach` | `interior` | 54 | -0.129712 / 0.410248 | 0.584737 / 1.21435 | -0.145942 / 0.821554 | 0.874306 / 2.11416 | -0.235802 / 1.40328 | -7.00442 | 0 | 8.45663 |
| `downstream_constriction` | `interior` | 8 | 0.121687 / 0.243299 | -1.06069 / 1.61933 | -1.03582 / 1.29872 | -1.11193 / 2.01873 | -1.304 / 1.6578 | 0.973497 | 0 | 8.07493 |
| `recovery` | `lower_edge` | 6 | 0.0505663 / 0.229417 | 0.501058 / 1.51034 | 0.0324381 / 0.227828 | 0.625205 / 1.79672 | 0.0520897 / 0.30875 | 0.303398 | 0 | 7.18689 |
| `upstream_approach` | `upper_shelf` | 18 | -0.157248 / 0.671231 | -0.220098 / 1.70248 | 0.14029 / 1.42167 | -0.433384 / 1.34031 | 0.165677 / 0.831398 | -2.83047 | 0.0555556 | 6.80992 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 3.08521 | 2.38356 | 2.38356 | 0.25 | 9.53426 |
| `hu` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | 0.889107 | 3.24937 | 2.36027 | 2.36027 | 0.25 | 9.44107 |
| `u` | `upstream_approach` | `lower_shelf` | `0,1` | 1 | -5.5 | 3.63205 | 1.27269 | -2.35936 | 2.35936 | 0.25 | 9.43742 |
| `hu` | `upstream_approach` | `upper_edge` | `9,2` | 2 | 3.5 | 1.14879 | 3.46601 | 2.31723 | 2.31723 | 0.25 | 9.26891 |
| `hu` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 0.701957 | 2.97847 | 2.27651 | 2.27651 | 0.25 | 9.10604 |
| `u` | `recovery` | `interior` | `3,17` | 17 | -2.5 | 0.179527 | 2.41113 | 2.2316 | 2.2316 | 0.25 | 8.9264 |
| `hu` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.185349 | 2.0096 | 2.19495 | 2.19495 | 0.25 | 8.77981 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 1.67538 | -2.15913 | 2.15913 | 0.25 | 8.63651 |
| `u` | `recovery` | `upper_edge` | `9,17` | 17 | 3.5 | 0.234362 | 2.39012 | 2.15576 | 2.15576 | 0.25 | 8.62302 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 2.033 | 2.14837 | 2.14837 | 0.25 | 8.59349 |
| `hu` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.0251073 | 2.11514 | 2.14025 | 2.14025 | 0.25 | 8.56098 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 2.18711 | 2.12425 | 2.12425 | 0.25 | 8.49701 |
| `hu` | `upstream_approach` | `interior` | `5,2` | 2 | -0.5 | -0.0269994 | 2.08716 | 2.11416 | 2.11416 | 0.25 | 8.45663 |
| `v` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.45712 | 1.35624 | -2.10088 | 2.10088 | 0.25 | 8.40353 |
| `v` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 1.14159 | -0.942681 | -2.08427 | 2.08427 | 0.25 | 8.3371 |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 2.43307 | 2.08403 | 2.08403 | 0.25 | 8.33612 |

## Blocked Reasons

- Final-frame `hu` field remains 9.53x over threshold at `constriction_throat/lower_shelf` cell 3,13.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `1.13532` m).
- Streamwise shear/momentum mismatch is still active in `constriction_throat/lower_shelf` (max u/hu delta `0.210905`/`2.38356`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `2.10088`/`1.17672`).

## Next Levers

- Start with `constriction_throat/lower_shelf` cell 3,13; `hu` delta is `2.38356` with reference h `0.255416` m and C++ h `1.12895` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
