# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_lower_edge_transition_momentum_face_state_width_depth_diagnostic.json`
Face/source audit report: `physics/reports/milestone18/constriction_lower_edge_transition_momentum_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `9`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.34647` m3/s
- Max abs balance delta: `15.2796` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.69924/1` | -1.34647 | -11.7968 | `width=0, bank=0, face_h=-0.295609, column_h=-0.267676` | `2.34847/1` | 0.302756 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.863296/-1` | 1.14438 | -1.1428 | `width=0, bank=0, face_h=0.122427, column_h=-0.267676` | `-3.68772/-1` | -1.68005 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.344635/1` | -1.11832 | -11.598 | `width=0, bank=0, face_h=-0.331233, column_h=-0.109997` | `1.37595/1` | -0.0870056 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-1.1726/-1` | 0.738674 | 2.74363 | `width=0, bank=0, face_h=0.427726, column_h=-0.0275627` | `-3.98015/-1` | -2.06887 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.656305/1` | 0.581995 | 13.7535 | `width=0, bank=0, face_h=0.520363, column_h=-0.00620731` | `0.375184/1` | 0.300874 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.58526/1` | 0.523743 | 11.3502 | `width=0, bank=0, face_h=0.436475, column_h=0.204499` | `0.384336/1` | 0.32282 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.265582/1` | -0.463309 | -15.2796 | `width=1, bank=0, face_h=-0.484644, column_h=-0.26724` | `1.02571/1` | 0.296818 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.27098/-1` | 0.398548 | 2.81595 | `width=1, bank=0, face_h=0.320594, column_h=-0.26724` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.17396/-1` | 0.194309 | 3.84012 | `width=0, bank=0, face_h=0.370523, column_h=-0.0603275` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.09913/-1` | 1.19949 | 0.582437 | `width=0, bank=0, face_h=0.397918, column_h=-0.0639718` | `-3.98015/-1` | -1.68153 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.14159/-1` | 0.141137 | 0 | `width=0, bank=0, face_h=0.381398, column_h=-0.109997` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.12816/-1` | 0.103554 | 0 | `width=0, bank=0, face_h=0.361115, column_h=-0.0884636` | `-3.98015/-1` | -2.74844 | `upstream_edge_width_depth_mapping` |

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

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `lower_edge_face` column 0 rows 1-2; q delta is -1.34647 m3/s, balance delta is -11.7968 m3/s2, native post-source delta is 0.302756 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
