# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_lower_edge_sign_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_lower_edge_sign_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.70621`
- Max h/u/v/hu/hv delta: `0.655706` / `0.70621` / `0.651338` / `0.663757` / `0.702115`
- Max profile mass delta: `3.98273` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `upper_shelf` | 18 | -0.00566374 / 0.139176 | -0.204784 / 0.70621 | 0.00736004 / 0.559386 | -0.0722619 / 0.442833 | 0.00976301 / 0.272495 | -0.101947 | 0.0555556 | 2.82484 |
| `recovery` | `interior` | 46 | 0.086581 / 0.398864 | -0.0925679 / 0.647627 | 0.0384787 / 0.556684 | 0.0550765 / 0.596372 | 0.0625003 / 0.702115 | 3.98273 | 0 | 2.80846 |
| `upstream_approach` | `upper_edge` | 10 | 0.0486362 / 0.382043 | -0.33763 / 0.671582 | 0.0989524 / 0.611694 | 0.0365658 / 0.452691 | -0.18569 / 0.621231 | 0.486362 | 0 | 2.68633 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | 0.0369647 / 0.257488 | 0.163568 / 0.490964 | 0.251705 / 0.455718 | 0.245821 / 0.668858 | 0.481471 | 0 | 2.67543 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.106349 / 0.4256 | -0.168146 / 0.464393 | 0.111641 / 0.663757 | -0.151888 / 0.482735 | 0.809547 | 0 | 2.65503 |
| `upstream_approach` | `lower_shelf` | 12 | -0.0978414 / 0.40319 | -0.0354577 / 0.628275 | 0.0602853 / 0.651338 | -0.0808123 / 0.556494 | -0.0441143 / 0.658013 | -1.1741 | 0 | 2.63205 |
| `recovery` | `upper_edge` | 8 | 0.195636 / 0.655706 | -0.0922976 / 0.654883 | 0.111401 / 0.585144 | 0.0201325 / 0.144237 | -0.0421774 / 0.16439 | 1.56509 | 0 | 2.62283 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0960614 / 0.42951 | -0.0404087 / 0.382857 | 0.0879208 / 0.544494 | -0.0797097 / 0.652559 | -0.709597 | 0 | 2.61024 |
| `upstream_approach` | `interior` | 54 | -0.047536 / 0.466456 | 0.0718932 / 0.480905 | -0.0736635 / 0.502471 | 0.108086 / 0.622135 | -0.147033 / 0.613842 | -2.56694 | 0 | 2.48854 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0926512 / 0.387147 | 0.146691 / 0.306653 | 0.098028 / 0.456117 | 0.20507 / 0.412687 | 0.208015 | 0 | 1.82447 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.149524 / 0.30557 | 0.178911 / 0.286263 | 0.202827 / 0.350132 | 0.267166 / 0.440334 | -0.0500269 | 0 | 1.76134 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `u` | `upstream_approach` | `upper_shelf` | `10,4` | 4 | 4.5 | 3.0443 | 2.33809 | -0.70621 | 0.70621 | 0.25 | 2.82484 |
| `u` | `upstream_approach` | `upper_shelf` | `10,5` | 5 | 4.5 | 2.82416 | 2.11967 | -0.704488 | 0.704488 | 0.25 | 2.81795 |
| `hv` | `recovery` | `interior` | `4,20` | 20 | -1.5 | -0.114402 | 0.587714 | 0.702115 | 0.702115 | 0.25 | 2.80846 |
| `hv` | `recovery` | `interior` | `6,16` | 16 | 0.5 | 1.02735 | 0.355262 | -0.672084 | 0.672084 | 0.25 | 2.68834 |
| `u` | `upstream_approach` | `upper_edge` | `9,3` | 3 | 3.5 | 3.41154 | 2.73996 | -0.671582 | 0.671582 | 0.25 | 2.68633 |
| `hv` | `constriction_throat` | `interior` | `6,10` | 10 | 0.5 | -1.26983 | -0.600968 | 0.668858 | 0.668858 | 0.25 | 2.67543 |
| `hv` | `constriction_throat` | `interior` | `6,11` | 11 | 0.5 | -0.518623 | 0.148306 | 0.666928 | 0.666928 | 0.25 | 2.66771 |
| `hu` | `downstream_constriction` | `interior` | `6,14` | 14 | 0.5 | 3.91865 | 4.5824 | 0.663757 | 0.663757 | 0.25 | 2.65503 |
| `u` | `upstream_approach` | `upper_edge` | `9,4` | 4 | 3.5 | 3.40365 | 2.73996 | -0.663692 | 0.663692 | 0.25 | 2.65477 |
| `hv` | `upstream_approach` | `lower_shelf` | `1,5` | 5 | -4.5 | 1.06765 | 0.409636 | -0.658013 | 0.658013 | 0.25 | 2.63205 |
| `u` | `upstream_approach` | `upper_edge` | `9,5` | 5 | 3.5 | 3.39654 | 2.74047 | -0.656071 | 0.656071 | 0.25 | 2.62428 |
| `h` | `recovery` | `upper_edge` | `9,19` | 19 | 3.5 | 0.288044 | 0.94375 | 0.655706 | 0.655706 | 0.25 | 2.62283 |
| `u` | `recovery` | `upper_edge` | `9,22` | 22 | 3.5 | 0.885822 | 0.23094 | -0.654883 | 0.654883 | 0.25 | 2.61953 |
| `hv` | `upstream_approach` | `lower_edge` | `2,0` | 0 | -3.5 | 1.70802 | 1.05546 | -0.652559 | 0.652559 | 0.25 | 2.61024 |
| `v` | `upstream_approach` | `lower_shelf` | `0,2` | 2 | -5.5 | 0.677913 | 1.32925 | 0.651338 | 0.651338 | 0.25 | 2.60535 |
| `u` | `recovery` | `interior` | `6,19` | 19 | 0.5 | 2.91578 | 2.26815 | -0.647627 | 0.647627 | 0.25 | 2.59051 |

## Blocked Reasons

- Final-frame `u` field remains 2.82x over threshold at `upstream_approach/upper_shelf` cell 10,4.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `0.655706` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/upper_shelf` (max u/hu delta `0.70621`/`0.442833`).
- Cross-stream shear/momentum mismatch is still active in `recovery/interior` (max v/hv delta `0.556684`/`0.702115`).

## Next Levers

- Start with `upstream_approach/upper_shelf` cell 10,4; `u` delta is `-0.70621` with reference h `0.209063` m and C++ h `0.254615` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
