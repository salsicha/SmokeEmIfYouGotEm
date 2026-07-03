# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_upper_interior_cross_stream_slowdown_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_upper_interior_cross_stream_slowdown_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.337763` m3/s
- Max abs flux/source balance delta: `9.58436` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `37`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.345255/2.06218/1.19353/0.412073` | 0.337763 | `1->1` | `0.496297/0.121338/0.617635` | `1.35105/0.823513` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.339468/2.06218/1.1475/0.389537` | 0.328021 | `1->1` | `0.463488/0.166629/0.630117` | `1.31208/0.840156` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `1.07584/1.30444/1.07894/1.16077` | -0.302188 | `1->1` | `-2.40698/-3.3454/-5.75238` | `1.20875/7.66984` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.0323/2.5244/1.53708/1.58673` | 0.26986 | `1->1` | `0.936273/0.415853/1.35213` | `1.07944/1.80284` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.01824/2.537/-2.34278/-2.38551` | -0.0868945 | `-1->-1` | `0.297458/0/0.297458` | `0.347578/0.39661` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `1.15659/1.78829/1.70166/1.96812` | -0.0775862 | `1->1` | `-0.622401/-0.812379/-1.43478` | `0.310345/1.91304` |
| `lower_edge_face` | 6 | `1-2` | 6 | -4 | -2 | `1.39221/0.371742/0.523551/0.728892` | `1.09034/0.566455/0.602431/0.656855` | -0.0720362 | `1->1` | `-3.66171/-5.92264/-9.58436` | `0.288145/12.7791` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.03155/0.990712/-1.39161/-1.43552` | -0.0671994 | `-1->-1` | `0.569879/0/0.569879` | `0.268798/0.759839` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.12501/2.01156/-1.42501/-1.60315` | 0.0663807 | `-1->-1` | `-0.45972/0/-0.45972` | `0.265523/0.612959` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.23917/1.73483/-1.65965/-2.05659` | -0.0489147 | `-1->-1` | `0.158018/0/0.158018` | `0.195659/0.210691` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `0.99043/2.63489/0.785217/0.777702` | -0.0461928 | `1->1` | `-0.755879/-1.41791/-2.17379` | `0.184771/2.89839` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.05645/2.58415/-1.76699/-1.86674` | 0.0445331 | `-1->-1` | `-0.102716/0/-0.102716` | `0.178132/0.136954` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.58301 | `1.58301/1` | 3.199 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.39307 | `-1.39307/-1` | -2.54832 | `False` | `False` | `False` | `False` | `0.0403061/-0` |
| `upper_edge_face` | 23 | `8-9` | `-0.895987/-1` | 1.65118 | `1.65118/1` | 2.54716 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.15199 | `1.15196/1` | 2.47174 | `False` | `False` | `True` | `True` | `-13.1812/-3.93222` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.31215 | `-1.31215/-1` | -2.47117 | `False` | `False` | `False` | `False` | `0.0403061/-0` |
| `upper_edge_face` | 20 | `8-9` | `-0.521241/-1` | 1.94684 | `1.94684/1` | 2.46808 | `False` | `False` | `False` | `False` | `-0/-2.75897` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.27754 | `1.27754/1` | 2.42463 | `False` | `False` | `False` | `False` | `-13.9792/-4.8311` |
| `upper_edge_face` | 22 | `8-9` | `-0.717076/-1` | 1.58888 | `1.58888/1` | 2.30595 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.57043 | `-1.57043/-1` | -2.28314 | `False` | `False` | `False` | `False` | `1.02399/-0` |
| `upper_edge_face` | 21 | `8-9` | `-0.57985/-1` | 1.67332 | `1.67332/1` | 2.25317 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93508 | `1.93508/1` | 2.23113 | `False` | `False` | `False` | `False` | `-0/-0.904524` |
| `lower_inner_source_face` | 8 | `3-4` | `0.0648287/1` | -2.16432 | `-2.16432/-1` | -2.22915 | `False` | `False` | `False` | `False` | `4.78238/-0` |

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

- Start with `lower_edge_face` column 8 rows 2-3; reconstructed q delta is 0.337763 m3/s and balance delta is 0.617635 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 8 rows 2-3; post-source q delta is 1.52027 m3/s.
