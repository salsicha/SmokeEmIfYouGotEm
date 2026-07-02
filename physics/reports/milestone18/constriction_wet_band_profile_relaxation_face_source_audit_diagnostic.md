# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_wet_band_profile_relaxation/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_wet_band_profile_relaxation/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `6`
- X-momentum sign mismatch count: `5`
- Opposition mismatch count: `6`
- Max abs lateral volume-flux delta: `2.00177` m3/s
- Max abs flux/source balance delta: `16.0182` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `54`
- C++ internal face-state reconstruction applications: `16`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.60898/1.70429/0.0383315/0.0616748` | 1.73121 | `-1->1` | `3.74831/0/3.74831` | `6.92482/4.99775` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.67643/1.94002/0.0359489/0.0602659` | 1.46761 | `-1->1` | `-4.08005/0/-4.08005` | `5.87045/5.44007` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.56007/1.76732/0.0511195/0.07975` | 1.44807 | `-1->1` | `5.29476/0/5.29476` | `5.79227/7.05968` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.59369/2.00897/0.00592063/0.00943565` | 1.29216 | `-1->0` | `4.93337/0/4.93337` | `5.16863/6.57783` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `1.81015/1.84391/-0.0064955/-0.0117578` | 1.24528 | `-1->0` | `-1.61576/0/-1.61576` | `4.98112/2.15434` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.55466/2.12801/-0.0312277/-0.0485485` | 1.18317 | `-1->-1` | `4.43419/0/4.43419` | `4.73266/5.91225` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.39076/2.05904/-0.213442/-0.296846` | 2.00177 | `-1->-1` | `-0.826241/0/-0.826241` | `8.0071/1.10165` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.768041/1.92332/0.272402/0.209216` | -1.83649 | `1->1` | `-7.58252/-8.43572/-16.0182` | `7.34597/21.3577` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.22319/1.96916/-0.186181/-0.227734` | 1.77994 | `-1->-1` | `-3.40583/0/-3.40583` | `7.11975/4.5411` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.85015/2.00889/0.235347/0.20008` | -1.77491 | `1->1` | `-5.08953/-2.51506/-7.60459` | `7.09962/10.1395` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.48939/2.15561/-0.23693/-0.352882` | 1.55839 | `-1->-1` | `2.08869/0/2.08869` | `6.23358/2.78491` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.52307/2.17449/-0.0986909/-0.150314` | 1.21796 | `-1->-1` | `3.89035/0/3.89035` | `4.87184/5.18714` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 2.48287 | `2.48286/1` | 3.80264 | `False` | `False` | `True` | `True` | `-13.2562/-1.61865` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 2.23752 | `2.23752/1` | 3.38461 | `False` | `False` | `False` | `False` | `-12.2897/-1.61865` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | -3.21412 | `-3.21412/-1` | -3.28843 | `False` | `False` | `False` | `False` | `0/12.1831` |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.82479 | `-1.82479/-1` | -2.98381 | `False` | `False` | `False` | `False` | `0.00837411/-0` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | -2.84538 | `-2.84538/-1` | -2.90689 | `False` | `False` | `False` | `False` | `0/11.2794` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 2.01478 | `2.01478/1` | 2.8525 | `False` | `False` | `False` | `False` | `-11.449/-1.61865` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.54656 | `-1.54656/-1` | -2.70181 | `False` | `False` | `False` | `False` | `0.00837411/-0` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 2.07239 | `2.07229/1` | 2.55672 | `False` | `False` | `True` | `True` | `-11.7076/-1.61865` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 1.98974 | `1.98957/1` | 2.42654 | `False` | `False` | `True` | `True` | `-11.5333/-1.61865` |
| `upper_outer_face` | 4 | `9-10` | `-0.491578/-1` | 1.85733 | `1.85708/1` | 2.34866 | `False` | `False` | `True` | `True` | `-11.1841/-1.61865` |
| `upper_outer_face` | 1 | `9-10` | `-0.956016/-1` | 1.37965 | `1.37936/1` | 2.33537 | `False` | `False` | `True` | `True` | `-9.91031/-1.61865` |

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
| 8 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |

## Blocked Reasons

- C++ reconstructed y-face volume flux signs do not match GeoClaw on one or more upstream edge faces.
- C++ reconstructed y-face x-momentum transport signs do not match GeoClaw.
- C++ reconstructed upstream lateral volume-flux deltas exceed the diagnostic threshold.
- C++ reconstructed normal momentum plus bed-source balance deltas exceed the diagnostic threshold.
- GeoClaw has opposite-signed lower/upper upstream edge fluxes that C++ still does not reproduce.
- C++ internal y-face Riemann/post-source flux signs still disagree with the GeoClaw final-frame edge flow.

## Next Levers

- Start with `upper_edge_face` column 6 rows 8-9; reconstructed q delta is 1.73121 m3/s and balance delta is 3.74831 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `upper_edge_face` column 6 rows 8-9; post-source q delta is 1.0241 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
