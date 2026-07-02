# Milestone 18 Constriction Field-Profile Diagnostic

Schema: `raftsim.milestone18.constriction_field_profile.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_boundary_upper_shelf_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_boundary_upper_shelf_final_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max field delta: `1.50734`
- Max h/u/v/hu/hv delta: `0.941747` / `1.37013` / `1.33994` / `1.50734` / `1.47376`
- Max profile mass delta: `4.86553` m3
- Max material wet mismatch fraction: `0.0555556`

## Worst Profile Bins

| Zone | Profile | Samples | h delta/max | u delta/max | v delta/max | hu delta/max | hv delta/max | Mass delta | Wet mismatch | Ratio |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `constriction_throat` | `lower_shelf` | 4 | 0.146465 / 0.541319 | 0.0899832 / 0.210905 | 0.0464152 / 0.525518 | 0.43136 / 1.50734 | 0.0691856 / 0.363317 | 0.585861 | 0 | 6.02937 |
| `upstream_approach` | `interior` | 54 | -0.0901025 / 0.521951 | 0.204109 / 0.618443 | -0.150255 / 0.822056 | 0.283304 / 1.03841 | -0.256741 / 1.47376 | -4.86553 | 0 | 5.89504 |
| `downstream_constriction` | `interior` | 8 | 0.101009 / 0.221016 | -0.85976 / 1.32805 | -0.168212 / 0.46441 | -0.884481 / 1.45797 | -0.152069 / 0.482933 | 0.808072 | 0 | 5.8319 |
| `recovery` | `upper_shelf` | 1 | 0.0651685 / 0.0651685 | 1.37013 / 1.37013 | -0.544941 / 0.544941 | 0.305525 / 0.305525 | -0.0479334 / 0.0479334 | 0.0651685 | 0 | 5.48053 |
| `upstream_approach` | `upper_shelf` | 18 | -0.0520649 / 0.484683 | -0.289488 / 1.34588 | 0.119538 / 1.22438 | -0.202715 / 1.19928 | 0.0683443 / 0.855276 | -0.937168 | 0.0555556 | 5.38353 |
| `upstream_approach` | `upper_edge` | 10 | 0.286723 / 0.790034 | -0.70439 / 1.34175 | 0.239947 / 1.27589 | 0.359465 / 1.33543 | -0.598106 / 1.32469 | 2.86723 | 0 | 5.36701 |
| `constriction_throat` | `upper_edge` | 2 | 0.338706 / 0.48652 | -0.00211336 / 0.00647273 | 0.433589 / 1.33994 | 0.808597 / 1.12343 | -0.0431986 / 0.0865425 | 0.677412 | 0 | 5.35976 |
| `upstream_approach` | `lower_edge` | 10 | 0.0715437 / 0.941747 | -0.00682626 / 1.23756 | -0.183936 / 0.894022 | 0.307069 / 1.33032 | -0.249236 / 1.14195 | 0.715437 | 0 | 5.32128 |
| `constriction_throat` | `lower_edge` | 4 | -0.0867638 / 0.229337 | 0.00938983 / 0.519775 | 0.402207 / 1.04506 | -0.171705 / 1.30783 | 0.497916 / 1.08999 | -0.347055 | 0 | 5.23131 |
| `upstream_approach` | `lower_shelf` | 12 | -0.124843 / 0.568586 | -0.0283498 / 1.29646 | 0.193732 / 0.769686 | -0.0855385 / 0.966142 | 0.0425439 / 0.746987 | -1.49811 | 0 | 5.18582 |
| `recovery` | `interior` | 46 | 0.0761542 / 0.525361 | -0.167372 / 1.03856 | -0.00166709 / 0.721932 | -0.0799763 / 1.2371 | 0.0125834 / 0.910055 | 3.50309 | 0 | 4.94838 |
| `constriction_throat` | `interior` | 8 | 0.0405979 / 0.162798 | -0.143354 / 0.822348 | 0.0410284 / 0.596311 | -0.0170108 / 1.16579 | 0.0998727 / 0.666928 | 0.324783 | 0 | 4.66317 |

## Worst Final-Frame Cells

| Field | Zone | Profile | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hu` | `constriction_throat` | `lower_shelf` | `3,10` | 10 | -2.5 | 1.49207 | 2.99941 | 1.50734 | 1.50734 | 0.25 | 6.02937 |
| `hv` | `upstream_approach` | `interior` | `3,5` | 5 | -2.5 | 1.06936 | -0.404397 | -1.47376 | 1.47376 | 0.25 | 5.89504 |
| `hu` | `downstream_constriction` | `interior` | `5,15` | 15 | -0.5 | 4.05104 | 2.59307 | -1.45797 | 1.45797 | 0.25 | 5.8319 |
| `hv` | `upstream_approach` | `interior` | `3,6` | 6 | -2.5 | 0.891438 | -0.501427 | -1.39287 | 1.39287 | 0.25 | 5.57146 |
| `u` | `recovery` | `upper_shelf` | `9,16` | 16 | 3.5 | 0.0628575 | 1.43299 | 1.37013 | 1.37013 | 0.25 | 5.48053 |
| `u` | `upstream_approach` | `upper_shelf` | `10,1` | 1 | 4.5 | 3.39685 | 2.05096 | -1.34588 | 1.34588 | 0.25 | 5.38353 |
| `u` | `upstream_approach` | `upper_edge` | `9,2` | 2 | 3.5 | 3.50488 | 2.16313 | -1.34175 | 1.34175 | 0.25 | 5.36701 |
| `v` | `constriction_throat` | `upper_edge` | `7,10` | 10 | 1.5 | -2.58013 | -1.24019 | 1.33994 | 1.33994 | 0.25 | 5.35976 |
| `hu` | `upstream_approach` | `upper_edge` | `9,6` | 6 | 3.5 | 1.30029 | 2.63572 | 1.33543 | 1.33543 | 0.25 | 5.34172 |
| `hu` | `downstream_constriction` | `interior` | `4,15` | 15 | -1.5 | 3.86465 | 2.53332 | -1.33133 | 1.33133 | 0.25 | 5.3253 |
| `hu` | `upstream_approach` | `lower_edge` | `2,6` | 6 | -3.5 | 0.921728 | 2.25205 | 1.33032 | 1.33032 | 0.25 | 5.32128 |
| `u` | `downstream_constriction` | `interior` | `5,14` | 14 | -0.5 | 3.48923 | 2.16118 | -1.32805 | 1.32805 | 0.25 | 5.31219 |
| `hv` | `upstream_approach` | `upper_edge` | `9,5` | 5 | 3.5 | -0.823694 | -2.14838 | -1.32469 | 1.32469 | 0.25 | 5.29876 |
| `hu` | `constriction_throat` | `lower_edge` | `4,13` | 13 | -1.5 | 4.26895 | 2.96112 | -1.30783 | 1.30783 | 0.25 | 5.23131 |
| `hu` | `downstream_constriction` | `interior` | `5,14` | 14 | -0.5 | 4.19804 | 2.89462 | -1.30342 | 1.30342 | 0.25 | 5.21367 |
| `u` | `upstream_approach` | `lower_shelf` | `1,6` | 6 | -4.5 | 0.26938 | 1.56583 | 1.29646 | 1.29646 | 0.25 | 5.18582 |

## Blocked Reasons

- Final-frame `hu` field remains 6.03x over threshold at `constriction_throat/lower_shelf` cell 3,10.
- Depth/profile mismatch is still active in `upstream_approach/lower_edge` (max h delta `0.941747` m).
- Streamwise shear/momentum mismatch is still active in `constriction_throat/lower_shelf` (max u/hu delta `0.210905`/`1.50734`).
- Cross-stream shear/momentum mismatch is still active in `upstream_approach/interior` (max v/hv delta `0.822056`/`1.47376`).

## Next Levers

- Start with `constriction_throat/lower_shelf` cell 3,10; `hu` delta is `1.50734` with reference h `0.627212` m and C++ h `1.16853` m.
- Retune edge/interior water redistribution before another velocity-only pass; edge depths are part of the field blocker.
- Retune streamwise shear/reverse-flow profile together with depth so hu does not remain the dominant Linf error.
- Retune cross-stream circulation/sign by zone and profile role, then rerun face-state and face/source audits.
- Keep feature forcing off; this report is a water-field closure target, not gameplay forcing evidence.
