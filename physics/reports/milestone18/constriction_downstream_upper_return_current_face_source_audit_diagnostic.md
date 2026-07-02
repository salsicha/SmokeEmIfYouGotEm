# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_downstream_upper_return_final/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_downstream_upper_return_final/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `1`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.60433` m3/s
- Max abs flux/source balance delta: `15.0904` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `53`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.01918/1.60916/-0.318349/-0.324455` | -0.676249 | `1->-1` | `-1.229/-2.27144/-3.50043` | `2.705/4.66724` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.926667/1.36761/0.39999/0.370658` | -1.60433 | `1->1` | `-4.32149/-1.0138/-5.33529` | `6.41731/7.11372` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.903395/1.24383/0.62919/0.568408` | -1.4773 | `1->1` | `-6.17219/-5.78008/-11.9523` | `5.90921/15.9364` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.919513/1.3257/0.297024/0.273117` | -1.18984 | `1->1` | `-5.10831/-6.41263/-11.5209` | `4.75936/15.3612` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.43306/1.45566/-0.857846/-1.22934` | 1.06928 | `-1->-1` | `0.750931/0/0.750931` | `4.2771/1.00124` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.3637/1.32766/-0.707456/-0.96476` | 1.04291 | `-1->-1` | `-0.982721/0/-0.982721` | `4.17165/1.3103` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.944558/1.43942/0.375565/0.354743` | -0.96213 | `1->1` | `-2.22025/-1.30569/-3.52594` | `3.84852/4.70125` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `1.72987/1.6713/-1.18349/-2.04728` | -0.790243 | `-1->-1` | `-0.586865/0/-0.586865` | `3.16097/0.782486` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.47152/1.53188/-0.88925/-1.30855` | 0.60273 | `-1->-1` | `2.90907/0/2.90907` | `2.41092/3.87877` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.849181/1.72623/0.731712/0.621356` | 0.547046 | `1->1` | `3.41148/10.0084/13.4199` | `2.18818/17.8931` |
| `lower_edge_face` | 6 | `1-2` | 6 | -4 | -2 | `1.39221/0.371742/0.523551/0.728892` | `0.915453/1.24676/0.213234/0.195206` | -0.533686 | `1->1` | `-5.73642/-9.35394/-15.0904` | `2.13474/20.1205` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.760887/1.66078/0.755478/0.574834` | 0.513317 | `1->1` | `2.72527/8.43488/11.1602` | `2.05327/14.8802` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.73664 | `-1.73664/-1` | -2.89566 | `False` | `False` | `False` | `False` | `0.023606/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.58559 | `-1.58559/-1` | -2.74085 | `False` | `False` | `False` | `False` | `0.023606/-0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.26623 | `2.26623/1` | 2.38374 | `False` | `False` | `False` | `False` | `-9.61006/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.26245 | `2.26245/1` | 2.37044 | `False` | `False` | `False` | `False` | `-9.57564/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.26033 | `2.26033/1` | 2.35426 | `False` | `False` | `False` | `False` | `-9.52056/0` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.26472 | `2.26472/1` | 2.35025 | `False` | `False` | `False` | `False` | `-9.42844/0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 0.995444 | `0.995431/1` | 2.31521 | `False` | `False` | `True` | `True` | `-12.3528/-1.61865` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.92185 | `1.92185/1` | 2.2179 | `False` | `False` | `False` | `False` | `-0/-0.898287` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.905043 | `0.905043/1` | 2.05213 | `False` | `False` | `False` | `False` | `-11.3141/-1.61865` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 0.794877 | `0.794653/1` | 1.97615 | `False` | `False` | `True` | `True` | `-9.12229/-1.61865` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.30502 | `-1.30502/-1` | -1.93727 | `False` | `False` | `False` | `False` | `2.7772/11.2286` |

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

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.676249 m3/s and balance delta is -3.50043 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is -0.110554 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
