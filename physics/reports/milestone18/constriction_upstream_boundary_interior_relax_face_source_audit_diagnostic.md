# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_upstream_boundary_interior_relax_3p0/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_upstream_boundary_interior_relax_3p0/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `1`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.83996` m3/s
- Max abs flux/source balance delta: `14.0552` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `52`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.03422/1.87684/-0.10979/-0.113547` | -0.465342 | `1->-1` | `-1.16833/-1.97634/-3.14467` | `1.86137/4.1929` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.873968/1.94628/0.154494/0.135023` | -1.83996 | `1->1` | `-4.91434/-2.04776/-6.9621` | `7.35985/9.2828` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.835628/1.69402/0.440827/0.368368` | -1.67734 | `1->1` | `-6.94548/-7.10967/-14.0552` | `6.70937/18.7402` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.33412/1.83774/-0.249965/-0.333483` | 1.67419 | `-1->-1` | `-1.97333/0/-1.97333` | `6.69675/2.6311` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.4361/2.04253/-0.445901/-0.640357` | 1.65826 | `-1->-1` | `0.0246303/0/0.0246303` | `6.63305/0.0328403` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.917286/2.02337/0.064392/0.0590659` | -1.25781 | `1->1` | `-2.59873/-1.84077/-4.4395` | `5.03123/5.91933` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.924103/1.53117/0.247/0.228253` | -1.2347 | `1->1` | `-5.09154/-6.32257/-11.4141` | `4.93882/15.2188` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.52471/2.11173/-0.537667/-0.819787` | 1.09149 | `-1->-1` | `2.968/0/2.968` | `4.36596/3.95733` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.57894/1.77328/-0.459963/-0.726253` | 0.943277 | `-1->-1` | `3.61019/0/3.61019` | `3.77311/4.81359` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.56069/1.8067/-0.343155/-0.535559` | 0.83276 | `-1->-1` | `5.48395/0/5.48395` | `3.33104/7.31193` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.5373/2.1282/-0.449692/-0.691311` | 0.676962 | `-1->-1` | `4.39992/0/4.39992` | `2.70785/5.86656` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.57885/1.99253/-0.394848/-0.623406` | 0.659317 | `-1->-1` | `4.94852/0/4.94852` | `2.63727/6.59803` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.79412 | `1.7941/1` | 3.11389 | `False` | `False` | `True` | `True` | `-12.8669/-1.61865` |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.88161 | `-1.88161/-1` | -3.04062 | `False` | `False` | `False` | `False` | `0.0153381/-0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.69997 | `1.69997/1` | 2.84706 | `False` | `False` | `False` | `False` | `-12.1095/-1.61865` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.58858 | `-1.58858/-1` | -2.74383 | `False` | `False` | `False` | `False` | `0.0153381/-0` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 1.63095 | `1.63095/1` | 2.46867 | `False` | `False` | `False` | `False` | `-11.3441/-1.61865` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 1.25612 | `1.25585/1` | 2.43734 | `False` | `False` | `True` | `True` | `-9.4497/-1.61865` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.2428 | `2.2428/1` | 2.36032 | `False` | `False` | `False` | `False` | `-9.55654/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.21633 | `2.21633/1` | 2.32432 | `False` | `False` | `False` | `False` | `-9.47673/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.17349 | `2.17349/1` | 2.26742 | `False` | `False` | `False` | `False` | `-9.34739/0` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.52435 | `-1.52435/-1` | -2.23706 | `False` | `False` | `False` | `False` | `1.09648/-0` |
| `upper_outer_face` | 1 | `9-10` | `-0.956016/-1` | 1.27726 | `1.27698/1` | 2.23299 | `False` | `False` | `True` | `True` | `-10.2263/-1.61865` |

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

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.465342 m3/s and balance delta is -3.14467 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is 0.23619 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
