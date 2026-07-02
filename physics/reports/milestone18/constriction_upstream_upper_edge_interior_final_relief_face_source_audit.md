# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_upper_edge_interior_final_relief/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_upper_edge_interior_final_relief/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `0`
- X-momentum sign mismatch count: `0`
- Opposition mismatch count: `0`
- Max abs lateral volume-flux delta: `0.706075` m3/s
- Max abs flux/source balance delta: `12.8506` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `41`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.974057/1.82678/0.77704/0.756882` | -0.706075 | `1->1` | `-4.0947/-5.34248/-9.43719` | `2.8243/12.5829` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.827206/1.44208/0.77533/0.641358` | 0.567048 | `1->1` | `3.2734/9.57723/12.8506` | `2.26819/17.1342` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.65357/1.30119/-1.19257/-1.972` | -0.564649 | `-1->-1` | `-2.10394/0/-2.10394` | `2.2586/2.80525` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.671197/1.44208/0.729291/0.489498` | 0.427981 | `1->1` | `2.01796/6.67515/8.69312` | `1.71193/11.5908` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.07565/2.27795/-2.15269/-2.31554` | -0.404264 | `-1->-1` | `1.78418/0/1.78418` | `1.61706/2.37891` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.4666/1.09135/-1.19193/-1.74808` | -0.379765 | `-1->-1` | `5.98668/0/5.98668` | `1.51906/7.98225` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `1.09119/2.29466/1.52205/1.66085` | 0.343974 | `1->1` | `1.63857/1.5712/3.20978` | `1.37589/4.2797` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.978086/2.52887/0.58898/0.576073` | 0.339947 | `1->1` | `-1.55992/-3.47093/-5.03084` | `1.35979/6.70779` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.23174/1.77041/-1.12015/-1.37973` | 0.289802 | `-1->-1` | `0.0350239/0/0.0350239` | `1.15921/0.0466985` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.17619/1.76343/-1.23938/-1.45775` | -0.226037 | `-1->-1` | `1.16992/0/1.16992` | `0.904148/1.55989` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.18302/1.76282/-1.29669/-1.53401` | -0.165737 | `-1->-1` | `1.35096/0/1.35096` | `0.662947/1.80127` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `1.07143/2.13245/1.70618/1.82805` | -0.146936 | `1->1` | `0.0679823/1.82642/1.8944` | `0.587745/2.52587` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.88844 | `1.88844/1` | 3.50443 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.7254 | `1.72538/1` | 3.04516 | `False` | `False` | `True` | `True` | `-12.5033/-1.63696` |
| `upper_edge_face` | 23 | `8-9` | `-0.895987/-1` | 1.74528 | `1.74528/1` | 2.64127 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.39301 | `-1.39301/-1` | -2.54826 | `False` | `False` | `False` | `False` | `0.0407966/-0` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.3121 | `-1.3121/-1` | -2.47112 | `False` | `False` | `False` | `False` | `0.0407966/-0` |
| `upper_edge_face` | 20 | `8-9` | `-0.521241/-1` | 1.94922 | `1.94922/1` | 2.47046 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 22 | `8-9` | `-0.717076/-1` | 1.67936 | `1.67936/1` | 2.39644 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `lower_inner_source_face` | 16 | `3-4` | `0.712711/1` | -1.57032 | `-1.57032/-1` | -2.28303 | `False` | `False` | `False` | `False` | `1.02391/-0` |
| `upper_edge_face` | 21 | `8-9` | `-0.57985/-1` | 1.68197 | `1.68197/1` | 2.26182 | `False` | `False` | `False` | `False` | `-0/-2.75906` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.94063 | `1.94063/1` | 2.23669 | `False` | `False` | `False` | `False` | `-0/-0.904535` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.86537 | `0.86537/1` | 2.01246 | `False` | `False` | `False` | `False` | `-11.5435/-1.61865` |
| `lower_edge_face` | 10 | `3-4` | `0.126093/1` | -1.70297 | `-1.70297/-1` | -1.82906 | `False` | `False` | `False` | `False` | `4.59844/12.2421` |

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

- Start with `lower_edge_face` column 5 rows 1-2; reconstructed q delta is -0.706075 m3/s and balance delta is -9.43719 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 5 rows 1-2; post-source q delta is 0.211642 m3/s.
