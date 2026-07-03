# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **PASS**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_edge_source_balance_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_edge_source_balance_final_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.207968` m3/s
- Max abs flux/source balance delta: `0.742917` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `35`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.339468/2.06218/0.793843/0.269484` | 0.207968 | `1->1` | `0.230423/0.166629/0.397053` | `0.831871/0.529403` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.345255/2.06218/0.698421/0.241133` | 0.166823 | `1->1` | `0.172886/0.121338/0.294224` | `0.667292/0.392298` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `1.246/1.29853/1.0929/1.36175` | -0.101202 | `1->1` | `-0.233276/-0.0069592/-0.240235` | `0.40481/0.320313` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `1.06189/2.49659/0.698403/0.741629` | -0.0822662 | `1->1` | `-0.129206/-0.0158293/-0.145035` | `0.329065/0.19338` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.03155/0.990712/-1.39161/-1.43552` | -0.0671994 | `-1->-1` | `0.569879/0/0.569879` | `0.268798/0.759839` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.23917/1.73487/-1.65965/-2.05659` | -0.0489147 | `-1->-1` | `0.158018/0/0.158018` | `0.195659/0.210691` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.01824/2.537/-2.2136/-2.25398` | 0.0446391 | `-1->-1` | `-0.301859/0/-0.301859` | `0.178557/0.402479` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.05645/2.58415/-1.76699/-1.86674` | 0.0445331 | `-1->-1` | `-0.102716/0/-0.102716` | `0.178132/0.136954` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `1.87485/1.06705/-0.68993/-1.29352` | -0.0364774 | `-1->-1` | `0.446046/0/0.446046` | `0.14591/0.594728` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.12501/2.04343/-1.45218/-1.63372` | 0.0358146 | `-1->-1` | `-0.371775/0/-0.371775` | `0.143258/0.4957` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.1311/2.29728/-1.10314/-1.24776` | 0.0349641 | `-1->-1` | `0.127176/0/0.127176` | `0.139856/0.169567` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.98725/2.6703/1.3022/1.2856` | -0.0312745 | `1->1` | `-0.274842/-0.468075/-0.742917` | `0.125098/0.990556` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.58301 | `1.58301/1` | 3.199 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.19143 | `1.19141/1` | 2.51119 | `False` | `False` | `True` | `True` | `-13.8025/-3.93222` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.31215 | `-1.31215/-1` | -2.47117 | `False` | `False` | `False` | `False` | `0.0403061/-0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.27753 | `1.27753/1` | 2.42462 | `False` | `False` | `False` | `False` | `-13.9792/-4.8311` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.57043 | `-1.57043/-1` | -2.28314 | `False` | `False` | `False` | `False` | `1.02399/-0` |
| `upper_edge_face` | 20 | `8-9` | `-0.521241/-1` | 1.74084 | `1.74084/1` | 2.26209 | `False` | `False` | `False` | `False` | `-0/-2.75897` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.78891 | `1.78891/1` | 2.08496 | `False` | `False` | `False` | `False` | `-0/-0.904524` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -0.914069 | `-0.914069/-1` | -2.06932 | `False` | `False` | `False` | `False` | `1.0043/-0` |
| `lower_inner_source_face` | 8 | `3-4` | `0.0648287/1` | -2.00375 | `-2.00375/-1` | -2.06858 | `False` | `False` | `False` | `False` | `4.78238/-0` |
| `upper_edge_face` | 23 | `8-9` | `-0.895987/-1` | 1.10424 | `1.10424/1` | 2.00023 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 22 | `8-9` | `-0.717076/-1` | 1.26375 | `1.26375/1` | 1.98082 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.34072 | `-1.34072/-1` | -1.97296 | `False` | `False` | `False` | `False` | `2.79649/11.3066` |

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

## Next Levers

- Start with `lower_edge_face` column 9 rows 2-3; reconstructed q delta is 0.207968 m3/s and balance delta is 0.397053 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 9 rows 2-3; post-source q delta is 0.685184 m3/s.
