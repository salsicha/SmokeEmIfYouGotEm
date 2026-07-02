# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_upper_interior_streamwise_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_upper_interior_streamwise_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.09267`
- Max h/u/v/hu/hv delta: `0.843576` / `1.09267` / `1.05171` / `1.08183` / `1.06264`
- Max profile mass delta: `3.5153` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `upstream_approach` | `lower_shelf` | 12 | -0.124918 / 0.568508 | -0.0898695 / 1.09267 | 0.195688 / 0.770026 | -0.102957 / 0.966161 | 0.0431356 / 0.749009 | -1.49902 | 0 | 4.37068 |
| `upstream_approach` | `lower_edge` | 10 | -0.0896744 / 0.309993 | 0.168523 / 0.758785 | -0.0104278 / 0.481362 | 0.179669 / 1.08183 | -0.0374522 / 0.802198 | -0.896744 | 0 | 4.32734 |
| `upstream_approach` | `upper_edge` | 10 | 0.0883857 / 0.382043 | -0.38412 / 0.739957 | 0.12597 / 0.82526 | 0.101353 / 0.241214 | -0.276559 / 1.06264 | 0.883857 | 0 | 4.25057 |
| `upstream_approach` | `upper_shelf` | 18 | 0.00873265 / 0.139176 | -0.232882 / 0.735229 | 0.0727366 / 1.05171 | -0.0543781 / 0.539529 | 0.0368259 / 0.690071 | 0.157188 | 0.0555556 | 4.20685 |
| `recovery` | `upper_edge` | 8 | 0.254065 / 0.843576 | 0.0357814 / 1.02485 | 0.0504429 / 0.728964 | 0.192095 / 1.03029 | -0.11536 / 0.903836 | 2.03252 | 0 | 4.12117 |
| `constriction_throat` | `upper_edge` | 2 | 0.265621 / 0.441761 | -0.00211336 / 0.00647273 | 0.256184 / 0.615661 | 0.62534 / 1.02016 | -0.282657 / 0.630358 | 0.531242 | 0 | 4.08063 |
| `recovery` | `interior` | 46 | 0.0764195 / 0.525296 | -0.0810126 / 0.986797 | -0.0015732 / 0.722094 | 0.0525064 / 0.742519 | 0.0130269 / 0.910213 | 3.5153 | 0 | 3.94719 |
| `upstream_approach` | `interior` | 54 | -0.050146 / 0.466456 | 0.201887 / 0.618456 | -0.0736635 / 0.502471 | 0.326074 / 0.9848 | -0.146707 / 0.613639 | -2.70788 | 0 | 3.9392 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 0.906559 / 0.906559 | -0.0814311 / 0.0814311 | 0.203539 / 0.203539 | 0.0540387 / 0.0540387 | 0.0651685 | 0 | 3.62623 |
| `downstream_constriction` | `interior` | 8 | 0.101193 / 0.221196 | -0.408645 / 0.777015 | -0.16815 / 0.464393 | -0.289764 / 0.600363 | -0.151893 / 0.482735 | 0.809547 | 0 | 3.10806 |
| `constriction_throat` | `interior` | 8 | 0.0601838 / 0.165409 | 0.0369647 / 0.257488 | 0.163568 / 0.490964 | 0.251705 / 0.455718 | 0.245821 / 0.668858 | 0.481471 | 0 | 2.67543 |
| `recovery` | `lower_edge` | 6 | 0.0346691 / 0.210524 | 0.0926512 / 0.387147 | 0.146691 / 0.306653 | 0.098028 / 0.456117 | 0.20507 / 0.412687 | 0.208015 | 0 | 1.82447 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `u` | `upstream_approach` | `lower_shelf` | `1,1` | 1 | -4.5 | 3.85418 | 2.76151 | -1.09267 | 1.09267 | 0.25 | 4.37068 |
| `hu` | `upstream_approach` | `lower_edge` | `2,5` | 5 | -3.5 | 1.31208 | 2.39391 | 1.08183 | 1.08183 | 0.25 | 4.32734 |
| `hv` | `upstream_approach` | `upper_edge` | `8,8` | 8 | 2.5 | -1.17242 | -2.23506 | -1.06264 | 1.06264 | 0.25 | 4.25057 |
| `v` | `upstream_approach` | `upper_shelf` | `9,7` | 7 | 3.5 | -1.51195 | -0.460232 | 1.05171 | 1.05171 | 0.25 | 4.20685 |
| `hu` | `recovery` | `upper_edge` | `8,16` | 16 | 2.5 | 0.169789 | 1.20008 | 1.03029 | 1.03029 | 0.25 | 4.12117 |
| `u` | `recovery` | `upper_edge` | `9,18` | 18 | 3.5 | -0.115375 | 0.909479 | 1.02485 | 1.02485 | 0.25 | 4.09942 |
| `hu` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | 0.889107 | 1.90926 | 1.02016 | 1.02016 | 0.25 | 4.08063 |
| `u` | `recovery` | `interior` | `7,17` | 17 | 1.5 | 1.83624 | 2.82303 | 0.986797 | 0.986797 | 0.25 | 3.94719 |
| `hu` | `upstream_approach` | `interior` | `5,4` | 4 | -0.5 | 0.227272 | 1.21207 | 0.9848 | 0.9848 | 0.25 | 3.9392 |
| `hu` | `upstream_approach` | `interior` | `7,9` | 9 | 1.5 | 1.86748 | 2.8373 | 0.969819 | 0.969819 | 0.25 | 3.87928 |
| `hu` | `upstream_approach` | `lower_shelf` | `0,0` | 0 | -5.5 | 1.55561 | 0.589447 | -0.966161 | 0.966161 | 0.25 | 3.86464 |
| `hu` | `upstream_approach` | `interior` | `7,8` | 8 | 1.5 | 2.07008 | 3.02701 | 0.956935 | 0.956935 | 0.25 | 3.82774 |
| `hu` | `upstream_approach` | `interior` | `4,4` | 4 | -1.5 | 0.590536 | 1.54033 | 0.949798 | 0.949798 | 0.25 | 3.79919 |
| `hu` | `upstream_approach` | `interior` | `7,0` | 0 | 1.5 | 0.392268 | 1.32435 | 0.932083 | 0.932083 | 0.25 | 3.72833 |
| `hv` | `recovery` | `interior` | `7,17` | 17 | 1.5 | 0.939262 | 0.0290492 | -0.910213 | 0.910213 | 0.25 | 3.64085 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 0.969416 | 0.906559 | 0.906559 | 0.25 | 3.62623 |

## Blocked Reasons

- Final-frame `u` field remains 4.37x over threshold at `upstream_approach/lower_shelf` cell 1,1.
- Depth/profile mismatch is still active in `recovery/upper_edge` (max h delta `0.843576` m).
- Streamwise shear/momentum mismatch is still active in `upstream_approach/lower_shelf` (max u/hu delta `1.09267`/`0.966161`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/upper_edge` (max v/hv delta `0.82526`/`1.06264`).

## Next Levers

- Start with `upstream_approach/lower_shelf` cell 1,1; `u` delta is `-1.09267` with reference h `0.302369` m and C++ h `0.55938` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
