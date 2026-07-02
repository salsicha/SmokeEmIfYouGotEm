# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_transition_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_transition_final_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `1`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.88858` m3/s
- Max abs flux/source balance delta: `16.5518` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `54`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.03943/2.03661/-0.104854/-0.108988` | -0.460782 | `1->-1` | `-1.11637/-1.8741/-2.99048` | `1.84313/3.9873` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.749213/2.01782/0.20973/0.157133` | -1.88858 | `1->1` | `-7.74668/-8.80513/-16.5518` | `7.55431/22.0691` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.847628/2.07211/0.120092/0.101793` | -1.87319 | `1->1` | `-5.1454/-2.56454/-7.70993` | `7.49277/10.2799` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.38153/2.16688/-0.487882/-0.674025` | 1.6246 | `-1->-1` | `-0.686194/0/-0.686194` | `6.49838/0.914925` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.18856/2.11297/-0.403863/-0.480015` | 1.52766 | `-1->-1` | `-3.66397/0/-3.66397` | `6.11063/4.8853` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.898565/2.15717/0.0585877/0.0526449` | -1.26423 | `1->1` | `-2.7662/-2.20808/-4.97428` | `5.05691/6.63237` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.918257/1.62691/0.248263/0.22797` | -1.23499 | `1->1` | `-5.14416/-6.43728/-11.5814` | `4.93995/15.4419` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.48678/2.2425/-0.545247/-0.810663` | 1.10061 | `-1->-1` | `2.40896/0/2.40896` | `4.40245/3.21195` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.57848/1.97052/-0.455598/-0.719153` | 0.950378 | `-1->-1` | `3.59674/0/3.59674` | `3.80151/4.79566` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.57953/1.98234/-0.34771/-0.54922` | 0.819098 | `-1->-1` | `5.78139/0/5.78139` | `3.27639/7.70851` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.51677/2.26142/-0.451711/-0.685144` | 0.68313 | `-1->-1` | `4.09105/0/4.09105` | `2.73252/5.45474` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.56742/2.17088/-0.39241/-0.615072` | 0.667651 | `-1->-1` | `4.76738/0/4.76738` | `2.6706/6.35651` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.81865 | `1.81863/1` | 3.13841 | `False` | `False` | `True` | `True` | `-12.9436/-1.61865` |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.84455 | `-1.84455/-1` | -3.00357 | `False` | `False` | `False` | `False` | `0.0104931/-0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.70747 | `1.70747/1` | 2.85456 | `False` | `False` | `False` | `False` | `-12.1431/-1.61865` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.56192 | `-1.56192/-1` | -2.71717 | `False` | `False` | `False` | `False` | `0.0104931/-0` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 1.66087 | `1.66087/1` | 2.49859 | `False` | `False` | `False` | `False` | `-11.4813/-1.61865` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.21441 | `2.21441/1` | 2.33192 | `False` | `False` | `False` | `False` | `-9.47476/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.18298 | `2.18298/1` | 2.29097 | `False` | `False` | `False` | `False` | `-9.38013/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.13346 | `2.13346/1` | 2.22738 | `False` | `False` | `False` | `False` | `-9.2305/0` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.48315 | `-1.48315/-1` | -2.19586 | `False` | `False` | `False` | `False` | `1.07093/-0` |
| `upper_outer_face` | 10 | `7-8` | `-0.269081/-1` | 1.91272 | `1.91272/1` | 2.1818 | `False` | `False` | `False` | `False` | `-10.5147/0` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.04906 | `2.04906/1` | 2.13458 | `False` | `False` | `False` | `False` | `-8.9746/0` |

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
| 7 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
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

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.460782 m3/s and balance delta is -2.99048 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is 0.224797 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
