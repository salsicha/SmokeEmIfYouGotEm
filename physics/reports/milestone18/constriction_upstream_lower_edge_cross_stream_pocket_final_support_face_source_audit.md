# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_lower_edge_cross_stream_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_lower_edge_cross_stream_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.706065` m3/s
- Max abs flux/source balance delta: `9.43695` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `41`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.974065/1.45833/0.777045/0.756892` | -0.706065 | `1->1` | `-4.09462/-5.34233/-9.43695` | `2.82426/12.5826` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.978093/2.52878/0.588889/0.575988` | 0.339862 | `1->1` | `-1.55995/-3.47078/-5.03073` | `1.35945/6.70764` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.345255/2.06218/1.19353/0.412073` | 0.337763 | `1->1` | `0.496297/0.121338/0.617635` | `1.35105/0.823513` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.339468/2.06218/1.1475/0.389537` | 0.328021 | `1->1` | `0.463488/0.166629/0.630117` | `1.31208/0.840156` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `1.15659/1.95784/1.5076/1.74367` | -0.302035 | `1->1` | `-1.34271/-0.812379/-2.15509` | `1.20814/2.87346` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.40762/0.881935/-1.18425/-1.66698` | -0.298664 | `-1->-1` | `5.04571/0/5.04571` | `1.19465/6.72761` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.23286/1.77273/-1.11978/-1.38053` | 0.289004 | `-1->-1` | `0.0489413/0/0.0489413` | `1.15602/0.0652551` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.63997/1.09711/-1.02846/-1.68664` | -0.279296 | `-1->-1` | `-2.94069/0/-2.94069` | `1.11718/3.92092` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.0323/2.52431/1.53708/1.58673` | 0.26986 | `1->1` | `0.936273/0.415853/1.35213` | `1.07944/1.80284` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.988887/2.3619/1.72774/1.70854` | -0.266445 | `1->1` | `-0.93323/0.206966/-0.726264` | `1.06578/0.968352` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.17616/2.05184/-1.23929/-1.45761` | -0.225893 | `-1->-1` | `1.1692/0/1.1692` | `0.903571/1.55894` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.18363/1.60071/-1.53903/-1.82164` | 0.186034 | `-1->-1` | `-1.11165/0/-1.11165` | `0.744136/1.4822` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.33638 | `1.33635/1` | 2.65613 | `False` | `False` | `True` | `True` | `-13.1807/-3.93222` |
| `upper_edge_face` | 23 | `8-9` | `-0.895987/-1` | 1.75907 | `1.75907/1` | 2.65506 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.39307 | `-1.39307/-1` | -2.54832 | `False` | `False` | `False` | `False` | `0.0403061/-0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.31215 | `-1.31215/-1` | -2.47117 | `False` | `False` | `False` | `False` | `0.0403061/-0` |
| `upper_edge_face` | 20 | `8-9` | `-0.521241/-1` | 1.94681 | `1.94681/1` | 2.46806 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 22 | `8-9` | `-0.717076/-1` | 1.67831 | `1.67831/1` | 2.39539 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.57043 | `-1.57043/-1` | -2.28314 | `False` | `False` | `False` | `False` | `1.02399/-0` |
| `upper_edge_face` | 21 | `8-9` | `-0.57985/-1` | 1.67337 | `1.67337/1` | 2.25322 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.94414 | `1.94414/1` | 2.24019 | `False` | `False` | `False` | `False` | `-0/-0.904524` |
| `lower_inner_source_face` | 8 | `3-4` | `0.0648287/1` | -2.16433 | `-2.16433/-1` | -2.22915 | `False` | `False` | `False` | `False` | `4.78238/-0` |
| `lower_edge_face` | 10 | `3-4` | `0.126093/1` | -1.6951 | `-1.6951/-1` | -1.82119 | `False` | `False` | `False` | `False` | `4.59844/12.2148` |

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

- Start with `lower_edge_face` column 5 rows 1-2; reconstructed q delta is -0.706065 m3/s and balance delta is -9.43695 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 5 rows 1-2; post-source q delta is 0.211634 m3/s.
