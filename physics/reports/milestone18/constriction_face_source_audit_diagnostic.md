# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `13`
- X-momentum sign mismatch count: `11`
- Opposition mismatch count: `10`
- Max abs lateral volume-flux delta: `2.72633` m3/s
- Max abs flux/source balance delta: `15.4485` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `65`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.87408/1.48959/0.563905/1.0568` | 2.72633 | `-1->1` | `8.87096/0/8.87096` | `10.9053/11.8279` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `2.08705/1.79584/0.5158/1.0765` | 2.33354 | `-1->1` | `4.23255/0/4.23255` | `9.33415/5.6434` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.87032/1.73543/0.438622/0.820362` | 2.10309 | `-1->1` | `9.99331/0/9.99331` | `8.41234/13.3244` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.97687/2.01478/0.329316/0.651014` | 2.05836 | `-1->1` | `1.5158/0/1.5158` | `8.23344/2.02107` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.791026/1.55621/-0.00162915/-0.0012887` | -2.047 | `1->0` | `-7.46374/-7.98476/-15.4485` | `8.18799/20.598` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.856628/1.78001/-0.00737186/-0.00631494` | -1.9813 | `1->0` | `-5.08234/-2.38795/-7.47029` | `7.9252/9.96039` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.37158/1.57789/-0.022217/-0.0304725` | 1.9772 | `-1->0` | `-1.55884/0/-1.55884` | `7.9088/2.07846` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.77789/1.85435/0.289872/0.51536` | 1.74707 | `-1->1` | `8.23103/0/8.23103` | `6.98829/10.9747` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.8115/1.8984/0.198853/0.360223` | 1.72854 | `-1->1` | `9.52034/0/9.52034` | `6.91417/12.6938` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.67752/1.97161/0.133581/0.224084` | 1.59236 | `-1->1` | `6.33011/0/6.33011` | `6.36943/8.44015` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.90901/1.95068/-0.0101519/-0.00922819` | -1.3261 | `1->0` | `-2.67658/-2.00314/-4.67972` | `5.30441/6.23962` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.5007/1.80207/-0.028015/-0.0420422` | 2.25658 | `-1->-1` | `0.670909/0/0.670909` | `9.02631/0.894546` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 3.73518 | `3.73516/1` | 5.05494 | `False` | `True` | `True` | `-15.3551/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 3.24479 | `3.24479/1` | 4.39188 | `False` | `False` | `False` | `-14.5448/-1.61865` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | -4.01191 | `-4.01191/-1` | -4.08622 | `False` | `False` | `False` | `0/14.5448` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -2.71479 | `-2.71479/-1` | -3.8738 | `False` | `False` | `False` | `0.0059057/-0` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | -1.84967 | `-1.84934/-1` | -3.82432 | `False` | `True` | `True` | `1.61865/10.9866` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | -2.34688 | `-2.34668/-1` | -3.80963 | `False` | `True` | `True` | `1.32435/14.0343` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 3.24105 | `3.24092/1` | 3.72535 | `False` | `True` | `True` | `-13.7887/-1.61865` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | -3.62305 | `-3.62305/-1` | -3.68457 | `False` | `False` | `False` | `0/13.3281` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | -1.59003 | `-1.58973/-1` | -3.63544 | `False` | `True` | `True` | `1.61865/10.0213` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 2.71237 | `2.71237/1` | 3.55009 | `False` | `False` | `False` | `-13.3281/-1.61865` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 3.10053 | `3.10031/1` | 3.53729 | `False` | `True` | `True` | `-13.7606/-1.61865` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | -2.06442 | `-2.06406/-1` | -3.38094 | `False` | `True` | `True` | `1.61865/11.7574` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->0` | `-1->0` | `True` | `False` | `False` |
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

- Start with `upper_edge_face` column 6 rows 8-9; reconstructed q delta is 2.72633 m3/s and balance delta is 8.87096 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `upper_edge_face` column 6 rows 8-9; post-source q delta is 2.61144 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
