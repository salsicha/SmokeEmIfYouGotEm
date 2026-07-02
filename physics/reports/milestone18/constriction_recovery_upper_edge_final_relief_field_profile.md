# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_upper_edge_final_relief/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_upper_edge_final_relief/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.56295`
- Max h/u/v/hu/hv delta: `0.941348` / `1.37024` / `1.33994` / `1.56295` / `1.47379`
- Max profile mass delta: `5.37158` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `upper_shelf` | 18 | -0.100647 / 0.674547 | -0.318989 / 1.35021 | 0.0837223 / 1.22435 | -0.331285 / 1.56295 | 0.0677384 / 0.85528 | -1.81165 | 0.0555556 | 6.25179 |
| `constriction_throat` | `lower_shelf` | 4 | 0.146009 / 0.54121 | 0.0899809 / 0.210905 | 0.0464172 / 0.525518 | 0.430125 / 1.50705 | 0.0684075 / 0.360205 | 0.584036 | 0 | 6.02821 |
| `upstream_approach` | `interior` | 54 | -0.0994737 / 0.521367 | 0.197108 / 0.618346 | -0.146782 / 0.822104 | 0.264522 / 1.03731 | -0.248681 / 1.47379 | -5.37158 | 0 | 5.89516 |
| `downstream_constriction` | `interior` | 8 | 0.100563 / 0.220582 | -0.859827 / 1.32817 | -0.168338 / 0.464449 | -0.8854 / 1.45931 | -0.152466 / 0.483376 | 0.804501 | 0 | 5.83722 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 1.37024 / 1.37024 | -0.544843 / 0.544843 | 0.305549 / 0.305549 | -0.0479119 / 0.0479119 | 0.0651685 | 0 | 5.48096 |
| `upstream_approach` | `upper_edge` | 10 | 0.23488 / 0.789938 | -0.704392 / 1.34175 | 0.198374 / 1.27589 | 0.247494 / 1.33522 | -0.510382 / 1.32461 | 2.3488 | 0 | 5.36701 |
| `constriction_throat` | `upper_edge` | 2 | 0.337795 / 0.486411 | -0.00211336 / 0.00647273 | 0.43356 / 1.33994 | 0.806248 / 1.12318 | -0.0437169 / 0.0864074 | 0.675591 | 0 | 5.35976 |
| `upstream_approach` | `lower_edge` | 10 | 0.0658591 / 0.941348 | -0.00975562 / 1.23756 | -0.179509 / 0.894022 | 0.294126 / 1.33016 | -0.245676 / 1.14172 | 0.658591 | 0 | 5.32066 |
| `constriction_throat` | `lower_edge` | 4 | -0.0870705 / 0.230032 | 0.00946868 / 0.519465 | 0.402273 / 1.04529 | -0.172412 / 1.30933 | 0.497767 / 1.08929 | -0.348282 | 0 | 5.2373 |
| `upstream_approach` | `lower_shelf` | 12 | -0.125054 / 0.56859 | -0.0315032 / 1.29645 | 0.195017 / 0.769666 | -0.0878902 / 0.966651 | 0.0426445 / 0.746951 | -1.50065 | 0 | 5.18581 |
| `recovery` | `interior` | 46 | 0.0755361 / 0.525565 | -0.167415 / 1.03861 | -0.00162908 / 0.721617 | -0.0811796 / 1.23842 | 0.0125526 / 0.909752 | 3.47466 | 0 | 4.95368 |
| `constriction_throat` | `interior` | 8 | 0.0402942 / 0.162787 | -0.14325 / 0.822048 | 0.0411288 / 0.595649 | -0.0177093 / 1.1672 | 0.100011 / 0.666928 | 0.322354 | 0 | 4.66882 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `upstream_approach` | `upper_shelf` | `11,0` | 0 | 5.5 | 2.00238 | 0.439432 | -1.56295 | 1.56295 | 0.25 | 6.25179 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,10` | 10 | -2.5 | 1.49207 | 2.99912 | 1.50705 | 1.50705 | 0.25 | 6.02821 |
| `hv` | `upstream_approach` | `interior` | `3,5` | 5 | -2.5 | 1.06936 | -0.404426 | -1.47379 | 1.47379 | 0.25 | 5.89516 |
| `hu` | `downstream_constriction` | `interior` | `5,15` | 15 | -0.5 | 4.05104 | 2.59173 | -1.45931 | 1.45931 | 0.25 | 5.83722 |
| `hv` | `upstream_approach` | `interior` | `3,6` | 6 | -2.5 | 0.891438 | -0.501482 | -1.39292 | 1.39292 | 0.25 | 5.57168 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 1.4331 | 1.37024 | 1.37024 | 0.25 | 5.48096 |
| `u` | `upstream_approach` | `upper_shelf` | `10,1` | 1 | 4.5 | 3.39685 | 2.04664 | -1.35021 | 1.35021 | 0.25 | 5.40084 |
| `u` | `upstream_approach` | `upper_edge` | `9,2` | 2 | 3.5 | 3.50488 | 2.16313 | -1.34175 | 1.34175 | 0.25 | 5.36701 |
| `v` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | -2.58013 | -1.24019 | 1.33994 | 1.33994 | 0.25 | 5.35976 |
| `hu` | `upstream_approach` | `upper_edge` | `9,6` | 6 | 3.5 | 1.30029 | 2.63551 | 1.33522 | 1.33522 | 0.25 | 5.34089 |
| `hu` | `downstream_constriction` | `interior` | `4,15` | 15 | -1.5 | 3.86465 | 2.53298 | -1.33167 | 1.33167 | 0.25 | 5.32668 |
| `hu` | `upstream_approach` | `lower_edge` | `2,6` | 6 | -3.5 | 0.921728 | 2.25189 | 1.33016 | 1.33016 | 0.25 | 5.32066 |
| `u` | `downstream_constriction` | `interior` | `5,14` | 14 | -0.5 | 3.48923 | 2.16106 | -1.32817 | 1.32817 | 0.25 | 5.31268 |
| `hv` | `upstream_approach` | `upper_edge` | `9,5` | 5 | 3.5 | -0.823694 | -2.1483 | -1.32461 | 1.32461 | 0.25 | 5.29843 |
| `hu` | `constriction_throat` | `lower_edge` | `4,13` | 13 | -1.5 | 4.26895 | 2.95962 | -1.30933 | 1.30933 | 0.25 | 5.2373 |
| `hu` | `downstream_constriction` | `interior` | `5,14` | 14 | -0.5 | 4.19804 | 2.89352 | -1.30452 | 1.30452 | 0.25 | 5.21806 |

## Blocked Reasons

- Final-frame `hu` field remains 6.25x over threshold at `upstream_approach/upper_shelf` cell 11,0.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `0.941348` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/upper_shelf` (max u/hu delta `1.35021`/`1.56295`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/interior` (max v/hv delta `0.822104`/`1.47379`).

## Next Levers

- Start with `upstream_approach/upper_shelf` cell 11,0; `hu` delta is `-1.56295` with reference h `0.864998` m and C++ h `0.19045` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
