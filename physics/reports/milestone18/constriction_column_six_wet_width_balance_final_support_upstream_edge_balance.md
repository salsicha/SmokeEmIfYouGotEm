# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_column_six_wet_width_balance_final_support_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_column_six_wet_width_balance_final_support_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `5`
- Blocked targets: `5`
- Width/depth coupled blockers: `0`
- Source-balance blockers: `5`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.132175` m3/s
- Max abs balance delta: `3.34688` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 3 | `1-2` | `0.823895/1` | `0.691719/1` | -0.132175 | -2.30136 | `width=0, bank=0, face_h=-0.0722688, column_h=-0.0196697` | `2.03084/1` | 1.20694 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.46348/-1` | -0.0952054 | 0.941804 | `width=0, bank=0, face_h=0.0744712, column_h=-0.0196697` | `-2.57664/-1` | -1.20836 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `1.96812/1` | -0.0775862 | -1.43478 | `width=0, bank=0, face_h=-0.0414057, column_h=-0.0470814` | `3.41704/1` | 1.37133 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | `0.379808/1` | 0.0280133 | 3.34688 | `width=0, bank=0, face_h=0.106778, column_h=0.0130552` | `3.70575/1` | 3.35396 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.720694/1` | -0.00819801 | -1.11743 | `width=0, bank=0, face_h=-0.0337693, column_h=-0.0454958` | `3.13854/1` | 2.40965 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.

## Next Levers

- Start with `lower_edge_face` column 3 rows 1-2; q delta is -0.132175 m3/s, balance delta is -2.30136 m3/s2, native post-source delta is 1.20694 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
