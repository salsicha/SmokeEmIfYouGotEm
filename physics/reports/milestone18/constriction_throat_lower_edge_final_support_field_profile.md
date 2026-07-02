# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_throat_lower_edge_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_throat_lower_edge_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.26675`
- Max h/u/v/hu/hv delta: `0.944214` / `1.26675` / `1.22439` / `1.23716` / `1.26045`
- Max profile mass delta: `3.5018` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `upper_shelf` | 18 | -0.0520344 / 0.484683 | -0.204202 / 1.26675 | 0.122929 / 1.22439 | -0.160357 / 1.19873 | 0.0700108 / 0.855263 | -0.936619 | 0.0555556 | 5.06702 |
| `upstream_approach` | `interior` | 54 | -0.0490701 / 0.52657 | 0.204637 / 0.61841 | -0.0982248 / 0.739795 | 0.329591 / 1.04713 | -0.189914 / 1.26045 | -2.64978 | 0 | 5.0418 |
| `upstream_approach` | `upper_edge` | 10 | 0.0829265 / 0.43989 | -0.559517 / 1.24842 | 0.095275 / 0.82526 | -0.0185482 / 0.300021 | -0.275585 / 1.09012 | 0.829265 | 0 | 4.99366 |
| `upstream_approach` | `lower_edge` | 10 | 0.0728057 / 0.944214 | -0.0801694 / 1.23756 | -0.183971 / 0.894022 | 0.188837 / 1.08181 | -0.249541 / 1.14337 | 0.728057 | 0 | 4.95023 |
| `recovery` | `interior` | 46 | 0.0761261 / 0.525371 | -0.167374 / 1.03856 | -0.00166535 / 0.721918 | -0.080031 / 1.23716 | 0.0125821 / 0.910042 | 3.5018 | 0 | 4.94862 |
| `constriction_throat` | `interior` | 8 | 0.0480783 / 0.165426 | -0.145163 / 0.82226 | 0.0419608 / 0.596279 | -0.000661892 / 1.16569 | 0.0988016 / 0.666928 | 0.384626 | 0 | 4.66275 |
| `upstream_approach` | `lower_shelf` | 12 | -0.12482 / 0.568561 | -0.0892821 / 1.08966 | 0.193761 / 0.769794 | -0.102087 / 0.966143 | 0.0426074 / 0.747178 | -1.49784 | 0 | 4.35862 |
| `recovery` | `lower_shelf` | 6 | -0.0741668 / 0.141071 | 0.961327 / 1.08658 | -0.0253339 / 0.291724 | 0.202525 / 0.266347 | -0.00873634 / 0.0891502 | -0.445001 | 0 | 4.3463 |
| `constriction_throat` | `upper_edge` | 2 | 0.318188 / 0.445533 | -0.00211336 / 0.00647273 | 0.0714253 / 0.615661 | 0.761248 / 1.02886 | -0.318839 / 0.637768 | 0.636376 | 0 | 4.11544 |
| `recovery` | `upper_edge` | 8 | 0.253979 / 0.843526 | 0.0356353 / 1.02488 | 0.0505882 / 0.727805 | 0.191837 / 1.0288 | -0.115169 / 0.902388 | 2.03183 | 0 | 4.1152 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 0.906598 / 0.906598 | -0.0813964 / 0.0813964 | 0.203548 / 0.203548 | 0.0540463 / 0.0540463 | 0.0651685 | 0 | 3.62639 |
| `downstream_constriction` | `interior` | 8 | 0.100999 / 0.221006 | -0.408671 / 0.777072 | -0.168217 / 0.464411 | -0.290244 / 0.601119 | -0.152082 / 0.482949 | 0.807994 | 0 | 3.10829 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `u` | `upstream_approach` | `upper_shelf` | `9,9` | 9 | 3.5 | 0.274161 | 1.54092 | 1.26675 | 1.26675 | 0.25 | 5.06702 |
| `hv` | `upstream_approach` | `interior` | `8,2` | 2 | 2.5 | -0.689505 | -1.94995 | -1.26045 | 1.26045 | 0.25 | 5.0418 |
| `u` | `upstream_approach` | `upper_edge` | `9,3` | 3 | 3.5 | 3.41154 | 2.16313 | -1.24842 | 1.24842 | 0.25 | 4.99366 |
| `u` | `upstream_approach` | `upper_edge` | `9,4` | 4 | 3.5 | 3.40365 | 2.16313 | -1.24053 | 1.24053 | 0.25 | 4.96211 |
| `u` | `upstream_approach` | `lower_edge` | `3,9` | 9 | -2.5 | 2.27586 | 1.0383 | -1.23756 | 1.23756 | 0.25 | 4.95023 |
| `hu` | `recovery` | `interior` | `5,21` | 21 | -0.5 | 3.74045 | 2.50329 | -1.23716 | 1.23716 | 0.25 | 4.94862 |
| `u` | `upstream_approach` | `upper_edge` | `9,5` | 5 | 3.5 | 3.39654 | 2.16313 | -1.23341 | 1.23341 | 0.25 | 4.93365 |
| `v` | `upstream_approach` | `upper_shelf` | `9,9` | 9 | 3.5 | -1.99059 | -0.766196 | 1.22439 | 1.22439 | 0.25 | 4.89757 |
| `hu` | `upstream_approach` | `upper_shelf` | `11,1` | 1 | 5.5 | 1.75106 | 0.55233 | -1.19873 | 1.19873 | 0.25 | 4.7949 |
| `hu` | `constriction_throat` | `interior` | `5,13` | 13 | -0.5 | 4.34086 | 3.17517 | -1.16569 | 1.16569 | 0.25 | 4.66275 |
| `v` | `upstream_approach` | `upper_shelf` | `9,7` | 7 | 3.5 | -1.51195 | -0.363073 | 1.14887 | 1.14887 | 0.25 | 4.59549 |
| `hv` | `upstream_approach` | `lower_edge` | `3,8` | 8 | -2.5 | 0.212418 | -0.930953 | -1.14337 | 1.14337 | 0.25 | 4.57348 |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 1.49238 | 1.14335 | 1.14335 | 0.25 | 4.57338 |
| `u` | `upstream_approach` | `lower_edge` | `3,8` | 8 | -2.5 | 2.159 | 1.0383 | -1.1207 | 1.1207 | 0.25 | 4.48278 |
| `hu` | `recovery` | `interior` | `6,21` | 21 | 0.5 | 3.63894 | 2.52242 | -1.11652 | 1.11652 | 0.25 | 4.46608 |
| `hu` | `recovery` | `interior` | `7,19` | 19 | 1.5 | 2.42826 | 1.33137 | -1.09689 | 1.09689 | 0.25 | 4.38754 |

## Blocked Reasons

- Final-frame `u` field remains 5.07x over threshold at `upstream_approach/upper_shelf` cell 9,9.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `0.944214` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/upper_shelf` (max u/hu delta `1.26675`/`1.19873`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/interior` (max v/hv delta `0.739795`/`1.26045`).

## Next Levers

- Start with `upstream_approach/upper_shelf` cell 9,9; `u` delta is `1.26675` with reference h `0.202025` m and C++ h `0.22` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
