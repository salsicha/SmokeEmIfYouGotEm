# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_throat_upper_edge_depth_final_relief/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_throat_upper_edge_depth_final_relief/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `0.986797`
- Max h/u/v/hu/hv delta: `0.843576` / `0.986797` / `0.820926` / `0.9848` / `0.910213`
- Max profile mass delta: `3.5153` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `recovery` | `interior` | 46 | 0.0764195 / 0.525296 | -0.0810126 / 0.986797 | -0.0015732 / 0.722094 | 0.0525064 / 0.742519 | 0.0130269 / 0.910213 | 3.5153 | 0 | 3.94719 |
| `upstream_approach` | `interior` | 54 | -0.047536 / 0.466456 | 0.201887 / 0.618456 | -0.0736635 / 0.502471 | 0.328013 / 0.9848 | -0.147033 / 0.613842 | -2.56694 | 0 | 3.9392 |
| `upstream_approach` | `lower_shelf` | 12 | -0.152561 / 0.568508 | -0.0102587 / 0.78483 | 0.195688 / 0.770026 | -0.155303 / 0.963603 | -0.0474653 / 0.658071 | -1.83073 | 0 | 3.85441 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 0.906559 / 0.906559 | -0.0814311 / 0.0814311 | 0.203539 / 0.203539 | 0.0540387 / 0.0540387 | 0.0651685 | 0 | 3.62623 |
| `recovery` | `upper_edge` | 8 | 0.254065 / 0.843576 | -0.103505 / 0.820992 | 0.201988 / 0.820926 | 0.0458994 / 0.376896 | 0.0391632 / 0.337855 | 2.03252 | 0 | 3.3743 |
| `upstream_approach` | `lower_edge` | 10 | -0.0709597 / 0.309993 | 0.0960614 / 0.42951 | -0.0104278 / 0.481362 | 0.0879208 / 0.544494 | -0.0288711 / 0.802245 | -0.709597 | 0 | 3.20898 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.408645 / 0.777015 | -0.16815 / 0.464393 | -0.289764 / 0.600363 | -0.151893 / 0.482735 | 0.809547 | 0 | 3.10806 |
| `upstream_approach` | `upper_edge` | 10 | 0.0883857 / 0.382043 | -0.38412 / 0.739957 | 0.155319 / 0.733193 | 0.101353 / 0.241214 | -0.231712 / 0.621231 | 0.883857 | 0 | 2.95983 |
| `upstream_approach` | `upper_shelf` | 18 | 0.00873265 / 0.139176 | -0.232882 / 0.735229 | 0.0354577 / 0.734767 | -0.0543781 / 0.539529 | 0.0158495 / 0.520679 | 0.157188 | 0.0555556 | 2.94091 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | 0.0369647 / 0.257488 | 0.163568 / 0.490964 | 0.251705 / 0.455718 | 0.245821 / 0.668858 | 0.481471 | 0 | 2.67543 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0926512 / 0.387147 | 0.146691 / 0.306653 | 0.098028 / 0.456117 | 0.20507 / 0.412687 | 0.208015 | 0 | 1.82447 |
| `constriction_throat` | `lower_edge` | 4 | -0.0125067 / 0.0643546 | 0.149524 / 0.30557 | 0.178911 / 0.286263 | 0.202827 / 0.350132 | 0.267166 / 0.440334 | -0.0500269 | 0 | 1.76134 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `u` | `recovery` | `interior` | `7,17` | 17 | 1.5 | 1.83624 | 2.82303 | 0.986797 | 0.986797 | 0.25 | 3.94719 |
| `hu` | `upstream_approach` | `interior` | `5,4` | 4 | -0.5 | 0.227272 | 1.21207 | 0.9848 | 0.9848 | 0.25 | 3.9392 |
| `hu` | `upstream_approach` | `interior` | `7,9` | 9 | 1.5 | 1.86748 | 2.8373 | 0.969819 | 0.969819 | 0.25 | 3.87928 |
| `hu` | `upstream_approach` | `lower_shelf` | `0,0` | 0 | -5.5 | 1.55561 | 0.592005 | -0.963603 | 0.963603 | 0.25 | 3.85441 |
| `hu` | `upstream_approach` | `interior` | `7,8` | 8 | 1.5 | 2.07008 | 3.02701 | 0.956935 | 0.956935 | 0.25 | 3.82774 |
| `hu` | `upstream_approach` | `interior` | `4,4` | 4 | -1.5 | 0.590536 | 1.54033 | 0.949798 | 0.949798 | 0.25 | 3.79919 |
| `hu` | `upstream_approach` | `interior` | `7,0` | 0 | 1.5 | 0.392268 | 1.32435 | 0.932083 | 0.932083 | 0.25 | 3.72833 |
| `hv` | `recovery` | `interior` | `7,17` | 17 | 1.5 | 0.939262 | 0.0290492 | -0.910213 | 0.910213 | 0.25 | 3.64085 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 0.969416 | 0.906559 | 0.906559 | 0.25 | 3.62623 |
| `hu` | `upstream_approach` | `interior` | `4,5` | 5 | -1.5 | 0.950301 | 1.8325 | 0.882195 | 0.882195 | 0.25 | 3.52878 |
| `u` | `recovery` | `interior` | `5,19` | 19 | -0.5 | 3.12161 | 2.25911 | -0.862509 | 0.862509 | 0.25 | 3.45003 |
| `hu` | `upstream_approach` | `interior` | `8,0` | 0 | 2.5 | 1.76952 | 2.63045 | 0.860926 | 0.860926 | 0.25 | 3.4437 |
| `hu` | `upstream_approach` | `interior` | `5,5` | 5 | -0.5 | 0.765272 | 1.62311 | 0.857842 | 0.857842 | 0.25 | 3.43137 |
| `u` | `recovery` | `interior` | `8,18` | 18 | 2.5 | 0.528384 | 1.37372 | 0.845332 | 0.845332 | 0.25 | 3.38133 |
| `h` | `recovery` | `upper_edge` | `9,19` | 19 | 3.5 | 0.288044 | 1.13162 | 0.843576 | 0.843576 | 0.25 | 3.3743 |
| `hu` | `upstream_approach` | `interior` | `5,2` | 2 | -0.5 | -0.0269994 | 0.816161 | 0.84316 | 0.84316 | 0.25 | 3.37264 |

## Blocked Reasons

- Final-frame `u` field remains 3.95x over threshold at `recovery/interior` cell 7,17.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `0.843576` m).
- Streamwise shear/momentum mismatch is still active in `recovery/interior` (max u/hu delta `0.986797`/`0.742519`).
- Cross-stream shear/momentum mismatch is still active in `recovery/interior` (max v/hv delta `0.722094`/`0.910213`).

## Next Levers

- Start with `recovery/interior` cell 7,17; `u` delta is `0.986797` with reference h `1.25301` m and C++ h `1.05584` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
