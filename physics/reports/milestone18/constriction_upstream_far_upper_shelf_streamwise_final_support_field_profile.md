# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_far_upper_shelf_streamwise_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_far_upper_shelf_streamwise_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.33994`
- Max h/u/v/hu/hv delta: `0.944214` / `1.29647` / `1.33994` / `1.33656` / `1.32513`
- Max profile mass delta: `4.70026` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `constriction_throat` | `upper_edge` | 2 | 0.318188 / 0.445533 | -0.00211336 / 0.00647273 | 0.433565 / 1.33994 | 0.761248 / 1.02886 | -0.0178103 / 0.0357113 | 0.636376 | 0 | 5.35976 |
| `upstream_approach` | `upper_edge` | 10 | 0.287974 / 0.790563 | -0.559517 / 1.24842 | 0.095275 / 0.82526 | 0.422355 / 1.33656 | -0.66114 / 1.32513 | 2.87974 | 0 | 5.34622 |
| `upstream_approach` | `lower_edge` | 10 | 0.0728057 / 0.944214 | -0.00682794 / 1.23756 | -0.183971 / 0.894022 | 0.308567 / 1.33106 | -0.249541 / 1.14337 | 0.728057 | 0 | 5.32425 |
| `constriction_throat` | `lower_edge` | 4 | -0.0582717 / 0.22934 | 0.0063422 / 0.519684 | 0.396673 / 1.04511 | -0.105239 / 1.30773 | 0.486408 / 1.09004 | -0.233087 | 0 | 5.23093 |
| `upstream_approach` | `lower_shelf` | 12 | -0.12482 / 0.568561 | -0.0283555 / 1.29647 | 0.193761 / 0.769794 | -0.0854805 / 0.966143 | 0.0426074 / 0.747178 | -1.49784 | 0 | 5.18589 |
| `upstream_approach` | `upper_shelf` | 18 | -0.0520344 / 0.484683 | -0.204202 / 1.26675 | 0.122929 / 1.22439 | -0.160357 / 1.19873 | 0.0700108 / 0.855263 | -0.936619 | 0.0555556 | 5.06702 |
| `upstream_approach` | `interior` | 54 | -0.0870419 / 0.52657 | 0.204158 / 0.61841 | -0.09453 / 0.739795 | 0.286494 / 1.04713 | -0.167874 / 1.26045 | -4.70026 | 0 | 5.0418 |
| `recovery` | `interior` | 46 | 0.0761261 / 0.525371 | -0.167374 / 1.03856 | -0.00166535 / 0.721918 | -0.080031 / 1.23716 | 0.0125821 / 0.910042 | 3.5018 | 0 | 4.94862 |
| `constriction_throat` | `interior` | 8 | 0.0480783 / 0.165426 | -0.145163 / 0.82226 | 0.0419608 / 0.596279 | -0.000661892 / 1.16569 | 0.0988016 / 0.666928 | 0.384626 | 0 | 4.66275 |
| `recovery` | `lower_shelf` | 6 | -0.0741668 / 0.141071 | 0.961327 / 1.08658 | -0.0253339 / 0.291724 | 0.202525 / 0.266347 | -0.00873634 / 0.0891502 | -0.445001 | 0 | 4.3463 |
| `recovery` | `upper_edge` | 8 | 0.253979 / 0.843526 | 0.0356353 / 1.02488 | 0.0505882 / 0.727805 | 0.191837 / 1.0288 | -0.115169 / 0.902388 | 2.03183 | 0 | 4.1152 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 0.906598 / 0.906598 | -0.0813964 / 0.0813964 | 0.203548 / 0.203548 | 0.0540463 / 0.0540463 | 0.0651685 | 0 | 3.62639 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `v` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | -2.58013 | -1.24019 | 1.33994 | 1.33994 | 0.25 | 5.35976 |
| `hu` | `upstream_approach` | `upper_edge` | `9,6` | 6 | 3.5 | 1.30029 | 2.63684 | 1.33656 | 1.33656 | 0.25 | 5.34622 |
| `hu` | `upstream_approach` | `lower_edge` | `2,6` | 6 | -3.5 | 0.921728 | 2.25279 | 1.33106 | 1.33106 | 0.25 | 5.32425 |
| `hv` | `upstream_approach` | `upper_edge` | `9,5` | 5 | 3.5 | -0.823694 | -2.14882 | -1.32513 | 1.32513 | 0.25 | 5.30052 |
| `hu` | `constriction_throat` | `lower_edge` | `4,13` | 13 | -1.5 | 4.26895 | 2.96121 | -1.30773 | 1.30773 | 0.25 | 5.23093 |
| `u` | `upstream_approach` | `lower_shelf` | `1,6` | 6 | -4.5 | 0.26938 | 1.56585 | 1.29647 | 1.29647 | 0.25 | 5.18589 |
| `u` | `upstream_approach` | `upper_shelf` | `9,9` | 9 | 3.5 | 0.274161 | 1.54092 | 1.26675 | 1.26675 | 0.25 | 5.06702 |
| `hv` | `upstream_approach` | `interior` | `8,2` | 2 | 2.5 | -0.689505 | -1.94995 | -1.26045 | 1.26045 | 0.25 | 5.0418 |
| `u` | `upstream_approach` | `upper_edge` | `9,3` | 3 | 3.5 | 3.41154 | 2.16313 | -1.24842 | 1.24842 | 0.25 | 4.99366 |
| `u` | `upstream_approach` | `upper_edge` | `9,4` | 4 | 3.5 | 3.40365 | 2.16313 | -1.24053 | 1.24053 | 0.25 | 4.96211 |
| `u` | `upstream_approach` | `lower_edge` | `3,9` | 9 | -2.5 | 2.27586 | 1.0383 | -1.23756 | 1.23756 | 0.25 | 4.95023 |
| `hu` | `recovery` | `interior` | `5,21` | 21 | -0.5 | 3.74045 | 2.50329 | -1.23716 | 1.23716 | 0.25 | 4.94862 |
| `u` | `upstream_approach` | `upper_edge` | `9,5` | 5 | 3.5 | 3.39654 | 2.16313 | -1.23341 | 1.23341 | 0.25 | 4.93365 |
| `v` | `upstream_approach` | `upper_shelf` | `9,9` | 9 | 3.5 | -1.99059 | -0.766196 | 1.22439 | 1.22439 | 0.25 | 4.89757 |
| `hu` | `upstream_approach` | `upper_shelf` | `11,1` | 1 | 5.5 | 1.75106 | 0.55233 | -1.19873 | 1.19873 | 0.25 | 4.7949 |
| `hv` | `upstream_approach` | `upper_edge` | `9,4` | 4 | 3.5 | -0.84568 | -2.01787 | -1.17219 | 1.17219 | 0.25 | 4.68875 |

## Blocked Reasons

- Final-frame `v` field remains 5.36x over threshold at `constriction_throat/upper_edge` cell 7,10.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `0.944214` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/upper_edge` (max u/hu delta `1.24842`/`1.33656`).
- Cross-stream shear/momentum mismatch is still active in `constriction_throat/upper_edge` (max v/hv delta `1.33994`/`0.0357113`).

## Next Levers

- Start with `constriction_throat/upper_edge` cell 7,10; `v` delta is `1.33994` with reference h `0.385715` m and C++ h `0.831248` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
