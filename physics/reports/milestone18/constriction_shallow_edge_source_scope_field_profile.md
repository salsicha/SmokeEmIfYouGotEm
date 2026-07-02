# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_shallow_edge_source_scope/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_shallow_edge_source_scope/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `2.31593`
- Max h/u/v/hu/hv delta: `1.11472` / `2.24265` / `2.09945` / `2.31593` / `1.64778`
- Max profile mass delta: `7.63484` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `upper_edge` | 10 | 0.650253 / 1.04919 | -0.527359 / 1.72081 | 0.838382 / 1.92649 | 1.39921 / 2.31593 | -0.573998 / 1.47323 | 6.50253 | 0 | 9.26373 |
| `recovery` | `interior` | 46 | -0.0405865 / 0.369704 | -0.186278 / 2.24265 | -0.17888 / 0.913928 | -0.393932 / 2.19147 | -0.222711 / 1.11017 | -1.86698 | 0 | 8.9706 |
| `downstream_constriction` | `upper_edge` | 2 | 0.112871 / 0.147246 | 1.32491 / 1.67253 | -0.787197 / 1.01052 | 1.71225 / 2.17632 | -0.981308 / 1.25801 | 0.225743 | 0 | 8.7053 |
| `recovery` | `upper_edge` | 8 | 0.724011 / 1.11472 | 1.24864 / 2.16729 | 0.373067 / 1.56232 | 1.50297 / 1.92141 | -0.215077 / 0.797185 | 5.79209 | 0 | 8.66916 |
| `upstream_approach` | `interior` | 54 | -0.141386 / 0.400213 | 0.601066 / 1.24294 | -0.144593 / 0.813777 | 0.884042 / 2.1417 | -0.229101 / 1.41792 | -7.63484 | 0 | 8.5668 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 2.13443 / 2.13443 | -1.26926 / 1.26926 | 0.47367 / 0.47367 | -0.207283 / 0.207283 | 0.0651685 | 0 | 8.5377 |
| `constriction_throat` | `upper_edge` | 2 | 0.755803 / 0.780622 | 0.148778 / 0.232725 | -0.382297 / 2.09945 | 2.01895 / 2.07084 | -0.861863 / 1.26651 | 1.51161 | 0 | 8.39779 |
| `upstream_approach` | `lower_shelf` | 12 | -0.234907 / 0.647319 | -0.452418 / 1.99585 | 0.0087035 / 2.09818 | -0.483031 / 1.23308 | -0.249213 / 1.17735 | -2.81889 | 0 | 8.39272 |
| `constriction_throat` | `lower_shelf` | 4 | 0.280961 / 0.745321 | 0.103568 / 0.210905 | -0.371794 / 1.719 | 0.809489 / 2.07022 | -0.103636 / 0.338007 | 1.12385 | 0 | 8.2809 |
| `downstream_constriction` | `interior` | 8 | 0.104356 / 0.227108 | -1.0562 / 1.61526 | -1.03468 / 1.29792 | -1.13488 / 2.04033 | -1.29629 / 1.64778 | 0.834849 | 0 | 8.16134 |
| `recovery` | `lower_edge` | 6 | 0.0332911 / 0.210057 | 0.501543 / 1.52858 | 0.033676 / 0.228086 | 0.612738 / 1.77353 | 0.0525296 / 0.308866 | 0.199747 | 0 | 7.09411 |
| `upstream_approach` | `upper_shelf` | 18 | -0.157933 / 0.678357 | -0.200189 / 1.68853 | 0.128259 / 1.60579 | -0.431871 / 1.3255 | 0.164542 / 0.832526 | -2.8428 | 0.0555556 | 6.75413 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `upstream_approach` | `upper_edge` | `9,2` | 2 | 3.5 | 1.14879 | 3.46472 | 2.31593 | 2.31593 | 0.25 | 9.26373 |
| `u` | `recovery` | `interior` | `3,17` | 17 | -2.5 | 0.179527 | 2.42218 | 2.24265 | 2.24265 | 0.25 | 8.9706 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 1.64304 | -2.19147 | 2.19147 | 0.25 | 8.76588 |
| `hu` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.185349 | 1.99098 | 2.17632 | 2.17632 | 0.25 | 8.7053 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 2.05192 | 2.16729 | 2.16729 | 0.25 | 8.66916 |
| `u` | `recovery` | `upper_edge` | `9,17` | 17 | 3.5 | 0.234362 | 2.4001 | 2.16574 | 2.16574 | 0.25 | 8.66295 |
| `hu` | `upstream_approach` | `interior` | `5,2` | 2 | -0.5 | -0.0269994 | 2.1147 | 2.1417 | 2.1417 | 0.25 | 8.5668 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 2.19728 | 2.13443 | 2.13443 | 0.25 | 8.5377 |
| `v` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 1.14159 | -0.957854 | -2.09945 | 2.09945 | 0.25 | 8.39779 |
| `v` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.45712 | 1.35894 | -2.09818 | 2.09818 | 0.25 | 8.39272 |
| `hu` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 3.75007 | 1.6571 | -2.09296 | 2.09296 | 0.25 | 8.37185 |
| `hu` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | 0.889107 | 2.95994 | 2.07084 | 2.07084 | 0.25 | 8.28335 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 2.77187 | 2.07022 | 2.07022 | 0.25 | 8.2809 |
| `u` | `recovery` | `interior` | `8,17` | 17 | 2.5 | 0.350557 | 2.40895 | 2.05839 | 2.05839 | 0.25 | 8.23357 |
| `hu` | `recovery` | `interior` | `5,20` | 20 | -0.5 | 3.83038 | 1.78339 | -2.04698 | 2.04698 | 0.25 | 8.18793 |
| `u` | `recovery` | `upper_edge` | `8,16` | 16 | 2.5 | 0.137262 | 2.17993 | 2.04266 | 2.04266 | 0.25 | 8.17066 |

## Blocked Reasons

- Final-frame `hu` field remains 9.26x over threshold at `upstream_approach/upper_edge` cell 9,2.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `1.11472` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/upper_edge` (max u/hu delta `1.72081`/`2.31593`).
- Cross-stream shear/momentum mismatch is still active in `constriction_throat/upper_edge` (max v/hv delta `2.09945`/`1.26651`).

## Next Levers

- Start with `upstream_approach/upper_edge` cell 9,2; `hu` delta is `2.31593` with reference h `0.327768` m and C++ h `1.37696` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
