# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_broad_interior_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_broad_interior_final_profile/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `1.00669` m3/s
- Max abs flux/source balance delta: `12.8095` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `43`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.97838/1.81108/1.27028/1.24282` | 1.00669 | `1->1` | `-0.317665/-3.46515/-3.78282` | `4.02676/5.04376` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `0.994045/2.01431/1.58365/1.57422` | 0.750328 | `1->1` | `1.16167/-1.34699/-0.185321` | `3.00131/0.247094` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.825756/1.44208/0.77533/0.640233` | 0.565923 | `1->1` | `3.26077/9.54877/12.8095` | `2.26369/17.0794` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.65228/1.30108/-1.19257/-1.97047` | -0.563119 | `-1->-1` | `-2.12665/0/-2.12665` | `2.25248/2.83553` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.09089/2.1181/1.7212/1.87765` | 0.560777 | `1->1` | `2.33933/1.56541/3.90474` | `2.24311/5.20632` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.972844/1.64186/0.968376/0.942078` | -0.520879 | `1->1` | `-3.78213/-5.36628/-9.14841` | `2.08351/12.1979` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.45814/1.63839/-0.838793/-1.22308` | 0.446454 | `-1->-1` | `2.50254/0/2.50254` | `1.78581/3.33672` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.668488/1.44208/0.729291/0.487522` | 0.426006 | `1->1` | `1.99872/6.62201/8.62073` | `1.70402/11.4943` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.46158/1.09109/-1.19192/-1.74209` | -0.373767 | `-1->-1` | `5.90731/0/5.90731` | `1.49507/7.87642` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.20902/2.4446/-1.80658/-2.18418` | -0.272903 | `-1->-1` | `2.23996/0/2.23996` | `1.09161/2.98662` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.15978/2.40934/-1.77371/-2.05711` | 0.241511 | `-1->-1` | `-0.130492/0/-0.130492` | `0.966043/0.17399` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.44003/1.88391/-1.10283/-1.58811` | -0.21984 | `-1->-1` | `4.41998/0/4.41998` | `0.879358/5.89331` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.71614 | `1.71612/1` | 3.0359 | `False` | `False` | `True` | `True` | `-12.4652/-1.63696` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.41109 | `-1.41109/-1` | -2.56634 | `False` | `False` | `False` | `False` | `0.0395283/-0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.30789 | `-1.30789/-1` | -2.4669 | `False` | `False` | `False` | `False` | `0.0395283/-0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93602 | `1.93602/1` | 2.23207 | `False` | `False` | `False` | `False` | `-0/-0.903064` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.36691 | `-1.36691/-1` | -2.07963 | `False` | `False` | `False` | `False` | `0.859349/-0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.862717 | `0.862717/1` | 2.00981 | `False` | `False` | `False` | `False` | `-11.5287/-1.61865` |
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

- Start with `lower_edge_face` column 4 rows 1-2; reconstructed q delta is 1.00669 m3/s and balance delta is -3.78282 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 4 rows 1-2; post-source q delta is 1.80166 m3/s.
