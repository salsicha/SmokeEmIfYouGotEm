# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_upper_interior_streamwise_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_upper_interior_streamwise_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.428216`
- Max h/u/v/hu/hv delta: `0.355242` / `0.410862` / `0.402237` / `0.428216` / `0.412687`
- Max profile mass delta: `4.35758` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | 0.0152946 / 0.257488 | 0.0467912 / 0.247685 | 0.221008 / 0.428216 | 0.0773332 / 0.37973 | 0.481471 | 0 | 1.71286 |
| `upstream_approach` | `interior` | 54 | -0.0472677 / 0.263487 | 0.0257762 / 0.26848 | -0.0342043 / 0.259132 | 0.0251212 / 0.420063 | -0.0662284 / 0.400549 | -2.55245 | 0 | 1.68025 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0281762 / 0.197679 | 0.146691 / 0.306653 | 0.023389 / 0.222921 | 0.20507 / 0.412687 | 0.208015 | 0 | 1.65075 |
| `recovery` | `interior` | 46 | 0.09473 / 0.340402 | -0.0642755 / 0.309551 | -0.0107176 / 0.278258 | 0.097621 / 0.411457 | -0.00546702 / 0.349635 | 4.35758 | 0 | 1.64583 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.131509 / 0.410862 | -0.107961 / 0.285449 | 0.0659062 / 0.360888 | -0.0765761 / 0.286294 | 0.809547 | 0 | 1.64345 |
| `upstream_approach` | `upper_edge` | 10 | 0.0111988 / 0.159496 | -0.127704 / 0.405134 | 0.0359169 / 0.254659 | -0.00494173 / 0.323998 | -0.0259527 / 0.228382 | 0.111988 | 0 | 1.62054 |
| `upstream_approach` | `lower_shelf` | 12 | -0.0345226 / 0.293742 | -0.00878871 / 0.324043 | 0.0469043 / 0.402237 | 0.0108789 / 0.323404 | -0.00376502 / 0.294638 | -0.414271 | 0 | 1.60895 |
| `upstream_approach` | `upper_shelf` | 18 | -0.0122372 / 0.0899976 | -0.0884109 / 0.389058 | -0.0231396 / 0.300528 | -0.0462422 / 0.291333 | 0.0158199 / 0.272483 | -0.22027 | 0.0555556 | 1.55623 |
| `recovery` | `upper_edge` | 8 | 0.113578 / 0.355242 | -0.00938194 / 0.279153 | 0.0320627 / 0.239044 | 0.0427882 / 0.124942 | -0.0928032 / 0.18549 | 0.908621 | 0 | 1.42097 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.149524 / 0.30557 | 0.107269 / 0.196049 | 0.202827 / 0.350132 | 0.156857 / 0.312878 | -0.0500269 | 0 | 1.40053 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |
| `constriction_throat` | `upper_edge` | 2 | 0.105621 / 0.121761 | -0.00211336 / 0.00647273 | -0.0594552 / 0.103293 | 0.256167 / 0.28181 | -0.128521 / 0.322086 | 0.211242 | 0 | 1.28834 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `constriction_throat` | `interior` | `5,11` | 11 | -0.5 | 4.23942 | 4.66763 | 0.428216 | 0.428216 | 0.25 | 1.71286 |
| `hu` | `upstream_approach` | `interior` | `6,9` | 9 | 0.5 | 3.20714 | 2.78708 | -0.420063 | 0.420063 | 0.25 | 1.68025 |
| `hv` | `recovery` | `lower_edge` | `2,22` | 22 | -3.5 | -0.28061 | 0.132077 | 0.412687 | 0.412687 | 0.25 | 1.65075 |
| `hu` | `recovery` | `interior` | `6,20` | 20 | 0.5 | 3.73165 | 4.14311 | 0.411457 | 0.411457 | 0.25 | 1.64583 |
| `u` | `downstream_constriction` | `interior` | `5,15` | 15 | -0.5 | 3.14455 | 2.73369 | -0.410862 | 0.410862 | 0.25 | 1.64345 |
| `u` | `upstream_approach` | `upper_edge` | `9,3` | 3 | 3.5 | 3.41154 | 3.00641 | -0.405134 | 0.405134 | 0.25 | 1.62054 |
| `v` | `upstream_approach` | `lower_shelf` | `0,1` | 1 | -5.5 | 0.846449 | 1.24869 | 0.402237 | 0.402237 | 0.25 | 1.60895 |
| `hv` | `upstream_approach` | `interior` | `8,1` | 1 | 2.5 | -1.18716 | -1.58771 | -0.400549 | 0.400549 | 0.25 | 1.6022 |
| `hu` | `upstream_approach` | `interior` | `5,2` | 2 | -0.5 | -0.0269994 | 0.372788 | 0.399788 | 0.399788 | 0.25 | 1.59915 |
| `hu` | `upstream_approach` | `interior` | `5,9` | 9 | -0.5 | 3.4075 | 3.00976 | -0.397734 | 0.397734 | 0.25 | 1.59094 |
| `u` | `upstream_approach` | `upper_edge` | `9,5` | 5 | 3.5 | 3.39654 | 3.00692 | -0.389623 | 0.389623 | 0.25 | 1.55849 |
| `u` | `upstream_approach` | `upper_shelf` | `10,4` | 4 | 4.5 | 3.0443 | 2.65524 | -0.389058 | 0.389058 | 0.25 | 1.55623 |
| `hu` | `upstream_approach` | `interior` | `6,3` | 3 | 0.5 | 0.533641 | 0.922287 | 0.388646 | 0.388646 | 0.25 | 1.55458 |
| `u` | `upstream_approach` | `upper_shelf` | `10,5` | 5 | 4.5 | 2.82416 | 2.43661 | -0.387542 | 0.387542 | 0.25 | 1.55017 |
| `hv` | `upstream_approach` | `interior` | `3,0` | 0 | -2.5 | 0.440979 | 0.0540921 | -0.386887 | 0.386887 | 0.25 | 1.54755 |
| `hu` | `upstream_approach` | `interior` | `8,3` | 3 | 2.5 | 2.87954 | 2.4962 | -0.383335 | 0.383335 | 0.25 | 1.53334 |

## Blocked Reasons

- Final-frame `hu` field remains 1.71x over threshold at `constriction_throat/interior` cell 5,11.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `0.355242` m).
- Streamwise shear/momentum mismatch is still active in `constriction_throat/interior` (max u/hu delta `0.257488`/`0.428216`).
- Cross-stream shear/momentum mismatch is still active in `recovery/lower_edge` (max v/hv delta `0.306653`/`0.412687`).

## Next Levers

- Start with `constriction_throat/interior` cell 5,11; `hu` delta is `0.428216` with reference h `1.52828` m and C++ h `1.53972` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
