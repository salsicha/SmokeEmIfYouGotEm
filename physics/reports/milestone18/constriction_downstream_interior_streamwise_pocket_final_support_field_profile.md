# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_downstream_interior_streamwise_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_downstream_interior_streamwise_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.770026`
- Max h/u/v/hu/hv delta: `0.655706` / `0.746159` / `0.770026` / `0.76214` / `0.741659`
- Max profile mass delta: `3.98273` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `lower_shelf` | 12 | -0.120756 / 0.568508 | 0.0547079 / 0.717361 | 0.106047 / 0.770026 | -0.0653352 / 0.432063 | -0.0520593 / 0.658071 | -1.44907 | 0 | 3.0801 |
| `upstream_approach` | `interior` | 54 | -0.047536 / 0.466456 | 0.112752 / 0.480905 | -0.0736635 / 0.502471 | 0.177611 / 0.76214 | -0.147033 / 0.613842 | -2.56694 | 0 | 3.04856 |
| `recovery` | `interior` | 46 | 0.086581 / 0.398864 | -0.0963646 / 0.746159 | 0.0384787 / 0.556684 | 0.0509663 / 0.742519 | 0.0625003 / 0.702115 | 3.98273 | 0 | 2.98464 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0960614 / 0.42951 | -0.0593994 / 0.41712 | 0.0879208 / 0.544494 | -0.110573 / 0.741659 | -0.709597 | 0 | 2.96663 |
| `upstream_approach` | `upper_edge` | 10 | 0.0702204 / 0.382043 | -0.38412 / 0.739957 | 0.155319 / 0.733193 | 0.0620589 / 0.452691 | -0.194602 / 0.621231 | 0.702204 | 0 | 2.95983 |
| `upstream_approach` | `upper_shelf` | 18 | -0.00237846 / 0.139176 | -0.232882 / 0.735229 | 0.0354577 / 0.734767 | -0.0808225 / 0.539529 | 0.0217607 / 0.520679 | -0.0428122 | 0.0555556 | 2.94091 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | 0.0369647 / 0.257488 | 0.163568 / 0.490964 | 0.251705 / 0.455718 | 0.245821 / 0.668858 | 0.481471 | 0 | 2.67543 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.111804 / 0.4256 | -0.168146 / 0.464393 | 0.104644 / 0.663757 | -0.151888 / 0.482735 | 0.809547 | 0 | 2.65503 |
| `recovery` | `upper_edge` | 8 | 0.195636 / 0.655706 | -0.0922976 / 0.654883 | 0.111401 / 0.585144 | 0.0201325 / 0.144237 | -0.0421774 / 0.16439 | 1.56509 | 0 | 2.62283 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0926512 / 0.387147 | 0.146691 / 0.306653 | 0.098028 / 0.456117 | 0.20507 / 0.412687 | 0.208015 | 0 | 1.82447 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.149524 / 0.30557 | 0.178911 / 0.286263 | 0.202827 / 0.350132 | 0.267166 / 0.440334 | -0.0500269 | 0 | 1.76134 |
| `constriction_throat` | `lower_shelf` | 4 | 0.017873 / 0.0600621 | 0.0210815 / 0.137102 | 0.0873373 / 0.33579 | 0.0615502 / 0.233658 | 0.0704974 / 0.241447 | 0.071492 | 0 | 1.34316 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `v` | `upstream_approach` | `lower_shelf` | `1,6` | 6 | -4.5 | 0.667834 | 1.43786 | 0.770026 | 0.770026 | 0.25 | 3.0801 |
| `hu` | `upstream_approach` | `interior` | `4,0` | 0 | -1.5 | 0.262025 | 1.02417 | 0.76214 | 0.76214 | 0.25 | 3.04856 |
| `u` | `recovery` | `interior` | `4,16` | 16 | -1.5 | 3.09709 | 2.35094 | -0.746159 | 0.746159 | 0.25 | 2.98464 |
| `hu` | `recovery` | `interior` | `4,20` | 20 | -1.5 | 3.42222 | 4.16474 | 0.742519 | 0.742519 | 0.25 | 2.97007 |
| `hv` | `upstream_approach` | `lower_edge` | `2,5` | 5 | -3.5 | 1.00936 | 0.267699 | -0.741659 | 0.741659 | 0.25 | 2.96663 |
| `u` | `upstream_approach` | `upper_edge` | `9,6` | 6 | 3.5 | 2.86357 | 2.12361 | -0.739957 | 0.739957 | 0.25 | 2.95983 |
| `hv` | `upstream_approach` | `lower_edge` | `2,6` | 6 | -3.5 | 0.73735 | -0.00174169 | -0.739091 | 0.739091 | 0.25 | 2.95637 |
| `u` | `upstream_approach` | `upper_shelf` | `9,7` | 7 | 3.5 | 1.73171 | 0.996485 | -0.735229 | 0.735229 | 0.25 | 2.94091 |
| `v` | `upstream_approach` | `upper_shelf` | `9,7` | 7 | 3.5 | -1.51195 | -0.777178 | 0.734767 | 0.734767 | 0.25 | 2.93907 |
| `v` | `upstream_approach` | `upper_edge` | `9,1` | 1 | 3.5 | -3.72743 | -2.99424 | 0.733193 | 0.733193 | 0.25 | 2.93277 |
| `hu` | `upstream_approach` | `interior` | `4,1` | 1 | -1.5 | 0.436815 | 1.15637 | 0.719559 | 0.719559 | 0.25 | 2.87824 |
| `u` | `upstream_approach` | `lower_shelf` | `1,4` | 4 | -4.5 | 2.88154 | 3.5989 | 0.717361 | 0.717361 | 0.25 | 2.86945 |
| `u` | `upstream_approach` | `upper_shelf` | `10,4` | 4 | 4.5 | 3.0443 | 2.33809 | -0.70621 | 0.70621 | 0.25 | 2.82484 |
| `hv` | `upstream_approach` | `lower_edge` | `2,4` | 4 | -3.5 | -0.189569 | 0.516308 | 0.705877 | 0.705877 | 0.25 | 2.82351 |
| `u` | `upstream_approach` | `upper_shelf` | `10,5` | 5 | 4.5 | 2.82416 | 2.11967 | -0.704488 | 0.704488 | 0.25 | 2.81795 |
| `hv` | `recovery` | `interior` | `4,20` | 20 | -1.5 | -0.114402 | 0.587714 | 0.702115 | 0.702115 | 0.25 | 2.80846 |

## Blocked Reasons

- Final-frame `v` field remains 3.08x over threshold at `upstream_approach/lower_shelf` cell 1,6.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `0.655706` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/interior` (max u/hu delta `0.480905`/`0.76214`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max v/hv delta `0.770026`/`0.658071`).

## Next Levers

- Start with `upstream_approach/lower_shelf` cell 1,6; `v` delta is `0.770026` with reference h `0.840273` m and C++ h `0.271765` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
