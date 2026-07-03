# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_boundary_cross_stream_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_boundary_cross_stream_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.477967`
- Max h/u/v/hu/hv delta: `0.355242` / `0.439552` / `0.402237` / `0.477967` / `0.477009`
- Max profile mass delta: `4.35758` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `interior` | 54 | -0.0472677 / 0.263487 | 0.0479633 / 0.37006 | -0.0369009 / 0.272398 | 0.0633053 / 0.477967 | -0.0710778 / 0.473632 | -2.55245 | 0 | 1.91187 |
| `recovery` | `interior` | 46 | 0.09473 / 0.340402 | -0.0497051 / 0.439552 | 0.00608171 / 0.339079 | 0.110298 / 0.436356 | 0.0192588 / 0.477009 | 4.35758 | 0 | 1.90804 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0192081 / 0.181599 | 0.0176677 / 0.283437 | -0.0380703 / 0.231657 | 0.0154178 / 0.468124 | -0.709597 | 0 | 1.8725 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0926512 / 0.387147 | 0.146691 / 0.306653 | 0.098028 / 0.456117 | 0.20507 / 0.412687 | 0.208015 | 0 | 1.82447 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | 0.0369647 / 0.257488 | 0.0467912 / 0.247685 | 0.251705 / 0.455718 | 0.0773332 / 0.37973 | 0.481471 | 0 | 1.82287 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.149524 / 0.30557 | 0.178911 / 0.286263 | 0.202827 / 0.350132 | 0.267166 / 0.440334 | -0.0500269 | 0 | 1.76134 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.131509 / 0.410862 | -0.107961 / 0.285449 | 0.0659062 / 0.360888 | -0.0765761 / 0.286294 | 0.809547 | 0 | 1.64345 |
| `upstream_approach` | `upper_edge` | 10 | 0.0111988 / 0.159496 | -0.127704 / 0.405134 | 0.0359169 / 0.254659 | -0.00494173 / 0.323998 | -0.0259527 / 0.228382 | 0.111988 | 0 | 1.62054 |
| `upstream_approach` | `lower_shelf` | 12 | -0.0345226 / 0.293742 | -0.00878871 / 0.324043 | 0.0469043 / 0.402237 | 0.0108789 / 0.323404 | -0.00376502 / 0.294638 | -0.414271 | 0 | 1.60895 |
| `upstream_approach` | `upper_shelf` | 18 | -0.0122372 / 0.0899976 | -0.0884109 / 0.389058 | -0.0231396 / 0.300528 | -0.0462422 / 0.291333 | 0.0158199 / 0.272483 | -0.22027 | 0.0555556 | 1.55623 |
| `recovery` | `upper_edge` | 8 | 0.113578 / 0.355242 | -0.00938194 / 0.279153 | 0.0320627 / 0.239044 | 0.0427882 / 0.124942 | -0.0928032 / 0.18549 | 0.908621 | 0 | 1.42097 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `upstream_approach` | `interior` | `4,5` | 5 | -1.5 | 0.950301 | 1.42827 | 0.477967 | 0.477967 | 0.25 | 1.91187 |
| `hv` | `recovery` | `interior` | `4,22` | 22 | -1.5 | -0.418139 | 0.0588702 | 0.477009 | 0.477009 | 0.25 | 1.90804 |
| `hv` | `upstream_approach` | `interior` | `8,3` | 3 | 2.5 | -0.396559 | -0.870191 | -0.473632 | 0.473632 | 0.25 | 1.89453 |
| `hv` | `upstream_approach` | `lower_edge` | `2,2` | 2 | -3.5 | 0.239435 | 0.70756 | 0.468124 | 0.468124 | 0.25 | 1.8725 |
| `hv` | `upstream_approach` | `interior` | `7,6` | 6 | 1.5 | -1.2542 | -0.78747 | 0.466735 | 0.466735 | 0.25 | 1.86694 |
| `hu` | `upstream_approach` | `interior` | `6,5` | 5 | 0.5 | 1.32619 | 1.79203 | 0.465841 | 0.465841 | 0.25 | 1.86336 |
| `hu` | `upstream_approach` | `interior` | `6,4` | 4 | 0.5 | 0.887966 | 1.35309 | 0.465123 | 0.465123 | 0.25 | 1.86049 |
| `hu` | `recovery` | `lower_edge` | `2,18` | 18 | -3.5 | -0.362344 | 0.0937732 | 0.456117 | 0.456117 | 0.25 | 1.82447 |
| `hu` | `constriction_throat` | `interior` | `6,11` | 11 | 0.5 | 3.83851 | 4.29422 | 0.455718 | 0.455718 | 0.25 | 1.82287 |
| `hu` | `upstream_approach` | `interior` | `5,5` | 5 | -0.5 | 0.765272 | 1.21172 | 0.446445 | 0.446445 | 0.25 | 1.78578 |
| `hv` | `constriction_throat` | `lower_edge` | `4,11` | 11 | -1.5 | 0.0148011 | 0.455135 | 0.440334 | 0.440334 | 0.25 | 1.76134 |
| `u` | `recovery` | `interior` | `3,17` | 17 | -2.5 | 0.179527 | 0.619079 | 0.439552 | 0.439552 | 0.25 | 1.75821 |
| `hu` | `recovery` | `interior` | `8,20` | 20 | 2.5 | 1.02833 | 1.46468 | 0.436356 | 0.436356 | 0.25 | 1.74542 |
| `hu` | `constriction_throat` | `interior` | `5,11` | 11 | -0.5 | 4.23942 | 4.66763 | 0.428216 | 0.428216 | 0.25 | 1.71286 |
| `hu` | `recovery` | `interior` | `3,18` | 18 | -2.5 | 0.349034 | 0.777136 | 0.428102 | 0.428102 | 0.25 | 1.71241 |
| `hv` | `upstream_approach` | `interior` | `8,1` | 1 | 2.5 | -1.18716 | -1.60967 | -0.422507 | 0.422507 | 0.25 | 1.69003 |

## Blocked Reasons

- Final-frame `hu` field remains 1.91x over threshold at `upstream_approach/interior` cell 4,5.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `0.355242` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/interior` (max u/hu delta `0.37006`/`0.477967`).
- Cross-stream shear/momentum mismatch is still active in `recovery/interior` (max v/hv delta `0.339079`/`0.477009`).

## Next Levers

- Start with `upstream_approach/interior` cell 4,5; `hu` delta is `0.477967` with reference h `1.87213` m and C++ h `1.62735` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
