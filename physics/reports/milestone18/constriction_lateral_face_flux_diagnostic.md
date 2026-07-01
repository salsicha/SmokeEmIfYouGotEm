# Milestone 18 Constriction Lateral Face Flux Diagnostic

Schema: `raftsim.milestone18.constriction_lateral_face_flux.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s

## Summary

- Sign mismatch count: `13`
- Opposition mismatch count: `10`
- Max abs lateral flux delta: `2.72825` m3/s

## Worst Lateral Faces

| Face | Column | Rows | x m | y-face m | GeoClaw h/v/flux | C++ h/v/flux | Delta | Threshold | Ratio | Signs |
| --- | ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | --- |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | `1.15452/-1.44608/-1.66953` | `1.87412/0.564913/1.05871` | 2.72825 | 0.25 | 10.913 | `-1->1` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | `1.85262/-0.678521/-1.25704` | `2.08708/0.516715/1.07843` | 2.33546 | 0.25 | 9.34186 | `-1->1` |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | `1.03834/-2.21375/-2.29862` | `1.50071/-0.0280077/-0.0420315` | 2.25659 | 0.25 | 9.02635 | `-1->0` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | `1.10988/-1.15573/-1.28272` | `1.87019/0.439837/0.822577` | 2.1053 | 0.25 | 8.4212 | `-1->1` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | `1.85053/-0.760508/-1.40735` | `1.97694/0.329997/0.652385` | 2.05973 | 0.25 | 8.23893 | `-1->1` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | `1.198/1.70761/2.04571` | `0.791031/-0.00162882/-0.00128845` | -2.047 | 0.25 | 8.18799 | `1->0` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | `0.978339/2.01871/1.97499` | `0.856632/-0.00736464/-0.00630879` | -1.98129 | 0.25 | 7.92518 | `1->0` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | `1.23942/-1.61985/-2.00767` | `1.37159/-0.0222167/-0.0304723` | 1.9772 | 0.25 | 7.9088 | `-1->0` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | `1.0484/-1.82303/-1.91128` | `1.60337/-0.0308035/-0.0493893` | 1.86189 | 0.25 | 7.44755 | `-1->0` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | `1.11127/-1.10838/-1.23171` | `1.77783/0.290841/0.517064` | 1.74878 | 0.25 | 6.99511 | `-1->1` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | `0.983374/-1.39145/-1.36832` | `1.81151/0.199424/0.361259` | 1.72958 | 0.25 | 6.91831 | `-1->1` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | `1.08534/-1.26068/-1.36827` | `1.67751/0.134209/0.225138` | 1.59341 | 0.25 | 6.37365 | `-1->1` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 6 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |

## Blocked Reasons

- C++ upstream lateral face velocity signs do not match GeoClaw on one or more edge faces.
- C++ upstream lateral face volume-flux proxy deltas exceed the diagnostic threshold.
- GeoClaw shows opposite-signed lower/upper upstream edge faces that C++ does not reproduce.

## Next Levers

- Start with `upper_edge_face` column 6 rows 8-9; the GeoClaw/C++ lateral flux proxy differs by 2.72825 m3/s.
- Instrument or reconstruct the actual finite-volume lateral face flux/source balance before adding another post-step velocity or depth transport.
- Preserve GeoClaw's opposite-signed lower/upper upstream edge behavior; a single-sign lateral transport will keep damaging Froude shape.
