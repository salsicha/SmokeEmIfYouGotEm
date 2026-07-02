# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_throat_shelf_edge_final_relief_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_throat_shelf_edge_final_relief_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `7`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.706346` m3/s
- Max abs balance delta: `12.8095` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.756611/1` | -0.706346 | -9.44557 | `width=0, bank=0, face_h=-0.272577, column_h=-0.0921411` | `1.67499/1` | 0.212038 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.640231/1` | 0.565921 | 12.8095 | `width=0, bank=0, face_h=0.486683, column_h=-0.000890706` | `0.520985/1` | 0.446675 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.487517/1` | 0.426001 | 8.62056 | `width=0, bank=0, face_h=0.337507, column_h=0.228351` | `0.618562/1` | 0.557045 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.74207/-1` | -0.373748 | 5.90707 | `width=0, bank=0, face_h=0.478187, column_h=0.228351` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.63334/-1` | -0.350613 | 3.80503 | `width=0, bank=0, face_h=0.274674, column_h=-0.0921411` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.58673/-1` | 0.0828005 | 2.70978 | `width=1, bank=0, face_h=0.265365, column_h=-0.250556` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.683951/1` | -0.0449406 | 0 | `width=1, bank=0, face_h=-0.440126, column_h=-0.250556` | `1.30018/1` | 0.571293 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.97046/-1` | -0.563115 | -2.12671 | `width=0, bank=0, face_h=-0.198258, column_h=-0.000890706` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.85973/-1` | 0.438886 | -1.72262 | `width=0, bank=0, face_h=0.00499391, column_h=-0.0346386` | `-2.99856/-1` | -0.69994 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.64938/-1` | -0.417669 | 3.34811 | `width=0, bank=0, face_h=0.222951, column_h=-0.0645104` | `-3.98015/-1` | -2.74844 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.66002/1` | 0.343149 | 3.19299 | `width=0, bank=0, face_h=0.0795718, column_h=0.00716199` | `2.88449/1` | 1.56761 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `0.575939/1` | 0.339813 | -5.03856 | `width=0, bank=0, face_h=-0.177169, column_h=-0.0645104` | `2.00144/1` | 1.76531 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.706346 m3/s, balance delta is -9.44557 m3/s2, native post-source delta is 0.212038 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
