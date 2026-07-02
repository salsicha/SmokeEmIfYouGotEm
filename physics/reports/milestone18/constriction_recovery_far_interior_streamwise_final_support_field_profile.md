# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_far_interior_streamwise_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_far_interior_streamwise_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.19874`
- Max h/u/v/hu/hv delta: `0.843543` / `1.18365` / `1.05171` / `1.19874` / `1.06274`
- Max profile mass delta: `3.50548` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `upper_shelf` | 18 | -0.0100319 / 0.318959 | -0.298379 / 0.735237 | 0.0888337 / 1.05171 | -0.136939 / 1.19874 | 0.0403555 / 0.690062 | -0.180574 | 0.0555556 | 4.79494 |
| `recovery` | `lower_shelf` | 6 | -0.0741665 / 0.141071 | 1.0051 / 1.18365 | -0.0253249 / 0.291725 | 0.212442 / 0.266344 | -0.00873423 / 0.0891503 | -0.444999 | 0 | 4.73458 |
| `constriction_throat` | `interior` | 8 | 0.0473059 / 0.165415 | -0.145195 / 0.822304 | 0.0421612 / 0.596381 | -0.00266341 / 1.16548 | 0.0994474 / 0.668973 | 0.378447 | 0 | 4.66192 |
| `recovery` | `interior` | 46 | 0.0762061 / 0.525345 | -0.0878764 / 0.986856 | -0.00166534 / 0.721967 | 0.0361699 / 1.14349 | 0.0125622 / 0.910089 | 3.50548 | 0 | 4.57398 |
| `upstream_approach` | `lower_shelf` | 12 | -0.124716 / 0.568508 | -0.089278 / 1.08965 | 0.193781 / 0.770024 | -0.102045 / 0.966143 | 0.0426408 / 0.747178 | -1.49659 | 0 | 4.35861 |
| `upstream_approach` | `lower_edge` | 10 | -0.0839864 / 0.310003 | 0.169161 / 0.758783 | -0.0169766 / 0.480942 | 0.189211 / 1.08182 | -0.0451976 / 0.801849 | -0.839864 | 0 | 4.32727 |
| `upstream_approach` | `upper_edge` | 10 | 0.0845691 / 0.382264 | -0.384119 / 0.739957 | 0.0953235 / 0.82526 | 0.0841779 / 0.241316 | -0.270243 / 1.06274 | 0.845691 | 0 | 4.25095 |
| `recovery` | `upper_edge` | 8 | 0.254005 / 0.843543 | 0.0356779 / 1.02487 | 0.0505455 / 0.728145 | 0.191913 / 1.02924 | -0.115225 / 0.902813 | 2.03204 | 0 | 4.11695 |
| `constriction_throat` | `upper_edge` | 2 | 0.316416 / 0.44174 | -0.00211336 / 0.00647273 | 0.071429 / 0.615661 | 0.757195 / 1.02011 | -0.315028 / 0.630316 | 0.632833 | 0 | 4.08043 |
| `upstream_approach` | `interior` | 54 | -0.0441563 / 0.466528 | 0.203704 / 0.618418 | -0.0790613 / 0.502487 | 0.334012 / 0.984673 | -0.157463 / 0.614527 | -2.38444 | 0 | 3.93869 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 0.906584 / 0.906584 | -0.0814088 / 0.0814088 | 0.203545 / 0.203545 | 0.0540436 / 0.0540436 | 0.0651685 | 0 | 3.62634 |
| `downstream_constriction` | `interior` | 8 | 0.101055 / 0.221061 | -0.408664 / 0.777057 | -0.168198 / 0.464406 | -0.290106 / 0.600903 | -0.152028 / 0.482887 | 0.808441 | 0 | 3.10823 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `upstream_approach` | `upper_shelf` | `11,1` | 1 | 5.5 | 1.75106 | 0.55232 | -1.19874 | 1.19874 | 0.25 | 4.79494 |
| `u` | `recovery` | `lower_shelf` | `1,21` | 21 | -4.5 | 0.0702233 | 1.25387 | 1.18365 | 1.18365 | 0.25 | 4.73458 |
| `hu` | `constriction_throat` | `interior` | `5,13` | 13 | -0.5 | 4.34086 | 3.17538 | -1.16548 | 1.16548 | 0.25 | 4.66192 |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 1.49253 | 1.14349 | 1.14349 | 0.25 | 4.57398 |
| `hu` | `recovery` | `interior` | `7,19` | 19 | 1.5 | 2.42826 | 1.33146 | -1.0968 | 1.0968 | 0.25 | 4.38721 |
| `u` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.85418 | 2.76452 | -1.08965 | 1.08965 | 0.25 | 4.35861 |
| `u` | `recovery` | `lower_shelf` | `1,22` | 22 | -4.5 | 0.324993 | 1.41414 | 1.08915 | 1.08915 | 0.25 | 4.3566 |
| `hu` | `recovery` | `interior` | `7,20` | 20 | 1.5 | 2.39188 | 1.30378 | -1.0881 | 1.0881 | 0.25 | 4.35241 |
| `hu` | `upstream_approach` | `lower_edge` | `2,5` | 5 | -3.5 | 1.31208 | 2.39389 | 1.08182 | 1.08182 | 0.25 | 4.32727 |
| `u` | `recovery` | `lower_shelf` | `1,20` | 20 | -4.5 | -0.0551087 | 1.01225 | 1.06735 | 1.06735 | 0.25 | 4.26942 |
| `u` | `recovery` | `lower_shelf` | `1,18` | 18 | -4.5 | 0.900419 | 1.96476 | 1.06434 | 1.06434 | 0.25 | 4.25735 |
| `hv` | `upstream_approach` | `upper_edge` | `8,8` | 8 | 2.5 | -1.17242 | -2.23516 | -1.06274 | 1.06274 | 0.25 | 4.25095 |
| `v` | `upstream_approach` | `upper_shelf` | `9,7` | 7 | 3.5 | -1.51195 | -0.460233 | 1.05171 | 1.05171 | 0.25 | 4.20685 |
| `hu` | `recovery` | `upper_edge` | `8,16` | 16 | 2.5 | 0.169789 | 1.19903 | 1.02924 | 1.02924 | 0.25 | 4.11695 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 0.909496 | 1.02487 | 1.02487 | 0.25 | 4.09948 |
| `hu` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | 0.889107 | 1.90922 | 1.02011 | 1.02011 | 0.25 | 4.08043 |

## Blocked Reasons

- Final-frame `hu` field remains 4.79x over threshold at `upstream_approach/upper_shelf` cell 11,1.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `0.843543` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/upper_shelf` (max u/hu delta `0.735237`/`1.19874`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/upper_edge` (max v/hv delta `0.82526`/`1.06274`).

## Next Levers

- Start with `upstream_approach/upper_shelf` cell 11,1; `hu` delta is `-1.19874` with reference h `0.524139` m and C++ h `0.205179` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
