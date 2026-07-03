# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_lower_shelf_depth_momentum_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_lower_shelf_depth_momentum_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.552267`
- Max h/u/v/hu/hv delta: `0.466456` / `0.550955` / `0.502471` / `0.552267` / `0.549948`
- Max profile mass delta: `4.6392` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.102651 / 0.410862 | -0.150126 / 0.463802 | 0.104562 / 0.552267 | -0.125319 / 0.52695 | 0.809547 | 0 | 2.20907 |
| `upstream_approach` | `upper_edge` | 10 | 0.0111954 / 0.159496 | -0.209572 / 0.550955 | 0.0774136 / 0.254659 | -0.0389702 / 0.452691 | -0.0172247 / 0.412882 | 0.111954 | 0 | 2.20382 |
| `recovery` | `interior` | 46 | 0.100852 / 0.376764 | -0.0843054 / 0.550763 | 0.0249749 / 0.37979 | 0.0786438 / 0.532979 | 0.0494944 / 0.508163 | 4.6392 | 0 | 2.20305 |
| `upstream_approach` | `interior` | 54 | -0.0450389 / 0.466456 | 0.056693 / 0.461626 | -0.0448257 / 0.502471 | 0.0860492 / 0.533837 | -0.0993226 / 0.549948 | -2.4321 | 0 | 2.19979 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0621087 / 0.42951 | 0.0463075 / 0.286296 | 0.0328033 / 0.544494 | 0.0627319 / 0.489749 | -0.709597 | 0 | 2.17797 |
| `upstream_approach` | `upper_shelf` | 18 | -0.0122377 / 0.139176 | -0.128632 / 0.502464 | -0.0255148 / 0.300528 | -0.0628628 / 0.442833 | 0.00914678 / 0.272495 | -0.220279 | 0.0555556 | 2.00986 |
| `upstream_approach` | `lower_shelf` | 12 | -0.0680165 / 0.40319 | -0.0077522 / 0.324043 | 0.00579123 / 0.481163 | -0.00258799 / 0.323404 | -0.0247756 / 0.294638 | -0.816198 | 0 | 1.92465 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0926512 / 0.387147 | 0.146691 / 0.306653 | 0.098028 / 0.456117 | 0.20507 / 0.412687 | 0.208015 | 0 | 1.82447 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | 0.0369647 / 0.257488 | 0.0467912 / 0.247685 | 0.251705 / 0.455718 | 0.0773332 / 0.37973 | 0.481471 | 0 | 1.82287 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.149524 / 0.30557 | 0.178911 / 0.286263 | 0.202827 / 0.350132 | 0.267166 / 0.440334 | -0.0500269 | 0 | 1.76134 |
| `recovery` | `upper_edge` | 8 | 0.113578 / 0.355242 | -0.00938194 / 0.279153 | 0.0320627 / 0.239044 | 0.0427882 / 0.124942 | -0.0928032 / 0.18549 | 0.908621 | 0 | 1.42097 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `downstream_constriction` | `interior` | `7,14` | 14 | 1.5 | 1.22494 | 1.77721 | 0.552267 | 0.552267 | 0.25 | 2.20907 |
| `u` | `upstream_approach` | `upper_edge` | `9,1` | 1 | 3.5 | 3.43843 | 2.88747 | -0.550955 | 0.550955 | 0.25 | 2.20382 |
| `u` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 2.91578 | 2.36502 | -0.550763 | 0.550763 | 0.25 | 2.20305 |
| `hv` | `upstream_approach` | `interior` | `5,4` | 4 | -0.5 | 0.125899 | -0.424048 | -0.549948 | 0.549948 | 0.25 | 2.19979 |
| `hv` | `upstream_approach` | `interior` | `8,4` | 4 | 2.5 | -0.38081 | -0.930519 | -0.549709 | 0.549709 | 0.25 | 2.19884 |
| `hu` | `upstream_approach` | `lower_edge` | `2,4` | 4 | -3.5 | 1.86526 | 2.40976 | 0.544494 | 0.544494 | 0.25 | 2.17797 |
| `u` | `recovery` | `interior` | `4,19` | 19 | -1.5 | 2.89388 | 2.35636 | -0.537514 | 0.537514 | 0.25 | 2.15006 |
| `hu` | `upstream_approach` | `interior` | `3,6` | 6 | -2.5 | 1.36476 | 1.8986 | 0.533837 | 0.533837 | 0.25 | 2.13535 |
| `hu` | `recovery` | `interior` | `5,23` | 23 | -0.5 | 3.25221 | 2.71923 | -0.532979 | 0.532979 | 0.25 | 2.13192 |
| `hv` | `downstream_constriction` | `interior` | `6,14` | 14 | 0.5 | 0.965359 | 0.438408 | -0.52695 | 0.52695 | 0.25 | 2.1078 |
| `hu` | `upstream_approach` | `interior` | `6,2` | 2 | 0.5 | 0.266706 | 0.793014 | 0.526308 | 0.526308 | 0.25 | 2.10523 |
| `u` | `recovery` | `interior` | `7,19` | 19 | 1.5 | 1.81784 | 1.29607 | -0.52177 | 0.52177 | 0.25 | 2.08708 |
| `hv` | `upstream_approach` | `interior` | `8,3` | 3 | 2.5 | -0.396559 | -0.907005 | -0.510446 | 0.510446 | 0.25 | 2.04178 |
| `hv` | `recovery` | `interior` | `5,20` | 20 | -0.5 | 0.0756 | 0.583763 | 0.508163 | 0.508163 | 0.25 | 2.03265 |
| `v` | `upstream_approach` | `interior` | `7,9` | 9 | 1.5 | -1.42932 | -0.926849 | 0.502471 | 0.502471 | 0.25 | 2.00988 |
| `u` | `upstream_approach` | `upper_shelf` | `10,2` | 2 | 4.5 | 3.28259 | 2.78012 | -0.502464 | 0.502464 | 0.25 | 2.00986 |

## Blocked Reasons

- Final-frame `hu` field remains 2.21x over threshold at `downstream_constriction/interior` cell 7,14.
- Depth/profile mismatch is still active in `upstream_approach/interior` (max h delta `0.466456` m).
- Streamwise shear/momentum mismatch is still active in `downstream_constriction/interior` (max u/hu delta `0.410862`/`0.552267`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/interior` (max v/hv delta `0.502471`/`0.549948`).

## Next Levers

- Start with `downstream_constriction/interior` cell 7,14; `hu` delta is `0.552267` with reference h `1.11836` m and C++ h `1.33955` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
