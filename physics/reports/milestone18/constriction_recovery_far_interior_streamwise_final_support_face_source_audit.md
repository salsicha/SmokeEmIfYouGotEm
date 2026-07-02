# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_far_interior_streamwise_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_far_interior_streamwise_final_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.706071` m3/s
- Max abs flux/source balance delta: `13.5608` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `42`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.97406/1.82047/0.777042/0.756886` | -0.706071 | `1->1` | `-4.09467/-5.34242/-9.43708` | `2.82429/12.5828` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.64/1.31453/-1.18693/-1.94656` | -0.539217 | `-1->-1` | `-2.36444/0/-2.36444` | `2.15687/3.15259` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.09119/2.29466/1.52205/1.66085` | 0.34398 | `1->1` | `1.63861/1.57125/3.20987` | `1.37592/4.27982` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.978087/2.52887/0.588981/0.576075` | 0.339948 | `1->1` | `-1.5599/-3.47089/-5.03079` | `1.35979/6.70772` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.345255/2.06218/1.19353/0.412073` | 0.337763 | `1->1` | `0.496297/0.121338/0.617635` | `1.35105/0.823513` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.339468/2.06218/1.1475/0.389537` | 0.328021 | `1->1` | `0.463488/0.166629/0.630117` | `1.31208/0.840156` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.40777/1.09936/-1.18446/-1.66744` | -0.299126 | `-1->-1` | `5.04862/0/5.04862` | `1.1965/6.73149` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.23286/1.77274/-1.11999/-1.3808` | 0.288734 | `-1->-1` | `0.0496154/0/0.0496154` | `1.15493/0.0661538` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.17616/2.05185/-1.23929/-1.45761` | -0.225891 | `-1->-1` | `1.16919/0/1.16919` | `0.903566/1.55892` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `1.07143/2.13245/1.70618/1.82806` | -0.14693 | `1->1` | `0.0680245/1.82647/1.89449` | `0.587719/2.52599` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.20104/2.05561/-1.18424/-1.42232` | -0.139599 | `-1->-1` | `1.23515/0/1.23515` | `0.558396/1.64687` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.183/2.05123/-1.27461/-1.50787` | -0.139592 | `-1->-1` | `1.28355/0/1.28355` | `0.558367/1.71141` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.46901 | `1.46899/1` | 2.78877 | `False` | `False` | `True` | `True` | `-13.1806/-3.93235` |
| `upper_edge_face` | 23 | `8-9` | `-0.895987/-1` | 1.75879 | `1.75879/1` | 2.65477 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.39303 | `-1.39303/-1` | -2.54828 | `False` | `False` | `False` | `False` | `0.0406291/-0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.31212 | `-1.31212/-1` | -2.47114 | `False` | `False` | `False` | `False` | `0.0406291/-0` |
| `upper_edge_face` | 20 | `8-9` | `-0.521241/-1` | 1.94652 | `1.94652/1` | 2.46776 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 22 | `8-9` | `-0.717076/-1` | 1.678 | `1.678/1` | 2.39507 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.57036 | `-1.57036/-1` | -2.28307 | `False` | `False` | `False` | `False` | `1.02394/-0` |
| `upper_edge_face` | 21 | `8-9` | `-0.57985/-1` | 1.67305 | `1.67305/1` | 2.2529 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.94061 | `1.94061/1` | 2.23667 | `False` | `False` | `False` | `False` | `-0/-0.904528` |
| `lower_inner_source_face` | 8 | `3-4` | `0.0648287/1` | -2.16437 | `-2.16437/-1` | -2.2292 | `False` | `False` | `False` | `False` | `4.78238/-0` |
| `lower_edge_face` | 10 | `3-4` | `0.126093/1` | -1.69476 | `-1.69476/-1` | -1.82086 | `False` | `False` | `False` | `False` | `4.59844/12.2136` |

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

- Start with `lower_edge_face` column 5 rows 1-2; reconstructed q delta is -0.706071 m3/s and balance delta is -9.43708 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 5 rows 1-2; post-source q delta is 0.211638 m3/s.
