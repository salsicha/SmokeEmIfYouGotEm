# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_lower_edge_transition_source_depth/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_lower_edge_transition_source_depth/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.52479` m3/s
- Max abs flux/source balance delta: `14.1467` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `50`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.03349/1.7463/0.0280376/0.0289766` | -0.322818 | `1->1` | `-1.18738/-1.99065/-3.17803` | `1.29127/4.23737` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.961589/1.54679/0.468176/0.450193` | -1.52479 | `1->1` | `-3.93554/-0.328628/-4.26417` | `6.09917/5.68556` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.974992/1.44637/0.80105/0.781018` | -1.26469 | `1->1` | `-5.24453/-4.37534/-9.61987` | `5.05877/12.8265` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.46499/1.47684/-0.753943/-1.10452` | 0.903155 | `-1->-1` | `0.572791/0/0.572791` | `3.61262/0.763721` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.978178/1.59715/0.433916/0.424447` | -0.892426 | `1->1` | `-1.85223/-0.646067/-2.4983` | `3.5697/3.33107` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.50408/1.67282/-0.950583/-1.42975` | 0.86887 | `-1->-1` | `2.07857/0/2.07857` | `3.47548/2.77142` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.966001/1.36629/0.633701/0.612155` | -0.850802 | `1->1` | `-4.37157/-5.50055/-9.87212` | `3.40321/13.1628` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.873303/1.74091/0.759964/0.663679` | 0.589369 | `1->1` | `3.665/10.4816/14.1467` | `2.35748/18.8622` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.786306/1.66643/0.760839/0.598253` | 0.536736 | `1->1` | `2.93908/8.93361/11.8727` | `2.14694/15.8302` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.47884/1.57048/-0.800453/-1.18374` | 0.485786 | `-1->-1` | `2.72242/0/2.72242` | `1.94314/3.62989` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.966536/1.36408/0.727277/0.70294` | 0.466813 | `1->1` | `-1.49815/-3.69753/-5.19568` | `1.86725/6.92757` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.54054/1.73148/-0.993782/-1.53096` | 0.380314 | `-1->-1` | `4.28668/0/4.28668` | `1.52126/5.71557` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.86029 | `-1.86029/-1` | -3.01931 | `False` | `False` | `False` | `False` | `0.0487429/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.69441 | `-1.69441/-1` | -2.84966 | `False` | `False` | `False` | `False` | `0.0487429/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.32628 | `1.32626/1` | 2.64604 | `False` | `False` | `True` | `True` | `-12.6161/-1.61865` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.42545 | `2.42545/1` | 2.51097 | `False` | `False` | `False` | `False` | `-9.86558/0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.37233 | `2.37233/1` | 2.48984 | `False` | `False` | `False` | `False` | `-9.90847/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.39297 | `2.39297/1` | 2.48689 | `False` | `False` | `False` | `False` | `-9.88766/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.37864 | `2.37864/1` | 2.48663 | `False` | `False` | `False` | `False` | `-9.90074/0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93371 | `1.93371/1` | 2.22977 | `False` | `False` | `False` | `False` | `-0/-0.902076` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.04365 | `1.04365/1` | 2.19074 | `False` | `False` | `False` | `False` | `-11.8004/-1.61865` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 0.909424 | `0.909181/1` | 2.09068 | `False` | `False` | `True` | `True` | `-9.8534/-1.61865` |
| `upper_outer_face` | 10 | `7-8` | `-0.269081/-1` | 1.6785 | `1.6785/1` | 1.94758 | `False` | `False` | `False` | `False` | `-9.7392/0` |

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
- C++ reconstructed upstream lateral volume-flux deltas exceed the diagnostic threshold.
- C++ reconstructed normal momentum plus bed-source balance deltas exceed the diagnostic threshold.
- GeoClaw has opposite-signed lower/upper upstream edge fluxes that C++ still does not reproduce.
- C++ internal y-face Riemann/post-source flux signs still disagree with the GeoClaw final-frame edge flow.

## Next Levers

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.322818 m3/s and balance delta is -3.17803 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is 0.199919 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
