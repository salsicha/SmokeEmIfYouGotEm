# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_upstream_transition_edge_final_profile_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_upstream_transition_edge_final_profile_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `9`
- Source-balance blockers: `10`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `1.00669` m3/s
- Max abs balance delta: `12.8097` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.640238/1` | 0.565928 | 12.8097 | `width=0, bank=0, face_h=0.486692, column_h=-0.000883441` | `0.520962/1` | 0.446652 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.942079/1` | -0.520878 | -9.14841 | `width=0, bank=0, face_h=-0.273511, column_h=-0.0924912` | `1.70197/1` | 0.239013 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.22308/-1` | 0.446451 | 2.50259 | `width=1, bank=0, face_h=0.303623, column_h=-0.251007` | `-3.90274/-1` | -2.23321 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.487525/1` | 0.426009 | 8.62083 | `width=0, bank=0, face_h=0.337517, column_h=0.228371` | `0.618538/1` | 0.557022 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.74209/-1` | -0.373776 | 5.90743 | `width=0, bank=0, face_h=0.47821, column_h=0.228371` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.58812/-1` | -0.219843 | 4.42003 | `width=0, bank=0, face_h=0.354692, column_h=-0.0255585` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.38294/-1` | -0.151228 | 4.0553 | `width=0, bank=0, face_h=0.327111, column_h=-0.0645392` | `-3.98015/-1` | -2.74844 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.2168/-1` | 0.0659247 | 0 | `width=0, bank=0, face_h=0.346379, column_h=-0.0924912` | `-3.97255/-1` | -2.68983 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.696724/1` | -0.0321677 | 0 | `width=1, bank=0, face_h=-0.440668, column_h=-0.251007` | `1.31479/1` | 0.585893 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `1.24282/1` | 1.00669 | -3.78281 | `width=0, bank=0, face_h=-0.176613, column_h=-0.0645392` | `2.03779/1` | 1.80166 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.97047/-1` | -0.563127 | -2.12653 | `width=0, bank=0, face_h=-0.198248, column_h=-0.000883441` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.87765/1` | 0.560777 | 3.90475 | `width=0, bank=0, face_h=0.0797865, column_h=0.00746997` | `2.90326/1` | 1.58639 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 8 rows 2-3; q delta is 0.565928 m3/s, balance delta is 12.8097 m3/s2, native post-source delta is 0.446652 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
