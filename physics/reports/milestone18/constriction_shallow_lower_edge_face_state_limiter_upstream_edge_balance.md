# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_shallow_lower_edge_face_state_limiter_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_shallow_lower_edge_face_state_limiter_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `7`
- Blocked targets: `7`
- Width/depth coupled blockers: `2`
- Source-balance blockers: `6`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.29451` m3/s
- Max abs balance delta: `5.53726` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.720694/1` | -0.00819801 | -1.11743 | `width=1, bank=0, face_h=-0.0337693, column_h=-0.160457` | `3.13854/1` | 2.40965 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.63372/-1` | 0.0358146 | -0.371775 | `width=1, bank=0, face_h=-0.029509, column_h=-0.160457` | `-1.71542/-1` | -0.0458902 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `1.16845/1` | -0.29451 | -5.53726 | `width=0, bank=0, face_h=-0.163673, column_h=-0.0893286` | `2.44124/1` | 0.978282 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 3 | `1-2` | `0.823895/1` | `0.691719/1` | -0.132175 | -2.30136 | `width=0, bank=0, face_h=-0.0722688, column_h=-0.0196697` | `2.03084/1` | 1.20694 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.46348/-1` | -0.0952054 | 0.941804 | `width=0, bank=0, face_h=0.0744712, column_h=-0.0196697` | `-2.57664/-1` | -1.20836 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `1.96812/1` | -0.0775862 | -1.43478 | `width=0, bank=0, face_h=-0.0414057, column_h=-0.0470814` | `3.41704/1` | 1.37133 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | `0.379808/1` | 0.0280133 | 3.34688 | `width=0, bank=0, face_h=0.106778, column_h=0.0130552` | `3.70575/1` | 3.35396 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 6 rows 1-2; q delta is -0.00819801 m3/s, balance delta is -1.11743 m3/s2, native post-source delta is 2.40965 m3/s, wet-width delta is 1 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
