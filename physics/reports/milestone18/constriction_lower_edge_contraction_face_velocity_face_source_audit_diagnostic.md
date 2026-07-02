# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_lower_edge_contraction_face_velocity/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_lower_edge_contraction_face_velocity/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `1.54926` m3/s
- Max abs flux/source balance delta: `14.2326` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `49`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.961539/1.56938/0.44275/0.425722` | -1.54926 | `1->1` | `-3.9583/-0.329613/-4.28791` | `6.19706/5.71721` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.974059/1.46197/0.783716/0.763386` | -1.28232 | `1->1` | `-5.28081/-4.39366/-9.67447` | `5.1293/12.8993` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.979897/1.61885/0.411986/0.403704` | -0.913169 | `1->1` | `-1.85357/-0.612333/-2.46591` | `3.65268/3.28788` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.46304/1.51289/-0.791854/-1.15852` | 0.849155 | `-1->-1` | `0.629513/0/0.629513` | `3.39662/0.839351` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.966831/1.36694/0.678499/0.655993` | -0.806964 | `1->1` | `-4.30653/-5.48426/-9.79079` | `3.22786/13.0544` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.50401/1.71552/-0.995996/-1.49799` | 0.800635 | `-1->-1` | `2.21042/0/2.21042` | `3.20254/2.94723` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.874047/1.74131/0.807057/0.705406` | 0.631096 | `1->1` | `3.73631/10.4963/14.2326` | `2.52438/18.9768` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.48068/1.57177/-0.735582/-1.08916` | 0.580368 | `-1->-1` | `2.60276/0/2.60276` | `2.32147/3.47034` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.787262/1.66662/0.814574/0.641283` | 0.579767 | `1->1` | `3.01365/8.95235/11.966` | `2.31907/15.9547` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.968163/1.36545/0.726944/0.7038` | 0.467674 | `1->1` | `-1.48231/-3.6656/-5.14791` | `1.87069/6.86389` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.54402/1.77318/-1.03286/-1.59475` | 0.31653 | `-1->-1` | `4.46495/0/4.46495` | `1.26612/5.95327` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.49672/1.66121/-0.654852/-0.980132` | 0.302591 | `-1->-1` | `4.10525/0/4.10525` | `1.21036/5.47367` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.86676 | `-1.86676/-1` | -3.02578 | `False` | `False` | `False` | `False` | `0.0498792/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.70014 | `-1.70014/-1` | -2.8554 | `False` | `False` | `False` | `False` | `0.0498792/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.43412 | `1.43411/1` | 2.75389 | `False` | `False` | `True` | `True` | `-12.6459/-1.61865` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.43383 | `2.43383/1` | 2.51935 | `False` | `False` | `False` | `False` | `-9.88794/0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.37751 | `2.37751/1` | 2.49502 | `False` | `False` | `False` | `False` | `-9.92292/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.3998 | `2.3998/1` | 2.49372 | `False` | `False` | `False` | `False` | `-9.90629/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.38445 | `2.38445/1` | 2.49243 | `False` | `False` | `False` | `False` | `-9.91681/0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.12377 | `1.12377/1` | 2.27086 | `False` | `False` | `False` | `False` | `-11.8193/-1.61865` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.9354 | `1.9354/1` | 2.23146 | `False` | `False` | `False` | `False` | `-0/-0.902615` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 0.882001 | `0.881761/1` | 2.06326 | `False` | `False` | `True` | `True` | `-9.83845/-1.61865` |
| `upper_outer_face` | 10 | `7-8` | `-0.269081/-1` | 1.68281 | `1.68281/1` | 1.95189 | `False` | `False` | `False` | `False` | `-9.75381/0` |

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

- Start with `lower_edge_face` column 1 rows 1-2; reconstructed q delta is -1.54926 m3/s and balance delta is -4.28791 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 1 rows 1-2; post-source q delta is 0.0865891 m3/s.
