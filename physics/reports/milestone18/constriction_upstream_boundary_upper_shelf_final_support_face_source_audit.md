# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_boundary_upper_shelf_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_boundary_upper_shelf_final_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.706295` m3/s
- Max abs flux/source balance delta: `12.8157` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `47`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.973825/1.82678/0.777/0.756662` | -0.706295 | `1->1` | `-4.09712/-5.34704/-9.44416` | `2.82518/12.5922` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.825972/1.44208/0.77533/0.640401` | 0.566091 | `1->1` | `3.26265/9.55302/12.8157` | `2.26436/17.0876` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.65255/1.30109/-1.19258/-1.97079` | -0.563439 | `-1->-1` | `-2.12196/0/-2.12196` | `2.25376/2.82928` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.04939/1.90342/-1.78166/-1.86965` | 0.42897 | `-1->-1` | `-1.64433/0/-1.64433` | `1.71588/2.19244` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.668599/1.44208/0.729291/0.487603` | 0.426087 | `1->1` | `1.99951/6.62419/8.62371` | `1.70435/11.4983` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.33478/1.7686/-1.23586/-1.6496` | -0.417889 | `-1->-1` | `3.35503/0/3.35503` | `1.67155/4.47338` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.46198/1.09112/-1.19193/-1.74259` | -0.374269 | `-1->-1` | `5.91378/0/5.91378` | `1.49708/7.88504` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.38471/1.77357/-1.17964/-1.63346` | -0.350742 | `-1->-1` | `3.80726/0/3.80726` | `1.40297/5.07634` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.09076/2.29465/1.52206/1.6602` | 0.343326 | `1->1` | `1.63301/1.5628/3.19582` | `1.3733/4.26109` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.97788/2.52889/0.588992/0.575963` | 0.339837 | `1->1` | `-1.56195/-3.47496/-5.03691` | `1.35935/6.71589` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.30373/1.76675/-1.29524/-1.68865` | -0.320376 | `-1->-1` | `3.02144/0/3.02144` | `1.2815/4.02859` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `1.0709/2.13246/1.7062/1.82716` | -0.147824 | `1->1` | `0.060914/1.81599/1.8769` | `0.591297/2.50253` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.71908 | `1.71906/1` | 3.03884 | `False` | `False` | `True` | `True` | `-12.4777/-1.63696` |
| `upper_edge_face` | 23 | `8-9` | `-0.895987/-1` | 1.74533 | `1.74533/1` | 2.64132 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.39301 | `-1.39301/-1` | -2.54826 | `False` | `False` | `False` | `False` | `0.0405659/-0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.31211 | `-1.31211/-1` | -2.47112 | `False` | `False` | `False` | `False` | `0.0405659/-0` |
| `upper_edge_face` | 20 | `8-9` | `-0.521241/-1` | 1.94927 | `1.94927/1` | 2.47052 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 22 | `8-9` | `-0.717076/-1` | 1.67942 | `1.67942/1` | 2.39649 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.57034 | `-1.57034/-1` | -2.28305 | `False` | `False` | `False` | `False` | `1.02392/-0` |
| `upper_edge_face` | 21 | `8-9` | `-0.57985/-1` | 1.68203 | `1.68203/1` | 2.26188 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93536 | `1.93536/1` | 2.23141 | `False` | `False` | `False` | `False` | `-0/-0.902854` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.863242 | `0.863242/1` | 2.01033 | `False` | `False` | `False` | `False` | `-11.5316/-1.61865` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.17941 | `-1.17941/-1` | -1.81165 | `False` | `False` | `False` | `False` | `2.79132/11.2857` |

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

- Start with `lower_edge_face` column 5 rows 1-2; reconstructed q delta is -0.706295 m3/s and balance delta is -9.44416 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 5 rows 1-2; post-source q delta is 0.211979 m3/s.
