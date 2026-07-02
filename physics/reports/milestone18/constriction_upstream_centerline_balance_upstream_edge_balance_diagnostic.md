# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_upstream_centerline_balance_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_upstream_centerline_balance_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `9`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.47731` m3/s
- Max abs balance delta: `15.0906` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.568401/1` | -1.47731 | -11.9526 | `width=0, bank=0, face_h=-0.294614, column_h=-0.266477` | `2.26909/1` | 0.223385 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.273114/1` | -1.18984 | -11.5212 | `width=0, bank=0, face_h=-0.326849, column_h=-0.104453` | `1.28546/1` | -0.177495 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.22932/-1` | 1.0693 | 0.750484 | `width=0, bank=0, face_h=0.394694, column_h=-0.0661322` | `-3.98015/-1` | -1.68153 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.964734/-1` | 1.04294 | -0.983116 | `width=0, bank=0, face_h=0.124254, column_h=-0.266477` | `-3.79131/-1` | -1.78363 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-1.30852/-1` | 0.602755 | 2.90868 | `width=0, bank=0, face_h=0.423088, column_h=-0.0306599` | `-3.98015/-1` | -2.06887 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.62135/1` | 0.54704 | 13.4196 | `width=0, bank=0, face_h=0.510103, column_h=-0.0230498` | `0.349985/1` | 0.275675 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.195203/1` | -0.533688 | -15.0906 | `width=1, bank=0, face_h=-0.476763, column_h=-0.256865` | `0.903393/1` | 0.174502 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.574824/1` | 0.513308 | 11.1599 | `width=0, bank=0, face_h=0.429902, column_h=0.193558` | `0.390419/1` | 0.328902 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.44199/-1` | 0.227542 | 3.3194 | `width=1, bank=0, face_h=0.334494, column_h=-0.256865` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.29875/-1` | 0.0695664 | 0 | `width=0, bank=0, face_h=0.490126, column_h=0.193558` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.29947/-1` | 0.0687995 | 0 | `width=0, bank=0, face_h=0.366972, column_h=-0.0627914` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.25542/-1` | 0.0272989 | 0 | `width=0, bank=0, face_h=0.388768, column_h=-0.104453` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_mapping` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `lower_edge_face` column 0 rows 1-2; q delta is -1.47731 m3/s, balance delta is -11.9526 m3/s2, native post-source delta is 0.223385 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
