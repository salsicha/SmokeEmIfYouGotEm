# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_upstream_edge_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_upstream_edge_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `11`
- X-momentum sign mismatch count: `11`
- Opposition mismatch count: `10`
- Max abs lateral volume-flux delta: `2.33091` m3/s
- Max abs flux/source balance delta: `16.3406` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `65`
- C++ internal face-state reconstruction applications: `16`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.97907/1.5722/0.334186/0.661378` | 2.33091 | `-1->1` | `10.4804/0/10.4804` | `9.32363/13.9738` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.46368/2.08504/0.00196832/0.002881` | 2.3015 | `-1->0` | `0.131475/0/0.131475` | `9.206/0.175299` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.32521/1.80887/-0.0107054/-0.0141869` | 1.99348 | `-1->0` | `-2.1728/0/-2.1728` | `7.97394/2.89706` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `2.20959/1.8681/0.313957/0.693717` | 1.95075 | `-1->1` | `6.47764/0/6.47764` | `7.80302/8.63685` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.58856/2.25416/0.0118176/0.0187728` | 1.93005 | `-1->0` | `3.50238/0/3.50238` | `7.7202/4.66984` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `2.08944/2.08845/0.181607/0.379457` | 1.7868 | `-1->1` | `3.61562/0/3.61562` | `7.14721/4.82083` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.96535/1.83822/0.216355/0.425212` | 1.70793 | `-1->1` | `11.5134/0/11.5134` | `6.83174/15.3512` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.92171/1.97565/0.0874681/0.168088` | 1.53641 | `-1->1` | `11.4815/0/11.4815` | `6.14563/15.3087` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.69577/2.2061/0.0531998/0.0902148` | 1.45849 | `-1->1` | `6.60698/0/6.60698` | `5.83395/8.8093` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.84352/2.01024/0.119425/0.220163` | 1.45188 | `-1->1` | `9.27381/0/9.27381` | `5.80751/12.3651` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.765998/1.78688/0.0429952/0.0329342` | -2.01278 | `1->1` | `-7.65347/-8.47581/-16.1293` | `8.0511/21.5057` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.960855/0.987824/0.0522416/0.0501967` | -0.0113197 | `1->0` | `3.98238/12.3583/16.3406` | `0.0452786/21.7875` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 3.81473 | `3.81471/1` | 5.13449 | `False` | `False` | `True` | `True` | `-16.2568/-1.61865` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | -4.52263 | `-4.52263/-1` | -4.59694 | `False` | `False` | `False` | `False` | `0/15.3731` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 3.35378 | `3.35378/1` | 4.50087 | `False` | `False` | `False` | `False` | `-15.3731/-1.61865` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | -4.07153 | `-4.07153/-1` | -4.13305 | `False` | `False` | `False` | `False` | `0/14.139` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -2.71667 | `-2.71667/-1` | -3.87569 | `False` | `False` | `False` | `False` | `0.00663975/-0` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 3.25175 | `3.25163/1` | 3.73605 | `False` | `False` | `True` | `True` | `-14.5609/-1.61865` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 2.8494 | `2.8494/1` | 3.68712 | `False` | `False` | `False` | `False` | `-14.139/-1.61865` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 3.08581 | `3.08559/1` | 3.52257 | `False` | `False` | `True` | `True` | `-14.4599/-1.61865` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -2.14823 | `-2.14823/-1` | -3.30348 | `False` | `False` | `False` | `False` | `0.00663975/-0` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | -3.02354 | `-2.90848/-1` | -3.26028 | `True` | `True` | `True` | `True` | `1.61865/16.2568` |
| `upper_outer_face` | 10 | `7-8` | `-0.269081/-1` | 2.92681 | `2.92681/1` | 3.19589 | `False` | `False` | `False` | `False` | `-13.5384/0` |
| `upper_outer_face` | 4 | `9-10` | `-0.491578/-1` | 2.69104 | `2.69073/1` | 3.18231 | `False` | `False` | `True` | `True` | `-13.549/-1.61865` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 6 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
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

- Start with `upper_edge_face` column 6 rows 8-9; reconstructed q delta is 2.33091 m3/s and balance delta is 10.4804 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `upper_edge_face` column 6 rows 8-9; post-source q delta is 1.66984 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
