# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_shallow_edge_source_scope/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_shallow_edge_source_scope/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `1.15354` m3/s
- Max abs flux/source balance delta: `14.1035` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `49`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.945207/1.74856/0.869064/0.821446` | -1.15354 | `1->1` | `-3.58563/-0.650032/-4.23567` | `4.61416/5.64756` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.963984/1.68253/1.16701/1.12498` | -0.920726 | `1->1` | `-4.66199/-4.59132/-9.25331` | `3.6829/12.3377` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.963112/1.38424/0.711525/0.685279` | -0.777678 | `1->1` | `-4.29923/-5.55722/-9.85645` | `3.11071/13.1419` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.964355/1.44489/0.909924/0.87749` | 0.641363 | `1->1` | `-1.23159/-3.74032/-4.97191` | `2.56545/6.62921` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.869434/1.73897/0.809849/0.70411` | 0.6298 | `1->1` | `3.69778/10.4057/14.1035` | `2.5192/18.8047` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.47245/1.57802/-0.740111/-1.08978` | 0.579754 | `-1->-1` | `2.48892/0/2.48892` | `2.31901/3.31857` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.781701/1.66585/0.815394/0.637394` | 0.575878 | `1->1` | `2.96821/8.84325/11.8115` | `2.30351/15.7486` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.968434/1.76843/0.837128/0.810703` | -0.50617 | `1->1` | `-1.45078/-0.837246/-2.28803` | `2.02468/3.05071` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.5148/2.47743/-1.52429/-2.30899` | -0.397714 | `-1->-1` | `5.89899/0/5.89899` | `1.59086/7.86532` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.48948/1.67041/-0.652817/-0.972359` | 0.310364 | `-1->-1` | `3.99214/0/3.99214` | `1.24145/5.32286` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `0.97437/1.54954/1.12437/1.09555` | 0.271657 | `1->1` | `-0.28951/-1.733/-2.02251` | `1.08663/2.69668` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.50691/1.64252/-0.757517/-1.14151` | 0.226767 | `-1->-1` | `4.49994/0/4.49994` | `0.907067/5.99992` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.88452 | `-1.88452/-1` | -3.04354 | `False` | `False` | `False` | `False` | `0.0397474/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.81802 | `-1.81802/-1` | -2.97327 | `False` | `False` | `False` | `False` | `0.0397474/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.3973 | `1.39728/1` | 2.71706 | `False` | `False` | `True` | `True` | `-12.4567/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.10453 | `1.10453/1` | 2.25162 | `False` | `False` | `False` | `False` | `-11.7024/-1.61865` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93602 | `1.93602/1` | 2.23207 | `False` | `False` | `False` | `False` | `-0/-0.903065` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.10905 | `2.10905/1` | 2.22656 | `False` | `False` | `False` | `False` | `-9.60881/0` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.1408 | `2.1408/1` | 2.22632 | `False` | `False` | `False` | `False` | `-9.69928/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.067 | `2.067/1` | 2.17498 | `False` | `False` | `False` | `False` | `-9.48487/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.06634 | `2.06634/1` | 2.16026 | `False` | `False` | `False` | `False` | `-9.48275/0` |
| `lower_edge_face` | 19 | `1-2` | `0.255654/1` | -1.68758 | `-1.68758/-1` | -1.94324 | `False` | `False` | `False` | `False` | `1.66679/10.5104` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 1.07075 | `1.07075/1` | 1.90848 | `False` | `False` | `False` | `False` | `-10.7525/-1.61865` |

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

- Start with `lower_edge_face` column 1 rows 1-2; reconstructed q delta is -1.15354 m3/s and balance delta is -4.23567 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 1 rows 1-2; post-source q delta is 0.358457 m3/s.
