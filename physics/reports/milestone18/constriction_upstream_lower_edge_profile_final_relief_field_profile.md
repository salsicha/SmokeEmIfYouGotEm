# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_lower_edge_profile_final_relief/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_lower_edge_profile_final_relief/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.23696`
- Max h/u/v/hu/hv delta: `0.843545` / `1.08965` / `1.05171` / `1.23696` / `1.06274`
- Max profile mass delta: `3.50584` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `recovery` | `interior` | 46 | 0.0762139 / 0.525345 | -0.167367 / 1.03856 | -0.00167087 / 0.721966 | -0.0798583 / 1.23696 | 0.0125861 / 0.910088 | 3.50584 | 0 | 4.94786 |
| `upstream_approach` | `upper_shelf` | 18 | -0.010032 / 0.31896 | -0.298379 / 0.735237 | 0.0888337 / 1.05171 | -0.136939 / 1.19874 | 0.0403556 / 0.690063 | -0.180576 | 0.0555556 | 4.79495 |
| `constriction_throat` | `interior` | 8 | 0.0473046 / 0.165415 | -0.145195 / 0.822303 | 0.0421617 / 0.596378 | -0.00266631 / 1.16549 | 0.0994481 / 0.668975 | 0.378437 | 0 | 4.66195 |
| `upstream_approach` | `lower_shelf` | 12 | -0.124716 / 0.568509 | -0.089278 / 1.08965 | 0.193781 / 0.770024 | -0.102045 / 0.966143 | 0.0426408 / 0.747178 | -1.4966 | 0 | 4.35861 |
| `recovery` | `lower_shelf` | 6 | -0.0741665 / 0.141071 | 0.961329 / 1.08658 | -0.0253347 / 0.291725 | 0.202527 / 0.266344 | -0.00873645 / 0.0891504 | -0.444999 | 0 | 4.34634 |
| `upstream_approach` | `lower_edge` | 10 | -0.0839865 / 0.310003 | 0.169161 / 0.758783 | -0.0169766 / 0.480942 | 0.18921 / 1.08182 | -0.0451976 / 0.801849 | -0.839865 | 0 | 4.32727 |
| `upstream_approach` | `upper_edge` | 10 | 0.0845675 / 0.382263 | -0.384119 / 0.739957 | 0.0953234 / 0.82526 | 0.0841741 / 0.241315 | -0.27024 / 1.06274 | 0.845675 | 0 | 4.25095 |
| `recovery` | `upper_edge` | 8 | 0.254005 / 0.843545 | 0.0356766 / 1.02487 | 0.0505467 / 0.728136 | 0.191911 / 1.02922 | -0.115224 / 0.902801 | 2.03204 | 0 | 4.1169 |
| `constriction_throat` | `upper_edge` | 2 | 0.316413 / 0.44174 | -0.00211336 / 0.00647273 | 0.0714289 / 0.615661 | 0.757186 / 1.02011 | -0.31503 / 0.630316 | 0.632826 | 0 | 4.08043 |
| `upstream_approach` | `interior` | 54 | -0.0441581 / 0.466525 | 0.203704 / 0.618417 | -0.0790615 / 0.502488 | 0.33401 / 0.98467 | -0.157463 / 0.614527 | -2.38454 | 0 | 3.93868 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 0.906584 / 0.906584 | -0.0814087 / 0.0814087 | 0.203545 / 0.203545 | 0.0540436 / 0.0540436 | 0.0651685 | 0 | 3.62634 |
| `downstream_constriction` | `interior` | 8 | 0.101053 / 0.221059 | -0.408664 / 0.777057 | -0.168199 / 0.464406 | -0.290112 / 0.600911 | -0.152029 / 0.482889 | 0.808425 | 0 | 3.10823 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `recovery` | `interior` | `5,21` | 21 | -0.5 | 3.74045 | 2.50348 | -1.23696 | 1.23696 | 0.25 | 4.94786 |
| `hu` | `upstream_approach` | `upper_shelf` | `11,1` | 1 | 5.5 | 1.75106 | 0.552319 | -1.19874 | 1.19874 | 0.25 | 4.79495 |
| `hu` | `constriction_throat` | `interior` | `5,13` | 13 | -0.5 | 4.34086 | 3.17537 | -1.16549 | 1.16549 | 0.25 | 4.66195 |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 1.49252 | 1.14349 | 1.14349 | 0.25 | 4.57396 |
| `hu` | `recovery` | `interior` | `6,21` | 21 | 0.5 | 3.63894 | 2.52265 | -1.1163 | 1.1163 | 0.25 | 4.46519 |
| `hu` | `recovery` | `interior` | `7,19` | 19 | 1.5 | 2.42826 | 1.33146 | -1.0968 | 1.0968 | 0.25 | 4.38722 |
| `u` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.85418 | 2.76452 | -1.08965 | 1.08965 | 0.25 | 4.35861 |
| `hu` | `recovery` | `interior` | `7,20` | 20 | 1.5 | 2.39188 | 1.30414 | -1.08774 | 1.08774 | 0.25 | 4.35095 |
| `u` | `recovery` | `lower_shelf` | `1,21` | 21 | -4.5 | 0.0702233 | 1.15681 | 1.08658 | 1.08658 | 0.25 | 4.34634 |
| `hu` | `upstream_approach` | `lower_edge` | `2,5` | 5 | -3.5 | 1.31208 | 2.39389 | 1.08182 | 1.08182 | 0.25 | 4.32727 |
| `u` | `recovery` | `lower_shelf` | `1,20` | 20 | -4.5 | -0.0551087 | 1.01081 | 1.06592 | 1.06592 | 0.25 | 4.26368 |
| `u` | `recovery` | `lower_shelf` | `1,18` | 18 | -4.5 | 0.900419 | 1.96476 | 1.06434 | 1.06434 | 0.25 | 4.25735 |
| `hv` | `upstream_approach` | `upper_edge` | `8,8` | 8 | 2.5 | -1.17242 | -2.23516 | -1.06274 | 1.06274 | 0.25 | 4.25095 |
| `v` | `upstream_approach` | `upper_shelf` | `9,7` | 7 | 3.5 | -1.51195 | -0.460233 | 1.05171 | 1.05171 | 0.25 | 4.20685 |
| `u` | `recovery` | `interior` | `5,21` | 21 | -0.5 | 2.74567 | 1.70711 | -1.03856 | 1.03856 | 0.25 | 4.15423 |
| `hu` | `recovery` | `upper_edge` | `8,16` | 16 | 2.5 | 0.169789 | 1.19901 | 1.02922 | 1.02922 | 0.25 | 4.1169 |

## Blocked Reasons

- Final-frame `hu` field remains 4.95x over threshold at `recovery/interior` cell 5,21.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `0.843545` m).
- Streamwise shear/momentum mismatch is still active in `recovery/interior` (max u/hu delta `1.03856`/`1.23696`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/upper_edge` (max v/hv delta `0.82526`/`1.06274`).

## Next Levers

- Start with `recovery/interior` cell 5,21; `hu` delta is `-1.23696` with reference h `1.36231` m and C++ h `1.4665` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
