# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_throat_lower_edge_streamwise_relief_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_throat_lower_edge_streamwise_relief_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.349635`
- Max h/u/v/hu/hv delta: `0.340402` / `0.329199` / `0.33579` / `0.342481` / `0.349635`
- Max profile mass delta: `4.48044` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `recovery` | `interior` | 46 | 0.0974008 / 0.340402 | -0.0728419 / 0.309551 | -0.0154389 / 0.278258 | 0.0872434 / 0.336402 | -0.0115977 / 0.349635 | 4.48044 | 0 | 1.39854 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.0726396 / 0.240816 | 0.107269 / 0.196049 | 0.0844461 / 0.342481 | 0.156857 / 0.312878 | -0.0500269 | 0 | 1.36992 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | -0.0168364 / 0.150006 | 0.0158585 / 0.0774815 | 0.171535 / 0.340909 | 0.0297054 / 0.125431 | 0.481471 | 0 | 1.36364 |
| `upstream_approach` | `interior` | 54 | -0.0472677 / 0.263487 | 0.0328676 / 0.254233 | -0.0153606 / 0.177068 | 0.0371391 / 0.339519 | -0.034126 / 0.289765 | -2.55245 | 0 | 1.35808 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.104128 / 0.329199 | -0.107961 / 0.285449 | 0.103474 / 0.248846 | -0.0765761 / 0.286294 | 0.809547 | 0 | 1.3168 |
| `upstream_approach` | `lower_shelf` | 12 | -0.0345226 / 0.293742 | -0.00878871 / 0.324043 | 0.0133891 / 0.221148 | 0.0108789 / 0.323404 | -0.0136829 / 0.294638 | -0.414271 | 0 | 1.29617 |
| `constriction_throat` | `upper_edge` | 2 | 0.105621 / 0.121761 | -0.00211336 / 0.00647273 | -0.0594552 / 0.103293 | 0.256167 / 0.28181 | -0.128521 / 0.322086 | 0.211242 | 0 | 1.28834 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0192081 / 0.181599 | -0.0107517 / 0.173703 | -0.0380703 / 0.231657 | -0.0321846 / 0.28896 | -0.709597 | 0 | 1.23997 |
| `upstream_approach` | `upper_shelf` | 18 | -0.00913431 / 0.0899976 | -0.0443429 / 0.270835 | -0.0100128 / 0.300528 | -0.0272571 / 0.291333 | 0.0169122 / 0.272483 | -0.164418 | 0.0555556 | 1.20211 |
| `recovery` | `upper_edge` | 8 | 0.0982205 / 0.232384 | -0.00938194 / 0.279153 | 0.0320627 / 0.239044 | 0.0445599 / 0.124942 | -0.0869955 / 0.18549 | 0.785764 | 0 | 1.11661 |
| `upstream_approach` | `upper_edge` | 10 | 0.00561358 / 0.103644 | -0.0774046 / 0.262286 | 0.0102379 / 0.105336 | 0.000946168 / 0.237098 | -0.0270507 / 0.239362 | 0.0561358 | 0 | 1.04915 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hv` | `recovery` | `interior` | `7,21` | 21 | 1.5 | 0.156071 | -0.193564 | -0.349635 | 0.349635 | 0.25 | 1.39854 |
| `hu` | `constriction_throat` | `lower_edge` | `4,10` | 10 | -1.5 | 3.78946 | 4.13194 | 0.342481 | 0.342481 | 0.25 | 1.36992 |
| `hu` | `constriction_throat` | `interior` | `6,12` | 12 | 0.5 | 3.95219 | 4.2931 | 0.340909 | 0.340909 | 0.25 | 1.36364 |
| `h` | `recovery` | `interior` | `8,20` | 20 | 2.5 | 1.40312 | 1.74352 | 0.340402 | 0.340402 | 0.25 | 1.36161 |
| `hu` | `upstream_approach` | `interior` | `7,3` | 3 | 1.5 | 1.81754 | 1.47802 | -0.339519 | 0.339519 | 0.25 | 1.35808 |
| `hu` | `upstream_approach` | `interior` | `4,9` | 9 | -1.5 | 3.37615 | 3.03746 | -0.338689 | 0.338689 | 0.25 | 1.35476 |
| `hv` | `recovery` | `interior` | `3,21` | 21 | -2.5 | -0.42448 | -0.0865693 | 0.33791 | 0.33791 | 0.25 | 1.35164 |
| `hu` | `recovery` | `interior` | `7,16` | 16 | 1.5 | 2.07175 | 2.40816 | 0.336402 | 0.336402 | 0.25 | 1.34561 |
| `v` | `constriction_throat` | `lower_shelf` | `3,11` | 11 | -2.5 | 0.693877 | 1.02967 | 0.33579 | 0.33579 | 0.25 | 1.34316 |
| `hu` | `constriction_throat` | `interior` | `5,10` | 10 | -0.5 | 3.88779 | 4.2206 | 0.332812 | 0.332812 | 0.25 | 1.33125 |
| `u` | `downstream_constriction` | `interior` | `6,15` | 15 | 0.5 | 3.03794 | 2.70874 | -0.329199 | 0.329199 | 0.25 | 1.3168 |
| `u` | `upstream_approach` | `lower_shelf` | `0,2` | 2 | -5.5 | 3.28259 | 2.95854 | -0.324043 | 0.324043 | 0.25 | 1.29617 |
| `hu` | `upstream_approach` | `lower_shelf` | `0,2` | 2 | -5.5 | 0.56416 | 0.887563 | 0.323404 | 0.323404 | 0.25 | 1.29361 |
| `hv` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | -0.995196 | -1.31728 | -0.322086 | 0.322086 | 0.25 | 1.28834 |
| `hu` | `upstream_approach` | `interior` | `4,2` | 2 | -1.5 | 0.544031 | 0.85827 | 0.314239 | 0.314239 | 0.25 | 1.25696 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 4.14779 | 0.313287 | 0.313287 | 0.25 | 1.25315 |

## Blocked Reasons

- Final-frame `hv` field remains 1.40x over threshold at `recovery/interior` cell 7,21.
- Depth/profile mismatch is still active in `recovery/interior` (max h delta `0.340402` m).
- Streamwise shear/momentum mismatch is still active in `constriction_throat/lower_edge` (max u/hu delta `0.240816`/`0.342481`).
- Cross-stream shear/momentum mismatch is still active in `recovery/interior` (max v/hv delta `0.278258`/`0.349635`).

## Next Levers

- Start with `recovery/interior` cell 7,21; `hv` delta is `-0.349635` with reference h `1.42421` m and C++ h `1.46453` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
