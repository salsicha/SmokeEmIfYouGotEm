# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_upstream_boundary_upper_shelf_final_support_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_upstream_boundary_upper_shelf_final_support_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `7`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.706295` m3/s
- Max abs balance delta: `12.8157` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.756662/1` | -0.706295 | -9.44416 | `width=0, bank=0, face_h=-0.27253, column_h=-0.0919029` | `1.67494/1` | 0.211979 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.640401/1` | 0.566091 | 12.8157 | `width=0, bank=0, face_h=0.486902, column_h=-0.00070603` | `0.520454/1` | 0.446143 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.487603/1` | 0.426087 | 8.62371 | `width=0, bank=0, face_h=0.337625, column_h=0.228741` | `0.618285/1` | 0.556769 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.74259/-1` | -0.374269 | 5.91378 | `width=0, bank=0, face_h=0.478611, column_h=0.228741` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.63346/-1` | -0.350742 | 3.80726 | `width=0, bank=0, face_h=0.274831, column_h=-0.0919029` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.5869/-1` | 0.0826271 | 2.71229 | `width=1, bank=0, face_h=0.265532, column_h=-0.2503` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.684004/1` | -0.0448878 | 0 | `width=1, bank=0, face_h=-0.440076, column_h=-0.2503` | `1.3001/1` | 0.571209 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.97079/-1` | -0.563439 | -2.12196 | `width=0, bank=0, face_h=-0.197989, column_h=-0.00070603` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.86965/-1` | 0.42897 | -1.64433 | `width=0, bank=0, face_h=0.0110513, column_h=-0.0284235` | `-2.99154/-1` | -0.692918 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.6496/-1` | -0.417889 | 3.35503 | `width=0, bank=0, face_h=0.223503, column_h=-0.0642023` | `-3.98015/-1` | -2.74844 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.6602/1` | 0.343326 | 3.19582 | `width=0, bank=0, face_h=0.0796537, column_h=0.00747322` | `2.88445/1` | 1.56757 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `0.575963/1` | 0.339837 | -5.03691 | `width=0, bank=0, face_h=-0.177113, column_h=-0.0642023` | `2.00137/1` | 1.76524 | `upstream_edge_y_face_flux_source_balance` |

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
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.706295 m3/s, balance delta is -9.44416 m3/s2, native post-source delta is 0.211979 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
