# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_y_face_opposition_flux/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_y_face_opposition_flux/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `12`
- X-momentum sign mismatch count: `12`
- Opposition mismatch count: `8`
- Max abs lateral volume-flux delta: `5.88954` m3/s
- Max abs flux/source balance delta: `15.7667` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `60`
- C++ internal face-state reconstruction applications: `16`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `1.01807/0.108287/-4.34803/-4.42658` | -5.88954 | `1->-1` | `14.9941/-4.47901/10.5151` | `23.5582/14.0201` |
| `lower_edge_face` | 6 | `1-2` | 6 | -4 | -2 | `1.39221/0.371742/0.523551/0.728892` | `1.0717/0.941333/-3.79291/-4.06486` | -4.79375 | `1->-1` | `11.1625/-6.28838/4.87417` | `19.175/6.4989` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `2.02797/1.60693/0.948262/1.92305` | 3.59258 | `-1->1` | `13.044/0/13.044` | `14.3703/17.392` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `2.26883/1.88875/0.881738/2.00052` | 3.25755 | `-1->1` | `9.32517/0/9.32517` | `13.0302/12.4336` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `2.14457/2.11525/0.649634/1.39318` | 2.80053 | `-1->1` | `5.59664/0/5.59664` | `11.2021/7.46218` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.99435/1.90491/0.730517/1.45691` | 2.73963 | `-1->1` | `13.049/0/13.049` | `10.9585/17.3986` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.48306/2.09094/0.0425796/0.0631482` | 2.36177 | `-1->1` | `0.414253/0/0.414253` | `9.44707/0.552337` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.97677/2.00341/0.480748/0.950329` | 2.31865 | `-1->1` | `12.9766/0/12.9766` | `9.27459/17.3021` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.35275/1.77478/0.0146988/0.0198839` | 2.02756 | `-1->0` | `-1.81086/0/-1.81086` | `8.11022/2.41448` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.59788/2.29111/0.0647862/0.10352` | 2.0148 | `-1->1` | `3.65452/0/3.65452` | `8.05919/4.8727` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.8573/2.09081/0.381612/0.70877` | 1.94048 | `-1->1` | `9.76811/0/9.76811` | `7.76194/13.0241` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.70442/2.28129/0.231395/0.394393` | 1.76267 | `-1->1` | `6.83756/0/6.83756` | `7.05067/9.11675` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 4.67563 | `4.6756/1` | 5.99539 | `False` | `False` | `True` | `True` | `-16.6928/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 4.04522 | `4.04522/1` | 5.19231 | `False` | `False` | `False` | `False` | `-15.7787/-1.61865` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 4.06408 | `4.06395/1` | 4.54838 | `False` | `False` | `True` | `True` | `-14.9263/-1.61865` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | -4.20993 | `-4.20993/-1` | -4.28424 | `False` | `False` | `False` | `False` | `0/15.7787` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 3.4114 | `3.4114/1` | 4.24912 | `False` | `False` | `False` | `False` | `-14.5441/-1.61865` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 3.72392 | `3.72368/1` | 4.16066 | `False` | `False` | `True` | `True` | `-14.6733/-1.61865` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | -3.86385 | `-3.86385/-1` | -3.92536 | `False` | `False` | `False` | `False` | `0/14.5441` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -2.71807 | `-2.71807/-1` | -3.87709 | `False` | `False` | `False` | `False` | `0.00707126/-0` |
| `upper_outer_face` | 4 | `9-10` | `-0.491578/-1` | 2.99847 | `2.99815/1` | 3.48972 | `False` | `False` | `True` | `True` | `-13.6648/-1.61865` |
| `upper_outer_face` | 10 | `7-8` | `-0.269081/-1` | 3.08679 | `3.08679/1` | 3.35588 | `False` | `False` | `False` | `False` | `-13.9779/0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -2.1496 | `-2.1496/-1` | -3.30485 | `False` | `False` | `False` | `False` | `0.00707126/-0` |
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

- Start with `lower_edge_face` column 5 rows 1-2; reconstructed q delta is -5.88954 m3/s and balance delta is 10.5151 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 5 rows 1-2; post-source q delta is -1.91458 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
