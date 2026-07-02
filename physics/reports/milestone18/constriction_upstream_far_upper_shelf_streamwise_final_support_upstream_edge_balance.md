# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_upstream_far_upper_shelf_streamwise_final_support_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_upstream_far_upper_shelf_streamwise_final_support_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `7`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.706075` m3/s
- Max abs balance delta: `12.8506` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.756882/1` | -0.706075 | -9.43719 | `width=0, bank=0, face_h=-0.272298, column_h=-0.090556` | `1.6746/1` | 0.211642 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.641358/1` | 0.567048 | 12.8506 | `width=0, bank=0, face_h=0.488136, column_h=9.38352e-05` | `0.517464/1` | 0.443154 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.489498/1` | 0.427981 | 8.69312 | `width=0, bank=0, face_h=0.340222, column_h=0.232673` | `0.612181/1` | 0.550664 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.74808/-1` | -0.379765 | 5.98668 | `width=0, bank=0, face_h=0.48323, column_h=0.232673` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.63492/-1` | -0.352197 | 3.82852 | `width=0, bank=0, face_h=0.276293, column_h=-0.090556` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.5887/-1` | 0.0808314 | 2.73687 | `width=1, bank=0, face_h=0.267152, column_h=-0.248804` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.684229/1` | -0.0446629 | 0 | `width=1, bank=0, face_h=-0.439811, column_h=-0.248804` | `1.29958/1` | 0.570689 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.972/-1` | -0.564649 | -2.10394 | `width=0, bank=0, face_h=-0.196966, column_h=9.38352e-05` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.65101/-1` | -0.419296 | 3.37383 | `width=0, bank=0, face_h=0.224827, column_h=-0.0629947` | `-3.98015/-1` | -2.74844 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-2.31554/-1` | -0.404264 | 1.78418 | `width=0, bank=0, face_h=0.027246, column_h=0.00971622` | `-2.97095/-1` | -1.05967 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.66085/1` | 0.343974 | 3.20978 | `width=0, bank=0, face_h=0.0800817, column_h=0.00971622` | `2.8841/1` | 1.56723 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `0.576073/1` | 0.339947 | -5.03084 | `width=0, bank=0, face_h=-0.176907, column_h=-0.0629947` | `2.00114/1` | 1.76501 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.706075 m3/s, balance delta is -9.43719 m3/s2, native post-source delta is 0.211642 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
