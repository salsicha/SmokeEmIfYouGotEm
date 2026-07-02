# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_transition_edge_face_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_transition_edge_face_balance/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `6`
- X-momentum sign mismatch count: `5`
- Opposition mismatch count: `6`
- Max abs lateral volume-flux delta: `2.00203` m3/s
- Max abs flux/source balance delta: `16.0255` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `52`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.60919/1.70343/0.0383548/0.0617202` | 1.73125 | `-1->1` | `3.75159/0/3.75159` | `6.925/5.00211` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.55907/1.75912/0.211466/0.32969` | 1.69801 | `-1->1` | `5.34509/0/5.34509` | `6.79204/7.12678` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.67781/1.92875/0.145554/0.244211` | 1.65156 | `-1->1` | `-4.02409/0/-4.02409` | `6.60623/5.36546` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.59371/2.00855/0.00594836/0.00947995` | 1.2922 | `-1->0` | `4.93365/0/4.93365` | `5.16881/6.57821` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `1.81114/1.8414/-0.00812977/-0.0147242` | 1.24231 | `-1->0` | `-1.59815/0/-1.59815` | `4.96926/2.13086` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.55455/2.12774/-0.0311795/-0.0484702` | 1.18324 | `-1->-1` | `4.43259/0/4.43259` | `4.73297/5.91012` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.39025/2.05911/-0.213333/-0.296586` | 2.00203 | `-1->-1` | `-0.833275/0/-0.833275` | `8.00814/1.11103` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.767775/1.92376/0.272533/0.209244` | -1.83647 | `1->1` | `-7.58449/-8.44096/-16.0255` | `7.34586/21.3673` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.22262/1.96963/-0.186088/-0.227514` | 1.78016 | `-1->-1` | `-3.41271/0/-3.41271` | `7.12063/4.55028` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.849901/2.00896/0.235487/0.200141` | -1.77484 | `1->1` | `-5.09156/-2.51994/-7.6115` | `7.09938/10.1487` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.48897/2.15548/-0.236828/-0.352631` | 1.55865 | `-1->-1` | `2.08241/0/2.08241` | `6.23458/2.77655` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.52287/2.17422/-0.0986038/-0.150161` | 1.21811 | `-1->-1` | `3.88733/0/3.88733` | `4.87245/5.18311` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 2.48332 | `2.48331/1` | 3.80309 | `False` | `False` | `True` | `True` | `-13.2635/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 2.34591 | `2.34591/1` | 3.49301 | `False` | `False` | `False` | `False` | `-12.2996/-1.61865` |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 2.1583 | `2.1583/1` | 2.99603 | `False` | `False` | `False` | `False` | `-11.4416/-1.61865` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.8249 | `-1.8249/-1` | -2.98392 | `False` | `False` | `False` | `False` | `0.00838416/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.54665 | `-1.54665/-1` | -2.7019 | `False` | `False` | `False` | `False` | `0.00838416/-0` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 2.07285 | `2.07275/1` | 2.55718 | `False` | `False` | `True` | `True` | `-11.7092/-1.61865` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 1.98981 | `1.98963/1` | 2.42661 | `False` | `False` | `True` | `True` | `-11.5334/-1.61865` |
| `upper_outer_face` | 4 | `9-10` | `-0.491578/-1` | 1.85718 | `1.85693/1` | 2.34851 | `False` | `False` | `True` | `True` | `-11.1833/-1.61865` |
| `upper_outer_face` | 1 | `9-10` | `-0.956016/-1` | 1.37886 | `1.37858/1` | 2.33459 | `False` | `False` | `True` | `True` | `-9.90665/-1.61865` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.19817 | `2.19817/1` | 2.31568 | `False` | `False` | `False` | `False` | `-9.4279/0` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 1.11838 | `1.11813/1` | 2.29962 | `False` | `False` | `True` | `True` | `-8.69815/-1.61865` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 6 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->0` | `True` | `False` | `False` |
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

- Start with `upper_edge_face` column 6 rows 8-9; reconstructed q delta is 1.73125 m3/s and balance delta is 3.75159 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `upper_edge_face` column 6 rows 8-9; post-source q delta is 1.02409 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
