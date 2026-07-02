# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_upstream_lower_edge_profile_final_relief_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_upstream_lower_edge_profile_final_relief_face_source_audit.json`
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
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.756886/1` | -0.706071 | -9.43709 | `width=0, bank=0, face_h=-0.272295, column_h=-0.0905707` | `1.6746/1` | 0.211638 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.66744/-1` | -0.299123 | 5.04859 | `width=0, bank=0, face_h=0.424394, column_h=0.125107` | `-3.97491/-1` | -2.60659 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.684596/1` | -0.044296 | -13.5608 | `width=1, bank=0, face_h=-0.439256, column_h=-0.24744` | `1.29833/1` | 0.56944 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.3808/-1` | 0.288735 | 0.0496024 | `width=1, bank=0, face_h=0.0783426, column_h=-0.24744` | `-2.10723/-1` | -0.437699 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.94656/-1` | -0.539216 | -2.36445 | `width=0, bank=0, face_h=-0.210535, column_h=-0.075676` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.66085/1` | 0.343979 | 3.20986 | `width=0, bank=0, face_h=0.0800841, column_h=0.00968453` | `2.8841/1` | 1.56722 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `0.576075/1` | 0.339948 | -5.03079 | `width=0, bank=0, face_h=-0.176906, column_h=-0.0630094` | `2.00114/1` | 1.76501 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.4576/-1` | -0.225889 | 1.16916 | `width=0, bank=0, face_h=0.0648826, column_h=-0.0630094` | `-2.52099/-1` | -1.28928 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `1.82806/1` | -0.14693 | 1.89449 | `width=0, bank=0, face_h=0.093092, column_h=-0.0257112` | `2.92409/1` | 0.949107 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.42232/-1` | -0.139596 | 1.23512 | `width=0, bank=0, face_h=0.091153, column_h=-0.0905707` | `-2.29075/-1` | -1.00803 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.50786/-1` | -0.139589 | 1.28353 | `width=0, bank=0, face_h=0.0976569, column_h=-0.0250609` | `-2.87421/-1` | -1.50594 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 3 | `1-2` | `0.823895/1` | `0.932284/1` | 0.108389 | -1.83283 | `width=0, bank=0, face_h=-0.0696664, column_h=-0.0250609` | `2.31258/1` | 1.48869 | `upstream_edge_y_face_flux_source_balance` |

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

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.706071 m3/s, balance delta is -9.43709 m3/s2, native post-source delta is 0.211638 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
