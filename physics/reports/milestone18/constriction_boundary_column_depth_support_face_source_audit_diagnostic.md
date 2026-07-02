# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_boundary_column_depth_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_boundary_column_depth_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `1`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.42857` m3/s
- Max abs flux/source balance delta: `14.9694` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `50`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.027/1.75729/-0.0465229/-0.0477789` | -0.399573 | `1->-1` | `-1.25159/-2.11803/-3.36962` | `1.59829/4.49283` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.962211/1.45649/0.567874/0.546414` | -1.42857 | `1->1` | `-3.83015/-0.316429/-4.14658` | `5.71429/5.52877` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.979056/1.38455/0.870919/0.852678` | -1.19303 | `1->1` | `-5.0886/-4.29561/-9.38422` | `4.77212/12.5123` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.50525/1.50337/-0.771312/-1.16102` | 1.1376 | `-1->-1` | `1.63225/0/1.63225` | `4.55042/2.17633` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.47352/1.33337/-0.601693/-0.886605` | 1.12107 | `-1->-1` | `0.396467/0/0.396467` | `4.48427/0.528623` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.927012/1.34775/0.376616/0.349127` | -1.11383 | `1->1` | `-4.99003/-6.26551/-11.2555` | `4.45532/15.0074` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.971364/1.5122/0.54112/0.525624` | -0.791249 | `1->1` | `-1.81714/-0.77975/-2.59689` | `3.165/3.46252` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.52683/1.56741/-0.803818/-1.22729` | 0.683985 | `-1->-1` | `3.54541/0/3.54541` | `2.73594/4.72722` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.871453/1.74095/0.755675/0.658536` | 0.584226 | `1->1` | `3.64244/10.4454/14.0878` | `2.3369/18.7837` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.783655/1.66658/0.75946/0.595155` | 0.533638 | `1->1` | `2.91548/8.88159/11.7971` | `2.13455/15.7294` |
| `lower_edge_face` | 6 | `1-2` | 6 | -4 | -2 | `1.39221/0.371742/0.523551/0.728892` | `0.918391/1.28787/0.292335/0.268478` | -0.460414 | `1->1` | `-5.67314/-9.29631/-14.9694` | `1.84165/19.9593` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.49684/1.52836/-0.86365/-1.29274` | 0.376787 | `-1->-1` | `3.154/0/3.154` | `1.50715/4.20533` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.83817 | `-1.83817/-1` | -2.99719 | `False` | `False` | `False` | `False` | `0.0446235/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.67451 | `-1.67451/-1` | -2.82976 | `False` | `False` | `False` | `False` | `0.0446235/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.29795 | `1.29794/1` | 2.61772 | `False` | `False` | `True` | `True` | `-12.5988/-1.61865` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.39447 | `2.39447/1` | 2.47999 | `False` | `False` | `False` | `False` | `-9.78242/0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.35242 | `2.35242/1` | 2.46993 | `False` | `False` | `False` | `False` | `-9.85286/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.35696 | `2.35696/1` | 2.46494 | `False` | `False` | `False` | `False` | `-9.84057/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.36813 | `2.36813/1` | 2.46205 | `False` | `False` | `False` | `False` | `-9.81963/0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.92932 | `1.92932/1` | 2.22537 | `False` | `False` | `False` | `False` | `-0/-0.900673` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 1.02248 | `1.02223/1` | 2.20372 | `False` | `False` | `True` | `True` | `-9.91797/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.02739 | `1.02739/1` | 2.17448 | `False` | `False` | `False` | `False` | `-11.753/-1.61865` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.31091 | `-1.31091/-1` | -1.94316 | `False` | `False` | `False` | `False` | `2.78458/11.2584` |

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
| 7 | `1->0` | `-1->-1` | `True` | `False` | `False` |
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

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.399573 m3/s and balance delta is -3.36962 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is 0.1359 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
