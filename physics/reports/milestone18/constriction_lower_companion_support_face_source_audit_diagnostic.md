# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_lower_companion_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_lower_companion_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `12`
- X-momentum sign mismatch count: `12`
- Opposition mismatch count: `8`
- Max abs lateral volume-flux delta: `4.54348` m3/s
- Max abs flux/source balance delta: `15.599` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `59`
- C++ internal face-state reconstruction applications: `16`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `1.03856/1.33329/-2.96617/-3.08053` | -4.54348 | `1->-1` | `5.09125/-4.07702/1.01423` | `18.1739/1.35231` |
| `lower_edge_face` | 6 | `1-2` | 6 | -4 | -2 | `1.39221/0.371742/0.523551/0.728892` | `1.0945/1.25473/-2.17693/-2.38264` | -3.11153 | `1->-1` | `1.17396/-5.84108/-4.66712` | `12.4461/6.22283` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `2.03006/1.60278/0.5378/1.09176` | 2.7613 | `-1->1` | `11.8491/0/11.8491` | `11.0452/15.7988` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `2.27078/1.88862/0.508064/1.1537` | 2.41074 | `-1->1` | `8.19067/0/8.19067` | `9.64296/10.9209` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.49687/2.07043/0.0447544/0.0669915` | 2.36561 | `-1->1` | `0.61637/0/0.61637` | `9.46245/0.821827` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `2.01172/1.87612/0.456189/0.917725` | 2.20045 | `-1->1` | `12.7446/0/12.7446` | `8.80179/16.9928` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `2.14288/2.11908/0.339704/0.727947` | 2.13529 | `-1->1` | `4.90341/0/4.90341` | `8.54117/6.53788` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.36526/1.75333/0.0160319/0.0218877` | 2.02956 | `-1->0` | `-1.64405/0/-1.64405` | `8.11824/2.19207` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.61403/2.26201/0.0675464/0.109022` | 2.0203 | `-1->1` | `3.90964/0/3.90964` | `8.08119/5.21285` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.88419/2.05965/0.333288/0.627976` | 1.85969 | `-1->1` | `10.2003/0/10.2003` | `7.43876/13.6004` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.97557/2.00569/0.218975/0.4326` | 1.80092 | `-1->1` | `12.5911/0/12.5911` | `7.20368/16.7881` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.73234/2.23919/0.213004/0.368995` | 1.73727 | `-1->1` | `7.29556/0/7.29556` | `6.94908/9.72742` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 4.21596 | `4.21594/1` | 5.53572 | `False` | `False` | `True` | `True` | `-16.7071/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 3.67402 | `3.67402/1` | 4.82111 | `False` | `False` | `False` | `False` | `-15.7663/-1.61865` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | -4.53191 | `-4.53191/-1` | -4.60622 | `False` | `False` | `False` | `False` | `0/15.7663` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | -4.11596 | `-4.11596/-1` | -4.17748 | `False` | `False` | `False` | `False` | `0/14.5352` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 3.60703 | `3.6069/1` | 4.09133 | `False` | `False` | `True` | `True` | `-14.9361/-1.61865` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 3.11949 | `3.11949/1` | 3.95722 | `False` | `False` | `False` | `False` | `-14.5352/-1.61865` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 3.46473 | `3.46449/1` | 3.90147 | `False` | `False` | `True` | `True` | `-14.8012/-1.61865` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -2.7187 | `-2.7187/-1` | -3.87772 | `False` | `False` | `False` | `False` | `0.00728823/-0` |
| `upper_outer_face` | 4 | `9-10` | `-0.491578/-1` | 3.01276 | `3.01244/1` | 3.50402 | `False` | `False` | `True` | `True` | `-13.8626/-1.61865` |
| `upper_outer_face` | 10 | `7-8` | `-0.269081/-1` | 3.08382 | `3.08382/1` | 3.3529 | `False` | `False` | `False` | `False` | `-13.9698/0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -2.15022 | `-2.15022/-1` | -3.30547 | `False` | `False` | `False` | `False` | `0.00728823/-0` |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->-1` | `-1->1` | `True` | `True` | `True` |
| 6 | `1->-1` | `-1->1` | `True` | `True` | `True` |
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

- Start with `lower_edge_face` column 5 rows 1-2; reconstructed q delta is -4.54348 m3/s and balance delta is 1.01423 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 5 rows 1-2; post-source q delta is -1.93347 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
