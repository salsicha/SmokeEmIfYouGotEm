# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_recovery_centerline_depth_transfer/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_recovery_centerline_depth_transfer/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `1`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.84269` m3/s
- Max abs flux/source balance delta: `13.8828` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `52`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.03847/1.8763/-0.110853/-0.115117` | -0.466911 | `1->-1` | `-1.12484/-1.89297/-3.01781` | `1.86765/4.02374` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.881961/1.94284/0.149996/0.132291` | -1.84269 | `1->1` | `-4.84651/-1.89092/-6.73743` | `7.37078/8.98324` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.842021/1.68666/0.437558/0.368434` | -1.67728 | `1->1` | `-6.89405/-6.98424/-13.8783` | `6.7091/18.5044` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.3477/1.82944/-0.253443/-0.341566` | 1.66611 | `-1->-1` | `-1.79146/0/-1.79146` | `6.66442/2.38861` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.45234/2.0394/-0.449773/-0.653223` | 1.6454 | `-1->-1` | `0.263018/0/0.263018` | `6.58159/0.35069` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.923777/2.02516/0.0610734/0.0564182` | -1.26045 | `1->1` | `-2.54047/-1.71341/-4.25388` | `5.04182/5.67184` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.927642/1.53183/0.246299/0.228478` | -1.23448 | `1->1` | `-5.0595/-6.25314/-11.3126` | `4.93792/15.0835` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.53815/2.11328/-0.541137/-0.83235` | 1.07893 | `-1->-1` | `3.17953/0/3.17953` | `4.31571/4.23938` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.58565/1.77374/-0.460825/-0.730708` | 0.938822 | `-1->-1` | `3.71712/0/3.71712` | `3.75529/4.95616` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.57246/1.80068/-0.342977/-0.539319` | 0.829 | `-1->-1` | `5.66609/0/5.66609` | `3.316/7.55479` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.54696/2.13103/-0.452603/-0.70016` | 0.668114 | `-1->-1` | `4.55214/0/4.55214` | `2.67246/6.06952` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.58592/1.99368/-0.396198/-0.628339` | 0.654384 | `-1->-1` | `5.06105/0/5.06105` | `2.61754/6.74807` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.80875 | `1.80873/1` | 3.12851 | `False` | `False` | `True` | `True` | `-12.9294/-1.61865` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.77138 | `-1.77138/-1` | -2.9304 | `False` | `False` | `False` | `False` | `0.0320228/-0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.71613 | `1.71613/1` | 2.86322 | `False` | `False` | `False` | `False` | `-12.1773/-1.61865` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.60931 | `-1.60931/-1` | -2.76456 | `False` | `False` | `False` | `False` | `0.0320228/-0` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 1.65204 | `1.65204/1` | 2.48976 | `False` | `False` | `False` | `False` | `-11.4278/-1.61865` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 1.27607 | `1.2758/1` | 2.45729 | `False` | `False` | `True` | `True` | `-9.5462/-1.61865` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.30224 | `2.30224/1` | 2.41976 | `False` | `False` | `False` | `False` | `-9.71123/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.30036 | `2.30036/1` | 2.40834 | `False` | `False` | `False` | `False` | `-9.68216/0` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.31486 | `2.31486/1` | 2.40039 | `False` | `False` | `False` | `False` | `-9.56782/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.30211 | `2.30211/1` | 2.39603 | `False` | `False` | `False` | `False` | `-9.63769/0` |
| `upper_outer_face` | 1 | `9-10` | `-0.956016/-1` | 1.30087 | `1.30058/1` | 2.25659 | `False` | `False` | `True` | `True` | `-10.3439/-1.61865` |

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
| 7 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ reconstructed y-face volume flux signs do not match GeoClaw on one or more upstream edge faces.
- C++ reconstructed y-face x-momentum transport signs do not match GeoClaw.
- C++ reconstructed upstream lateral volume-flux deltas exceed the diagnostic threshold.
- C++ reconstructed normal momentum plus bed-source balance deltas exceed the diagnostic threshold.
- GeoClaw has opposite-signed lower/upper upstream edge fluxes that C++ still does not reproduce.
- C++ internal y-face Riemann/post-source flux signs still disagree with the GeoClaw final-frame edge flow.

## Next Levers

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.466911 m3/s and balance delta is -3.01781 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is 0.221954 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
