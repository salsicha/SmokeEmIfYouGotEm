# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_throat_interior_cross_stream_pocket_final_support_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_throat_interior_cross_stream_pocket_final_support_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `4`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.559722` m3/s
- Max abs balance delta: `9.18516` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.903236/1` | -0.559722 | -9.18516 | `width=0, bank=0, face_h=-0.272206, column_h=-0.0905715` | `1.86241/1` | 0.399457 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.25976/-1` | 0.409768 | -1.33357 | `width=1, bank=0, face_h=-0.029509, column_h=-0.247442` | `-1.44818/-1` | 0.221349 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.66698/-1` | -0.298664 | 5.04571 | `width=0, bank=0, face_h=0.424249, column_h=0.125027` | `-3.97389/-1` | -2.60557 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.656855/1` | -0.0720362 | 0 | `width=1, bank=0, face_h=-0.301868, column_h=-0.247442` | `2.39879/1` | 1.6699 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `1.74367/1` | -0.302035 | -2.15509 | `width=0, bank=0, face_h=-0.0414057, column_h=-0.0606812` | `3.28534/1` | 1.23963 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `-1.68664/-1` | -0.279296 | -2.94069 | `width=0, bank=0, face_h=-0.210563, column_h=-0.075691` | `-3.98015/-1` | -2.5728 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.58673/1` | 0.26986 | 1.35213 | `width=0, bank=0, face_h=0.0211954, column_h=0.0105839` | `2.4671/1` | 1.15023 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.45761/-1` | -0.225893 | 1.1692 | `width=0, bank=0, face_h=0.0648856, column_h=-0.0630068` | `-2.52105/-1` | -1.28933 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-1.82471/-1` | 0.182962 | -1.10218 | `width=0, bank=0, face_h=-0.0557906, column_h=-0.0606812` | `-3.68214/-1` | -1.67447 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.50833/-1` | -0.140055 | 1.33216 | `width=0, bank=0, face_h=0.102397, column_h=-0.024794` | `-2.89658/-1` | -1.52831 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.42224/-1` | -0.139518 | 1.23427 | `width=0, bank=0, face_h=0.0910891, column_h=-0.0905715` | `-2.29042/-1` | -1.00769 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 3 | `1-2` | `0.823895/1` | `0.687689/1` | -0.136206 | -2.30697 | `width=0, bank=0, face_h=-0.0722688, column_h=-0.024794` | `2.02592/1` | 1.20203 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.559722 m3/s, balance delta is -9.18516 m3/s2, native post-source delta is 0.399457 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
