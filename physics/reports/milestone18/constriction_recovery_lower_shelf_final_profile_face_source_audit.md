# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_lower_shelf_final_profile/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_lower_shelf_final_profile/finite_volume_roe/scenario/constriction_seed_16`
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
- Max abs flux/source balance delta: `13.5606` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `42`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.974065/1.82047/0.777045/0.756892` | -0.706065 | `1->1` | `-4.09462/-5.34233/-9.43695` | `2.82426/12.5826` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.63997/1.31453/-1.18693/-1.94653` | -0.539187 | `-1->-1` | `-2.36493/0/-2.36493` | `2.15675/3.15324` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.0806/2.29211/1.53719/1.66108` | 0.344202 | `1->1` | `1.55121/1.36336/2.91458` | `1.37681/3.8861` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.978093/2.52888/0.588975/0.576072` | 0.339945 | `1->1` | `-1.55985/-3.47078/-5.03063` | `1.35978/6.70751` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.345255/2.06218/1.19353/0.412073` | 0.337763 | `1->1` | `0.496297/0.121338/0.617635` | `1.35105/0.823513` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.339468/2.06218/1.1475/0.389537` | 0.328021 | `1->1` | `0.463488/0.166629/0.630117` | `1.31208/0.840156` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.40762/1.09935/-1.18447/-1.66728` | -0.298964 | `-1->-1` | `5.04642/0/5.04642` | `1.19585/6.72856` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.23286/1.77273/-1.11999/-1.38079` | 0.288741 | `-1->-1` | `0.0495298/0/0.0495298` | `1.15497/0.0660397` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.17616/2.05184/-1.23929/-1.45761` | -0.225893 | `-1->-1` | `1.1692/0/1.1692` | `0.903571/1.55894` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.07378/2.26184/-1.98336/-2.12969` | 0.168932 | `-1->-1` | `-0.497447/0/-0.497447` | `0.675726/0.663263` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `1.05713/2.1297/1.72774/1.82644` | -0.148545 | `1->1` | `-0.0446944/1.54583/1.50114` | `0.594178/2.00151` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.18774/2.05121/-1.26992/-1.50833` | -0.140055 | `-1->-1` | `1.33216/0/1.33216` | `0.56022/1.77622` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.46906 | `1.46904/1` | 2.78882 | `False` | `False` | `True` | `True` | `-13.1807/-3.93222` |
| `upper_edge_face` | 23 | `8-9` | `-0.895987/-1` | 1.75907 | `1.75907/1` | 2.65506 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.39307 | `-1.39307/-1` | -2.54832 | `False` | `False` | `False` | `False` | `0.0403061/-0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.31215 | `-1.31215/-1` | -2.47117 | `False` | `False` | `False` | `False` | `0.0403061/-0` |
| `upper_edge_face` | 20 | `8-9` | `-0.521241/-1` | 1.94681 | `1.94681/1` | 2.46806 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 22 | `8-9` | `-0.717076/-1` | 1.67831 | `1.67831/1` | 2.39539 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.57043 | `-1.57043/-1` | -2.28314 | `False` | `False` | `False` | `False` | `1.02399/-0` |
| `upper_edge_face` | 21 | `8-9` | `-0.57985/-1` | 1.67337 | `1.67337/1` | 2.25322 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.9406 | `1.9406/1` | 2.23665 | `False` | `False` | `False` | `False` | `-0/-0.904524` |
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
