# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_lower_edge_flux_magnitude_face_state_width_depth_diagnostic.json`
Face/source audit report: `physics/reports/milestone18/constriction_lower_edge_flux_magnitude_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `9`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.34656` m3/s
- Max abs balance delta: `15.0996` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.699146/1` | -1.34656 | -11.8047 | `width=0, bank=0, face_h=-0.295887, column_h=-0.268088` | `2.34886/1` | 0.303146 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.862744/-1` | 1.14493 | -1.1513 | `width=0, bank=0, face_h=0.121824, column_h=-0.268088` | `-3.68685/-1` | -1.67918 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.345512/1` | -1.11745 | -11.4962 | `width=0, bank=0, face_h=-0.327684, column_h=-0.104938` | `1.36763/1` | -0.0953252 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-1.17235/-1` | 0.738931 | 2.74087 | `width=0, bank=0, face_h=0.427556, column_h=-0.0276777` | `-3.98015/-1` | -2.06887 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.622449/1` | 0.548139 | 13.4101 | `width=0, bank=0, face_h=0.509697, column_h=-0.0237124` | `0.353681/1` | 0.279371 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.574973/1` | 0.513457 | 11.1499 | `width=0, bank=0, face_h=0.429519, column_h=0.192933` | `0.392246/1` | 0.33073 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.233351/1` | -0.495541 | -15.0996 | `width=1, bank=0, face_h=-0.477706, column_h=-0.257825` | `0.952091/1` | 0.223199 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.38788/-1` | 0.28165 | 3.19977 | `width=1, bank=0, face_h=0.333271, column_h=-0.257825` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.17452/-1` | 0.193754 | 3.8486 | `width=0, bank=0, face_h=0.371079, column_h=-0.059913` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.09851/-1` | 1.20011 | 0.574393 | `width=0, bank=0, face_h=0.397393, column_h=-0.0643326` | `-3.98015/-1` | -1.68153 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.14976/-1` | 0.132963 | 0 | `width=0, bank=0, face_h=0.388273, column_h=-0.104938` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.13041/-1` | 0.101304 | 0 | `width=0, bank=0, face_h=0.363237, column_h=-0.0868974` | `-3.98015/-1` | -2.74844 | `upstream_edge_width_depth_mapping` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
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

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `lower_edge_face` column 0 rows 1-2; q delta is -1.34656 m3/s, balance delta is -11.8047 m3/s2, native post-source delta is 0.303146 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
