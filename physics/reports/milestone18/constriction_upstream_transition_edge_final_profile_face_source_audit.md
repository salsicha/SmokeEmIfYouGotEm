# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_transition_edge_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_transition_edge_final_profile/finite_volume_roe/scenario/constriction_seed_16`
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
- Max abs flux/source balance delta: `12.8097` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `42`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.97838/1.81108/1.27028/1.24282` | 1.00669 | `1->1` | `-0.317662/-3.46515/-3.78281` | `4.02676/5.04375` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `0.994045/2.01431/1.58365/1.57422` | 0.750328 | `1->1` | `1.16167/-1.34698/-0.185312` | `3.00131/0.247083` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.825762/1.44208/0.77533/0.640238` | 0.565928 | `1->1` | `3.26083/9.5489/12.8097` | `2.26371/17.0796` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.65229/1.30108/-1.19257/-1.97047` | -0.563127 | `-1->-1` | `-2.12653/0/-2.12653` | `2.25251/2.83537` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.09089/2.1181/1.7212/1.87765` | 0.560777 | `1->1` | `2.33934/1.56541/3.90475` | `2.24311/5.20633` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.972844/1.64186/0.968376/0.942079` | -0.520878 | `1->1` | `-3.78213/-5.36628/-9.14841` | `2.08351/12.1979` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.45814/1.63839/-0.838793/-1.22308` | 0.446451 | `-1->-1` | `2.50259/0/2.50259` | `1.7858/3.33679` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.668492/1.44208/0.729291/0.487525` | 0.426009 | `1->1` | `1.99875/6.62208/8.62083` | `1.70403/11.4944` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.46158/1.09109/-1.19192/-1.74209` | -0.373776 | `-1->-1` | `5.90743/0/5.90743` | `1.4951/7.87658` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.20902/2.4446/-1.80658/-2.18419` | -0.272911 | `-1->-1` | `2.24002/0/2.24002` | `1.09164/2.9867` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.15978/2.40934/-1.77371/-2.05712` | 0.241503 | `-1->-1` | `-0.13043/0/-0.13043` | `0.966012/0.173907` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.44003/1.88391/-1.10283/-1.58812` | -0.219843 | `-1->-1` | `4.42003/0/4.42003` | `0.879372/5.89337` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.71615 | `1.71614/1` | 3.03592 | `False` | `False` | `True` | `True` | `-12.4653/-1.63696` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.41109 | `-1.41109/-1` | -2.56634 | `False` | `False` | `False` | `False` | `0.0397161/-0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.30789 | `-1.30789/-1` | -2.46691 | `False` | `False` | `False` | `False` | `0.0397161/-0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93601 | `1.93601/1` | 2.23207 | `False` | `False` | `False` | `False` | `-0/-0.903063` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.36691 | `-1.36691/-1` | -2.07963 | `False` | `False` | `False` | `False` | `0.859348/-0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.862731 | `0.862731/1` | 2.00982 | `False` | `False` | `False` | `False` | `-11.5288/-1.61865` |
| `lower_edge_face` | 19 | `1-2` | `0.255654/1` | -1.63752 | `-1.63752/-1` | -1.89318 | `False` | `False` | `False` | `False` | `1.66679/10.5059` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.17989 | `-1.17989/-1` | -1.81214 | `False` | `False` | `False` | `False` | `2.79197/11.2883` |
| `upper_edge_face` | 10 | `6-7` | `-1.60771/-1` | 0.123157 | `0.123157/1` | 1.73087 | `False` | `False` | `False` | `False` | `-0/-6.41666` |
| `lower_edge_face` | 11 | `3-4` | `0.372864/1` | -1.2493 | `-1.2493/-1` | -1.62216 | `False` | `False` | `False` | `False` | `2.80192/11.3285` |
| `lower_edge_face` | 20 | `1-2` | `0.090122/1` | -1.48992 | `-1.48992/-1` | -1.58005 | `False` | `False` | `False` | `False` | `1.66679/9.91752` |

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

- Start with `lower_edge_face` column 4 rows 1-2; reconstructed q delta is 1.00669 m3/s and balance delta is -3.78281 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 4 rows 1-2; post-source q delta is 1.80166 m3/s.
