# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_throat_middle_interior_cross_stream_balance_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_throat_middle_interior_cross_stream_balance_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.37965`
- Max h/u/v/hu/hv delta: `0.355242` / `0.353905` / `0.33579` / `0.361214` / `0.37965`
- Max profile mass delta: `4.35758` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `interior` | 54 | -0.0472677 / 0.263487 | 0.0328676 / 0.254233 | -0.023475 / 0.220581 | 0.0371391 / 0.339519 | -0.0478692 / 0.37965 | -2.55245 | 0 | 1.5186 |
| `recovery` | `interior` | 46 | 0.09473 / 0.340402 | -0.0694028 / 0.309551 | -0.015338 / 0.278258 | 0.0899629 / 0.361214 | -0.012368 / 0.349635 | 4.35758 | 0 | 1.44485 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.107501 / 0.353905 | -0.107961 / 0.285449 | 0.0992171 / 0.360888 | -0.0765761 / 0.286294 | 0.809547 | 0 | 1.44355 |
| `recovery` | `upper_edge` | 8 | 0.113578 / 0.355242 | -0.00938194 / 0.279153 | 0.0320627 / 0.239044 | 0.0427882 / 0.124942 | -0.0928032 / 0.18549 | 0.908621 | 0 | 1.42097 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.149524 / 0.30557 | 0.107269 / 0.196049 | 0.202827 / 0.350132 | 0.156857 / 0.312878 | -0.0500269 | 0 | 1.40053 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | -0.0168364 / 0.150006 | 0.0158585 / 0.0774815 | 0.171535 / 0.340909 | 0.0297054 / 0.125431 | 0.481471 | 0 | 1.36364 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |
| `upstream_approach` | `lower_shelf` | 12 | -0.0345226 / 0.293742 | -0.00878871 / 0.324043 | 0.0133891 / 0.221148 | 0.0108789 / 0.323404 | -0.0136829 / 0.294638 | -0.414271 | 0 | 1.29617 |
| `constriction_throat` | `upper_edge` | 2 | 0.105621 / 0.121761 | -0.00211336 / 0.00647273 | -0.0594552 / 0.103293 | 0.256167 / 0.28181 | -0.128521 / 0.322086 | 0.211242 | 0 | 1.28834 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0192081 / 0.181599 | -0.0107517 / 0.173703 | -0.0380703 / 0.231657 | -0.0321846 / 0.28896 | -0.709597 | 0 | 1.23997 |
| `upstream_approach` | `upper_shelf` | 18 | -0.00913431 / 0.0899976 | -0.0443429 / 0.270835 | -0.0100128 / 0.300528 | -0.0272571 / 0.291333 | 0.0169122 / 0.272483 | -0.164418 | 0.0555556 | 1.20211 |
| `upstream_approach` | `upper_edge` | 10 | 0.00561358 / 0.103644 | -0.0774046 / 0.262286 | 0.0102379 / 0.105336 | 0.000946168 / 0.237098 | -0.0270507 / 0.239362 | 0.0561358 | 0 | 1.04915 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hv` | `upstream_approach` | `interior` | `5,3` | 3 | -0.5 | 0.0515802 | -0.32807 | -0.37965 | 0.37965 | 0.25 | 1.5186 |
| `hu` | `recovery` | `interior` | `6,18` | 18 | 0.5 | 3.72586 | 4.08707 | 0.361214 | 0.361214 | 0.25 | 1.44485 |
| `hu` | `downstream_constriction` | `interior` | `5,14` | 14 | -0.5 | 4.19804 | 4.55893 | 0.360888 | 0.360888 | 0.25 | 1.44355 |
| `hv` | `upstream_approach` | `interior` | `5,5` | 5 | -0.5 | -0.064195 | -0.422441 | -0.358246 | 0.358246 | 0.25 | 1.43298 |
| `h` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | 0.217616 | 0.572857 | 0.355242 | 0.355242 | 0.25 | 1.42097 |
| `u` | `downstream_constriction` | `interior` | `4,15` | 15 | -1.5 | 3.1188 | 2.76489 | -0.353905 | 0.353905 | 0.25 | 1.41562 |
| `hu` | `constriction_throat` | `lower_edge` | `4,11` | 11 | -1.5 | 4.12013 | 4.47026 | 0.350132 | 0.350132 | 0.25 | 1.40053 |
| `hu` | `downstream_constriction` | `interior` | `4,14` | 14 | -1.5 | 4.10354 | 4.45343 | 0.349886 | 0.349886 | 0.25 | 1.39954 |
| `hv` | `recovery` | `interior` | `7,21` | 21 | 1.5 | 0.156071 | -0.193564 | -0.349635 | 0.349635 | 0.25 | 1.39854 |
| `hu` | `constriction_throat` | `lower_edge` | `4,10` | 10 | -1.5 | 3.78946 | 4.13194 | 0.342481 | 0.342481 | 0.25 | 1.36992 |
| `hu` | `constriction_throat` | `interior` | `6,12` | 12 | 0.5 | 3.95219 | 4.2931 | 0.340909 | 0.340909 | 0.25 | 1.36364 |
| `h` | `recovery` | `interior` | `8,20` | 20 | 2.5 | 1.40312 | 1.74352 | 0.340402 | 0.340402 | 0.25 | 1.36161 |
| `hu` | `upstream_approach` | `interior` | `7,3` | 3 | 1.5 | 1.81754 | 1.47802 | -0.339519 | 0.339519 | 0.25 | 1.35808 |
| `hu` | `upstream_approach` | `interior` | `4,9` | 9 | -1.5 | 3.37615 | 3.03746 | -0.338689 | 0.338689 | 0.25 | 1.35476 |
| `hv` | `recovery` | `interior` | `3,21` | 21 | -2.5 | -0.42448 | -0.0865693 | 0.33791 | 0.33791 | 0.25 | 1.35164 |
| `hu` | `recovery` | `interior` | `7,16` | 16 | 1.5 | 2.07175 | 2.40816 | 0.336402 | 0.336402 | 0.25 | 1.34561 |

## Blocked Reasons

- Final-frame `hv` field remains 1.52x over threshold at `upstream_approach/interior` cell 5,3.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `0.355242` m).
- Streamwise shear/momentum mismatch is still active in `recovery/interior` (max u/hu delta `0.309551`/`0.361214`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/interior` (max v/hv delta `0.220581`/`0.37965`).

## Next Levers

- Start with `upstream_approach/interior` cell 5,3; `hv` delta is `-0.37965` with reference h `1.81583` m and C++ h `1.73159` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
