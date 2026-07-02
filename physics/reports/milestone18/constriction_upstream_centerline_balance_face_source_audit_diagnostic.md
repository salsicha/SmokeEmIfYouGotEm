# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_upstream_centerline_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_upstream_centerline_balance/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `1`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.60434` m3/s
- Max abs flux/source balance delta: `15.0906` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `53`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.01917/1.60916/-0.318343/-0.324446` | -0.676241 | `1->-1` | `-1.22909/-2.2716/-3.50069` | `2.70496/4.66758` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.926653/1.36761/0.399989/0.370651` | -1.60434 | `1->1` | `-4.32162/-1.01407/-5.3357` | `6.41734/7.11426` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.903382/1.24384/0.629192/0.568401` | -1.47731 | `1->1` | `-6.17231/-5.78033/-11.9526` | `5.90923/15.9369` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.919506/1.3257/0.297022/0.273114` | -1.18984 | `1->1` | `-5.10838/-6.41277/-11.5212` | `4.75937/15.3615` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.43303/1.45565/-0.857844/-1.22932` | 1.0693 | `-1->-1` | `0.750484/0/0.750484` | `4.27722/1.00065` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.36367/1.32766/-0.707452/-0.964734` | 1.04294 | `-1->-1` | `-0.983116/0/-0.983116` | `4.17175/1.31082` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.944546/1.43941/0.375562/0.354736` | -0.962137 | `1->1` | `-2.22037/-1.30593/-3.5263` | `3.84855/4.70173` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `1.72984/1.6713/-1.18348/-2.04724` | -0.7902 | `-1->-1` | `-0.587403/0/-0.587403` | `3.1608/0.783204` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.47149/1.53187/-0.889248/-1.30852` | 0.602755 | `-1->-1` | `2.90868/0/2.90868` | `2.41102/3.87823` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.849173/1.72623/0.731712/0.62135` | 0.54704 | `1->1` | `3.41141/10.0082/13.4196` | `2.18816/17.8928` |
| `lower_edge_face` | 6 | `1-2` | 6 | -4 | -2 | `1.39221/0.371742/0.523551/0.728892` | `0.915446/1.24676/0.213233/0.195203` | -0.533688 | `1->1` | `-5.73649/-9.35408/-15.0906` | `2.13475/20.1208` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.760876/1.66078/0.755477/0.574824` | 0.513308 | `1->1` | `2.72518/8.43467/11.1599` | `2.05323/14.8798` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.73199 | `-1.73199/-1` | -2.89101 | `False` | `False` | `False` | `False` | `0.0235947/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.57426 | `-1.57426/-1` | -2.72951 | `False` | `False` | `False` | `False` | `0.0235947/-0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.26618 | `2.26618/1` | 2.38369 | `False` | `False` | `False` | `False` | `-9.60991/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.26242 | `2.26242/1` | 2.3704 | `False` | `False` | `False` | `False` | `-9.57553/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.26034 | `2.26034/1` | 2.35427 | `False` | `False` | `False` | `False` | `-9.52058/0` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.26487 | `2.26487/1` | 2.3504 | `False` | `False` | `False` | `False` | `-9.42883/0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 0.995397 | `0.995384/1` | 2.31517 | `False` | `False` | `True` | `True` | `-12.3525/-1.61865` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.92174 | `1.92174/1` | 2.21779 | `False` | `False` | `False` | `False` | `-0/-0.898253` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 0.905023 | `0.905023/1` | 2.05212 | `False` | `False` | `False` | `False` | `-11.3139/-1.61865` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 0.794844 | `0.79462/1` | 1.97612 | `False` | `False` | `True` | `True` | `-9.1221/-1.61865` |
| `lower_edge_face` | 12 | `3-4` | `0.632247/1` | -1.30494 | `-1.30494/-1` | -1.93719 | `False` | `False` | `False` | `False` | `2.7771/11.2282` |

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

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.676241 m3/s and balance delta is -3.50069 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is -0.110518 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
