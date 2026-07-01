# Milestone 18 Constriction Face/Source Audit

Schema: `raftsim.milestone18.constriction_face_source_audit.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_y_face_state_reconstruction/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_y_face_state_reconstruction/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Finite-volume y-face flux/source reconstruction from exported final frames; this is not internal per-timestep Riemann telemetry.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Balance delta threshold: `0.75` m3/s2

## Summary

- Volume sign mismatch count: `14`
- X-momentum sign mismatch count: `13`
- Opposition mismatch count: `10`
- Max abs lateral volume-flux delta: `2.31188` m3/s
- Max abs flux/source balance delta: `15.4598` m3/s2
- C++ internal audit samples: `96`
- C++ internal post-source sign mismatches: `62`
- C++ internal face-state reconstruction applications: `16`
- C++ internal constriction source-split applications: `32`

## Worst Face/Source Samples

| Face | Column | Rows | x m | y-face m | bed step | GeoClaw h/u/v/q | C++ h/u/v/q | q delta | x-mom signs | normal/source/balance delta | Ratios |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| `upper_edge_face` | 1 | `8-9` | 1 | 3 | 0 | `1.03834/2.53794/-2.21375/-2.29862` | `1.50034/1.80448/0.00883931/0.013262` | 2.31188 | `-1->0` | `0.664542/0/0.664542` | `9.24753/0.886055` |
| `upper_edge_face` | 6 | `8-9` | 6 | 3 | 0 | `1.15452/2.04305/-1.44608/-1.66953` | `1.8741/1.48778/0.304821/0.571263` | 2.24079 | `-1->1` | `8.44944/0/8.44944` | `8.96318/11.2659` |
| `lower_edge_face` | 0 | `1-2` | 0 | -4 | -2 | `1.198/1.78633/1.70761/2.04571` | `0.790602/1.55918/0.0198245/0.0156733` | -2.03004 | `1->0` | `-7.46672/-7.99307/-15.4598` | `8.12015/20.6131` |
| `upper_edge_face` | 0 | `8-9` | 0 | 3 | 0 | `1.23942/1.73908/-1.61985/-2.00767` | `1.37074/1.58088/-0.000592241/-0.000811807` | 2.00686 | `-1->0` | `-1.57089/0/-1.57089` | `8.02744/2.09453` |
| `lower_edge_face` | 1 | `1-2` | 1 | -4 | -2 | `0.978339/2.7455/2.01871/1.97499` | `0.856405/1.78246/0.0291847/0.0249939` | -1.94999 | `1->0` | `-5.08354/-2.39234/-7.47588` | `7.79997/9.96783` |
| `upper_edge_face` | 2 | `8-9` | 2 | 3 | 0 | `1.0484/2.59117/-1.82303/-1.91128` | `1.60392/1.97379/0.0161096/0.0258384` | 1.93712 | `-1->1` | `3.74314/0/3.74314` | `7.74846/4.99086` |
| `upper_edge_face` | 7 | `7-8` | 7 | 2 | 0 | `1.85262/1.05684/-0.678521/-1.25704` | `2.08298/1.79957/0.281902/0.587196` | 1.84423 | `-1->1` | `3.7595/0/3.7595` | `7.37694/5.01267` |
| `upper_edge_face` | 8 | `7-8` | 8 | 2 | 0 | `1.85053/0.89686/-0.760508/-1.40735` | `1.97172/2.01726/0.150377/0.296502` | 1.70385 | `-1->1` | `1.24635/0/1.24635` | `6.81539/1.6618` |
| `upper_edge_face` | 5 | `8-9` | 5 | 3 | 0 | `1.10988/2.4002/-1.15573/-1.28272` | `1.87375/1.73012/0.193842/0.363212` | 1.64594 | `-1->1` | `9.76692/0/9.76692` | `6.58374/13.0226` |
| `upper_edge_face` | 9 | `7-8` | 9 | 2 | 0 | `0.983374/0.990442/-1.39145/-1.36832` | `1.80829/1.89688/0.0586189/0.106` | 1.47432 | `-1->1` | `9.39791/0/9.39791` | `5.89727/12.5306` |
| `upper_edge_face` | 3 | `8-9` | 3 | 3 | 0 | `1.08534/2.51154/-1.26068/-1.36827` | `1.68195/1.96768/0.0476209/0.080096` | 1.44837 | `-1->1` | `6.37694/0/6.37694` | `5.79348/8.50258` |
| `upper_edge_face` | 4 | `8-9` | 4 | 3 | 0 | `1.11127/2.46802/-1.10838/-1.23171` | `1.78383/1.84643/0.104997/0.187296` | 1.41901 | `-1->1` | `8.20501/0/8.20501` | `5.67604/10.94` |

## C++ Internal Y-Face Audit

| Face | Column | Rows | GeoClaw q/sign | C++ base q | C++ post-source q/sign | Delta | State Reconstructed | Source Applied | Split Applied | Hydro Face Source | Cell bed-source S/N |
| --- | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| `upper_outer_face` | 7 | `8-9` | `-1.31978/-1` | 3.45518 | `3.45516/1` | 4.77494 | `False` | `False` | `True` | `True` | `-15.3251/-1.61865` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | -4.17082 | `-4.17082/-1` | -4.24513 | `False` | `False` | `False` | `False` | `0/14.507` |
| `upper_outer_face` | 8 | `8-9` | `-1.14709/-1` | 3.03448 | `3.03448/1` | 4.18157 | `False` | `False` | `False` | `False` | `-14.507/-1.61865` |
| `lower_inner_source_face` | 15 | `3-4` | `1.15902/1` | -2.7148 | `-2.7148/-1` | -3.87382 | `False` | `False` | `False` | `False` | `0.00590985/-0` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | -3.7397 | `-3.7397/-1` | -3.80121 | `False` | `False` | `False` | `False` | `0/13.3045` |
| `upper_outer_face` | 6 | `9-10` | `-0.484427/-1` | 2.96971 | `2.96959/1` | 3.45402 | `False` | `False` | `True` | `True` | `-13.7884/-1.61865` |
| `upper_outer_face` | 9 | `8-9` | `-0.837723/-1` | 2.56239 | `2.56239/1` | 3.40012 | `False` | `False` | `False` | `False` | `-13.3045/-1.61865` |
| `lower_inner_source_face` | 14 | `3-4` | `1.15525/1` | -2.14644 | `-2.14644/-1` | -3.30169 | `False` | `False` | `False` | `False` | `0.00590985/-0` |
| `upper_outer_face` | 5 | `9-10` | `-0.436978/-1` | 2.85271 | `2.85249/1` | 3.28947 | `False` | `False` | `True` | `True` | `-13.7859/-1.61865` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | -2.54162 | `-1.65222/-1` | -3.11517 | `True` | `False` | `True` | `True` | `1.32435/13.9744` |
| `upper_edge_face` | 11 | `6-7` | `-1.61599/-1` | 1.49788 | `1.49788/1` | 3.11387 | `False` | `False` | `False` | `False` | `-0/0` |
| `upper_outer_face` | 4 | `9-10` | `-0.491578/-1` | 2.55644 | `2.55615/1` | 3.04772 | `False` | `False` | `True` | `True` | `-13.1241/-1.61865` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->0` | `True` | `False` | `False` |
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

- Start with `upper_edge_face` column 1 rows 8-9; reconstructed q delta is 2.31188 m3/s and balance delta is 0.664542 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `upper_edge_face` column 1 rows 8-9; post-source q delta is 0.536457 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
