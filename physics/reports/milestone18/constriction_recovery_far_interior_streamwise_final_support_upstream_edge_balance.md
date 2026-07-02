# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_recovery_far_interior_streamwise_final_support_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_recovery_far_interior_streamwise_final_support_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `4`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.706071` m3/s
- Max abs balance delta: `13.5608` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.756886/1` | -0.706071 | -9.43708 | `width=0, bank=0, face_h=-0.272294, column_h=-0.0905698` | `1.6746/1` | 0.211638 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.66744/-1` | -0.299126 | 5.04862 | `width=0, bank=0, face_h=0.424396, column_h=0.125109` | `-3.97491/-1` | -2.6066 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.684596/1` | -0.0442959 | -13.5608 | `width=1, bank=0, face_h=-0.439256, column_h=-0.247439` | `1.29833/1` | 0.56944 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.3808/-1` | 0.288734 | 0.0496154 | `width=1, bank=0, face_h=0.0783436, column_h=-0.247439` | `-2.10723/-1` | -0.437697 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.94656/-1` | -0.539217 | -2.36444 | `width=0, bank=0, face_h=-0.210534, column_h=-0.0756754` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.66085/1` | 0.34398 | 3.20987 | `width=0, bank=0, face_h=0.0800842, column_h=0.00968586` | `2.8841/1` | 1.56722 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `0.576075/1` | 0.339948 | -5.03079 | `width=0, bank=0, face_h=-0.176906, column_h=-0.0630085` | `2.00114/1` | 1.76501 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.45761/-1` | -0.225891 | 1.16919 | `width=0, bank=0, face_h=0.0648849, column_h=-0.0630085` | `-2.52101/-1` | -1.28929 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `1.82806/1` | -0.14693 | 1.89449 | `width=0, bank=0, face_h=0.0930922, column_h=-0.0257097` | `2.92409/1` | 0.949107 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.42232/-1` | -0.139599 | 1.23515 | `width=0, bank=0, face_h=0.0911554, column_h=-0.0905698` | `-2.29077/-1` | -1.00804 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.50787/-1` | -0.139592 | 1.28355 | `width=0, bank=0, face_h=0.0976589, column_h=-0.0250601` | `-2.87422/-1` | -1.50595 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 3 | `1-2` | `0.823895/1` | `0.932284/1` | 0.108389 | -1.83282 | `width=0, bank=0, face_h=-0.0696663, column_h=-0.0250601` | `2.31258/1` | 1.48869 | `upstream_edge_y_face_flux_source_balance` |

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
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.706071 m3/s, balance delta is -9.43708 m3/s2, native post-source delta is 0.211638 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
