# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_upper_boundary_window_velocity_face_state_width_depth_diagnostic.json`
Face/source audit report: `physics/reports/milestone18/constriction_upper_boundary_window_velocity_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `11`
- Source-balance blockers: `9`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `0.850075` m3/s
- Max abs balance delta: `14.1667` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.612882/1` | -0.850075 | -9.83857 | `width=0, bank=0, face_h=-0.279217, column_h=-0.0848054` | `1.57172/1` | 0.108767 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.498/-1` | 0.800615 | 2.21068 | `width=0, bank=0, face_h=0.465687, column_h=-0.0170982` | `-3.98015/-1` | -1.68153 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.663787/1` | 0.589477 | 14.1667 | `width=0, bank=0, face_h=0.534952, column_h=0.0180734` | `0.33103/1` | 0.25672 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.59887/1` | 0.537354 | 11.8988 | `width=0, bank=0, face_h=0.456273, column_h=0.23836` | `0.330736/1` | 0.26922 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.18553/-1` | 0.483996 | 2.74772 | `width=1, bank=0, face_h=0.32594, column_h=-0.246331` | `-3.8904/-1` | -2.22087 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-1.59477/-1` | 0.316508 | 4.46526 | `width=0, bank=0, face_h=0.495632, column_h=0.0192813` | `-3.98015/-1` | -2.06887 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.474753/1` | -0.254138 | -13.9293 | `width=1, bank=0, face_h=-0.443201, column_h=-0.246331` | `1.18768/1` | 0.45879 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.03051/-1` | 0.252208 | 4.17263 | `width=0, bank=0, face_h=0.386817, column_h=-0.0848054` | `-3.81041/-1` | -2.52769 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.09948/-1` | 0.132238 | 0 | `width=0, bank=0, face_h=0.382235, column_h=-0.0562402` | `-3.9427/-1` | -2.71098 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.26971/-1` | 0.09856 | 0 | `width=0, bank=0, face_h=0.425449, column_h=-0.0164299` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.32833/-1` | 0.039986 | 0 | `width=0, bank=0, face_h=0.541579, column_h=0.23836` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | `0.0281292/0` | -0.323665 | -3.15347 | `width=0, bank=0, face_h=-0.100633, column_h=-0.0977564` | `0.548291/1` | 0.196497 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->0` | `-1->-1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.850075 m3/s, balance delta is -9.83857 m3/s2, native post-source delta is 0.108767 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
