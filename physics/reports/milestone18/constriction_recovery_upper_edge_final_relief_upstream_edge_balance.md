# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_recovery_upper_edge_final_relief_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_recovery_upper_edge_final_relief_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `7`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.706344` m3/s
- Max abs balance delta: `12.81` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.756613/1` | -0.706344 | -9.44548 | `width=0, bank=0, face_h=-0.272574, column_h=-0.092127` | `1.67499/1` | 0.212033 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.640247/1` | 0.565937 | 12.81 | `width=0, bank=0, face_h=0.486703, column_h=-0.000875535` | `0.520936/1` | 0.446626 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.487527/1` | 0.42601 | 8.6209 | `width=0, bank=0, face_h=0.337519, column_h=0.228375` | `0.618532/1` | 0.557016 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.7421/-1` | -0.373781 | 5.90751 | `width=0, bank=0, face_h=0.478215, column_h=0.228375` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.63335/-1` | -0.350627 | 3.80523 | `width=0, bank=0, face_h=0.274687, column_h=-0.092127` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.58674/-1` | 0.082787 | 2.70997 | `width=1, bank=0, face_h=0.265377, column_h=-0.250542` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.683953/1` | -0.0449385 | 0 | `width=1, bank=0, face_h=-0.440124, column_h=-0.250542` | `1.30018/1` | 0.571289 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.97049/-1` | -0.56314 | -2.12633 | `width=0, bank=0, face_h=-0.198237, column_h=-0.000875535` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.85978/-1` | 0.438844 | -1.72195 | `width=0, bank=0, face_h=0.0050675, column_h=-0.0345851` | `-2.99841/-1` | -0.699795 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.64949/-1` | -0.417778 | 3.35316 | `width=0, bank=0, face_h=0.223365, column_h=-0.0644098` | `-3.98015/-1` | -2.74844 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.66003/1` | 0.343161 | 3.19193 | `width=0, bank=0, face_h=0.0795326, column_h=0.00708046` | `2.88457/1` | 1.56769 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `0.575935/1` | 0.339809 | -5.0381 | `width=0, bank=0, face_h=-0.177153, column_h=-0.0644098` | `2.00141/1` | 1.76528 | `upstream_edge_y_face_flux_source_balance` |

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

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.706344 m3/s, balance delta is -9.44548 m3/s2, native post-source delta is 0.212033 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
