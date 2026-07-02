# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_downstream_upper_intermediate/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_downstream_upper_intermediate/finite_volume_roe/scenario/constriction_seed_16`
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
- Max abs flux/source balance delta: `14.2147` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `51`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.961187/1.56967/0.442921/0.42573` | -1.54926 | `1->1` | `-3.96154/-0.336515/-4.29805` | `6.19702/5.73074` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.973879/1.46229/0.78388/0.763404` | -1.28231 | `1->1` | `-5.2824/-4.3972/-9.67959` | `5.12922/12.9061` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.979488/1.61892/0.412084/0.403631` | -0.913242 | `1->1` | `-1.8575/-0.620369/-2.47787` | `3.65297/3.30383` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.46265/1.51331/-0.791653/-1.15791` | 0.849765 | `-1->-1` | `0.623076/0/0.623076` | `3.39906/0.830768` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.966388/1.36692/0.678433/0.65563` | -0.807327 | `1->1` | `-4.31102/-5.49295/-9.80397` | `3.22931/13.072` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.50328/1.71588/-0.99572/-1.49685` | 0.801772 | `-1->-1` | `2.19818/0/2.19818` | `3.20709/2.93091` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.873411/1.74118/0.807424/0.705213` | 0.630903 | `1->1` | `3.73096/10.4838/14.2147` | `2.52361/18.953` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.47988/1.57177/-0.735431/-1.08835` | 0.581183 | `-1->-1` | `2.59029/0/2.59029` | `2.32473/3.45372` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.786694/1.66643/0.814701/0.64092` | 0.579404 | `1->1` | `3.00905/8.9412/11.9503` | `2.31762/15.9337` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.967721/1.36541/0.726868/0.703406` | 0.467279 | `1->1` | `-1.48685/-3.67427/-5.16112` | `1.86912/6.88149` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.54317/1.77327/-1.03264/-1.59353` | 0.317745 | `-1->-1` | `4.45048/0/4.45048` | `1.27098/5.93398` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.49586/1.66126/-0.654699/-0.979338` | 0.303384 | `-1->-1` | `4.09196/0/4.09196` | `1.21354/5.45595` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.92271 | `-1.92271/-1` | -3.08173 | `False` | `False` | `False` | `False` | `0.0454406/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.852 | `-1.852/-1` | -3.00725 | `False` | `False` | `False` | `False` | `0.0454406/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.43213 | `1.43212/1` | 2.7519 | `False` | `False` | `True` | `True` | `-12.6349/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.12114 | `1.12114/1` | 2.26823 | `False` | `False` | `False` | `False` | `-11.8034/-1.61865` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.17947 | `2.17947/1` | 2.26499 | `False` | `False` | `False` | `False` | `-9.81182/0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.13538 | `2.13538/1` | 2.25289 | `False` | `False` | `False` | `False` | `-9.68588/0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.94362 | `1.94362/1` | 2.23968 | `False` | `False` | `False` | `False` | `-0/-0.905234` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.09398 | `2.09398/1` | 2.20197 | `False` | `False` | `False` | `False` | `-9.56442/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.09668 | `2.09668/1` | 2.19061 | `False` | `False` | `False` | `False` | `-9.5722/0` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 0.881647 | `0.881407/1` | 2.0629 | `False` | `False` | `True` | `True` | `-9.83562/-1.61865` |
| `lower_edge_face` | 19 | `1-2` | `0.255654/1` | -1.72533 | `-1.72533/-1` | -1.98098 | `False` | `False` | `False` | `False` | `1.66679/10.6528` |

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

- Start with `lower_edge_face` column 1 rows 1-2; reconstructed q delta is -1.54926 m3/s and balance delta is -4.29805 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 1 rows 1-2; post-source q delta is 0.0872085 m3/s.
