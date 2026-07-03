# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_mid_upper_interior_streamwise_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_mid_upper_interior_streamwise_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.52695`
- Max h/u/v/hu/hv delta: `0.466456` / `0.52177` / `0.502471` / `0.526308` / `0.52695`
- Max profile mass delta: `4.35758` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.131509 / 0.410862 | -0.165998 / 0.463802 | 0.0659062 / 0.360888 | -0.14658 / 0.52695 | 0.809547 | 0 | 2.1078 |
| `upstream_approach` | `interior` | 54 | -0.0398238 / 0.466456 | 0.0481195 / 0.37006 | -0.0327296 / 0.502471 | 0.0761101 / 0.526308 | -0.0754752 / 0.487838 | -2.15048 | 0 | 2.10523 |
| `recovery` | `interior` | 46 | 0.09473 / 0.350468 | -0.0536672 / 0.52177 | 0.0290209 / 0.37979 | 0.106663 / 0.499837 | 0.052841 / 0.508163 | 4.35758 | 0 | 2.08708 |
| `upstream_approach` | `upper_shelf` | 18 | -0.0122377 / 0.139176 | -0.128632 / 0.502464 | -0.0255148 / 0.300528 | -0.0628628 / 0.442833 | 0.00914678 / 0.272495 | -0.220279 | 0.0555556 | 2.00986 |
| `upstream_approach` | `lower_shelf` | 12 | -0.0680165 / 0.40319 | -0.0077522 / 0.324043 | 0.00579123 / 0.481163 | -0.00258799 / 0.323404 | -0.0247756 / 0.294638 | -0.816198 | 0 | 1.92465 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0192081 / 0.181599 | 0.0176677 / 0.283437 | -0.0380703 / 0.231657 | 0.0154178 / 0.468124 | -0.709597 | 0 | 1.8725 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0926512 / 0.387147 | 0.146691 / 0.306653 | 0.098028 / 0.456117 | 0.20507 / 0.412687 | 0.208015 | 0 | 1.82447 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | 0.0369647 / 0.257488 | 0.0467912 / 0.247685 | 0.251705 / 0.455718 | 0.0773332 / 0.37973 | 0.481471 | 0 | 1.82287 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.149524 / 0.30557 | 0.178911 / 0.286263 | 0.202827 / 0.350132 | 0.267166 / 0.440334 | -0.0500269 | 0 | 1.76134 |
| `upstream_approach` | `upper_edge` | 10 | 0.0111954 / 0.159496 | -0.127704 / 0.405134 | 0.0359169 / 0.254659 | -0.00494509 / 0.323998 | -0.0259506 / 0.228382 | 0.111954 | 0 | 1.62054 |
| `recovery` | `upper_edge` | 8 | 0.113578 / 0.355242 | -0.00938194 / 0.279153 | 0.0320627 / 0.239044 | 0.0427882 / 0.124942 | -0.0928032 / 0.18549 | 0.908621 | 0 | 1.42097 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hv` | `downstream_constriction` | `interior` | `6,14` | 14 | 0.5 | 0.965359 | 0.438408 | -0.52695 | 0.52695 | 0.25 | 2.1078 |
| `hu` | `upstream_approach` | `interior` | `6,2` | 2 | 0.5 | 0.266706 | 0.793014 | 0.526308 | 0.526308 | 0.25 | 2.10523 |
| `u` | `recovery` | `interior` | `7,19` | 19 | 1.5 | 1.81784 | 1.29607 | -0.52177 | 0.52177 | 0.25 | 2.08708 |
| `hv` | `recovery` | `interior` | `5,20` | 20 | -0.5 | 0.0756 | 0.583763 | 0.508163 | 0.508163 | 0.25 | 2.03265 |
| `v` | `upstream_approach` | `interior` | `7,9` | 9 | 1.5 | -1.42932 | -0.926849 | 0.502471 | 0.502471 | 0.25 | 2.00988 |
| `u` | `upstream_approach` | `upper_shelf` | `10,2` | 2 | 4.5 | 3.28259 | 2.78012 | -0.502464 | 0.502464 | 0.25 | 2.00986 |
| `hu` | `recovery` | `interior` | `7,23` | 23 | 1.5 | 2.28839 | 2.78822 | 0.499837 | 0.499837 | 0.25 | 1.99935 |
| `hv` | `recovery` | `interior` | `3,20` | 20 | -2.5 | -0.183417 | 0.312223 | 0.49564 | 0.49564 | 0.25 | 1.98256 |
| `hu` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.83451 | 4.32596 | 0.491452 | 0.491452 | 0.25 | 1.96581 |
| `hv` | `upstream_approach` | `interior` | `3,1` | 1 | -2.5 | 0.3193 | -0.168537 | -0.487838 | 0.487838 | 0.25 | 1.95135 |
| `v` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.45712 | 2.97596 | -0.481163 | 0.481163 | 0.25 | 1.92465 |
| `hu` | `upstream_approach` | `interior` | `4,5` | 5 | -1.5 | 0.950301 | 1.42827 | 0.477967 | 0.477967 | 0.25 | 1.91187 |
| `hv` | `recovery` | `interior` | `4,22` | 22 | -1.5 | -0.418139 | 0.0588702 | 0.477009 | 0.477009 | 0.25 | 1.90804 |
| `hv` | `upstream_approach` | `interior` | `8,3` | 3 | 2.5 | -0.396559 | -0.870191 | -0.473632 | 0.473632 | 0.25 | 1.89453 |
| `hv` | `upstream_approach` | `lower_edge` | `2,2` | 2 | -3.5 | 0.239435 | 0.70756 | 0.468124 | 0.468124 | 0.25 | 1.8725 |
| `hv` | `upstream_approach` | `interior` | `7,6` | 6 | 1.5 | -1.2542 | -0.78747 | 0.466735 | 0.466735 | 0.25 | 1.86694 |

## Blocked Reasons

- Final-frame `hv` field remains 2.11x over threshold at `downstream_constriction/interior` cell 6,14.
- Depth/profile mismatch is still active in `upstream_approach/interior` (max h delta `0.466456` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/interior` (max u/hu delta `0.37006`/`0.526308`).
- Cross-stream shear/momentum mismatch is still active in `downstream_constriction/interior` (max v/hv delta `0.463802`/`0.52695`).

## Next Levers

- Start with `downstream_constriction/interior` cell 6,14; `hv` delta is `-0.52695` with reference h `1.16693` m and C++ h `1.2062` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
