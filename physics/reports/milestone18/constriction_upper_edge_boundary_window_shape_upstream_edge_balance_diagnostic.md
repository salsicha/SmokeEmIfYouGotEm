# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_upper_edge_boundary_window_shape_face_state_width_depth_diagnostic.json`
Face/source audit report: `physics/reports/milestone18/constriction_upper_edge_boundary_window_shape_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `11`
- Source-balance blockers: `9`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.11311` m3/s
- Max abs balance delta: `14.8858` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.349851/1` | -1.11311 | -11.1393 | `width=0, bank=0, face_h=-0.315298, column_h=-0.0861857` | `1.34025/1` | -0.122702 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.42893/-1` | 0.869693 | 2.06814 | `width=0, bank=0, face_h=0.465102, column_h=-0.0175624` | `-3.98015/-1` | -1.68153 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.658902/1` | 0.584592 | 14.1554 | `width=0, bank=0, face_h=0.534811, column_h=0.0178186` | `0.322427/1` | 0.248117 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.597143/1` | 0.535627 | 11.8817 | `width=0, bank=0, face_h=0.455731, column_h=0.237409` | `0.329583/1` | 0.268067 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.269024/1` | -0.459868 | -14.8858 | `width=1, bank=0, face_h=-0.470901, column_h=-0.246319` | `0.989384/1` | 0.260493 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-1.52979/-1` | 0.381482 | 4.2699 | `width=0, bank=0, face_h=0.491115, column_h=0.0161636` | `-3.98015/-1` | -2.06887 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.29928/-1` | 0.370253 | 3.24592 | `width=1, bank=0, face_h=0.34809, column_h=-0.246319` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.17509/-1` | 0.107637 | 4.7552 | `width=0, bank=0, face_h=0.412832, column_h=-0.0861857` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.26659/-1` | 0.10168 | 0 | `width=0, bank=0, face_h=0.422467, column_h=-0.0212471` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.1748/-1` | 0.0569173 | 0 | `width=0, bank=0, face_h=0.39944, column_h=-0.0595572` | `-3.98015/-1` | -2.74844 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.33206/-1` | 0.0362593 | 0 | `width=0, bank=0, face_h=0.540499, column_h=0.237409` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | `-0.0511303/0` | -0.402925 | -3.2846 | `width=0, bank=0, face_h=-0.105102, column_h=-0.0988624` | `0.47536/1` | 0.123566 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->0` | `-1->-1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
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

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -1.11311 m3/s, balance delta is -11.1393 m3/s2, native post-source delta is -0.122702 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
