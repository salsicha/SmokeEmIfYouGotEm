# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_upper_core_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_upper_core_final_profile/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.986026` m3/s
- Max abs flux/source balance delta: `12.8096` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `44`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.978447/1.81978/1.24907/1.22215` | 0.986026 | `1->1` | `-0.369185/-3.46383/-3.83302` | `3.94411/5.11069` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `0.993893/2.01938/1.55615/1.54665` | 0.722751 | `1->1` | `1.07397/-1.34997/-0.275997` | `2.891/0.367996` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.825759/1.44208/0.77533/0.640236` | 0.565926 | `1->1` | `3.2608/9.54884/12.8096` | `2.2637/17.0795` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.65228/1.30108/-1.19257/-1.97047` | -0.563123 | `-1->-1` | `-2.12658/0/-2.12658` | `2.25249/2.83544` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.972987/1.6529/0.950749/0.925066` | -0.537891 | `1->1` | `-3.81354/-5.36348/-9.17702` | `2.15156/12.236` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.09073/2.1219/1.69665/1.85059` | 0.533717 | `1->1` | `2.24558/1.56222/3.8078` | `2.13487/5.07706` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.04335/1.90023/-1.78235/-1.85962` | 0.438996 | `-1->-1` | `-1.72284/0/-1.72284` | `1.75598/2.29712` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.668488/1.44208/0.729291/0.487522` | 0.426006 | `1->1` | `1.99872/6.62201/8.62073` | `1.70402/11.4943` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.33409/1.76861/-1.23611/-1.64908` | -0.417365 | `-1->-1` | `3.34578/0/3.34578` | `1.66946/4.46105` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.46158/1.09109/-1.19192/-1.74208` | -0.373766 | `-1->-1` | `5.90731/0/5.90731` | `1.49507/7.87641` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.3845/1.77357/-1.17967/-1.63326` | -0.350535 | `-1->-1` | `3.80419/0/3.80419` | `1.40214/5.07225` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.30396/1.76676/-1.29499/-1.68862` | -0.320346 | `-1->-1` | `3.02388/0/3.02388` | `1.28138/4.03184` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.71768 | `1.71766/1` | 3.03744 | `False` | `False` | `True` | `True` | `-12.4721/-1.63696` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.41109 | `-1.41109/-1` | -2.56634 | `False` | `False` | `False` | `False` | `0.039526/-0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.30789 | `-1.30789/-1` | -2.4669 | `False` | `False` | `False` | `False` | `0.039526/-0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93602 | `1.93602/1` | 2.23207 | `False` | `False` | `False` | `False` | `-0/-0.903064` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.36692 | `-1.36692/-1` | -2.07963 | `False` | `False` | `False` | `False` | `0.859349/-0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.862724 | `0.862724/1` | 2.00982 | `False` | `False` | `False` | `False` | `-11.5288/-1.61865` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 1.80723 | `1.80723/1` | 1.89276 | `False` | `False` | `False` | `False` | `-7.691/0` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.17989 | `-1.17989/-1` | -1.81214 | `False` | `False` | `False` | `False` | `2.79197/11.2883` |
| `lower_edge_face` | 19 | `1-2` | `0.255654/1` | -1.53414 | `-1.53414/-1` | -1.7898 | `False` | `False` | `False` | `False` | `1.66679/10.5076` |
| `upper_edge_face` | 10 | `6-7` | `-1.60771/-1` | 0.123156 | `0.123156/1` | 1.73087 | `False` | `False` | `False` | `False` | `-0/-6.41666` |
| `lower_edge_face` | 11 | `3-4` | `0.372864/1` | -1.2493 | `-1.2493/-1` | -1.62216 | `False` | `False` | `False` | `False` | `2.80192/11.3285` |

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

- Start with `lower_edge_face` column 4 rows 1-2; reconstructed q delta is 0.986026 m3/s and balance delta is -3.83302 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 4 rows 1-2; post-source q delta is 1.77706 m3/s.
