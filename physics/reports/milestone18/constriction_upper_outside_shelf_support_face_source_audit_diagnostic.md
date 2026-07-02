# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_upper_outside_shelf_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_upper_outside_shelf_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.99982` m3/s
- Max abs flux/source balance delta: `16.1413` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `54`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.54711/2.14082/-0.0382874/-0.059235` | 1.17248 | `-1->-1` | `4.32016/0/4.32016` | `4.68992/5.76022` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.38037/2.06723/-0.216462/-0.298798` | 1.99982 | `-1->-1` | `-0.966064/0/-0.966064` | `7.99929/1.28808` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.763615/1.93253/0.265964/0.203094` | -1.84262 | `1->1` | `-7.61875/-8.52257/-16.1413` | `7.37046/21.5218` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.845764/2.01427/0.234873/0.198647` | -1.77634 | `1->1` | `-5.12645/-2.60112/-7.72757` | `7.10535/10.3034` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.20852/1.97886/-0.194354/-0.23488` | 1.77279 | `-1->-1` | `-3.57754/0/-3.57754` | `7.09117/4.77005` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.48274/2.16388/-0.239732/-0.35546` | 1.55582 | `-1->-1` | `1.99324/0/1.99324` | `6.22327/2.65765` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.57942/1.77661/-0.123006/-0.194278` | 1.47525 | `-1->-1` | `3.30752/0/3.30752` | `5.90101/4.41003` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.51703/2.18284/-0.102542/-0.155559` | 1.21272 | `-1->-1` | `3.80133/0/3.80133` | `4.85086/5.06843` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.5742/2.04029/-0.0627457/-0.0987741` | 1.18395 | `-1->-1` | `4.63663/0/4.63663` | `4.73579/6.18217` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.55915/1.84876/-0.128156/-0.199814` | 1.1685 | `-1->-1` | `5.30216/0/5.30216` | `4.67402/7.06955` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.929683/1.56914/0.340968/0.316992` | -1.14596 | `1->1` | `-4.9891/-6.2131/-11.2022` | `4.58386/14.9363` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.896413/2.10571/0.2058/0.184481` | -1.13239 | `1->1` | `-2.75026/-2.2503/-5.00057` | `4.52957/6.66742` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 2.14571 | `2.1457/1` | 3.46548 | `False` | `False` | `True` | `True` | `-12.879/-1.61865` |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.9608 | `1.9608/1` | 3.10789 | `False` | `False` | `False` | `False` | `-12.0536/-1.61865` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.83468 | `-1.83468/-1` | -2.9937 | `False` | `False` | `False` | `False` | `0.00936451/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.55461 | `-1.55461/-1` | -2.70986 | `False` | `False` | `False` | `False` | `0.00936451/-0` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 1.81697 | `1.81697/1` | 2.65469 | `False` | `False` | `False` | `False` | `-11.3343/-1.61865` |
| `upper_outer_face` | 4 | `9-10` | `-0.491578/-1` | 1.83334 | `1.83309/1` | 2.32467 | `False` | `False` | `True` | `True` | `-11.1208/-1.61865` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.20623 | `2.20623/1` | 2.32375 | `False` | `False` | `False` | `False` | `-9.45123/0` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 1.82816 | `1.82807/1` | 2.31249 | `False` | `False` | `True` | `True` | `-11.3668/-1.61865` |
| `upper_outer_face` | 1 | `9-10` | `-0.956016/-1` | 1.35488 | `1.3546/1` | 2.31061 | `False` | `False` | `True` | `True` | `-9.81914/-1.61865` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 1.86815 | `1.86797/1` | 2.30495 | `False` | `False` | `True` | `True` | `-11.3239/-1.61865` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.17351 | `2.17351/1` | 2.28149 | `False` | `False` | `False` | `False` | `-9.35267/0` |

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

- Start with `upper_edge_face` column 4 rows 8-9; reconstructed q delta is 1.17248 m3/s and balance delta is 4.32016 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `upper_edge_face` column 4 rows 8-9; post-source q delta is -0.699634 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
