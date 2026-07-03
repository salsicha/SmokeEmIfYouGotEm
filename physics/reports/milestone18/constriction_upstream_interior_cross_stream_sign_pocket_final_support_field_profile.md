# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_interior_cross_stream_sign_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_interior_cross_stream_sign_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.597129`
- Max h/u/v/hu/hv delta: `0.466456` / `0.593001` / `0.584986` / `0.597129` / `0.562798`
- Max profile mass delta: `4.6392` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `interior` | 54 | -0.0450389 / 0.466456 | 0.063074 / 0.461626 | -0.0448257 / 0.502471 | 0.0968841 / 0.597129 | -0.0993226 / 0.549948 | -2.4321 | 0 | 2.38851 |
| `recovery` | `interior` | 46 | 0.100852 / 0.376764 | -0.0955941 / 0.593001 | 0.039265 / 0.412192 | 0.0619446 / 0.596372 | 0.0685506 / 0.562798 | 4.6392 | 0 | 2.38549 |
| `recovery` | `upper_edge` | 8 | 0.113578 / 0.355242 | -0.00938194 / 0.279153 | 0.0753094 / 0.584986 | 0.0427882 / 0.124942 | -0.0765857 / 0.185478 | 0.908621 | 0 | 2.33994 |
| `upstream_approach` | `lower_shelf` | 12 | -0.080879 / 0.40319 | -0.00779507 / 0.324043 | 0.0313216 / 0.481163 | -0.0396959 / 0.55627 | -0.0242037 / 0.294638 | -0.970548 | 0 | 2.22508 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.102651 / 0.410862 | -0.150126 / 0.463802 | 0.104562 / 0.552267 | -0.125319 / 0.52695 | 0.809547 | 0 | 2.20907 |
| `upstream_approach` | `upper_edge` | 10 | 0.0211691 / 0.159496 | -0.209572 / 0.550955 | 0.0774136 / 0.254659 | -0.00732788 / 0.452691 | -0.036867 / 0.412882 | 0.211691 | 0 | 2.20382 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0621087 / 0.42951 | 0.0463075 / 0.286296 | 0.0328033 / 0.544494 | 0.0627319 / 0.489749 | -0.709597 | 0 | 2.17797 |
| `upstream_approach` | `upper_shelf` | 18 | -0.0092036 / 0.139176 | -0.128632 / 0.502464 | -0.0255148 / 0.300528 | -0.0548065 / 0.442833 | 0.00594327 / 0.272495 | -0.165665 | 0.0555556 | 2.00986 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0926512 / 0.387147 | 0.146691 / 0.306653 | 0.098028 / 0.456117 | 0.20507 / 0.412687 | 0.208015 | 0 | 1.82447 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | 0.0369647 / 0.257488 | 0.0467912 / 0.247685 | 0.251705 / 0.455718 | 0.0773332 / 0.37973 | 0.481471 | 0 | 1.82287 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.149524 / 0.30557 | 0.178911 / 0.286263 | 0.202827 / 0.350132 | 0.267166 / 0.440334 | -0.0500269 | 0 | 1.76134 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `upstream_approach` | `interior` | `3,0` | 0 | -2.5 | 0.590908 | 1.18804 | 0.597129 | 0.597129 | 0.25 | 2.38851 |
| `hu` | `recovery` | `interior` | `7,22` | 22 | 1.5 | 2.31822 | 2.91459 | 0.596372 | 0.596372 | 0.25 | 2.38549 |
| `u` | `recovery` | `interior` | `4,21` | 21 | -1.5 | 2.39704 | 1.80404 | -0.593001 | 0.593001 | 0.25 | 2.372 |
| `hu` | `recovery` | `interior` | `4,21` | 21 | -1.5 | 3.23168 | 2.64207 | -0.589607 | 0.589607 | 0.25 | 2.35843 |
| `v` | `recovery` | `upper_edge` | `9,23` | 23 | 3.5 | -1.91186 | -1.32688 | 0.584986 | 0.584986 | 0.25 | 2.33994 |
| `hu` | `recovery` | `interior` | `6,23` | 23 | 0.5 | 3.30212 | 2.73868 | -0.563437 | 0.563437 | 0.25 | 2.25375 |
| `hv` | `recovery` | `interior` | `3,22` | 22 | -2.5 | -0.490583 | 0.0722146 | 0.562798 | 0.562798 | 0.25 | 2.25119 |
| `hu` | `upstream_approach` | `lower_shelf` | `1,4` | 4 | -4.5 | 1.4337 | 0.87743 | -0.55627 | 0.55627 | 0.25 | 2.22508 |
| `hu` | `downstream_constriction` | `interior` | `7,14` | 14 | 1.5 | 1.22494 | 1.77721 | 0.552267 | 0.552267 | 0.25 | 2.20907 |
| `u` | `upstream_approach` | `upper_edge` | `9,1` | 1 | 3.5 | 3.43843 | 2.88747 | -0.550955 | 0.550955 | 0.25 | 2.20382 |
| `u` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 2.91578 | 2.36502 | -0.550763 | 0.550763 | 0.25 | 2.20305 |
| `hv` | `upstream_approach` | `interior` | `5,4` | 4 | -0.5 | 0.125899 | -0.424048 | -0.549948 | 0.549948 | 0.25 | 2.19979 |
| `hv` | `upstream_approach` | `interior` | `8,4` | 4 | 2.5 | -0.38081 | -0.930519 | -0.549709 | 0.549709 | 0.25 | 2.19884 |
| `hu` | `upstream_approach` | `lower_edge` | `2,4` | 4 | -3.5 | 1.86526 | 2.40976 | 0.544494 | 0.544494 | 0.25 | 2.17797 |
| `u` | `recovery` | `interior` | `4,19` | 19 | -1.5 | 2.89388 | 2.35636 | -0.537514 | 0.537514 | 0.25 | 2.15006 |
| `hu` | `upstream_approach` | `interior` | `3,6` | 6 | -2.5 | 1.36476 | 1.8986 | 0.533837 | 0.533837 | 0.25 | 2.13535 |

## Blocked Reasons

- Final-frame `hu` field remains 2.39x over threshold at `upstream_approach/interior` cell 3,0.
- Depth/profile mismatch is still active in `upstream_approach/interior` (max h delta `0.466456` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/interior` (max u/hu delta `0.461626`/`0.597129`).
- Cross-stream shear/momentum mismatch is still active in `recovery/upper_edge` (max v/hv delta `0.584986`/`0.185478`).

## Next Levers

- Start with `upstream_approach/interior` cell 3,0; `hu` delta is `0.597129` with reference h `1.76401` m and C++ h `1.69732` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
