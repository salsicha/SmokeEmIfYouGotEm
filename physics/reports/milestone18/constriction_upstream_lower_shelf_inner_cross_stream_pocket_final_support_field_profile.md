# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_lower_shelf_inner_cross_stream_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_lower_shelf_inner_cross_stream_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.655706`
- Max h/u/v/hu/hv delta: `0.655706` / `0.654883` / `0.651338` / `0.622135` / `0.652559`
- Max profile mass delta: `3.98273` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `recovery` | `upper_edge` | 8 | 0.195636 / 0.655706 | -0.0922976 / 0.654883 | 0.111401 / 0.585144 | 0.0201325 / 0.144237 | -0.0421774 / 0.16439 | 1.56509 | 0 | 2.62283 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0960614 / 0.42951 | -0.0404087 / 0.382857 | 0.0879208 / 0.544494 | -0.0797097 / 0.652559 | -0.709597 | 0 | 2.61024 |
| `upstream_approach` | `lower_shelf` | 12 | -0.080879 / 0.40319 | -0.0610673 / 0.628275 | 0.0856281 / 0.651338 | -0.0563511 / 0.55627 | -0.00791182 / 0.294638 | -0.970548 | 0 | 2.60535 |
| `recovery` | `interior` | 46 | 0.086581 / 0.398864 | -0.0925679 / 0.647627 | 0.0392297 / 0.412192 | 0.0550765 / 0.596372 | 0.0617324 / 0.562798 | 3.98273 | 0 | 2.59051 |
| `upstream_approach` | `upper_shelf` | 18 | -0.0092036 / 0.139176 | -0.167475 / 0.632868 | 0.00736004 / 0.559386 | -0.0721051 / 0.442833 | 0.0127739 / 0.272495 | -0.165665 | 0.0555556 | 2.53147 |
| `upstream_approach` | `interior` | 54 | -0.047536 / 0.466456 | 0.0718932 / 0.480905 | -0.0736635 / 0.502471 | 0.108086 / 0.622135 | -0.147033 / 0.613842 | -2.56694 | 0 | 2.48854 |
| `upstream_approach` | `upper_edge` | 10 | 0.0346531 / 0.382043 | -0.238731 / 0.609377 | 0.0989524 / 0.611694 | 0.0481444 / 0.452691 | -0.15956 / 0.621231 | 0.346531 | 0 | 2.48492 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.102651 / 0.410862 | -0.150126 / 0.463802 | 0.104562 / 0.552267 | -0.125319 / 0.52695 | 0.809547 | 0 | 2.20907 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0926512 / 0.387147 | 0.146691 / 0.306653 | 0.098028 / 0.456117 | 0.20507 / 0.412687 | 0.208015 | 0 | 1.82447 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | 0.0369647 / 0.257488 | 0.0467912 / 0.247685 | 0.251705 / 0.455718 | 0.0773332 / 0.37973 | 0.481471 | 0 | 1.82287 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.149524 / 0.30557 | 0.178911 / 0.286263 | 0.202827 / 0.350132 | 0.267166 / 0.440334 | -0.0500269 | 0 | 1.76134 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `h` | `recovery` | `upper_edge` | `9,19` | 19 | 3.5 | 0.288044 | 0.94375 | 0.655706 | 0.655706 | 0.25 | 2.62283 |
| `u` | `recovery` | `upper_edge` | `9,22` | 22 | 3.5 | 0.885822 | 0.23094 | -0.654883 | 0.654883 | 0.25 | 2.61953 |
| `hv` | `upstream_approach` | `lower_edge` | `2,0` | 0 | -3.5 | 1.70802 | 1.05546 | -0.652559 | 0.652559 | 0.25 | 2.61024 |
| `v` | `upstream_approach` | `lower_shelf` | `0,2` | 2 | -5.5 | 0.677913 | 1.32925 | 0.651338 | 0.651338 | 0.25 | 2.60535 |
| `u` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 2.91578 | 2.26815 | -0.647627 | 0.647627 | 0.25 | 2.59051 |
| `u` | `upstream_approach` | `upper_shelf` | `10,3` | 3 | 4.5 | 3.20029 | 2.56743 | -0.632868 | 0.632868 | 0.25 | 2.53147 |
| `u` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.85418 | 3.2259 | -0.628275 | 0.628275 | 0.25 | 2.5131 |
| `u` | `upstream_approach` | `upper_shelf` | `10,1` | 1 | 4.5 | 3.39685 | 2.77106 | -0.625784 | 0.625784 | 0.25 | 2.50313 |
| `hu` | `upstream_approach` | `interior` | `3,5` | 5 | -2.5 | 1.20058 | 1.82272 | 0.622135 | 0.622135 | 0.25 | 2.48854 |
| `hv` | `upstream_approach` | `upper_edge` | `8,9` | 9 | 2.5 | -1.08285 | -1.70408 | -0.621231 | 0.621231 | 0.25 | 2.48492 |
| `u` | `recovery` | `interior` | `4,19` | 19 | -1.5 | 2.89388 | 2.27335 | -0.620533 | 0.620533 | 0.25 | 2.48213 |
| `hv` | `upstream_approach` | `interior` | `3,3` | 3 | -2.5 | 0.21559 | -0.398253 | -0.613842 | 0.613842 | 0.25 | 2.45537 |
| `v` | `upstream_approach` | `upper_edge` | `9,6` | 6 | 3.5 | -2.31426 | -1.70257 | 0.611694 | 0.611694 | 0.25 | 2.44678 |
| `u` | `upstream_approach` | `upper_edge` | `9,2` | 2 | 3.5 | 3.50488 | 2.8955 | -0.609377 | 0.609377 | 0.25 | 2.43751 |
| `u` | `upstream_approach` | `upper_shelf` | `9,9` | 9 | 3.5 | 0.274161 | 0.874989 | 0.600827 | 0.600827 | 0.25 | 2.40331 |
| `hv` | `upstream_approach` | `interior` | `4,4` | 4 | -1.5 | 0.333128 | -0.266011 | -0.59914 | 0.59914 | 0.25 | 2.39656 |

## Blocked Reasons

- Final-frame `h` field remains 2.62x over threshold at `recovery/upper_edge` cell 9,19.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `0.655706` m).
- Streamwise shear/momentum mismatch is still active in `recovery/upper_edge` (max u/hu delta `0.654883`/`0.144237`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_edge` (max v/hv delta `0.382857`/`0.652559`).

## Next Levers

- Start with `recovery/upper_edge` cell 9,19; `h` delta is `0.655706` with reference h `0.288044` m and C++ h `0.94375` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
