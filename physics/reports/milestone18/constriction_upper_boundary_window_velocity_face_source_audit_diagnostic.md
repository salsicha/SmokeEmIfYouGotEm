# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upper_boundary_window_velocity_retune/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upper_boundary_window_velocity_retune/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `1`
- X-momentum sign mismatch count: `1`
- Opposition mismatch count: `1`
- Max abs lateral volume-flux delta: `1.54926` m3/s
- Max abs flux/source balance delta: `14.1667` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `50`
- C++ internal face-state reconstruction applications: `20`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `lower_edge_face` | 7 | `2-3` | 7 | -3 | -2 | `1.13495/0.730822/0.309964/0.351794` | `1.03432/1.74695/0.0271959/0.0281292` | -0.323665 | `1->0` | `-1.17905/-1.97443/-3.15347` | `1.29466/4.20463` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.961547/1.56937/0.44275/0.425725` | -1.54926 | `1->1` | `-3.95822/-0.329459/-4.28768` | `6.19704/5.71691` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.974064/1.46196/0.783714/0.763388` | -1.28232 | `1->1` | `-5.28076/-4.39356/-9.67432` | `5.12929/12.8991` |
| `lower_edge_face` | 2 | `1-2` | 2 | -4 | -2 | `1.01111/2.71386/1.30241/1.31687` | `0.979907/1.61885/0.411987/0.403709` | -0.913164 | `1->1` | `-1.85348/-0.612154/-2.46564` | `3.65266/3.28752` |
| `lower_edge_face` | 5 | `1-2` | 5 | -4 | -2 | `1.24635/1.26151/1.17379/1.46296` | `0.967137/1.36684/0.633707/0.612882` | -0.850075 | `1->1` | `-4.36033/-5.47824/-9.83857` | `3.4003/13.1181` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.46305/1.51288/-0.791857/-1.15853` | 0.849141 | `-1->-1` | `0.629688/0/0.629688` | `3.39657/0.839584` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.50402/1.71552/-0.995998/-1.498` | 0.800615 | `-1->-1` | `2.21068/0/2.21068` | `3.20246/2.94757` |
| `lower_edge_face` | 8 | `2-3` | 8 | -3 | -2 | `0.33907/1.6661/0.219158/0.0743101` | `0.874023/1.74123/0.759462/0.663787` | 0.589477 | `1->1` | `3.67092/10.4958/14.1667` | `2.35791/18.8889` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.787248/1.66653/0.760713/0.59887` | 0.537354 | `1->1` | `2.94674/8.95208/11.8988` | `2.14941/15.8651` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.48046/1.57099/-0.800788/-1.18553` | 0.483996 | `-1->-1` | `2.74772/0/2.74772` | `1.93598/3.66363` |
| `lower_edge_face` | 4 | `1-2` | 4 | -4 | -2 | `1.15499/1.95534/0.20444/0.236126` | `0.968188/1.36543/0.726971/0.703845` | 0.467718 | `1->1` | `-1.48203/-3.66512/-5.14715` | `1.87087/6.86286` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.54404/1.77317/-1.03286/-1.59477` | 0.316508 | `-1->-1` | `4.46526/0/4.46526` | `1.26603/5.95368` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.94692 | `1.94692/1` | 3.56291 | `False` | `False` | `False` | `False` | `-0/-0.906282` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -1.86685 | `-1.86685/-1` | -3.02586 | `False` | `False` | `False` | `False` | `0.0498933/-0` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -1.70022 | `-1.70022/-1` | -2.85547 | `False` | `False` | `False` | `False` | `0.0498933/-0` |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 1.33079 | `1.33078/1` | 2.65056 | `False` | `False` | `True` | `True` | `-12.6413/-1.61865` |
| `upper_outer_face` | 20 | `9-10` | `-0.085522/-1` | 2.43397 | `2.43397/1` | 2.51949 | `False` | `False` | `False` | `False` | `-9.88831/0` |
| `upper_outer_face` | 23 | `9-10` | `-0.117512/-1` | 2.37762 | `2.37762/1` | 2.49514 | `False` | `False` | `False` | `False` | `-9.92324/0` |
| `upper_outer_face` | 21 | `9-10` | `-0.0939244/-1` | 2.39992 | `2.39992/1` | 2.49385 | `False` | `False` | `False` | `False` | `-9.90663/0` |
| `upper_outer_face` | 22 | `9-10` | `-0.107986/-1` | 2.38456 | `2.38456/1` | 2.49255 | `False` | `False` | `False` | `False` | `-9.91713/0` |
| `upper_edge_face` | 12 | `6-7` | `-0.296055/-1` | 1.93543 | `1.93543/1` | 2.23148 | `False` | `False` | `False` | `False` | `-0/-0.902623` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 1.04646 | `1.04646/1` | 2.19355 | `False` | `False` | `False` | `False` | `-11.8187/-1.61865` |
| `upper_outer_face` | 0 | `9-10` | `-1.1815/-1` | 0.882014 | `0.881773/1` | 2.06327 | `False` | `False` | `True` | `True` | `-9.83853/-1.61865` |
| `upper_outer_face` | 10 | `7-8` | `-0.269081/-1` | 1.68268 | `1.68268/1` | 1.95177 | `False` | `False` | `False` | `False` | `-9.75339/0` |

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

- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.323665 m3/s and balance delta is -3.15347 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is 0.196497 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
