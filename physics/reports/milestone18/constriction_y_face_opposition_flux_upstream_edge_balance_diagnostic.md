# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_y_face_opposition_flux_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_y_face_opposition_flux_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `6`
- Paired-edge opposition mismatches: `8`
- Max abs volume-flux delta: `5.88954` m3/s
- Max abs balance delta: `13.049` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `-4.42658/-1` | -5.88954 | 10.5151 | `width=-1, bank=1, face_h=-0.228288, column_h=0.33213` | `-0.451623/-1` | -1.91458 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `-4.06486/-1` | -4.79375 | 4.87417 | `width=0, bank=1, face_h=-0.320509, column_h=0.206855` | `-1.07935/-1` | -1.80824 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `1.92305/1` | 3.59258 | 13.044 | `width=0, bank=1, face_h=0.873453, column_h=0.206855` | `0.836478/1` | 2.50601 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 7 | `7-8` | `-1.25704/-1` | `2.00052/1` | 3.25755 | 9.32517 | `width=-1, bank=1, face_h=0.416219, column_h=0.322993` | `1.82182/1` | 3.07885 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `1.39318/1` | 2.80053 | 5.59664 | `width=0, bank=0, face_h=0.294033, column_h=0.383559` | `1.39318/1` | 2.80053 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `0.950329/1` | 2.31865 | 12.9766 | `width=0, bank=0, face_h=0.993397, column_h=0.591146` | `0.950329/1` | 2.31865 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `1.45691/1` | 2.73963 | 13.049 | `width=-1, bank=1, face_h=0.884468, column_h=0.33213` | `-0.458478/-1` | 0.824245 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `0.0631482/0` | 2.36177 | 0.414253 | `width=-1, bank=1, face_h=0.444727, column_h=-0.0280784` | `-3.00037/-1` | -0.701753 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `0.0198839/0` | 2.02756 | -1.81086 | `width=-2, bank=1, face_h=0.113332, column_h=-0.192824` | `-2.95047/-1` | -0.942803 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `0.10352/1` | 2.0148 | 3.65452 | `width=0, bank=0, face_h=0.549472, column_h=-0.0231842` | `-3.04381/-1` | -1.13253 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `0.70877/1` | 1.94048 | 9.76811 | `width=-1, bank=1, face_h=0.74603, column_h=0.244131` | `-1.86922/-1` | -0.637503 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `0.394393/1` | 1.76267 | 6.83756 | `width=-1, bank=1, face_h=0.619074, column_h=0.14316` | `-2.78194/-1` | -1.41367 | `upstream_edge_width_depth_flux_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 0 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->-1` | `-1->1` | `True` | `True` | `True` |
| 6 | `1->-1` | `-1->1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Native C++ post-source y-face flux signs still disagree with GeoClaw.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -5.88954 m3/s, balance delta is 10.5151 m3/s2, native post-source delta is -1.91458 m3/s, wet-width delta is -1 cells, and bank-row delta is 1 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
