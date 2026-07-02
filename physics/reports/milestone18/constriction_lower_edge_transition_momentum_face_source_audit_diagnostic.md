# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_lower_edge_transition_momentum_floor2/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_lower_edge_transition_momentum_floor2/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `1`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.44986` m3/s
- Max abs flux/source balance delta: `15.2796` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `52`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.01482/1.75026/-0.0336581/-0.0341567` | -0.385951 | `1->-1` | `-1.37468/-2.35707/-3.73175` | `1.5438/4.97567` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.928109/1.42929/0.565807/0.525131` | -1.44986 | `1->1` | `-4.15951/-0.985504/-5.14502` | `5.79942/6.86002` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.902388/1.31828/0.774878/0.69924` | -1.34647 | `1->1` | `-5.99692/-5.79985/-11.7968` | `5.38588/15.729` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.43625/1.47322/-0.765279/-1.09913` | 1.19949 | `-1->-1` | `0.582437/0/0.582437` | `4.79794/0.776582` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.36185/1.35102/-0.633916/-0.863296` | 1.14438 | `-1->-1` | `-1.1428/0/-1.1428` | `4.5775/1.52373` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.915121/1.34627/0.3766/0.344635` | -1.11832 | `1->1` | `-5.09916/-6.4988/-11.598` | `4.47329/15.4639` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.946714/1.48966/0.543562/0.514598` | -0.802275 | `1->1` | `-2.05376/-1.26339/-3.31715` | `3.2091/4.42287` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.47613/1.54246/-0.794376/-1.1726` | 0.738674 | `-1->-1` | `2.74363/0/2.74363` | `2.9547/3.65817` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.859434/1.73721/0.763649/0.656305` | 0.581995 | `1->1` | `3.54394/10.2095/13.7535` | `2.32798/18.338` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.76745/1.66654/0.762603/0.58526` | 0.523743 | `1->1` | `2.78652/8.56364/11.3502` | `2.09497/15.1335` |
| `lower_edge_face` | 6 | `1-2` | 6 | -4 | -2 | `1.39221/0.371742/0.523551/0.728892` | `0.907565/1.28682/0.292632/0.265582` | -0.463309 | `1->1` | `-5.77087/-9.50871/-15.2796` | `1.85324/20.3728` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.47511/1.52648/-0.861617/-1.27098` | 0.398548 | `-1->-1` | `2.81595/0/2.81595` | `1.59419/3.75461` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.7333 | `-1.7333/-1` | -2.89231 | `False` | `False` | `False` | `False` | `0.0230743/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.58274 | `-1.58274/-1` | -2.73799 | `False` | `False` | `False` | `False` | `0.0230743/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.23164 | `1.23162/1` | 2.5514 | `False` | `False` | `True` | `True` | `-12.2268/-1.61865` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.26397 | `2.26397/1` | 2.38148 | `False` | `False` | `False` | `False` | `-9.60356/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.25982 | `2.25982/1` | 2.3678 | `False` | `False` | `False` | `False` | `-9.56813/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.25702 | `2.25702/1` | 2.35094 | `False` | `False` | `False` | `False` | `-9.51127/0` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.26056 | `2.26056/1` | 2.34608 | `False` | `False` | `False` | `False` | `-9.41696/0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.92167 | `1.92167/1` | 2.21772 | `False` | `False` | `False` | `False` | `-0/-0.898231` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.981794 | `0.981794/1` | 2.12889 | `False` | `False` | `False` | `False` | `-11.4541/-1.61865` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 0.843635 | `0.843407/1` | 2.0249 | `False` | `False` | `True` | `True` | `-9.10875/-1.61865` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.30488 | `-1.30488/-1` | -1.93713 | `False` | `False` | `False` | `False` | `2.77703/11.2279` |

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
| 7 | `1->0` | `-1->-1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ reconstructed y-face volume flux signs do not match GeoClaw on one or more upstream edge faces.
- C++ reconstructed y-face x-momentum transport signs do not match GeoClaw.
- C++ reconstructed upstream lateral volume-flux deltas exceed the diagnostic threshold.
- C++ reconstructed normal momentum plus bed-source balance deltas exceed the diagnostic threshold.
- GeoClaw has opposite-signed lower/upper upstream edge fluxes that C++ still does not reproduce.
- C++ internal y-face Riemann/post-source flux signs still disagree with the GeoClaw final-frame edge flow.

## Next Levers

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.385951 m3/s and balance delta is -3.73175 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is 0.187652 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
