# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_throat_transfer_off_center/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_throat_transfer_off_center/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `1.14704` m3/s
- Max abs flux/source balance delta: `14.2148` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `49`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.961335/1.72889/0.861247/0.827947` | -1.14704 | `1->1` | `-3.43564/-0.333615/-3.76926` | `4.58816/5.02567` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.972965/1.66537/1.15859/1.12727` | -0.918444 | `1->1` | `-4.5835/-4.41512/-8.99862` | `3.67378/11.9982` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.966505/1.38001/0.716337/0.692343` | -0.770614 | `1->1` | `-4.25876/-5.49066/-9.74942` | `3.08245/12.9992` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.967395/1.44047/0.914055/0.884252` | 0.648126 | `1->1` | `-1.19297/-3.68068/-4.87365` | `2.5925/6.4982` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.873412/1.74118/0.807424/0.705214` | 0.630904 | `1->1` | `3.73097/10.4838/14.2148` | `2.52362/18.953` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.4799/1.57177/-0.734825/-1.08747` | 0.582063 | `-1->-1` | `2.58933/0/2.58933` | `2.32825/3.45244` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.786697/1.66644/0.814701/0.640923` | 0.579407 | `1->1` | `3.00908/8.94127/11.9504` | `2.31763/15.9338` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.979578/1.75373/0.827392/0.810495` | -0.506379 | `1->1` | `-1.35237/-0.618608/-1.97098` | `2.02551/2.62797` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.53094/2.4484/-1.53607/-2.35163` | -0.440357 | `-1->-1` | `6.23283/0/6.23283` | `1.76143/8.31044` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.49601/1.66127/-0.642557/-0.96127` | 0.321452 | `-1->-1` | `4.07061/0/4.07061` | `1.28581/5.42748` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `0.976066/1.54673/1.12434/1.09743` | 0.273533 | `1->1` | `-0.271217/-1.69974/-1.97096` | `1.09413/2.62794` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.51038/1.62969/-0.752885/-1.13714` | 0.231129 | `-1->-1` | `4.54281/0/4.54281` | `0.924516/6.05708` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.92271 | `-1.92271/-1` | -3.08173 | `False` | `False` | `False` | `False` | `0.0454577/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.852 | `-1.852/-1` | -3.00725 | `False` | `False` | `False` | `False` | `0.0454577/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.43217 | `1.43215/1` | 2.75194 | `False` | `False` | `True` | `True` | `-12.635/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.12115 | `1.12115/1` | 2.26824 | `False` | `False` | `False` | `False` | `-11.8035/-1.61865` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.17947 | `2.17947/1` | 2.26499 | `False` | `False` | `False` | `False` | `-9.81183/0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.13538 | `2.13538/1` | 2.25289 | `False` | `False` | `False` | `False` | `-9.68589/0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.94283 | `1.94283/1` | 2.23889 | `False` | `False` | `False` | `False` | `-0/-0.905235` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.09399 | `2.09399/1` | 2.20198 | `False` | `False` | `False` | `False` | `-9.56444/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.09669 | `2.09669/1` | 2.19061 | `False` | `False` | `False` | `False` | `-9.57222/0` |
| `lower_edge_face` | 19 | `1-2` | `0.255654/1` | -1.72533 | `-1.72533/-1` | -1.98099 | `False` | `False` | `False` | `False` | `1.66679/10.6528` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 1.08409 | `1.08409/1` | 1.92181 | `False` | `False` | `False` | `False` | `-10.8219/-1.61865` |

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

- Start with `lower_edge_face` column 1 rows 1-2; reconstructed q delta is -1.14704 m3/s and balance delta is -3.76926 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 1 rows 1-2; post-source q delta is 0.337361 m3/s.
