# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_final_lower_edge_shear_narrow/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_final_lower_edge_shear_narrow/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `2.70432`
- Max h/u/v/hu/hv delta: `1.13531` / `2.70432` / `2.48586` / `2.5603` / `1.73887`
- Max profile mass delta: `7.03794` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `lower_shelf` | 12 | -0.233009 / 0.647162 | -0.914257 / 2.70432 | -0.378136 / 2.48586 | -0.57718 / 1.29439 | -0.336008 / 1.29202 | -2.79611 | 0 | 10.8173 |
| `constriction_throat` | `upper_edge` | 2 | 0.921373 / 0.939111 | 0.21459 / 0.298576 | -0.374711 / 2.26205 | 2.5325 / 2.5603 | -1.02087 / 1.62268 | 1.84275 | 0 | 10.2412 |
| `downstream_constriction` | `upper_edge` | 2 | 0.130176 / 0.163934 | 1.64057 / 1.93427 | -0.78832 / 1.01179 | 2.14771 / 2.5502 | -0.990017 / 1.26891 | 0.260352 | 0 | 10.2008 |
| `constriction_throat` | `lower_shelf` | 4 | 0.363975 / 0.917973 | 0.0943592 / 0.210905 | -0.372092 / 1.71999 | 1.0204 / 2.50502 | -0.0955261 / 0.315762 | 1.4559 | 0 | 10.0201 |
| `upstream_approach` | `upper_edge` | 10 | 0.671929 / 1.09425 | -0.746205 / 1.73254 | 0.989752 / 2.47139 | 1.14519 / 1.94861 | -0.398188 / 0.779505 | 6.71929 | 0 | 9.88556 |
| `recovery` | `interior` | 46 | -0.0205058 / 0.334141 | -0.187924 / 2.2316 | -0.17978 / 0.915515 | -0.356235 / 2.15914 | -0.223265 / 1.11438 | -0.943268 | 0 | 8.9264 |
| `recovery` | `upper_edge` | 8 | 0.75556 / 1.13531 | 1.24604 / 2.15576 | 0.371308 / 1.5623 | 1.56129 / 2.14021 | -0.220807 / 0.802884 | 6.04448 | 0 | 8.62303 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 2.12425 / 2.12425 | -1.27063 / 1.27063 | 0.471432 / 0.471432 | -0.207584 / 0.207584 | 0.0651685 | 0 | 8.49701 |
| `upstream_approach` | `interior` | 54 | -0.130332 / 0.410239 | 0.541215 / 1.20886 | -0.158479 / 0.802149 | 0.802385 / 2.10381 | -0.256742 / 1.42345 | -7.03794 | 0 | 8.41525 |
| `upstream_approach` | `upper_shelf` | 18 | -0.160996 / 0.687788 | -0.515051 / 1.89201 | 0.223683 / 2.04414 | -0.502354 / 1.56197 | 0.187979 / 0.831394 | -2.89792 | 0.0555556 | 8.17657 |
| `downstream_constriction` | `interior` | 8 | 0.121682 / 0.243295 | -1.06069 / 1.61933 | -1.03582 / 1.29872 | -1.11194 / 2.01874 | -1.304 / 1.6578 | 0.973458 | 0 | 8.07497 |
| `recovery` | `lower_edge` | 6 | 0.0505631 / 0.229415 | 0.501057 / 1.51034 | 0.0324371 / 0.227827 | 0.625201 / 1.79672 | 0.0520882 / 0.308748 | 0.303378 | 0 | 7.18686 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `u` | `upstream_approach` | `lower_shelf` | `0,1` | 1 | -5.5 | 3.63205 | 0.927726 | -2.70432 | 2.70432 | 0.25 | 10.8173 |
| `hu` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | 0.889107 | 3.4494 | 2.5603 | 2.5603 | 0.25 | 10.2412 |
| `hu` | `downstream_constriction` | `upper_edge` | `8,14` | 14 | 2.5 | -0.185349 | 2.36485 | 2.5502 | 2.5502 | 0.25 | 10.2008 |
| `hu` | `constriction_throat` | `lower_shelf` | `3,13` | 13 | -2.5 | 0.701648 | 3.20667 | 2.50502 | 2.50502 | 0.25 | 10.0201 |
| `hu` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 0.701957 | 3.20667 | 2.50471 | 2.50471 | 0.25 | 10.0188 |
| `v` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.45712 | 0.971261 | -2.48586 | 2.48586 | 0.25 | 9.94345 |
| `v` | `upstream_approach` | `upper_edge` | `9,1` | 1 | 3.5 | -3.72743 | -1.25604 | 2.47139 | 2.47139 | 0.25 | 9.88556 |
| `u` | `upstream_approach` | `lower_shelf` | `1,7` | 7 | -4.5 | -0.525053 | 1.91405 | 2.43911 | 2.43911 | 0.25 | 9.75642 |
| `u` | `upstream_approach` | `lower_shelf` | `0,2` | 2 | -5.5 | 3.28259 | 0.929667 | -2.35292 | 2.35292 | 0.25 | 9.41168 |
| `v` | `constriction_throat` | `upper_edge` | `7,13` | 13 | 1.5 | 1.14159 | -1.12046 | -2.26205 | 2.26205 | 0.25 | 9.04821 |
| `u` | `recovery` | `interior` | `3,17` | 17 | -2.5 | 0.179527 | 2.41113 | 2.2316 | 2.2316 | 0.25 | 8.9264 |
| `u` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.85418 | 1.65117 | -2.203 | 2.203 | 0.25 | 8.81202 |
| `u` | `upstream_approach` | `lower_shelf` | `1,3` | 3 | -4.5 | 3.49092 | 1.29596 | -2.19496 | 2.19496 | 0.25 | 8.77984 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 1.67537 | -2.15914 | 2.15914 | 0.25 | 8.63655 |
| `u` | `recovery` | `upper_edge` | `9,17` | 17 | 3.5 | 0.234362 | 2.39012 | 2.15576 | 2.15576 | 0.25 | 8.62303 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 2.033 | 2.14837 | 2.14837 | 0.25 | 8.5935 |

## Blocked Reasons

- Final-frame `u` field remains 10.82x over threshold at `upstream_approach/lower_shelf` cell 0,1.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `1.13531` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max u/hu delta `2.70432`/`1.29439`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `2.48586`/`1.29202`).

## Next Levers

- Start with `upstream_approach/lower_shelf` cell 0,1; `u` delta is `-2.70432` with reference h `0.258901` m and C++ h `0.186` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
