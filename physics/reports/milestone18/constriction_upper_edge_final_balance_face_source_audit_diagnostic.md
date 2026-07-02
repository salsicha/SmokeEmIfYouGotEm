# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_upper_edge_final_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_upper_edge_final_balance/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.99953` m3/s
- Max abs flux/source balance delta: `15.9559` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `54`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.55275/2.13555/-0.0351535/-0.0545847` | 1.17713 | `-1->-1` | `4.40553/0/4.40553` | `4.70852/5.87404` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.3951/2.05858/-0.214384/-0.299087` | 1.99953 | `-1->-1` | `-0.766169/0/-0.766169` | `7.99813/1.02156` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.770347/1.91953/0.271282/0.208981` | -1.83673 | `1->1` | `-7.56542/-8.39049/-15.9559` | `7.34691/21.2745` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.22809/1.96517/-0.186999/-0.229651` | 1.77802 | `-1->-1` | `-3.34632/0/-3.34632` | `7.11208/4.46176` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.852268/2.00847/0.234145/0.199555` | -1.77543 | `1->1` | `-5.07221/-2.4735/-7.54571` | `7.10173/10.0609` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.4928/2.15715/-0.237792/-0.354976` | 1.5563 | `-1->-1` | `2.13928/0/2.13928` | `6.2252/2.85237` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.58266/1.77127/-0.120326/-0.190436` | 1.47909 | `-1->-1` | `3.3568/0/3.3568` | `5.91638/4.47573` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.52413/2.17822/-0.0994532/-0.151579` | 1.21669 | `-1->-1` | `3.90633/0/3.90633` | `4.86678/5.20844` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.57881/2.03421/-0.0595841/-0.0940721` | 1.18865 | `-1->-1` | `4.70741/0/4.70741` | `4.7546/6.27654` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.55669/1.84631/-0.126987/-0.19768` | 1.17064 | `-1->-1` | `5.26413/0/5.26413` | `4.68255/7.01884` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.931721/1.56716/0.341889/0.318545` | -1.14441 | `1->1` | `-4.96967/-6.17312/-11.1428` | `4.57765/14.8571` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.901263/2.1024/0.205128/0.184874` | -1.132 | `1->1` | `-2.70754/-2.15514/-4.86268` | `4.528/6.48358` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 2.14258 | `2.14256/1` | 3.46234 | `False` | `False` | `True` | `True` | `-12.8642/-1.61865` |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.95015 | `1.95015/1` | 3.09724 | `False` | `False` | `False` | `False` | `-12.0056/-1.61865` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.82456 | `-1.82456/-1` | -2.98357 | `False` | `False` | `False` | `False` | `0.00836057/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.54641 | `-1.54641/-1` | -2.70166 | `False` | `False` | `False` | `False` | `0.00836057/-0` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 1.81343 | `1.81343/1` | 2.65115 | `False` | `False` | `False` | `False` | `-11.3169/-1.61865` |
| `upper_outer_face` | 1 | `9-10` | `-0.956016/-1` | 1.38632 | `1.38603/1` | 2.34205 | `False` | `False` | `True` | `True` | `-9.94148/-1.61865` |
| `upper_outer_face` | 4 | `9-10` | `-0.491578/-1` | 1.84908 | `1.84883/1` | 2.34041 | `False` | `False` | `True` | `True` | `-11.1665/-1.61865` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 1.83904 | `1.83895/1` | 2.32338 | `False` | `False` | `True` | `True` | `-11.3961/-1.61865` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 1.88229 | `1.88212/1` | 2.3191 | `False` | `False` | `True` | `True` | `-11.363/-1.61865` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.19797 | `2.19797/1` | 2.31548 | `False` | `False` | `False` | `False` | `-9.42729/0` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 1.12627 | `1.12601/1` | 2.30751 | `False` | `False` | `True` | `True` | `-8.736/-1.61865` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ reconstructed y-face volume flux signs do not match GeoClaw on one or more upstream edge faces.
- C++ reconstructed upstream lateral volume-flux deltas exceed the diagnostic threshold.
- C++ reconstructed normal momentum plus bed-source balance deltas exceed the diagnostic threshold.
- GeoClaw has opposite-signed lower/upper upstream edge fluxes that C++ still does not reproduce.
- C++ internal y-face Riemann/post-source flux signs still disagree with the GeoClaw final-frame edge flow.

## Next Levers

- Start with `upper_edge_face` column 4 rows 8-9; reconstructed q delta is 1.17713 m3/s and balance delta is 4.40553 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `upper_edge_face` column 4 rows 8-9; post-source q delta is -0.699467 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
