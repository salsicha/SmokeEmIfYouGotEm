# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_recovery_lower_interior_cross_stream_pocket_final_support_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_recovery_lower_interior_cross_stream_pocket_final_support_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `2`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.302188` m3/s
- Max abs balance delta: `9.58436` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.656855/1` | -0.0720362 | -9.58436 | `width=1, bank=0, face_h=-0.301868, column_h=-0.247442` | `2.39879/1` | 1.6699 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.60319/-1` | 0.0663386 | -0.4596 | `width=1, bank=0, face_h=-0.029509, column_h=-0.247442` | `-1.6745/-1` | -0.00496879 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `1.16077/1` | -0.302188 | -5.75238 | `width=0, bank=0, face_h=-0.17051, column_h=-0.0905715` | `2.4518/1` | 0.98884 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `0.512366/1` | 0.27624 | -5.09928 | `width=0, bank=0, face_h=-0.176822, column_h=-0.0630068` | `1.92359/1` | 1.68746 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.58673/1` | 0.26986 | 1.35213 | `width=0, bank=0, face_h=0.0211954, column_h=0.0105839` | `2.4671/1` | 1.15023 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.45755/-1` | -0.225841 | 1.16865 | `width=0, bank=0, face_h=0.0648437, column_h=-0.0630068` | `-2.52076/-1` | -1.28905 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-1.82471/-1` | 0.182962 | -1.10218 | `width=0, bank=0, face_h=-0.0557906, column_h=-0.0606812` | `-3.68214/-1` | -1.67447 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.50833/-1` | -0.140055 | 1.33216 | `width=0, bank=0, face_h=0.102397, column_h=-0.024794` | `-2.89658/-1` | -1.52831 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-2.42674/-1` | -0.128123 | 0.763059 | `width=0, bank=0, face_h=0.0354444, column_h=-0.0150012` | `-3.14486/-1` | -0.846237 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `1.96812/1` | -0.0775862 | -1.43478 | `width=0, bank=0, face_h=-0.0414057, column_h=-0.0606812` | `3.41704/1` | 1.37133 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 3 | `1-2` | `0.823895/1` | `0.777702/1` | -0.0461928 | -2.17379 | `width=0, bank=0, face_h=-0.0722688, column_h=-0.024794` | `2.13313/1` | 1.30924 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | `0.314011/1` | -0.0377829 | -2.86736 | `width=0, bank=0, face_h=-0.0941857, column_h=-0.025649` | `2.28865/1` | 1.93685 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 6 rows 1-2; q delta is -0.0720362 m3/s, balance delta is -9.58436 m3/s2, native post-source delta is 1.6699 m3/s, wet-width delta is 1 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
