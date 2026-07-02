# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_lower_edge_flux_magnitude_firstwet/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_lower_edge_flux_magnitude_firstwet/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `1`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.4499` m3/s
- Max abs flux/source balance delta: `15.0996` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `52`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.01874/1.6094/-0.302488/-0.308157` | -0.659952 | `1->-1` | `-1.24345/-2.28003/-3.52348` | `2.63981/4.69797` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.927863/1.42921/0.565911/0.525087` | -1.4499 | `1->1` | `-4.16173/-0.990339/-5.15206` | `5.79959/6.86942` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.90211/1.31855/0.775013/0.699146` | -1.34656 | `1->1` | `-5.99936/-5.80531/-11.8047` | `5.38625/15.7396` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.43573/1.47315/-0.765124/-1.09851` | 1.20011 | `-1->-1` | `0.574393/0/0.574393` | `4.80044/0.765858` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.36124/1.35136/-0.633791/-0.862744` | 1.14493 | `-1->-1` | `-1.1513/0/-1.1513` | `4.57971/1.53507` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.91867/1.34084/0.3761/0.345512` | -1.11745 | `1->1` | `-5.06708/-6.42917/-11.4962` | `4.46978/15.3283` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.946641/1.48917/0.543627/0.51462` | -0.802253 | `1->1` | `-2.0544/-1.26483/-3.31923` | `3.20901/4.42564` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `1.72857/1.67035/-1.17108/-2.02429` | -0.767251 | `-1->-1` | `-0.661357/0/-0.661357` | `3.069/0.88181` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.47596/1.54191/-0.794293/-1.17235` | 0.738931 | `-1->-1` | `2.74087/0/2.74087` | `2.95573/3.65449` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.848767/1.726/0.733357/0.622449` | 0.548139 | `1->1` | `3.40986/10.0002/13.4101` | `2.19256/17.8801` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.760494/1.66067/0.756053/0.574973` | 0.513457 | `1->1` | `2.72277/8.42716/11.1499` | `2.05383/14.8666` |
| `lower_edge_face` | 6 | `1-2` | 6 | -4 | -2 | `1.39221/0.371742/0.523551/0.728892` | `0.914503/1.25865/0.255167/0.233351` | -0.495541 | `1->1` | `-5.72703/-9.37259/-15.0996` | `1.98216/20.1328` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.7355 | `-1.7355/-1` | -2.89452 | `False` | `False` | `False` | `False` | `0.0234706/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.58467 | `-1.58467/-1` | -2.73992 | `False` | `False` | `False` | `False` | `0.0234706/-0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.26577 | `2.26577/1` | 2.38328 | `False` | `False` | `False` | `False` | `-9.60869/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.26182 | `2.26182/1` | 2.36981 | `False` | `False` | `False` | `False` | `-9.57381/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.25943 | `2.25943/1` | 2.35335 | `False` | `False` | `False` | `False` | `-9.51803/0` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.26343 | `2.26343/1` | 2.34895 | `False` | `False` | `False` | `False` | `-9.42493/0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.00448 | `1.00447/1` | 2.32425 | `False` | `False` | `True` | `True` | `-12.3401/-1.61865` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.92176 | `1.92176/1` | 2.21782 | `False` | `False` | `False` | `False` | `-0/-0.89826` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.906524 | `0.906524/1` | 2.05362 | `False` | `False` | `False` | `False` | `-11.3084/-1.61865` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 0.842956 | `0.842728/1` | 2.02422 | `False` | `False` | `True` | `True` | `-9.10457/-1.61865` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.30496 | `-1.30496/-1` | -1.9372 | `False` | `False` | `False` | `False` | `2.77712/11.2283` |

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

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.659952 m3/s and balance delta is -3.52348 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is -0.0931519 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
