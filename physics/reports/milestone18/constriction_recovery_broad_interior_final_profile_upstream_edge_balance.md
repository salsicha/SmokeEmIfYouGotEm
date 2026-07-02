# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_recovery_broad_interior_final_profile_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_recovery_broad_interior_final_profile_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `9`
- Source-balance blockers: `10`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `1.00669` m3/s
- Max abs balance delta: `12.8095` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.640233/1` | 0.565923 | 12.8095 | `width=0, bank=0, face_h=0.486685, column_h=-0.000888378` | `0.520978/1` | 0.446668 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.942078/1` | -0.520879 | -9.14841 | `width=0, bank=0, face_h=-0.273511, column_h=-0.0924949` | `1.70197/1` | 0.239014 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.22308/-1` | 0.446454 | 2.50254 | `width=1, bank=0, face_h=0.303619, column_h=-0.251011` | `-3.90275/-1` | -2.23322 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.487522/1` | 0.426006 | 8.62073 | `width=0, bank=0, face_h=0.337513, column_h=0.228364` | `0.618546/1` | 0.55703 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.74209/-1` | -0.373767 | 5.90731 | `width=0, bank=0, face_h=0.478203, column_h=0.228364` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.58811/-1` | -0.21984 | 4.41998 | `width=0, bank=0, face_h=0.354689, column_h=-0.0255619` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.38294/-1` | -0.151225 | 4.05525 | `width=0, bank=0, face_h=0.327108, column_h=-0.0645428` | `-3.98015/-1` | -2.74844 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.2168/-1` | 0.0659275 | 0 | `width=0, bank=0, face_h=0.346376, column_h=-0.0924949` | `-3.97256/-1` | -2.68983 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.696724/1` | -0.0321679 | 0 | `width=1, bank=0, face_h=-0.440668, column_h=-0.251011` | `1.31479/1` | 0.585894 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `1.24282/1` | 1.00669 | -3.78282 | `width=0, bank=0, face_h=-0.176613, column_h=-0.0645428` | `2.03779/1` | 1.80166 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.97047/-1` | -0.563119 | -2.12665 | `width=0, bank=0, face_h=-0.198255, column_h=-0.000888378` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.87765/1` | 0.560777 | 3.90474 | `width=0, bank=0, face_h=0.0797862, column_h=0.00746594` | `2.90326/1` | 1.58639 | `upstream_edge_y_face_flux_source_balance` |

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

- Start with `lower_edge_face` column 8 rows 2-3; q delta is 0.565923 m3/s, balance delta is 12.8095 m3/s2, native post-source delta is 0.446668 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
