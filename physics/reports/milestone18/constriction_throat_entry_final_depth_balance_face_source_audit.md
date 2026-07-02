# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_throat_entry_final_depth_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_throat_entry_final_depth_balance/finite_volume_roe/scenario/constriction_seed_16`
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
- Max abs flux/source balance delta: `14.1035` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `44`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.97838/1.81108/1.27028/1.24282` | 1.00669 | `1->1` | `-0.317659/-3.46515/-3.7828` | `4.02676/5.04374` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `0.994045/2.01431/1.58365/1.57422` | 0.750328 | `1->1` | `1.16167/-1.34698/-0.185307` | `3.00131/0.247076` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.869434/1.73897/0.809849/0.70411` | 0.6298 | `1->1` | `3.69778/10.4057/14.1035` | `2.5192/18.8047` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.781699/1.66585/0.815393/0.637392` | 0.575876 | `1->1` | `2.96819/8.84321/11.8114` | `2.3035/15.7485` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.09089/2.1181/1.7212/1.87765` | 0.560778 | `1->1` | `2.33934/1.56542/3.90476` | `2.24311/5.20635` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.972835/1.64188/0.968375/0.942069` | -0.520888 | `1->1` | `-3.78222/-5.36645/-9.14867` | `2.08355/12.1982` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.45446/1.64473/-0.839028/-1.22034` | 0.449193 | `-1->-1` | `2.44804/0/2.44804` | `1.79677/3.26405` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.20902/2.4446/-1.80658/-2.18419` | -0.272917 | `-1->-1` | `2.24008/0/2.24008` | `1.09167/2.98677` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.15979/2.40934/-1.77371/-2.05712` | 0.241496 | `-1->-1` | `-0.130368/0/-0.130368` | `0.965983/0.173824` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.44004/1.88391/-1.10283/-1.58812` | -0.219845 | `-1->-1` | `4.42006/0/4.42006` | `0.879381/5.89341` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.5142/1.50395/-0.770507/-1.1667` | 0.201619 | `-1->-1` | `5.49791/0/5.49791` | `0.806476/7.33055` |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.02912/1.53738/0.170312/0.175272` | -0.176522 | `1->1` | `-1.20253/-2.07635/-3.27888` | `0.70609/4.37184` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.88327 | `-1.88327/-1` | -3.04228 | `False` | `False` | `False` | `False` | `0.0397685/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.818 | `-1.818/-1` | -2.97325 | `False` | `False` | `False` | `False` | `0.0397685/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.35659 | `1.35657/1` | 2.67635 | `False` | `False` | `True` | `True` | `-12.4163/-1.63642` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.10453 | `1.10453/1` | 2.25162 | `False` | `False` | `False` | `False` | `-11.7024/-1.61865` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93601 | `1.93601/1` | 2.23207 | `False` | `False` | `False` | `False` | `-0/-0.903063` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.37325 | `-1.37325/-1` | -2.08596 | `False` | `False` | `False` | `False` | `0.861669/-0` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 1.07075 | `1.07075/1` | 1.90847 | `False` | `False` | `False` | `False` | `-10.7524/-1.61865` |
| `lower_edge_face` | 19 | `1-2` | `0.255654/1` | -1.63744 | `-1.63744/-1` | -1.89309 | `False` | `False` | `False` | `False` | `1.66679/10.5055` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.17989 | `-1.17989/-1` | -1.81214 | `False` | `False` | `False` | `False` | `2.79197/11.2883` |
| `upper_edge_face` | 10 | `6-7` | `-1.60771/-1` | 0.126335 | `0.126335/1` | 1.73405 | `False` | `False` | `False` | `False` | `-0/-6.40131` |
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

- Start with `lower_edge_face` column 4 rows 1-2; reconstructed q delta is 1.00669 m3/s and balance delta is -3.7828 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 4 rows 1-2; post-source q delta is 1.80166 m3/s.
