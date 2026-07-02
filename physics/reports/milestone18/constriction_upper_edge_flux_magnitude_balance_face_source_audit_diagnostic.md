# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_upper_edge_flux_magnitude_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_upper_edge_flux_magnitude_balance/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `4`
- X-momentum sign mismatch count: `4`
- Opposition mismatch count: `4`
- Max abs lateral volume-flux delta: `2.05596` m3/s
- Max abs flux/source balance delta: `16.4093` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `59`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.846062/2.08263/-0.0957106/-0.0809771` | -2.05596 | `1->-1` | `-5.16288/-2.59526/-7.75814` | `8.22385/10.3442` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.755688/2.01767/0.0284899/0.0215295` | -2.02418 | `1->0` | `-7.73122/-8.6781/-16.4093` | `8.09672/21.8791` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.90328/2.15756/-0.169848/-0.153421` | -1.47029 | `1->-1` | `-2.70155/-2.11558/-4.81713` | `5.88117/6.42284` |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.03731/2.03032/-0.299122/-0.310282` | -0.662076 | `1->-1` | `-1.05661/-1.91576/-2.97237` | `2.64831/3.96316` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.38097/2.17265/-0.655538/-0.905281` | 1.39334 | `-1->-1` | `-0.429149/0/-0.429149` | `5.57336/0.572199` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.1924/2.11284/-0.536008/-0.639133` | 1.36854 | `-1->-1` | `-3.47045/0/-3.47045` | `5.47415/4.62727` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.928552/1.6108/0.129509/0.120256` | -1.3427 | `1->1` | `-5.09192/-6.23528/-11.3272` | `5.37081/15.1029` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.4926/2.24172/-0.725686/-1.08316` | 0.828115 | `-1->-1` | `2.83805/0/2.83805` | `3.31246/3.78407` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.5736/1.95128/-0.593448/-0.933852` | 0.735679 | `-1->-1` | `3.74787/0/3.74787` | `2.94272/4.99716` |
| `lower_edge_face` | 6 | `1-2` | 6 | -4 | -2 | `1.39221/0.371742/0.523551/0.728892` | `0.93866/1.48813/0.0767025/0.0719975` | -0.656894 | `1->1` | `-5.56147/-8.89863/-14.4601` | `2.62758/19.2801` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `0.913896/1.69589/0.197398/0.180401` | -0.643494 | `1->1` | `-2.04582/-2.91952/-4.96534` | `2.57398/6.62045` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.57795/1.9794/-0.524746/-0.828022` | 0.540297 | `-1->-1` | `6.00033/0/6.00033` | `2.16119/8.00044` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.84483 | `-1.84483/-1` | -3.00385 | `False` | `False` | `False` | `False` | `0.0105281/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.65403 | `1.65402/1` | 2.9738 | `False` | `False` | `True` | `True` | `-12.9096/-1.61865` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.56213 | `-1.56213/-1` | -2.71738 | `False` | `False` | `False` | `False` | `0.0105281/-0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.54468 | `1.54468/1` | 2.69177 | `False` | `False` | `False` | `False` | `-12.126/-1.61865` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | -2.94069 | `-1.99143/-1` | -2.34323 | `True` | `True` | `True` | `True` | `1.98653/13.2775` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 1.49793 | `1.49793/1` | 2.33565 | `False` | `False` | `False` | `False` | `-11.4698/-1.61865` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.21465 | `2.21465/1` | 2.33216 | `False` | `False` | `False` | `False` | `-9.47546/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.18326 | `2.18326/1` | 2.29125 | `False` | `False` | `False` | `False` | `-9.38094/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.13378 | `2.13378/1` | 2.2277 | `False` | `False` | `False` | `False` | `-9.23144/0` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.48348 | `-1.48348/-1` | -2.19619 | `False` | `False` | `False` | `False` | `1.07113/-0` |
| `upper_outer_face` | 10 | `7-8` | `-0.269081/-1` | 1.90842 | `1.90842/1` | 2.1775 | `False` | `False` | `False` | `False` | `-10.5008/0` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->0` | `-1->-1` | `True` | `False` | `False` |
| 1 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 2 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
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

- Start with `lower_edge_face` column 1 rows 1-2; reconstructed q delta is -2.05596 m3/s and balance delta is -7.75814 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 1 rows 1-2; post-source q delta is -0.31461 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
