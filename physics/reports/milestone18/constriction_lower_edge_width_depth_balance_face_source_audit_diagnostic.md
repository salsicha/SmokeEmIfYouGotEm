# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_lower_edge_width_depth_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_lower_edge_width_depth_balance/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `10`
- X-momentum sign mismatch count: `10`
- Opposition mismatch count: `10`
- Max abs lateral volume-flux delta: `2.97684` m3/s
- Max abs flux/source balance delta: `15.7838` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `58`
- C++ internal face-state reconstruction applications: `16`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `2.01026/1.57671/0.650319/1.30731` | 2.97684 | `-1->1` | `11.7197/0/11.7197` | `11.9073/15.6262` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `2.25091/1.86718/0.602099/1.35527` | 2.61231 | `-1->1` | `7.97982/0/7.97982` | `10.4492/10.6398` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.48246/2.08448/0.0444801/0.0659398` | 2.36456 | `-1->1` | `0.405672/0/0.405672` | `9.45824/0.540896` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.98861/1.84054/0.535998/1.06589` | 2.34861 | `-1->1` | `12.4438/0/12.4438` | `9.39446/16.5918` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `2.13075/2.09497/0.408218/0.869809` | 2.27716 | `-1->1` | `4.75684/0/4.75684` | `9.10862/6.34245` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.35128/1.77272/0.0158199/0.0213771` | 2.02905 | `-1->0` | `-1.83037/0/-1.83037` | `8.1162/2.44049` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.59752/2.28399/0.067072/0.107149` | 2.01843 | `-1->1` | `3.64949/0/3.64949` | `8.0737/4.86598` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.85813/2.01825/0.398085/0.739692` | 1.97141 | `-1->1` | `9.80709/0/9.80709` | `7.88562/13.0761` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.9602/1.99308/0.272113/0.533395` | 1.90171 | `-1->1` | `12.3448/0/12.3448` | `7.60685/16.4597` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.69379/2.24577/0.241342/0.408781` | 1.77705 | `-1->1` | `6.66777/0/6.66777` | `7.10822/8.89035` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.778616/1.75052/0.0693232/0.0539762` | -1.99173 | `1->1` | `-7.55554/-8.22824/-15.7838` | `7.96693/21.045` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.845313/2.06252/0.0977679/0.0826445` | -1.89234 | `1->1` | `-5.16877/-2.60996/-7.77873` | `7.56937/10.3716` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 4.27816 | `4.27814/1` | 5.59792 | `False` | `False` | `True` | `True` | `-16.5609/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 3.72392 | `3.72392/1` | 4.87101 | `False` | `False` | `False` | `False` | `-15.677/-1.61865` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | -4.42016 | `-4.42016/-1` | -4.49447 | `False` | `False` | `False` | `False` | `0/15.677` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 3.68406 | `3.68393/1` | 4.16835 | `False` | `False` | `True` | `True` | `-14.8006/-1.61865` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | -4.01546 | `-4.01546/-1` | -4.07697 | `False` | `False` | `False` | `False` | `0/14.4222` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 3.14098 | `3.14098/1` | 3.9787 | `False` | `False` | `False` | `False` | `-14.4222/-1.61865` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 3.49413 | `3.49389/1` | 3.93087 | `False` | `False` | `True` | `True` | `-14.6311/-1.61865` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -2.71798 | `-2.71798/-1` | -3.877 | `False` | `False` | `False` | `False` | `0.00699064/-0` |
| `upper_outer_face` | 4 | `9-10` | `-0.491578/-1` | 3.01753 | `3.01721/1` | 3.50879 | `False` | `False` | `True` | `True` | `-13.6709/-1.61865` |
| `upper_outer_face` | 10 | `7-8` | `-0.269081/-1` | 3.04023 | `3.04023/1` | 3.30931 | `False` | `False` | `False` | `False` | `-13.8508/0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -2.14954 | `-2.14954/-1` | -3.30479 | `False` | `False` | `False` | `False` | `0.00699064/-0` |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 6 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |

## Blocked Reasons

- C++ reconstructed y-face volume flux signs do not match GeoClaw on one or more upstream edge faces.
- C++ reconstructed y-face x-momentum transport signs do not match GeoClaw.
- C++ reconstructed upstream lateral volume-flux deltas exceed the diagnostic threshold.
- C++ reconstructed normal momentum plus bed-source balance deltas exceed the diagnostic threshold.
- GeoClaw has opposite-signed lower/upper upstream edge fluxes that C++ still does not reproduce.
- C++ internal y-face Riemann/post-source flux signs still disagree with the GeoClaw final-frame edge flow.

## Next Levers

- Start with `upper_edge_face` column 6 rows 8-9; reconstructed q delta is 2.97684 m3/s and balance delta is 11.7197 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `upper_edge_face` column 6 rows 8-9; post-source q delta is 2.05363 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
