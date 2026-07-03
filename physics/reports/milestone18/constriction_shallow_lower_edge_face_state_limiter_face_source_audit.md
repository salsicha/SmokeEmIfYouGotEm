# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_shallow_lower_edge_face_state_limiter/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_shallow_lower_edge_face_state_limiter/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.29451` m3/s
- Max abs flux/source balance delta: `5.53726` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `35`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `1.08268/1.30431/1.07922/1.16845` | -0.29451 | `1->1` | `-2.32599/-3.21127/-5.53726` | `1.17804/7.38302` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.339468/2.06218/0.793843/0.269484` | 0.207968 | `1->1` | `0.230423/0.166629/0.397053` | `0.831871/0.529403` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.345255/2.06218/0.698421/0.241133` | 0.166823 | `1->1` | `0.172886/0.121338/0.294224` | `0.667292/0.392298` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `0.99043/2.49659/0.698403/0.691719` | -0.132175 | `1->1` | `-0.883444/-1.41791/-2.30136` | `0.528702/3.06848` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.15981/2.35204/-1.26182/-1.46348` | -0.0952054 | `-1->-1` | `0.941804/0/0.941804` | `0.380822/1.25574` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `1.15659/1.78829/1.70166/1.96812` | -0.0775862 | `1->1` | `-0.622401/-0.812379/-1.43478` | `0.310345/1.91304` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.03155/0.990712/-1.39161/-1.43552` | -0.0671994 | `-1->-1` | `0.569879/0/0.569879` | `0.268798/0.759839` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.23917/1.73487/-1.65965/-2.05659` | -0.0489147 | `-1->-1` | `0.158018/0/0.158018` | `0.195659/0.210691` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.01824/2.537/-2.2136/-2.25398` | 0.0446391 | `-1->-1` | `-0.301859/0/-0.301859` | `0.178557/0.402479` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.05645/2.58415/-1.76699/-1.86674` | 0.0445331 | `-1->-1` | `-0.102716/0/-0.102716` | `0.178132/0.136954` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.12501/2.04343/-1.45218/-1.63372` | 0.0358146 | `-1->-1` | `-0.371775/0/-0.371775` | `0.143258/0.4957` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.1311/2.29728/-1.10314/-1.24776` | 0.0349641 | `-1->-1` | `0.127176/0/0.127176` | `0.139856/0.169567` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.58301 | `1.58301/1` | 3.199 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.31215 | `-1.31215/-1` | -2.47117 | `False` | `False` | `False` | `False` | `0.0403061/-0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.27753 | `1.27753/1` | 2.42462 | `False` | `False` | `False` | `False` | `-13.9792/-4.8311` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.03469 | `1.03466/1` | 2.35445 | `False` | `False` | `True` | `True` | `-13.1812/-3.93222` |
| `upper_edge_face` | 22 | `8-9` | `-0.717076/-1` | 1.58888 | `1.58888/1` | 2.30595 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.57043 | `-1.57043/-1` | -2.28314 | `False` | `False` | `False` | `False` | `1.02399/-0` |
| `upper_edge_face` | 20 | `8-9` | `-0.521241/-1` | 1.74084 | `1.74084/1` | 2.26209 | `False` | `False` | `False` | `False` | `-0/-2.75897` |
| `upper_edge_face` | 21 | `8-9` | `-0.57985/-1` | 1.64532 | `1.64532/1` | 2.22518 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.78891 | `1.78891/1` | 2.08496 | `False` | `False` | `False` | `False` | `-0/-0.904524` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -0.914069 | `-0.914069/-1` | -2.06932 | `False` | `False` | `False` | `False` | `1.0043/-0` |
| `lower_inner_source_face` | 8 | `3-4` | `0.0648287/1` | -2.00375 | `-2.00375/-1` | -2.06858 | `False` | `False` | `False` | `False` | `4.78238/-0` |
| `upper_edge_face` | 23 | `8-9` | `-0.895987/-1` | 1.10424 | `1.10424/1` | 2.00023 | `False` | `False` | `False` | `False` | `-0/-2.75906` |

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

- Start with `lower_edge_face` column 5 rows 1-2; reconstructed q delta is -0.29451 m3/s and balance delta is -5.53726 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 5 rows 1-2; post-source q delta is 0.978282 m3/s.
