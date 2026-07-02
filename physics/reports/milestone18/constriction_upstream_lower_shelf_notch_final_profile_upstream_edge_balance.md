# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_upstream_lower_shelf_notch_final_profile_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_upstream_lower_shelf_notch_final_profile_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `7`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.706346` m3/s
- Max abs balance delta: `12.8096` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.756611/1` | -0.706346 | -9.44556 | `width=0, bank=0, face_h=-0.272576, column_h=-0.0921353` | `1.67499/1` | 0.212037 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.640236/1` | 0.565926 | 12.8096 | `width=0, bank=0, face_h=0.486689, column_h=-0.000885774` | `0.520969/1` | 0.446659 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.487522/1` | 0.426006 | 8.62073 | `width=0, bank=0, face_h=0.337513, column_h=0.228364` | `0.618546/1` | 0.55703 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.74209/-1` | -0.373766 | 5.90731 | `width=0, bank=0, face_h=0.478202, column_h=0.228364` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.63334/-1` | -0.350618 | 3.8051 | `width=0, bank=0, face_h=0.274678, column_h=-0.0921353` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.58674/-1` | 0.0827953 | 2.70985 | `width=1, bank=0, face_h=0.265369, column_h=-0.25055` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.683952/1` | -0.04494 | 0 | `width=1, bank=0, face_h=-0.440126, column_h=-0.25055` | `1.30018/1` | 0.571292 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.97047/-1` | -0.563123 | -2.12658 | `width=0, bank=0, face_h=-0.198251, column_h=-0.000885774` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.85975/-1` | 0.43887 | -1.72249 | `width=0, bank=0, face_h=0.00500306, column_h=-0.0346285` | `-2.99855/-1` | -0.699931 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.64939/-1` | -0.417673 | 3.34817 | `width=0, bank=0, face_h=0.222955, column_h=-0.0645051` | `-3.98015/-1` | -2.74844 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.66002/1` | 0.343151 | 3.19302 | `width=0, bank=0, face_h=0.0795727, column_h=0.00717051` | `2.88448/1` | 1.56761 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `0.575939/1` | 0.339813 | -5.03854 | `width=0, bank=0, face_h=-0.177169, column_h=-0.0645051` | `2.00144/1` | 1.76531 | `upstream_edge_y_face_flux_source_balance` |

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

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.706346 m3/s, balance delta is -9.44556 m3/s2, native post-source delta is 0.212037 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
