# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_outer_upper_shelf_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_outer_upper_shelf_final_profile/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.706346` m3/s
- Max abs flux/source balance delta: `12.8095` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `44`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.973779/1.82678/0.776984/0.756611` | -0.706346 | `1->1` | `-4.09761/-5.34794/-9.44555` | `2.82538/12.5941` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.825753/1.44208/0.77533/0.640231` | 0.565921 | `1->1` | `3.26074/9.54871/12.8095` | `2.26368/17.0793` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.65228/1.30108/-1.19257/-1.97046` | -0.563115 | `-1->-1` | `-2.1267/0/-2.1267` | `2.25246/2.83561` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.04339/1.90035/-1.78241/-1.85975` | 0.438873 | `-1->-1` | `-1.72216/0/-1.72216` | `1.75549/2.29622` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.668481/1.44208/0.729291/0.487517` | 0.426001 | `1->1` | `1.99868/6.62187/8.62055` | `1.704/11.4941` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.33463/1.76861/-1.23591/-1.64948` | -0.417766 | `-1->-1` | `3.353/0/3.353` | `1.67107/4.47066` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.46156/1.09109/-1.19192/-1.74207` | -0.373748 | `-1->-1` | `5.90707/0/5.90707` | `1.49499/7.87609` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.38456/1.77357/-1.17968/-1.63334` | -0.350615 | `-1->-1` | `3.80505/0/3.80505` | `1.40246/5.07341` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.09064/2.29456/1.52207/1.66003` | 0.343156 | `1->1` | `1.63146/1.56037/3.19183` | `1.37262/4.25577` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.977838/2.52889/0.588987/0.575934` | 0.339808 | `1->1` | `-1.56237/-3.47579/-5.03817` | `1.35923/6.71755` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.30359/1.76676/-1.29529/-1.68852` | -0.320246 | `-1->-1` | `3.01947/0/3.01947` | `1.28098/4.02596` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.02372/1.82299/-1.74097/-1.78226` | 0.225409 | `-1->-1` | `-2.54372/0/-2.54372` | `0.901638/3.39163` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.71765 | `1.71763/1` | 3.03741 | `False` | `False` | `True` | `True` | `-12.4719/-1.63696` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.39282 | `-1.39282/-1` | -2.54807 | `False` | `False` | `False` | `False` | `0.0394717/-0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.3119 | `-1.3119/-1` | -2.47091 | `False` | `False` | `False` | `False` | `0.0394717/-0` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.57003 | `-1.57003/-1` | -2.28274 | `False` | `False` | `False` | `False` | `1.02369/-0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93533 | `1.93533/1` | 2.23138 | `False` | `False` | `False` | `False` | `-0/-0.902845` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.862711 | `0.862711/1` | 2.0098 | `False` | `False` | `False` | `False` | `-11.5287/-1.61865` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 1.80723 | `1.80723/1` | 1.89275 | `False` | `False` | `False` | `False` | `-7.69099/0` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.17938 | `-1.17938/-1` | -1.81163 | `False` | `False` | `False` | `False` | `2.79129/11.2856` |
| `lower_edge_face` | 19 | `1-2` | `0.255654/1` | -1.53416 | `-1.53416/-1` | -1.78981 | `False` | `False` | `False` | `False` | `1.66679/10.5076` |
| `upper_edge_face` | 10 | `6-7` | `-1.60771/-1` | 0.123151 | `0.123151/1` | 1.73086 | `False` | `False` | `False` | `False` | `-0/-6.41665` |
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

- Start with `lower_edge_face` column 5 rows 1-2; reconstructed q delta is -0.706346 m3/s and balance delta is -9.44555 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 5 rows 1-2; post-source q delta is 0.212036 m3/s.
