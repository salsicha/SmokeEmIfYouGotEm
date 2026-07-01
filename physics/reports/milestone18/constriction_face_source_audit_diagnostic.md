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
- Max abs lateral volume-flux delta: `2.72825` m3/s
- Max abs flux/source balance delta: `15.4484` m3/s2

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.87412/1.4894/0.564913/1.05871` | 2.72825 | `-1->1` | `8.87381/0/8.87381` | `10.913/11.8317` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `2.08708/1.7958/0.516715/1.07843` | 2.33546 | `-1->1` | `4.23522/0/4.23522` | `9.34186/5.64697` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.87019/1.73549/0.439837/0.822577` | 2.1053 | `-1->1` | `9.99285/0/9.99285` | `8.4212/13.3238` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.97694/2.01476/0.329997/0.652385` | 2.05973 | `-1->1` | `1.51818/0/1.51818` | `8.23893/2.02424` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.791031/1.5562/-0.00162882/-0.00128845` | -2.047 | `1->0` | `-7.4637/-7.98466/-15.4484` | `8.18799/20.5978` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.856632/1.78002/-0.00736464/-0.00630879` | -1.98129 | `1->0` | `-5.08231/-2.38789/-7.4702` | `7.92518/9.96026` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.37159/1.57788/-0.0222167/-0.0304723` | 1.9772 | `-1->0` | `-1.55871/0/-1.55871` | `7.9088/2.07827` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.77783/1.85451/0.290841/0.517064` | 1.74878 | `-1->1` | `8.23092/0/8.23092` | `6.99511/10.9746` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.81151/1.89836/0.199424/0.361259` | 1.72958 | `-1->1` | `9.52095/0/9.52095` | `6.91831/12.6946` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.67751/1.97168/0.134209/0.225138` | 1.59341 | `-1->1` | `6.33018/0/6.33018` | `6.37365/8.44023` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.90901/1.95071/-0.010121/-0.00920011` | -1.32607 | `1->0` | `-2.67658/-2.00314/-4.67971` | `5.30429/6.23962` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.50071/1.80208/-0.0280077/-0.0420315` | 2.25659 | `-1->-1` | `0.671012/0/0.671012` | `9.02635/0.894683` |

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

## Next Levers

- Start with `upper_edge_face` column 6 rows 8-9; reconstructed q delta is 2.72825 m3/s and balance delta is 8.87381 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
