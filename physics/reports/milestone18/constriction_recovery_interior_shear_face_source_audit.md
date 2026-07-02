# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_interior_shear/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_interior_shear/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.777682` m3/s
- Max abs flux/source balance delta: `14.1035` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `43`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.963108/1.38423/0.711525/0.685275` | -0.777682 | `1->1` | `-4.29927/-5.5573/-9.85657` | `3.11073/13.1421` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.964245/1.44476/0.909951/0.877416` | 0.641289 | `1->1` | `-1.23267/-3.74248/-4.97515` | `2.56516/6.63353` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.869434/1.73897/0.809849/0.70411` | 0.6298 | `1->1` | `3.69778/10.4057/14.1035` | `2.5192/18.8047` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.19673/2.40934/-1.41157/-1.68926` | 0.609362 | `-1->-1` | `-0.967656/0/-0.967656` | `2.43745/1.29021` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.47245/1.57802/-0.740111/-1.08978` | 0.579755 | `-1->-1` | `2.4889/0/2.4889` | `2.31902/3.31853` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.781699/1.66585/0.815393/0.637392` | 0.575876 | `1->1` | `2.96819/8.84321/11.8114` | `2.3035/15.7485` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.15828/2.23635/-1.2801/-1.48272` | 0.524955 | `-1->-1` | `-2.30836/0/-2.30836` | `2.09982/3.07781` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `1.06786/1.74341/1.39028/1.48462` | -0.490363 | `1->1` | `-1.0244/1.75642/0.732025` | `1.96145/0.976033` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `1.08125/1.6956/1.55819/1.6848` | -0.36091 | `1->1` | `-2.17318/-2.29049/-4.46368` | `1.44364/5.95157` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.48947/1.6704/-0.652816/-0.972352` | 0.310371 | `-1->-1` | `3.99201/0/3.99201` | `1.24148/5.32268` |
| `lower_edge_face` | 3 | `1-2` | 3 | -4 | -2 | `1.0627/2.45456/0.775286/0.823895` | `0.975704/1.54853/1.13117/1.10369` | 0.279794 | `1->1` | `-0.260096/-1.70684/-1.96693` | `1.11918/2.62258` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.50375/1.63383/-0.752429/-1.13146` | 0.236812 | `-1->-1` | `4.4399/0/4.4399` | `0.947248/5.91986` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.88327 | `-1.88327/-1` | -3.04228 | `False` | `False` | `False` | `False` | `0.0397685/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.818 | `-1.818/-1` | -2.97325 | `False` | `False` | `False` | `False` | `0.0397685/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.39728 | `1.39727/1` | 2.71705 | `False` | `False` | `True` | `True` | `-12.4567/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.10453 | `1.10453/1` | 2.25162 | `False` | `False` | `False` | `False` | `-11.7024/-1.61865` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93601 | `1.93601/1` | 2.23207 | `False` | `False` | `False` | `False` | `-0/-0.903063` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.37325 | `-1.37325/-1` | -2.08596 | `False` | `False` | `False` | `False` | `0.861669/-0` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 1.07075 | `1.07075/1` | 1.90847 | `False` | `False` | `False` | `False` | `-10.7524/-1.61865` |
| `lower_edge_face` | 19 | `1-2` | `0.255654/1` | -1.63744 | `-1.63744/-1` | -1.89309 | `False` | `False` | `False` | `False` | `1.66679/10.5055` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.17989 | `-1.17989/-1` | -1.81214 | `False` | `False` | `False` | `False` | `2.79197/11.2883` |
| `lower_edge_face` | 11 | `3-4` | `0.372864/1` | -1.2493 | `-1.2493/-1` | -1.62216 | `False` | `False` | `False` | `False` | `2.80192/11.3285` |
| `lower_edge_face` | 20 | `1-2` | `0.090122/1` | -1.48992 | `-1.48992/-1` | -1.58004 | `False` | `False` | `False` | `False` | `1.66679/9.91751` |

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

- Start with `lower_edge_face` column 5 rows 1-2; reconstructed q delta is -0.777682 m3/s and balance delta is -9.85657 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 5 rows 1-2; post-source q delta is 0.180913 m3/s.
