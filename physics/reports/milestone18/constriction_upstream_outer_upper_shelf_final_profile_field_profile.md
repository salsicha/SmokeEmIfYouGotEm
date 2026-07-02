# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_outer_upper_shelf_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_outer_upper_shelf_final_profile/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.57786`
- Max h/u/v/hu/hv delta: `0.941307` / `1.37024` / `1.57786` / `1.56295` / `1.47379`
- Max profile mass delta: `5.37291` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `recovery` | `upper_edge` | 8 | 0.580467 / 0.842688 | 0.208114 / 1.02502 | 0.511005 / 1.57786 | 0.443279 / 1.02597 | -0.0732274 / 0.899627 | 4.64373 | 0 | 6.31146 |
| `upstream_approach` | `upper_shelf` | 18 | -0.100647 / 0.674549 | -0.31899 / 1.35021 | 0.0837223 / 1.22435 | -0.331286 / 1.56295 | 0.0677386 / 0.85528 | -1.81165 | 0.0555556 | 6.25181 |
| `constriction_throat` | `lower_shelf` | 4 | 0.146001 / 0.541208 | 0.0899807 / 0.210905 | 0.0464172 / 0.525518 | 0.430104 / 1.50705 | 0.0683949 / 0.360155 | 0.584006 | 0 | 6.02819 |
| `upstream_approach` | `interior` | 54 | -0.0994983 / 0.521335 | 0.197107 / 0.618344 | -0.146783 / 0.822105 | 0.264495 / 1.03726 | -0.248674 / 1.47379 | -5.37291 | 0 | 5.89514 |
| `downstream_constriction` | `interior` | 8 | 0.100538 / 0.220559 | -0.859833 / 1.32818 | -0.16834 / 0.46445 | -0.885454 / 1.45937 | -0.152481 / 0.48339 | 0.804304 | 0 | 5.83748 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 1.37024 / 1.37024 | -0.544842 / 0.544842 | 0.30555 / 0.30555 | -0.0479116 / 0.0479116 | 0.0651685 | 0 | 5.48097 |
| `upstream_approach` | `upper_edge` | 10 | 0.23487 / 0.789933 | -0.704392 / 1.34175 | 0.198373 / 1.27589 | 0.247483 / 1.33521 | -0.51037 / 1.3246 | 2.3487 | 0 | 5.36701 |
| `constriction_throat` | `upper_edge` | 2 | 0.337781 / 0.486409 | -0.00211336 / 0.00647273 | 0.43356 / 1.33994 | 0.80621 / 1.12317 | -0.043725 / 0.086405 | 0.675561 | 0 | 5.35976 |
| `upstream_approach` | `lower_edge` | 10 | 0.0658484 / 0.941307 | -0.00975573 / 1.23756 | -0.179509 / 0.894022 | 0.294113 / 1.33016 | -0.245673 / 1.14169 | 0.658484 | 0 | 5.32063 |
| `constriction_throat` | `lower_edge` | 4 | -0.0870764 / 0.230043 | 0.00946987 / 0.51946 | 0.402274 / 1.04529 | -0.172426 / 1.30935 | 0.497764 / 1.08928 | -0.348306 | 0 | 5.2374 |
| `upstream_approach` | `lower_shelf` | 12 | -0.125054 / 0.56859 | -0.0315032 / 1.29645 | 0.195016 / 0.769665 | -0.0878908 / 0.966651 | 0.042644 / 0.74695 | -1.50065 | 0 | 5.18581 |
| `recovery` | `lower_shelf` | 6 | -0.0741688 / 0.141071 | 1.01905 / 1.1774 | -0.0223146 / 0.292114 | 0.215599 / 0.266383 | -0.0080527 / 0.0892385 | -0.445013 | 0 | 4.70961 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `v` | `recovery` | `upper_edge` | `9,20` | 20 | 3.5 | -1.32242 | 0.255446 | 1.57786 | 1.57786 | 0.25 | 6.31146 |
| `hu` | `upstream_approach` | `upper_shelf` | `11,0` | 0 | 5.5 | 2.00238 | 0.439429 | -1.56295 | 1.56295 | 0.25 | 6.25181 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,10` | 10 | -2.5 | 1.49207 | 2.99911 | 1.50705 | 1.50705 | 0.25 | 6.02819 |
| `hv` | `upstream_approach` | `interior` | `3,5` | 5 | -2.5 | 1.06936 | -0.404422 | -1.47379 | 1.47379 | 0.25 | 5.89514 |
| `hu` | `downstream_constriction` | `interior` | `5,15` | 15 | -0.5 | 4.05104 | 2.59167 | -1.45937 | 1.45937 | 0.25 | 5.83748 |
| `hv` | `upstream_approach` | `interior` | `3,6` | 6 | -2.5 | 0.891438 | -0.501477 | -1.39291 | 1.39291 | 0.25 | 5.57166 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 1.4331 | 1.37024 | 1.37024 | 0.25 | 5.48097 |
| `u` | `upstream_approach` | `upper_shelf` | `10,1` | 1 | 4.5 | 3.39685 | 2.04663 | -1.35021 | 1.35021 | 0.25 | 5.40085 |
| `u` | `upstream_approach` | `upper_edge` | `9,2` | 2 | 3.5 | 3.50488 | 2.16313 | -1.34175 | 1.34175 | 0.25 | 5.36701 |
| `v` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | -2.58013 | -1.24019 | 1.33994 | 1.33994 | 0.25 | 5.35976 |
| `hu` | `upstream_approach` | `upper_edge` | `9,6` | 6 | 3.5 | 1.30029 | 2.6355 | 1.33521 | 1.33521 | 0.25 | 5.34085 |
| `hu` | `downstream_constriction` | `interior` | `4,15` | 15 | -1.5 | 3.86465 | 2.53292 | -1.33172 | 1.33172 | 0.25 | 5.32689 |
| `hu` | `upstream_approach` | `lower_edge` | `2,6` | 6 | -3.5 | 0.921728 | 2.25189 | 1.33016 | 1.33016 | 0.25 | 5.32063 |
| `u` | `downstream_constriction` | `interior` | `5,14` | 14 | -0.5 | 3.48923 | 2.16105 | -1.32818 | 1.32818 | 0.25 | 5.3127 |
| `hv` | `upstream_approach` | `upper_edge` | `9,5` | 5 | 3.5 | -0.823694 | -2.1483 | -1.3246 | 1.3246 | 0.25 | 5.29841 |
| `hu` | `constriction_throat` | `lower_edge` | `4,13` | 13 | -1.5 | 4.26895 | 2.9596 | -1.30935 | 1.30935 | 0.25 | 5.2374 |

## Blocked Reasons

- Final-frame `v` field remains 6.31x over threshold at `recovery/upper_edge` cell 9,20.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `0.941307` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/upper_shelf` (max u/hu delta `1.35021`/`1.56295`).
- Cross-stream shear/momentum mismatch is still active in `recovery/upper_edge` (max v/hv delta `1.57786`/`0.899627`).

## Next Levers

- Start with `recovery/upper_edge` cell 9,20; `v` delta is `1.57786` with reference h `0.251909` m and C++ h `1.04533` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
