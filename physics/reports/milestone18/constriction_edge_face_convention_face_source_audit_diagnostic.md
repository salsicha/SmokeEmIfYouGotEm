# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_edge_face_convention/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_edge_face_convention/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `13`
- X-momentum sign mismatch count: `12`
- Opposition mismatch count: `10`
- Max abs lateral volume-flux delta: `2.33225` m3/s
- Max abs flux/source balance delta: `15.4882` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `65`
- C++ internal face-state reconstruction applications: `16`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.49764/1.81346/0.0224578/0.0336336` | 2.33225 | `-1->1` | `0.625433/0/0.625433` | `9.32902/0.833911` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.88031/1.49141/0.34188/0.642842` | 2.31237 | `-1->1` | `8.60956/0/8.60956` | `9.24949/11.4794` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.789554/1.56563/0.0279757/0.0220884` | -2.02362 | `1->0` | `-7.47453/-8.01364/-15.4882` | `8.09448/20.6509` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.36869/1.58741/0.0076241/0.010435` | 2.01811 | `-1->0` | `-1.59833/0/-1.59833` | `8.07243/2.1311` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.60068/1.98536/0.0338765/0.0542254` | 1.9655 | `-1->1` | `3.69359/0/3.69359` | `7.86201/4.92479` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `2.09104/1.80156/0.317266/0.663418` | 1.92046 | `-1->1` | `3.96959/0/3.96959` | `7.68182/5.29279` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.97976/2.02035/0.177056/0.350528` | 1.75787 | `-1->1` | `1.41952/0/1.41952` | `7.0315/1.8927` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.87867/1.73579/0.233333/0.438356` | 1.72108 | `-1->1` | `9.88936/0/9.88936` | `6.88432/13.1858` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.81559/1.90313/0.079279/0.143938` | 1.51226 | `-1->1` | `9.53286/0/9.53286` | `6.04903/12.7105` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.67952/1.98597/0.079997/0.134357` | 1.50263 | `-1->1` | `6.34389/0/6.34389` | `6.01052/8.45852` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.78589/1.85754/0.14352/0.25631` | 1.48802 | `-1->1` | `8.2582/0/8.2582` | `5.9521/11.0109` |
| `lower_edge_face` | 9 | `2-3` | 9 | -3 | -2 | `0.330975/1.13986/0.185864/0.0615163` | `0.907794/0.951563/0.0481471/0.0437077` | -0.0178087 | `1->0` | `3.49552/11.3172/14.8127` | `0.0712346/19.7503` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 3.51624 | `3.51622/1` | 4.836 | `False` | `False` | `True` | `True` | `-15.3845/-1.61865` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | -4.17047 | `-4.17047/-1` | -4.24478 | `False` | `False` | `False` | `False` | `0/14.5661` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 3.0831 | `3.0831/1` | 4.23019 | `False` | `False` | `False` | `False` | `-14.5661/-1.61865` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -2.71488 | `-2.71488/-1` | -3.8739 | `False` | `False` | `False` | `False` | `0.00594331/-0` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | -3.74375 | `-3.74375/-1` | -3.80526 | `False` | `False` | `False` | `False` | `0/13.3582` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 3.02349 | `3.02337/1` | 3.5078 | `False` | `False` | `True` | `True` | `-13.8342/-1.61865` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 2.59966 | `2.59966/1` | 3.43739 | `False` | `False` | `False` | `False` | `-13.3582/-1.61865` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 2.90563 | `2.90541/1` | 3.34239 | `False` | `False` | `True` | `True` | `-13.8221/-1.61865` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -2.14651 | `-2.14651/-1` | -3.30176 | `False` | `False` | `False` | `False` | `0.00594331/-0` |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |
| `upper_outer_face` | 4 | `9-10` | `-0.491578/-1` | 2.59968 | `2.59938/1` | 3.09096 | `False` | `False` | `True` | `True` | `-13.1393/-1.61865` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | -2.75765 | `-2.65026/-1` | -3.00206 | `True` | `True` | `True` | `True` | `1.61865/15.3845` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 6 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 9 | `1->0` | `-1->1` | `True` | `False` | `False` |

## Blocked Reasons

- C++ reconstructed y-face volume flux signs do not match GeoClaw on one or more upstream edge faces.
- C++ reconstructed y-face x-momentum transport signs do not match GeoClaw.
- C++ reconstructed upstream lateral volume-flux deltas exceed the diagnostic threshold.
- C++ reconstructed normal momentum plus bed-source balance deltas exceed the diagnostic threshold.
- GeoClaw has opposite-signed lower/upper upstream edge fluxes that C++ still does not reproduce.
- C++ internal y-face Riemann/post-source flux signs still disagree with the GeoClaw final-frame edge flow.

## Next Levers

- Start with `upper_edge_face` column 1 rows 8-9; reconstructed q delta is 2.33225 m3/s and balance delta is 0.625433 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `upper_edge_face` column 1 rows 8-9; post-source q delta is 0.556185 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
