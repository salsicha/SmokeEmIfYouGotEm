# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_edge_downstream_strong/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_edge_downstream_strong/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `1.54937` m3/s
- Max abs flux/source balance delta: `14.2114` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `51`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.961002/1.56967/0.442884/0.425613` | -1.54937 | `1->1` | `-3.96335/-0.340139/-4.30349` | `6.19749/5.73798` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.973739/1.46234/0.783902/0.763316` | -1.28239 | `1->1` | `-5.28378/-4.39994/-9.68373` | `5.12958/12.9116` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.979316/1.61886/0.412033/0.403511` | -0.913363 | `1->1` | `-1.85922/-0.623746/-2.48297` | `3.65345/3.31063` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.46231/1.51336/-0.791592/-1.15756` | 0.850116 | `-1->-1` | `0.61797/0/0.61797` | `3.40046/0.82396` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.96627/1.36691/0.678397/0.655514` | -0.807443 | `1->1` | `-4.31224/-5.49526/-9.8075` | `3.22977/13.0767` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.50289/1.71587/-0.995701/-1.49643` | 0.802194 | `-1->-1` | `2.19189/0/2.19189` | `3.20878/2.92252` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.873293/1.74113/0.80746/0.705149` | 0.630839 | `1->1` | `3.72992/10.4815/14.2114` | `2.52335/18.9485` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.47964/1.57176/-0.735433/-1.08817` | 0.581357 | `-1->-1` | `2.58669/0/2.58669` | `2.32543/3.44891` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.786528/1.66641/0.814687/0.640774` | 0.579258 | `1->1` | `3.00764/8.93795/11.9456` | `2.31703/15.9275` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.967609/1.36539/0.726831/0.703288` | 0.467162 | `1->1` | `-1.48803/-3.67648/-5.16451` | `1.86865/6.88602` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.5428/1.7732/-1.03263/-1.59315` | 0.31813 | `-1->-1` | `4.44455/0/4.44455` | `1.27252/5.92606` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.49563/1.66126/-0.654698/-0.979188` | 0.303535 | `-1->-1` | `4.0885/0/4.0885` | `1.21414/5.45133` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.90391 | `-1.90391/-1` | -3.06293 | `False` | `False` | `False` | `False` | `0.0449663/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.765 | `-1.765/-1` | -2.92025 | `False` | `False` | `False` | `False` | `0.0449663/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.4312 | `1.43119/1` | 2.75097 | `False` | `False` | `True` | `True` | `-12.6304/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.12056 | `1.12056/1` | 2.26765 | `False` | `False` | `False` | `False` | `-11.8003/-1.61865` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.17934 | `2.17934/1` | 2.26486 | `False` | `False` | `False` | `False` | `-9.81146/0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.13444 | `2.13444/1` | 2.25195 | `False` | `False` | `False` | `False` | `-9.68316/0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.9401 | `1.9401/1` | 2.23615 | `False` | `False` | `False` | `False` | `-0/-0.904111` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.09312 | `2.09312/1` | 2.2011 | `False` | `False` | `False` | `False` | `-9.56188/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.09597 | `2.09597/1` | 2.1899 | `False` | `False` | `False` | `False` | `-9.57012/0` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 0.881274 | `0.881033/1` | 2.06253 | `False` | `False` | `True` | `True` | `-9.8334/-1.61865` |
| `lower_edge_face` | 19 | `1-2` | `0.255654/1` | -1.72668 | `-1.72668/-1` | -1.98233 | `False` | `False` | `False` | `False` | `1.66679/10.6579` |

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

- Start with `lower_edge_face` column 1 rows 1-2; reconstructed q delta is -1.54937 m3/s and balance delta is -4.30349 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 1 rows 1-2; post-source q delta is 0.0874451 m3/s.
