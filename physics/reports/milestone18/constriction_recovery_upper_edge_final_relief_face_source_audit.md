# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_upper_edge_final_relief/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_upper_edge_final_relief/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.706344` m3/s
- Max abs flux/source balance delta: `12.81` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `47`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.973781/1.82678/0.776985/0.756613` | -0.706344 | `1->1` | `-4.09759/-5.3479/-9.44548` | `2.82538/12.594` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.825773/1.44208/0.77533/0.640247` | 0.565937 | `1->1` | `3.26092/9.54911/12.81` | `2.26375/17.08` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.6523/1.30108/-1.19257/-1.97049` | -0.56314 | `-1->-1` | `-2.12633/0/-2.12633` | `2.25256/2.83511` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.0434/1.90035/-1.78241/-1.85978` | 0.438844 | `-1->-1` | `-1.72195/0/-1.72195` | `1.75538/2.29593` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.668494/1.44208/0.729291/0.487527` | 0.42601 | `1->1` | `1.99877/6.62213/8.6209` | `1.70404/11.4945` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.33464/1.76861/-1.23591/-1.64949` | -0.417778 | `-1->-1` | `3.35316/0/3.35316` | `1.67111/4.47089` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.46159/1.09109/-1.19192/-1.7421` | -0.373781 | `-1->-1` | `5.90751/0/5.90751` | `1.49513/7.87668` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.38457/1.77357/-1.17968/-1.63335` | -0.350627 | `-1->-1` | `3.80523/0/3.80523` | `1.40251/5.07364` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.09064/2.29456/1.52207/1.66003` | 0.343161 | `1->1` | `1.6315/1.56043/3.19193` | `1.37264/4.2559` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.97784/2.52889/0.588987/0.575935` | 0.339809 | `1->1` | `-1.56235/-3.47575/-5.0381` | `1.35924/6.71747` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.3036/1.76676/-1.29529/-1.68853` | -0.320258 | `-1->-1` | `3.01963/0/3.01963` | `1.28103/4.02617` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.02373/1.82299/-1.74097/-1.78229` | 0.225379 | `-1->-1` | `-2.54349/0/-2.54349` | `0.901516/3.39133` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.71771 | `1.71769/1` | 3.03747 | `False` | `False` | `True` | `True` | `-12.4722/-1.63696` |
| `upper_edge_face` | 23 | `8-9` | `-0.895987/-1` | 1.7443 | `1.7443/1` | 2.64029 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.39283 | `-1.39283/-1` | -2.54808 | `False` | `False` | `False` | `False` | `0.0399061/-0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.31191 | `-1.31191/-1` | -2.47093 | `False` | `False` | `False` | `False` | `0.0399061/-0` |
| `upper_edge_face` | 20 | `8-9` | `-0.521241/-1` | 1.94822 | `1.94822/1` | 2.46946 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 22 | `8-9` | `-0.717076/-1` | 1.67832 | `1.67832/1` | 2.3954 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.57004 | `-1.57004/-1` | -2.28275 | `False` | `False` | `False` | `False` | `1.0237/-0` |
| `upper_edge_face` | 21 | `8-9` | `-0.57985/-1` | 1.68093 | `1.68093/1` | 2.26078 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93534 | `1.93534/1` | 2.23139 | `False` | `False` | `False` | `False` | `-0/-0.902847` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.862753 | `0.862753/1` | 2.00984 | `False` | `False` | `False` | `False` | `-11.5289/-1.61865` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.17939 | `-1.17939/-1` | -1.81164 | `False` | `False` | `False` | `False` | `2.7913/11.2856` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ reconstructed upstream lateral volume-flux deltas exceed the diagnostic threshold.
- C++ reconstructed normal momentum plus bed-source balance deltas exceed the diagnostic threshold.
- C++ internal y-face Riemann/post-source flux signs still disagree with the GeoClaw final-frame edge flow.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; reconstructed q delta is -0.706344 m3/s and balance delta is -9.44548 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 5 rows 1-2; post-source q delta is 0.212033 m3/s.
