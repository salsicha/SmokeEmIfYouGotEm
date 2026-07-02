# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upper_edge_boundary_window2_late_shape_soft/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upper_edge_boundary_window2_late_shape_soft/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `1`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.5249` m3/s
- Max abs flux/source balance delta: `14.8858` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `50`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.02985/1.75982/-0.0496483/-0.0511303` | -0.402925 | `1->-1` | `-1.22251/-2.06209/-3.2846` | `1.6117/4.37947` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.961275/1.54723/0.468221/0.450089` | -1.5249 | `1->1` | `-3.93853/-0.334797/-4.27333` | `6.09959/5.69778` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.974839/1.44655/0.801109/0.780952` | -1.26476 | `1->1` | `-5.24601/-4.37836/-9.62436` | `5.05903/12.8325` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.931056/1.35029/0.375757/0.349851` | -1.11311 | `1->1` | `-4.95319/-6.18616/-11.1393` | `4.45243/14.8525` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.46465/1.47706/-0.753842/-1.10411` | 0.903561 | `-1->-1` | `0.567467/0/0.567467` | `3.61424/0.756623` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.977672/1.598/0.433857/0.424169` | -0.892704 | `1->1` | `-1.85724/-0.656003/-2.51324` | `3.57082/3.35099` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.50344/1.67333/-0.95044/-1.42893` | 0.869693 | `-1->-1` | `2.06814/0/2.06814` | `3.47877/2.75751` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.873881/1.74217/0.753995/0.658902` | 0.584592 | `1->1` | `3.66239/10.493/14.1554` | `2.33837/18.8738` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.786705/1.66699/0.759043/0.597143` | 0.535627 | `1->1` | `2.94024/8.94143/11.8817` | `2.14251/15.8422` |
| `lower_edge_face` | 6 | `1-2` | 6 | -4 | -2 | `1.39221/0.371742/0.523551/0.728892` | `0.921307/1.28908/0.292002/0.269024` | -0.459868 | `1->1` | `-5.64675/-9.23908/-14.8858` | `1.83947/19.8478` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.53952/1.73247/-0.993684/-1.52979` | 0.381482 | `-1->-1` | `4.2699/0/4.2699` | `1.52593/5.6932` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.50261/1.53075/-0.864681/-1.29928` | 0.370253 | `-1->-1` | `3.24592/0/3.24592` | `1.48101/4.32789` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.85834 | `-1.85834/-1` | -3.01735 | `False` | `False` | `False` | `False` | `0.0484626/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.69267 | `-1.69267/-1` | -2.84792 | `False` | `False` | `False` | `False` | `0.0484626/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.31335 | `1.31334/1` | 2.63312 | `False` | `False` | `True` | `True` | `-12.6851/-1.61865` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.42253 | `2.42253/1` | 2.50805 | `False` | `False` | `False` | `False` | `-9.85779/0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.37039 | `2.37039/1` | 2.4879 | `False` | `False` | `False` | `False` | `-9.90305/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.37651 | `2.37651/1` | 2.48449 | `False` | `False` | `False` | `False` | `-9.89481/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.39053 | `2.39053/1` | 2.48446 | `False` | `False` | `False` | `False` | `-9.881/0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.9332 | `1.9332/1` | 2.22926 | `False` | `False` | `False` | `False` | `-0/-0.901913` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.03681 | `1.03681/1` | 2.1839 | `False` | `False` | `False` | `False` | `-11.8147/-1.61865` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 0.90904 | `0.908797/1` | 2.09029 | `False` | `False` | `True` | `True` | `-9.85097/-1.61865` |
| `upper_outer_face` | 10 | `7-8` | `-0.269081/-1` | 1.68033 | `1.68033/1` | 1.94941 | `False` | `False` | `False` | `False` | `-9.74541/0` |

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
| 7 | `1->0` | `-1->-1` | `True` | `False` | `False` |
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

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.402925 m3/s and balance delta is -3.2846 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is 0.123566 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
