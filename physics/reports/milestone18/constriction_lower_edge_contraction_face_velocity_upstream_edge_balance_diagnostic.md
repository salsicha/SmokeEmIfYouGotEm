# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_lower_edge_contraction_face_velocity_face_state_width_depth_diagnostic.json`
Face/source audit report: `physics/reports/milestone18/constriction_lower_edge_contraction_face_velocity_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `11`
- Source-balance blockers: `10`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `1.54926` m3/s
- Max abs balance delta: `14.2326` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.655993/1` | -0.806964 | -9.79079 | `width=0, bank=0, face_h=-0.279524, column_h=-0.084858` | `1.61296/1` | 0.150003 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.49799/-1` | 0.800635 | 2.21042 | `width=0, bank=0, face_h=0.465671, column_h=-0.0171095` | `-3.98015/-1` | -1.68153 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.705406/1` | 0.631096 | 14.2326 | `width=0, bank=0, face_h=0.534977, column_h=0.0181136` | `0.453181/1` | 0.378871 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.08916/-1` | 0.580368 | 2.60276 | `width=1, bank=0, face_h=0.326162, column_h=-0.246309` | `-3.78256/-1` | -2.11303 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.641283/1` | 0.579767 | 11.966 | `width=0, bank=0, face_h=0.456287, column_h=0.238382` | `0.454259/1` | 0.392743 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-1.59475/-1` | 0.31653 | 4.46495 | `width=0, bank=0, face_h=0.495613, column_h=0.0192682` | `-3.98015/-1` | -2.06887 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-0.980132/-1` | 0.302591 | 4.10525 | `width=0, bank=0, face_h=0.386839, column_h=-0.084858` | `-3.75681/-1` | -2.47408 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.17714/-1` | 0.191183 | 5.66829 | `width=0, bank=0, face_h=0.541604, column_h=0.238382` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.558606/1` | -0.170286 | -13.8538 | `width=1, bank=0, face_h=-0.443754, column_h=-0.246309` | `1.27584/1` | 0.546951 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.0995/-1` | 0.132214 | 0 | `width=0, bank=0, face_h=0.38219, column_h=-0.0562742` | `-3.94269/-1` | -2.71097 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.26969/-1` | 0.0985824 | 0 | `width=0, bank=0, face_h=0.425428, column_h=-0.0164455` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `0.425722/1` | -1.54926 | -4.28791 | `width=0, bank=0, face_h=-0.0167998, column_h=-0.0171095` | `2.06158/1` | 0.0865891 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.806964 m3/s, balance delta is -9.79079 m3/s2, native post-source delta is 0.150003 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
