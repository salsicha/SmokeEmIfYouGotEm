# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_material_wet_mask_validation/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_material_wet_mask_validation/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `3.27416`
- Max h/u/v/hu/hv delta: `1.10953` / `3.10592` / `2.48585` / `3.27416` / `1.73971`
- Max profile mass delta: `6.99479` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `recovery` | `lower_edge` | 6 | 0.0310288 / 0.145631 | 2.02718 / 3.10592 | 0.101312 / 0.188231 | 2.60821 / 3.27416 | 0.126801 / 0.255274 | 0.186173 | 0 | 13.0966 |
| `downstream_constriction` | `upper_edge` | 2 | 0.0837514 / 0.0913857 | 2.43907 / 2.59608 | -0.773313 / 0.991551 | 3.08609 / 3.25482 | -0.954273 / 1.23248 | 0.167503 | 0 | 13.0193 |
| `recovery` | `upper_edge` | 8 | 0.712027 / 1.10953 | 1.99075 / 2.92973 | 0.727099 / 1.80016 | 2.29725 / 2.72183 | 0.144303 / 0.496205 | 5.69621 | 0 | 11.7189 |
| `recovery` | `interior` | 46 | -0.03742 / 0.388169 | 0.357441 / 2.83198 | -0.03085 / 0.558599 | 0.298741 / 2.54681 | -0.0510399 / 0.727158 | -1.72132 | 0 | 11.3279 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 2.73749 / 2.73749 | -0.859323 / 0.859323 | 0.606344 / 0.606344 | -0.117098 / 0.117098 | 0.0651685 | 0 | 10.9499 |
| `upstream_approach` | `lower_shelf` | 12 | -0.232984 / 0.647151 | -0.914283 / 2.70434 | -0.378091 / 2.48585 | -0.577153 / 1.2944 | -0.335966 / 1.29201 | -2.7958 | 0 | 10.8173 |
| `constriction_throat` | `upper_edge` | 2 | 0.89638 / 0.939981 | 0.27377 / 0.298576 | -0.398975 / 2.31058 | 2.53058 / 2.56256 | -1.02008 / 1.62017 | 1.79276 | 0 | 10.2502 |
| `constriction_throat` | `lower_shelf` | 4 | 0.351203 / 0.867117 | 0.123966 / 0.210905 | -0.371157 / 1.71621 | 1.0187 / 2.4989 | -0.0965132 / 0.318366 | 1.40481 | 0 | 9.99561 |
| `upstream_approach` | `upper_edge` | 10 | 0.672916 / 1.09507 | -0.746198 / 1.73246 | 0.989455 / 2.47107 | 1.1469 / 1.95079 | -0.399676 / 0.780954 | 6.72916 | 0 | 9.88429 |
| `upstream_approach` | `interior` | 54 | -0.129533 / 0.411275 | 0.541177 / 1.20879 | -0.158747 / 0.80196 | 0.803455 / 2.10471 | -0.257511 / 1.42403 | -6.99479 | 0 | 8.41883 |
| `recovery` | `lower_shelf` | 6 | -0.0800904 / 0.147614 | 1.86451 / 2.08349 | -0.0160015 / 0.279141 | 0.394201 / 0.462613 | -0.00724267 / 0.0875858 | -0.480542 | 0 | 8.33395 |
| `upstream_approach` | `upper_shelf` | 18 | -0.160996 / 0.687797 | -0.515053 / 1.89237 | 0.22351 / 2.0442 | -0.502355 / 1.562 | 0.187942 / 0.831279 | -2.89793 | 0.0555556 | 8.1768 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `recovery` | `lower_edge` | `2,18` | 18 | -3.5 | -0.362344 | 2.91181 | 3.27416 | 3.27416 | 0.25 | 13.0966 |
| `hu` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.185349 | 3.06947 | 3.25482 | 3.25482 | 0.25 | 13.0193 |
| `u` | `recovery` | `lower_edge` | `2,18` | 18 | -3.5 | -0.306137 | 2.79978 | 3.10592 | 3.10592 | 0.25 | 12.4237 |
| `hu` | `recovery` | `lower_edge` | `2,19` | 19 | -3.5 | -0.349493 | 2.74465 | 3.09414 | 3.09414 | 0.25 | 12.3766 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 2.81435 | 2.92973 | 2.92973 | 0.25 | 11.7189 |
| `hu` | `downstream_constriction` | `upper_edge` | `8,15` | 15 | 2.5 | -0.0924264 | 2.82493 | 2.91736 | 2.91736 | 0.25 | 11.6694 |
| `hu` | `recovery` | `lower_edge` | `2,20` | 20 | -3.5 | -0.0818346 | 2.76511 | 2.84695 | 2.84695 | 0.25 | 11.3878 |
| `u` | `recovery` | `interior` | `3,17` | 17 | -2.5 | 0.179527 | 3.01151 | 2.83198 | 2.83198 | 0.25 | 11.3279 |
| `u` | `recovery` | `upper_edge` | `9,17` | 17 | 3.5 | 0.234362 | 3.01151 | 2.77715 | 2.77715 | 0.25 | 11.1086 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 2.80034 | 2.73749 | 2.73749 | 0.25 | 10.9499 |
| `hu` | `recovery` | `upper_edge` | `9,19` | 19 | 3.5 | -0.0167685 | 2.70506 | 2.72183 | 2.72183 | 0.25 | 10.8873 |
| `u` | `upstream_approach` | `lower_shelf` | `0,1` | 1 | -5.5 | 3.63205 | 0.927715 | -2.70434 | 2.70434 | 0.25 | 10.8173 |
| `hu` | `recovery` | `upper_edge` | `9,20` | 20 | 3.5 | 0.048893 | 2.72599 | 2.6771 | 2.6771 | 0.25 | 10.7084 |
| `u` | `recovery` | `upper_edge` | `8,16` | 16 | 2.5 | 0.137262 | 2.77688 | 2.63962 | 2.63962 | 0.25 | 10.5585 |
| `u` | `recovery` | `interior` | `8,17` | 17 | 2.5 | 0.350557 | 2.98779 | 2.63724 | 2.63724 | 0.25 | 10.5489 |
| `hu` | `recovery` | `upper_edge` | `9,21` | 21 | 3.5 | 0.136229 | 2.73942 | 2.60319 | 2.60319 | 0.25 | 10.4128 |

## Blocked Reasons

- Final-frame `hu` field remains 13.10x over threshold at `recovery/lower_edge` cell 2,18.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `1.10953` m).
- Streamwise shear/momentum mismatch is still active in `recovery/lower_edge` (max u/hu delta `3.10592`/`3.27416`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `2.48585`/`1.29201`).

## Next Levers

- Start with `recovery/lower_edge` cell 2,18; `hu` delta is `3.27416` with reference h `1.1836` m and C++ h `1.04002` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
