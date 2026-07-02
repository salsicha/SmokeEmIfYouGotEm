# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_downstream_throat_interior_final_support_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_downstream_throat_interior_final_support_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `4`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.706065` m3/s
- Max abs balance delta: `13.5606` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.756892/1` | -0.706065 | -9.43695 | `width=0, bank=0, face_h=-0.27229, column_h=-0.0905715` | `1.67459/1` | 0.211634 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.66728/-1` | -0.298964 | 5.04642 | `width=0, bank=0, face_h=0.424249, column_h=0.125027` | `-3.97436/-1` | -2.60604 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.684602/1` | -0.0442896 | -13.5606 | `width=1, bank=0, face_h=-0.439251, column_h=-0.247442` | `1.29833/1` | 0.569434 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.38079/-1` | 0.288741 | 0.0495298 | `width=1, bank=0, face_h=0.0783373, column_h=-0.247442` | `-2.10728/-1` | -0.437753 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.94653/-1` | -0.539187 | -2.36493 | `width=0, bank=0, face_h=-0.210563, column_h=-0.075691` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.66108/1` | 0.344202 | 2.91458 | `width=0, bank=0, face_h=0.0694885, column_h=0.0105839` | `2.90391/1` | 1.58704 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `0.576072/1` | 0.339945 | -5.03063 | `width=0, bank=0, face_h=-0.1769, column_h=-0.0630068` | `2.00113/1` | 1.765 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.45761/-1` | -0.225893 | 1.1692 | `width=0, bank=0, face_h=0.0648856, column_h=-0.0630068` | `-2.52105/-1` | -1.28933 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `1.82644/1` | -0.148545 | 1.50114 | `width=0, bank=0, face_h=0.0787885, column_h=-0.0150012` | `2.95054/1` | 0.975558 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.50833/-1` | -0.140055 | 1.33216 | `width=0, bank=0, face_h=0.102397, column_h=-0.0244649` | `-2.89658/-1` | -1.52831 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.42231/-1` | -0.139587 | 1.23503 | `width=0, bank=0, face_h=0.0911467, column_h=-0.0905715` | `-2.29075/-1` | -1.00803 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 3 | `1-2` | `0.823895/1` | `0.932153/1` | 0.108258 | -1.84334 | `width=0, bank=0, face_h=-0.0700269, column_h=-0.0244649` | `2.31322/1` | 1.48933 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.706065 m3/s, balance delta is -9.43695 m3/s2, native post-source delta is 0.211634 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
